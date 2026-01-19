-- AI Revenue Optimization System Migration
-- Extends existing infrastructure for $5M+ ARR acceleration
-- Builds on existing billing (008) and competitive intelligence systems
-- ===================================================================

-- Pricing Strategies Configuration
CREATE TABLE pricing_strategies (
    id BIGSERIAL PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL,
    strategy_name VARCHAR(255) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL CHECK (strategy_type IN ('dynamic', 'fixed', 'competitor_based', 'value_based')),
    base_price DECIMAL(10, 2) NOT NULL,
    
    -- Dynamic pricing configuration
    market_factor_weight DECIMAL(3, 2) DEFAULT 0.3,
    demand_factor_weight DECIMAL(3, 2) DEFAULT 0.3,
    competition_factor_weight DECIMAL(3, 2) DEFAULT 0.4,
    
    -- Price elasticity settings
    min_price DECIMAL(10, 2) NOT NULL,
    max_price DECIMAL(10, 2) NOT NULL,
    elasticity_coefficient DECIMAL(5, 4) DEFAULT 0.5,
    
    -- Market responsiveness
    competitor_response_threshold DECIMAL(3, 2) DEFAULT 0.15,
    demand_surge_multiplier DECIMAL(3, 2) DEFAULT 1.25,
    
    -- A/B testing configuration
    is_test_variant BOOLEAN DEFAULT FALSE,
    test_group_percentage DECIMAL(3, 2) DEFAULT 0.0,
    test_start_date TIMESTAMP WITH TIME ZONE,
    test_end_date TIMESTAMP WITH TIME ZONE,
    
    -- Performance tracking
    revenue_impact_score DECIMAL(5, 2) DEFAULT 0.0,
    conversion_rate DECIMAL(5, 4) DEFAULT 0.0,
    customer_satisfaction_score DECIMAL(3, 2) DEFAULT 0.0,
    
    -- Metadata and audit
    configuration JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_pricing_location FOREIGN KEY (location_id)
        REFERENCES tenants(location_id) ON DELETE CASCADE,
    CONSTRAINT unique_strategy_per_location UNIQUE (location_id, strategy_name),
    CONSTRAINT valid_price_range CHECK (min_price <= base_price AND base_price <= max_price),
    CONSTRAINT valid_weights CHECK (market_factor_weight + demand_factor_weight + competition_factor_weight <= 1.0)
);

-- Lead ML Features Store (Real-time feature computation)
CREATE TABLE lead_ml_features (
    id BIGSERIAL PRIMARY KEY,
    lead_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,
    
    -- Behavioral features (100+ signals)
    conversation_quality_score DECIMAL(5, 4),
    engagement_velocity DECIMAL(5, 4),
    response_time_median INTEGER,
    question_completion_rate DECIMAL(5, 4),
    urgency_indicators_count INTEGER DEFAULT 0,
    
    -- Market timing features
    market_momentum_score DECIMAL(5, 4),
    seasonal_demand_factor DECIMAL(5, 4),
    inventory_pressure_score DECIMAL(5, 4),
    
    -- Competitive features
    competitor_mention_count INTEGER DEFAULT 0,
    price_sensitivity_score DECIMAL(5, 4),
    alternative_consideration_score DECIMAL(5, 4),
    
    -- Demographic and psychographic features
    budget_range_lower INTEGER,
    budget_range_upper INTEGER,
    timeline_urgency_days INTEGER,
    decision_maker_confidence DECIMAL(5, 4),
    
    -- Historical context features
    previous_inquiries_count INTEGER DEFAULT 0,
    referral_source_quality_score DECIMAL(5, 4),
    digital_engagement_score DECIMAL(5, 4),
    
    -- ML model predictions
    closing_probability DECIMAL(5, 4),
    churn_probability DECIMAL(5, 4),
    upsell_probability DECIMAL(5, 4),
    optimal_contact_window_hours INTEGER,
    predicted_ltv DECIMAL(10, 2),
    
    -- Feature engineering metadata
    feature_extraction_version VARCHAR(20) DEFAULT '2.0',
    feature_count INTEGER DEFAULT 0,
    feature_completeness_score DECIMAL(5, 4),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Performance tracking
    prediction_accuracy DECIMAL(5, 4),
    model_confidence DECIMAL(5, 4),
    
    CONSTRAINT fk_lead_features_location FOREIGN KEY (location_id)
        REFERENCES tenants(location_id) ON DELETE CASCADE,
    CONSTRAINT unique_lead_features UNIQUE (lead_id, location_id)
);

