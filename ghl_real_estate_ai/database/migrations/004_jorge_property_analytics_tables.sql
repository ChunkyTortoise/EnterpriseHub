-- Jorge's Enhanced Lead Bot - Property Matching & Analytics Tables
-- Migration: 004_jorge_property_analytics_tables.sql
-- Author: Claude Code - Advanced Analytics Integration
-- Created: 2026-01-19

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- ==========================================
-- PROPERTY MATCHING SYSTEM TABLES
-- ==========================================

-- Property inventory cache (from MLS)
CREATE TABLE jorge_properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mls_number VARCHAR(50) UNIQUE,

    -- Address
    street VARCHAR(255) NOT NULL,
    city VARCHAR(100) DEFAULT 'Rancho Cucamonga',
    state VARCHAR(10) DEFAULT 'CA',
    zip_code VARCHAR(10) NOT NULL,
    neighborhood VARCHAR(100),
    coordinates POINT, -- PostGIS point for lat/lng

    -- Basic info
    price DECIMAL(12,2) NOT NULL,
    bedrooms INTEGER NOT NULL,
    bathrooms DECIMAL(3,1) NOT NULL,
    sqft INTEGER NOT NULL,
    lot_size_sqft INTEGER,
    year_built INTEGER,
    property_type VARCHAR(50) NOT NULL, -- single_family, townhome, condo, etc.

    -- Features (stored as JSONB for flexibility)
    features JSONB DEFAULT '{}',
    amenities TEXT[],

    -- Schools (JSONB array)
    schools JSONB DEFAULT '[]',

    -- Market data
    days_on_market INTEGER DEFAULT 0,
    price_per_sqft DECIMAL(8,2),
    estimated_value DECIMAL(12,2),
    price_history JSONB DEFAULT '[]',

    -- Location intelligence
    commute_to_la_minutes INTEGER,
    walkability_score INTEGER CHECK (walkability_score >= 0 AND walkability_score <= 100),

    -- Media
    images TEXT[] DEFAULT '{}',
    virtual_tour_url TEXT,

    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'pending', 'sold', 'withdrawn')),
    listing_date DATE NOT NULL,
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lead property preferences (extracted from conversations and scoring)
CREATE TABLE jorge_lead_preferences (
    lead_id VARCHAR(50) PRIMARY KEY,

    -- Budget
    budget_min DECIMAL(12,2),
    budget_max DECIMAL(12,2),

    -- Property requirements
    preferred_bedrooms INTEGER,
    min_bedrooms INTEGER,
    preferred_bathrooms DECIMAL(3,1),
    min_bathrooms DECIMAL(3,1),

    -- Location preferences
    preferred_neighborhoods TEXT[],
    max_commute_minutes INTEGER,
    school_rating_min INTEGER CHECK (school_rating_min >= 1 AND school_rating_min <= 10),

    -- Features
    must_have_features TEXT[],
    nice_to_have_features TEXT[],
    dealbreaker_features TEXT[],

    -- Property type and size
    property_type_preference VARCHAR(50),
    max_year_built INTEGER,
    min_sqft INTEGER,
    max_sqft INTEGER,

    -- Timeline
    timeline_urgency VARCHAR(20) CHECK (timeline_urgency IN ('immediate', '30d', '60d', '90d', 'flexible')),

    -- Extraction metadata
    extracted_from_scoring BOOLEAN DEFAULT TRUE,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Timestamps
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Property match history and results
CREATE TABLE jorge_property_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id VARCHAR(50) NOT NULL,
    property_id UUID NOT NULL REFERENCES jorge_properties(id) ON DELETE CASCADE,

    -- Scoring
    match_score DECIMAL(5,2) NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
    neural_score DECIMAL(5,2) CHECK (neural_score >= 0 AND neural_score <= 100),
    rule_score DECIMAL(5,2) CHECK (rule_score >= 0 AND rule_score <= 100),
    confidence_level VARCHAR(20) CHECK (confidence_level IN ('very_high', 'high', 'medium', 'low', 'very_low')),

    -- Reasoning (AI-generated explanations)
    match_reasoning JSONB,
    jorge_talking_points TEXT[],

    -- Ranking and algorithm
    recommendation_rank INTEGER CHECK (recommendation_rank >= 1),
    algorithm_used VARCHAR(30) DEFAULT 'jorge_optimized',

    -- Performance tracking
    processing_time_ms INTEGER,
    model_version VARCHAR(50),

    -- Lead interaction tracking
    presented_to_lead BOOLEAN DEFAULT FALSE,
    lead_response VARCHAR(20) CHECK (lead_response IN ('interested', 'not_interested', 'viewed', 'scheduled_showing')),
    viewed_at TIMESTAMP WITH TIME ZONE,
    response_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    matched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key constraint
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- ==========================================
-- ANALYTICS SYSTEM TABLES
-- ==========================================

-- Revenue forecasting storage
CREATE TABLE revenue_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Forecast details
    forecast_date DATE NOT NULL,
    horizon_days INTEGER NOT NULL CHECK (horizon_days > 0),
    forecasted_revenue DECIMAL(12,2) NOT NULL,
    confidence_lower DECIMAL(12,2),
    confidence_upper DECIMAL(12,2),
    confidence_level DECIMAL(3,2) CHECK (confidence_level >= 0.5 AND confidence_level <= 0.99),

    -- Predictions
    predicted_conversions INTEGER,
    avg_deal_value DECIMAL(12,2),

    -- Model performance
    model_accuracy DECIMAL(5,4) CHECK (model_accuracy >= 0 AND model_accuracy <= 1),
    historical_mape DECIMAL(5,4), -- Mean Absolute Percentage Error
    model_version VARCHAR(50),

    -- Business context
    key_assumptions TEXT[],
    risk_factors TEXT[],
    market_conditions VARCHAR(20) CHECK (market_conditions IN ('hot', 'warm', 'cool', 'cold')),

    -- Actual tracking (filled later for accuracy measurement)
    actual_revenue DECIMAL(12,2),
    actual_conversions INTEGER,
    forecast_error DECIMAL(5,4), -- Actual error when measured

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversion funnel performance snapshots
CREATE TABLE funnel_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Snapshot details
    snapshot_date DATE NOT NULL,
    time_window_days INTEGER DEFAULT 30,

    -- Funnel stage details
    stage VARCHAR(50) NOT NULL CHECK (stage IN ('new_lead', 'qualified', 'appointment', 'showing', 'offer', 'under_contract', 'closed')),
    lead_count INTEGER NOT NULL CHECK (lead_count >= 0),
    conversion_rate DECIMAL(5,4) CHECK (conversion_rate >= 0 AND conversion_rate <= 1),
    avg_time_in_stage_days DECIMAL(8,2),
    drop_off_count INTEGER DEFAULT 0,
    drop_off_percentage DECIMAL(5,4),

    -- Segmentation
    segment_type VARCHAR(50), -- 'source', 'agent', 'geography', 'priority'
    segment_value VARCHAR(100),

    -- Performance metadata
    improvement_potential_percent DECIMAL(5,2),
    bottleneck_indicator BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lead scoring performance and accuracy tracking
CREATE TABLE lead_scoring_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id VARCHAR(50) NOT NULL,

    -- Scoring details
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    priority_level VARCHAR(20) CHECK (priority_level IN ('immediate', 'high', 'medium', 'low', 'disqualified')),
    predicted_conversion_probability DECIMAL(5,4) CHECK (predicted_conversion_probability >= 0 AND predicted_conversion_probability <= 1),
    predicted_timeline_days INTEGER,

    -- Dimension breakdown (6D scoring)
    intent_score DECIMAL(5,2),
    financial_score DECIMAL(5,2),
    timeline_score DECIMAL(5,2),
    engagement_score DECIMAL(5,2),
    referral_score DECIMAL(5,2),
    local_score DECIMAL(5,2),

    -- Actual outcome (tracked over time)
    actual_converted BOOLEAN,
    actual_conversion_date TIMESTAMP WITH TIME ZONE,
    actual_timeline_days INTEGER,
    conversion_value DECIMAL(12,2),

    -- Model performance
    model_version VARCHAR(50),
    prediction_error DECIMAL(5,4), -- |predicted - actual|
    calibration_bucket VARCHAR(20), -- '0-20%', '20-40%', etc.

    -- Timestamps
    scored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- ROI tracking by lead source and campaign
CREATE TABLE source_roi_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Source identification
    tracking_date DATE NOT NULL,
    source_type VARCHAR(100) NOT NULL, -- 'Zillow', 'Facebook', 'Referral', etc.
    campaign_id VARCHAR(255),
    source_details JSONB DEFAULT '{}',

    -- Cost tracking
    acquisition_cost DECIMAL(10,2) DEFAULT 0,
    operational_cost DECIMAL(10,2) DEFAULT 0,
    total_cost DECIMAL(10,2) NOT NULL,

    -- Revenue tracking
    total_revenue DECIMAL(12,2) DEFAULT 0,
    attributed_conversions INTEGER DEFAULT 0,
    avg_deal_value DECIMAL(12,2),

    -- ROI calculations
    roi_percentage DECIMAL(7,2), -- Can be negative
    ltv_cac_ratio DECIMAL(5,2),
    payback_period_days INTEGER,

    -- Quality metrics
    avg_lead_score DECIMAL(5,2),
    conversion_rate DECIMAL(5,4) CHECK (conversion_rate >= 0 AND conversion_rate <= 1),
    cost_per_conversion DECIMAL(10,2),

    -- Performance indicators
    lead_quality_index DECIMAL(5,2), -- 0-100 composite score
    efficiency_score DECIMAL(5,2),   -- 0-100 cost efficiency

    -- Timestamps
    measurement_period_days INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Market timing and conditions analysis
CREATE TABLE market_timing_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_date DATE NOT NULL,
    market_area VARCHAR(100) DEFAULT 'Rancho Cucamonga',

    -- Supply metrics
    active_inventory INTEGER DEFAULT 0,
    new_listings_count INTEGER DEFAULT 0,
    inventory_months DECIMAL(4,2), -- Months of supply

    -- Demand metrics
    buyer_demand_index DECIMAL(5,2) CHECK (buyer_demand_index >= 0 AND buyer_demand_index <= 100),
    showing_activity_count INTEGER DEFAULT 0,
    offer_activity_count INTEGER DEFAULT 0,

    -- Pricing metrics
    median_list_price DECIMAL(12,2),
    median_sale_price DECIMAL(12,2),
    price_velocity_percent DECIMAL(5,4), -- Rate of change
    avg_days_on_market INTEGER,

    -- Market intelligence
    market_temperature VARCHAR(20) CHECK (market_temperature IN ('hot', 'warm', 'cool', 'cold')),
    best_action VARCHAR(50) CHECK (best_action IN ('buy_now', 'wait', 'sell_now', 'list_now')),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Additional insights
    seasonal_factor DECIMAL(4,2) DEFAULT 1.0,
    economic_indicators JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Geographic performance analysis
CREATE TABLE geographic_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    performance_date DATE NOT NULL,

    -- Location details
    zip_code VARCHAR(10) NOT NULL,
    neighborhood VARCHAR(200),
    city VARCHAR(100) DEFAULT 'Rancho Cucamonga',
    location_point POINT, -- PostGIS for mapping

    -- Lead metrics
    total_leads INTEGER DEFAULT 0,
    qualified_leads INTEGER DEFAULT 0,
    avg_lead_score DECIMAL(5,2),

    -- Conversion metrics
    total_conversions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4) CHECK (conversion_rate >= 0 AND conversion_rate <= 1),
    avg_deal_value DECIMAL(12,2),
    total_revenue DECIMAL(12,2) DEFAULT 0,

    -- Market metrics
    median_property_price DECIMAL(12,2),
    price_appreciation_3m DECIMAL(5,4), -- 3-month price change
    inventory_level INTEGER DEFAULT 0,

    -- Performance indicators
    market_share_estimate DECIMAL(5,4) CHECK (market_share_estimate >= 0 AND market_share_estimate <= 1),
    competitive_pressure VARCHAR(20) CHECK (competitive_pressure IN ('low', 'medium', 'high', 'very_high')),
    growth_potential DECIMAL(5,2) CHECK (growth_potential >= 0 AND growth_potential <= 100),

    -- Business intelligence
    opportunity_score DECIMAL(5,2) CHECK (opportunity_score >= 0 AND opportunity_score <= 100),
    saturation_level DECIMAL(3,2) CHECK (saturation_level >= 0 AND saturation_level <= 1),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance goals and tracking
