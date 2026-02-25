"""
PMW Performance Intelligence — LangGraph agent
Analyses GA4, Clarity, Search Console. Flags underperforming pages, UX issues.
"""
from typing import TypedDict, List


class PerfState(TypedDict):
    ga4_data: dict
    clarity_data: dict
    gsc_data: dict
    performance_summary: dict


async def analyse_performance(state: PerfState) -> dict:
    """Placeholder: fetch GA4, Clarity, GSC; identify issues."""
    ga4 = state.get("ga4_data", {})
    clarity = state.get("clarity_data", {})

    underperforming = [
        p for p in ga4.get("pages", [])
        if p.get("bounce_rate", 0) > 0.65 or p.get("avg_session", 0) < 60
    ]
    no_affiliate_clicks = [
        p for p in ga4.get("pages", [])
        if p.get("affiliate_clicks", 0) == 0 and p.get("sessions", 0) > 200
    ]

    return {
        "performance_summary": {
            "week_sessions": ga4.get("totals", {}).get("sessions", 0),
            "underperforming": underperforming,
            "no_affiliate": no_affiliate_clicks,
        }
    }
