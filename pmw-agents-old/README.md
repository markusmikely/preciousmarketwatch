# PMW Agents — Railway Deployment

Railway-aware architecture: PMW-Bridge (API), PMW-Agents (workers), PMW-Postgres, PMW-Redis.

## Structure

| Service | Responsibility | Public? |
|---------|----------------|---------|
| PMW-Bridge | FastAPI + WebSocket API | Yes (HTTP) |
| PMW-Agents | LangGraph orchestration workers | No (private only) |
| PMW-Postgres | Persistent state | No |
| PMW-Redis | Queue + ephemeral state | No |

## Environment Variables (Railway)

### PMW-Bridge
- `DATABASE_URL` — Postgres connection
- `REDIS_URL` — Redis connection
- `JWT_SECRET` — Auth (optional for v1)
- `SERVICE_ROLE=bridge`

### PMW-Agents
- `DATABASE_URL` — Postgres connection
- `REDIS_URL` — Redis connection
- `ANTHROPIC_API_KEY` — LLM API key
- `SERVICE_ROLE=agents`
- `WORKER_CONCURRENCY=2`

In production, use Railway internal hostnames (e.g. `@PMW-Postgres:5432`).

## Build Order

1. **Migrations** — Run in Railway (Postgres) before first deploy:
   ```bash
   cd agents && alembic upgrade head
   ```

2. **Seed topics** (optional):
   ```bash
   cd agents && python scripts/seed_topics.py
   ```

3. **Trigger a run**:
   ```bash
   curl -X POST https://YOUR-BRIDGE-URL/workflow/trigger -H "Content-Type: application/json" -d '{"topic_id": 1}'
   ```

## API

- `POST /workflow/trigger` — `{"topic_id": 1}` → creates run, pushes to Redis queue
- `GET /health` — Health check
- `WS /ws/events` — Real-time events (stage.started, stage.complete, run.complete, etc.)

## V1 Pipeline Flow

Topic → Research (score ≥ 0.75) → Planning (≥ 0.80) → Content (≥ 0.80) → Publish (draft to WP)
