"""
PMW Content Pipeline — Base Agent (v2.1)

v2.1 changes:
  - Added FailureConfig dataclass (used by stage agents in __init__)
  - Added EventType string constants (used by _emit_event calls)
  - Added _emit_event / _write_stage_record / _handle_failure compatibility
    methods that delegate to _emit() / _write_stage()
  - All existing code unchanged — this is purely additive

Simplified architecture:
  - call_llm() calls infra.llm.generate() directly (2 hops, not 5)
  - Cost recorded immediately after each call via cost_tracker
  - Event emission is fire-and-forget via _emit()
  - Stage records written via _write_stage()
  - No dynamic tenacity — retry logic is explicit in call_llm()

Agents override run(state: dict) -> dict. That's the only contract.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

log = logging.getLogger("pmw.agent")


# ── Enums ─────────────────────────────────────────────────────────────

class ModelProvider(str, Enum):
    ANTHROPIC   = "anthropic"
    OPENAI      = "openai"
    HUGGINGFACE = "huggingface"
    DEEPSEEK    = "deepseek"


class AgentStatus(str, Enum):
    PENDING           = "pending"
    RUNNING           = "running"
    SUCCESS           = "success"
    FAILED            = "failed"
    WAITING_FOR_HUMAN = "awaiting_restart"


class EventType(str, Enum):
    """Event type constants used by stage agents when calling _emit_event()."""
    STAGE_STARTED  = "stage.started"
    STAGE_COMPLETE = "stage.complete"
    STAGE_FAILED   = "stage.failed"
    STAGE_RETRY    = "stage.retry"
    RUN_STARTED    = "run.started"
    RUN_COMPLETE   = "run.complete"
    RUN_FAILED     = "run.failed"


# ── Config ────────────────────────────────────────────────────────────

@dataclass
class ModelConfig:
    provider:    ModelProvider
    model_id:    str
    temperature: float = 0.2
    max_tokens:  int   = 4096


@dataclass
class FailureConfig:
    """
    Configuration for how a stage handles failure.
    Used by stage agents in __init__ but not consumed by BaseAgent directly.
    Stored as self.failure_config for stage-level failure handling.
    """
    failure_message:    str  = "Stage failed."
    human_in_the_loop:  bool = False
    max_retries:        int  = 2


# ── Result ────────────────────────────────────────────────────────────

@dataclass
class LLMResult:
    """What call_llm() returns. Flat, no nesting."""
    text:          str
    input_tokens:  int
    output_tokens: int
    cost_usd:      float
    model:         str
    attempts:      int = 1


# ── Base Agent ────────────────────────────────────────────────────────

class BaseAgent(ABC):
    """
    Abstract base for all pipeline agents.

    Every agent implements run(state: dict) -> dict.
    LLM agents call self.call_llm() inside run().
    Non-LLM agents simply don't — no separate class needed.

    LLM call path (2 hops):
      call_llm() → infra.llm.generate() + cost_tracker.record_usage()

    Override MAX_RETRIES to change attempt ceiling per subclass.
    """

    MAX_RETRIES: int = 2  # 3 total attempts

    def __init__(
        self,
        agent_name:     str,
        stage_name:     str,
        model_config:   ModelConfig   | None = None,
        failure_config: FailureConfig | None = None,
    ):
        self.agent_name     = agent_name
        self.stage_name     = stage_name
        self.model_config   = model_config
        self.failure_config = failure_config
        self.log            = logging.getLogger(f"pmw.agent.{agent_name}")

    # ── THE LLM call — flat, explicit retry ───────────────────────────

    async def call_llm(
        self,
        prompt:      str,
        run_id:      int,
        temperature: float | None = None,
        system_prompt: str | None = None,
        attempt:     int | None = None,   # accepted but ignored (compat)
    ) -> LLMResult:
        """
        Call LLM with retry. Returns LLMResult on success.
        Raises on exhaustion (caller handles failure in run()).

        Call path:
          1. infra.llm.generate()       — the actual API call
          2. cost_tracker.record_usage() — writes to llm_call_logs

        That's it. No service layer in between.
        """
        if not self.model_config:
            raise RuntimeError(f"[{self.agent_name}] call_llm() requires model_config")

        from infrastructure import get_infrastructure
        from services.cost_tracking_service import CostTrackingService

        infra = get_infrastructure()
        tracker = CostTrackingService()
        temp = temperature if temperature is not None else self.model_config.temperature

        last_error = None
        total_cost = 0.0
        total_in = 0
        total_out = 0

        for att in range(1, self.MAX_RETRIES + 2):  # +2 because range is exclusive
            try:
                response = await infra.llm.generate(
                    provider    = self.model_config.provider.value,
                    model       = self.model_config.model_id,
                    prompt      = prompt,
                    temperature = temp,
                    max_tokens  = self.model_config.max_tokens,
                    system_prompt = system_prompt,
                )

                # Record cost immediately
                cost = await tracker.record_usage(
                    run_id       = run_id,
                    stage_name   = self.stage_name,
                    attempt      = att,
                    provider     = self.model_config.provider.value,
                    model        = self.model_config.model_id,
                    input_tokens = response.input_tokens,
                    output_tokens = response.output_tokens,
                )

                total_cost += cost
                total_in += response.input_tokens
                total_out += response.output_tokens

                # Validate output (subclass can override to parse JSON, etc.)
                validated = self.validate_output(response.text)

                return LLMResult(
                    text          = validated if isinstance(validated, str) else json.dumps(validated),
                    input_tokens  = total_in,
                    output_tokens = total_out,
                    cost_usd      = total_cost,
                    model         = self.model_config.model_id,
                    attempts      = att,
                )

            except ValueError as ve:
                # Validation error — retry with same prompt
                last_error = ve
                self.log.warning(
                    f"Validation failed (attempt {att}): {ve}",
                    extra={"run_id": run_id},
                )
                if att > self.MAX_RETRIES:
                    raise

            except Exception as exc:
                last_error = exc
                self.log.warning(
                    f"LLM call failed (attempt {att}): {exc}",
                    extra={"run_id": run_id},
                )
                if att > self.MAX_RETRIES:
                    raise

                # Brief backoff before retry
                import asyncio
                await asyncio.sleep(min(2 ** att, 10))

        # Should not reach here, but just in case
        raise last_error or RuntimeError("call_llm exhausted retries")

    # ── Output validation — override in subclasses ────────────────────

    def validate_output(self, raw_output: str) -> Any:
        """
        Parse and validate raw LLM output.
        Raise ValueError to trigger a retry.
        Default: return raw string unchanged.
        """
        return raw_output

    # ── Event + stage record helpers (fire-and-forget) ────────────────

    async def _emit(self, event_type: str, run_id: int, payload: dict) -> None:
        """Publish event to Redis + vault. Never raises."""
        try:
            from services.event_service import EventService
            await EventService().emit(
                event_type = event_type,
                run_id     = run_id,
                agent_name = self.agent_name,
                stage_name = self.stage_name,
                payload    = payload,
            )
        except Exception as exc:
            self.log.debug(f"Event emission failed: {exc}")

    async def _emit_event(self, event_type, run_id: int, payload: dict) -> None:
        """
        Compatibility wrapper — stage agents call _emit_event(EventType.X, ...).
        Delegates to _emit() with the string value.
        """
        evt = event_type.value if isinstance(event_type, Enum) else str(event_type)
        await self._emit(evt, run_id, payload)

    async def _write_stage(
        self,
        run_id:  int,
        status:  str,
        attempt: int = 1,
        *,
        score:     float | None = None,
        passed:    bool  | None = None,
        output:    dict  | None = None,
        feedback:  dict  | None = None,
        in_tok:    int          = 0,
        out_tok:   int          = 0,
        cost_usd:  float        = 0.0,
        error:     str   | None = None,
        topic_wp_id: int | None = None,
    ) -> None:
        """Write/upsert workflow_stages row. Never raises."""
        try:
            from services.event_service import EventService
            await EventService().write_stage_record(
                run_id           = run_id,
                stage_name       = self.stage_name,
                status           = status,
                attempt          = attempt,
                model_used       = self.model_config.model_id if self.model_config else None,
                score            = score,
                passed_threshold = passed,
                output           = output,
                judge_feedback   = feedback,
                input_tokens     = in_tok,
                output_tokens    = out_tok,
                cost_usd         = cost_usd,
                error            = error,
            )
        except Exception as exc:
            self.log.debug(f"Stage record write failed: {exc}")

    async def _write_stage_record(
        self,
        run_id: int,
        status: str = "running",
        attempt: int = 1,
        *,
        passed_threshold: bool | None = None,
        score: float | None = None,
        output: dict | None = None,
        judge_feedback: dict | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        error: str | None = None,
        prompt_hash: str | None = None,
        **kwargs,
    ) -> None:
        """
        Compatibility wrapper — stage agents call _write_stage_record().
        Delegates to _write_stage() with mapped parameter names.
        """
        await self._write_stage(
            run_id,
            status,
            attempt,
            score=score,
            passed=passed_threshold,
            output=output,
            feedback=judge_feedback,
            in_tok=input_tokens,
            out_tok=output_tokens,
            cost_usd=cost_usd,
            error=error,
        )

    async def _handle_failure(self, run_id: int, error_msg: str) -> Any:
        """
        Compatibility wrapper — stage agents call _handle_failure().
        Writes a failed stage record and returns a simple result object.
        """
        await self._write_stage(run_id, "failed", error=error_msg)

        # Return a simple namespace-like object with .meta for arc_coherence compat
        class _FailureResult:
            def __init__(self, fc):
                self.meta = {
                    "human_in_the_loop": fc.human_in_the_loop if fc else False,
                    "failure_message": fc.failure_message if fc else error_msg,
                }
        return _FailureResult(self.failure_config)

    # ── The only abstract method ──────────────────────────────────────

    @abstractmethod
    async def run(self, state: dict) -> dict:
        """
        LangGraph node entry point.
        Accepts state dict, returns dict of state updates.
        """


# ── JSON output mixin ─────────────────────────────────────────────────

class JSONOutputMixin:
    """
    Mixin for agents whose LLM always returns JSON.
    Strips markdown fences and parses. Raises ValueError on failure → retry.
    """

    def validate_output(self, raw_output: str) -> dict:
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"LLM did not return valid JSON: {exc}\n"
                f"Raw (first 300): {raw_output[:300]}"
            )