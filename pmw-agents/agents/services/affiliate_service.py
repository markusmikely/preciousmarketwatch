"""
AffiliateService — load, score, and manage affiliate intelligence.

Owns:
  - Loading active affiliates from Postgres
  - Scoring affiliates against a topic (geo × 0.4 + product × 0.4 + commission × 0.2)
  - Appending intelligence runs (append-only ledger)
  - Rebuilding aggregate intelligence summary (atomic upsert)

Does NOT own:
  - Affiliate CRUD (dashboard/admin UI owns that)
  - WP affiliate page rendering (PageManagementService owns that)
  - Compliance review workflow (dashboard owns that)

Usage:
    from services import services
    affiliates = await services.affiliates.get_active_affiliates()
    scored     = await services.affiliates.score_affiliates_for_topic(topic, affiliates)
    primary    = scored[0]
"""

from __future__ import annotations

import json
import logging
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.affiliate")


class AffiliateService:
    """Stateless service — Postgres access via get_infrastructure()."""

    # ── Load affiliates ────────────────────────────────────────────────────

    async def get_active_affiliates(self) -> list[dict]:
        """
        SELECT all active affiliates.
        Returns list of affiliate dicts.
        """
        infra = get_infrastructure()
        rows = await infra.postgres.fetch(
            """
            SELECT id, name, url, value_prop, faq_url,
                   commission_type, commission_rate, cookie_days,
                   geo_focus, min_transaction, active
            FROM affiliates
            WHERE active = true
            ORDER BY name
            """
        )
        return [dict(r) for r in rows]

    async def get_affiliate(self, affiliate_id: int) -> dict | None:
        """Fetch a single affiliate by Postgres ID."""
        infra = get_infrastructure()
        row = await infra.postgres.fetchrow(
            "SELECT * FROM affiliates WHERE id = $1",
            affiliate_id,
        )
        return dict(row) if row else None

    # ── Score affiliates against a topic ───────────────────────────────────

    async def score_affiliates_for_topic(
        self,
        topic: dict,
        affiliates: list[dict],
    ) -> list[dict]:
        """
        Score and rank affiliates by fit against the selected topic.

        Scoring formula:
          fit_score = (geo_match × 0.40) + (product_match × 0.40) + (commission_score × 0.20)

        geo_match:     1.0 if affiliate.geo_focus == topic.geography or affiliate.geo_focus == "global"
                       0.5 if partial overlap
                       0.0 if no match
        product_match: 1.0 if affiliate supports topic.asset_class
                       0.5 if affiliate supports related class
                       0.0 if no match
        commission_score: normalised 0-1 based on commission_rate relative to max in list

        Returns:
            List of affiliate dicts with 'fit_score' added, sorted descending.
            Affiliates with fit_score < 0.40 are excluded.
        """
        if not affiliates:
            return []

        topic_geo = (topic.get("geography") or "uk").lower()
        topic_asset = (topic.get("asset_class") or "").lower()

        # Find max commission for normalisation
        max_commission = max(
            (float(a.get("commission_rate") or 0) for a in affiliates),
            default=1.0,
        ) or 1.0  # avoid division by zero

        scored = []
        for aff in affiliates:
            aff_geo = (aff.get("geo_focus") or "").lower()
            aff_commission = float(aff.get("commission_rate") or 0)

            # Geo match
            if aff_geo == topic_geo or aff_geo == "global":
                geo_score = 1.0
            elif aff_geo in ("uk", "us", "global") and topic_geo in ("uk", "us", "global"):
                geo_score = 0.3  # some overlap for English-speaking markets
            else:
                geo_score = 0.0

            # Product/asset match — check if affiliate name/value_prop mentions the asset
            value_prop = (aff.get("value_prop") or "").lower()
            aff_name = (aff.get("name") or "").lower()
            combined_text = f"{value_prop} {aff_name}"

            if topic_asset and topic_asset in combined_text:
                product_score = 1.0
            elif topic_asset in ("gold", "silver", "platinum") and "precious metal" in combined_text:
                product_score = 0.8
            elif topic_asset == "ira" and ("ira" in combined_text or "retirement" in combined_text):
                product_score = 1.0
            elif any(metal in combined_text for metal in ("gold", "silver", "platinum", "bullion")):
                product_score = 0.5  # general precious metals affiliate
            else:
                product_score = 0.0

            # Commission score (normalised)
            commission_score = aff_commission / max_commission if max_commission > 0 else 0

            # Weighted total
            fit_score = round(
                (geo_score * 0.40) + (product_score * 0.40) + (commission_score * 0.20),
                3,
            )

            scored.append({
                **aff,
                "fit_score": fit_score,
                "score_breakdown": {
                    "geo": round(geo_score, 2),
                    "product": round(product_score, 2),
                    "commission": round(commission_score, 2),
                },
            })

        # Sort by fit_score descending, filter out poor fits
        scored.sort(key=lambda a: a["fit_score"], reverse=True)
        qualified = [a for a in scored if a["fit_score"] >= 0.40]

        log.info(
            f"Scored {len(affiliates)} affiliates, {len(qualified)} qualified",
            extra={
                "topic_asset": topic_asset,
                "topic_geo": topic_geo,
                "top_affiliate": qualified[0]["name"] if qualified else "none",
            },
        )

        return qualified

    # ── Intelligence Store — append run ────────────────────────────────────

    async def append_intelligence_run(
        self,
        affiliate_id: int,
        run_id: int,
        data: dict,
    ) -> None:
        """
        INSERT INTO affiliate_intelligence_runs (append-only ledger).
        ON CONFLICT DO NOTHING ensures idempotency on re-runs.

        Args:
            affiliate_id: affiliates.id
            run_id: workflow_runs.id
            data: Dict containing topic, market, factors, psychology, keyword fields.
        """
        infra = get_infrastructure()

        topic = data.get("topic", {})
        market = data.get("market", {})
        factors = data.get("factors", {})
        psych = data.get("psychology", {})
        kw = data.get("keywords", {})

        await infra.postgres.execute(
            """
            INSERT INTO affiliate_intelligence_runs (
                affiliate_id, run_id, topic_id, asset_class, geography,
                spot_price_gbp, price_trend_pct_30d, price_trend_pct_90d,
                market_stance, emotional_trigger,
                top_factors_json,
                objections_json, motivations_json, verbatim_phrases,
                paa_questions, source_quality,
                compliance_review_required
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11::jsonb,
                $12::jsonb, $13::jsonb, $14::jsonb,
                $15::jsonb, $16, $17
            )
            ON CONFLICT (run_id, affiliate_id) DO NOTHING
            """,
            affiliate_id,
            run_id,
            topic.get("id"),
            topic.get("asset_class", ""),
            topic.get("geography", "uk"),
            market.get("spot_price_gbp"),
            market.get("price_trend_pct_30d"),
            market.get("price_trend_pct_90d"),
            market.get("market_stance"),
            market.get("emotional_trigger"),
            json.dumps(factors.get("factors", [])),
            json.dumps(psych.get("objections", [])),
            json.dumps(psych.get("motivations", [])),
            json.dumps(psych.get("verbatim_phrases", [])),
            json.dumps(kw.get("paa_questions", [])),
            psych.get("source_quality", {}).get("data_richness", "low"),
            psych.get("any_section_requires_review", False),
        )

        log.info(
            "Intelligence run appended",
            extra={"affiliate_id": affiliate_id, "run_id": run_id},
        )

    # ── Intelligence Store — rebuild summary ───────────────────────────────

    async def rebuild_intelligence_summary(self, affiliate_id: int) -> dict:
        """
        Rebuild affiliate_intelligence_summary from all runs in the ledger.
        Uses atomic UPSERT — no read-modify-write race condition.

        Returns the computed summary dict.
        """
        infra = get_infrastructure()

        # Fetch all runs for this affiliate
        rows = await infra.postgres.fetch(
            """
            SELECT * FROM affiliate_intelligence_runs
            WHERE affiliate_id = $1
            ORDER BY ran_at DESC
            """,
            affiliate_id,
        )

        if not rows:
            log.warning(f"No intelligence runs found for affiliate {affiliate_id}")
            return {}

        all_runs = [dict(r) for r in rows]
        latest = all_runs[0]

        # ── Aggregate objections by frequency ──────────────────────────
        objection_counts: dict[str, dict] = {}
        for run in all_runs:
            for obj in json.loads(run.get("objections_json") or "[]"):
                key = (obj.get("objection") or "").strip().lower()
                if not key:
                    continue
                if key not in objection_counts:
                    objection_counts[key] = {
                        "objection": obj["objection"],
                        "run_count": 0,
                        "sources": set(),
                        "compliance_review_required": obj.get("compliance_review_required", False),
                    }
                objection_counts[key]["run_count"] += 1
                objection_counts[key]["sources"].add(obj.get("source", ""))

        top_objections = sorted(
            [
                {**v, "sources": list(v["sources"])}
                for v in objection_counts.values()
            ],
            key=lambda x: x["run_count"],
            reverse=True,
        )[:8]

        # ── Aggregate motivations ──────────────────────────────────────
        motivation_counts: dict[str, dict] = {}
        for run in all_runs:
            for mot in json.loads(run.get("motivations_json") or "[]"):
                key = (mot.get("motivation") or "").strip().lower()
                if not key:
                    continue
                if key not in motivation_counts:
                    motivation_counts[key] = {
                        "motivation": mot["motivation"],
                        "run_count": 0,
                    }
                motivation_counts[key]["run_count"] += 1

        top_motivations = sorted(
            list(motivation_counts.values()),
            key=lambda x: x["run_count"],
            reverse=True,
        )[:6]

        # ── Deduplicated verbatim pool ─────────────────────────────────
        phrase_seen: dict[str, dict] = {}
        for run in all_runs:
            for phrase in json.loads(run.get("verbatim_phrases") or "[]"):
                normalised = " ".join(phrase.lower().split())
                if normalised not in phrase_seen:
                    phrase_seen[normalised] = {
                        "phrase": phrase,
                        "first_seen": (run.get("ran_at") or "").isoformat()
                            if hasattr(run.get("ran_at"), "isoformat") else str(run.get("ran_at", "")),
                        "run_count": 0,
                    }
                phrase_seen[normalised]["run_count"] += 1

        verbatim_pool = sorted(
            list(phrase_seen.values()),
            key=lambda x: x["run_count"],
            reverse=True,
        )[:20]

        # ── PAA pool ───────────────────────────────────────────────────
        paa_seen: dict[str, dict] = {}
        for run in all_runs:
            for q in json.loads(run.get("paa_questions") or "[]"):
                normalised = " ".join(q.lower().split())
                if normalised not in paa_seen:
                    paa_seen[normalised] = {
                        "question": q,
                        "run_count": 0,
                    }
                paa_seen[normalised]["run_count"] += 1

        paa_pool = sorted(
            list(paa_seen.values()),
            key=lambda x: x["run_count"],
            reverse=True,
        )[:15]

        # ── Pending compliance review check ────────────────────────────
        has_pending = any(
            r.get("compliance_review_required") and not r.get("compliance_reviewed_at")
            for r in all_runs
        )

        # ── Helper for safe ISO string ─────────────────────────────────
        def to_iso(val):
            if val is None:
                return None
            if hasattr(val, "isoformat"):
                return val.isoformat()
            return str(val)

        # ── Atomic UPSERT to summary ───────────────────────────────────
        summary = {
            "affiliate_id": affiliate_id,
            "total_runs": len(all_runs),
            "first_run_at": to_iso(all_runs[-1].get("ran_at")),
            "last_run_at": to_iso(latest.get("ran_at")),
            "latest_spot_price_gbp": latest.get("spot_price_gbp"),
            "latest_price_trend_30d": latest.get("price_trend_pct_30d"),
            "latest_market_stance": latest.get("market_stance"),
            "latest_ran_at": to_iso(latest.get("ran_at")),
            "top_objections": top_objections,
            "top_motivations": top_motivations,
            "verbatim_pool": verbatim_pool,
            "paa_pool": paa_pool,
            "latest_factors": json.loads(latest.get("top_factors_json") or "[]"),
            "has_pending_review": has_pending,
        }

        # Get partner_key from affiliates table
        aff = await self.get_affiliate(affiliate_id)
        partner_key = aff.get("name", "").lower().replace(" ", "-") if aff else "unknown"

        await infra.postgres.execute(
            """
            INSERT INTO affiliate_intelligence_summary (
                affiliate_id, partner_key,
                total_runs, first_run_at, last_run_at,
                latest_spot_price_gbp, latest_price_trend_30d,
                latest_market_stance, latest_ran_at,
                top_objections_json, top_motivations_json,
                verbatim_pool_json, paa_pool_json,
                latest_factors_json, has_pending_review,
                updated_at
            ) VALUES (
                $1, $2,
                $3, $4::timestamptz, $5::timestamptz,
                $6, $7, $8, $9::timestamptz,
                $10::jsonb, $11::jsonb,
                $12::jsonb, $13::jsonb,
                $14::jsonb, $15,
                NOW()
            )
            ON CONFLICT (affiliate_id) DO UPDATE SET
                partner_key            = EXCLUDED.partner_key,
                total_runs             = EXCLUDED.total_runs,
                last_run_at            = EXCLUDED.last_run_at,
                latest_spot_price_gbp  = EXCLUDED.latest_spot_price_gbp,
                latest_price_trend_30d = EXCLUDED.latest_price_trend_30d,
                latest_market_stance   = EXCLUDED.latest_market_stance,
                latest_ran_at          = EXCLUDED.latest_ran_at,
                top_objections_json    = EXCLUDED.top_objections_json,
                top_motivations_json   = EXCLUDED.top_motivations_json,
                verbatim_pool_json     = EXCLUDED.verbatim_pool_json,
                paa_pool_json          = EXCLUDED.paa_pool_json,
                latest_factors_json    = EXCLUDED.latest_factors_json,
                has_pending_review     = EXCLUDED.has_pending_review,
                updated_at             = NOW()
            """,
            affiliate_id,
            partner_key,
            summary["total_runs"],
            summary["first_run_at"],
            summary["last_run_at"],
            summary["latest_spot_price_gbp"],
            summary["latest_price_trend_30d"],
            summary["latest_market_stance"],
            summary["latest_ran_at"],
            json.dumps(summary["top_objections"]),
            json.dumps(summary["top_motivations"]),
            json.dumps(summary["verbatim_pool"]),
            json.dumps(summary["paa_pool"]),
            json.dumps(summary["latest_factors"]),
            summary["has_pending_review"],
        )

        log.info(
            "Intelligence summary rebuilt",
            extra={"affiliate_id": affiliate_id, "total_runs": summary["total_runs"]},
        )
        return summary

    # ── Read summary ───────────────────────────────────────────────────────

    async def get_intelligence_summary(self, affiliate_id: int) -> dict | None:
        """Read the current summary row for an affiliate."""
        infra = get_infrastructure()
        row = await infra.postgres.fetchrow(
            "SELECT * FROM affiliate_intelligence_summary WHERE affiliate_id = $1",
            affiliate_id,
        )
        return dict(row) if row else None