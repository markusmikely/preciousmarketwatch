"""Add lock_expires_at to workflow_runs for crash recovery.

Revision ID: 002_lock_expires
Revises: 001_initial
Create Date: 2025-02-24

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_lock_expires"
down_revision: Union[str, Sequence[str], None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE workflow_runs ADD COLUMN IF NOT EXISTS
        lock_expires_at TIMESTAMPTZ;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE workflow_runs DROP COLUMN IF EXISTS lock_expires_at;
        """
    )
