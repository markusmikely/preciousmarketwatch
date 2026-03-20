"""
Stage 1b — BriefBuilder

Processes ALL topics against ALL affiliates in a single pass:
  1. For each topic, score all affiliates
  2. If best affiliate >= threshold (0.40):
     - Acquire Postgres topic lock
     - Run LLM coherence check
     - If coherence >= 0.60: add to locked_briefs
     - If coherence < 0.60: add to review_items
  3. If no affiliate >= threshold:
     - Add to review_items (saved to topic_briefs table for dashboard)
  4. Return locked_briefs (proceed to stages 2-8) + review_items (saved to DB)

This replaces the old sequential chain:
  topic_selector → affiliate_scorer → brief_locker

The old chain processed one topic per run. This node processes ALL
eligible topics in a single run, producing a list of briefs.

Depends on: topic_loader (all_topics), affiliate_loader (all_affiliates)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging

from nodes.base import (
    BaseAgent, JSONOutputMixin, ModelConfig, ModelProvider,
    FailureConfig, EventType, AgentStatus,
)
from prompts.registry import PromptRegistry

log = logging.getLogger("pmw.node.brief_builder")

# Thresholds
AFFILIATE_FIT_THRESHOLD = 0.40
COHERENCE_THRESHOLD = 0.60


class BriefBuilder(JSONOutputMixin, BaseAgent):
    """
    Processes all topics × all affiliates → list of locked briefs.

    For each topic:
      1. Score affiliates → pick best primary + secondary
      2. If primary fit_score >= 0.40: lock topic + LLM coherence check
      3. If coherence >= 0.60: brief passes → locked_briefs
      4. Otherwise: topic → review_items (saved to Postgres)

    Output in state:
      locked_briefs: list of briefs ready for stages 2-8
      review_items:  list of topics needing human review (saved to DB)
    """

    MAX_RETRIES = 2  # Per-topic coherence check retries

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
            failure_config=FailureConfig(
                failure_message="Brief coherence check failed.",
                human_in_the_loop=False,  # Individual topic failures don't halt the run
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        all_topics = state.get("all_topics") or []
        all_affiliates = state.get("all_affiliates") or []

        await self._emit_event(EventType.STAGE_STARTED, run_id, {
            "topic_count": len(all_topics),
            "affiliate_count": len(all_affiliates),
        })
        await self._write_stage_record(run_id, status="running", attempt=1)

        if not all_topics:
            return self._fail(state, "No topics available to process")

        if not all_affiliates:
            return self._fail(state, "No affiliates available for scoring")

        from services import services

        locked_briefs = []
        review_items = []
        total_cost = 0.0
        all_model_usage = list(state.get("model_usage", []))

        for topic in all_topics:
            topic_id = topic.get("id")
            topic_title = topic.get("title", "Untitled")

            try:
                # ── Step 1: Score affiliates for this topic ───────────
                scored = await services.affiliates.score_affiliates_for_topic(
                    topic=topic,
                    affiliates=all_affiliates,
                )

                if not scored:
                    # No affiliate scored above threshold
                    review_item = self._build_review_item(
                        topic=topic,
                        reason=f"No affiliate scored above {AFFILIATE_FIT_THRESHOLD} threshold",
                        score_data={"all_scores_below_threshold": True},
                    )
                    review_items.append(review_item)
                    await self._save_topic_brief_to_db(
                        run_id, review_item, status="needs_review",
                    )
                    self.log.info(
                        f"Topic '{topic_title}' → needs_review (no qualifying affiliate)",
                        run_id=run_id,
                    )
                    continue

                primary = scored[0]
                secondary = scored[1] if len(scored) > 1 else None

                # ── Step 2: Acquire Postgres topic lock ───────────────
                acquired = await services.workflows.acquire_topic_lock(
                    topic_wp_id=topic_id,
                    run_id=run_id,
                )

                if not acquired:
                    # Topic already locked by another run — skip silently
                    self.log.info(
                        f"Topic '{topic_title}' already locked — skipping",
                        run_id=run_id,
                    )
                    continue

                # ── Step 3: LLM coherence check ──────────────────────
                prompt = self._build_coherence_prompt(topic, primary)
                prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

                try:
                    result = await self.call_llm(prompt, run_id, attempt=1)
                    enrichments = result.output  # validated JSON
                    coherence_score = enrichments.get("coherence_score", 0)
                    total_cost += result.cost_usd

                    all_model_usage.append({
                        "stage": f"{self.stage_name}.{topic_id}",
                        "model": self.model_config.model_id,
                        "input_tokens": result.input_tokens,
                        "output_tokens": result.output_tokens,
                        "cost_usd": result.cost_usd,
                    })

                except Exception as llm_exc:
                    # LLM failure for this topic — add to review, continue
                    review_item = self._build_review_item(
                        topic=topic,
                        reason=f"LLM coherence check failed: {llm_exc}",
                        score_data={
                            "primary_affiliate": primary["name"],
                            "fit_score": primary["fit_score"],
                        },
                        affiliate=primary,
                    )
                    review_items.append(review_item)
                    await self._save_topic_brief_to_db(
                        run_id, review_item, status="needs_review",
                    )
                    # Release the lock since we can't proceed
                    await services.workflows.release_topic_lock(
                        topic_wp_id=topic_id, run_id=run_id, success=False,
                    )
                    self.log.warning(
                        f"Topic '{topic_title}' → needs_review (LLM failed: {llm_exc})",
                        run_id=run_id,
                    )
                    continue

                # ── Step 4: Check coherence threshold ─────────────────
                if coherence_score < COHERENCE_THRESHOLD:
                    review_item = self._build_review_item(
                        topic=topic,
                        reason=(
                            f"Coherence score {coherence_score:.2f} below "
                            f"{COHERENCE_THRESHOLD} threshold"
                        ),
                        score_data={
                            "coherence_score": coherence_score,
                            "primary_affiliate": primary["name"],
                            "fit_score": primary["fit_score"],
                        },
                        affiliate=primary,
                        brief_data=enrichments,
                    )
                    review_items.append(review_item)
                    await self._save_topic_brief_to_db(
                        run_id, review_item, status="needs_review",
                        coherence_score=coherence_score,
                        affiliate_id=primary.get("id"),
                    )
                    # Release lock — topic won't proceed
                    await services.workflows.release_topic_lock(
                        topic_wp_id=topic_id, run_id=run_id, success=False,
                    )
                    self.log.info(
                        f"Topic '{topic_title}' → needs_review "
                        f"(coherence {coherence_score:.2f} < {COHERENCE_THRESHOLD})",
                        run_id=run_id,
                    )
                    continue

                # ── Step 5: Brief passed — lock it ────────────────────
                brief = self._assemble_brief(
                    topic=topic,
                    primary=primary,
                    secondary=secondary,
                    enrichments=enrichments,
                    coherence_score=coherence_score,
                    run_id=run_id,
                )
                locked_briefs.append(brief)

                await self._save_topic_brief_to_db(
                    run_id, brief, status="passed",
                    coherence_score=coherence_score,
                    affiliate_id=primary.get("id"),
                    secondary_affiliate_id=secondary.get("id") if secondary else None,
                    fit_score=primary["fit_score"],
                )

                # Fire-and-forget WP display status
                asyncio.create_task(
                    services.topics.mark_topic_running(topic_id, run_id)
                )

                self.log.info(
                    f"Topic '{topic_title}' → PASSED "
                    f"(affiliate={primary['name']}, fit={primary['fit_score']:.2f}, "
                    f"coherence={coherence_score:.2f})",
                    run_id=run_id,
                )

            except Exception as exc:
                # Unexpected error for this topic — log and continue
                self.log.error(
                    f"Unexpected error processing topic '{topic_title}': {exc}",
                    run_id=run_id,
                )
                review_items.append(self._build_review_item(
                    topic=topic,
                    reason=f"Unexpected error: {exc}",
                    score_data={},
                ))
                continue

        # ── Summary ───────────────────────────────────────────────────
        output = {
            "locked_count": len(locked_briefs),
            "review_count": len(review_items),
            "total_topics": len(all_topics),
            "skipped_locked": len(all_topics) - len(locked_briefs) - len(review_items),
            "total_cost_usd": round(total_cost, 6),
        }

        self.log.info(
            f"BriefBuilder complete: {len(locked_briefs)} passed, "
            f"{len(review_items)} needs_review, "
            f"{output['skipped_locked']} already locked",
            run_id=run_id,
        )

        if not locked_briefs:
            # No briefs passed — this is not a hard failure.
            # The run completes with zero bundles, which is valid.
            # Topics needing review are already saved to DB.
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=False,
                output=output,
                cost_usd=total_cost,
            )
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)

            return {
                "locked_briefs": [],
                "review_items": review_items,
                "completed_bundles": [],
                "current_stage": "stage1.brief_builder",
                "status": "complete",  # Not "failed" — zero briefs is a valid outcome
                "model_usage": all_model_usage,
            }

        await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)
        await self._write_stage_record(
            run_id, status="complete", attempt=1,
            passed_threshold=True,
            output=output,
            cost_usd=total_cost,
        )

        return {
            "locked_briefs": locked_briefs,
            "review_items": review_items,
            "completed_bundles": [],  # Will be populated by stages 2-8
            "current_stage": "stage1.brief_builder",
            "model_usage": all_model_usage,
        }

    # ── Brief assembly ────────────────────────────────────────────────

    def _assemble_brief(
        self,
        topic: dict,
        primary: dict,
        secondary: dict | None,
        enrichments: dict,
        coherence_score: float,
        run_id: int,
    ) -> dict:
        return {
            "topic": topic,
            "affiliate": {
                "primary": primary,
                "secondary": secondary,
            },
            "meta": {
                "run_id": run_id,
                "coherence_score": coherence_score,
                "validation_passed": True,
                "warnings": [
                    i for i in enrichments.get("issues", [])
                    if i.get("severity") == "warning"
                ],
            },
            "reader": {
                "profile": enrichments.get("enriched_reader_profile", ""),
                "moment": enrichments.get("enriched_reader_moment", ""),
                "article_angle": enrichments.get("suggested_article_angle", ""),
            },
        }

    def _build_review_item(
        self,
        topic: dict,
        reason: str,
        score_data: dict,
        affiliate: dict | None = None,
        brief_data: dict | None = None,
    ) -> dict:
        return {
            "topic": topic,
            "reason": reason,
            "score_data": score_data,
            "affiliate": affiliate,
            "brief_data": brief_data,
            "status": "needs_review",
        }

    # ── Postgres save for topic_briefs table ──────────────────────────

    async def _save_topic_brief_to_db(
        self,
        run_id: int,
        item: dict,
        status: str,
        coherence_score: float | None = None,
        affiliate_id: int | None = None,
        secondary_affiliate_id: int | None = None,
        fit_score: float | None = None,
    ) -> None:
        """Save to topic_briefs table for dashboard review queue."""
        try:
            from infrastructure import get_infrastructure
            infra = get_infrastructure()

            topic = item.get("topic", {})
            await infra.postgres.execute(
                """
                INSERT INTO topic_briefs (
                    run_id, topic_wp_id, topic_title,
                    affiliate_id, affiliate_name,
                    secondary_affiliate_id,
                    fit_score, coherence_score,
                    status, review_reason,
                    brief_json, score_breakdown_json
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11::jsonb, $12::jsonb
                )
                """,
                run_id,
                topic.get("id"),
                topic.get("title", ""),
                affiliate_id,
                (item.get("affiliate") or {}).get("name"),
                secondary_affiliate_id,
                fit_score,
                coherence_score,
                status,
                item.get("reason"),
                json.dumps(item) if status == "passed" else json.dumps(item.get("brief_data")),
                json.dumps(item.get("score_data", {})),
            )
        except Exception as exc:
            self.log.warning(
                f"topic_briefs write failed (non-blocking): {exc}",
                run_id=run_id,
            )

    # ── LLM coherence prompt ──────────────────────────────────────────

    def _build_coherence_prompt(self, topic: dict, affiliate: dict) -> str:
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
        """Parse JSON + validate coherence_score exists."""
        data = super().validate_output(raw_output)
        if "coherence_score" not in data:
            raise ValueError("LLM output missing 'coherence_score' field")
        return data

    # ── Failure helper ────────────────────────────────────────────────

    def _fail(self, state: dict, error_msg: str) -> dict:
        self.log.error(error_msg, run_id=state["run_id"])
        return {
            "locked_briefs": [],
            "review_items": [],
            "completed_bundles": [],
            "current_stage": "stage1.brief_builder",
            "status": "failed",
            "errors": state.get("errors", []) + [{
                "stage": "stage1.brief_builder",
                "error": error_msg,
            }],
        }