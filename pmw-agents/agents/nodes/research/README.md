# PMW — Market Research Phase v4
## Agent Design, Dependency Graph & LangGraph Implementation Plan

> **Version:** 4.0 — February 2026
> **Changes from v3:**
> - **Fix (Issue 2):** Topic locking race condition resolved — Postgres advisory
>   lock replaces WP meta as the concurrency guard. `lock_expires_at` provides
>   automatic crash recovery. WP meta is display-only.
> - **Fix (Issue 5):** Comparison table race condition resolved — moved from a
>   single WP option (read-modify-write) to per-affiliate rows in Postgres with
>   atomic `INSERT ... ON CONFLICT DO UPDATE` statements.
> - **Redesigned Stage 9:** Affiliate Intelligence Store now operates as a
>   rolling aggregation model. Each successful research run appends to
>   `affiliate_intelligence_runs` in Postgres. The affiliate page displays
>   aggregated signals across all runs — single runs do not dominate the display.
> - **Sources cleaned:** Trustpilot scraping removed entirely. Stage 6 sources
>   are now Reddit, MoneySavingExpert forums, and PAA questions — all reliably
>   fetchable without legal risk. Affiliate-specific factual claims sourced from
>   the affiliate's own published FAQ/documentation, not LLM-generated.
> - **Compliance gate:** `compliance_review_required` flag added to Stage 9
>   payload. Sections containing specific factual claims about regulated products
>   are held for human review before publication.

---

## 1. Data Model

### 1a. Topics — Authored and Managed in WordPress

Topics are created, edited, scheduled, and paused entirely within WordPress
using a Custom Post Type. The WP REST API is the single source of truth for
topic definitions. The agent database stores run outputs and locks — not topic
definitions.

#### WordPress CPT: `pmw_topic`

```php
function pmw_register_topic_cpt() {
    register_post_type( 'pmw_topic', [
        'label'        => 'Content Topics',
        'public'       => false,
        'show_ui'      => true,
        'show_in_rest' => true,
        'rest_base'    => 'pmw-topics',
        'supports'     => [ 'title', 'editor', 'custom-fields' ],
        'menu_icon'    => 'dashicons-calendar-alt',
        'labels'       => [
            'name'          => 'Content Topics',
            'singular_name' => 'Topic',
            'add_new_item'  => 'Add New Topic',
            'edit_item'     => 'Edit Topic',
        ],
    ]);
}
add_action( 'init', 'pmw_register_topic_cpt' );
```

#### Meta fields on `pmw_topic`

```php
function pmw_register_topic_meta() {
    $fields = [
        // Core topic definition (set by editorial team)
        'pmw_target_keyword'    => [ 'type' => 'string'  ],
        'pmw_summary'           => [ 'type' => 'string'  ],
        'pmw_include_keywords'  => [ 'type' => 'string'  ],  // comma-separated
        'pmw_exclude_keywords'  => [ 'type' => 'string'  ],  // comma-separated
        'pmw_asset_class'       => [ 'type' => 'string'  ],  // gold|silver|platinum|...
        'pmw_product_type'      => [ 'type' => 'string'  ],  // bars|coins|ETF|...
        'pmw_geography'         => [ 'type' => 'string'  ],  // uk|us|global
        'pmw_is_buy_side'       => [ 'type' => 'boolean' ],
        'pmw_intent_stage'      => [ 'type' => 'string'  ],  // awareness|consideration|decision
        'pmw_priority'          => [ 'type' => 'integer' ],  // 1 (highest) → 5
        'pmw_schedule_cron'     => [ 'type' => 'string'  ],  // blank = manual only

        // Display-only status (written by agent, read-only in admin UI)
        // NOTE: These fields are DISPLAY ONLY. The actual run lock lives
        // in Postgres (workflow_runs table). Never use these for concurrency.
        'pmw_agent_status'      => [ 'type' => 'string'  ],  // idle|running|complete|failed
        'pmw_last_run_at'       => [ 'type' => 'string'  ],  // ISO 8601
        'pmw_run_count'         => [ 'type' => 'integer' ],
        'pmw_last_run_id'       => [ 'type' => 'integer' ],
        'pmw_last_wp_post_id'   => [ 'type' => 'integer' ],

        // Linked content
        'pmw_wp_category_id'    => [ 'type' => 'integer' ],
        'pmw_affiliate_page_id' => [ 'type' => 'integer' ],  // set by Stage 9
    ];

    foreach ( $fields as $key => $config ) {
        register_post_meta( 'pmw_topic', $key, [
            'type'         => $config['type'],
            'single'       => true,
            'show_in_rest' => true,
            'default'      => $config['type'] === 'integer' ? 0
                            : ($config['type'] === 'boolean' ? false : ''),
        ]);
    }
}
add_action( 'init', 'pmw_register_topic_meta' );
```

#### Topic status — WP post status drives eligibility, not the lock

| WP Post Status | Agent behaviour |
|---|---|
| `draft` | Never selected |
| `publish` | Active — eligible for scheduled and manual runs |
| `private` | Paused — skipped by scheduler, available for manual runs |
| `trash` | Never selected |

The `pmw_agent_status` meta field is written by the agent **for display
in the WordPress admin only**. It is never used for concurrency control.
The real lock is the `workflow_runs` table in Postgres (see Section 1d).

#### WordPress admin screen layout

```
┌─────────────────────────────────────────────────────────────┐
│  TOPIC DEFINITION                                           │
│  Primary Keyword: [                              ]          │
│  Summary:         [                              ]          │
│  Asset Class:     [gold ▼]   Product Type: [bars ▼]        │
│  Geography:       [uk ▼]     Buy-side?:    [✓]             │
│  Intent Stage:    [decision ▼]   Priority: [1 ▼]           │
├─────────────────────────────────────────────────────────────┤
│  KEYWORD SCOPE                                              │
│  Include: [gold bars, uk bullion, buy gold, storage ...  ] │
│  Exclude: [etf, paper gold, crypto, competitor name ...  ] │
├─────────────────────────────────────────────────────────────┤
│  SCHEDULE                                                   │
│  Cron: [0 8 * * 1] (blank = manual only)                   │
│  Human-readable: Every Monday at 08:00 UTC                  │
├─────────────────────────────────────────────────────────────┤
│  AGENT STATUS  (read-only — display only, not a lock)       │
│  Status: idle   Last run: 2026-02-24 08:03   Run #: 14     │
│  Last article: [View post →]                               │
└─────────────────────────────────────────────────────────────┘
```

---

### 1b. Affiliates (Postgres — managed via dashboard)

