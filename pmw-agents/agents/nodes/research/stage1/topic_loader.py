from agents.nodes.base import BaseAgent

class TopicLoader(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="topic_loader",
            stage_name="research.stage1.topic_loader",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data