-- Revenue Optimization Campaigns
CREATE TABLE revenue_optimizations (
    id BIGSERIAL PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL,
    campaign_name VARCHAR(255) NOT NULL,
    optimization_type VARCHAR(50) NOT NULL CHECK (optimization_type IN ('upsell', 'retention', 'pricing', 'acquisition')),
    
    -- Campaign configuration
    target_audience JSONB DEFAULT '{}',  -- Audience criteria and filters
    trigger_conditions JSONB DEFAULT '{}',  -- Automated trigger conditions
    campaign_settings JSONB DEFAULT '{}',  -- Campaign-specific settings
    
    -- Automation rules
    is_automated BOOLEAN DEFAULT TRUE,
    trigger_frequency VARCHAR(20) DEFAULT 'real_time',  -- real_time, hourly, daily
    max_touches_per_lead INTEGER DEFAULT 3,
    cooldown_period_hours INTEGER DEFAULT 24,
    
    -- Performance targets
    target_revenue_increase_pct DECIMAL(5, 2),
    target_conversion_rate_pct DECIMAL(5, 4),
    target_customer_lifetime_value DECIMAL(10, 2),
    
    -- A/B testing
    test_variant_name VARCHAR(255),
    test_allocation_percentage DECIMAL(3, 2) DEFAULT 50.0,
    control_group_size INTEGER DEFAULT 100,
    
    -- Results tracking
    leads_processed INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12, 2) DEFAULT 0.0,
    conversion_rate_achieved DECIMAL(5, 4) DEFAULT 0.0,
    campaign_roi DECIMAL(7, 4) DEFAULT 0.0,
    
    -- Campaign lifecycle
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived')),
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    last_execution TIMESTAMP WITH TIME ZONE,
    next_execution TIMESTAMP WITH TIME ZONE,
    
    -- Audit trail
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_revenue_opt_location FOREIGN KEY (location_id)
        REFERENCES tenants(location_id) ON DELETE CASCADE
);

-- Competitive Intelligence Market Data
CREATE TABLE competitive_intelligence (
    id BIGSERIAL PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL CHECK (analysis_type IN ('pricing', 'features', 'sentiment', 'market_share')),
    
    -- Competitor information
    competitor_name VARCHAR(255) NOT NULL,
    competitor_category VARCHAR(100),  -- direct, indirect, substitute
    market_segment VARCHAR(100),
    
    -- Intelligence data
    pricing_data JSONB DEFAULT '{}',  -- Competitor pricing information
    feature_comparison JSONB DEFAULT '{}',  -- Feature set comparisons
    market_positioning JSONB DEFAULT '{}',  -- Positioning analysis
    sentiment_analysis JSONB DEFAULT '{}',  -- Social sentiment data
    
    -- Market impact metrics
    threat_level VARCHAR(20) DEFAULT 'medium' CHECK (threat_level IN ('low', 'medium', 'high', 'critical')),
    opportunity_score DECIMAL(5, 2) DEFAULT 0.0,
    market_share_estimate DECIMAL(5, 4),
    competitive_advantage_score DECIMAL(5, 2),
    
    -- Data sources and confidence
    data_sources TEXT[],  -- Array of data sources
    confidence_score DECIMAL(5, 4),
    data_freshness_hours INTEGER,
    
    -- Actionable insights
    recommended_responses JSONB DEFAULT '{}',
    strategic_implications JSONB DEFAULT '{}',
    risk_assessment JSONB DEFAULT '{}',
    
    -- Automation triggers
    alert_threshold_met BOOLEAN DEFAULT FALSE,
    auto_response_triggered BOOLEAN DEFAULT FALSE,
    escalation_required BOOLEAN DEFAULT FALSE,
    
    -- Audit and tracking
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT fk_competitive_intel_location FOREIGN KEY (location_id)
        REFERENCES tenants(location_id) ON DELETE CASCADE
);

