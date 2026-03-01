from typing import TypedDict, Optional

class GenerationState(TypedDict):
    """
    Phase 3 internal state. Fields TBD when Generation is designed.
    """
    run_id:            int
    research_bundle:   Optional[dict]   # from Phase 1
    content_plan:      Optional[dict]   # from Phase 2
    generation_result: Optional[dict]   # produced by Phase 3
    status:            str
    errors:            list[dict]
    model_usage:       list[dict]