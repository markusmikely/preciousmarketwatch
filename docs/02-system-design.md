# System Design: Precious Market Watch

## 📋 Executive Summary
Precious Market Watch is an AI-powered affiliate blogging platform that automates content creation for the precious metals and gemstones niche. The system combines modern web technologies with AI agents to research, generate, and publish content while maintaining factual accuracy and SEO optimization.

## 🎯 System Goals
1. **Automation**: Reduce manual content creation by 80%
2. **Accuracy**: Maintain 95%+ factual accuracy in AI-generated content
3. **Performance**: Sub-2-second page load times
4. **Scalability**: Support daily generation of 2-3 quality articles
5. **Revenue**: Drive 30% quarterly affiliate revenue growth

## 🏗️ Architecture Overview

### High-Level Architecture

#### 1. **System Overview**
```mermaid
graph TB
    subgraph Clients["🖥️ Client Layer"]
        WEB["Main Website<br/>(React)<br/>— No Auth —"]
        DASH["Agent Dashboard<br/>(React)<br/>— JWT Protected —"]
    end

    subgraph Auth["🔐 Auth Layer"]
        JWT["JWT Auth Service<br/>(Dashboard only)"]
        GUARD["Route Guard<br/>(Engine API)"]
    end

    subgraph Delivery["⚡ Delivery Layer"]
        CDN["CDN<br/>(Static Assets + Cache)"]
        LB["Load Balancer"]
    end

    subgraph APIs["🔌 API Layer"]
        WP["WordPress API<br/>(REST + GraphQL)"]
        ENGINE["Agent Workflow Engine<br/>(Custom API)"]
    end

    subgraph RealTime["🔄 Real-Time Layer"]
        WS["WebSocket Server<br/>(Live Agent Updates)"]
    end

    subgraph AgentLayer["🤖 Agent Layer"]
        ORCH["Orchestrator<br/>(LangGraph)"]
        MQ["Message Queue<br/>(Task Bus)"]

        subgraph AgentPool["Agent Pool — Concurrent where independent"]
            RA["Research Agent"]
            CA["Content Agent"]
            FC["Fact Check Agent"]
            SEO["SEO Agent"]
            IMP["WP Import Agent"]
        end
    end

    subgraph Data["🗄️ Data Layer"]
        DB[("SQL Database<br/>(Shared — Prototype)")]
        CACHE["Object Cache<br/>(Redis)"]
    end

    %% Public site — no auth
    WEB -->|"GraphQL / REST"| CDN
    CDN -->|"Cache miss"| LB
    LB --> WP

    %% Dashboard — auth required
    DASH -->|"Login"| JWT
    JWT -->|"Issue token"| DASH
    DASH -->|"REST + JWT"| GUARD
    GUARD --> ENGINE
    DASH <-->|"WebSocket + JWT"| WS
    WS --> ENGINE

    %% Engine to queue
    ENGINE -->|"Dispatch workflow"| ORCH
    ORCH -->|"Publish tasks"| MQ

    %% Queue to agents — concurrent unless blocked by dependency
    MQ -->|"Task: research"| RA
    MQ -->|"Task: content<br/>[depends: research ✓]"| CA
    MQ -->|"Task: fact-check<br/>[depends: content ✓]"| FC
    MQ -->|"Task: seo<br/>[depends: content ✓]"| SEO
    MQ -->|"Task: import<br/>[depends: fact-check ✓, seo ✓]"| IMP

    %% Agents report back
    RA -->|"Result + ready flag"| ORCH
    CA -->|"Result + ready flag"| ORCH
    FC -->|"Result + ready flag"| ORCH
    SEO -->|"Result + ready flag"| ORCH
    IMP -->|"Publish to WP"| WP

    %% Orchestrator pushes status to WS
    ORCH -->|"Broadcast status"| WS

    %% Data access
    WP --> CACHE
    CACHE -->|"Cache miss"| DB
    ENGINE --> DB
    ORCH --> DB
    RA --> DB
    CA --> DB
    FC --> DB
    SEO --> DB
    IMP --> DB
```

---

## 1a. Agent Dependency Model — Pipeline Overview

> This is a **strictly sequential pipeline**. Each agent depends on the previous completing and passing its quality threshold score before the next is released to the queue. There is no concurrency in v1 — correctness of each stage gates the next.

```mermaid
graph TD
    TRIG(["⚡ TriggerManual or Scheduled"])

    TRIG -->|"Load topics for todayor specific task_id"| TL

    TL["📋 Task LoaderValidates task has all requiredcomponents: topic, affiliate,target keyword, metadata"]

    TL -->|"Validation passedtask_status = queued"| MQ1[/"Queue"/]
    TL -->|"Validation failed"| FAIL_TL(["❌ FailedMissing required fields"])

    MQ1 --> RA

    subgraph RA_LOOP["Research Agent — retry loop"]
        RA["🔍 Research AgentCollects facts, news,trends for topic"]
        RA_SCORE{"Score ≥threshold?"}
        RA_RETRY{"Retriesremaining?"}
        RA --> RA_SCORE
        RA_SCORE -->|"No"| RA_RETRY
        RA_RETRY -->|"Yes — retry"| RA
        RA_RETRY -->|"No"| FAIL_RA
    end

    FAIL_RA(["❌ Research FailedMax retries exceeded"])
    RA_SCORE -->|"Yesresearch_ready = true"| MQ2[/"Queue"/]

    MQ2 --> CP

    subgraph CP_LOOP["Content Planning Agent — retry loop"]
        CP["📐 Content Planning AgentStructured prompt producescontent plan: sections,angles, affiliate placement"]
        CP_SCORE{"Score ≥threshold?"}
        CP_RETRY{"Retriesremaining?"}
        CP --> CP_SCORE
        CP_SCORE -->|"No"| CP_RETRY
        CP_RETRY -->|"Yes — retry"| CP
        CP_RETRY -->|"No"| FAIL_CP
    end

    FAIL_CP(["❌ Planning FailedMax retries exceeded"])
    CP_SCORE -->|"Yesplanning_ready = true"| MQ3[/"Queue"/]

    MQ3 --> CG

    subgraph CG_LOOP["Content Generation Agent — retry loop"]
        CG["✍️ Content Generation AgentProduces full article draftfrom content plan"]
        CG_SCORE{"Score ≥threshold?"}
        CG_RETRY{"Retriesremaining?"}
        CG --> CG_SCORE
        CG_SCORE -->|"No"| CG_RETRY
        CG_RETRY -->|"Yes — retry"| CG
        CG_RETRY -->|"No"| FAIL_CG
    end

    FAIL_CG(["❌ Generation FailedMax retries exceeded"])
    CG_SCORE -->|"Yescontent_ready = true"| MQ4[/"Queue"/]

    MQ4 --> PUB

    PUB["📤 Publishing AgentFormats + pushes articleto WordPress via API"]
    PUB -->|"wp_post_id returned"| DONE(["✅ Article Published"])
    PUB -->|"WP API error"| FAIL_PUB(["❌ Publish FailedManual intervention required"])

    style FAIL_TL fill:#f8d7da,stroke:#dc3545
    style FAIL_RA fill:#f8d7da,stroke:#dc3545
    style FAIL_CP fill:#f8d7da,stroke:#dc3545
    style FAIL_CG fill:#f8d7da,stroke:#dc3545
    style FAIL_PUB fill:#f8d7da,stroke:#dc3545
    style DONE fill:#d4edda,stroke:#28a745
    style TL fill:#cce5ff,stroke:#004085
    style RA fill:#cce5ff,stroke:#004085
    style CP fill:#cce5ff,stroke:#004085
    style CG fill:#cce5ff,stroke:#004085
    style PUB fill:#cce5ff,stroke:#004085
```

