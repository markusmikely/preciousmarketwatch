"""
Stage 9 — IntelligenceAggregation (NonLLM, Background Task)

Dispatched as asyncio.create_task from BundleAssembler — not a graph node.
Its failure does NOT block the research pipeline.

Three steps:
  1. Append this run's data to affiliate_intelligence_runs (append-only ledger)
  2. Rebuild affiliate_intelligence_summary (atomic upsert from all runs)
  3. Update WP affiliate intelligence page from the summary

Design: Every operation is atomic. No read-modify-write.
Single runs cannot dominate displayed data — frequency ranking requires
multiple appearances across runs.
"""

from __future__ import annotations

import logging

from nodes.base import BaseAgent, EventType

log = logging.getLogger("pmw.node.intelligence_aggregation")


class IntelligenceAggregation(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="intelligence_aggregation",
            stage_name="research.stage9.intelligence_aggregation",
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        topic = brief.get("topic") or state.get("selected_topic") or {}
        primary = brief.get("affiliate", {}).get("primary") or state.get("primary_affiliate") or {}
        market_context = state.get("market_context") or {}
        top_factors = state.get("top_factors") or {}
        buyer_psychology = state.get("buyer_psychology") or {}
        keyword_research = state.get("keyword_research") or {}

        affiliate_id = primary.get("id")
        if not affiliate_id:
            log.warning("No affiliate ID — skipping intelligence aggregation", extra={"run_id": run_id})
            return {"intelligence_write_result": {"skipped": True, "reason": "no_affiliate_id"}}

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "affiliate_id": affiliate_id,
            "affiliate_name": primary.get("name"),
        })
        await self._write_stage_record(run_id, status="running", attempt=1)

        results = {
            "run_appended": False,
            "summary_updated": False,
            "wp_page_updated": False,
            "errors": [],
        }

        try:
            from services import services

            # ── 1. Append this run to the raw ledger ──────────────────
            try:
                await services.affiliates.append_intelligence_run(
                    affiliate_id=affiliate_id,
                    run_id=run_id,
                    data={
                        "topic": topic,
                        "market": market_context,
                        "factors": top_factors,
                        "psychology": buyer_psychology,
                        "keywords": keyword_research,
                    },
                )
                results["run_appended"] = True
                log.info(f"Intelligence run appended for affiliate {affiliate_id}", extra={"run_id": run_id})
            except Exception as exc:
                results["errors"].append(f"Run append failed: {exc}")
                log.warning(f"Intelligence run append failed: {exc}", extra={"run_id": run_id})
                # Can't rebuild summary without the append
                await self._write_stage_record(
                    run_id, status="failed", attempt=1,
                    error=f"Run append failed: {exc}",
                    output=results,
                )
                return {"intelligence_write_result": results}

            # ── 2. Rebuild the aggregate summary ──────────────────────
            try:
                summary = await services.affiliates.rebuild_intelligence_summary(affiliate_id)
                results["summary_updated"] = True
                results["total_runs"] = summary.get("total_runs", 0)
                log.info(
                    f"Intelligence summary rebuilt: {summary.get('total_runs', 0)} total runs",
                    extra={"run_id": run_id, "affiliate_id": affiliate_id},
                )
            except Exception as exc:
                results["errors"].append(f"Summary rebuild failed: {exc}")
                log.warning(f"Summary rebuild failed: {exc}", extra={"run_id": run_id})
                summary = {}

            # ── 3. Update WP affiliate page ───────────────────────────
            if summary:
                try:
                    page_id = await services.pages.upsert_affiliate_intelligence_page(
                        affiliate=primary,
                        aggregated_data=summary,
                    )
                    if page_id:
                        results["wp_page_updated"] = True
                        results["wp_page_id"] = page_id
                        log.info(
                            f"WP affiliate page updated: ID={page_id}",
                            extra={"run_id": run_id},
                        )
                except Exception as exc:
                    results["errors"].append(f"WP page update failed: {exc}")
                    log.warning(f"WP page update failed: {exc}", extra={"run_id": run_id})

            # ── Write final stage record ──────────────────────────────
            status = "complete" if results["run_appended"] else "failed"
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, results)
            await self._write_stage_record(
                run_id, status=status, attempt=1,
                passed_threshold=results["run_appended"],
                output=results,
            )

            return {"intelligence_write_result": results}

        except Exception as exc:
            log.error(f"IntelligenceAggregation failed: {exc}", extra={"run_id": run_id})
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "intelligence_write_result": {
                    **results,
                    "errors": results["errors"] + [str(exc)],
                },
            }