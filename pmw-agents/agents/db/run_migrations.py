"""
Run Alembic migrations on app startup.

Usage:
    from agents.db.run_migrations import run_migrations
    run_migrations()

Or from CLI (from pmw-agents root):
    python -m agents.db.run_migrations
"""
import os
import subprocess
import sys


def run_migrations() -> bool:
    """
    Run alembic upgrade head. Returns True on success, False on skip, raises on failure.
    Skips if DATABASE_URL is not set.
    """
    if not os.getenv("DATABASE_URL"):
        return False

    # pmw-agents root (parent of agents/)
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Alembic migration failed:\n{result.stderr or result.stdout}")

    return True


if __name__ == "__main__":
    try:
        run_migrations()
        print("Migrations completed successfully.")
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