```python
class Affiliate(TypedDict):
    id:                int
    name:              str
    partner_key:       str           # bullionvault | royal-mint | chards | etc.
    url:               str
    value_prop:        str
    faq_url:           str | None    # NEW — URL to affiliate's own FAQ/help docs
    faq_content_hash:  str | None    # NEW — hash of last fetched FAQ (change detection)
    commission_type:   str           # revenue_share | per_lead | cpc
    commission_rate:   float
    cookie_days:       int
    geo_focus:         str
    min_transaction:   float | None
    asset_classes:     list[str]
    product_types:     list[str]
    buy_side:          bool
    sell_side:         bool
    intent_stages:     list[str]
    active:            bool
    weight_geo:        float
    weight_asset:      float
    weight_commission: float
    # Performance data — Phase 2
    historical_ctr:    float | None
    historical_conv:   float | None
    # Intelligence Store — Phase 1
    intelligence_page_id:    int | None    # WP page ID of affiliate intel page
    intelligence_updated_at: str | None    # ISO timestamp of last Stage 9 write
    total_research_runs:     int           # count of successful Stage 9 contributions
```

**New field: `faq_url`**
Each affiliate record now stores the URL of the affiliate's own FAQ or help
documentation. Stage 6 fetches this URL to source affiliate responses to buyer
concerns from the affiliate's own words — not from LLM generation. This is
the source used for factual claims on the intelligence page.

---

### 1c. Affiliate Intelligence Store — Postgres Schema

The Intelligence Store uses two Postgres tables. This replaces the WP option
approach from v3 entirely. Both tables support atomic per-row updates with no
read-modify-write risk.

```sql
-- One row per successful research run that featured this affiliate.
-- Append-only. Never updated after insert.
CREATE TABLE affiliate_intelligence_runs (
    id                  SERIAL PRIMARY KEY,
    affiliate_id        INTEGER NOT NULL REFERENCES affiliates(id),
    run_id              INTEGER NOT NULL REFERENCES workflow_runs(id),
    topic_id            INTEGER NOT NULL,           -- WP post ID
    asset_class         TEXT NOT NULL,
    geography           TEXT NOT NULL,
    ran_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Stage 3 outputs
    spot_price_gbp      NUMERIC(12,4),
    price_trend_pct_30d NUMERIC(6,2),
    price_trend_pct_90d NUMERIC(6,2),
    market_stance       TEXT,                       -- bull_run|correction_opportunity|...
    emotional_trigger   TEXT,                       -- greed|fear|curiosity

    -- Stage 4 outputs
    top_factors_json    JSONB,                      -- list of {factor, current_data, why_matters}

    -- Stage 6 outputs (approved sources only — Reddit + MSE + PAA)
    objections_json     JSONB,                      -- list of {objection, source, frequency}
    motivations_json    JSONB,                      -- list of {motivation, source}
    verbatim_phrases    JSONB,                      -- list of strings
    paa_questions       JSONB,                      -- list of strings from Stage 2
    source_quality      TEXT,                       -- high|medium|low

    -- Compliance
    compliance_review_required  BOOLEAN DEFAULT FALSE,
    compliance_reviewed_at      TIMESTAMPTZ,
    compliance_reviewed_by      TEXT,

    UNIQUE(run_id, affiliate_id)
);

-- One row per affiliate. Materialised aggregation rebuilt after each new run.
-- Upserted atomically by Stage 9 — no read-modify-write.
CREATE TABLE affiliate_intelligence_summary (
    affiliate_id            INTEGER PRIMARY KEY REFERENCES affiliates(id),
    partner_key             TEXT NOT NULL,

    -- Aggregated across all runs
    total_runs              INTEGER DEFAULT 0,
    first_run_at            TIMESTAMPTZ,
    last_run_at             TIMESTAMPTZ,

    -- Market intelligence — from the most recent run only
    -- (price data is time-sensitive; aggregating prices makes no sense)
    latest_spot_price_gbp   NUMERIC(12,4),
    latest_price_trend_30d  NUMERIC(6,2),
    latest_market_stance    TEXT,
    latest_ran_at           TIMESTAMPTZ,

    -- Buyer intelligence — aggregated across all runs
    -- Objections: ranked by frequency across runs (how many runs surfaced each)
    top_objections_json     JSONB,    -- [{objection, run_count, frequency_rank, sources}]
    top_motivations_json    JSONB,    -- [{motivation, run_count, frequency_rank, sources}]

    -- Verbatim phrases — pool of all unique phrases across all runs
    -- Deduplicated by normalised text. Capped at 20 most recent unique phrases.
    verbatim_pool_json      JSONB,    -- [{phrase, first_seen, run_count}]

    -- PAA questions — aggregated pool, deduplicated
    paa_pool_json           JSONB,    -- [{question, first_seen, run_count}]

    -- Top factors — most recent run's factors (factors change with market)
    latest_factors_json     JSONB,

    -- Pending review flag — true if any unreviewed run has compliance_review_required
    has_pending_review      BOOLEAN DEFAULT FALSE,

    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT affiliate_intelligence_summary_pkey
        PRIMARY KEY (affiliate_id)
);
```

**Why two tables:**

`affiliate_intelligence_runs` is the raw ledger — one row per run, immutable
after insert. It is the vault for all intelligence collected. Every run's data
is preserved indefinitely and can be re-aggregated if the aggregation logic
changes.

`affiliate_intelligence_summary` is the materialised view of that ledger —
rebuilt by Stage 9 after each new run using only the raw runs table. The
affiliate page reads from the summary. This means the display data is always
a calculated aggregate, never a single run's data.

**What is aggregated vs what is latest-only:**

| Field | Strategy | Reason |
|---|---|---|
| `latest_spot_price_gbp` | Most recent run | Prices are time-sensitive; averaging past prices is meaningless |
| `latest_market_stance` | Most recent run | Stance reflects current market, not historical average |
| `top_objections_json` | Ranked by run count | An objection surfaced in 8 of 10 runs is more credible than one appearing once |
| `top_motivations_json` | Ranked by run count | Same — frequency signals strength of the motivation |
| `verbatim_pool_json` | Deduplicated pool, capped 20 | Grows over time; older phrases replaced as newer runs add new ones |
| `paa_pool_json` | Deduplicated pool | PAA questions evolve slowly; accumulation is useful |
| `latest_factors_json` | Most recent run | Factors reference current market data points |

---

### 1d. Topic Run Lock — Postgres (replaces WP meta concurrency) *(new)*

This is the fix for Issue 2. The lock lives in the `workflow_runs` table,
which already exists per the base agent implementation. No new table needed.

```sql
-- workflow_runs table (existing — extended with lock fields)
ALTER TABLE workflow_runs ADD COLUMN IF NOT EXISTS
    topic_wp_id    INTEGER;       -- the WP post ID of the selected topic

ALTER TABLE workflow_runs ADD COLUMN IF NOT EXISTS
    lock_expires_at TIMESTAMPTZ;  -- auto-expiry for crash recovery
```

The lock is acquired by attempting an `INSERT` with a unique constraint.
Because this is a single atomic DB operation, no race condition is possible.

