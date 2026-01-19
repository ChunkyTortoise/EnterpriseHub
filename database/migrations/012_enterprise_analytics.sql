-- Migration 012: Enterprise Analytics Database Schema
-- Version: 2.0.0
-- Description: Creates comprehensive analytics tables for revenue attribution, CLV analysis, and competitive intelligence
-- Purpose: Support $5M+ ARR scaling with enterprise-grade analytics infrastructure
-- Apply to: PostgreSQL 15+ with existing Service 6 schema

-- Check PostgreSQL version
DO $$
BEGIN
    IF current_setting('server_version_num')::integer < 150000 THEN
        RAISE EXCEPTION 'PostgreSQL version 15.0 or higher required. Current version: %', version();
    END IF;
END $$;

-- Record migration start
INSERT INTO schema_migrations (version, description, applied_at, applied_by)
VALUES ('012', 'Enterprise Analytics - Revenue Attribution, CLV, Competitive Intelligence', NOW(), current_user);

-- Start timing
\timing on

-- ================================================================================================
-- REVENUE ATTRIBUTION TABLES
-- ================================================================================================

-- Customer touchpoints for attribution modeling
CREATE TABLE IF NOT EXISTS customer_touchpoints (
    touchpoint_id VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100),
    touchpoint_type VARCHAR(50) NOT NULL, -- 'organic_search', 'paid_search', 'social_media', etc.
    channel VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    medium VARCHAR(100) NOT NULL,
    campaign_id VARCHAR(100),
    content TEXT,

    -- Engagement metrics
    page_views INTEGER DEFAULT 1,
    session_duration DECIMAL(10,2), -- seconds
    conversion_value DECIMAL(12,2),

    -- Tracking data
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    referrer_url TEXT,
    landing_page_url TEXT,

    -- Custom attributes as JSONB for flexibility
    custom_attributes JSONB DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT fk_touchpoint_customer FOREIGN KEY (customer_id) REFERENCES contacts(id) ON DELETE CASCADE
);

-- Revenue events for attribution analysis
CREATE TABLE IF NOT EXISTS revenue_attribution_events (
    event_id VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'subscription_started', 'subscription_upgraded', 'one_time_purchase', etc.

    -- Revenue details
    revenue_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',

    -- Subscription details (if applicable)
    subscription_id VARCHAR(100),
    plan_type VARCHAR(100),
    billing_cycle VARCHAR(20), -- 'monthly', 'quarterly', 'yearly'
    commission_rate DECIMAL(5,4), -- for commission-based revenue

    -- Attribution settings
    attribution_window_days INTEGER DEFAULT 90,

    -- Tracking
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Custom attributes
    custom_attributes JSONB DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT fk_revenue_event_customer FOREIGN KEY (customer_id) REFERENCES contacts(id) ON DELETE CASCADE,

    -- Check constraints
    CONSTRAINT chk_revenue_positive CHECK (revenue_amount > 0),
    CONSTRAINT chk_attribution_window CHECK (attribution_window_days > 0 AND attribution_window_days <= 365),
    CONSTRAINT chk_commission_rate CHECK (commission_rate IS NULL OR (commission_rate >= 0 AND commission_rate <= 1))
);

-- Attribution results for different models
CREATE TABLE IF NOT EXISTS attribution_results (
    result_id VARCHAR(100) PRIMARY KEY,
    revenue_event_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    attribution_model VARCHAR(50) NOT NULL, -- 'first_touch', 'last_touch', 'linear', 'time_decay', 'position_based'

    -- Attribution details
    total_revenue DECIMAL(15,2) NOT NULL,
    journey_duration_days INTEGER NOT NULL,
    total_touchpoints INTEGER NOT NULL,

    -- Touchpoint attribution breakdown (JSONB array)
    attributed_touchpoints JSONB NOT NULL,

    -- Model confidence and metadata
    model_confidence DECIMAL(3,2) DEFAULT 0.85,
    model_version VARCHAR(20) DEFAULT '1.0',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- for cache invalidation

    -- Foreign key constraints
    CONSTRAINT fk_attribution_revenue_event FOREIGN KEY (revenue_event_id) REFERENCES revenue_attribution_events(event_id) ON DELETE CASCADE,
    CONSTRAINT fk_attribution_customer FOREIGN KEY (customer_id) REFERENCES contacts(id) ON DELETE CASCADE,

    -- Unique constraint to prevent duplicate attribution results
    UNIQUE(revenue_event_id, attribution_model)
);

