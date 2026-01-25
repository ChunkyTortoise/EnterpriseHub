-- Lead Intelligence Tables (Track A) - Phase 1 Foundation
-- Creates database schema for AI Lead Generation and Enhanced Lead Scoring
-- Follows multi-tenant isolation with (location_id, client_id) compound keys

-- Lead Source Quality Metrics
-- Tracks performance metrics for different lead sources
CREATE TABLE lead_source_quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id VARCHAR(50) NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- organic_search, paid_search, referral, etc.

    -- Performance Metrics
    total_leads INTEGER DEFAULT 0,
    qualified_leads INTEGER DEFAULT 0,
    converted_leads INTEGER DEFAULT 0,
    quality_score DECIMAL(5,2) DEFAULT 50.00,
    conversion_rate DECIMAL(5,2) DEFAULT 0.00,
    qualification_rate DECIMAL(5,2) DEFAULT 0.00,

    -- Financial Metrics
    total_cost DECIMAL(10,2) DEFAULT 0.00,
    cost_per_lead DECIMAL(8,2),
    cost_per_conversion DECIMAL(10,2),
    roi DECIMAL(8,2),
    lifetime_value DECIMAL(12,2),

    -- Timing Metrics
    average_time_to_convert INTEGER, -- days
    lead_velocity DECIMAL(8,2) DEFAULT 0.00, -- leads per day

    -- Trend Analysis
    performance_trend VARCHAR(20) DEFAULT 'stable', -- improving, declining, stable
    trend_confidence DECIMAL(3,2) DEFAULT 0.00,

    -- Metadata
    analysis_period_days INTEGER DEFAULT 30,
    last_analysis TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Multi-tenant isolation
    CONSTRAINT pk_source_quality PRIMARY KEY (location_id, source_id),
    INDEX idx_source_quality_type (location_id, source_type),
    INDEX idx_source_quality_performance (location_id, quality_score DESC),
    INDEX idx_source_quality_updated (location_id, updated_at DESC)
);

-- Enhanced Lead Scores
-- Stores comprehensive lead scoring results beyond basic FRS/PCS
CREATE TABLE enhanced_lead_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Enhanced Scoring Components (0-100 scale)
    overall_score DECIMAL(5,2) NOT NULL,
    source_quality_score DECIMAL(5,2) NOT NULL,
    behavioral_engagement_score DECIMAL(5,2) NOT NULL,
    intent_clarity_score DECIMAL(5,2) NOT NULL,
    conversion_readiness_score DECIMAL(5,2) NOT NULL,

    -- Source Analysis
    source_type VARCHAR(50),
    source_attribution_confidence DECIMAL(3,2) DEFAULT 1.00,
    source_quality_factors TEXT[], -- Array of quality factors

    -- Behavioral Analysis
    engagement_signals INTEGER DEFAULT 0,
    response_velocity_ms DECIMAL(10,2),
    message_complexity_score DECIMAL(5,2) DEFAULT 0.00,
    question_depth_score DECIMAL(5,2) DEFAULT 0.00,
    urgency_indicators TEXT[], -- Array of detected urgency signals
    authority_signals TEXT[], -- Array of detected authority signals

    -- Integration with Base System
    base_frs_score DECIMAL(5,2),
    base_pcs_score DECIMAL(5,2),
    base_intent_classification VARCHAR(20), -- Hot, Warm, Lukewarm, Cold

    -- ML Integration
    closing_probability DECIMAL(5,4), -- 0.0000 to 1.0000
    ml_confidence DECIMAL(5,4),
    risk_factors TEXT[], -- Array of ML-identified risk factors
    positive_signals TEXT[], -- Array of ML-identified positive signals

    -- Processing Metadata
    scoring_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    processing_time_ms DECIMAL(8,2) NOT NULL,
    confidence_level DECIMAL(5,4) NOT NULL,
    scoring_version VARCHAR(10) DEFAULT 'v1.0',

    -- Action Recommendations
    next_action_recommendations TEXT[], -- Array of recommended actions
    priority_score DECIMAL(5,2) DEFAULT 0.00,

    -- Multi-tenant isolation and performance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT pk_enhanced_scores PRIMARY KEY (location_id, lead_id, scoring_timestamp),
    INDEX idx_enhanced_scores_overall (location_id, overall_score DESC),
    INDEX idx_enhanced_scores_recent (location_id, lead_id, scoring_timestamp DESC),
    INDEX idx_enhanced_scores_priority (location_id, priority_score DESC),
    INDEX idx_enhanced_scores_conversion (location_id, conversion_readiness_score DESC)
);

