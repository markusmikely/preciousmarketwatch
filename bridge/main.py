"""
PMW Bridge — FastAPI WebSocket server
Subscribes to Redis, pushes events to WordPress dashboard.
"""
import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis

REDIS_URL = "redis://localhost:6379"
CHANNEL = "pmw:events"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await aioredis.from_url(REDIS_URL)
    yield
    await app.state.redis.close()


app = FastAPI(
    title="PMW Bridge",
    description="WebSocket bridge between LangGraph agents and WordPress Mission Control",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    pubsub = app.state.redis.pubsub()
    await pubsub.subscribe(CHANNEL)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"].decode())
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(CHANNEL)
        await pubsub.close()


@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


async def publish_event(event_type: str, payload: dict):
    """Call from agent engine to publish events to Redis."""
    msg = json.dumps({
        "type": event_type,
        "payload": payload,
        "ts": datetime.utcnow().isoformat(),
    })
    await app.state.redis.publish(CHANNEL, msg)
