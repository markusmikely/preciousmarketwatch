"""
PMW Config — Railway-aware environment
In production (Railway), all services use internal DNS hostnames. Never use localhost.
"""
import os

# Postgres — Railway: postgres://USER:PASSWORD@PMW-Postgres:5432/DB_NAME
_raw = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pmw_agents")
DATABASE_URL = _raw.replace("postgres://", "postgresql://", 1) if _raw.startswith("postgres://") else _raw

# Redis — Railway: redis://:PASSWORD@PMW-Redis:6379
REDIS_URL = os.environ.get(
    "REDIS_URL",
    "redis://localhost:6379",
)

SERVICE_ROLE = os.environ.get("SERVICE_ROLE", "agents")
WORKER_CONCURRENCY = int(os.environ.get("WORKER_CONCURRENCY", "2"))
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Queue / channel keys
QUEUE_AGENT = "agent:queue"
CHANNEL_EVENTS = "pmw:events"
