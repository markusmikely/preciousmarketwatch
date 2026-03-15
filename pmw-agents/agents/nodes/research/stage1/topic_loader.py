from nodes.base import BaseAgent

class TopicLoader(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="topic_loader",
            stage_name="research.stage1.topic_loader",
        )

    async def run(self, state: dict, run_id: int = 0) -> dict:
        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)
        try:
            
            topics   = await topic_service.get_eligible_topics()         # WP fetch + Postgres lock check
            candidate_topics = await topic_service.filter_locked_topics(topics)  # remove currently running
            output = {
                candidate_topics: candidate_topics
            }
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {})
            await self._write_stage_record(run_id, status="complete", attempt=1,
                passed_threshold=True, output=output)
            return AgentResult(status=AgentStatus.SUCCESS, output=output, attempts=1)
        except Exception as exc:
            return await self._handle_failure(run_id, str(exc))
