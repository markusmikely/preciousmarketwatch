from agents.nodes.base import BaseAgent

class ToolMapping(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="tool_mapping",
            stage_name="research.stage7.tool_mapping",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data