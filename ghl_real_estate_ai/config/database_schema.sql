-- EnterpriseHub Real Estate AI - Production Database Schema
-- Critical Missing Component: Database persistence for all services
--
-- This schema supports:
-- - Lead tracking and attribution
-- - Property data storage
-- - Market analytics
-- - A/B testing results
-- - Follow-up engine state
-- - Revenue attribution
-- - Churn prediction
-- - Behavioral analysis

-- Enable PostGIS for geospatial operations
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- LEAD MANAGEMENT TABLES
-- ============================================================================

CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Lead Identification
    ghl_lead_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),

    -- Lead Source Attribution
    source VARCHAR(100) NOT NULL, -- website, referral, social, paid_ads
    campaign_id VARCHAR(255),
    referrer_url TEXT,
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),

    -- Lead Qualification
    lead_score INTEGER DEFAULT 0,
    qualification_stage VARCHAR(50) DEFAULT 'unqualified',
    budget_min DECIMAL(12,2),
    budget_max DECIMAL(12,2),
    prequalified_amount DECIMAL(12,2),

    -- Property Preferences
    preferred_locations JSONB,
    property_types TEXT[], -- {single_family, condo, townhome}
    bedrooms_min INTEGER,
    bedrooms_max INTEGER,
    bathrooms_min DECIMAL(3,1),
    bathrooms_max DECIMAL(3,1),

    -- Behavioral Data
    engagement_score INTEGER DEFAULT 0,
    last_activity_date TIMESTAMP WITH TIME ZONE,
    total_property_views INTEGER DEFAULT 0,
    total_inquiries INTEGER DEFAULT 0,
    total_tours INTEGER DEFAULT 0,

    -- Conversion Tracking
    converted BOOLEAN DEFAULT FALSE,
    conversion_date TIMESTAMP WITH TIME ZONE,
    conversion_value DECIMAL(12,2),
    conversion_type VARCHAR(50), -- purchase, rental, listing

    -- Meta
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes for performance
    CONSTRAINT leads_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_leads_ghl_id ON leads(ghl_lead_id);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_score ON leads(lead_score DESC);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_stage ON leads(qualification_stage);
CREATE INDEX idx_leads_activity ON leads(last_activity_date DESC);
CREATE INDEX idx_leads_converted ON leads(converted, conversion_date);

-- ============================================================================
-- PROPERTY TABLES
-- ============================================================================

CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Property Identification
    property_id VARCHAR(255) UNIQUE NOT NULL,
    mls_number VARCHAR(100),

    -- Address & Location
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(20) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    location GEOMETRY(POINT, 4326), -- PostGIS point for geospatial queries

    -- Property Details
    price DECIMAL(12,2) NOT NULL,
    list_price DECIMAL(12,2) NOT NULL,
    square_feet INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    lot_size INTEGER,
    year_built INTEGER,
    property_type VARCHAR(50) NOT NULL,

    -- Market Status
    status VARCHAR(20) DEFAULT 'active',
    list_date DATE,
    last_price_change DATE,
    price_change_amount DECIMAL(12,2),
    days_on_market INTEGER DEFAULT 0,
    price_per_sqft DECIMAL(8,2),

    -- Valuation
    estimated_value DECIMAL(12,2),
    value_confidence DECIMAL(3,2),
    comparative_market_analysis JSONB,

    -- Property Features
    features JSONB,
    description TEXT,
    photos TEXT[],

    -- School & Neighborhood
    school_district VARCHAR(100),
    neighborhood_id UUID REFERENCES neighborhoods(id),
    walkability_score INTEGER,

    -- Data Source
    data_source VARCHAR(50) DEFAULT 'mls',
    data_quality_score DECIMAL(3,2) DEFAULT 0.0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Meta
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Geospatial index for location-based queries
CREATE INDEX idx_properties_location ON properties USING GIST (location);
CREATE INDEX idx_properties_price ON properties(price);
CREATE INDEX idx_properties_status ON properties(status);
CREATE INDEX idx_properties_type ON properties(property_type);
CREATE INDEX idx_properties_bedrooms ON properties(bedrooms);
CREATE INDEX idx_properties_city_zip ON properties(city, zip_code);
CREATE INDEX idx_properties_list_date ON properties(list_date DESC);

