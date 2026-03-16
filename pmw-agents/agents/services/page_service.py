"""
PageManagementService — create/update WordPress affiliate intelligence pages.

Owns:
  - Finding existing WP pages by slug
  - Creating new WP pages for affiliate intelligence
  - Updating existing pages with aggregated intelligence data

Does NOT own:
  - Intelligence aggregation (AffiliateService owns that)
  - Data collection (BuyerResearchService / MarketService own that)

Usage:
    from services import services
    page_id = await services.pages.upsert_affiliate_intelligence_page(affiliate, summary)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.page_management")


class PageManagementService:
    """Stateless service — WordPress access via get_infrastructure()."""

    async def upsert_affiliate_intelligence_page(
        self,
        affiliate: dict,
        aggregated_data: dict,
    ) -> int | None:
        """
        Create or update the WordPress intelligence page for an affiliate.

        The page slug is deterministic: affiliates-{partner_key}.
        If the page exists, it's updated. If not, it's created.

        Intelligence data is stored in WP post meta as JSON,
        then rendered by the WordPress theme template.

        Args:
            affiliate: Affiliate dict with name, partner_key, url, etc.
            aggregated_data: Summary dict from AffiliateService.rebuild_intelligence_summary().

        Returns:
            WP page ID (int), or None if the operation failed.
        """
        infra = get_infrastructure()
        partner_key = affiliate.get("name", "").lower().replace(" ", "-")
        slug = f"affiliates-{partner_key}"

        # Build the page payload
        page_data = {
            "title": f"{affiliate.get('name', 'Unknown')} — Investment Intelligence",
            "slug": slug,
            "status": "publish",
            "meta": {
                "pmw_intelligence_data": json.dumps(aggregated_data),
                "pmw_intelligence_updated": aggregated_data.get("last_run_at", ""),
                "pmw_partner_key": partner_key,
                "pmw_pending_review": str(aggregated_data.get("has_pending_review", False)),
            },
        }

        try:
            # Check if page already exists by slug
            existing = await infra.wordpress.get_all(
                "/pages",
                params={"slug": slug, "_fields": "id", "per_page": 1},
            )

            if existing and isinstance(existing, list) and len(existing) > 0:
                # Update existing page
                page_id = existing[0].get("id")
                await infra.wordpress.client.request(
                    method="POST",
                    url=f"{infra.wordpress.api_url}/pages/{page_id}",
                    json=page_data,
                )
                log.info(f"Updated affiliate page: {slug} (ID={page_id})")
                return page_id
            else:
                # Create new page
                resp = await infra.wordpress.client.request(
                    method="POST",
                    url=f"{infra.wordpress.api_url}/pages",
                    json=page_data,
                )
                new_id = resp.json().get("id")
                log.info(f"Created affiliate page: {slug} (ID={new_id})")
                return new_id

        except Exception as exc:
            log.error(
                f"Affiliate page upsert failed for {slug}",
                extra={"error": str(exc)},
            )
            return None