"""
Shared pytest fixtures for PMW agent tests.

Uses pytest-asyncio for async tests.
Uses unittest.mock for patching external dependencies (DB, Redis, LLM APIs).
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


# ── Async event loop ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for all async tests in session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ── Mock DB pool ───────────────────────────────────────────────────────────

@pytest.fixture
def mock_db_conn():
    """Mock asyncpg connection."""
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value="INSERT 0 1")
    conn.fetchval = AsyncMock(return_value=None)
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetch = AsyncMock(return_value=[])
    return conn


@pytest.fixture
def mock_db_pool(mock_db_conn):
    """Mock asyncpg pool that yields mock_db_conn."""
    pool = AsyncMock()
    pool.acquire = MagicMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=mock_db_conn),
        __aexit__=AsyncMock(return_value=None),
    ))
    return pool


# ── Mock Redis ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.publish = AsyncMock(return_value=1)
    redis.xadd = AsyncMock(return_value="1234567890-0")
    redis.xreadgroup = AsyncMock(return_value=None)
    redis.xack = AsyncMock(return_value=1)
    redis.xgroup_create = AsyncMock(return_value=True)
    return redis


# ── Mock LLM response ──────────────────────────────────────────────────────

@dataclass
class MockLLMResponse:
    text: str
    input_tokens: int = 150
    output_tokens: int = 400
    model: str = "claude-sonnet-4-6"
    provider: str = "anthropic"
    cost_usd: float = 0.006


def make_llm_response(content: dict | str) -> MockLLMResponse:
    """Helper to create a mock LLM response with JSON content."""
    text = json.dumps(content) if isinstance(content, dict) else content
    return MockLLMResponse(text=text)


@pytest.fixture
def mock_llm_service():
    """Mock LLMService.generate() — returns configurable responses."""
    service = AsyncMock()
    service.generate = AsyncMock(return_value=make_llm_response({"status": "ok"}))
    return service


# ── Sample research state ──────────────────────────────────────────────────

@pytest.fixture
def sample_run_id():
    return 42


@pytest.fixture
def sample_topic():
    return {
        "id": 101,
        "title": "Best Gold ISAs UK 2026",
        "target_keyword": "best gold isa uk",
        "asset_class": "gold",
        "geo_focus": "uk",
        "priority": 8,
        "reader_intent": "consideration_buyer",
        "topic_category": "gold-isa",
    }


@pytest.fixture
def sample_affiliate():
    return {
        "id": 1,
        "name": "BullionVault",
        "partner_key": "bullionvault",
        "commission_type": "revenue_share",
        "commission_rate": 0.005,
        "asset_classes": ["gold", "silver"],
        "geo_focus": "uk",
        "active": True,
        "faq_url": "https://www.bullionvault.com/help/",
    }


@pytest.fixture
def sample_research_state(sample_run_id, sample_topic):
    return {
        "run_id": sample_run_id,
        "triggered_by": "manual",
        "candidate_topics": [sample_topic],
        "selected_topic": sample_topic,
        "topic_lock_acquired": True,
        "brief": {
            "topic": sample_topic,
            "meta": {"validation_passed": True, "coherence_score": 0.9},
        },
        "keyword_research": None,
        "market_context": None,
        "competitor_analysis": None,
        "top_factors": None,
        "buyer_psychology": None,
        "tool_mapping": None,
        "arc_validation": None,
        "research_bundle": None,
        "current_stage": "start",
        "status": "running",
        "errors": [],
        "retry_counts": {},
        "model_usage": [],
    }