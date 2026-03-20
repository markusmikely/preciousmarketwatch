"""
Stage 1a — TopicLoader

Fetches eligible topics from WordPress, syncs to Postgres, filters
locked topics, applies TOPICS_PER_RUN batch limit, returns all_topics.
"""

from __future__ import annotations
import logging
from nodes.base import BaseAgent
from infrastructure import get_infrastructure
from config.settings import settings

log = logging.getLogger("pmw.node.topic_loader")


class TopicLoader(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="topic_loader", stage_name="research.stage1.topic_loader")

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        await self._write_stage(run_id, "running")

        try:
            from services import services

            wp_topics = await services.topics.get_eligible_topics()
            self.log.info(f"Fetched {len(wp_topics)} topics from WordPress")

            if not wp_topics:
                await self._write_stage(run_id, "failed", error="No published topics found")
                return {"all_topics": [], "status": "failed",
                        "errors": state.get("errors", []) + [{"stage": self.stage_name, "error": "No published topics"}]}

            await self._sync_topics(wp_topics)
            unlocked = await services.topics.filter_locked_topics(wp_topics)

            if not unlocked:
                await self._write_stage(run_id, "failed", error="All topics locked")
                return {"all_topics": [], "status": "failed",
                        "errors": state.get("errors", []) + [{"stage": self.stage_name, "error": "All topics locked"}]}

            # Apply batch limit from settings
            batch_size = settings.TOPICS_PER_RUN
            if batch_size > 0:
                # Sort by priority (lower = higher priority) then by least-run
                unlocked.sort(key=lambda t: (t.get("priority", 5), t.get("run_count", 0)))
                unlocked = unlocked[:batch_size]
                self.log.info(f"Batch limited to {len(unlocked)} topics (TOPICS_PER_RUN={batch_size})")

            await self._write_stage(run_id, "complete", passed=True,
                                    output={"count": len(unlocked), "ids": [t["id"] for t in unlocked]})

            return {"all_topics": unlocked, "current_stage": self.stage_name}

        except Exception as exc:
            self.log.error(f"TopicLoader failed: {exc}")
            await self._write_stage(run_id, "failed", error=str(exc))
            return {"all_topics": [], "status": "failed",
                    "errors": state.get("errors", []) + [{"stage": self.stage_name, "error": str(exc)}]}

    async def _sync_topics(self, wp_topics: list[dict]) -> None:
        infra = get_infrastructure()
        for t in wp_topics:
            try:
                await infra.postgres.execute(
                    """
                    INSERT INTO topics (id, topic_name, target_keyword, summary,
                        include_keywords, exclude_keywords, asset_class, product_type,
                        geography, is_buy_side, intent_stage, priority, schedule_cron,
                        agent_status, last_run_at, run_count, last_run_id,
                        last_wp_post_id, wp_category_id, affiliate_page_id)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,
                            $15::timestamptz,$16,$17,$18,$19,$20)
                    ON CONFLICT (id) DO UPDATE SET
                        topic_name=EXCLUDED.topic_name, target_keyword=EXCLUDED.target_keyword,
                        summary=EXCLUDED.summary, include_keywords=EXCLUDED.include_keywords,
                        exclude_keywords=EXCLUDED.exclude_keywords, asset_class=EXCLUDED.asset_class,
                        product_type=EXCLUDED.product_type, geography=EXCLUDED.geography,
                        is_buy_side=EXCLUDED.is_buy_side, intent_stage=EXCLUDED.intent_stage,
                        priority=EXCLUDED.priority, schedule_cron=EXCLUDED.schedule_cron
                    """,
                    t["id"], t.get("title",""), t.get("target_keyword",""), t.get("summary",""),
                    t.get("include_keywords",""), t.get("exclude_keywords",""),
                    t.get("asset_class",""), t.get("product_type",""), t.get("geography","uk"),
                    t.get("is_buy_side",False), t.get("intent_stage","consideration"),
                    t.get("priority",5), t.get("schedule_cron",""), t.get("agent_status","idle"),
                    t.get("last_run_at") or None, t.get("run_count",0),
                    t.get("last_run_id") or None, t.get("last_wp_post_id") or None,
                    t.get("wp_category_id") or None, t.get("affiliate_page_id") or None,
                )
            except Exception as exc:
                log.warning(f"Topic sync failed for WP ID {t.get('id')}: {exc}")