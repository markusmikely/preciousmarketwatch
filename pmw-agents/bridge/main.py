"""
PMW Bridge — FastAPI + WebSocket API
Accepts trigger, writes run to DB, pushes signal to Redis. Streams events via WebSocket.
Never executes agent logic.
"""
import json
import asyncio
from typing import Any

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from config import DATABASE_URL, REDIS_URL, QUEUE_AGENT, CHANNEL_EVENTS
from db import get_session
from models import WorkflowRun, WorkflowStage, Topic

app = FastAPI(title="PMW Bridge", description="Trigger API + WebSocket events")


class TriggerRequest(BaseModel):
    topic_id: int


class TriggerResponse(BaseModel):
    run_id: int
    stage_id: int
    status: str


@app.post("/workflow/trigger", response_model=TriggerResponse)
def trigger_workflow(req: TriggerRequest) -> TriggerResponse:
    """Create workflow run, first stage (research), push to Redis queue."""
    import redis

    with get_session() as session:
        topic = session.query(Topic).filter(Topic.id == req.topic_id, Topic.active).first()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found or inactive")

        run = WorkflowRun(
            topic_id=topic.id,
            status="running",
            current_stage="research",
        )
        session.add(run)
        session.flush()

        stage = WorkflowStage(
            run_id=run.id,
            stage_name="research",
            status="pending",
            attempt_number=1,
        )
        session.add(stage)
        session.flush()

        run_id = run.id
        stage_id = stage.id

    # Push to Redis (signal bus)
    r = redis.from_url(REDIS_URL)
    payload = json.dumps({"stage_id": stage_id, "run_id": run_id})
    r.lpush(QUEUE_AGENT, payload)
    r.publish(CHANNEL_EVENTS, json.dumps({
        "type": "run.started",
        "payload": {"run_id": run_id, "stage_id": stage_id, "stage_name": "research"},
    }))
    r.close()

    return TriggerResponse(run_id=run_id, stage_id=stage_id, status="queued")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "pmw-bridge"}


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """Stream Redis pub/sub events to connected clients."""
    await websocket.accept()
    pubsub = None
    try:
        r = await aioredis.from_url(REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe(CHANNEL_EVENTS)

        async def listener():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        await websocket.send_text(message["data"].decode())
                    except Exception:
                        break

        task = asyncio.create_task(listener())
        try:
            while True:
                # Keep connection alive; client can ping
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
        except WebSocketDisconnect:
            task.cancel()
    except Exception as e:
        await websocket.close(code=1011)
    finally:
        if pubsub:
            await pubsub.unsubscribe(CHANNEL_EVENTS)
            await pubsub.close()