-- Customer Lifetime Value Analytics
CREATE TABLE customer_lifetime_analytics (
    id BIGSERIAL PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL,
    customer_segment VARCHAR(100) NOT NULL,
    
    -- CLV Calculations
    historical_clv DECIMAL(12, 2),
    predicted_clv DECIMAL(12, 2),
    potential_clv DECIMAL(12, 2),  -- With optimization
    clv_confidence_interval_lower DECIMAL(12, 2),
    clv_confidence_interval_upper DECIMAL(12, 2),
    
    -- Contributing factors
    average_transaction_value DECIMAL(10, 2),
    transaction_frequency DECIMAL(5, 2),  -- Transactions per period
    customer_lifespan_months DECIMAL(5, 1),
    churn_probability DECIMAL(5, 4),
    
    -- Optimization opportunities
    upsell_opportunity_value DECIMAL(10, 2),
    cross_sell_opportunity_value DECIMAL(10, 2),
    retention_value_at_risk DECIMAL(10, 2),
    acquisition_cost DECIMAL(8, 2),
    
    -- Behavioral insights
    engagement_score DECIMAL(5, 4),
    satisfaction_score DECIMAL(5, 4),
    referral_likelihood DECIMAL(5, 4),
    price_sensitivity DECIMAL(5, 4),
    
    -- Performance tracking
    actual_revenue_mtd DECIMAL(10, 2) DEFAULT 0.0,
    predicted_revenue_mtd DECIMAL(10, 2) DEFAULT 0.0,
    variance_percentage DECIMAL(5, 2) DEFAULT 0.0,
    
    -- Time-based analysis
    calculation_period_start DATE NOT NULL,
    calculation_period_end DATE NOT NULL,
    next_review_date DATE,
    
    -- Model metadata
    model_version VARCHAR(20) DEFAULT '1.0',
    calculation_method VARCHAR(50) DEFAULT 'predictive_ml',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_clv_analytics_location FOREIGN KEY (location_id)
        REFERENCES tenants(location_id) ON DELETE CASCADE,
    CONSTRAINT unique_segment_period UNIQUE (location_id, customer_segment, calculation_period_start)
);

-- ML Model Performance Tracking
CREATE TABLE ml_model_performance (
    id BIGSERIAL PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50) NOT NULL CHECK (model_type IN ('lead_scoring', 'pricing', 'churn', 'upsell', 'clv')),
    
    -- Performance metrics
    accuracy DECIMAL(5, 4),
    precision_score DECIMAL(5, 4),
    recall_score DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    auc_score DECIMAL(5, 4),
    
    -- Business impact metrics
    revenue_impact DECIMAL(12, 2),
    conversion_rate_improvement DECIMAL(5, 4),
    cost_reduction DECIMAL(10, 2),
    customer_satisfaction_impact DECIMAL(5, 4),
    
    -- Model drift detection
    feature_drift_score DECIMAL(5, 4),
    prediction_drift_score DECIMAL(5, 4),
    performance_degradation_pct DECIMAL(5, 2),
    
    -- Training and deployment info
    training_data_size INTEGER,
    training_date TIMESTAMP WITH TIME ZONE,
    deployment_date TIMESTAMP WITH TIME ZONE,
    last_retrain_date TIMESTAMP WITH TIME ZONE,
    next_retrain_scheduled TIMESTAMP WITH TIME ZONE,
    
    -- Model configuration
    hyperparameters JSONB DEFAULT '{}',
    feature_importance JSONB DEFAULT '{}',
    training_metrics JSONB DEFAULT '{}',
    
    -- A/B testing results
    ab_test_id VARCHAR(255),
    test_group VARCHAR(50),
    control_group_performance JSONB DEFAULT '{}',
    variant_group_performance JSONB DEFAULT '{}',
    statistical_significance DECIMAL(5, 4),
    
    -- Status and lifecycle
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('training', 'testing', 'active', 'deprecated', 'retired')),
    is_production BOOLEAN DEFAULT FALSE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_model_perf_location FOREIGN KEY (location_id)
        REFERENCES tenants(location_id) ON DELETE CASCADE,
    CONSTRAINT unique_model_version UNIQUE (location_id, model_name, model_version)
);

