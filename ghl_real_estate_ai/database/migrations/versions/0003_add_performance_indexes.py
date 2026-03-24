"""Add performance indexes for high-frequency query columns.

These indexes target the query patterns in transaction_service.py
(milestone timeline view, celebration checks) and llm_cost_log
(cost analytics by bot_type, model).

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-24
"""

from alembic import op

# revision identifiers
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Transaction milestone queries (transaction_service.py:445-507)
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_real_estate_transactions_transaction_id
        ON real_estate_transactions (transaction_id);
    """)

    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_transaction_celebrations_tx_type
        ON transaction_celebrations (transaction_id, milestone_type);
    """)

    # Note: milestone_timeline_view is a VIEW, not a table — cannot index a view.
    # Index the underlying milestone_timeline table instead.
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_milestone_timeline_tx_order
        ON milestone_timeline (transaction_id, order_sequence);
    """)

    # Note: idx_llm_cost_log_bot_type removed — already covered by
    # migration 0002's composite index on (created_at, bot_type).

    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_llm_cost_log_model_created
        ON llm_cost_log (model, created_at);
    """)

    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_llm_cost_log_conversation
        ON llm_cost_log (conversation_id);
    """)

    # Lead engagement queries (frequently filtered by contact + timestamp)
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_communication_logs_contact_created
        ON communication_logs (contact_id, created_at DESC);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_real_estate_transactions_transaction_id;")
    op.execute("DROP INDEX IF EXISTS idx_transaction_celebrations_tx_type;")
    op.execute("DROP INDEX IF EXISTS idx_milestone_timeline_tx_order;")
    op.execute("DROP INDEX IF EXISTS idx_llm_cost_log_model_created;")
    op.execute("DROP INDEX IF EXISTS idx_llm_cost_log_conversation;")
    op.execute("DROP INDEX IF EXISTS idx_communication_logs_contact_created;")
