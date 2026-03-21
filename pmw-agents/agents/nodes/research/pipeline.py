"""
Research Pipeline (v3.0) — content-type-aware stage routing.

  affiliate       → stages 2, 3, 4, 5, 6, 7, 8 (full research)
  authority       → stages 2, 5 (keyword + competitor only)
  market_commentary → stages 2, 3 (keyword + market only)

Partial bundles are assembled from whichever stages ran.
"""

from __future__ import annotations

import asyncio
import logging

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

    async def process_with_limit(brief, index):
        async with semaphore:
            return await _research_one_brief(brief, index, len(locked_briefs), run_id)

    results = await asyncio.gather(
        *(process_with_limit(b, i) for i, b in enumerate(locked_briefs)),
        return_exceptions=True,
    )

    bundles, errors, usage = [], [], []
    for i, result in enumerate(results):
        title = locked_briefs[i].get("topic", {}).get("title", f"Brief #{i}")
        if isinstance(result, Exception):
            errors.append({"topic_title": title, "stage": "pipeline", "error": str(result)})
            continue
        if result.get("bundle"):
            bundles.append(result["bundle"])
        errors.extend(result.get("errors", []))
        usage.extend(result.get("model_usage", []))

    log.info(f"Research done: {len(bundles)}/{len(locked_briefs)} completed")
    return {"completed_bundles": bundles, "errors": errors, "model_usage": usage}


async def _research_one_brief(brief, index, total, run_id):
    topic = brief.get("topic", {})
    title = topic.get("title", f"Brief #{index}")
    topic_id = topic.get("id")
    content_type = topic.get("content_type", "affiliate")

    log.info(f"━━━ [{index+1}/{total}] '{title}' [{content_type}] ━━━")

    # Build per-brief state
    s = {
        "run_id": run_id, "brief": brief, "selected_topic": topic,
        "primary_affiliate": brief.get("affiliate", {}).get("primary"),
        "secondary_affiliate": brief.get("affiliate", {}).get("secondary"),
        "keyword_research": None, "market_context": None,
        "competitor_analysis": None, "top_factors": None,
        "raw_sources_cache_key": None, "buyer_psychology": None,
        "available_tools": None, "tool_mapping": None,
        "arc_validation": None, "research_bundle": None,
        "status": "running", "errors": [], "model_usage": [],
    }

    stages = {
        "keyword": KeywordResearch(), "market": MarketContext(),
        "competitor": CompetitorAnalysis(), "factors": TopFactors(),
        "data_fetch": DataFetcher(), "psychology": PsychologySynthesis(),
        "tool_load": ToolLoader(), "tool_map": ToolMapping(),
        "arc": ArcCoherence(), "bundle": BundleAssembler(),
    }

    try:
        if content_type == "authority":
            await _run_authority_stages(s, stages)
        elif content_type == "market_commentary":
            await _run_commentary_stages(s, stages)
        else:
            await _run_affiliate_stages(s, stages)

        if s.get("status") == "failed":
            return _brief_result(s, title, topic_id, run_id, success=False)

        # Assemble bundle from whatever stages ran
        _merge(s, await stages["bundle"].run(s))
        bundle = s.get("research_bundle")

        if bundle:
            log.info(f"✓ '{title}' → bundle complete")
        else:
            log.warning(f"'{title}' → bundle assembly produced no output")

        return _brief_result(s, title, topic_id, run_id, success=bool(bundle))

    except Exception as exc:
        log.error(f"'{title}' failed: {exc}", exc_info=True)
        _release_lock(topic_id, run_id)
        return {"bundle": None, "errors": [{"topic_title": title, "error": str(exc)}],
                "model_usage": s.get("model_usage", [])}


async def _run_affiliate_stages(s, stages):
    """Full research: stages 2,3,5 parallel → 4 → 6a,6b → 7a,7b → 8a."""
    kw, mkt, comp = await asyncio.gather(
        stages["keyword"].run(s), stages["market"].run(s), stages["competitor"].run(s),
    )
    _merge(s, kw); _merge(s, mkt); _merge(s, comp)
    if _any_failed(kw, mkt, comp):
        s["status"] = "failed"; return

    _merge(s, await stages["factors"].run(s))
    if s.get("status") == "failed": return

    _merge(s, await stages["data_fetch"].run(s))
    _merge(s, await stages["psychology"].run(s))
    if s.get("status") == "failed": return

    _merge(s, await stages["tool_load"].run(s))
    _merge(s, await stages["tool_map"].run(s))

    _merge(s, await stages["arc"].run(s))
    arc = s.get("arc_validation") or {}
    if not arc.get("arc_coherent", False):
        s["status"] = "failed"
        s["errors"].append({"stage": "arc_coherence", "error": arc.get("arc_summary", "Arc incoherent")})


async def _run_authority_stages(s, stages):
    """Authority content: keyword research + competitor analysis only."""
    kw, comp = await asyncio.gather(
        stages["keyword"].run(s), stages["competitor"].run(s),
    )
    _merge(s, kw); _merge(s, comp)
    if _any_failed(kw, comp):
        s["status"] = "failed"


async def _run_commentary_stages(s, stages):
    """Commentary content: keyword research + market context only."""
    kw, mkt = await asyncio.gather(
        stages["keyword"].run(s), stages["market"].run(s),
    )
    _merge(s, kw); _merge(s, mkt)
    if _any_failed(kw, mkt):
        s["status"] = "failed"


# ── Bundle assembler needs to handle partial bundles ──────────────────

# (The existing BundleAssembler checks REQUIRED_SECTIONS — we need to
#  update it to only require sections that were supposed to run.)
# This is handled in the updated bundle_assembler.py below.


# ── Helpers ───────────────────────────────────────────────────────────

def _merge(state, updates):
    for k, v in updates.items():
        if v is not None or k in ("status", "errors", "model_usage"):
            if k == "errors" and isinstance(v, list):
                state.setdefault("errors", []).extend(v)
            elif k == "model_usage" and isinstance(v, list):
                state.setdefault("model_usage", []).extend(v)
            else:
                state[k] = v

def _any_failed(*dicts):
    return any(isinstance(d, dict) and d.get("status") == "failed" for d in dicts)

def _brief_result(s, title, topic_id, run_id, success):
    if not success:
        _release_lock(topic_id, run_id)
    return {
        "bundle": s.get("research_bundle"),
        "errors": s.get("errors", []),
        "model_usage": s.get("model_usage", []),
    }

def _release_lock(topic_id, run_id):
    if not topic_id: return
    try:
        asyncio.create_task(_do_release(topic_id, run_id))
    except Exception:
        pass

async def _do_release(topic_id, run_id):
    try:
        from services import services
        await services.workflows.release_topic_lock(topic_wp_id=topic_id, run_id=run_id, success=False)
    except Exception as exc:
        log.debug(f"Lock release failed: {exc}")