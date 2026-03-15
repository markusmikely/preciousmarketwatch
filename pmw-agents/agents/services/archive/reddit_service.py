"""Reddit data service — fetch buyer objections, motivations, verbatim phrases."""

import re
from typing import Any

import httpx

from .base_service import BaseDataService

USER_AGENT = "PMW-Research/1.0 (affiliate content research; contact@preciousmarketwatch.com)"


class RedditService(BaseDataService):
    """Fetch buyer objections, verbatim phrases, motivations from Reddit."""

    ALLOWED_SUBREDDITS = [
        "Gold",
        "Silverbugs",
        "Platinum",
        "PreciousMetals",
        "UKInvesting",
        "investing",
        "Gemstones",
        "Diamonds",
        "Emeralds",
        "Sapphires",
    ]

    def __init__(
        self,
        max_retries: int = 3,
        backoff_sec: float = 2.0,
        max_posts_per_sub: int = 5,
    ) -> None:
        super().__init__(max_retries, backoff_sec)
        self.max_posts_per_sub = max_posts_per_sub

    def fetch(self, topic_keyword: str) -> dict[str, Any]:
        """Search allowed subreddits for posts matching topic_keyword.

        Returns objections, motivations, and verbatim phrases extracted from
        titles and selftext. Uses Reddit JSON API (no auth required).
        """
        if not topic_keyword or not topic_keyword.strip():
            return {"status": "failed", "data": None}

        objections: list[str] = []
        motivations: list[str] = []
        verbatim_phrases: list[str] = []

        query = topic_keyword.strip()[:100]
        headers = {"User-Agent": USER_AGENT}

        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            for sub in self.ALLOWED_SUBREDDITS[:6]:  # Limit to 6 subreddits per run
                url = (
                    f"https://www.reddit.com/r/{sub}/search.json"
                    f"?q={query}&restrict_sr=on&sort=relevance&limit={self.max_posts_per_sub}"
                )
                try:
                    resp = client.get(url, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                except (httpx.HTTPError, ValueError):
                    continue

                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    title = post.get("title", "")
                    selftext = post.get("selftext", "") or ""
                    combined = f"{title} {selftext}".strip()

                    if not combined:
                        continue

                    # Extract short phrases (verbatim-like snippets)
                    sentences = re.split(r"[.!?]\s+", combined)
                    for s in sentences[:3]:  # First few per post
                        s = s.strip()
                        if 20 <= len(s) <= 200:
                            verbatim_phrases.append(s)

                    # Heuristics for objections vs motivations (simplified)
                    objection_markers = [
                        "worried", "scared", "afraid", "concern", "risk",
                        "scam", "fake", "worth it", "should i", "is it safe",
                        "too expensive", "overpriced", "don't trust",
                    ]
                    motivation_markers = [
                        "want to", "looking to", "best way", "how to",
                        "recommend", "advice", "tips", "invest",
                    ]
                    combined_lower = combined.lower()
                    for m in objection_markers:
                        if m in combined_lower and title not in (obj for obj in objections):
                            objections.append(title[:150])
                            break
                    for m in motivation_markers:
                        if m in combined_lower and title not in (mot for mot in motivations):
                            motivations.append(title[:150])
                            break

        # Deduplicate and cap
        verbatim_phrases = list(dict.fromkeys(verbatim_phrases))[:15]
        objections = list(dict.fromkeys(objections))[:10]
        motivations = list(dict.fromkeys(motivations))[:10]

        return {
            "status": "success",
            "data": {
                "objections": objections,
                "motivations": motivations,
                "verbatim_phrases": verbatim_phrases,
            },
        }
