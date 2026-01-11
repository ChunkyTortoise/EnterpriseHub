-- Phase 3 Business Impact Tracking Database Schema
-- Created: January 11, 2026
-- Purpose: Track ROI and business metrics for Phase 3 features

-- =============================================================================
-- CORE TRACKING TABLES
-- =============================================================================

-- Daily business metrics snapshot
CREATE TABLE IF NOT EXISTS business_metrics_daily (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    tenant_id VARCHAR(50),

    -- Overall Platform Metrics
    total_leads_processed INTEGER DEFAULT 0,
    total_revenue_impact DECIMAL(12,2) DEFAULT 0,
    total_operating_cost DECIMAL(10,2) DEFAULT 0,
    net_roi_percentage DECIMAL(8,4) DEFAULT 0,

    -- Feature Adoption Rates
    real_time_intelligence_adoption_rate DECIMAL(5,4) DEFAULT 0,
    property_vision_adoption_rate DECIMAL(5,4) DEFAULT 0,
    churn_prevention_adoption_rate DECIMAL(5,4) DEFAULT 0,
    ai_coaching_adoption_rate DECIMAL(5,4) DEFAULT 0,

    -- Performance Metrics
    websocket_avg_latency_ms DECIMAL(8,3) DEFAULT 0,
    ml_inference_avg_latency_ms DECIMAL(8,3) DEFAULT 0,
    vision_analysis_avg_time_ms DECIMAL(10,3) DEFAULT 0,
    coaching_analysis_avg_time_ms DECIMAL(8,3) DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Real-Time Lead Intelligence Metrics
CREATE TABLE IF NOT EXISTS lead_intelligence_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    tenant_id VARCHAR(50),

    -- Core Metrics
    leads_processed INTEGER DEFAULT 0,
    avg_response_time_minutes DECIMAL(8,2) DEFAULT 0,
    conversion_rate_improvement DECIMAL(5,4) DEFAULT 0,
    agent_productivity_improvement DECIMAL(5,4) DEFAULT 0,

    -- Financial Impact
    estimated_revenue_impact DECIMAL(10,2) DEFAULT 0,
    leads_converted INTEGER DEFAULT 0,
    avg_deal_value DECIMAL(10,2) DEFAULT 0,

    -- Performance
    websocket_events_processed INTEGER DEFAULT 0,
    avg_scoring_latency_ms DECIMAL(8,3) DEFAULT 0,
    error_rate DECIMAL(5,4) DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Multimodal Property Intelligence Metrics
CREATE TABLE IF NOT EXISTS property_intelligence_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    tenant_id VARCHAR(50),

    -- Core Metrics
    properties_analyzed INTEGER DEFAULT 0,
    luxury_properties_identified INTEGER DEFAULT 0,
    match_satisfaction_score DECIMAL(5,4) DEFAULT 0,
    qualified_matches_increase DECIMAL(5,4) DEFAULT 0,

    -- Financial Impact
    estimated_revenue_impact DECIMAL(10,2) DEFAULT 0,
    higher_value_matches INTEGER DEFAULT 0,
    avg_property_value_increase DECIMAL(10,2) DEFAULT 0,

    -- Performance
    vision_analyses_completed INTEGER DEFAULT 0,
    avg_analysis_time_ms DECIMAL(10,3) DEFAULT 0,
    accuracy_rate DECIMAL(5,4) DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Churn Prevention Metrics
CREATE TABLE IF NOT EXISTS churn_prevention_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    tenant_id VARCHAR(50),

    -- Core Metrics
    leads_at_risk_identified INTEGER DEFAULT 0,
    interventions_triggered INTEGER DEFAULT 0,
    successful_interventions INTEGER DEFAULT 0,
    churn_rate_before DECIMAL(5,4) DEFAULT 0,
    churn_rate_after DECIMAL(5,4) DEFAULT 0,

    -- Financial Impact
    estimated_revenue_saved DECIMAL(10,2) DEFAULT 0,
    leads_retained INTEGER DEFAULT 0,
    avg_lead_lifetime_value DECIMAL(8,2) DEFAULT 0,

    -- Performance
    avg_intervention_latency_seconds INTEGER DEFAULT 0,
    prediction_accuracy DECIMAL(5,4) DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Coaching Metrics
CREATE TABLE IF NOT EXISTS ai_coaching_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    tenant_id VARCHAR(50),
    agent_id VARCHAR(50),

    -- Core Metrics
    coaching_sessions INTEGER DEFAULT 0,
    performance_improvement DECIMAL(5,4) DEFAULT 0,
    training_time_reduction DECIMAL(5,4) DEFAULT 0,
    conversation_quality_score DECIMAL(5,4) DEFAULT 0,

    -- Financial Impact
    estimated_revenue_impact DECIMAL(10,2) DEFAULT 0,
    productivity_hours_saved DECIMAL(8,2) DEFAULT 0,

    -- Performance
    avg_coaching_latency_ms DECIMAL(8,3) DEFAULT 0,
    coaching_accuracy DECIMAL(5,4) DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- COST TRACKING TABLES
-- =============================================================================

-- Operating Costs by Category
CREATE TABLE IF NOT EXISTS operating_costs_daily (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    cost_category VARCHAR(100) NOT NULL, -- 'anthropic_api', 'railway', 'vercel', etc.

    -- Cost Details
    amount DECIMAL(10,2) NOT NULL,
    usage_units INTEGER DEFAULT 0, -- API calls, compute hours, etc.
    cost_per_unit DECIMAL(10,6) DEFAULT 0,

    -- Additional Context
    description TEXT,
    tenant_id VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, cost_category, tenant_id)
);

