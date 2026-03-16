"""
MarketService — live price, trends, news, and market stance for Stage 3.

Owns:
  - Fetching live spot prices via infra.price
  - Computing price trends from historical data
  - Fetching recent news via infra.news
  - Deriving market_stance algorithmically from price data

Does NOT own:
  - HTTP transport (PriceClient / NewsClient via infrastructure)
  - LLM synthesis of market context (Stage 3 node owns that)

Usage:
    from services import services
    price = await services.market.get_spot_price("gold", "uk")
    trend = await services.market.get_price_trend("gold", days=30)
    news  = await services.market.get_recent_news("gold price", "uk")
    stance = services.market.derive_market_stance(price, trend)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.market")


# Market stance thresholds (from Research README Section 6)
STANCE_THRESHOLDS = {
    "bull_run":               {"min_30d": 5.0,  "news_sentiment": "positive"},
    "cautious_optimism":      {"min_30d": 5.0,  "news_sentiment": "mixed"},
    "steady_hold":            {"min_30d": -2.0, "max_30d": 2.0},
    "correction_opportunity": {"max_30d": -2.0, "news_sentiment": "recovery"},
    "defensive_position":     {"max_30d": -5.0, "news_sentiment": "negative"},
}


class MarketService:
    """Stateless service — price/news access via get_infrastructure()."""

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
        infra = get_infrastructure()

        try:
            result = await infra.price.get_spot_price(asset_class, geography)
            return result
        except Exception as exc:
            log.warning(
                f"Spot price fetch failed for {asset_class}",
                extra={"error": str(exc)},
            )
            return {
                "price_gbp": None,
                "price_usd": None,
                "currency": "GBP" if geography == "uk" else "USD",
                "asset": asset_class,
                "source": "unavailable",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

    # ── Price trend ────────────────────────────────────────────────────────

    async def get_price_trend(
        self,
        asset_class: str,
        days: int = 30,
        geography: str = "uk",
    ) -> dict:
        """
        Fetch historical price and compute % change over the given period.

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
        infra = get_infrastructure()

        try:
            result = await infra.price.get_historical(asset_class, days, geography)
            return result
        except Exception as exc:
            log.warning(
                f"Price trend fetch failed for {asset_class} ({days}d)",
                extra={"error": str(exc)},
            )
            return {
                "trend_pct": None,
                "period_days": days,
                "start_price": None,
                "end_price": None,
                "high": None,
                "low": None,
            }

    # ── Recent news ────────────────────────────────────────────────────────

    async def get_recent_news(
        self,
        keyword: str,
        geography: str = "uk",
        days_back: int = 30,
        min_results: int = 3,
    ) -> list[dict]:
        """
        Fetch recent news articles relevant to the keyword.

        Returns:
            List of news dicts with title, source, date, summary, url.
        """
        infra = get_infrastructure()

        try:
            articles = await infra.news.search(
                keyword=keyword,
                geography=geography,
                days_back=days_back,
            )
            if len(articles) < min_results:
                log.info(
                    f"Only {len(articles)} news articles found (min {min_results})",
                    extra={"keyword": keyword},
                )
            return articles
        except Exception as exc:
            log.warning(
                f"News fetch failed for '{keyword}'",
                extra={"error": str(exc)},
            )
            return []

    # ── Market stance derivation (pure algorithm — no API call) ────────────

    @staticmethod
    def derive_market_stance(
        price_data: dict,
        trend_30d: dict | None = None,
        trend_90d: dict | None = None,
        news_articles: list[dict] | None = None,
    ) -> dict:
        """
        Derive market stance algorithmically from price data and news.

        Market stance rules (from Research README):
          - Price up >5% in 30d AND positive news → 'bull_run'
          - Price up >5% in 30d BUT mixed news → 'cautious_optimism'
          - Price flat (±2%) → 'steady_hold'
          - Price down but news suggests recovery → 'correction_opportunity'
          - Price down with negative outlook → 'defensive_position'

        Also derives emotional_trigger:
          - bull_run / cautious_optimism → 'greed'
          - correction_opportunity → 'curiosity'
          - defensive_position → 'fear'
          - steady_hold → 'curiosity'

        Returns:
            {
                "market_stance": str,
                "emotional_trigger": str,
                "stance_rationale": str,
            }
        """
        pct_30d = (trend_30d or {}).get("trend_pct") or 0.0
        pct_90d = (trend_90d or {}).get("trend_pct") or 0.0

        # Simple news sentiment heuristic
        news_sentiment = MarketService._assess_news_sentiment(news_articles or [])

        # Determine stance
        if pct_30d > 5.0 and news_sentiment in ("positive", "neutral"):
            stance = "bull_run"
            rationale = f"Price up {pct_30d:.1f}% in 30 days with {news_sentiment} news sentiment."
        elif pct_30d > 5.0:
            stance = "cautious_optimism"
            rationale = f"Price up {pct_30d:.1f}% in 30 days but mixed news signals."
        elif -2.0 <= pct_30d <= 2.0:
            stance = "steady_hold"
            rationale = f"Price relatively flat ({pct_30d:+.1f}% over 30 days)."
        elif pct_30d < -2.0 and news_sentiment in ("positive", "recovery"):
            stance = "correction_opportunity"
            rationale = f"Price down {pct_30d:.1f}% but news suggests potential recovery."
        elif pct_30d < -5.0:
            stance = "defensive_position"
            rationale = f"Price down {pct_30d:.1f}% in 30 days with negative outlook."
        else:
            stance = "steady_hold"
            rationale = f"Moderate movement ({pct_30d:+.1f}% over 30 days)."

        # Emotional trigger mapping
        trigger_map = {
            "bull_run": "greed",
            "cautious_optimism": "greed",
            "steady_hold": "curiosity",
            "correction_opportunity": "curiosity",
            "defensive_position": "fear",
        }

        return {
            "market_stance": stance,
            "emotional_trigger": trigger_map.get(stance, "curiosity"),
            "stance_rationale": rationale,
            "price_trend_pct_30d": pct_30d,
            "price_trend_pct_90d": pct_90d,
            "news_sentiment": news_sentiment,
        }

    @staticmethod
    def _assess_news_sentiment(articles: list[dict]) -> str:
        """
        Simple keyword-based news sentiment assessment.
        Returns: "positive" | "negative" | "mixed" | "neutral"
        """
        if not articles:
            return "neutral"

        positive_words = {"surge", "rally", "high", "gain", "record", "bull", "rise", "growth", "strong"}
        negative_words = {"crash", "drop", "fall", "decline", "bear", "sell", "slump", "weak", "loss"}

        pos_count = 0
        neg_count = 0

        for article in articles:
            text = (
                (article.get("title") or "") + " " +
                (article.get("summary") or "") + " " +
                (article.get("description") or "")
            ).lower()
            pos_count += sum(1 for w in positive_words if w in text)
            neg_count += sum(1 for w in negative_words if w in text)

        if pos_count > neg_count * 2:
            return "positive"
        elif neg_count > pos_count * 2:
            return "negative"
        elif pos_count > 0 and neg_count > 0:
            return "mixed"
        return "neutral"