CREATE TABLE performance_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Goal definition
    goal_name VARCHAR(255) NOT NULL,
    goal_category VARCHAR(50) CHECK (goal_category IN ('revenue', 'conversion', 'quality', 'efficiency', 'market', 'geographic')),
    metric_name VARCHAR(100) NOT NULL,
    target_value DECIMAL(12,2) NOT NULL,
    current_value DECIMAL(12,2),

    -- Timeline
    goal_period VARCHAR(20) CHECK (goal_period IN ('weekly', 'monthly', 'quarterly', 'yearly')),
    start_date DATE NOT NULL,
    target_date DATE NOT NULL,

    -- Progress tracking
    completion_percentage DECIMAL(5,2) CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    on_track BOOLEAN DEFAULT TRUE,
    forecast_completion_date DATE,
    weekly_progress DECIMAL(5,2),

    -- Context
    assigned_to VARCHAR(255), -- agent_id or team name
    priority VARCHAR(20) CHECK (priority IN ('high', 'medium', 'low')),
    description TEXT,

    -- Performance metadata
    baseline_value DECIMAL(12,2),
    improvement_rate DECIMAL(5,4), -- Daily improvement rate
    variance_from_plan DECIMAL(5,4), -- How far off track

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- INDEXES FOR PERFORMANCE
-- ==========================================

