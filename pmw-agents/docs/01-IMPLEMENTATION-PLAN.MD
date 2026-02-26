# PreciousMarketWatch — Final Implementation Plan
> **Version:** 2.0 — 2026-02  
> **Status:** Authorised for implementation  
> **Deployment target:** Railway (agent services) · IONOS (WordPress)  
> **Changes from v1.0:** Revised scoring model · Rich media layer · Tools & calculators strategy · Reader intent classification · E-E-A-T enforcement · Affiliate commission analysis · Profitability roadmap  

---

## Executive Summary

This document is the single source of truth for building PreciousMarketWatch into a profitable, self-sustaining affiliate media business. It covers the AI agent pipeline, the website tools layer, the scoring model, the infrastructure, and the revenue strategy in one place.

**The core argument:** Content alone will get you to £1–3k/month. Content plus a tools layer that gives visitors a reason to return is what unlocks £10–20k/month. Both must be built in parallel — the pipeline produces the content, the tools produce the authority and return visits that make the content convert.

**North star metric:** £10k/month gross affiliate revenue within 9 months of first article published. Every decision in this document should be evaluated against that target.

**Revenue model reality check based on market research:**
- Augusta Precious Metals: $500/qualified lead + lifetime commission. One referral per week = £2k+/month
- BullionVault: commission on purchase + ongoing storage fee (compounding revenue)
- The Royal Mint / Chards: percentage of transaction value on bullion purchases
- JM Bullion / APMEX: 6% per sale — one £5,000 gold bar purchase = £300 commission

The maths works. The question is purely whether you can generate sufficient qualified traffic with purchase intent. That is what this plan solves.

---

## Table of Contents

