"""
PriceClient — precious metals price API transport.

Owns:
  - Live spot price fetching
  - Historical price data for trend calculations
  - Response normalisation to standard dicts

Supports multiple price APIs via configuration:
  - MetalPriceAPI (default if METAL_PRICE_API_KEY is set)
  - Fallback: GoldAPI.io or hardcoded test data

Does NOT own:
  - Trend calculation logic (MarketService owns that)
  - Market stance derivation (MarketService owns that)

Lifecycle:
    infra.price is instantiated in Infrastructure.__init__
    No connect()/close() needed — uses infra.http for transport.

Usage:
    price = await infra.price.get_spot_price("gold", "uk")
    trend = await infra.price.get_historical("gold", days=30, geography="uk")
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

log = logging.getLogger("pmw.infra.price")

# API endpoints
METALS_API_BASE = "https://api.metalpriceapi.com/v1"
GOLDAPI_BASE = "https://www.goldapi.io/api"

# Asset class to API symbol mapping
ASSET_SYMBOLS = {
    "gold": "XAU",
    "silver": "XAG",
    "platinum": "XPT",
    "palladium": "XPD",
}

# Currency mapping by geography
GEO_CURRENCY = {
    "uk": "GBP",
    "us": "USD",
    "global": "USD",
}


class PriceClient:
    """
    Precious metals price client.
    Uses MetalPriceAPI if key is configured, otherwise falls back
    to GoldAPI.io or returns unavailable status.
    """

    def __init__(self, http=None) -> None:
        self._http = http
        self._metal_price_key = os.environ.get("METAL_PRICE_API_KEY", "")
        self._goldapi_key = os.environ.get("GOLDAPI_KEY", "")

    def set_http(self, http) -> None:
        """Called by Infrastructure after HTTPClient is connected."""
        self._http = http

    def _require_http(self):
        if self._http is None:
            raise RuntimeError(
                "PriceClient has no HTTPClient. "
                "Ensure Infrastructure.connect() has been called."
            )
        return self._http

    # ── Live spot price ────────────────────────────────────────────────────

    async def get_spot_price(
        self,
        asset_class: str,
        geography: str = "uk",
    ) -> dict:
        """
        Fetch live spot price for an asset class.

        Returns:
            {
                "price_gbp": float | None,
                "price_usd": float | None,
                "currency": "GBP" | "USD",
                "asset": str,
                "source": str,
                "fetched_at": str (ISO),
            }
        """
        symbol = ASSET_SYMBOLS.get(asset_class.lower())
        currency = GEO_CURRENCY.get(geography.lower(), "GBP")

        if not symbol:
            log.warning(f"Unknown asset class: {asset_class}")
            return self._empty_price(asset_class, currency)

        # Try MetalPriceAPI first
        if self._metal_price_key:
            result = await self._fetch_metalprice(symbol, currency)
            if result:
                return result

        # Fallback to GoldAPI
        if self._goldapi_key:
            result = await self._fetch_goldapi(symbol, currency)
            if result:
                return result

        log.warning(f"No price API configured for {asset_class}")
        return self._empty_price(asset_class, currency)

    # ── Historical prices ──────────────────────────────────────────────────

    async def get_historical(
        self,
        asset_class: str,
        days: int = 30,
        geography: str = "uk",
    ) -> dict:
        """
        Fetch historical prices and compute trend.

        Returns:
            {
                "trend_pct": float | None,
                "period_days": int,
                "start_price": float | None,
                "end_price": float | None,
                "high": float | None,
                "low": float | None,
            }
        """
        symbol = ASSET_SYMBOLS.get(asset_class.lower())
        currency = GEO_CURRENCY.get(geography.lower(), "GBP")

        if not symbol:
            return self._empty_trend(days)

        # Try MetalPriceAPI historical endpoint
        if self._metal_price_key:
            result = await self._fetch_historical_metalprice(symbol, currency, days)
            if result:
                return result

        # Fallback: estimate from current price (not ideal, but better than nothing)
        log.warning(f"No historical price data available for {asset_class}")
        return self._empty_trend(days)

    # ── MetalPriceAPI implementation ───────────────────────────────────────

    async def _fetch_metalprice(self, symbol: str, currency: str) -> dict | None:
        """Fetch from MetalPriceAPI /v1/latest endpoint."""
        http = self._require_http()

        try:
            resp = await http.get(
                f"{METALS_API_BASE}/latest",
                params={
                    "api_key": self._metal_price_key,
                    "base": currency,
                    "currencies": symbol,
                },
            )
            data = resp.json()

            if not data.get("success"):
                log.warning(f"MetalPriceAPI error: {data.get('error', {})}")
                return None

            rates = data.get("rates", {})
            # MetalPriceAPI returns rates as currency per 1 oz of metal
            # Rate = price of 1 unit of currency in metal
            # So price of 1 oz metal in currency = 1 / rate
            rate = rates.get(symbol)
            if rate and rate > 0:
                price = round(1.0 / rate, 2)
            else:
                return None

            return {
                "price_gbp": price if currency == "GBP" else None,
                "price_usd": price if currency == "USD" else None,
                "currency": currency,
                "asset": symbol,
                "source": "metalpriceapi",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as exc:
            log.warning(f"MetalPriceAPI fetch failed: {exc}")
            return None

    async def _fetch_historical_metalprice(
        self, symbol: str, currency: str, days: int
    ) -> dict | None:
        """Fetch historical data from MetalPriceAPI."""
        http = self._require_http()
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        try:
            # Fetch start date price
            resp_start = await http.get(
                f"{METALS_API_BASE}/{start_date}",
                params={
                    "api_key": self._metal_price_key,
                    "base": currency,
                    "currencies": symbol,
                },
            )
            data_start = resp_start.json()

            # Fetch current price
            resp_end = await http.get(
                f"{METALS_API_BASE}/latest",
                params={
                    "api_key": self._metal_price_key,
                    "base": currency,
                    "currencies": symbol,
                },
            )
            data_end = resp_end.json()

            start_rate = (data_start.get("rates") or {}).get(symbol)
            end_rate = (data_end.get("rates") or {}).get(symbol)

            if not start_rate or not end_rate or start_rate == 0 or end_rate == 0:
                return None

            start_price = round(1.0 / start_rate, 2)
            end_price = round(1.0 / end_rate, 2)
            trend_pct = round(((end_price - start_price) / start_price) * 100, 2)

            return {
                "trend_pct": trend_pct,
                "period_days": days,
                "start_price": start_price,
                "end_price": end_price,
                "high": None,  # Would need time-series data for this
                "low": None,
            }

        except Exception as exc:
            log.warning(f"MetalPriceAPI historical fetch failed: {exc}")
            return None

    # ── GoldAPI fallback ───────────────────────────────────────────────────

    async def _fetch_goldapi(self, symbol: str, currency: str) -> dict | None:
        """Fetch from GoldAPI.io."""
        http = self._require_http()

        try:
            resp = await http.get(
                f"{GOLDAPI_BASE}/{symbol}/{currency}",
                headers={
                    "x-access-token": self._goldapi_key,
                    "Content-Type": "application/json",
                },
            )
            data = resp.json()
            price = data.get("price")

            if not price:
                return None

            return {
                "price_gbp": price if currency == "GBP" else None,
                "price_usd": price if currency == "USD" else None,
                "currency": currency,
                "asset": symbol,
                "source": "goldapi",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as exc:
            log.warning(f"GoldAPI fetch failed: {exc}")
            return None

    # ── Empty result helpers ───────────────────────────────────────────────

    @staticmethod
    def _empty_price(asset_class: str, currency: str) -> dict:
        return {
            "price_gbp": None,
            "price_usd": None,
            "currency": currency,
            "asset": asset_class,
            "source": "unavailable",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _empty_trend(days: int) -> dict:
        return {
            "trend_pct": None,
            "period_days": days,
            "start_price": None,
            "end_price": None,
            "high": None,
            "low": None,
        }