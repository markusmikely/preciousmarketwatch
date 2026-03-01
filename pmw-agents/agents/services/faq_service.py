"""FAQ service — fetch affiliate FAQ content from faq_url."""

from typing import Any

import httpx

from .base_service import BaseDataService

USER_AGENT = "PMW-Research/1.0 (affiliate content research; contact@preciousmarketwatch.com)"


class FAQService(BaseDataService):
    """Fetch affiliate FAQ content from faq_url."""

    def fetch(self, faq_url: str | None) -> dict[str, Any]:
        """Fetch FAQ page HTML. Returns raw text for LLM extraction."""
        if not faq_url or not str(faq_url).strip():
            return {"status": "failed", "data": None}

        url = str(faq_url).strip()
        if not url.startswith(("http://", "https://")):
            return {"status": "failed", "data": None}

        headers = {"User-Agent": USER_AGENT}

        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    return {"status": "success", "data": resp.text}
        except httpx.HTTPError:
            pass

        return {"status": "failed", "data": None}
