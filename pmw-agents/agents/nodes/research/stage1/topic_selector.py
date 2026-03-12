from nodes.base import BaseAgent

class TopicSelector(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="topic_selector",
            stage_name="research.stage1.topic_selector",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data