-- ============================================================================
-- NEIGHBORHOOD & MARKET DATA
-- ============================================================================

CREATE TABLE neighborhoods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identification
    name VARCHAR(200) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(20) NOT NULL,
    zip_codes TEXT[],
    boundary GEOMETRY(MULTIPOLYGON, 4326), -- Neighborhood boundaries

    -- Market Metrics
    median_price DECIMAL(12,2),
    price_trend_3m DECIMAL(5,4), -- Percentage change
    price_trend_1y DECIMAL(5,4),
    inventory_months DECIMAL(4,2),
    avg_days_on_market INTEGER,
    sale_to_list_ratio DECIMAL(3,2),

    -- Demographics
    population INTEGER,
    median_income DECIMAL(12,2),
    median_age DECIMAL(4,1),
    education_level VARCHAR(50),

    -- Amenities & Ratings
    school_rating DECIMAL(3,1),
    walkability_score INTEGER,
    transit_score INTEGER,
    crime_score INTEGER,

    -- Market Analysis
    market_temperature VARCHAR(20), -- hot, warm, cool, cold
    investment_grade VARCHAR(20), -- A, B, C, D
    rental_yield_estimate DECIMAL(5,4),

    -- Meta
    last_analyzed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_neighborhoods_city_state ON neighborhoods(city, state);
CREATE INDEX idx_neighborhoods_boundary ON neighborhoods USING GIST (boundary);
CREATE INDEX idx_neighborhoods_median_price ON neighborhoods(median_price DESC);

-- ============================================================================
-- LEAD-PROPERTY INTERACTIONS
-- ============================================================================

CREATE TABLE lead_property_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign Keys
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    -- Interaction Details
    interaction_type VARCHAR(50) NOT NULL, -- viewed, saved, inquired, toured, offered
    interaction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Context
    source VARCHAR(100), -- website, app, email, sms
    device_type VARCHAR(50),
    user_agent TEXT,
    referrer_url TEXT,

    -- Engagement Metrics
    duration_seconds INTEGER,
    scroll_percentage INTEGER,
    clicked_elements JSONB,

    -- Follow-up Status
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_completed BOOLEAN DEFAULT FALSE,
    follow_up_date TIMESTAMP WITH TIME ZONE,

    -- Attribution
    attributed_to_conversion BOOLEAN DEFAULT FALSE,
    attribution_weight DECIMAL(5,4) DEFAULT 0.0000,

    -- Meta
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_interactions_lead_id ON lead_property_interactions(lead_id);
CREATE INDEX idx_interactions_property_id ON lead_property_interactions(property_id);
CREATE INDEX idx_interactions_type_date ON lead_property_interactions(interaction_type, interaction_date DESC);
CREATE INDEX idx_interactions_follow_up ON lead_property_interactions(follow_up_required, follow_up_completed);

-- ============================================================================
-- FOLLOW-UP ENGINE TABLES
-- ============================================================================

CREATE TABLE follow_up_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Campaign Definition
    name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(100) NOT NULL, -- behavioral, time_based, manual
    trigger_criteria JSONB NOT NULL,

    -- Campaign Flow
    sequence_steps JSONB NOT NULL, -- Array of step definitions
    total_steps INTEGER NOT NULL,

    -- Targeting
    target_segments JSONB, -- Lead qualification criteria
    exclusion_rules JSONB,

    -- Performance
    active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,

    -- A/B Testing
    ab_test_id UUID,
    ab_test_variant VARCHAR(10),

    -- Meta
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE follow_up_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- References
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES follow_up_campaigns(id),

    -- Execution State
    current_step INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'active', -- active, paused, completed, failed

    -- Schedule
    next_execution_time TIMESTAMP WITH TIME ZONE,
    last_execution_time TIMESTAMP WITH TIME ZONE,

    -- Agent Decisions
    agent_decisions JSONB, -- Track autonomous agent choices
    personalizations JSONB, -- Dynamic content decisions

    -- Performance
    total_opens INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_replies INTEGER DEFAULT 0,
    conversion_achieved BOOLEAN DEFAULT FALSE,

    -- Meta
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_executions_lead_id ON follow_up_executions(lead_id);
CREATE INDEX idx_executions_campaign_id ON follow_up_executions(campaign_id);
CREATE INDEX idx_executions_status ON follow_up_executions(status);
CREATE INDEX idx_executions_next_time ON follow_up_executions(next_execution_time);

