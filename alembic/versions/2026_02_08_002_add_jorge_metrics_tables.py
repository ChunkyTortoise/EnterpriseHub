"""Add Jorge metrics tables

Revision ID: 002
Revises: 001
Create Date: 2026-02-08 10:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create jorge_bot_interactions table
    op.create_table(
        "jorge_bot_interactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("bot_type", sa.String(50), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_jorge_interactions_timestamp",
        "jorge_bot_interactions",
        ["timestamp"],
    )
    op.create_index(
        "idx_jorge_interactions_bot_type",
        "jorge_bot_interactions",
        ["bot_type"],
    )

    # Create jorge_handoff_events table
    op.create_table(
        "jorge_handoff_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_bot", sa.String(50), nullable=False),
        sa.Column("target_bot", sa.String(50), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_jorge_handoffs_timestamp",
        "jorge_handoff_events",
        ["timestamp"],
    )

    # Create jorge_performance_operations table
    op.create_table(
        "jorge_performance_operations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("bot_name", sa.String(50), nullable=False),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_jorge_perf_ops_timestamp",
        "jorge_performance_operations",
        ["timestamp"],
    )
    op.create_index(
        "idx_jorge_perf_ops_bot_name",
        "jorge_performance_operations",
        ["bot_name"],
    )

    # Create jorge_alert_rules table
    op.create_table(
        "jorge_alert_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("condition_config", postgresql.JSONB(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warning"),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("channels", postgresql.JSONB(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_jorge_alert_rules_name",
        "jorge_alert_rules",
        ["name"],
        unique=True,
    )

    # Create jorge_alerts table
    op.create_table(
        "jorge_alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rule_name", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("triggered_at", sa.Float(), nullable=False),
        sa.Column("performance_stats", postgresql.JSONB(), nullable=True),
        sa.Column("channels_sent", postgresql.JSONB(), nullable=True),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("acknowledged_at", sa.Float(), nullable=True),
        sa.Column("acknowledged_by", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_jorge_alerts_triggered_at",
        "jorge_alerts",
        ["triggered_at"],
    )
    op.create_index(
        "idx_jorge_alerts_rule_name",
        "jorge_alerts",
        ["rule_name"],
    )


def downgrade() -> None:
    # Drop tables and indexes in reverse order
    op.drop_index("idx_jorge_alerts_rule_name", "jorge_alerts")
    op.drop_index("idx_jorge_alerts_triggered_at", "jorge_alerts")
    op.drop_table("jorge_alerts")

    op.drop_index("idx_jorge_alert_rules_name", "jorge_alert_rules")
    op.drop_table("jorge_alert_rules")

    op.drop_index("idx_jorge_perf_ops_bot_name", "jorge_performance_operations")
    op.drop_index("idx_jorge_perf_ops_timestamp", "jorge_performance_operations")
    op.drop_table("jorge_performance_operations")

    op.drop_index("idx_jorge_handoffs_timestamp", "jorge_handoff_events")
    op.drop_table("jorge_handoff_events")

    op.drop_index("idx_jorge_interactions_bot_type", "jorge_bot_interactions")
    op.drop_index("idx_jorge_interactions_timestamp", "jorge_bot_interactions")
    op.drop_table("jorge_bot_interactions")
