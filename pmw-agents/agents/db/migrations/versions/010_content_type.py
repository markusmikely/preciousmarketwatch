"""010 — Add content_type to topics for routing article generation.

Revision ID: 010_content_type
Revises: 008_multi_topic
Create Date: 2026-03-21
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "010_content_type"
down_revision: Union[str, Sequence[str], None] = "009_topic_research_results"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "topics",
        sa.Column("content_type", sa.String(50), server_default="affiliate", nullable=False),
    )
    op.create_index("idx_topics_content_type", "topics", ["content_type"])


def downgrade() -> None:
    op.drop_index("idx_topics_content_type", "topics")
    op.drop_column("topics", "content_type")