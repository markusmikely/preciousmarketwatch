"""
CostTrackingService — record LLM usage and calculate costs.

Flat and focused: one method to record, one to read.
Writes to llm_call_logs table. Reads prices from model_prices
table with hard-coded fallback.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.cost_tracking")


class CostTrackingService:

    _FALLBACK_PRICES: dict[str, dict[str, float]] = {
        "claude-opus-4-6":   {"input": 0.015,   "output": 0.075},
        "claude-sonnet-4-6": {"input": 0.003,   "output": 0.015},
        "claude-haiku-4-5":  {"input": 0.00025, "output": 0.00125},
        "gpt-4o":             {"input": 0.005,   "output": 0.015},
        "gpt-4o-mini":        {"input": 0.00015, "output": 0.0006},
        "deepseek-chat":      {"input": 0.00014, "output": 0.00028},
    }

    # Cached column name detection (avoids querying information_schema every call)
    _column_name: str | None = None

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
        """Record usage and return cost in USD. Never raises."""
        timestamp = timestamp or datetime.utcnow()
        infra = get_infrastructure()

        price = await self._get_price(provider, model, timestamp)
        cost = round(
            (input_tokens / 1_000) * price["input"]
            + (output_tokens / 1_000) * price["output"],
            6,
        )

        snapshot = json.dumps({
            "provider": provider, "model": model,
            "input_rate": price["input"], "output_rate": price["output"],
        })

        try:
            col = await self._get_attempt_column(infra)
            await infra.postgres.execute(
                f"""
                INSERT INTO llm_call_logs
                    (run_id, stage_name, {col}, provider, model,
                     input_tokens, output_tokens, cost_usd, price_snapshot, called_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10)
                """,
                run_id, stage_name, attempt, provider, model,
                input_tokens, output_tokens, cost, snapshot, timestamp,
            )
        except Exception as exc:
            log.error(f"llm_call_logs write failed: {exc}",
                      extra={"run_id": run_id, "stage": stage_name})

        return cost

    async def get_run_cost(self, run_id: int) -> float:
        infra = get_infrastructure()
        val = await infra.postgres.fetchval(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_call_logs WHERE run_id = $1",
            run_id,
        )
        return float(val or 0)

    async def _get_price(self, provider: str, model: str, ts: datetime) -> dict:
        infra = get_infrastructure()
        try:
            row = await infra.postgres.fetchrow(
                """
                SELECT input_rate_per_1k, output_rate_per_1k
                FROM model_prices
                WHERE provider = $1 AND model = $2
                  AND effective_from <= $3
                  AND (effective_to IS NULL OR effective_to > $3)
                ORDER BY effective_from DESC LIMIT 1
                """,
                provider, model, ts,
            )
            if row:
                return {"input": float(row["input_rate_per_1k"]),
                        "output": float(row["output_rate_per_1k"])}
        except Exception:
            pass
        fb = self._FALLBACK_PRICES.get(model, {"input": 0.001, "output": 0.002})
        return fb

    async def _get_attempt_column(self, infra) -> str:
        """Detect whether column is 'attempt' (pre-008) or 'attempt_number' (post-008)."""
        if self._column_name:
            return self._column_name
        try:
            exists = await infra.postgres.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'llm_call_logs' AND column_name = 'attempt_number'
                )
                """
            )
            self._column_name = "attempt_number" if exists else "attempt"
        except Exception:
            self._column_name = "attempt"
        return self._column_name