---

## 1b. Agent Behaviour Reference

| Agent | Input | Output | Threshold | Max Retries | Failure Behaviour |
|-------|-------|--------|-----------|-------------|-------------------|
| **Task Loader** | `task_id` or today's topic list | Validated task record pushed to queue | All required fields present | 0 (no retry — fix data) | Mark task `invalid`, alert |
| **Research Agent** | Task record (topic, affiliate, keyword) | Scored research bundle: facts, news, trends | Configurable score (e.g. ≥ 0.75) | Configurable (e.g. 3) | Mark run `research_failed` |
| **Content Planning Agent** | Research bundle | Scored content plan: sections, angles, CTA placement | Configurable score (e.g. ≥ 0.80) | Configurable (e.g. 3) | Mark run `planning_failed` |
| **Content Generation Agent** | Content plan + research bundle | Scored article draft | Configurable score (e.g. ≥ 0.80) | Configurable (e.g. 3) | Mark run `generation_failed` |
| **Publishing Agent** | Final article draft | WordPress post ID | WP API 200 response | 2 (network retry only) | Mark run `publish_failed`, alert |

---

## 1c. Workflow Run Schema (Dependency Flags + Retry Tracking)

> Each `pmw_workflow_runs` row represents one article's full journey. Ready flags gate the next stage. Attempt counts and scores are recorded per agent for observability and tuning.

```mermaid
erDiagram
    pmw_topics {
        int id PK
        string title "Article topic"
        string target_keyword
        string affiliate_id FK
        string status "pending | queued | in_progress | published | failed"
        date scheduled_date "Which day to publish"
        datetime created_at
    }

    pmw_affiliates {
        int id PK
        string name
        string product_url
        decimal commission_rate
        string status "active | paused"
    }

    pmw_workflow_runs {
        int id PK
        int topic_id FK
        string status "pending | running | complete | failed"
        datetime started_at
        datetime completed_at

        boolean task_loaded "Task Loader passed validation"

        boolean research_ready "Research Agent passed threshold"
        json research_output "Facts, news, trends bundle"
        float research_score "Quality score 0.0–1.0"
        int research_attempts "Number of attempts made"

        boolean planning_ready "Content Planning Agent passed threshold"
        json planning_output "Content plan: sections, angles, CTAs"
        float planning_score
        int planning_attempts

        boolean content_ready "Content Generation Agent passed threshold"
        json content_output "Full article draft"
        float content_score
        int content_attempts

        boolean published "Publishing Agent succeeded"
        int wp_post_id "WordPress post ID"

        string failed_at_stage "task_loader | research | planning | content | publishing"
        text failure_reason
    }

    pmw_task_queue {
        int id PK
        int run_id FK
        string agent_type "task_loader | research | planning | content | publishing"
        string status "queued | claimed | done | failed"
        json payload "Input passed to agent"
        json result "Output returned by agent"
        float score "Quality score if applicable"
        int attempt_number "Which attempt this is"
        datetime queued_at
        datetime claimed_at
        datetime completed_at
    }

    pmw_agents {
        int id PK
        string agent_type
        string status "idle | busy | error"
        json config "model, temperature, prompt templates, score_threshold, max_retries"
        datetime last_active
    }

    pmw_topics ||--o{ pmw_workflow_runs : "runs through"
    pmw_affiliates ||--o{ pmw_topics : "promoted by"
    pmw_workflow_runs ||--o{ pmw_task_queue : "generates tasks"
    pmw_agents ||--o{ pmw_task_queue : "claims and works"
```

---

## 2. Main Website — Data Flow

> Public-facing React app. No authentication. Newsletter signup only.

```mermaid
sequenceDiagram
    participant U as 🧑 User (Browser)
    participant CDN as CDN
    participant LB as Load Balancer
    participant WP as WordPress GraphQL API
    participant CACHE as Object Cache
    participant DB as SQL Database

    U->>CDN: Request page / static assets
    CDN-->>U: Serve cached static assets (HTML, JS, CSS)

    U->>CDN: GraphQL query (e.g. fetch articles)
    alt Cache HIT
        CDN-->>U: Return cached response
    else Cache MISS
        CDN->>LB: Forward request
        LB->>WP: Route to WordPress API
        WP->>CACHE: Check object cache
        alt Object Cache HIT
            CACHE-->>WP: Return cached data
        else Object Cache MISS
            WP->>DB: Query database
            DB-->>WP: Return data
            WP->>CACHE: Store in object cache
        end
        WP-->>LB: Return response
        LB-->>CDN: Return response
        CDN-->>U: Return response (+ cache for TTL)
    end

    U->>WP: POST /newsletter-signup
    WP->>DB: INSERT subscriber record
    WP-->>U: 200 OK
```

---

## 3. Agent Dashboard — Data Flow

> Internal React dashboard. JWT-protected. REST for actions, WebSocket for live pipeline updates.

### 3a. Authentication Flow


```mermaid
sequenceDiagram
    participant U as 👤 User (Browser)
    participant DASH as React Dashboard
    participant JWT as JWT Auth Service
    participant ENGINE as Workflow Engine API
    participant LOG as failure.log

    U->>DASH: Navigate to dashboard
    DASH-->>U: Render login screen

    U->>DASH: Submit credentials
    DASH->>JWT: POST /auth/login { email, password }

    alt Invalid credentials
        JWT-->>DASH: 401 Unauthorised
        DASH-->>U: Show error message
        JWT->>LOG: WARN login_failed { email, ip, timestamp }
    else Valid credentials
        JWT->>JWT: Sign JWT { userId, role, exp: +8h }
        JWT-->>DASH: 200 { token, refreshToken }
        DASH->>DASH: Store token in memory
        DASH-->>U: Redirect to dashboard home
    end

    Note over DASH,ENGINE: All subsequent API calls include Authorization: Bearer token

    DASH->>ENGINE: GET /api/v1/runs { Authorization: Bearer token }

    alt Token expired or invalid
        ENGINE-->>DASH: 401 Unauthorised
        DASH->>JWT: POST /auth/refresh { refreshToken }
        alt Refresh valid
            JWT-->>DASH: 200 { token }
            DASH->>ENGINE: Retry original request
        else Refresh expired
            JWT-->>DASH: 401 Session expired
            DASH-->>U: Redirect to login
        end
    else Token valid
        ENGINE-->>DASH: 200 JSON response
        DASH-->>U: Render data
    end
```

---


```mermaid
sequenceDiagram
    participant A as 🧑‍💼 Agent (Browser)
    participant DASH as React Dashboard
    participant ENGINE as Workflow Engine API
    participant WS as WebSocket Server
    participant DB as SQL Database

    Note over A,WS: Initial Load & Connection

    A->>DASH: Open dashboard
    DASH->>ENGINE: GET /api/v1/agents (REST)
    ENGINE->>DB: SELECT agents
    DB-->>ENGINE: Agent records
    ENGINE-->>DASH: 200 JSON response
    DASH-->>A: Render agent list

    DASH->>WS: Upgrade → WebSocket connection
    WS-->>DASH: Connection established ✓

    Note over A,WS: Live Operation

    A->>DASH: Trigger workflow action
    DASH->>ENGINE: POST /api/v1/workflows/:id/run (REST)
    ENGINE->>DB: INSERT workflow_run record
    ENGINE->>WS: Broadcast status update
    WS-->>DASH: { event: "workflow.started", id: "..." }
    DASH-->>A: UI updates live

    ENGINE->>DB: UPDATE workflow_run (progress)
    ENGINE->>WS: Broadcast progress event
    WS-->>DASH: { event: "workflow.progress", pct: 42 }
    DASH-->>A: Progress indicator updates

    ENGINE->>DB: UPDATE workflow_run (complete)
    ENGINE->>WS: Broadcast completion event
    WS-->>DASH: { event: "workflow.complete", result: {...} }
    DASH-->>A: Show result
```

