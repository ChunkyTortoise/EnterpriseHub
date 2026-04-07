"""Add cost_records table for LLM cost governance tracking.

Revision ID: 2026_04_07_017
Revises: 2026_04_07_016
Create Date: 2026-04-07 11:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_04_07_017"
down_revision = "2026_04_07_016"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cost_records (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            request_id VARCHAR(256) NOT NULL,
            agent_name VARCHAR(128) NOT NULL,
            model VARCHAR(128) NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            cost_usd DOUBLE PRECISION NOT NULL,
            prompt_version VARCHAR(256),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_cost_records_created_at ON cost_records (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cost_records_agent_name ON cost_records (agent_name)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS cost_records")
