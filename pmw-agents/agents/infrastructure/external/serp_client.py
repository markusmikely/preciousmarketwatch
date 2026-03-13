"""
SerpClient — SerpAPI transport for SERP results and People Also Ask.

Owns:
  - SerpAPI HTTP requests (via shared HTTPClient)
  - Response parsing to clean dicts
  - API key injection from environment

Does NOT own:
  - HTTP connection management (HTTPClient owns that)
  - Business logic — callers decide what to do with results

Services use:
    results = await infra.serp.search("best gold IRA UK", gl="uk", hl="en")
    organic = await infra.serp.organic_results("buy gold bullion UK")
    paa     = await infra.serp.people_also_ask("gold price today")
"""

from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger("pmw.infra.serp")

SERP_API_BASE = "https://serpapi.com/search"


class SerpClient:
    """
    SerpAPI client. Injected with the shared HTTPClient from Infrastructure.
    """

    def __init__(
        self,
        http=None,                     # HTTPClient — injected by Infrastructure
        api_key: str | None = None,
    ) -> None:
        self._http = http
        self._api_key = api_key or os.environ.get("SERP_API_KEY", "")

    def set_http(self, http) -> None:
        """Called by Infrastructure after HTTPClient is connected."""
        self._http = http

    def _require_key(self) -> str:
        if not self._api_key:
            raise RuntimeError(
                "SERP_API_KEY is not set. "
                "Add it to your environment variables."
            )
        return self._api_key

    # ── Core search ────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        engine: str = "google",
        gl: str = "uk",
        hl: str = "en",
        num: int = 10,
        **extra_params: Any,
    ) -> dict[str, Any]:
        """
        Run a full SerpAPI search and return the raw parsed JSON.

        Args:
            query:  Search query string
            engine: SerpAPI engine (default "google")
            gl:     Google country code (default "uk")
            hl:     Google language code (default "en")
            num:    Number of results to request (max 100)

        Returns:
            Raw SerpAPI response dict with all sections intact.

        Usage:
            raw = await infra.serp.search("best place to buy gold UK")
        """
        if not self._http:
            raise RuntimeError(
                "SerpClient has no HTTPClient. "
                "Ensure Infrastructure.connect() has been called."
            )

        params = {
            "api_key": self._require_key(),
            "q":       query,
            "engine":  engine,
            "gl":      gl,
            "hl":      hl,
            "num":     num,
            **extra_params,
        }

        log.debug("SerpAPI search", extra={"query": query, "engine": engine})

        try:
            response = await self._http.get(SERP_API_BASE, params=params)
            return response.json()
        except Exception as exc:
            log.error("SerpAPI search failed", extra={"query": query, "error": str(exc)})
            raise

    # ── Parsed helpers ─────────────────────────────────────────────────────

    async def organic_results(
        self,
        query: str,
        gl: str = "uk",
        hl: str = "en",
        num: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Fetch organic search results for a query.

        Returns a list of dicts, each with keys:
            position, title, link, snippet, displayed_link

        Usage:
            results = await infra.serp.organic_results("gold bullion dealers UK")
            for r in results:
                print(r["position"], r["title"], r["link"])
        """
        raw = await self.search(query, gl=gl, hl=hl, num=num)
        items = raw.get("organic_results", [])
        return [
            {
                "position":       r.get("position"),
                "title":          r.get("title", ""),
                "link":           r.get("link", ""),
                "snippet":        r.get("snippet", ""),
                "displayed_link": r.get("displayed_link", ""),
            }
            for r in items
        ]

    async def people_also_ask(
        self,
        query: str,
        gl: str = "uk",
        hl: str = "en",
    ) -> list[dict[str, Any]]:
        """
        Fetch People Also Ask questions for a query.

        Returns a list of dicts, each with keys:
            question, snippet, title, link

        Usage:
            paa = await infra.serp.people_also_ask("how to buy gold UK")
            for item in paa:
                print(item["question"])
        """
        raw = await self.search(query, gl=gl, hl=hl, num=10)
        items = raw.get("related_questions", [])
        return [
            {
                "question": r.get("question", ""),
                "snippet":  r.get("snippet", ""),
                "title":    r.get("title", ""),
                "link":     r.get("link", ""),
            }
            for r in items
        ]

    async def related_searches(
        self,
        query: str,
        gl: str = "uk",
        hl: str = "en",
    ) -> list[str]:
        """
        Fetch related search queries.

        Returns a plain list of query strings.
        """
        raw = await self.search(query, gl=gl, hl=hl, num=10)
        return [
            r.get("query", "")
            for r in raw.get("related_searches", [])
            if r.get("query")
        ]