# graphs/generation_graph.py
import logging
from graphs.base_graph import BaseGraph
from graphs.phase_result import PhaseResult

log = logging.getLogger(__name__)

class GenerationGraph(BaseGraph):
    _state_schema = dict  # replace with GenerationState when designed

    @classmethod
    async def create(cls) -> "GenerationGraph":
        """Create GenerationGraph instance with proper connection pool."""
        log.info("Creating GenerationGraph...")
        instance = await super().create()
        log.info("GenerationGraph created successfully")
        return instance

    def _build_nodes(self):
        self.add_node("generation_stub", self._generation_stub)

    def _build_edges(self):
        self.add_edge(self.START, "generation_stub")
        self.add_edge("generation_stub", self.END)

    def _make_input(self, input_data: dict) -> dict:
        return {
            "workflow_id":     input_data["workflow_id"],
            "research_bundle": input_data.get("research_bundle"),
            "content_plan":    input_data.get("content_plan"),
            "status":          "running",
            "errors":          [],
            "model_usage":     [],
        }

    def _make_result(self, final_state: dict) -> PhaseResult:
        return PhaseResult(
            workflow_id = final_state.get("workflow_id"),
            status   = final_state.get("status", "failed"),
            output   = final_state.get("generation_result"),
            cost_usd = self._sum_cost(final_state.get("model_usage", [])),
            errors   = final_state.get("errors", []),
        )

    async def _generation_stub(self, state: dict) -> dict:
        log.info(f"[STUB] Generation | workflow={state.get('workflow_id')}")
        return {
            "generation_result": None, 
            "status": "complete",
            "errors": [], 
            "model_usage": []
        }