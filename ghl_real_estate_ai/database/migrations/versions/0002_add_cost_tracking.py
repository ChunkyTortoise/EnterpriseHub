"""Add llm_cost_log table for API cost tracking.

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-20
"""

from alembic import op

# revision identifiers
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS llm_cost_log (
        id BIGSERIAL PRIMARY KEY,
        conversation_id VARCHAR(255) NOT NULL,
        contact_id VARCHAR(255),
        bot_type VARCHAR(50),
        model VARCHAR(100),
        input_tokens INTEGER DEFAULT 0,
        output_tokens INTEGER DEFAULT 0,
        cache_creation_tokens INTEGER DEFAULT 0,
        cache_read_tokens INTEGER DEFAULT 0,
        estimated_cost_usd NUMERIC(10,6),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_cost_log_created_bot
        ON llm_cost_log (created_at, bot_type);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS llm_cost_log CASCADE")
