from nodes.base import BaseAgent

class CompetitorAnalysis(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="competitor_analysis",
            stage_name="research.stage5.competitor_analysis",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data