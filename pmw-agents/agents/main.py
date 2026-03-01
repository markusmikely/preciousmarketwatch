"""
PMW Agents — background worker service.

On container start:
  1. Run Alembic migrations
  2. Build the workflow graph (once)
  3. Enter async worker loop — runs one workflow tick per interval
"""
import asyncio
import os
import subprocess
import sys
import time
import logging
import signal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("pmw.main")

# How long to wait between workflow ticks (seconds)
WORKER_INTERVAL = int(os.getenv("WORKER_INTERVAL", "30"))

# ── Migrations ────────────────────────────────────────────────────────

def run_migrations() -> None:
    """
    Run Alembic migrations.
    Safe to call on every container start — alembic upgrade head is idempotent.
    """
    log.info("Running database migrations...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
        log.info("Migrations complete.")
    except Exception as e:
        log.error(f"Migration failed: {e}")
        raise


# ── Worker loop ───────────────────────────────────────────────────────

async def worker_loop(graph) -> None:
    """
    Async worker loop. Runs one workflow tick per WORKER_INTERVAL seconds.

    The loop runs indefinitely until the process receives SIGTERM or SIGINT,
    at which point it finishes the current tick and exits cleanly.

    graph is the compiled MainGraph instance — built once before the
    loop starts and reused for every tick.
    """
    log.info(f"Entering worker loop (interval={WORKER_INTERVAL}s)...")

    # Shutdown flag — set by signal handler
    shutdown = asyncio.Event()

    def _handle_signal():
        log.info("Shutdown signal received — finishing current tick then exiting.")
        shutdown.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_signal)

    while not shutdown.is_set():
        tick_start = time.monotonic()
        log.info("PMW Agents — starting workflow tick...")

        try:
            import uuid
            result = await graph.run({
                "workflow_id":  str(uuid.uuid4()),
                "triggered_by": "scheduler",
            })

            if result.succeeded:
                log.info(
                    f"Tick complete | "
                    f"topic='{result.meta.get('topic_title', 'unknown')}' "
                    f"phases={((result.output or {}).get('phase_statuses', {}))} "
                    f"cost=${result.cost_usd:.4f}"
                )
            elif result.needs_hitl:
                log.warning(
                    f"Tick requires human review (HITL) | "
                    f"errors={result.errors}"
                )
            else:
                log.error(
                    f"Tick failed | errors={result.errors}"
                )

        except Exception as e:
            # Never let an unhandled exception kill the worker loop.
            # Log it and continue to the next tick.
            log.exception(f"Unhandled error in workflow tick: {e}")

        # Sleep for the remainder of the interval, but wake immediately
        # if a shutdown signal arrives mid-sleep.
        elapsed = time.monotonic() - tick_start
        remaining = max(0.0, WORKER_INTERVAL - elapsed)

        try:
            await asyncio.wait_for(
                asyncio.shield(shutdown.wait()),
                timeout=remaining,
            )
        except asyncio.TimeoutError:
            pass   # normal — interval elapsed, run next tick

    log.info("Worker loop exited cleanly.")


# ── Entry point ───────────────────────────────────────────────────────

def _db_url() -> str:
    """Return DATABASE_URL with postgres:// -> postgresql:// for psycopg."""
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


async def main() -> None:
    log.info("PMW Agents starting...")

    # 1. Migrations — synchronous, must complete before anything else
    run_migrations()

    # 2. Build the graph using a connection pool (avoids from_conn_string context
    #    manager issues with some langgraph-checkpoint-postgres versions).
    log.info("Building workflow graph...")
    try:
        from psycopg_pool import AsyncConnectionPool
        from psycopg.rows import dict_row
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from graphs.main_graph import MainGraph

        db_url = _db_url()
        connection_kwargs = {"autocommit": True, "row_factory": dict_row}
        pool = AsyncConnectionPool(
            conninfo=db_url,
            max_size=20,
            kwargs=connection_kwargs,
            open=False,
        )
        await pool.open()
        checkpointer = AsyncPostgresSaver(pool)
        setup_result = checkpointer.setup()
        # In langgraph-checkpoint-postgres v3+, setup() returns an async context manager
        if setup_result is not None and hasattr(setup_result, "__aenter__"):
            async with setup_result:
                pass  # Tables created on enter
        elif asyncio.iscoroutine(setup_result):
            await setup_result

        graph = await MainGraph.create_with_checkpointer(checkpointer)
        log.info("Workflow graph ready.")

        # 3. Run the worker loop — never returns until shutdown signal
        await worker_loop(graph)
    except Exception as e:
        log.error(f"Failed to build workflow graph: {e}")
        raise

    log.info("PMW Agents shut down.")


if __name__ == "__main__":
    asyncio.run(main())