"""
Stage 3 — MarketContext

Pre-LLM: Parallel spot price + price trends + recent news fetch
Algorithmic: Market stance derivation (no LLM needed)
LLM: Market context synthesis for article writing
"""

from __future__ import annotations

import asyncio
import hashlib
import json

from nodes.base import (
    BaseAgent, JSONOutputMixin, ModelConfig, ModelProvider,
    FailureConfig, EventType, AgentStatus,
)
from prompts.registry import PromptRegistry
from services.llm_service import LLMTimeoutError, LLMRateLimitError, LLMProviderError


class MarketContext(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 2

    def __init__(self):
        super().__init__(
            agent_name="market_context",
            stage_name="research.stage3.market_context",
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                temperature=0.2,
                max_tokens=4096,
            ),
            failure_config=FailureConfig(
                failure_message="Market context synthesis failed.",
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        brief = state.get("brief") or {}
        topic = brief.get("topic") or state.get("selected_topic") or {}
        asset_class = topic.get("asset_class", "gold")
        geography = topic.get("geography", "uk")
        keyword = topic.get("target_keyword", asset_class)

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "model": self.model_config.model_id,
        })
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            from services import services

            # ── Parallel data fetch ───────────────────────────────────
            spot_price, trend_30d, trend_90d, news = await asyncio.gather(
                services.market.get_spot_price(asset_class, geography),
                services.market.get_price_trend(asset_class, days=30, geography=geography),
                services.market.get_price_trend(asset_class, days=90, geography=geography),
                services.market.get_recent_news(keyword, geography, days_back=30),
            )

            # ── Algorithmic stance derivation ─────────────────────────
            stance_data = services.market.derive_market_stance(
                price_data=spot_price,
                trend_30d=trend_30d,
                trend_90d=trend_90d,
                news_articles=news,
            )

            # ── LLM synthesis ─────────────────────────────────────────
            prompt = PromptRegistry.render("stage3_market_synthesis", {
                "ASSET_CLASS": asset_class,
                "GEOGRAPHY": geography,
                "TARGET_KEYWORD": keyword,
                "PRICE_JSON": json.dumps(
                    {**spot_price, "trend_30d": trend_30d, "trend_90d": trend_90d},
                    default=str,
                ),
                "NEWS_JSON": json.dumps(news[:10], default=str),
            })
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

            result = await self.call_llm(prompt, run_id, attempt=1)
            llm_output = result.output

            # Merge algorithmic stance with LLM synthesis
            market_context = {
                **llm_output,
                **stance_data,  # algorithmic stance overrides LLM stance
                "spot_price_gbp": spot_price.get("price_gbp"),
                "spot_price_usd": spot_price.get("price_usd"),
                "price_source": spot_price.get("source"),
            }

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "market_stance": market_context.get("market_stance"),
                "cost_usd": result.cost_usd,
            })
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True,
                output=market_context,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
                prompt_hash=prompt_hash,
            )

            return {
                "market_context": market_context,
                "current_stage": "stage3.market_context",
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
                "market_context": None,
                "current_stage": "stage3.market_context",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage3.market_context", "error": str(exc),
                }],
            }
        except Exception as exc:
            self.log.error(f"MarketContext failed: {exc}", run_id=run_id)
            await self._write_stage_record(run_id, status="failed", attempt=1, error=str(exc))
            return {
                "market_context": None,
                "current_stage": "stage3.market_context",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage3.market_context", "error": str(exc),
                }],
            }