-- ================================================================================================
-- CUSTOMER LIFETIME VALUE (CLV) TABLES
-- ================================================================================================

-- Customer metrics for CLV calculation
CREATE TABLE IF NOT EXISTS customer_lifetime_metrics (
    customer_id VARCHAR(100) PRIMARY KEY,

    -- Purchase history
    first_purchase_date TIMESTAMP WITH TIME ZONE,
    last_purchase_date TIMESTAMP WITH TIME ZONE,
    total_purchases INTEGER DEFAULT 0,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    avg_order_value DECIMAL(12,2) DEFAULT 0,
    purchase_frequency DECIMAL(8,4) DEFAULT 0, -- purchases per period

    -- Tenure and recency
    tenure_days INTEGER DEFAULT 0,
    recency_days INTEGER DEFAULT 0,

    -- Engagement metrics
    total_sessions INTEGER DEFAULT 0,
    avg_session_duration DECIMAL(10,2) DEFAULT 0,
    total_page_views INTEGER DEFAULT 0,
    email_opens INTEGER DEFAULT 0,
    email_clicks INTEGER DEFAULT 0,
    support_tickets INTEGER DEFAULT 0,

    -- Subscription metrics (if applicable)
    subscription_plan VARCHAR(100),
    monthly_recurring_revenue DECIMAL(12,2),
    subscription_status VARCHAR(50),

    -- Calculated scores
    rfm_score VARCHAR(3), -- e.g., '555' for top quintile in all dimensions
    engagement_score DECIMAL(5,2), -- 0-100 calculated engagement score
    satisfaction_score DECIMAL(3,2), -- 0-5.0 customer satisfaction

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT fk_clv_metrics_customer FOREIGN KEY (customer_id) REFERENCES contacts(id) ON DELETE CASCADE,

    -- Check constraints
    CONSTRAINT chk_purchase_frequency CHECK (purchase_frequency >= 0),
    CONSTRAINT chk_engagement_score CHECK (engagement_score IS NULL OR (engagement_score >= 0 AND engagement_score <= 100)),
    CONSTRAINT chk_satisfaction_score CHECK (satisfaction_score IS NULL OR (satisfaction_score >= 0 AND satisfaction_score <= 5))
);

-- CLV predictions and analysis
CREATE TABLE IF NOT EXISTS clv_predictions (
    prediction_id VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,

    -- Prediction results
    predicted_clv DECIMAL(15,2) NOT NULL,
    confidence_lower_bound DECIMAL(15,2),
    confidence_upper_bound DECIMAL(15,2),
    prediction_horizon_days INTEGER NOT NULL,

    -- Model details
    model_used VARCHAR(50) NOT NULL, -- 'traditional', 'probabilistic', 'machine_learning', 'hybrid'
    model_version VARCHAR(20) DEFAULT '1.0',

    -- Prediction breakdown
    predicted_future_purchases INTEGER,
    predicted_future_revenue DECIMAL(15,2),
    retention_probability DECIMAL(5,4), -- 0-1 probability

    -- Risk assessment
    churn_probability DECIMAL(5,4), -- 0-1 probability
    churn_risk_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'

    -- Segmentation
    customer_segment VARCHAR(50), -- 'champions', 'loyal_customers', 'at_risk', etc.

    -- Recommendations (JSONB array)
    recommendations JSONB DEFAULT '[]',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, -- predictions expire

    -- Foreign key constraints
    CONSTRAINT fk_clv_prediction_customer FOREIGN KEY (customer_id) REFERENCES contacts(id) ON DELETE CASCADE,

    -- Check constraints
    CONSTRAINT chk_predicted_clv_positive CHECK (predicted_clv >= 0),
    CONSTRAINT chk_retention_probability CHECK (retention_probability >= 0 AND retention_probability <= 1),
    CONSTRAINT chk_churn_probability CHECK (churn_probability >= 0 AND churn_probability <= 1)
);