CREATE TABLE follow_up_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- References
    execution_id UUID NOT NULL REFERENCES follow_up_executions(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Message Details
    step_number INTEGER NOT NULL,
    message_type VARCHAR(50) NOT NULL, -- email, sms, call, task
    channel VARCHAR(50), -- gmail, twilio, ghl, etc

    -- Content
    subject VARCHAR(500),
    content TEXT NOT NULL,
    personalized_content JSONB, -- Dynamic insertions

    -- Delivery
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,

    -- Engagement
    opened_at TIMESTAMP WITH TIME ZONE,
    first_click_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE,
    reply_content TEXT,

    -- Status
    status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, sent, delivered, opened, clicked, replied, failed
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Agent Attribution
    generated_by_agent VARCHAR(100),
    confidence_score DECIMAL(3,2),

    -- Meta
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_execution_id ON follow_up_messages(execution_id);
CREATE INDEX idx_messages_lead_id ON follow_up_messages(lead_id);
CREATE INDEX idx_messages_scheduled ON follow_up_messages(scheduled_for);
CREATE INDEX idx_messages_status ON follow_up_messages(status);
CREATE INDEX idx_messages_type ON follow_up_messages(message_type);

-- ============================================================================
-- A/B TESTING TABLES
-- ============================================================================

CREATE TABLE ab_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Test Definition
    name VARCHAR(255) NOT NULL,
    description TEXT,
    hypothesis TEXT,

    -- Test Configuration
    test_type VARCHAR(50) NOT NULL, -- message_content, timing, channel, landing_page
    control_variant JSONB NOT NULL,
    test_variants JSONB NOT NULL, -- Array of variant definitions

    -- Traffic Allocation
    allocation_method VARCHAR(50) DEFAULT 'random', -- random, weighted, thompson_sampling
    traffic_allocation JSONB NOT NULL, -- Percentage per variant

    -- Success Metrics
    primary_metric VARCHAR(100) NOT NULL,
    secondary_metrics JSONB,
    minimum_effect_size DECIMAL(5,4),
    confidence_level DECIMAL(3,2) DEFAULT 0.95,

    -- Test Lifecycle
    status VARCHAR(50) DEFAULT 'draft', -- draft, running, paused, completed, failed
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    target_sample_size INTEGER,

    -- Statistical Analysis
    statistical_significance BOOLEAN DEFAULT FALSE,
    winning_variant VARCHAR(10),
    confidence_interval JSONB,
    p_value DECIMAL(10,8),

    -- Meta
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE ab_test_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- References
    test_id UUID NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Assignment
    variant VARCHAR(10) NOT NULL,
    assignment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Outcomes
    conversion_achieved BOOLEAN DEFAULT FALSE,
    conversion_date TIMESTAMP WITH TIME ZONE,
    conversion_value DECIMAL(12,2),
    secondary_conversions JSONB,

    -- Meta
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(test_id, lead_id)
);

CREATE INDEX idx_ab_participants_test_id ON ab_test_participants(test_id);
CREATE INDEX idx_ab_participants_lead_id ON ab_test_participants(lead_id);
CREATE INDEX idx_ab_participants_variant ON ab_test_participants(test_id, variant);

-- ============================================================================
-- BEHAVIORAL ANALYSIS TABLES
-- ============================================================================

