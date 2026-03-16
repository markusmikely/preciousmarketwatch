"""
Stage 6a — DataFetcher (NonLLM)

Parallel fetch of buyer psychology source data:
  - Reddit threads via services.buyer.fetch_reddit()
  - MoneySavingExpert forum via services.buyer.fetch_mse()
  - Affiliate FAQ via services.buyer.fetch_affiliate_faq()
  - PAA questions from state (already fetched in Stage 2)

Caches all sources in Redis (1h TTL) so Stage 6b retries don't re-fetch.

Depends on: Stage 4 + Stage 5 (barrier.stage6)
"""

from __future__ import annotations

import asyncio

from nodes.base import BaseAgent, EventType


class DataFetcher(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="data_fetcher",
            stage_name="research.stage6.data_fetcher",
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        topic = brief.get("topic") or state.get("selected_topic") or {}
        primary = brief.get("affiliate", {}).get("primary") or state.get("primary_affiliate") or {}
        keyword = topic.get("target_keyword", "")
        geography = topic.get("geography", "uk")

        # PAA questions come from Stage 2 — no new fetch needed
        paa_questions = (state.get("keyword_research") or {}).get("paa_questions", [])

        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            from services import services

            # ── Parallel fetch ────────────────────────────────────────
            reddit_posts, mse_threads, affiliate_faq = await asyncio.gather(
                services.buyer.fetch_reddit(keyword, geography),
                services.buyer.fetch_mse(keyword),
                services.buyer.fetch_affiliate_faq(primary.get("faq_url")),
            )

            source_counts = {
                "reddit": len(reddit_posts),
                "mse": len(mse_threads),
                "paa": len(paa_questions),
                "affiliate_faq": 1 if affiliate_faq.get("available") else 0,
            }

            # At least one source should return data
            total_sources = sum(1 for v in source_counts.values() if v > 0)
            if total_sources == 0:
                self.log.warning("No buyer psychology sources returned data", run_id=run_id)

            # ── Assemble sources dict ─────────────────────────────────
            raw_sources = {
                "reddit": reddit_posts,
                "mse": mse_threads,
                "paa": paa_questions,
                "affiliate_faq": affiliate_faq,
            }

            # ── Cache in Redis (1h TTL) ───────────────────────────────
            cache_key = await services.buyer.cache_sources(
                run_id=run_id,
                sources=raw_sources,
                ttl_seconds=3600,
            )

            output = {
                "source_counts": source_counts,
                "total_sources_with_data": total_sources,
                "cache_key": cache_key,
            }

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True, output=output,
            )

            return {
                "raw_sources_cache_key": cache_key,
                "current_stage": "stage6.data_fetcher",
            }

        except Exception as exc:
            self.log.error(f"DataFetcher failed: {exc}", run_id=run_id)
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "raw_sources_cache_key": None,
                "current_stage": "stage6.data_fetcher",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage6.data_fetcher", "error": str(exc),
                }],
            }