"""Tests for BaseAgent._calculate_cost and stage record writes."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agents.nodes.base import BaseAgent, ModelConfig, ModelProvider, AgentStatus, AgentResult


class ConcreteAgent(BaseAgent):
    """Minimal concrete subclass for testing BaseAgent methods."""
    def __init__(self):
        super().__init__(
            agent_name="test-agent",
            stage_name="test.stage",
            requires_llm=True,
            model_config=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_id="claude-sonnet-4-6",
                cost_per_1k_input_tokens=0.003,
                cost_per_1k_output_tokens=0.015,
            ),
        )

    async def run(self, state):
        return state

    def build_prompt(self, input_data):
        return "test prompt"

    def validate_output(self, raw):
        return {"result": raw}


def test_calculate_cost_correct():
    """_calculate_cost should use model_config rates."""
    agent = ConcreteAgent()
    cost = agent._calculate_cost(input_tokens=1000, output_tokens=500)
    # (1000/1000 * 0.003) + (500/1000 * 0.015) = 0.003 + 0.0075 = 0.0105
    assert abs(cost - 0.0105) < 0.0000001


def test_calculate_cost_zero_tokens():
    """Zero tokens → zero cost."""
    agent = ConcreteAgent()
    assert agent._calculate_cost(0, 0) == 0.0


def test_calculate_cost_returns_zero_without_model_config():
    """If model_config is None, cost should be 0."""
    agent = ConcreteAgent()
    agent.model_config = None
    assert agent._calculate_cost(1000, 500) == 0.0


@pytest.mark.asyncio
async def test_write_stage_record_upserts(mock_db_pool):
    """_write_stage_record should INSERT or UPDATE workflow_stages."""
    agent = ConcreteAgent()

    with patch.object(type(agent).__mro__[1], '_DBPool') as mock_class:
        mock_class.get = AsyncMock(return_value=mock_db_pool)
        await agent._write_stage_record(
            run_id=42,
            status="complete",
            attempt=1,
            score=0.87,
            passed_threshold=True,
            cost_usd=0.006,
        )

    conn = mock_db_pool.acquire().__aenter__.return_value
    conn.execute.assert_called_once()
    sql = conn.execute.call_args[0][0]
    assert "workflow_stages" in sql
    assert "ON CONFLICT" in sql