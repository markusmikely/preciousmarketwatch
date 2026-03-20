"""
Research Pipeline — plain async orchestrator for stages 2-8.

This replaces the LangGraph inner loop with direct async Python.
Each brief gets its own stages 2-8 run. Multiple briefs run
concurrently up to BRIEF_CONCURRENCY limit.

Benefits over the old LangGraph loop:
  - asyncio.gather with semaphore = true concurrency (not sequential)
  - No checkpointing overhead per-brief (crash = skip that brief)
  - Direct function calls = no state serialisation per stage
  - Failed brief = logged and skipped, others continue

Usage (called from research_graph._process_briefs node):
    from nodes.research.pipeline import research_briefs
    results = await research_briefs(locked_briefs, run_id, triggered_by)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from config.settings import settings

# Stage nodes
from nodes.research.stage2.keyword_research import KeywordResearch
from nodes.research.stage3.market_context import MarketContext
from nodes.research.stage4.top_factors import TopFactors
from nodes.research.stage5.competitor_analysis import CompetitorAnalysis
from nodes.research.stage6.data_fetcher import DataFetcher
from nodes.research.stage6.psychology_synthesis import PsychologySynthesis
from nodes.research.stage7.tool_loader import ToolLoader
from nodes.research.stage7.tool_mapping import ToolMapping
from nodes.research.stage8.arc_coherence import ArcCoherence
from nodes.research.stage8.bundle_assembler import BundleAssembler

log = logging.getLogger("pmw.research.pipeline")


async def research_briefs(
    locked_briefs: list[dict],
    run_id: int,
    triggered_by: str = "scheduler",
) -> dict:
    """
    Process multiple briefs through stages 2-8 with controlled concurrency.

    Args:
        locked_briefs: List of brief dicts from BriefBuilder (passed coherence).
        run_id: workflow_runs.id shared by all briefs.
        triggered_by: "scheduler" | "manual"

    Returns:
        {
            "completed_bundles": [research_bundle, ...],
            "errors": [{"topic_title": str, "stage": str, "error": str}, ...],
            "model_usage": [usage_dict, ...],
        }
    """
    if not locked_briefs:
        return {"completed_bundles": [], "errors": [], "model_usage": []}

    concurrency = max(1, settings.BRIEF_CONCURRENCY)
    semaphore = asyncio.Semaphore(concurrency)

    log.info(
        f"Research pipeline: {len(locked_briefs)} brief(s), "
        f"concurrency={concurrency}"
    )

    async def process_with_limit(brief: dict, index: int) -> dict:
        async with semaphore:
            return await _research_one_brief(brief, index, len(locked_briefs), run_id, triggered_by)

    results = await asyncio.gather(
        *(process_with_limit(b, i) for i, b in enumerate(locked_briefs)),
        return_exceptions=True,
    )

    # Collect results
    bundles = []
    errors = []
    usage = []

    for i, result in enumerate(results):
        title = locked_briefs[i].get("topic", {}).get("title", f"Brief #{i}")

        if isinstance(result, Exception):
            log.error(f"Brief '{title}' raised: {result}")
            errors.append({"topic_title": title, "stage": "pipeline", "error": str(result)})
            continue

        if result.get("bundle"):
            bundles.append(result["bundle"])
        if result.get("errors"):
            errors.extend(result["errors"])
        if result.get("model_usage"):
            usage.extend(result["model_usage"])

    log.info(f"Research pipeline done: {len(bundles)}/{len(locked_briefs)} completed")

    return {"completed_bundles": bundles, "errors": errors, "model_usage": usage}


async def _research_one_brief(
    brief: dict,
    index: int,
    total: int,
    run_id: int,
    triggered_by: str,
) -> dict:
    """
    Run stages 2-8 for a single brief. Returns {bundle, errors, model_usage}.

    Each stage is a direct async function call. No LangGraph state merging.
    The brief_state dict is updated in place as stages complete.
    """
    topic = brief.get("topic", {})
    title = topic.get("title", f"Brief #{index}")
    topic_id = topic.get("id")

    log.info(f"━━━ [{index+1}/{total}] '{title}' starting stages 2-8 ━━━")

    # Build per-brief state (plain dict — not LangGraph state)
    s = {
        "run_id": run_id,
        "triggered_by": triggered_by,
        "brief": brief,
        "selected_topic": topic,
        "primary_affiliate": brief.get("affiliate", {}).get("primary"),
        "secondary_affiliate": brief.get("affiliate", {}).get("secondary"),
        "keyword_research": None,
        "market_context": None,
        "competitor_analysis": None,
        "top_factors": None,
        "raw_sources_cache_key": None,
        "buyer_psychology": None,
        "available_tools": None,
        "tool_mapping": None,
        "arc_validation": None,
        "research_bundle": None,
        "current_stage": "stage2",
        "status": "running",
        "errors": [],
        "model_usage": [],
    }

    # Instantiate stage nodes
    stages = {
        "keyword":     KeywordResearch(),
        "market":      MarketContext(),
        "competitor":  CompetitorAnalysis(),
        "factors":     TopFactors(),
        "data_fetch":  DataFetcher(),
        "psychology":  PsychologySynthesis(),
        "tool_load":   ToolLoader(),
        "tool_map":    ToolMapping(),
        "arc":         ArcCoherence(),
        "bundle":      BundleAssembler(),
    }

    try:
        # ── Stages 2, 3, 5 — can run concurrently ─────────────────
        kw_result, market_result, comp_result = await asyncio.gather(
            stages["keyword"].run(s),
            stages["market"].run(s),
            stages["competitor"].run(s),
        )

        _merge(s, kw_result)
        _merge(s, market_result)
        _merge(s, comp_result)

        if _any_failed(s, kw_result, market_result, comp_result):
            return _brief_error(s, title, "stages 2/3/5")

        # ── Stage 4 — needs keyword + market ──────────────────────
        _merge(s, await stages["factors"].run(s))
        if s.get("status") == "failed":
            return _brief_error(s, title, "stage4")

        # ── Stage 6a + 6b — data fetch then synthesis ─────────────
        _merge(s, await stages["data_fetch"].run(s))
        # data_fetch failure is non-fatal (synthesis gets empty sources)

        _merge(s, await stages["psychology"].run(s))
        if s.get("status") == "failed":
            return _brief_error(s, title, "stage6")

        # ── Stage 7a + 7b — tool load then mapping ───────────────
        _merge(s, await stages["tool_load"].run(s))
        # tool_load failure is non-fatal

        _merge(s, await stages["tool_map"].run(s))
        # tool_map failure is non-fatal

        # ── Stage 8a — arc coherence ──────────────────────────────
        _merge(s, await stages["arc"].run(s))
        arc = s.get("arc_validation") or {}
        if not arc.get("arc_coherent", False):
            log.warning(f"'{title}' failed arc coherence — skipping")
            _release_lock(topic_id, run_id)
            return {
                "bundle": None,
                "errors": [{"topic_title": title, "stage": "arc_coherence",
                           "error": arc.get("arc_summary", "Arc incoherent")}],
                "model_usage": s.get("model_usage", []),
            }

        # ── Stage 8b — bundle assembly ────────────────────────────
        _merge(s, await stages["bundle"].run(s))
        bundle = s.get("research_bundle")

        if bundle:
            log.info(f"✓ '{title}' → research bundle complete")
        else:
            log.warning(f"'{title}' bundle assembler produced no output")
            _release_lock(topic_id, run_id)

        return {
            "bundle": bundle,
            "errors": s.get("errors", []),
            "model_usage": s.get("model_usage", []),
        }

    except Exception as exc:
        log.error(f"'{title}' failed unexpectedly: {exc}", exc_info=True)
        _release_lock(topic_id, run_id)
        return {
            "bundle": None,
            "errors": [{"topic_title": title, "stage": "pipeline", "error": str(exc)}],
            "model_usage": s.get("model_usage", []),
        }


# ── Helpers ───────────────────────────────────────────────────────────

def _merge(state: dict, updates: dict) -> None:
    """Merge node output into state dict. In-place, no copy."""
    for key, value in updates.items():
        if value is not None or key in ("status", "errors", "model_usage"):
            if key == "errors" and isinstance(value, list):
                state.setdefault("errors", []).extend(value)
            elif key == "model_usage" and isinstance(value, list):
                state.setdefault("model_usage", []).extend(value)
            else:
                state[key] = value


def _any_failed(*dicts) -> bool:
    """Check if any of the result dicts have status=failed."""
    for d in dicts:
        if isinstance(d, dict) and d.get("status") == "failed":
            return True
    return False


def _brief_error(state: dict, title: str, stage: str) -> dict:
    """Build error return for a failed brief."""
    errors = state.get("errors", [])
    last_err = errors[-1]["error"] if errors else "Unknown"
    log.warning(f"'{title}' failed at {stage}: {last_err}")
    topic_id = state.get("selected_topic", {}).get("id")
    _release_lock(topic_id, state.get("run_id", 0))
    return {
        "bundle": None,
        "errors": [{"topic_title": title, "stage": stage, "error": last_err}],
        "model_usage": state.get("model_usage", []),
    }


def _release_lock(topic_id: int | None, run_id: int) -> None:
    """Fire-and-forget lock release."""
    if not topic_id:
        return
    try:
        asyncio.create_task(_do_release(topic_id, run_id))
    except Exception:
        pass


async def _do_release(topic_id: int, run_id: int) -> None:
    try:
        from services import services
        await services.workflows.release_topic_lock(
            topic_wp_id=topic_id, run_id=run_id, success=False,
        )
    except Exception as exc:
        log.debug(f"Lock release failed for topic {topic_id}: {exc}")