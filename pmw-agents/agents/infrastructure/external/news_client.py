"""
NewsClient — news API transport for market context research.

Owns:
  - News API HTTP requests via the shared HTTPClient
  - Response parsing to clean dicts
  - Fallback to Google News RSS if NewsAPI key is not configured

Does NOT own:
  - HTTP connection management (HTTPClient owns that)
  - Business logic about what news means (MarketService owns that)

Lifecycle (called by Infrastructure):
    infra.news is instantiated in Infrastructure.__init__
    No connect()/close() needed — uses infra.http for transport.

Usage:
    articles = await infra.news.search("gold price UK", geography="uk", days_back=30)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote_plus

log = logging.getLogger("pmw.infra.news")

NEWSAPI_BASE = "https://newsapi.org/v2/everything"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"


class NewsClient:
    """
    News API client. Uses NewsAPI.org if API key is configured,
    falls back to Google News RSS (no auth required) otherwise.
    """

    def __init__(self, http=None, api_key: str | None = None) -> None:
        self._http = http
        self._api_key = api_key or os.environ.get("NEWS_API_KEY", "")

    def set_http(self, http) -> None:
        """Called by Infrastructure after HTTPClient is connected."""
        self._http = http

    def _require_http(self):
        if self._http is None:
            raise RuntimeError(
                "NewsClient has no HTTPClient. "
                "Ensure Infrastructure.connect() has been called."
            )
        return self._http

    async def search(
        self,
        keyword: str,
        geography: str = "uk",
        days_back: int = 30,
        max_results: int = 10,
    ) -> list[dict]:
        """
        Search for recent news articles matching the keyword.

        Tries NewsAPI.org first (if key configured), falls back to
        Google News RSS parsing.

        Args:
            keyword: Search query.
            geography: "uk" | "us" | "global".
            days_back: How far back to search.
            max_results: Maximum articles to return.

        Returns:
            List of article dicts with title, source, date, summary, url.
        """
        if self._api_key:
            return await self._search_newsapi(keyword, geography, days_back, max_results)
        else:
            return await self._search_google_rss(keyword, geography, max_results)

    # ── NewsAPI.org ────────────────────────────────────────────────────────

    async def _search_newsapi(
        self,
        keyword: str,
        geography: str,
        days_back: int,
        max_results: int,
    ) -> list[dict]:
        """Search via NewsAPI.org /v2/everything endpoint."""
        http = self._require_http()
        from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # Language mapping
        language = {"uk": "en", "us": "en", "global": "en"}.get(geography, "en")

        params = {
            "q": keyword,
            "from": from_date,
            "sortBy": "relevancy",
            "language": language,
            "pageSize": min(max_results, 100),
            "apiKey": self._api_key,
        }

        try:
            resp = await http.get(NEWSAPI_BASE, params=params)
            data = resp.json()

            articles = []
            for item in data.get("articles", [])[:max_results]:
                articles.append({
                    "title": item.get("title", ""),
                    "source": (item.get("source") or {}).get("name", ""),
                    "published_at": item.get("publishedAt", ""),
                    "summary": (item.get("description") or "")[:300],
                    "url": item.get("url", ""),
                })

            log.info(f"NewsAPI: {len(articles)} articles for '{keyword}'")
            return articles

        except Exception as exc:
            log.warning(f"NewsAPI search failed: {exc}")
            # Fall back to Google News RSS
            return await self._search_google_rss(keyword, geography, max_results)

    # ── Google News RSS fallback ───────────────────────────────────────────

    async def _search_google_rss(
        self,
        keyword: str,
        geography: str,
        max_results: int,
    ) -> list[dict]:
        """
        Fallback: parse Google News RSS feed for the keyword.
        No API key required. Returns less structured data than NewsAPI.
        """
        http = self._require_http()

        # Google News RSS with geo parameter
        geo_param = {"uk": "GB", "us": "US", "global": ""}.get(geography, "")
        encoded_query = quote_plus(keyword)
        url = f"{GOOGLE_NEWS_RSS}?q={encoded_query}&hl=en&gl={geo_param}&ceid={geo_param}:en"

        try:
            resp = await http.get(
                url,
                headers={"User-Agent": "PMW-Research-Agent/1.0"},
            )
            xml_text = resp.text

            # Parse RSS XML
            articles = self._parse_rss(xml_text, max_results)
            log.info(f"Google News RSS: {len(articles)} articles for '{keyword}'")
            return articles

        except Exception as exc:
            log.warning(f"Google News RSS fetch failed: {exc}")
            return []

    @staticmethod
    def _parse_rss(xml_text: str, max_results: int) -> list[dict]:
        """Parse RSS XML into article dicts."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_text)

            articles = []
            for item in root.findall(".//item")[:max_results]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                source = (item.findtext("source") or "").strip()
                description = (item.findtext("description") or "").strip()

                # Clean HTML from description
                import re
                clean_desc = re.sub(r"<[^>]+>", "", description)[:300]

                if title:
                    articles.append({
                        "title": title,
                        "source": source or "Google News",
                        "published_at": pub_date,
                        "summary": clean_desc,
                        "url": link,
                    })

            return articles

        except Exception:
            return []