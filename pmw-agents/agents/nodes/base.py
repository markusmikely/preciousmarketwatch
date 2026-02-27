"""
PMW Content Pipeline — Base Agent Class v2
==========================================
Full integration with:
  - Redis event bus  (Section 9b — WebSocket event catalogue)
  - Postgres vault   (Section 5a — vault_events immutable audit log)
  - workflow_stages  (Section 5a — per-stage cost + score tracking)
  - LangSmith tracing (Section 14 — LANGCHAIN_TRACING_V2)
  - Cost tracking    (Section 11b — cost per agent, per run)
  - Structured logging at every lifecycle point

Agents that don't need an LLM set requires_llm=False and override run().
All agents — LLM or not — still emit events and write stage records.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Structured logger — emits JSON lines for Railway log drain
# ---------------------------------------------------------------------------

class StructuredLogger:
    """
    Wraps standard logging to emit structured JSON lines.
    Every log entry includes: agent_name, run_id, stage, timestamp, level.
    """

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
    HUGGINGFACE = "huggingface"
    DEEPSEEK    = "deepseek"


class AgentStatus(str, Enum):
    PENDING           = "pending"
    RUNNING           = "running"
    SUCCESS           = "success"
    FAILED            = "failed"
    WAITING_FOR_HUMAN = "awaiting_restart"   # matches plan AWAITING_RESTART status


class EventType(str, Enum):
    """
    Canonical event types — must match Section 9b WebSocket event catalogue
    exactly so the Bridge WebSocket manager can route them correctly.
    """
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
    """
    Provider + model settings.

    provider:     Which SDK to initialise.
    model_id:     Provider-specific model string.
    temperature:  Default inference temperature.
    max_tokens:   Response token budget.
    extra_params: Provider-specific overrides (e.g. base_url for DeepSeek,
                  use_inference_api for HuggingFace).

    Cost reference (USD per 1k tokens, approximate Feb 2026):
        claude-opus-4-6     input $0.015  / output $0.075
        claude-sonnet-4-6   input $0.003  / output $0.015
        claude-haiku-4-5    input $0.00025/ output $0.00125
        deepseek-chat       input $0.00014/ output $0.00028
    """
    provider:     ModelProvider
    model_id:     str
    temperature:  float = 0.2
    max_tokens:   int   = 4096
    extra_params: dict  = field(default_factory=dict)

    # Per-token costs in USD — used for cost tracking (Section 11b)
    cost_per_1k_input_tokens:  float = 0.0
    cost_per_1k_output_tokens: float = 0.0


@dataclass
class RetryConfig:
    """
    Retry and temperature escalation.

    max_retries:            Additional attempts after the first.
    retry_delay_seconds:    Sleep between attempts.
    temperature_escalation: Per-attempt temperatures. Last value reused if
                            list is shorter than max_retries.
    """
    max_retries:            int         = 2
    retry_delay_seconds:    float       = 1.0
    temperature_escalation: list[float] | None = None


@dataclass
class FailureConfig:
    """
    Defines post-exhaustion behaviour.

    failure_message:     Logged and returned in AgentResult.error.
    human_in_the_loop:   If True, status → WAITING_FOR_HUMAN and a
                         stage.awaiting_restart event is emitted (plan §9b).
                         The pipeline halts at interrupt_before=["handle_failure"]
                         in LangGraph; operator restarts from the dashboard.
    on_failure_callback: Optional callable(AgentResult) for alerting
                         (Slack, PagerDuty, etc.).
    """
    failure_message:     str  = "Agent failed after maximum retries."
    human_in_the_loop:   bool = False
    on_failure_callback: Callable[[AgentResult], None] | None = None


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    """
    Normalised output from every agent run — success or failure.

    status:         Final AgentStatus.
    output:         Validated, typed output on success; None on failure.
    raw_llm_output: Last raw LLM string (stored in workflow_stages.output_json).
    attempts:       Total attempts made (including retries).
    error:          Failure reason string.
    input_tokens:   Prompt tokens consumed (sum across all attempts).
    output_tokens:  Response tokens (sum across all attempts).
    cost_usd:       Total USD cost for this agent run.
    model_used:     Model ID string for the final successful call.
    meta:           Arbitrary extra fields (e.g. human_in_the_loop flag).
    """
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
# Infrastructure clients (lazy singletons)
# ---------------------------------------------------------------------------

class _RedisClient:
    """
    Thin wrapper around redis.asyncio.
    Publishes events to the 'pmw:events' channel consumed by the
    Bridge WebSocket manager (Section 9a WS /ws/events).
    """
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            try:
                import redis.asyncio as aioredis
            except ImportError:
                raise ImportError("pip install redis[asyncio]")
            cls._instance = aioredis.from_url(
                os.environ.get("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True,
            )
        return cls._instance


class _DBPool:
    """
    Thin wrapper around asyncpg connection pool.
    Used for writing vault_events and workflow_stages (Section 5a).
    """
    _pool = None

    @classmethod
    async def get(cls):
        if cls._pool is None:
            # Run Alembic migrations before first DB connection
            if os.environ.get("DATABASE_URL"):
                try:
                    try:
                        from agents.db.run_migrations import run_migrations
                    except ImportError:
                        from ..db.run_migrations import run_migrations
                    run_migrations()
                except RuntimeError:
                    raise  # Migration failed — surface to caller
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning("Migration check (non-fatal): %s", e)
            try:
                import asyncpg
            except ImportError:
                raise ImportError("pip install asyncpg")
            cls._pool = await asyncpg.create_pool(
                dsn=os.environ.get(
                    "DATABASE_URL",
                    "postgresql://pmw:pmw@localhost:5432/pmw",
                ),
                min_size=1,
                max_size=5,
            )
        return cls._pool


# ---------------------------------------------------------------------------
# Base Agent
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    Abstract base for all PMW pipeline agents.

    Every agent — LLM-backed or not — participates in:
      - Structured JSON logging (StructuredLogger)
      - Redis event emission  (stage.started / complete / retry /
                               awaiting_restart / cost.update)
      - Postgres vault_events immutable audit trail (Section 5a)
      - workflow_stages cost + score record writes  (Section 5a)
      - LangSmith tracing when LANGCHAIN_TRACING_V2=true (Section 14)

    Subclass and implement:
        run(input_data, run_id)  — main task logic
        validate_output(raw)     — parse + validate raw LLM text; raise on fail

    Optionally override:
        build_prompt(input_data) — construct prompt string from input
        preprocess(input_data)   — transform input before run()
        postprocess(result)      — transform AgentResult after run()
    """

    def __init__(
        self,
        *,
        agent_name:      str,
        stage_name:      str,                       # maps to plan stage names
        model_config:    ModelConfig  | None = None,
        retry_config:    RetryConfig  | None = None,
        failure_config:  FailureConfig | None = None,
        prompt_template: str          | None = None,
        requires_llm:    bool                = True,
    ):
        self.agent_name      = agent_name
        self.stage_name      = stage_name
        self.model_config    = model_config
        self.retry_config    = retry_config   or RetryConfig()
        self.failure_config  = failure_config or FailureConfig()
        self.prompt_template = prompt_template
        self.requires_llm    = requires_llm

        self.log = StructuredLogger(agent_name)

        if self.requires_llm and self.model_config is None:
            raise ValueError(
                f"[{self.agent_name}] model_config required when requires_llm=True"
            )

        if self.requires_llm:
            self._llm_client = self._init_llm_client()
            self._tracer     = self._init_tracer()
        else:
            self._llm_client = None
            self._tracer     = None

        self.log.info(
            "Agent initialised",
            provider=self.model_config.provider  if self.model_config else "none",
            model   =self.model_config.model_id  if self.model_config else "none",
            requires_llm=self.requires_llm,
        )

    # ------------------------------------------------------------------
    # Client initialisation
    # ------------------------------------------------------------------

    def _init_llm_client(self) -> Any:
        provider = self.model_config.provider

        if provider == ModelProvider.ANTHROPIC:
            try:
                import anthropic
            except ImportError:
                raise ImportError("pip install anthropic")
            return anthropic.AsyncAnthropic()

        if provider == ModelProvider.HUGGINGFACE:
            use_api = self.model_config.extra_params.get("use_inference_api", False)
            if use_api:
                try:
                    from huggingface_hub import AsyncInferenceClient
                except ImportError:
                    raise ImportError("pip install huggingface-hub")
                return AsyncInferenceClient(model=self.model_config.model_id)
            else:
                try:
                    from transformers import pipeline as hf_pipeline
                except ImportError:
                    raise ImportError("pip install transformers accelerate")
                return hf_pipeline(
                    "text-generation",
                    model=self.model_config.model_id,
                    **self.model_config.extra_params,
                )

        if provider == ModelProvider.DEEPSEEK:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError("pip install openai")
            return AsyncOpenAI(
                api_key  =self.model_config.extra_params.get("api_key"),
                base_url =self.model_config.extra_params.get(
                    "base_url", "https://api.deepseek.com"
                ),
            )

        raise ValueError(f"Unknown provider: {provider}")

    def _init_tracer(self):
        """
        Initialise LangSmith client when LANGCHAIN_TRACING_V2=true.
        Returns None silently if langsmith is not installed or disabled.
        """
        if os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() != "true":
            return None
        try:
            from langsmith import Client
            return Client()
        except ImportError:
            self.log.warning(
                "LangSmith not installed — tracing disabled. pip install langsmith"
            )
            return None

    # ------------------------------------------------------------------
    # Event emission — Redis pub/sub (Section 9b)
    # ------------------------------------------------------------------

    async def _emit_event(
        self,
        event_type: EventType,
        run_id:     int,
        payload:    dict,
    ) -> None:
        """
        Publish a structured event to Redis 'pmw:events'.
        The Bridge WebSocket manager subscribes and fans out to dashboard clients.
        Also writes an immutable vault_events record.
        Never raises — event failure must not block the pipeline.
        """
        event = {
            "event_type": event_type.value,
            "run_id":     run_id,
            "agent":      self.agent_name,
            "stage":      self.stage_name,
            "ts":         datetime.now(timezone.utc).isoformat(),
            **payload,
        }

        # ── Redis publish ──────────────────────────────────────────────
        try:
            redis = _RedisClient.get()
            await redis.publish("pmw:events", json.dumps(event))
        except Exception as exc:
            self.log.warning(
                "Redis publish failed — event not delivered to dashboard",
                run_id=run_id,
                event_type=event_type.value,
                error=str(exc),
            )

        # ── Immutable vault append ─────────────────────────────────────
        await self._append_vault_event(run_id, event_type.value, event)

    async def _append_vault_event(
        self,
        run_id:     int,
        event_type: str,
        payload:    dict,
    ) -> None:
        """
        Append an immutable record to vault_events (Section 5a).
        Computes payload_hash and chains previous_hash for tamper detection.
        The DB app user must NOT have UPDATE/DELETE on vault_events
        (enforced by nightly compliance test §17c).
        """
        try:
            pool         = await _DBPool.get()
            payload_str  = json.dumps(payload, sort_keys=True)
            payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

            async with pool.acquire() as conn:
                prev = await conn.fetchval(
                    "SELECT payload_hash FROM vault_events "
                    "WHERE run_id = $1 ORDER BY created_at DESC LIMIT 1",
                    run_id,
                )
                previous_hash = prev or ("0" * 64)

                await conn.execute(
                    """
                    INSERT INTO vault_events
                        (event_type, run_id, stage_name, payload,
                         payload_hash, previous_hash)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    event_type,
                    run_id,
                    self.stage_name,
                    json.dumps(payload),
                    payload_hash,
                    previous_hash,
                )
        except Exception as exc:
            # Vault write failure must never stop the pipeline
            self.log.error(
                "Vault event write failed",
                run_id=run_id,
                event_type=event_type,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # workflow_stages record writes (Section 5a)
    # ------------------------------------------------------------------

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
        """
        Upsert a workflow_stages row for this stage + attempt.
        Called at stage start, on each retry, and on completion / failure.
        """
        try:
            pool = await _DBPool.get()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO workflow_stages
                        (run_id, stage_name, status, attempt_number,
                         score, passed_threshold, output_json, judge_feedback,
                         prompt_hash, model_used,
                         input_tokens, output_tokens, cost_usd,
                         completed_at)
                    VALUES
                        ($1, $2, $3, $4,
                         $5, $6, $7::jsonb, $8::jsonb,
                         $9, $10,
                         $11, $12, $13,
                         CASE WHEN $3 IN ('complete', 'failed', 'awaiting_restart')
                              THEN NOW() ELSE NULL END)
                    ON CONFLICT (run_id, stage_name, attempt_number)
                    DO UPDATE SET
                        status           = EXCLUDED.status,
                        score            = EXCLUDED.score,
                        passed_threshold = EXCLUDED.passed_threshold,
                        output_json      = EXCLUDED.output_json,
                        judge_feedback   = EXCLUDED.judge_feedback,
                        input_tokens     = EXCLUDED.input_tokens,
                        output_tokens    = EXCLUDED.output_tokens,
                        cost_usd         = EXCLUDED.cost_usd,
                        completed_at     = EXCLUDED.completed_at
                    """,
                    run_id,
                    self.stage_name,
                    status,
                    attempt,
                    score,
                    passed_threshold,
                    json.dumps(output)         if output         else None,
                    json.dumps(judge_feedback) if judge_feedback else None,
                    prompt_hash,
                    self.model_config.model_id if self.model_config else None,
                    input_tokens,
                    output_tokens,
                    cost_usd,
                )
        except Exception as exc:
            self.log.error(
                "workflow_stages write failed",
                run_id=run_id,
                stage=self.stage_name,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Cost calculation
    # ------------------------------------------------------------------

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Compute USD cost from token counts and model pricing config.
        Returns 0.0 if cost rates not set.
        """
        if self.model_config is None:
            return 0.0
        in_cost  = (input_tokens  / 1000) * self.model_config.cost_per_1k_input_tokens
        out_cost = (output_tokens / 1000) * self.model_config.cost_per_1k_output_tokens
        return round(in_cost + out_cost, 6)

    # ------------------------------------------------------------------
    # LLM call — normalised across providers, returns token counts
    # ------------------------------------------------------------------

    async def _call_llm(
        self,
        prompt:      str,
        temperature: float | None = None,
    ) -> tuple[str, int, int]:
        """
        Call the configured LLM asynchronously.

        Returns
        -------
        (response_text, input_tokens, output_tokens)

        Token counts are summed across retries for total cost tracking.
        """
        if not self.requires_llm:
            raise RuntimeError(
                f"[{self.agent_name}] _call_llm() called on a non-LLM agent"
            )

        temp     = temperature if temperature is not None else self.model_config.temperature
        provider = self.model_config.provider

        # ── LangSmith trace span ───────────────────────────────────────
        run_tree = None
        if self._tracer:
            try:
                from langsmith.run_trees import RunTree
                run_tree = RunTree(
                    name         = f"{self.agent_name}.llm_call",
                    run_type     = "llm",
                    inputs       = {"prompt": prompt[:500]},
                    project_name = os.environ.get("LANGCHAIN_PROJECT", "pmw"),
                )
                run_tree.post()
            except Exception:
                run_tree = None   # tracing is best-effort

        try:
            # ── Anthropic ──────────────────────────────────────────────
            if provider == ModelProvider.ANTHROPIC:
                response = await self._llm_client.messages.create(
                    model       = self.model_config.model_id,
                    max_tokens  = self.model_config.max_tokens,
                    temperature = temp,
                    messages    = [{"role": "user", "content": prompt}],
                )
                text    = response.content[0].text
                in_tok  = response.usage.input_tokens
                out_tok = response.usage.output_tokens

            # ── HuggingFace ────────────────────────────────────────────
            elif provider == ModelProvider.HUGGINGFACE:
                use_api = self.model_config.extra_params.get("use_inference_api", False)
                if use_api:
                    text = await self._llm_client.text_generation(
                        prompt,
                        max_new_tokens=self.model_config.max_tokens,
                        temperature=temp,
                    )
                else:
                    loop    = asyncio.get_event_loop()
                    outputs = await loop.run_in_executor(
                        None,
                        lambda: self._llm_client(
                            prompt,
                            max_new_tokens=self.model_config.max_tokens,
                            temperature=temp,
                            do_sample=True,
                        )
                    )
                    text = outputs[0]["generated_text"][len(prompt):]
                # HuggingFace doesn't return exact token counts — approximate
                in_tok  = len(prompt.split())
                out_tok = len(text.split())

            # ── DeepSeek (OpenAI-compatible) ───────────────────────────
            elif provider == ModelProvider.DEEPSEEK:
                response = await self._llm_client.chat.completions.create(
                    model       = self.model_config.model_id,
                    max_tokens  = self.model_config.max_tokens,
                    temperature = temp,
                    messages    = [{"role": "user", "content": prompt}],
                )
                text    = response.choices[0].message.content
                in_tok  = response.usage.prompt_tokens
                out_tok = response.usage.completion_tokens

            else:
                raise ValueError(f"Unknown provider: {provider}")

            if run_tree:
                run_tree.end(outputs={"response": text[:200]})
                run_tree.patch()

            return text, in_tok, out_tok

        except Exception as exc:
            if run_tree:
                run_tree.end(error=str(exc))
                run_tree.patch()
            raise

    # ------------------------------------------------------------------
    # Prompt building hook
    # ------------------------------------------------------------------

    def build_prompt(self, input_data: Any) -> str:
        """
        Return the final prompt string for this input.
        Default: return prompt_template unchanged.
        Override to replace {{PLACEHOLDER}} tokens.
        """
        if self.prompt_template is None:
            raise NotImplementedError(
                f"[{self.agent_name}] Override build_prompt() or set prompt_template"
            )
        return self.prompt_template

    # ------------------------------------------------------------------
    # Pre / post processing hooks
    # ------------------------------------------------------------------

    def preprocess(self, input_data: Any) -> Any:
        return input_data

    def postprocess(self, result: AgentResult) -> AgentResult:
        return result

    # ------------------------------------------------------------------
    # Output validation — override in every LLM agent
    # ------------------------------------------------------------------

    def validate_output(self, raw_output: str) -> Any:
        """
        Parse and validate raw LLM text.
        Raise ValueError on failure — the retry loop will catch it.
        """
        return raw_output

    # ------------------------------------------------------------------
    # Core run method — must be implemented by every subclass
    # ------------------------------------------------------------------

    @abstractmethod
    async def run(self, input_data: Any, run_id: int) -> AgentResult:
        """
        Execute the agent task.

        run_id is required by all agents (LLM or not) for event emission
        and audit logging.

        LLM agents delegate to _run_with_retries().
        Non-LLM agents implement their logic directly, calling
        _emit_event() and _write_stage_record() at start and completion.
        """

    # ------------------------------------------------------------------
    # Retry loop — called by LLM agents from run()
    # ------------------------------------------------------------------

    async def _run_with_retries(
        self,
        prompt:         str,
        run_id:         int,
        attempt_offset: int = 0,   # non-zero when restarting after human review
    ) -> AgentResult:
        """
        LLM retry loop with full event emission, DB writes, and cost tracking.

        Lifecycle per attempt:
          1. stage.started emitted (first attempt only)
          2. LLM called → cost.update emitted
          3. validate_output()
             - Pass  → stage.complete emitted, stage record written, return
             - Fail  → stage.retry emitted, stage record written, sleep, retry
          4. Exhausted → stage.awaiting_restart or run.failed emitted
        """
        max_attempts  = self.retry_config.max_retries + 1
        total_in_tok  = 0
        total_out_tok = 0
        total_cost    = 0.0
        last_error:   str | None = None
        last_raw:     str | None = None

        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        for attempt in range(1, max_attempts + 1):
            abs_attempt = attempt_offset + attempt
            temperature = self._get_temperature(attempt)

            # ── stage.started (first attempt only) ────────────────────
            if attempt == 1:
                self.log.info(
                    "Stage started",
                    run_id=run_id,
                    attempt=abs_attempt,
                    temperature=temperature,
                    model=self.model_config.model_id,
                )
                await self._emit_event(EventType.STAGE_STARTED, run_id, {
                    "attempt":     abs_attempt,
                    "temperature": temperature,
                    "model":       self.model_config.model_id,
                    "prompt_hash": prompt_hash,
                })
                await self._write_stage_record(
                    run_id=run_id, status="running",
                    attempt=abs_attempt, prompt_hash=prompt_hash,
                )

            # ── LLM call ──────────────────────────────────────────────
            try:
                raw, in_tok, out_tok = await self._call_llm(prompt, temperature)
                last_raw       = raw
                total_in_tok  += in_tok
                total_out_tok += out_tok
                attempt_cost   = self._calculate_cost(in_tok, out_tok)
                total_cost    += attempt_cost

                # cost.update → dashboard running total (Section 11b)
                await self._emit_event(EventType.COST_UPDATE, run_id, {
                    "attempt":       abs_attempt,
                    "model":         self.model_config.model_id,
                    "input_tokens":  in_tok,
                    "output_tokens": out_tok,
                    "cost_usd":      attempt_cost,
                })

                self.log.debug(
                    "LLM response received",
                    run_id=run_id,
                    attempt=abs_attempt,
                    in_tok=in_tok,
                    out_tok=out_tok,
                    cost_usd=attempt_cost,
                    preview=raw[:120].replace("\n", " "),
                )

            except Exception as exc:
                last_error = f"LLM call error: {exc}"
                self.log.error(
                    "LLM call failed",
                    run_id=run_id,
                    attempt=abs_attempt,
                    error=last_error,
                )
                if attempt < max_attempts:
                    await self._emit_event(EventType.STAGE_RETRY, run_id, {
                        "attempt":           abs_attempt,
                        "error":             last_error,
                        "next_temperature":  self._get_temperature(attempt + 1),
                    })
                    await self._write_stage_record(
                        run_id=run_id, status="retrying", attempt=abs_attempt,
                        error=last_error, input_tokens=total_in_tok,
                        output_tokens=total_out_tok, cost_usd=total_cost,
                        prompt_hash=prompt_hash,
                    )
                    await asyncio.sleep(self.retry_config.retry_delay_seconds)
                continue

            # ── Output validation ──────────────────────────────────────
            try:
                validated = self.validate_output(raw)

                self.log.info(
                    "Stage complete",
                    run_id=run_id,
                    attempt=abs_attempt,
                    total_cost_usd=total_cost,
                )
                await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                    "attempt":       abs_attempt,
                    "input_tokens":  total_in_tok,
                    "output_tokens": total_out_tok,
                    "cost_usd":      total_cost,
                })
                await self._write_stage_record(
                    run_id=run_id, status="complete", attempt=abs_attempt,
                    passed_threshold=True,
                    output=validated if isinstance(validated, dict)
                           else {"result": str(validated)},
                    input_tokens=total_in_tok, output_tokens=total_out_tok,
                    cost_usd=total_cost, prompt_hash=prompt_hash,
                )

                return AgentResult(
                    status        = AgentStatus.SUCCESS,
                    output        = validated,
                    raw_llm_output= raw,
                    attempts      = abs_attempt,
                    input_tokens  = total_in_tok,
                    output_tokens = total_out_tok,
                    cost_usd      = total_cost,
                    model_used    = self.model_config.model_id,
                )

            except Exception as exc:
                last_error = f"Validation failed: {exc}"
                self.log.warning(
                    "Validation failed — retrying",
                    run_id=run_id,
                    attempt=abs_attempt,
                    error=last_error,
                    raw_preview=raw[:200].replace("\n", " "),
                )
                if attempt < max_attempts:
                    await self._emit_event(EventType.STAGE_RETRY, run_id, {
                        "attempt":           abs_attempt,
                        "weakest_criterion": last_error,
                        "next_temperature":  self._get_temperature(attempt + 1),
                    })
                    await self._write_stage_record(
                        run_id=run_id, status="retrying", attempt=abs_attempt,
                        passed_threshold=False, error=last_error,
                        input_tokens=total_in_tok, output_tokens=total_out_tok,
                        cost_usd=total_cost, prompt_hash=prompt_hash,
                    )
                    await asyncio.sleep(self.retry_config.retry_delay_seconds)

        # ── All attempts exhausted ─────────────────────────────────────
        return await self._handle_failure(
            run_id        = run_id,
            error         = last_error,
            raw_output    = last_raw,
            attempts      = attempt_offset + max_attempts,
            total_in_tok  = total_in_tok,
            total_out_tok = total_out_tok,
            total_cost    = total_cost,
            prompt_hash   = prompt_hash,
        )

    async def _handle_failure(
        self,
        run_id:        int,
        error:         str | None,
        raw_output:    str | None,
        attempts:      int,
        total_in_tok:  int,
        total_out_tok: int,
        total_cost:    float,
        prompt_hash:   str | None = None,
    ) -> AgentResult:
        """
        Called when all retries are exhausted.
        Routes to WAITING_FOR_HUMAN (stage.awaiting_restart) or
        hard FAILED (run.failed) based on failure_config.
        """
        final_message = f"{self.failure_config.failure_message} | {error}"

        if self.failure_config.human_in_the_loop:
            status     = AgentStatus.WAITING_FOR_HUMAN
            event_type = EventType.STAGE_AWAITING_RESTART
            db_status  = "awaiting_restart"
            self.log.warning(
                "Stage awaiting human restart",
                run_id=run_id,
                attempts=attempts,
                error=final_message,
            )
        else:
            status     = AgentStatus.FAILED
            event_type = EventType.RUN_FAILED
            db_status  = "failed"
            self.log.error(
                "Stage failed — pipeline halted",
                run_id=run_id,
                attempts=attempts,
                error=final_message,
            )

        await self._emit_event(event_type, run_id, {
            "attempts":      attempts,
            "final_error":   error,
            "judge_feedback": {"message": final_message},
            "cost_usd":      total_cost,
        })
        await self._write_stage_record(
            run_id=run_id, status=db_status, attempt=attempts,
            passed_threshold=False, error=final_message,
            input_tokens=total_in_tok, output_tokens=total_out_tok,
            cost_usd=total_cost, prompt_hash=prompt_hash,
        )

        result = AgentResult(
            status        = status,
            output        = None,
            raw_llm_output= raw_output,
            attempts      = attempts,
            error         = final_message,
            input_tokens  = total_in_tok,
            output_tokens = total_out_tok,
            cost_usd      = total_cost,
            model_used    = self.model_config.model_id if self.model_config else None,
            meta          = {"human_in_the_loop": self.failure_config.human_in_the_loop},
        )

        if self.failure_config.on_failure_callback:
            try:
                self.failure_config.on_failure_callback(result)
            except Exception as cb_exc:
                self.log.warning(
                    "Failure callback raised",
                    run_id=run_id,
                    error=str(cb_exc),
                )

        return result

    def _get_temperature(self, attempt: int) -> float:
        if not self.retry_config.temperature_escalation:
            return self.model_config.temperature if self.model_config else 0.2
        escalation = self.retry_config.temperature_escalation
        return escalation[min(attempt - 1, len(escalation) - 1)]


# ---------------------------------------------------------------------------
# JSON output mixin
# ---------------------------------------------------------------------------

class JSONOutputMixin:
    """
    Mixin for agents whose LLM returns only valid JSON.

    Usage
    -----
    class MyAgent(JSONOutputMixin, BaseAgent):
        def validate_output(self, raw):
            data = super().validate_output(raw)   # strips fences + parses JSON
            assert data.get("confidence", 0) >= 0.8, "confidence below threshold"
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


# ---------------------------------------------------------------------------
# NonLLMAgent — deterministic pipeline steps
# ---------------------------------------------------------------------------

class NonLLMAgent(BaseAgent, ABC):
    """
    Base for agents that perform deterministic work without an LLM:
    price fetchers, web scrapers, schema validators, data transformers.

    Still participates fully in event emission, vault logging, and stage records.
    Subclass and implement: execute(input_data, run_id) -> Any
    """

    def __init__(
        self,
        *,
        agent_name:    str,
        stage_name:    str,
        failure_config: FailureConfig | None = None,
    ):
        super().__init__(
            agent_name    = agent_name,
            stage_name    = stage_name,
            requires_llm  = False,
            failure_config = failure_config or FailureConfig(),
        )

    @abstractmethod
    async def execute(self, input_data: Any, run_id: int) -> Any:
        """Implement deterministic logic here. Raise on failure."""

    async def run(self, input_data: Any, run_id: int) -> AgentResult:
        input_data = self.preprocess(input_data)

        self.log.info("Non-LLM stage started", run_id=run_id)
        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "agent_type": "non_llm",
        })
        await self._write_stage_record(
            run_id=run_id, status="running", attempt=1,
        )

        try:
            output = await self.execute(input_data, run_id)

            self.log.info("Non-LLM stage complete", run_id=run_id)
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "cost_usd": 0.0,
            })
            await self._write_stage_record(
                run_id=run_id, status="complete", attempt=1,
                passed_threshold=True,
                output=output if isinstance(output, dict)
                       else {"result": str(output)},
                cost_usd=0.0,
            )

            result = AgentResult(
                status   = AgentStatus.SUCCESS,
                output   = output,
                attempts = 1,
                cost_usd = 0.0,
            )
            return self.postprocess(result)

        except Exception as exc:
            return await self._handle_failure(
                run_id=run_id, error=str(exc), raw_output=None,
                attempts=1, total_in_tok=0, total_out_tok=0, total_cost=0.0,
            )


