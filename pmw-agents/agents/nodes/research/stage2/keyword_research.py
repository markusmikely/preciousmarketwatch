"""
Stage 2 — KeywordResearch (v2.2)

Pre-LLM: Fetch SERP data via services.serp.research_keyword()
LLM: Analyse SERP data, confirm intent, identify PAA opportunities
Validation: confidence ≥ 0.75, ≥5 secondary keywords, ≥3 PAA questions

Fixes from v2.1:
  - Removed imports of LLMTimeoutError/LLMRateLimitError/LLMProviderError
    (call_llm in base.py handles retries internally and re-raises on exhaustion)
  - call_llm returns LLMResult with .text (validated string), not .output
  - Graceful fallback when SERP service is unavailable or returns empty data
  - Exception handler writes "failed" stage record on all error paths
"""

from __future__ import annotations

import hashlib
import json
import logging

from nodes.base import (
    BaseAgent, JSONOutputMixin, ModelConfig, ModelProvider,
    FailureConfig, EventType,
)
from prompts.registry import PromptRegistry

log = logging.getLogger("pmw.node.keyword_research")


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
            # ── Pre-LLM: Fetch SERP data ──────────────────────────────
            serp_bundle = await self._fetch_serp_data(topic)

            # ── Build prompt ──────────────────────────────────────────
            prompt = PromptRegistry.render("stage2_keyword_serp", {
                "TARGET_KEYWORD": topic.get("target_keyword", ""),
                "INTENT_STAGE": topic.get("intent_stage", "consideration"),
                "ASSET_CLASS": topic.get("asset_class", ""),
                "GEOGRAPHY": topic.get("geography", "uk"),
                "SERP_JSON": json.dumps(serp_bundle, default=str),
            })
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

            # ── LLM call (base.py handles retries via call_llm) ───────
            result = await self.call_llm(prompt, run_id)

            # call_llm returns LLMResult. .text is the validated output
            # (validate_output ran inside call_llm). JSONOutputMixin
            # returns a dict from validate_output, but call_llm
            # json.dumps it back to string for LLMResult.text.
            if isinstance(result.text, str):
                output = json.loads(result.text)
            else:
                output = result.text

            # Merge SERP bundle data for downstream stages
            output["serp_bundle"] = serp_bundle

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "confidence": output.get("confidence"),
                "secondary_count": len(output.get("secondary_keywords", [])),
                "paa_count": len(output.get("paa_questions", [])),
                "cost_usd": result.cost_usd,
            })
            await self._write_stage_record(
                run_id, status="complete", attempt=result.attempts,
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

        except Exception as exc:
            self.log.error(f"KeywordResearch failed: {exc}")
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

    async def _fetch_serp_data(self, topic: dict) -> dict:
        """
        Fetch SERP data via services.serp.research_keyword().
        Returns a SerpBundle dict on success, or a minimal stub on failure
        so the LLM can still attempt analysis from the topic definition alone.
        """
        try:
            from services import services
            return await services.serp.research_keyword(
                keyword=topic.get("target_keyword", ""),
                geography=topic.get("geography", "uk"),
                include_keywords=topic.get("include_keywords", ""),
                exclude_keywords=topic.get("exclude_keywords", ""),
            )
        except Exception as exc:
            self.log.warning(f"SERP fetch failed, using stub: {exc}")
            return {
                "keyword": topic.get("target_keyword", ""),
                "geography": topic.get("geography", "uk"),
                "organic_results": [],
                "paa_questions": [],
                "related_searches": [],
                "top_formats": [],
                "content_gap_signals": [],
                "competitor_count": 0,
                "own_ranking": None,
                "serp_unavailable": True,
            }

    def validate_output(self, raw_output: str) -> dict:
        """
        Parse JSON and validate keyword research quality thresholds.
        Raises ValueError to trigger retry via call_llm.
        """
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