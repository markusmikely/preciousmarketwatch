"""
AffiliateService — load, score, sync, and manage affiliate intelligence.

Owns:
  - Syncing dealer CPT entries from WordPress → Postgres affiliates table
  - Loading active affiliates from Postgres
  - Scoring affiliates against a topic (geo × 0.4 + product × 0.4 + commission × 0.2)
  - Appending intelligence runs (append-only ledger)
  - Rebuilding aggregate intelligence summary (atomic upsert)

Does NOT own:
  - Affiliate CRUD (WordPress dealer CPT admin UI owns that)
  - WP affiliate page rendering (PageManagementService owns that)
  - Compliance review workflow (dashboard owns that)

Usage:
    from services import services

    # Full sync + return (used by affiliate_loader node):
    affiliates = await services.affiliates.sync_and_get_active()

    # Score against a topic:
    scored = await services.affiliates.score_affiliates_for_topic(topic, affiliates)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from infrastructure import get_infrastructure

log = logging.getLogger("pmw.services.affiliate")


class AffiliateService:
    """Stateless service — WordPress + Postgres access via get_infrastructure()."""

    # ══════════════════════════════════════════════════════════════════════
    # WORDPRESS → POSTGRES SYNC
    # ══════════════════════════════════════════════════════════════════════

    async def fetch_from_wordpress(self, active_only: bool = True) -> list[dict]:
        """
        Fetch dealer CPT posts from WordPress via GraphQL.
        Returns normalised affiliate dicts ready for Postgres upsert.
        """
        infra = get_infrastructure()
        try:
            dealers = await infra.wordpress.query_dealers(
                status="PUBLISH",
                active_only=active_only,
                first=100,
            )
            log.info(f"Fetched {len(dealers)} dealer(s) from WordPress")
            return dealers
        except Exception as exc:
            log.error(f"Failed to fetch dealers from WordPress: {exc}")
            raise

    async def sync_to_postgres(self, wp_dealers: list[dict]) -> int:
        """
        Upsert WordPress dealer data into the Postgres affiliates table.
        Uses wp_dealer_id as the conflict key.

        Returns number of dealers synced.
        """
        if not wp_dealers:
            return 0

        infra = get_infrastructure()
        synced = 0

        # Check which columns exist (handles pre/post migration 007)
        has_new_columns = await self._check_new_columns_exist()

        for d in wp_dealers:
            wp_id = d.get("wp_dealer_id")
            if not wp_id:
                log.warning(f"Dealer missing wp_dealer_id, skipping: {d.get('name')}")
                continue

            try:
                if has_new_columns:
                    await self._upsert_full(infra, d, wp_id)
                else:
                    await self._upsert_basic(infra, d, wp_id)
                synced += 1
            except Exception as exc:
                log.warning(
                    f"Affiliate sync failed for WP dealer ID {wp_id} "
                    f"({d.get('name')}): {exc}"
                )

        log.info(f"Synced {synced}/{len(wp_dealers)} dealer(s) to Postgres")
        return synced

    async def _check_new_columns_exist(self) -> bool:
        """Check if migration 007 columns exist on the affiliates table."""
        infra = get_infrastructure()
        try:
            result = await infra.postgres.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'affiliates'
                    AND column_name = 'wp_dealer_id'
                )
                """
            )
            return bool(result)
        except Exception:
            return False

    async def _upsert_full(self, infra, d: dict, wp_id: int) -> None:
        """Upsert with all columns (post-migration 007)."""
        await infra.postgres.execute(
            """
            INSERT INTO affiliates (
                wp_dealer_id, name, partner_key, url, value_prop,
                commission_type, commission_rate, cookie_days,
                geo_focus, min_transaction, faq_url,
                asset_classes, product_types,
                buy_side, sell_side, intent_stages,
                active
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8,
                $9, $10, $11,
                $12, $13,
                $14, $15, $16,
                $17
            )
            ON CONFLICT (wp_dealer_id) DO UPDATE SET
                name             = EXCLUDED.name,
                partner_key      = EXCLUDED.partner_key,
                url              = EXCLUDED.url,
                value_prop       = EXCLUDED.value_prop,
                commission_type  = EXCLUDED.commission_type,
                commission_rate  = EXCLUDED.commission_rate,
                cookie_days      = EXCLUDED.cookie_days,
                geo_focus        = EXCLUDED.geo_focus,
                min_transaction  = EXCLUDED.min_transaction,
                faq_url          = EXCLUDED.faq_url,
                asset_classes    = EXCLUDED.asset_classes,
                product_types    = EXCLUDED.product_types,
                buy_side         = EXCLUDED.buy_side,
                sell_side        = EXCLUDED.sell_side,
                intent_stages    = EXCLUDED.intent_stages,
                active           = EXCLUDED.active
            """,
            wp_id,
            d.get("name", ""),
            d.get("partner_key", ""),
            d.get("url", ""),
            d.get("value_prop", ""),
            d.get("commission_type", ""),
            float(d.get("commission_rate", 0) or 0),
            int(d.get("cookie_days", 0) or 0),
            d.get("geo_focus", ""),
            float(d.get("min_transaction", 0) or 0),
            d.get("faq_url", ""),
            d.get("asset_classes", ""),
            d.get("product_types", ""),
            bool(d.get("buy_side", True)),
            bool(d.get("sell_side", False)),
            d.get("intent_stages", ""),
            bool(d.get("active", True)),
        )

    async def _upsert_basic(self, infra, d: dict, wp_id: int) -> None:
        """
        Upsert using only the original schema columns (pre-migration 007).
        Falls back to matching on name since wp_dealer_id column doesn't exist.
        """
        # Check if this affiliate already exists by name
        existing = await infra.postgres.fetchrow(
            "SELECT id FROM affiliates WHERE name = $1",
            d.get("name", ""),
        )

        if existing:
            await infra.postgres.execute(
                """
                UPDATE affiliates SET
                    url             = $1,
                    value_prop      = $2,
                    commission_type = $3,
                    commission_rate = $4,
                    cookie_days     = $5,
                    geo_focus       = $6,
                    min_transaction = $7,
                    faq_url         = $8,
                    active          = $9
                WHERE name = $10
                """,
                d.get("url", ""),
                d.get("value_prop", ""),
                d.get("commission_type", ""),
                float(d.get("commission_rate", 0) or 0),
                int(d.get("cookie_days", 0) or 0),
                d.get("geo_focus", ""),
                float(d.get("min_transaction", 0) or 0),
                d.get("faq_url", ""),
                bool(d.get("active", True)),
                d.get("name", ""),
            )
        else:
            await infra.postgres.execute(
                """
                INSERT INTO affiliates (
                    name, url, value_prop,
                    commission_type, commission_rate, cookie_days,
                    geo_focus, min_transaction, faq_url, active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                d.get("name", ""),
                d.get("url", ""),
                d.get("value_prop", ""),
                d.get("commission_type", ""),
                float(d.get("commission_rate", 0) or 0),
                int(d.get("cookie_days", 0) or 0),
                d.get("geo_focus", ""),
                float(d.get("min_transaction", 0) or 0),
                d.get("faq_url", ""),
                bool(d.get("active", True)),
            )

    async def sync_and_get_active(self) -> list[dict]:
        """
        Convenience: fetch WP → sync Postgres → return active affiliates.
        This is the primary method called by the affiliate_loader node.
        """
        wp_dealers = await self.fetch_from_wordpress(active_only=False)
        if wp_dealers:
            await self.sync_to_postgres(wp_dealers)
        return await self.get_active_affiliates()

    # ══════════════════════════════════════════════════════════════════════
    # POSTGRES READS
    # ══════════════════════════════════════════════════════════════════════

    async def get_active_affiliates(self) -> list[dict]:
        """
        SELECT all active affiliates from Postgres.

        Uses a resilient query that works both before and after
        migration 007_affiliates_wp_sync. Checks which columns exist
        and adapts the SELECT accordingly.
        """
        infra = get_infrastructure()
        has_new_columns = await self._check_new_columns_exist()

        if has_new_columns:
            rows = await infra.postgres.fetch(
                """
                SELECT id, wp_dealer_id, name, partner_key, url, value_prop,
                       faq_url, commission_type, commission_rate, cookie_days,
                       geo_focus, min_transaction, active,
                       asset_classes, product_types, buy_side, sell_side,
                       intent_stages
                FROM affiliates
                WHERE active = true
                ORDER BY name
                """
            )
        else:
            # Pre-migration 007: only original columns exist
            rows = await infra.postgres.fetch(
                """
                SELECT id, name, url, value_prop,
                       faq_url, commission_type, commission_rate, cookie_days,
                       geo_focus, min_transaction, active
                FROM affiliates
                WHERE active = true
                ORDER BY name
                """
            )

        affiliates = [dict(r) for r in rows]
        log.info(f"Loaded {len(affiliates)} active affiliate(s) from Postgres")
        return affiliates

    async def get_affiliate(self, affiliate_id: int) -> dict | None:
        """Fetch a single affiliate by Postgres ID."""
        infra = get_infrastructure()
        row = await infra.postgres.fetchrow(
            "SELECT * FROM affiliates WHERE id = $1",
            affiliate_id,
        )
        return dict(row) if row else None

    async def get_affiliate_by_wp_id(self, wp_dealer_id: int) -> dict | None:
        """Fetch a single affiliate by its WordPress dealer post ID."""
        infra = get_infrastructure()
        has_new = await self._check_new_columns_exist()
        if not has_new:
            return None
        row = await infra.postgres.fetchrow(
            "SELECT * FROM affiliates WHERE wp_dealer_id = $1",
            wp_dealer_id,
        )
        return dict(row) if row else None

    # ══════════════════════════════════════════════════════════════════════
    # SCORING
    # ══════════════════════════════════════════════════════════════════════

    async def score_affiliates_for_topic(
        self,
        topic: dict,
        affiliates: list[dict],
    ) -> list[dict]:
        """
        Score and rank affiliates by fit against the selected topic.

        Scoring formula:
          fit_score = (geo_match × 0.40) + (product_match × 0.40) + (commission_score × 0.20)

        Returns:
            List of affiliate dicts with 'fit_score' added, sorted descending.
            Affiliates with fit_score < 0.40 are excluded.
        """
        if not affiliates:
            return []

        topic_geo = (topic.get("geography") or "uk").lower()
        topic_asset = (topic.get("asset_class") or "").lower()

        max_commission = max(
            (float(a.get("commission_rate") or 0) for a in affiliates),
            default=1.0,
        ) or 1.0

        scored = []
        for aff in affiliates:
            aff_geo = (aff.get("geo_focus") or "").lower()
            aff_commission = float(aff.get("commission_rate") or 0)

            # ── Geo match ──────────────────────────────────────────
            if aff_geo == topic_geo or aff_geo == "global":
                geo_score = 1.0
            elif aff_geo in ("uk", "us", "global") and topic_geo in ("uk", "us", "global"):
                geo_score = 0.3
            else:
                geo_score = 0.0

            # ── Product/asset match ────────────────────────────────
            # Build a combined text from all available fields for matching
            aff_assets = (aff.get("asset_classes") or "").lower()
            value_prop = (aff.get("value_prop") or "").lower()
            aff_name = (aff.get("name") or "").lower()
            combined_text = f"{aff_assets} {value_prop} {aff_name}"

            if topic_asset and aff_assets and topic_asset in [a.strip() for a in aff_assets.split(",")]:
                product_score = 1.0
            elif topic_asset and topic_asset in combined_text:
                product_score = 0.9
            elif topic_asset in ("gold", "silver", "platinum") and "precious metal" in combined_text:
                product_score = 0.8
            elif topic_asset == "ira" and ("ira" in combined_text or "retirement" in combined_text):
                product_score = 1.0
            elif any(metal in combined_text for metal in ("gold", "silver", "platinum", "bullion")):
                product_score = 0.5
            elif not topic_asset:
                # No asset class on the topic — give a base score to all affiliates
                product_score = 0.5
            else:
                product_score = 0.0

            # ── Commission score (normalised) ──────────────────────
            commission_score = aff_commission / max_commission if max_commission > 0 else 0

            # ── Weighted total ─────────────────────────────────────
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

        scored.sort(key=lambda a: a["fit_score"], reverse=True)
        qualified = [a for a in scored if a["fit_score"] >= 0.40]

        log.info(
            f"Scored {len(affiliates)} affiliates, {len(qualified)} qualified "
            f"(topic_asset={topic_asset!r}, topic_geo={topic_geo!r})",
            extra={
                "top_affiliate": qualified[0]["name"] if qualified else "none",
                "top_score": qualified[0]["fit_score"] if qualified else 0,
                "all_scores": [
                    {"name": a["name"], "score": a["fit_score"]}
                    for a in scored[:5]
                ],
            },
        )

        return qualified

    # ══════════════════════════════════════════════════════════════════════
    # INTELLIGENCE STORE
    # ══════════════════════════════════════════════════════════════════════

    async def append_intelligence_run(
        self,
        affiliate_id: int,
        run_id: int,
        data: dict,
    ) -> None:
        """INSERT INTO affiliate_intelligence_runs (append-only ledger)."""
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
        log.info("Intelligence run appended", extra={"affiliate_id": affiliate_id, "run_id": run_id})

    async def rebuild_intelligence_summary(self, affiliate_id: int) -> dict:
        """
        Rebuild affiliate_intelligence_summary from all runs in the ledger.
        Uses atomic UPSERT — no read-modify-write race condition.
        """
        infra = get_infrastructure()

        rows = await infra.postgres.fetch(
            "SELECT * FROM affiliate_intelligence_runs WHERE affiliate_id = $1 ORDER BY ran_at DESC",
            affiliate_id,
        )
        if not rows:
            log.warning(f"No intelligence runs found for affiliate {affiliate_id}")
            return {}

        all_runs = [dict(r) for r in rows]
        latest = all_runs[0]

        # ── Aggregate objections ───────────────────────────────────
        objection_counts: dict[str, dict] = {}
        for run in all_runs:
            for obj in json.loads(run.get("objections_json") or "[]"):
                key = (obj.get("objection") or "").strip().lower()
                if not key:
                    continue
                if key not in objection_counts:
                    objection_counts[key] = {
                        "objection": obj["objection"], "run_count": 0,
                        "sources": set(),
                        "compliance_review_required": obj.get("compliance_review_required", False),
                    }
                objection_counts[key]["run_count"] += 1
                objection_counts[key]["sources"].add(obj.get("source", ""))

        top_objections = sorted(
            [{**v, "sources": list(v["sources"])} for v in objection_counts.values()],
            key=lambda x: x["run_count"], reverse=True,
        )[:8]

        # ── Aggregate motivations ──────────────────────────────────
        motivation_counts: dict[str, dict] = {}
        for run in all_runs:
            for mot in json.loads(run.get("motivations_json") or "[]"):
                key = (mot.get("motivation") or "").strip().lower()
                if not key:
                    continue
                if key not in motivation_counts:
                    motivation_counts[key] = {"motivation": mot["motivation"], "run_count": 0}
                motivation_counts[key]["run_count"] += 1

        top_motivations = sorted(
            list(motivation_counts.values()), key=lambda x: x["run_count"], reverse=True,
        )[:6]

        # ── Verbatim pool ──────────────────────────────────────────
        phrase_seen: dict[str, dict] = {}
        for run in all_runs:
            for phrase in json.loads(run.get("verbatim_phrases") or "[]"):
                normalised = " ".join(phrase.lower().split())
                if normalised not in phrase_seen:
                    ran_at = run.get("ran_at")
                    phrase_seen[normalised] = {
                        "phrase": phrase,
                        "first_seen": ran_at.isoformat() if hasattr(ran_at, "isoformat") else str(ran_at or ""),
                        "run_count": 0,
                    }
                phrase_seen[normalised]["run_count"] += 1

        verbatim_pool = sorted(list(phrase_seen.values()), key=lambda x: x["run_count"], reverse=True)[:20]

        # ── PAA pool ───────────────────────────────────────────────
        paa_seen: dict[str, dict] = {}
        for run in all_runs:
            for q in json.loads(run.get("paa_questions") or "[]"):
                normalised = " ".join(q.lower().split())
                if normalised not in paa_seen:
                    paa_seen[normalised] = {"question": q, "run_count": 0}
                paa_seen[normalised]["run_count"] += 1

        paa_pool = sorted(list(paa_seen.values()), key=lambda x: x["run_count"], reverse=True)[:15]

        has_pending = any(
            r.get("compliance_review_required") and not r.get("compliance_reviewed_at")
            for r in all_runs
        )

        def to_iso(val):
            if val is None:
                return None
            return val.isoformat() if hasattr(val, "isoformat") else str(val)

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

        aff = await self.get_affiliate(affiliate_id)
        partner_key = (
            aff.get("partner_key")
            or aff.get("name", "").lower().replace(" ", "-")
            if aff else "unknown"
        )

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
                $1, $2, $3, $4::timestamptz, $5::timestamptz,
                $6, $7, $8, $9::timestamptz,
                $10::jsonb, $11::jsonb, $12::jsonb, $13::jsonb,
                $14::jsonb, $15, NOW()
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
            affiliate_id, partner_key,
            summary["total_runs"], summary["first_run_at"], summary["last_run_at"],
            summary["latest_spot_price_gbp"], summary["latest_price_trend_30d"],
            summary["latest_market_stance"], summary["latest_ran_at"],
            json.dumps(summary["top_objections"]), json.dumps(summary["top_motivations"]),
            json.dumps(summary["verbatim_pool"]), json.dumps(summary["paa_pool"]),
            json.dumps(summary["latest_factors"]), summary["has_pending_review"],
        )

        log.info("Intelligence summary rebuilt", extra={"affiliate_id": affiliate_id, "total_runs": summary["total_runs"]})
        return summary

    async def get_intelligence_summary(self, affiliate_id: int) -> dict | None:
        """Read the current summary row for an affiliate."""
        infra = get_infrastructure()
        row = await infra.postgres.fetchrow(
            "SELECT * FROM affiliate_intelligence_summary WHERE affiliate_id = $1",
            affiliate_id,
        )
        return dict(row) if row else None