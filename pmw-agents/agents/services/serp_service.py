"""
SerpService — SERP research via infra.serp (SerpAPI).

Owns:
  - Orchestrating organic + PAA + related search calls
  - Applying keyword include/exclude filters from topic meta
  - Returning a structured SerpBundle for downstream agents
  - Extracting competitor URLs for Stage 5

Does NOT own:
  - HTTP transport (SerpClient via infra.serp owns that)
  - Business logic about what to do with SERP data (nodes own that)

Usage:
    from services import services
    bundle = await services.serp.research_keyword(
        keyword="best gold ISA UK",
        geography="uk",
        include_keywords="gold isa, gold investment",
        exclude_keywords="crypto, bitcoin",
    )
    urls = await services.serp.get_competitor_urls("best gold ISA UK", geography="uk")
"""

from __future__ import annotations

import logging
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.serp")

# PMW's own domain — excluded from competitor results
OWN_DOMAIN = "preciousmarketwatch.com"


class SerpService:
    """Stateless service — SerpAPI access via get_infrastructure().serp."""

    async def research_keyword(
        self,
        keyword: str,
        geography: str = "uk",
        include_keywords: str = "",
        exclude_keywords: str = "",
    ) -> dict:
        """
        Run a full SERP research pass for a keyword.

        Calls:
          1. infra.serp.organic_results() — top 10 organic results
          2. infra.serp.people_also_ask() — PAA questions
          3. infra.serp.related_searches() — related queries

        Then applies include/exclude keyword filters and returns a
        structured SerpBundle.

        Args:
            keyword: Target keyword to research.
            geography: "uk" | "us" | "global" — maps to SerpAPI gl parameter.
            include_keywords: Comma-separated keywords to validate relevance.
            exclude_keywords: Comma-separated keywords to filter out.

        Returns:
            SerpBundle dict with organic_results, paa_questions, related_searches,
            top_formats, content_gap_signals, and metadata.
        """
        infra = get_infrastructure()
        gl = self._geo_to_gl(geography)

        # Parse include/exclude lists
        include_set = self._parse_keyword_list(include_keywords)
        exclude_set = self._parse_keyword_list(exclude_keywords)

        # Fetch all SERP data
        try:
            organic = await infra.serp.organic_results(keyword, gl=gl, num=10)
        except Exception as exc:
            log.warning(f"Organic results fetch failed: {exc}")
            organic = []

        try:
            paa = await infra.serp.people_also_ask(keyword, gl=gl)
        except Exception as exc:
            log.warning(f"PAA fetch failed: {exc}")
            paa = []

        try:
            related = await infra.serp.related_searches(keyword, gl=gl)
        except Exception as exc:
            log.warning(f"Related searches fetch failed: {exc}")
            related = []

        # Apply exclude filter to organic results
        if exclude_set:
            organic = [
                r for r in organic
                if not any(
                    excl in (r.get("title", "") + " " + r.get("snippet", "")).lower()
                    for excl in exclude_set
                )
            ]

        # Filter related searches
        if exclude_set:
            related = [
                q for q in related
                if not any(excl in q.lower() for excl in exclude_set)
            ]

        # Detect dominant result formats
        top_formats = self._detect_formats(organic)

        # Identify content gaps (topics in PAA/related not covered by top results)
        content_gaps = self._identify_gaps(organic, paa, related)

        bundle = {
            "keyword": keyword,
            "geography": geography,
            "organic_results": organic[:10],
            "paa_questions": [q.get("question", q) if isinstance(q, dict) else q for q in paa],
            "related_searches": related[:10],
            "top_formats": top_formats,
            "content_gap_signals": content_gaps,
            "competitor_count": len([r for r in organic if OWN_DOMAIN not in r.get("link", "")]),
            "own_ranking": self._find_own_position(organic),
        }

        log.info(
            "SERP research complete",
            extra={
                "keyword": keyword,
                "organic_count": len(organic),
                "paa_count": len(paa),
                "related_count": len(related),
            },
        )

        return bundle

    async def get_competitor_urls(
        self,
        keyword: str,
        geography: str = "uk",
        exclude_domain: str = OWN_DOMAIN,
        limit: int = 5,
    ) -> list[dict]:
        """
        Fetch top-ranking competitor URLs for a keyword.

        Returns:
            List of dicts with url, title, snippet, position.
            Own domain is excluded.
        """
        infra = get_infrastructure()
        gl = self._geo_to_gl(geography)

        try:
            organic = await infra.serp.organic_results(keyword, gl=gl, num=10)
        except Exception as exc:
            log.error(f"Competitor URL fetch failed: {exc}")
            return []

        competitors = [
            r for r in organic
            if exclude_domain not in (r.get("link") or "")
        ]

        return competitors[:limit]

    # ── Private helpers ────────────────────────────────────────────────────

    @staticmethod
    def _geo_to_gl(geography: str) -> str:
        """Map PMW geography to SerpAPI gl parameter."""
        return {
            "uk": "uk",
            "us": "us",
            "global": "us",  # Default to US for global queries
        }.get(geography.lower(), "uk")

    @staticmethod
    def _parse_keyword_list(keywords_str: str) -> set[str]:
        """Parse comma-separated keyword string into a lowercase set."""
        if not keywords_str:
            return set()
        return {kw.strip().lower() for kw in keywords_str.split(",") if kw.strip()}

    @staticmethod
    def _detect_formats(organic: list[dict]) -> list[str]:
        """Detect dominant content formats from organic result titles/snippets."""
        format_signals = {
            "listicle": ["best", "top", "ranked", "list"],
            "guide": ["guide", "how to", "complete", "ultimate", "step"],
            "comparison": ["vs", "versus", "compare", "comparison", "difference"],
            "review": ["review", "reviews", "rated", "rating"],
            "news": ["2026", "2025", "today", "latest", "update", "news"],
        }

        format_scores: dict[str, int] = {}
        for result in organic[:5]:
            text = (result.get("title", "") + " " + result.get("snippet", "")).lower()
            for fmt, signals in format_signals.items():
                if any(s in text for s in signals):
                    format_scores[fmt] = format_scores.get(fmt, 0) + 1

        # Return formats sorted by frequency
        return sorted(format_scores.keys(), key=lambda f: format_scores[f], reverse=True)

    @staticmethod
    def _identify_gaps(
        organic: list[dict],
        paa: list[dict],
        related: list[str],
    ) -> list[str]:
        """Identify content gaps — topics in PAA/related not covered by top results."""
        # Combine all organic text
        organic_text = " ".join(
            (r.get("title", "") + " " + r.get("snippet", "")).lower()
            for r in organic[:5]
        )

        gaps = []

        # Check PAA questions not addressed by top results
        for item in paa:
            question = item.get("question", item) if isinstance(item, dict) else item
            # Simple heuristic: if key words from the question don't appear in organic text
            words = [w for w in question.lower().split() if len(w) > 4]
            if words and not any(w in organic_text for w in words[:2]):
                gaps.append(f"PAA: {question}")

        # Check related searches not covered
        for query in related[:5]:
            words = [w for w in query.lower().split() if len(w) > 4]
            if words and not any(w in organic_text for w in words[:2]):
                gaps.append(f"Related: {query}")

        return gaps[:8]

    @staticmethod
    def _find_own_position(organic: list[dict]) -> int | None:
        """Find PMW's own position in organic results. Returns None if not ranking."""
        for result in organic:
            if OWN_DOMAIN in (result.get("link") or ""):
                return result.get("position")
        return None