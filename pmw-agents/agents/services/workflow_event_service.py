"""
WorkflowEventService — unified event emission for all workflow activity.

Replaces the inline _emit_event + _append_vault_event combo in BaseAgent.
Also used directly by graphs and the orchestrator for workflow-level events.

Usage:
    from agents.services.workflow_event_service import WorkflowEventService
    svc = WorkflowEventService()
    await svc.emit(run_id=42, event_type="stage.started", source="agent",
                   stage_name="stage1.brief_locker", agent_name="BriefLocker",
                   payload={"attempt": 1})
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger("pmw.workflow_event_service")


class WorkflowEventService:
    """
    Single point of truth for all workflow events.

    On every emit():
      1. Writes a row to workflow_logs  (operational, queryable)
      2. Publishes to Redis pmw:events  (real-time dashboard)
      3. Appends to vault_events        (immutable audit chain)
      4. Optionally updates workflow_runs.current_stage
    """

    # ── Redis ──────────────────────────────────────────────────────────────

    @staticmethod
    def _get_redis():
        try:
            import redis.asyncio as aioredis
            return aioredis.from_url(
                os.environ.get("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True,
            )
        except ImportError:
            raise ImportError("pip install redis[asyncio]")

    # ── DB pool ────────────────────────────────────────────────────────────

    _pool = None

    @classmethod
    async def _get_pool(cls):
        if cls._pool is None:
            import asyncpg
            cls._pool = await asyncpg.create_pool(
                os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://"),
                min_size=1,
                max_size=5,
            )
        return cls._pool

    # ── Main method ────────────────────────────────────────────────────────

    async def emit(
        self,
        *,
        run_id: int | None,
        event_type: str,
        source: str,
        payload: dict[str, Any] | None = None,
        agent_name: str | None = None,
        stage_name: str | None = None,
        level: str = "INFO",
        update_current_stage: bool = False,
    ) -> None:
        """
        Emit a workflow event to all three destinations.
        Never raises — event failure must never block the pipeline.
        """
        payload = payload or {}
        ts = datetime.now(timezone.utc).isoformat()

        event = {
            "event_type": event_type,
            "run_id": run_id,
            "agent": agent_name,
            "stage": stage_name,
            "source": source,
            "ts": ts,
            **payload,
        }

        message = payload.get("message", event_type)

        # 1. workflow_logs DB write
        await self._write_log(
            run_id=run_id,
            level=level,
            source=source,
            agent_name=agent_name,
            stage_name=stage_name,
            message=message,
            payload=payload,
        )

        # 2. Redis publish
        await self._publish_redis(event)

        # 3. vault_events append
        if run_id is not None:
            await self._append_vault(run_id, event_type, event)

        # 4. Update current_stage on workflow_runs
        if update_current_stage and run_id is not None and stage_name:
            await self._update_current_stage(run_id, stage_name)

    # ── Private helpers ────────────────────────────────────────────────────

    async def _write_log(self, run_id, level, source, agent_name, stage_name, message, payload):
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO workflow_logs
                        (run_id, level, source, agent_name, stage_name, message, payload)
                    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
                    """,
                    run_id, level, source, agent_name, stage_name,
                    message, json.dumps(payload),
                )
        except Exception as exc:
            log.warning(f"workflow_logs write failed: {exc}")

    async def _publish_redis(self, event: dict):
        try:
            redis = self._get_redis()
            await redis.publish("pmw:events", json.dumps(event))
        except Exception as exc:
            log.warning(f"Redis publish failed: {exc}")

    async def _append_vault(self, run_id: int, event_type: str, payload: dict):
        try:
            pool = await self._get_pool()
            payload_str = json.dumps(payload, sort_keys=True)
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
                        (event_type, run_id, stage_name, payload, payload_hash, previous_hash)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    event_type,
                    run_id,
                    payload.get("stage"),
                    json.dumps(payload),
                    payload_hash,
                    previous_hash,
                )
        except Exception as exc:
            log.warning(f"vault_events write failed: {exc}")

    async def _update_current_stage(self, run_id: int, stage_name: str):
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE workflow_runs SET current_stage = $1 WHERE id = $2",
                    stage_name, run_id,
                )
        except Exception as exc:
            log.warning(f"workflow_runs current_stage update failed: {exc}")


# Module-level singleton
_event_service: WorkflowEventService | None = None


def get_event_service() -> WorkflowEventService:
    global _event_service
    if _event_service is None:
        _event_service = WorkflowEventService()
    return _event_service