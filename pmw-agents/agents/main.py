"""
PMW Agents — background worker service.

On container start:
  1. Run Alembic migrations
  2. Run the workflow
"""
import asyncio
import logging
import os
import subprocess
import sys
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("pmw.main")


# ── Migrations ────────────────────────────────────────────────────────

def run_migrations() -> None:
    """
    Run Alembic migrations synchronously before the event loop starts.
    Safe to call on every container start — 'alembic upgrade head' is idempotent.
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
    except Exception as exc:
        log.error(f"Migration failed: {exc}")
        raise

# ── Entry point ────────────────────────────────────────────────────────────

async def main() -> None:
    log.info("PMW Agents starting...")
    
    # 1. Run migrations before connecting anything
    run_migrations()
 
    # 2. Connect infrastructure (Postgres pool, Redis, LLM SDKs, HTTP session)
    from infrastructure import get_infrastructure
    infra = get_infrastructure()
    await infra.connect()

    try:
        # 3. Recover any tasks that were in-flight when the last worker died
        try:
            from services.task_queue_service import TaskQueueService
            await TaskQueueService().recover_stale()
            log.info("Stale task recovery complete.")
        except ImportError:
            log.warning("TaskQueueService not found — skipping stale recovery.")
        except Exception as exc:
            log.warning(f"Stale task recovery failed (non-fatal): {exc}")
 
        # 4. Run the workflow orchestrator
        from orchestrator import run_workflow
        log.info("Starting workflow execution...")
        await run_workflow(triggered_by="scheduler")
 
    except Exception as exc:
        log.error(f"Worker error: {exc}")
        raise
 
    finally:
        # 5. Always close infrastructure cleanly, even on error
        await infra.close()
        log.info("PMW Agents shut down.")
 
 
if __name__ == "__main__":
    asyncio.run(main())