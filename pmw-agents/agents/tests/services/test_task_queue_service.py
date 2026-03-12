"""Tests for TaskQueueService."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.services.task_queue_service import TaskQueueService


@pytest.fixture
def service():
    return TaskQueueService()


@pytest.mark.asyncio
async def test_enqueue_writes_to_postgres_first(service, mock_db_pool, mock_redis):
    """enqueue() must write to Postgres before touching Redis."""
    mock_db_pool.acquire().__aenter__.return_value.fetchval = AsyncMock(return_value=99)

    with patch.object(TaskQueueService, '_get_pool', return_value=mock_db_pool), \
         patch.object(TaskQueueService, '_get_redis', return_value=mock_redis):

        task_id = await service.enqueue("research_pipeline", {"run_id": 42}, run_id=42)

    assert task_id == 99
    # Postgres INSERT was called
    conn = mock_db_pool.acquire().__aenter__.return_value
    assert conn.fetchval.called


@pytest.mark.asyncio
async def test_enqueue_survives_redis_failure(service, mock_db_pool):
    """enqueue() should succeed even if Redis is unavailable."""
    mock_db_pool.acquire().__aenter__.return_value.fetchval = AsyncMock(return_value=1)
    mock_db_pool.acquire().__aenter__.return_value.execute = AsyncMock()

    failing_redis = AsyncMock()
    failing_redis.xgroup_create = AsyncMock(side_effect=ConnectionError("Redis down"))

    with patch.object(TaskQueueService, '_get_pool', return_value=mock_db_pool), \
         patch.object(TaskQueueService, '_get_redis', return_value=failing_redis):

        # Should not raise
        task_id = await service.enqueue("research_pipeline", {"run_id": 1})
        assert task_id == 1


@pytest.mark.asyncio
async def test_complete_updates_status(service, mock_db_pool, mock_redis):
    """complete() should set status = 'complete' in Postgres."""
    conn = mock_db_pool.acquire().__aenter__.return_value

    with patch.object(TaskQueueService, '_get_pool', return_value=mock_db_pool), \
         patch.object(TaskQueueService, '_get_redis', return_value=mock_redis):

        await service.complete(task_id=99)

    conn.execute.assert_called()
    sql = conn.execute.call_args[0][0]
    assert "complete" in sql


@pytest.mark.asyncio
async def test_recover_stale_requeues_processing_tasks(service, mock_db_pool):
    """recover_stale() should reset processing → queued for stale tasks."""
    stale_tasks = [
        {"id": 10, "workflow_slug": "research_pipeline", "payload": json.dumps({"run_id": 5})},
    ]
    conn = mock_db_pool.acquire().__aenter__.return_value
    conn.fetch = AsyncMock(return_value=stale_tasks)

    with patch.object(TaskQueueService, '_get_pool', return_value=mock_db_pool):
        await service.recover_stale()

    # Should have called execute to re-queue the stale task
    conn.execute.assert_called()
    sql = conn.execute.call_args[0][0]
    assert "queued" in sql