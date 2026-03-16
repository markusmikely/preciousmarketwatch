"""
WorkflowService — manages workflow_runs lifecycle and topic locking.

Owns:
  - Creating workflow_runs rows (run_id = workflow_runs.id)
  - Postgres-based topic locking (atomic, crash-safe)
  - Run status transitions (running → complete/failed)
  - Stale lock recovery on worker startup

Does NOT own:
  - LangGraph graph execution (orchestrator owns that)
  - WP display status writes (TopicService owns that)
  - Event emission (EventService owns that)

Usage:
    from services import services
    run_id   = await services.workflows.create_run(topic_id=101, triggered_by="scheduler")
    acquired = await services.workflows.acquire_topic_lock(topic_wp_id=101, run_id=run_id)
    await services.workflows.release_topic_lock(topic_wp_id=101, run_id=run_id, success=True)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.workflow")

# Default lock expiry — any run holding a lock longer than this is considered crashed
DEFAULT_LOCK_EXPIRY_MINUTES = 120


class WorkflowService:
    """
    Stateless service — all state lives in Postgres via get_infrastructure().
    """

    # ── Run lifecycle ──────────────────────────────────────────────────────

    async def create_run(
        self,
        topic_id: int | None = None,
        triggered_by: str = "scheduler",
    ) -> int:
        """
        Insert a new workflow_runs row and return its id.
        This id is the run_id used throughout the entire pipeline.

        Args:
            topic_id: topics.id (Postgres) or WP post ID — optional at creation
                      time because Stage 1 selects the topic.
            triggered_by: "scheduler" | "manual" | "api"

        Returns:
            workflow_runs.id — the canonical run_id.
        """
        infra = get_infrastructure()
        run_id = await infra.postgres.fetchval(
            """
            INSERT INTO workflow_runs (topic_id, status, current_stage, started_at)
            VALUES ($1, 'pending', 'start', NOW())
            RETURNING id
            """,
            topic_id,
        )
        log.info("Workflow run created", extra={"run_id": run_id, "triggered_by": triggered_by})
        return run_id

    async def get_run(self, run_id: int) -> dict | None:
        """Fetch a single workflow_runs row as a dict. Returns None if not found."""
        infra = get_infrastructure()
        row = await infra.postgres.fetchrow(
            "SELECT * FROM workflow_runs WHERE id = $1",
            run_id,
        )
        return dict(row) if row else None

    # ── Topic locking (Postgres-based, atomic) ─────────────────────────────

    async def acquire_topic_lock(
        self,
        topic_wp_id: int,
        run_id: int,
        expires_minutes: int = DEFAULT_LOCK_EXPIRY_MINUTES,
    ) -> bool:
        """
        Attempt to claim a topic for a pipeline run.

        Uses workflow_runs as the lock table — a row with status='running'
        and a non-expired lock_expires_at means the topic is locked.

        Returns True if the lock was acquired, False if already locked.

        This is safe against race conditions:
          1. Expire any stale locks for this topic (crashed runs)
          2. Check if any valid lock exists
          3. Claim the lock by updating this run's row

        All three operations run inside a single transaction.
        """
        infra = get_infrastructure()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

        async with infra.postgres.transaction() as conn:
            # Step 1: Expire stale locks for this topic
            await conn.execute(
                """
                UPDATE workflow_runs
                SET status = 'failed',
                    failed_at = NOW(),
                    lock_expires_at = NULL
                WHERE topic_id = $1
                  AND status = 'running'
                  AND lock_expires_at < NOW()
                """,
                topic_wp_id,
            )

            # Step 2: Check for any active (non-expired) lock
            existing = await conn.fetchrow(
                """
                SELECT id FROM workflow_runs
                WHERE topic_id = $1
                  AND status = 'running'
                  AND lock_expires_at > NOW()
                  AND id != $2
                """,
                topic_wp_id,
                run_id,
            )

            if existing:
                log.info(
                    "Topic lock not acquired — held by another run",
                    extra={
                        "run_id": run_id,
                        "topic_wp_id": topic_wp_id,
                        "held_by": existing["id"],
                    },
                )
                return False

            # Step 3: Claim the lock
            await conn.execute(
                """
                UPDATE workflow_runs
                SET status = 'running',
                    topic_id = $1,
                    lock_expires_at = $2,
                    current_stage = 'stage1.brief_locker'
                WHERE id = $3
                """,
                topic_wp_id,
                expires_at,
                run_id,
            )

        log.info(
            "Topic lock acquired",
            extra={"run_id": run_id, "topic_wp_id": topic_wp_id},
        )
        return True

    async def release_topic_lock(
        self,
        topic_wp_id: int,
        run_id: int,
        success: bool,
        wp_post_id: int | None = None,
    ) -> None:
        """
        Release the topic lock on pipeline completion or failure.
        Updates workflow_runs status and clears lock_expires_at.

        Args:
            topic_wp_id: WP post ID of the topic.
            run_id: workflow_runs.id.
            success: True → status='complete', False → status='failed'.
            wp_post_id: WP post ID of the published article (on success).
        """
        infra = get_infrastructure()
        final_status = "complete" if success else "failed"
        timestamp_col = "completed_at" if success else "failed_at"

        await infra.postgres.execute(
            f"""
            UPDATE workflow_runs
            SET status = $1,
                {timestamp_col} = NOW(),
                lock_expires_at = NULL,
                wp_post_id = COALESCE($2, wp_post_id)
            WHERE id = $3
            """,
            final_status,
            wp_post_id,
            run_id,
        )

        log.info(
            "Topic lock released",
            extra={
                "run_id": run_id,
                "topic_wp_id": topic_wp_id,
                "status": final_status,
            },
        )

    # ── Run failure ────────────────────────────────────────────────────────

    async def fail_run(self, run_id: int, error: str) -> None:
        """
        Mark a run as failed. Clears any held lock.

        Args:
            run_id: workflow_runs.id.
            error: Error message to store (for dashboard display).
        """
        infra = get_infrastructure()
        await infra.postgres.execute(
            """
            UPDATE workflow_runs
            SET status = 'failed',
                failed_at = NOW(),
                lock_expires_at = NULL
            WHERE id = $1
              AND status NOT IN ('complete', 'failed')
            """,
            run_id,
        )
        log.error("Run failed", extra={"run_id": run_id, "error": error[:500]})

    # ── Stale lock recovery (called on worker startup) ─────────────────────

    async def recover_stale_runs(
        self,
        stale_after_minutes: int = DEFAULT_LOCK_EXPIRY_MINUTES,
    ) -> int:
        """
        Reset expired locks on worker startup. Any run with status='running'
        and lock_expires_at in the past is assumed to be from a crashed worker.

        Returns the number of stale runs recovered.
        """
        infra = get_infrastructure()
        rows = await infra.postgres.fetch(
            """
            UPDATE workflow_runs
            SET status = 'failed',
                failed_at = NOW(),
                lock_expires_at = NULL
            WHERE status = 'running'
              AND lock_expires_at < NOW()
            RETURNING id, topic_id
            """,
        )

        count = len(rows)
        if count > 0:
            stale_ids = [r["id"] for r in rows]
            log.warning(
                f"Recovered {count} stale run(s)",
                extra={"stale_run_ids": stale_ids},
            )
        else:
            log.info("No stale runs found")

        return count

    # ── Update helpers ─────────────────────────────────────────────────────

    async def update_current_stage(self, run_id: int, stage_name: str) -> None:
        """Update the current_stage field for dashboard display."""
        infra = get_infrastructure()
        await infra.postgres.execute(
            "UPDATE workflow_runs SET current_stage = $1 WHERE id = $2",
            stage_name,
            run_id,
        )

    async def update_total_cost(self, run_id: int, cost_usd: float) -> None:
        """Update the total_cost_usd field."""
        infra = get_infrastructure()
        await infra.postgres.execute(
            "UPDATE workflow_runs SET total_cost_usd = $1 WHERE id = $2",
            cost_usd,
            run_id,
        )