-- Lead Attribution Touchpoints
-- Tracks multi-touch attribution data for lead journey analysis
CREATE TABLE lead_attribution_touchpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id VARCHAR(50) NOT NULL,
    lead_id VARCHAR(100) NOT NULL,

    -- Touchpoint Details
    touchpoint_type VARCHAR(50) NOT NULL, -- first_touch, middle_touch, last_touch
    channel VARCHAR(50) NOT NULL, -- google_ads, facebook_ads, organic, etc.
    campaign_id VARCHAR(100),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    utm_content VARCHAR(100),
    utm_term VARCHAR(100),

    -- Attribution Values
    attribution_value DECIMAL(5,2) NOT NULL, -- percentage of attribution (0-100)
    attribution_model VARCHAR(30) NOT NULL, -- first_touch, last_touch, linear, time_decay

    -- Context
    page_url TEXT,
    referrer_url TEXT,
    user_agent TEXT,
    ip_address VARCHAR(45), -- IPv6 compatible

    -- Timing
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    session_duration INTEGER, -- seconds
    pages_viewed INTEGER DEFAULT 1,

    -- Conversion Context
    conversion_value DECIMAL(10,2), -- if this touchpoint led to conversion
    conversion_type VARCHAR(50), -- lead, qualified, converted

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT pk_attribution_touchpoints PRIMARY KEY (location_id, id),
    INDEX idx_attribution_lead_journey (location_id, lead_id, occurred_at),
    INDEX idx_attribution_channel (location_id, channel, occurred_at DESC),
    INDEX idx_attribution_campaign (location_id, campaign_id, occurred_at DESC),
    INDEX idx_attribution_conversion (location_id, conversion_value DESC, occurred_at DESC)
);

-- Lead Generation Recommendations
-- Stores AI-generated optimization recommendations for lead generation
CREATE TABLE lead_generation_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recommendation_id VARCHAR(100) UNIQUE NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Recommendation Classification
    channel VARCHAR(50) NOT NULL, -- google_ads, facebook_ads, etc.
    category VARCHAR(50) NOT NULL, -- timing, communication, automation, personalization
    priority VARCHAR(20) NOT NULL, -- low, medium, high, urgent, critical

    -- Recommendation Content
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    expected_impact TEXT,
    implementation_difficulty VARCHAR(20) DEFAULT 'medium', -- low, medium, high
    estimated_timeframe VARCHAR(50) DEFAULT 'immediate', -- immediate, days, weeks, months

    -- Financial Projections
    projected_lead_increase DECIMAL(5,2), -- percentage increase
    projected_cost_reduction DECIMAL(5,2), -- percentage reduction
    projected_roi_improvement DECIMAL(5,2), -- percentage improvement
    investment_required DECIMAL(10,2), -- dollars required

    -- Implementation Details
    action_items TEXT[], -- Array of action items
    success_metrics TEXT[], -- Array of success metrics
    risk_factors TEXT[], -- Array of risk factors
    dependencies TEXT[], -- Array of dependencies

    -- Validation
    confidence_score DECIMAL(5,4) NOT NULL,
    data_quality VARCHAR(20) DEFAULT 'good', -- excellent, good, fair, poor
    validation_status VARCHAR(20) DEFAULT 'pending', -- validated, pending, rejected

    -- Lifecycle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    implemented_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,

    -- Performance Tracking (if implemented)
    actual_lead_increase DECIMAL(5,2),
    actual_cost_reduction DECIMAL(5,2),
    actual_roi_improvement DECIMAL(5,2),
    implementation_notes TEXT,

    CONSTRAINT pk_lead_gen_recommendations PRIMARY KEY (location_id, recommendation_id),
    INDEX idx_recommendations_priority (location_id, priority, created_at DESC),
    INDEX idx_recommendations_channel (location_id, channel, created_at DESC),
    INDEX idx_recommendations_confidence (location_id, confidence_score DESC),
    INDEX idx_recommendations_status (location_id, validation_status, created_at DESC)
);

