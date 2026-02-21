"""Add A/B test promotion events table

Revision ID: 007
Revises: 006
Create Date: 2026-02-10 15:00:00.000000

Tracks automatic promotion of A/B test winners to production config.
Records promotion criteria, metrics snapshot, canary rollout status,
and provides full audit trail for continuous optimization loop.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ab_promotion_events table."""
    op.create_table(
        "ab_promotion_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("experiment_id", sa.String(255), nullable=False, index=True, comment="Experiment name/identifier"),
        sa.Column("promoted_variant", sa.String(255), nullable=False, comment="Winning variant promoted to default"),
        sa.Column("previous_default", sa.String(255), nullable=True, comment="Previous default variant (for rollback)"),
        sa.Column(
            "promotion_type", sa.String(50), nullable=False, server_default="automatic", comment="automatic or manual"
        ),
        sa.Column(
            "promoted_by",
            sa.String(255),
            nullable=False,
            server_default="system",
            comment="User ID or 'system' for auto-promotion",
        ),
        # Metrics snapshot at promotion time
        sa.Column("p_value", sa.Float(), nullable=False, comment="Statistical significance p-value"),
        sa.Column("lift_percent", sa.Float(), nullable=False, comment="Percentage improvement over control"),
        sa.Column("sample_size", sa.Integer(), nullable=False, comment="Total impressions across all variants"),
        sa.Column("runtime_days", sa.Float(), nullable=False, comment="Experiment duration in days"),
        sa.Column("winner_conversion_rate", sa.Float(), nullable=False, comment="Winner's conversion rate"),
        sa.Column("control_conversion_rate", sa.Float(), nullable=False, comment="Control variant conversion rate"),
        sa.Column("confidence_interval_lower", sa.Float(), nullable=True, comment="95% CI lower bound for winner"),
        sa.Column("confidence_interval_upper", sa.Float(), nullable=True, comment="95% CI upper bound for winner"),
        # Canary rollout tracking
        sa.Column(
            "canary_status",
            sa.String(50),
            nullable=False,
            server_default="pending",
            comment="pending, canary, monitoring, completed, rolled_back",
        ),
        sa.Column(
            "canary_start_time",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When canary rollout started (20% traffic)",
        ),
        sa.Column(
            "canary_end_time", sa.DateTime(timezone=True), nullable=True, comment="When canary completed or rolled back"
        ),
        sa.Column(
            "full_rollout_time", sa.DateTime(timezone=True), nullable=True, comment="When promoted to 100% traffic"
        ),
        sa.Column(
            "rollback_time", sa.DateTime(timezone=True), nullable=True, comment="When rolled back (if applicable)"
        ),
        sa.Column("rollback_reason", sa.Text(), nullable=True, comment="Why rollback occurred"),
        # Full metrics snapshot (JSON)
        sa.Column(
            "metrics_snapshot",
            postgresql.JSONB(),
            nullable=True,
            comment="Complete experiment results at promotion time",
        ),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes for common query patterns
    op.create_index(
        "idx_ab_promotion_events_experiment",
        "ab_promotion_events",
        ["experiment_id"],
    )
    op.create_index(
        "idx_ab_promotion_events_status",
        "ab_promotion_events",
        ["canary_status"],
    )
    op.create_index(
        "idx_ab_promotion_events_created_at",
        "ab_promotion_events",
        ["created_at"],
    )
    op.create_index(
        "idx_ab_promotion_events_experiment_status",
        "ab_promotion_events",
        ["experiment_id", "canary_status"],
    )


def downgrade() -> None:
    """Drop ab_promotion_events table."""
    op.drop_index("idx_ab_promotion_events_experiment_status", table_name="ab_promotion_events")
    op.drop_index("idx_ab_promotion_events_created_at", table_name="ab_promotion_events")
    op.drop_index("idx_ab_promotion_events_status", table_name="ab_promotion_events")
    op.drop_index("idx_ab_promotion_events_experiment", table_name="ab_promotion_events")
    op.drop_table("ab_promotion_events")