---

## 4. API Layer Detail

### 4a. WordPress API (Main Website Backend)

```mermaid
graph LR
    subgraph WP_API["WordPress API"]
        direction TB
        GQL["WPGraphQL/graphql endpoint"]
        REST["WP REST API/wp-json/wp/v2/"]
        NL["Newsletter Handler/wp-json/pmw/v1/subscribe"]
        HOOK["Action / Filter Hooks"]
    end

    subgraph WP_DATA["WordPress Data"]
        CPT["Custom Post Types(Articles, Prices, Reports)"]
        META["Post Meta(Market Data)"]
        OPT["Options / Settings"]
    end

    GQL --> CPT
    GQL --> META
    REST --> CPT
    NL --> OPT
    HOOK --> CPT
```


### 4b. Agent Workflow Engine — "Flight Recorder" API

> The Engine is designed as an **Agentic Observability platform**, not a standard CRUD API. Every agent thought, tool call, score, retry, and human intervention is recorded as an immutable event. This architecture satisfies EU AI Act requirements for traceability (Art. 12), transparency (Art. 50), risk management (Art. 9), and human oversight (Art. 14).

---

#### API Surface — Component Map

```mermaid
graph TB
    subgraph AUTH["🔐 Auth Middleware"]
        JWT_G["JWT GuardAll routes except /auth"]
    end

    subgraph WF["📋 Workflow & Execution"]
        WF1["POST /workflows/trigger"]
        WF2["GET /workflows/{run_id}/trace"]
        WF3["POST /workflows/{run_id}/restart"]
        WF4["PATCH /workflows/{run_id}/intervene"]
        WF5["DELETE /workflows/{run_id}/kill"]
    end

    subgraph SCORE["📊 Scoring & Evaluation"]
        SC1["GET /agents/{agent_id}/config"]
        SC2["POST /eval/score"]
        SC3["GET /threshold/{run_id}"]
    end

    subgraph COMPLY["⚖️ EU AI Act Compliance"]
        CO1["GET /audit/logs/{run_id}"]
        CO2["GET /transparency/disclosure"]
        CO3["GET /risk/assessment"]
    end

    subgraph WS["🔄 WebSocket — Live Events"]
        WS1["stage.started"]
        WS2["stage.complete"]
        WS3["stage.retry"]
        WS4["stage.awaiting_restart"]
        WS5["run.complete"]
        WS6["run.failed"]
        WS7["intervention.applied"]
        WS8["run.killed"]
    end

    subgraph SINK["🗄️ Data & Log Sinks"]
        DB[("SQL Database")]
        LOG["failure.log(structured JSON)"]
        VAULT["Compliance Vault(immutable audit store)"]
    end

    JWT_G --> WF
    JWT_G --> SCORE
    JWT_G --> COMPLY

    WF --> DB
    WF --> LOG
    WF --> WS
    WF --> VAULT

    SCORE --> DB
    COMPLY --> VAULT
    COMPLY --> DB
```

---

#### Group 1 — Workflow & Execution Endpoints

```mermaid
sequenceDiagram
    participant C as Client
    participant E as Engine API
    participant O as Orchestrator
    participant DB as Database
    participant V as Compliance Vault

    Note over C,V: POST /workflows/trigger — start a unique run

    C->>E: POST /workflows/trigger{ topic_id, overrides: { research: { threshold: 0.9 } } }
    E->>DB: INSERT pmw_workflow_runs { topic_id, overrides, status: pending }
    DB-->>E: run_id: 101
    E->>V: WRITE run_created event { run_id, topic_id, overrides, timestamp, user_id }
    E->>O: Dispatch run_id: 101
    E-->>C: 202 Accepted { run_id: 101 }

    Note over C,V: GET /workflows/{run_id}/trace — full thought tree

    C->>E: GET /workflows/101/trace
    E->>DB: SELECT all task_queue rows + agent_thoughts WHERE run_id = 101
    DB-->>E: Full event tree
    E-->>C: 200 { run_id, stages: [{ agent, attempts: [{ prompt, response, tool_calls, score, passed, timestamp }] }] }

    Note over C,V: POST /workflows/{run_id}/restart — resume from failed step

    C->>E: POST /workflows/101/restart { from_stage: planning }
    E->>DB: SELECT preserved outputs WHERE run_id = 101 AND stage IN (task_loader, research)
    E->>DB: UPDATE run SET status = running, failed_at_stage = null
    E->>V: WRITE human_restart event { run_id, from_stage: planning, user_id, timestamp }
    E->>O: Dispatch run_id: 101 from stage: planning
    E-->>C: 202 Accepted { run_id: 101, resuming_from: planning }

    Note over C,V: PATCH /workflows/{run_id}/intervene — human corrects mid-flight

    C->>E: PATCH /workflows/101/intervene{ stage: content, corrected_output: { ... }, resume: true }
    E->>DB: UPDATE task_queue SET result = corrected_output, status = done (for stage: content)
    E->>DB: UPDATE run SET content_ready = true, intervention = true
    E->>V: WRITE human_intervention event { run_id, stage, original, corrected, user_id, timestamp }
    E->>O: Resume from next stage
    E-->>C: 200 OK { run_id: 101, intervention_logged: true, resuming_from: publishing }

    Note over C,V: DELETE /workflows/{run_id}/kill — emergency halt

    C->>E: DELETE /workflows/101/kill
    E->>O: HALT all active tasks for run_id: 101
    E->>DB: UPDATE run SET status = killed
    E->>V: WRITE kill_event { run_id, user_id, timestamp, reason: manual }
    E-->>C: 200 OK { run_id: 101, status: killed }
```

---

#### Group 2 — Scoring & Evaluation Endpoints

| Endpoint | Method | Purpose | Request | Response |
|----------|--------|---------|---------|----------|
| `/agents/{agent_id}/config` | GET | Retrieve scoring rubric for an agent | — | `{ agent_type, model, threshold, max_retries, criteria: [{ name, weight, description }] }` |
| `/eval/score` | POST | Judge Agent evaluates output against criterion | `{ run_id, stage, output, criteria }` | `{ score, breakdown: [{ criterion, score, reasoning }], passed }` |
| `/threshold/{run_id}` | GET | Check current stage score vs threshold | — | `{ stage, score, threshold, status: passed \| awaiting_restart \| failed_threshold }` |

**Scoring rubric example — Research Agent:**

```json
{
  "agent_type": "research",
  "model": "claude-sonnet-4-6",
  "threshold": 0.75,
  "max_retries": 3,
  "criteria": [
    { "name": "source_count",    "weight": 0.20, "description": "Minimum 5 distinct sources" },
    { "name": "recency",         "weight": 0.25, "description": "At least 3 sources from last 30 days" },
    { "name": "relevance",       "weight": 0.30, "description": "Sources directly address topic + keyword" },
    { "name": "factual_density", "weight": 0.25, "description": "Concrete data points, prices, statistics present" }
  ]
}
```

**Threshold behaviour:**

```mermaid
graph LR
    EVAL["Judge Agentscores output"]
    CHECK{"score >=threshold?"}
    PASS["Set ready flagEnqueue next stage"]
    RETRY{"Retriesremaining?"}
    AWAIT["Status: AWAITING_RESTARTWS → stage.awaiting_restartDashboard: show Restart button"]
    FAIL["Status: FAILED_THRESHOLDWrite to failure.logWS → run.failed"]

    EVAL --> CHECK
    CHECK -->|"Yes"| PASS
    CHECK -->|"No"| RETRY
    RETRY -->|"Yes"| EVAL
    RETRY -->|"No — threshold override available"| AWAIT
    AWAIT -->|"No override / time limit"| FAIL
```