-- Channel Performance Analytics
-- Aggregated performance data for lead generation channels
CREATE TABLE channel_performance_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,

    -- Time Period
    analysis_date DATE NOT NULL,
    analysis_period_days INTEGER NOT NULL,

    -- Volume Metrics
    total_leads INTEGER DEFAULT 0,
    qualified_leads INTEGER DEFAULT 0,
    converted_leads INTEGER DEFAULT 0,

    -- Quality Metrics
    average_lead_score DECIMAL(5,2) DEFAULT 0.00,
    conversion_rate DECIMAL(5,2) DEFAULT 0.00,
    qualification_rate DECIMAL(5,2) DEFAULT 0.00,

    -- Financial Metrics
    total_spend DECIMAL(12,2) DEFAULT 0.00,
    cost_per_lead DECIMAL(8,2),
    cost_per_conversion DECIMAL(10,2),
    total_revenue DECIMAL(12,2) DEFAULT 0.00,
    roi DECIMAL(8,2),

    -- Timing Metrics
    average_time_to_convert DECIMAL(6,2), -- days
    lead_velocity DECIMAL(8,2) DEFAULT 0.00, -- leads per day

    -- Trend Analysis
    performance_trend VARCHAR(20) DEFAULT 'stable',
    trend_confidence DECIMAL(3,2) DEFAULT 0.00,
    period_over_period_change DECIMAL(6,2) DEFAULT 0.00, -- percentage change

    -- Optimization Data
    optimization_opportunities TEXT[], -- Array of opportunities
    competitive_position VARCHAR(20) DEFAULT 'unknown', -- leading, competitive, lagging
    market_share_estimate DECIMAL(5,2), -- percentage

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT pk_channel_analytics PRIMARY KEY (location_id, channel, analysis_date),
    INDEX idx_channel_analytics_performance (location_id, roi DESC, analysis_date DESC),
    INDEX idx_channel_analytics_recent (location_id, channel, analysis_date DESC),
    INDEX idx_channel_analytics_trend (location_id, performance_trend, analysis_date DESC)
);

-- Lead Intelligence Insights Cache
-- Caches computed lead intelligence insights for performance
CREATE TABLE lead_intelligence_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id VARCHAR(50) NOT NULL,
    insight_type VARCHAR(50) NOT NULL, -- channel_performance, source_analysis, forecast

    -- Insight Content
    insight_data JSONB NOT NULL, -- Structured insight data
    summary_text TEXT,
    confidence_level DECIMAL(5,4) NOT NULL,

    -- Metadata
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    version VARCHAR(10) DEFAULT 'v1.0',

    -- Performance tracking
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,

    CONSTRAINT pk_intelligence_insights PRIMARY KEY (location_id, insight_type, generated_at),
    INDEX idx_insights_current (location_id, insight_type, expires_at DESC),
    INDEX idx_insights_confidence (location_id, confidence_level DESC),
    INDEX idx_insights_access (location_id, access_count DESC)
);

-- Comments for documentation
COMMENT ON TABLE lead_source_quality_metrics IS 'Lead source performance tracking with quality scoring and ROI analysis';
COMMENT ON TABLE enhanced_lead_scores IS 'Comprehensive lead scoring beyond basic FRS/PCS with ML integration';
COMMENT ON TABLE lead_attribution_touchpoints IS 'Multi-touch attribution tracking for lead journey analysis';
COMMENT ON TABLE lead_generation_recommendations IS 'AI-generated optimization recommendations for lead generation channels';
COMMENT ON TABLE channel_performance_analytics IS 'Aggregated channel performance analytics with trend analysis';
COMMENT ON TABLE lead_intelligence_insights IS 'Cached lead intelligence insights and analytics for performance optimization';