"""
Stage 1a — TopicLoader (v3.0)

Smart sync:
  - First run (empty Postgres): full WP fetch → batch sync
  - Subsequent runs: load from Postgres, check WP for new topics only
  - Syncs content_type field from WordPress
  - Skips exhausted topics (all affiliates failed in prior runs)
  - Caps at 100 topics
  - Batch upsert for efficiency
"""

from __future__ import annotations

import logging

from nodes.base import BaseAgent, EventType
from infrastructure import get_infrastructure
from config.settings import settings

log = logging.getLogger("pmw.node.topic_loader")

MAX_TOPICS = 100


class TopicLoader(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="topic_loader",
            stage_name="research.stage1.topic_loader",
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]

        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage(run_id, "running")

        try:
            from services import services

            # ── Smart sync ────────────────────────────────────────────
            known_ids = await services.topics.get_known_topic_ids()

            if known_ids:
                self.log.info(f"{len(known_ids)} topics in Postgres — loading locally")
                try:
                    new_topics = await services.topics.get_new_topics_only(known_ids)
                    if new_topics:
                        await self._batch_sync(new_topics)
                        self.log.info(f"Synced {len(new_topics)} new topic(s)")
                except Exception as exc:
                    self.log.warning(f"WP new-topic check failed (non-fatal): {exc}")

                all_topics = await services.topics.load_from_postgres()
            else:
                self.log.info("Empty Postgres — full WP fetch")
                wp_topics = await services.topics.get_eligible_topics()
                if not wp_topics:
                    return await self._fail(state, run_id, "No published topics in WordPress")
                await self._batch_sync(wp_topics)
                all_topics = wp_topics

            if not all_topics:
                return await self._fail(state, run_id, "No topics available")

            # Cap
            if len(all_topics) > MAX_TOPICS:
                self.log.info(f"Capping {len(all_topics)} → {MAX_TOPICS}")
                all_topics = all_topics[:MAX_TOPICS]

            # Filter locked
            unlocked = await services.topics.filter_locked_topics(all_topics)
            if not unlocked:
                return await self._fail(state, run_id, f"All {len(all_topics)} topic(s) locked")

            # Filter exhausted (affiliate topics where all affiliates failed coherence)
            eligible = await self._filter_exhausted(unlocked)

            # Batch select with cooldown
            batch_size = settings.TOPICS_PER_RUN or MAX_TOPICS
            batch = await services.topics.select_batch(eligible, batch_size)

            if not batch:
                self.log.info("No topics eligible after cooldown")
                await self._write_stage(run_id, "complete", passed=False,
                                        output={"count": 0, "reason": "cooldown"})
                return {"all_topics": [], "status": "complete", "current_stage": self.stage_name}

            self.log.info(
                f"Selected {len(batch)} topic(s) "
                f"({len(eligible)} eligible, {len(unlocked)} unlocked, {len(all_topics)} total)"
            )

            output = {
                "count": len(batch),
                "by_type": self._count_by_type(batch),
                "titles": [t.get("title", "?")[:50] for t in batch[:5]],
            }
            await self._write_stage(run_id, "complete", passed=True, output=output)
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)

            return {"all_topics": batch, "current_stage": self.stage_name}

        except Exception as exc:
            return await self._fail(state, run_id, str(exc))

    # ── Batch sync ─────────────────────────────────────────────────────

    async def _batch_sync(self, topics: list[dict]) -> None:
        """Batch upsert topics to Postgres including content_type."""
        if not topics:
            return
        infra = get_infrastructure()

        # Check if content_type column exists (migration 010)
        has_content_type = await self._column_exists("topics", "content_type")

        args_list = []
        for t in topics:
            args = (
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
            if has_content_type:
                args = args + (t.get("content_type", "affiliate"),)
            args_list.append(args)

        if has_content_type:
            sql = """
                INSERT INTO topics (
                    id, topic_name, target_keyword, summary,
                    include_keywords, exclude_keywords, asset_class, product_type,
                    geography, is_buy_side, intent_stage, priority, schedule_cron,
                    agent_status, last_run_at, run_count, last_run_id,
                    last_wp_post_id, wp_category_id, affiliate_page_id, content_type
                ) VALUES (
                    $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,
                    $15::timestamptz,$16,$17,$18,$19,$20,$21
                )
                ON CONFLICT (id) DO UPDATE SET
                    topic_name=EXCLUDED.topic_name, target_keyword=EXCLUDED.target_keyword,
                    summary=EXCLUDED.summary, include_keywords=EXCLUDED.include_keywords,
                    exclude_keywords=EXCLUDED.exclude_keywords, asset_class=EXCLUDED.asset_class,
                    product_type=EXCLUDED.product_type, geography=EXCLUDED.geography,
                    is_buy_side=EXCLUDED.is_buy_side, intent_stage=EXCLUDED.intent_stage,
                    priority=EXCLUDED.priority, schedule_cron=EXCLUDED.schedule_cron,
                    content_type=EXCLUDED.content_type
            """
        else:
            sql = """
                INSERT INTO topics (
                    id, topic_name, target_keyword, summary,
                    include_keywords, exclude_keywords, asset_class, product_type,
                    geography, is_buy_side, intent_stage, priority, schedule_cron,
                    agent_status, last_run_at, run_count, last_run_id,
                    last_wp_post_id, wp_category_id, affiliate_page_id
                ) VALUES (
                    $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,
                    $15::timestamptz,$16,$17,$18,$19,$20
                )
                ON CONFLICT (id) DO UPDATE SET
                    topic_name=EXCLUDED.topic_name, target_keyword=EXCLUDED.target_keyword,
                    summary=EXCLUDED.summary, asset_class=EXCLUDED.asset_class,
                    product_type=EXCLUDED.product_type, geography=EXCLUDED.geography,
                    priority=EXCLUDED.priority
            """

        try:
            await infra.postgres.executemany(sql, args_list)
        except Exception as exc:
            self.log.warning(f"Batch sync failed, trying one-by-one: {exc}")
            for args in args_list:
                try:
                    await infra.postgres.execute(sql, *args)
                except Exception as inner:
                    log.warning(f"Topic sync failed for WP ID {args[0]}: {inner}")

    # ── Exhausted topic filter ─────────────────────────────────────────

    async def _filter_exhausted(self, topics: list[dict]) -> list[dict]:
        """
        Remove affiliate topics where ALL affiliates have failed coherence
        in prior runs. Authority/commentary topics are never exhausted.
        """
        if not topics:
            return []

        # Only check affiliate topics
        affiliate_ids = [
            t["id"] for t in topics
            if t.get("content_type", "affiliate") == "affiliate"
        ]
        if not affiliate_ids:
            return topics

        infra = get_infrastructure()
        try:
            rows = await infra.postgres.fetch(
                """
                SELECT topic_wp_id
                FROM topic_briefs
                WHERE topic_wp_id = ANY($1::int[])
                GROUP BY topic_wp_id
                HAVING COUNT(*) FILTER (WHERE status = 'passed') = 0
                   AND COUNT(*) > 0
                """,
                affiliate_ids,
            )
            exhausted = {r["topic_wp_id"] for r in rows}

            if exhausted:
                self.log.info(f"Filtered {len(exhausted)} exhausted affiliate topic(s)")
                from services import services
                for tid in exhausted:
                    try:
                        await services.topics.mark_topic_failed(
                            tid, "All affiliates failed coherence in prior runs"
                        )
                    except Exception:
                        pass

            return [t for t in topics if t["id"] not in exhausted]

        except Exception as exc:
            self.log.warning(f"Exhausted check failed (non-fatal): {exc}")
            return topics

    # ── Helpers ─────────────────────────────────────────────────────────

    async def _column_exists(self, table: str, column: str) -> bool:
        infra = get_infrastructure()
        try:
            return bool(await infra.postgres.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name=$1 AND column_name=$2)",
                table, column,
            ))
        except Exception:
            return False

    @staticmethod
    def _count_by_type(topics: list[dict]) -> dict:
        counts = {}
        for t in topics:
            ct = t.get("content_type", "affiliate")
            counts[ct] = counts.get(ct, 0) + 1
        return counts

    async def _fail(self, state, run_id, msg):
        self.log.error(f"TopicLoader: {msg}")
        await self._write_stage(run_id, "failed", error=msg)
        await self._emit_event(EventType.STAGE_FAILED, run_id, {"error": msg})
        return {
            "all_topics": [], "status": "failed",
            "errors": state.get("errors", []) + [{"stage": self.stage_name, "error": msg}],
        }