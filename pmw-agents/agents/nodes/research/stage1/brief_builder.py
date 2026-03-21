"""
Stage 1c — BriefBuilder (v3.0)

For each topic in all_topics:
  1. Score all affiliates with manual filter (geo × 0.4 + product × 0.4 + commission × 0.2)
  2. For each qualifying affiliate → LLM coherence check (topic × affiliate pair)
  3. Only affiliates passing coherence threshold are included in the brief
  4. Primary = highest coherence, secondary = second highest
  5. If 0 affiliates pass → topic goes to review queue
  6. If 1+ pass → lock topic, lock brief → locked_briefs

Key change from v2:
  Coherence is per-AFFILIATE, not per-topic. The LLM evaluates each
  topic×affiliate pair independently. This means different affiliates
  can have different coherence scores for the same topic, and only the
  ones that make editorial sense get included.

  Example: "Best Gold ISA UK" might score coherence=0.92 with BullionVault
  (they offer gold ISAs) but coherence=0.31 with a coin dealer (no ISA product).
  Only BullionVault makes it into the brief.

Features:
  - Exponential backoff on 529/overloaded errors
  - 1-second delay between topics to avoid API rate pressure
  - Per-affiliate coherence scores stored in topic_briefs
  - _done() writes stage record (never leaves "running" stuck)
  - Accumulated cost/tokens tracked across all LLM calls
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

MAX_LLM_RETRIES = 3
INITIAL_BACKOFF_SECS = 2.0
BACKOFF_MULTIPLIER = 2.0
INTER_TOPIC_DELAY_SECS = 1.0
# Max affiliates to coherence-check per topic (avoid burning tokens
# on low-scoring affiliates that barely passed the manual filter)
MAX_AFFILIATES_TO_CHECK = 5


def _clean(obj):
    """Recursively convert Decimal → float for JSON safety."""
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

    # ══════════════════════════════════════════════════════════════════
    # MAIN ENTRY POINT
    # ══════════════════════════════════════════════════════════════════

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        all_topics = state.get("all_topics") or []
        all_affiliates = state.get("all_affiliates") or []
        await self._write_stage(run_id, "running")

        if not all_topics:
            return await self._done(state, run_id, [], [], "No topics to process")
        if not all_affiliates:
            return await self._done(state, run_id, [], [], "No affiliates available")

        from services import services

        locked = []
        review = []
        all_usage = []
        total_in_tok = 0
        total_out_tok = 0

        for i, topic in enumerate(all_topics):
            title = topic.get("title", "Untitled")

            if i > 0:
                await asyncio.sleep(INTER_TOPIC_DELAY_SECS)

            try:
                result = await self._process_one_topic(
                    topic, all_affiliates, run_id, services,
                )

                if result["status"] == "passed":
                    locked.append(result["brief"])
                    self.log.info(
                        f"✓ '{title}' → locked "
                        f"(primary={result['primary_name']} coherence={result['primary_coherence']:.2f}, "
                        f"affiliates_passed={result['affiliates_passed']}/{result['affiliates_checked']})"
                    )
                elif result["status"] == "skipped":
                    self.log.info(f"⊘ '{title}' → skipped (already locked)")
                else:
                    review.append(result.get("review_item", {}))
                    self.log.info(f"⚠ '{title}' → needs_review ({result.get('reason', '?')})")

                # Accumulate usage from all LLM calls for this topic
                for u in result.get("usage_list", []):
                    all_usage.append(u)
                    total_in_tok += u.get("input_tokens", 0)
                    total_out_tok += u.get("output_tokens", 0)

                if result["status"] in ("passed", "needs_review"):
                    await self._save_to_db(run_id, result)

            except Exception as exc:
                self.log.error(f"✗ '{title}' → error: {exc}")
                review.append({
                    "topic": topic, "reason": str(exc), "status": "needs_review",
                })

        # ── Write final stage record with accumulated cost ────────────
        total_cost = sum(u.get("cost_usd", 0) for u in all_usage)
        output = {
            "locked": len(locked),
            "review": len(review),
            "total": len(all_topics),
        }

        await self._write_stage(
            run_id, "complete",
            passed=len(locked) > 0,
            output=output,
            in_tok=total_in_tok,
            out_tok=total_out_tok,
            cost_usd=total_cost,
        )
        await self._emit("stage.complete", run_id, {**output, "cost_usd": total_cost})

        return {
            "locked_briefs": locked,
            "review_items": review,
            "completed_bundles": [],
            "current_stage": self.stage_name,
            "model_usage": state.get("model_usage", []) + all_usage,
            "status": "complete" if state.get("status") != "failed" else "failed",
        }

    # ══════════════════════════════════════════════════════════════════
    # PER-TOPIC PROCESSING
    # ══════════════════════════════════════════════════════════════════

    async def _process_one_topic(self, topic, affiliates, run_id, services):
        """
        Process a single topic:
          1. Manual scoring → qualifying affiliates
          2. Per-affiliate LLM coherence check
          3. Filter by coherence threshold
          4. Lock topic if any affiliate passes
          5. Build brief with passing affiliates
        """
        tid = topic.get("id")
        title = topic.get("title", "Untitled")

        # ── Step 1: Manual filter ─────────────────────────────────────
        scored = await services.affiliates.score_affiliates_for_topic(topic, affiliates)

        if not scored:
            return {
                "status": "needs_review",
                "reason": f"No affiliate scored above {settings.AFFILIATE_FIT_THRESHOLD}",
                "review_item": {
                    "topic": topic,
                    "reason": "No qualifying affiliate after manual filter",
                    "scores": [],
                },
                "topic": topic,
                "usage_list": [],
                "affiliates_checked": 0,
                "affiliates_passed": 0,
            }

        qualifying = _clean(scored)
        candidates = qualifying[:MAX_AFFILIATES_TO_CHECK]

        self.log.info(
            f"Topic '{title}': {len(qualifying)}/{len(affiliates)} pass manual filter "
            f"(threshold={settings.AFFILIATE_FIT_THRESHOLD}), "
            f"checking coherence for top {len(candidates)}"
        )

        # ── Step 2: Per-affiliate LLM coherence check ─────────────────
        coherence_results = []
        usage_list = []

        for aff in candidates:
            try:
                enrichments, llm_usage = await self._coherence_check_with_backoff(
                    topic, aff, run_id,
                )
                coherence_score = float(enrichments.get("coherence_score", 0))
                coherence_results.append({
                    "affiliate": aff,
                    "coherence_score": coherence_score,
                    "enrichments": enrichments,
                    "passed": coherence_score >= settings.COHERENCE_THRESHOLD,
                })
                usage_list.append(llm_usage)

                self.log.debug(
                    f"  {aff['name']}: coherence={coherence_score:.2f} "
                    f"({'PASS' if coherence_score >= settings.COHERENCE_THRESHOLD else 'FAIL'})"
                )

            except Exception as exc:
                self.log.warning(
                    f"  {aff['name']}: coherence check failed: {exc}"
                )
                coherence_results.append({
                    "affiliate": aff,
                    "coherence_score": 0.0,
                    "enrichments": None,
                    "passed": False,
                    "error": str(exc),
                })

        # ── Step 3: Filter by coherence threshold ─────────────────────
        passed_affiliates = [
            r for r in coherence_results if r["passed"]
        ]
        passed_affiliates.sort(
            key=lambda r: r["coherence_score"], reverse=True,
        )

        affiliates_checked = len(coherence_results)
        affiliates_passed = len(passed_affiliates)

        if not passed_affiliates:
            # All affiliates failed coherence — topic needs review
            best = max(coherence_results, key=lambda r: r["coherence_score"])
            return {
                "status": "needs_review",
                "reason": (
                    f"0/{affiliates_checked} affiliates passed coherence "
                    f"(threshold={settings.COHERENCE_THRESHOLD}, "
                    f"best={best['affiliate']['name']} at {best['coherence_score']:.2f})"
                ),
                "review_item": {
                    "topic": topic,
                    "reason": "No affiliate passed coherence check",
                    "coherence_scores": [
                        {
                            "affiliate": r["affiliate"]["name"],
                            "coherence": r["coherence_score"],
                            "fit_score": r["affiliate"].get("fit_score", 0),
                            "error": r.get("error"),
                        }
                        for r in coherence_results
                    ],
                },
                "topic": topic,
                "coherence_scores": {
                    r["affiliate"]["name"]: r["coherence_score"]
                    for r in coherence_results
                },
                "usage_list": usage_list,
                "affiliates_checked": affiliates_checked,
                "affiliates_passed": 0,
            }

        # ── Step 4: Lock topic ────────────────────────────────────────
        acquired = await services.workflows.acquire_topic_lock(
            topic_wp_id=tid, run_id=run_id,
        )
        if not acquired:
            return {
                "status": "skipped",
                "topic": topic,
                "usage_list": usage_list,
                "affiliates_checked": affiliates_checked,
                "affiliates_passed": affiliates_passed,
            }

        # ── Step 5: Build brief with passing affiliates ───────────────
        primary_result = passed_affiliates[0]
        secondary_result = passed_affiliates[1] if len(passed_affiliates) > 1 else None
        primary = primary_result["affiliate"]
        secondary = secondary_result["affiliate"] if secondary_result else None
        primary_enrichments = primary_result["enrichments"]

        brief = {
            "topic": _clean(topic),
            "affiliate": {
                "primary": primary,
                "primary_coherence": primary_result["coherence_score"],
                "secondary": secondary,
                "secondary_coherence": (
                    secondary_result["coherence_score"] if secondary_result else None
                ),
                # All affiliates that passed both manual + coherence filters
                "all_verified": [
                    {
                        **r["affiliate"],
                        "coherence_score": r["coherence_score"],
                    }
                    for r in passed_affiliates
                ],
                "verified_count": affiliates_passed,
                "checked_count": affiliates_checked,
                "total_scored": len(affiliates),
            },
            "meta": {
                "run_id": run_id,
                "coherence_score": primary_result["coherence_score"],
                "validation_passed": True,
                "warnings": [
                    i for i in primary_enrichments.get("issues", [])
                    if i.get("severity") == "warning"
                ],
                "coherence_scores": {
                    r["affiliate"]["name"]: r["coherence_score"]
                    for r in coherence_results
                },
            },
            "reader": {
                "profile": primary_enrichments.get("enriched_reader_profile", ""),
                "moment": primary_enrichments.get("enriched_reader_moment", ""),
                "article_angle": primary_enrichments.get("suggested_article_angle", ""),
            },
        }

        asyncio.create_task(services.topics.mark_topic_running(tid, run_id))

        return {
            "status": "passed",
            "brief": brief,
            "topic": topic,
            "primary_name": primary["name"],
            "primary_coherence": primary_result["coherence_score"],
            "affiliate_id": primary.get("id"),
            "affiliate_name": primary["name"],
            "fit_score": float(primary.get("fit_score", 0)),
            "secondary_id": secondary.get("id") if secondary else None,
            "affiliates_checked": affiliates_checked,
            "affiliates_passed": affiliates_passed,
            "coherence_scores": {
                r["affiliate"]["name"]: r["coherence_score"]
                for r in coherence_results
            },
            "usage_list": usage_list,
        }

    # ══════════════════════════════════════════════════════════════════
    # LLM COHERENCE CHECK (per affiliate)
    # ══════════════════════════════════════════════════════════════════

    async def _coherence_check_with_backoff(self, topic, affiliate, run_id):
        """
        Run LLM coherence check for a specific topic × affiliate pair.
        Returns (enrichments_dict, usage_dict).
        Retries with exponential backoff on overloaded/rate-limit errors.
        """
        prompt = self._coherence_prompt(topic, affiliate)
        last_exc = None
        backoff = INITIAL_BACKOFF_SECS

        for attempt in range(1, MAX_LLM_RETRIES + 1):
            try:
                result = await self.call_llm(prompt, run_id)
                enrichments = (
                    json.loads(result.text)
                    if isinstance(result.text, str)
                    else result.text
                )
                return enrichments, {
                    "stage": (
                        f"{self.stage_name}"
                        f".{topic.get('id')}"
                        f".{affiliate.get('name', '?')}"
                    ),
                    "model": self.model_config.model_id,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "cost_usd": result.cost_usd,
                }
            except Exception as exc:
                last_exc = exc
                exc_str = str(exc)
                is_overloaded = (
                    "529" in exc_str
                    or "overloaded" in exc_str.lower()
                    or "rate" in exc_str.lower()
                )
                if is_overloaded and attempt < MAX_LLM_RETRIES:
                    self.log.warning(
                        f"LLM overloaded checking {affiliate.get('name', '?')} "
                        f"(attempt {attempt}/{MAX_LLM_RETRIES}), "
                        f"retrying in {backoff:.0f}s..."
                    )
                    await asyncio.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
                else:
                    self.log.warning(
                        f"LLM call failed for {affiliate.get('name', '?')} "
                        f"(attempt {attempt}/{MAX_LLM_RETRIES}): {exc_str}"
                    )
                    break
        raise last_exc

    def _coherence_prompt(self, topic, affiliate):
        """Build the coherence check prompt for a topic × affiliate pair."""
        return PromptRegistry.render("stage1_5_brief_validation", {
            "TOPIC_TITLE": topic.get("title", ""),
            "TARGET_KEYWORD": topic.get("target_keyword", ""),
            "ASSET_CLASS": topic.get("asset_class", ""),
            "PRODUCT_TYPE": topic.get("product_type", ""),
            "GEOGRAPHY": topic.get("geography", "uk"),
            "IS_BUY_SIDE": str(topic.get("is_buy_side", False)),
            "INTENT_STAGE": topic.get("intent_stage", "consideration"),
            "AFFILIATE_NAME": affiliate.get("name", ""),
            "AFFILIATE_KEY": affiliate.get(
                "partner_key",
                affiliate.get("name", "").lower().replace(" ", "-"),
            ),
            "AFFILIATE_VALUE_PROP": affiliate.get("value_prop", ""),
            "AFFILIATE_GEO": affiliate.get("geo_focus", ""),
            "COMMISSION_TYPE": affiliate.get("commission_type", ""),
        })

    def validate_output(self, raw_output: str) -> dict:
        """Parse JSON and require coherence_score field."""
        data = super().validate_output(raw_output)
        if "coherence_score" not in data:
            raise ValueError("Missing 'coherence_score' in LLM output")
        return data

    # ══════════════════════════════════════════════════════════════════
    # DB + EXIT HELPERS
    # ══════════════════════════════════════════════════════════════════

    async def _save_to_db(self, run_id, result):
        """Save brief/review result to topic_briefs table."""
        try:
            from infrastructure import get_infrastructure
            infra = get_infrastructure()
            topic = result.get("topic", {})

            brief_json = (
                json.dumps(_clean(result.get("brief")))
                if result.get("brief")
                else None
            )
            # Store per-affiliate coherence scores in the breakdown
            score_breakdown = {
                "coherence_scores": result.get("coherence_scores", {}),
                "affiliates_checked": result.get("affiliates_checked", 0),
                "affiliates_passed": result.get("affiliates_passed", 0),
            }
            if result.get("review_item"):
                score_breakdown["review_item"] = _clean(result["review_item"])

            # Use primary affiliate's coherence as the headline score
            primary_coherence = result.get("primary_coherence")
            if primary_coherence is None:
                # For review items, use the best coherence from any affiliate
                scores = result.get("coherence_scores", {})
                primary_coherence = max(scores.values()) if scores else None

            await infra.postgres.execute(
                """INSERT INTO topic_briefs (
                    run_id, topic_wp_id, topic_title,
                    affiliate_id, affiliate_name, secondary_affiliate_id,
                    fit_score, coherence_score, status, review_reason,
                    brief_json, score_breakdown_json
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12::jsonb)""",
                run_id,
                topic.get("id"),
                topic.get("title", ""),
                result.get("affiliate_id"),
                result.get("affiliate_name"),
                result.get("secondary_id"),
                float(result.get("fit_score")) if result.get("fit_score") is not None else None,
                float(primary_coherence) if primary_coherence is not None else None,
                result["status"],
                result.get("reason"),
                brief_json,
                json.dumps(_clean(score_breakdown)),
            )
        except Exception as exc:
            self.log.warning(f"topic_briefs write failed: {exc}")

    async def _done(self, state, run_id, locked, review, msg):
        """
        Early-exit helper. Writes the stage record before returning
        so the workflow_stages row is never left stuck as "running".
        """
        has_results = len(locked) > 0
        status = "complete" if has_results else "failed"

        await self._write_stage(
            run_id, status,
            passed=has_results,
            output={"locked": len(locked), "review": len(review), "reason": msg},
            error=msg if not has_results else None,
        )

        return {
            "locked_briefs": locked,
            "review_items": review,
            "completed_bundles": [],
            "current_stage": self.stage_name,
            "status": "complete",
            "errors": state.get("errors", []) + (
                [{"stage": self.stage_name, "error": msg}] if not locked else []
            ),
            "model_usage": state.get("model_usage", []),
        }