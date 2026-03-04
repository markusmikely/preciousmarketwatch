from agents.infrastructure.llm_client import LLMClient
from agents.infrastructure.http_client import HTTPClient
from agents.infrastructure.news_client import NewsClient
from agents.infrastructure.postgres_client import PostgresClient
from agents.infrastructure.redis_client import RedisClient
from agents.infrastructure.serp_client import SerpClient
from agents.infrastructure.wordpress_client import WordpressClient

class Infrastructure:
    def __init__(self):
        self.llm_client = LLMClient()
        self.http_client = HTTPClient()
        self.news_client = NewsClient()
        self.postgres_client = PostgresClient()
        self.redis_client = RedisClient()
        self.serp_client = SerpClient()
        self.wordpress_client = WordpressClient()

    