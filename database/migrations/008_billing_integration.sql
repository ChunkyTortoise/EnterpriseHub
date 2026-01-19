-- ===================================================================
-- Billing Integration Migration
-- Creates comprehensive subscription management and usage tracking
-- Supports Stripe integration with usage-based pricing
-- ===================================================================

-- Stripe customers table (maps location_id to Stripe customer_id)
CREATE TABLE stripe_customers (
    id BIGSERIAL PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL UNIQUE,
    stripe_customer_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    name VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_location FOREIGN KEY (location_id)
        REFERENCES tenants(location_id) ON DELETE CASCADE
);

-- Subscriptions table (core billing entity)
CREATE TABLE subscriptions (
    id BIGSERIAL PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL,
    stripe_subscription_id VARCHAR(255) NOT NULL UNIQUE,
    stripe_customer_id VARCHAR(255) NOT NULL,
    tier VARCHAR(50) NOT NULL CHECK (tier IN ('starter', 'professional', 'enterprise')),
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    usage_allowance INTEGER NOT NULL,
    usage_current INTEGER DEFAULT 0,
    overage_rate DECIMAL(10, 2) NOT NULL,
    base_price DECIMAL(10, 2) NOT NULL,
    trial_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_customer FOREIGN KEY (stripe_customer_id)
        REFERENCES stripe_customers(stripe_customer_id) ON DELETE CASCADE
);

-- Usage tracking table (per-lead billing records)
CREATE TABLE usage_records (
    id BIGSERIAL PRIMARY KEY,
    subscription_id BIGINT NOT NULL,
    stripe_usage_record_id VARCHAR(255) UNIQUE,
    lead_id VARCHAR(255) NOT NULL,
    contact_id VARCHAR(255) NOT NULL,
    quantity INTEGER DEFAULT 1,
    amount DECIMAL(10, 2) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    pricing_multiplier DECIMAL(5, 2),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    billing_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    billing_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata JSONB DEFAULT '{}',

    CONSTRAINT fk_subscription FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(id) ON DELETE CASCADE
);

-- Billing events log (webhook processing and audit trail)
CREATE TABLE billing_events (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(255) NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    stripe_customer_id VARCHAR(255),
    subscription_id BIGINT,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Invoices tracking (payment status and history)
CREATE TABLE invoices (
    id BIGSERIAL PRIMARY KEY,
    stripe_invoice_id VARCHAR(255) NOT NULL UNIQUE,
    subscription_id BIGINT NOT NULL,
    stripe_customer_id VARCHAR(255) NOT NULL,
    amount_due DECIMAL(10, 2) NOT NULL,
    amount_paid DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    hosted_invoice_url TEXT,
    invoice_pdf TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_invoice_subscription FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(id) ON DELETE CASCADE
);

-- ===================================================================
-- Performance Indexes
-- ===================================================================

-- Primary lookup indexes
CREATE INDEX idx_subscriptions_location_status ON subscriptions(location_id, status);
CREATE INDEX idx_subscriptions_tier ON subscriptions(tier, status);
CREATE INDEX idx_stripe_customers_location ON stripe_customers(location_id);

-- Usage record performance indexes
CREATE INDEX idx_usage_subscription_period ON usage_records(subscription_id, billing_period_start);
CREATE INDEX idx_usage_contact ON usage_records(contact_id);
CREATE INDEX idx_usage_timestamp ON usage_records(timestamp DESC);
CREATE INDEX idx_usage_records_billing_period ON usage_records(subscription_id, billing_period_start, billing_period_end);

-- Billing events processing indexes
CREATE INDEX idx_billing_events_processed ON billing_events(processed, created_at);
CREATE INDEX idx_billing_events_type ON billing_events(event_type);
CREATE INDEX idx_billing_events_customer ON billing_events(stripe_customer_id);

-- Invoice status and period indexes
CREATE INDEX idx_invoices_subscription ON invoices(subscription_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_period ON invoices(period_start, period_end);

-- ===================================================================
-- Triggers for updated_at timestamps
-- ===================================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_stripe_customers_updated_at
    BEFORE UPDATE ON stripe_customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===================================================================
-- Data Validation Comments
-- ===================================================================

-- Subscription tiers: starter ($99/month, 50 leads), professional ($249/month, 150 leads), enterprise ($499/month, 500 leads)
-- Overage rates: starter $1.00/lead, professional $1.50/lead, enterprise $0.75/lead
-- Usage allowance: Reset to 0 at start of each billing period
-- Status values: active, past_due, canceled, unpaid, trialing
-- All monetary values stored as DECIMAL(10,2) for precision