# ---------------------------------------------------------------------------
# Example: Stage 1.1 — Topic & Affiliate Parser
# Demonstrates the full LLM agent pattern with all instrumentation wired in.
# ---------------------------------------------------------------------------

PROMPT_1_1 = """\
SYSTEM:
You are a structured data extraction agent for Precious Metals Watch (PMW).
Extract specific fields from the user-provided topic and affiliate input.
Do not guess. Return null for any field you cannot extract with confidence >= 0.8.
Return only valid JSON. No preamble. No markdown fencing.

SCHEMA:
{
  "topic_raw":                   "string",
  "topic_normalised":            "string | null",
  "asset_class":                 "gold | silver | platinum | palladium | gemstones | mixed | null",
  "product_type":                "string | null",
  "geography":                   "string | null",
  "is_buy_side":                 "boolean | null",
  "affiliate_raw":               "string | null",
  "affiliate_key":               "bullionvault | royal-mint | chards | hatton-garden | other | null",
  "affiliate_product_or_action": "string | null",
  "confidence":                  "float 0.0-1.0",
  "null_fields":                 ["array of field names that returned null"]
}

RULES:
- geography defaults to "UK" only if topic clearly implies UK context.
- is_buy_side: true=buying signals, false=sell signals, null=unclear.

USER INPUT:
Topic:     {{TOPIC_INPUT}}
Affiliate: {{AFFILIATE_INPUT}}
"""


