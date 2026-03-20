# graphs/research_graph.py
"""
Research subgraph — multi-topic architecture.

Stage 1 processes ALL eligible topics in a single pass:
  topic_loader → affiliate_loader → brief_builder

This produces:
  locked_briefs:  list of briefs that passed scoring + coherence
  review_items:   list of topics saved to DB for human review

Then for each locked brief, stages 2-8 run sequentially:
  keyword_research → market_context → competitor_analysis →
  top_factors → data_fetcher → psychology_synthesis →
  tool_loader → tool_mapping → arc_coherence → bundle_assembler

Each completed brief's research_bundle is appended to completed_bundles.
The parent graph receives the full list.

If a brief fails during stages 2-8, it's logged and skipped — other
briefs continue processing. A single bad topic doesn't halt the run.
"""

import logging
from graphs.base_graph import BaseGraph
from graphs.phase_result import PhaseResult
from state.research_state import ResearchState

# Stage 1 nodes
from nodes.research.stage1.topic_loader import TopicLoader
from nodes.research.stage1.affiliate_loader import AffiliateLoader
from nodes.research.stage1.brief_builder import BriefBuilder
# Stages 2-8 nodes
from nodes.research.stage2.keyword_research import KeywordResearch
from nodes.research.stage3.market_context import MarketContext
from nodes.research.stage4.top_factors import TopFactors
from nodes.research.stage5.competitor_analysis import CompetitorAnalysis
from nodes.research.stage6.data_fetcher import DataFetcher
from nodes.research.stage6.psychology_synthesis import PsychologySynthesis
from nodes.research.stage7.tool_loader import ToolLoader
from nodes.research.stage7.tool_mapping import ToolMapping
from nodes.research.stage8.arc_coherence import ArcCoherence
from nodes.research.stage8.bundle_assembler import BundleAssembler

log = logging.getLogger(__name__)


