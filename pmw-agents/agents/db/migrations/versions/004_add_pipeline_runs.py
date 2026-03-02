"""add pipeline_runs table and update workflow_runs

Revision ID: 004_pipeline_runs
Revises: 003_stage6_affiliate_sources
Create Date: 2026-03-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP

# revision identifiers, used by Alembic.
revision: str = "004_pipeline_runs"
down_revision: Union[str, Sequence[str], None] = "003_stage6_affiliate_sources"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create pipeline_runs table
    op.create_table('pipeline_runs',
        sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('pipeline_run_id', UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('triggered_by', sa.Text(), nullable=False),
        sa.Column('topic_wp_id', sa.Integer(), nullable=True),
        sa.Column('topic_title', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='running'),
        sa.Column('phase_statuses', JSONB(), nullable=True),
        sa.Column('total_cost_usd', sa.Numeric(10, 6), nullable=False, server_default='0'),
        sa.Column('wp_post_id', sa.Integer(), nullable=True),
        sa.Column('started_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('failed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('error_summary', JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_pipeline_runs'))
    )
    
    # Add pipeline_run_id column to workflow_runs
    op.add_column('workflow_runs', 
        sa.Column('pipeline_run_id', sa.Integer(), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_workflow_runs_pipeline_run_id_pipeline_runs',
        'workflow_runs', 'pipeline_runs',
        ['pipeline_run_id'], ['id']
    )
    
    # Add phase column to workflow_runs
    op.add_column('workflow_runs',
        sa.Column('phase', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    # Remove phase column from workflow_runs
    op.drop_column('workflow_runs', 'phase')
    
    # Remove foreign key constraint and pipeline_run_id column
    op.drop_constraint('fk_workflow_runs_pipeline_run_id_pipeline_runs', 'workflow_runs', type_='foreignkey')
    op.drop_column('workflow_runs', 'pipeline_run_id')
    
    # Drop pipeline_runs table
    op.drop_table('pipeline_runs')