> **`AWAITING_RESTART` vs `FAILED_THRESHOLD`:** When max retries are exhausted, the run enters `AWAITING_RESTART` and the dashboard surfaces a manual restart button. If no human action is taken within a configurable window (e.g. 24 hours), it transitions to `FAILED_THRESHOLD` and is logged as a terminal failure.

---

#### Group 3 — EU AI Act Compliance Endpoints

| Endpoint | Method | EU AI Act Article | Purpose | Output |
|----------|--------|-------------------|---------|--------|
| `GET /audit/logs/{run_id}` | GET | Art. 12 — Traceability | Immutable export of every prompt, model response, tool call, score, and intervention for a run | JSON or PDF bundle |
| `GET /transparency/disclosure` | GET | Art. 50 — Transparency | Generates the required disclosure statement identifying which content is AI-generated | `{ disclosure_text, affected_sections, model_versions_used }` |
| `GET /risk/assessment` | GET | Art. 9 — Risk Management | Dashboard view of score drift, hallucination flags, and failure rates across all runs | `{ runs_assessed, avg_scores_by_stage, failure_rate, drift_flags }` |
| `DELETE /workflows/{run_id}/kill` | DELETE | Art. 14 — Human Oversight | Emergency halt — stops all API calls, clears in-flight data from memory | `{ status: killed, vault_entry_id }` |

**Audit log structure (per run):**

```json
{
  "run_id": 101,
  "topic_id": 42,
  "started_at": "2026-02-19T09:00:00Z",
  "completed_at": "2026-02-19T09:14:32Z",
  "triggered_by": "user_id:7 (manual)",
  "overrides_applied": { "research": { "threshold": 0.9 } },
  "stages": [
    {
      "stage": "research",
      "attempts": [
        {
          "attempt": 1,
          "model": "claude-sonnet-4-6",
          "prompt_hash": "sha256:a3f9...",
          "tool_calls": ["fetch_news(gold)", "fetch_price_history(gold, 30d)"],
          "score": 0.61,
          "passed": false,
          "timestamp": "2026-02-19T09:01:14Z"
        },
        {
          "attempt": 2,
          "model": "claude-sonnet-4-6",
          "prompt_hash": "sha256:b7c2...",
          "tool_calls": ["fetch_news(gold)", "fetch_trends(gold, silver)"],
          "score": 0.82,
          "passed": true,
          "timestamp": "2026-02-19T09:03:47Z"
        }
      ]
    }
  ],
  "interventions": [],
  "human_restarts": [],
  "final_status": "complete",
  "wp_post_id": 5821
}
```

---

#### WebSocket Event Catalogue

All events are broadcast on the authenticated WebSocket connection. Every event carries `run_id` and `timestamp` as base fields.

| Event | Trigger | Payload |
|-------|---------|---------|
| `stage.started` | Orchestrator enqueues a stage | `{ run_id, stage, attempt }` |
| `stage.complete` | Agent passes threshold | `{ run_id, stage, score, attempt, duration_ms }` |
| `stage.retry` | Agent fails threshold, retries remain | `{ run_id, stage, score, threshold, attempt, max_attempts }` |
| `stage.awaiting_restart` | Max retries exhausted, human action needed | `{ run_id, stage, final_score, threshold, attempts }` |
| `run.complete` | Publishing agent succeeds | `{ run_id, wp_post_id, total_duration_ms }` |
| `run.failed` | Terminal failure (threshold or publish error) | `{ run_id, failed_at_stage, reason, attempts }` |
| `intervention.applied` | Human corrects output mid-flight | `{ run_id, stage, corrected_by_user_id, resuming_from }` |
| `run.killed` | Kill switch activated | `{ run_id, killed_by_user_id }` |


---

## 5. Database Schema (Prototype — Shared SQL)

> Single MySQL database serving both WordPress and the Workflow Engine in prototype phase. Tables are namespaced by prefix (`wp_` for WordPress, `pmw_` for the engine) to avoid collisions. The Compliance Vault tables (`pmw_vault_*`) are enforced as append-only through MySQL triggers — see Section 5b.

---

### 5a. Full Schema

```mermaid
erDiagram

    %% ─── WordPress tables ───────────────────────────────
    wp_posts {
        bigint ID PK
        string post_title
        string post_type
        string post_status
        datetime post_date
    }
    wp_postmeta {
        bigint meta_id PK
        bigint post_id FK
        string meta_key
        text meta_value
    }
    wp_pmw_subscribers {
        int id PK
        string email
        datetime subscribed_at
        string status
    }

    %% ─── Topics & Affiliates ────────────────────────────
    pmw_affiliates {
        int id PK
        string name
        string product_url
        decimal commission_rate
        string status "active | paused"
        datetime created_at
    }
    pmw_topics {
        int id PK
        int affiliate_id FK
        string title
        string target_keyword
        string status "pending | queued | in_progress | published | failed"
        date scheduled_date
        datetime created_at
    }

    %% ─── Agent configuration ────────────────────────────
    pmw_agents {
        int id PK
        string agent_type "task_loader | research | planning | content | publishing"
        string status "idle | busy | error"
        float score_threshold
        int max_retries
        string model "LLM model identifier"
        json prompt_templates
        json scoring_criteria "Array of criterion with weights"
        datetime last_active
        datetime updated_at
    }

    %% ─── Workflow runs ──────────────────────────────────
    pmw_workflow_runs {
        int id PK
        int topic_id FK
        string status "pending | running | awaiting_restart | complete | failed_threshold | killed"
        json overrides "Per-run threshold overrides"
        int triggered_by_user_id
        string trigger_type "manual | scheduled"
        datetime started_at
        datetime completed_at

        boolean task_loaded
        boolean research_ready
        float research_score
        int research_attempts
        json research_output

        boolean planning_ready
        float planning_score
        int planning_attempts
        json planning_output

        boolean content_ready
        float content_score
        int content_attempts
        json content_output

        boolean published
        int wp_post_id
        boolean human_intervened "Any manual intervention applied"

        string failed_at_stage
        text failure_reason
        datetime awaiting_restart_since
    }

    %% ─── Task queue ─────────────────────────────────────
    pmw_task_queue {
        int id PK
        int run_id FK
        int agent_id FK
        string agent_type
        string status "queued | claimed | done | failed"
        int attempt_number
        json payload "Input passed to agent"
        json result "Output returned by agent"
        string prompt_hash "sha256 of prompt used"
        string model_used
        json tool_calls "Array of tool call records"
        float score
        json score_breakdown "Per-criterion scores"
        boolean passed_threshold
        datetime queued_at
        datetime claimed_at
        datetime completed_at
    }

    %% ─── Human actions ───────────────────────────────────
    pmw_interventions {
        int id PK
        int run_id FK
        int user_id FK
        string action_type "restart | intervene | kill | threshold_override"
        string from_stage "Stage restarted from (if restart)"
        json original_output "Output before correction"
        json corrected_output "Human-supplied correction"
        json override_values "Threshold values overridden"
        datetime actioned_at
    }

    %% ─── Compliance Vault (hash-chained ledger — see 5b) ──
    pmw_vault_genesis {
        int id PK "Always exactly 1 row — the chain anchor"
        string hash "0000...0000 known constant"
        string version "Schema version chain was started under"
        datetime created_at
    }

    pmw_vault_events {
        int id PK "Auto-increment — gaps break the chain"
        int run_id FK
        int topic_id FK
        string event_type "run_created | stage_complete | stage_retry | intervention | restart | kill | run_complete | run_failed"
        int user_id "NULL for system events"
        json payload "Full event snapshot"
        string previous_hash "current_hash of row id-1 — genesis row uses 0000...0000"
        string current_hash "sha256(payload + previous_hash + recorded_at)"
        datetime recorded_at "DB DEFAULT NOW() — never supplied by application"
    }

    pmw_vault_audit_exports {
        int id PK
        int run_id FK
        int exported_by_user_id FK
        string format "json | pdf"
        string export_hash "sha256 of full export content"
        string chain_verified "true | false — chain check run at export time"
        datetime exported_at
    }

    %% ─── Relationships ───────────────────────────────────
    wp_posts            ||--o{ wp_postmeta           : "has meta"
    pmw_affiliates      ||--o{ pmw_topics             : "promoted by"
    pmw_topics          ||--o{ pmw_workflow_runs       : "runs through"
    pmw_workflow_runs   ||--o{ pmw_task_queue          : "generates tasks"
    pmw_agents          ||--o{ pmw_task_queue          : "claims tasks"
    pmw_workflow_runs   ||--o{ pmw_interventions       : "records actions"
    pmw_vault_genesis   ||--o{ pmw_vault_events        : "anchors"
    pmw_workflow_runs   ||--o{ pmw_vault_events        : "audited by"
    pmw_workflow_runs   ||--o{ pmw_vault_audit_exports : "exported as"
```

