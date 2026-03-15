from nodes.base import BaseAgent

class AffiliateLoader(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="affiliate_loader",
            stage_name="research.stage1.affiliate_loader",
        )

    async def run(self, state: dict, run_id: int = 0) -> dict:
        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)
        try:
            
            affiliates = await affiliate_service.get_active_affiliates()
            output = {
                candidate_affiliates: affiliates
            }
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {})
            await self._write_stage_record(run_id, status="complete", attempt=1,
                passed_threshold=True, output=output)
            return AgentResult(status=AgentStatus.SUCCESS, output=output, attempts=1)
        except Exception as exc:
            return await self._handle_failure(run_id, str(exc))