from nodes.base import BaseAgent

class CompetitorAnalysis(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="competitor_analysis",
            stage_name="research.stage5.competitor_analysis",
        )

    async def run(self, state: dict, run_id: int = 0) -> dict
        return {}