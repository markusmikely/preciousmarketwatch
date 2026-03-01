"""
Database helpers for workflow runs.
run_id = workflow_runs.id — the single canonical identifier for a pipeline run.
"""
import os
from typing import Optional

import psycopg
from psycopg.rows import dict_row


def _conninfo() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def create_workflow_run(
    topic_id: Optional[int] = None,
    triggered_by: str = "scheduler",
) -> int:
    """
    Insert a new workflow_runs row and return its id.
    This id is the run_id used throughout the pipeline.
    """
    with psycopg.connect(_conninfo(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO workflow_runs (topic_id, status)
                VALUES (%s, 'pending')
                RETURNING id
                """,
                (topic_id,),
            )
            row = cur.fetchone()
            conn.commit()
            return row["id"]
