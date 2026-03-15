from nodes.base import BaseAgent

class TopicSelector(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="topic_selector",
            stage_name="research.stage1.topic_selector",
        )

    async def run(self, state: dict, run_id: int = 0) -> dict
        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)
        try:
            
            selected = await topic_service.select_next_topic(state['candidate_topics'])
            output = {
                'selected_topic': selected
            }
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {})
            await self._write_stage_record(run_id, status="complete", attempt=1,
                passed_threshold=True, output=output)
            return AgentResult(status=AgentStatus.SUCCESS, output=output, attempts=1)
        except Exception as exc:
            return await self._handle_failure(run_id, str(exc))