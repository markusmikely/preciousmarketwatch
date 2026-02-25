"""
PMW Trend Analyst — LangGraph intelligence agent
Fetches trends from Google Trends, Reddit, financial news, Twitter.
"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, END


class TrendState(TypedDict):
    raw_signals: List[dict]
    scored_topics: List[dict]
    brief: dict


async def fetch_all_trend_signals(state: TrendState) -> TrendState:
    """Placeholder: fetch from Google Trends, Reddit, news APIs."""
    return {**state, "raw_signals": []}


def score_and_rank_topics(state: TrendState) -> TrendState:
    """Placeholder: score by search velocity, social engagement."""
    return {**state, "scored_topics": []}


def generate_trend_brief(state: TrendState) -> TrendState:
    """Placeholder: LLM call to generate brief."""
    return {**state, "brief": {}}


def publish_to_wordpress(state: TrendState) -> TrendState:
    """Placeholder: write to pmw_intelligence_briefs WP option via REST."""
    return state


def build_trend_analyst(checkpointer=None):
    g = StateGraph(TrendState)

    g.add_node("fetch_trends", fetch_all_trend_signals)
    g.add_node("score_topics", score_and_rank_topics)
    g.add_node("generate_brief", generate_trend_brief)
    g.add_node("publish_brief", publish_to_wordpress)

    g.set_entry_point("fetch_trends")
    g.add_edge("fetch_trends", "score_topics")
    g.add_edge("score_topics", "generate_brief")
    g.add_edge("generate_brief", "publish_brief")
    g.add_edge("publish_brief", END)

    return g.compile(checkpointer=checkpointer)
