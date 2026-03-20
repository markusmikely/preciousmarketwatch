# graphs/research_graph.py
"""
Research subgraph — multi-topic, clean architecture.

LangGraph handles 3 nodes only (phase lifecycle + checkpointing):
  1. load_data    — fetch all topics + all affiliates
  2. build_briefs — score every topic × affiliate pair, produce locked_briefs
  3. research     — run stages 2-8 concurrently per brief (plain async)

The inner per-brief processing (stages 2-8) uses asyncio.gather via
nodes/research/pipeline.py — no LangGraph overhead for that work.

This graph checkpoints between nodes, so if the process crashes after
load_data but before research, it resumes from build_briefs.
"""

import logging
from graphs.base_graph import BaseGraph
from graphs.phase_result import PhaseResult
from state.research_state import ResearchState

from nodes.research.stage1.topic_loader import TopicLoader
from nodes.research.stage1.affiliate_loader import AffiliateLoader
from nodes.research.stage1.brief_builder import BriefBuilder

log = logging.getLogger(__name__)


class ResearchGraph(BaseGraph):
    _state_schema = ResearchState

    @classmethod
    async def create(cls) -> "ResearchGraph":
        log.info("Creating ResearchGraph...")
        instance = await super().create()
        log.info("ResearchGraph created")
        return instance

    def _build_nodes(self):
        self._topic_loader = TopicLoader()
        self._affiliate_loader = AffiliateLoader()
        self._brief_builder = BriefBuilder()

        self.add_node("load_topics",      self._topic_loader.run)
        self.add_node("load_affiliates",  self._affiliate_loader.run)
        self.add_node("build_briefs",     self._brief_builder.run)
        self.add_node("research_briefs",  self._research_briefs_node)

    def _build_edges(self):
        self.add_edge(self.START, "load_topics")

        self.add_conditional_edges("load_topics", self._route_on_status,
            {"continue": "load_affiliates", "failed": self.END})

        self.add_conditional_edges("load_affiliates", self._route_on_status,
            {"continue": "build_briefs", "failed": self.END})

        self.add_conditional_edges("build_briefs", self._route_after_briefs,
            {"process": "research_briefs", "empty": self.END, "failed": self.END})

        self.add_edge("research_briefs", self.END)

    # ── The only complex node — delegates to plain async pipeline ─────

    async def _research_briefs_node(self, state: dict) -> dict:
        """
        Run stages 2-8 for all locked briefs using plain async concurrency.
        This is a LangGraph node that delegates to pipeline.research_briefs().
        """
        from nodes.research.pipeline import research_briefs

        locked = state.get("locked_briefs") or []
        if not locked:
            return {"completed_bundles": [], "status": "complete"}

        result = await research_briefs(
            locked_briefs=locked,
            run_id=state["run_id"],
            triggered_by=state.get("triggered_by", "scheduler"),
        )

        return {
            "completed_bundles": result["completed_bundles"],
            "errors":           state.get("errors", []) + result.get("errors", []),
            "model_usage":      state.get("model_usage", []) + result.get("model_usage", []),
            "status":           "complete",
            "current_stage":    "research_complete",
        }

    # ── Routers ───────────────────────────────────────────────────────

    @staticmethod
    def _route_on_status(state: dict) -> str:
        return "failed" if state.get("status") == "failed" else "continue"

    @staticmethod
    def _route_after_briefs(state: dict) -> str:
        if state.get("status") == "failed":
            return "failed"
        locked = state.get("locked_briefs") or []
        return "process" if locked else "empty"

    # ── Input / output translation ────────────────────────────────────

    def _make_input(self, input_data: dict) -> dict:
        return {
            "run_id":            input_data["run_id"],
            "triggered_by":      input_data.get("triggered_by", "scheduler"),
            "all_topics":        None,
            "all_affiliates":    None,
            "locked_briefs":     None,
            "review_items":      None,
            "completed_bundles": [],
            "current_stage":     "start",
            "status":            "running",
            "errors":            [],
            "model_usage":       [],
        }

    def _make_result(self, final_state: dict) -> PhaseResult:
        completed = final_state.get("completed_bundles") or []
        review = final_state.get("review_items") or []

        return PhaseResult(
            run_id   = final_state.get("run_id", 0),
            status   = final_state.get("status", "failed"),
            output   = completed if completed else None,
            cost_usd = self._sum_cost(final_state.get("model_usage", [])),
            errors   = final_state.get("errors", []),
            meta     = {
                "bundles_completed": len(completed),
                "topics_for_review": len(review),
                "topic_titles": [b.get("topic", {}).get("title", "") for b in completed],
            },
        )