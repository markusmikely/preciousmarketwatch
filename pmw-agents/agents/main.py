"""
PMW Agents — background worker service.

On container start:
  1. Run Alembic migrations
  2. Run the workflow
"""
import asyncio
import os
import subprocess
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("pmw.main")


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


# ── Entry point ───────────────────────────────────────────────────────

async def main() -> None:
    log.info("PMW Agents starting...")

    # 1. Run migrations first
    run_migrations()

    # 2. Import and run the workflow from orchestrator
    try:
        from orchestrator import run_workflow
        
        log.info("Starting workflow execution...")
        await run_workflow(triggered_by="scheduler")
        
    except Exception as e:
        log.error(f"Workflow execution failed: {e}")
        raise

    log.info("PMW Agents shut down.")


if __name__ == "__main__":
    asyncio.run(main())