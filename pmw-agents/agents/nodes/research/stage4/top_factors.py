from nodes.base import BaseAgent

class TopFactors(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="top_factors",
            stage_name="research.stage4.top_factors",
        )

    async def run(self, state: dict, run_id: int = 0) -> dict:
        return state