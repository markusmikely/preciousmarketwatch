class NewsService(BaseDataService):
    """Fetch recent news for a given keyword/asset."""
    
    async def fetch(
        self,
        keyword: str,
        days_back: int = 30,
        min_results: int = 5,
    ) -> dict:
        """
        Returns:
            {
                "articles": [
                    {
                        "title": str,
                        "source": str,
                        "published_at": "ISO 8601",
                        "summary": str,    # first 200 words
                        "url": str,
                        "relevance": float  # 0.0–1.0
                    }
                ],
                "count": int,
                "oldest_date": "ISO 8601",
                "newest_date": "ISO 8601"
            }
        """