from nodes.base import BaseAgent

class ToolLoader(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="tool_loader",
            stage_name="research.stage7.tool_loader",
        )

    async def run(self, state: dict, run_id: int = 0) -> dict:
        return {}