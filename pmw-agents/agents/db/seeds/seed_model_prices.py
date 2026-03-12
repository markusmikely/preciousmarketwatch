"""
Seed model_prices table from config/pricing.py.
Run: python -m agents.db.seeds.seed_model_prices
"""
import asyncio
import os
from datetime import datetime, timezone

import asyncpg

from config.pricing import ModelPricing


async def seed():
    dsn = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn)

    rows_inserted = 0
    rows_skipped = 0

    for provider_key, models in ModelPricing._prices.items():
        for model_id, price in models.items():
            # Check if this exact record already exists
            existing = await conn.fetchval(
                """
                SELECT id FROM model_prices
                WHERE provider = $1 AND model = $2
                  AND effective_from = $3
                """,
                provider_key,
                model_id,
                datetime.combine(price.effective_from, datetime.min.time()).replace(tzinfo=timezone.utc),
            )
            if existing:
                rows_skipped += 1
                continue

            await conn.execute(
                """
                INSERT INTO model_prices (provider, model, input_rate_per_1k, output_rate_per_1k, effective_from)
                VALUES ($1, $2, $3, $4, $5)
                """,
                provider_key,
                model_id,
                price.input_rate,
                price.output_rate,
                datetime.combine(price.effective_from, datetime.min.time()).replace(tzinfo=timezone.utc),
            )
            rows_inserted += 1
            print(f"  ✓ {provider_key}/{model_id}")

    await conn.close()
    print(f"\nDone. {rows_inserted} inserted, {rows_skipped} already existed.")


if __name__ == "__main__":
    asyncio.run(seed())