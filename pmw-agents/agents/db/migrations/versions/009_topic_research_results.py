"""009 — Per-topic research results storage.

Revision ID: 009_topic_research_results
Revises: 008_multi_topic
Create Date: 2026-03-21
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "009_topic_research_results"
down_revision: Union[str, Sequence[str], None] = "008_multi_topic"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "topic_research_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_wp_id", sa.Integer(), nullable=False),
        sa.Column("topic_title", sa.Text(), nullable=False),
        sa.Column("stage_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("attempt_number", sa.Integer(), server_default=sa.text("1")),
        sa.Column("output_json", postgresql.JSONB()),
        sa.Column("error", sa.Text()),
        sa.Column("model_used", sa.String(100)),
        sa.Column("input_tokens", sa.Integer(), server_default=sa.text("0")),
        sa.Column("output_tokens", sa.Integer(), server_default=sa.text("0")),
        sa.Column("cost_usd", sa.Numeric(10, 8), server_default=sa.text("0")),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_trr_run_topic", "topic_research_results", ["run_id", "topic_wp_id"])
    op.create_index("idx_trr_stage", "topic_research_results", ["stage_name", "status"])
    op.create_unique_constraint("uq_trr_run_topic_stage_attempt", "topic_research_results",
                                ["run_id", "topic_wp_id", "stage_name", "attempt_number"])
    op.create_index("idx_trr_failed", "topic_research_results", ["status", "completed_at"],
                    postgresql_where=sa.text("status = 'failed'"))


def downgrade() -> None:
    op.drop_index("idx_trr_failed", "topic_research_results")
    op.drop_constraint("uq_trr_run_topic_stage_attempt", "topic_research_results")
    op.drop_index("idx_trr_stage", "topic_research_results")
    op.drop_index("idx_trr_run_topic", "topic_research_results")
    op.drop_table("topic_research_results")