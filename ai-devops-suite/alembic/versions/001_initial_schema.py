"""Initial schema for AI DevOps Suite.

Revision ID: 001
Create Date: 2026-02-16
"""

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create all tables."""
    from alembic import op
    import sqlalchemy as sa
    from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY

    # Agent events
    op.create_table(
        "agent_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("agent_id", sa.String(256), nullable=False),
        sa.Column("trace_id", sa.String(256), nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("duration_ms", sa.Float, nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("tokens_input", sa.Integer, nullable=True),
        sa.Column("tokens_output", sa.Integer, nullable=True),
        sa.Column("cost_usd", sa.Float, nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("error_type", sa.String(128), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata", JSON, nullable=True),
    )
    op.create_index("ix_agent_events_tenant", "agent_events", ["tenant_id"])
    op.create_index("ix_agent_events_agent", "agent_events", ["agent_id"])
    op.create_index("ix_agent_events_tenant_ts", "agent_events", ["tenant_id", "timestamp"])

    # Metric snapshots
    op.create_table(
        "metric_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", sa.String(256), nullable=False),
        sa.Column("metric_name", sa.String(128), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("window_seconds", sa.Integer, nullable=False),
    )

    # Prompts
    op.create_table(
        "prompts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("latest_version", sa.Integer, nullable=False),
    )

    # Prompt versions
    op.create_table(
        "prompt_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("prompt_id", UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("variables", ARRAY(sa.String), nullable=False),
        sa.Column("model_hint", sa.String(128), nullable=True),
        sa.Column("tags", ARRAY(sa.String), nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("parent_version", sa.Integer, nullable=True),
        sa.Column("changelog", sa.Text, nullable=True),
    )

    # Experiments
    op.create_table(
        "experiments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("prompt_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("metric", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("significance_threshold", sa.Float, nullable=False),
        sa.Column("min_samples", sa.Integer, nullable=False),
        sa.Column("variants", JSON, nullable=False),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # Experiment results
    op.create_table(
        "experiment_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", UUID(as_uuid=True), nullable=False),
        sa.Column("variant_name", sa.String(64), nullable=False),
        sa.Column("metric_value", sa.Float, nullable=False),
        sa.Column("recorded_at", sa.DateTime, nullable=False),
    )

    # Pipeline jobs
    op.create_table(
        "pipeline_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("url_pattern", sa.Text, nullable=False),
        sa.Column("extraction_schema", JSON, nullable=False),
        sa.Column("llm_model", sa.String(128), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # Job runs
    op.create_table(
        "job_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("records_extracted", sa.Integer, nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
    )

    # Extraction results
    op.create_table(
        "extraction_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_run_id", UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", UUID(as_uuid=True), nullable=False),
        sa.Column("data", JSON, nullable=False),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("extracted_at", sa.DateTime, nullable=False),
        sa.Column("quality_score", sa.Integer, nullable=True),
    )

    # Schedules
    op.create_table(
        "schedules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("cron_expression", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("next_run_at", sa.DateTime, nullable=True),
    )

    # Alert rules
    op.create_table(
        "alert_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("metric_name", sa.String(128), nullable=False),
        sa.Column("condition", sa.String(20), nullable=False),
        sa.Column("threshold", sa.Float, nullable=True),
        sa.Column("cooldown_seconds", sa.Integer, nullable=False),
        sa.Column("notification_channels", JSON, nullable=False),
        sa.Column("is_active", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # Alert history
    op.create_table(
        "alert_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("metric_name", sa.String(128), nullable=False),
        sa.Column("metric_value", sa.Float, nullable=False),
        sa.Column("threshold", sa.Float, nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("triggered_at", sa.DateTime, nullable=False),
        sa.Column("acknowledged_at", sa.DateTime, nullable=True),
    )


def downgrade():
    from alembic import op
    for table in [
        "alert_history", "alert_rules", "schedules", "extraction_results",
        "job_runs", "pipeline_jobs", "experiment_results", "experiments",
        "prompt_versions", "prompts", "metric_snapshots", "agent_events",
    ]:
        op.drop_table(table)
