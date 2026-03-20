"""
Research phase state — plain TypedDict for LangGraph checkpointing.

Stage 1 populates all_topics + all_affiliates + locked_briefs.
The research pipeline node then processes each brief through stages 2-8
using plain async Python (not LangGraph nodes), accumulating results
into completed_bundles.
"""
from typing import TypedDict, Optional


class ResearchState(TypedDict):
    # ── Run identity ─────────────────────────────────────────────
    run_id:       int
    triggered_by: str

    # ── Stage 1 outputs ──────────────────────────────────────────
    all_topics:     Optional[list[dict]]
    all_affiliates: Optional[list[dict]]
    locked_briefs:  Optional[list[dict]]   # Briefs that passed → stages 2-8
    review_items:   Optional[list[dict]]   # Topics → saved to DB for HITL

    # ── Stage 2-8 aggregate output ───────────────────────────────
    completed_bundles: list[dict]           # Final research bundles

    # ── Pipeline control ─────────────────────────────────────────
    current_stage: str
    status:        str           # "running" | "complete" | "failed"
    errors:        list[dict]
    model_usage:   list[dict]    # [{stage, model, tokens, cost}]