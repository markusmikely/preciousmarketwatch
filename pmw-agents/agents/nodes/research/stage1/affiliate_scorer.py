from nodes.base import BaseAgent

class AffiliateScorer(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="affiliate_scorer",
            stage_name="research.stage1.affiliate_scorer",
        )

    async def run(self, input_data, run_id):
        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)
        try:
            
            scored   = await affiliate_service.score_affiliates_for_topic(input_data['selected_topic'], input_data['candidate_affiliates'])
            primary  = scored[0]
            secondary = scored[1] if len(scored) > 1 else None
            output = {
                scored_affiliates: scored,
                primary_affiliate: primary,
                secondary_affiliate: secondary
            }
            
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {})
            await self._write_stage_record(run_id, status="complete", attempt=1,
                passed_threshold=True, output=output)
            return AgentResult(status=AgentStatus.SUCCESS, output=output, attempts=1)
        except Exception as exc:
            return await self._handle_failure(run_id, str(exc))