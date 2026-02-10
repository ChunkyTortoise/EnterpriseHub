"""Add abandonment_events table for lead recovery tracking

Revision ID: 004
Revises: 003
Create Date: 2026-02-10 10:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create abandonment_events table for tracking silent leads."""
    op.create_table(
        "abandonment_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("contact_id", sa.String(100), nullable=False, unique=True),
        sa.Column("location_id", sa.String(100), nullable=False),
        sa.Column("bot_type", sa.String(50), nullable=False),
        sa.Column(
            "last_contact_timestamp",
            sa.Float(),
            nullable=False,
            comment="Unix timestamp of last inbound message from contact",
        ),
        sa.Column(
            "current_stage",
            sa.String(10),
            nullable=False,
            server_default="24h",
            comment="Current abandonment stage: 24h, 3d, 7d, 14d, 30d",
        ),
        sa.Column(
            "recovery_attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Number of recovery messages sent",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=True,
            comment="Contact preferences, interests, budget for personalization",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("NOW()"),
        ),
    )

    # Index on contact_id for fast lookups
    op.create_index(
        "idx_abandonment_contact_id",
        "abandonment_events",
        ["contact_id"],
        unique=True,
    )

    # Index on location_id + last_contact_timestamp for batch detection queries
    op.create_index(
        "idx_abandonment_location_timestamp",
        "abandonment_events",
        ["location_id", "last_contact_timestamp"],
    )

    # Index on current_stage for filtering by recovery stage
    op.create_index(
        "idx_abandonment_stage",
        "abandonment_events",
        ["current_stage"],
    )


def downgrade() -> None:
    """Drop abandonment_events table and related indexes."""
    op.drop_index("idx_abandonment_stage", table_name="abandonment_events")
    op.drop_index("idx_abandonment_location_timestamp", table_name="abandonment_events")
    op.drop_index("idx_abandonment_contact_id", table_name="abandonment_events")
    op.drop_table("abandonment_events")
