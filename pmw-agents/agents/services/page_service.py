"""
PageManagementService — create/update WordPress affiliate intelligence pages via GraphQL.

Owns:
  - Finding existing WP pages by slug (GraphQL query)
  - Creating new WP pages for affiliate intelligence (GraphQL mutation)
  - Updating existing pages with aggregated intelligence data (GraphQL mutation)

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
    """Stateless service — WordPress access via get_infrastructure() (GraphQL)."""

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
        then rendered by the WordPress theme/React frontend.

        Args:
            affiliate: Affiliate dict with name, partner_key, url, etc.
            aggregated_data: Summary dict from AffiliateService.rebuild_intelligence_summary().

        Returns:
            WP page ID (int), or None if the operation failed.
        """
        infra = get_infrastructure()
        partner_key = affiliate.get("name", "").lower().replace(" ", "-")
        slug = f"affiliates-{partner_key}"
        title = f"{affiliate.get('name', 'Unknown')} — Investment Intelligence"

        # Build the meta payload for the page
        page_meta = {
            "pmw_intelligence_data": json.dumps(aggregated_data),
            "pmw_intelligence_updated": aggregated_data.get("last_run_at", ""),
            "pmw_partner_key": partner_key,
            "pmw_pending_review": str(aggregated_data.get("has_pending_review", False)),
        }

        try:
            # Check if page already exists by slug
            existing = await infra.wordpress.find_page_by_slug(slug)

            if existing and existing.get("id"):
                # Update existing page
                page_id = existing["id"]
                success = await infra.wordpress.update_page(
                    page_id=page_id,
                    title=title,
                    meta=page_meta,
                )
                if success:
                    log.info(f"Updated affiliate page: {slug} (ID={page_id})")
                    return page_id
                else:
                    log.warning(f"Affiliate page update returned false for {slug}")
                    return page_id  # page exists even if update had issues
            else:
                # Create new page
                new_id = await infra.wordpress.create_page(
                    title=title,
                    slug=slug,
                    status="PUBLISH",
                    meta=page_meta,
                )
                if new_id:
                    log.info(f"Created affiliate page: {slug} (ID={new_id})")
                return new_id

        except Exception as exc:
            log.error(
                f"Affiliate page upsert failed for {slug}",
                extra={"error": str(exc)},
            )
            return None