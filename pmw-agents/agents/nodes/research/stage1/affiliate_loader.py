"""
Stage 1.3 — AffiliateLoader

Loads active affiliates from Postgres. Affiliates are managed via
the dashboard/seed scripts and stored in Postgres directly.

If WordPress affiliate data is added in the future, this node would
sync from WP → Postgres similar to TopicLoader. For now, Postgres
is the single source for affiliate definitions.
"""

from __future__ import annotations

from nodes.base import BaseAgent, EventType


class AffiliateLoader(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="affiliate_loader",
            stage_name="research.stage1.affiliate_loader",
        )

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]

        await self._emit_event(EventType.STAGE_STARTED, run_id, {})
        await self._write_stage_record(run_id, status="running", attempt=1)

        try:
            from services import services

            affiliates = await services.affiliates.get_active_affiliates()

            if not affiliates:
                error_msg = "No active affiliates found in Postgres"
                self.log.warning(error_msg, run_id=run_id)
                await self._write_stage_record(
                    run_id, status="failed", attempt=1, error=error_msg,
                )
                return {
                    "candidate_affiliates": [],
                    "current_stage": "stage1.affiliate_loader",
                    "status": "failed",
                    "errors": state.get("errors", []) + [{
                        "stage": "stage1.affiliate_loader",
                        "error": error_msg,
                    }],
                }

            output = {
                "count": len(affiliates),
                "affiliate_names": [a["name"] for a in affiliates],
            }
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True, output=output,
            )

            return {
                "candidate_affiliates": affiliates,
                "current_stage": "stage1.affiliate_loader",
            }

        except Exception as exc:
            self.log.error(f"AffiliateLoader failed: {exc}", run_id=run_id)
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "candidate_affiliates": [],
                "current_stage": "stage1.affiliate_loader",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage1.affiliate_loader",
                    "error": str(exc),
                }],
            }