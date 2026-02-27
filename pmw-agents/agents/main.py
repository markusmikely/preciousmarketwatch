"""
PMW Agents — background worker service.

On container start:
  1. Run Alembic migrations
  2. Enter infinite loop with heartbeat
"""
import os
import subprocess
import sys
import time


def run_migrations() -> None:
    """
    Run Alembic migrations.
    Safe to call on every container start.
    """
    print("Running database migrations...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
        print("Migrations complete.")
    except Exception as e:
        print("Migration failed:", str(e))
        raise


def worker_loop() -> None:
    """
    Placeholder worker loop.
    Eventually this will:
      - Poll DB for pending topics
      - Execute workflow
      - Update workflow_runs
    """
    print("Entering worker loop...")

    while True:
        print("PMW Agents heartbeat: waiting for work...")
        time.sleep(30)


if __name__ == "__main__":
    print("PMW Agents starting...")

    run_migrations()

    print("PMW Agents started successfully.")

    worker_loop()
