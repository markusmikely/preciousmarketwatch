"""Base data service for affiliate/topic research scrapers."""

import logging
import time
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseDataService(ABC):
    """Base service for retries, logging, and failure tracking."""

    def __init__(self, max_retries: int = 3, backoff_sec: float = 2.0) -> None:
        self.max_retries = max_retries
        self.backoff_sec = backoff_sec

    @abstractmethod
    def fetch(self, *args, **kwargs):
        """Override in child classes. Returns dict with status and data."""
        raise NotImplementedError

    def run(self, *args, **kwargs) -> dict:
        """Execute fetch with retries. Returns {status, data}."""
        attempt = 0
        while attempt < self.max_retries:
            try:
                return self.fetch(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    "%s fetch failed on attempt %d/%d: %s",
                    self.__class__.__name__,
                    attempt + 1,
                    self.max_retries,
                    e,
                )
                attempt += 1
                time.sleep(self.backoff_sec)
        return {"status": "failed", "data": None}
