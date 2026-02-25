"""
PMW Content Production Pipeline — LangGraph
Research → Validate → Write → Fact Check → Edit → SEO → Publish → Distribute
"""
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END


class ContentState(TypedDict):
    topic: str
    research: dict
    draft: str
    fact_check: dict
    edited: str
    seo: dict


def metals_analyst_node(state: ContentState) -> ContentState:
    # Placeholder
    return {**state, "research": {}}


def research_director_node(state: ContentState) -> ContentState:
    # Placeholder
    return state


def market_writer_node(state: ContentState) -> ContentState:
    # Placeholder
    return {**state, "draft": ""}


def fact_checker_node(state: ContentState) -> ContentState:
    # Placeholder
    return {**state, "fact_check": {}}


def editor_in_chief_node(state: ContentState) -> ContentState:
    # Placeholder
    return {**state, "edited": state.get("draft", "")}


def seo_strategist_node(state: ContentState) -> ContentState:
    # Placeholder
    return {**state, "seo": {}}


def publisher_node(state: ContentState) -> ContentState:
    # Placeholder: WordPress REST API
    return state


def distribution_node(state: ContentState) -> ContentState:
    # Placeholder: Newsletter, Social
    return state


def human_review_checkpoint(state: ContentState) -> ContentState:
    # Placeholder: human-in-the-loop
    return state


def check_approval_required(state: ContentState) -> Literal["human", "auto"]:
    return "auto"


def build_content_pipeline(checkpointer=None):
    g = StateGraph(ContentState)

    g.add_node("research", metals_analyst_node)
    g.add_node("validate", research_director_node)
    g.add_node("write", market_writer_node)
    g.add_node("fact_check", fact_checker_node)
    g.add_node("edit", editor_in_chief_node)
    g.add_node("seo", seo_strategist_node)
    g.add_node("publish", publisher_node)
    g.add_node("distribute", distribution_node)
    g.add_node("human_review", human_review_checkpoint)

    g.set_entry_point("research")
    g.add_edge("research", "validate")
    g.add_edge("validate", "write")
    g.add_edge("write", "fact_check")
    g.add_edge("fact_check", "edit")
    g.add_edge("edit", "seo")
    g.add_conditional_edges("seo", check_approval_required, {
        "human": "human_review",
        "auto": "publish",
    })
    g.add_edge("human_review", "publish")
    g.add_edge("publish", "distribute")
    g.add_edge("distribute", END)

    return g.compile(checkpointer=checkpointer, interrupt_before=["human_review"])