-- Property matching indexes
CREATE INDEX idx_jorge_properties_status ON jorge_properties(status) WHERE status = 'active';
CREATE INDEX idx_jorge_properties_price ON jorge_properties(price);
CREATE INDEX idx_jorge_properties_neighborhood ON jorge_properties(neighborhood);
CREATE INDEX idx_jorge_properties_zip ON jorge_properties(zip_code);
CREATE INDEX idx_jorge_properties_bedrooms ON jorge_properties(bedrooms);
CREATE INDEX idx_jorge_properties_sqft ON jorge_properties(sqft);
CREATE INDEX idx_jorge_properties_updated ON jorge_properties(updated_at DESC);
CREATE INDEX idx_jorge_properties_coordinates ON jorge_properties USING GIST(coordinates);

CREATE INDEX idx_jorge_lead_preferences_lead ON jorge_lead_preferences(lead_id);
CREATE INDEX idx_jorge_lead_preferences_budget ON jorge_lead_preferences(budget_min, budget_max);

CREATE INDEX idx_jorge_property_matches_lead ON jorge_property_matches(lead_id);
CREATE INDEX idx_jorge_property_matches_property ON jorge_property_matches(property_id);
CREATE INDEX idx_jorge_property_matches_score ON jorge_property_matches(match_score DESC);
CREATE INDEX idx_jorge_property_matches_presented ON jorge_property_matches(presented_to_lead);
CREATE INDEX idx_jorge_property_matches_response ON jorge_property_matches(lead_response) WHERE lead_response IS NOT NULL;

