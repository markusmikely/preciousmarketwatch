# agents/services/base_service.py — async version
class BaseDataService(ABC):
    def __init__(self, max_retries: int = 3, backoff_sec: float = 2.0):
        self.max_retries = max_retries
        self.backoff_sec = backoff_sec

    @abstractmethod
    async def fetch(self, *args, **kwargs) -> dict:
        raise NotImplementedError

    async def run(self, *args, **kwargs) -> dict:
        attempt = 0
        while attempt < self.max_retries:
            try:
                return await self.fetch(*args, **kwargs)
            except Exception as e:
                logger.warning("%s attempt %d/%d: %s",
                    self.__class__.__name__, attempt + 1, self.max_retries, e)
                attempt += 1
                await asyncio.sleep(self.backoff_sec)
        return {"status": "failed", "data": None}