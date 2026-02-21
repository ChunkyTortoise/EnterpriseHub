"""Add objection events table

Revision ID: 006
Revises: 005
Create Date: 2026-02-10 14:00:00.000000

Tracks objection handling events for Phase 2.2 objection framework.
Records objection type, category, response used, and outcome for analytics
and A/B testing optimization.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create objection_events table."""
    op.create_table(
        "objection_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("contact_id", sa.String(255), nullable=False, index=True),
        sa.Column(
            "objection_type",
            sa.String(50),
            nullable=False,
            index=True,
            comment="Specific objection type (e.g., pricing_general, timing_not_ready)",
        ),
        sa.Column(
            "objection_category",
            sa.String(50),
            nullable=False,
            index=True,
            comment="High-level category: pricing, timing, competition, trust, authority, value",
        ),
        sa.Column("confidence", sa.Float(), nullable=False, comment="Detection confidence score (0.0-1.0)"),
        sa.Column("matched_text", sa.Text(), nullable=True, comment="Text fragment that triggered objection detection"),
        sa.Column(
            "graduation_level",
            sa.String(50),
            nullable=False,
            comment="Response level: validate, data, social_proof, market_test",
        ),
        sa.Column(
            "response_variant", sa.Integer(), nullable=False, server_default="0", comment="A/B test variant index"
        ),
        sa.Column("response_text", sa.Text(), nullable=True, comment="Actual response text sent to contact"),
        sa.Column(
            "outcome", sa.String(50), nullable=True, comment="resolved, unresolved, escalated, or null if pending"
        ),
        sa.Column(
            "outcome_timestamp", sa.DateTime(timezone=True), nullable=True, comment="When outcome was determined"
        ),
        sa.Column(
            "market_data", postgresql.JSONB(), nullable=True, comment="Market data used to fill response template"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create composite indexes for common query patterns
    op.create_index(
        "idx_objection_events_contact_category",
        "objection_events",
        ["contact_id", "objection_category"],
    )
    op.create_index(
        "idx_objection_events_type_outcome",
        "objection_events",
        ["objection_type", "outcome"],
    )
    op.create_index(
        "idx_objection_events_created_at",
        "objection_events",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop objection_events table."""
    op.drop_index("idx_objection_events_created_at", table_name="objection_events")
    op.drop_index("idx_objection_events_type_outcome", table_name="objection_events")
    op.drop_index("idx_objection_events_contact_category", table_name="objection_events")
    op.drop_table("objection_events")
