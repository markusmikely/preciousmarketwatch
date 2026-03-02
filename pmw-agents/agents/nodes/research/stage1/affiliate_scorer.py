from agents.nodes.base import BaseAgent

class AffiliateScorer(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="affiliate_scorer",
            stage_name="research.stage1.affiliate_scorer",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data