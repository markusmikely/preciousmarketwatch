from nodes.base import BaseAgent

class BriefLocker(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="brief_locker",
            stage_name="research.stage1.brief_locker",
        )
        
    async def run(self, state: dict, run_id: int = 0) -> dict:
        
        state  = self.preprocess(state)
        
        try:
            await self._lock_topic(state['selected_topic'], run_id)
            # Step 2 — draft brief assembly (pure Python, no service needed)
            draft_brief = self._assemble_draft_brief(selected_topic, primary_affiliate, secondary_affiliate)
            # Step 3 — LLM coherence check (via base agent _run_with_retries)
            
            result = await self._coherence_check(draft_brief, run_id)
            # Step 4 — write WP display status (fire and forget)
            self._write_task(selected_topic["id"], run_id)
            
        except (LLMTimeoutError, LLMRateLimitError, LLMProviderError, ValueError) as exc:
            return await self._handle_failure(run_id, str(exc))

        await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
            "cost_usd": result.cost_usd,
        })
        await self._write_stage_record(run_id, status="complete", attempt=1,
            passed_threshold=True, output=result.output,
            input_tokens=result.input_tokens, output_tokens=result.output_tokens,
            cost_usd=result.cost_usd, prompt_hash=prompt_hash)

        return self.postprocess(result)

    def _write_task(self, topic_id, run_id):
        asyncio.create_task(
            topic_service.mark_topic_running(selected_topic["id"], run_id)
        )

    async def _coherence_check(self, draft_brief, run_id):
        prompt      = self.build_prompt(draft_brief)
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "model": self.model_config.model_id,
        })
        await self._write_stage_record(run_id, status="running", attempt=1,
                                        prompt_hash=prompt_hash)
        
        result = await self.call_llm(prompt, run_id, attempt=1)

        return result

    async def _lock_topic(self, selected_topic, run_id):
        # Step 1 — atomic lock
        from services.workflow_service import WorkflowService
        workflow_service = WorkflowService()

        acquired = await workflow_service.acquire_topic_lock(
            topic_wp_id=selected_topic["id"], run_id=run_id
        )
        if not acquired:
            raise TopicLockConflictError(...)

    def _assemble_draft_brief(self, selected_topic, primary_affiliate, secondary_affiliate) -> dict:
        return {
            "topic": selected_topic,
            "affiliate": {
                "primary": primary_affiliate,
                "secondary": secondary_affiliate
            },
            "meta": {
                "run_id": 1,
                "coherence_score": 0,
                "validation_passed": 'bool',
                "warnings":' list[str]',
            },
            "reader": {
                "profile": 'str',              # enriched by LLM
                "moment": 'str',               # enriched by LLM
                "article_angle": 'str',        # enriched by LLM
            }
        }