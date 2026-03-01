"""Stage 6 Affiliate Sources — add faq_url and indexes.

Revision ID: 003_stage6_affiliate_sources
Revises: 002_lock_expires
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_stage6_affiliate_sources"
down_revision: Union[str, Sequence[str], None] = "002_lock_expires"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("affiliates", sa.Column("faq_url", sa.Text(), nullable=True))
    op.create_index("idx_affiliates_faq_url", "affiliates", ["faq_url"])
    op.create_index(
        "idx_affiliate_intelligence_runs_affiliate_run",
        "affiliate_intelligence_runs",
        ["affiliate_id", "run_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_affiliate_intelligence_runs_affiliate_run",
        "affiliate_intelligence_runs",
    )
    op.drop_index("idx_affiliates_faq_url", "affiliates")
    op.drop_column("affiliates", "faq_url")
