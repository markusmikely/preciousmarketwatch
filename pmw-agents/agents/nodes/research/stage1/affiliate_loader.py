"""
Stage 1a.2 — AffiliateLoader

Fetches ALL affiliate dealers from WordPress, syncs to Postgres,
returns the full active list in all_affiliates.

Brief_builder uses all_affiliates to score every topic against
every affiliate. Individual try/catch blocks ensure WP or sync
failures fall back to existing Postgres data.
"""

from __future__ import annotations

import logging

from nodes.base import BaseAgent, EventType

log = logging.getLogger("pmw.node.affiliate_loader")


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

            # ── Step 1: Fetch dealers from WordPress ──────────────────
            wp_dealers = []
            try:
                wp_dealers = await services.affiliates.fetch_from_wordpress(
                    active_only=False,
                )
                self.log.info(
                    f"Fetched {len(wp_dealers)} dealer(s) from WordPress",
                    run_id=run_id,
                )
            except Exception as wp_exc:
                self.log.warning(
                    f"WordPress dealer fetch failed (falling back to Postgres): {wp_exc}",
                    run_id=run_id,
                )

            # ── Step 2: Sync to Postgres ──────────────────────────────
            if wp_dealers:
                try:
                    synced = await services.affiliates.sync_to_postgres(wp_dealers)
                    self.log.info(f"Synced {synced} dealer(s) to Postgres", run_id=run_id)
                except Exception as sync_exc:
                    self.log.warning(
                        f"Postgres sync failed (using existing data): {sync_exc}",
                        run_id=run_id,
                    )

            # ── Step 3: Load active affiliates from Postgres ──────────
            affiliates = await services.affiliates.get_active_affiliates()

            if not affiliates:
                error_msg = (
                    "No active affiliates found in Postgres. "
                    "Check WordPress dealer CPT has published dealers "
                    "with 'Active in Pipeline' checked."
                )
                self.log.warning(error_msg, run_id=run_id)
                await self._write_stage_record(
                    run_id, status="failed", attempt=1, error=error_msg,
                )
                return {
                    "all_affiliates": [],
                    "current_stage": "stage1.affiliate_loader",
                    "status": "failed",
                    "errors": state.get("errors", []) + [{
                        "stage": "stage1.affiliate_loader",
                        "error": error_msg,
                    }],
                }

            # ── Success ───────────────────────────────────────────────
            output = {
                "count": len(affiliates),
                "affiliate_names": [a["name"] for a in affiliates],
                "wp_synced": len(wp_dealers),
            }
            await self._emit_event(EventType.STAGE_COMPLETE, run_id, output)
            await self._write_stage_record(
                run_id, status="complete", attempt=1,
                passed_threshold=True, output=output,
            )

            return {
                "all_affiliates": affiliates,
                "current_stage": "stage1.affiliate_loader",
            }

        except Exception as exc:
            self.log.error(f"AffiliateLoader failed: {exc}", run_id=run_id)
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=str(exc),
            )
            return {
                "all_affiliates": [],
                "current_stage": "stage1.affiliate_loader",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage1.affiliate_loader",
                    "error": str(exc),
                }],
            }