"""Initial schema — affiliates, topics (WP-aligned), workflow, intelligence, etc.

Revision ID: 001_initial
Revises:
Create Date: 2025-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # ---- affiliates ----
    op.create_table(
        "affiliates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("value_prop", sa.Text(), nullable=False),
        sa.Column("commission_type", sa.String(50)),
        sa.Column("commission_rate", sa.Numeric(8, 2)),
        sa.Column("cookie_days", sa.Integer()),
        sa.Column("geo_focus", sa.String(50)),
        sa.Column("min_transaction", sa.Numeric(10, 2)),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # ---- topics (fully aligned with WordPress pmw_topic meta) ----
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("topic_name", sa.String(255), nullable=False),
        sa.Column("target_keyword", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("include_keywords", sa.Text()),
        sa.Column("exclude_keywords", sa.Text()),
        sa.Column("asset_class", sa.String(50)),
        sa.Column("product_type", sa.String(50)),
        sa.Column("geography", sa.String(50)),
        sa.Column("is_buy_side", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("intent_stage", sa.String(50)),
        sa.Column("priority", sa.Integer(), server_default=sa.text("5")),
        sa.Column("schedule_cron", sa.String(50)),
        sa.Column("agent_status", sa.String(50), server_default=sa.text("'idle'")),
        sa.Column("last_run_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("run_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("last_run_id", sa.Integer()),
        sa.Column("last_wp_post_id", sa.Integer()),
        sa.Column("wp_category_id", sa.Integer()),
        sa.Column("affiliate_page_id", sa.Integer()),
        sa.Column("affiliate_id", sa.Integer(), sa.ForeignKey("affiliates.id")),
        sa.Column("status", sa.String(50), server_default=sa.text("'active'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_topics_asset_class", "topics", ["asset_class"])
    op.create_index("idx_topics_priority", "topics", ["priority"])

    # ---- workflow_runs ----
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("topic_id", sa.Integer(), sa.ForeignKey("topics.id")),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("current_stage", sa.String(50)),
        sa.Column("final_score", sa.Numeric(4, 3)),
        sa.Column("wp_post_id", sa.Integer()),
        sa.Column("wp_post_url", sa.Text()),
        sa.Column("human_intervened", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("threshold_overrides", postgresql.JSONB()),
        sa.Column("reader_intent", sa.String(50)),
        sa.Column("total_cost_usd", sa.Numeric(8, 6)),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("failed_at", sa.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_workflow_runs_status", "workflow_runs", ["status"])
    op.create_index("idx_workflow_runs_topic", "workflow_runs", ["topic_id"])
    op.create_index("idx_workflow_runs_started", "workflow_runs", ["started_at"], postgresql_ops={"started_at": "DESC"})

    # ---- workflow_stages ----
    op.create_table(
        "workflow_stages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE")),
        sa.Column("stage_name", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("attempt_number", sa.Integer(), server_default=sa.text("1")),
        sa.Column("score", sa.Numeric(4, 3)),
        sa.Column("passed_threshold", sa.Boolean()),
        sa.Column("output_json", postgresql.JSONB()),
        sa.Column("judge_feedback", postgresql.JSONB()),
        sa.Column("prompt_hash", sa.String(64)),
        sa.Column("model_used", sa.String(100)),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("cost_usd", sa.Numeric(8, 6)),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_workflow_stages_run", "workflow_stages", ["run_id"])
    op.create_index("idx_workflow_stages_stage", "workflow_stages", ["stage_name"])

    # ---- affiliate_intelligence_runs (topic_id = WP post ID, no FK) ----
    op.create_table(
        "affiliate_intelligence_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("affiliate_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("asset_class", sa.Text(), nullable=False),
        sa.Column("geography", sa.Text(), nullable=False),
        sa.Column("ran_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("spot_price_gbp", sa.Numeric(12, 4)),
        sa.Column("price_trend_pct_30d", sa.Numeric(6, 2)),
        sa.Column("price_trend_pct_90d", sa.Numeric(6, 2)),
        sa.Column("market_stance", sa.Text()),
        sa.Column("emotional_trigger", sa.Text()),
        sa.Column("top_factors_json", postgresql.JSONB()),
        sa.Column("objections_json", postgresql.JSONB()),
        sa.Column("motivations_json", postgresql.JSONB()),
        sa.Column("verbatim_phrases", postgresql.JSONB()),
        sa.Column("paa_questions", postgresql.JSONB()),
        sa.Column("source_quality", sa.Text()),
        sa.Column("compliance_review_required", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("compliance_reviewed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("compliance_reviewed_by", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["affiliate_id"], ["affiliates.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"]),
        sa.UniqueConstraint("run_id", "affiliate_id", name="uq_affiliate_intelligence_runs_run_affiliate"),
    )
    op.create_index("idx_affiliate_runs_affiliate", "affiliate_intelligence_runs", ["affiliate_id"])
    op.create_index("idx_affiliate_runs_topic", "affiliate_intelligence_runs", ["topic_id"])

    # ---- affiliate_intelligence_summary ----
    op.create_table(
        "affiliate_intelligence_summary",
        sa.Column("affiliate_id", sa.Integer(), nullable=False),
        sa.Column("partner_key", sa.Text(), nullable=False),
        sa.Column("total_runs", sa.Integer(), server_default=sa.text("0")),
        sa.Column("first_run_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("last_run_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("latest_spot_price_gbp", sa.Numeric(12, 4)),
        sa.Column("latest_price_trend_30d", sa.Numeric(6, 2)),
        sa.Column("latest_market_stance", sa.Text()),
        sa.Column("latest_ran_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("top_objections_json", postgresql.JSONB()),
        sa.Column("top_motivations_json", postgresql.JSONB()),
        sa.Column("verbatim_pool_json", postgresql.JSONB()),
        sa.Column("paa_pool_json", postgresql.JSONB()),
        sa.Column("latest_factors_json", postgresql.JSONB()),
        sa.Column("has_pending_review", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("affiliate_id"),
        sa.ForeignKeyConstraint(["affiliate_id"], ["affiliates.id"]),
    )

    # ---- agent_configs ----
    op.create_table(
        "agent_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("threshold", sa.Numeric(4, 3)),
        sa.Column("max_retries", sa.Integer(), server_default=sa.text("3")),
        sa.Column("temperature", sa.Numeric(3, 2), server_default=sa.text("0.7")),
        sa.Column("criteria_weights", postgresql.JSONB()),
        sa.Column("prompt_template", postgresql.JSONB()),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_name", name="uq_agent_configs_agent_name"),
    )

    # ---- interventions ----
    op.create_table(
        "interventions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id")),
        sa.Column("stage_name", sa.String(50)),
        sa.Column("intervened_by", sa.Integer()),
        sa.Column("original_output", postgresql.JSONB()),
        sa.Column("corrected_output", postgresql.JSONB()),
        sa.Column("reason", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # ---- vault_events ----
    op.create_table(
        "vault_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("idempotency_key", postgresql.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("run_id", sa.Integer()),
        sa.Column("topic_id", sa.Integer()),
        sa.Column("stage_name", sa.String(50)),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("previous_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_vault_events_idempotency_key"),
    )
    op.create_index("idx_vault_events_run", "vault_events", ["run_id"])
    op.create_index("idx_vault_events_type", "vault_events", ["event_type"])

    # ---- users ----
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default=sa.text("'operator'")),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # ---- generated_media ----
    op.create_table(
        "generated_media",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id")),
        sa.Column("media_type", sa.String(50), nullable=False),
        sa.Column("prompt_used", sa.Text()),
        sa.Column("wp_media_id", sa.Integer()),
        sa.Column("wp_media_url", sa.Text()),
        sa.Column("file_format", sa.String(20)),
        sa.Column("generator", sa.String(50)),
        sa.Column("cost_usd", sa.Numeric(8, 6)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_generated_media_run", "generated_media", ["run_id"])

    # ---- social_posts ----
    op.create_table(
        "social_posts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id")),
        sa.Column("wp_post_id", sa.Integer()),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("hashtags", postgresql.ARRAY(sa.Text())),
        sa.Column("hook_type", sa.String(50)),
        sa.Column("score", sa.Numeric(4, 3)),
        sa.Column("status", sa.String(50), server_default=sa.text("'draft'")),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_social_posts_run", "social_posts", ["run_id"])

    # ---- performance_reports ----
    op.create_table(
        "performance_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("report_type", sa.String(50)),
        sa.Column("ga4_data", postgresql.JSONB()),
        sa.Column("clarity_data", postgresql.JSONB()),
        sa.Column("search_console_data", postgresql.JSONB()),
        sa.Column("agent_analysis", sa.Text()),
        sa.Column("recommendations", postgresql.JSONB()),
        sa.Column("scoring_correlation", postgresql.JSONB()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # ---- article_performance ----
    op.create_table(
        "article_performance",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("wp_post_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id")),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("sessions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("bounce_rate", sa.Numeric(5, 2)),
        sa.Column("avg_session_sec", sa.Integer()),
        sa.Column("affiliate_clicks", sa.Integer(), server_default=sa.text("0")),
        sa.Column("conversions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("impressions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("clicks", sa.Integer(), server_default=sa.text("0")),
        sa.Column("avg_position", sa.Numeric(5, 2)),
        sa.Column("scroll_depth_p75", sa.Integer()),
        sa.Column("rage_clicks", sa.Integer(), server_default=sa.text("0")),
        sa.Column("content_score", sa.Numeric(4, 3)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("wp_post_id", "date", name="uq_article_performance_wp_post_date"),
    )
    op.create_index("idx_article_performance_run", "article_performance", ["run_id"])


def downgrade() -> None:
    op.drop_index("idx_article_performance_run", "article_performance")
    op.drop_table("article_performance")
    op.drop_table("performance_reports")
    op.drop_index("idx_social_posts_run", "social_posts")
    op.drop_table("social_posts")
    op.drop_index("idx_generated_media_run", "generated_media")
    op.drop_table("generated_media")
    op.drop_table("users")
    op.drop_index("idx_vault_events_type", "vault_events")
    op.drop_index("idx_vault_events_run", "vault_events")
    op.drop_table("vault_events")
    op.drop_table("interventions")
    op.drop_table("agent_configs")
    op.drop_table("affiliate_intelligence_summary")
    op.drop_index("idx_affiliate_runs_topic", "affiliate_intelligence_runs")
    op.drop_index("idx_affiliate_runs_affiliate", "affiliate_intelligence_runs")
    op.drop_table("affiliate_intelligence_runs")
    op.drop_index("idx_workflow_stages_stage", "workflow_stages")
    op.drop_index("idx_workflow_stages_run", "workflow_stages")
    op.drop_table("workflow_stages")
    op.drop_index("idx_workflow_runs_started", "workflow_runs")
    op.drop_index("idx_workflow_runs_topic", "workflow_runs")
    op.drop_index("idx_workflow_runs_status", "workflow_runs")
    op.drop_table("workflow_runs")
    op.drop_index("idx_topics_priority", "topics")
    op.drop_index("idx_topics_asset_class", "topics")
    op.drop_table("topics")
    op.drop_table("affiliates")
