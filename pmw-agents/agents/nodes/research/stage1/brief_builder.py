"""
Stage 1c — BriefBuilder

For each topic in all_topics:
  1. Score all affiliates → pick best primary + secondary
  2. If fit_score >= threshold → lock topic + LLM coherence check
  3. If coherence >= threshold → brief passes → locked_briefs
  4. Otherwise → saved to topic_briefs table (dashboard HITL review)

Single-topic failure never halts the run. The output is a list.

Changes from previous version:
  - Exponential backoff on 529/overloaded errors (up to 3 retries)
  - 1-second delay between topics to avoid API rate pressure
  - all_qualifying affiliates attached to each brief (not just primary/secondary)
  - Decimal→float conversion for JSON serialisation safety
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

# Retry config for 529/overloaded errors
MAX_LLM_RETRIES = 3
INITIAL_BACKOFF_SECS = 2.0
BACKOFF_MULTIPLIER = 2.0

# Delay between topic processing to avoid API rate pressure
INTER_TOPIC_DELAY_SECS = 1.0


def _clean(obj):
    """Deep-convert Decimal values to float for JSON safety."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
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

        for i, topic in enumerate(all_topics):
            tid = topic.get("id")
            title = topic.get("title", "Untitled")

            # ── Rate-limit: pause between topics to avoid API pressure ──
            if i > 0:
                await asyncio.sleep(INTER_TOPIC_DELAY_SECS)

            try:
                result = await self._process_one_topic(
                    topic, all_affiliates, run_id, services,
                )

                if result["status"] == "passed":
                    locked.append(result["brief"])
                    if result.get("usage"):
                        usage.append(result["usage"])
                    self.log.info(
                        f"✓ '{title}' → passed "
                        f"(affiliate={result['affiliate_name']}, "
                        f"fit={result['fit_score']:.2f}, "
                        f"coherence={result['coherence']:.2f}, "
                        f"qualifying={result.get('qualifying_count', '?')}/{result.get('total_scored', '?')})"
                    )
                elif result["status"] == "skipped":
                    self.log.info(f"⊘ '{title}' → skipped (already locked)")
                else:
                    review.append(result["review_item"])
                    self.log.info(f"⚠ '{title}' → needs_review ({result['reason']})")

                # Save to topic_briefs table (both passed and review)
                if result["status"] in ("passed", "needs_review"):
                    await self._save_to_db(run_id, result)

            except Exception as exc:
                self.log.error(f"✗ '{title}' → error: {exc}")
                review.append({"topic": topic, "reason": str(exc), "status": "needs_review"})

        # Write stage record
        output = {"locked": len(locked), "review": len(review), "total": len(all_topics)}
        await self._write_stage(run_id, "complete", passed=len(locked) > 0, output=output,
                                cost_usd=sum(u.get("cost_usd", 0) for u in usage))
        await self._emit("stage.complete", run_id, output)

        return {
            "locked_briefs": locked,
            "review_items": review,
            "completed_bundles": [],
            "current_stage": self.stage_name,
            "model_usage": state.get("model_usage", []) + usage,
            "status": "complete" if not state.get("status") == "failed" else "failed",
        }

    # ── Per-topic processing ──────────────────────────────────────────────

    async def _process_one_topic(
        self, topic: dict, affiliates: list[dict], run_id: int, services,
    ) -> dict:
        """Process a single topic. Returns a result dict with status + data."""
        tid = topic.get("id")

        # 1. Score affiliates (pure Python — no LLM call)
        scored = await services.affiliates.score_affiliates_for_topic(topic, affiliates)

        if not scored:
            return {
                "status": "needs_review",
                "reason": f"No affiliate scored above {settings.AFFILIATE_FIT_THRESHOLD}",
                "review_item": {"topic": topic, "reason": "No qualifying affiliate", "scores": []},
                "topic": topic,
            }

        # All qualifying affiliates (above threshold), ranked by score
        qualifying = _clean(scored)  # Decimal safety
        primary = qualifying[0]
        secondary = qualifying[1] if len(qualifying) > 1 else None

        self.log.info(
            f"Topic '{topic.get('title', '?')}': "
            f"{len(qualifying)}/{len(affiliates)} affiliates qualify "
            f"(threshold={settings.AFFILIATE_FIT_THRESHOLD})"
        )

        # 2. Acquire topic lock
        acquired = await services.workflows.acquire_topic_lock(topic_wp_id=tid, run_id=run_id)
        if not acquired:
            return {"status": "skipped", "topic": topic}

        # 3. LLM coherence check — WITH exponential backoff on 529
        try:
            enrichments, llm_usage = await self._coherence_check_with_backoff(
                topic, primary, run_id,
            )
            coherence = float(enrichments.get("coherence_score", 0))
        except Exception as exc:
            # LLM failed after all retries — release lock, add to review
            await services.workflows.release_topic_lock(topic_wp_id=tid, run_id=run_id, success=False)
            return {
                "status": "needs_review",
                "reason": f"LLM coherence check failed: {exc}",
                "review_item": {"topic": topic, "reason": str(exc), "affiliate": primary["name"]},
                "topic": topic,
            }

        # 4. Check coherence threshold
        if coherence < settings.COHERENCE_THRESHOLD:
            await services.workflows.release_topic_lock(topic_wp_id=tid, run_id=run_id, success=False)
            return {
                "status": "needs_review",
                "reason": f"Coherence {coherence:.2f} < {settings.COHERENCE_THRESHOLD}",
                "review_item": {"topic": topic, "coherence": coherence, "affiliate": primary["name"]},
                "topic": topic,
                "coherence": coherence,
                "affiliate_name": primary["name"],
                "fit_score": float(primary["fit_score"]),
            }

        # 5. Brief passed — assemble with all qualifying affiliates
        brief = {
            "topic": _clean(topic),
            "affiliate": {
                "primary": primary,
                "secondary": secondary,
                "all_qualifying": qualifying,
                "qualifying_count": len(qualifying),
                "total_scored": len(affiliates),
            },
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

        # Fire-and-forget WP status update
        asyncio.create_task(services.topics.mark_topic_running(tid, run_id))

        return {
            "status": "passed",
            "brief": brief,
            "topic": topic,
            "coherence": coherence,
            "affiliate_name": primary["name"],
            "fit_score": float(primary["fit_score"]),
            "affiliate_id": primary.get("id"),
            "secondary_id": secondary.get("id") if secondary else None,
            "qualifying_count": len(qualifying),
            "total_scored": len(affiliates),
            "usage": llm_usage,
        }

    # ── LLM call with exponential backoff ─────────────────────────────────

    async def _coherence_check_with_backoff(
        self, topic: dict, affiliate: dict, run_id: int,
    ) -> tuple[dict, dict]:
        """
        Call the LLM for coherence check with exponential backoff on 529 errors.

        Returns:
            (enrichments_dict, usage_dict)

        Raises:
            Exception if all retries exhausted.
        """
        prompt = self._coherence_prompt(topic, affiliate)
        last_exc = None
        backoff = INITIAL_BACKOFF_SECS

        for attempt in range(1, MAX_LLM_RETRIES + 1):
            try:
                result = await self.call_llm(prompt, run_id)
                enrichments = json.loads(result.text) if isinstance(result.text, str) else result.text

                usage = {
                    "stage": f"{self.stage_name}.{topic.get('id')}",
                    "model": self.model_config.model_id,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "cost_usd": result.cost_usd,
                }
                return enrichments, usage

            except Exception as exc:
                last_exc = exc
                exc_str = str(exc)

                # Check if this is a retryable 529/overloaded error
                is_overloaded = (
                    "529" in exc_str
                    or "overloaded" in exc_str.lower()
                    or "rate" in exc_str.lower()
                )

                if is_overloaded and attempt < MAX_LLM_RETRIES:
                    self.log.warning(
                        f"LLM call failed (attempt {attempt}/{MAX_LLM_RETRIES}): {exc_str}. "
                        f"Retrying in {backoff:.0f}s..."
                    )
                    await asyncio.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
                    continue
                else:
                    # Non-retryable error, or final retry exhausted
                    self.log.warning(
                        f"LLM call failed (attempt {attempt}/{MAX_LLM_RETRIES}): {exc_str}"
                    )
                    break

        raise last_exc  # type: ignore[misc]

    # ── Helpers ───────────────────────────────────────────────────────────

    def _coherence_prompt(self, topic: dict, affiliate: dict) -> str:
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

    def validate_output(self, raw_output: str) -> dict:
        data = super().validate_output(raw_output)
        if "coherence_score" not in data:
            raise ValueError("Missing 'coherence_score' in LLM output")
        return data

    async def _save_to_db(self, run_id: int, result: dict) -> None:
        try:
            from infrastructure import get_infrastructure
            infra = get_infrastructure()
            topic = result.get("topic", {})

            # Clean all data for JSON serialisation (Decimal safety)
            brief_json = json.dumps(_clean(result.get("brief"))) if result.get("brief") else None
            review_json = json.dumps(_clean(result.get("review_item", {})))

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
                float(result.get("fit_score")) if result.get("fit_score") is not None else None,
                float(result.get("coherence")) if result.get("coherence") is not None else None,
                result["status"],
                result.get("reason"),
                brief_json,
                review_json,
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