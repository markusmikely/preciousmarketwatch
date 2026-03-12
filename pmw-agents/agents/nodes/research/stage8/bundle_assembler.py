from nodes.base import BaseAgent

class BundleAssembler(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="bundle_assembler",
            stage_name="research.stage8.bundle_assembler",
        )

    def run(self, input_data: dict, run_id: int) -> dict:
        return input_data