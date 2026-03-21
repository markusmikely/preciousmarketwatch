"""
config/models.py — Centralised model configuration.

All agents import ModelConfig from here. Change env vars to switch provider.

    PIPELINE_MODEL=deepseek-chat     → all pipeline agents use DeepSeek
    JUDGE_MODEL=deepseek-chat        → judge/quality agents use DeepSeek
    JUDGE_MODEL_FAST=deepseek-chat   → fast/cheap calls use DeepSeek
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# These are duplicated from nodes.base to avoid circular imports.
# nodes.base also defines them — they're the same classes.
# Agents can import from either place.

class ModelProvider(str, Enum):
    ANTHROPIC   = "anthropic"
    OPENAI      = "openai"
    HUGGINGFACE = "huggingface"
    DEEPSEEK    = "deepseek"


@dataclass
class ModelConfig:
    provider:    ModelProvider
    model_id:    str
    temperature: float = 0.2
    max_tokens:  int   = 4096


# ── Model ID → Provider mapping ───────────────────────────────────────

_MODEL_PROVIDERS = {
    "claude-opus-4-6":       ModelProvider.ANTHROPIC,
    "claude-sonnet-4-6":     ModelProvider.ANTHROPIC,
    "claude-haiku-4-5":      ModelProvider.ANTHROPIC,
    "deepseek-chat":         ModelProvider.DEEPSEEK,
    "deepseek-coder":        ModelProvider.DEEPSEEK,
    "deepseek-reasoner":     ModelProvider.DEEPSEEK,
    "gpt-4o":                ModelProvider.OPENAI,
    "gpt-4o-mini":           ModelProvider.OPENAI,
    "gpt-3.5-turbo":         ModelProvider.OPENAI,
    "llama-3.1-8b":          ModelProvider.HUGGINGFACE,
    "llama-3.1-70b":         ModelProvider.HUGGINGFACE,
}


def _resolve_provider(model_id: str) -> ModelProvider:
    provider = _MODEL_PROVIDERS.get(model_id)
    if provider:
        return provider
    m = model_id.lower()
    if "claude" in m:
        return ModelProvider.ANTHROPIC
    if "gpt" in m:
        return ModelProvider.OPENAI
    if "deepseek" in m:
        return ModelProvider.DEEPSEEK
    return ModelProvider.DEEPSEEK


def get_pipeline_model(temperature: float = 0.2, max_tokens: int = 4096) -> ModelConfig:
    from config.settings import settings
    model_id = settings.PIPELINE_MODEL
    return ModelConfig(
        provider=_resolve_provider(model_id),
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_fast_model(temperature: float = 0.1, max_tokens: int = 512) -> ModelConfig:
    from config.settings import settings
    model_id = settings.JUDGE_MODEL_FAST
    return ModelConfig(
        provider=_resolve_provider(model_id),
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_judge_model(temperature: float = 0.1, max_tokens: int = 4096) -> ModelConfig:
    from config.settings import settings
    model_id = settings.JUDGE_MODEL
    return ModelConfig(
        provider=_resolve_provider(model_id),
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
    )