-- =============================================================================
-- ROI CALCULATION TABLES
-- =============================================================================

-- Weekly ROI Summary
CREATE TABLE IF NOT EXISTS roi_weekly_summary (
    id SERIAL PRIMARY KEY,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    tenant_id VARCHAR(50),

    -- Revenue Impact by Feature
    lead_intelligence_revenue DECIMAL(10,2) DEFAULT 0,
    property_intelligence_revenue DECIMAL(10,2) DEFAULT 0,
    churn_prevention_revenue DECIMAL(10,2) DEFAULT 0,
    ai_coaching_revenue DECIMAL(10,2) DEFAULT 0,
    total_revenue_impact DECIMAL(12,2) DEFAULT 0,

    -- Cost Breakdown
    infrastructure_costs DECIMAL(8,2) DEFAULT 0,
    api_costs DECIMAL(8,2) DEFAULT 0,
    operational_costs DECIMAL(8,2) DEFAULT 0,
    total_costs DECIMAL(10,2) DEFAULT 0,

    -- ROI Calculations
    net_revenue DECIMAL(12,2) DEFAULT 0,
    roi_percentage DECIMAL(8,4) DEFAULT 0,
    payback_period_days INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(week_start_date, tenant_id)
);

-- =============================================================================
-- FEATURE ROLLOUT TRACKING
-- =============================================================================

-- Track feature rollout percentage and impact
CREATE TABLE IF NOT EXISTS feature_rollout_tracking (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    rollout_percentage INTEGER NOT NULL, -- 10, 25, 50, 100

    -- Metrics at this rollout level
    active_users INTEGER DEFAULT 0,
    feature_usage_events INTEGER DEFAULT 0,
    error_rate DECIMAL(5,4) DEFAULT 0,
    performance_score DECIMAL(5,4) DEFAULT 0,
    user_satisfaction_score DECIMAL(5,4) DEFAULT 0,

    -- Business Impact at this level
    revenue_impact DECIMAL(10,2) DEFAULT 0,
    cost_impact DECIMAL(8,2) DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, feature_name)
);

-- =============================================================================
-- ALERT AND MONITORING TABLES
-- =============================================================================

-- Business Impact Alerts
CREATE TABLE IF NOT EXISTS business_impact_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL, -- 'performance_drop', 'roi_below_target', etc.
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    feature_name VARCHAR(100),

    -- Alert Details
    message TEXT NOT NULL,
    current_value DECIMAL(10,4),
    threshold_value DECIMAL(10,4),

    -- Status
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'acknowledged', 'resolved'
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Daily metrics indexes
CREATE INDEX IF NOT EXISTS idx_business_metrics_daily_date ON business_metrics_daily(date);
CREATE INDEX IF NOT EXISTS idx_business_metrics_daily_tenant ON business_metrics_daily(tenant_id);

