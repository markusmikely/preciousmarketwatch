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

