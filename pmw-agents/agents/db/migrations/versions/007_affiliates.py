"""Add wp_dealer_id and sync columns to affiliates for WordPress dealer CPT sync.

Revision ID: 007_affiliates_wp_sync
Revises: 006_error_column
Create Date: 2026-03-20

The affiliate_loader node now fetches dealers from WordPress (dealer CPT)
and syncs them into the Postgres affiliates table — mirroring how
topic_loader syncs pmw_topic posts into the topics table.

wp_dealer_id is the WordPress post ID of the dealer CPT entry.
It serves as the join key for upserts (ON CONFLICT).

Additional columns added to match WordPress meta fields that were
previously only managed in Postgres seed scripts.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007_affiliates_wp_sync"
down_revision: Union[str, Sequence[str], None] = "006_error_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # wp_dealer_id: WordPress post ID of the dealer CPT entry.
    # Used as the upsert key when syncing from WordPress.
    op.add_column(
        "affiliates",
        sa.Column("wp_dealer_id", sa.Integer(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_affiliates_wp_dealer_id",
        "affiliates",
        ["wp_dealer_id"],
    )
    op.create_index(
        "idx_affiliates_wp_dealer_id",
        "affiliates",
        ["wp_dealer_id"],
    )

    # partner_key: URL-safe slug for the affiliate (e.g. "bullionvault").
    # Used for affiliate intelligence page slugs and internal references.
    op.add_column(
        "affiliates",
        sa.Column("partner_key", sa.String(100), nullable=True),
    )

    # Additional fields that were missing from the original schema
    # but are defined in the research README and seed data.
    # These are now managed in WordPress dealer meta and synced here.
    op.add_column(
        "affiliates",
        sa.Column("asset_classes", sa.Text(), nullable=True),
    )  # JSON array: ["gold", "silver", ...]
    op.add_column(
        "affiliates",
        sa.Column("product_types", sa.Text(), nullable=True),
    )  # JSON array: ["bars", "coins", ...]
    op.add_column(
        "affiliates",
        sa.Column("buy_side", sa.Boolean(), server_default=sa.text("true")),
    )
    op.add_column(
        "affiliates",
        sa.Column("sell_side", sa.Boolean(), server_default=sa.text("false")),
    )
    op.add_column(
        "affiliates",
        sa.Column("intent_stages", sa.Text(), nullable=True),
    )  # JSON array: ["awareness", "consideration", "decision"]


def downgrade() -> None:
    op.drop_column("affiliates", "intent_stages")
    op.drop_column("affiliates", "sell_side")
    op.drop_column("affiliates", "buy_side")
    op.drop_column("affiliates", "product_types")
    op.drop_column("affiliates", "asset_classes")
    op.drop_column("affiliates", "partner_key")
    op.drop_index("idx_affiliates_wp_dealer_id", "affiliates")
    op.drop_constraint("uq_affiliates_wp_dealer_id", "affiliates")
    op.drop_column("affiliates", "wp_dealer_id")