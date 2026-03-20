"""
TopicService — fetch topics, filter locks, select batch, track status.

All status tracking lives in Postgres only. WordPress is read-only
(source of truth for topic definitions, never written to by the pipeline).

Usage:
    from services import services
    topics   = await services.topics.get_eligible_topics()
    unlocked = await services.topics.filter_locked_topics(topics)
    batch    = await services.topics.select_batch(unlocked, batch_size=10)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from infrastructure import get_infrastructure
from config.settings import settings

log = logging.getLogger("pmw.services.topic")


class TopicService:

    # ── Fetch from WordPress ───────────────────────────────────────────

    async def get_eligible_topics(self) -> list[dict]:
        """Fetch published pmw_topic posts from WordPress via GraphQL."""
        infra = get_infrastructure()
        try:
            raw_topics = await infra.wordpress.query_topics(status="PUBLISH", first=100)
        except Exception as exc:
            log.error(f"Failed to fetch topics from WordPress: {exc}")
            return []

        topics = []
        for raw in raw_topics:
            meta = raw.get("meta", {})
            topics.append({
                "id":               raw.get("id"),
                "title":            raw.get("title", {}).get("rendered", ""),
                "target_keyword":   meta.get("pmw_target_keyword", ""),
                "summary":          meta.get("pmw_summary", ""),
                "include_keywords": meta.get("pmw_include_keywords", ""),
                "exclude_keywords": meta.get("pmw_exclude_keywords", ""),
                "asset_class":      meta.get("pmw_asset_class", ""),
                "product_type":     meta.get("pmw_product_type", ""),
                "geography":        meta.get("pmw_geography", "uk"),
                "is_buy_side":      meta.get("pmw_is_buy_side", False),
                "intent_stage":     meta.get("pmw_intent_stage", "consideration"),
                "priority":         meta.get("pmw_priority", 5),
                "schedule_cron":    meta.get("pmw_schedule_cron", ""),
                "last_run_at":      meta.get("pmw_last_run_at", ""),
                "run_count":        meta.get("pmw_run_count", 0),
                "last_run_id":      meta.get("pmw_last_run_id", 0),
                "last_wp_post_id":  meta.get("pmw_last_wp_post_id", 0),
                "wp_category_id":   meta.get("pmw_wp_category_id", 0),
                "affiliate_page_id": meta.get("pmw_affiliate_page_id", 0),
            })

        log.info(f"Fetched {len(topics)} eligible topics from WordPress")
        return topics

    async def get_new_topics_only(self, known_wp_ids: list[int]) -> list[dict]:
        """Fetch only topics from WP not already in Postgres."""
        all_topics = await self.get_eligible_topics()
        known_set = set(known_wp_ids)
        new = [t for t in all_topics if t["id"] not in known_set]
        if new:
            log.info(f"Found {len(new)} new topic(s) not yet in Postgres")
        return new

    # ── Load from Postgres ─────────────────────────────────────────────

    async def load_from_postgres(self) -> list[dict]:
        """Load topics directly from Postgres topics table."""
        infra = get_infrastructure()
        rows = await infra.postgres.fetch(
            """
            SELECT id, topic_name as title, target_keyword, summary,
                   include_keywords, exclude_keywords, asset_class,
                   product_type, geography, is_buy_side, intent_stage,
                   priority, schedule_cron, agent_status, last_run_at,
                   run_count, last_run_id, last_wp_post_id,
                   wp_category_id, affiliate_page_id
            FROM topics
            WHERE status = 'active'
            ORDER BY priority, run_count
            """
        )
        topics = []
        for r in rows:
            d = dict(r)
            if d.get("last_run_at") and hasattr(d["last_run_at"], "isoformat"):
                d["last_run_at"] = d["last_run_at"].isoformat()
            else:
                d["last_run_at"] = str(d.get("last_run_at", "")) if d.get("last_run_at") else ""
            topics.append(d)
        return topics

    async def get_known_topic_ids(self) -> list[int]:
        """Return list of WP post IDs already synced to Postgres."""
        infra = get_infrastructure()
        rows = await infra.postgres.fetch("SELECT id FROM topics")
        return [r["id"] for r in rows]

    # ── Filter locked topics ───────────────────────────────────────────

    async def filter_locked_topics(self, topics: list[dict]) -> list[dict]:
        """Remove topics with active Postgres locks."""
        if not topics:
            return []

        infra = get_infrastructure()
        topic_ids = [t["id"] for t in topics]

        rows = await infra.postgres.fetch(
            """
            SELECT DISTINCT topic_id FROM workflow_runs
            WHERE topic_id = ANY($1::int[])
              AND status = 'running'
              AND lock_expires_at > NOW()
            """,
            topic_ids,
        )
        locked_ids = {r["topic_id"] for r in rows}
        unlocked = [t for t in topics if t["id"] not in locked_ids]

        if locked_ids:
            log.info(f"Filtered out {len(locked_ids)} locked topic(s)")

        return unlocked

    # ── Batch selection ────────────────────────────────────────────────

    async def select_batch(
        self, candidates: list[dict], batch_size: int = 0,
    ) -> list[dict]:
        """
        Select the best N topics from candidates.
        Excludes topics run in the last 24 hours.
        Sorts by priority (lower = higher), then least-run.
        """
        if not candidates:
            return []

        now = datetime.now(timezone.utc)
        cooldown = now - timedelta(hours=24)

        eligible = []
        for t in candidates:
            last_run = t.get("last_run_at", "")
            if last_run:
                try:
                    last_dt = datetime.fromisoformat(str(last_run).replace("Z", "+00:00"))
                    if last_dt > cooldown:
                        continue
                except (ValueError, TypeError):
                    pass
            eligible.append(t)

        if not eligible:
            log.warning("All candidates run in last 24h — using full list")
            eligible = candidates

        eligible.sort(key=lambda t: (t.get("priority", 5), t.get("run_count", 0)))

        if batch_size > 0:
            eligible = eligible[:batch_size]

        return eligible

    # ── Postgres-only status tracking ──────────────────────────────────
    #
    # No WordPress writes. All status lives in Postgres topics table.
    # The dashboard reads from Postgres, not WP meta.

    async def mark_topic_running(self, topic_wp_id: int, run_id: int) -> None:
        """Mark topic as running in Postgres."""
        infra = get_infrastructure()
        try:
            await infra.postgres.execute(
                """
                UPDATE topics SET
                    agent_status = 'running',
                    last_run_id = $1,
                    last_run_at = NOW()
                WHERE id = $2
                """,
                run_id, topic_wp_id,
            )
        except Exception as exc:
            log.warning(f"Postgres topic status update failed for {topic_wp_id}: {exc}")

    async def mark_topic_complete(
        self, topic_wp_id: int, run_id: int, wp_post_id: int | None = None,
    ) -> None:
        """Mark topic as complete in Postgres. Increments run_count."""
        infra = get_infrastructure()
        try:
            await infra.postgres.execute(
                """
                UPDATE topics SET
                    agent_status = 'idle',
                    last_run_id = $1,
                    last_run_at = NOW(),
                    run_count = COALESCE(run_count, 0) + 1,
                    last_wp_post_id = COALESCE($2, last_wp_post_id)
                WHERE id = $3
                """,
                run_id, wp_post_id, topic_wp_id,
            )
        except Exception as exc:
            log.warning(f"Postgres topic complete update failed for {topic_wp_id}: {exc}")

    async def mark_topic_failed(self, topic_wp_id: int, error: str = "") -> None:
        """Mark topic as failed in Postgres."""
        infra = get_infrastructure()
        try:
            await infra.postgres.execute(
                "UPDATE topics SET agent_status = 'failed' WHERE id = $1",
                topic_wp_id,
            )
        except Exception as exc:
            log.warning(f"Postgres topic failed update for {topic_wp_id}: {exc}")