-- Churn predictions and risk assessment
CREATE TABLE IF NOT EXISTS churn_predictions (
    prediction_id VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,

    -- Churn assessment
    churn_probability DECIMAL(5,4) NOT NULL, -- 0-1 probability
    risk_level VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    predicted_churn_date TIMESTAMP WITH TIME ZONE,

    -- Contributing factors (JSONB arrays)
    risk_factors JSONB DEFAULT '[]',
    protective_factors JSONB DEFAULT '[]',

    -- Intervention recommendations
    intervention_strategies JSONB DEFAULT '[]',
    urgency_score INTEGER, -- 1-10 scale

    -- Model details
    model_confidence DECIMAL(3,2),
    feature_importance JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, -- predictions expire

    -- Foreign key constraints
    CONSTRAINT fk_churn_prediction_customer FOREIGN KEY (customer_id) REFERENCES contacts(id) ON DELETE CASCADE,

    -- Check constraints
    CONSTRAINT chk_churn_prob_range CHECK (churn_probability >= 0 AND churn_probability <= 1),
    CONSTRAINT chk_urgency_score CHECK (urgency_score IS NULL OR (urgency_score >= 1 AND urgency_score <= 10))
);

-- Cohort analysis for customer segments
CREATE TABLE IF NOT EXISTS customer_cohorts (
    cohort_id VARCHAR(100) PRIMARY KEY,
    cohort_month DATE NOT NULL, -- first day of the cohort month
    cohort_size INTEGER NOT NULL,

    -- Retention data by period (JSONB object: {period: retention_rate})
    retention_rates JSONB NOT NULL DEFAULT '{}',

    -- Revenue data by period (JSONB object: {period: {total_revenue, cumulative_revenue, avg_clv}})
    revenue_by_period JSONB NOT NULL DEFAULT '{}',

    -- Churn data by period (JSONB object: {period: churn_rate})
    churn_rates JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint on cohort month
    UNIQUE(cohort_month)
);

-- ================================================================================================
-- COMPETITIVE INTELLIGENCE TABLES
-- ================================================================================================

-- Competitor profiles and tracking
CREATE TABLE IF NOT EXISTS competitor_profiles (
    competitor_id VARCHAR(100) PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    website_url VARCHAR(500),

    -- Classification
    tier VARCHAR(50) NOT NULL, -- 'tier_1_direct', 'tier_2_adjacent', 'tier_3_emerging', 'tier_4_niche'
    market_segments JSONB DEFAULT '[]', -- array of market segments

    -- Business metrics
    estimated_revenue DECIMAL(15,2),
    estimated_customers INTEGER,
    employee_count INTEGER,
    funding_total DECIMAL(15,2),
    founded_year INTEGER,

    -- Product information
    primary_features JSONB DEFAULT '[]', -- array of features
    pricing_model VARCHAR(100), -- 'subscription', 'one-time', 'freemium', etc.
    starting_price DECIMAL(12,2),
    enterprise_price DECIMAL(12,2),

    -- Market position
    market_share_percentage DECIMAL(5,2),
    geographic_presence JSONB DEFAULT '[]', -- array of regions
    target_industries JSONB DEFAULT '[]', -- array of industries

    -- Competitive assessment
    threat_level VARCHAR(20) DEFAULT 'medium', -- 'critical', 'high', 'medium', 'low', 'negligible'
    strength_areas JSONB DEFAULT '[]',
    weakness_areas JSONB DEFAULT '[]',

    -- Data tracking
    data_sources JSONB DEFAULT '[]',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Check constraints
    CONSTRAINT chk_market_share CHECK (market_share_percentage IS NULL OR (market_share_percentage >= 0 AND market_share_percentage <= 100)),
    CONSTRAINT chk_pricing CHECK (starting_price IS NULL OR starting_price >= 0),
    CONSTRAINT chk_enterprise_pricing CHECK (enterprise_price IS NULL OR enterprise_price >= 0)
);

