from __future__ import annotations
 
import logging
import os

# LLM Client
from infrastructure.llm.llm_client import LLMClient
# HTTP Client
from infrastructure.http.http_client import HTTPClient
# Postgres Client
from infrastructure.database.postgres_client import PostgresClient
# Cache Client
from infrastructure.cache.redis_client import RedisClient
# Owned Clients
from infrastructure.owned.wordpress.wp_db_client import WordpressClient
# External Clients
from infrastructure.external.news_client import NewsClient
from infrastructure.external.price_client import PriceClient
from infrastructure.external.reddit_client import RedditClient
from infrastructure.external.serp_client import SERPClient

log = logging.getLogger("pmw.infra")

class Infrastructure:
    def __init__(self):
        self.llm = LLMClient()
        self.http = HTTPClient()
        self.postgres = PostgresClient()
        self.redis = RedisClient()
        self.news = NewsClient()
        self.price = PriceClient()
        self.reddit = RedditClient(http=None)
        self.serp = SERPClient(http=None)
        self.wordpress = WordpressClient(
            base_url=os.environ.get("WP_API_URL", ""),
            username=os.environ.get("WP_API_USER", ""),
            password=os.environ.get("WP_API_PASSWORD", ""),
        )

    async def connect(self) -> None:
        log.info("Infrastructure connecting...")
 
        await self.postgres.connect()
        await self.redis.connect()
        await self.llm.connect()
        await self.http.connect()   

        self.serp.set_http(self.http)
        self.reddit.set_http(self.http)

        log.info("Infrastructure ready")

    
    async def close(self) -> None:
        log.info("Infrastructure shutting down...")
 
        for name, client, method in [
            ("postgres",  self.postgres,  self.postgres.close),
            ("redis",     self.redis,     self.redis.close),
            ("llm",       self.llm,       self.llm.close),
            ("http",      self.http,      self.http.close),
            ("wordpress", self.wordpress, self.wordpress.close),
        ]:
            try:
                await method()
            except Exception as exc:
                log.error(f"Error closing {name}: {exc}")
 
        log.info("Infrastructure closed")

_instance: Infrastructure | None = None
 
 
def get_infrastructure() -> Infrastructure:
    """
    Return the global Infrastructure singleton.
 
    Always call await get_infrastructure().connect() once at startup before
    any service accesses the singleton. Services should import and call this
    function rather than holding a module-level reference.
 
    Usage:
        infra = get_infrastructure()
        row = await infra.postgres.fetchrow("SELECT 1")
    """
    global _instance
    if _instance is None:
        _instance = Infrastructure()
    return _instance