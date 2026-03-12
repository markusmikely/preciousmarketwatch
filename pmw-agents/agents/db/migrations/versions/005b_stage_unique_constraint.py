"""005b_stage_unique_constraint

Revision ID: 005b
Revises: 005
"""
from alembic import op

revision = '005b_stage_unique_constraint'
down_revision: Union[str, Sequence[str], None] = "005_observability"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_unique_constraint(
        "uq_workflow_stages_run_stage_attempt",
        "workflow_stages",
        ["run_id", "stage_name", "attempt_number"]
    )

def downgrade() -> None:
    op.drop_constraint("uq_workflow_stages_run_stage_attempt", "workflow_stages")