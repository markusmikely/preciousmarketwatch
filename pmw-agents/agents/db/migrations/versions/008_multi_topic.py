"""008 — Multi-topic support + fix llm_call_logs column.

Revision ID: 008_multi_topic
Revises: 007_affiliates_wp_sync
Create Date: 2026-03-20
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
    # 1. Fix llm_call_logs: column is "attempt" but code writes "attempt_number"
    op.alter_column("llm_call_logs", "attempt", new_column_name="attempt_number")

    # 2. topic_briefs — per-topic outcome tracking + HITL review queue
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
        sa.Column("review_reason", sa.Text()),
        sa.Column("brief_json", postgresql.JSONB()),
        sa.Column("score_breakdown_json", postgresql.JSONB()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("reviewed_by", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_topic_briefs_run", "topic_briefs", ["run_id"])
    op.create_index("idx_topic_briefs_status", "topic_briefs", ["status"],
                    postgresql_where=sa.text("status = 'needs_review'"))

    # 3. Per-topic tracking in workflow_stages
    op.add_column("workflow_stages", sa.Column("topic_wp_id", sa.Integer(), nullable=True))
    op.create_index("idx_workflow_stages_topic", "workflow_stages", ["run_id", "topic_wp_id"])


def downgrade() -> None:
    op.drop_index("idx_workflow_stages_topic", "workflow_stages")
    op.drop_column("workflow_stages", "topic_wp_id")
    op.drop_index("idx_topic_briefs_status", "topic_briefs")
    op.drop_index("idx_topic_briefs_run", "topic_briefs")
    op.drop_table("topic_briefs")
    op.alter_column("llm_call_logs", "attempt_number", new_column_name="attempt")