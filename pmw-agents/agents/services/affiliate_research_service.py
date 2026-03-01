"""Affiliate research orchestrator — runs all data sources for Stage 6."""

from typing import Any

from .faq_service import FAQService
from .mse_forum_service import MSEForumService
from .paa_service import PAAService
from .reddit_service import RedditService


class AffiliateResearchService:
    """Orchestrates Reddit, MSE, PAA, and FAQ data fetches for affiliate research."""

    def __init__(
        self,
        reddit: RedditService | None = None,
        mse: MSEForumService | None = None,
        paa: PAAService | None = None,
        faq: FAQService | None = None,
    ) -> None:
        self.reddit = reddit or RedditService()
        self.mse = mse or MSEForumService()
        self.paa = paa or PAAService()
        self.faq = faq or FAQService()

    def run_research(
        self,
        topic_keyword: str,
        run_id: int,
        faq_url: str | None = None,
        topic_id: int | None = None,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch data from enabled sources.

        Args:
            topic_keyword: Target keyword for Reddit/MSE search.
            run_id: Workflow run ID for PAA lookup from Stage 2.
            faq_url: Affiliate FAQ URL (optional).
            topic_id: Optional topic ID for PAA context.
            sources: List of source names to use. Default: all.

        Returns:
            {status, data: {reddit?, mse_forums?, paa_questions?, faq?}}
        """
        sources = sources or ["reddit", "mse_forums", "paa_questions", "faq"]
        results: dict[str, Any] = {"status": "running", "data": {}}

        if "reddit" in sources:
            results["data"]["reddit"] = self.reddit.run(topic_keyword)

        if "mse_forums" in sources:
            results["data"]["mse_forums"] = self.mse.run(topic_keyword)

        if "paa_questions" in sources:
            results["data"]["paa_questions"] = self.paa.run(run_id, topic_id)

        if "faq" in sources and faq_url:
            results["data"]["faq"] = self.faq.run(faq_url)
        elif "faq" in sources:
            results["data"]["faq"] = {"status": "skipped", "data": None}

        results["status"] = "complete"
        return results
