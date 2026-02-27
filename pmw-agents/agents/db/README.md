# PMW Database Setup (Railway Postgres + Alembic)

This directory contains Alembic migrations for the PMW agent database. The schema mirrors WordPress `pmw_topic` meta and stores workflow runs, affiliate intelligence, and audit logs.

## Prerequisites

- Python 3.10+
- Access to Railway Postgres (or local Postgres for development)
- `DATABASE_URL` environment variable

---

## Step 1 — Railway Environment Variables

In **Railway** → Your Postgres service → **Variables** (or **Connect**):

1. Copy the connection string. It looks like:
   ```
   postgresql://USER:PASSWORD@HOST:PORT/DBNAME
   ```
   Railway may show `postgres://` — Alembic converts this to `postgresql://` automatically.

2. Add this to your **PMW-Agents** and **PMW-Bridge** services:
   ```
   DATABASE_URL=postgresql://...
   ```

---

## Step 2 — Install Python Dependencies

From the `pmw-agents` project root:

```bash
pip install -r agents/requirements.txt
```

Required packages include:

- `alembic` — migration runner
- `psycopg2-binary` — PostgreSQL driver (Alembic uses sync connections)
- `asyncpg` — async driver for the app runtime

---

## Step 3 — Configure Alembic (Optional)

Alembic reads `DATABASE_URL` from the environment. No changes are needed if that variable is set.

For local development without Railway:

1. Create `.env` in `pmw-agents/` or `pmw-agents/agents/`:
   ```
   DATABASE_URL=postgresql://user:pass@localhost:5432/pmw
   ```

2. Load it before running Alembic (e.g. `source .env` or use `python-dotenv`).

You can also set `sqlalchemy.url` in `alembic.ini` for local runs, but env var is preferred.

---

## Step 4 — Run Migrations

From the **pmw-agents** project root:

```bash
# Apply all pending migrations
alembic upgrade head

# Check current revision
alembic current

# Show migration history
alembic history
```

On first run, `001_initial_schema` creates all tables:

- `affiliates` — affiliate partners
- `topics` — WP-aligned topic definitions (target_keyword, summary, asset_class, etc.)
- `workflow_runs` — content pipeline runs
- `workflow_stages` — per-stage results and scores
- `affiliate_intelligence_runs` — research outputs per affiliate
- `affiliate_intelligence_summary` — aggregated affiliate intelligence
- `agent_configs` — agent model/threshold config
- `interventions` — human corrections
- `vault_events` — immutable audit log
- `users` — dashboard users
- `generated_media` — images/infographics
- `social_posts` — social content per run
- `performance_reports` — GA4/Clarity/ Search Console data
- `article_performance` — per-article metrics

---

## Step 5 — Auto-Run Migrations on Startup (Recommended)

To run migrations when the app starts (e.g. on Railway deploy):

Add to your FastAPI/LangGraph app startup:

```python
import subprocess
import os

def run_migrations():
    """Run Alembic migrations on app startup."""
    if not os.getenv("DATABASE_URL"):
        return  # Skip if no DB configured
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=os.path.dirname(os.path.dirname(__file__)),  # pmw-agents root
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Migration failed: {result.stderr}")
```

Call `run_migrations()` before starting the server.

---

## Topics Table — WordPress Alignment

The `topics` table matches WordPress `pmw_topic` CPT meta:

| Postgres Column    | WordPress Meta          |
|--------------------|-------------------------|
| `topic_name`       | post title              |
| `target_keyword`   | `pmw_target_keyword`    |
| `summary`          | `pmw_summary`           |
| `include_keywords` | `pmw_include_keywords`  |
| `exclude_keywords` | `pmw_exclude_keywords`  |
| `asset_class`      | `pmw_asset_class`       |
| `product_type`     | `pmw_product_type`      |
| `geography`        | `pmw_geography`         |
| `is_buy_side`      | `pmw_is_buy_side`       |
| `intent_stage`     | `pmw_intent_stage`      |
| `priority`         | `pmw_priority`          |
| `schedule_cron`    | `pmw_schedule_cron`     |
| `agent_status`     | `pmw_agent_status`      |
| `last_run_at`      | `pmw_last_run_at`       |
| `run_count`        | `pmw_run_count`         |
| `last_run_id`      | `pmw_last_run_id`       |
| `last_wp_post_id`  | `pmw_last_wp_post_id`   |
| `wp_category_id`   | `pmw_wp_category_id`    |
| `affiliate_page_id`| `pmw_affiliate_page_id` |

**Important:** Topics are authored in WordPress. The agent DB stores run outputs and locks. The `topics` table can be a sync/cache from WP REST API, or populated by a bridge service.

---

## Creating New Migrations

```bash
# Create a new revision
alembic revision -m "add_new_table"

# Edit the generated file in agents/db/migrations/versions/
# Implement upgrade() and downgrade()
```

---

## Troubleshooting

| Problem | Solution |
|--------|----------|
| `ModuleNotFoundError: psycopg2` | `pip install psycopg2-binary` |
| `Connection refused` | Check `DATABASE_URL` and Postgres host/port |
| `relation "topics" does not exist` | Run `alembic upgrade head` |
| Railway `postgres://` URL | Env script converts to `postgresql://` automatically |
