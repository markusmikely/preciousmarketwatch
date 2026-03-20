# agents/state/research_state.py
"""
Research phase state — supports multi-topic processing.

A single pipeline run now processes ALL eligible topics:
  - Stage 1 loads all topics + all affiliates, scores each pair,
    and produces a list of locked briefs (passing) and a list of
    review items (failing).
  - Stages 2-8 run once per passing brief, accumulating results
    into the briefs_in_progress list.
  - The final output is a list of completed research_bundles.

The parent graph (MainGraph) receives this list and fans each bundle
into independent planning→content→publish pipelines, all sharing
the same run_id.
"""

from typing import TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState


class ResearchState(MessagesState):
    """
    State for the research subgraph.

    Key change from v1: research now processes ALL topics in a single
    run. The output is a list of research_bundles, not a single one.

    Fields marked [MULTI] are new for multi-topic support.
    Fields marked [REMOVED] were replaced by the multi-topic fields.
    """

    # ── Run identity ─────────────────────────────────────────────
    run_id:       int     # workflow_runs.id — single identifier for this pipeline run
    triggered_by: str     # "scheduler" | "manual" | "api"

    # ── Stage 1: All topics + All affiliates [MULTI] ─────────────
    all_topics:           Optional[list[dict]]     # All eligible topics from WP
    all_affiliates:       Optional[list[dict]]     # All active affiliates from Postgres

    # ── Stage 1: Brief assembly results [MULTI] ──────────────────
    # Each item is a dict with: topic, primary_affiliate, secondary_affiliate,
    # brief, coherence_score, status ('passed'|'needs_review'|'failed')
    locked_briefs:        Optional[list[dict]]     # Briefs that passed → proceed to stages 2-8
    review_items:         Optional[list[dict]]     # Topics needing HITL → saved to topic_briefs table

    # ── Current brief being processed (set by the per-brief loop) ─
    current_brief_index:  Optional[int]            # Index into locked_briefs being processed
    current_brief:        Optional[dict]           # The brief currently being researched

    # ── Per-brief stage outputs (accumulated during stages 2-8) ───
    # These are reset for each brief in the loop
    keyword_research:     Optional[dict]   # Stage 2
    market_context:       Optional[dict]   # Stage 3
    competitor_analysis:  Optional[dict]   # Stage 5
    top_factors:          Optional[dict]   # Stage 4
    raw_sources_cache_key: Optional[str]   # Stage 6a Redis key
    buyer_psychology:     Optional[dict]   # Stage 6b
    tool_mapping:         Optional[dict]   # Stage 7
    arc_validation:       Optional[dict]   # Stage 8a

    # ── Completed research bundles [MULTI] ────────────────────────
    # Each completed brief's research_bundle is appended here after
    # stages 2-8 finish successfully for that brief.
    completed_bundles:    Optional[list[dict]]

    # ── Pipeline control ─────────────────────────────────────────
    current_stage:  str
    status:         str        # "running" | "complete" | "failed" | "hitl"
    errors:         list[dict]
    retry_counts:   dict[str, int]
    model_usage:    list[dict] # [{stage, model, input_tokens, output_tokens, cost_usd}]
    hitl_required:  Optional[bool]
    hitl_stage:     Optional[str]
    hitl_reason:    Optional[str]