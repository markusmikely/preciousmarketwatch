# agents/config/pricing.py
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Optional
from enum import Enum

class ModelProvider(str, Enum):
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"

@dataclass
class ModelPrice:
    """Base price per 1K tokens:."""
    input_rate: float # USD per 1K input tokens
    output_rate: float # USD per 1K output tokens
    effective_from: date
    effective_to: Optional[date] = None
# ─────────────────────────────────────────────────────────────────────────────
# All prices verified March 2026 from official provider documentation.
# Stored as USD per 1,000 tokens (your existing format).
# Per-million = multiply by 1,000.
#
# IMPORTANT: LLM pricing changes frequently. Each ModelPrice carries an
# effective_date — re-verify any price older than 90 days before using
# for budget projections. Set PRICE_STALENESS_DAYS in settings to alert.
# ─────────────────────────────────────────────────────────────────────────────

class ModelPricing:
    """
    Base model prices from providers.
    These change raely, so they live in code with version control.
    """

    # Current prices (Feb 2026)
    _prices: Dict[str, Dict[str, ModelPrice]] = {
        "anthropic": {
            "claude-opus-4-6": ModelPrice(0.005, 0.025, date(2026, 3, 2)),
            "claude-sonnet-4-6": ModelPrice(0.003, 0.015, date(2026, 3, 2)),
            "claude-haiku-4-5@20251001": ModelPrice(0.001, 0.005, date(2026, 3, 2)),
        },
        "openai": {
            "gpt-4o": ModelPrice(0.005, 0.015, date(2024, 4, 15)),
            "gpt-4o-mini": ModelPrice(0.00015, 0.0006, date(2024, 7, 18)),
            "gpt-3.5-turbo": ModelPrice(0.0005, 0.0015, date(2023, 11, 6)),
            "gpt-5-mini": ModelPrice(0.00015, 0.0006, date(2026, 3, 2)),
            "gpt-5.2": ModelPrice(0.00175, 0.0006, date(2026, 3, 2)),
            "gpt-5.2-pro": ModelPrice(0.00015, 0.0006, date(2026, 3, 2)),
        },
        "deepseek": {
            "deepseek-chat": ModelPrice(0.00014, 0.00028, date(2024, 1, 1)),
        }
        "huggingface": {
            "llama-3.1-8b": ModelPrice(0.0001, 0.0005, date(2024, 1, 1)),
            "llama-3.1-70b": ModelPrice(0.0003, 0.0015, date(2024, 1, 1)),
        }
    }