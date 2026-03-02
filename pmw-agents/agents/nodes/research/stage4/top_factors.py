from agents.nodes.base import BaseAgent

class TopFactors(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="top_factors",
            stage_name="research.stage4.top_factors",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data