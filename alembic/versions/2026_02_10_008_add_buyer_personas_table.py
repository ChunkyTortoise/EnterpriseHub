"""Add buyer personas table

Revision ID: 008
Revises: 007
Create Date: 2026-02-10 16:00:00.000000

Tracks buyer persona classifications for personalized communication.
Stores persona type, confidence scores, detected signals, and behavioral analysis.
Enables response tailoring based on buyer motivation and lifecycle stage.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create buyer_personas table."""
    op.create_table(
        "buyer_personas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "lead_id",
            sa.String(255),
            nullable=False,
            comment="Lead/contact ID from GoHighLevel",
        ),
        sa.Column(
            "persona_type",
            sa.String(50),
            nullable=False,
            comment="Buyer persona type (first_time, upsizer, downsizer, investor, relocator, luxury)",
        ),
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False,
            comment="Confidence score 0.0-1.0",
        ),
        sa.Column(
            "detected_signals",
            postgresql.JSONB(),
            nullable=True,
            comment="Detected keyword signals",
        ),
        sa.Column(
            "behavioral_signals",
            postgresql.JSONB(),
            nullable=True,
            comment="Behavioral signal scores",
        ),
        sa.Column(
            "conversation_turns",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Number of conversation turns analyzed",
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

    # Create indexes for efficient queries
    op.create_index(
        "idx_buyer_personas_lead_id",
        "buyer_personas",
        ["lead_id"],
        unique=True,
    )

    op.create_index(
        "idx_buyer_personas_persona_type",
        "buyer_personas",
        ["persona_type"],
    )

    op.create_index(
        "idx_buyer_personas_confidence",
        "buyer_personas",
        ["confidence"],
    )

    op.create_index(
        "idx_buyer_personas_created_at",
        "buyer_personas",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop buyer_personas table and indexes."""
    # Drop indexes in reverse order
    op.drop_index("idx_buyer_personas_created_at", "buyer_personas")
    op.drop_index("idx_buyer_personas_confidence", "buyer_personas")
    op.drop_index("idx_buyer_personas_persona_type", "buyer_personas")
    op.drop_index("idx_buyer_personas_lead_id", "buyer_personas")

    # Drop table
    op.drop_table("buyer_personas")
