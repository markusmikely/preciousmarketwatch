"""
Stage 2 — KeywordResearch

Pre-LLM: Fetch SERP data via services.serp.research_keyword()
LLM: Analyse SERP data, confirm intent, identify PAA opportunities
Validation: confidence ≥ 0.75, ≥5 secondary keywords, ≥3 PAA questions
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


class KeywordResearch(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 3

    def __init__(self):
        super().__init__(
            agent_name="keyword_research",
            stage_name="research.stage2.keyword_research",
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                temperature=0.2,
                max_tokens=4096,
            ),
            failure_config=FailureConfig(
                failure_message="Keyword research failed after max retries.",
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        topic = brief.get("topic") or state.get("selected_topic") or {}

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "model": self.model_config.model_id,
        })
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            from services import services

            # ── Pre-LLM: Fetch SERP data ──────────────────────────────
            serp_bundle = await services.serp.research_keyword(
                keyword=topic.get("target_keyword", ""),
                geography=topic.get("geography", "uk"),
                include_keywords=topic.get("include_keywords", ""),
                exclude_keywords=topic.get("exclude_keywords", ""),
            )

            # ── Build prompt ──────────────────────────────────────────
            prompt = PromptRegistry.render("stage2_keyword_serp", {
                "TARGET_KEYWORD": topic.get("target_keyword", ""),
                "INTENT_STAGE": topic.get("intent_stage", "consideration"),
                "ASSET_CLASS": topic.get("asset_class", ""),
                "GEOGRAPHY": topic.get("geography", "uk"),
                "SERP_JSON": json.dumps(serp_bundle, default=str),
            })
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

            # ── LLM call ──────────────────────────────────────────────
            result = await self.call_llm(prompt, run_id, attempt=1)
            output = result.output  # validated JSON

            # Merge SERP bundle data into the output for downstream stages
            output["serp_bundle"] = serp_bundle

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "confidence": output.get("confidence"),
                "cost_usd": result.cost_usd,
            })
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True,
                score=output.get("confidence"),
                output=output,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
                prompt_hash=prompt_hash,
            )

            return {
                "keyword_research": output,
                "current_stage": "stage2.keyword_research",
                "model_usage": state.get("model_usage", []) + [{
                    "stage": self.stage_name,
                    "model": self.model_config.model_id,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "cost_usd": result.cost_usd,
                }],
            }

        except (LLMTimeoutError, LLMRateLimitError, LLMProviderError, ValueError) as exc:
            failure = await self._handle_failure(run_id, str(exc))
            return {
                "keyword_research": None,
                "current_stage": "stage2.keyword_research",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage2.keyword_research",
                    "error": str(exc),
                }],
            }
        except Exception as exc:
            self.log.error(f"KeywordResearch failed: {exc}", run_id=run_id)
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "keyword_research": None,
                "current_stage": "stage2.keyword_research",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage2.keyword_research",
                    "error": str(exc),
                }],
            }

    def validate_output(self, raw_output: str) -> dict:
        data = super().validate_output(raw_output)
        confidence = data.get("confidence", 0)
        if confidence < 0.75:
            raise ValueError(f"Confidence {confidence} below 0.75 threshold")
        secondary = data.get("secondary_keywords", [])
        if len(secondary) < 5:
            raise ValueError(f"Only {len(secondary)} secondary keywords (need ≥5)")
        paa = data.get("paa_questions", [])
        if len(paa) < 3:
            raise ValueError(f"Only {len(paa)} PAA questions (need ≥3)")
        return data