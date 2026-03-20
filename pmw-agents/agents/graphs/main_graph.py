# graphs/main_graph.py
"""
Top-level workflow orchestrator — multi-topic architecture.

Research phase now returns a LIST of research_bundles (one per topic).
Planning and generation phases process each bundle independently,
all sharing the same pipeline run_id.

Flow:
  research → [list of bundles] → for each bundle: planning → generation
"""

from __future__ import annotations

import asyncio
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
    Top-level orchestrator — multi-topic.

    research_node: produces a list of research_bundles
    planning_node: processes each bundle through planning
    generation_node: processes each planned bundle through generation

    All bundles share the same run_id. Per-topic tracking is done via
    the topic_wp_id recorded in workflow_stages and topic_briefs.
    """

    _state_schema = PipelineState

    def __init__(self, checkpointer: AsyncPostgresSaver):
        super().__init__(checkpointer)
        self._research:   ResearchGraph   | None = None
        self._planning:   PlanningGraph   | None = None
        self._generation: GenerationGraph | None = None

    @classmethod
    async def create_with_checkpointer(
        cls, checkpointer: AsyncPostgresSaver
    ) -> "MainGraph":
        instance = cls(checkpointer)
        instance._research = await ResearchGraph.create_with_checkpointer(checkpointer)
        instance._planning = await PlanningGraph.create_with_checkpointer(checkpointer)
        instance._generation = await GenerationGraph.create_with_checkpointer(checkpointer)

        instance._build_nodes()
        instance._build_edges()
        instance._compiled = instance._builder.compile(checkpointer=checkpointer)

        log.info("MainGraph compiled and ready")
        return instance

    @classmethod
    async def create(cls) -> "MainGraph":
        import os
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

    # ── Graph construction ────────────────────────────────────────────

    def _build_nodes(self):
        self.add_node("research",   self._research_node)
        self.add_node("process_bundles", self._process_bundles_node)

    def _build_edges(self):
        self.add_edge(self.START, "research")
        self.add_conditional_edges(
            "research",
            self._route_after_research,
            {
                "process": "process_bundles",
                "empty":   self.END,
                "failed":  self.END,
            },
        )
        self.add_edge("process_bundles", self.END)

    # ── Input / output translation ────────────────────────────────────

    def _make_input(self, input_data: dict) -> dict:
        return {
            "run_id":            input_data["run_id"],
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
            # Multi-topic fields
            "research_bundles":  [],
            "planning_results":  [],
            "generation_results": [],
        }

    def _make_result(self, final_state: dict) -> PhaseResult:
        bundles = final_state.get("research_bundles") or []
        planning = final_state.get("planning_results") or []
        generation = final_state.get("generation_results") or []

        return PhaseResult(
            run_id   = final_state.get("run_id"),
            status   = final_state.get("status", "failed"),
            output   = {
                "research_bundles":   bundles,
                "planning_results":   planning,
                "generation_results": generation,
                "phase_statuses":     final_state.get("phase_statuses", {}),
                "topics_processed":   len(bundles),
            },
            cost_usd = final_state.get("total_cost_usd", 0.0),
            errors   = final_state.get("errors", []),
            meta     = {
                "topics_researched": len(bundles),
                "topics_planned":    len(planning),
                "topics_generated":  len(generation),
                "topic_titles":      [
                    b.get("topic", {}).get("title", "")
                    for b in bundles
                ],
            },
        )

    # ── Routing ───────────────────────────────────────────────────────

    @staticmethod
    def _route_after_research(state: dict) -> str:
        if state.get("status") == "failed":
            return "failed"
        bundles = state.get("research_bundles") or []
        if len(bundles) == 0:
            return "empty"
        return "process"

    # ── Phase nodes ───────────────────────────────────────────────────

    async def _research_node(self, state: PipelineState) -> dict:
        """
        Run research phase — produces a LIST of research_bundles.
        """
        result: PhaseResult = await self._research.run({
            "run_id":       state["run_id"],
            "triggered_by": state.get("triggered_by", "scheduler"),
        })

        bundles = result.output if result.succeeded and isinstance(result.output, list) else []

        return {
            "run_id":           state["run_id"],
            "research_bundles": bundles,
            "phase_statuses":   {
                **state.get("phase_statuses", {}),
                "research": "complete" if result.succeeded else result.status,
            },
            "total_cost_usd":   state.get("total_cost_usd", 0.0) + result.cost_usd,
            "errors":           state.get("errors", []) + result.errors,
            "status":           "running" if bundles else result.status,
        }

    async def _process_bundles_node(self, state: PipelineState) -> dict:
        """
        For each research_bundle, run planning → generation.

        All bundles share the same run_id. Each bundle produces
        independent planning_result and generation_result.
        """
        run_id = state["run_id"]
        bundles = state.get("research_bundles") or []
        planning_results = []
        generation_results = []
        total_cost = state.get("total_cost_usd", 0.0)
        all_errors = list(state.get("errors", []))

        log.info(
            f"Processing {len(bundles)} bundle(s) through planning → generation",
            extra={"run_id": run_id},
        )

        for i, bundle in enumerate(bundles):
            topic_title = bundle.get("topic", {}).get("title", f"Bundle #{i}")
            log.info(
                f"━━━ Bundle {i+1}/{len(bundles)}: '{topic_title}' ━━━",
                extra={"run_id": run_id},
            )

            # ── Planning ──────────────────────────────────────────────
            try:
                planning_result: PhaseResult = await self._planning.run({
                    "run_id":          run_id,
                    "research_bundle": bundle,
                })
                total_cost += planning_result.cost_usd

                if planning_result.succeeded:
                    planning_results.append({
                        "topic_title": topic_title,
                        "content_plan": planning_result.output,
                        "cost_usd": planning_result.cost_usd,
                    })
                else:
                    all_errors.append({
                        "phase": "planning",
                        "topic_title": topic_title,
                        "error": f"Planning failed: {planning_result.errors}",
                    })
                    continue  # Skip generation for this bundle

            except Exception as exc:
                all_errors.append({
                    "phase": "planning",
                    "topic_title": topic_title,
                    "error": str(exc),
                })
                continue

            # ── Generation ────────────────────────────────────────────
            try:
                gen_result: PhaseResult = await self._generation.run({
                    "run_id":          run_id,
                    "research_bundle": bundle,
                    "content_plan":    planning_result.output,
                })
                total_cost += gen_result.cost_usd

                if gen_result.succeeded:
                    generation_results.append({
                        "topic_title": topic_title,
                        "generation_result": gen_result.output,
                        "wp_post_id": (gen_result.output or {}).get("wp_post_id"),
                        "cost_usd": gen_result.cost_usd,
                    })
                else:
                    all_errors.append({
                        "phase": "generation",
                        "topic_title": topic_title,
                        "error": f"Generation failed: {gen_result.errors}",
                    })

            except Exception as exc:
                all_errors.append({
                    "phase": "generation",
                    "topic_title": topic_title,
                    "error": str(exc),
                })

        log.info(
            f"Bundle processing complete: "
            f"{len(planning_results)} planned, {len(generation_results)} generated",
            extra={"run_id": run_id},
        )

        return {
            "run_id":             run_id,
            "planning_results":   planning_results,
            "generation_results": generation_results,
            "total_cost_usd":     total_cost,
            "errors":             all_errors,
            "phase_statuses":     {
                **state.get("phase_statuses", {}),
                "planning":   "complete",
                "generation": "complete",
            },
            "status": "complete",
        }

    # ── Shared failure handler ────────────────────────────────────────

    @staticmethod
    def _phase_failure(state: PipelineState, phase: str, result: PhaseResult) -> dict:
        log.error(f"Phase '{phase}' failed | status={result.status}")
        return {
            "run_id":          state["run_id"],
            "phase_statuses":  {**state.get("phase_statuses", {}), phase: result.status},
            "total_cost_usd":  state.get("total_cost_usd", 0.0) + result.cost_usd,
            "errors":          state.get("errors", []) + result.errors,
            "status":          "failed",
        }