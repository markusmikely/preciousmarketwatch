"""
Stage 7a — ToolLoader (NonLLM)

Loads available PMW tools filtered by topic's asset class and geography.
Transient data — available_tools is passed to Stage 7b but not stored
in ResearchState permanently (it's a static registry lookup).

Depends on: barrier.stage7 (Stage 2 + Stage 4 + Stage 6b)
"""

from __future__ import annotations

from nodes.base import BaseAgent, EventType


class ToolLoader(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="tool_loader",
            stage_name="research.stage7.tool_loader",
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        topic = brief.get("topic") or state.get("selected_topic") or {}

        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            from services import services

            tools = await services.tools.get_available_tools(
                asset_class=topic.get("asset_class", ""),
                geography=topic.get("geography", "uk"),
            )

            output = {
                "tool_count": len(tools),
                "tool_names": [t["name"] for t in tools],
            }

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True, output=output,
            )

            # available_tools is transient — used by Stage 7b ToolMapping
            # but not stored as a permanent ResearchState field
            return {
                "available_tools": tools,
                "current_stage": "stage7.tool_loader",
            }

        except Exception as exc:
            self.log.error(f"ToolLoader failed: {exc}", run_id=run_id)
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "available_tools": [],
                "current_stage": "stage7.tool_loader",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage7.tool_loader", "error": str(exc),
                }],
            }