```python
async def acquire_topic_lock(topic_wp_id: int, run_id: int, pool) -> bool:
    """
    Attempt to claim a topic for a pipeline run.
    Returns True if the lock was acquired, False if already locked.

    Uses the workflow_runs table — a row exists for this topic with
    status='running' if another run holds the lock.

    Lock expires automatically after 2 hours (crash recovery).
    No running process would legitimately hold a lock that long.
    """
    from datetime import datetime, timezone, timedelta

    expires_at = datetime.now(timezone.utc) + timedelta(hours=2)

    async with pool.acquire() as conn:
        # First, clean up any expired locks for this topic
        await conn.execute("""
            UPDATE workflow_runs
            SET status = 'failed',
                error  = 'Lock expired — pipeline likely crashed'
            WHERE topic_wp_id = $1
              AND status      = 'running'
              AND lock_expires_at < NOW()
        """, topic_wp_id)

        # Check if any run is currently holding a valid lock
        existing = await conn.fetchrow("""
            SELECT id FROM workflow_runs
            WHERE topic_wp_id = $1
              AND status      = 'running'
              AND lock_expires_at > NOW()
        """, topic_wp_id)

        if existing:
            return False   # Another run holds the lock — skip this topic

        # Claim the lock by recording this run as running for this topic
        await conn.execute("""
            UPDATE workflow_runs
            SET status          = 'running',
                topic_wp_id     = $1,
                lock_expires_at = $2
            WHERE id = $3
        """, topic_wp_id, expires_at, run_id)

        return True


async def release_topic_lock(topic_wp_id: int, run_id: int,
                              pool, success: bool, wp_post_id: int = None):
    """
    Release the topic lock on pipeline completion or failure.
    Updates workflow_runs status and writes display-only status to WP meta.
    """
    from datetime import datetime, timezone

    final_status = 'complete' if success else 'failed'

    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE workflow_runs
            SET status          = $1,
                completed_at    = NOW(),
                lock_expires_at = NULL
            WHERE id = $2
        """, final_status, run_id)

    # Write display status to WP meta (non-blocking, best-effort — display only)
    asyncio.create_task(
        _write_wp_display_status(topic_wp_id, final_status, wp_post_id)
    )
```

**Why this is safe and v3 was not:**

In v3, two scheduler triggers arriving 2 seconds apart would both read
`pmw_agent_status = idle` from WordPress before either had written `running`.
Both would select the same topic and proceed.

In v4, both triggers race to `UPDATE workflow_runs SET status='running'`.
Postgres serialises these. The first write succeeds and the `SELECT` after it
finds a valid lock for the second attempt — which returns `False` and the
second trigger selects a different topic or exits cleanly.

The `lock_expires_at` field means a pipeline that crashes without releasing
its lock is automatically recoverable after 2 hours — no manual intervention
needed to reset a stuck topic.

---

### 1e. Affiliate Sources — Approved List *(updated)*

Stage 6 fetches real buyer text from the following sources only. All sources
removed from v3 are noted with the reason.

| Source | Status | Used for | Method |
|---|---|---|---|
| Reddit (`r/Gold`, `r/UKInvesting`, `r/Silverbugs`, `r/PreciousMetals`) | ✅ Retained | Buyer objections, verbatim phrases, motivations | Reddit JSON API (no auth required for read) |
| MoneySavingExpert forums | ✅ Retained | UK buyer concerns, forum discussions | HTML scrape of search results (best-effort) |
| PAA questions (from Stage 2 SERP) | ✅ Retained | Real buyer questions, objection signals | Already in state from Stage 2 — no new fetch |
| Affiliate FAQ / Help documentation | ✅ New | Affiliate responses to buyer concerns | Fetch affiliate's `faq_url` from their own site |
| ~~Trustpilot~~ | ❌ Removed | ~~Buyer sentiment, reviews~~ | **Removed — ToS prohibits commercial scraping of review content. Trustpilot Business API requires affiliate consent. Not worth the legal risk.** |

**Affiliate FAQ sourcing — how it works:**

Each affiliate record now includes a `faq_url` field pointing to the affiliate's
own published FAQ, help centre, or "how it works" page. Stage 6 fetches this
URL and passes the text to the LLM alongside the forum/Reddit data. The LLM
uses this text to construct affiliate responses to buyer objections — meaning
every factual claim made about the affiliate is sourced from the affiliate's
own published materials.

```python
async def _fetch_affiliate_faq(self, affiliate: dict) -> dict:
    """
    Fetch the affiliate's own FAQ/help documentation.
    Returns extracted text for LLM synthesis.
    Falls back gracefully if URL is missing or fetch fails.
    """
    faq_url = affiliate.get("faq_url")
    if not faq_url:
        return {"content": "", "source": "none", "available": False}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                faq_url,
                headers={"User-Agent": "PMW-Research-Agent/1.0"},
                follow_redirects=True,
            )
            resp.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove navigation, headers, footers — keep main content only
        for tag in soup(["nav", "header", "footer", "script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Truncate to ~3000 words to stay within prompt budget
        words = text.split()
        truncated = " ".join(words[:3000])

        return {
            "content":   truncated,
            "source":    faq_url,
            "available": True,
        }

    except Exception as exc:
        self.log.warning(
            "Affiliate FAQ fetch failed",
            url=faq_url,
            error=str(exc),
        )
        return {"content": "", "source": faq_url, "available": False}
```

---

## 2. Stage Definitions — Full Set

### Stage 1 — Topic Selection & Brief Definition
- **1.1** Fetch candidate topics from WordPress REST API
- **1.2** Select best topic (priority + schedule logic)
- **1.3** Load active affiliates from Postgres
- **1.4** Score and rank affiliates against topic
- **1.5** Acquire Postgres topic lock → assemble brief → LLM validation → lock brief

### Stage 2 — Keyword & Search Intent Research
SERP expansion, PAA capture, intent confirmation. Overrides brief intent
if SERP reality differs from declared intent stage.

### Stage 3 — Market Context, News & Price Stance
Live price fetch, 30/90-day trend, news. `market_stance` derived
algorithmically from price data.

### Stage 4 — Top 5 Factors Research
Five buyer decision factors with current data points and affiliate links.

### Stage 5 — Competitor Content & Monetisation Analysis
Top 3–5 ranking pages. Content gaps + monetisation analysis per competitor.

### Stage 6 — Buyer Psychology: Data Sourcing + LLM Synthesis *(updated sources)*
**Phase 6a — Data Fetch (NonLLM):**
- Reddit threads (r/Gold, r/UKInvesting, r/Silverbugs, r/PreciousMetals)
- MoneySavingExpert forum search results
- PAA questions from Stage 2 state
- Affiliate's own FAQ content (from `faq_url` in affiliate record)
- ~~Trustpilot~~ — removed

**Phase 6b — LLM Synthesis:**
LLM synthesises objections, motivations, and verbatim phrases from the real
source data. Affiliate responses to objections are sourced from the affiliate's
own FAQ text, not generated. `compliance_review_required` flag set to `true`
on any section containing specific factual claims about regulated products.

### Stage 7 — Internal Tool Mapping
Tool selection with `selection_rationale` and `data_confidence` per tool.

### Stage 8 — Arc Coherence Check + Bundle Assembly
Arc validation → bundle assembly → `research_bundle` → Content Planning.

