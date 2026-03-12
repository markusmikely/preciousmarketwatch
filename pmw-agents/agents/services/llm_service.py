# agents/services/llm_service.py
import time
from services.cost_tracking_service import CostTrackingService
from dataclasses import dataclass
import os
from typing import Optional, Dict, Any, Tuple 
from enum import Enum 
from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError
)
import logging
from datetime import datetime

from exceptions import (
    LLMError, LLMTimeoutError, LLMRateLimitError, LLMProviderError
)

from providers import (
    AnthropicProvider, HuggingFaceProvider, DeepSeekProvider
)
from config import settings

logger = logging.getLogger(__name__)

class ModelProvider(str, Enum):
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    DEEPSEEK = "deepseek"

@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: ModelProvider
    cost_usd: float


class LLMService:
    """
    LLM Service with Tenacity retry decorators.
    """

    def __init__(self):
        self._providers = {}
        self._initialize_providers()
        self._cost_tracker = CostTrackingService()

    def _initialize_providers(self):
        """Initialize configured providers."""
        if settings.ANTHROPIC_API_KEY:
            self._providers[ModelProvider.ANTHROPIC] = AnthropicProvider(
                api_key=settings.ANTHROPIC_API_KEY,
            )
        if settings.HUGGINGFACE_API_KEY:
            self._providers[ModelProvider.HUGGINGFACE] = HuggingFaceProvider(
                api_key=settings.HUGGINGFACE_API_KEY,
            )
        if settings.DEEPSEEK_API_KEY:
            self._providers[ModelProvider.DEEPSEEK] = DeepSeekProvider(
                api_key=settings.DEEPSEEK_API_KEY,
            )
            

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(LLMTimeoutError, LLMRateLimitError, ConnectionError)
    )
    async def generate(
        self,
        model: str,
        prompt: str,
        provider: ModelProvider,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        run_id: int | None = None,
        agent_name: str | None = None,
        stage_name: str | None = None,
        attempt: int = 1,
        **kwargs,
    ) -> "LLMResponse":
        start_ms = int(time.time() * 1000)

        if provider not in self._providers:
            raise LLMProviderError(f"Provider {provider} not configured")

        try:
        response = await self._providers[provider].generate(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        latency_ms = int(time.time() * 1000) - start_ms

        # Calculate cost via service (uses DB historical price, falls back to config)
        cost_usd = await self._cost_tracker.record_usage(
            run_id=run_id,
            stage_name=stage_name or "unknown",
            attempt=attempt,
            provider=provider,
            model=model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            agent_name=agent_name,
            latency_ms=latency_ms,
        )

        return LLMResponse(
            text=response.text,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            model=model,
            provider=provider,
            cost_usd=cost_usd,
        )
    except Exception as e:
        # Log failed call too
        await self._cost_tracker.record_failed_call(
            run_id=run_id,
            stage_name=stage_name or "unknown",
            agent_name=agent_name,
            provider=provider,
            model=model,
            error=str(e),
        )
        self._transform_error(e)

    def _transform_error(self, error: Exception) -> LLMError:
        """Transform provider errors to our types."""
        error_str = str(error).lower()
        if "timeout" in error_str:
            return LLMTimeoutError(str(error))
        if "rate limit" in error_str:
            return LLMRateLimitError(str(error))
        return LLMProviderError(str(error))

    