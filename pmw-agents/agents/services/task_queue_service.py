"""
TaskQueueService — durable task queue using Redis Streams + Postgres mirror.

Redis Streams = fast path (workers consume via XREADGROUP).
Postgres agent_task_queue = recovery path (survives Redis restart).

Usage:
    queue = TaskQueueService()
    task_id = await queue.enqueue("research_pipeline", {"run_id": 42, ...}, run_id=42)
    task    = await queue.claim_next("research_pipeline", worker_id="worker-1")
    await queue.complete(task_id)
    await queue.recover_stale()  # call on worker startup
"""
from __future__ import annotations

import json
import logging
import os
import socket
from datetime import datetime, timezone

log = logging.getLogger("pmw.task_queue_service")

STREAM_PREFIX = "pmw:tasks:"
CONSUMER_GROUP = "pmw-workers"
STALE_MINUTES = 10


class TaskQueueService:

    def __init__(self):
        self._redis = None
        self._pool = None

    # ── Infrastructure ────────────────────────────────────────────────────

    def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                os.environ.get("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True,
            )
        return self._redis

    async def _get_pool(self):
        if self._pool is None:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://"),
                min_size=1,
                max_size=5,
            )
        return self._pool

    def _stream_key(self, workflow_slug: str) -> str:
        return f"{STREAM_PREFIX}{workflow_slug}"

    # ── Public API ────────────────────────────────────────────────────────

    async def enqueue(
        self,
        workflow_slug: str,
        payload: dict,
        run_id: int | None = None,
    ) -> int:
        """
        Add a task to the queue. Returns the Postgres row id.
        """
        pool = await self._get_pool()

        # 1. Write to Postgres first (durable record)
        async with pool.acquire() as conn:
            task_id = await conn.fetchval(
                """
                INSERT INTO agent_task_queue (run_id, workflow_slug, payload, status)
                VALUES ($1, $2, $3::jsonb, 'queued')
                RETURNING id
                """,
                run_id, workflow_slug, json.dumps(payload),
            )

        # 2. Push to Redis Stream
        try:
            redis = self._get_redis()
            stream_key = self._stream_key(workflow_slug)

            # Ensure consumer group exists
            try:
                await redis.xgroup_create(stream_key, CONSUMER_GROUP, id="0", mkstream=True)
            except Exception:
                pass  # group already exists

            stream_id = await redis.xadd(
                stream_key,
                {"task_id": str(task_id), "payload": json.dumps(payload)},
            )

            # Store the Redis stream ID for deduplication
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE agent_task_queue SET redis_stream_id = $1 WHERE id = $2",
                    stream_id, task_id,
                )
        except Exception as exc:
            log.warning(f"Redis stream enqueue failed (task {task_id} still safe in Postgres): {exc}")

        log.info(f"Task enqueued: id={task_id} workflow={workflow_slug} run_id={run_id}")
        return task_id

    async def claim_next(
        self,
        workflow_slug: str,
        worker_id: str | None = None,
    ) -> dict | None:
        """
        Claim the next available task. Returns None if queue is empty.
        Uses Redis XREADGROUP; falls back to Postgres if Redis unavailable.
        """
        worker_id = worker_id or socket.gethostname()

        try:
            redis = self._get_redis()
            stream_key = self._stream_key(workflow_slug)
            messages = await redis.xreadgroup(
                CONSUMER_GROUP,
                worker_id,
                {stream_key: ">"},
                count=1,
                block=0,  # non-blocking
            )

            if not messages:
                return None

            _, entries = messages[0]
            stream_id, fields = entries[0]
            task_id = int(fields["task_id"])
            payload = json.loads(fields["payload"])

            # Mark as processing in Postgres
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE agent_task_queue
                    SET status = 'processing', claimed_at = NOW(), worker_id = $1,
                        attempts = attempts + 1
                    WHERE id = $2
                    """,
                    worker_id, task_id,
                )

            return {"id": task_id, "payload": payload, "stream_id": stream_id}

        except Exception as exc:
            log.warning(f"Redis claim failed, trying Postgres fallback: {exc}")
            return await self._claim_from_postgres(workflow_slug, worker_id)

    async def complete(self, task_id: int, stream_id: str | None = None):
        """Mark a task as complete."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE agent_task_queue SET status = 'complete', completed_at = NOW() WHERE id = $1",
                task_id,
            )
        # Acknowledge in Redis stream
        if stream_id:
            try:
                workflow_slug = await self._get_slug_for_task(task_id)
                redis = self._get_redis()
                await redis.xack(self._stream_key(workflow_slug), CONSUMER_GROUP, stream_id)
            except Exception as exc:
                log.warning(f"Redis xack failed: {exc}")

    async def fail(self, task_id: int, error: str, stream_id: str | None = None):
        """Mark a task as failed."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT attempts FROM agent_task_queue WHERE id = $1", task_id
            )
            new_status = "dead_letter" if (row and row["attempts"] >= 3) else "queued"
            await conn.execute(
                "UPDATE agent_task_queue SET status = $1, last_error = $2 WHERE id = $3",
                new_status, error, task_id,
            )

    async def recover_stale(self):
        """
        Called on worker startup. Re-queues tasks stuck in 'processing'
        for longer than STALE_MINUTES (indicates crashed worker).
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            stale = await conn.fetch(
                f"""
                SELECT id, workflow_slug, payload FROM agent_task_queue
                WHERE status = 'processing'
                  AND claimed_at < NOW() - INTERVAL '{STALE_MINUTES} minutes'
                """
            )
            for row in stale:
                await conn.execute(
                    "UPDATE agent_task_queue SET status = 'queued', claimed_at = NULL, worker_id = NULL WHERE id = $1",
                    row["id"],
                )
                log.warning(f"Recovered stale task {row['id']} ({row['workflow_slug']})")

        log.info(f"Stale task recovery complete. {len(stale)} tasks re-queued.")

    # ── Private helpers ───────────────────────────────────────────────────

    async def _claim_from_postgres(self, workflow_slug: str, worker_id: str) -> dict | None:
        """Postgres fallback when Redis is unavailable."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE agent_task_queue
                SET status = 'processing', claimed_at = NOW(), worker_id = $1, attempts = attempts + 1
                WHERE id = (
                    SELECT id FROM agent_task_queue
                    WHERE workflow_slug = $2 AND status = 'queued'
                    ORDER BY enqueued_at
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id, payload
                """,
                worker_id, workflow_slug,
            )
        if not row:
            return None
        return {"id": row["id"], "payload": json.loads(row["payload"]), "stream_id": None}

    async def _get_slug_for_task(self, task_id: int) -> str:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT workflow_slug FROM agent_task_queue WHERE id = $1", task_id
            )