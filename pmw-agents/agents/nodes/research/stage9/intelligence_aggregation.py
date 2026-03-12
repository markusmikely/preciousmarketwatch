from nodes.base import BaseAgent

class IntelligenceAggregation(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="intelligence_aggregation",
            stage_name="research.stage9.intelligence_aggregation",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data