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