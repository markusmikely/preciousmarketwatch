"""Stage 5 — CompetitorAnalysis (model-config patched)"""

from __future__ import annotations

import hashlib
import json

from nodes.base import BaseAgent, JSONOutputMixin, FailureConfig, EventType
from config.models import get_pipeline_model
from prompts.registry import PromptRegistry


class CompetitorAnalysis(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 3

    def __init__(self):
        super().__init__(
            agent_name="competitor_analysis",
            stage_name="research.stage5.competitor_analysis",
            model_config=get_pipeline_model(temperature=0.2, max_tokens=4096),
            failure_config=FailureConfig(failure_message="Competitor analysis failed."),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        topic = brief.get("topic") or state.get("selected_topic") or {}
        primary = brief.get("affiliate", {}).get("primary") or state.get("primary_affiliate") or {}

        await self._emit_event(EventType.STAGE_STARTED, run_id, {"model": self.model_config.model_id})
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            from services import services

            competitor_urls = await services.serp.get_competitor_urls(
                keyword=topic.get("target_keyword", ""), geography=topic.get("geography", "uk"), limit=5,
            )
            urls = [c.get("link", c.get("url", "")) for c in competitor_urls if c.get("link") or c.get("url")]
            pages = await services.competitors.fetch_multiple(urls[:5], max_concurrent=3)

            competitor_data = []
            for url_info, page in zip(competitor_urls, pages):
                competitor_data.append({
                    "url": page.get("url", url_info.get("link", "")),
                    "title": page.get("title", url_info.get("title", "")),
                    "snippet": url_info.get("snippet", ""),
                    "position": url_info.get("position"),
                    "word_count": page.get("word_count", 0),
                    "text_preview": page.get("text", "")[:2000],
                    "available": page.get("available", False),
                })

            prompt = PromptRegistry.render("stage5_competitor_analysis", {
                "TARGET_KEYWORD": topic.get("target_keyword", ""),
                "ASSET_CLASS": topic.get("asset_class", ""),
                "AFFILIATE_NAME": primary.get("name", ""),
                "COMPETITOR_JSON": json.dumps(competitor_data, default=str),
            })
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

            result = await self.call_llm(prompt, run_id)
            output = json.loads(result.text) if isinstance(result.text, str) else result.text

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {"cost_usd": result.cost_usd})
            await self._write_stage_record(
                run_id, status="complete", attempt=1, passed_threshold=True,
                output=output, input_tokens=result.input_tokens,
                output_tokens=result.output_tokens, cost_usd=result.cost_usd, prompt_hash=prompt_hash,
            )
            return {
                "competitor_analysis": output, "current_stage": "stage5.competitor_analysis",
                "model_usage": state.get("model_usage", []) + [{
                    "stage": self.stage_name, "model": self.model_config.model_id,
                    "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
                    "cost_usd": result.cost_usd,
                }],
            }
        except Exception as exc:
            self.log.error(f"CompetitorAnalysis failed: {exc}")
            await self._write_stage_record(run_id, status="failed", attempt=1, error=str(exc))
            return {"competitor_analysis": None, "current_stage": "stage5.competitor_analysis", "status": "failed",
                    "errors": state.get("errors", []) + [{"stage": "stage5.competitor_analysis", "error": str(exc)}]}

    def validate_output(self, raw_output: str) -> dict:
        data = super().validate_output(raw_output)
        if len(data.get("competitors", [])) < 3:
            raise ValueError(f"Only {len(data.get('competitors', []))} competitors (need ≥3)")
        return data