-- Feature-specific indexes
CREATE INDEX IF NOT EXISTS idx_lead_intelligence_date ON lead_intelligence_metrics(date);
CREATE INDEX IF NOT EXISTS idx_property_intelligence_date ON property_intelligence_metrics(date);
CREATE INDEX IF NOT EXISTS idx_churn_prevention_date ON churn_prevention_metrics(date);
CREATE INDEX IF NOT EXISTS idx_ai_coaching_date ON ai_coaching_metrics(date);
CREATE INDEX IF NOT EXISTS idx_ai_coaching_agent ON ai_coaching_metrics(agent_id);

-- Cost tracking indexes
CREATE INDEX IF NOT EXISTS idx_operating_costs_date ON operating_costs_daily(date);
CREATE INDEX IF NOT EXISTS idx_operating_costs_category ON operating_costs_daily(cost_category);

-- ROI tracking indexes
CREATE INDEX IF NOT EXISTS idx_roi_weekly_start_date ON roi_weekly_summary(week_start_date);
CREATE INDEX IF NOT EXISTS idx_roi_weekly_tenant ON roi_weekly_summary(tenant_id);

-- Rollout tracking indexes
CREATE INDEX IF NOT EXISTS idx_feature_rollout_date ON feature_rollout_tracking(date);
CREATE INDEX IF NOT EXISTS idx_feature_rollout_feature ON feature_rollout_tracking(feature_name);

-- Alert indexes
CREATE INDEX IF NOT EXISTS idx_alerts_status ON business_impact_alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON business_impact_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_feature ON business_impact_alerts(feature_name);

-- =============================================================================
-- INITIAL DATA SETUP
-- =============================================================================

-- Insert default cost categories
INSERT INTO operating_costs_daily (date, cost_category, amount, description)
VALUES
    (CURRENT_DATE, 'anthropic_api', 0.00, 'Daily Anthropic API usage costs'),
    (CURRENT_DATE, 'railway', 0.00, 'Railway hosting costs'),
    (CURRENT_DATE, 'vercel', 0.00, 'Vercel hosting costs'),
    (CURRENT_DATE, 'database', 0.00, 'PostgreSQL and Redis costs'),
    (CURRENT_DATE, 'monitoring', 0.00, 'Monitoring and alerting costs')
ON CONFLICT (date, cost_category, tenant_id) DO NOTHING;

-- =============================================================================
-- VIEWS FOR EASY REPORTING
-- =============================================================================

-- Daily ROI Summary View
CREATE OR REPLACE VIEW daily_roi_summary AS
SELECT
    bmd.date,
    bmd.tenant_id,
    bmd.total_revenue_impact,
    COALESCE(SUM(ocd.amount), 0) as total_daily_costs,
    bmd.total_revenue_impact - COALESCE(SUM(ocd.amount), 0) as net_daily_revenue,
    CASE
        WHEN COALESCE(SUM(ocd.amount), 0) > 0
        THEN ((bmd.total_revenue_impact - COALESCE(SUM(ocd.amount), 0)) / COALESCE(SUM(ocd.amount), 1)) * 100
        ELSE 0
    END as daily_roi_percentage
FROM business_metrics_daily bmd
LEFT JOIN operating_costs_daily ocd ON bmd.date = ocd.date AND bmd.tenant_id = ocd.tenant_id
GROUP BY bmd.date, bmd.tenant_id, bmd.total_revenue_impact
ORDER BY bmd.date DESC;

-- Feature Performance Summary View
CREATE OR REPLACE VIEW feature_performance_summary AS
SELECT
    date,
    'Real-Time Intelligence' as feature_name,
    leads_processed as usage_metric,
    conversion_rate_improvement as improvement_metric,
    estimated_revenue_impact as revenue_impact,
    avg_scoring_latency_ms as performance_ms
FROM lead_intelligence_metrics
UNION ALL
SELECT
    date,
    'Property Intelligence' as feature_name,
    properties_analyzed as usage_metric,
    match_satisfaction_score as improvement_metric,
    estimated_revenue_impact as revenue_impact,
    avg_analysis_time_ms as performance_ms