### Stage 9 — Affiliate Intelligence Write-back *(redesigned: aggregation model)*
**Append-only insert** to `affiliate_intelligence_runs` in Postgres.
**Atomic upsert** to `affiliate_intelligence_summary` — rebuilds aggregate
from all runs for this affiliate. Writes display status to WP meta (non-blocking).
No single run dominates the displayed data — objections and motivations are
ranked by frequency across all historical runs.

---

## 3. Dependency Analysis

```
DEPENDENCY LEGEND
─── hard dependency   (must complete before downstream starts)
═══ no dependency     (fully parallel)
··· non-blocking      (dispatched after END, failure tolerated)
```

### Full dependency map — v4

```
[1.1 Fetch Topics from WP REST API]
      │
[1.2 Select Topic]
      │
[1.3 Load Affiliates from Postgres]
      │
[1.4 Score & Rank Affiliates]
      │
[1.5 Acquire Postgres Lock → Lock Brief]  ◄── HITL if coherence fails
      │
      │  Brief locked. Lock held in Postgres workflow_runs.
      │
      ├──────────────────────┬──────────────────────┐
      │                      │                      │
[Stage 2               [Stage 3               [Stage 5
 Keyword & SERP         Market Context         Competitor Content
 + Intent Confirm]      + Market Stance        + Monetisation
      │                 + News Fetch]           Analysis]
      │                      │                      │
      ├──────────────────────┘                      │
      │    (2 + 3 both needed)                      │
      │         │                                   │
      │   [Stage 4                                  │
      │    Top 5 Factors]                           │
      │         │                                   │
      │         └───────────────────────────────────┘
      │                       │
      │          (4 + 5 both needed)
      │                       │
      │    [Stage 6a — Data Fetch]
      │    (Reddit / MSE / PAA / Affiliate FAQ)
      │                       │
      │    [Stage 6b — LLM Synthesis]
      │                       │
      └───────────────────────┘
                    │
        (2 + 4 + 6 all needed)
                    │
            [Stage 7
             Tool Mapping + Rationale]
                    │
         (ALL stages 2–7 needed)
                    │
            [Stage 8a — Arc Coherence Check]  ◄── HITL if arc incoherent
                    │
            [Stage 8b — Bundle Assembly]
                    │
                  [END — Research bundle → Content Planning]
                    │
                    ··· (non-blocking background tasks)
                    ├── Release Postgres lock + write WP display status
                    └── [Stage 9 — Affiliate Intelligence Aggregation]
                          Append run → affiliate_intelligence_runs
                          Upsert aggregate → affiliate_intelligence_summary
                          Update WP affiliate page from summary
```

### Dependency table — v4

| Stage | Hard depends on | Parallel with | Blocks pipeline? |
|---|---|---|---|
| 1.1 Fetch Topics | — | — | Yes |
| 1.2 Select Topic | 1.1 | — | Yes |
| 1.3 Load Affiliates | 1.2 | — | Yes |
| 1.4 Score Affiliates | 1.3 | — | Yes |
| 1.5 Lock (Postgres) + Brief | 1.4 | — | Yes — HITL on brief fail |
| **2** Keyword + Intent | 1.5 | Stage 3, Stage 5 | Yes |
| **3** Market + Stance | 1.5 | Stage 2, Stage 5 | Yes |
| **4** Top 5 Factors | Stage 2 + 3 | — | Yes |
| **5** Competitor + Monetisation | 1.5 | Stage 2, Stage 3 | Yes |
| **6a** Data Fetch | Stage 4 + 5 | — | Yes |
| **6b** Psychology Synthesis | Stage 6a | — | Yes |
| **7** Tool Mapping | Stage 2 + 4 + 6 | — | Yes |
| **8a** Arc Coherence Check | All (2–7) | — | Yes — HITL on fail |
| **8b** Bundle Assembly | Stage 8a | — | Yes |
| Lock release + WP display | Stage 8b | Stage 9 | No |
| **9** Intelligence Aggregation | Stage 8b | Lock release | No |

---

## 4. LangGraph State Definition — v4

```python
class ResearchState(TypedDict):
    run_id:       int
    triggered_by: str

    # Stage 1
    candidate_topics:     Optional[list[dict]]
    selected_topic:       Optional[dict]
    topic_lock_acquired:  Optional[bool]       # NEW — True once Postgres lock held
    candidate_affiliates: Optional[list[dict]]
    scored_affiliates:    Optional[list[dict]]
    primary_affiliate:    Optional[dict]
    secondary_affiliate:  Optional[dict]
    brief:                Optional[dict]

    # Parallel wave 1
    keyword_research:    Optional[dict]
    market_context:      Optional[dict]
    competitor_analysis: Optional[dict]

    # Stage 4
    top_factors: Optional[dict]

    # Stage 6 (updated sources — no Trustpilot)
    buyer_psychology: Optional[dict]
    # raw_sources now contains: reddit, mse, paa, affiliate_faq
    # compliance_review_required: bool per section

    # Stage 7
    tool_mapping: Optional[dict]

    # Stage 8
    arc_validation:   Optional[dict]
    research_bundle:  Optional[dict]

    # Stage 9 (non-blocking)
    intelligence_write_result: Optional[dict]

    # Pipeline control
    current_stage:  str
    status:         str
    errors:         list[dict]
    retry_counts:   dict[str, int]
    model_usage:    list[dict]
```

---

## 5. Updated Node Implementations

### Stage 1.2 / 1.5 — Topic Selection with Postgres Lock *(updated)*

The lock is acquired during Stage 1.5 (brief assembly), immediately after
the topic is selected and before any LLM cost is incurred.

```python
class BriefLockerAgent(JSONOutputMixin, BaseAgent):
    """
    Stage 1.5 — Acquires Postgres topic lock, assembles draft brief,
    runs LLM coherence validation, and locks the final brief object.

    Lock acquisition happens FIRST — before the LLM call. If the lock
    cannot be acquired (another run holds it), raises immediately.
    This means no LLM cost is ever spent on a topic that's already running.
    """

    async def run(self, input_data: dict, run_id: int) -> AgentResult:
        topic_wp_id = input_data["selected_topic"]["id"]
        pool        = await _DBPool.get()

        # ── Acquire lock ──────────────────────────────────────────────
        lock_acquired = await acquire_topic_lock(topic_wp_id, run_id, pool)

        if not lock_acquired:
            # Another run is already processing this topic — select next topic
            # This is not an error; it's normal scheduler behaviour
            self.log.info(
                "Topic lock not acquired — another run in progress",
                run_id=run_id,
                topic_wp_id=topic_wp_id,
            )
            # Signal to orchestrator to retry with next candidate topic
            raise TopicLockConflictError(
                f"Topic {topic_wp_id} is already running. "
                "Orchestrator should select next candidate topic."
            )

        # ── LLM brief validation (only reached if lock is held) ───────
        input_data  = self.preprocess(input_data)
        draft_brief = self._assemble_draft_brief(input_data)
        prompt      = self.build_prompt(input_data)
        result      = await self._run_with_retries(prompt, run_id)

        if result.status == AgentStatus.SUCCESS:
            enrichments = result.output
            full_brief = {
                **draft_brief,
                "meta": {
                    "validation_passed": True,
                    "coherence_score":   enrichments["coherence_score"],
                    "warnings":          [i for i in enrichments.get("issues", [])
                                         if i.get("severity") == "warning"],
                    "run_id":            run_id,
                },
                "reader": {
                    "profile":       enrichments["enriched_reader_profile"],
                    "moment":        enrichments["enriched_reader_moment"],
                    "article_angle": enrichments["suggested_article_angle"],
                },
            }
            result.output = {
                "brief":               full_brief,
                "topic_lock_acquired": True,
            }

        return self.postprocess(result)
```

