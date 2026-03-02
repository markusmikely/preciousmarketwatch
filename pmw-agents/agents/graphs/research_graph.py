# graphs/research_graph.py

import logging
from graphs.base_graph import BaseGraph
from graphs.phase_result import PhaseResult
from state.research_state import ResearchState  # internal — never seen by parent

# Stage 1 nodes
from nodes.research.stage1.affiliate_loader import AffiliateLoader
from nodes.research.stage1.affiliate_scorer import AffiliateScorer
from nodes.research.stage1.topic_loader import TopicLoader
from nodes.research.stage1.topic_selector import TopicSelector
from nodes.research.stage1.brief_locker import BriefLocker
# Stage 2 nodes 
from nodes.research.stage2.keyword_research import KeywordResearch
# Stage 3 nodes
from nodes.research.stage3.market_context import MarketContext
# Stage 4 nodes
from nodes.research.stage4.top_factors import TopFactors
# Stage 5 nodes
from nodes.research.stage5.competitor_analysis import CompetitorAnalysis
# Stage 6 nodes
from nodes.research.stage6.data_fetcher import DataFetcher
from nodes.research.stage6.psychology_synthesis import PsychologySynthesis
# Stage 7 nodes
from nodes.research.stage7.tool_loader import ToolLoader
from nodes.research.stage7.tool_mapping import ToolMapping
# Stage 8 nodes
from nodes.research.stage8.arc_coherence import ArcCoherence
from nodes.research.stage8.bundle_assembler import BundleAssembler
# Stage 9 nodes
from nodes.research.stage9.intelligence_aggregation import IntelligenceAggregation 

log = logging.getLogger(__name__)