-- Revenue Attribution and Analytics
CREATE TABLE revenue_attribution_events (
    id BIGSERIAL PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL,
    event_id VARCHAR(255) NOT NULL UNIQUE,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('lead_generated', 'lead_qualified', 'proposal_sent', 'deal_closed', 'upsell_completed', 'churn_prevented')),
    lead_id VARCHAR(255),
    customer_id VARCHAR(255),
    
    -- Revenue attribution
    revenue_amount DECIMAL(12, 2),
    attributed_channel VARCHAR(100),
    attribution_model VARCHAR(50) DEFAULT 'multi_touch',
    attribution_confidence DECIMAL(5, 4),
    
    -- AI/ML contribution
    ai_assisted BOOLEAN DEFAULT FALSE,
    ai_recommendation_followed BOOLEAN DEFAULT FALSE,
    pricing_optimization_applied BOOLEAN DEFAULT FALSE,
    campaign_id BIGINT,  -- Reference to revenue_optimizations
    
    -- Performance context
    baseline_expected_revenue DECIMAL(12, 2),
    optimized_revenue DECIMAL(12, 2),
    revenue_lift_percentage DECIMAL(5, 2),
    
    -- Time-to-value metrics
    lead_to_close_days INTEGER,
    first_touch_to_close_days INTEGER,
    optimization_to_close_days INTEGER,
    
    -- Competitive context
    competitive_pressure_level VARCHAR(20),
    competitor_mentions_count INTEGER DEFAULT 0,
    competitive_response_applied BOOLEAN DEFAULT FALSE,
    
    -- Event metadata
    event_metadata JSONB DEFAULT '{}',
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_revenue_attr_location FOREIGN KEY (location_id)
        REFERENCES tenants(location_id) ON DELETE CASCADE,
    CONSTRAINT fk_revenue_attr_campaign FOREIGN KEY (campaign_id)
        REFERENCES revenue_optimizations(id) ON DELETE SET NULL
);

-- Indexes for Performance Optimization
CREATE INDEX idx_pricing_strategies_location_active ON pricing_strategies(location_id, is_active) WHERE is_active = true;
CREATE INDEX idx_pricing_strategies_test_dates ON pricing_strategies(test_start_date, test_end_date) WHERE is_test_variant = true;

CREATE INDEX idx_lead_ml_features_lead_location ON lead_ml_features(lead_id, location_id);
CREATE INDEX idx_lead_ml_features_closing_prob ON lead_ml_features(closing_probability DESC);
CREATE INDEX idx_lead_ml_features_churn_risk ON lead_ml_features(churn_probability DESC);
CREATE INDEX idx_lead_ml_features_updated ON lead_ml_features(last_updated);

CREATE INDEX idx_revenue_opt_location_status ON revenue_optimizations(location_id, status);
CREATE INDEX idx_revenue_opt_execution_time ON revenue_optimizations(next_execution) WHERE status = 'active';
CREATE INDEX idx_revenue_opt_type_performance ON revenue_optimizations(optimization_type, campaign_roi DESC);

CREATE INDEX idx_competitive_intel_location_threat ON competitive_intelligence(location_id, threat_level);
CREATE INDEX idx_competitive_intel_freshness ON competitive_intelligence(collected_at DESC);
CREATE INDEX idx_competitive_intel_alerts ON competitive_intelligence(alert_threshold_met) WHERE alert_threshold_met = true;

CREATE INDEX idx_clv_analytics_location_segment ON customer_lifetime_analytics(location_id, customer_segment);
CREATE INDEX idx_clv_analytics_review_date ON customer_lifetime_analytics(next_review_date);

CREATE INDEX idx_ml_model_perf_location_type ON ml_model_performance(location_id, model_type);
CREATE INDEX idx_ml_model_perf_production ON ml_model_performance(is_production, status) WHERE is_production = true;
CREATE INDEX idx_ml_model_perf_retrain ON ml_model_performance(next_retrain_scheduled);