CREATE TABLE behavioral_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- References
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Signal Details
    signal_type VARCHAR(100) NOT NULL,
    signal_value DECIMAL(8,4),
    weight DECIMAL(5,4),
    confidence DECIMAL(3,2),

    -- Context
    source VARCHAR(100), -- website, email, phone, app
    session_id VARCHAR(255),
    page_url TEXT,

    -- Signal Data
    raw_data JSONB,
    processed_data JSONB,

    -- Timing
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Meta
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_signals_lead_id ON behavioral_signals(lead_id);
CREATE INDEX idx_signals_type ON behavioral_signals(signal_type);
CREATE INDEX idx_signals_detected ON behavioral_signals(detected_at DESC);
CREATE INDEX idx_signals_value ON behavioral_signals(signal_value DESC);

CREATE TABLE churn_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- References
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Prediction
    churn_probability DECIMAL(5,4) NOT NULL,
    risk_level VARCHAR(20) NOT NULL, -- low, medium, high, critical

    -- Contributing Factors
    feature_importances JSONB,
    key_risk_factors JSONB,

    -- Recommendations
    intervention_recommendations JSONB,
    expected_intervention_impact DECIMAL(5,4),

    -- Model Information
    model_version VARCHAR(50),
    model_confidence DECIMAL(3,2),
    prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Action Taken
    intervention_applied BOOLEAN DEFAULT FALSE,
    intervention_date TIMESTAMP WITH TIME ZONE,
    intervention_result VARCHAR(50),

    -- Meta
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_churn_lead_id ON churn_predictions(lead_id);
CREATE INDEX idx_churn_probability ON churn_predictions(churn_probability DESC);
CREATE INDEX idx_churn_risk_level ON churn_predictions(risk_level);
CREATE INDEX idx_churn_prediction_date ON churn_predictions(prediction_date DESC);

-- ============================================================================
-- REVENUE ATTRIBUTION TABLES
-- ============================================================================

CREATE TABLE revenue_attributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- References
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Attribution Model
    model_type VARCHAR(50) DEFAULT 'first_touch', -- first_touch, last_touch, linear, time_decay, position_based
    attribution_confidence DECIMAL(5,4),

    -- Revenue Details
    total_revenue DECIMAL(12,2) NOT NULL,
    attributed_revenue DECIMAL(12,2) NOT NULL,
    commission_amount DECIMAL(12,2),

    -- Touchpoint Attribution
    touchpoint_attributions JSONB NOT NULL, -- Array of {touchpoint, weight, attributed_value}

    -- Journey Analysis
    journey_length_days INTEGER,
    total_touchpoints INTEGER,
    first_touchpoint_date TIMESTAMP WITH TIME ZONE,
    conversion_touchpoint_date TIMESTAMP WITH TIME ZONE,

    -- Channel Performance
    top_channel VARCHAR(100),
    channel_mix JSONB, -- Breakdown by channel

    -- System Attribution
    ai_system_attribution DECIMAL(12,2), -- Revenue attributed to AI system
    human_agent_attribution DECIMAL(12,2),
    organic_attribution DECIMAL(12,2),

    -- Validation
    validated BOOLEAN DEFAULT FALSE,
    validation_date TIMESTAMP WITH TIME ZONE,
    validation_notes TEXT,

    -- Meta
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_attribution_lead_id ON revenue_attributions(lead_id);
CREATE INDEX idx_attribution_total_revenue ON revenue_attributions(total_revenue DESC);
CREATE INDEX idx_attribution_ai_attribution ON revenue_attributions(ai_system_attribution DESC);
CREATE INDEX idx_attribution_analysis_date ON revenue_attributions(analysis_date DESC);

-- ============================================================================
-- MARKET ANALYTICS TABLES
-- ============================================================================

