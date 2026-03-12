"""Tests for Stage 8a ArcCoherence validation node."""
import pytest
from unittest.mock import AsyncMock, patch

ARC_PASS_OUTPUT = {
    "passed": True,
    "coherence_score": 0.88,
    "narrative_arc": "fear → research → action",
    "issues": [],
    "recommendation": None,
}

ARC_FAIL_OUTPUT = {
    "passed": False,
    "coherence_score": 0.35,
    "narrative_arc": "unclear",
    "issues": [{"severity": "critical", "description": "No clear buying signal"}],
    "recommendation": "Revisit market_context and buyer_psychology",
}


@pytest.mark.asyncio
async def test_arc_coherence_pass_sets_arc_validation(sample_research_state):
    """Passing arc check should set arc_validation with passed=True."""
    from agents.graphs.research_graph import ArcCoherence
    from agents.nodes.base import AgentResult, AgentStatus

    # Give the state a complete research bundle
    sample_research_state.update({
        "keyword_research": {"primary_keyword": "gold isa"},
        "market_context": {"stance": "bull_run"},
        "top_factors": {"factors": []},
        "buyer_psychology": {"motivations": []},
        "tool_mapping": {"tools": []},
    })

    agent = ArcCoherence()
    with patch.object(agent, '_run_with_retries', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = AgentResult(
            status=AgentStatus.SUCCESS,
            output=ARC_PASS_OUTPUT,
        )
        result = await agent.run(sample_research_state)

    assert result["arc_validation"]["passed"] is True
    assert result["status"] == "running"


@pytest.mark.asyncio
async def test_arc_coherence_fail_triggers_hitl(sample_research_state):
    """Failed arc check should set hitl_required=True."""
    from agents.graphs.research_graph import ArcCoherence
    from agents.nodes.base import AgentResult, AgentStatus

    sample_research_state.update({
        "keyword_research": {},
        "market_context": {},
        "top_factors": {},
        "buyer_psychology": {},
        "tool_mapping": {},
    })

    agent = ArcCoherence()
    with patch.object(agent, '_run_with_retries', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = AgentResult(
            status=AgentStatus.SUCCESS,
            output=ARC_FAIL_OUTPUT,
        )
        result = await agent.run(sample_research_state)

    assert result.get("hitl_required") is True
    assert result["arc_validation"]["passed"] is False