"""
ResearchResultsService — persist per-topic research stage outputs.

Writes to topic_research_results table (migration 009).

Usage:
    from services import services
    await services.research_results.save(
        run_id=42, topic_wp_id=101, topic_title="Best Gold ISA UK",
        stage_name="stage2.keyword_research", status="complete",
        output={"confidence": 0.92, ...}, cost_usd=0.003,
    )
    result = await services.research_results.get_latest(
        run_id=42, topic_wp_id=101, stage_name="stage2.keyword_research",
    )
"""

from __future__ import annotations

import json
import logging
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.research_results")


class ResearchResultsService:

    async def save(
        self,
        run_id: int,
        topic_wp_id: int,
        topic_title: str,
        stage_name: str,
        status: str,
        attempt: int = 1,
        output: dict | None = None,
        error: str | None = None,
        model_used: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> int | None:
        """UPSERT a research result. Returns row ID or None (never raises)."""
        infra = get_infrastructure()
        try:
            return await infra.postgres.fetchval(
                """
                INSERT INTO topic_research_results (
                    run_id, topic_wp_id, topic_title, stage_name,
                    status, attempt_number,
                    output_json, error, model_used,
                    input_tokens, output_tokens, cost_usd,
                    completed_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7::jsonb, $8, $9, $10, $11, $12,
                    CASE WHEN $5 IN ('complete','failed','skipped')
                         THEN NOW() ELSE NULL END
                )
                ON CONFLICT (run_id, topic_wp_id, stage_name, attempt_number)
                DO UPDATE SET
                    status=EXCLUDED.status, output_json=EXCLUDED.output_json,
                    error=EXCLUDED.error, model_used=EXCLUDED.model_used,
                    input_tokens=EXCLUDED.input_tokens, output_tokens=EXCLUDED.output_tokens,
                    cost_usd=EXCLUDED.cost_usd, completed_at=EXCLUDED.completed_at
                RETURNING id
                """,
                run_id, topic_wp_id, topic_title, stage_name,
                status, attempt,
                json.dumps(output) if output else None,
                error, model_used, input_tokens, output_tokens, cost_usd,
            )
        except Exception as exc:
            log.error(f"topic_research_results write failed: {exc}",
                      extra={"run_id": run_id, "topic": topic_wp_id, "stage": stage_name})
            return None

    async def get_latest(self, run_id: int, topic_wp_id: int, stage_name: str) -> dict | None:
        """Get the latest result for a topic+stage in a run."""
        infra = get_infrastructure()
        row = await infra.postgres.fetchrow(
            """SELECT * FROM topic_research_results
               WHERE run_id=$1 AND topic_wp_id=$2 AND stage_name=$3
               ORDER BY attempt_number DESC LIMIT 1""",
            run_id, topic_wp_id, stage_name,
        )
        if not row:
            return None
        result = dict(row)
        if result.get("output_json") and isinstance(result["output_json"], str):
            try:
                result["output_json"] = json.loads(result["output_json"])
            except json.JSONDecodeError:
                pass
        return result

    async def get_topic_stages(self, run_id: int, topic_wp_id: int) -> list[dict]:
        """All stage results for a topic in a run."""
        infra = get_infrastructure()
        rows = await infra.postgres.fetch(
            """SELECT stage_name, status, attempt_number, cost_usd,
                      input_tokens, output_tokens, model_used, error,
                      started_at, completed_at
               FROM topic_research_results
               WHERE run_id=$1 AND topic_wp_id=$2 ORDER BY started_at""",
            run_id, topic_wp_id,
        )
        return [dict(r) for r in rows]

    async def get_topic_history(self, topic_wp_id: int, limit: int = 20) -> list[dict]:
        """Research history across all runs for a topic."""
        infra = get_infrastructure()
        rows = await infra.postgres.fetch(
            """SELECT run_id, topic_title,
                      COUNT(*) AS stage_count,
                      COUNT(*) FILTER (WHERE status='complete') AS stages_complete,
                      COUNT(*) FILTER (WHERE status='failed') AS stages_failed,
                      SUM(cost_usd) AS total_cost_usd,
                      MIN(started_at) AS started_at, MAX(completed_at) AS completed_at
               FROM topic_research_results WHERE topic_wp_id=$1
               GROUP BY run_id, topic_title ORDER BY MIN(started_at) DESC LIMIT $2""",
            topic_wp_id, limit,
        )
        return [dict(r) for r in rows]

    async def get_run_summary(self, run_id: int) -> list[dict]:
        """Summary of all topic results for a run (one row per topic)."""
        infra = get_infrastructure()
        rows = await infra.postgres.fetch(
            """SELECT topic_wp_id, topic_title,
                      COUNT(*) AS total_stages,
                      COUNT(*) FILTER (WHERE status='complete') AS complete,
                      COUNT(*) FILTER (WHERE status='failed') AS failed,
                      SUM(cost_usd) AS cost_usd,
                      array_agg(DISTINCT stage_name ORDER BY stage_name)
                          FILTER (WHERE status='failed') AS failed_stages
               FROM topic_research_results WHERE run_id=$1
               GROUP BY topic_wp_id, topic_title ORDER BY topic_title""",
            run_id,
        )
        return [dict(r) for r in rows]