CREATE TABLE market_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Market Identification
    area_code VARCHAR(20) NOT NULL,
    area_name VARCHAR(200) NOT NULL,
    area_type VARCHAR(50), -- zip_code, city, county, metro

    -- Price Metrics
    median_price DECIMAL(12,2),
    median_price_1m DECIMAL(12,2),
    median_price_3m DECIMAL(12,2),
    median_price_1y DECIMAL(12,2),
    price_trend_percentage DECIMAL(7,4),
    price_per_sqft_median DECIMAL(8,2),

    -- Market Activity
    active_listings INTEGER,
    new_listings_7d INTEGER,
    sold_listings_7d INTEGER,
    pending_listings INTEGER,
    inventory_months DECIMAL(4,2),

    -- Market Conditions
    avg_days_on_market INTEGER,
    sale_to_list_ratio DECIMAL(5,4),
    market_temperature VARCHAR(20),
    absorption_rate DECIMAL(5,4),

    -- Investment Metrics
    rental_yield_estimate DECIMAL(5,4),
    cap_rate_estimate DECIMAL(5,4),
    appreciation_forecast_1y DECIMAL(7,4),

    -- Data Quality
    data_completeness DECIMAL(3,2),
    confidence_score DECIMAL(3,2),
    last_data_update TIMESTAMP WITH TIME ZONE,

    -- Meta
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(area_code, snapshot_date)
);

CREATE INDEX idx_market_snapshots_area ON market_snapshots(area_code, snapshot_date DESC);
CREATE INDEX idx_market_snapshots_price ON market_snapshots(median_price DESC);
CREATE INDEX idx_market_snapshots_temperature ON market_snapshots(market_temperature);

-- ============================================================================
-- SYSTEM MONITORING TABLES
-- ============================================================================

CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Metric Identification
    metric_name VARCHAR(200) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- counter, gauge, histogram, timer
    service_name VARCHAR(100) NOT NULL,

    -- Metric Value
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(20),

    -- Dimensions
    tags JSONB,
    host VARCHAR(100),
    environment VARCHAR(50),

    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Meta
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Partitioning by timestamp for performance
CREATE INDEX idx_metrics_name_timestamp ON system_metrics(metric_name, timestamp DESC);
CREATE INDEX idx_metrics_service_timestamp ON system_metrics(service_name, timestamp DESC);
CREATE INDEX idx_metrics_timestamp ON system_metrics(timestamp DESC);

-- ============================================================================
-- PERFORMANCE TRACKING
-- ============================================================================

CREATE TABLE performance_benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Benchmark Definition
    benchmark_name VARCHAR(200) NOT NULL,
    benchmark_type VARCHAR(100) NOT NULL, -- response_time, throughput, accuracy, conversion
    service_component VARCHAR(100),

    -- Performance Data
    target_value DECIMAL(15,6),
    actual_value DECIMAL(15,6),
    threshold_warning DECIMAL(15,6),
    threshold_critical DECIMAL(15,6),

    -- Status
    status VARCHAR(50), -- healthy, warning, critical
    deviation_percentage DECIMAL(7,4),

    -- Context
    measurement_period INTERVAL,
    sample_size INTEGER,
    measurement_conditions JSONB,

    -- Meta
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_benchmarks_name_date ON performance_benchmarks(benchmark_name, measured_at DESC);
CREATE INDEX idx_benchmarks_status ON performance_benchmarks(status, measured_at DESC);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to tables with updated_at columns
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_properties_updated_at BEFORE UPDATE ON properties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_neighborhoods_updated_at BEFORE UPDATE ON neighborhoods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_follow_up_campaigns_updated_at BEFORE UPDATE ON follow_up_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_follow_up_executions_updated_at BEFORE UPDATE ON follow_up_executions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_follow_up_messages_updated_at BEFORE UPDATE ON follow_up_messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ab_tests_updated_at BEFORE UPDATE ON ab_tests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Lead Performance Summary
CREATE VIEW lead_performance_summary AS
SELECT
    l.id,
    l.ghl_lead_id,
    l.email,
    l.lead_score,
    l.qualification_stage,
    l.total_property_views,
    l.total_inquiries,
    l.total_tours,
    l.converted,
    l.conversion_value,
    COUNT(lpi.id) as total_interactions,
    MAX(lpi.interaction_date) as last_interaction,
    CASE
        WHEN l.converted THEN 'Converted'
        WHEN COUNT(lpi.id) > 10 THEN 'Highly Engaged'
        WHEN COUNT(lpi.id) > 5 THEN 'Engaged'
        WHEN COUNT(lpi.id) > 0 THEN 'Active'
        ELSE 'New'
    END as engagement_level
