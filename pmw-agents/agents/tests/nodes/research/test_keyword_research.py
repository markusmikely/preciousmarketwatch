"""Tests for Stage 2 KeywordResearch node."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

KEYWORD_RESEARCH_LLM_OUTPUT = {
    "primary_keyword": "best gold isa uk",
    "secondary_keywords": ["gold isa comparison", "gold isa 2026"],
    "reader_intent": "consideration_buyer",
    "serp_format": "comparison",
    "paa_questions": [
        "Is a gold ISA worth it?",
        "What is the best gold ISA in the UK?",
    ],
    "search_volume_estimate": "high",
}


@pytest.mark.asyncio
async def test_keyword_research_populates_state(sample_research_state, mock_llm_service):
    """KeywordResearch should populate keyword_research in state."""
    from agents.graphs.research_graph import KeywordResearch

    agent = KeywordResearch()
    from agents.nodes.base import AgentResult, AgentStatus
    with patch.object(agent, '_run_with_retries', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = AgentResult(
            status=AgentStatus.SUCCESS,
            output=KEYWORD_RESEARCH_LLM_OUTPUT,
        )
        result = await agent.run(sample_research_state)

    assert result.get("keyword_research") is not None
    assert result["keyword_research"]["primary_keyword"] == "best gold isa uk"


@pytest.mark.asyncio
async def test_keyword_research_sets_reader_intent(sample_research_state):
    """KeywordResearch output should carry reader_intent into state."""
    from agents.graphs.research_graph import KeywordResearch
    from agents.nodes.base import AgentResult, AgentStatus

    agent = KeywordResearch()
    with patch.object(agent, '_run_with_retries', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = AgentResult(
            status=AgentStatus.SUCCESS,
            output=KEYWORD_RESEARCH_LLM_OUTPUT,
        )
        result = await agent.run(sample_research_state)

    assert result.get("keyword_research", {}).get("reader_intent") == "consideration_buyer"


@pytest.mark.asyncio
async def test_keyword_research_failure_sets_error(sample_research_state):
    """On LLM failure, status should be 'failed' with error details."""
    from agents.graphs.research_graph import KeywordResearch
    from agents.nodes.base import AgentResult, AgentStatus

    agent = KeywordResearch()
    with patch.object(agent, '_run_with_retries', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = AgentResult(
            status=AgentStatus.FAILED,
            output=None,
            error="Max retries exceeded",
        )
        result = await agent.run(sample_research_state)

    assert result["status"] == "failed"
    assert len(result["errors"]) > 0