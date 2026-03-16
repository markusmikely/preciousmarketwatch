"""
Stage 1.2 — TopicSelector

Selects the best topic from candidate_topics using priority sort,
24h cooldown, and run count tiebreaking.
"""

from __future__ import annotations

from nodes.base import BaseAgent, EventType


class TopicSelector(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="topic_selector",
            stage_name="research.stage1.topic_selector",
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        candidates = state.get("candidate_topics") or []

        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            from services import services

            selected = await services.topics.select_next_topic(candidates)

            if not selected:
                error_msg = "No topic could be selected from candidates"
                await self._write_stage_record(
                    run_id, status="failed", attempt=1, error=error_msg,
                )
                return {
                    "selected_topic": None,
                    "current_stage": "stage1.topic_selector",
                    "status": "failed",
                    "errors": state.get("errors", []) + [{
                        "stage": "stage1.topic_selector",
                        "error": error_msg,
                    }],
                }

            output = {
                "topic_id": selected["id"],
                "title": selected.get("title", ""),
                "priority": selected.get("priority"),
            }
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True, output=output,
            )

            return {
                "selected_topic": selected,
                "current_stage": "stage1.topic_selector",
            }

        except Exception as exc:
            self.log.error(f"TopicSelector failed: {exc}", run_id=run_id)
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "selected_topic": None,
                "current_stage": "stage1.topic_selector",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage1.topic_selector",
                    "error": str(exc),
                }],
            }