class Stage1ParserAgent(JSONOutputMixin, BaseAgent):
    """Stage 1.1 — Parses raw topic + affiliate input into a structured brief."""

    def __init__(self):
        super().__init__(
            agent_name   = "Stage1ParserAgent",
            stage_name   = "research",
            model_config = ModelConfig(
                provider                   = ModelProvider.ANTHROPIC,
                model_id                   = "claude-haiku-4-5-20251001",
                temperature                = 0.2,
                max_tokens                 = 1024,
                cost_per_1k_input_tokens   = 0.00025,
                cost_per_1k_output_tokens  = 0.00125,
            ),
            retry_config = RetryConfig(
                max_retries            = 2,
                retry_delay_seconds    = 1.0,
                temperature_escalation = [0.2, 0.4, 0.6],
            ),
            failure_config = FailureConfig(
                failure_message   = (
                    "Topic parser failed. Please provide a clearer topic and affiliate."
                ),
                human_in_the_loop = False,
            ),
            prompt_template = PROMPT_1_1,
            requires_llm    = True,
        )

    def build_prompt(self, input_data: dict) -> str:
        return self.prompt_template.replace(
            "{{TOPIC_INPUT}}",     input_data.get("topic",     "")
        ).replace(
            "{{AFFILIATE_INPUT}}", input_data.get("affiliate", "")
        )

    def validate_output(self, raw: str) -> dict:
        data = super().validate_output(raw)         # JSON parse via mixin
        conf = data.get("confidence", 0.0)
        if conf < 0.8:
            raise ValueError(f"Confidence {conf:.2f} below 0.8 threshold")
        return data

    async def run(self, input_data: dict, run_id: int) -> AgentResult:
        input_data = self.preprocess(input_data)
        prompt     = self.build_prompt(input_data)
        result     = await self._run_with_retries(prompt, run_id)
        return self.postprocess(result)


