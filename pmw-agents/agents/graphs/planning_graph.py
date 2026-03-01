# graphs/planning_graph.py
import logging
from graphs.base_graph import BaseGraph
from graphs.phase_result import PhaseResult

log = logging.getLogger(__name__)

class PlanningGraph(BaseGraph):
    _state_schema = dict  # replace with PlanningState when designed

    @classmethod
    async def create(cls) -> "PlanningGraph":
        """Create PlanningGraph instance with proper connection pool."""
        log.info("Creating PlanningGraph...")
        instance = await super().create()
        log.info("PlanningGraph created successfully")
        return instance

    def _build_nodes(self):
        self.add_node("planning_stub", self._planning_stub)

    def _build_edges(self):
        self.add_edge(self.START, "planning_stub")
        self.add_edge("planning_stub", self.END)

    def _make_input(self, input_data: dict) -> dict:
        return {
            "run_id":          input_data["run_id"],
            "research_bundle": input_data.get("research_bundle"),
            "status":          "running",
            "errors":          [],
            "model_usage":     [],
        }

    def _make_result(self, final_state: dict) -> PhaseResult:
        return PhaseResult(
            run_id   = final_state.get("run_id", 0),
            status   = final_state.get("status", "failed"),
            output   = final_state.get("content_plan"),
            cost_usd = self._sum_cost(final_state.get("model_usage", [])),
            errors   = final_state.get("errors", []),
        )

    async def _planning_stub(self, state: dict) -> dict:
        log.info(f"[STUB] Planning | run_id={state.get('run_id')}")
        return {
            "run_id": state.get("run_id"),
            "content_plan": {},  # Stub: empty dict so result.succeeded is True 
            "status": "complete",
            "errors": [], 
            "model_usage": []
        }