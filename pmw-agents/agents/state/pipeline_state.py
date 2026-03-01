# agents/state/types.py
from typing import TypedDict, Optional, List
from langchain_core.messages import MessageState

class PipelineState(MessageState):
    # Identity
    run_id:           int
    topic_id:         int
    topic:            dict

    # Reader intent (set by Research, used by Planning + Content)
    reader_intent:    Optional[str]    # price_checker | consideration_buyer | curiosity_reader

    # Model data
    model_data:       dict
    # Stage outputs
    task_data:        Optional[dict]
    research_output:  Optional[dict]
    planning_output:  Optional[dict]
    content_output:   Optional[dict]
    media_output:     Optional[dict]   # NEW

    # Scoring state
    current_stage:    str    # {phase: "complete"|"failed"|"hitl"|"skipped"}
    current_score:    Optional[float]
    attempt_number:   int
    judge_feedback:   Optional[dict]
    score_history:    List[dict]

    # Control
    status:           str # "running" | "complete" | "failed" | "hitl" | "partial"
    errors:         list[dict]  # [{phase, stage, error, ts}] — accumulated 
    threshold_overrides: Optional[dict]

    # Metadata
    started_at:       str
    
    wp_post_id: Optional[int]   # set when article is published (Phase 3)  # cost tracking