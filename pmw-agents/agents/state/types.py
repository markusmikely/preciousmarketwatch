# agents/state/types.py
from typing import TypedDict, Optional, List

class PipelineState(TypedDict):
    # Identity
    run_id:           int
    topic_id:         int
    topic:            dict

    # Stage outputs
    task_data:        Optional[dict]
    research_output:  Optional[dict]
    planning_output:  Optional[dict]
    content_output:   Optional[dict]
    media_output:     Optional[dict]   # NEW

    # Reader intent (set by Research, used by Planning + Content)
    reader_intent:    Optional[str]    # price_checker | consideration_buyer | curiosity_reader

    # Scoring state
    current_stage:    str
    current_score:    Optional[float]
    attempt_number:   int
    judge_feedback:   Optional[dict]
    score_history:    List[dict]

    # Control
    status:           str
    error:            Optional[str]
    threshold_overrides: Optional[dict]

    # Metadata
    started_at:       str
    model_usage:      List[dict]       # cost tracking