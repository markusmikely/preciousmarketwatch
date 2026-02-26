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