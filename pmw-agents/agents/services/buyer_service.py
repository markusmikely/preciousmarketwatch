"""
BuyerResearchService — fetch buyer psychology sources for Stage 6.

Owns:
  - Reddit thread search via infra.reddit
  - MoneySavingExpert forum search via infra.http + BeautifulSoup
  - Affiliate FAQ page fetch via infra.http + BeautifulSoup
  - Redis caching of fetched sources (1h TTL)

Does NOT own:
  - LLM synthesis of buyer psychology (Stage 6b node owns that)
  - PAA questions (already in state from Stage 2)

Usage:
    from services import services
    reddit = await services.buyer.fetch_reddit("gold ISA", "uk")
    mse    = await services.buyer.fetch_mse("gold ISA")
    faq    = await services.buyer.fetch_affiliate_faq("https://bullionvault.com/faq")
    key    = await services.buyer.cache_sources(run_id=42, sources={...})
"""

from __future__ import annotations

import json
import logging
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.buyer")

# Subreddit mapping by geography
GEO_SUBREDDITS = {
    "uk":     ["Gold", "UKInvesting", "Silverbugs", "PreciousMetals"],
    "us":     ["Gold", "personalfinance", "Silverbugs", "PreciousMetals"],
    "global": ["Gold", "PreciousMetals", "Silverbugs"],
}


class BuyerResearchService:
    """Stateless service — HTTP/Redis access via get_infrastructure()."""

    # ── Reddit ─────────────────────────────────────────────────────────────

    async def fetch_reddit(
        self,
        keyword: str,
        geography: str = "uk",
        limit: int = 5,
    ) -> list[dict]:
        """
        Search Reddit for buyer discussions matching the keyword.

        Uses infra.reddit.search() which handles the Reddit JSON API,
        subreddit allow-list enforcement, and response parsing.

        Args:
            keyword: Search query (e.g. "gold ISA UK").
            geography: "uk" | "us" | "global" — selects subreddit set.
            limit: Max posts per subreddit.

        Returns:
            List of post dicts with title, selftext, score, url, source.
        """
        infra = get_infrastructure()
        subreddits = GEO_SUBREDDITS.get(geography.lower(), GEO_SUBREDDITS["uk"])

        try:
            posts = await infra.reddit.search(
                query=keyword,
                subreddits=subreddits[:3],  # Cap at 3 subs to stay within rate limits
                limit=limit,
                time_filter="year",
            )
            log.info(f"Reddit: {len(posts)} posts for '{keyword}'")
            return posts
        except Exception as exc:
            log.warning(f"Reddit fetch failed: {exc}")
            return []

    # ── MoneySavingExpert ──────────────────────────────────────────────────

    async def fetch_mse(
        self,
        keyword: str,
        max_results: int = 5,
    ) -> list[dict]:
        """
        Search MoneySavingExpert forums for UK buyer discussions.

        Scrapes the MSE search results page using BS4.
        MSE uses Vanilla forum software with standard HTML patterns.

        Returns:
            List of dicts with title, excerpt, source.
        """
        infra = get_infrastructure()
        url = "https://forums.moneysavingexpert.com/search"
        params = {"query": keyword, "scope": "site"}

        try:
            resp = await infra.http.get(
                url,
                params=params,
                headers={"User-Agent": "Mozilla/5.0 (compatible; PMW-Research/1.0)"},
            )
            html = resp.text
        except Exception as exc:
            log.warning(f"MSE fetch failed: {exc}")
            return []

        # Parse with BeautifulSoup
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            results = []
            # MSE search results use .searchResult or similar patterns
            for item in soup.select(".searchResult, .DiscussionLink, .Result")[:max_results]:
                title_el = item.select_one("a, .Title, .title")
                excerpt_el = item.select_one(".Excerpt, .excerpt, .Body, .blurb")

                title = title_el.get_text(strip=True) if title_el else ""
                excerpt = excerpt_el.get_text(strip=True)[:500] if excerpt_el else ""

                if title:
                    results.append({
                        "title": title,
                        "excerpt": excerpt,
                        "source": "moneysavingexpert",
                    })

            log.info(f"MSE: {len(results)} threads for '{keyword}'")
            return results

        except ImportError:
            log.error("BeautifulSoup not installed — MSE parsing unavailable")
            return []
        except Exception as exc:
            log.warning(f"MSE parse failed: {exc}")
            return []

    # ── Affiliate FAQ ──────────────────────────────────────────────────────

    async def fetch_affiliate_faq(self, faq_url: str | None) -> dict:
        """
        Fetch and extract text from the affiliate's FAQ/help page.

        Uses BS4 to strip navigation, headers, footers, and scripts.
        Truncates to ~3000 words to stay within prompt budget.

        Args:
            faq_url: URL of the affiliate's FAQ page. None → skipped.

        Returns:
            {
                "content": str (extracted text, max ~3000 words),
                "source": str (URL),
                "available": bool,
            }
        """
        if not faq_url:
            return {"content": "", "source": "none", "available": False}

        infra = get_infrastructure()

        try:
            resp = await infra.http.get(
                faq_url,
                headers={"User-Agent": "PMW-Research-Agent/1.0"},
            )
            html = resp.text
        except Exception as exc:
            log.warning(f"Affiliate FAQ fetch failed: {exc}", extra={"url": faq_url})
            return {"content": "", "source": faq_url, "available": False}

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Remove non-content elements
            for tag in soup(["nav", "header", "footer", "script", "style", "aside", "form"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)

            # Truncate to ~3000 words
            words = text.split()
            truncated = " ".join(words[:3000])

            log.info(
                f"Affiliate FAQ fetched: {len(words)} words (truncated to {min(len(words), 3000)})",
                extra={"url": faq_url},
            )

            return {
                "content": truncated,
                "source": faq_url,
                "available": True,
            }

        except ImportError:
            log.error("BeautifulSoup not installed — FAQ parsing unavailable")
            return {"content": "", "source": faq_url, "available": False}
        except Exception as exc:
            log.warning(f"FAQ parse failed: {exc}", extra={"url": faq_url})
            return {"content": "", "source": faq_url, "available": False}

    # ── Redis caching ──────────────────────────────────────────────────────

    async def cache_sources(
        self,
        run_id: int,
        sources: dict,
        ttl_seconds: int = 3600,
    ) -> str:
        """
        Cache fetched sources in Redis with a 1-hour TTL.

        This avoids re-fetching if the Stage 6 LLM synthesis retries.

        Args:
            run_id: workflow_runs.id.
            sources: Dict of all raw source data.
            ttl_seconds: Cache expiry (default 1 hour).

        Returns:
            Redis cache key.
        """
        infra = get_infrastructure()
        cache_key = f"pmw:sources:{run_id}"

        try:
            await infra.redis.set(cache_key, json.dumps(sources), ex=ttl_seconds)
            log.debug(f"Sources cached at {cache_key} (TTL={ttl_seconds}s)")
        except Exception as exc:
            log.warning(f"Redis cache write failed: {exc}")

        return cache_key

    async def load_cached_sources(self, cache_key: str) -> dict | None:
        """
        Load cached sources from Redis.

        Returns:
            Parsed dict of source data, or None if cache miss / expired.
        """
        infra = get_infrastructure()

        try:
            raw = await infra.redis.get(cache_key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            log.warning(f"Redis cache read failed: {exc}")

        return None