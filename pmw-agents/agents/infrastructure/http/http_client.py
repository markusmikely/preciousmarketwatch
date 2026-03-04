# generic async HTTP with retry
from typing import Optional, Dict, Any
import httpx

class HTTPClient:
    def __init__(self):
        self.session = httpx.AsyncClient()

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        return await self.session.get(url, params=params)

    async def post(self, url: str, data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        return await self.session.post(url, data=data)