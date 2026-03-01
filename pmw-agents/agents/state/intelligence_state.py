from typing import TypedDict, Optional

class IntelligenceState(TypedDict):
    """
    Phase 4 state. Separate from workflow — runs on its own schedule.
    Fields TBD when Intelligence phase is designed.
    """
    intelligence_run_id: str
    triggered_at:        str
    topics_created:      int
    topics_updated:      int
    performance_updated: int
    status:              str