-- Analytics indexes
CREATE INDEX idx_revenue_forecasts_date ON revenue_forecasts(forecast_date DESC);
CREATE INDEX idx_revenue_forecasts_horizon ON revenue_forecasts(horizon_days, forecast_date);

CREATE INDEX idx_funnel_snapshots_date_stage ON funnel_snapshots(snapshot_date DESC, stage);
CREATE INDEX idx_funnel_snapshots_segment ON funnel_snapshots(segment_type, segment_value);

CREATE INDEX idx_lead_scoring_history_lead ON lead_scoring_history(lead_id, scored_at DESC);
CREATE INDEX idx_lead_scoring_history_score ON lead_scoring_history(score DESC, scored_at DESC);
CREATE INDEX idx_lead_scoring_history_converted ON lead_scoring_history(actual_converted, scored_at DESC) WHERE actual_converted IS NOT NULL;
CREATE INDEX idx_lead_scoring_history_calibration ON lead_scoring_history(calibration_bucket);

CREATE INDEX idx_source_roi_date_source ON source_roi_tracking(tracking_date DESC, source_type);
CREATE INDEX idx_source_roi_performance ON source_roi_tracking(roi_percentage DESC, tracking_date DESC);

CREATE INDEX idx_market_timing_date_area ON market_timing_metrics(metric_date DESC, market_area);

CREATE INDEX idx_geographic_performance_date_zip ON geographic_performance(performance_date DESC, zip_code);
CREATE INDEX idx_geographic_performance_conversion ON geographic_performance(conversion_rate DESC, performance_date DESC);
CREATE INDEX idx_geographic_performance_location ON geographic_performance USING GIST(location_point);

CREATE INDEX idx_performance_goals_target ON performance_goals(target_date, on_track);
CREATE INDEX idx_performance_goals_category ON performance_goals(goal_category, completion_percentage);

-- ==========================================
-- FUNCTIONS AND TRIGGERS
-- ==========================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_jorge_properties_updated_at
    BEFORE UPDATE ON jorge_properties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jorge_lead_preferences_updated_at
    BEFORE UPDATE ON jorge_lead_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_revenue_forecasts_updated_at
    BEFORE UPDATE ON revenue_forecasts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lead_scoring_history_updated_at
    BEFORE UPDATE ON lead_scoring_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_performance_goals_updated_at
    BEFORE UPDATE ON performance_goals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ==========================================

