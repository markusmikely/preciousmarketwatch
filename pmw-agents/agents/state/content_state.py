from typing import TypedDict, Optional

class ContentPlanningState(TypedDict):
    """
    Phase 2 internal state. Fields TBD when Content Planning is designed.
    Stub exists so imports don't break and the interface is declared.
    """
    run_id:          int
    research_bundle: Optional[dict]   # received from Phase 1
    content_plan:    Optional[dict]   # produced by Phase 2
    status:          str
    errors:          list[dict]
    model_usage:     list[dict]