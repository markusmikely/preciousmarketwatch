"""
PMW Bridge Config — Railway-aware
"""
import os

_raw = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pmw_agents")
DATABASE_URL = _raw.replace("postgres://", "postgresql://", 1) if _raw.startswith("postgres://") else _raw
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
SERVICE_ROLE = os.environ.get("SERVICE_ROLE", "bridge")

QUEUE_AGENT = "agent:queue"
CHANNEL_EVENTS = "pmw:events"