FROM property_intelligence_metrics
UNION ALL
SELECT
    date,
    'Churn Prevention' as feature_name,
    interventions_triggered as usage_metric,
    (churn_rate_before - churn_rate_after) as improvement_metric,
    estimated_revenue_saved as revenue_impact,
    avg_intervention_latency_seconds * 1000 as performance_ms
FROM churn_prevention_metrics
UNION ALL
SELECT
    date,
    'AI Coaching' as feature_name,
    coaching_sessions as usage_metric,
    performance_improvement as improvement_metric,
    estimated_revenue_impact as revenue_impact,
    avg_coaching_latency_ms as performance_ms
FROM ai_coaching_metrics
ORDER BY date DESC, feature_name;

-- Business Impact Health Check View
CREATE OR REPLACE VIEW business_impact_health AS
SELECT
    CURRENT_DATE as check_date,

    -- Performance Health (Green if all metrics meet targets)
    CASE
        WHEN AVG(bmd.websocket_avg_latency_ms) < 50
         AND AVG(bmd.ml_inference_avg_latency_ms) < 35
         AND AVG(bmd.vision_analysis_avg_time_ms) < 1500
         AND AVG(bmd.coaching_analysis_avg_time_ms) < 2000
        THEN 'GREEN'
        WHEN AVG(bmd.websocket_avg_latency_ms) < 100
         AND AVG(bmd.ml_inference_avg_latency_ms) < 70
        THEN 'YELLOW'
        ELSE 'RED'
    END as performance_health,

    -- ROI Health (Green if > 500%)
    CASE
        WHEN AVG(bmd.net_roi_percentage) > 5.0 THEN 'GREEN'
        WHEN AVG(bmd.net_roi_percentage) > 2.0 THEN 'YELLOW'
        ELSE 'RED'
    END as roi_health,

    -- Adoption Health (Green if > 80%)
    CASE
        WHEN (AVG(bmd.real_time_intelligence_adoption_rate) +
              AVG(bmd.property_vision_adoption_rate) +
              AVG(bmd.churn_prevention_adoption_rate) +
              AVG(bmd.ai_coaching_adoption_rate)) / 4 > 0.8 THEN 'GREEN'
        WHEN (AVG(bmd.real_time_intelligence_adoption_rate) +
              AVG(bmd.property_vision_adoption_rate) +
              AVG(bmd.churn_prevention_adoption_rate) +
              AVG(bmd.ai_coaching_adoption_rate)) / 4 > 0.6 THEN 'YELLOW'
        ELSE 'RED'
    END as adoption_health,

    -- Overall Health Score
    CASE
        WHEN (AVG(bmd.net_roi_percentage) > 5.0
              AND AVG(bmd.websocket_avg_latency_ms) < 50
              AND (AVG(bmd.real_time_intelligence_adoption_rate) +
                   AVG(bmd.property_vision_adoption_rate) +
                   AVG(bmd.churn_prevention_adoption_rate) +
                   AVG(bmd.ai_coaching_adoption_rate)) / 4 > 0.8)
        THEN 'EXCELLENT'
        WHEN AVG(bmd.net_roi_percentage) > 2.0 THEN 'GOOD'
        WHEN AVG(bmd.net_roi_percentage) > 0.5 THEN 'FAIR'
        ELSE 'POOR'
    END as overall_health

FROM business_metrics_daily bmd
WHERE bmd.date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY check_date;

COMMENT ON TABLE business_metrics_daily IS 'Daily snapshot of all Phase 3 business metrics and ROI';
COMMENT ON TABLE lead_intelligence_metrics IS 'Real-time lead intelligence feature performance tracking';
COMMENT ON TABLE property_intelligence_metrics IS 'Multimodal property analysis feature performance tracking';
COMMENT ON TABLE churn_prevention_metrics IS 'Proactive churn prevention feature performance tracking';
COMMENT ON TABLE ai_coaching_metrics IS 'AI-powered coaching feature performance tracking';
COMMENT ON TABLE operating_costs_daily IS 'Daily operating costs by category for ROI calculation';
COMMENT ON TABLE roi_weekly_summary IS 'Weekly ROI summary across all features';
COMMENT ON TABLE feature_rollout_tracking IS 'Track feature rollout progress and impact at each stage';
COMMENT ON TABLE business_impact_alerts IS 'Business impact monitoring and alerting';

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO enterprisehub_api;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO enterprisehub_readonly;