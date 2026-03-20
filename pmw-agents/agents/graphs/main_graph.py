# graphs/main_graph.py
"""
Top-level orchestrator — multi-topic.

3 LangGraph nodes with checkpointing:
  1. research         → list of research_bundles
  2. process_bundles  → planning + generation per bundle
  3. END

Checkpointing between nodes means: if the process crashes after
research completes, it resumes at process_bundles with the full
list of bundles intact. That's the real value of LangGraph here.
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
    _state_schema = PipelineState

    def __init__(self, checkpointer: AsyncPostgresSaver):
        super().__init__(checkpointer)
        self._research:   ResearchGraph   | None = None
        self._planning:   PlanningGraph   | None = None
        self._generation: GenerationGraph | None = None

    @classmethod
    async def create_with_checkpointer(cls, checkpointer: AsyncPostgresSaver) -> "MainGraph":
        instance = cls(checkpointer)
        instance._research   = await ResearchGraph.create_with_checkpointer(checkpointer)
        instance._planning   = await PlanningGraph.create_with_checkpointer(checkpointer)
        instance._generation = await GenerationGraph.create_with_checkpointer(checkpointer)

        instance._build_nodes()
        instance._build_edges()
        instance._compiled = instance._builder.compile(checkpointer=checkpointer)
        log.info("MainGraph compiled")
        return instance

    @classmethod
    async def create(cls) -> "MainGraph":
        import os
        from psycopg_pool import AsyncConnectionPool
        from psycopg.rows import dict_row

        db_url = os.environ.get("DATABASE_URL", "")
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        pool = AsyncConnectionPool(
            conninfo=db_url, max_size=20,
            kwargs={"autocommit": True, "row_factory": dict_row}, open=False,
        )
        await pool.open()
        checkpointer = AsyncPostgresSaver(pool)
        result = checkpointer.setup()
        if result is not None and hasattr(result, "__aenter__"):
            async with result:
                pass
        elif asyncio.iscoroutine(result):
            await result
        return await cls.create_with_checkpointer(checkpointer)

    # ── Graph structure ───────────────────────────────────────────────

    def _build_nodes(self):
        self.add_node("research",        self._research_node)
        self.add_node("process_bundles", self._process_bundles_node)

    def _build_edges(self):
        self.add_edge(self.START, "research")
        self.add_conditional_edges("research", self._route_after_research,
            {"process": "process_bundles", "empty": self.END, "failed": self.END})
        self.add_edge("process_bundles", self.END)

    # ── Input / output ────────────────────────────────────────────────

    def _make_input(self, input_data: dict) -> dict:
        return {
            "run_id":              input_data["run_id"],
            "triggered_by":        input_data.get("triggered_by", "scheduler"),
            "research_bundles":    [],
            "planning_results":    [],
            "generation_results":  [],
            "phase_statuses":      {},
            "total_cost_usd":      0.0,
            "errors":              [],
            "status":              "running",
        }

    def _make_result(self, final_state: dict) -> PhaseResult:
        bundles = final_state.get("research_bundles") or []
        planned = final_state.get("planning_results") or []
        generated = final_state.get("generation_results") or []

        return PhaseResult(
            run_id   = final_state.get("run_id"),
            status   = final_state.get("status", "failed"),
            output   = {
                "research_bundles":   bundles,
                "planning_results":   planned,
                "generation_results": generated,
                "topics_processed":   len(bundles),
            },
            cost_usd = final_state.get("total_cost_usd", 0.0),
            errors   = final_state.get("errors", []),
            meta     = {
                "topics_researched": len(bundles),
                "topics_planned":    len(planned),
                "topics_generated":  len(generated),
            },
        )

    # ── Routing ───────────────────────────────────────────────────────

    @staticmethod
    def _route_after_research(state: dict) -> str:
        if state.get("status") == "failed":
            return "failed"
        return "process" if state.get("research_bundles") else "empty"

    # ── Phase nodes ───────────────────────────────────────────────────

    async def _research_node(self, state: PipelineState) -> dict:
        result = await self._research.run({
            "run_id":       state["run_id"],
            "triggered_by": state.get("triggered_by", "scheduler"),
        })

        bundles = result.output if result.succeeded and isinstance(result.output, list) else []

        return {
            "run_id":           state["run_id"],
            "research_bundles": bundles,
            "phase_statuses":   {**state.get("phase_statuses", {}),
                                 "research": "complete" if bundles else result.status},
            "total_cost_usd":   state.get("total_cost_usd", 0.0) + result.cost_usd,
            "errors":           state.get("errors", []) + result.errors,
            "status":           "running" if bundles else ("complete" if not result.errors else "failed"),
        }

    async def _process_bundles_node(self, state: PipelineState) -> dict:
        """Run planning → generation for each research bundle."""
        run_id = state["run_id"]
        bundles = state.get("research_bundles") or []
        planned = []
        generated = []
        cost = state.get("total_cost_usd", 0.0)
        errors = list(state.get("errors", []))

        log.info(f"Processing {len(bundles)} bundle(s) through planning → generation")

        for i, bundle in enumerate(bundles):
            title = bundle.get("topic", {}).get("title", f"Bundle #{i}")
            log.info(f"━━━ [{i+1}/{len(bundles)}] '{title}' ━━━")

            # ── Planning ──────────────────────────────────────────
            try:
                p_result = await self._planning.run({
                    "run_id": run_id,
                    "research_bundle": bundle,
                })
                cost += p_result.cost_usd

                if not p_result.succeeded:
                    errors.append({"phase": "planning", "topic_title": title,
                                   "error": str(p_result.errors)})
                    continue

                planned.append({"topic_title": title, "content_plan": p_result.output,
                                "cost_usd": p_result.cost_usd})
            except Exception as exc:
                errors.append({"phase": "planning", "topic_title": title, "error": str(exc)})
                continue

            # ── Generation ────────────────────────────────────────
            try:
                g_result = await self._generation.run({
                    "run_id": run_id,
                    "research_bundle": bundle,
                    "content_plan": p_result.output,
                })
                cost += g_result.cost_usd

                if g_result.succeeded:
                    generated.append({
                        "topic_title": title,
                        "wp_post_id": (g_result.output or {}).get("wp_post_id"),
                        "cost_usd": g_result.cost_usd,
                    })
                else:
                    errors.append({"phase": "generation", "topic_title": title,
                                   "error": str(g_result.errors)})
            except Exception as exc:
                errors.append({"phase": "generation", "topic_title": title, "error": str(exc)})

        log.info(f"Done: {len(planned)} planned, {len(generated)} generated")

        return {
            "run_id":             run_id,
            "planning_results":   planned,
            "generation_results": generated,
            "total_cost_usd":     cost,
            "errors":             errors,
            "phase_statuses":     {**state.get("phase_statuses", {}),
                                   "planning": "complete", "generation": "complete"},
            "status":             "complete",
        }