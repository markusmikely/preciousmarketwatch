"""
PMW Director — LangGraph orchestration graph
Ingests intelligence briefs, builds editorial calendar, assigns tasks.
"""
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, END


class DirectorState(TypedDict):
    intelligence_briefs: List[dict]
    editorial_calendar: List[dict]
    active_tasks: List[dict]
    human_commands: List[dict]
    errors: List[dict]


def ingest_intelligence_briefs(state: DirectorState) -> DirectorState:
    # Placeholder: read from Redis/WP options
    return {**state, "intelligence_briefs": state.get("intelligence_briefs", [])}


def build_editorial_calendar(state: DirectorState) -> DirectorState:
    # Placeholder: prioritise topics from briefs
    return {**state, "editorial_calendar": state.get("editorial_calendar", [])}


def assign_tasks_to_agents(state: DirectorState) -> DirectorState:
    # Placeholder: create tasks from calendar
    return {**state, "active_tasks": state.get("active_tasks", [])}


def monitor_pipeline_state(state: DirectorState) -> DirectorState:
    # Placeholder: check task status
    return state


def handle_pipeline_errors(state: DirectorState) -> DirectorState:
    # Placeholder: handle errors
    return state


def wait_for_human_input(state: DirectorState) -> DirectorState:
    # Placeholder: human-in-the-loop checkpoint
    return state


def route_by_approval_mode(state: DirectorState) -> Literal["auto", "human"]:
    # Check pmw_approval_mode from WP
    return "auto"


def check_complete(state: DirectorState) -> Literal["continue", "done"]:
    return "done"


def build_director_graph(checkpointer=None):
    g = StateGraph(DirectorState)

    g.add_node("ingest_intelligence", ingest_intelligence_briefs)
    g.add_node("build_calendar", build_editorial_calendar)
    g.add_node("assign_tasks", assign_tasks_to_agents)
    g.add_node("monitor_pipeline", monitor_pipeline_state)
    g.add_node("handle_errors", handle_pipeline_errors)
    g.add_node("human_checkpoint", wait_for_human_input)

    g.set_entry_point("ingest_intelligence")
    g.add_edge("ingest_intelligence", "build_calendar")
    g.add_edge("build_calendar", "assign_tasks")
    g.add_conditional_edges("assign_tasks", route_by_approval_mode, {
        "auto": "monitor_pipeline",
        "human": "human_checkpoint",
    })
    g.add_edge("human_checkpoint", "monitor_pipeline")
    g.add_edge("monitor_pipeline", "handle_errors")
    g.add_conditional_edges("handle_errors", check_complete, {
        "continue": "ingest_intelligence",
        "done": END,
    })

    return g.compile(checkpointer=checkpointer)
