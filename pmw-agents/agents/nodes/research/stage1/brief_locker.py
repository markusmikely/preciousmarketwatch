from nodes.base import BaseAgent

class BriefLocker(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="brief_locker",
            stage_name="research.stage1.brief_locker",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data