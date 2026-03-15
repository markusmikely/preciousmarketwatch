class InternalLinkService(BaseDataService):
    """Search existing WP posts for internal link opportunities."""
    
    async def fetch(
        self,
        keyword: str,
        category: str | None = None,
        limit: int = 3,
    ) -> dict:
        """
        Calls WP REST API: GET /wp/v2/posts?search={keyword}&per_page={limit}
        
        Returns:
            {
                "links": [
                    {
                        "post_id": int,
                        "title": str,
                        "url": str,
                        "excerpt": str,
                        "relevance": float
                    }
                ],
                "count": int
            }
        """