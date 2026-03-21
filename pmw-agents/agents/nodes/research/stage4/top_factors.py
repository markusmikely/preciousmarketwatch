"""
Stage 4 — TopFactors

LLM: Identify the 5 most important buyer decision factors with current data points.
Depends on: Stage 2 (keyword_research) + Stage 3 (market_context)
Validation: exactly 5 factors, each with data points and affiliate connection.
"""

from __future__ import annotations

import hashlib
import json

from nodes.base import (
    BaseAgent, JSONOutputMixin, ModelConfig, ModelProvider,
    FailureConfig, EventType, AgentStatus,
)
from prompts.registry import PromptRegistry
from services.llm_service import LLMTimeoutError, LLMRateLimitError, LLMProviderError


class TopFactors(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 3

    def __init__(self):
        super().__init__(
            agent_name="top_factors",
            stage_name="research.stage4.top_factors",
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                temperature=0.3,
                max_tokens=4096,
            ),
            failure_config=FailureConfig(
                failure_message="Top factors analysis failed after max retries.",
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        topic = brief.get("topic") or state.get("selected_topic") or {}
        primary = brief.get("affiliate", {}).get("primary") or state.get("primary_affiliate") or {}
        keyword_research = state.get("keyword_research") or {}
        market_context = state.get("market_context") or {}

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "model": self.model_config.model_id,
        })
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            prompt = PromptRegistry.render("stage4_top_factors", {
                "TOPIC_TITLE": topic.get("title", ""),
                "TARGET_KEYWORD": topic.get("target_keyword", ""),
                "ASSET_CLASS": topic.get("asset_class", ""),
                "INTENT_STAGE": topic.get("intent_stage", "consideration"),
                "AFFILIATE_NAME": primary.get("name", ""),
                "AFFILIATE_VALUE_PROP": primary.get("value_prop", ""),
                "MARKET_CONTEXT_JSON": json.dumps(market_context, default=str),
                "KEYWORD_RESEARCH_JSON": json.dumps(keyword_research, default=str),
            })
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

            result = await self.call_llm(prompt, run_id, attempt=1)
            output = result.output

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "factor_count": len(output.get("factors", [])),
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
                "top_factors": output,
                "current_stage": "stage4.top_factors",
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
                "top_factors": None,
                "current_stage": "stage4.top_factors",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage4.top_factors", "error": str(exc),
                }],
            }
        except Exception as exc:
            self.log.error(f"TopFactors failed: {exc}", run_id=run_id)
            await self._write_stage_record(run_id, status="failed", attempt=1, error=str(exc))
            return {
                "top_factors": None,
                "current_stage": "stage4.top_factors",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage4.top_factors", "error": str(exc),
                }],
            }

    def validate_output(self, raw_output: str) -> dict:
        data = super().validate_output(raw_output)
        factors = data.get("factors", [])
        if len(factors) != 5:
            raise ValueError(f"Expected exactly 5 factors, got {len(factors)}")
        for i, f in enumerate(factors):
            if not f.get("current_data"):
                raise ValueError(f"Factor {i+1} missing 'current_data' field")
        return data