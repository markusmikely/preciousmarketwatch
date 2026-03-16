"""
Stage 1.5 — BriefLocker

Acquires Postgres topic lock, assembles draft brief, runs LLM coherence
validation, and locks the final brief object.

Lock acquisition happens FIRST — before the LLM call. If the lock
cannot be acquired, the pipeline fails gracefully (no LLM cost wasted).

Uses stage1_5_brief_validation prompt template.
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


class BriefLocker(JSONOutputMixin, BaseAgent):
    MAX_RETRIES = 2  # 3 total attempts

    def __init__(self):
        super().__init__(
            agent_name="brief_locker",
            stage_name="research.stage1.brief_locker",
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                temperature=0.2,
                max_tokens=2048,
            ),
            failure_config=FailureConfig(
                failure_message="Brief coherence check failed after max retries.",
                human_in_the_loop=True,
            ),
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        selected_topic = state.get("selected_topic") or {}
        primary_affiliate = state.get("primary_affiliate") or {}
        secondary_affiliate = state.get("secondary_affiliate")

        try:
            from services import services

            # ── Step 1: Acquire Postgres topic lock ────────────────────
            acquired = await services.workflows.acquire_topic_lock(
                topic_wp_id=selected_topic["id"],
                run_id=run_id,
            )

            if not acquired:
                self.log.info(
                    "Topic lock not acquired — another run in progress",
                    run_id=run_id,
                    topic_id=selected_topic.get("id"),
                )
                return {
                    "topic_lock_acquired": False,
                    "current_stage": "stage1.brief_locker",
                    "status": "failed",
                    "errors": state.get("errors", []) + [{
                        "stage": "stage1.brief_locker",
                        "error": f"Topic {selected_topic.get('id')} is already locked by another run",
                    }],
                }

            # ── Step 2: Assemble draft brief ───────────────────────────
            draft_brief = self._assemble_draft_brief(
                selected_topic, primary_affiliate, secondary_affiliate, run_id,
            )

            # ── Step 3: LLM coherence check ────────────────────────────
            prompt = self._build_coherence_prompt(selected_topic, primary_affiliate)
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

            await self._emit_event(EventType.STAGE_STARTED, run_id, {
                "model": self.model_config.model_id,
            })
            await self._write_stage_record(
                run_id, status="running", attempt=1, prompt_hash=prompt_hash,
            )

            result = await self.call_llm(prompt, run_id, attempt=1)

            # ── Step 4: Enrich brief with LLM output ──────────────────
            enrichments = result.output  # validated JSON from JSONOutputMixin
            coherence_score = enrichments.get("coherence_score", 0)

            if coherence_score < 0.60 or not enrichments.get("proceed", True):
                # Brief incoherent — route to HITL
                self.log.warning(
                    f"Brief coherence too low: {coherence_score}",
                    run_id=run_id,
                )
                full_brief = {**draft_brief, "meta": {
                    **draft_brief["meta"],
                    "validation_passed": False,
                    "coherence_score": coherence_score,
                }}
                return {
                    "brief": full_brief,
                    "topic_lock_acquired": True,
                    "current_stage": "stage1.brief_locker",
                    "hitl_required": True,
                    "hitl_stage": "stage1.brief_locker",
                    "hitl_reason": f"Brief coherence score {coherence_score:.2f} below 0.60 threshold",
                }

            # Enrich the brief with LLM-generated reader insights
            full_brief = {
                **draft_brief,
                "meta": {
                    **draft_brief["meta"],
                    "validation_passed": True,
                    "coherence_score": coherence_score,
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

            # ── Step 5: Fire-and-forget WP display status ─────────────
            asyncio.create_task(
                services.topics.mark_topic_running(selected_topic["id"], run_id)
            )

            await self._emit_event(EventType.STAGE_COMPLETE, run_id, {
                "coherence_score": coherence_score,
                "cost_usd": result.cost_usd,
            })
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True,
                score=coherence_score,
                output={"coherence_score": coherence_score, "proceed": True},
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
                prompt_hash=prompt_hash,
            )

            return {
                "brief": full_brief,
                "topic_lock_acquired": True,
                "current_stage": "stage1.brief_locker",
                "model_usage": state.get("model_usage", []) + [{
                    "stage": self.stage_name,
                    "model": self.model_config.model_id,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "cost_usd": result.cost_usd,
                }],
            }

        except (LLMTimeoutError, LLMRateLimitError, LLMProviderError, ValueError) as exc:
            self.log.error(f"BriefLocker LLM failed: {exc}", run_id=run_id)
            failure = await self._handle_failure(run_id, str(exc))
            return {
                "topic_lock_acquired": True,  # lock was acquired before LLM call
                "current_stage": "stage1.brief_locker",
                "hitl_required": failure.meta.get("human_in_the_loop", False),
                "hitl_stage": "stage1.brief_locker",
                "hitl_reason": str(exc),
                "status": "hitl" if failure.meta.get("human_in_the_loop") else "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage1.brief_locker",
                    "error": str(exc),
                }],
            }
        except Exception as exc:
            self.log.error(f"BriefLocker failed: {exc}", run_id=run_id)
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "current_stage": "stage1.brief_locker",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage1.brief_locker",
                    "error": str(exc),
                }],
            }

    def _assemble_draft_brief(
        self, topic: dict, primary: dict, secondary: dict | None, run_id: int,
    ) -> dict:
        return {
            "topic": topic,
            "affiliate": {
                "primary": primary,
                "secondary": secondary,
            },
            "meta": {
                "run_id": run_id,
                "coherence_score": 0,
                "validation_passed": False,
                "warnings": [],
            },
            "reader": {
                "profile": "",
                "moment": "",
                "article_angle": "",
            },
        }

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
            "AFFILIATE_KEY": affiliate.get("name", "").lower().replace(" ", "-"),
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