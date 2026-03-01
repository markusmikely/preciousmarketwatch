# graphs/main_graph.py

from __future__ import annotations

import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from graphs.base_graph import BaseGraph
from graphs.phase_result import PhaseResult
from graphs.research_graph import ResearchGraph
from graphs.planning_graph import PlanningGraph
from graphs.generation_graph import GenerationGraph
from state.pipeline_state import PipelineState

log = logging.getLogger(__name__)


class MainGraph(BaseGraph):
    """
    Top-level workflow orchestrator.

    Chains three phase subgraphs:
        research -> planning -> generation -> END

    Each phase node does exactly three things:
        1. Call subgraph.run(input)    — complete black box
        2. Check result.succeeded      — route on failure
        3. Return dict of PipelineState updates only

    The parent knows nothing about what happens inside a phase.
    Token usage, internal stages, retries — all invisible here.
    Adding a phase = one new node + one new edge + one run() call.
    """

    _state_schema = PipelineState

    def __init__(self, checkpointer: AsyncPostgresSaver):
        super().__init__(checkpointer)
        self._research:   ResearchGraph   | None = None
        self._planning:   PlanningGraph   | None = None
        self._generation: GenerationGraph | None = None

    @classmethod
    async def create(cls) -> "MainGraph":
        """
        Build MainGraph and all phase subgraphs.
        Subgraphs are built once here and reused for every run.
        """
        # Create the checkpointer using connection pool (same as in BaseGraph)
        import os
        from psycopg_pool import AsyncConnectionPool
        from psycopg.rows import dict_row
        
        connection_kwargs = {
            "autocommit": True,
            "row_factory": dict_row
        }
        
        pool = AsyncConnectionPool(
            conninfo=os.environ["DATABASE_URL"],
            max_size=20,
            kwargs=connection_kwargs,
            open=False
        )
        
        await pool.open()
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()

        instance = cls(checkpointer)
        
        # Create phase subgraphs - they will create their own checkpointer instances
        # This is okay because they'll use separate connection pools
        instance._research   = await ResearchGraph.create()
        instance._planning   = await PlanningGraph.create()
        instance._generation = await GenerationGraph.create()

        instance._build_nodes()
        instance._build_edges()
        instance._compiled = instance._builder.compile(
            checkpointer=checkpointer
        )

        log.info("MainGraph compiled and ready")
        return instance

    # ── Graph construction ────────────────────────────────────────────

    def _build_nodes(self):
        self.add_node("research",   self._research_node)
        self.add_node("planning",   self._planning_node)
        self.add_node("generation", self._generation_node)

    def _build_edges(self):
        self.add_edge(self.START,   "research")
        self.add_edge("research",   "planning")
        self.add_edge("planning",   "generation")
        self.add_edge("generation", self.END)

    # ── Input / output translation ────────────────────────────────────

    def _make_input(self, input_data: dict) -> dict:
        return {
            "workflow_id":       input_data["workflow_id"],
            "triggered_by":      input_data.get("triggered_by", "scheduler"),
            "topic_wp_id":       None,
            "topic_title":       None,
            "research_bundle":   None,
            "content_plan":      None,
            "generation_result": None,
            "phase_statuses":    {},
            "total_cost_usd":    0.0,
            "errors":            [],
            "status":            "running",
            "wp_post_id":        None,
        }

    def _make_result(self, final_state: dict) -> PhaseResult:
        return PhaseResult(
            status   = final_state.get("status", "failed"),
            output   = {
                "research_bundle":   final_state.get("research_bundle"),
                "content_plan":      final_state.get("content_plan"),
                "generation_result": final_state.get("generation_result"),
                "wp_post_id":        final_state.get("wp_post_id"),
                "phase_statuses":    final_state.get("phase_statuses", {}),
            },
            cost_usd = final_state.get("total_cost_usd", 0.0),
            errors   = final_state.get("errors", []),
            meta     = {
                "topic_title": final_state.get("topic_title"),
                "topic_wp_id": final_state.get("topic_wp_id"),
            },
        )

    # ── Phase nodes ───────────────────────────────────────────────────
    #
    # Pattern is identical for every node:
    #   result = await self._subgraph.run({only what this phase needs})
    #   if not result.succeeded: return self._phase_failure(...)
    #   return {only the PipelineState fields that changed}
    #
    # The node does NOT know:
    #   - How many internal stages the subgraph has
    #   - What the subgraph's internal state fields are called
    #   - How the subgraph handles retries or HITL internally

    async def _research_node(self, state: PipelineState) -> dict:
        result: PhaseResult = await self._research.run({
            "workflow_id":  state["workflow_id"],
            "triggered_by": state.get("triggered_by", "scheduler"),
        })

        if not result.succeeded:
            return self._phase_failure(state, "research", result)

        return {
            "research_bundle": result.output,
            "topic_wp_id":     result.meta.get("topic_wp_id"),
            "topic_title":     result.meta.get("topic_title"),
            "phase_statuses":  {**state.get("phase_statuses", {}), "research": "complete"},
            "total_cost_usd":  state.get("total_cost_usd", 0.0) + result.cost_usd,
            "errors":          state.get("errors", []) + result.errors,
        }

    async def _planning_node(self, state: PipelineState) -> dict:
        result: PhaseResult = await self._planning.run({
            "workflow_id":     state["workflow_id"],
            "research_bundle": state.get("research_bundle"),
        })

        if not result.succeeded:
            return self._phase_failure(state, "planning", result)

        return {
            "content_plan":   result.output,
            "phase_statuses": {**state.get("phase_statuses", {}), "planning": "complete"},
            "total_cost_usd": state.get("total_cost_usd", 0.0) + result.cost_usd,
            "errors":         state.get("errors", []) + result.errors,
        }

    async def _generation_node(self, state: PipelineState) -> dict:
        result: PhaseResult = await self._generation.run({
            "workflow_id":     state["workflow_id"],
            "research_bundle": state.get("research_bundle"),
            "content_plan":    state.get("content_plan"),
        })

        if not result.succeeded:
            return self._phase_failure(state, "generation", result)

        return {
            "generation_result": result.output,
            "wp_post_id":        (result.output or {}).get("wp_post_id"),
            "phase_statuses":    {**state.get("phase_statuses", {}), "generation": "complete"},
            "total_cost_usd":    state.get("total_cost_usd", 0.0) + result.cost_usd,
            "errors":            state.get("errors", []) + result.errors,
            "status":            "complete",
        }

    # ── Shared failure handler ────────────────────────────────────────

    @staticmethod
    def _phase_failure(state: PipelineState, phase: str, result: PhaseResult) -> dict:
        log.error(f"Phase '{phase}' failed | status={result.status}")
        return {
            "phase_statuses": {**state.get("phase_statuses", {}), phase: result.status},
            "total_cost_usd": state.get("total_cost_usd", 0.0) + result.cost_usd,
            "errors":         state.get("errors", []) + result.errors,
            "status":         "failed",
        }