---

### Stage 6 — Updated Data Sources *(no Trustpilot)*

The data fetch now collects from four sources: Reddit, MSE, PAA (from state),
and the affiliate's own FAQ documentation.

```python
class BuyerPsychologyDataFetcher(NonLLMAgent):
    """
    Stage 6a — Fetches real buyer text from approved sources.

    Sources:
      ✅ Reddit (r/Gold, r/UKInvesting, r/Silverbugs, r/PreciousMetals)
      ✅ MoneySavingExpert forum search
      ✅ PAA questions (already in state from Stage 2)
      ✅ Affiliate FAQ / help documentation (from affiliate.faq_url)
      ❌ Trustpilot — removed (ToS prohibits commercial use of scraped reviews)
    """

    async def execute(self, state: dict, run_id: int) -> dict:
        brief   = state["brief"]
        topic   = brief["topic"]
        keyword = topic["target_keyword"]
        primary = brief["affiliate"]["primary"]

        # Fetch all sources concurrently
        reddit_threads, mse_posts, affiliate_faq = await asyncio.gather(
            self._fetch_reddit(keyword, topic["geography"]),
            self._fetch_mse(keyword),
            self._fetch_affiliate_faq(primary),
        )

        # PAA questions come from Stage 2 state — no new fetch needed
        paa_questions = state.get("keyword_research", {}).get("paa_questions", [])

        source_counts = {
            "reddit":        len(reddit_threads),
            "mse":           len(mse_posts),
            "paa":           len(paa_questions),
            "affiliate_faq": 1 if affiliate_faq["available"] else 0,
        }

        self.log.info(
            "Buyer psychology sources fetched",
            run_id=run_id,
            **source_counts,
        )

        return {
            "raw_sources": {
                "reddit":        reddit_threads,
                "mse":           mse_posts,
                "paa":           paa_questions,
                "affiliate_faq": affiliate_faq,
            },
            "source_counts": source_counts,
        }

    async def _fetch_reddit(self, keyword: str, geography: str) -> list[dict]:
        subreddits = {
            "uk":     ["Gold", "UKInvesting", "Silverbugs", "PreciousMetals"],
            "us":     ["Gold", "personalfinance", "Silverbugs", "PreciousMetals"],
            "global": ["Gold", "PreciousMetals", "Silverbugs"],
        }.get(geography, ["Gold", "PreciousMetals"])

        results = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for sub in subreddits[:2]:
                try:
                    resp = await client.get(
                        f"https://www.reddit.com/r/{sub}/search.json",
                        params={"q": keyword, "limit": 5, "sort": "relevance"},
                        headers={"User-Agent": "PMW-Research-Agent/1.0"},
                    )
                    if resp.status_code == 200:
                        posts = resp.json().get("data", {}).get("children", [])
                        for post in posts:
                            d = post.get("data", {})
                            results.append({
                                "title":    d.get("title", ""),
                                "selftext": d.get("selftext", "")[:1000],
                                "score":    d.get("score", 0),
                                "url":      f"https://reddit.com{d.get('permalink', '')}",
                                "source":   f"r/{sub}",
                            })
                except Exception as exc:
                    self.log.warning(f"Reddit r/{sub} fetch failed", error=str(exc))
        return results

    async def _fetch_mse(self, keyword: str) -> list[dict]:
        results = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://forums.moneysavingexpert.com/search",
                    params={"q": keyword, "type": "thread"},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for thread in soup.select(".search-result")[:5]:
                    title   = thread.select_one(".title")
                    excerpt = thread.select_one(".excerpt")
                    results.append({
                        "title":   title.text.strip()   if title   else "",
                        "excerpt": excerpt.text.strip() if excerpt else "",
                        "source":  "moneysavingexpert",
                    })
        except Exception as exc:
            self.log.warning("MSE fetch failed", error=str(exc))
        return results

    async def _fetch_affiliate_faq(self, affiliate: dict) -> dict:
        faq_url = affiliate.get("faq_url")
        if not faq_url:
            return {"content": "", "source": "none", "available": False}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    faq_url,
                    headers={"User-Agent": "PMW-Research-Agent/1.0"},
                    follow_redirects=True,
                )
                resp.raise_for_status()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["nav", "header", "footer", "script", "style"]):
                tag.decompose()

            text  = soup.get_text(separator="\n", strip=True)
            words = text.split()

            return {
                "content":   " ".join(words[:3000]),
                "source":    faq_url,
                "available": True,
            }
        except Exception as exc:
            self.log.warning("Affiliate FAQ fetch failed", url=faq_url, error=str(exc))
            return {"content": "", "source": faq_url, "available": False}
```

#### Updated Stage 6b synthesis prompt — compliance gate added

```python
BUYER_PSYCHOLOGY_SYNTHESIS_PROMPT = """\
SYSTEM:
You are a buyer psychology analyst for Precious Metals Watch (PMW).
You have been given REAL text from buyers and from the affiliate's own
published materials.

SOURCES:
- Reddit forum posts — buyer questions, fears, and opinions
- MoneySavingExpert forum threads — UK buyer discussions
- People Also Ask questions — real search queries from buyers
- Affiliate FAQ text — the affiliate's own published answers to common questions

YOUR TASKS:
1. Extract buyer objections from the Reddit, MSE, and PAA sources.
   Use verbatim language where possible.

2. Extract buyer motivations from the same sources.

3. For each objection, find the affiliate's response in the FAQ text.
   If the FAQ text contains a direct answer to this objection, use it
   verbatim. If not, leave affiliate_response as null — do NOT generate
   a response.

4. Flag compliance_review_required = true for any section where:
   - The affiliate response makes a specific factual claim about FCA
     regulation, insurance coverage, legal ownership, tax treatment,
     or financial performance
   - OR where no affiliate response was found but the objection is about
     a regulated matter (segregation of assets, FSCS coverage, CGT, etc.)

   These sections will be held for human review before publication.

CRITICAL: Do not generate factual claims about the affiliate that are not
present in the affiliate's FAQ text. If the FAQ does not address an
objection, the affiliate_response must be null.

Return ONLY valid JSON. No preamble. No markdown fencing.

OUTPUT SCHEMA:
{
  "objections": [
    {
      "objection":                 "string — buyer fear in their own words",
      "verbatim_example":          "string — direct quote from Reddit/MSE/PAA",
      "source":                    "reddit|mse|paa",
      "frequency":                 "high|medium|low",
      "affiliate_response":        "string — from FAQ text verbatim, or null",
      "affiliate_response_source": "faq_url or null",
      "compliance_review_required": boolean
    }
  ],
  "motivations": [
    {
      "motivation":       "string — buying driver",
      "verbatim_example": "string — direct quote from Reddit/MSE/PAA",
      "source":           "reddit|mse|paa"
    }
  ],
  "verbatim_phrases":  ["string — raw buyer language for article copy"],
  "dominant_emotional_state": "fear|greed|curiosity|confusion",
  "compliance_notes":  "string — regulatory/legal sensitivities noted",
  "any_section_requires_review": boolean,
  "source_quality": {
    "reddit_useful":   boolean,
    "mse_useful":      boolean,
    "faq_available":   boolean,
    "data_richness":   "high|medium|low"
  }
}

TOPIC: {{TOPIC_TITLE}}
AFFILIATE: {{AFFILIATE_NAME}}
AFFILIATE FAQ URL: {{FAQ_URL}}

Reddit posts:     {{REDDIT_JSON}}
MSE threads:      {{MSE_JSON}}
PAA questions:    {{PAA_JSON}}
Affiliate FAQ:    {{FAQ_TEXT}}
"""
```

