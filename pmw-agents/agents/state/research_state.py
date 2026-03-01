# agents/state/research_state.py
from typing import TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState

class ResearchState(MessagesState):
    """
    State for the research subgraph.
    Every field is Optional because LangGraph initialises state incrementally —
    a node only sees the fields that have been written so far.

    Key design rule: structured outputs (dicts, lists) go here directly.
    Large raw content (scraped HTML, forum text) is stored in Redis;
    only the Redis cache key is stored in state.
    """

    # ── Run identity ─────────────────────────────────────────────────
    run_id:       int     # workflow_runs.id — single identifier for this pipeline run
    triggered_by: str     # "scheduler" | "manual" | "api"

    # ── Stage 1 ──────────────────────────────────────────────────────
    candidate_topics:     Optional[list[dict]]
    selected_topic:       Optional[dict]
    topic_lock_acquired:  Optional[bool]
    candidate_affiliates: Optional[list[dict]]
    scored_affiliates:    Optional[list[dict]]
    primary_affiliate:    Optional[dict]
    secondary_affiliate:  Optional[dict]
    brief:                Optional[dict]

    # ── Parallel wave 1 outputs ───────────────────────────────────────
    keyword_research:    Optional[dict]   # Stage 2
    market_context:      Optional[dict]   # Stage 3
    competitor_analysis: Optional[dict]   # Stage 5

    # ── Stage 4 ──────────────────────────────────────────────────────
    top_factors: Optional[dict]

    # ── Stage 6 ──────────────────────────────────────────────────────
    # Note: raw_sources_cache_key is a Redis key, not the raw content itself
    raw_sources_cache_key: Optional[str]    # e.g. "pmw:sources:run_42"
    buyer_psychology:      Optional[dict]   # synthesised output only

    # ── Stage 7 ──────────────────────────────────────────────────────
    tool_mapping: Optional[dict]

    # ── Stage 8 ──────────────────────────────────────────────────────
    arc_validation:  Optional[dict]
    research_bundle: Optional[dict]    # final output → parent graph

    # ── Pipeline control ─────────────────────────────────────────────
    current_stage: str
    status:        str      # "running" | "complete" | "failed" | "hitl"
    errors:        list[dict]
    retry_counts:  dict[str, int]
    model_usage:   list[dict]    # [{stage, model, input_tokens, output_tokens, cost_usd}]
    hitl_required: Optional[bool]
    hitl_stage:    Optional[str]
    hitl_reason:   Optional[str] 