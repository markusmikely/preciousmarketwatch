"""
HTTPClient — shared httpx AsyncClient for all outbound HTTP calls.

Owns:
  - A single persistent httpx.AsyncClient (connection-pooling, keep-alive)
  - Default headers, timeouts, and retry transport
  - Convenience get/post helpers

SerpClient, RedditClient, and any future external clients receive
this client via dependency injection from Infrastructure — they never
create their own httpx sessions.

Lifecycle (called by Infrastructure):
    await client.connect()   # startup  — creates the underlying session
    await client.close()     # shutdown — drains and closes the session
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger("pmw.infra.http")

# Retry on transient network errors (not 4xx/5xx — callers decide those)
_RETRY_TRANSPORT = httpx.AsyncHTTPTransport(retries=3)


class HTTPClient:
    """
    Thin wrapper around httpx.AsyncClient.

    All external clients (SerpClient, RedditClient, …) share a single
    instance so connection pools are not duplicated per-service.
    """

    def __init__(
        self,
        timeout: float = 20.0,
        user_agent: str = "PMW-Agents/1.0",
    ) -> None:
        self._timeout = httpx.Timeout(timeout, connect=10.0)
        self._user_agent = user_agent
        self._client: httpx.AsyncClient | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Create the underlying httpx session. No-op if already created."""
        if self._client is not None:
            return
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            transport=_RETRY_TRANSPORT,
            headers={"User-Agent": self._user_agent},
            follow_redirects=True,
        )
        log.info("HTTPClient session created")

    async def close(self) -> None:
        """Close the httpx session and release connections."""
        if self._client:
            await self._client.aclose()
            self._client = None
            log.info("HTTPClient session closed")

    def _get(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError(
                "HTTPClient.connect() has not been called. "
                "Ensure Infrastructure.connect() runs at worker startup."
            )
        return self._client

    # ── Request helpers ────────────────────────────────────────────────────

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        HTTP GET. Raises httpx.HTTPStatusError on 4xx/5xx.

        Usage:
            resp = await infra.http.get("https://serpapi.com/search", params={...})
            data = resp.json()
        """
        response = await self._get().get(url, params=params, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    async def post(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        HTTP POST. Raises httpx.HTTPStatusError on 4xx/5xx.
        """
        response = await self._get().post(
            url, json=json, data=data, headers=headers, **kwargs
        )
        response.raise_for_status()
        return response