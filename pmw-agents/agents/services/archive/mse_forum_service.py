"""MoneySavingExpert forum service — UK buyer discussions."""

import re
from typing import Any
from urllib.parse import quote_plus

import httpx

from .base_service import BaseDataService

USER_AGENT = "PMW-Research/1.0 (affiliate content research; contact@preciousmarketwatch.com)"
MSE_SEARCH_BASE = "https://forums.moneysavingexpert.com/search"


class MSEForumService(BaseDataService):
    """Scrape MSE forums for UK buyer discussions on precious metals/investing."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_sec: float = 2.0,
        max_results: int = 10,
    ) -> None:
        super().__init__(max_retries, backoff_sec)
        self.max_results = max_results

    def fetch(self, topic_keyword: str) -> dict[str, Any]:
        """Search MSE forums for discussions matching topic_keyword.

        Parses HTML search results for titles and snippets. MSE uses Vanilla
        forum software; we fetch the search page and extract discussion links.
        """
        if not topic_keyword or not topic_keyword.strip():
            return {"status": "failed", "data": None}

        query = topic_keyword.strip()[:80]
        encoded = quote_plus(query)
        url = f"{MSE_SEARCH_BASE}?query={encoded}&scope=site&types[]=discussion&types[]=comment"

        headers = {"User-Agent": USER_AGENT}

        objections: list[str] = []
        motivations: list[str] = []
        verbatim_phrases: list[str] = []

        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                html = resp.text
        except httpx.HTTPError as e:
            return {"status": "failed", "data": None, "error": str(e)}

        # Extract discussion titles/snippets from common Vanilla/HTML patterns
        # Title links often: <a ... class="...Title..." href="...">...</a>
        title_pattern = re.compile(
            r'<a[^>]+href="/discussion/[^"]+"[^>]*>([^<]{10,200})</a>',
            re.IGNORECASE,
        )
        # Snippet/excerpt patterns
        snippet_pattern = re.compile(
            r'(?:class="[^"]*Excerpt[^"]*"|class="[^"]*Body[^"]*")[^>]*>([^<]{20,300})</',
            re.IGNORECASE,
        )

        titles = list(dict.fromkeys(title_pattern.findall(html)))[:self.max_results]
        snippets = list(dict.fromkeys(snippet_pattern.findall(html)))[:self.max_results]

        # Decode HTML entities
        def clean(t: str) -> str:
            t = re.sub(r"&amp;", "&", t)
            t = re.sub(r"&lt;", "<", t)
            t = re.sub(r"&gt;", ">", t)
            t = re.sub(r"&quot;", '"', t)
            t = re.sub(r"&#39;", "'", t)
            return t.strip()

        titles = [clean(t) for t in titles if t.strip()]
        snippets = [clean(s) for s in snippets if len(s.strip()) >= 20]

        # Use titles as motivations (people asking), snippets as verbatim
        motivations = titles[:8]
        verbatim_phrases = snippets[:10]

        # Heuristic objections from negative language in snippets
        objection_words = ["scam", "worried", "concern", "risk", "fake", "avoid"]
        for s in snippets:
            if any(w in s.lower() for w in objection_words):
                objections.append(s[:150])

        if not objections and snippets:
            objections = [snippets[0][:120]] if snippets else []

        return {
            "status": "success",
            "data": {
                "objections": objections[:8],
                "motivations": motivations,
                "verbatim_phrases": verbatim_phrases,
            },
        }