-- Daily funnel performance summary
CREATE MATERIALIZED VIEW daily_funnel_summary AS
SELECT
    snapshot_date,
    stage,
    SUM(lead_count) as total_leads,
    AVG(conversion_rate) as avg_conversion_rate,
    AVG(avg_time_in_stage_days) as avg_time_in_stage
FROM funnel_snapshots
WHERE snapshot_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY snapshot_date, stage
ORDER BY snapshot_date DESC,
         CASE stage
            WHEN 'new_lead' THEN 1
            WHEN 'qualified' THEN 2
            WHEN 'appointment' THEN 3
            WHEN 'showing' THEN 4
            WHEN 'offer' THEN 5
            WHEN 'under_contract' THEN 6
            WHEN 'closed' THEN 7
         END;

-- Lead scoring accuracy summary
CREATE MATERIALIZED VIEW scoring_accuracy_summary AS
SELECT
    DATE(scored_at) as score_date,
    COUNT(*) as total_scored,
    AVG(score) as avg_score,
    COUNT(*) FILTER (WHERE actual_converted = true) as actual_conversions,
    COUNT(*) FILTER (WHERE actual_converted = false) as actual_non_conversions,
    -- Accuracy calculation for leads where we have outcomes
    CASE
        WHEN COUNT(*) FILTER (WHERE actual_converted IS NOT NULL) > 0 THEN
            AVG(CASE WHEN (predicted_conversion_probability > 0.5 AND actual_converted = true)
                      OR (predicted_conversion_probability <= 0.5 AND actual_converted = false)
                 THEN 1.0 ELSE 0.0 END) FILTER (WHERE actual_converted IS NOT NULL)
        ELSE NULL
    END as prediction_accuracy
FROM lead_scoring_history
WHERE scored_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(scored_at)
ORDER BY score_date DESC;

-- Geographic performance rollup
CREATE MATERIALIZED VIEW geographic_summary AS
SELECT
    zip_code,
    neighborhood,
    AVG(avg_lead_score) as avg_lead_score,
    SUM(total_leads) as total_leads,
    SUM(total_conversions) as total_conversions,
    AVG(conversion_rate) as avg_conversion_rate,
    SUM(total_revenue) as total_revenue,
    AVG(avg_deal_value) as avg_deal_value,
    AVG(median_property_price) as avg_property_price
FROM geographic_performance
WHERE performance_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY zip_code, neighborhood
HAVING SUM(total_leads) >= 5  -- Only include areas with significant activity
ORDER BY total_revenue DESC;

-- Indexes on materialized views
CREATE UNIQUE INDEX idx_daily_funnel_summary_date_stage ON daily_funnel_summary(snapshot_date, stage);
CREATE UNIQUE INDEX idx_scoring_accuracy_summary_date ON scoring_accuracy_summary(score_date);
CREATE UNIQUE INDEX idx_geographic_summary_zip_neighborhood ON geographic_summary(zip_code, neighborhood);

-- ==========================================
-- COMMENTS FOR DOCUMENTATION
-- ==========================================

COMMENT ON TABLE jorge_properties IS 'Property inventory cache from MLS with Rancho Cucamonga market focus';
COMMENT ON TABLE jorge_lead_preferences IS 'AI-extracted property preferences from lead conversations and scoring';
COMMENT ON TABLE jorge_property_matches IS 'Property-lead matches with hybrid neural+rules scoring and explanations';
COMMENT ON TABLE revenue_forecasts IS 'Revenue forecasting with confidence intervals and accuracy tracking';
COMMENT ON TABLE funnel_snapshots IS 'Conversion funnel performance snapshots for trend analysis';
COMMENT ON TABLE lead_scoring_history IS 'Lead scoring accuracy and calibration tracking';
COMMENT ON TABLE source_roi_tracking IS 'ROI analysis by lead source with attribution modeling';
COMMENT ON TABLE market_timing_metrics IS 'Market timing intelligence for Rancho Cucamonga real estate';
COMMENT ON TABLE geographic_performance IS 'Geographic performance analysis by ZIP code and neighborhood';
COMMENT ON TABLE performance_goals IS 'Goal tracking and progress monitoring for business metrics';

-- Insert initial test data for development
-- This would be removed in production migration