"""Add churn detection and recovery tables

Revision ID: 2026_02_10_012
Revises: 2026_02_10_011
Create Date: 2026-02-10 17:30:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_02_10_012"
down_revision = "2026_02_10_011"
branch_labels = None
depends_on = None


def upgrade():
    # Create churn_risk_assessments table
    op.create_table(
        "churn_risk_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("risk_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("risk_level", sa.String(length=50), nullable=False),
        sa.Column("signals", postgresql.JSONB(), nullable=False),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=False),
        sa.Column("days_inactive", sa.Integer(), nullable=False),
        sa.Column("recommended_action", sa.String(length=100), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Create indexes for churn_risk_assessments
    op.create_index("idx_churn_assessments_contact", "churn_risk_assessments", ["contact_id"])
    op.create_index("idx_churn_assessments_risk", "churn_risk_assessments", ["risk_level"])
    op.create_index("idx_churn_assessments_date", "churn_risk_assessments", [sa.text("assessed_at DESC")])

    # Create recovery_actions table
    op.create_table(
        "recovery_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("churn_risk_assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("strategy", sa.String(length=100), nullable=False),
        sa.Column("message_template", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("ghl_message_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Create indexes for recovery_actions
    op.create_index("idx_recovery_actions_contact", "recovery_actions", ["contact_id"])
    op.create_index("idx_recovery_actions_status", "recovery_actions", ["status"])
    op.create_index("idx_recovery_actions_scheduled", "recovery_actions", ["scheduled_at"])

    # Create recovery_outcomes table
    op.create_table(
        "recovery_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "recovery_action_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recovery_actions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("response_time_hours", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("next_action", sa.String(length=100), nullable=True),
        sa.Column("outcome_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Create indexes for recovery_outcomes
    op.create_index("idx_recovery_outcomes_action", "recovery_outcomes", ["recovery_action_id"])
    op.create_index("idx_recovery_outcomes_contact", "recovery_outcomes", ["contact_id"])
    op.create_index("idx_recovery_outcomes_outcome", "recovery_outcomes", ["outcome"])


def downgrade():
    # Drop indexes for recovery_outcomes
    op.drop_index("idx_recovery_outcomes_outcome", table_name="recovery_outcomes")
    op.drop_index("idx_recovery_outcomes_contact", table_name="recovery_outcomes")
    op.drop_index("idx_recovery_outcomes_action", table_name="recovery_outcomes")

    # Drop recovery_outcomes table
    op.drop_table("recovery_outcomes")

    # Drop indexes for recovery_actions
    op.drop_index("idx_recovery_actions_scheduled", table_name="recovery_actions")
    op.drop_index("idx_recovery_actions_status", table_name="recovery_actions")
    op.drop_index("idx_recovery_actions_contact", table_name="recovery_actions")

    # Drop recovery_actions table
    op.drop_table("recovery_actions")

    # Drop indexes for churn_risk_assessments
    op.drop_index("idx_churn_assessments_date", table_name="churn_risk_assessments")
    op.drop_index("idx_churn_assessments_risk", table_name="churn_risk_assessments")
    op.drop_index("idx_churn_assessments_contact", table_name="churn_risk_assessments")

    # Drop churn_risk_assessments table
    op.drop_table("churn_risk_assessments")
