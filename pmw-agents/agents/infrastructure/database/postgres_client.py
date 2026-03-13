from __future__ import annotations
 
import logging
import os
from contextlib import asynccontextmanager
from typing import Any
 
import asyncpg
 
log = logging.getLogger("pmw.infra.postgres")
 
 
def _normalise_dsn(url: str) -> str:
    """Railway exposes postgres://, asyncpg requires postgresql://."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

class PostgresClient:
    """
    Async asyncpg connection pool.
 
    All query helpers acquire a connection from the pool, run the query,
    and release the connection — no manual connection management needed
    in calling code.
    """
    def __init__(
        self,
        dsn: str | None = None,
        min_size: int = 2,
        max_size: int = 10,
        command_timeout: float = 30.0,
    ) -> None:
        raw = dsn or os.environ.get("DATABASE_URL", "")
        if not raw:
            raise RuntimeError(
                "DATABASE_URL is not set. "
                "Provide it via the dsn argument or the DATABASE_URL environment variable."
            )
        self._dsn = _normalise_dsn(raw)
        self._min_size = min_size
        self._max_size = max_size
        self._command_timeout = command_timeout
        self._pool: asyncpg.Pool | None = None
 
    async def connect(self) -> None:
        """
        Create the asyncpg connection pool.
        Safe to call multiple times — no-op if pool already exists.
        """
        if self._pool is not None:
            return
        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
            command_timeout=self._command_timeout,
        )
        log.info(
            "PostgresClient pool created",
            extra={"min_size": self._min_size, "max_size": self._max_size},
        )

    async def close(self) -> None:
        """
        Gracefully close the connection pool.
        Waits for all active connections to complete before closing.
        """
        if self._pool:
            await self._pool.close()
            self._pool = None
            log.info("PostgresClient pool closed")
 
    async def _get_pool(self) -> asyncpg.Pool:
        """Return the pool, connecting lazily on first use if needed."""
        if self._pool is None:
            await self.connect()
        return self._pool  # type: ignore[return-value]

     # ── Context managers ───────────────────────────────────────────────────
 
    @asynccontextmanager
    async def connection(self):
        """
        Acquire a single connection as an async context manager.
 
        Usage:
            async with infra.postgres.connection() as conn:
                await conn.execute(...)
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            yield conn
 
    @asynccontextmanager
    async def transaction(self):
        """
        Run statements inside an explicit transaction.
 
        Usage:
            async with infra.postgres.transaction() as conn:
                await conn.execute("INSERT ...")
                await conn.execute("UPDATE ...")
            # auto-committed on exit, rolled back on exception
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                yield conn


     # ── Query helpers ───────────────────────────────────────────────────────
 
    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        """
        Fetch a single row. Returns None if no rows match.
 
        Usage:
            row = await infra.postgres.fetchrow(
                "SELECT * FROM workflow_runs WHERE id = $1", run_id
            )
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
 
    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """
        Fetch all matching rows as a list.
 
        Usage:
            rows = await infra.postgres.fetch(
                "SELECT * FROM topics WHERE active = $1", True
            )
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)
 
    async def fetchval(self, query: str, *args: Any) -> Any:
        """
        Fetch a single value from the first column of the first row.
 
        Usage:
            count = await infra.postgres.fetchval(
                "SELECT count(*) FROM workflow_runs WHERE status = $1", "running"
            )
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args)
 
    async def execute(self, query: str, *args: Any) -> str:
        """
        Execute a statement (INSERT / UPDATE / DELETE).
        Returns the Postgres status string, e.g. "INSERT 0 1".
 
        Usage:
            await infra.postgres.execute(
                "UPDATE workflow_runs SET status = $1 WHERE id = $2",
                "complete", run_id,
            )
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)
 
    async def executemany(self, query: str, args_list: list[tuple]) -> None:
        """
        Execute a statement once for each tuple in args_list.
        Efficient for bulk inserts.
 
        Usage:
            await infra.postgres.executemany(
                "INSERT INTO llm_call_logs (run_id, stage_name, cost_usd) VALUES ($1, $2, $3)",
                [(1, "research", 0.001), (1, "planning", 0.002)],
            )
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.executemany(query, args_list)