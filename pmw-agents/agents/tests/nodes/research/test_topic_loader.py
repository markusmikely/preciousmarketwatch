"""Tests for Stage 1.1 TopicLoader node."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_topic_loader_returns_candidate_topics(sample_research_state):
    """TopicLoader should populate candidate_topics in state."""
    from agents.graphs.research_graph import TopicLoader

    mock_topics = [
        {"id": 101, "title": "Best Gold ISA UK", "priority": 8, "asset_class": "gold"},
        {"id": 102, "title": "Silver Coin Prices", "priority": 6, "asset_class": "silver"},
    ]

    loader = TopicLoader()
    with patch.object(loader, 'execute', new_callable=AsyncMock, return_value=mock_topics):
        result = await loader.run(sample_research_state)

    assert "candidate_topics" in result
    assert len(result["candidate_topics"]) == 2


@pytest.mark.asyncio
async def test_topic_loader_sets_status_failed_when_no_topics(sample_research_state):
    """TopicLoader should set status=failed if no topics are available."""
    from agents.graphs.research_graph import TopicLoader

    loader = TopicLoader()
    with patch.object(loader, 'execute', new_callable=AsyncMock, return_value=[]):
        result = await loader.run(sample_research_state)

    assert result["status"] == "failed"
    assert len(result["errors"]) > 0