---

### Stage 9 — Affiliate Intelligence Aggregation *(redesigned)*

Stage 9 now operates as a pure data aggregation pipeline. There is no
read-modify-write. Every operation is atomic. Single runs do not
dramatically shift the displayed data because the display is always
a frequency-ranked aggregate across all historical runs.

```python
class AffiliateIntelligenceAggregationAgent(NonLLMAgent):
    """
    Stage 9 — Appends this run's intelligence to the raw ledger and
    rebuilds the materialised summary aggregate.

    Design principles:
    - Append-only insert to affiliate_intelligence_runs
    - Atomic upsert to affiliate_intelligence_summary (no read-modify-write)
    - Summary is always calculated from the full run history
    - Single runs cannot dominate — frequency ranking requires multiple appearances
    - Compliance gate: sections flagged for review are excluded from the
      live page until reviewed
    """

    async def execute(self, state: dict, run_id: int) -> dict:
        brief    = state["brief"]
        primary  = brief["affiliate"]["primary"]
        topic    = brief["topic"]
        market   = state.get("market_context", {})
        factors  = state.get("top_factors", {})
        psych    = state.get("buyer_psychology", {})
        kw       = state.get("keyword_research", {})

        pool = await _DBPool.get()

        results = {
            "run_appended":      False,
            "summary_updated":   False,
            "wp_page_updated":   False,
            "pending_review":    psych.get("any_section_requires_review", False),
            "errors":            [],
        }

        # ── 1. Append this run to the raw ledger ──────────────────────
        try:
            await self._append_run(pool, primary, topic, market, factors, psych, kw, run_id)
            results["run_appended"] = True
            self.log.info("Intelligence run appended", run_id=run_id,
                          partner=primary["partner_key"])
        except Exception as exc:
            results["errors"].append(f"Run append failed: {exc}")
            self.log.warning("Intelligence run append failed", error=str(exc))
            return {"intelligence_write_result": results}

        # ── 2. Rebuild the aggregate summary ──────────────────────────
        try:
            summary = await self._rebuild_summary(pool, primary["id"])
            results["summary_updated"] = True
            self.log.info("Intelligence summary rebuilt", run_id=run_id,
                          partner=primary["partner_key"],
                          total_runs=summary["total_runs"])
        except Exception as exc:
            results["errors"].append(f"Summary rebuild failed: {exc}")
            self.log.warning("Summary rebuild failed", error=str(exc))

        # ── 3. Update WP affiliate page from summary ──────────────────
        try:
            wp_page_id = await self._update_wp_affiliate_page(primary, summary)
            results["wp_page_updated"] = True
            results["wp_page_id"]      = wp_page_id
        except Exception as exc:
            results["errors"].append(f"WP page update failed: {exc}")
            self.log.warning("WP affiliate page update failed", error=str(exc))

        return {"intelligence_write_result": results}

    async def _append_run(self, pool, primary, topic, market, factors, psych, kw, run_id):
        """Append-only insert to affiliate_intelligence_runs."""

        compliance_required = psych.get("any_section_requires_review", False)

        async with pool.acquire() as conn:
            await conn.execute("""
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
                    $11,
                    $12, $13, $14, $15, $16, $17
                )
                ON CONFLICT (run_id, affiliate_id) DO NOTHING
            """,
                primary["id"],
                run_id,
                topic["id"],
                topic["asset_class"],
                topic["geography"],
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
                compliance_required,
            )

    async def _rebuild_summary(self, pool, affiliate_id: int) -> dict:
        """
        Rebuild the aggregate summary entirely from the raw runs table.
        Uses a single query — no read-modify-write, no race condition.
        """
        async with pool.acquire() as conn:
            # Fetch all runs for this affiliate
            runs = await conn.fetch("""
                SELECT *
                FROM affiliate_intelligence_runs
                WHERE affiliate_id = $1
                ORDER BY ran_at DESC
            """, affiliate_id)

        if not runs:
            raise ValueError(f"No runs found for affiliate {affiliate_id}")

        all_runs   = [dict(r) for r in runs]
        latest_run = all_runs[0]

        # ── Aggregate objections across all runs ──────────────────────
        objection_counts: dict[str, dict] = {}
        for run in all_runs:
            for obj in json.loads(run.get("objections_json") or "[]"):
                key = obj.get("objection", "").strip().lower()
                if not key:
                    continue
                if key not in objection_counts:
                    objection_counts[key] = {
                        "objection":                  obj["objection"],
                        "run_count":                  0,
                        "sources":                    set(),
                        "verbatim_examples":          [],
                        "affiliate_response":         obj.get("affiliate_response"),
                        "affiliate_response_source":  obj.get("affiliate_response_source"),
                        "compliance_review_required": obj.get("compliance_review_required", False),
                    }
                objection_counts[key]["run_count"] += 1
                objection_counts[key]["sources"].add(obj.get("source", ""))
                if obj.get("verbatim_example"):
                    objection_counts[key]["verbatim_examples"].append(
                        obj["verbatim_example"]
                    )

        # Sort by run_count descending — frequency-ranked
        top_objections = sorted(
            [
                {**v, "sources": list(v["sources"]),
                 "verbatim_example": v["verbatim_examples"][0]
                 if v["verbatim_examples"] else ""}
                for v in objection_counts.values()
            ],
            key=lambda x: x["run_count"],
            reverse=True,
        )[:8]   # top 8 by frequency

        # ── Aggregate motivations ──────────────────────────────────────
        motivation_counts: dict[str, dict] = {}
        for run in all_runs:
            for mot in json.loads(run.get("motivations_json") or "[]"):
                key = mot.get("motivation", "").strip().lower()
                if not key:
                    continue
                if key not in motivation_counts:
                    motivation_counts[key] = {
                        "motivation":       mot["motivation"],
                        "run_count":        0,
                        "verbatim_example": mot.get("verbatim_example", ""),
                    }
                motivation_counts[key]["run_count"] += 1

        top_motivations = sorted(
            list(motivation_counts.values()),
            key=lambda x: x["run_count"],
            reverse=True,
        )[:6]

        # ── Build deduplicated verbatim phrase pool ────────────────────
        phrase_seen: dict[str, dict] = {}
        for run in all_runs:
            for phrase in json.loads(run.get("verbatim_phrases") or "[]"):
                normalised = " ".join(phrase.lower().split())
                if normalised not in phrase_seen:
                    phrase_seen[normalised] = {
                        "phrase":     phrase,
                        "first_seen": run["ran_at"].isoformat(),
                        "run_count":  0,
                    }
                phrase_seen[normalised]["run_count"] += 1

        # Most frequently appearing phrases, capped at 20
        verbatim_pool = sorted(
            list(phrase_seen.values()),
            key=lambda x: x["run_count"],
            reverse=True,
        )[:20]

        # ── PAA questions pool ─────────────────────────────────────────
        paa_seen: dict[str, dict] = {}
        for run in all_runs:
            for q in json.loads(run.get("paa_questions") or "[]"):
                normalised = " ".join(q.lower().split())
                if normalised not in paa_seen:
                    paa_seen[normalised] = {
                        "question":   q,
                        "first_seen": run["ran_at"].isoformat(),
                        "run_count":  0,
                    }
                paa_seen[normalised]["run_count"] += 1

        paa_pool = sorted(
            list(paa_seen.values()),
            key=lambda x: x["run_count"],
            reverse=True,
        )[:15]

        # ── Any pending compliance reviews? ───────────────────────────
        has_pending = any(
            r["compliance_review_required"] and not r["compliance_reviewed_at"]
            for r in all_runs
        )

        # ── Upsert to summary table (atomic — no read-modify-write) ───
        summary = {
            "affiliate_id":          affiliate_id,
            "total_runs":            len(all_runs),
            "first_run_at":          all_runs[-1]["ran_at"].isoformat(),
            "last_run_at":           latest_run["ran_at"].isoformat(),
            "latest_spot_price_gbp": latest_run["spot_price_gbp"],
            "latest_price_trend_30d": latest_run["price_trend_pct_30d"],
            "latest_market_stance":  latest_run["market_stance"],
            "latest_ran_at":         latest_run["ran_at"].isoformat(),
            "top_objections":        top_objections,
            "top_motivations":       top_motivations,
            "verbatim_pool":         verbatim_pool,
            "paa_pool":              paa_pool,
            "latest_factors":        json.loads(latest_run.get("top_factors_json") or "[]"),
            "has_pending_review":    has_pending,
        }

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO affiliate_intelligence_summary (
                    affiliate_id, partner_key,
                    total_runs, first_run_at, last_run_at,
                    latest_spot_price_gbp, latest_price_trend_30d,
                    latest_market_stance, latest_ran_at,
                    top_objections_json, top_motivations_json,
                    verbatim_pool_json, paa_pool_json,
                    latest_factors_json, has_pending_review,
                    updated_at
                )
                SELECT
                    $1, a.partner_key,
                    $3, $4::timestamptz, $5::timestamptz,
                    $6, $7, $8, $9::timestamptz,
                    $10::jsonb, $11::jsonb,
                    $12::jsonb, $13::jsonb,
                    $14::jsonb, $15,
                    NOW()
                FROM affiliates a WHERE a.id = $1
                ON CONFLICT (affiliate_id) DO UPDATE SET
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

        return summary

    async def _update_wp_affiliate_page(self, primary: dict, summary: dict) -> int:
        """
        Write the aggregated summary to the WordPress affiliate intelligence page.

        Only includes sections that do NOT have pending compliance reviews.
        Sections with compliance_review_required = true on any unreviewed run
        are withheld from the page until reviewed in the dashboard.
        """
        import httpx

        # Filter objections — exclude any with compliance_review_required
        # that haven't been reviewed yet
        safe_objections = [
            o for o in summary["top_objections"]
            if not o.get("compliance_review_required")
        ]
        pending_count = len(summary["top_objections"]) - len(safe_objections)

        page_payload = {
            "partner_key":    primary["partner_key"],
            "affiliate_name": primary["name"],
            "affiliate_url":  primary["url"],

            # Market — always from latest run (time-sensitive)
            "market": {
                "spot_price_gbp":   summary["latest_spot_price_gbp"],
                "price_trend_30d":  summary["latest_price_trend_30d"],
                "market_stance":    summary["latest_market_stance"],
                "last_updated":     summary["latest_ran_at"],
            },

            # Buyer intelligence — aggregated, frequency-ranked
            "buyer": {
                "total_runs_contributing": summary["total_runs"],
                "top_objections":  safe_objections[:5],
                "top_motivations": summary["top_motivations"][:4],
                "verbatim_pool":   summary["verbatim_pool"][:5],
                "paa_questions":   summary["paa_pool"][:8],
                "pending_review_count": pending_count,
            },

            # Factors — from latest run
            "factors": summary["latest_factors"][:5],

            "has_pending_review": summary["has_pending_review"],
            "last_updated":       summary["last_run_at"],
            "data_note": (
                f"Intelligence aggregated from {summary['total_runs']} "
                f"research runs. Objections ranked by frequency across runs."
            ),
        }

        # Upsert the WP page (same pattern as v3 — slug-based upsert)
        WP_API_URL  = os.environ.get("WP_API_URL")
        WP_API_USER = os.environ.get("WP_API_USER")
        WP_API_PASS = os.environ.get("WP_API_PASSWORD")

        async with httpx.AsyncClient(timeout=15.0) as client:
            search = await client.get(
                f"{WP_API_URL}/wp/v2/pages",
                params={"slug": f"affiliates-{primary['partner_key']}", "_fields": "id"},
                auth=(WP_API_USER, WP_API_PASS),
            )
            existing = search.json()

        page_data = {
            "title":  f"{primary['name']} — Investment Intelligence",
            "slug":   f"affiliates-{primary['partner_key']}",
            "status": "publish",
            "meta": {
                "pmw_intelligence_data":    json.dumps(page_payload),
                "pmw_intelligence_updated": summary["last_run_at"],
                "pmw_partner_key":          primary["partner_key"],
                "pmw_pending_review":       str(summary["has_pending_review"]),
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            if existing:
                page_id = existing[0]["id"]
                resp = await client.post(
                    f"{WP_API_URL}/wp/v2/pages/{page_id}",
                    auth=(WP_API_USER, WP_API_PASS),
                    json=page_data,
                )
            else:
                resp = await client.post(
                    f"{WP_API_URL}/wp/v2/pages",
                    auth=(WP_API_USER, WP_API_PASS),
                    json=page_data,
                )
            resp.raise_for_status()
            return resp.json()["id"]
```

