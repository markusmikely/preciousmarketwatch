"""
CostTrackingService — record LLM token usage and calculate costs.

Writes to llm_call_logs (created in migration 005_observability).
Reads model prices from model_prices table, falling back to env config.

Usage (called by LLMService after every generate() call):
    tracker = CostTrackingService()
    cost_usd = await tracker.record_usage(
        run_id=42,
        stage_name="research.stage2.serp",
        attempt=1,
        provider="anthropic",
        model="claude-sonnet-4-6",
        input_tokens=1200,
        output_tokens=400,
    )
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.cost_tracking")


class CostTrackingService:
    """
    Tracks LLM usage costs with historical price accuracy.

    Prices are looked up from the model_prices table first (allowing
    retroactive correction), falling back to MODEL_PRICE_* env vars,
    and finally to hard-coded defaults so the service never breaks.
    """

    # ── Hard-coded fallback prices (USD per 1k tokens) ─────────────────────
    # Keep in sync with seed_model_prices.py.  Used only when DB has no row.
    _FALLBACK_PRICES: dict[str, dict[str, float]] = {
        "claude-opus-4-6":        {"input": 0.015,  "output": 0.075},
        "claude-sonnet-4-6":      {"input": 0.003,  "output": 0.015},
        "claude-haiku-4-5":       {"input": 0.00025,"output": 0.00125},
        "gpt-4o":                  {"input": 0.005,  "output": 0.015},
        "gpt-4o-mini":             {"input": 0.00015,"output": 0.0006},
        "deepseek-chat":           {"input": 0.00014,"output": 0.00028},
    }

    async def record_usage(
        self,
        run_id: int,
        stage_name: str,
        attempt: int,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        timestamp: datetime | None = None,
    ) -> float:
        """
        Record model usage and return the calculated cost in USD.

        Looks up the effective price at `timestamp` from model_prices,
        calculates cost, and inserts a row into llm_call_logs.

        Returns:
            Total cost in USD for this call.
        """
        timestamp = timestamp or datetime.utcnow()

        price = await self._get_price_at_time(
            provider=provider,
            model=model,
            timestamp=timestamp,
        )

        input_cost  = (input_tokens  / 1_000) * price["input_rate"]
        output_cost = (output_tokens / 1_000) * price["output_rate"]
        total_cost  = round(input_cost + output_cost, 6)

        price_snapshot = {
            "provider":            provider,
            "model":               model,
            "input_rate_per_1k":   price["input_rate"],
            "output_rate_per_1k":  price["output_rate"],
            "effective_from":      price["effective_from"],
            "calculated_at":       timestamp.isoformat(),
        }

        infra = get_infrastructure()
        try:
            await infra.postgres.execute(
                """
                INSERT INTO llm_call_logs
                    (run_id, stage_name, attempt_number, provider, model,
                     input_tokens, output_tokens, cost_usd, price_snapshot,
                     called_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10)
                """,
                run_id,
                stage_name,
                attempt,
                provider,
                model,
                input_tokens,
                output_tokens,
                total_cost,
                json.dumps(price_snapshot),
                timestamp,
            )
        except Exception as exc:
            # Cost write failure must never block the pipeline
            log.error(
                "llm_call_logs write failed",
                extra={"run_id": run_id, "stage": stage_name, "error": str(exc)},
            )

        return total_cost

    async def _get_price_at_time(
        self,
        provider: str,
        model: str,
        timestamp: datetime,
    ) -> dict[str, Any]:
        """
        Return the price effective at `timestamp`.

        Lookup order:
          1. model_prices table (allows price history + corrections)
          2. Hard-coded _FALLBACK_PRICES
        """
        infra = get_infrastructure()
        try:
            row = await infra.postgres.fetchrow(
                """
                SELECT input_rate_per_1k, output_rate_per_1k, effective_from
                FROM model_prices
                WHERE provider = $1
                  AND model     = $2
                  AND effective_from <= $3
                  AND (effective_to IS NULL OR effective_to > $3)
                ORDER BY effective_from DESC
                LIMIT 1
                """,
                provider,
                model,
                timestamp,
            )
            if row:
                return {
                    "input_rate":    float(row["input_rate_per_1k"]),
                    "output_rate":   float(row["output_rate_per_1k"]),
                    "effective_from": str(row["effective_from"]),
                }
        except Exception as exc:
            log.warning(
                "model_prices lookup failed — using fallback",
                extra={"model": model, "error": str(exc)},
            )

        # Fallback — use hard-coded defaults
        fallback = self._FALLBACK_PRICES.get(model, {"input": 0.001, "output": 0.002})
        return {
            "input_rate":    fallback["input"],
            "output_rate":   fallback["output"],
            "effective_from": "fallback",
        }

    async def get_run_cost(self, run_id: int) -> float:
        """Return the total cost in USD for all LLM calls in a run."""
        infra = get_infrastructure()
        val = await infra.postgres.fetchval(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_call_logs WHERE run_id = $1",
            run_id,
        )
        return float(val or 0)


# Global instance — import and use this in services/nodes
cost_tracker = CostTrackingService()