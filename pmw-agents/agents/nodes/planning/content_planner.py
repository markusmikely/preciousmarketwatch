"""
Planning Phase — ContentPlanner

Routes to the correct planning template based on content_type:
  - affiliate → plan_affiliate.json
  - authority → plan_authority.json
  - market_commentary → plan_commentary.json

The planner receives the research bundle (which may be partial for
non-affiliate content) and produces a structured article plan.

The plan is the contract between research and generation — the generator
follows the plan's sections, word counts, and CTA placements exactly.

Input (from state):  research_bundle (dict)
Output (to state):   content_plan (dict)
"""

from __future__ import annotations

import json
import logging

from nodes.base import (
    BaseAgent, JSONOutputMixin, ModelConfig, ModelProvider,
    EventType, FailureConfig,
)
from prompts.registry import PromptRegistry

log = logging.getLogger("pmw.node.content_planner")


class ContentPlanner(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 2

    def __init__(self):
        super().__init__(
            agent_name="content_planner",
            stage_name="planning.content_planner",
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                temperature=0.3,
                max_tokens=4096,
            ),
            failure_config=FailureConfig(
                failure_message="Content planning failed.",
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        bundle = state.get("research_bundle") or {}
        brief = bundle.get("brief") or {}
        topic = brief.get("topic") or bundle.get("topic") or {}
        content_type = topic.get("content_type", "affiliate")

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "content_type": content_type,
            "model": self.model_config.model_id,
        })
        await self._write_stage(run_id, "running")

        try:
            # Fetch internal link targets for the planner
            internal_links = await self._get_internal_links(topic)

            # Build the prompt using the correct template
            prompt = self._build_prompt(content_type, bundle, topic, internal_links)

            result = await self.call_llm(prompt, run_id)

            plan = json.loads(result.text) if isinstance(result.text, str) else result.text

            # Enrich plan with metadata
            plan["content_type"] = content_type
            plan["run_id"] = run_id
            plan["topic_wp_id"] = topic.get("id")

            section_count = len(plan.get("sections", []))
            total_words = sum(s.get("word_count", 0) for s in plan.get("sections", []))

            await self._write_stage(
                run_id, "complete", passed=True,
                output={
                    "sections": section_count,
                    "target_words": total_words,
                    "content_type": content_type,
                },
                in_tok=result.input_tokens,
                out_tok=result.output_tokens,
                cost_usd=result.cost_usd,
            )
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "sections": section_count,
                "target_words": total_words,
                "cost_usd": result.cost_usd,
            })

            return {
                "content_plan": plan,
                "status": "complete",
                "model_usage": state.get("model_usage", []) + [{
                    "stage": self.stage_name,
                    "model": self.model_config.model_id,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "cost_usd": result.cost_usd,
                }],
            }

        except Exception as exc:
            self.log.error(f"ContentPlanner failed: {exc}")
            await self._write_stage(run_id, "failed", error=str(exc))
            await self._emit_event(EventType.STAGE_FAILED, run_id, {"error": str(exc)})
            return {
                "content_plan": None,
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": self.stage_name, "error": str(exc),
                }],
            }

    def _build_prompt(
        self,
        content_type: str,
        bundle: dict,
        topic: dict,
        internal_links: list[dict],
    ) -> str:
        """Build the planning prompt from the correct template + research data."""
        brief = bundle.get("brief") or {}
        affiliate = brief.get("affiliate", {})
        primary = affiliate.get("primary") or {}
        secondary = affiliate.get("secondary") or {}
        market = bundle.get("market_context") or {}
        factors = bundle.get("top_factors") or {}
        competitor = bundle.get("competitor_analysis") or {}
        keyword = bundle.get("keyword_research") or {}

        # Build concise summaries (not full JSON dumps — save tokens)
        market_summary = self._summarise_market(market)
        factors_summary = self._summarise_factors(factors)
        competitor_gaps = self._summarise_competitor_gaps(competitor)
        paa_questions = self._format_paa(keyword)
        news_summary = self._summarise_news(market)
        links_text = self._format_internal_links(internal_links)

        template_key = {
            "affiliate": "plan_affiliate",
            "authority": "plan_authority",
            "market_commentary": "plan_commentary",
        }.get(content_type, "plan_affiliate")

        variables = {
            "TOPIC_TITLE": topic.get("title", ""),
            "TARGET_KEYWORD": topic.get("target_keyword", ""),
            "ASSET_CLASS": topic.get("asset_class", ""),
            "GEOGRAPHY": topic.get("geography", "uk"),
            "INTENT_STAGE": topic.get("intent_stage", "consideration"),
            "AFFILIATE_NAME": primary.get("name", "N/A"),
            "AFFILIATE_VALUE_PROP": (primary.get("value_prop") or "")[:200],
            "AFFILIATE_URL": primary.get("url", ""),
            "SECONDARY_AFFILIATE_NAME": secondary.get("name", "N/A"),
            "SECONDARY_AFFILIATE_URL": secondary.get("url", ""),
            "MARKET_SUMMARY": market_summary,
            "NEWS_SUMMARY": news_summary,
            "FACTORS_SUMMARY": factors_summary,
            "COMPETITOR_GAPS": competitor_gaps,
            "PAA_QUESTIONS": paa_questions,
            "INTERNAL_LINKS": links_text,
        }

        return PromptRegistry.render(template_key, variables)

    # ── Research data summarisers (keep prompts token-efficient) ───────

    @staticmethod
    def _summarise_market(market: dict) -> str:
        if not market:
            return "No market data available."
        parts = []
        if market.get("spot_price_gbp"):
            parts.append(f"Spot price: £{market['spot_price_gbp']}")
        if market.get("price_trend_pct_30d"):
            parts.append(f"30d trend: {market['price_trend_pct_30d']:+.1f}%")
        if market.get("market_stance"):
            parts.append(f"Stance: {market['market_stance']}")
        if market.get("stance_rationale"):
            parts.append(market["stance_rationale"])
        return " | ".join(parts) if parts else "Market data unavailable."

    @staticmethod
    def _summarise_factors(factors: dict) -> str:
        if not factors:
            return "No factors data."
        items = factors.get("factors", [])
        if not items:
            return "No factors identified."
        lines = []
        for f in items[:5]:
            lines.append(
                f"- {f.get('factor', '?')}: {f.get('current_data', 'N/A')}"
            )
        return "\n".join(lines)

    @staticmethod
    def _summarise_competitor_gaps(competitor: dict) -> str:
        if not competitor:
            return "No competitor data."
        gap = competitor.get("overall_gap_analysis", "")
        diff = competitor.get("recommended_differentiator", "")
        parts = []
        if gap:
            parts.append(f"Gap: {gap}")
        if diff:
            parts.append(f"Differentiator: {diff}")
        comps = competitor.get("competitors", [])
        for c in comps[:3]:
            weaknesses = c.get("weaknesses", [])
            if weaknesses:
                parts.append(f"- {c.get('title', '?')}: weak on {', '.join(weaknesses[:2])}")
        return "\n".join(parts) if parts else "No competitor gaps identified."

    @staticmethod
    def _format_paa(keyword: dict) -> str:
        paa = keyword.get("paa_questions", [])
        if not paa:
            return "No PAA questions found."
        return "\n".join(f"- {q}" for q in paa[:8])

    @staticmethod
    def _summarise_news(market: dict) -> str:
        news = market.get("news_summary", [])
        if not news:
            return "No recent news."
        lines = []
        for n in news[:5]:
            headline = n.get("headline", n.get("title", ""))
            source = n.get("source", "")
            lines.append(f"- {headline} ({source})")
        return "\n".join(lines)

    @staticmethod
    def _format_internal_links(links: list[dict]) -> str:
        if not links:
            return "No existing articles to link to yet."
        lines = []
        for link in links[:10]:
            lines.append(f"- {link.get('title', '?')} → {link.get('url', '/')}")
        return "\n".join(lines)

    async def _get_internal_links(self, topic: dict) -> list[dict]:
        """Fetch existing posts to serve as internal link targets."""
        try:
            from services import services
            return await services.publishing.get_internal_link_targets(
                asset_class=topic.get("asset_class", ""),
                limit=15,
            )
        except Exception as exc:
            self.log.debug(f"Internal link fetch failed: {exc}")
            return []

    def validate_output(self, raw_output: str) -> dict:
        data = super().validate_output(raw_output)
        sections = data.get("sections", [])
        if not sections:
            raise ValueError("Plan has no sections")
        if not data.get("title"):
            raise ValueError("Plan missing title")
        return data