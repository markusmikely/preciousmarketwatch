from nodes.base import BaseAgent

class KeywordResearch(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="keyword_research",
            stage_name="research.stage2.keyword_research",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data