CREATE INDEX idx_revenue_attr_location_type ON revenue_attribution_events(location_id, event_type);
CREATE INDEX idx_revenue_attr_timestamp ON revenue_attribution_events(event_timestamp DESC);
CREATE INDEX idx_revenue_attr_ai_assisted ON revenue_attribution_events(ai_assisted) WHERE ai_assisted = true;
CREATE INDEX idx_revenue_attr_revenue_amount ON revenue_attribution_events(revenue_amount DESC);

-- Create views for common analytics queries
CREATE VIEW revenue_optimization_dashboard AS
SELECT 
    ro.location_id,
    ro.optimization_type,
    COUNT(*) as active_campaigns,
    SUM(ro.revenue_generated) as total_revenue_generated,
    AVG(ro.campaign_roi) as average_roi,
    SUM(ro.leads_processed) as total_leads_processed
FROM revenue_optimizations ro
WHERE ro.status = 'active'
GROUP BY ro.location_id, ro.optimization_type;

CREATE VIEW ml_model_health_dashboard AS
SELECT 
    mp.location_id,
    mp.model_type,
    mp.model_name,
    mp.model_version,
    mp.accuracy,
    mp.revenue_impact,
    mp.performance_degradation_pct,
    mp.last_retrain_date,
    mp.next_retrain_scheduled,
    CASE 
        WHEN mp.performance_degradation_pct > 10 THEN 'needs_retrain'
        WHEN mp.performance_degradation_pct > 5 THEN 'monitor'
        ELSE 'healthy'
    END as model_health_status
FROM ml_model_performance mp
WHERE mp.is_production = true;

CREATE VIEW competitive_threat_monitor AS
SELECT 
    ci.location_id,
    ci.competitor_name,
    ci.threat_level,
    ci.opportunity_score,
    ci.market_share_estimate,
    ci.collected_at,
    ci.data_freshness_hours,
    CASE 
        WHEN ci.data_freshness_hours > 24 THEN 'stale'
        WHEN ci.threat_level = 'critical' AND ci.alert_threshold_met THEN 'urgent'
        ELSE 'current'
    END as intelligence_status
FROM competitive_intelligence ci
ORDER BY ci.collected_at DESC;

-- Create triggers for automated timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_pricing_strategies_updated_at BEFORE UPDATE ON pricing_strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_revenue_optimizations_updated_at BEFORE UPDATE ON revenue_optimizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ml_model_performance_updated_at BEFORE UPDATE ON ml_model_performance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for automatic campaign execution scheduling
CREATE OR REPLACE FUNCTION schedule_next_campaign_execution()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.trigger_frequency = 'real_time' THEN
        NEW.next_execution = NOW() + INTERVAL '1 minute';
    ELSIF NEW.trigger_frequency = 'hourly' THEN
        NEW.next_execution = NOW() + INTERVAL '1 hour';
    ELSIF NEW.trigger_frequency = 'daily' THEN
        NEW.next_execution = NOW() + INTERVAL '1 day';
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER schedule_campaign_execution_trigger BEFORE INSERT OR UPDATE ON revenue_optimizations
    FOR EACH ROW WHEN (NEW.status = 'active')
    EXECUTE FUNCTION schedule_next_campaign_execution();

-- Comments for documentation
COMMENT ON TABLE pricing_strategies IS 'AI-powered dynamic pricing strategies with A/B testing support';
COMMENT ON TABLE lead_ml_features IS 'Real-time feature store for ML models with 100+ behavioral signals';
COMMENT ON TABLE revenue_optimizations IS 'Automated revenue optimization campaigns with trigger-based execution';
COMMENT ON TABLE competitive_intelligence IS 'Real-time competitive intelligence data with threat assessment';
COMMENT ON TABLE customer_lifetime_analytics IS 'CLV optimization analytics with predictive modeling';
COMMENT ON TABLE ml_model_performance IS 'ML model performance tracking with drift detection';
COMMENT ON TABLE revenue_attribution_events IS 'Revenue attribution events for AI-powered optimization tracking';