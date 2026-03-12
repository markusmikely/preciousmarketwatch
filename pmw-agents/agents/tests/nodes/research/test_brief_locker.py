"""Tests for Stage 1.5 BriefLocker node."""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

VALID_BRIEF_LLM_RESPONSE = {
    "coherence_score": 0.92,
    "issues": [],
    "enriched_reader_profile": "First-time gold investor, UK, 35-55",
    "enriched_reader_moment": "Comparing ISA providers",
    "suggested_article_angle": "Best gold ISAs for beginners 2026",
}


@pytest.mark.asyncio
async def test_brief_locker_acquires_lock_before_llm_call(
    sample_research_state, sample_topic, mock_llm_service
):
    """BriefLocker must acquire topic lock BEFORE making any LLM call."""
    from agents.graphs.research_graph import BriefLocker

    call_order = []

    async def mock_lock(topic_id, run_id, pool):
        call_order.append("lock")
        return True

    locker = BriefLocker()
    sample_research_state["selected_topic"] = sample_topic

    with patch("agents.graphs.research_graph.acquire_topic_lock", side_effect=mock_lock), \
         patch.object(locker, '_run_with_retries', new_callable=AsyncMock) as mock_llm:

        from agents.nodes.base import AgentResult, AgentStatus
        mock_llm.return_value = AgentResult(
            status=AgentStatus.SUCCESS,
            output=VALID_BRIEF_LLM_RESPONSE,
        )
        mock_llm.side_effect = lambda *a, **kw: (call_order.append("llm"), mock_llm.return_value)[1]

        await locker.run(sample_research_state)

    assert call_order[0] == "lock", "Lock must be acquired before LLM call"
    assert "llm" in call_order, "LLM should have been called"


@pytest.mark.asyncio
async def test_brief_locker_does_not_call_llm_if_lock_fails(
    sample_research_state, sample_topic
):
    """BriefLocker must NOT call LLM if topic lock cannot be acquired."""
    from agents.graphs.research_graph import BriefLocker
    from agents.exceptions import TopicLockConflictError

    locker = BriefLocker()
    sample_research_state["selected_topic"] = sample_topic

    with patch("agents.graphs.research_graph.acquire_topic_lock", return_value=False):
        with pytest.raises(TopicLockConflictError):
            await locker.run(sample_research_state)


@pytest.mark.asyncio
async def test_brief_locker_marks_lock_acquired_in_state(
    sample_research_state, sample_topic
):
    """On success, state should have topic_lock_acquired=True and a valid brief."""
    from agents.graphs.research_graph import BriefLocker
    from agents.nodes.base import AgentResult, AgentStatus

    locker = BriefLocker()
    sample_research_state["selected_topic"] = sample_topic

    with patch("agents.graphs.research_graph.acquire_topic_lock", return_value=True), \
         patch.object(locker, '_run_with_retries', new_callable=AsyncMock) as mock_llm:

        mock_llm.return_value = AgentResult(
            status=AgentStatus.SUCCESS,
            output=VALID_BRIEF_LLM_RESPONSE,
        )
        result = await locker.run(sample_research_state)

    assert result.get("topic_lock_acquired") is True
    assert result.get("brief") is not None