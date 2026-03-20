"""
Stage 1.3 — AffiliateLoader

Fetches affiliate dealers from WordPress (dealer CPT via GraphQL),
syncs them to the Postgres affiliates table, then returns all active
affiliates from Postgres.

This mirrors the TopicLoader pattern:
  1. GET dealers from WordPress via GraphQL (source of truth)
  2. UPSERT each dealer into Postgres affiliates table (working copy)
  3. Return active affiliates from Postgres

If WordPress is unreachable, falls back to whatever is already in
Postgres — the pipeline doesn't fail just because WP is temporarily down.

If no affiliates are found (neither from WP nor Postgres), sets
status="failed" which triggers the conditional edge in research_graph
to route to handle_failure.
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
            #
            # Non-fatal: if WP is down we fall back to Postgres.
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
            #
            # Non-fatal: if sync fails, Postgres may already have data
            # from a previous successful sync.
            if wp_dealers:
                try:
                    synced = await services.affiliates.sync_to_postgres(wp_dealers)
                    self.log.info(
                        f"Synced {synced} dealer(s) to Postgres",
                        run_id=run_id,
                    )
                except Exception as sync_exc:
                    self.log.warning(
                        f"Postgres sync failed (using existing data): {sync_exc}",
                        run_id=run_id,
                    )
            else:
                self.log.info(
                    "No dealers from WordPress — using existing Postgres data",
                    run_id=run_id,
                )

            # ── Step 3: Load active affiliates from Postgres ──────────
            #
            # This is the critical step. If THIS fails, the node fails.
            affiliates = await services.affiliates.get_active_affiliates()

            if not affiliates:
                error_msg = (
                    "No active affiliates found in Postgres. "
                    "Check: (1) WordPress dealer CPT has published dealers "
                    "with 'Active in Pipeline' checked, (2) migration "
                    "007_affiliates_wp_sync has been applied, (3) at least "
                    "one previous sync succeeded."
                )
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

            self.log.info(
                f"AffiliateLoader complete: {len(affiliates)} active affiliate(s)",
                run_id=run_id,
            )

            return {
                "candidate_affiliates": affiliates,
                "current_stage": "stage1.affiliate_loader",
                # Do NOT return "status" on success.
                # The initial state has status="running" which is correct.
                # _route_on_status only checks for status=="failed".
                # Not returning "status" means LangGraph keeps the existing
                # value ("running"), and the router returns "continue".
            }

        except Exception as exc:
            error_str = str(exc)
            self.log.error(
                f"AffiliateLoader unexpected error: {error_str}",
                run_id=run_id,
            )
            await self._write_stage_record(
                run_id, status="failed", attempt=1, error=error_str,
            )
            return {
                "candidate_affiliates": [],
                "current_stage": "stage1.affiliate_loader",
                "status": "failed",
                "errors": state.get("errors", []) + [{
                    "stage": "stage1.affiliate_loader",
                    "error": error_str,
                }],
            }