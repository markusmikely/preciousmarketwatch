"""
Stage 1c — BriefBuilder (v3.2 — content_type routing)

Routes by content_type:
  affiliate       → category match → per-affiliate coherence → lock brief
  authority       → no affiliate needed → lock brief with empty affiliate section
  market_commentary → optional soft affiliate → lock brief

Pre-LLM category match (zero tokens) filters affiliates before LLM check.
Compact coherence prompt (~200 input, ~100 output tokens per affiliate).
"""

from __future__ import annotations

import asyncio
import json
import logging
from decimal import Decimal

from nodes.base import BaseAgent, JSONOutputMixin, ModelConfig, ModelProvider, EventType
from config.settings import settings

log = logging.getLogger("pmw.node.brief_builder")

INTER_TOPIC_DELAY_SECS = 1.0
MAX_AFFILIATES_TO_CHECK = 5


def _clean(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    return obj


class BriefBuilder(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 1

    def __init__(self):
        super().__init__(
            agent_name="brief_builder",
            stage_name="research.stage1.brief_builder",
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                temperature=0.1,
                max_tokens=512,
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        all_topics = state.get("all_topics") or []
        all_affiliates = state.get("all_affiliates") or []

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "topics": len(all_topics), "affiliates": len(all_affiliates),
        })
        await self._write_stage(run_id, "running")

        if not all_topics:
            return await self._done(state, run_id, [], [], "No topics to process")

        from services import services

        locked = []
        review = []
        all_usage = []
        total_in, total_out = 0, 0

        for i, topic in enumerate(all_topics):
            title = topic.get("title", "Untitled")
            content_type = topic.get("content_type", "affiliate")

            if i > 0:
                await asyncio.sleep(INTER_TOPIC_DELAY_SECS)

            try:
                if content_type in ("authority", "market_commentary"):
                    result = await self._process_non_affiliate(
                        topic, all_affiliates, run_id, services, content_type,
                    )
                else:
                    if not all_affiliates:
                        result = {
                            "status": "needs_review",
                            "reason": "No affiliates available for affiliate content",
                            "review_item": {"topic": topic, "reason": "No affiliates"},
                            "topic": topic, "usage_list": [],
                        }
                    else:
                        result = await self._process_affiliate(
                            topic, all_affiliates, run_id, services,
                        )

                if result["status"] == "passed":
                    locked.append(result["brief"])
                    self.log.info(f"✓ '{title}' [{content_type}] → locked")
                elif result["status"] == "skipped":
                    self.log.info(f"⊘ '{title}' → skipped")
                else:
                    review.append(result.get("review_item", {}))
                    self.log.info(f"⚠ '{title}' → {result.get('reason', '?')}")

                for u in result.get("usage_list", []):
                    all_usage.append(u)
                    total_in += u.get("input_tokens", 0)
                    total_out += u.get("output_tokens", 0)

                if result["status"] in ("passed", "needs_review"):
                    await self._save_to_db(run_id, result)

            except Exception as exc:
                self.log.error(f"✗ '{title}' → error: {exc}")
                review.append({"topic": topic, "reason": str(exc), "status": "needs_review"})

        total_cost = sum(u.get("cost_usd", 0) for u in all_usage)
        output = {"locked": len(locked), "review": len(review), "total": len(all_topics)}

        await self._write_stage(
            run_id, "complete", passed=len(locked) > 0, output=output,
            in_tok=total_in, out_tok=total_out, cost_usd=total_cost,
        )
        await self._emit_event(EventType.STAGE_COMPLETE, run_id, {**output, "cost_usd": total_cost})

        return {
            "locked_briefs": locked, "review_items": review, "completed_bundles": [],
            "current_stage": self.stage_name,
            "model_usage": state.get("model_usage", []) + all_usage,
            "status": "complete" if state.get("status") != "failed" else "failed",
        }

    # ── Non-affiliate topics (authority, commentary) ──────────────────

    async def _process_non_affiliate(self, topic, all_affiliates, run_id, services, content_type):
        """
        Authority/commentary topics don't need affiliate coherence checks.
        Just lock the topic and build a minimal brief.
        For commentary, optionally pick the best affiliate for a soft mention.
        """
        tid = topic.get("id")

        acquired = await services.workflows.acquire_topic_lock(topic_wp_id=tid, run_id=run_id)
        if not acquired:
            return {"status": "skipped", "topic": topic, "usage_list": []}

        # For commentary, pick best matching affiliate for soft mention
        soft_affiliate = None
        if content_type == "market_commentary" and all_affiliates:
            matched = self._category_match(topic, all_affiliates)
            if matched:
                soft_affiliate = self._rank_matched(matched)[0]

        brief = {
            "topic": _clean(topic),
            "affiliate": {
                "primary": soft_affiliate,
                "primary_coherence": None,
                "secondary": None,
                "all_verified": [],
                "verified_count": 0,
                "total_affiliates": len(all_affiliates),
            },
            "meta": {"run_id": run_id, "content_type": content_type, "validation_passed": True},
            "reader": {},
        }

        asyncio.create_task(services.topics.mark_topic_running(tid, run_id))

        return {
            "status": "passed", "brief": brief, "topic": topic,
            "primary_name": soft_affiliate["name"] if soft_affiliate else "none",
            "primary_coherence": None,
            "affiliate_id": soft_affiliate.get("id") if soft_affiliate else None,
            "affiliate_name": soft_affiliate.get("name") if soft_affiliate else None,
            "fit_score": None, "secondary_id": None,
            "usage_list": [],
        }

    # ── Affiliate topics (full flow) ──────────────────────────────────

    async def _process_affiliate(self, topic, all_affiliates, run_id, services):
        tid = topic.get("id")
        title = topic.get("title", "Untitled")

        # Phase 1: category match
        matched = self._category_match(topic, all_affiliates)
        if not matched:
            return {
                "status": "needs_review",
                "reason": "No affiliates match topic categories",
                "review_item": {"topic": topic, "reason": "No category match"},
                "topic": topic, "usage_list": [],
            }

        ranked = self._rank_matched(matched)
        candidates = ranked[:MAX_AFFILIATES_TO_CHECK]

        self.log.info(
            f"  '{title}': {len(matched)}/{len(all_affiliates)} category-matched, "
            f"checking top {len(candidates)}"
        )

        # Phase 2: per-affiliate coherence
        results = []
        usage_list = []

        for aff in candidates:
            try:
                score, rationale, usage = await self._coherence_check(topic, aff, run_id)
                results.append({
                    "affiliate": aff, "coherence_score": score,
                    "rationale": rationale, "passed": score >= settings.COHERENCE_THRESHOLD,
                })
                usage_list.append(usage)
            except Exception as exc:
                self.log.warning(f"  {aff['name']}: coherence failed: {exc}")
                results.append({
                    "affiliate": aff, "coherence_score": 0.0,
                    "rationale": str(exc), "passed": False,
                })

        passed = sorted([r for r in results if r["passed"]],
                        key=lambda r: r["coherence_score"], reverse=True)

        if not passed:
            best = max(results, key=lambda r: r["coherence_score"])
            return {
                "status": "needs_review",
                "reason": f"0/{len(results)} passed coherence (best={best['affiliate']['name']} {best['coherence_score']:.2f})",
                "review_item": {
                    "topic": topic, "reason": "No affiliate passed coherence",
                    "scores": [{"name": r["affiliate"]["name"], "score": r["coherence_score"]}
                               for r in results],
                },
                "topic": topic,
                "coherence_scores": {r["affiliate"]["name"]: r["coherence_score"] for r in results},
                "usage_list": usage_list,
            }

        acquired = await services.workflows.acquire_topic_lock(topic_wp_id=tid, run_id=run_id)
        if not acquired:
            return {"status": "skipped", "topic": topic, "usage_list": usage_list}

        primary = passed[0]
        secondary = passed[1] if len(passed) > 1 else None

        brief = {
            "topic": _clean(topic),
            "affiliate": {
                "primary": primary["affiliate"],
                "primary_coherence": primary["coherence_score"],
                "primary_rationale": primary["rationale"],
                "secondary": secondary["affiliate"] if secondary else None,
                "secondary_coherence": secondary["coherence_score"] if secondary else None,
                "all_verified": [{**r["affiliate"], "coherence_score": r["coherence_score"]}
                                 for r in passed],
                "verified_count": len(passed),
                "total_affiliates": len(all_affiliates),
            },
            "meta": {
                "run_id": run_id, "content_type": "affiliate",
                "coherence_score": primary["coherence_score"],
                "validation_passed": True,
                "coherence_scores": {r["affiliate"]["name"]: r["coherence_score"] for r in results},
            },
            "reader": {},
        }

        asyncio.create_task(services.topics.mark_topic_running(tid, run_id))

        return {
            "status": "passed", "brief": brief, "topic": topic,
            "primary_name": primary["affiliate"]["name"],
            "primary_coherence": primary["coherence_score"],
            "affiliate_id": primary["affiliate"].get("id"),
            "affiliate_name": primary["affiliate"]["name"],
            "fit_score": float(primary["affiliate"].get("_rank_score", 0)),
            "secondary_id": secondary["affiliate"].get("id") if secondary else None,
            "coherence_scores": {r["affiliate"]["name"]: r["coherence_score"] for r in results},
            "usage_list": usage_list,
        }

    # ── Category matching (zero tokens) ───────────────────────────────

    @staticmethod
    def _category_match(topic, affiliates):
        topic_asset = (topic.get("asset_class") or "").lower().strip()
        topic_geo = (topic.get("geography") or "uk").lower().strip()
        topic_buy = topic.get("is_buy_side", False)

        matched = []
        for aff in affiliates:
            if topic_buy and not aff.get("buy_side", True):
                continue
            aff_assets = (aff.get("asset_classes") or "").lower()
            aff_geo = (aff.get("geo_focus") or "").lower()
            aff_vp = (aff.get("value_prop") or "").lower()
            aff_name = (aff.get("name") or "").lower()
            combined = f"{aff_assets} {aff_vp} {aff_name}"

            asset_match = (
                (topic_asset and topic_asset in combined)
                or (topic_asset in ("gold", "silver", "platinum")
                    and any(m in combined for m in ("precious metal", "bullion")))
            )
            geo_match = aff_geo in (topic_geo, "global", "")

            if asset_match and geo_match:
                matched.append(aff)
        return matched

    @staticmethod
    def _rank_matched(matched):
        for aff in matched:
            commission = float(aff.get("commission_rate") or 0)
            cookies = int(aff.get("cookie_days") or 0)
            aff["_rank_score"] = (commission * 10) + (min(cookies, 90) / 90 * 0.3)
        return sorted(matched, key=lambda a: a["_rank_score"], reverse=True)

    # ── Coherence check (compact prompt) ──────────────────────────────

    async def _coherence_check(self, topic, affiliate, run_id):
        prompt = (
            "Score how well this affiliate fits this article topic. "
            "Return JSON: {\"score\": 0.0-1.0, \"rationale\": \"1 sentence\"}\n\n"
            f"TOPIC: {topic.get('title', '')}\n"
            f"Keyword: {topic.get('target_keyword', '')}\n"
            f"Asset: {topic.get('asset_class', '')} | Geo: {topic.get('geography', 'uk')}\n\n"
            f"AFFILIATE: {affiliate.get('name', '')}\n"
            f"Offers: {(affiliate.get('value_prop') or '')[:100]}\n"
            f"Assets: {(affiliate.get('asset_classes') or '')[:60]}\n\n"
            "0.8+ = direct fit. 0.4-0.7 = loose. <0.4 = poor."
        )
        result = await self.call_llm(prompt, run_id)
        data = json.loads(result.text) if isinstance(result.text, str) else result.text
        return float(data.get("score", 0)), data.get("rationale", ""), {
            "stage": f"{self.stage_name}.{topic.get('id')}.{affiliate.get('name', '?')}",
            "model": self.model_config.model_id,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "cost_usd": result.cost_usd,
        }

    def validate_output(self, raw_output: str) -> dict:
        data = super().validate_output(raw_output)
        if "score" not in data:
            raise ValueError("Missing 'score'")
        return data

    # ── DB + helpers ──────────────────────────────────────────────────

    async def _save_to_db(self, run_id, result):
        try:
            from infrastructure import get_infrastructure
            infra = get_infrastructure()
            topic = result.get("topic", {})
            brief_json = json.dumps(_clean(result.get("brief"))) if result.get("brief") else None
            scores = result.get("coherence_scores", {})
            breakdown = json.dumps(_clean({"coherence_scores": scores, **result.get("review_item", {})}))
            primary_coherence = result.get("primary_coherence")
            if primary_coherence is None and scores:
                primary_coherence = max(scores.values())
            await infra.postgres.execute(
                """INSERT INTO topic_briefs (run_id, topic_wp_id, topic_title,
                    affiliate_id, affiliate_name, secondary_affiliate_id,
                    fit_score, coherence_score, status, review_reason,
                    brief_json, score_breakdown_json)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12::jsonb)""",
                run_id, topic.get("id"), topic.get("title", ""),
                result.get("affiliate_id"), result.get("affiliate_name"),
                result.get("secondary_id"),
                float(result.get("fit_score")) if result.get("fit_score") is not None else None,
                float(primary_coherence) if primary_coherence is not None else None,
                result["status"], result.get("reason"), brief_json, breakdown,
            )
        except Exception as exc:
            self.log.warning(f"topic_briefs write failed: {exc}")

    async def _done(self, state, run_id, locked, review, msg):
        has = len(locked) > 0
        await self._write_stage(
            run_id, "complete" if has else "failed", passed=has,
            output={"locked": len(locked), "review": len(review), "reason": msg},
            error=msg if not has else None,
        )
        return {
            "locked_briefs": locked, "review_items": review, "completed_bundles": [],
            "current_stage": self.stage_name, "status": "complete",
            "errors": state.get("errors", []) + ([{"stage": self.stage_name, "error": msg}] if not has else []),
            "model_usage": state.get("model_usage", []),
        }