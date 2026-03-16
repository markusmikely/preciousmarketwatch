"""
Stage 7b — ToolMapping

LLM: Map available PMW tools to article sections with rationale.
Validation: ≥1 tool selected (unless no_tool_fits=true)
Depends on: Stage 7a (available_tools in state)
"""


from __future__ import annotations

import hashlib
import json

from nodes.base import (
    BaseAgent, JSONOutputMixin, ModelConfig, ModelProvider,
    FailureConfig, EventType,
)
from prompts.registry import PromptRegistry
from services.llm_service import LLMTimeoutError, LLMRateLimitError, LLMProviderError


class ToolMapping(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 2

    def __init__(self):
        super().__init__(
            agent_name="tool_mapping",
            stage_name="research.stage7.tool_mapping",
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                temperature=0.2,
                max_tokens=2048,
            ),
            failure_config=FailureConfig(
                failure_message="Tool mapping failed after max retries.",
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        topic = brief.get("topic") or state.get("selected_topic") or {}
        available_tools = state.get("available_tools") or []
        keyword_research = state.get("keyword_research") or {}
        top_factors = state.get("top_factors") or {}
        buyer_psychology = state.get("buyer_psychology") or {}

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "model": self.model_config.model_id,
            "available_tools": len(available_tools),
        })
        await self._write_stage_record(run_id, status="running", attempt=1)

        # If no tools available, skip LLM call entirely
        if not available_tools:
            output = {
                "selected_tools": [],
                "no_tool_fits": True,
                "no_tool_reason": "No tools available for this asset class/geography",
            }
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True, output=output,
            )
            return {
                "tool_mapping": output,
                "current_stage": "stage7.tool_mapping",
            }

        try:
            prompt = PromptRegistry.render("stage7_tool_mapping", {
                "TOPIC_TITLE": topic.get("title", ""),
                "TARGET_KEYWORD": topic.get("target_keyword", ""),
                "ASSET_CLASS": topic.get("asset_class", ""),
                "INTENT_STAGE": topic.get("intent_stage", "consideration"),
                "TOOLS_JSON": json.dumps(available_tools, default=str),
                "BUYER_PSYCHOLOGY_JSON": json.dumps(buyer_psychology, default=str),
                "TOP_FACTORS_JSON": json.dumps(top_factors, default=str),
                "KEYWORD_RESEARCH_JSON": json.dumps(keyword_research, default=str),
            })
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

            result = await self.call_llm(prompt, run_id, attempt=1)
            output = result.output

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "tools_selected": len(output.get("selected_tools", [])),
                "cost_usd": result.cost_usd,
            })
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True, output=output,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
                prompt_hash=prompt_hash,
            )

            return {
                "tool_mapping": output,
                "current_stage": "stage7.tool_mapping",
                "model_usage": state.get("model_usage", []) + [{
                    "stage": self.stage_name,
                    "model": self.model_config.model_id,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "cost_usd": result.cost_usd,
                }],
            }

        except (LLMTimeoutError, LLMRateLimitError, LLMProviderError, ValueError) as exc:
            await self._handle_failure(run_id, str(exc))
            return {
                "tool_mapping": None,
                "current_stage": "stage7.tool_mapping",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage7.tool_mapping", "error": str(exc),
                }],
            }
        except Exception as exc:
            self.log.error(f"ToolMapping failed: {exc}", run_id=run_id)
            await self._write_stage_record(run_id, status="failed", attempt=1, error=str(exc))
            return {
                "tool_mapping": None,
                "current_stage": "stage7.tool_mapping",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage7.tool_mapping", "error": str(exc),
                }],
            }

    def validate_output(self, raw_output: str) -> dict:
        data = super().validate_output(raw_output)
        if not data.get("no_tool_fits", False):
            tools = data.get("selected_tools", [])
            if len(tools) < 1:
                raise ValueError("Expected ≥1 selected tool (or no_tool_fits=true)")
            for t in tools:
                if not t.get("selection_rationale"):
                    raise ValueError(f"Tool '{t.get('tool_name')}' missing selection_rationale")
        return data