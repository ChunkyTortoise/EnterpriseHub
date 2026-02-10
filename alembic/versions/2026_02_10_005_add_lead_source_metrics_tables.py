"""Add lead source metrics tables

Revision ID: 005
Revises: 004
Create Date: 2026-02-10 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lead_source_contacts table
    # Tracks all contacts and their source attribution
    op.create_table(
        "lead_source_contacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("contact_id", sa.String(255), nullable=False, unique=True),
        sa.Column("source_name", sa.String(100), nullable=False),
        sa.Column("stage", sa.String(50), nullable=False, server_default="contact"),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("custom_fields", postgresql.JSONB(), nullable=True),
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_lead_source_contacts_contact_id",
        "lead_source_contacts",
        ["contact_id"],
        unique=True,
    )
    op.create_index(
        "idx_lead_source_contacts_source_name",
        "lead_source_contacts",
        ["source_name"],
    )
    op.create_index(
        "idx_lead_source_contacts_stage",
        "lead_source_contacts",
        ["stage"],
    )
    op.create_index(
        "idx_lead_source_contacts_created_at",
        "lead_source_contacts",
        ["created_at"],
    )

    # Create lead_source_conversions table
    # Tracks conversion events through the funnel
    op.create_table(
        "lead_source_conversions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("contact_id", sa.String(255), nullable=False),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("revenue", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_lead_source_conversions_contact_id",
        "lead_source_conversions",
        ["contact_id"],
    )
    op.create_index(
        "idx_lead_source_conversions_stage",
        "lead_source_conversions",
        ["stage"],
    )
    op.create_index(
        "idx_lead_source_conversions_created_at",
        "lead_source_conversions",
        ["created_at"],
    )

    # Create lead_source_metrics table
    # Aggregated metrics for dashboard (updated daily)
    op.create_table(
        "lead_source_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_name", sa.String(100), nullable=False, unique=True),
        sa.Column("total_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("qualified_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("appointments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("showings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("offers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("closed_deals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_deal_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("conversion_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_lead_source_metrics_source_name",
        "lead_source_metrics",
        ["source_name"],
        unique=True,
    )
    op.create_index(
        "idx_lead_source_metrics_conversion_rate",
        "lead_source_metrics",
        ["conversion_rate"],
    )
    op.create_index(
        "idx_lead_source_metrics_total_revenue",
        "lead_source_metrics",
        ["total_revenue"],
    )

    # Create lead_source_costs table (optional)
    # For tracking marketing costs per source
    op.create_table(
        "lead_source_costs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_name", sa.String(100), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_lead_source_costs_source_name",
        "lead_source_costs",
        ["source_name"],
    )
    op.create_index(
        "idx_lead_source_costs_date",
        "lead_source_costs",
        ["date"],
    )
    # Unique constraint to prevent duplicate cost entries for same source/date
    op.create_index(
        "idx_lead_source_costs_unique",
        "lead_source_costs",
        ["source_name", "date"],
        unique=True,
    )


def downgrade() -> None:
    # Drop tables and indexes in reverse order
    op.drop_index("idx_lead_source_costs_unique", "lead_source_costs")
    op.drop_index("idx_lead_source_costs_date", "lead_source_costs")
    op.drop_index("idx_lead_source_costs_source_name", "lead_source_costs")
    op.drop_table("lead_source_costs")

    op.drop_index("idx_lead_source_metrics_total_revenue", "lead_source_metrics")
    op.drop_index("idx_lead_source_metrics_conversion_rate", "lead_source_metrics")
    op.drop_index("idx_lead_source_metrics_source_name", "lead_source_metrics")
    op.drop_table("lead_source_metrics")

    op.drop_index("idx_lead_source_conversions_created_at", "lead_source_conversions")
    op.drop_index("idx_lead_source_conversions_stage", "lead_source_conversions")
    op.drop_index("idx_lead_source_conversions_contact_id", "lead_source_conversions")
    op.drop_table("lead_source_conversions")

    op.drop_index("idx_lead_source_contacts_created_at", "lead_source_contacts")
    op.drop_index("idx_lead_source_contacts_stage", "lead_source_contacts")
    op.drop_index("idx_lead_source_contacts_source_name", "lead_source_contacts")
    op.drop_index("idx_lead_source_contacts_contact_id", "lead_source_contacts")
    op.drop_table("lead_source_contacts")
