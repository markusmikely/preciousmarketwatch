class PriceService(BaseDataService):
    """Fetch current spot prices and trends for precious metals."""
    
    async def fetch(self, asset_class: str, geography: str = "uk") -> dict:
        """
        Returns:
            {
                "spot_price_gbp": float,
                "spot_price_usd": float,
                "currency": "GBP",
                "trend_30d_pct": float,      # e.g. +2.4
                "trend_90d_pct": float,      # e.g. +8.1
                "high_30d": float,
                "low_30d": float,
                "last_updated": "ISO 8601",
                "source": "api_name"
            }
        """