"""
Stage 1b — AffiliateLoader

Fetches dealers from WordPress, syncs to Postgres, returns all_affiliates.
WP fetch and sync failures are non-fatal — falls back to existing Postgres data.
"""

from __future__ import annotations
from nodes.base import (
    BaseAgent, JSONOutputMixin, ModelConfig, ModelProvider,
    FailureConfig, EventType, AgentStatus,
)

log = logging.getLogger("pmw.node.affiliate_loader")


class AffiliateLoader(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="affiliate_loader", stage_name="research.stage1.affiliate_loader")

    async def run(self, state: dict) -> dict:
        run_id = state["run_id"]
        await self._write_stage(run_id, "running")

        try:
            from services import services

            # Step 1: Fetch from WordPress (non-fatal)
            wp_dealers = []
            try:
                wp_dealers = await services.affiliates.fetch_from_wordpress(active_only=False)
                self.log.info(f"Fetched {len(wp_dealers)} dealer(s) from WordPress")
            except Exception as exc:
                self.log.warning(f"WP dealer fetch failed (using Postgres): {exc}")

            # Step 2: Sync to Postgres (non-fatal)
            if wp_dealers:
                try:
                    synced = await services.affiliates.sync_to_postgres(wp_dealers)
                    self.log.info(f"Synced {synced} dealer(s) to Postgres")
                except Exception as exc:
                    self.log.warning(f"Postgres sync failed (using existing data): {exc}")

            # Step 3: Load from Postgres (this is the critical step)
            affiliates = await services.affiliates.get_active_affiliates()

            if not affiliates:
                error = "No active affiliates found in Postgres"
                await self._write_stage(run_id, "failed", error=error)
                return {"all_affiliates": [], "status": "failed",
                        "errors": state.get("errors", []) + [{"stage": self.stage_name, "error": error}]}

            await self._write_stage(run_id, "complete", passed=True,
                                    output={"count": len(affiliates), "names": [a["name"] for a in affiliates]})

            return {"all_affiliates": affiliates, "current_stage": self.stage_name}

        except Exception as exc:
            self.log.error(f"AffiliateLoader failed: {exc}")
            await self._write_stage(run_id, "failed", error=str(exc))
            return {"all_affiliates": [], "status": "failed",
                    "errors": state.get("errors", []) + [{"stage": self.stage_name, "error": str(exc)}]}