---

### 5b. Compliance Vault — Hash-Chain Ledger

> The Compliance Vault uses a **private hash-chained ledger** — the same cryptographic principle that underpins blockchain, without distributed consensus overhead. Each event record contains the hash of the previous record. Tampering with any row breaks every subsequent hash in the chain, making alteration detectable by a simple sequential verification scan.
>
> This sits on top of the MySQL trigger and permission controls from the previous design — those still apply. The hash chain adds a cryptographic guarantee that those controls alone cannot provide: even a DBA with SUPER privilege who bypassed triggers and edited a row would leave a detectably broken chain.

---

#### How the chain works

```mermaid
graph LR
    G["🔒 Genesis Recordid: 0hash: 0000...0000written once at DB init"]

    E1["Event id: 1payload: run_createdprevious_hash: 0000...0000current_hash: sha256(payload+prev+ts)= abc1..."]

    E2["Event id: 2payload: stage_completeprevious_hash: abc1...current_hash: sha256(payload+prev+ts)= def2..."]

    E3["Event id: 3payload: stage_retryprevious_hash: def2...current_hash: sha256(payload+prev+ts)= ghi3..."]

    TAMPER["⚠️ Attacker editsEvent id: 2 payload"]

    BROKEN["❌ Event id: 3previous_hash: def2...Recomputed hash of id:2= xyz9... MISMATCHChain broken — detected"]

    G -->|"anchors"| E1
    E1 -->|"chains into"| E2
    E2 -->|"chains into"| E3
    TAMPER -.->|"mutates"| E2
    E2 -.->|"hash now invalid"| BROKEN
```

---

#### Genesis record — written once at DB initialisation

```sql
-- Run exactly once during database setup.
-- The hash value is a known constant committed to your codebase.
-- Never insert into pmw_vault_genesis again.

CREATE TABLE pmw_vault_genesis (
    id          INT PRIMARY KEY DEFAULT 1,
    hash        CHAR(64) NOT NULL,
    version     VARCHAR(20) NOT NULL,
    created_at  DATETIME DEFAULT NOW(),
    CONSTRAINT  only_one_genesis CHECK (id = 1)
);

INSERT INTO pmw_vault_genesis (id, hash, version)
VALUES (1, '0000000000000000000000000000000000000000000000000000000000000000', '1.0.0');
```

---

#### INSERT pattern — application code responsibility

> The application must fetch the `current_hash` of the last row before every INSERT. This serialises vault writes — only one can occur at a time. For your throughput (a handful of events per article run) this is not a bottleneck.

```sql
-- Step 1: Get the hash of the most recent row (or genesis if chain is empty)
SELECT COALESCE(
    (SELECT current_hash FROM pmw_vault_events ORDER BY id DESC LIMIT 1),
    (SELECT hash FROM pmw_vault_genesis)
) AS previous_hash;

-- Step 2: INSERT the new event — recorded_at is set by DB, not application
INSERT INTO pmw_vault_events (
    run_id,
    topic_id,
    event_type,
    user_id,
    payload,
    previous_hash,
    current_hash
    -- recorded_at: NOT supplied — DB DEFAULT NOW() ensures app cannot fake timestamp
)
VALUES (
    :run_id,
    :topic_id,
    :event_type,
    :user_id,
    :payload_json,
    :previous_hash,                          -- from Step 1
    SHA2(
        CONCAT(:payload_json, :previous_hash, NOW()),
        256
    )
);
```

> **Critical:** Steps 1 and 2 must run inside a **serialised transaction** with `SELECT ... FOR UPDATE` on the last vault row, or under an application-level mutex. If two events are inserted concurrently they may read the same `previous_hash` and produce a fork, which breaks the chain.

```sql
-- Production-safe pattern with row lock
START TRANSACTION;

SELECT current_hash INTO @prev_hash
FROM pmw_vault_events
ORDER BY id DESC
LIMIT 1
FOR UPDATE;                                  -- locks the row until commit

-- Fallback to genesis if table is empty
SET @prev_hash = COALESCE(@prev_hash,
    (SELECT hash FROM pmw_vault_genesis));

INSERT INTO pmw_vault_events (
    run_id, topic_id, event_type, user_id,
    payload, previous_hash, current_hash
)
VALUES (
    :run_id, :topic_id, :event_type, :user_id,
    :payload_json,
    @prev_hash,
    SHA2(CONCAT(:payload_json, @prev_hash, NOW()), 256)
);

COMMIT;
```

---

#### Chain verification — the audit integrity check

> Run this on every audit export and on a scheduled basis (e.g. nightly). Any mismatch means a row was tampered with after insertion.

```sql
-- Verification query: walk the chain and flag any broken links
SELECT
    e.id,
    e.run_id,
    e.event_type,
    e.recorded_at,
    e.previous_hash                                         AS stored_previous_hash,
    e.current_hash                                          AS stored_current_hash,
    SHA2(CONCAT(e.payload, e.previous_hash, e.recorded_at), 256)
                                                            AS recomputed_hash,
    CASE
        WHEN e.current_hash =
             SHA2(CONCAT(e.payload, e.previous_hash, e.recorded_at), 256)
        THEN 'OK'
        ELSE '*** TAMPERED ***'
    END                                                     AS integrity_status,
    CASE
        WHEN e.id = 1 THEN
            CASE WHEN e.previous_hash =
                (SELECT hash FROM pmw_vault_genesis)
            THEN 'OK' ELSE '*** GENESIS MISMATCH ***' END
        ELSE
            CASE WHEN e.previous_hash =
                (SELECT current_hash FROM pmw_vault_events
                 WHERE id = e.id - 1)
            THEN 'OK' ELSE '*** CHAIN BROKEN ***' END
    END                                                     AS chain_link_status
FROM pmw_vault_events e
ORDER BY e.id ASC;
```

---

#### Trigger and permission controls (unchanged — still required)

