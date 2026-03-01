# graphs/research_graph.py

import logging
from graphs.base_graph import BaseGraph
from graphs.phase_result import PhaseResult
from state.research_state import ResearchState  # internal — never seen by parent

log = logging.getLogger(__name__)


class ResearchGraph(BaseGraph):
    """
    Phase 1 — Research subgraph.

    Internal state: ResearchState (20+ fields, never seen by MainGraph)
    Public contract: run({"workflow_id", "triggered_by"}) -> PhaseResult

    _make_input  : two parent fields in -> full ResearchState out
    _make_result : full ResearchState in -> PhaseResult out (only boundary)
    """

    _state_schema = ResearchState

    @classmethod
    async def create(cls) -> "ResearchGraph":
        """Create ResearchGraph instance with proper connection pool."""
        log.info("Creating ResearchGraph...")
        instance = await super().create()
        log.info("ResearchGraph created successfully")
        return instance

    def _build_nodes(self):
        # TODAY: stub. Replace with full 9-stage research implementation.
        self.add_node("research_stub", self._research_stub)

    def _build_edges(self):
        self.add_edge(self.START, "research_stub")
        self.add_edge("research_stub", self.END)

    def _make_input(self, input_data: dict) -> dict:
        """
        The parent passes only workflow_id and triggered_by.
        Everything else is initialised here as ResearchState defaults.
        """
        return {
            "workflow_id":         input_data["workflow_id"],
            "triggered_by":        input_data.get("triggered_by", "scheduler"),
            "run_id":              None,
            "candidate_topics":    None,
            "selected_topic":      None,
            "topic_lock_acquired": None,
            "brief":               None,
            "keyword_research":    None,
            "market_context":      None,
            "competitor_analysis": None,
            "top_factors":         None,
            "buyer_psychology":    None,
            "tool_mapping":        None,
            "arc_validation":      None,
            "research_bundle":     None,
            "current_stage":       "start",
            "status":              "running",
            "errors":              [],
            "retry_counts":        {},
            "model_usage":         [],
        }

    def _make_result(self, final_state: dict) -> PhaseResult:
        """
        Only research_bundle and a small meta dict escape this method.
        All 20+ ResearchState fields are discarded here.
        """
        selected_topic = final_state.get("selected_topic") or {}
        return PhaseResult(
            status   = final_state.get("status", "failed"),
            output   = final_state.get("research_bundle"),
            cost_usd = self._sum_cost(final_state.get("model_usage", [])),
            errors   = final_state.get("errors", []),
            meta     = {
                "topic_wp_id": selected_topic.get("id"),
                "topic_title": selected_topic.get("title"),
            },
        )

    async def _research_stub(self, state: dict) -> dict:
        log.info(f"[STUB] Research | workflow={state.get('workflow_id')}")
        return {
            "research_bundle": {
                "topic":            {"id": 1, "title": "Stub Topic"},
                "prompt_variables": {},
            },
            "selected_topic": {"id": 1, "title": "Stub Topic"},
            "status":         "complete",
            "errors":         [],
            "model_usage":    [],
        }