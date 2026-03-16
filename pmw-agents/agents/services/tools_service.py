"""
ToolsService — load and filter PMW tools for Stage 7 tool mapping.

Owns:
  - Loading available tools from the tool registry
  - Filtering tools by asset_class and geography
  - Returning structured tool dicts for LLM tool mapping

The tool registry is currently in-code (TOOL_REGISTRY below).
Phase 2: move to a Postgres table or WP custom post type.

Usage:
    from services import services
    tools = await services.tools.get_available_tools("gold", "uk")
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("pmw.services.tools")


# ── Tool registry — move to DB in Phase 2 ─────────────────────────────────
# Each tool has: name, url, description, asset_classes, geographies, tool_type

TOOL_REGISTRY: list[dict] = [
    {
        "name": "Gold Value Calculator",
        "url": "https://preciousmarketwatch.com/tools/gold-calculator/",
        "description": "Calculate the current value of gold by weight and purity.",
        "asset_classes": ["gold"],
        "geographies": ["uk", "us", "global"],
        "tool_type": "calculator",
    },
    {
        "name": "Silver Value Calculator",
        "url": "https://preciousmarketwatch.com/tools/silver-calculator/",
        "description": "Calculate the current value of silver by weight.",
        "asset_classes": ["silver"],
        "geographies": ["uk", "us", "global"],
        "tool_type": "calculator",
    },
    {
        "name": "Investment Return Calculator",
        "url": "https://preciousmarketwatch.com/tools/investment-calculator/",
        "description": "See how much gold, silver, or platinum would have returned over any period.",
        "asset_classes": ["gold", "silver", "platinum"],
        "geographies": ["uk", "us", "global"],
        "tool_type": "calculator",
    },
    {
        "name": "Dealer Comparison Table",
        "url": "https://preciousmarketwatch.com/tools/compare-dealers/",
        "description": "Compare UK gold dealers on price, storage, fees, and regulation.",
        "asset_classes": ["gold", "silver", "platinum"],
        "geographies": ["uk"],
        "tool_type": "comparison",
    },
    {
        "name": "Portfolio Tracker",
        "url": "https://preciousmarketwatch.com/tools/portfolio-tracker/",
        "description": "Track your precious metals portfolio value in real time.",
        "asset_classes": ["gold", "silver", "platinum"],
        "geographies": ["uk", "us", "global"],
        "tool_type": "tracker",
    },
    {
        "name": "Scrap Gold Calculator",
        "url": "https://preciousmarketwatch.com/tools/scrap-gold-calculator/",
        "description": "Calculate the melt value of scrap gold jewellery by carat.",
        "asset_classes": ["gold"],
        "geographies": ["uk"],
        "tool_type": "calculator",
    },
    {
        "name": "Gold/Silver Ratio Tracker",
        "url": "https://preciousmarketwatch.com/tools/gold-silver-ratio/",
        "description": "Track the live gold-to-silver ratio with historical chart.",
        "asset_classes": ["gold", "silver"],
        "geographies": ["uk", "us", "global"],
        "tool_type": "tracker",
    },
    {
        "name": "Gold IRA Eligibility Checker",
        "url": "https://preciousmarketwatch.com/tools/gold-ira-checker/",
        "description": "Check if you qualify for a gold IRA and estimate tax benefits.",
        "asset_classes": ["gold", "ira"],
        "geographies": ["us"],
        "tool_type": "checker",
    },
    {
        "name": "Storage Cost Comparison",
        "url": "https://preciousmarketwatch.com/tools/storage-costs/",
        "description": "Compare vault storage costs across leading providers.",
        "asset_classes": ["gold", "silver", "platinum"],
        "geographies": ["uk", "global"],
        "tool_type": "comparison",
    },
]


class ToolsService:
    """Stateless service — reads from in-code registry (Phase 2: DB)."""

    async def get_available_tools(
        self,
        asset_class: str = "",
        geography: str = "uk",
    ) -> list[dict]:
        """
        Load and filter tools by asset class and geography.

        Args:
            asset_class: "gold" | "silver" | "platinum" | "ira" | "" (all).
            geography: "uk" | "us" | "global".

        Returns:
            List of tool dicts matching the filters.
        """
        asset = asset_class.lower().strip()
        geo = geography.lower().strip()

        tools = []
        for tool in TOOL_REGISTRY:
            # Filter by asset class (if specified)
            if asset and asset not in tool.get("asset_classes", []):
                continue

            # Filter by geography
            tool_geos = tool.get("geographies", [])
            if geo not in tool_geos and "global" not in tool_geos:
                continue

            tools.append({
                "name": tool["name"],
                "url": tool["url"],
                "description": tool["description"],
                "tool_type": tool["tool_type"],
            })

        log.info(
            f"Tools loaded: {len(tools)} matching asset_class={asset or 'any'}, geo={geo}",
        )
        return tools