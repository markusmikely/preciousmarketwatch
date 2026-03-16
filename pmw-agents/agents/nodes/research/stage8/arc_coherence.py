"""
Stage 8a — ArcCoherence

LLM: Validates that the complete research output tells a coherent
buying intent story: problem → market context → factors → affiliate solution → tools.

If arc is incoherent but recoverable → hitl_required=True
If arc confidence too low → hard failure

Depends on: barrier.stage8 (Stage 5 + Stage 7)
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


class ArcCoherence(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 1  # Arc check gets 2 total attempts — then HITL

    def __init__(self):
        super().__init__(
            agent_name="arc_coherence",
            stage_name="research.stage8.arc_coherence",
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                temperature=0.1,
                max_tokens=2048,
            ),
            failure_config=FailureConfig(
                failure_message="Arc coherence check failed.",
                human_in_the_loop=True,
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        keyword_research = state.get("keyword_research") or {}
        market_context = state.get("market_context") or {}
        top_factors = state.get("top_factors") or {}
        competitor_analysis = state.get("competitor_analysis") or {}
        buyer_psychology = state.get("buyer_psychology") or {}
        tool_mapping = state.get("tool_mapping") or {}

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "model": self.model_config.model_id,
        })
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            prompt = PromptRegistry.render("stage8a_arc_coherence", {
                "BRIEF_JSON": json.dumps(brief, default=str),
                "KEYWORD_JSON": json.dumps(keyword_research, default=str),
                "MARKET_JSON": json.dumps(market_context, default=str),
                "FACTORS_JSON": json.dumps(top_factors, default=str),
                "COMPETITOR_JSON": json.dumps(competitor_analysis, default=str),
                "PSYCHOLOGY_JSON": json.dumps(buyer_psychology, default=str),
                "TOOLS_JSON": json.dumps(tool_mapping, default=str),
            })
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

            result = await self.call_llm(prompt, run_id, attempt=1)
            output = result.output

            arc_coherent = output.get("arc_coherent", False)
            proceed = output.get("proceed", False)

            # Derive arc_confidence from chain_checks
            chain = output.get("chain_checks", {})
            checks_passed = sum(1 for v in chain.values() if v)
            checks_total = max(len(chain), 1)
            arc_confidence = round(checks_passed / checks_total, 2)

            # Enrich output with computed confidence
            output["arc_confidence"] = arc_confidence

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "arc_coherent": arc_coherent,
                "arc_confidence": arc_confidence,
                "cost_usd": result.cost_usd,
            })
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=arc_coherent,
                score=arc_confidence,
                output=output,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
                prompt_hash=prompt_hash,
            )

            # Route decision is made by research_graph.route_after_arc()
            # We just set the state fields it reads
            state_update = {
                "arc_validation": output,
                "current_stage": "stage8.arc_coherence",
                "model_usage": state.get("model_usage", []) + [{
                    "stage": self.stage_name,
                    "model": self.model_config.model_id,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "cost_usd": result.cost_usd,
                }],
            }

            # If arc is incoherent, set HITL fields for route_after_arc()
            if not arc_coherent:
                state_update["hitl_required"] = True
                state_update["hitl_stage"] = "stage8.arc_coherence"
                state_update["hitl_reason"] = (
                    f"Arc coherence check failed (confidence={arc_confidence}). "
                    f"Issues: {json.dumps(output.get('issues', []))}"
                )

            return state_update

        except (LLMTimeoutError, LLMRateLimitError, LLMProviderError, ValueError) as exc:
            failure = await self._handle_failure(run_id, str(exc))
            return {
                "arc_validation": None,
                "current_stage": "stage8.arc_coherence",
                "hitl_required": failure.meta.get("human_in_the_loop", False),
                "hitl_stage": "stage8.arc_coherence",
                "hitl_reason": str(exc),
                "status": "hitl" if failure.meta.get("human_in_the_loop") else "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage8.arc_coherence", "error": str(exc),
                }],
            }
        except Exception as exc:
            self.log.error(f"ArcCoherence failed: {exc}", run_id=run_id)
            await self._write_stage_record(run_id, status="failed", attempt=1, error=str(exc))
            return {
                "arc_validation": None,
                "current_stage": "stage8.arc_coherence",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage8.arc_coherence", "error": str(exc),
                }],
            }