"""Tests for ResearchGraph conditional routing logic."""
import pytest
from unittest.mock import MagicMock

from agents.graphs.research_graph import ResearchGraph


@pytest.fixture
def graph():
    """ResearchGraph instance without a real checkpointer."""
    # We only need routing methods — no DB/Redis needed
    g = ResearchGraph.__new__(ResearchGraph)
    return g


def test_route_after_brief_lock_fanout(graph):
    """Happy path: returns fan-out list of parallel stage names."""
    state = {
        "hitl_required": False,
        "status": "running",
    }
    result = graph.route_after_brief_lock(state)
    assert isinstance(result, list)
    assert "stage2.keyword_research" in result
    assert "stage3.market_context" in result
    assert "stage5.competitor_analysis" in result


def test_route_after_brief_lock_hitl(graph):
    """HITL flag should route to hitl_gate."""
    state = {"hitl_required": True, "status": "running"}
    result = graph.route_after_brief_lock(state)
    assert result == "hitl" or (isinstance(result, list) and "hitl" in result)


def test_route_after_brief_lock_failure(graph):
    """Failed status should route to handle_failure."""
    state = {"hitl_required": False, "status": "failed"}
    result = graph.route_after_brief_lock(state)
    assert result == "failed" or (isinstance(result, list) and "failed" in result)


def test_route_after_arc_continue(graph):
    """Arc validation pass should route to bundle_assembler."""
    state = {
        "arc_validation": {"passed": True, "coherence_score": 0.9},
        "status": "running",
        "hitl_required": False,
    }
    result = graph.route_after_arc(state)
    assert result == "continue"


def test_route_after_arc_hitl(graph):
    """Arc validation fail should route to hitl_gate."""
    state = {
        "arc_validation": {"passed": False, "coherence_score": 0.4},
        "status": "running",
        "hitl_required": True,
    }
    result = graph.route_after_arc(state)
    assert result == "hitl"