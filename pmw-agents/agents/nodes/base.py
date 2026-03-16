"""
PMW Content Pipeline — Base Agent
==================================

One function to call the LLM: call_llm().
Tenacity retry is applied dynamically so each subclass's MAX_RETRIES is respected.
Agents override run() and call it if they need it.
No separate NonLLMAgent class — if your run() doesn't call call_llm(), that's fine.

C1 Fix: run() now accepts (self, state: dict) -> dict to match LangGraph's
node calling convention. Nodes extract run_id from state["run_id"] internally.
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
from typing import Any, Callable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    RetryError,
)

from services.llm_service import LLMTimeoutError, LLMRateLimitError, LLMProviderError


# ---------------------------------------------------------------------------
# Structured logger
# ---------------------------------------------------------------------------

class StructuredLogger:
    def __init__(self, agent_name: str):
        self._logger    = logging.getLogger(f"pmw.agent.{agent_name}")
        self.agent_name = agent_name

    def _emit(self, level: str, message: str, run_id: int | None = None, **kwargs):
        record = {
            "ts":      datetime.now(timezone.utc).isoformat(),
            "level":   level,
            "agent":   self.agent_name,
            "message": message,
            "run_id":  run_id,
            **kwargs,
        }
        record = {k: v for k, v in record.items() if v is not None}
        getattr(self._logger, level.lower())(json.dumps(record))

    def info   (self, msg, run_id=None, **kw): self._emit("INFO",    msg, run_id, **kw)
    def warning(self, msg, run_id=None, **kw): self._emit("WARNING", msg, run_id, **kw)
    def error  (self, msg, run_id=None, **kw): self._emit("ERROR",   msg, run_id, **kw)
    def debug  (self, msg, run_id=None, **kw): self._emit("DEBUG",   msg, run_id, **kw)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

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
    STAGE_STARTED          = "stage.started"
    STAGE_COMPLETE         = "stage.complete"
    STAGE_RETRY            = "stage.retry"
    STAGE_AWAITING_RESTART = "stage.awaiting_restart"
    RUN_COMPLETE           = "run.complete"
    RUN_FAILED             = "run.failed"
    COST_UPDATE            = "cost.update"
    MEDIA_GENERATED        = "media.generated"
    MEDIA_WARNING          = "media.warning"
    INTERVENTION_APPLIED   = "intervention.applied"


# ---------------------------------------------------------------------------
# Config dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    """Provider + model settings. Only needed when call_llm() will be used."""
    provider:    ModelProvider
    model_id:    str
    temperature: float = 0.2
    max_tokens:  int   = 4096
    extra_params: dict = field(default_factory=dict)
    # Fallback costs — used by CostTrackingService only if DB price lookup fails
    cost_per_1k_input_tokens:  float = 0.0
    cost_per_1k_output_tokens: float = 0.0


@dataclass
class FailureConfig:
    """
    Defines behaviour when all retries are exhausted.

    human_in_the_loop:   True  → WAITING_FOR_HUMAN + stage.awaiting_restart
                         False → FAILED + run.failed
    on_failure_callback: Optional callable for alerting (Slack, PagerDuty).
    """
    failure_message:     str                               = "Agent failed after maximum retries."
    human_in_the_loop:   bool                              = False
    on_failure_callback: Callable[[AgentResult], None] | None = None


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    status:         AgentStatus
    output:         Any
    raw_llm_output: str | None = None
    attempts:       int        = 0
    error:          str | None = None
    input_tokens:   int        = 0
    output_tokens:  int        = 0
    cost_usd:       float      = 0.0
    model_used:     str | None = None
    meta:           dict       = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Base Agent
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    Abstract base for all PMW pipeline agents.

    Every agent overrides run(state). LLM agents call self.call_llm() inside run().
    Non-LLM agents simply don't — no separate class needed.

    C1 Fix: run() now accepts a single state dict (LangGraph convention).
    Nodes extract run_id via state["run_id"] internally.
    run() returns a dict of state updates (not AgentResult).

    Override MAX_RETRIES on the subclass to change the attempt ceiling:

        class KeywordResearchAgent(JSONOutputMixin, BaseAgent):
            MAX_RETRIES = 3   # 4 total attempts

        class TopicLoaderAgent(BaseAgent):
            # No MAX_RETRIES override needed — doesn't call call_llm()
            async def run(self, state):
                ...
    """

    # Override per subclass to change total attempt count.
    MAX_RETRIES: int = 2  # default: 3 total attempts (1 + 2 retries)

    def __init__(
        self,
        *,
        agent_name:      str,
        stage_name:      str,
        model_config:    ModelConfig   | None = None,
        failure_config:  FailureConfig | None = None,
        prompt_template: str           | None = None,
    ):
        self.agent_name      = agent_name
        self.stage_name      = stage_name
        self.model_config    = model_config
        self.failure_config  = failure_config or FailureConfig()
        self.prompt_template = prompt_template

        self.log = StructuredLogger(agent_name)

        # LangSmith tracer — only initialised if model_config is provided
        self._tracer = self._init_tracer() if model_config else None

        self.log.info(
            "Agent initialised",
            provider = model_config.provider.value if model_config else "none",
            model    = model_config.model_id       if model_config else "none",
        )

    # ------------------------------------------------------------------
    # LangSmith tracer
    # ------------------------------------------------------------------

    def _init_tracer(self):
        if os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() != "true":
            return None
        try:
            from langsmith import Client
            return Client()
        except ImportError:
            self.log.warning("LangSmith not installed — tracing disabled")
            return None

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------

    async def _emit_event(self, event_type: EventType, run_id: int, payload: dict) -> None:
        from services import services
        await services.events.emit(
            event_type = event_type.value,
            run_id     = run_id,
            agent_name = self.agent_name,
            stage_name = self.stage_name,
            payload    = payload,
        )

    async def _write_stage_record(
        self,
        run_id:           int,
        status:           str,
        attempt:          int,
        score:            float | None = None,
        passed_threshold: bool  | None = None,
        output:           dict  | None = None,
        judge_feedback:   dict  | None = None,
        prompt_hash:      str   | None = None,
        input_tokens:     int          = 0,
        output_tokens:    int          = 0,
        cost_usd:         float        = 0.0,
        error:            str   | None = None,
    ) -> None:
        from services import services
        await services.events.write_stage_record(
            run_id           = run_id,
            stage_name       = self.stage_name,
            status           = status,
            attempt          = attempt,
            model_used       = self.model_config.model_id if self.model_config else None,
            score            = score,
            passed_threshold = passed_threshold,
            output           = output,
            judge_feedback   = judge_feedback,
            prompt_hash      = prompt_hash,
            input_tokens     = input_tokens,
            output_tokens    = output_tokens,
            cost_usd         = cost_usd,
            error            = error,
        )

    # ------------------------------------------------------------------
    # THE LLM call — tenacity applied dynamically so MAX_RETRIES works
    # ------------------------------------------------------------------

    async def call_llm(
        self,
        prompt:      str,
        run_id:      int,
        attempt:     int = 1,
        temperature: float | None = None,
    ) -> AgentResult:
        """
        Call the LLM, record cost, validate output.

        Tenacity retry is built fresh on every call using self.MAX_RETRIES,
        so subclass overrides always take effect. The decorator is NOT on
        the method signature — it wraps an inner function instead.

        Args:
            prompt:      Full prompt string.
            run_id:      workflow_runs.id — for cost attribution and events.
            attempt:     Current attempt number (1-indexed). Pass the same
                         value on every call — tenacity manages the count.
            temperature: Override temperature. Defaults to model_config.temperature.

        Returns:
            AgentResult with status=SUCCESS, output=validated, tokens, cost.

        Raises (on exhaustion, reraise=True):
            LLMTimeoutError / LLMRateLimitError / LLMProviderError / ValueError
            Catch these in run() and pass to _handle_failure().
        """
        if self.model_config is None:
            raise RuntimeError(
                f"[{self.agent_name}] call_llm() requires model_config — "
                "pass it to __init__ or don't call call_llm() in this agent."
            )

        from services import services

        temp = temperature if temperature is not None else self.model_config.temperature

        # ── Build tenacity decorator dynamically from self.MAX_RETRIES ──
        @retry(
            stop    = stop_after_attempt(self.MAX_RETRIES + 1),
            wait    = wait_exponential(multiplier=1, min=2, max=10),
            retry   = retry_if_exception_type((
                LLMTimeoutError,
                LLMRateLimitError,
                LLMProviderError,
                ValueError,          # raised by validate_output() on bad LLM output
            )),
            reraise = True,
        )
        async def _attempt() -> AgentResult:
            raw, in_tok, out_tok, cost_usd = await services.llm.generate(
                model_config = self.model_config,
                prompt       = prompt,
                run_id       = run_id,
                stage_name   = self.stage_name,
                attempt      = attempt,
                temperature  = temp,
                tracer       = self._tracer,
            )

            # Emit cost.update so dashboard shows running total
            await self._emit_event(EventType.COST_UPDATE, run_id, {
                "attempt":       attempt,
                "model":         self.model_config.model_id,
                "input_tokens":  in_tok,
                "output_tokens": out_tok,
                "cost_usd":      cost_usd,
            })

            self.log.debug(
                "LLM response received",
                run_id   = run_id,
                attempt  = attempt,
                in_tok   = in_tok,
                out_tok  = out_tok,
                cost_usd = cost_usd,
                preview  = raw[:120].replace("\n", " "),
            )

            # validate_output() raising ValueError → tenacity retries
            validated = self.validate_output(raw)

            return AgentResult(
                status         = AgentStatus.SUCCESS,
                output         = validated,
                raw_llm_output = raw,
                attempts       = attempt,
                input_tokens   = in_tok,
                output_tokens  = out_tok,
                cost_usd       = cost_usd,
                model_used     = self.model_config.model_id,
            )

        return await _attempt()

    # ------------------------------------------------------------------
    # Failure handler — call from run() when call_llm() raises on exhaustion
    # ------------------------------------------------------------------

    async def _handle_failure(
        self,
        run_id:       int,
        error:        str,
        total_cost:   float        = 0.0,
        in_tok:       int          = 0,
        out_tok:      int          = 0,
        raw_output:   str | None   = None,
        prompt_hash:  str | None   = None,
    ) -> AgentResult:
        """
        Route to HITL or hard failure based on FailureConfig.
        Call this in run() when call_llm() raises after exhausting retries.
        """
        total_attempts = self.MAX_RETRIES + 1
        final_message  = f"{self.failure_config.failure_message} | {error}"

        if self.failure_config.human_in_the_loop:
            status     = AgentStatus.WAITING_FOR_HUMAN
            event_type = EventType.STAGE_AWAITING_RESTART
            db_status  = "awaiting_restart"
            self.log.warning(
                "Stage awaiting human restart",
                run_id   = run_id,
                attempts = total_attempts,
                error    = final_message,
            )
        else:
            status     = AgentStatus.FAILED
            event_type = EventType.RUN_FAILED
            db_status  = "failed"
            self.log.error(
                "Stage failed — pipeline halted",
                run_id   = run_id,
                attempts = total_attempts,
                error    = final_message,
            )

        await self._emit_event(event_type, run_id, {
            "attempts":       total_attempts,
            "final_error":    error,
            "judge_feedback": {"message": final_message},
            "cost_usd":       total_cost,
        })
        await self._write_stage_record(
            run_id           = run_id,
            status           = db_status,
            attempt          = total_attempts,
            passed_threshold = False,
            error            = final_message,
            input_tokens     = in_tok,
            output_tokens    = out_tok,
            cost_usd         = total_cost,
            prompt_hash      = prompt_hash,
        )

        result = AgentResult(
            status         = status,
            output         = None,
            raw_llm_output = raw_output,
            attempts       = total_attempts,
            error          = final_message,
            input_tokens   = in_tok,
            output_tokens  = out_tok,
            cost_usd       = total_cost,
            model_used     = self.model_config.model_id if self.model_config else None,
            meta           = {"human_in_the_loop": self.failure_config.human_in_the_loop},
        )

        if self.failure_config.on_failure_callback:
            try:
                self.failure_config.on_failure_callback(result)
            except Exception as cb_exc:
                self.log.warning("Failure callback raised", run_id=run_id, error=str(cb_exc))

        return result

    # ------------------------------------------------------------------
    # Hooks — override in subclasses as needed
    # ------------------------------------------------------------------

    def build_prompt(self, input_data: Any) -> str:
        """Build the prompt string. Override to fill {{PLACEHOLDER}} tokens."""
        if self.prompt_template is None:
            raise NotImplementedError(
                f"[{self.agent_name}] Override build_prompt() or set prompt_template"
            )
        return self.prompt_template

    def validate_output(self, raw_output: str) -> Any:
        """
        Parse and validate raw LLM output.
        Raise ValueError to trigger a tenacity retry.
        Default: return the raw string unchanged.
        """
        return raw_output

    def preprocess(self, input_data: Any) -> Any:
        return input_data

    def postprocess(self, result: AgentResult) -> AgentResult:
        return result

    # ------------------------------------------------------------------
    # The only abstract method — every agent implements this
    # ------------------------------------------------------------------

    @abstractmethod
    async def run(self, state: dict) -> dict:
        """
        LangGraph node entry point.

        Accepts the full LangGraph state dict.
        Returns a dict of state field updates (LangGraph merges these into state).

        Extract run_id internally:
            run_id = state["run_id"]

        LLM agent pattern:
            async def run(self, state):
                run_id = state["run_id"]
                topic = state.get("selected_topic") or {}

                await self._emit_event(EventType.STAGE_STARTED, run_id, {})
                await self._write_stage_record(run_id, status="running", attempt=1)

                prompt = PromptRegistry.render("template_name", {...})
                try:
                    result = await self.call_llm(prompt, run_id, attempt=1)
                except (LLMTimeoutError, ...) as exc:
                    return await self._handle_failure(run_id, str(exc))

                return {"my_output": result.output, "current_stage": "my.stage"}

        Non-LLM agent pattern:
            async def run(self, state):
                run_id = state["run_id"]
                await self._emit_event(EventType.STAGE_STARTED, run_id, {})
                data = await services.some_service.do_work()
                return {"my_data": data, "current_stage": "my.stage"}
        """


# ---------------------------------------------------------------------------
# JSON output mixin
# ---------------------------------------------------------------------------

class JSONOutputMixin:
    """
    Mixin for agents whose LLM always returns JSON.
    Strips markdown fences and parses. Raises ValueError on failure → retry.

    Usage:
        class KeywordResearchAgent(JSONOutputMixin, BaseAgent):
            MAX_RETRIES = 3

            def validate_output(self, raw):
                data = super().validate_output(raw)       # strips fences + parses
                if data.get("confidence", 0) < 0.75:
                    raise ValueError(f"confidence {data['confidence']} below threshold")
                return data
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
                f"LLM did not return valid JSON: {exc}\n\nRaw (first 300):\n{raw_output[:300]}"
            )