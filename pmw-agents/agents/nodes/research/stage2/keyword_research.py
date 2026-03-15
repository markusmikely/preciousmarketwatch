from nodes.base import BaseAgent

class KeywordResearch(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="keyword_research",
            stage_name="research.stage2.keyword_research",
        )

    async def run(self, state: dict, run_id: int = 0) -> dict:
        return {}