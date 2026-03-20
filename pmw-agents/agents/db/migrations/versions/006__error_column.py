"""005b_stage_unique_constraint

Revision ID: 006
Revises: 005b
"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

revision = '006_error_column'
down_revision: Union[str, Sequence[str], None] = "005b_stage_unique_constraint"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
        # Add the error column (nullable text — only populated on failures)
    op.add_column(
        "workflow_stages",
        sa.Column("error", sa.Text(), nullable=True),
    )
 
    # The INSERT … ON CONFLICT (run_id, stage_name, attempt_number) in
    # BaseAgent._write_stage_record requires a unique constraint on these
    # three columns.  The initial schema only had individual indexes.
    op.create_unique_constraint(
        "uq_workflow_stages_run_stage_attempt",
        "workflow_stages",
        ["run_id", "stage_name", "attempt_number"],
    )

def downgrade() -> None:
    op.drop_constraint(
        "uq_workflow_stages_run_stage_attempt",
        "workflow_stages",
        type_="unique",
    )
    op.drop_column("workflow_stages", "error") 