```sql
-- Triggers: block any mutation at DB level
CREATE TRIGGER pmw_vault_events_no_update
BEFORE UPDATE ON pmw_vault_events FOR EACH ROW
SIGNAL SQLSTATE '45000'
SET MESSAGE_TEXT = 'pmw_vault_events is a hash-chained ledger. Updates are not permitted.';

CREATE TRIGGER pmw_vault_events_no_delete
BEFORE DELETE ON pmw_vault_events FOR EACH ROW
SIGNAL SQLSTATE '45000'
SET MESSAGE_TEXT = 'pmw_vault_events is a hash-chained ledger. Deletes are not permitted.';

CREATE TRIGGER pmw_vault_genesis_no_update
BEFORE UPDATE ON pmw_vault_genesis FOR EACH ROW
SIGNAL SQLSTATE '45000'
SET MESSAGE_TEXT = 'Genesis record is immutable.';

CREATE TRIGGER pmw_vault_genesis_no_delete
BEFORE DELETE ON pmw_vault_genesis FOR EACH ROW
SIGNAL SQLSTATE '45000'
SET MESSAGE_TEXT = 'Genesis record is immutable.';

-- App DB user: INSERT + SELECT only on vault tables
CREATE USER 'pmw_app'@'%' IDENTIFIED BY '';
GRANT SELECT, INSERT ON preciousmarket.pmw_vault_events TO 'pmw_app'@'%';
GRANT SELECT          ON preciousmarket.pmw_vault_genesis TO 'pmw_app'@'%';
GRANT SELECT, INSERT ON preciousmarket.pmw_vault_audit_exports TO 'pmw_app'@'%';

-- Full access on mutable engine tables
GRANT SELECT, INSERT, UPDATE, DELETE ON preciousmarket.pmw_workflow_runs TO 'pmw_app'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON preciousmarket.pmw_task_queue TO 'pmw_app'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON preciousmarket.pmw_topics TO 'pmw_app'@'%';
GRANT SELECT, INSERT                 ON preciousmarket.pmw_interventions TO 'pmw_app'@'%';

-- Read-only user for compliance officer / audit export
CREATE USER 'pmw_readonly'@'%' IDENTIFIED BY '';
GRANT SELECT ON preciousmarket.pmw_vault_events TO 'pmw_readonly'@'%';
GRANT SELECT ON preciousmarket.pmw_vault_genesis TO 'pmw_readonly'@'%';
GRANT SELECT ON preciousmarket.pmw_vault_audit_exports TO 'pmw_readonly'@'%';

FLUSH PRIVILEGES;
```

---

#### What this gives you vs the previous checksum approach

| | Simple checksum (previous design) | Hash-chain ledger (current design) |
|---|---|---|
| Detects row edit | ✅ Checksum mismatch | ✅ Current hash mismatch |
| Detects row deletion | ❌ Gap not detectable | ✅ Chain link broken at next row |
| Detects row reordering | ❌ | ✅ previous_hash points to wrong row |
| Detects mass re-hash by attacker | ❌ Each row is independent | ⚠️ Possible if attacker rewrites ALL hashes — genesis anchor makes this detectable externally |
| External verifiability | ❌ Requires DB access to verify | ✅ Exported chain can be verified offline |
| EU AI Act Art. 12 | Partial | Strong — cryptographic proof of sequence integrity |

> **Upgrade path:** When you outgrow MySQL for the vault, the INSERT interface (payload → hash chain) stays identical. You would replace the MySQL tables with Amazon QLDB or a Merkle-tree store without changing a single line of application code — only the database driver changes.

---

### 5c. Compliance Vault — Queue-Backed Write Architecture

> The hash-chain INSERT requires serialisation — each row must know the hash of the previous row before it can be written. In Section 5b this is handled with `SELECT ... FOR UPDATE`. At higher throughput (many parallel workflow runs emitting vault events simultaneously) this database lock becomes a bottleneck. A **single-consumer queue** resolves this: producers fire events onto the queue without waiting; one dedicated `VaultWriter` drains the queue sequentially, maintaining the chain guarantee without any database locking.

---

## 6. Infrastructure Overview

```mermaid
graph TB
    subgraph Internet["🌐 Internet"]
        USER_A["Public User"]
        USER_B["Agent / Internal User"]
    end

    subgraph Edge["Edge / DNS"]
        DNS["DNS"]
        CDN["CDNCloudflare / Fastly"]
    end

    subgraph Host["Hosting"]
        LB["Load Balancernginx / ALB"]
        subgraph App["Application Servers"]
            WP_S["WordPress ServerPHP / Apache"]
            ENG_S["Workflow EngineNode.js / Python"]
        end
        subgraph Data["Data"]
            DB[("SQL DatabaseMySQL / PostgreSQL")]
            CACHE["Object CacheRedis"]
        end
    end

    USER_A -->|"HTTPS"| DNS
    USER_B -->|"HTTPS + WSS"| DNS
    DNS --> CDN
    CDN -->|"Cache miss"| LB
    LB --> WP_S
    LB --> ENG_S
    WP_S --> CACHE
    WP_S --> DB
    ENG_S --> DB
```

---

## 7. Caching Strategy

> Four distinct cache layers sit between the public internet and the database. A request is served by the earliest layer that holds a valid cached copy. Invalidation flows inward — a WordPress publish event clears outward from the DB up to the CDN edge.

```mermaid
graph TB
    REQ["🌐 Incoming Request(GraphQL / REST)"]

    REQ --> L1{"L1 — CDN CacheCloudflare / FastlyTTL: 5–60 min"}

    L1 -->|"HIT"| RES1["✅ Return to clientServed from edge"]

    L1 -->|"MISS"| L2{"L2 — WordPress Page CacheWP Rocket / W3 Total CacheTTL: 10–30 min"}

    L2 -->|"HIT"| RES2["✅ Return to clientRepopulate CDN edge"]

    L2 -->|"MISS"| L3{"L3 — Object CacheRedis via WP Object Cache APITTL: 5–15 min"}

    L3 -->|"HIT"| RES3["✅ Return to clientRepopulate page cache + CDN"]

    L3 -->|"MISS"| L4{"L4 — WP Transient CacheShort-lived DB-backed valuesTTL: per transient"}

    L4 -->|"HIT"| RES4["✅ Return to clientRepopulate object cache + above"]

    L4 -->|"MISS"| DB[("SQL DatabaseSource of truth")]

    DB --> STORE["Build responseStore in transient → Redis→ page cache → CDN"]
    STORE --> RES5["✅ Return to client"]

    subgraph Invalidation["🔄 Cache Invalidation — triggered on WordPress publish / update"]
        INV_WP["WP save_post hook fires"]
        INV_TR["Clear relevant transients"]
        INV_OC["Flush Redis object cache keys"]
        INV_PC["Flush page cache for post URL"]
        INV_CDN["Purge CDN edge cache for post URL"]

        INV_WP --> INV_TR --> INV_OC --> INV_PC --> INV_CDN
    end
```

| Layer | Tool | What it caches | TTL | Invalidated by |
|-------|------|---------------|-----|---------------|
| **L1 — CDN** | Cloudflare / Fastly | Full HTTP responses at the edge | 5–60 min | WP publish hook → CDN purge API |
| **L2 — Page Cache** | WP Rocket / W3 Total Cache | Rendered PHP page output as static HTML | 10–30 min | WP publish hook → plugin flush |
| **L3 — Object Cache** | Redis via WP Object Cache API | WP object cache: posts, terms, user data, query results | 5–15 min | `wp_cache_delete()` on `save_post` |
| **L4 — Transient Cache** | WordPress Transients API (DB-backed, Redis-backed when object cache active) | Expensive computed values: API responses, aggregated data | Per transient (minutes to hours) | `delete_transient()` on relevant hooks |
| **DB Query Cache** | MySQL query cache (if enabled) | Raw query result sets | Session / auto | Query invalidated on table write |

> **Note on L4:** When Redis object cache is active, WordPress automatically stores transients in Redis rather than the database. This means L3 and L4 are served from the same Redis instance but keyed differently — transients use a `_transient_` key prefix. The diagram shows them as separate logical layers because they have separate TTLs and separate invalidation hooks.

---

