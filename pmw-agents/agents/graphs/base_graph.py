# graphs/base_graph.py

from __future__ import annotations

import os
import logging
from abc import ABC, abstractmethod
from typing import Type

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from graphs.phase_result import PhaseResult

log = logging.getLogger(__name__)


class BaseGraph(ABC):
    """
    Base class for all PMW graphs.

    Every graph — main orchestrator and every phase subgraph — shares
    the same interface:
        graph  = await SubclassGraph.create()
        result = await graph.run(input_data)   # returns PhaseResult

    Subclasses declare:
        _state_schema  : the TypedDict for this graph's internal state
        _build_nodes() : add nodes to self._builder
        _build_edges() : add edges to self._builder
        _make_input()  : translate raw input dict into initial state
        _make_result() : translate final state into PhaseResult

    Everything else is handled here.
    """

    # Declare in subclass: _state_schema = MyStateType
    _state_schema: Type = None

    def __init__(self, checkpointer: AsyncPostgresSaver):
        assert self._state_schema is not None, (
            f"{self.__class__.__name__} must declare _state_schema"
        )
        self._builder      = StateGraph(self._state_schema)
        self._checkpointer = checkpointer
        self._compiled: CompiledStateGraph | None = None
        self.START = START
        self.END   = END

    # ── Async factory ─────────────────────────────────────────────────

    # @classmethod
    async def create_with_checkpointer(
        cls, checkpointer: AsyncPostgresSaver
    ) -> "BaseGraph":
        """Build and compile graph using an existing checkpointer."""
        instance = cls(checkpointer)
        instance._build_nodes()
        instance._build_edges()
        instance._compiled = instance._builder.compile(checkpointer=checkpointer)
        log.info(f"{cls.__name__} compiled and ready")
        return instance

    @classmethod
    async def create(cls) -> "BaseGraph":
        """
        Build, compile, and return a ready-to-run graph using a new connection pool.
        For production, prefer create_with_checkpointer when the caller provides
        a checkpointer (e.g. from AsyncPostgresSaver.from_conn_string context).
        """
        from psycopg_pool import AsyncConnectionPool
        from psycopg.rows import dict_row

        db_url = os.environ.get("DATABASE_URL", "")
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        connection_kwargs = {"autocommit": True, "row_factory": dict_row}
        pool = AsyncConnectionPool(
            conninfo=db_url, max_size=20, kwargs=connection_kwargs, open=False
        )
        await pool.open()
        checkpointer = AsyncPostgresSaver(pool)
        setup_result = checkpointer.setup()
        if setup_result is not None and hasattr(setup_result, "__aenter__"):
            async with setup_result:
                pass
        elif asyncio.iscoroutine(setup_result):
            await setup_result
        return await cls.create_with_checkpointer(checkpointer)

    # ── Public run interface ──────────────────────────────────────────

    async def run(self, input_data: dict) -> PhaseResult:
        """
        Invoke this graph with the given input dict.

        The caller does not need to know the subgraph's internal state
        schema. _make_input() translates the dict internally.
        _make_result() ensures only a PhaseResult crosses the boundary
        back to the caller — the full internal state is never exposed.
        """
        assert self._compiled is not None, (
            f"{self.__class__.__name__}.run() called before create()"
        )

        thread_id = self._make_thread_id(input_data)
        config = {
            "configurable":    {"thread_id": thread_id},
            "recursion_limit": 60,
        }

        log.info(f"{self.__class__.__name__} starting | thread={thread_id}")

        try:
            initial_state = self._make_input(input_data)
            final_state   = await self._compiled.ainvoke(initial_state, config=config)
            result        = self._make_result(final_state)
        except Exception as exc:
            log.exception(f"{self.__class__.__name__} raised unexpectedly")
            result = PhaseResult(
                status   = "failed",
                output   = None,
                cost_usd = 0.0,
                errors   = [{"error": str(exc), "source": self.__class__.__name__}],
            )

        log.info(
            f"{self.__class__.__name__} done | "
            f"status={result.status} cost=${result.cost_usd:.4f}"
        )
        return result

    # ── Abstract methods — implement in each subclass ─────────────────

    @abstractmethod
    def _build_nodes(self):
        """Add nodes to self._builder."""
        raise NotImplementedError

    @abstractmethod
    def _build_edges(self):
        """Add edges to self._builder."""
        raise NotImplementedError

    @abstractmethod
    def _make_input(self, input_data: dict) -> dict:
        """
        Translate the caller's input dict into this graph's initial state.
        Keeps the caller decoupled from the internal state schema.
        """
        raise NotImplementedError

    @abstractmethod
    def _make_result(self, final_state: dict) -> PhaseResult:
        """
        Translate final internal state into a PhaseResult.
        This is the ONLY thing that escapes to the caller.
        Discard everything else here.
        """
        raise NotImplementedError

    def _make_thread_id(self, input_data: dict) -> str:
        """
        Stable thread_id for checkpointing, scoped to workflow + phase.
        Override if you need different scoping.
        """
        workflow_id = input_data.get("workflow_id", "unknown")
        print(f"test workflow_id: {workflow_id}")
        phase_name  = self.__class__.__name__.lower().replace("graph", "")
        return f"{workflow_id}:{phase_name}"

    # ── Builder proxies — cleaner than self._builder.add_node() ───────

    def add_node(self, name: str, fn):
        self._builder.add_node(name, fn)

    def add_edge(self, source: str, target: str):
        self._builder.add_edge(source, target)

    def add_conditional_edges(self, source: str, router, path_map: dict):
        self._builder.add_conditional_edges(source, router, path_map)

    # ── Cost helper — available to all subclasses ─────────────────────

    @staticmethod
    def _sum_cost(model_usage: list) -> float:
        return round(sum(u.get("cost_usd", 0.0) for u in model_usage), 6)