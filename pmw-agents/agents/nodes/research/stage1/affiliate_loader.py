from agents.nodes.base import BaseAgent

class AffiliateLoader(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="affiliate_loader",
            stage_name="research.stage1.affiliate_loader",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data