## 8. Upgrade Path Notes (Post-Prototype)

```mermaid
graph LR
    NOW["PrototypeShared SQL DB"]
    N1["Split DBsWP DB + Engine DB"]
    N2["Add Read Replicasfor WP queries"]
    N3["Message Queuefor async workflows"]
    N4["Separate WebSocketscale-out service"]

    NOW -->|"Phase 2"| N1
    N1 -->|"Phase 2"| N2
    N2 -->|"Phase 3"| N3
    N3 -->|"Phase 3"| N4
```

> **Key decision point:** When the Workflow Engine begins writing at high volume, move it to its own database instance to prevent contention with WordPress reads.



## 🧩 System Components

### 1. Frontend Layer (React)

```text
frontend/
├── src/
│   ├── components/
│   │   ├── MarketDashboard/    # Real-time price displays
│   │   ├── ArticleFeed/        # Content presentation
│   │   ├── PriceCharts/        # Interactive visualizations
│   │   └── Newsletter/         # Subscription management
│   ├── hooks/
│   │   ├── useMarketData/      # Market data fetching
│   │   └── useContent/         # Content management
│   ├── pages/
│   │   ├── Home/              # Landing page
│   │   ├── Blog/              # Article listings
│   │   ├── Analysis/          # Market analysis
│   │   └── Admin/             # Content management
│   └── services/
│       ├── api/               # GraphQL client
│       └── analytics/         # Tracking service
└── public/                    # Static assets
```

**Key Technologies:**

- React 18 with TypeScript

- Apollo Client for GraphQL

- Recharts for data visualization

- Tailwind CSS for styling

- React Router v6 for navigation

### 2. Backend Layer (WordPress Headless CMS)

```text
backend/
├── wp-content/
│   ├── plugins/
│   │   ├── precious-market-api/     # Custom endpoints
│   │   ├── ai-content-importer/     # AI content ingestion
│   │   └── market-data-sync/        # Price synchronization
│   └── themes/                      # Headless theme
├── docker/
│   └── docker-compose.yml           # Local development
└── wp-config.php                    # Custom configuration
```

**Key Technologies:**

- WordPress 6.4+ as headless CMS

- WPGraphQL for GraphQL API

- Custom PHP plugins for extended functionality

- MySQL 8.0 for data persistence

- Redis for object caching

### 3. AI Engine (Python/LangChain/LangGraph)

```text
agents/
├── core/
│   ├── orchestrator.py            # Main workflow controller
│   └── state_manager.py           # Agent state persistence
├── agents/
│   ├── research_agent.py          # Market data research
│   ├── content_agent.py           # Article generation
│   ├── fact_checker.py            # Content verification
│   └── seo_agent.py               # SEO optimization
├── tools/
│   ├── market_data_fetcher.py     # Price data collection
│   ├── news_scraper.py            # News aggregation
│   └── citation_verifier.py       # Source validation
├── workflows/
│   └── content_workflow.py        # LangGraph state machine
└── database/
    └── models.py                  # SQLAlchemy models
```

**Key Technologies:**

- Python 3.11+

- LangChain for LLM orchestration

- LangGraph for workflow management

- SQLAlchemy for database operations

- Celery for task queue (optional)

- PostgreSQL for agent data (or MySQL)

### 4. Data Architecture

```mermaid
erDiagram
    ARTICLES {
        int id PK
        string title
        text content
        string status
        datetime created_at
        datetime published_at
        boolean ai_generated
        json metadata
        int author_id FK
    }
    
    MARKET_DATA {
        int id PK
        string metal_type
        decimal price
        string currency
        datetime timestamp
        string source
        json metadata
    }
    
    AGENT_RUNS {
        int id PK
        string agent_type
        json input_data
        json output_data
        string status
        datetime started_at
        datetime completed_at
        int article_id FK
    }
    
    CONTENT_PLANS {
        int id PK
        string name
        json schedule
        json topics
        string status
        datetime created_at
    }
    
    AFFILIATE_LINKS {
        int id PK
        string product
        string url
        decimal commission
        string status
        int article_id FK
    }
    
    ARTICLES ||--o{ AGENT_RUNS : "generated_by"
    ARTICLES ||--o{ AFFILIATE_LINKS : "contains"
    CONTENT_PLANS ||--o{ ARTICLES : "produces"
```

## 🔄 System Workflows

### Content Generation Workflow

```mermaid
sequenceDiagram
    participant CM as Content Manager
    participant Scheduler
    participant Orchestrator
    participant Research
    participant Generator
    participant Editor
    participant WordPress
    participant Frontend
    
    CM->>Scheduler: Create Content Plan
    Scheduler->>Orchestrator: Daily Trigger
    Orchestrator->>Research: Gather Market Data
    Research-->>Orchestrator: Research Results
    Orchestrator->>Generator: Generate Draft
    Generator-->>Orchestrator: Article Draft
    Orchestrator->>Editor: Human Review Required
    Editor->>Editor: Review & Edit
    Editor->>WordPress: Approve & Publish
    WordPress->>Frontend: Content Available
    Frontend-->>User: Display Content
```

Real-time Data Flow

```mermaid
graph LR
    A[Market Data APIs] --> B[Data Ingestion Service]
    B --> C[Redis Cache]
    C --> D[React Frontend]
    C --> E[AI Research Agents]
    D --> F[User Browser]
    E --> G[Content Generation]
    G --> H[WordPress CMS]
```

## 🚀 Technical Specifications

### API Design

```graphql
# GraphQL Schema Overview
type Query {
  articles(status: ArticleStatus): [Article!]!
  article(id: ID!): Article
  marketData(metal: MetalType!, range: DateRange): [MarketPoint!]!
  contentPlans: [ContentPlan!]!
  agentRuns(status: RunStatus): [AgentRun!]!
}

type Mutation {
  createArticle(input: ArticleInput!): Article!
  updateArticle(id: ID!, input: ArticleInput!): Article!
  scheduleContentPlan(input: ContentPlanInput!): ContentPlan!
  triggerAgentRun(agentType: AgentType!, input: JSON): AgentRun!
}

type Article {
  id: ID!
  title: String!
  content: String!
  excerpt: String
  status: ArticleStatus!
  aiGenerated: Boolean!
  metadata: JSON
  marketData: [MarketPoint!]
  affiliateLinks: [AffiliateLink!]
  createdAt: DateTime!
  publishedAt: DateTime
}
```

## Performance Requirements

Metric	Target	Monitoring
Page Load Time	< 2 seconds	Lighthouse, Web Vitals
API Response Time	< 200ms	New Relic, Datadog
Content Generation	< 5 minutes per article	Custom metrics
Database Query	< 50ms	MySQL slow query log
Cache Hit Rate	> 90%	Redis monitoring

## Scalability Considerations

- Frontend: Static export with incremental regeneration

- API: WordPress with Redis caching and CDN

- AI Agents: Queue-based processing with horizontal scaling

- Database: Read replicas for analytics, connection pooling

- Storage: S3/CDN for media, database for structured data

## 🔒 Security Architecture

### Authentication & Authorization

```yaml
Authentication:
  - WordPress JWT for API access
  - API keys for AI agent communication
  - OAuth for admin dashboard (optional)

Authorization Levels:
  1. Public Readers: Read-only access to published content
  2. Content Editors: Create/edit articles, manage schedules
  3. Administrators: Full system control, agent configuration
  4. AI Agents: Specific API endpoints only

Data Protection:
  - HTTPS everywhere (TLS 1.3)
  - API rate limiting
  - SQL injection prevention (prepared statements)
  - XSS protection (React built-in, WordPress escaping)
  - Regular security audits
```
### Data Privacy

- GDPR compliance for EU visitors

- CCPA compliance for California visitors

