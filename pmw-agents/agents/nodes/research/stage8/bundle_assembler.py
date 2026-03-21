"""
Stage 8b — BundleAssembler (v3.0 — content-type aware)

Assembles research state into the final research_bundle dict.
Validates required sections based on content_type:
  affiliate       → all sections required
  authority       → only keyword_research + competitor_analysis
  market_commentary → only keyword_research + market_context

Releases topic lock and dispatches Stage 9 (background).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from nodes.base import BaseAgent, EventType

# Required sections by content type
REQUIRED_BY_TYPE = {
    "affiliate": ["brief", "keyword_research", "market_context", "top_factors",
                   "competitor_analysis", "buyer_psychology", "tool_mapping", "arc_validation"],
    "authority": ["brief", "keyword_research", "competitor_analysis"],
    "market_commentary": ["brief", "keyword_research", "market_context"],
}


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
        content_type = topic.get("content_type", "affiliate")

        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage(run_id, "running")

        try:
            # Validate required sections for this content type
            required = REQUIRED_BY_TYPE.get(content_type, REQUIRED_BY_TYPE["affiliate"])
            missing = [s for s in required if not state.get(s)]

            if missing:
                error_msg = f"Bundle incomplete for {content_type} — missing: {missing}"
                self.log.error(error_msg)
                await self._write_stage(run_id, "failed", error=error_msg)
                return {
                    "research_bundle": None, "status": "failed",
                    "errors": state.get("errors", []) + [{"stage": self.stage_name, "error": error_msg}],
                }

            # Assemble — include whatever sections are available
            bundle = {
                "run_id": run_id,
                "content_type": content_type,
                "assembled_at": datetime.now(timezone.utc).isoformat(),
                "brief": brief,
                "topic": topic,
                "primary_affiliate": brief.get("affiliate", {}).get("primary"),
                "secondary_affiliate": brief.get("affiliate", {}).get("secondary"),
                "reader": brief.get("reader", {}),
                # Research outputs (None if stage didn't run)
                "keyword_research": state.get("keyword_research"),
                "confirmed_intent": (state.get("keyword_research") or {}).get("confirmed_intent"),
                "paa_questions": (state.get("keyword_research") or {}).get("paa_questions", []),
                "market_context": state.get("market_context"),
                "market_stance": (state.get("market_context") or {}).get("market_stance"),
                "emotional_trigger": (state.get("market_context") or {}).get("emotional_trigger"),
                "top_factors": state.get("top_factors"),
                "competitor_analysis": state.get("competitor_analysis"),
                "buyer_psychology": state.get("buyer_psychology"),
                "tool_mapping": state.get("tool_mapping"),
                "arc_validation": state.get("arc_validation"),
                # Cost
                "total_cost_usd": sum(u.get("cost_usd", 0) for u in state.get("model_usage", [])),
                "model_usage": state.get("model_usage", []),
            }

            output = {
                "content_type": content_type,
                "sections_present": [k for k, v in bundle.items() if v is not None and k not in
                                     ("run_id", "assembled_at", "total_cost_usd", "model_usage", "content_type")],
                "total_cost_usd": bundle["total_cost_usd"],
            }

            await self._write_stage(run_id, "complete", passed=True, output=output)
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)

            # Release lock + dispatch Stage 9 (background, non-blocking)
            asyncio.create_task(self._release_lock(topic.get("id"), run_id))
            if content_type == "affiliate":
                asyncio.create_task(self._dispatch_intelligence(state, run_id))

            return {"research_bundle": bundle, "status": "complete"}

        except Exception as exc:
            self.log.error(f"BundleAssembler failed: {exc}")
            await self._write_stage(run_id, "failed", error=str(exc))
            return {
                "research_bundle": None, "status": "failed",
                "errors": state.get("errors", []) + [{"stage": self.stage_name, "error": str(exc)}],
            }

    async def _release_lock(self, topic_wp_id, run_id):
        if not topic_wp_id: return
        try:
            from services import services
            await services.workflows.release_topic_lock(topic_wp_id=topic_wp_id, run_id=run_id, success=True)
            asyncio.create_task(services.topics.mark_topic_complete(topic_wp_id, run_id))
        except Exception as exc:
            self.log.warning(f"Lock release failed: {exc}")

    async def _dispatch_intelligence(self, state, run_id):
        try:
            from nodes.research.stage9.intelligence_aggregation import IntelligenceAggregation
            await IntelligenceAggregation().run(state)
        except Exception as exc:
            self.log.warning(f"Intelligence aggregation failed (non-blocking): {exc}")