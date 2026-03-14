"""
LLMService — the single service all agents use to generate LLM responses.

Owns:
  - Calling infra.llm.generate() (the infrastructure LLMClient)
  - Recording cost immediately after every call via CostTrackingService
  - LangSmith trace spans (best-effort)
  - Error normalisation to typed exceptions
  - Returning a fully populated LLMCallResult (text + tokens + cost)

Does NOT own:
  - Retry logic — BaseAgent._run_with_retries() owns that
  - Prompt construction — sub-agents own that
  - Stage record writes — EventService owns that
  - Temperature escalation — BaseAgent owns that

Usage from BaseAgent:
    result = await self._llm_service.generate(
        model_config = self.model_config,
        prompt       = prompt,
        run_id       = run_id,
        stage_name   = self.stage_name,
        attempt      = attempt,
        temperature  = temperature,   # optional override
    )
    text      = result.text
    in_tok    = result.input_tokens
    out_tok   = result.output_tokens
    cost      = result.cost_usd       # already recorded in llm_call_logs

Configured as an attribute on the main service container:
    from services import services
    result = await services.llm.generate(...)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

log = logging.getLogger("pmw.services.llm")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LLMError(Exception):
    """Base exception for all LLM service errors."""

class LLMTimeoutError(LLMError):
    """Request timed out."""

class LLMRateLimitError(LLMError):
    """Provider rate limit hit — caller should back off."""

class LLMProviderError(LLMError):
    """Provider returned an error (4xx/5xx, bad response, etc.)."""

class LLMNotConfiguredError(LLMError):
    """Requested provider is not configured (missing API key)."""


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class LLMCallResult:
    """
    Fully populated result from a single LLM call.

    text:          The generated response text.
    input_tokens:  Prompt tokens consumed.
    output_tokens: Response tokens generated.
    model:         Model ID string used.
    provider:      Provider string used.
    cost_usd:      USD cost for this call — already recorded in llm_call_logs.
                   Agents can use this for the cost.update event payload.
    """
    text:          str
    input_tokens:  int
    output_tokens: int
    model:         str
    provider:      str
    cost_usd:      float


# ---------------------------------------------------------------------------
# LLMService
# ---------------------------------------------------------------------------

class LLMService:
    """
    The single LLM interface used by all agents.

    Stateless — all connections come from get_infrastructure().
    Instantiated once on the ServiceContainer and accessed via services.llm.

    Every call to generate():
      1. Calls infra.llm.generate() (LLMClient handles provider dispatch)
      2. Calls CostTrackingService.record_usage() immediately after
      3. Opens/closes a LangSmith trace span (best-effort)
      4. Returns a fully populated LLMCallResult
    """

    async def generate(
        self,
        model_config,                  # nodes.base.ModelConfig
        prompt:      str,
        run_id:      int,
        stage_name:  str,
        attempt:     int,
        temperature: float | None = None,
        tracer = None,                  # optional LangSmith Client instance
    ) -> LLMCallResult:
        """
        Generate a response and record cost in one call.

        Args:
            model_config: ModelConfig dataclass from the calling agent.
                          Provides provider, model_id, max_tokens, temperature,
                          and fallback cost rates.
            prompt:       Full prompt string.
            run_id:       workflow_runs.id — for cost attribution.
            stage_name:   Stage identifier — for cost attribution.
            attempt:      Attempt number within the retry loop.
            temperature:  Override temperature. Defaults to model_config.temperature.
            tracer:       Optional LangSmith Client for trace spans.

        Returns:
            LLMCallResult — text, token counts, cost (already persisted).

        Raises:
            LLMTimeoutError       on request timeout.
            LLMRateLimitError     on 429 / rate limit.
            LLMProviderError      on any other provider error.
            LLMNotConfiguredError if the requested provider has no API key.
        """
        from infrastructure import get_infrastructure
        from services.cost_tracking_service import CostTrackingService

        infra = get_infrastructure()
        temp  = temperature if temperature is not None else model_config.temperature

        # ── LangSmith trace span (best-effort) ────────────────────────
        run_tree = None
        if tracer:
            try:
                from langsmith.run_trees import RunTree
                run_tree = RunTree(
                    name         = f"{stage_name}.llm_call",
                    run_type     = "llm",
                    inputs       = {"prompt": prompt[:500], "model": model_config.model_id},
                    project_name = os.environ.get("LANGCHAIN_PROJECT", "pmw"),
                )
                run_tree.post()
            except Exception:
                run_tree = None  # tracing is always best-effort

        # ── Generate ──────────────────────────────────────────────────
        try:
            response = await infra.llm.generate(
                provider    = model_config.provider.value,
                model       = model_config.model_id,
                prompt      = prompt,
                temperature = temp,
                max_tokens  = model_config.max_tokens,
            )
        except Exception as exc:
            if run_tree:
                try:
                    run_tree.end(error=str(exc))
                    run_tree.patch()
                except Exception:
                    pass
            raise self._normalise_error(exc) from exc

        # ── Record cost immediately ────────────────────────────────────
        cost_usd = await CostTrackingService().record_usage(
            run_id        = run_id,
            stage_name    = stage_name,
            attempt       = attempt,
            provider      = model_config.provider.value,
            model         = model_config.model_id,
            input_tokens  = response.input_tokens,
            output_tokens = response.output_tokens,
        )

        # ── Close LangSmith span ──────────────────────────────────────
        if run_tree:
            try:
                run_tree.end(outputs={
                    "response":      response.text[:200],
                    "input_tokens":  response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd":      cost_usd,
                })
                run_tree.patch()
            except Exception:
                pass

        log.debug(
            "LLM call complete",
            extra={
                "stage":       stage_name,
                "model":       model_config.model_id,
                "run_id":      run_id,
                "attempt":     attempt,
                "in_tok":      response.input_tokens,
                "out_tok":     response.output_tokens,
                "cost_usd":    cost_usd,
            },
        )

        return LLMCallResult(
            text          = response.text,
            input_tokens  = response.input_tokens,
            output_tokens = response.output_tokens,
            model         = model_config.model_id,
            provider      = model_config.provider.value,
            cost_usd      = cost_usd,
        )

    # ── Error normalisation ────────────────────────────────────────────────

    @staticmethod
    def _normalise_error(exc: Exception) -> LLMError:
        """
        Map raw provider exceptions to typed LLM errors.
        Callers catch LLMTimeoutError / LLMRateLimitError for retry decisions.
        """
        msg = str(exc).lower()
        if "timeout" in msg or "timed out" in msg:
            return LLMTimeoutError(str(exc))
        if "rate limit" in msg or "429" in msg or "too many requests" in msg:
            return LLMRateLimitError(str(exc))
        if "not configured" in msg or "api key" in msg:
            return LLMNotConfiguredError(str(exc))
        return LLMProviderError(str(exc))