class ResearchGraph(BaseGraph):
    """
    Phase 1 — Research subgraph.

    Internal state: ResearchState (20+ fields, never seen by MainGraph)
    Public contract: run({"run_id", "triggered_by"}) -> PhaseResult

    _make_input  : run_id + triggered_by in -> full ResearchState out
    _make_result : full ResearchState in -> PhaseResult out (only boundary)
    """

    _state_schema = ResearchState

    @classmethod
    async def create(cls) -> "ResearchGraph":
        """Create ResearchGraph instance with proper connection pool."""
        log.info("Creating ResearchGraph...")
        instance = await super().create()
        log.info("ResearchGraph created successfully")
        return instance

    def _build_nodes(self):
        topic_loader = TopicLoader()
        topic_selector = TopicSelector()
        affiliate_loader = AffiliateLoader()
        affiliate_scorer = AffiliateScorer()
        brief_locker = BriefLocker()
        keyword_research = KeywordResearch()
        market_context = MarketContext()
        competitor_analysis = CompetitorAnalysis()
        data_fetcher = DataFetcher()
        top_factors = TopFactors()
        psychology_synthesis = PsychologySynthesis()
        tool_loader = ToolLoader()
        tool_mapping = ToolMapping()
        arc_coherence = ArcCoherence()
        bundle_assembler = BundleAssembler()
        # Stage 1
        self.add_node("stage1.topic_loader",       topic_loader.run)
        self.add_node("stage1.topic_selector",     topic_selector.run)
        self.add_node("stage1.affiliate_loader",   affiliate_loader.run)
        self.add_node("stage1.affiliate_scorer",   affiliate_scorer.run)
        self.add_node("stage1.brief_locker",       brief_locker.run)

        # Parallel wave 1
        self.add_node("stage2.keyword_research",    keyword_research.run)
        self.add_node("stage3.market_context",      market_context.run)
        self.add_node("stage5.competitor_analysis", competitor_analysis.run)

        # Barriers (named no-ops)
        self.add_node("barrier.stage4", self._noop)
        self.add_node("barrier.stage6", self._noop)
        self.add_node("barrier.stage7", self._noop)
        self.add_node("barrier.stage8", self._noop)

        # Stage 4, 6, 7, 8
        self.add_node("stage4.top_factors",          top_factors.run)
        self.add_node("stage6.data_fetcher",         data_fetcher.run)
        self.add_node("stage6.psychology_synthesis", psychology_synthesis.run)
        self.add_node("stage7.tool_loader",          tool_loader.run)
        self.add_node("stage7.tool_mapping",         tool_mapping.run)
        self.add_node("stage8.arc_coherence",        arc_coherence.run)
        self.add_node("stage8.bundle_assembler",     bundle_assembler.run)

        # Control nodes
        self.add_node("hitl_gate",      self._hitl)
        self.add_node("handle_failure", self._failure)

        # Stage 9 is NOT a graph node — dispatched as asyncio.create_task
        # from within bundle_assembler

    def _build_edges(self):
        # ── Stage 1 — sequential chain ────────────────────────────────
        self.add_edge(self.START,                  "stage1.topic_loader")
        self.add_edge("stage1.topic_loader",       "stage1.topic_selector")
        self.add_edge("stage1.topic_selector",     "stage1.affiliate_loader")
        self.add_edge("stage1.affiliate_loader",   "stage1.affiliate_scorer")
        self.add_edge("stage1.affiliate_scorer",   "stage1.brief_locker")

        # ── After brief lock — conditional fan-out or HITL ────────────
        self.add_conditional_edges(
            "stage1.brief_locker",
            self.route_after_brief_lock,
            {
                "stage2.keyword_research":    "stage2.keyword_research",
                "stage3.market_context":      "stage3.market_context",
                "stage5.competitor_analysis": "stage5.competitor_analysis",
                "hitl":                       "hitl_gate",
                "failed":                     "handle_failure",
            }
        )

        # ── Stage 4 barrier — waits for stage2 + stage3 ───────────────
        self.add_edge("stage2.keyword_research", "barrier.stage4")
        self.add_edge("stage3.market_context",   "barrier.stage4")
        self.add_edge("barrier.stage4",          "stage4.top_factors")

        # ── Stage 6 barrier — waits for stage4 + stage5 ───────────────
        self.add_edge("stage4.top_factors",           "barrier.stage6")
        self.add_edge("stage5.competitor_analysis",   "barrier.stage6")
        self.add_edge("barrier.stage6",               "stage6.data_fetcher")
        self.add_edge("stage6.data_fetcher",          "stage6.psychology_synthesis")

        # ── Stage 7 barrier — waits for stage2 + stage4 + stage6b ────
        self.add_edge("stage2.keyword_research",     "barrier.stage7")
        self.add_edge("stage4.top_factors",          "barrier.stage7")
        self.add_edge("stage6.psychology_synthesis", "barrier.stage7")
        self.add_edge("barrier.stage7",              "stage7.tool_loader")
        self.add_edge("stage7.tool_loader",          "stage7.tool_mapping")

        # ── Stage 8 barrier — waits for stage5 + stage7 ──────────────
        # (stage2, 3, 4, 6 are already upstream of stage7)
        self.add_edge("stage5.competitor_analysis", "barrier.stage8")
        self.add_edge("stage7.tool_mapping",        "barrier.stage8")
        self.add_edge("barrier.stage8",             "stage8.arc_coherence")

        # ── Arc coherence — conditional: pass or HITL ─────────────────
        self.add_conditional_edges(
            "stage8.arc_coherence",
            self.route_after_arc,
            {
                "continue": "stage8.bundle_assembler",
                "hitl":     "hitl_gate",
                "failed":   "handle_failure",
            }
        )

        # ── END — pipeline completes at bundle assembler ───────────────
        # Stage 9 dispatched as background task from within bundle_assembler
        self.add_edge("stage8.bundle_assembler", self.END)

        # ── Terminal nodes ─────────────────────────────────────────────
        self.add_edge("hitl_gate",      self.END)
        self.add_edge("handle_failure", self.END)


    def _make_input(self, input_data: dict) -> dict:
        """
        The parent passes run_id and triggered_by.
        run_id = workflow_runs.id, same value throughout the pipeline.
        """
        return {
            "run_id":              input_data["run_id"],
            "triggered_by":        input_data.get("triggered_by", "scheduler"),
            "candidate_topics":    None,
            "selected_topic":      None,
            "topic_lock_acquired": None,
            "brief":               None,
            "keyword_research":    None,
            "market_context":      None,
            "competitor_analysis": None,
            "top_factors":         None,
            "buyer_psychology":    None,
            "tool_mapping":        None,
            "arc_validation":      None,
            "research_bundle":     None,
            "current_stage":       "start",
            "status":              "running",
            "errors":              [],
            "retry_counts":        {},
            "model_usage":         [],
        }

    def _make_result(self, final_state: dict) -> PhaseResult:
        """
        Only research_bundle and a small meta dict escape this method.
        All 20+ ResearchState fields are discarded here.
        """
        selected_topic = final_state.get("selected_topic") or {}
        return PhaseResult(
            run_id   = final_state.get("run_id", 0),
            status   = final_state.get("status", "failed"),
            output   = final_state.get("research_bundle"),
            cost_usd = self._sum_cost(final_state.get("model_usage", [])),
            errors   = final_state.get("errors", []),
            meta     = {
                "topic_wp_id": selected_topic.get("id"),
                "topic_title": selected_topic.get("title"),
            },
        )

    def route_after_brief_lock(self, state: ResearchState) -> [str]:
        if state.get("hitl_required"):
            return "hitl"
        if state.get("status") == "failed":
            return "failed"
        # Fan-out — return list to trigger parallel execution
        return ["stage2.keyword_research", "stage3.market_context", "stage5.competitor_analysis"]
    
    def route_after_arc(self, state: ResearchState) -> str:
        """
        Conditional edge function called after stage8.arc_coherence completes.

        LangGraph calls this with the current state and uses the returned
        string to select the next node from the path_map in add_conditional_edges.

        Three possible outcomes:
            "continue"  → arc is coherent, proceed to bundle assembly
            "hitl"      → arc is incoherent but recoverable, suspend for human review
            "failed"    → arc confidence too low to recover, hard failure

        Reads from:
            state["arc_validation"]  — written by arc_coherence node
            state["status"]          — written by arc_coherence node on hard failure

        Arc validation schema (what arc_coherence writes):
            {
                "arc_coherent":    bool,
                "arc_confidence":  float,   # 0.0 → 1.0
                "issues":          list[dict],
                "recommendations": list[str],
            }
        """
        # Hard failure — arc_coherence node itself errored before producing output
        # This means something went wrong in the LLM call or the node logic,
        # not just a bad arc. Status "failed" set by the node directly.
        if state.get("status") == "failed":
            return "failed"

        arc = state.get("arc_validation")

        # arc_validation missing entirely — node produced no output
        # Treat as hard failure, not HITL — there's nothing for a human to review
        if not arc:
            return "failed"

        arc_coherent   = arc.get("arc_coherent", False)
        arc_confidence = arc.get("arc_confidence", 0.0)

        # Happy path — arc is coherent, proceed
        if arc_coherent:
            return "continue"

        # Arc incoherent — decide between HITL and hard failure based on confidence.
        #
        # High confidence incoherence (0.3 → 1.0):
        #   The model is sure the arc doesn't work — but a human may be able to
        #   resolve it (e.g. conflicting intent signals, wrong affiliate pairing).
        #   Route to HITL so a human can inspect the issues and recommendations
        #   written to arc_validation by the arc_coherence node.
        #
        # Low confidence incoherence (0.0 → 0.3):
        #   The model is uncertain — the arc might be fine but the check itself
        #   is unreliable. Hard failure is safer than suspending for human review
        #   on a result we can't trust. The run will be retried on the next tick.
        if arc_confidence >= 0.3:
            return "hitl"

        return "failed"