FROM leads l
LEFT JOIN lead_property_interactions lpi ON l.id = lpi.lead_id
GROUP BY l.id, l.ghl_lead_id, l.email, l.lead_score, l.qualification_stage,
         l.total_property_views, l.total_inquiries, l.total_tours, l.converted, l.conversion_value;

-- Property Market Performance
CREATE VIEW property_market_performance AS
SELECT
    p.id,
    p.property_id,
    p.address,
    p.city,
    p.price,
    p.days_on_market,
    p.status,
    COUNT(lpi.id) as total_views,
    COUNT(DISTINCT lpi.lead_id) as unique_viewers,
    AVG(lpi.duration_seconds) as avg_view_duration,
    COUNT(CASE WHEN lpi.interaction_type = 'inquired' THEN 1 END) as inquiries,
    COUNT(CASE WHEN lpi.interaction_type = 'toured' THEN 1 END) as tours,
    ROUND(
        COUNT(CASE WHEN lpi.interaction_type = 'inquired' THEN 1 END)::DECIMAL /
        NULLIF(COUNT(lpi.id), 0) * 100,
        2
    ) as inquiry_rate
FROM properties p
LEFT JOIN lead_property_interactions lpi ON p.id = lpi.property_id
WHERE p.status IN ('active', 'pending')
GROUP BY p.id, p.property_id, p.address, p.city, p.price, p.days_on_market, p.status;

-- Revenue Attribution Summary
CREATE VIEW revenue_attribution_summary AS
SELECT
    DATE_TRUNC('month', ra.analysis_date) as month,
    COUNT(*) as total_conversions,
    SUM(ra.total_revenue) as total_revenue,
    SUM(ra.attributed_revenue) as attributed_revenue,
    SUM(ra.ai_system_attribution) as ai_system_revenue,
    SUM(ra.human_agent_attribution) as human_agent_revenue,
    ROUND(AVG(ra.attribution_confidence), 4) as avg_confidence,
    ROUND(
        SUM(ra.ai_system_attribution) / NULLIF(SUM(ra.total_revenue), 0) * 100,
        2
    ) as ai_attribution_percentage
FROM revenue_attributions ra
WHERE ra.validated = true
GROUP BY DATE_TRUNC('month', ra.analysis_date)
ORDER BY month DESC;

-- ============================================================================
-- SAMPLE DATA INSERTION FUNCTIONS (for development)
-- ============================================================================

-- Function to generate sample leads for testing
CREATE OR REPLACE FUNCTION insert_sample_lead(
    p_email VARCHAR(255),
    p_first_name VARCHAR(100) DEFAULT 'Test',
    p_last_name VARCHAR(100) DEFAULT 'User',
    p_source VARCHAR(100) DEFAULT 'website'
) RETURNS UUID AS $$
DECLARE
    new_lead_id UUID;
BEGIN
    INSERT INTO leads (
        ghl_lead_id, email, first_name, last_name, source,
        lead_score, budget_min, budget_max, bedrooms_min, bedrooms_max
    ) VALUES (
        'GHL_' || REPLACE(p_email, '@', '_') || '_' || EXTRACT(epoch FROM NOW()),
        p_email, p_first_name, p_last_name, p_source,
        FLOOR(RANDOM() * 100),
        300000 + FLOOR(RANDOM() * 200000),
        500000 + FLOOR(RANDOM() * 300000),
        2 + FLOOR(RANDOM() * 3),
        3 + FLOOR(RANDOM() * 3)
    ) RETURNING id INTO new_lead_id;

    RETURN new_lead_id;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your environment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;