from agents.nodes.base import BaseAgent

class MarketContext(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="market_context",
            stage_name="research.stage3.market_context",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data