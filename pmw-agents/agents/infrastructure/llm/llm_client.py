"""
LLMClient — unified async LLM interface for all providers.

Owns:
  - SDK initialisation for Anthropic, OpenAI, DeepSeek, HuggingFace
  - API key injection from environment
  - Transport-level retries (tenacity)
  - Raw response normalisation to RawLLMResponse

Does NOT own:
  - Cost calculation — that stays in CostTrackingService
  - Business-level retry logic — that stays in LLMService / BaseAgent
  - DB writes

Services use:
    response = await infra.llm.generate(
        provider="anthropic",
        model="claude-sonnet-4-6",
        prompt="...",
        temperature=0.2,
        max_tokens=4096,
    )
    text         = response.text
    input_tokens = response.input_tokens
    output_tokens = response.output_tokens

Lifecycle (called by Infrastructure):
    await client.connect()   # startup — initialises SDK clients
    await client.close()     # shutdown — no-op for most SDKs
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger("pmw.infra.llm")


@dataclass
class RawLLMResponse:
    """
    Normalised response from any provider SDK.
    No cost is attached here — CostTrackingService handles that separately.
    """
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str


class LLMClient:
    """
    Multi-provider async LLM client.

    Providers are initialised lazily in connect() based on which API keys
    are configured. Callers never import provider SDKs directly.
    """

    def __init__(
        self,
        anthropic_api_key: str | None = None,
        openai_api_key: str | None = None,
        deepseek_api_key: str | None = None,
        huggingface_api_key: str | None = None,
    ) -> None:
        # Keys — fall back to env vars if not explicitly provided
        self._anthropic_key   = anthropic_api_key   or os.environ.get("ANTHROPIC_API_KEY", "")
        self._openai_key      = openai_api_key      or os.environ.get("OPENAI_API_KEY", "")
        self._deepseek_key    = deepseek_api_key    or os.environ.get("DEEPSEEK_API_KEY", "")
        self._huggingface_key = huggingface_api_key or os.environ.get("HUGGINGFACE_API_KEY", "")

        # SDK clients — set in connect()
        self._anthropic_client = None
        self._openai_client    = None
        self._deepseek_client  = None
        self._hf_client        = None

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """
        Initialise SDK clients for every configured provider.
        Logs which providers are active. Does NOT make any API calls.
        """
        active: list[str] = []

        if self._anthropic_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.AsyncAnthropic(
                    api_key=self._anthropic_key
                )
                active.append("anthropic")
            except ImportError:
                log.warning("anthropic package not installed — provider unavailable")

        if self._openai_key:
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(api_key=self._openai_key)
                active.append("openai")
            except ImportError:
                log.warning("openai package not installed — provider unavailable")

        if self._deepseek_key:
            try:
                from openai import AsyncOpenAI  # DeepSeek uses OpenAI-compatible API
                self._deepseek_client = AsyncOpenAI(
                    api_key=self._deepseek_key,
                    base_url="https://api.deepseek.com",
                )
                active.append("deepseek")
            except ImportError:
                log.warning(
                    "openai package not installed — DeepSeek provider unavailable"
                )

        if self._huggingface_key:
            try:
                from huggingface_hub import AsyncInferenceClient
                self._hf_client = AsyncInferenceClient(token=self._huggingface_key)
                active.append("huggingface")
            except ImportError:
                log.warning("huggingface-hub not installed — provider unavailable")

        if not active:
            log.warning(
                "LLMClient: no providers configured. "
                "Set ANTHROPIC_API_KEY, OPENAI_API_KEY, etc."
            )
        else:
            log.info(f"LLMClient ready — active providers: {active}")

    async def close(self) -> None:
        """Close any persistent connections. Currently a no-op for all SDKs."""
        pass

    # ── Main interface ─────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        reraise=True,
    )
    async def generate(
        self,
        provider: str,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> RawLLMResponse:
        """
        Call the specified provider and return a normalised RawLLMResponse.

        Args:
            provider:      "anthropic" | "openai" | "deepseek" | "huggingface"
            model:         Provider-specific model ID, e.g. "claude-sonnet-4-6"
            prompt:        User message text
            temperature:   Sampling temperature (0.0 – 1.0)
            max_tokens:    Maximum tokens in the response
            system_prompt: Optional system message (Anthropic and OpenAI)

        Returns:
            RawLLMResponse with .text, .input_tokens, .output_tokens

        Raises:
            ValueError: Unknown provider
            RuntimeError: Provider not configured (missing API key)
        """
        p = provider.lower()
        if p == "anthropic":
            return await self._call_anthropic(
                model, prompt, temperature, max_tokens, system_prompt
            )
        elif p == "openai":
            return await self._call_openai_compat(
                self._openai_client, "openai",
                model, prompt, temperature, max_tokens, system_prompt,
            )
        elif p == "deepseek":
            return await self._call_openai_compat(
                self._deepseek_client, "deepseek",
                model, prompt, temperature, max_tokens, system_prompt,
            )
        elif p == "huggingface":
            return await self._call_huggingface(model, prompt, temperature, max_tokens)
        else:
            raise ValueError(
                f"Unknown provider: {provider!r}. "
                "Must be one of: anthropic, openai, deepseek, huggingface"
            )

    # ── Provider implementations ───────────────────────────────────────────

    async def _call_anthropic(
        self,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None,
    ) -> RawLLMResponse:
        if not self._anthropic_client:
            raise RuntimeError(
                "Anthropic provider not configured. Set ANTHROPIC_API_KEY."
            )
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self._anthropic_client.messages.create(**kwargs)
        return RawLLMResponse(
            text=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=model,
            provider="anthropic",
        )

    async def _call_openai_compat(
        self,
        client: Any,
        provider_name: str,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None,
    ) -> RawLLMResponse:
        if not client:
            raise RuntimeError(
                f"{provider_name} provider not configured. "
                f"Set {'OPENAI_API_KEY' if provider_name == 'openai' else 'DEEPSEEK_API_KEY'}."
            )
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return RawLLMResponse(
            text=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=model,
            provider=provider_name,
        )

    async def _call_huggingface(
        self,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> RawLLMResponse:
        if not self._hf_client:
            raise RuntimeError(
                "HuggingFace provider not configured. Set HUGGINGFACE_API_KEY."
            )
        text = await self._hf_client.text_generation(
            prompt,
            model=model,
            max_new_tokens=max_tokens,
            temperature=temperature,
        )
        # HuggingFace Inference API does not return exact token counts — approximate
        in_tok  = len(prompt.split())
        out_tok = len(text.split())
        return RawLLMResponse(
            text=text,
            input_tokens=in_tok,
            output_tokens=out_tok,
            model=model,
            provider="huggingface",
        )