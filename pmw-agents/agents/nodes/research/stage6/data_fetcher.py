from agents.nodes.base import BaseAgent

class DataFetcher(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="data_fetcher",
            stage_name="research.stage6.data_fetcher",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data