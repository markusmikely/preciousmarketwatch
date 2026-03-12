"""Tests for CostTrackingService."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
import asyncpg

from agents.services.cost_tracking_service import CostTrackingService
from agents.config.pricing import ModelProvider


@pytest.fixture
def service():
    return CostTrackingService()


@pytest.mark.asyncio
async def test_record_usage_calculates_correct_cost(service, mock_db_pool):
    """record_usage() should calculate cost from DB price and return it."""
    # DB returns a price row
    mock_row = {"input_rate_per_1k": 0.003, "output_rate_per_1k": 0.015, "effective_from": datetime.now()}
    mock_db_pool.acquire().__aenter__.return_value.fetchrow = AsyncMock(return_value=mock_row)

    with patch.object(CostTrackingService, '_get_pool', return_value=mock_db_pool):
        cost = await service.record_usage(
            run_id=42,
            stage_name="stage2.keyword_research",
            attempt=1,
            provider=ModelProvider.ANTHROPIC,
            model="claude-sonnet-4-6",
            input_tokens=1000,   # 1k input tokens × $0.003 = $0.003
            output_tokens=500,   # 500 output tokens × $0.015/1k = $0.0075
        )

    # Expected: (1000/1000 * 0.003) + (500/1000 * 0.015) = 0.003 + 0.0075 = 0.0105
    assert abs(cost - 0.0105) < 0.000001


@pytest.mark.asyncio
async def test_record_usage_falls_back_to_config_pricing(service, mock_db_pool):
    """When no DB price row found, fall back to config/pricing.py."""
    # DB returns no row
    mock_db_pool.acquire().__aenter__.return_value.fetchrow = AsyncMock(return_value=None)

    with patch.object(CostTrackingService, '_get_pool', return_value=mock_db_pool):
        cost = await service.record_usage(
            run_id=42,
            stage_name="stage1.brief_locker",
            attempt=1,
            provider=ModelProvider.ANTHROPIC,
            model="claude-sonnet-4-6",
            input_tokens=500,
            output_tokens=300,
        )

    # Should return a positive number (from config pricing)
    assert cost > 0


@pytest.mark.asyncio
async def test_record_usage_writes_to_llm_call_logs(service, mock_db_pool):
    """record_usage() should INSERT into llm_call_logs."""
    mock_row = {"input_rate_per_1k": 0.003, "output_rate_per_1k": 0.015, "effective_from": datetime.now()}
    conn = mock_db_pool.acquire().__aenter__.return_value
    conn.fetchrow = AsyncMock(return_value=mock_row)

    with patch.object(CostTrackingService, '_get_pool', return_value=mock_db_pool):
        await service.record_usage(
            run_id=1, stage_name="test", attempt=1,
            provider=ModelProvider.ANTHROPIC, model="claude-sonnet-4-6",
            input_tokens=100, output_tokens=50,
        )

    conn.execute.assert_called()
    sql = conn.execute.call_args[0][0]
    assert "llm_call_logs" in sql


@pytest.mark.asyncio
async def test_cost_is_zero_for_zero_tokens(service, mock_db_pool):
    """Zero tokens should produce zero cost."""
    mock_row = {"input_rate_per_1k": 0.003, "output_rate_per_1k": 0.015, "effective_from": datetime.now()}
    mock_db_pool.acquire().__aenter__.return_value.fetchrow = AsyncMock(return_value=mock_row)

    with patch.object(CostTrackingService, '_get_pool', return_value=mock_db_pool):
        cost = await service.record_usage(
            run_id=1, stage_name="test", attempt=1,
            provider=ModelProvider.ANTHROPIC, model="claude-sonnet-4-6",
            input_tokens=0, output_tokens=0,
        )

    assert cost == 0.0