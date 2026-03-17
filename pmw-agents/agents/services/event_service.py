"""
EventService — single point of truth for all pipeline event emission.

Replaces the inline _emit_event, _append_vault_event, and _write_stage_record
methods that previously lived directly in BaseAgent with direct DB/Redis access.

Responsibilities:
  - Publish structured events to Redis 'pmw:events' (Bridge WebSocket fan-out)
  - Write immutable vault_events rows (tamper-detection hash chain)
  - Upsert workflow_stages rows (per-stage cost + score audit trail)

Never raises — event/DB failures are logged but never propagate to the pipeline.
The pipeline continuing is always more important than a log entry succeeding.

Usage (from BaseAgent):
    await self._event_service.emit(
        event_type="stage.started", run_id=42,
        agent_name="keyword_research", stage_name="stage2.keyword_research",
        payload={"attempt": 1, "model": "claude-haiku-4-5"},
    )
    await self._event_service.write_stage_record(
        run_id=42, stage_name="stage2.keyword_research",
        status="complete", attempt=1, ...
    )
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger("pmw.services.event")


class EventService:
    """
    Stateless service — instantiated fresh per call from BaseAgent properties.
    All state lives in the infrastructure singletons (Redis, Postgres).
    """

    # ── Event emission ─────────────────────────────────────────────────────

    async def emit(
        self,
        event_type: str,
        run_id:     int,
        agent_name: str,
        stage_name: str,
        payload:    dict,
    ) -> None:
        """
        Publish a structured event to Redis 'pmw:events' AND write
        an immutable vault_events row.

        Both operations are attempted independently — a Redis failure does not
        prevent the vault write, and vice versa. Neither failure propagates.

        Args:
            event_type: Event string, e.g. "stage.started", "cost.update"
            run_id:     workflow_runs.id
            agent_name: Agent class name for traceability
            stage_name: Stage identifier, e.g. "stage2.keyword_research"
            payload:    Event-specific data dict
        """
        event = {
            "event_type": event_type,
            "run_id":     run_id,
            "agent":      agent_name,
            "stage":      stage_name,
            "ts":         datetime.now(timezone.utc).isoformat(),
            **payload,
        }

        await self._publish_redis(run_id, event_type, event)
        await self._write_vault(run_id, stage_name, event_type, event)

    async def _publish_redis(
        self, run_id: int, event_type: str, event: dict
    ) -> None:
        """Publish to 'pmw:events' Redis channel. Never raises."""
        try:
            from infrastructure import get_infrastructure
            await get_infrastructure().redis.publish(
                "pmw:events", json.dumps(event)
            )
        except Exception as exc:
            log.warning(
                "Redis publish failed — event not delivered to dashboard",
                extra={
                    "run_id":     run_id,
                    "event_type": event_type,
                    "error":      str(exc),
                },
            )

    async def _write_vault(
        self,
        run_id:     int,
        stage_name: str,
        event_type: str,
        payload:    dict,
    ) -> None:
        """
        Append an immutable row to vault_events.
        Computes SHA-256 of the payload and chains the previous row's hash
        so any tampering of historical records is detectable.
        Never raises.
        """
        try:
            from infrastructure import get_infrastructure
            pg = get_infrastructure().postgres

            payload_str  = json.dumps(payload, sort_keys=True)
            payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

            async with pg.connection() as conn:
                prev = await conn.fetchval(
                    """
                    SELECT payload_hash FROM vault_events
                    WHERE run_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    run_id,
                )
                previous_hash = prev or ("0" * 64)

                await conn.execute(
                    """
                    INSERT INTO vault_events
                        (event_type, run_id, stage_name, payload,
                         payload_hash, previous_hash)
                    VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                    """,
                    event_type,
                    run_id,
                    stage_name,
                    json.dumps(payload),
                    payload_hash,
                    previous_hash,
                )
        except Exception as exc:
            log.error(
                "vault_events write failed",
                extra={
                    "run_id":     run_id,
                    "event_type": event_type,
                    "error":      str(exc),
                },
            )

    # ── Stage record writes ────────────────────────────────────────────────

    async def write_stage_record(
        self,
        run_id:           int,
        stage_name:       str,
        status:           str,
        attempt:          int,
        model_used:       str   | None = None,
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
        UPSERT a workflow_stages row for run_id + stage_name + attempt_number.

        Called by BaseAgent at every lifecycle point:
          - status="running"          on stage start
          - status="retrying"         on each retry
          - status="complete"         on success
          - status="failed"           on final failure
          - status="awaiting_restart" on HITL halt

        completed_at is set automatically for terminal statuses.
        Never raises.
        """
        try:
            from infrastructure import get_infrastructure
            pg = get_infrastructure().postgres

            print("[EVENT:SERVICE:TESTING]", 
                run_id,
                stage_name,
                status,
                attempt,
                score,
                passed_threshold,
                json.dumps(output)         if output         else None,
                json.dumps(judge_feedback) if judge_feedback else None,
                prompt_hash,
                model_used,
                input_tokens,
                output_tokens,
                cost_usd,
                error)
            await pg.execute(
                """
                INSERT INTO workflow_stages
                    (run_id, stage_name, status, attempt_number,
                     score, passed_threshold, output_json, judge_feedback,
                     prompt_hash, model_used,
                     input_tokens, output_tokens, cost_usd, error,
                     completed_at)
                VALUES
                    ($1, $2, $3, $4,
                     $5, $6, $7::jsonb, $8::jsonb,
                     $9, $10,
                     $11, $12, $13, $14,
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
                    error            = EXCLUDED.error,
                    completed_at     = EXCLUDED.completed_at
                """,
                run_id,
                stage_name,
                status,
                attempt,
                score,
                passed_threshold,
                json.dumps(output)         if output         else None,
                json.dumps(judge_feedback) if judge_feedback else None,
                prompt_hash,
                model_used,
                input_tokens,
                output_tokens,
                cost_usd,
                error,
            )
        except Exception as exc:
            log.error(
                "workflow_stages write failed",
                extra={
                    "run_id":     run_id,
                    "stage_name": stage_name,
                    "status":     status,
                    "error":      str(exc),
                },
            )