-- Pricing intelligence and analysis
CREATE TABLE IF NOT EXISTS competitive_pricing_intelligence (
    pricing_id VARCHAR(100) PRIMARY KEY,
    competitor_id VARCHAR(100) NOT NULL,

    -- Pricing structure
    pricing_model VARCHAR(100) NOT NULL,
    pricing_tiers JSONB NOT NULL, -- detailed pricing structure

    -- Strategy analysis
    price_positioning VARCHAR(50), -- 'premium', 'value', 'budget', 'penetration'
    discount_strategies JSONB DEFAULT '[]',
    contract_terms JSONB DEFAULT '{}',

    -- Comparative analysis
    price_vs_market_avg DECIMAL(5,4), -- percentage difference from market average
    price_change_history JSONB DEFAULT '[]', -- historical price changes

    -- Intelligence insights
    pricing_strengths JSONB DEFAULT '[]',
    pricing_vulnerabilities JSONB DEFAULT '[]',
    recommended_response JSONB DEFAULT '[]',

    -- Data quality
    confidence_score DECIMAL(3,2) DEFAULT 0.5, -- 0-1 indicating data reliability
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT fk_pricing_competitor FOREIGN KEY (competitor_id) REFERENCES competitor_profiles(competitor_id) ON DELETE CASCADE,

    -- Check constraints
    CONSTRAINT chk_confidence_score CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- Feature comparison matrix
CREATE TABLE IF NOT EXISTS feature_comparisons (
    comparison_id VARCHAR(100) PRIMARY KEY,
    feature_category VARCHAR(100) NOT NULL, -- 'core_crm', 'automation', 'analytics', etc.

    -- Our implementation
    our_implementation JSONB NOT NULL,

    -- Competitor implementations (JSONB object: {competitor_id: implementation_details})
    competitor_implementations JSONB NOT NULL DEFAULT '{}',

    -- Analysis results
    our_advantage_score DECIMAL(5,2), -- -1.0 to 1.0, where 1.0 is significant advantage
    key_differentiators JSONB DEFAULT '[]',
    gaps_to_address JSONB DEFAULT '[]',

    -- Market context
    customer_importance_score DECIMAL(3,2), -- 0-1 based on customer feedback
    market_trend_direction VARCHAR(20), -- 'growing', 'stable', 'declining'

    -- Metadata
    last_analyzed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint on feature category
    UNIQUE(feature_category)
);

-- Market sentiment tracking
CREATE TABLE IF NOT EXISTS market_sentiment (
    sentiment_id VARCHAR(100) PRIMARY KEY,
    competitor_id VARCHAR(100) NOT NULL,

    -- Sentiment metrics
    overall_sentiment VARCHAR(20), -- 'very_positive', 'positive', 'neutral', 'negative', 'very_negative'
    review_sentiment_avg DECIMAL(3,2), -- 0-5.0 average rating
    social_sentiment_score DECIMAL(4,3), -- -1.0 to 1.0

    -- Data sources
    review_platforms JSONB DEFAULT '{}', -- platform -> average rating
    social_mentions JSONB DEFAULT '{}', -- platform -> mention count
    news_sentiment DECIMAL(4,3), -- -1.0 to 1.0

    -- Trend analysis
    sentiment_trend_30d DECIMAL(4,3), -- change over 30 days
    review_volume_trend DECIMAL(5,2), -- review volume change percentage

    -- Insights
    positive_themes JSONB DEFAULT '[]',
    negative_themes JSONB DEFAULT '[]',
    sentiment_drivers JSONB DEFAULT '[]',

    -- Data quality
    data_confidence DECIMAL(3,2) DEFAULT 0.5,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT fk_sentiment_competitor FOREIGN KEY (competitor_id) REFERENCES competitor_profiles(competitor_id) ON DELETE CASCADE,

    -- Check constraints
    CONSTRAINT chk_review_sentiment CHECK (review_sentiment_avg IS NULL OR (review_sentiment_avg >= 0 AND review_sentiment_avg <= 5)),
    CONSTRAINT chk_social_sentiment CHECK (social_sentiment_score >= -1 AND social_sentiment_score <= 1),
    CONSTRAINT chk_sentiment_confidence CHECK (data_confidence >= 0 AND data_confidence <= 1)
);

-- Competitive threats and alerts
CREATE TABLE IF NOT EXISTS competitive_threats (
    threat_id VARCHAR(100) PRIMARY KEY,
    competitor_id VARCHAR(100) NOT NULL,
    threat_type VARCHAR(100) NOT NULL, -- 'pricing', 'feature', 'acquisition', 'market_entry', etc.

    -- Threat assessment
    severity VARCHAR(20) NOT NULL, -- 'critical', 'high', 'medium', 'low', 'negligible'
    urgency VARCHAR(20) NOT NULL, -- 'immediate', 'short_term', 'medium_term', 'long_term'

    -- Threat details
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    evidence JSONB DEFAULT '[]', -- supporting evidence
    potential_impact VARCHAR(100), -- 'revenue_loss', 'market_share_loss', 'customer_churn', etc.

    -- Response planning
    recommended_responses JSONB DEFAULT '[]',
    response_timeline VARCHAR(100),
    required_resources JSONB DEFAULT '[]',

    -- Monitoring
    monitoring_indicators JSONB DEFAULT '[]',
    escalation_triggers JSONB DEFAULT '[]',

    -- Status tracking
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'monitoring', 'resolved', 'expired'
    assigned_to VARCHAR(100), -- team or individual responsible

    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT fk_threat_competitor FOREIGN KEY (competitor_id) REFERENCES competitor_profiles(competitor_id) ON DELETE CASCADE
);

-- Market opportunities identification
CREATE TABLE IF NOT EXISTS market_opportunities (
    opportunity_id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    -- Opportunity assessment
    market_size_estimate DECIMAL(15,2), -- TAM/SAM in dollars
    growth_potential VARCHAR(20), -- 'high', 'medium', 'low'
    competitive_intensity VARCHAR(20), -- 'low', 'medium', 'high'

    -- Implementation analysis
    effort_required VARCHAR(20), -- 'low', 'medium', 'high'
    time_to_market_months INTEGER,
    required_capabilities JSONB DEFAULT '[]',

    -- Strategic value
    strategic_importance VARCHAR(20), -- 'critical', 'high', 'medium', 'low'
    revenue_potential_12m DECIMAL(15,2),
    customer_segments JSONB DEFAULT '[]', -- target segments

    -- Risk assessment
    risks JSONB DEFAULT '[]',
    mitigation_strategies JSONB DEFAULT '[]',

    -- Prioritization
    priority_score DECIMAL(5,2) DEFAULT 0, -- 0-100 calculated priority

    -- Status tracking
    status VARCHAR(50) DEFAULT 'identified', -- 'identified', 'evaluating', 'approved', 'in_progress', 'completed', 'rejected'
    assigned_to VARCHAR(100),

    -- Timestamps
    identified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Check constraints
    CONSTRAINT chk_priority_score CHECK (priority_score >= 0 AND priority_score <= 100),
    CONSTRAINT chk_time_to_market CHECK (time_to_market_months IS NULL OR time_to_market_months > 0)
);

-- ================================================================================================
-- PERFORMANCE OPTIMIZATION INDEXES
-- ================================================================================================

-- Customer touchpoints indexes
CREATE INDEX IF NOT EXISTS idx_touchpoints_customer_timestamp ON customer_touchpoints(customer_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_touchpoints_channel_timestamp ON customer_touchpoints(channel, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_touchpoints_type_timestamp ON customer_touchpoints(touchpoint_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_touchpoints_session ON customer_touchpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_touchpoints_campaign ON customer_touchpoints(campaign_id) WHERE campaign_id IS NOT NULL;

-- Revenue attribution events indexes
CREATE INDEX IF NOT EXISTS idx_revenue_events_customer_timestamp ON revenue_attribution_events(customer_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_revenue_events_type_timestamp ON revenue_attribution_events(event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_revenue_events_amount ON revenue_attribution_events(revenue_amount DESC);
CREATE INDEX IF NOT EXISTS idx_revenue_events_subscription ON revenue_attribution_events(subscription_id) WHERE subscription_id IS NOT NULL;

-- Attribution results indexes
CREATE INDEX IF NOT EXISTS idx_attribution_results_customer ON attribution_results(customer_id);
CREATE INDEX IF NOT EXISTS idx_attribution_results_model ON attribution_results(attribution_model);
CREATE INDEX IF NOT EXISTS idx_attribution_results_revenue ON attribution_results(total_revenue DESC);

-- CLV metrics indexes
CREATE INDEX IF NOT EXISTS idx_clv_metrics_segment ON customer_lifetime_metrics(subscription_status) WHERE subscription_status IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_clv_metrics_rfm ON customer_lifetime_metrics(rfm_score) WHERE rfm_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_clv_metrics_revenue ON customer_lifetime_metrics(total_revenue DESC);
CREATE INDEX IF NOT EXISTS idx_clv_metrics_recency ON customer_lifetime_metrics(recency_days);

-- CLV predictions indexes
CREATE INDEX IF NOT EXISTS idx_clv_predictions_customer ON clv_predictions(customer_id);
CREATE INDEX IF NOT EXISTS idx_clv_predictions_segment ON clv_predictions(customer_segment);
CREATE INDEX IF NOT EXISTS idx_clv_predictions_risk ON clv_predictions(churn_risk_level);
CREATE INDEX IF NOT EXISTS idx_clv_predictions_value ON clv_predictions(predicted_clv DESC);
CREATE INDEX IF NOT EXISTS idx_clv_predictions_expires ON clv_predictions(expires_at);

-- Churn predictions indexes
CREATE INDEX IF NOT EXISTS idx_churn_predictions_customer ON churn_predictions(customer_id);
CREATE INDEX IF NOT EXISTS idx_churn_predictions_risk ON churn_predictions(risk_level, churn_probability DESC);
CREATE INDEX IF NOT EXISTS idx_churn_predictions_urgency ON churn_predictions(urgency_score DESC) WHERE urgency_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_churn_predictions_expires ON churn_predictions(expires_at);

-- Competitor profiles indexes
CREATE INDEX IF NOT EXISTS idx_competitors_tier ON competitor_profiles(tier);
CREATE INDEX IF NOT EXISTS idx_competitors_threat_level ON competitor_profiles(threat_level);
CREATE INDEX IF NOT EXISTS idx_competitors_market_share ON competitor_profiles(market_share_percentage DESC) WHERE market_share_percentage IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_competitors_updated ON competitor_profiles(last_updated DESC);

-- Competitive threats indexes
CREATE INDEX IF NOT EXISTS idx_threats_competitor ON competitive_threats(competitor_id);
CREATE INDEX IF NOT EXISTS idx_threats_severity_urgency ON competitive_threats(severity, urgency, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_threats_status ON competitive_threats(status, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_threats_type ON competitive_threats(threat_type, detected_at DESC);

-- Market opportunities indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_priority ON market_opportunities(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_status ON market_opportunities(status, identified_at DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_strategic ON market_opportunities(strategic_importance, priority_score DESC);

-- Time-series partitioning preparation (for future scaling)
-- Note: These would be implemented when data volume requires partitioning

-- ================================================================================================
-- ANALYTICS VIEWS FOR BUSINESS INTELLIGENCE
-- ================================================================================================

-- Real-time revenue metrics view
CREATE OR REPLACE VIEW revenue_metrics_realtime AS
SELECT
    DATE_TRUNC('day', timestamp) as date,
    COUNT(*) as total_events,
    SUM(revenue_amount) as total_revenue,
    AVG(revenue_amount) as avg_revenue_per_event,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(revenue_amount) / COUNT(DISTINCT customer_id) as avg_revenue_per_customer
FROM revenue_attribution_events
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY date DESC;

-- Customer health score view
CREATE OR REPLACE VIEW customer_health_scores AS
SELECT
    clm.customer_id,
    clm.total_revenue,
    clm.recency_days,
    clm.engagement_score,
    clm.satisfaction_score,
    cp.predicted_clv,
    cp.churn_risk_level,
    chr.churn_probability,
    -- Calculate composite health score (0-100)
    CASE
        WHEN chr.churn_probability IS NOT NULL THEN
            GREATEST(0, LEAST(100,
                (COALESCE(clm.engagement_score, 50) * 0.3) +
                ((100 - (chr.churn_probability * 100)) * 0.4) +
                (CASE
                    WHEN clm.recency_days <= 7 THEN 30
                    WHEN clm.recency_days <= 30 THEN 20
                    WHEN clm.recency_days <= 90 THEN 10
                    ELSE 5
                END * 0.3)
            ))
        ELSE COALESCE(clm.engagement_score, 50)
    END as health_score
FROM customer_lifetime_metrics clm
LEFT JOIN clv_predictions cp ON clm.customer_id = cp.customer_id
    AND cp.expires_at > NOW()
LEFT JOIN churn_predictions chr ON clm.customer_id = chr.customer_id
    AND chr.expires_at > NOW();

-- Channel performance view
CREATE OR REPLACE VIEW channel_performance_summary AS
SELECT
    ct.channel,
    ct.touchpoint_type,
    COUNT(*) as total_touchpoints,
    COUNT(DISTINCT ct.customer_id) as unique_customers,
    COUNT(DISTINCT rae.event_id) as conversion_events,
    SUM(rae.revenue_amount) as total_attributed_revenue,
    AVG(rae.revenue_amount) as avg_revenue_per_conversion,
    (COUNT(DISTINCT rae.event_id)::DECIMAL / COUNT(DISTINCT ct.customer_id)) * 100 as conversion_rate
FROM customer_touchpoints ct
LEFT JOIN revenue_attribution_events rae ON ct.customer_id = rae.customer_id
    AND rae.timestamp BETWEEN ct.timestamp AND ct.timestamp + INTERVAL '90 days'
WHERE ct.timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY ct.channel, ct.touchpoint_type
ORDER BY total_attributed_revenue DESC;

-- Competitive threat dashboard view
CREATE OR REPLACE VIEW competitive_threats_dashboard AS
SELECT
    ct.threat_id,
    ct.competitor_id,
    cp.company_name,
    ct.threat_type,
    ct.severity,
    ct.urgency,
    ct.title,
    ct.status,
    ct.detected_at,
    EXTRACT(DAYS FROM NOW() - ct.detected_at) as days_since_detection,
    CASE
        WHEN ct.severity = 'critical' THEN 4
        WHEN ct.severity = 'high' THEN 3
        WHEN ct.severity = 'medium' THEN 2
        WHEN ct.severity = 'low' THEN 1
        ELSE 0
    END as severity_score
FROM competitive_threats ct
JOIN competitor_profiles cp ON ct.competitor_id = cp.competitor_id
WHERE ct.status = 'active'
ORDER BY severity_score DESC, ct.detected_at DESC;

-- ================================================================================================
-- FUNCTIONS AND TRIGGERS
-- ================================================================================================

-- Function to update customer lifetime metrics
CREATE OR REPLACE FUNCTION update_customer_lifetime_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update metrics when revenue events are inserted/updated
    INSERT INTO customer_lifetime_metrics (
        customer_id,
        first_purchase_date,
        last_purchase_date,
        total_purchases,
        total_revenue,
        avg_order_value,
        updated_at
    )
    SELECT
        NEW.customer_id,
        MIN(timestamp) as first_purchase_date,
        MAX(timestamp) as last_purchase_date,
        COUNT(*) as total_purchases,
        SUM(revenue_amount) as total_revenue,
        AVG(revenue_amount) as avg_order_value,
        NOW() as updated_at
    FROM revenue_attribution_events
    WHERE customer_id = NEW.customer_id
    ON CONFLICT (customer_id) DO UPDATE SET
        last_purchase_date = EXCLUDED.last_purchase_date,
        total_purchases = EXCLUDED.total_purchases,
        total_revenue = EXCLUDED.total_revenue,
        avg_order_value = EXCLUDED.avg_order_value,
        tenure_days = EXTRACT(DAYS FROM NOW() - customer_lifetime_metrics.first_purchase_date),
        recency_days = EXTRACT(DAYS FROM NOW() - EXCLUDED.last_purchase_date),
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update CLV metrics
CREATE TRIGGER trg_update_clv_metrics
    AFTER INSERT OR UPDATE ON revenue_attribution_events
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_lifetime_metrics();

-- Function to clean up expired predictions
CREATE OR REPLACE FUNCTION cleanup_expired_predictions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean up expired CLV predictions
    DELETE FROM clv_predictions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Clean up expired churn predictions
    DELETE FROM churn_predictions WHERE expires_at < NOW();

    -- Clean up old attribution results (keep 1 year)
    DELETE FROM attribution_results WHERE created_at < NOW() - INTERVAL '1 year';

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate attribution weights (simplified)
CREATE OR REPLACE FUNCTION calculate_attribution_weights(
    touchpoint_timestamps TIMESTAMP[],
    attribution_model VARCHAR DEFAULT 'last_touch'
)
RETURNS DECIMAL[] AS $$
DECLARE
    weights DECIMAL[];
    touchpoint_count INTEGER;
    i INTEGER;
BEGIN
    touchpoint_count := array_length(touchpoint_timestamps, 1);

    IF touchpoint_count IS NULL OR touchpoint_count = 0 THEN
        RETURN ARRAY[]::DECIMAL[];
    END IF;

    CASE attribution_model
        WHEN 'first_touch' THEN
            -- Give all credit to first touchpoint
            weights := ARRAY[1.0];
            FOR i IN 2..touchpoint_count LOOP
                weights := array_append(weights, 0.0);
            END LOOP;

        WHEN 'last_touch' THEN
            -- Give all credit to last touchpoint
            FOR i IN 1..(touchpoint_count-1) LOOP
                weights := array_append(weights, 0.0);
            END LOOP;
            weights := array_append(weights, 1.0);

        WHEN 'linear' THEN
            -- Distribute credit equally
            FOR i IN 1..touchpoint_count LOOP
                weights := array_append(weights, 1.0 / touchpoint_count);
            END LOOP;

        ELSE
            -- Default to last touch
            FOR i IN 1..(touchpoint_count-1) LOOP
                weights := array_append(weights, 0.0);
            END LOOP;
            weights := array_append(weights, 1.0);
    END CASE;

    RETURN weights;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- DATA VALIDATION AND CONSTRAINTS
-- ================================================================================================

-- Validate customer touchpoint data integrity
CREATE OR REPLACE FUNCTION validate_touchpoint_data()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure timestamp is not in the future
    IF NEW.timestamp > NOW() + INTERVAL '1 hour' THEN
        RAISE EXCEPTION 'Touchpoint timestamp cannot be more than 1 hour in the future';
    END IF;

    -- Ensure session duration is reasonable (< 24 hours)
    IF NEW.session_duration IS NOT NULL AND NEW.session_duration > 86400 THEN
        RAISE EXCEPTION 'Session duration cannot exceed 24 hours';
    END IF;

    -- Set updated_at
    NEW.updated_at := NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_touchpoint_data
    BEFORE INSERT OR UPDATE ON customer_touchpoints
    FOR EACH ROW
    EXECUTE FUNCTION validate_touchpoint_data();

-- ================================================================================================
-- PERFORMANCE MONITORING
-- ================================================================================================

-- Create monitoring table for query performance
CREATE TABLE IF NOT EXISTS analytics_query_performance (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_type VARCHAR(100) NOT NULL, -- 'attribution_report', 'clv_analysis', etc.
    execution_time_ms INTEGER NOT NULL,
    rows_processed INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Query metadata
    parameters JSONB DEFAULT '{}',
    performance_notes TEXT
);

-- Index for performance monitoring
CREATE INDEX IF NOT EXISTS idx_query_performance_type_time ON analytics_query_performance(query_type, executed_at DESC);

-- ================================================================================================
-- SECURITY AND PERMISSIONS
-- ================================================================================================

-- Create analytics role for read-only access
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analytics_readonly') THEN
        CREATE ROLE analytics_readonly;
    END IF;
END $$;

-- Grant appropriate permissions for analytics role
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;
GRANT USAGE ON SCHEMA public TO analytics_readonly;

-- Ensure analytics tables have proper permissions
GRANT SELECT ON
    customer_touchpoints,
    revenue_attribution_events,
    attribution_results,
    customer_lifetime_metrics,
    clv_predictions,
    churn_predictions,
    customer_cohorts,
    competitor_profiles,
    competitive_pricing_intelligence,
    feature_comparisons,
    market_sentiment,
    competitive_threats,
    market_opportunities
TO analytics_readonly;

-- Grant access to views
GRANT SELECT ON
    revenue_metrics_realtime,
    customer_health_scores,
    channel_performance_summary,
    competitive_threats_dashboard
TO analytics_readonly;

-- ================================================================================================
-- FINAL VALIDATION AND CLEANUP
-- ================================================================================================

-- Validate all tables were created successfully
DO $$
DECLARE
    table_count INTEGER;
    expected_tables TEXT[] := ARRAY[
        'customer_touchpoints',
        'revenue_attribution_events',
        'attribution_results',
        'customer_lifetime_metrics',
        'clv_predictions',
        'churn_predictions',
        'customer_cohorts',
        'competitor_profiles',
        'competitive_pricing_intelligence',
        'feature_comparisons',
        'market_sentiment',
        'competitive_threats',
        'market_opportunities',
        'analytics_query_performance'
    ];
    missing_tables TEXT[] := ARRAY[]::TEXT[];
    table_name TEXT;
BEGIN
    -- Check that all expected tables exist
    FOREACH table_name IN ARRAY expected_tables LOOP
        IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = table_name) THEN
            missing_tables := array_append(missing_tables, table_name);
        END IF;
    END LOOP;

    IF array_length(missing_tables, 1) > 0 THEN
        RAISE EXCEPTION 'Missing tables: %', array_to_string(missing_tables, ', ');
    END IF;

    -- Count total tables created
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_name = ANY(expected_tables);

    RAISE NOTICE 'Enterprise Analytics Migration completed successfully. Created % tables.', table_count;
END $$;

-- Update migration record with completion time
UPDATE schema_migrations
SET execution_time_ms = EXTRACT(EPOCH FROM (NOW() - applied_at)) * 1000,
    checksum = md5('012_enterprise_analytics_complete')
WHERE version = '012';

-- Log completion with summary
SELECT
    'Migration 012 completed successfully' as status,
    version,
    description,
    applied_at,
    execution_time_ms || ' ms' as execution_time
FROM schema_migrations
WHERE version = '012';

COMMIT;