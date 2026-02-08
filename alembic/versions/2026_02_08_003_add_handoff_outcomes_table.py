"""Add handoff outcomes table

Revision ID: 003
Revises: 002
Create Date: 2026-02-08 14:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jorge_handoff_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("contact_id", sa.String(100), nullable=False),
        sa.Column("source_bot", sa.String(50), nullable=False),
        sa.Column("target_bot", sa.String(50), nullable=False),
        sa.Column(
            "outcome",
            sa.String(20),
            nullable=False,
        ),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_jorge_handoff_outcomes_bots",
        "jorge_handoff_outcomes",
        ["source_bot", "target_bot"],
    )
    op.create_index(
        "idx_jorge_handoff_outcomes_timestamp",
        "jorge_handoff_outcomes",
        ["timestamp"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_jorge_handoff_outcomes_timestamp",
        "jorge_handoff_outcomes",
    )
    op.drop_index(
        "idx_jorge_handoff_outcomes_bots",
        "jorge_handoff_outcomes",
    )
    op.drop_table("jorge_handoff_outcomes")