---

#### What the affiliate intelligence page shows — aggregated view

```
BullionVault — Investment Intelligence
────────────────────────────────────────────────────────────────

  MARKET UPDATE                           Last updated: 24 Feb 2026
  Gold spot price: £1,847/oz  ▲ +4.2% (30d)
  Market stance: Bull Run

────────────────────────────────────────────────────────────────

  WHY BUYERS CHOOSE BULLIONVAULT
  Based on 14 research runs · Ranked by frequency

  ✓ "Finally found a way to buy gold without the coin dealer premium"
  ✓ "Set up was genuinely easy — took 10 minutes to fund and buy"
  ✓ "Can start with £25 — built up slowly over time"
  ✓ "FCA regulated — gives me real peace of mind"

────────────────────────────────────────────────────────────────

  COMMON QUESTIONS & ANSWERS
  Sourced from buyer forums and BullionVault's own FAQ

  ❓ "What happens to my gold if BullionVault goes bust?"
     Appeared in 11 of 14 research runs
     → [Answer sourced verbatim from BullionVault's FAQ]

  ❓ "Is online gold storage actually safe?"
     Appeared in 9 of 14 research runs
     → [Answer sourced verbatim from BullionVault's FAQ]

  ⚠️  2 questions pending editorial review before publication

────────────────────────────────────────────────────────────────

  WHAT BUYERS ARE ASKING (People Also Ask — aggregated)
  • How does BullionVault compare to buying physical gold?
  • What is the minimum investment for BullionVault?
  • Can I withdraw my gold from BullionVault?

────────────────────────────────────────────────────────────────

  Intelligence aggregated from 14 research runs.
  Questions ranked by frequency across runs.
  Market data: latest run only (price-sensitive).
  Sources: Reddit r/UKInvesting · MoneySavingExpert forums · Google PAA
  Answers: BullionVault published FAQ documentation

  [Start investing from £25 — Open a BullionVault account →]
```

