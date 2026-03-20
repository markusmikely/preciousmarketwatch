"""
Pipeline state — the top-level orchestrator state.

Plain TypedDict. LangGraph uses this for checkpointing at phase
boundaries (research → planning → generation). No MessagesState
inheritance — we don't use LangGraph's message accumulation.
"""
from typing import TypedDict, Optional


class PipelineState(TypedDict):
    # ── Identity ─────────────────────────────────────────────────
    run_id:        int
    triggered_by:  str

    # ── Phase outputs (multi-topic) ──────────────────────────────
    research_bundles:   list[dict]    # List of completed research bundles
    planning_results:   list[dict]    # List of completed content plans
    generation_results: list[dict]    # List of published articles

    # ── Aggregate tracking ───────────────────────────────────────
    phase_statuses:  dict             # {research: "complete", planning: "complete", ...}
    total_cost_usd:  float
    errors:          list[dict]       # [{phase, topic_title, error}]
    status:          str              # "running" | "complete" | "failed"