"""
Stage 1.4 — AffiliateScorer

Scores and ranks affiliates against the selected topic.
Uses geo×0.4 + product×0.4 + commission×0.2 formula.
Sets primary_affiliate and secondary_affiliate in state.
"""

from __future__ import annotations

from nodes.base import BaseAgent, EventType


class AffiliateScorer(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="affiliate_scorer",
            stage_name="research.stage1.affiliate_scorer",
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        selected_topic = state.get("selected_topic") or {}
        candidates = state.get("candidate_affiliates") or []

        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            from services import services

            scored = await services.affiliates.score_affiliates_for_topic(
                topic=selected_topic,
                affiliates=candidates,
            )

            if not scored:
                error_msg = (
                    f"No affiliates scored above threshold for topic "
                    f"'{selected_topic.get('title', 'unknown')}'"
                )
                self.log.warning(error_msg, run_id=run_id)
                await self._write_stage_record(
                    run_id, status="failed", attempt=1, error=error_msg,
                )
                return {
                    "scored_affiliates": [],
                    "primary_affiliate": None,
                    "secondary_affiliate": None,
                    "current_stage": "stage1.affiliate_scorer",
                    "status": "failed",
                    "errors": state.get("errors", []) + [{
                        "stage": "stage1.affiliate_scorer",
                        "error": error_msg,
                    }],
                }

            primary = scored[0]
            secondary = scored[1] if len(scored) > 1 else None

            output = {
                "primary": primary["name"],
                "primary_score": primary["fit_score"],
                "secondary": secondary["name"] if secondary else None,
                "total_qualified": len(scored),
            }
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True, output=output,
            )

            return {
                "scored_affiliates": scored,
                "primary_affiliate": primary,
                "secondary_affiliate": secondary,
                "current_stage": "stage1.affiliate_scorer",
            }

        except Exception as exc:
            self.log.error(f"AffiliateScorer failed: {exc}", run_id=run_id)
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "scored_affiliates": [],
                "primary_affiliate": None,
                "secondary_affiliate": None,
                "current_stage": "stage1.affiliate_scorer",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage1.affiliate_scorer",
                    "error": str(exc),
                }],
            }