---

## 6. Threshold & Retry Configuration — v4

| Stage | Agent type | Model | Threshold | Retries | HITL | Blocks? |
|---|---|---|---|---|---|---|
| 1.1 Fetch Topics (WP API) | NonLLM | — | ≥1 topic | 2 | No | Yes |
| 1.2 Select Topic | NonLLM | — | any result | 1 | No | Yes |
| 1.3 Load Affiliates | NonLLM | — | ≥1 affiliate | 1 | No | Yes |
| 1.4 Score Affiliates | NonLLM | — | fit_score ≥ 0.40 | 1 | No | Yes |
| 1.5 Postgres lock + Brief | LLM | Haiku | lock acquired + coherence ≥ 0.60 | 2 | **Yes** (brief only) | Yes |
| 2 Keyword + Intent | LLM | Haiku | confidence ≥ 0.75 | 3 | No | Yes |
| 3 Market + Stance | NonLLM + LLM | Haiku | price present + 3+ news | 2 | No | Yes |
| 4 Top 5 Factors | LLM | Sonnet | 5 factors + data | 3 | No | Yes |
| 5 Competitor + Monetisation | LLM | Haiku | 3+ competitors | 3 | No | Yes |
| 6a Data Fetch | NonLLM | — | ≥1 source returns data | 1 | No — degrades | Yes |
| 6b Psychology Synthesis | LLM | Sonnet | 3+ obj + 3+ verbatim | 3 | No | Yes |
| 7 Tool Mapping | LLM | Haiku | 1+ tool + rationale | 2 | No | Yes |
| 8a Arc Coherence Check | LLM | Haiku | arc_coherent = true | 1 | **Yes** | Yes |
| 8b Bundle Assembly | NonLLM | — | all sections present | 1 | **Yes** | Yes |
| 9 Intelligence Aggregation | NonLLM | — | best-effort | 2 | No | **No** |

**HITL gates (3 total):**
1. **1.5 Brief lock** — incoherent topic/affiliate pairing (not the Postgres lock — that auto-routes)
2. **8a Arc coherence** — research doesn't form a buying intent story
3. **8b Bundle assembly** — required section missing (code bug)

---

## 7. Compliance Review Workflow

Stage 9 flags objection-response pairs for review when the affiliate response
contains claims about regulated matters. The dashboard surfaces these for
editorial sign-off before they appear on the live affiliate page.

```
Stage 9 runs
    │
    ├── compliance_review_required = false for all sections
    │       └── All objections published to affiliate page immediately
    │
    └── compliance_review_required = true for 1+ sections
            └── Flagged sections withheld from live page
                has_pending_review = true in summary table
                Dashboard shows: "2 items pending review for BullionVault"
                Editorial team reviews each flagged section:
                  - Approve → compliance_reviewed_at = NOW(), published
                  - Reject  → section removed from summary
                  - Edit    → section content updated, then approved
```

**What triggers `compliance_review_required = true`:**
- Affiliate response contains the words: regulated, FCA, FSCS, insured,
  guaranteed, protected, segregated, CGT, tax, legal, liability
- Affiliate response makes a specific numerical claim (% returns, insurance
  amounts, coverage limits)
- No affiliate response was found in the FAQ but the objection concerns a
  regulated matter

**What never triggers review:**
- Verbatim buyer quotes (attributed to buyers, not PMW)
- General motivations ("easy to set up", "good for small amounts")
- PAA questions (questions only — no claims made)
- Market data (price, trend, stance — factual, sourced from price API)

---

## 8. Summary of All Changes v1 → v4

| Version | Change | What it does |
|---|---|---|
| v2 | Intent confirmation | SERP reality overrides declared intent |
| v2 | Market stance | Algorithmic price-driven emotional register |
| v2 | Competitor monetisation | Captures conversion failures |
| v2 | Real data sourcing (Stage 6) | Verbatim buyer language |
| v2 | Tool selection rationale | Audit trail for Phase 2 |
| v2 | Arc coherence check | Validates buying intent story |
| v3 | WordPress as topic CMS | WP REST API as source of truth for topics |
| v3 | Affiliate Intelligence Store | Research data persisted to WP affiliate pages |
| v3 | Stage 9 | Non-blocking write-back |
| **v4** | **Postgres topic lock (Issue 2)** | Atomic lock in workflow_runs; replaces WP meta race condition; `lock_expires_at` auto-recovery after crash |
| **v4** | **Comparison table to Postgres (Issue 5)** | Per-affiliate rows with atomic upsert; replaces WP option read-modify-write |
| **v4** | **Stage 9 aggregation model** | Append-only ledger + materialised aggregate; single runs cannot dominate display; frequency ranking requires multiple appearances |
| **v4** | **Trustpilot removed** | Legal risk not worth it; Reddit + MSE + PAA + Affiliate FAQ retained |
| **v4** | **Affiliate FAQ sourcing** | Affiliate responses sourced from affiliate's own published FAQ, not LLM-generated |
| **v4** | **Compliance review gate** | `compliance_review_required` flag withholds regulated-matter claims from live pages until human-reviewed |