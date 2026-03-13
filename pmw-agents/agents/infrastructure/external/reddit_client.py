"""
RedditClient — Reddit JSON API transport for community sentiment research.

Owns:
  - Reddit JSON API requests via the shared HTTPClient
  - Subreddit allow-list enforcement (PMW approved subs only)
  - Response parsing to clean dicts

Does NOT own:
  - HTTP connection management (HTTPClient owns that)
  - Business logic about what to do with posts

Services use:
    posts = await infra.reddit.search("gold IRA reviews", subreddits=["personalfinance"])
    top   = await infra.reddit.top_posts("Silverbugs", limit=10)

Approved subreddits (precious metals + UK personal finance only):
    UKPersonalFinance, personalfinance, Gold, Silverbugs,
    PreciousMetals, UKInvesting, investing, BullionStar
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("pmw.infra.reddit")

REDDIT_BASE  = "https://www.reddit.com"
USER_AGENT   = "PMW-Research-Agent/1.0 (affiliate content research)"

# Only research-appropriate subreddits — keeps results on-topic
# and avoids scraping unrelated communities
ALLOWED_SUBREDDITS: frozenset[str] = frozenset({
    "UKPersonalFinance",
    "personalfinance",
    "Gold",
    "Silverbugs",
    "PreciousMetals",
    "UKInvesting",
    "investing",
    "BullionStar",
    "CryptoCurrency",   # for comparative sentiment
    "FinancialIndependence",
})


class RedditClient:
    """
    Reddit JSON API client. Injected with the shared HTTPClient from Infrastructure.
    No OAuth — uses the public `.json` endpoint which is free and unauthenticated.
    """

    def __init__(self, http=None) -> None:
        self._http = http   # HTTPClient — injected by Infrastructure

    def set_http(self, http) -> None:
        """Called by Infrastructure after HTTPClient is connected."""
        self._http = http

    def _require_http(self):
        if self._http is None:
            raise RuntimeError(
                "RedditClient has no HTTPClient. "
                "Ensure Infrastructure.connect() has been called."
            )
        return self._http

    def _validate_subreddit(self, sub: str) -> str:
        """Raise if sub is not in the approved list."""
        if sub not in ALLOWED_SUBREDDITS:
            raise ValueError(
                f"Subreddit r/{sub} is not in the PMW allow-list. "
                f"Allowed: {sorted(ALLOWED_SUBREDDITS)}"
            )
        return sub

    # ── Parsing helpers ────────────────────────────────────────────────────

    @staticmethod
    def _parse_post(child: dict) -> dict[str, Any]:
        d = child.get("data", {})
        return {
            "id":        d.get("id", ""),
            "title":     d.get("title", ""),
            "selftext":  (d.get("selftext") or "")[:2000],  # truncate long posts
            "score":     d.get("score", 0),
            "url":       f"https://reddit.com{d.get('permalink', '')}",
            "subreddit": d.get("subreddit", ""),
            "num_comments": d.get("num_comments", 0),
            "created_utc":  d.get("created_utc"),
        }

    # ── Public interface ───────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        subreddits: list[str] | None = None,
        sort: str = "relevance",
        time_filter: str = "year",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search across one or more subreddits for posts matching `query`.

        Args:
            query:       Search string
            subreddits:  List of subreddits to search. Defaults to the PMW
                         precious-metals shortlist. All must be in ALLOWED_SUBREDDITS.
            sort:        Reddit sort: "relevance" | "new" | "top" | "comments"
            time_filter: "hour" | "day" | "week" | "month" | "year" | "all"
            limit:       Results per subreddit (max 25)

        Returns:
            Flat list of post dicts sorted by score descending.
        """
        http = self._require_http()

        # Default subreddits — the three most relevant for PMW content
        if not subreddits:
            subreddits = ["Gold", "PreciousMetals", "UKPersonalFinance"]

        headers = {"User-Agent": USER_AGENT}
        all_posts: list[dict] = []

        for sub in subreddits:
            self._validate_subreddit(sub)
            url = f"{REDDIT_BASE}/r/{sub}/search.json"
            params = {
                "q":          query,
                "restrict_sr": 1,
                "sort":       sort,
                "t":          time_filter,
                "limit":      min(limit, 25),
            }
            try:
                resp = await http.get(url, params=params, headers=headers)
                children = resp.json().get("data", {}).get("children", [])
                all_posts.extend(self._parse_post(c) for c in children)
                log.debug(f"Reddit r/{sub}: {len(children)} results for '{query}'")
            except Exception as exc:
                log.warning(
                    f"Reddit r/{sub} fetch failed",
                    extra={"query": query, "error": str(exc)},
                )

        # Sort by score so highest-signal posts come first
        all_posts.sort(key=lambda p: p["score"], reverse=True)
        return all_posts

    async def top_posts(
        self,
        subreddit: str,
        time_filter: str = "month",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Fetch top posts from a subreddit over a time window.

        Args:
            subreddit:   Subreddit name (must be in ALLOWED_SUBREDDITS)
            time_filter: "day" | "week" | "month" | "year" | "all"
            limit:       Max posts to return (max 25)

        Returns:
            List of post dicts sorted by score descending.
        """
        http = self._require_http()
        self._validate_subreddit(subreddit)

        url = f"{REDDIT_BASE}/r/{subreddit}/top.json"
        params = {"t": time_filter, "limit": min(limit, 25)}
        headers = {"User-Agent": USER_AGENT}

        try:
            resp = await http.get(url, params=params, headers=headers)
            children = resp.json().get("data", {}).get("children", [])
            return [self._parse_post(c) for c in children]
        except Exception as exc:
            log.error(
                f"Reddit top posts failed for r/{subreddit}",
                extra={"error": str(exc)},
            )
            return []

    async def post_comments(
        self,
        subreddit: str,
        post_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Fetch top-level comments from a specific post.

        Useful for extracting verbatim buyer sentiment around specific products.

        Args:
            subreddit: Subreddit the post belongs to
            post_id:   Reddit post ID (e.g. "abc123")
            limit:     Max comments to return

        Returns:
            List of comment dicts with keys: id, body, score, created_utc
        """
        http = self._require_http()
        self._validate_subreddit(subreddit)

        url = f"{REDDIT_BASE}/r/{subreddit}/comments/{post_id}.json"
        params = {"limit": min(limit, 50)}
        headers = {"User-Agent": USER_AGENT}

        try:
            resp = await http.get(url, params=params, headers=headers)
            data = resp.json()
            # Reddit returns [post_listing, comment_listing]
            if not isinstance(data, list) or len(data) < 2:
                return []
            comment_children = data[1].get("data", {}).get("children", [])
            comments = []
            for c in comment_children:
                d = c.get("data", {})
                if d.get("body") and d.get("body") != "[deleted]":
                    comments.append({
                        "id":          d.get("id", ""),
                        "body":        d["body"][:1000],
                        "score":       d.get("score", 0),
                        "created_utc": d.get("created_utc"),
                    })
            return comments
        except Exception as exc:
            log.error(
                "Reddit comments fetch failed",
                extra={"subreddit": subreddit, "post_id": post_id, "error": str(exc)},
            )
            return []