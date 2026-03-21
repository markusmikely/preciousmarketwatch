"""Stage 8a — ArcCoherence (model-config patched — uses judge model)"""

from __future__ import annotations

import hashlib
import json

from nodes.base import BaseAgent, JSONOutputMixin, FailureConfig, EventType
from config.models import get_judge_model
from prompts.registry import PromptRegistry


class ArcCoherence(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 1

    def __init__(self):
        super().__init__(
            agent_name="arc_coherence",
            stage_name="research.stage8.arc_coherence",
            model_config=get_judge_model(temperature=0.1, max_tokens=2048),
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

        await self._emit_event(EventType.STAGE_STARTED, run_id, {"model": self.model_config.model_id})
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

            result = await self.call_llm(prompt, run_id)
            output = json.loads(result.text) if isinstance(result.text, str) else result.text

            arc_coherent = output.get("arc_coherent", False)
            chain = output.get("chain_checks", {})
            checks_passed = sum(1 for v in chain.values() if v)
            arc_confidence = round(checks_passed / max(len(chain), 1), 2)
            output["arc_confidence"] = arc_confidence

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "arc_coherent": arc_coherent, "arc_confidence": arc_confidence,
                "cost_usd": result.cost_usd,
            })
            await self._write_stage_record(
                run_id, status="complete", attempt=1, passed_threshold=arc_coherent,
                score=arc_confidence, output=output,
                input_tokens=result.input_tokens, output_tokens=result.output_tokens,
                cost_usd=result.cost_usd, prompt_hash=prompt_hash,
            )

            state_update = {
                "arc_validation": output, "current_stage": "stage8.arc_coherence",
                "model_usage": state.get("model_usage", []) + [{
                    "stage": self.stage_name, "model": self.model_config.model_id,
                    "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
                    "cost_usd": result.cost_usd,
                }],
            }
            if not arc_coherent:
                state_update["hitl_required"] = True
                state_update["hitl_stage"] = "stage8.arc_coherence"
                state_update["hitl_reason"] = f"Arc coherence failed (confidence={arc_confidence})"

            return state_update

        except Exception as exc:
            self.log.error(f"ArcCoherence failed: {exc}")
            failure = await self._handle_failure(run_id, str(exc))
            return {
                "arc_validation": None, "current_stage": "stage8.arc_coherence",
                "hitl_required": failure.meta.get("human_in_the_loop", False),
                "status": "hitl" if failure.meta.get("human_in_the_loop") else "failed",
                "errors": state.get("errors", []) + [{"stage": "stage8.arc_coherence", "error": str(exc)}],
            }