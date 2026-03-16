"""
CompetitorService — fetch competitor page content for Stage 5.

Owns:
  - Fetching competitor URLs via infra.http
  - Extracting main body text with BeautifulSoup
  - Stripping nav, header, footer, sidebar, ads
  - Truncating to 5000 words per page

Does NOT own:
  - Selecting which URLs to fetch (SerpService → Stage 5 node)
  - LLM analysis of competitor content (Stage 5 node owns that)

Usage:
    from services import services
    page = await services.competitors.fetch_page_content("https://example.com/gold-guide")
"""

from __future__ import annotations

import logging
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.competitor")

MAX_WORDS = 5000
REQUEST_TIMEOUT = 15.0


class CompetitorService:
    """Stateless service — HTTP access via get_infrastructure()."""

    async def fetch_page_content(self, url: str) -> dict:
        """
        Fetch a competitor page and extract the main body text.

        Steps:
          1. GET the URL via infra.http
          2. Parse with BeautifulSoup
          3. Remove nav, header, footer, script, style, aside, sidebar
          4. Extract text, truncate to 5000 words

        Args:
            url: Full URL of the competitor page.

        Returns:
            {
                "url": str,
                "title": str (from <title> tag),
                "word_count": int,
                "text": str (truncated body text),
                "available": bool,
            }
        """
        infra = get_infrastructure()

        # Fetch the page
        try:
            resp = await infra.http.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; PMW-Research/1.0; "
                        "+https://preciousmarketwatch.com)"
                    ),
                },
            )
            html = resp.text
        except Exception as exc:
            log.warning(f"Competitor page fetch failed: {url}", extra={"error": str(exc)})
            return {
                "url": url,
                "title": "",
                "word_count": 0,
                "text": "",
                "available": False,
            }

        # Parse and extract
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Remove non-content elements
            for tag in soup([
                "nav", "header", "footer", "script", "style",
                "aside", "form", "iframe", "noscript",
            ]):
                tag.decompose()

            # Also remove common sidebar/ad classes
            for selector in [
                ".sidebar", ".ad", ".advertisement", ".social-share",
                ".comments", ".related-posts", "#sidebar", "#comments",
                "[role='navigation']", "[role='complementary']",
            ]:
                for el in soup.select(selector):
                    el.decompose()

            # Extract and clean text
            text = soup.get_text(separator="\n", strip=True)

            # Remove excessive blank lines
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            text = "\n".join(lines)

            # Truncate to MAX_WORDS
            words = text.split()
            truncated = " ".join(words[:MAX_WORDS])
            word_count = min(len(words), MAX_WORDS)

            log.debug(
                f"Competitor page extracted: {word_count} words from {url}",
            )

            return {
                "url": url,
                "title": title[:200],
                "word_count": word_count,
                "text": truncated,
                "available": True,
            }

        except ImportError:
            log.error("BeautifulSoup not installed — competitor parsing unavailable")
            return {"url": url, "title": "", "word_count": 0, "text": "", "available": False}
        except Exception as exc:
            log.warning(f"Competitor page parse failed: {url}", extra={"error": str(exc)})
            return {"url": url, "title": "", "word_count": 0, "text": "", "available": False}

    async def fetch_multiple(
        self,
        urls: list[str],
        max_concurrent: int = 3,
    ) -> list[dict]:
        """
        Fetch multiple competitor pages concurrently.

        Args:
            urls: List of competitor page URLs.
            max_concurrent: Max concurrent requests (polite crawling).

        Returns:
            List of page content dicts.
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_limit(url: str) -> dict:
            async with semaphore:
                return await self.fetch_page_content(url)

        results = await asyncio.gather(
            *(fetch_with_limit(u) for u in urls),
            return_exceptions=True,
        )

        pages = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                log.warning(f"Competitor fetch error for {urls[i]}: {result}")
                pages.append({
                    "url": urls[i],
                    "title": "",
                    "word_count": 0,
                    "text": "",
                    "available": False,
                })
            else:
                pages.append(result)

        return pages