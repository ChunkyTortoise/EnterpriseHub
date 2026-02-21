"""Add sentiment analysis tables

Revision ID: 2026_02_10_009
Revises: 2026_02_10_008
Create Date: 2026-02-10 16:40:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_02_10_009"
down_revision = "2026_02_10_008"
branch_labels = None
depends_on = None


def upgrade():
    # Create conversation_sentiments table
    op.create_table(
        "conversation_sentiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message_index", sa.Integer(), nullable=False),
        sa.Column("sentiment", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("intensity", sa.Numeric(precision=3, scale=2), server_default="0.5"),
        sa.Column("key_phrases", postgresql.JSONB(), server_default="[]"),
        sa.Column("escalation_level", sa.String(length=50), server_default="none"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Create indexes for conversation_sentiments
    op.create_index("idx_conversation_sentiments_conversation", "conversation_sentiments", ["conversation_id"])
    op.create_index("idx_conversation_sentiments_sentiment", "conversation_sentiments", ["sentiment"])
    op.create_index("idx_conversation_sentiments_escalation", "conversation_sentiments", ["escalation_level"])

    # Create sentiment_escalations table
    op.create_table(
        "sentiment_escalations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("escalation_level", sa.String(length=50), nullable=False),
        sa.Column("sentiment", sa.String(length=50), nullable=False),
        sa.Column("intensity", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Create indexes for sentiment_escalations
    op.create_index("idx_sentiment_escalations_contact", "sentiment_escalations", ["contact_id"])
    op.create_index("idx_sentiment_escalations_level", "sentiment_escalations", ["escalation_level"])


def downgrade():
    # Drop indexes first
    op.drop_index("idx_sentiment_escalations_level", table_name="sentiment_escalations")
    op.drop_index("idx_sentiment_escalations_contact", table_name="sentiment_escalations")
    op.drop_index("idx_conversation_sentiments_escalation", table_name="conversation_sentiments")
    op.drop_index("idx_conversation_sentiments_sentiment", table_name="conversation_sentiments")
    op.drop_index("idx_conversation_sentiments_conversation", table_name="conversation_sentiments")

    # Drop tables
    op.drop_table("sentiment_escalations")
    op.drop_table("conversation_sentiments")
