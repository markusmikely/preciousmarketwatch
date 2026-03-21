"""
Stage 1a — TopicLoader

Smart sync:
  - First run (empty Postgres): full WP fetch → sync all
  - Subsequent runs: load from Postgres, only check WP for new topics
  - Applies TOPICS_PER_RUN batch limit + 24h cooldown
"""

from __future__ import annotations
import logging
from nodes.base import (
    BaseAgent, JSONOutputMixin, ModelConfig, ModelProvider,
    FailureConfig, EventType, AgentStatus,
)
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

            # ── Smart sync ────────────────────────────────────────────
            known_ids = await services.topics.get_known_topic_ids()

            if known_ids:
                self.log.info(f"{len(known_ids)} topics in Postgres — loading locally")

                # Check for new WP topics (non-fatal)
                try:
                    new_topics = await services.topics.get_new_topics_only(known_ids)
                    if new_topics:
                        await self._sync_topics(new_topics)
                        self.log.info(f"Synced {len(new_topics)} new topic(s)")
                except Exception as exc:
                    self.log.warning(f"WP new-topic check failed: {exc}")

                all_topics = await services.topics.load_from_postgres()
            else:
                self.log.info("Empty Postgres — full WP fetch")
                wp_topics = await services.topics.get_eligible_topics()

                if not wp_topics:
                    return self._fail(state, run_id, "No published topics in WordPress")

                await self._sync_topics(wp_topics)
                all_topics = wp_topics

            if not all_topics:
                return self._fail(state, run_id, "No topics available")

            # ── Filter locked + batch select ──────────────────────────
            unlocked = await services.topics.filter_locked_topics(all_topics)
            if not unlocked:
                return self._fail(state, run_id, f"All {len(all_topics)} topic(s) locked")

            batch = await services.topics.select_batch(unlocked, settings.TOPICS_PER_RUN)
            if not batch:
                # Not a failure — just nothing eligible after cooldown
                self.log.info("No topics eligible after 24h cooldown")
                await self._write_stage(run_id, "complete", passed=False, output={"count": 0})
                return {"all_topics": [], "status": "complete", "current_stage": self.stage_name}

            self.log.info(
                f"Selected {len(batch)} topic(s) "
                f"(from {len(unlocked)} unlocked, {len(all_topics)} total)"
            )
            await self._write_stage(run_id, "complete", passed=True,
                                    output={"count": len(batch)})

            return {"all_topics": batch, "current_stage": self.stage_name}

        except Exception as exc:
            return self._fail(state, run_id, str(exc))

    def _fail(self, state, run_id, msg):
        self.log.error(f"TopicLoader: {msg}")
        import asyncio
        asyncio.ensure_future(self._write_stage(run_id, "failed", error=msg))
        return {
            "all_topics": [], "status": "failed",
            "errors": state.get("errors", []) + [{"stage": self.stage_name, "error": msg}],
        }

    async def _sync_topics(self, topics: list[dict]) -> None:
        infra = get_infrastructure()
        for t in topics:
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
                    t["id"], t.get("title", ""), t.get("target_keyword", ""),
                    t.get("summary", ""), t.get("include_keywords", ""),
                    t.get("exclude_keywords", ""), t.get("asset_class", ""),
                    t.get("product_type", ""), t.get("geography", "uk"),
                    t.get("is_buy_side", False), t.get("intent_stage", "consideration"),
                    t.get("priority", 5), t.get("schedule_cron", ""),
                    t.get("agent_status", "idle"),
                    t.get("last_run_at") or None, t.get("run_count", 0),
                    t.get("last_run_id") or None, t.get("last_wp_post_id") or None,
                    t.get("wp_category_id") or None, t.get("affiliate_page_id") or None,
                )
            except Exception as exc:
                log.warning(f"Topic sync failed for WP ID {t.get('id')}: {exc}")