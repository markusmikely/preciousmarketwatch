"""
PMW Content Pipeline — Base Agent (v2.1 + model config fix)

ModelConfig and ModelProvider now live in config.models (canonical source).
Re-exported here for backward compat so existing agents don't break.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ── Canonical model definitions live in config.models ─────────────────
# Re-export so agents can still do: from nodes.base import ModelConfig, ModelProvider
from config.models import ModelConfig, ModelProvider

log = logging.getLogger("pmw.agent")


# ── Enums ─────────────────────────────────────────────────────────────

class AgentStatus(str, Enum):
    PENDING           = "pending"
    RUNNING           = "running"
    SUCCESS           = "success"
    FAILED            = "failed"
    WAITING_FOR_HUMAN = "awaiting_restart"


class EventType(str, Enum):
    STAGE_STARTED  = "stage.started"
    STAGE_COMPLETE = "stage.complete"
    STAGE_FAILED   = "stage.failed"
    STAGE_RETRY    = "stage.retry"
    RUN_STARTED    = "run.started"
    RUN_COMPLETE   = "run.complete"
    RUN_FAILED     = "run.failed"


# ── Config ────────────────────────────────────────────────────────────

@dataclass
class FailureConfig:
    failure_message:    str  = "Stage failed."
    human_in_the_loop:  bool = False
    max_retries:        int  = 2


# ── Result ────────────────────────────────────────────────────────────

@dataclass
class LLMResult:
    text:          str
    input_tokens:  int
    output_tokens: int
    cost_usd:      float
    model:         str
    attempts:      int = 1


# ── Base Agent ────────────────────────────────────────────────────────

class BaseAgent(ABC):
    MAX_RETRIES: int = 2

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

    async def call_llm(
        self,
        prompt:        str,
        run_id:        int,
        temperature:   float | None = None,
        system_prompt: str | None = None,
        attempt:       int | None = None,
    ) -> LLMResult:
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

        for att in range(1, self.MAX_RETRIES + 2):
            try:
                response = await infra.llm.generate(
                    provider      = self.model_config.provider.value,
                    model         = self.model_config.model_id,
                    prompt        = prompt,
                    temperature   = temp,
                    max_tokens    = self.model_config.max_tokens,
                    system_prompt = system_prompt,
                )

                cost = await tracker.record_usage(
                    run_id        = run_id,
                    stage_name    = self.stage_name,
                    attempt       = att,
                    provider      = self.model_config.provider.value,
                    model         = self.model_config.model_id,
                    input_tokens  = response.input_tokens,
                    output_tokens = response.output_tokens,
                )

                total_cost += cost
                total_in += response.input_tokens
                total_out += response.output_tokens

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
                last_error = ve
                self.log.warning(f"Validation failed (attempt {att}): {ve}")
                if att > self.MAX_RETRIES:
                    raise

            except Exception as exc:
                last_error = exc
                self.log.warning(f"LLM call failed (attempt {att}): {exc}")
                if att > self.MAX_RETRIES:
                    raise
                import asyncio
                await asyncio.sleep(min(2 ** att, 10))

        raise last_error or RuntimeError("call_llm exhausted retries")

    def validate_output(self, raw_output: str) -> Any:
        return raw_output

    # ── Event + stage record helpers ──────────────────────────────────

    async def _emit(self, event_type: str, run_id: int, payload: dict) -> None:
        try:
            from services.event_service import EventService
            await EventService().emit(
                event_type=event_type, run_id=run_id,
                agent_name=self.agent_name, stage_name=self.stage_name,
                payload=payload,
            )
        except Exception as exc:
            self.log.debug(f"Event emission failed: {exc}")

    async def _emit_event(self, event_type, run_id: int, payload: dict) -> None:
        evt = event_type.value if isinstance(event_type, Enum) else str(event_type)
        await self._emit(evt, run_id, payload)

    async def _write_stage(
        self, run_id: int, status: str, attempt: int = 1, *,
        score: float | None = None, passed: bool | None = None,
        output: dict | None = None, feedback: dict | None = None,
        in_tok: int = 0, out_tok: int = 0, cost_usd: float = 0.0,
        error: str | None = None, topic_wp_id: int | None = None,
    ) -> None:
        try:
            from services.event_service import EventService
            await EventService().write_stage_record(
                run_id=run_id, stage_name=self.stage_name, status=status,
                attempt=attempt,
                model_used=self.model_config.model_id if self.model_config else None,
                score=score, passed_threshold=passed, output=output,
                judge_feedback=feedback, input_tokens=in_tok,
                output_tokens=out_tok, cost_usd=cost_usd, error=error,
            )
        except Exception as exc:
            self.log.debug(f"Stage record write failed: {exc}")

    async def _write_stage_record(
        self, run_id: int, status: str = "running", attempt: int = 1, *,
        passed_threshold: bool | None = None, score: float | None = None,
        output: dict | None = None, judge_feedback: dict | None = None,
        input_tokens: int = 0, output_tokens: int = 0,
        cost_usd: float = 0.0, error: str | None = None,
        prompt_hash: str | None = None, **kwargs,
    ) -> None:
        await self._write_stage(
            run_id, status, attempt, score=score, passed=passed_threshold,
            output=output, feedback=judge_feedback,
            in_tok=input_tokens, out_tok=output_tokens,
            cost_usd=cost_usd, error=error,
        )

    async def _handle_failure(self, run_id: int, error_msg: str) -> Any:
        await self._write_stage(run_id, "failed", error=error_msg)
        class _FailureResult:
            def __init__(self, fc):
                self.meta = {
                    "human_in_the_loop": fc.human_in_the_loop if fc else False,
                    "failure_message": fc.failure_message if fc else error_msg,
                }
        return _FailureResult(self.failure_config)

    @abstractmethod
    async def run(self, state: dict) -> dict:
        """LangGraph node entry point."""


# ── JSON output mixin ─────────────────────────────────────────────────

class JSONOutputMixin:
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