"""
Stage 8b — BundleAssembler (NonLLM)

Assembles all research state fields into the final research_bundle dict.
Validates all required sections are present.
Releases the Postgres topic lock (fire-and-forget).
Dispatches Stage 9 IntelligenceAggregation as a background task.

This is the last node before END in the research graph.
The research_bundle is the ONLY thing that escapes to the parent graph
via _make_result().

Depends on: Stage 8a (arc_coherent=True)
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from nodes.base import BaseAgent, EventType


# Required sections in the research bundle
REQUIRED_SECTIONS = [
    "brief",
    "keyword_research",
    "market_context",
    "top_factors",
    "competitor_analysis",
    "buyer_psychology",
    "tool_mapping",
    "arc_validation",
]


class BundleAssembler(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="bundle_assembler",
            stage_name="research.stage8.bundle_assembler",
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        topic = brief.get("topic") or state.get("selected_topic") or {}

        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            # ── Validate all required sections ────────────────────────
            missing = []
            for section in REQUIRED_SECTIONS:
                if not state.get(section):
                    missing.append(section)

            if missing:
                error_msg = f"Research bundle incomplete — missing sections: {missing}"
                self.log.error(error_msg, run_id=run_id)
                await self._write_stage_record(
                    run_id, status="failed", attempt=1, error=error_msg,
                )
                return {
                    "research_bundle": None,
                    "current_stage": "stage8.bundle_assembler",
                    "hitl_required": True,
                    "hitl_stage": "stage8.bundle_assembler",
                    "hitl_reason": error_msg,
                    "status": "hitl",
                    "errors": state.get("errors", []) + [{
                        "stage": "stage8.bundle_assembler", "error": error_msg,
                    }],
                }

            # ── Assemble the research bundle ──────────────────────────
            research_bundle = {
                "run_id": run_id,
                "assembled_at": datetime.now(timezone.utc).isoformat(),

                # Stage 1 — Brief
                "brief": brief,
                "topic": topic,
                "primary_affiliate": brief.get("affiliate", {}).get("primary") or state.get("primary_affiliate"),
                "secondary_affiliate": brief.get("affiliate", {}).get("secondary") or state.get("secondary_affiliate"),
                "reader": brief.get("reader", {}),

                # Stage 2 — Keyword & Intent
                "keyword_research": state["keyword_research"],
                "confirmed_intent": state["keyword_research"].get("confirmed_intent"),
                "paa_questions": state["keyword_research"].get("paa_questions", []),

                # Stage 3 — Market Context
                "market_context": state["market_context"],
                "market_stance": state["market_context"].get("market_stance"),
                "emotional_trigger": state["market_context"].get("emotional_trigger"),

                # Stage 4 — Top Factors
                "top_factors": state["top_factors"],

                # Stage 5 — Competitor Analysis
                "competitor_analysis": state["competitor_analysis"],

                # Stage 6 — Buyer Psychology
                "buyer_psychology": state["buyer_psychology"],
                "compliance_review_required": state["buyer_psychology"].get(
                    "any_section_requires_review", False
                ),

                # Stage 7 — Tool Mapping
                "tool_mapping": state["tool_mapping"],

                # Stage 8a — Arc Validation
                "arc_validation": state["arc_validation"],

                # Metadata
                "total_cost_usd": sum(
                    u.get("cost_usd", 0) for u in state.get("model_usage", [])
                ),
                "model_usage": state.get("model_usage", []),
            }

            output = {
                "sections": list(research_bundle.keys()),
                "total_cost_usd": research_bundle["total_cost_usd"],
                "compliance_review_required": research_bundle["compliance_review_required"],
            }

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True, output=output,
            )

            # ── Release topic lock (fire-and-forget) ──────────────────
            asyncio.create_task(
                self._release_lock(topic.get("id"), run_id)
            )

            # ── Dispatch Stage 9 Intelligence Aggregation (background) ─
            asyncio.create_task(
                self._dispatch_intelligence_aggregation(state, run_id)
            )

            return {
                "research_bundle": research_bundle,
                "current_stage": "stage8.bundle_assembler",
                "status": "complete",
            }

        except Exception as exc:
            self.log.error(f"BundleAssembler failed: {exc}", run_id=run_id)
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "research_bundle": None,
                "current_stage": "stage8.bundle_assembler",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage8.bundle_assembler", "error": str(exc),
                }],
            }

    async def _release_lock(self, topic_wp_id: int | None, run_id: int) -> None:
        """Release Postgres topic lock and update WP display status."""
        if not topic_wp_id:
            return
        try:
            from services import services
            await services.workflows.release_topic_lock(
                topic_wp_id=topic_wp_id,
                run_id=run_id,
                success=True,
            )
            # Fire-and-forget WP display status
            asyncio.create_task(
                services.topics.mark_topic_complete(topic_wp_id, run_id)
            )
        except Exception as exc:
            self.log.warning(
                f"Lock release failed (non-blocking): {exc}",
                run_id=run_id,
            )

    async def _dispatch_intelligence_aggregation(self, state: dict, run_id: int) -> None:
        """
        Dispatch Stage 9 as a background task.
        Stage 9 is non-blocking — its failure doesn't affect the pipeline result.
        """
        try:
            from nodes.research.stage9.intelligence_aggregation import IntelligenceAggregation
            aggregator = IntelligenceAggregation()
            await aggregator.run(state)
        except Exception as exc:
            self.log.warning(
                f"Intelligence aggregation failed (non-blocking): {exc}",
                run_id=run_id,
            )