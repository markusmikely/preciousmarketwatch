# agents/services/cost_tracking/service.py
from datetime import datetime, date
from typing import Optional, Dict, Any
import json
import logging

from services.infrastructure import infrastructure
from core.pricing import ModelPricing, ModelProvider

class CostTrackingService:
    """
    Tracks model usage costs with historical accuracy.
    """
    
    async def record_usage(
        self,
        run_id: int,
        stage_name: str,
        attempt: int,
        provider: ModelProvider,
        model: str,
        input_tokens: int,
        output_tokens: int,
        timestamp: Optional[datetime] = None
    ) -> float:
        """
        Record model usage and calculate cost using prices effective at that time.
        """
        timestamp = timestamp or datetime.utcnow()
        
        # Get price effective at this timestamp
        price = await self._get_price_at_time(
            provider=provider,
            model=model,
            timestamp=timestamp
        )
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * price['input_rate']
        output_cost = (output_tokens / 1000) * price['output_rate']
        total_cost = round(input_cost + output_cost, 6)
        
        # Snapshot of price used
        price_snapshot = {
            'provider': provider.value,
            'model': model,
            'input_rate_per_1k': float(price['input_rate']),
            'output_rate_per_1k': float(price['output_rate']),
            'effective_from': price['effective_from'].isoformat() if price['effective_from'] else None,
            'calculated_at': timestamp.isoformat()
        }
        
        # Store in database
        await infrastructure.postgres.execute(
            """
            INSERT INTO llm_call_logs
                (run_id, agent_name, stage_name, attempt, provider, model,
                input_tokens, output_tokens, cost_usd, price_snapshot, latency_ms, success)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, true)
            """,
            run_id, agent_name, stage_name, attempt, provider.value, model,
            input_tokens, output_tokens, total_cost,
            json.dumps(price_snapshot), latency_ms,
        )
        
        # Update budget usage if applicable
        await self._update_budget_usage(run_id, total_cost, timestamp)
        
        return total_cost
    
    async def _get_price_at_time(
        self,
        provider: ModelProvider,
        model: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Get price effective at a specific timestamp.
        First checks DB for historical prices, falls back to config.
        """
        # Try database first (for historical prices)
        async with infrastructure.postgres.connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT input_rate_per_1k, output_rate_per_1k, effective_from
                FROM model_prices
                WHERE provider = $1 AND model = $2
                  AND effective_from <= $3
                  AND (effective_to IS NULL OR effective_to > $3)
                ORDER BY effective_from DESC
                LIMIT 1
                """,
                provider.value, model, timestamp
            )
            
            if row:
                return {
                    'input_rate': float(row['input_rate_per_1k']),
                    'output_rate': float(row['output_rate_per_1k']),
                    'effective_from': row['effective_from']
                }
        
        # Fall back to current config price
        price = ModelPricing.get_price(provider, model)
        return {
            'input_rate': price.input_rate,
            'output_rate': price.output_rate,
            'effective_from': datetime.combine(price.effective_from, datetime.min.time())
        }
    
    async def _update_budget_usage(self, run_id: int, cost: float, timestamp: datetime):
        """Update budget tracking for this run."""
        # Get project/team from run_id (you'd have this mapping elsewhere)
        # For now, simplified version
        billing_month = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        
        # You'd look up the budget ID based on run context
        # This is just an example
        pass
    
    async def check_budget(
        self,
        team_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Check current budget status and trigger alerts if needed.
        """
        async with infrastructure.postgres.connection() as conn:
            budget = await conn.fetchrow(
                """
                SELECT * FROM model_budgets
                WHERE team_id = $1 AND project_id = $2
                """,
                team_id, project_id
            )
            
            if not budget:
                return {'within_budget': True, 'message': 'No budget set'}
            
            # Get current month's usage
            first_of_month = date.today().replace(day=1)
            usage = await conn.fetchval(
                """
                SELECT SUM(cost_usd)
                FROM budget_usage
                WHERE budget_id = $1 AND billing_month = $2
                """,
                budget['id'], first_of_month
            )
            
            current_usage = float(usage or 0)
            budget_limit = float(budget['monthly_budget_usd'])
            percentage = (current_usage / budget_limit) * 100 if budget_limit > 0 else 0
            
            # Check thresholds
            if budget['alerts_enabled']:
                if percentage >= 90 and not budget['threshold_90_sent']:
                    await self._send_alert(team_id, project_id, 90, current_usage, budget_limit)
                    await conn.execute(
                        "UPDATE model_budgets SET threshold_90_sent = TRUE WHERE id = $1",
                        budget['id']
                    )
                elif percentage >= 70 and not budget['threshold_70_sent']:
                    await self._send_alert(team_id, project_id, 70, current_usage, budget_limit)
                    await conn.execute(
                        "UPDATE model_budgets SET threshold_70_sent = TRUE WHERE id = $1",
                        budget['id']
                    )
            
            return {
                'within_budget': current_usage < budget_limit,
                'current_usage_usd': current_usage,
                'budget_limit_usd': budget_limit,
                'percentage_used': round(percentage, 2),
                'reset_day': budget['reset_day']
            }
    
    async def _send_alert(self, team_id: str, project_id: str, 
                          threshold: int, usage: float, limit: float):
        """Send budget alert (Slack, email, etc.)."""
        # Implementation depends on your alerting system
        logger.warning(
            f"Budget alert: {team_id}/{project_id} at {threshold}% "
            f"(${usage:.2f}/${limit:.2f})"
        )

    async def record_failed_call(
        self,
        run_id: int | None,
        stage_name: str,
        agent_name: str | None,
        provider,
        model: str,
        error: str,
    ):
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO llm_call_logs
                        (run_id, agent_name, stage_name, provider, model,
                        input_tokens, output_tokens, cost_usd, price_snapshot, success, error)
                    VALUES ($1, $2, $3, $4, $5, 0, 0, 0, '{}', false, $6)
                    """,
                    run_id, agent_name, stage_name, str(provider), model, error,
                )
        except Exception as exc:
            log.warning(f"Failed to log failed LLM call: {exc}")


# Global instance
cost_tracker = CostTrackingService()