1. [Profitability Strategy](#1-profitability-strategy)
2. [Architecture Overview](#2-architecture-overview)
3. [Website Tools Layer](#3-website-tools-layer)
4. [Railway Service Configuration](#4-railway-service-configuration)
5. [Database Schema](#5-database-schema)
6. [Agent Workflow Design — Revised](#6-agent-workflow-design--revised)
7. [Scoring Model — Revised](#7-scoring-model--revised)
8. [Rich Media Layer](#8-rich-media-layer)
9. [Bridge API Specification](#9-bridge-api-specification)
10. [Public Agent Profiles](#10-public-agent-profiles)
11. [Dashboard Specification](#11-dashboard-specification)
12. [Social Content Automation](#12-social-content-automation)
13. [Analysis Team](#13-analysis-team)
14. [Environment Configuration](#14-environment-configuration)
15. [GitHub Workflow & CI/CD](#15-github-workflow--cicd)
16. [Implementation Phases](#16-implementation-phases)
17. [Testing Strategy](#17-testing-strategy)
18. [KPIs & Success Metrics](#18-kpis--success-metrics)
19. [Risk Register](#19-risk-register)

---

## 1. Profitability Strategy

### 1a. The Two-Track Model

Most AI affiliate sites fail because they treat content as the only lever. In the precious metals niche, content is necessary but not sufficient. The sites that generate serious recurring revenue do two things simultaneously:

**Track 1 — Content Engine (your pipeline):** Produce 2–3 SEO-optimised, affiliate-intent articles per day. This builds topical authority with Google over 3–6 months and drives organic search traffic. The pipeline you are building handles this.

**Track 2 — Tools & Data Layer (what most competitors skip):** Build interactive calculators, comparison tools, and price widgets that give visitors a reason to bookmark the site and return. Tools pages rank for high-commercial-intent queries ("gold value calculator", "how much is my gold worth") and put users in a transactional mindset before they see your affiliate CTA. This is the multiplier on Track 1.

```
Track 1 alone:     Organic traffic × article conversion rate = revenue
Track 1 + Track 2: (Organic + return visitors + bookmarks) × (article + tool conversion rate) = 3–5× revenue
```

### 1b. Revenue Trajectory

| Month | Primary drivers | Traffic target | Est. monthly revenue |
|-------|----------------|----------------|---------------------|
| 1–2 | Pipeline live, first 30 articles, 3 tools | 200–500 sessions/month | £0–200 |
| 3–4 | 60–90 articles, 6 tools, social active | 1k–3k sessions | £300–800 |
| 5–6 | 120+ articles, full tool suite, email list | 5k–10k sessions | £1k–3k |
| 7–8 | SEO compounding, 200+ articles | 15k–25k sessions | £3k–8k |
| 9–12 | Full authority, featured snippets, tools ranking | 30k–60k sessions | £8k–20k |

These are conservative estimates assuming UK-focused traffic and BullionVault/Royal Mint affiliate rates. Augusta Precious Metals ($500/lead) or similar high-ticket programs, if added, collapse the timeline to profitability significantly.

### 1c. Affiliate Portfolio Priority

Based on commission structure research, prioritise affiliates in this order:

| Priority | Affiliate | Why | Commission type |
|----------|-----------|-----|----------------|
| 1 | BullionVault | UK market leader, recurring storage commission | Purchase + ongoing storage % |
| 1 | Augusta Precious Metals | $500/qualified lead — one/week = significant revenue | Per qualified lead + lifetime |
| 2 | The Royal Mint | Highest brand trust in UK, converts well | % of transaction |
| 2 | Chards | UK specialist, good for comparison articles | % of transaction |
| 3 | GoldBroker | European audience, recurring storage | Purchase + storage |
| 3 | JM Bullion / APMEX | US audience, 6% per sale | % of transaction |
| 4 | Birch Gold Group | US Gold IRA audience, $25/qualified lead | Per lead |

**Critical insight from research:** Sites that earn $5k+/month in this niche focus heavily on the IRA/retirement market (US-focused) because the average transaction value is $50,000–$200,000 vs £2,000–£5,000 for UK bullion purchases. If you want to reach the upper end of your revenue target, you need both a UK bullion track and a US gold IRA track in your content strategy.

---

## 2. Architecture Overview

### 2a. Full System Map

```
┌──────────────────────────────────────────────────────────────────────┐
│  RAILWAY PROJECT: pmw-production                                     │
│                                                                      │
│  ┌─────────────────┐    ┌─────────────────┐                         │
│  │  PMW-Bridge     │    │  PMW-Agents     │                         │
│  │  FastAPI        │◄──►│  LangGraph      │                         │
│  │  WebSocket      │    │  Orchestrator   │                         │
│  │  REST API       │    │  Worker pool    │                         │
│  │  PUBLIC         │    │  PRIVATE        │                         │
│  └────────┬────────┘    └────────┬────────┘                         │
│           │                      │                                   │
│  ┌────────▼──────────────────────▼────────┐                         │
│  │  PMW-Postgres          PMW-Redis       │                         │
│  │  Source of truth       Signal bus      │                         │
│  └────────────────────────────────────────┘                         │
└──────────────────────────────────────────────────────────────────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐    ┌──────────────────────────────┐
│  WordPress      │    │  React Dashboard             │
│  IONOS hosting  │    │  Private operator interface  │
│  REST API       │    │  JWT auth                    │
│  Drafts → live  │    └──────────────────────────────┘
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│  preciousmarketwatch.com — Public Site               │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Articles    │  │  Pillar pages│  │  Tools    │  │
│  │  (pipeline)  │  │  + charts    │  │  layer    │  │
│  └──────────────┘  └──────────────┘  └───────────┘  │
│                                                      │
│  Behind Cloudflare CDN                               │
│  WPGraphQL → React frontend                          │
└──────────────────────────────────────────────────────┘
```

### 2b. Content Pipeline Data Flow

```
Scheduler (08:00 UTC daily)
    │
    ▼
POST /workflow/trigger {topic_id}  →  Bridge creates workflow_run
    │
    ├── Research Agent: fetch prices + news + SERP + PAA questions
    │       └── Judge: score ≥ 0.75
    ├── Planning Agent: structure + internal link lookup + E-E-A-T plan
    │       └── Judge: score ≥ 0.80
    ├── Content Agent: write article with facts, citations, E-E-A-T signals
    │       └── Judge: score ≥ 0.80
    ├── Media Agent: generate featured image + infographic brief
    │       └── Upload to WP media library
    └── Publishing Agent: create WP draft + metadata + media attached
    
WebSocket → Dashboard live view
Human reviews → approves → publishes
```

---

## 3. Website Tools Layer

> This section is not an agent pipeline concern — it is a WordPress/React development workstream that runs in parallel with the pipeline. Tools are static or near-static pages built once and maintained by the price data infrastructure you already have.

### 3a. Why Tools Are Not Optional

Direct evidence from the competitor research:

- APMEX's precious metals calculators page is one of their highest-traffic SEO assets — it ranks for "gold value calculator", "silver melt value", "platinum investment return" and dozens of similar commercial-intent queries
- Bullion.Directory's investment return calculator is their most-linked single page, generating backlinks from personal finance blogs that their articles never receive
- GoldTure.com (smaller site) has 11 distinct gold tools and ranks on page 1 for multiple calculator queries despite having thin article content

The key insight is that a calculator page, once built, requires zero ongoing maintenance cost (unlike articles which become stale) and generates compounding SEO value over years. Your pipeline costs £0.30–£0.60 per article in API costs. A calculator page costs ~4 hours of development time and then costs nothing forever.

### 3b. Tool Priority Matrix

Prioritised by: search volume × commercial intent × development effort

| Tool | Search intent | Affiliate linkage | Build effort | Priority |
|------|-------------|-------------------|-------------|---------|
| **Gold value calculator** | "how much is my gold worth" | "Ready to sell? BullionVault pays spot price" | Low — React component | **P1** |
| **Gold/silver investment return calculator** | "gold investment returns" | "Start investing with BullionVault from £25" | Low — math + chart | **P1** |
| **Precious metals portfolio tracker** | "track gold portfolio" | "Store securely with BullionVault" | Medium — localStorage | **P1** |
| **Dealer comparison table** | "best place to buy gold UK" | Direct affiliate links in table | Low — curated data | **P1** |
| **Scrap gold calculator** | "scrap gold value" | "Selling? Compare dealers first" | Low — existing formula | **P2** |
| **Gold/silver ratio tracker** | "gold silver ratio" | "Silver undervalued? Buy now via Chards" | Low — live data | **P2** |
| **Inflation hedge calculator** | "gold vs inflation" | "Protect purchasing power — BullionVault" | Medium — CPI data API | **P2** |
| **Coin melt value calculator** | "gold coin value UK" | "Find coins at Royal Mint" | Medium — coin database | **P2** |
| **Gold IRA eligibility checker** | "gold IRA rules" | "Qualify? Augusta Precious Metals" | Low — form + logic | **P3 (US focus)** |
| **Gemstone carat/value estimator** | "how much is my ruby worth" | "Get a professional valuation" | Medium — gemstone data | **P3** |
| **Storage cost comparison** | "gold storage costs UK" | Direct links to BullionVault, GoldBroker | Low — comparison table | **P3** |

### 3c. P1 Tools — Technical Specification

#### Tool 1: Gold Value Calculator

**Purpose:** User enters weight + purity → sees current market value in GBP/USD.  
**Affiliate hook:** "Your gold is worth £X. BullionVault will buy at [live spot price]. [Get an instant quote →]"  
**Data:** Live spot price from your existing metal price API.  
**Implementation:** WordPress page + React component embedded via shortcode or block. No backend needed — all client-side with a live price API call.

```javascript
// Core calculation logic
function calculateGoldValue(weightGrams, purity, spotPricePerOz) {
    const TROY_OZ_TO_GRAMS = 31.1035;
    const purityFactor = purity / 1000; // e.g. 750 for 18k = 0.750
    const pureGoldGrams = weightGrams * purityFactor;
    const pureGoldOz = pureGoldGrams / TROY_OZ_TO_GRAMS;
    return pureGoldOz * spotPricePerOz;
}

// Purity presets
const PURITY_PRESETS = {
    "24k (999)": 999, "22k (916)": 916, "18k (750)": 750,
    "14k (585)": 585, "9k (375)": 375, "Silver (925)": 925,
};
```

**Affiliate placement — critical detail:** The affiliate CTA is displayed *after* the calculation result, not before. The user has just discovered their gold is worth £800. That is the highest-intent moment in their entire visit. The CTA must be: "Your gold is worth approximately **£812** at today's spot price. BullionVault, the UK's most trusted bullion platform, will buy gold at competitive rates with same-day settlement. [Get a free quote from BullionVault →]"

#### Tool 2: Investment Return Calculator

**Purpose:** "If I had invested £X in gold/silver/platinum Y years ago, what would it be worth today?"  
**Affiliate hook:** "Gold has returned X% over 10 years. Start building your position from £25 with BullionVault."  
**Data:** Historical price data (MetalPriceAPI historical endpoint) + current spot.  
**Implementation:** React with recharts line chart showing the growth trajectory.

This tool is specifically valuable because it creates an emotional "what if" moment. Research shows this is one of the highest-converting content formats in the investment niche. The chart showing gold's performance against inflation over 20 years is a powerful visual argument for buying.

#### Tool 3: Dealer Comparison Table

**Purpose:** Side-by-side comparison of the top 5–8 UK gold dealers on: price premium over spot, storage fees, minimum purchase, delivery speed, FCA regulation status, customer rating.  
**Affiliate hook:** Every dealer name in the table is an affiliate link.  
**Data:** Semi-static — updated by the Performance Intelligence Agent weekly using live price checks.  
**SEO value:** "best gold dealers UK" is a high-commercial-intent query with significant search volume. A well-structured comparison table has a strong chance of earning a featured snippet position.

**Critical note on disclosure:** The ASA (UK Advertising Standards Authority) and FCA guidance both require clear disclosure that your comparison table includes affiliate links. Add a prominent disclosure box at the top: "This comparison table includes affiliate links. We may receive a commission if you purchase through these links. This does not affect our ratings, which are based on [criteria]." This is also a positive E-E-A-T signal — Google rewards transparent disclosure.

#### Tool 4: Portfolio Tracker

**Purpose:** User adds their holdings (X grams of gold, Y oz silver) and sees live portfolio value.  
**Affiliate hook:** "Your portfolio is worth £X. Protect it with insured vault storage from BullionVault — from £4/month."  
**Data:** Live spot prices.  
**Implementation:** React with localStorage for persistence (no login required for v1). Values update every 60 seconds.  
**Return visit driver:** This is the bookmark tool. A user who tracks their portfolio will return to the site every time they want to check value — daily or weekly for active investors.

### 3d. Integrating Tools with the Pipeline

The agent pipeline should be aware of your tools and link to them contextually in articles. Add to the Publishing Agent payload:

```python
# Add tool links based on topic category
TOOL_LINKS = {
    "gold":      "https://preciousmarketwatch.com/tools/gold-calculator/",
    "silver":    "https://preciousmarketwatch.com/tools/silver-calculator/",
    "portfolio": "https://preciousmarketwatch.com/tools/portfolio-tracker/",
    "dealers":   "https://preciousmarketwatch.com/tools/dealer-comparison/",
}

# In the content prompt, add:
# "Include one contextual internal link to a PMW tool where relevant.
#  Available tools: {{ tool_links }}"
```

This creates a bidirectional traffic flow: articles drive users to tools, tools drive users back to articles and affiliate CTAs.

---

## 4. Railway Service Configuration

### 4a. Service Registry

| Service | Type | Railway name | Port | Public URL | Auth |
|---------|------|-------------|------|-----------|------|
| PMW-Bridge | FastAPI | `pmw-bridge` | 8000 | `pmw-bridge.up.railway.app` | JWT |
| PMW-Agents | Python worker | `pmw-agents` | none | none | n/a |
| PMW-Postgres | Managed Postgres | `pmw-postgres` | 5432 | none | conn string |
| PMW-Redis | Managed Redis | `pmw-redis` | 6379 | none | conn string |

### 4b. Repository Structure

```
pmw-agents/
├── bridge/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── routers/
│   │   ├── workflows.py
│   │   ├── topics.py
│   │   ├── agents.py          ← /agents/public endpoint
│   │   ├── auth.py
│   │   ├── performance.py
│   │   └── social.py
│   ├── ws/manager.py
│   ├── services/
│   │   ├── wp_client.py
│   │   └── redis_client.py
│   └── models/schemas.py
│
├── agents/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                ← Worker entry point
│   ├── orchestrator.py        ← LangGraph graph builder
│   ├── nodes/
│   │   ├── task_loader.py
│   │   ├── research.py        ← Now includes SERP + PAA fetching
│   │   ├── planning.py        ← Now includes internal link lookup
│   │   ├── content.py         ← Now includes E-E-A-T enforcement
│   │   ├── media.py           ← NEW: image + infographic generation
│   │   ├── publishing.py
│   │   ├── social.py
│   │   ├── performance_intel.py
│   │   └── judge.py
│   ├── tools/
│   │   ├── metal_prices.py
│   │   ├── news_search.py
│   │   ├── serp_search.py     ← NEW: SERP + PAA fetching
│   │   ├── wp_search.py       ← NEW: internal link lookup
│   │   ├── image_gen.py       ← NEW: DALL-E 3 / Ideogram
│   │   ├── ga4.py
│   │   ├── clarity.py
│   │   ├── search_console.py
│   │   └── social_platforms.py
│   ├── scoring/
│   │   ├── base.py
│   │   ├── research_scorer.py ← Revised weights
│   │   ├── planning_scorer.py ← Revised weights + new criteria
│   │   ├── content_scorer.py  ← Revised weights + E-E-A-T
│   │   └── social_scorer.py   ← Revised weights + emotional trigger
│   ├── state/types.py
│   └── db/
│       ├── connection.py
│       ├── queries.py
│       └── migrations/
│
├── dashboard/
│   └── src/
│       ├── App.tsx
│       ├── store/index.ts
│       ├── components/
│       └── pages/
│
├── db/migrations/
│   ├── 001_initial.sql
│   ├── 002_social.sql
│   ├── 003_performance.sql
│   └── 004_media.sql          ← NEW
│
├── .env.example
├── .github/workflows/
└── docker-compose.yml
```

---

## 5. Database Schema

### 5a. Core Tables (Phase 1)

```sql
-- 001_initial.sql

CREATE TABLE affiliates (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    url             TEXT NOT NULL,
    value_prop      TEXT NOT NULL,
    commission_type VARCHAR(50),      -- cpa | cpc | revenue_share | per_lead
    commission_rate DECIMAL(8,2),     -- £/$ amount for per_lead, % for others
    cookie_days     INTEGER,
    geo_focus       VARCHAR(50),      -- uk | us | global
    min_transaction DECIMAL(10,2),    -- minimum qualifying transaction value
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE topics (
    id              SERIAL PRIMARY KEY,
    topic_name      VARCHAR(255) NOT NULL,
    topic_category  VARCHAR(100),     -- gold | silver | platinum | gemstones | ira
    target_keyword  VARCHAR(255) NOT NULL,
    affiliate_id    INTEGER REFERENCES affiliates(id),
    reader_intent   VARCHAR(50),      -- price_checker | consideration_buyer | curiosity_reader
    -- reader_intent set by Research Agent, used to select article template
    schedule_cron   VARCHAR(50),
    priority        INTEGER DEFAULT 5,
    status          VARCHAR(50) DEFAULT 'active',
    last_run_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE workflow_runs (
    id                  SERIAL PRIMARY KEY,
    topic_id            INTEGER REFERENCES topics(id),
    status              VARCHAR(50) NOT NULL DEFAULT 'pending',
    current_stage       VARCHAR(50),
    final_score         DECIMAL(4,3),
    wp_post_id          INTEGER,
    wp_post_url         TEXT,
    human_intervened    BOOLEAN DEFAULT FALSE,
    threshold_overrides JSONB,
    reader_intent       VARCHAR(50),      -- carried from research output
    total_cost_usd      DECIMAL(8,6),
    started_at          TIMESTAMPTZ DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    failed_at           TIMESTAMPTZ
);

CREATE INDEX idx_workflow_runs_status  ON workflow_runs(status);
CREATE INDEX idx_workflow_runs_topic   ON workflow_runs(topic_id);
CREATE INDEX idx_workflow_runs_started ON workflow_runs(started_at DESC);

CREATE TABLE workflow_stages (
    id               SERIAL PRIMARY KEY,
    run_id           INTEGER REFERENCES workflow_runs(id) ON DELETE CASCADE,
    stage_name       VARCHAR(50) NOT NULL,
    status           VARCHAR(50) NOT NULL DEFAULT 'pending',
    attempt_number   INTEGER DEFAULT 1,
    score            DECIMAL(4,3),
    passed_threshold BOOLEAN,
    output_json      JSONB,
    judge_feedback   JSONB,
    prompt_hash      VARCHAR(64),
    model_used       VARCHAR(100),
    input_tokens     INTEGER,
    output_tokens    INTEGER,
    cost_usd         DECIMAL(8,6),
    started_at       TIMESTAMPTZ DEFAULT NOW(),
    completed_at     TIMESTAMPTZ
);

CREATE INDEX idx_workflow_stages_run   ON workflow_stages(run_id);
CREATE INDEX idx_workflow_stages_stage ON workflow_stages(stage_name);

CREATE TABLE agent_configs (
    id               SERIAL PRIMARY KEY,
    agent_name       VARCHAR(100) UNIQUE NOT NULL,
    model            VARCHAR(100) NOT NULL,
    threshold        DECIMAL(4,3),
    max_retries      INTEGER DEFAULT 3,
    temperature      DECIMAL(3,2) DEFAULT 0.7,
    criteria_weights JSONB,
    prompt_template  JSONB,
    active           BOOLEAN DEFAULT TRUE,
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE interventions (
    id               SERIAL PRIMARY KEY,
    run_id           INTEGER REFERENCES workflow_runs(id),
    stage_name       VARCHAR(50),
    intervened_by    INTEGER,
    original_output  JSONB,
    corrected_output JSONB,
    reason           TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE vault_events (
    id               SERIAL PRIMARY KEY,
    idempotency_key  UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    event_type       VARCHAR(100) NOT NULL,
    run_id           INTEGER,
    topic_id         INTEGER,
    stage_name       VARCHAR(50),
    payload          JSONB NOT NULL,
    payload_hash     VARCHAR(64) NOT NULL,
    previous_hash    VARCHAR(64) NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vault_events_run  ON vault_events(run_id);
CREATE INDEX idx_vault_events_type ON vault_events(event_type);

CREATE TABLE users (
    id             SERIAL PRIMARY KEY,
    email          VARCHAR(255) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    role           VARCHAR(50) DEFAULT 'operator',
    active         BOOLEAN DEFAULT TRUE,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    last_login_at  TIMESTAMPTZ
);
```

### 5b. Media Table (Phase 1 Extension)

```sql
-- 004_media.sql

CREATE TABLE generated_media (
    id              SERIAL PRIMARY KEY,
    run_id          INTEGER REFERENCES workflow_runs(id),
    media_type      VARCHAR(50) NOT NULL,  -- featured_image | infographic | chart
    prompt_used     TEXT,
    wp_media_id     INTEGER,
    wp_media_url    TEXT,
    file_format     VARCHAR(20),           -- jpg | png | svg | webp
    generator       VARCHAR(50),           -- dalle3 | ideogram | svg_render
    cost_usd        DECIMAL(8,6),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_generated_media_run ON generated_media(run_id);
```

### 5c. Social and Performance Tables

```sql
-- 002_social.sql
CREATE TABLE social_posts (
    id           SERIAL PRIMARY KEY,
    run_id       INTEGER REFERENCES workflow_runs(id),
    wp_post_id   INTEGER,
    platform     VARCHAR(50) NOT NULL,
    content      TEXT NOT NULL,
    hashtags     TEXT[],
    hook_type    VARCHAR(50),   -- fear | greed | curiosity (from emotional trigger classifier)
    score        DECIMAL(4,3),
    status       VARCHAR(50) DEFAULT 'draft',
    scheduled_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- 003_performance.sql
CREATE TABLE performance_reports (
    id              SERIAL PRIMARY KEY,
    report_date     DATE NOT NULL,
    report_type     VARCHAR(50),
    ga4_data        JSONB,
    clarity_data    JSONB,
    search_console_data JSONB,
    agent_analysis  TEXT,
    recommendations JSONB,
    scoring_correlation JSONB,  -- NEW: correlation between content scores and real conversions
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE article_performance (
    id                SERIAL PRIMARY KEY,
    wp_post_id        INTEGER NOT NULL,
    run_id            INTEGER REFERENCES workflow_runs(id),
    date              DATE NOT NULL,
    sessions          INTEGER DEFAULT 0,
    bounce_rate       DECIMAL(5,2),
    avg_session_sec   INTEGER,
    affiliate_clicks  INTEGER DEFAULT 0,
    conversions       INTEGER DEFAULT 0,
    impressions       INTEGER DEFAULT 0,
    clicks            INTEGER DEFAULT 0,
    avg_position      DECIMAL(5,2),
    scroll_depth_p75  INTEGER,
    rage_clicks       INTEGER DEFAULT 0,
    content_score     DECIMAL(4,3),  -- from original run, for correlation analysis
    UNIQUE(wp_post_id, date)
);
```

---

## 6. Agent Workflow Design — Revised

### 6a. LangGraph State (Updated)

```python
# agents/state/types.py
from typing import TypedDict, Optional, List

class PipelineState(TypedDict):
    # Identity
    run_id:           int
    topic_id:         int
    topic:            dict

    # Stage outputs
    task_data:        Optional[dict]
    research_output:  Optional[dict]
    planning_output:  Optional[dict]
    content_output:   Optional[dict]
    media_output:     Optional[dict]   # NEW

    # Reader intent (set by Research, used by Planning + Content)
    reader_intent:    Optional[str]    # price_checker | consideration_buyer | curiosity_reader

    # Scoring state
    current_stage:    str
    current_score:    Optional[float]
    attempt_number:   int
    judge_feedback:   Optional[dict]
    score_history:    List[dict]

    # Control
    status:           str
    error:            Optional[str]
    threshold_overrides: Optional[dict]

    # Metadata
    started_at:       str
    model_usage:      List[dict]       # cost tracking
```

### 6b. LangGraph Graph (Updated with Media Node)

```python
# agents/orchestrator.py
def build_content_pipeline(checkpointer) -> StateGraph:
    g = StateGraph(PipelineState)

    g.add_node("task_loader",    task_loader.run)
    g.add_node("research",       research.run)
    g.add_node("judge_research", judge.evaluate_research)
    g.add_node("planning",       planning.run)
    g.add_node("judge_planning", judge.evaluate_planning)
    g.add_node("content",        content.run)
    g.add_node("judge_content",  judge.evaluate_content)
    g.add_node("media",          media.run)          # NEW — no Judge needed
    g.add_node("publishing",     publishing.run)
    g.add_node("handle_failure", handle_max_retries)

    g.set_entry_point("task_loader")
    g.add_edge("task_loader",    "research")
    g.add_edge("research",       "judge_research")

    g.add_conditional_edges("judge_research", route_after_judge, {
        "pass":        "planning",
        "retry":       "research",
        "max_retries": "handle_failure",
    })
    g.add_edge("planning",       "judge_planning")
    g.add_conditional_edges("judge_planning", route_after_judge, {
        "pass":        "content",
        "retry":       "planning",
        "max_retries": "handle_failure",
    })
    g.add_edge("content",        "judge_content")
    g.add_conditional_edges("judge_content", route_after_judge, {
        "pass":        "media",          # content → media before publishing
        "retry":       "content",
        "max_retries": "handle_failure",
    })
    g.add_edge("media",          "publishing")  # media always proceeds
    g.add_edge("publishing",     END)
    g.add_edge("handle_failure", END)

    return g.compile(
        checkpointer=checkpointer,
        interrupt_before=["handle_failure"]
    )
```

### 6c. Research Node (Updated — adds SERP, PAA, reader intent)

```python
# agents/nodes/research.py

async def run(state: PipelineState) -> PipelineState:
    topic   = state["topic"]
    attempt = state["attempt_number"]

    # ── Gather all data in parallel ───────────────────────────
    price_data, news_items, serp_data = await asyncio.gather(
        get_current_prices(topic["topic_name"]),
        search_recent_news(
            keyword  = topic["target_keyword"],
            days_back= 30 + (attempt * 15),
            min_results= 5
        ),
        fetch_serp_context(topic["target_keyword"]),  # NEW
    )

    # serp_data contains:
    # - top_result_formats: ["listicle", "guide", "comparison"]
    # - paa_questions: ["How much gold should I own?", ...]
    # - featured_snippet_type: "table" | "paragraph" | "list" | null
    # - competitor_titles: [str × 5]

    prompt_vars = {
        **build_base_vars(topic),
        "price_data":    json.dumps(price_data),
        "news_items":    json.dumps(news_items),
        "serp_context":  json.dumps(serp_data),  # NEW
    }

    output, usage = await tracked_llm_call(
        agent_name   = "research",
        template_key = "research",
        variables    = prompt_vars,
        run_id       = state["run_id"],
        attempt      = attempt,
    )

    # reader_intent extracted from research output and stored in state
    return {
        **state,
        "research_output": output,
        "reader_intent":   output.get("reader_intent"),  # NEW
        "current_stage":   "research",
        "model_usage":     state["model_usage"] + [usage],
    }
```

### 6d. Planning Node (Updated — adds internal links, E-E-A-T, SERP intent)

```python
# agents/nodes/planning.py

async def run(state: PipelineState) -> PipelineState:
    topic          = state["topic"]
    research       = state["research_output"]
    reader_intent  = state["reader_intent"]

    # ── Fetch internal link opportunities ─────────────────────
    internal_links = await find_internal_links(
        keyword  = topic["target_keyword"],
        category = topic["topic_category"],
        limit    = 3,
    )
    # Calls WP REST API: GET /wp/v2/posts?search={keyword}&per_page=3

    # ── Select article template based on reader intent ─────────
    template_key = {
        "price_checker":       "planning_price_checker",
        "consideration_buyer": "planning_consideration",
        "curiosity_reader":    "planning_curiosity",
    }.get(reader_intent, "planning_consideration")  # default to consideration

    prompt_vars = {
        **build_base_vars(topic),
        "research_output_json": json.dumps(research),
        "internal_links":       json.dumps(internal_links),  # NEW
        "reader_intent":        reader_intent,                # NEW
        "serp_context":         json.dumps(
                                    research.get("serp_context", {})
                                ),
        "tool_links":           json.dumps(
                                    get_relevant_tool_links(
                                        topic["topic_category"]
                                    )
                                ),  # NEW
    }

    output, usage = await tracked_llm_call(
        agent_name   = "planning",
        template_key = template_key,
        variables    = prompt_vars,
        run_id       = state["run_id"],
        attempt      = state["attempt_number"],
    )

    return {
        **state,
        "planning_output": output,
        "current_stage":   "planning",
        "model_usage":     state["model_usage"] + [usage],
    }
```

### 6e. Media Node (New)

```python
# agents/nodes/media.py
import httpx
import base64
from agents.db.queries import store_media_record
from agents.base import publish_event

async def run(state: PipelineState) -> PipelineState:
    run_id  = state["run_id"]
    content = state["content_output"]
    topic   = state["topic"]

    await publish_event("stage.started", {
        "run_id": run_id, "stage": "media"
    })

    media_results = []
    total_cost    = 0.0

    # ── 1. Featured image ─────────────────────────────────────
    try:
        image_prompt = build_image_prompt(content["title"], topic)
        image_url, img_cost = await generate_image(image_prompt)
        wp_media_id  = await upload_to_wp_media(image_url, content["title"])

        media_results.append({
            "type":       "featured_image",
            "wp_media_id": wp_media_id,
            "cost_usd":   img_cost,
        })
        total_cost += img_cost

        await store_media_record(run_id, "featured_image", image_prompt,
                                 wp_media_id, img_cost)
    except Exception as e:
        # Media failure is non-blocking — article still publishes without image
        await publish_event("media.warning", {
            "run_id": run_id, "type": "featured_image", "error": str(e)
        })

    # ── 2. Infographic (if planning flagged it as eligible) ───
    if content.get("infographic_eligible"):
        try:
            infographic_svg = await generate_infographic(
                content.get("infographic_data", {})
            )
            wp_media_id = await upload_svg_to_wp(infographic_svg,
                                                  content["title"])
            media_results.append({
                "type":        "infographic",
                "wp_media_id":  wp_media_id,
                "cost_usd":    0.0,  # SVG render is free
            })
            await store_media_record(run_id, "infographic", None,
                                     wp_media_id, 0.0)
        except Exception as e:
            await publish_event("media.warning", {
                "run_id": run_id, "type": "infographic", "error": str(e)
            })

    await publish_event("stage.complete", {
        "run_id": run_id, "stage": "media",
        "media_count": len(media_results), "cost_usd": total_cost
    })

    return {
        **state,
        "media_output": {"items": media_results, "total_cost": total_cost},
        "current_stage": "media",
        "model_usage": state["model_usage"] + [{
            "agent": "media", "cost_usd": total_cost
        }],
    }


def build_image_prompt(title: str, topic: dict) -> str:
    """
    Build a DALL-E 3 prompt for a financial/investment featured image.
    Avoids text in images (DALL-E renders text poorly).
    Uses abstract, premium financial photography style.
    """
    category_style = {
        "gold":      "gleaming gold bars and coins arranged on dark velvet, professional financial photography, dramatic side lighting",
        "silver":    "polished silver coins and bullion bars, cool tones, professional studio lighting",
        "platinum":  "platinum ingots with subtle metallic sheen, minimalist composition, premium look",
        "gemstones": "precious gemstones in elegant display, macro photography, rich colours",
    }.get(topic["topic_category"], "precious metals in professional studio photography")

    return (
        f"Premium financial photography for an article about: {title}. "
        f"Style: {category_style}. "
        f"No text or words in the image. Suitable for a financial news website. "
        f"High resolution, editorial quality, wide crop suitable for a blog header."
    )


async def generate_image(prompt: str) -> tuple[str, float]:
    """Generate image via DALL-E 3. Returns (url, cost_usd)."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            json={
                "model":   "dall-e-3",
                "prompt":  prompt,
                "n":       1,
                "size":    "1792x1024",  # landscape for blog headers
                "quality": "standard",  # $0.040/image — use "hd" for hero images
            },
            timeout=60.0
        )
        data = response.json()
        return data["data"][0]["url"], 0.040  # standard quality cost


async def generate_infographic(data: dict) -> str:
    """
    Generate an SVG infographic from structured data.
    Currently supports: comparison tables, step-by-step processes, stat highlights.
    Returns SVG string.
    """
    infographic_type = data.get("type", "stats")

    if infographic_type == "comparison":
        return render_comparison_svg(data["items"], data["title"])
    elif infographic_type == "steps":
        return render_steps_svg(data["steps"], data["title"])
    elif infographic_type == "stats":
        return render_stats_svg(data["stats"], data["title"])
    else:
        raise ValueError(f"Unknown infographic type: {infographic_type}")
```

---

## 7. Scoring Model — Revised

> All changes from v1.0 are marked with ★. Rationale for each change is given.

### 7a. Research Score (Revised)

**Key changes:**
- Added `reader_intent_signal` (10%) — Research Agent must identify whether the topic attracts price checkers, consideration buyers, or curiosity readers. This dramatically improves Planning Agent output quality.
- Added `serp_context` (5%) — Did the Research Agent capture PAA questions and top result formats? This feeds directly into Planning's format selection.
- Reduced `source_count` to 10% — quantity of sources is less important than quality. Five authoritative sources beat ten mediocre ones.
- Reduced `factual_density` to 10% — still important but shouldn't compete with affiliate context in weighting.

| Criterion | Weight | What it measures |
|-----------|--------|-----------------|
| `source_count` | 10% ★ (was 15%) | 5+ distinct authoritative sources |
| `recency` | 20% | 3+ sources < 30 days old |
| `relevance` | 20% ★ (was 25%) | Direct topic + keyword match |
| `affiliate_context` | 25% | Problem/solution signal for affiliate |
| `factual_density` | 10% ★ (was 15%) | Concrete prices, stats, named events |
| `reader_intent_signal` | 10% ★ NEW | Correctly identifies buyer mindset |
| `serp_context` | 5% ★ NEW | PAA questions + top format captured |

**Threshold:** 0.75 · **Max retries:** 3  
**Judge model:** claude-sonnet-4-6 ★ (was claude-opus-4-6 — Research evaluation is fact-checking, not nuanced judgment. Sonnet is sufficient and ~5× cheaper.)

### 7b. Planning Score (Revised)

**Key changes:**
- Added `serp_intent_match` (10%) — Does the article format match what Google is actually serving for this keyword? A long-form guide in a SERP full of listicles will underperform regardless of quality.
- Added `eeat_signals_planned` (10%) — Has the plan allocated space for: author attribution, citation format, outbound links to authoritative sources (World Gold Council, LBMA, FCA), and affiliate disclosure? Without this, Content Agent cannot execute E-E-A-T even if it tries.
- Added `tool_link_integration` (5%) — Has the plan included a natural reference to a PMW tool where applicable? Tools drive return visits and increase session depth.
- Reduced `seo_alignment` to 10% — keyword placement is now a hygiene check, not the primary SEO criterion. Real SEO authority comes from E-E-A-T and SERP intent matching.

| Criterion | Weight | What it measures |
|-----------|--------|-----------------|
| `problem_solution_flow` | 20% ★ (was 25%) | Clear problem → affiliate solution arc |
| `affiliate_integration` | 20% ★ (was 25%) | 3+ placements at natural conversion points |
| `seo_alignment` | 10% ★ (was 20%) | Keyword in title, H1, meta — hygiene check |
| `content_depth` | 10% | 4–5 distinct angles, no padding |
| `conversion_elements` | 15% | CTAs, FAQs, social hooks mapped |
| `serp_intent_match` | 10% ★ NEW | Format matches dominant SERP result type |
| `eeat_signals_planned` | 10% ★ NEW | Citations, disclosure, author section planned |
| `tool_link_integration` | 5% ★ NEW | PMW tool referenced where applicable |

**Threshold:** 0.80 · **Max retries:** 3 · **Judge model:** claude-opus-4-6

### 7c. Content Score (Revised)

**Key changes:**
- Added `eeat_execution` (10%) — Are E-E-A-T signals actually present in the final article? This is distinct from planning for them — the Judge checks execution. Specifically: 2+ outbound links to authoritative sources with anchor text, affiliate disclosure present, author/byline section present, at least one named source with date.
- Added `internal_links` (5%) — Are 2+ contextual internal links to related PMW content present?
- Reduced `keyword_integration` to 10% — Google's NLP understands semantic relevance. Keyword stuffing guidance is largely obsolete for a well-written article.
- Reduced `readability` to 10% — still matters but shouldn't crowd out conversion-focused criteria.

| Criterion | Weight | What it measures |
|-----------|--------|-----------------|
| `buying_intent_strength` | 25% ★ (was 30%) | 3+ natural affiliate mentions at high-intent moments |
| `factual_accuracy` | 20% | 5+ facts from research bundle, correctly cited |
| `keyword_integration` | 10% ★ (was 15%) | Primary keyword natural, not stuffed |
| `readability` | 10% ★ (was 15%) | Clear H2/H3 structure, short paragraphs |
| `cta_effectiveness` | 10% | Specific offer, named product, one action |
| `faq_quality` | 10% | Objection-handling FAQs with affiliate answer |
| `eeat_execution` | 10% ★ NEW | Citations, disclosure, author section executed |
| `internal_links` | 5% ★ NEW | 2+ contextual internal links present |

**Threshold:** 0.80 · **Max retries:** 3 · **Judge model:** claude-opus-4-6

### 7d. Social Score (Revised)

**Key changes:**
- Added `emotional_trigger` (10%) — Is the correct emotional register (fear/greed/curiosity) identified from the research context and applied in the hook? Fear performs best for inflation/economic uncertainty topics; greed for price rally topics; curiosity for data/comparison topics.
- Added `conversation_relevance` (10%) — Does the post reference or connect to a current trending conversation in the niche? Posts anchored to active discussions get significantly more engagement.
- Reduced `hook_strength` to 25% — still the most important criterion but emotional trigger now captures a specific dimension of what makes hooks work.

| Criterion | Weight | What it measures |
|-----------|--------|-----------------|
| `hook_strength` | 25% ★ (was 30%) | Opening line stops scroll |
| `affiliate_relevance` | 20% ★ (was 25%) | Natural, contextual affiliate reference |
| `platform_fit` | 15% ★ (was 20%) | Length, tone, format match platform norms |
| `cta_presence` | 10% ★ (was 15%) | Clear CTA with URL |
| `hashtag_quality` | 10% | 3–5 niche-specific hashtags |
| `emotional_trigger` | 10% ★ NEW | Fear/greed/curiosity correctly applied |
| `conversation_relevance` | 10% ★ NEW | Anchored to trending niche conversation |

**Threshold:** 0.75 · **Max retries:** 2 · **Judge model:** claude-sonnet-4-6

### 7e. Judge Model Assignment (Revised)

| Stage | Judge model | Rationale |
|-------|------------|-----------|
| Research | claude-sonnet-4-6 ★ | Fact-checking and source evaluation — no nuanced judgment needed |
| Planning | claude-opus-4-6 | Conversion architecture judgment — requires high reasoning |
| Content | claude-opus-4-6 | Buying intent evaluation — requires nuanced affiliate judgment |
| Social | claude-sonnet-4-6 ★ | Platform fit and hook evaluation — straightforward criteria |

**Cost impact of this change:** Research and Social now use Sonnet as Judge. Estimated saving: £0.08–0.12 per article run. Over 2–3 articles/day for 30 days: £5–10/month. Small but meaningful — it also reduces pipeline time because Sonnet responds faster than Opus.

### 7f. Scoring Model Calibration — Live Feedback Loop

From Phase 2 onwards, the Performance Intelligence Agent performs a weekly correlation analysis and reports it in the dashboard:

```python
# agents/nodes/performance_intel.py

async def run_scoring_correlation_analysis(db_conn):
    """
    Correlate original content scores with real-world affiliate conversion data.
    Runs weekly after 6+ weeks of data.
    Surfaces in performance report as 'Scoring Model Health'.
    """
    async with db_conn.cursor() as cur:
        await cur.execute("""
            SELECT
                wr.final_score,
                ap.affiliate_clicks,
                ap.conversions,
                ap.avg_position,
                ap.sessions
            FROM workflow_runs wr
            JOIN article_performance ap ON wr.wp_post_id = ap.wp_post_id
            WHERE wr.completed_at > NOW() - INTERVAL '90 days'
              AND wr.status = 'complete'
              AND ap.date > CURRENT_DATE - 30
        """)
        rows = await cur.fetchall()

    if len(rows) < 10:
        return {"status": "insufficient_data", "min_samples": 10}

    scores      = [r["final_score"]      for r in rows]
    conv_rates  = [
        r["conversions"] / max(r["sessions"], 1) for r in rows
    ]

    # Pearson correlation
    correlation = compute_pearson(scores, conv_rates)

    analysis = {
        "sample_size":      len(rows),
        "score_conv_correlation": round(correlation, 3),
        "interpretation":   interpret_correlation(correlation),
        "threshold_recommendation": recommend_threshold(scores, conv_rates),
    }

    # Alert if correlation is weak (< 0.3) — scoring model needs recalibration
    if correlation < 0.3:
        await publish_event("performance.scoring_alert", {
            "correlation":     correlation,
            "recommendation":  "Review Judge Agent prompts and criteria weights",
        })

    return analysis
```

---

## 8. Rich Media Layer

### 8a. Featured Images — Phase 1

Every article receives a DALL-E 3 featured image. The Media Agent runs after content is approved by the Judge, before publishing.

**Cost:** $0.040 per image (standard quality, 1792×1024). For 60 articles/month: $2.40/month. For 90: $3.60/month. Negligible.

**Why this matters beyond aesthetics:** Google's visual search and image carousels are a secondary traffic channel for investment content. An article with a professional-quality image appearing in Google image results for "gold price chart UK" creates an additional click path that text-only articles miss entirely. It also dramatically improves social share previews — the Open Graph image is what appears when someone shares the article on LinkedIn or Twitter.

**Prompt strategy:** Never ask DALL-E to render text. The prompt always specifies: "No text in the image." Use the category style mapping defined in Section 6e to ensure visual consistency across the site.

### 8b. Infographics — Phase 2

Infographics are generated as SVGs using structured data from the Research and Content outputs. They are more valuable than AI-generated images in two specific scenarios:

**Scenario 1 — Comparison articles:** When the Planning Agent creates a "best gold dealers UK" article, the Infographic Agent generates a visual comparison table as an SVG. This is highly shareable, appears in image search, and creates backlink bait — personal finance bloggers link to infographics they cannot easily reproduce themselves.

**Scenario 2 — Process articles:** "How to buy gold" topics generate a step-by-step process infographic. These earn featured snippet placements on Google for "steps to buy gold" queries and are the most-pinned content type on Pinterest in the investment niche.

**Implementation:**

```python
# agents/tools/infographic_renderer.py

def render_comparison_svg(items: list, title: str) -> str:
    """
    Generates a clean comparison table as SVG.
    items: [{"name": str, "score": float, "pros": [str], "link": str}]
    Returns SVG string ready for WordPress upload.
    """
    # PMW brand colours
    GOLD   = "#C9A84C"
    DARK   = "#1A1A2E"
    LIGHT  = "#F5F5F0"
    TEXT   = "#2D2D2D"

    width  = 800
    row_h  = 80
    height = 120 + (len(items) * row_h)

    rows_svg = ""
    for i, item in enumerate(items):
        y    = 120 + (i * row_h)
        bg   = LIGHT if i % 2 == 0 else "#EBEBE6"
        star = "★" * round(item.get("score", 3)) + "☆" * (5 - round(item.get("score", 3)))
        rows_svg += f"""
        <rect x="0" y="{y}" width="{width}" height="{row_h}" fill="{bg}"/>
        <text x="20"  y="{y+50}" font-size="16" fill="{TEXT}" font-weight="bold">{item['name']}</text>
        <text x="300" y="{y+50}" font-size="14" fill="{GOLD}">{star}</text>
        <text x="500" y="{y+50}" font-size="13" fill="{TEXT}">{item.get('highlight','')}</text>
        """

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <rect width="{width}" height="{height}" fill="{DARK}" rx="12"/>
    <text x="{width//2}" y="60" text-anchor="middle" font-size="22" fill="{GOLD}" font-weight="bold">{title}</text>
    <text x="{width//2}" y="90" text-anchor="middle" font-size="13" fill="{LIGHT}">PreciousMarketWatch.com</text>
    {rows_svg}
    </svg>"""
```

### 8c. Video — Phase 4

Weekly "Gold & Silver Price Update" short-form videos using a text-to-video API (Synthesia or HeyGen). 60-second format. Script generated by the Financial Intelligence Agent from the week's price movements and key news.

**Why this is Phase 4, not earlier:** Video requires a consistent presenter identity, brand guidelines for motion, and a script approval workflow. It should not be attempted until the content pipeline is stable and generating revenue. But when implemented, it opens YouTube as a traffic channel — which is currently completely unaddressed by every text-only precious metals affiliate site.

---

## 9. Bridge API Specification

### 9a. Endpoints

```
Authentication
POST   /auth/login                    → { access_token, refresh_token }
POST   /auth/refresh                  → { access_token }
POST   /auth/logout                   → 200

Workflows
POST   /workflow/trigger              → { run_id }
GET    /workflow/runs                 → RunRecord[]
GET    /workflow/runs/{run_id}        → RunRecord (includes media_output)
POST   /workflow/{run_id}/restart     → { queued: true }
PATCH  /workflow/{run_id}/intervene   → { applied: true }
DELETE /workflow/{run_id}/kill        → { killed: true }

Topics
GET    /topics                        → Topic[]
POST   /topics                        → Topic
PUT    /topics/{id}                   → Topic
DELETE /topics/{id}                   → 204
POST   /topics/{id}/run-now           → { run_id }

Agents (authenticated — dashboard)
GET    /agents                        → AgentConfig[]
PUT    /agents/{name}                 → AgentConfig

Agents Public Profiles (unauthenticated — public site)
GET    /agents/public                 → PublicAgentProfile[]
GET    /agents/public/{name}          → PublicAgentProfile

Performance (Phase 2)
GET    /performance/reports           → PerformanceReport[]
GET    /performance/reports/latest    → PerformanceReport
GET    /performance/articles          → ArticlePerformance[]
GET    /performance/scoring-health    → ScoringCorrelation ← NEW

Social (Phase 3)
GET    /social/posts                  → SocialPost[]
PUT    /social/posts/{id}/approve     → SocialPost
PUT    /social/posts/{id}/schedule    → SocialPost
DELETE /social/posts/{id}             → 204

Media
GET    /media/runs/{run_id}           → GeneratedMedia[] ← NEW

Audit
GET    /audit/logs/{run_id}           → AuditExport

Health
GET    /health                        → { status, db, redis, ts }

WebSocket
WS     /ws/events                     → real-time event stream
```

### 9b. WebSocket Event Catalogue

| Event type | Trigger | Key payload fields |
|-----------|---------|-------------------|
| `stage.started` | Agent begins stage | `run_id, stage, attempt` |
| `stage.complete` | Stage passes Judge | `run_id, stage, score, breakdown` |
| `stage.retry` | Stage fails Judge | `run_id, stage, score, weakest_criterion` |
| `stage.awaiting_restart` | Max retries | `run_id, stage, final_score, judge_feedback` |
| `run.complete` | Pipeline done | `run_id, wp_post_id, final_score, total_cost_usd` |
| `run.failed` | Fatal error | `run_id, stage, error` |
| `run.killed` | Operator action | `run_id, killed_by` |
| `intervention.applied` | Human override | `run_id, stage` |
| `media.generated` | ★ NEW | `run_id, type, wp_media_id, cost_usd` |
| `media.warning` | ★ NEW Image failed | `run_id, type, error` |
| `social.generated` | Social ready | `run_id, platforms, post_ids` |
| `performance.report_ready` | Analysis done | `report_id, summary` |
| `performance.scoring_alert` | ★ NEW Weak correlation | `correlation, recommendation` |
| `cost.update` | Any LLM call | `run_id, agent, model, cost_usd` |
| `heartbeat` | Every 30s | `ts, connected_clients` |

---

## 10. Public Agent Profiles

### 10a. Philosophy

The team page on preciousmarketwatch.com introduces each AI agent as a named team member. This serves three purposes: it is a positive E-E-A-T signal (Google rewards sites with identifiable authors and contributors), it builds reader trust by being transparent about AI use, and it differentiates PMW from generic AI content farms that hide their production process.

**Strict rule:** Public profiles expose zero internal mechanics. No model names, no thresholds, no prompt templates, no score data. Only: what the agent does, what it specialises in, its live contribution count, and its current status.

### 10b. Agent Registry

```python
PUBLIC_AGENT_PROFILES = [
    {
        "slug":         "research-analyst",
        "display_name": "The Research Analyst",
        "role":         "Market Research & Data Specialist",
        "tier":         "intelligence",
        "bio":          (
            "Monitors live price feeds, news sources, and market signals before "
            "every article enters production. Gathers a minimum of five authoritative "
            "sources, identifies the most recent developments, and maps out the "
            "specific problems our readers face — and how our recommended services "
            "address them."
        ),
        "specialisms":  ["Gold", "Silver", "Platinum", "Price Data",
                         "News Aggregation", "Market Trends"],
        "status":       "active",
    },
    {
        "slug":         "content-strategist",
        "display_name": "The Content Strategist",
        "role":         "Senior Content Architect",
        "tier":         "editorial",
        "bio":          (
            "Transforms research bundles into structured content plans with a "
            "clear problem-to-solution narrative arc. Ensures every article is "
            "architected to serve the reader first and naturally introduce "
            "recommended products at the moments of highest relevance."
        ),
        "specialisms":  ["Content Architecture", "SEO Strategy",
                         "Affiliate Integration", "Reader Journey Mapping"],
        "status":       "active",
    },
    {
        "slug":         "content-writer",
        "display_name": "The Content Writer",
        "role":         "Specialist Financial Copywriter",
        "tier":         "production",
        "bio":          (
            "Writes complete, publish-ready articles using the research bundle "
            "and content plan. Every article cites specific, dated sources; "
            "uses clear heading structure; and guides readers toward relevant "
            "products without pressure tactics. All content is reviewed by a "
            "human editor before publication."
        ),
        "specialisms":  ["Article Writing", "Precious Metals", "Gemstones",
                         "Investment Copy", "Factual Accuracy"],
        "status":       "active",
    },
    {
        "slug":         "quality-judge",
        "display_name": "The Quality Judge",
        "role":         "Editorial Quality Evaluator",
        "tier":         "editorial",
        "bio":          (
            "Independently evaluates every piece of work before it advances. "
            "Applies structured criteria and returns specific, actionable feedback "
            "when the output does not meet our standards. Nothing reaches the "
            "next stage without passing the Judge's review."
        ),
        "specialisms":  ["Quality Assurance", "Conversion Analysis",
                         "Factual Verification", "Editorial Standards"],
        "status":       "active",
    },
    {
        "slug":         "visual-designer",
        "display_name": "The Visual Designer",
        "role":         "Digital Asset Creator",
        "tier":         "production",
        "bio":          (
            "Creates the featured images and infographics that accompany each "
            "article. Specialises in premium financial photography aesthetics "
            "and data visualisation for investment content."
        ),
        "specialisms":  ["Featured Images", "Infographics",
                         "Data Visualisation", "Brand Consistency"],
        "status":       "active",
    },
    {
        "slug":         "social-author",
        "display_name": "The Social Author",
        "role":         "Social Media Content Specialist",
        "tier":         "production",
        "bio":          (
            "Adapts every published article into platform-native social content "
            "for Twitter, LinkedIn, Facebook, and Instagram. Monitors trending "
            "conversations in the precious metals community to keep PMW "
            "content relevant and timely."
        ),
        "specialisms":  ["Twitter", "LinkedIn", "Facebook", "Instagram",
                         "Engagement", "Trending Topics"],
        "status":       "in-development",
    },
    {
        "slug":         "performance-analyst",
        "display_name": "The Performance Analyst",
        "role":         "Analytics & Optimisation Specialist",
        "tier":         "intelligence",
        "bio":          (
            "Reviews traffic, engagement, and conversion data weekly. "
            "Identifies which content is delivering value for readers and "
            "generating results, and recommends specific improvements. "
            "Closes the feedback loop between what we publish and what "
            "readers actually find useful."
        ),
        "specialisms":  ["Google Analytics", "Search Console", "Heatmaps",
                         "Conversion Optimisation", "SEO Performance"],
        "status":       "in-development",
    },
]
```

---

## 11. Dashboard Specification

### 11a. Screen Map

```
/login          JWT authentication
/               Dashboard Home — today's runs, cost summary, quick stats
/runs           Run History — filterable list with score filter
/runs/:id       Run Detail — Flight Recorder with media preview panel
/runs/:id/audit Audit Export — compliance vault data
/topics         Topic Manager — CRUD + schedule + reader intent override
/agents         Agent Config — thresholds, models, criteria weights
/performance    Performance Panel — weekly report + scoring health
/social         Social Queue — per-platform review and approve
/media          Media Gallery — all generated images and infographics
```

### 11b. Cost Summary Panel (Dashboard Home)

Every run now surfaces total cost. The home dashboard shows:

```
┌──────────────────────────────────────────────────────┐
│  COST SUMMARY                                        │
│  Today:    £0.42  (3 runs)                          │
│  This month: £8.91  (61 runs)                       │
│  Avg per article: £0.14                             │
│  Projected monthly: £14.20                          │
│                                                      │
│  By agent:  Research £2.10  Planning £3.40          │
│             Content  £2.80  Judge    £0.41          │
│             Media    £0.20                          │
└──────────────────────────────────────────────────────┘
```

### 11c. Media Preview in Run Detail

The Flight Recorder (Run Detail screen) now includes a Media panel below the pipeline stages:

```
⑥ Media Agent     ✅  2 assets generated  Cost: $0.04
  ├─ Featured image  ✅  WP Media #2041  [Preview]
  └─ Infographic     ✅  WP Media #2042  [Preview]
```

### 11d. Scoring Health Panel (Phase 2)

In the Performance screen, a Scoring Health card shows the live correlation between content scores and real conversion data:

```
┌──────────────────────────────────────────────────────────┐
│  SCORING MODEL HEALTH                                    │
│  Based on last 90 days — 47 articles with conversion data│
│                                                          │
│  Score ↔ Conversion correlation:  0.64  ● Good          │
│  (Target: > 0.50 — currently tracking well)              │
│                                                          │
│  Articles scoring 0.85+ convert at 4.2% avg             │
│  Articles scoring 0.80–0.84 convert at 2.8% avg         │
│  Articles scoring < 0.80 (escaped) convert at 1.1% avg  │
│                                                          │
│  Recommendation: Thresholds calibrated well.            │
│  Consider raising content threshold to 0.82.            │
└──────────────────────────────────────────────────────────┘
```

---

## 12. Social Content Automation

### 12a. Emotional Trigger Classification

The Research Agent now outputs `emotional_trigger` based on the dominant news context:

```python
EMOTIONAL_TRIGGERS = {
    "fear":      [
        "inflation", "recession", "currency devaluation", "market crash",
        "economic uncertainty", "portfolio protection", "safe haven"
    ],
    "greed":     [
        "all-time high", "price surge", "rally", "bull market",
        "outperforms", "record price", "investment return"
    ],
    "curiosity": [
        "surprising", "did you know", "vs", "comparison", "ranked",
        "how much", "what is", "guide", "explained"
    ],
}

def classify_emotional_trigger(news_items: list, topic_name: str) -> str:
    text = " ".join([item.get("summary", "") for item in news_items]).lower()
    text += " " + topic_name.lower()

    scores = {
        trigger: sum(1 for kw in keywords if kw in text)
        for trigger, keywords in EMOTIONAL_TRIGGERS.items()
    }
    return max(scores, key=scores.get)
```

### 12b. Platform-Specific Templates

```json
{
  "social_twitter_fear": {
    "system": "Write a Twitter post that triggers protective instincts about financial security. Open with a stark fact or question. Max 280 chars. Return JSON only.",
    "user": "Article: {{ article_title }}\nKey fear signal: {{ fear_signal }}\nAffiliate: {{ affiliate_name }}\nURL: {{ article_url }}\nOUTPUT: {\"content\": \"string\", \"hashtags\": [\"string\"]}"
  },
  "social_twitter_greed": {
    "system": "Write a Twitter post that highlights an exciting price or return opportunity. Open with the number or percentage. Max 280 chars. Return JSON only.",
    "user": "Article: {{ article_title }}\nKey stat: {{ key_stat }}\nAffiliate: {{ affiliate_name }}\nURL: {{ article_url }}\nOUTPUT: {\"content\": \"string\", \"hashtags\": [\"string\"]}"
  },
  "social_linkedin": {
    "system": "Write a LinkedIn post for financially sophisticated investors. 2–3 short paragraphs. Professional tone. End with a question to encourage comments. Return JSON only.",
    "user": "Article: {{ article_title }}\nExcerpt: {{ article_excerpt }}\nKey insight: {{ key_insight }}\nURL: {{ article_url }}\nOUTPUT: {\"content\": \"string\", \"hashtags\": [\"string\"]}"
  }
}
```

---

## 13. Analysis Team

### 13a. Performance Intelligence Agent

Runs Monday 06:00 UTC. Pulls GA4, Clarity, Search Console data and generates structured recommendations.

```python
PERFORMANCE_PROMPT = """
You are a senior analytics specialist for a precious metals affiliate blog.
Analyse this week's data and generate specific, actionable recommendations.
Primary goal: increase affiliate click-through rate and qualified leads.
Secondary goal: identify content gaps that represent SEO opportunities.

Key context:
- Articles should drive affiliate clicks at > 3% CTR
- Return visit rate indicates tool engagement or bookmark behaviour  
- High impression / low click = title or meta description needs work
- Low scroll depth = content is not matching reader intent

Always return valid JSON only.
"""
```

### 13b. Scoring Correlation Analysis

Runs after 6+ weeks of data. Computes Pearson correlation between final content scores and real affiliate conversion rates. Alerts operator if correlation is below 0.30 (indicating scoring model is not predictive of actual performance). Results surface in the dashboard Scoring Health panel.

---

## 14. Environment Configuration

### 14a. Railway Variables

**PMW-Bridge:**
```bash
DATABASE_URL              # Injected by Railway
REDIS_URL                 # Injected by Railway
JWT_SECRET                # Min 32 chars
JWT_EXPIRY                = 8h
SERVICE_ROLE              = bridge
WP_API_URL                = https://preciousmarketwatch.com/wp/wp-json
WP_API_USER               # WP application password user
WP_API_PASSWORD           # WP application password
WP_DEFAULT_POST_STATUS    = draft
LOG_LEVEL                 = info
```

**PMW-Agents:**
```bash
DATABASE_URL              # Injected by Railway
REDIS_URL                 # Injected by Railway
ANTHROPIC_API_KEY         # Primary LLM
OPENAI_API_KEY            # For DALL-E 3 image generation
SERVICE_ROLE              = agents
WORKER_CONCURRENCY        = 2
PIPELINE_MODEL            = claude-sonnet-4-6
JUDGE_MODEL               = claude-opus-4-6
JUDGE_MODEL_FAST          = claude-sonnet-4-6   # Research + Social judge
JUDGE_TEMPERATURE         = 0.1
RESEARCH_THRESHOLD        = 0.75
PLANNING_THRESHOLD        = 0.80
CONTENT_THRESHOLD         = 0.80
SOCIAL_THRESHOLD          = 0.75
RESEARCH_MAX_RETRIES      = 3
PLANNING_MAX_RETRIES      = 3
CONTENT_MAX_RETRIES       = 3
IMAGE_GENERATION_ENABLED  = true
IMAGE_QUALITY             = standard           # standard | hd
INFOGRAPHIC_ENABLED       = false              # enable in Phase 2
LANGCHAIN_API_KEY         # LangSmith
LANGCHAIN_TRACING_V2      = true
LANGCHAIN_PROJECT         = pmw-production
SCHEDULER_ENABLED         = true
SCHEDULER_CRON            = 0 8 * * *
SCHEDULER_TIMEZONE        = Europe/London
SERP_API_KEY              # SerpAPI for SERP + PAA fetching
# Phase 2:
GA4_PROPERTY_ID           =
GA4_SERVICE_ACCOUNT       = (base64 JSON)
CLARITY_API_KEY           =
GSC_SERVICE_ACCOUNT       = (base64 JSON)
```

### 14b. .env.example (committed to repo)

```bash
# COMMIT THIS FILE ONLY — NO REAL VALUES

DATABASE_URL=postgresql://user:pass@localhost:5432/pmw
REDIS_URL=redis://:password@localhost:6379
JWT_SECRET=change-me-32-chars-minimum

WP_API_URL=https://preciousmarketwatch.com/wp/wp-json
WP_API_USER=pmw-agent
WP_API_PASSWORD=changeme
WP_DEFAULT_POST_STATUS=draft

ANTHROPIC_API_KEY=changeme
OPENAI_API_KEY=changeme
PIPELINE_MODEL=claude-sonnet-4-6
JUDGE_MODEL=claude-opus-4-6
JUDGE_MODEL_FAST=claude-sonnet-4-6
JUDGE_TEMPERATURE=0.1
WORKER_CONCURRENCY=2

RESEARCH_THRESHOLD=0.75
PLANNING_THRESHOLD=0.80
CONTENT_THRESHOLD=0.80
SOCIAL_THRESHOLD=0.75

IMAGE_GENERATION_ENABLED=true
IMAGE_QUALITY=standard
INFOGRAPHIC_ENABLED=false

LANGCHAIN_API_KEY=changeme
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=pmw-local

SERP_API_KEY=changeme
LOG_LEVEL=info
SCHEDULER_ENABLED=false
SCHEDULER_CRON=0 8 * * *
SCHEDULER_TIMEZONE=Europe/London

GA4_PROPERTY_ID=changeme
CLARITY_API_KEY=changeme
```

---

## 15. GitHub Workflow & CI/CD

### 15a. Branch Strategy

```
main        → deploys to Railway production
feature/*   → PRs against main, tests run automatically
```

### 15b. Deploy Bridge

```yaml
# .github/workflows/deploy-bridge.yml
name: Deploy Bridge
on:
  push:
    branches: [main]
    paths: ['bridge/**', '.github/workflows/deploy-bridge.yml']

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env: { POSTGRES_PASSWORD: testpass, POSTGRES_DB: pmw_test }
        options: --health-cmd pg_isready --health-interval 5s
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11', cache: pip,
                cache-dependency-path: bridge/requirements.txt }
      - run: cd bridge && pip install -r requirements.txt pytest pytest-asyncio httpx
      - run: cd bridge && python -m pytest tests/ -v
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/pmw_test
          REDIS_URL: redis://localhost:6379

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: railwayapp/railway-action@v1
        with: { service: pmw-bridge, token: '${{ secrets.RAILWAY_TOKEN }}' }
```

### 15c. Deploy Agents

```yaml
# .github/workflows/deploy-agents.yml
name: Deploy Agents
on:
  push:
    branches: [main]
    paths: ['agents/**', '.github/workflows/deploy-agents.yml']

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env: { POSTGRES_PASSWORD: testpass, POSTGRES_DB: pmw_test }
        options: --health-cmd pg_isready --health-interval 5s
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: cd agents && pip install -r requirements.txt pytest pytest-asyncio
      - run: cd agents && python -m pytest tests/ -v
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/pmw_test
          REDIS_URL: redis://localhost:6379
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY_TEST }}

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run migrations
        run: cd agents && pip install alembic psycopg2-binary && alembic upgrade head
        env: { DATABASE_URL: '${{ secrets.DATABASE_URL }}' }
      - uses: railwayapp/railway-action@v1
        with: { service: pmw-agents, token: '${{ secrets.RAILWAY_TOKEN }}' }
```

---

## 16. Implementation Phases

### Phase 1 — Content Pipeline + Tools Foundation (Weeks 1–4)

**Agent work:**
- [ ] Railway services deployed and connected
- [ ] Database migrations 001 + 004 run
- [ ] Agent configs seeded with revised scoring weights
- [ ] 10+ topics seeded, 3+ affiliates seeded with commission data
- [ ] Full pipeline: Task Loader → Research (with SERP/PAA) → Judge → Planning (with intent templates + internal links) → Judge → Content (with E-E-A-T) → Judge → Media → Publishing
- [ ] Media Agent: featured image generation active
- [ ] WebSocket events flowing to dashboard
- [ ] React dashboard: Home, Run Detail (with media panel), Run History, Agent Config
- [ ] `/agents/public` returning 5 profiles
- [ ] Cost tracking accurate to 6 decimal places (USD)
- [ ] LangSmith tracing 100% coverage
- [ ] Affiliate disclosure text in all published articles

**Tools work (parallel, WordPress developer):**
- [ ] Gold value calculator live at `/tools/gold-calculator/`
- [ ] Investment return calculator live at `/tools/investment-calculator/`
- [ ] Dealer comparison table live at `/tools/compare-dealers/` (manual data initially)
- [ ] Portfolio tracker live at `/tools/portfolio-tracker/`
- [ ] All tools linked from relevant pillar pages and article footer

**Definition of done — Phase 1:**
- Trigger a run → article draft in WordPress with featured image within 10 minutes
- Article has: affiliate disclosure, 2+ citations, author section, internal link, tool reference
- Dashboard shows live pipeline with cost per stage
- 4 tools live and functional

---

### Phase 2 — Analysis + Scoring Validation (Weeks 5–7)

- [ ] GA4, Clarity, Search Console integrations
- [ ] Database migrations 003 run
- [ ] Performance Intelligence Agent weekly cron
- [ ] Scoring correlation analysis (from Week 7 when 10+ articles have conversion data)
- [ ] Dashboard: Performance Panel, Scoring Health card
- [ ] Infographic generation for comparison articles
- [ ] Dealer comparison table updated weekly by Performance Agent
- [ ] `performance.scoring_alert` notification if correlation < 0.30

**Definition of done — Phase 2:**
- Weekly report appears in dashboard every Monday
- Scoring Health shows correlation for ≥ 10 articles
- Infographic generated for at least one comparison article

---

### Phase 3 — Social Automation (Weeks 8–10)

- [ ] Database migrations 002 run
- [ ] Social Agent with emotional trigger classification
- [ ] Per-platform templates (Twitter fear/greed/curiosity variants + LinkedIn + Facebook + Instagram)
- [ ] Social Queue in dashboard
- [ ] WordPress webhook → social generation trigger
- [ ] Social Author agent profile status: active

---

### Phase 4 — Intelligence + Video (Weeks 11–16)

- [ ] Trend Scout Agent (Google Trends + Reddit API)
- [ ] Content Gap Analyst (competitor keyword analysis)
- [ ] Director Agent: weekly topic calendar suggestions in Topic Manager
- [ ] YouTube Shorts script generation for weekly price updates
- [ ] Text-to-video integration (Synthesia or HeyGen)
- [ ] US Gold IRA content track (Augusta Precious Metals affiliate integration)

---

## 17. Testing Strategy

### 17a. Unit Tests — Coverage Requirements

| Module | Target |
|--------|--------|
| `scoring/base.py` — all composite score functions | 100% |
| `scoring/*_scorer.py` — weight validation, new criteria | 100% |
| `nodes/judge.py` — routing logic | 100% |
| `nodes/media.py` — `build_image_prompt()`, SVG renderers | 90%+ |
| `tools/infographic_renderer.py` — SVG output validation | 90%+ |
| `nodes/publishing.py` — `build_wp_payload()` | 100% |
| Vault hash chain functions | 100% |
| Agent state transitions | 100% |
| All other modules | 80%+ |

### 17b. Integration Tests

| Test | Verifies |
|------|---------|
| Research Agent + SERP tool | `serp_context` populated, `reader_intent` classified |
| Planning Agent + intent template | `consideration_buyer` topic uses correct template |
| Planning Agent + internal links | WP search call made, links returned in output |
| Content Agent + E-E-A-T check | `eeat_execution` criterion verified by Judge |
| Media Agent + image generation | WP media record created, run has `media_output` |
| Media failure non-blocking | Image generation fails → pipeline continues to publish |
| Full pipeline mock LLM | All 6 stages complete, WP draft has image attached |
| Retry with revised weights | Score computed correctly with new criterion weights |
| Social + emotional trigger | Fear topic → fear hook applied in social post |

### 17c. Compliance Tests (Nightly)

| Test | Verifies |
|------|---------|
| Vault immutability | No UPDATE/DELETE on vault_events by app user |
| Hash chain integrity | Zero broken links |
| Orphaned runs | No running runs > 30 min old |
| Affiliate disclosure present | All published articles contain disclosure text |
| No PII in logs | Logs contain no email addresses or names |

---

## 18. KPIs & Success Metrics

### 18a. Technical KPIs

| Metric | Target | Measured from |
|--------|--------|--------------|
| Pipeline success rate | > 80% without AWAITING_RESTART | Day 1 |
| Total pipeline time | < 10 min/article (includes media) | Day 1 |
| Research first-attempt pass rate | > 65% | Week 2 |
| Content first-attempt pass rate | > 70% | Week 2 |
| Score ↔ conversion correlation | > 0.40 | Week 8 (after data accumulates) |
| Media generation success rate | > 95% | Phase 1 |
| Image cost per article | < $0.05 | Phase 1 |
| Judge score variance | < 0.05 std dev | Week 2 |
| Vault DLQ rate | < 1% | Ongoing |
| LangSmith trace coverage | 100% | Day 1 |

### 18b. Business KPIs

| Metric | Target | Measured |
|--------|--------|---------|
| Articles published | 2–3/day | Daily |
| Tools monthly unique users | > 500 by month 3 | Monthly |
| Tool → affiliate click rate | > 8% | Monthly |
| Human intervention rate | < 20% | Weekly |
| Content score at publish | > 0.82 avg | Weekly |
| Organic traffic growth | +40% month-on-month | Monthly |
| Affiliate CTR (articles) | > 3% | Monthly |
| Affiliate CTR (tools) | > 8% | Monthly |
| Return visitor rate | > 25% | Monthly |
| Newsletter signups | > 2% of visitors | Monthly |
| Monthly gross affiliate revenue | £1k (month 4), £5k (month 7), £10k (month 10) | Monthly |

### 18c. Revenue Trajectory Assumptions

These numbers assume:
- UK-focused traffic at the traffic levels stated
- BullionVault as primary affiliate (% of transaction)
- The Royal Mint as secondary affiliate
- Augusta Precious Metals added in Phase 4 for US IRA traffic

If Augusta is added earlier (Phase 2), the £10k target moves to month 7 because a single qualified Augusta lead ($500) equals approximately 10 BullionVault commissions on small purchases.

---

## 19. Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| LLM hallucinations pass Judge | High | Medium | Draft-first publishing. Human review all drafts. `factual_accuracy` requires 5+ sourced facts. Affiliate disclosure builds reader trust if errors found. |
| Revised scoring weights miscalibrated | High | High (prototype) | Thresholds configurable per run. First-attempt pass rates tracked from day 1. Scoring correlation analysis from Phase 2 provides real feedback. |
| DALL-E 3 / image API downtime | Low | Medium | Media failure is non-blocking — article publishes without image. Retried on next manual re-run. |
| Tools not driving return visits | High | Low | Analytics from day 1. If tool pages show < 2 min avg session time at month 2, UX review triggered. |
| Anthropic API rate limiting | Medium | Medium | Exponential backoff. Respect retry-after. Phase 2: dedicated keys per agent. |
| Google SEO devalues AI content | High | Medium | Human review gate. E-E-A-T enforcement in scoring. Named agent authors + disclosure. Factual accuracy enforced. |
| Affiliate commission structure changes | Medium | Medium | All affiliate data in DB — one row change propagates. Phase 3: multiple affiliates per topic category. |
| Augusta Precious Metals affiliate rejected | Medium | Low | Apply with content portfolio from Phase 1. High-quality audit trail demonstrates editorial standards. |
| Railway outage | Medium | Low | LangGraph checkpointing means runs resume. Staging environment for pre-deploy testing. |
| Tool data goes stale (dealer comparison) | Medium | Medium | Performance Agent updates dealer data weekly. Manual override available in dashboard. |

---

## Appendix A — Requirements Files

### bridge/requirements.txt
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
asyncpg==0.30.0
redis[asyncio]==5.2.0
httpx==0.27.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
pydantic==2.9.0
```

### agents/requirements.txt
```
langgraph==0.2.50
langchain-anthropic==0.3.0
langchain-core==0.3.0
anthropic==0.40.0
openai==1.55.0
asyncpg==0.30.0
redis[asyncio]==5.2.0
httpx==0.27.0
python-dotenv==1.0.0
pydantic==2.9.0
alembic==1.14.0
langsmith==0.1.140
apscheduler==3.10.4
google-analytics-data==0.18.0
google-search-console==0.1.0
cairosvg==2.7.1
```

---

## Appendix B — Seed Data

### Affiliates (priority order)

```sql
INSERT INTO affiliates
    (name, url, value_prop, commission_type, commission_rate, cookie_days, geo_focus)
VALUES
('BullionVault',
 'https://www.bullionvault.com/?utm_source=pmw',
 'Buy, sell and store gold, silver and platinum at wholesale prices online. UK regulated.',
 'revenue_share', 0.5, 30, 'uk'),

('The Royal Mint',
 'https://www.royalmint.com/?utm_source=pmw',
 'The UK government mint. Investment gold and silver coins. FCA regulated. Free secure storage.',
 'revenue_share', 1.5, 30, 'uk'),

('Chards',
 'https://www.chards.co.uk/?utm_source=pmw',
 'One of the UK oldest coin dealers. Specialist gold, silver, and platinum bullion since 1964.',
 'revenue_share', 1.0, 30, 'uk'),

('Augusta Precious Metals',
 'https://www.augustapreciousmetals.com/?utm_source=pmw',
 'America most transparent gold IRA company 2022-2024. Harvard-trained economist onboarding.',
 'per_lead', 500.00, 90, 'us'),

('GoldBroker',
 'https://goldbroker.com/?utm_source=pmw',
 'Physical gold and silver with vault storage in Zurich, New York, and Singapore.',
 'revenue_share', 0.25, 60, 'global');
```

### Initial Topics (15)

```sql
INSERT INTO topics
    (topic_name, topic_category, target_keyword, affiliate_id,
     reader_intent, schedule_cron, priority)
VALUES
-- High priority UK gold (BullionVault)
('Gold Price Today UK',       'gold', 'gold price uk today',      1, 'price_checker',       '0 7 * * *', 1),
('Best Gold Dealers UK 2026', 'gold', 'best place to buy gold uk', 1, 'consideration_buyer', '0 9 * * 1', 1),
('How to Buy Gold UK Safely', 'gold', 'how to buy gold uk',        1, 'consideration_buyer', NULL,        1),

-- Silver (Royal Mint)
('Silver Price UK Today',         'silver', 'silver price uk',       2, 'price_checker',       '0 7 * * *', 1),
('Best Way to Buy Silver UK',     'silver', 'buy silver uk',         2, 'consideration_buyer', '0 9 * * 2', 2),
('Silver Investment Guide 2026',  'silver', 'silver investment uk',  2, 'curiosity_reader',    NULL,        2),

-- US Gold IRA (Augusta — Phase 4 focus but seed now)
('Gold IRA Rules 2026',              'ira', 'gold ira rules',           4, 'consideration_buyer', NULL, 2),
('Best Gold IRA Companies 2026',     'ira', 'best gold ira company',    4, 'consideration_buyer', '0 9 * * 4', 2),
('How to Convert 401k to Gold IRA',  'ira', '401k to gold ira rollover', 4, 'consideration_buyer', NULL, 3),

-- Platinum (Chards)
('Platinum Investment Guide',    'platinum', 'platinum investment',    3, 'consideration_buyer', NULL,        3),
('Palladium vs Platinum 2026',   'platinum', 'palladium vs platinum',  3, 'curiosity_reader',    NULL,        3),

-- Gemstones (Chards)
('Diamond Buying Guide 2026',    'gemstones', 'how to buy diamonds',   3, 'consideration_buyer', NULL,        3),
('Ruby vs Garnet Investment',    'gemstones', 'ruby vs garnet value',  3, 'curiosity_reader',    NULL,        4),

-- GoldBroker international
('Gold Storage Outside UK',       'gold', 'offshore gold storage',     5, 'consideration_buyer', NULL, 3),
('Gold Silver Ratio Explained',   'gold', 'gold silver ratio',         1, 'curiosity_reader',    NULL, 3);
```

---

## Appendix C — Local Development Setup

```bash
# 1. Clone
git clone https://github.com/YOUR_ORG/pmw-agents.git
cd pmw-agents

# 2. Environment
cp .env.example .env.local
# Edit .env.local — add ANTHROPIC_API_KEY, OPENAI_API_KEY, SERP_API_KEY

# 3. Start infrastructure
docker compose up -d

# 4. Run all migrations
cd agents
python -m alembic upgrade head

# 5. Seed data
python scripts/seed.py

# 6. Start bridge (terminal 1)
cd bridge && uvicorn main:app --reload --port 8000

# 7. Start agents (terminal 2)
cd agents && python main.py

# 8. Start dashboard (terminal 3)
cd dashboard && npm install && npm run dev

# 9. Trigger test run (verifies full pipeline)
curl -X POST http://localhost:8000/workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{"topic_id": 1}'

# 10. Watch Flight Recorder at http://localhost:5173
# Expected: pipeline completes in < 10 minutes
# Expected: WP draft created with featured image
# Expected: Article has affiliate disclosure + 2+ citations + internal link
```

---

## Appendix D — Tools Development Guide

The 4 priority tools should be built as React components embedded in WordPress pages via Gutenberg blocks or shortcodes. They require no backend beyond the live price API you already have on your pillar pages.

**Tech stack for tools:**
- React 18 (already used on site)
- Recharts for investment return calculator charts
- MetalPriceAPI or your existing price feed for live data
- localStorage for portfolio tracker persistence
- Cloudflare CDN caches tool pages — set Cache-Control: max-age=300 (5 min) to ensure prices are reasonably fresh

**Affiliate CTA pattern for tools:**
1. User interacts with tool
2. Calculation result appears
3. Immediately below result: contextual affiliate CTA tied to the calculation
4. CTA copy must reference the specific number the user just calculated
5. Track tool → affiliate click separately in GA4 (`event: tool_affiliate_click, tool_name: gold_calculator`)

**Example CTA copy patterns:**
- Gold calculator: "Your gold is worth approximately **£{value}** today. BullionVault offers competitive buy prices with same-day settlement. [Get a free quote →]"
- Investment return: "Gold returned **{pct}%** over your period. Start investing from £25 with BullionVault — no storage fees for the first year. [Open an account →]"
- Portfolio tracker: "Your portfolio is worth **£{total}** today. Insure it with BullionVault's fully allocated storage — your metals, your name, your vault. [Learn more →]"

---

*Document version 2.0 — February 2026*  
*Next review: end of Phase 1 (after Definition of Done achieved)*  
*Owner: PMW Engineering*