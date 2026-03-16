"""
TopicService — fetch topics from WordPress (GraphQL), filter by lock status, select next.

Owns:
  - Query pmw_topic CPT from WPGraphQL via infra.wordpress.query_topics()
  - Filtering out topics with active Postgres locks
  - Priority-based topic selection (respects 24h cooldown)
  - GraphQL mutation for display-only status updates (fire-and-forget)

Does NOT own:
  - Topic creation (WordPress admin UI owns that)
  - Topic locking (WorkflowService owns that)
  - Run lifecycle (WorkflowService owns that)

Usage:
    from services import services
    topics     = await services.topics.get_eligible_topics()
    unlocked   = await services.topics.filter_locked_topics(topics)
    selected   = await services.topics.select_next_topic(unlocked)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.topic")


class TopicService:
    """
    Stateless service — WordPress access via infra.wordpress (GraphQL),
    Postgres lock checks via infra.postgres.
    """

    # ── Fetch topics from WordPress ────────────────────────────────────────

    async def get_eligible_topics(self) -> list[dict]:
        """
        Fetch all published pmw_topic posts from WordPress via GraphQL.
        Only topics with status='publish' are eligible for scheduled runs.

        Returns:
            List of topic dicts with WP post ID, title, and all pmw_ meta fields.
        """
        infra = get_infrastructure()

        try:
            # WPGraphQL query — returns normalised dicts matching old REST shape
            raw_topics = await infra.wordpress.query_topics(
                status="PUBLISH",
                first=100,
            )
        except Exception as exc:
            log.error("Failed to fetch topics from WordPress", extra={"error": str(exc)})
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
                "agent_status":     meta.get("pmw_agent_status", "idle"),
                "last_run_at":      meta.get("pmw_last_run_at", ""),
                "run_count":        meta.get("pmw_run_count", 0),
                "last_run_id":      meta.get("pmw_last_run_id", 0),
                "last_wp_post_id":  meta.get("pmw_last_wp_post_id", 0),
                "wp_category_id":   meta.get("pmw_wp_category_id", 0),
                "affiliate_page_id": meta.get("pmw_affiliate_page_id", 0),
            })

        log.info(f"Fetched {len(topics)} eligible topics from WordPress")
        return topics

    # ── Filter out locked topics ───────────────────────────────────────────

    async def filter_locked_topics(self, topics: list[dict]) -> list[dict]:
        """
        Remove topics that have an active lock in workflow_runs.
        A topic is locked if there's a row with status='running' and
        lock_expires_at in the future.
        """
        if not topics:
            return []

        infra = get_infrastructure()
        topic_ids = [t["id"] for t in topics]

        rows = await infra.postgres.fetch(
            """
            SELECT DISTINCT topic_id
            FROM workflow_runs
            WHERE topic_id = ANY($1::int[])
              AND status = 'running'
              AND lock_expires_at > NOW()
            """,
            topic_ids,
        )
        locked_ids = {r["topic_id"] for r in rows}

        unlocked = [t for t in topics if t["id"] not in locked_ids]

        if locked_ids:
            log.info(
                f"Filtered out {len(locked_ids)} locked topic(s)",
                extra={"locked_ids": list(locked_ids)},
            )

        return unlocked

    # ── Select next topic ──────────────────────────────────────────────────

    async def select_next_topic(self, candidates: list[dict]) -> dict | None:
        """
        Select the best topic to run next.

        Selection criteria (in order):
          1. Exclude topics run in the last 24 hours
          2. Sort by priority (lower number = higher priority)
          3. Among equal priority, prefer topics with fewer total runs
          4. Among equal runs, prefer topics that haven't been run recently
        """
        if not candidates:
            return None

        now = datetime.now(timezone.utc)
        cooldown = now - timedelta(hours=24)

        eligible = []
        for t in candidates:
            last_run = t.get("last_run_at", "")
            if last_run:
                try:
                    last_dt = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
                    if last_dt > cooldown:
                        continue
                except (ValueError, TypeError):
                    pass
            eligible.append(t)

        if not eligible:
            log.warning("All candidates run in last 24h — using full list")
            eligible = candidates

        def sort_key(topic):
            priority = topic.get("priority", 5)
            run_count = topic.get("run_count", 0)
            last_run = topic.get("last_run_at", "")
            return (priority, run_count, last_run)

        eligible.sort(key=sort_key)

        selected = eligible[0]
        log.info(
            "Topic selected",
            extra={
                "topic_id": selected["id"],
                "title": selected["title"],
                "priority": selected.get("priority"),
            },
        )
        return selected

    # ── WP display status updates (fire-and-forget, via GraphQL) ───────────
    # These write to WP meta for display in the WordPress admin only.
    # They are NOT used for locking or concurrency control.

    async def mark_topic_running(self, topic_wp_id: int, run_id: int) -> None:
        """
        Update WP meta: pmw_agent_status=running, pmw_last_run_id=run_id.
        Fire-and-forget — failure is logged but never propagates.
        """
        await self._update_topic_meta(topic_wp_id, {
            "pmw_agent_status": "running",
            "pmw_last_run_id": run_id,
            "pmw_last_run_at": datetime.now(timezone.utc).isoformat(),
        })

    async def mark_topic_complete(
        self,
        topic_wp_id: int,
        run_id: int,
        wp_post_id: int | None = None,
    ) -> None:
        """
        Update WP meta: status=idle, increment run_count, set last_wp_post_id.
        Fire-and-forget.
        """
        infra = get_infrastructure()

        # Fetch current run_count from WP to increment
        try:
            current_meta = await infra.wordpress.get_topic_meta(topic_wp_id)
            current_count = current_meta.get("pmw_run_count", 0)
        except Exception:
            current_count = 0

        meta = {
            "pmw_agent_status": "idle",
            "pmw_last_run_id": run_id,
            "pmw_last_run_at": datetime.now(timezone.utc).isoformat(),
            "pmw_run_count": (current_count or 0) + 1,
        }
        if wp_post_id:
            meta["pmw_last_wp_post_id"] = wp_post_id

        await self._update_topic_meta(topic_wp_id, meta)

    async def mark_topic_failed(self, topic_wp_id: int, error: str) -> None:
        """
        Update WP meta: pmw_agent_status=failed.
        Fire-and-forget.
        """
        await self._update_topic_meta(topic_wp_id, {
            "pmw_agent_status": "failed",
        })

    async def _update_topic_meta(self, topic_wp_id: int, meta: dict) -> None:
        """
        Update topic meta fields via GraphQL mutation.
        Never raises — failures are logged and swallowed.
        """
        infra = get_infrastructure()
        try:
            await infra.wordpress.update_topic_meta(topic_wp_id, meta)
            log.debug(
                "WP topic meta updated",
                extra={"topic_wp_id": topic_wp_id, "meta_keys": list(meta.keys())},
            )
        except Exception as exc:
            log.warning(
                "WP topic meta update failed (non-blocking)",
                extra={"topic_wp_id": topic_wp_id, "error": str(exc)},
            )