- Data minimization (only collect necessary data)

- User data deletion procedures

- Privacy policy integration

# 📊 Monitoring & Observability

## Key Metrics to Track

```yaml
Business Metrics:
  - Articles published per day
  - Organic traffic growth
  - Affiliate revenue
  - User engagement (time on page, bounce rate)

Technical Metrics:
  - System uptime (target: 99.9%)
  - API latency (p95, p99)
  - Error rates (4xx, 5xx)
  - AI agent success/failure rates
  - Database performance (connections, query times)

Content Quality Metrics:
  - Factual accuracy (manual sampling)
  - SEO score (Yoast/equivalent)
  - Readability scores
  - User feedback (comments, shares)
```

### Alerting Strategy
```yaml
Critical (PagerDuty/SMS):
  - System downtime > 5 minutes
  - Database unresponsive
  - Security breach detected

Warning (Email/Slack):
  - API latency > 500ms
  - AI agent failure rate > 10%
  - Cache hit rate < 80%

Informational (Dashboard):
  - Content plan completion
  - Traffic milestones
  - Revenue targets
```

## 🐳 Deployment Architecture

### Development Environment

```docker-compose
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      VITE_API_URL: http://localhost:4000/graphql
    
  wordpress:
    image: wordpress:6.4
    ports: ["8080:80"]
    environment:
      WORDPRESS_DB_HOST: mysql
      WORDPRESS_DB_NAME: preciousmarket
    volumes:
      - ./backend/wp-content:/var/www/html/wp-content
  
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: preciousmarket
  
  ai-agents:
    build: ./agents
    depends_on: [mysql]
    environment:
      DATABASE_URL: mysql://root:rootpass@mysql:3306/preciousmarket
```

### Production Architecture

```mermaid
graph TB
    subgraph "Cloud Provider (AWS/DigitalOcean)"
        subgraph "Frontend"
            A[CDN - CloudFront]
            B[S3 - Static Assets]
        end
        
        subgraph "Backend"
            C[Load Balancer]
            D[EC2/App Runner - WordPress]
            E[RDS - MySQL]
            F[ElastiCache - Redis]
        end
        
        subgraph "AI Processing"
            G[ECS/EKS - AI Agents]
            H[SQS - Task Queue]
            I[CloudWatch - Monitoring]
        end
    end
    
    User --> A
    A --> D
    D --> E
    D --> F
    G --> D
    G --> H
    H --> G
```

## 🛣️ Implementation Roadmap

### Phase 1: Foundation (Months 1-2)

```mermaid
gantt
    title Phase 1: Core Infrastructure
    dateFormat YYYY-MM-DD
    
    section WordPress Setup
    Install & Configure :a1, 2024-01-01, 7d
    Custom Plugins :a2, after a1, 14d
    GraphQL API :a3, after a2, 7d
    
    section Database Design
    Schema Design :b1, 2024-01-08, 7d
    Migrations :b2, after b1, 7d
    Seed Data :b3, after b2, 3d
    
    section Basic Frontend
    React Setup :c1, 2024-01-15, 7d
    Article Display :c2, after c1, 10d
    Basic Styling :c3, after c2, 7d
```

### Phase 2: AI Integration (Months 3-4)
```mermaid
gantt
    title Phase 2: AI Agent Development
    dateFormat YYYY-MM-DD
    
    section Research Agent
    Market Data Integration :d1, 2024-02-15, 10d
    News Aggregation :d2, after d1, 10d
    Fact Gathering :d3, after d2, 7d
    
    section Content Generation
    Article Generation :e1, 2024-03-01, 14d
    Fact Checking :e2, after e1, 10d
    SEO Optimization :e3, after e2, 7d
    
    section Workflow Orchestration
    LangGraph Setup :f1, 2024-03-15, 7d
    State Management :f2, after f1, 7d
    Error Handling :f3, after f2, 7d
```

### Phase 3: Enhancement (Months 5-6)
```mermaid
gantt
    title Phase 3: Advanced Features
    dateFormat YYYY-MM-DD
    
    section User Experience
    Real-time Market Data :g1, 2024-04-15, 14d
    Interactive Charts :g2, after g1, 10d
    Newsletter System :g3, after g2, 7d
    
    section Content Management
    Scheduling System :h1, 2024-05-01, 10d
    Approval Workflow :h2, after h1, 7d
    Multi-platform Publishing :h3, after h2, 10d
    
    section Monetization
    Affiliate Integration :i1, 2024-05-15, 14d
    Analytics Dashboard :i2, after i1, 10d
    A/B Testing :i3, after i2, 7d
```

## 📈 Success Metrics & KPIs

### Technical KPIs
Metric	Target	Measurement Method
System Availability	99.9% uptime	Uptime monitoring
Page Load Time	< 2 seconds	Web Vitals API
API Response Time	< 200ms (p95)	Application monitoring
Content Generation Time	< 5 minutes	Agent run logs
Factual Accuracy	> 95%	Manual sampling

### Business KPIs
Metric	Target	Measurement Period
Articles Published	2-3 per day	Daily
Organic Traffic Growth	+40%	6 months
Affiliate Revenue Growth	+30%	Quarterly
User Engagement	+25% time on page	Monthly
SEO Ranking	Top 10 for target keywords	Quarterly

## 🧪 Testing Strategy
```yaml
Unit Tests (70%):
  - Frontend components
  - AI agent functions
  - WordPress plugin functions
  - Database models

Integration Tests (20%):
  - API endpoints
  - Agent workflows
  - Database migrations
  - Third-party API integrations

E2E Tests (10%):
  - User workflows
  - Content publishing
  - AI content generation
  - Critical user journeys
```

### Quality Gates
```yaml
Pre-commit:
  - ESLint/Prettier
  - TypeScript compilation
  - Unit test execution

Pre-deploy:
  - Integration test suite
  - Performance benchmarks
  - Security scanning

Post-deploy:
  - Smoke tests
  - Canary deployments
  - User acceptance testing
```

## 🚨 Risk Mitigation

### Technical Risks
Risk	Impact	Mitigation Strategy
AI content inaccuracies	High	Human review layer, fact-checking agents
WordPress performance	Medium	Caching strategy, CDN, optimized queries
API rate limiting	Medium	Queue system, retry logic, fallback sources
Data loss	High	Automated backups, point-in-time recovery

### Business Risks
Risk	Impact	Mitigation Strategy
Affiliate program changes	Medium	Multiple affiliate networks, direct partnerships
SEO algorithm changes	High	White-hat SEO, quality content, regular updates
Market volatility	Low	Diversified content topics, evergreen content
Competition	Medium	Unique value proposition, first-mover advantage

## 📚 Documentation Strategy

### Documentation Structure

```text
docs/
├── architecture/           # System design documents
├── api/                   # API references
├── deployment/            # Deployment guides
├── user-guides/          # End-user documentation
├── development/          # Developer onboarding
└── operations/           # Runbooks and procedures
```

### Living Documentation
- Architecture Decision Records (ADRs) for major decisions

- API documentation auto-generated from GraphQL schema

- Deployment runbooks with troubleshooting steps

- Knowledge base for common issues and solutions

## 🎯 Conclusion

This system design provides a scalable, maintainable architecture for Precious Market Watch that addresses the core problem of manual content creation in the precious metals affiliate space. By combining modern web technologies with AI-powered automation, the system enables efficient content generation while maintaining quality and accuracy.

**Key Success Factors:**

1. Robust AI workflow with human oversight

2. Performance-optimized React frontend

3. Scalable WordPress backend

4. Comprehensive monitoring and alerting

5. Iterative development based on metrics

The phased implementation approach allows for incremental delivery of value while managing risk and ensuring quality at each stage.

