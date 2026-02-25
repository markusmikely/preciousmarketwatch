# PMW Bridge

FastAPI WebSocket server connecting the LangGraph agent engine to WordPress Mission Control.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `WS /ws` — WebSocket for real-time events
- `GET /health` — Health check

## Redis

Ensure Redis is running. Events are published to channel `pmw:events`.

## WordPress

Set in wp-config.php:
```php
define( 'PMW_BRIDGE_WS_URL', 'ws://localhost:8000/ws' );
```