class ResearchGraph(BaseGraph):
    """
    Phase 1 — Research subgraph (multi-topic).

    Internal state: ResearchState
    Public contract: run({"run_id", "triggered_by"}) -> PhaseResult
      where PhaseResult.output = list of research_bundles
    """

    _state_schema = ResearchState

    @classmethod
    async def create(cls) -> "ResearchGraph":
        log.info("Creating ResearchGraph...")
        instance = await super().create()
        log.info("ResearchGraph created successfully")
        return instance

    def _build_nodes(self):
        # Stage 1: load everything + build briefs
        self.add_node("topic_loader",    TopicLoader().run)
        self.add_node("affiliate_loader", AffiliateLoader().run)
        self.add_node("brief_builder",   BriefBuilder().run)

        # Per-brief research stages (2-8)
        self.add_node("process_briefs",  self._process_all_briefs)

        # Terminal nodes
        self.add_node("handle_failure",  self._failure)

    def _build_edges(self):
        # Stage 1: sequential loading
        self.add_edge(self.START, "topic_loader")

        self.add_conditional_edges(
            "topic_loader",
            self._route_on_status,
            {"continue": "affiliate_loader", "failed": "handle_failure"},
        )
        self.add_conditional_edges(
            "affiliate_loader",
            self._route_on_status,
            {"continue": "brief_builder", "failed": "handle_failure"},
        )

        # After brief_builder: process all locked briefs
        self.add_conditional_edges(
            "brief_builder",
            self._route_after_brief_builder,
            {
                "process": "process_briefs",
                "empty":   self.END,     # No briefs passed — valid, run ends
                "failed":  "handle_failure",
            },
        )

        # After processing all briefs → END
        self.add_edge("process_briefs", self.END)
        self.add_edge("handle_failure", self.END)

    # ══════════════════════════════════════════════════════════════════════
    # PER-BRIEF PROCESSING (stages 2-8 loop)
    # ══════════════════════════════════════════════════════════════════════

    async def _process_all_briefs(self, state: dict) -> dict:
        """
        Process each locked brief through stages 2-8.

        This is a single LangGraph node that internally loops over
        locked_briefs. Each brief gets its own stages 2-8 run.
        Failed briefs are logged and skipped — others continue.

        The result is a list of completed_bundles in state.
        """
        run_id = state["run_id"]
        locked_briefs = state.get("locked_briefs") or []
        completed_bundles = []
        all_model_usage = list(state.get("model_usage", []))
        all_errors = list(state.get("errors", []))

        log.info(
            f"Processing {len(locked_briefs)} brief(s) through stages 2-8",
            extra={"run_id": run_id},
        )

        # Instantiate stage nodes once
        keyword_research = KeywordResearch()
        market_context = MarketContext()
        competitor_analysis = CompetitorAnalysis()
        top_factors = TopFactors()
        data_fetcher = DataFetcher()
        psychology_synthesis = PsychologySynthesis()
        tool_loader = ToolLoader()
        tool_mapping = ToolMapping()
        arc_coherence = ArcCoherence()
        bundle_assembler = BundleAssembler()

        for i, brief in enumerate(locked_briefs):
            topic = brief.get("topic", {})
            topic_title = topic.get("title", f"Brief #{i}")
            topic_id = topic.get("id")

            log.info(
                f"━━━ Brief {i+1}/{len(locked_briefs)}: '{topic_title}' ━━━",
                extra={"run_id": run_id, "topic_id": topic_id},
            )

            # Build per-brief state (starts with the brief + empty stage outputs)
            brief_state = {
                "run_id": run_id,
                "triggered_by": state.get("triggered_by", "scheduler"),
                "brief": brief,
                "selected_topic": topic,
                "primary_affiliate": brief.get("affiliate", {}).get("primary"),
                "secondary_affiliate": brief.get("affiliate", {}).get("secondary"),
                "keyword_research": None,
                "market_context": None,
                "competitor_analysis": None,
                "top_factors": None,
                "raw_sources_cache_key": None,
                "buyer_psychology": None,
                "tool_mapping": None,
                "arc_validation": None,
                "research_bundle": None,
                "available_tools": None,
                "current_stage": "stage2",
                "status": "running",
                "errors": [],
                "retry_counts": {},
                "model_usage": [],
            }

            try:
                # ── Stage 2: Keyword Research ─────────────────────────
                brief_state = self._merge(brief_state, await keyword_research.run(brief_state))
                if brief_state.get("status") == "failed":
                    raise _BriefStageError("stage2.keyword_research", brief_state)

                # ── Stage 3: Market Context ───────────────────────────
                brief_state = self._merge(brief_state, await market_context.run(brief_state))
                if brief_state.get("status") == "failed":
                    raise _BriefStageError("stage3.market_context", brief_state)

                # ── Stage 5: Competitor Analysis (parallel with 2+3 in theory,
                #    but sequential here for simplicity — concurrency in Phase 2)
                brief_state = self._merge(brief_state, await competitor_analysis.run(brief_state))
                if brief_state.get("status") == "failed":
                    raise _BriefStageError("stage5.competitor_analysis", brief_state)

                # ── Stage 4: Top Factors (needs 2+3) ──────────────────
                brief_state = self._merge(brief_state, await top_factors.run(brief_state))
                if brief_state.get("status") == "failed":
                    raise _BriefStageError("stage4.top_factors", brief_state)

                # ── Stage 6a: Data Fetcher ────────────────────────────
                brief_state = self._merge(brief_state, await data_fetcher.run(brief_state))
                if brief_state.get("status") == "failed":
                    raise _BriefStageError("stage6.data_fetcher", brief_state)

                # ── Stage 6b: Psychology Synthesis ────────────────────
                brief_state = self._merge(brief_state, await psychology_synthesis.run(brief_state))
                if brief_state.get("status") == "failed":
                    raise _BriefStageError("stage6.psychology_synthesis", brief_state)

                # ── Stage 7a: Tool Loader ─────────────────────────────
                brief_state = self._merge(brief_state, await tool_loader.run(brief_state))
                # Tool loader failure is non-fatal — proceed with empty tools

                # ── Stage 7b: Tool Mapping ────────────────────────────
                brief_state = self._merge(brief_state, await tool_mapping.run(brief_state))
                # Tool mapping failure is non-fatal

                # ── Stage 8a: Arc Coherence ───────────────────────────
                brief_state = self._merge(brief_state, await arc_coherence.run(brief_state))
                arc = brief_state.get("arc_validation") or {}
                if not arc.get("arc_coherent", False):
                    log.warning(
                        f"Brief '{topic_title}' failed arc coherence — skipping",
                        extra={"run_id": run_id, "arc": arc},
                    )
                    all_errors.append({
                        "stage": "stage8.arc_coherence",
                        "topic_id": topic_id,
                        "topic_title": topic_title,
                        "error": f"Arc coherence failed: {arc.get('arc_summary', 'unknown')}",
                    })
                    continue

                # ── Stage 8b: Bundle Assembler ────────────────────────
                brief_state = self._merge(brief_state, await bundle_assembler.run(brief_state))
                bundle = brief_state.get("research_bundle")

                if bundle:
                    completed_bundles.append(bundle)
                    all_model_usage.extend(brief_state.get("model_usage", []))
                    log.info(
                        f"Brief '{topic_title}' → research_bundle COMPLETE",
                        extra={"run_id": run_id},
                    )
                else:
                    all_errors.append({
                        "stage": "stage8.bundle_assembler",
                        "topic_id": topic_id,
                        "topic_title": topic_title,
                        "error": "Bundle assembler produced no output",
                    })

            except _BriefStageError as bse:
                log.warning(
                    f"Brief '{topic_title}' failed at {bse.stage} — skipping",
                    extra={"run_id": run_id},
                )
                all_errors.append({
                    "stage": bse.stage,
                    "topic_id": topic_id,
                    "topic_title": topic_title,
                    "error": str(bse),
                })
                # Release the topic lock so it can be retried next cycle
                try:
                    from services import services
                    await services.workflows.release_topic_lock(
                        topic_wp_id=topic_id, run_id=run_id, success=False,
                    )
                except Exception:
                    pass
                continue

            except Exception as exc:
                log.error(
                    f"Unexpected error processing brief '{topic_title}': {exc}",
                    extra={"run_id": run_id},
                    exc_info=True,
                )
                all_errors.append({
                    "stage": "process_briefs",
                    "topic_id": topic_id,
                    "topic_title": topic_title,
                    "error": str(exc),
                })
                continue

        log.info(
            f"Brief processing complete: {len(completed_bundles)}/{len(locked_briefs)} succeeded",
            extra={"run_id": run_id},
        )

        return {
            "completed_bundles": completed_bundles,
            "current_stage": "process_briefs",
            "status": "complete",
            "model_usage": all_model_usage,
            "errors": all_errors,
        }

    # ══════════════════════════════════════════════════════════════════════
    # ROUTING
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _route_on_status(state: dict) -> str:
        if state.get("status") == "failed":
            return "failed"
        return "continue"

    @staticmethod
    def _route_after_brief_builder(state: dict) -> str:
        """
        After brief_builder:
          - "process" if there are locked briefs to research
          - "empty" if zero briefs passed (valid — run ends cleanly)
          - "failed" if brief_builder itself failed
        """
        if state.get("status") == "failed":
            return "failed"

        locked = state.get("locked_briefs") or []
        if len(locked) == 0:
            return "empty"

        return "process"

    # ══════════════════════════════════════════════════════════════════════
    # TERMINALS
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def _failure(state: dict) -> dict:
        log.error("Research pipeline failed", extra={
            "run_id": state.get("run_id"),
            "errors": state.get("errors", []),
        })
        return {"status": "failed"}

    # ══════════════════════════════════════════════════════════════════════
    # INPUT / OUTPUT TRANSLATION
    # ══════════════════════════════════════════════════════════════════════

    def _make_input(self, input_data: dict) -> dict:
        return {
            "run_id":              input_data["run_id"],
            "triggered_by":        input_data.get("triggered_by", "scheduler"),
            "all_topics":          None,
            "all_affiliates":      None,
            "locked_briefs":       None,
            "review_items":        None,
            "current_brief_index": None,
            "current_brief":       None,
            "keyword_research":    None,
            "market_context":      None,
            "competitor_analysis": None,
            "top_factors":         None,
            "raw_sources_cache_key": None,
            "buyer_psychology":    None,
            "tool_mapping":        None,
            "arc_validation":      None,
            "completed_bundles":   [],
            "current_stage":       "start",
            "status":              "running",
            "errors":              [],
            "retry_counts":        {},
            "model_usage":         [],
        }

    def _make_result(self, final_state: dict) -> PhaseResult:
        """
        Returns PhaseResult where output = list of research_bundles.

        The parent graph (MainGraph) iterates this list and creates
        independent planning pipelines for each bundle.
        """
        completed = final_state.get("completed_bundles") or []
        review = final_state.get("review_items") or []

        return PhaseResult(
            run_id   = final_state.get("run_id", 0),
            status   = final_state.get("status", "failed"),
            output   = completed if completed else None,
            cost_usd = self._sum_cost(final_state.get("model_usage", [])),
            errors   = final_state.get("errors", []),
            meta     = {
                "bundles_completed": len(completed),
                "topics_for_review": len(review),
                "topic_titles": [
                    b.get("topic", {}).get("title", "")
                    for b in completed
                ],
            },
        )

    # ══════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _merge(base: dict, updates: dict) -> dict:
        """
        Merge node output into the per-brief state dict.
        Only overwrites keys that are present in updates.
        This mimics LangGraph's state merging but for the inner loop.
        """
        merged = {**base}
        for key, value in updates.items():
            if value is not None or key in ("status", "errors"):
                merged[key] = value
        return merged


class _BriefStageError(Exception):
    """Raised when a stage fails for a specific brief."""
    def __init__(self, stage: str, state: dict):
        self.stage = stage
        errors = state.get("errors", [])
        last_error = errors[-1]["error"] if errors else "Unknown error"
        super().__init__(f"Stage {stage} failed: {last_error}")