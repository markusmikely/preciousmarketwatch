from nodes.base import BaseAgent

class MarketContext(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="market_context",
            stage_name="research.stage3.market_context",
        )

    async def run(self, state: dict, run_id: int = 0) -> dict:
        return {}