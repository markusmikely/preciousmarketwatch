"""008 — Fix llm_call_logs column name + add topic_briefs review table.

Revision ID: 008_multi_topic
Revises: 007_affiliates_wp_sync
Create Date: 2026-03-20

Changes:
  1. Rename llm_call_logs.attempt → attempt_number (matches service code)
  2. Create topic_briefs table for HITL review queue
  3. Add topic_id column to workflow_stages for per-topic tracking
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008_multi_topic"
down_revision: Union[str, Sequence[str], None] = "007_affiliates_wp_sync"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Fix llm_call_logs column name ──────────────────────────────
    # The service code writes to "attempt_number" but migration 005
    # created the column as "attempt". Rename to match.
    op.alter_column(
        "llm_call_logs",
        "attempt",
        new_column_name="attempt_number",
    )

    # ── 2. topic_briefs — HITL review queue + successful briefs ───────
    # Every topic processed in a pipeline run gets a row here.
    # status: 'passed' | 'needs_review' | 'failed'
    # Passed briefs proceed to planning. Needs_review briefs are shown
    # in the dashboard for human intervention.
    op.create_table(
        "topic_briefs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_wp_id", sa.Integer(), nullable=False),
        sa.Column("topic_title", sa.Text(), nullable=False),
        sa.Column("affiliate_id", sa.Integer(), sa.ForeignKey("affiliates.id"), nullable=True),
        sa.Column("affiliate_name", sa.Text()),
        sa.Column("secondary_affiliate_id", sa.Integer(), sa.ForeignKey("affiliates.id"), nullable=True),
        sa.Column("fit_score", sa.Numeric(4, 3)),
        sa.Column("coherence_score", sa.Numeric(4, 3)),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        # status values:
        #   'passed'       — brief locked, proceeding to planning
        #   'needs_review' — no affiliate above threshold, or coherence failed
        #   'failed'       — unrecoverable error during brief assembly
        #   'pending'      — not yet processed
        sa.Column("review_reason", sa.Text()),
        # Why this topic needs review (e.g. "No affiliate scored above 0.40",
        # "Coherence score 0.52 below 0.60 threshold")
        sa.Column("brief_json", postgresql.JSONB()),
        # Full brief object for passed briefs; partial data for review items
        sa.Column("score_breakdown_json", postgresql.JSONB()),
        # Affiliate scoring breakdown for dashboard display
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("reviewed_by", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_topic_briefs_run", "topic_briefs", ["run_id"])
    op.create_index("idx_topic_briefs_status", "topic_briefs", ["status"])
    op.create_index(
        "idx_topic_briefs_review",
        "topic_briefs",
        ["status"],
        postgresql_where=sa.text("status = 'needs_review'"),
    )

    # ── 3. Add topic_wp_id to workflow_stages ─────────────────────────
    # When processing multiple topics per run, we need to know which
    # topic a stage record belongs to.
    op.add_column(
        "workflow_stages",
        sa.Column("topic_wp_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "idx_workflow_stages_topic",
        "workflow_stages",
        ["run_id", "topic_wp_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_workflow_stages_topic", "workflow_stages")
    op.drop_column("workflow_stages", "topic_wp_id")
    op.drop_index("idx_topic_briefs_review", "topic_briefs")
    op.drop_index("idx_topic_briefs_status", "topic_briefs")
    op.drop_index("idx_topic_briefs_run", "topic_briefs")
    op.drop_table("topic_briefs")
    op.alter_column("llm_call_logs", "attempt_number", new_column_name="attempt")