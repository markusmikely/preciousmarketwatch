"""PAA (People Also Ask) service — fetch Stage 2 questions from DB."""

import json
import os
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from .base_service import BaseDataService


class PAAService(BaseDataService):
    """Fetch PAA questions from Stage 2 workflow output stored in DB."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_sec: float = 2.0,
        database_url: str | None = None,
    ) -> None:
        super().__init__(max_retries, backoff_sec)
        self._database_url = database_url or os.getenv("DATABASE_URL")

    def fetch(self, run_id: int, topic_id: int | None = None) -> dict[str, Any]:
        """Load PAA questions from workflow_stages for the given run.

        Stage 2 (keyword/serp research) stores paa_questions in output_json.
        We query workflow_stages for this run and extract paa_questions from
        any stage whose output contains them.
        """
        if not self._database_url:
            return {"status": "failed", "data": None, "error": "DATABASE_URL not set"}

        db_url = self._database_url
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        try:
            conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        except Exception as e:
            return {"status": "failed", "data": None, "error": str(e)}

        try:
            with conn.cursor() as cur:
                # Find stages with paa_questions in output_json
                cur.execute(
                    """
                    SELECT output_json
                    FROM workflow_stages
                    WHERE run_id = %s
                      AND output_json IS NOT NULL
                      AND (
                        output_json ? 'paa_questions'
                        OR output_json ? 'keyword_research'
                      )
                    ORDER BY completed_at DESC NULLS LAST
                    LIMIT 1
                    """,
                    (run_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()

        if not row or not row.get("output_json"):
            return {"status": "success", "data": {"paa_questions": []}}

        output = row["output_json"]
        if isinstance(output, str):
            output = json.loads(output) if output else {}

        # Support both top-level paa_questions and nested under keyword_research
        paa = output.get("paa_questions")
        if paa is None and "keyword_research" in output:
            kw = output["keyword_research"]
            paa = kw.get("paa_questions") if isinstance(kw, dict) else None

        if not paa:
            paa = []

        if isinstance(paa, str):
            paa = json.loads(paa) if paa else []

        return {
            "status": "success",
            "data": {"paa_questions": list(paa)[:30]},
        }
