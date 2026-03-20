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
to route to handle_failure. This is a genuine error — the pipeline
cannot proceed without at least one affiliate.
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
            # query_dealers() calls WPGraphQL for all published dealer
            # CPT posts with pmwAffiliateActive=true. Returns normalised
            # dicts matching the affiliates table columns.
            #
            # We fetch ALL dealers (active_only=False) for the sync step
            # so that deactivated dealers also get their active=false
            # status synced to Postgres. Only active ones are returned
            # to the pipeline after sync.

            wp_dealers = await services.affiliates.fetch_from_wordpress(
                active_only=False,
            )
            self.log.info(
                f"Fetched {len(wp_dealers)} dealer(s) from WordPress",
                run_id=run_id,
            )

            # ── Step 2: Sync to Postgres (upsert by wp_dealer_id) ─────
            #
            # Each WP dealer is upserted into the affiliates table using
            # wp_dealer_id as the conflict key. This means:
            #   - New dealers in WP → inserted into Postgres
            #   - Existing dealers → all fields updated from WP values
            #   - Deactivated dealers → active=false synced to Postgres
            #
            # If WP returned nothing (network error, empty site), we
            # skip the sync and fall back to existing Postgres data.

            if wp_dealers:
                synced = await services.affiliates.sync_to_postgres(wp_dealers)
                self.log.info(
                    f"Synced {synced} dealer(s) to Postgres",
                    run_id=run_id,
                )
            else:
                self.log.warning(
                    "No dealers from WordPress — using existing Postgres data",
                    run_id=run_id,
                )

            # ── Step 3: Load active affiliates from Postgres ──────────
            #
            # After sync, Postgres is the canonical source for the rest
            # of the pipeline. This ensures affiliate IDs are stable
            # Postgres integers (used as foreign keys in intelligence tables).

            affiliates = await services.affiliates.get_active_affiliates()

            if not affiliates:
                error_msg = (
                    "No active affiliates found. "
                    "Check WordPress dealer CPT has published dealers "
                    "with 'Active in Pipeline' checked."
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
                "wp_synced": len(wp_dealers) if wp_dealers else 0,
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