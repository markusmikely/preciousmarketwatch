"""
Stage 1c — BriefBuilder

For each topic in all_topics:
  1. Score all affiliates → pick best primary + secondary
  2. If fit_score >= threshold → lock topic + LLM coherence check
  3. If coherence >= threshold → brief passes → locked_briefs
  4. Otherwise → saved to topic_briefs table (dashboard HITL review)
"""

from __future__ import annotations

import asyncio
import json
import logging
from decimal import Decimal

from nodes.base import BaseAgent, JSONOutputMixin, ModelConfig, ModelProvider
from config.settings import settings
from prompts.registry import PromptRegistry

log = logging.getLogger("pmw.node.brief_builder")


def _clean(obj):
    """Deep-convert Decimals to floats for JSON serialisation."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return obj


class BriefBuilder(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 2

    def __init__(self):
        super().__init__(
            agent_name="brief_builder",
            stage_name="research.stage1.brief_builder",
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                temperature=0.2,
                max_tokens=2048,
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        all_topics = state.get("all_topics") or []
        all_affiliates = state.get("all_affiliates") or []
        await self._write_stage(run_id, "running")

        if not all_topics:
            return self._done(state, [], [], "No topics to process")
        if not all_affiliates:
            return self._done(state, [], [], "No affiliates available")

        from services import services

        locked = []
        review = []
        usage = []

        for topic in all_topics:
            title = topic.get("title", "Untitled")
            try:
                result = await self._process_one(topic, all_affiliates, run_id, services)

                if result["status"] == "passed":
                    locked.append(result["brief"])
                    if result.get("usage"):
                        usage.append(result["usage"])
                    self.log.info(f"✓ '{title}' passed")
                elif result["status"] == "skipped":
                    self.log.info(f"⊘ '{title}' skipped (locked)")
                else:
                    review.append(result.get("review_item", {}))
                    self.log.info(f"⚠ '{title}' needs_review: {result.get('reason', '?')}")

                if result["status"] in ("passed", "needs_review"):
                    await self._save_to_db(run_id, result)

            except Exception as exc:
                self.log.error(f"✗ '{title}': {exc}")
                review.append({"topic": topic, "reason": str(exc), "status": "needs_review"})

        output = {"locked": len(locked), "review": len(review), "total": len(all_topics)}
        await self._write_stage(run_id, "complete", passed=len(locked) > 0, output=output,
                                cost_usd=sum(u.get("cost_usd", 0) for u in usage))

        return {
            "locked_briefs": locked, "review_items": review, "completed_bundles": [],
            "current_stage": self.stage_name, "status": "complete",
            "model_usage": state.get("model_usage", []) + usage,
        }

    async def _process_one(self, topic, affiliates, run_id, services):
        tid = topic.get("id")

        # 1. Score
        scored = await services.affiliates.score_affiliates_for_topic(topic, affiliates)
        if not scored:
            return {"status": "needs_review", "topic": topic,
                    "reason": f"No affiliate above {settings.AFFILIATE_FIT_THRESHOLD}",
                    "review_item": {"topic": topic, "reason": "No qualifying affiliate"}}

        primary = _clean(scored[0])
        secondary = _clean(scored[1]) if len(scored) > 1 else None

        # 2. Lock
        acquired = await services.workflows.acquire_topic_lock(topic_wp_id=tid, run_id=run_id)
        if not acquired:
            return {"status": "skipped", "topic": topic}

        # 3. LLM coherence
        try:
            prompt = self._coherence_prompt(topic, primary)
            result = await self.call_llm(prompt, run_id)
            enrichments = json.loads(result.text) if isinstance(result.text, str) else result.text
            coherence = float(enrichments.get("coherence_score", 0))
        except Exception as exc:
            await services.workflows.release_topic_lock(topic_wp_id=tid, run_id=run_id, success=False)
            return {"status": "needs_review", "topic": topic,
                    "reason": f"LLM failed: {exc}",
                    "review_item": {"topic": topic, "reason": str(exc)}}

        # 4. Threshold check
        if coherence < settings.COHERENCE_THRESHOLD:
            await services.workflows.release_topic_lock(topic_wp_id=tid, run_id=run_id, success=False)
            return {"status": "needs_review", "topic": topic,
                    "reason": f"Coherence {coherence:.2f} < {settings.COHERENCE_THRESHOLD}",
                    "coherence": coherence, "fit_score": float(primary.get("fit_score", 0)),
                    "affiliate_name": primary.get("name", ""),
                    "review_item": {"topic": topic, "coherence": coherence}}

        # 5. Passed — build brief
        brief = {
            "topic": topic,
            "affiliate": {"primary": primary, "secondary": secondary},
            "meta": {
                "run_id": run_id,
                "coherence_score": coherence,
                "validation_passed": True,
                "warnings": [i for i in enrichments.get("issues", []) if i.get("severity") == "warning"],
            },
            "reader": {
                "profile": enrichments.get("enriched_reader_profile", ""),
                "moment": enrichments.get("enriched_reader_moment", ""),
                "article_angle": enrichments.get("suggested_article_angle", ""),
            },
        }

        # Mark running in Postgres only (no WP write)
        asyncio.create_task(services.topics.mark_topic_running(tid, run_id))

        return {
            "status": "passed", "brief": brief, "topic": topic,
            "coherence": coherence,
            "fit_score": float(primary.get("fit_score", 0)),
            "affiliate_name": primary.get("name", ""),
            "affiliate_id": primary.get("id"),
            "secondary_id": secondary.get("id") if secondary else None,
            "usage": {
                "stage": f"{self.stage_name}.{tid}",
                "model": self.model_config.model_id,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "cost_usd": result.cost_usd,
            },
        }

    def _coherence_prompt(self, topic, affiliate):
        return PromptRegistry.render("stage1_5_brief_validation", {
            "TOPIC_TITLE": topic.get("title", ""),
            "TARGET_KEYWORD": topic.get("target_keyword", ""),
            "ASSET_CLASS": topic.get("asset_class", ""),
            "PRODUCT_TYPE": topic.get("product_type", ""),
            "GEOGRAPHY": topic.get("geography", "uk"),
            "IS_BUY_SIDE": str(topic.get("is_buy_side", False)),
            "INTENT_STAGE": topic.get("intent_stage", "consideration"),
            "AFFILIATE_NAME": affiliate.get("name", ""),
            "AFFILIATE_KEY": affiliate.get("partner_key", affiliate.get("name", "").lower().replace(" ", "-")),
            "AFFILIATE_VALUE_PROP": affiliate.get("value_prop", ""),
            "AFFILIATE_GEO": affiliate.get("geo_focus", ""),
            "COMMISSION_TYPE": affiliate.get("commission_type", ""),
        })

    def validate_output(self, raw_output):
        data = super().validate_output(raw_output)
        if "coherence_score" not in data:
            raise ValueError("Missing 'coherence_score'")
        return data

    async def _save_to_db(self, run_id, result):
        try:
            from infrastructure import get_infrastructure
            infra = get_infrastructure()
            topic = result.get("topic", {})
            brief = _clean(result.get("brief"))
            review = _clean(result.get("review_item", {}))

            await infra.postgres.execute(
                """
                INSERT INTO topic_briefs (run_id, topic_wp_id, topic_title,
                    affiliate_id, affiliate_name, secondary_affiliate_id,
                    fit_score, coherence_score, status, review_reason,
                    brief_json, score_breakdown_json)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12::jsonb)
                """,
                run_id, topic.get("id"), topic.get("title", ""),
                result.get("affiliate_id"), result.get("affiliate_name"),
                result.get("secondary_id"),
                float(result.get("fit_score") or 0),
                float(result.get("coherence") or 0),
                result["status"], result.get("reason"),
                json.dumps(brief) if brief else None,
                json.dumps(review) if review else None,
            )
        except Exception as exc:
            self.log.warning(f"topic_briefs write failed: {exc}")

    def _done(self, state, locked, review, msg):
        return {
            "locked_briefs": locked, "review_items": review, "completed_bundles": [],
            "current_stage": self.stage_name, "status": "complete",
            "errors": state.get("errors", []) + ([{"stage": self.stage_name, "error": msg}] if not locked else []),
            "model_usage": state.get("model_usage", []),
        }