# ---------------------------------------------------------------------------
# Smoke test — run directly (no real LLM or DB required for init checks)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level  = logging.DEBUG,
        format = "%(message)s",
        stream = sys.stdout,
    )

    class _MockPriceFetcher(NonLLMAgent):
        """Minimal non-LLM agent for smoke test."""
        async def execute(self, input_data, run_id):
            await asyncio.sleep(0.01)
            return {"gold_gbp": 1850.00, "silver_gbp": 22.50}

    async def _smoke():
        print("\n── Non-LLM agent (no DB/Redis) ─────────────")
        agent  = _MockPriceFetcher(
            agent_name   = "PriceFetcher",
            stage_name   = "price_fetch",
            failure_config = FailureConfig(failure_message="Price fetch failed"),
        )
        # Patch out infrastructure for smoke test
        agent._emit_event        = lambda *a, **kw: asyncio.sleep(0)
        agent._write_stage_record = lambda *a, **kw: asyncio.sleep(0)

        result = await agent.run({"metal": "gold"}, run_id=9999)
        print(f"  status:   {result.status}")
        print(f"  output:   {result.output}")
        print(f"  cost_usd: {result.cost_usd}")

        print("\n── LLM agent init (no API call) ─────────────")
        try:
            # Patch anthropic import for environments without it
            import unittest.mock as mock
            with mock.patch.dict("sys.modules", {"anthropic": mock.MagicMock()}):
                parser = Stage1ParserAgent()
            print(f"  agent_name:   {parser.agent_name}")
            print(f"  stage_name:   {parser.stage_name}")
            print(f"  model_id:     {parser.model_config.model_id}")
            print(f"  max_retries:  {parser.retry_config.max_retries}")
            print(f"  temp_escalation: {parser.retry_config.temperature_escalation}")
            print(f"  hitl:         {parser.failure_config.human_in_the_loop}")
            print("  OK — all config validated")
        except Exception as e:
            print(f"  Init check: {e}")

        print("\nSmoke test complete.\n")

    asyncio.run(_smoke())