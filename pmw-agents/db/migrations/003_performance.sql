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