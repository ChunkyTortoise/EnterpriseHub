"""Add billing tables: subscriptions, stripe_customers, usage_records, billing_events.

Revision ID: 2026_03_20_015
Revises: 2026_03_04_014
Create Date: 2026-03-20 01:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_03_20_015"
down_revision = "2026_03_04_014"
branch_labels = None
depends_on = None


def upgrade():
    # -- subscriptions --
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id SERIAL PRIMARY KEY,
            location_id VARCHAR(128) NOT NULL,
            stripe_subscription_id VARCHAR(128),
            stripe_customer_id VARCHAR(128),
            tier VARCHAR(64) NOT NULL DEFAULT 'starter',
            status VARCHAR(64) NOT NULL DEFAULT 'trialing',
            usage_allowance INTEGER NOT NULL DEFAULT 500,
            usage_current INTEGER NOT NULL DEFAULT 0,
            overage_rate NUMERIC(10, 4) NOT NULL DEFAULT 0.50,
            base_price NUMERIC(10, 2) NOT NULL DEFAULT 297.00,
            trial_end TIMESTAMPTZ,
            cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
            current_period_start TIMESTAMPTZ,
            current_period_end TIMESTAMPTZ,
            currency VARCHAR(8) NOT NULL DEFAULT 'usd',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            CONSTRAINT uq_subscriptions_location_id UNIQUE (location_id),
            CONSTRAINT uq_subscriptions_stripe_subscription_id UNIQUE (stripe_subscription_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_location_id ON subscriptions (location_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions (status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_sub_id ON subscriptions (stripe_subscription_id)"
    )

    # -- stripe_customers --
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS stripe_customers (
            id SERIAL PRIMARY KEY,
            location_id VARCHAR(128) NOT NULL,
            stripe_customer_id VARCHAR(128) NOT NULL,
            email VARCHAR(256),
            name VARCHAR(256),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            CONSTRAINT uq_stripe_customers_location_id UNIQUE (location_id),
            CONSTRAINT uq_stripe_customers_stripe_customer_id UNIQUE (stripe_customer_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_stripe_customers_location_id ON stripe_customers (location_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_stripe_customers_stripe_customer_id ON stripe_customers (stripe_customer_id)"
    )

    # -- usage_records --
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_records (
            id SERIAL PRIMARY KEY,
            subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
            stripe_usage_record_id VARCHAR(128),
            lead_id VARCHAR(128),
            contact_id VARCHAR(128),
            quantity INTEGER NOT NULL DEFAULT 1,
            amount NUMERIC(10, 4),
            tier VARCHAR(64),
            billing_period_start TIMESTAMPTZ,
            billing_period_end TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_usage_records_subscription_id ON usage_records (subscription_id)"
    )

    # -- billing_events --
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS billing_events (
            id SERIAL PRIMARY KEY,
            event_id VARCHAR(128) NOT NULL,
            event_type VARCHAR(128) NOT NULL,
            event_data JSONB,
            processing_result JSONB,
            processed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_billing_events_event_id UNIQUE (event_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_billing_events_event_id ON billing_events (event_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_billing_events_event_type ON billing_events (event_type)"
    )

    # Tier rename: 'professional' → 'growth' for any existing rows
    op.execute("UPDATE subscriptions SET tier = 'growth' WHERE tier = 'professional'")


def downgrade():
    op.execute("DROP TABLE IF EXISTS billing_events")
    op.execute("DROP TABLE IF EXISTS usage_records")
    op.execute("DROP TABLE IF EXISTS stripe_customers")
    op.execute("DROP TABLE IF EXISTS subscriptions")
