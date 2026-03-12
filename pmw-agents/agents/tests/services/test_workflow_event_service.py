"""Tests for WorkflowEventService."""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agents.services.workflow_event_service import WorkflowEventService


@pytest.fixture
def service():
    return WorkflowEventService()


@pytest.mark.asyncio
async def test_emit_writes_to_workflow_logs(service, mock_db_pool, mock_redis):
    """emit() should write a row to workflow_logs."""
    with patch.object(WorkflowEventService, '_get_pool', return_value=mock_db_pool), \
         patch.object(WorkflowEventService, '_get_redis', return_value=mock_redis):

        await service.emit(
            run_id=42,
            event_type="stage.started",
            source="agent",
            agent_name="BriefLocker",
            stage_name="stage1.brief_locker",
            payload={"attempt": 1},
        )

    mock_db_pool.acquire().__aenter__.return_value.execute.assert_called()
    call_args = mock_db_pool.acquire().__aenter__.return_value.execute.call_args[0]
    assert "workflow_logs" in call_args[0]


@pytest.mark.asyncio
async def test_emit_publishes_to_redis(service, mock_db_pool, mock_redis):
    """emit() should publish to Redis pmw:events channel."""
    with patch.object(WorkflowEventService, '_get_pool', return_value=mock_db_pool), \
         patch.object(WorkflowEventService, '_get_redis', return_value=mock_redis):

        await service.emit(
            run_id=42,
            event_type="stage.complete",
            source="agent",
            payload={"score": 0.87},
        )

    mock_redis.publish.assert_called_once()
    channel, message = mock_redis.publish.call_args[0]
    assert channel == "pmw:events"
    data = json.loads(message)
    assert data["event_type"] == "stage.complete"
    assert data["run_id"] == 42


@pytest.mark.asyncio
async def test_emit_never_raises_on_redis_failure(service, mock_db_pool):
    """emit() must never raise even if Redis is completely down."""
    failing_redis = AsyncMock()
    failing_redis.publish = AsyncMock(side_effect=ConnectionError("Redis down"))

    with patch.object(WorkflowEventService, '_get_pool', return_value=mock_db_pool), \
         patch.object(WorkflowEventService, '_get_redis', return_value=failing_redis):

        # Should not raise
        await service.emit(run_id=1, event_type="test", source="test")


@pytest.mark.asyncio
async def test_emit_never_raises_on_db_failure(service, mock_redis):
    """emit() must never raise even if DB is down."""
    failing_pool = AsyncMock()
    failing_pool.acquire = MagicMock(side_effect=Exception("DB down"))

    with patch.object(WorkflowEventService, '_get_pool', return_value=failing_pool), \
         patch.object(WorkflowEventService, '_get_redis', return_value=mock_redis):

        # Should not raise
        await service.emit(run_id=1, event_type="test", source="test")


@pytest.mark.asyncio
async def test_update_current_stage_called_when_requested(service, mock_db_pool, mock_redis):
    """update_current_stage=True should trigger a workflow_runs UPDATE."""
    conn = mock_db_pool.acquire().__aenter__.return_value

    with patch.object(WorkflowEventService, '_get_pool', return_value=mock_db_pool), \
         patch.object(WorkflowEventService, '_get_redis', return_value=mock_redis):

        await service.emit(
            run_id=42,
            event_type="stage.started",
            source="agent",
            stage_name="stage2.keyword_research",
            update_current_stage=True,
        )

    # Should have been called at least twice: workflow_logs + workflow_runs update
    assert conn.execute.call_count >= 2