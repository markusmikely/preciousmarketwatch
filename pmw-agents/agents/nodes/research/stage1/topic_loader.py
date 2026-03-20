"""
Stage 1a — TopicLoader

Fetches ALL eligible topics from WordPress, syncs to Postgres,
filters out locked topics, returns the full list in all_topics.

This is the first node in the research graph. It populates all_topics
which is then used by brief_builder to process every topic.
"""

from __future__ import annotations

import logging

from nodes.base import BaseAgent, EventType
from infrastructure import get_infrastructure

log = logging.getLogger("pmw.node.topic_loader")


class TopicLoader(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="topic_loader",
            stage_name="research.stage1.topic_loader",
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]

        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            from services import services

            # Step 1: Fetch published topics from WordPress
            wp_topics = await services.topics.get_eligible_topics()
            self.log.info(f"Fetched {len(wp_topics)} topics from WordPress", run_id=run_id)

            if not wp_topics:
                error_msg = "No published topics found in WordPress"
                self.log.info(error_msg, run_id=run_id)
                await self._write_stage_record(
                    run_id, status="failed", attempt=1, error=error_msg,
                )
                return {
                    "all_topics": [],
                    "current_stage": "stage1.topic_loader",
                    "status": "failed",
                    "errors": state.get("errors", []) + [{
                        "stage": "stage1.topic_loader",
                        "error": error_msg,
                        "recoverable": True,
                    }],
                }

            # Step 2: Sync each WP topic to Postgres
            await self._sync_topics_to_postgres(wp_topics)

            # Step 3: Filter out topics with active locks
            unlocked = await services.topics.filter_locked_topics(wp_topics)

            if not unlocked:
                error_msg = (
                    f"All {len(wp_topics)} topic(s) are currently locked by other runs. "
                    "Will retry next cycle."
                )
                self.log.info(error_msg, run_id=run_id)
                await self._write_stage_record(
                    run_id, status="failed", attempt=1, error=error_msg,
                )
                return {
                    "all_topics": [],
                    "current_stage": "stage1.topic_loader",
                    "status": "failed",
                    "errors": state.get("errors", []) + [{
                        "stage": "stage1.topic_loader",
                        "error": error_msg,
                        "recoverable": True,
                    }],
                }

            output = {"count": len(unlocked), "topic_ids": [t["id"] for t in unlocked]}
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True, output=output,
            )

            return {
                "all_topics": unlocked,
                "current_stage": "stage1.topic_loader",
            }

        except Exception as exc:
            self.log.error(f"TopicLoader failed: {exc}", run_id=run_id)
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "all_topics": [],
                "current_stage": "stage1.topic_loader",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage1.topic_loader",
                    "error": str(exc),
                }],
            }

    async def _sync_topics_to_postgres(self, wp_topics: list[dict]) -> None:
        """Upsert WP topics into the Postgres topics table."""
        infra = get_infrastructure()
        for t in wp_topics:
            try:
                await infra.postgres.execute(
                    """
                    INSERT INTO topics (
                        id, topic_name, target_keyword, summary,
                        include_keywords, exclude_keywords,
                        asset_class, product_type, geography,
                        is_buy_side, intent_stage, priority,
                        schedule_cron, agent_status,
                        last_run_at, run_count, last_run_id,
                        last_wp_post_id, wp_category_id, affiliate_page_id
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9,
                        $10, $11, $12, $13, $14,
                        $15::timestamptz, $16, $17, $18, $19, $20
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        topic_name       = EXCLUDED.topic_name,
                        target_keyword   = EXCLUDED.target_keyword,
                        summary          = EXCLUDED.summary,
                        include_keywords = EXCLUDED.include_keywords,
                        exclude_keywords = EXCLUDED.exclude_keywords,
                        asset_class      = EXCLUDED.asset_class,
                        product_type     = EXCLUDED.product_type,
                        geography        = EXCLUDED.geography,
                        is_buy_side      = EXCLUDED.is_buy_side,
                        intent_stage     = EXCLUDED.intent_stage,
                        priority         = EXCLUDED.priority,
                        schedule_cron    = EXCLUDED.schedule_cron
                    """,
                    t["id"],
                    t.get("title", ""),
                    t.get("target_keyword", ""),
                    t.get("summary", ""),
                    t.get("include_keywords", ""),
                    t.get("exclude_keywords", ""),
                    t.get("asset_class", ""),
                    t.get("product_type", ""),
                    t.get("geography", "uk"),
                    t.get("is_buy_side", False),
                    t.get("intent_stage", "consideration"),
                    t.get("priority", 5),
                    t.get("schedule_cron", ""),
                    t.get("agent_status", "idle"),
                    t.get("last_run_at") or None,
                    t.get("run_count", 0),
                    t.get("last_run_id") or None,
                    t.get("last_wp_post_id") or None,
                    t.get("wp_category_id") or None,
                    t.get("affiliate_page_id") or None,
                )
            except Exception as exc:
                log.warning(f"Topic sync failed for WP ID {t.get('id')}: {exc}")