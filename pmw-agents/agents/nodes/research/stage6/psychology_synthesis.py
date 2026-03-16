"""
Stage 6b — PsychologySynthesis

Loads cached sources from Redis (written by Stage 6a DataFetcher).
LLM synthesises buyer objections, motivations, verbatim phrases.
Affiliate responses sourced from affiliate FAQ text — not LLM-generated.
Compliance gate: flags sections with regulated-matter claims.

Validation: ≥3 objections, ≥3 motivations
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


class PsychologySynthesis(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 3

    def __init__(self):
        super().__init__(
            agent_name="psychology_synthesis",
            stage_name="research.stage6.psychology_synthesis",
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                temperature=0.3,
                max_tokens=4096,
            ),
            failure_config=FailureConfig(
                failure_message="Buyer psychology synthesis failed after max retries.",
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        topic = brief.get("topic") or state.get("selected_topic") or {}
        primary = brief.get("affiliate", {}).get("primary") or state.get("primary_affiliate") or {}
        cache_key = state.get("raw_sources_cache_key")

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "model": self.model_config.model_id,
        })
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            from services import services

            # ── Load cached sources from Redis ────────────────────────
            raw_sources = None
            if cache_key:
                raw_sources = await services.buyer.load_cached_sources(cache_key)

            if not raw_sources:
                self.log.warning(
                    "No cached sources found — Stage 6a may have failed",
                    run_id=run_id,
                )
                raw_sources = {"reddit": [], "mse": [], "paa": [], "affiliate_faq": {}}

            # ── Build prompt ──────────────────────────────────────────
            faq_data = raw_sources.get("affiliate_faq", {})
            prompt = PromptRegistry.render("stage6b_buyer_psychology", {
                "TOPIC_TITLE": topic.get("title", ""),
                "AFFILIATE_NAME": primary.get("name", ""),
                "FAQ_URL": primary.get("faq_url", ""),
                "REDDIT_JSON": json.dumps(raw_sources.get("reddit", []), default=str),
                "MSE_JSON": json.dumps(raw_sources.get("mse", []), default=str),
                "PAA_JSON": json.dumps(raw_sources.get("paa", []), default=str),
                "FAQ_TEXT": faq_data.get("content", "") if isinstance(faq_data, dict) else "",
            })
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

            # ── LLM call ──────────────────────────────────────────────
            result = await self.call_llm(prompt, run_id, attempt=1)
            output = result.output

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "objection_count": len(output.get("objections", [])),
                "motivation_count": len(output.get("motivations", [])),
                "compliance_review": output.get("any_section_requires_review", False),
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
                "buyer_psychology": output,
                "current_stage": "stage6.psychology_synthesis",
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
                "buyer_psychology": None,
                "current_stage": "stage6.psychology_synthesis",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage6.psychology_synthesis", "error": str(exc),
                }],
            }
        except Exception as exc:
            self.log.error(f"PsychologySynthesis failed: {exc}", run_id=run_id)
            await self._write_stage_record(run_id, status="failed", attempt=1, error=str(exc))
            return {
                "buyer_psychology": None,
                "current_stage": "stage6.psychology_synthesis",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage6.psychology_synthesis", "error": str(exc),
                }],
            }

    def validate_output(self, raw_output: str) -> dict:
        data = super().validate_output(raw_output)
        objections = data.get("objections", [])
        if len(objections) < 3:
            raise ValueError(f"Only {len(objections)} objections (need ≥3)")
        motivations = data.get("motivations", [])
        if len(motivations) < 3:
            raise ValueError(f"Only {len(motivations)} motivations (need ≥3)")
        return data