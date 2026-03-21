"""
Research Pipeline — plain async orchestrator for stages 2-8. (v2.2)

v2.2 changes:
  - Each stage result is persisted to topic_research_results table
  - Results survive process crashes and are visible in dashboard
  - _run_stage helper consolidates stage execution + persistence

Usage (called from research_graph._research_briefs_node):
    from nodes.research.pipeline import research_briefs
    results = await research_briefs(locked_briefs, run_id, triggered_by)
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from config.settings import settings

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
    if not locked_briefs:
        return {"completed_bundles": [], "errors": [], "model_usage": []}

    concurrency = max(1, settings.BRIEF_CONCURRENCY)
    semaphore = asyncio.Semaphore(concurrency)

    log.info(f"Research pipeline: {len(locked_briefs)} brief(s), concurrency={concurrency}")

    async def process_with_limit(brief: dict, index: int) -> dict:
        async with semaphore:
            return await _research_one_brief(brief, index, len(locked_briefs), run_id, triggered_by)

    results = await asyncio.gather(
        *(process_with_limit(b, i) for i, b in enumerate(locked_briefs)),
        return_exceptions=True,
    )

    bundles, errors, usage = [], [], []
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
    brief: dict, index: int, total: int, run_id: int, triggered_by: str,
) -> dict:
    topic = brief.get("topic", {})
    title = topic.get("title", f"Brief #{index}")
    topic_id = topic.get("id")

    log.info(f"━━━ [{index+1}/{total}] '{title}' starting stages 2-8 ━━━")

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

    stages = {
        "keyword":    KeywordResearch(),
        "market":     MarketContext(),
        "competitor": CompetitorAnalysis(),
        "factors":    TopFactors(),
        "data_fetch": DataFetcher(),
        "psychology": PsychologySynthesis(),
        "tool_load":  ToolLoader(),
        "tool_map":   ToolMapping(),
        "arc":        ArcCoherence(),
        "bundle":     BundleAssembler(),
    }

    try:
        # ── Stages 2, 3, 5 — concurrent ──────────────────────────
        kw_result, market_result, comp_result = await asyncio.gather(
            _run_stage(stages["keyword"], s, run_id, topic_id, title),
            _run_stage(stages["market"], s, run_id, topic_id, title),
            _run_stage(stages["competitor"], s, run_id, topic_id, title),
        )
        _merge(s, kw_result)
        _merge(s, market_result)
        _merge(s, comp_result)

        if _any_failed(s, kw_result, market_result, comp_result):
            return _brief_error(s, title, "stages 2/3/5")

        # ── Stage 4 ──────────────────────────────────────────────
        _merge(s, await _run_stage(stages["factors"], s, run_id, topic_id, title))
        if s.get("status") == "failed":
            return _brief_error(s, title, "stage4")

        # ── Stage 6a + 6b ────────────────────────────────────────
        _merge(s, await _run_stage(stages["data_fetch"], s, run_id, topic_id, title))
        _merge(s, await _run_stage(stages["psychology"], s, run_id, topic_id, title))
        if s.get("status") == "failed":
            return _brief_error(s, title, "stage6")

        # ── Stage 7a + 7b ────────────────────────────────────────
        _merge(s, await _run_stage(stages["tool_load"], s, run_id, topic_id, title))
        _merge(s, await _run_stage(stages["tool_map"], s, run_id, topic_id, title))

        # ── Stage 8a — arc coherence ─────────────────────────────
        _merge(s, await _run_stage(stages["arc"], s, run_id, topic_id, title))
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

        # ── Stage 8b — bundle assembly ───────────────────────────
        _merge(s, await _run_stage(stages["bundle"], s, run_id, topic_id, title))
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


# ── Stage runner with persistence ─────────────────────────────────────

async def _run_stage(
    stage_node,
    state: dict,
    run_id: int,
    topic_wp_id: int | None,
    topic_title: str,
) -> dict:
    """
    Run a stage node and persist the result to topic_research_results.
    This is fire-and-forget for persistence — stage failures are NOT
    caused by DB write failures.
    """
    stage_name = getattr(stage_node, "stage_name", stage_node.__class__.__name__)

    # Persist "running" status
    await _save_result(run_id, topic_wp_id, topic_title, stage_name, "running")

    # Run the actual stage
    result = await stage_node.run(state)

    # Persist the result
    status = "failed" if result.get("status") == "failed" else "complete"
    output_key = _find_output_key(result, stage_name)
    output_data = result.get(output_key) if output_key else None
    error = None
    if result.get("errors"):
        last_err = result["errors"][-1] if isinstance(result["errors"], list) else result["errors"]
        error = last_err.get("error", str(last_err)) if isinstance(last_err, dict) else str(last_err)

    # Extract cost info from model_usage if present
    cost_usd = 0.0
    in_tok = 0
    out_tok = 0
    model_used = None
    for u in result.get("model_usage", []):
        if isinstance(u, dict) and stage_name in u.get("stage", ""):
            cost_usd += u.get("cost_usd", 0)
            in_tok += u.get("input_tokens", 0)
            out_tok += u.get("output_tokens", 0)
            model_used = u.get("model", model_used)

    await _save_result(
        run_id, topic_wp_id, topic_title, stage_name, status,
        output=output_data, error=error,
        model_used=model_used, input_tokens=in_tok, output_tokens=out_tok,
        cost_usd=cost_usd,
    )

    return result


async def _save_result(
    run_id: int,
    topic_wp_id: int | None,
    topic_title: str,
    stage_name: str,
    status: str,
    output: Any = None,
    error: str | None = None,
    model_used: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
) -> None:
    """Fire-and-forget persistence to topic_research_results. Never raises."""
    if not topic_wp_id:
        return
    try:
        from services import services
        await services.research_results.save(
            run_id=run_id,
            topic_wp_id=topic_wp_id,
            topic_title=topic_title,
            stage_name=stage_name,
            status=status,
            output=output if isinstance(output, dict) else None,
            error=error,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
    except Exception as exc:
        log.debug(f"Research result persistence failed (non-blocking): {exc}")


def _find_output_key(result: dict, stage_name: str) -> str | None:
    """Find the primary output key in a stage result dict."""
    # Map stage names to their output keys
    key_map = {
        "keyword_research": "keyword_research",
        "market_context": "market_context",
        "competitor_analysis": "competitor_analysis",
        "top_factors": "top_factors",
        "data_fetcher": "raw_sources_cache_key",
        "psychology_synthesis": "buyer_psychology",
        "tool_loader": "available_tools",
        "tool_mapping": "tool_mapping",
        "arc_coherence": "arc_validation",
        "bundle_assembler": "research_bundle",
    }
    for pattern, key in key_map.items():
        if pattern in stage_name:
            return key
    return None


# ── Helpers ───────────────────────────────────────────────────────────

def _merge(state: dict, updates: dict) -> None:
    for key, value in updates.items():
        if value is not None or key in ("status", "errors", "model_usage"):
            if key == "errors" and isinstance(value, list):
                state.setdefault("errors", []).extend(value)
            elif key == "model_usage" and isinstance(value, list):
                state.setdefault("model_usage", []).extend(value)
            else:
                state[key] = value


def _any_failed(*dicts) -> bool:
    for d in dicts:
        if isinstance(d, dict) and d.get("status") == "failed":
            return True
    return False


def _brief_error(state: dict, title: str, stage: str) -> dict:
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