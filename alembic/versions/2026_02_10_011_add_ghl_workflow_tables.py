"""Add GHL workflow tables

Revision ID: 2026_02_10_011
Revises: 2026_02_10_010
Create Date: 2026-02-10 17:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_02_10_011"
down_revision = "2026_02_10_010"
branch_labels = None
depends_on = None


def upgrade():
    # Create ghl_workflow_operations table
    op.create_table(
        "ghl_workflow_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("operation_type", sa.String(length=50), nullable=False),
        sa.Column("operation_data", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("ghl_operation_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for ghl_workflow_operations
    op.create_index("idx_ghl_operations_contact", "ghl_workflow_operations", ["contact_id"])
    op.create_index("idx_ghl_operations_type", "ghl_workflow_operations", ["operation_type"])
    op.create_index("idx_ghl_operations_status", "ghl_workflow_operations", ["status"])

    # Create pipeline_stage_history table
    op.create_table(
        "pipeline_stage_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_stage", sa.String(length=50), nullable=True),
        sa.Column("to_stage", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("score_at_transition", sa.String(length=50), nullable=True),
        sa.Column("transitioned_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Create indexes for pipeline_stage_history
    op.create_index("idx_pipeline_history_contact", "pipeline_stage_history", ["contact_id"])
    op.create_index("idx_pipeline_history_stage", "pipeline_stage_history", ["to_stage"])
    op.create_index("idx_pipeline_history_date", "pipeline_stage_history", ["transitioned_at"])

    # Create bot_appointments table
    op.create_table(
        "bot_appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ghl_appointment_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("calendar_id", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="scheduled", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Create indexes for bot_appointments
    op.create_index("idx_bot_appointments_contact", "bot_appointments", ["contact_id"])
    op.create_index("idx_bot_appointments_status", "bot_appointments", ["status"])
    op.create_index("idx_bot_appointments_time", "bot_appointments", ["start_time"])


def downgrade():
    # Drop indexes for bot_appointments
    op.drop_index("idx_bot_appointments_time", table_name="bot_appointments")
    op.drop_index("idx_bot_appointments_status", table_name="bot_appointments")
    op.drop_index("idx_bot_appointments_contact", table_name="bot_appointments")

    # Drop bot_appointments table
    op.drop_table("bot_appointments")

    # Drop indexes for pipeline_stage_history
    op.drop_index("idx_pipeline_history_date", table_name="pipeline_stage_history")
    op.drop_index("idx_pipeline_history_stage", table_name="pipeline_stage_history")
    op.drop_index("idx_pipeline_history_contact", table_name="pipeline_stage_history")

    # Drop pipeline_stage_history table
    op.drop_table("pipeline_stage_history")

    # Drop indexes for ghl_workflow_operations
    op.drop_index("idx_ghl_operations_status", table_name="ghl_workflow_operations")
    op.drop_index("idx_ghl_operations_type", table_name="ghl_workflow_operations")
    op.drop_index("idx_ghl_operations_contact", table_name="ghl_workflow_operations")

    # Drop ghl_workflow_operations table
    op.drop_table("ghl_workflow_operations")
