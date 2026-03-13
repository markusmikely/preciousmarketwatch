"""
PAAService — fetch People Also Ask questions from workflow_stages output.

Stage 2 (SERP / keyword research) stores paa_questions inside output_json.
This service retrieves them for use by downstream stages (e.g. Stage 6 affiliate).

Previously used a raw psycopg2 sync connection — now uses the shared
PostgresClient from Infrastructure so all DB access goes through one pool.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from agents.infrastructure import get_infrastructure
from agents.services.base_service import BaseDataService

log = logging.getLogger("pmw.services.paa")


class PAAService(BaseDataService):
    """
    Fetch PAA questions produced by Stage 2 and stored in workflow_stages.

    No longer accepts a database_url constructor arg — all DB access goes
    through get_infrastructure().postgres.
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_sec: float = 2.0,
    ) -> None:
        super().__init__(max_retries, backoff_sec)

    # BaseDataService.run() wraps fetch() with retry + backoff.
    # fetch() must be synchronous per the base class contract.
    # We expose an async variant (fetch_async) for callers that can await.

    def fetch(self, run_id: int, topic_id: int | None = None) -> dict[str, Any]:
        """
        Synchronous shim required by BaseDataService.run().
        Delegates to the async implementation via asyncio.

        Prefer fetch_async() when calling from an async context.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside an event loop — schedule as a task and wait
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.fetch_async(run_id, topic_id))
                    return future.result()
            else:
                return loop.run_until_complete(self.fetch_async(run_id, topic_id))
        except Exception as exc:
            return {"status": "failed", "data": None, "error": str(exc)}

    async def fetch_async(
        self,
        run_id: int,
        topic_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Async implementation — preferred in all async contexts.

        Queries workflow_stages for this run and extracts paa_questions
        from whichever stage output contains them (Stage 2 keyword research).

        Returns:
            {
                "status": "success" | "failed",
                "data": {"paa_questions": [...up to 30 questions...]}
            }
        """
        infra = get_infrastructure()

        try:
            row = await infra.postgres.fetchrow(
                """
                SELECT output_json
                FROM workflow_stages
                WHERE run_id = $1
                  AND output_json IS NOT NULL
                  AND (
                    output_json::jsonb ? 'paa_questions'
                    OR output_json::jsonb ? 'keyword_research'
                  )
                ORDER BY completed_at DESC NULLS LAST
                LIMIT 1
                """,
                run_id,
            )
        except Exception as exc:
            log.error(
                "PAA fetch DB error",
                extra={"run_id": run_id, "error": str(exc)},
            )
            return {"status": "failed", "data": None, "error": str(exc)}

        if not row or not row["output_json"]:
            return {"status": "success", "data": {"paa_questions": []}}

        output = row["output_json"]
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except json.JSONDecodeError:
                output = {}

        # Support both top-level paa_questions and nested under keyword_research
        paa = output.get("paa_questions")
        if paa is None:
            kw = output.get("keyword_research")
            if isinstance(kw, dict):
                paa = kw.get("paa_questions")

        if not paa:
            paa = []

        if isinstance(paa, str):
            try:
                paa = json.loads(paa)
            except json.JSONDecodeError:
                paa = []

        return {
            "status": "success",
            "data": {"paa_questions": list(paa)[:30]},
        }