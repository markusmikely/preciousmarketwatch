"""005_observability

Revision ID: 005
Revises: 004
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ── workflow_logs ─────────────────────────────────────────────────────────
    # Operational log — human-readable, queryable.
    # Separate from vault_events (compliance/immutable chain).
    op.create_table(
        "workflow_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("level", sa.String(10), nullable=False),         # INFO | WARNING | ERROR | DEBUG
        sa.Column("source", sa.String(20), nullable=False),        # workflow | agent | llm | system
        sa.Column("agent_name", sa.String(100)),
        sa.Column("stage_name", sa.String(100)),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_workflow_logs_run", "workflow_logs", ["run_id", "created_at"])
    op.create_index("idx_workflow_logs_level", "workflow_logs", ["level"],
                    postgresql_where=sa.text("level IN ('ERROR', 'WARNING')"))

    # ── llm_call_logs ─────────────────────────────────────────────────────────
    # Granular per-call record. workflow_stages.cost_usd is the agent-level summary.
    op.create_table(
        "llm_call_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id"), nullable=True),
        sa.Column("agent_name", sa.String(100)),
        sa.Column("stage_name", sa.String(100)),
        sa.Column("attempt", sa.Integer(), server_default=sa.text("1")),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 8), nullable=False),
        sa.Column("price_snapshot", postgresql.JSONB(), nullable=False),  # rates used at time
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("success", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("error", sa.Text()),
        sa.Column("called_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_llm_calls_run", "llm_call_logs", ["run_id"])
    op.create_index("idx_llm_calls_model_date", "llm_call_logs", ["model", "called_at"])

    # ── workflow_schemas ──────────────────────────────────────────────────────
    # Declares the static topology of each workflow type.
    op.create_table(
        "workflow_schemas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("version", sa.String(20), server_default=sa.text("'1.0'")),
        sa.Column("wp_persona_post_id", sa.Integer()),   # WP CPT 'agents' post ID — NO FK (cross-DB)
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_workflow_schemas_slug"),
    )

    # ── workflow_schema_nodes ─────────────────────────────────────────────────
    op.create_table(
        "workflow_schema_nodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("schema_id", sa.Integer(), sa.ForeignKey("workflow_schemas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_key", sa.String(100), nullable=False),         # e.g. "stage1.brief_locker"
        sa.Column("display_name", sa.String(200)),
        sa.Column("description", sa.Text()),
        sa.Column("node_type", sa.String(50), server_default=sa.text("'agent'")),
        # node_type values: agent | conditional_router | barrier | terminal | hitl_gate
        sa.Column("agent_config_name", sa.String(100)),  # FK to agent_configs.agent_name (soft)
        sa.Column("wp_agent_post_id", sa.Integer()),     # WP CPT 'agents' post ID for this node
        sa.Column("position_x", sa.Integer()),           # optional visual layout hint
        sa.Column("position_y", sa.Integer()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schema_id", "node_key", name="uq_schema_node_key"),
    )

    # ── workflow_schema_edges ─────────────────────────────────────────────────
    op.create_table(
        "workflow_schema_edges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("schema_id", sa.Integer(), sa.ForeignKey("workflow_schemas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_node_key", sa.String(100), nullable=False),
        sa.Column("to_node_key", sa.String(100), nullable=False),
        sa.Column("condition", sa.String(100)),    # NULL = unconditional. "pass"/"retry"/"max_retries"
        sa.Column("label", sa.String(200)),        # human-readable: "Score ≥ threshold"
        sa.Column("is_happy_path", sa.Boolean(), server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_schema_edges_schema", "workflow_schema_edges", ["schema_id"])

    # ── agent_task_queue ──────────────────────────────────────────────────────
    # Durable queue mirror. Redis Streams = fast path; this table = recovery.
    op.create_table(
        "agent_task_queue",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id"), nullable=True),
        sa.Column("workflow_slug", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(50), server_default=sa.text("'queued'")),
        # status: queued | processing | complete | failed | dead_letter
        sa.Column("redis_stream_id", sa.String(100)),  # XADD message ID for deduplication
        sa.Column("worker_id", sa.String(100)),         # which worker claimed it
        sa.Column("enqueued_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("claimed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0")),
        sa.Column("last_error", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_task_queue_status", "agent_task_queue", ["status", "enqueued_at"])
    op.create_index("idx_task_queue_run", "agent_task_queue", ["run_id"])

    # ── model_prices ──────────────────────────────────────────────────────────
    # Historical price records. App falls back to config/pricing.py if no DB row found.
    op.create_table(
        "model_prices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("input_rate_per_1k", sa.Numeric(10, 8), nullable=False),
        sa.Column("output_rate_per_1k", sa.Numeric(10, 8), nullable=False),
        sa.Column("effective_from", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("effective_to", sa.TIMESTAMP(timezone=True)),    # NULL = current
        sa.Column("source_url", sa.Text()),                         # link to provider pricing page
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_model_prices_lookup", "model_prices", ["provider", "model", "effective_from"])

    # ── Alter agent_configs — add visibility + WP persona link ───────────────
    op.add_column("agent_configs", sa.Column("display_title", sa.String(200)))
    op.add_column("agent_configs", sa.Column("description", sa.Text()))
    op.add_column("agent_configs", sa.Column("wp_agent_post_id", sa.Integer()))
    # wp_agent_post_id: WP CPT 'agents' post ID — NO FK constraint (cross-DB)
    op.add_column("agent_configs", sa.Column("is_public", sa.Boolean(), server_default=sa.text("false")))
    op.add_column("agent_configs", sa.Column("specialisms", postgresql.ARRAY(sa.Text())))
    op.add_column("agent_configs", sa.Column("tier", sa.String(50)))
    # tier: intelligence | editorial | distribution | analysis


def downgrade() -> None:
    op.drop_column("agent_configs", "tier")
    op.drop_column("agent_configs", "specialisms")
    op.drop_column("agent_configs", "is_public")
    op.drop_column("agent_configs", "wp_agent_post_id")
    op.drop_column("agent_configs", "description")
    op.drop_column("agent_configs", "display_title")

    op.drop_index("idx_model_prices_lookup", "model_prices")
    op.drop_table("model_prices")
    op.drop_index("idx_task_queue_run", "agent_task_queue")
    op.drop_index("idx_task_queue_status", "agent_task_queue")
    op.drop_table("agent_task_queue")
    op.drop_index("idx_schema_edges_schema", "workflow_schema_edges")
    op.drop_table("workflow_schema_edges")
    op.drop_table("workflow_schema_nodes")
    op.drop_table("workflow_schemas")
    op.drop_index("idx_llm_calls_model_date", "llm_call_logs")
    op.drop_index("idx_llm_calls_run", "llm_call_logs")
    op.drop_table("llm_call_logs")
    op.drop_index("idx_workflow_logs_level", "workflow_logs")
    op.drop_index("idx_workflow_logs_run", "workflow_logs")
    op.drop_table("workflow_logs")