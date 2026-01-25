-- OLAP Data Warehouse Schema Extension for Jorge's Business Intelligence Dashboard
-- Extends existing PostgreSQL with star schema for fast analytical queries
-- Optimized for real-time BI dashboard and executive reporting

-- ====================
-- FACT TABLES - Events and Transactions
-- ====================

-- Fact table for all lead interactions
CREATE TABLE IF NOT EXISTS fact_lead_interactions (
    id BIGSERIAL PRIMARY KEY,
    lead_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,

    -- Jorge-specific metrics
    jorge_metrics JSONB,  -- FRS/PCS scores, temperature, qualification progress

    -- Event context
    dimensions JSONB,      -- location, source, bot_type, agent

    -- Performance tracking
    processing_time_ms DECIMAL(10,3),
    confidence_score DECIMAL(5,3),

    -- Indexing for analytics queries
    location_id VARCHAR(50),
    bot_type VARCHAR(30),
    lead_temperature VARCHAR(20),
    event_category VARCHAR(30),

    CONSTRAINT valid_confidence CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    CONSTRAINT valid_temperature CHECK (lead_temperature IN ('hot', 'warm', 'lukewarm', 'cold', 'ice_cold'))
);

-- Fact table for commission events and pipeline tracking
CREATE TABLE IF NOT EXISTS fact_commission_events (
    id BIGSERIAL PRIMARY KEY,
    lead_id VARCHAR(50) NOT NULL,
    deal_id VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Commission tracking
    commission_amount DECIMAL(10,2),
    pipeline_stage VARCHAR(50),  -- qualified, shown, offer, closed
    jorge_pipeline_value DECIMAL(12,2),  -- 6% commission tracking

    -- Deal context
    property_value DECIMAL(12,2),
    close_probability DECIMAL(5,3),
    days_in_pipeline INTEGER,

    -- Location context
    location_id VARCHAR(50),
    agent_id VARCHAR(50),

    CONSTRAINT positive_commission CHECK (commission_amount >= 0),
    CONSTRAINT valid_probability CHECK (close_probability BETWEEN 0.0 AND 1.0)
);

-- Fact table for bot performance metrics
CREATE TABLE IF NOT EXISTS fact_bot_performance (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Bot identification
    bot_type VARCHAR(50) NOT NULL,  -- jorge-seller, jorge-buyer, lead-bot, intent-decoder
    contact_id VARCHAR(50),

    -- Performance metrics
    processing_time_ms DECIMAL(10,3),
    success BOOLEAN,
    confidence_score DECIMAL(5,3),

    -- Bot-specific metrics
    bot_metrics JSONB,  -- qualification scores, sequence progress, etc.

    -- Context
    location_id VARCHAR(50),
    conversation_stage VARCHAR(30),

    CONSTRAINT valid_bot_type CHECK (bot_type IN ('jorge-seller', 'jorge-buyer', 'lead-bot', 'intent-decoder')),
    CONSTRAINT valid_confidence CHECK (confidence_score BETWEEN 0.0 AND 1.0)
);

-- ====================
-- AGGREGATION TABLES - Pre-computed Analytics
-- ====================

-- Daily aggregated metrics for fast dashboard loading
CREATE TABLE IF NOT EXISTS agg_daily_metrics (
    date DATE NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Bot performance aggregations
    bot_performance JSONB,    -- Jorge seller/buyer/lead bot metrics

    -- Lead funnel aggregations
    lead_funnel JSONB,        -- conversion rates by stage

    -- Revenue pipeline aggregations
    revenue_pipeline JSONB,   -- commission tracking and forecasting

    -- System performance
    system_performance JSONB, -- response times, error rates

    -- Computed at timestamp
    computed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    PRIMARY KEY (date, location_id)
);

-- Hourly aggregated metrics for real-time insights
CREATE TABLE IF NOT EXISTS agg_hourly_metrics (
    hour_bucket TIMESTAMP WITH TIME ZONE NOT NULL,  -- Truncated to hour
    location_id VARCHAR(50) NOT NULL,

    -- Real-time KPIs
    leads_processed INTEGER DEFAULT 0,
    conversations_active INTEGER DEFAULT 0,
    qualifications_completed INTEGER DEFAULT 0,
    hot_leads_generated INTEGER DEFAULT 0,

    -- Jorge bot specific metrics
    jorge_seller_interactions INTEGER DEFAULT 0,
    jorge_buyer_interactions INTEGER DEFAULT 0,
    jorge_avg_qualification_time_ms DECIMAL(10,3),

    -- Revenue metrics
    pipeline_value_added DECIMAL(12,2) DEFAULT 0,
    commission_pipeline DECIMAL(12,2) DEFAULT 0,

    -- Performance metrics
    avg_response_time_ms DECIMAL(10,3),
    error_rate DECIMAL(5,3),
    cache_hit_rate DECIMAL(5,3),

    -- Computed at timestamp
    computed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    PRIMARY KEY (hour_bucket, location_id),
    CONSTRAINT valid_error_rate CHECK (error_rate BETWEEN 0.0 AND 1.0),
    CONSTRAINT valid_cache_hit_rate CHECK (cache_hit_rate BETWEEN 0.0 AND 1.0)
);

-- ====================
-- DIMENSION TABLES - Lookup Data
-- ====================

-- Bot type dimension for analytics
CREATE TABLE IF NOT EXISTS dim_bot_types (
    bot_type VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100),
    description TEXT,
    category VARCHAR(30),  -- seller, buyer, lifecycle, analysis
    performance_targets JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Location dimension (if not exists)
CREATE TABLE IF NOT EXISTS dim_locations (
    location_id VARCHAR(50) PRIMARY KEY,
    location_name VARCHAR(200),
    timezone VARCHAR(50),
    market_type VARCHAR(30),  -- urban, suburban, rural
    avg_home_value DECIMAL(12,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ====================
-- INDEXES - Optimized for Analytics Queries
-- ====================

-- Indexes for fact_lead_interactions
CREATE INDEX IF NOT EXISTS idx_lead_interactions_timestamp ON fact_lead_interactions (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_lead_interactions_location ON fact_lead_interactions (location_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_lead_interactions_bot_type ON fact_lead_interactions (bot_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_lead_interactions_temperature ON fact_lead_interactions (lead_temperature, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_lead_interactions_event_type ON fact_lead_interactions (event_type, timestamp DESC);

-- Indexes for fact_commission_events
CREATE INDEX IF NOT EXISTS idx_commission_events_timestamp ON fact_commission_events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_commission_events_location ON fact_commission_events (location_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_commission_events_pipeline ON fact_commission_events (pipeline_stage, timestamp DESC);

-- Indexes for fact_bot_performance
CREATE INDEX IF NOT EXISTS idx_bot_performance_timestamp ON fact_bot_performance (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_bot_performance_bot_type ON fact_bot_performance (bot_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_bot_performance_location ON fact_bot_performance (location_id, timestamp DESC);

-- Indexes for aggregation tables
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON agg_daily_metrics (date DESC, location_id);
CREATE INDEX IF NOT EXISTS idx_hourly_metrics_hour ON agg_hourly_metrics (hour_bucket DESC, location_id);

-- ====================
-- MATERIALIZED VIEWS - Pre-computed Analytics
-- ====================

-- Real-time dashboard metrics view
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_real_time_dashboard AS
SELECT
    location_id,

    -- Lead metrics (last 24 hours)
    COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '24 hours' THEN 1 END) as leads_24h,
    COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '24 hours' AND lead_temperature = 'hot' THEN 1 END) as hot_leads_24h,

    -- Bot performance (last 24 hours)
    AVG(CASE WHEN timestamp >= NOW() - INTERVAL '24 hours' AND processing_time_ms IS NOT NULL
             THEN processing_time_ms END) as avg_response_time_24h,

    -- Jorge qualification metrics
    COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '24 hours' AND bot_type = 'jorge-seller' THEN 1 END) as jorge_seller_interactions_24h,
    COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '24 hours' AND bot_type = 'jorge-buyer' THEN 1 END) as jorge_buyer_interactions_24h,

    -- Conversion metrics
    CASE WHEN COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '24 hours' THEN 1 END) > 0
         THEN COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '24 hours' AND lead_temperature = 'hot' THEN 1 END)::DECIMAL /
              COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '24 hours' THEN 1 END)
         ELSE 0 END as hot_conversion_rate_24h,

    -- Last updated
    NOW() as updated_at

FROM fact_lead_interactions
WHERE timestamp >= NOW() - INTERVAL '7 days'  -- Keep recent data for calculations
GROUP BY location_id;

-- Weekly performance trends view
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_weekly_trends AS
SELECT
    location_id,
    DATE_TRUNC('week', timestamp) as week_start,
    bot_type,

    -- Volume metrics
    COUNT(*) as interactions,
    COUNT(CASE WHEN lead_temperature = 'hot' THEN 1 END) as hot_leads,

    -- Performance metrics
    AVG(processing_time_ms) as avg_response_time,
    AVG(confidence_score) as avg_confidence,

    -- Jorge-specific metrics
    AVG((jorge_metrics->>'frs_score')::DECIMAL) as avg_frs_score,
    AVG((jorge_metrics->>'pcs_score')::DECIMAL) as avg_pcs_score,

    -- Last updated
    NOW() as updated_at

FROM fact_lead_interactions
WHERE timestamp >= NOW() - INTERVAL '12 weeks'
  AND jorge_metrics IS NOT NULL
GROUP BY location_id, DATE_TRUNC('week', timestamp), bot_type
ORDER BY week_start DESC, location_id, bot_type;

-- ====================
-- DATA POPULATION - Initial Setup
-- ====================

-- Insert default bot types
INSERT INTO dim_bot_types (bot_type, display_name, description, category, performance_targets) VALUES
('jorge-seller', 'Jorge Seller Bot', 'Confrontational qualification for motivated sellers', 'seller', '{"target_response_time_ms": 50, "target_hot_rate": 0.15}'),
('jorge-buyer', 'Jorge Buyer Bot', 'Consultative qualification for serious buyers', 'buyer', '{"target_response_time_ms": 75, "target_qualification_rate": 0.25}'),
('lead-bot', 'Lead Lifecycle Bot', '3-7-30 day automated follow-up sequences', 'lifecycle', '{"target_response_time_ms": 100, "target_engagement_rate": 0.60}'),
('intent-decoder', 'Intent Analysis Engine', 'ML-powered intent classification and scoring', 'analysis', '{"target_response_time_ms": 25, "target_confidence": 0.85}')
ON CONFLICT (bot_type) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    performance_targets = EXCLUDED.performance_targets;

-- ====================
-- REFRESH FUNCTIONS - Automated Updates
-- ====================

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_real_time_dashboard;
    REFRESH MATERIALIZED VIEW mv_weekly_trends;

    -- Log refresh
    INSERT INTO fact_lead_interactions (lead_id, event_type, jorge_metrics, dimensions)
    VALUES ('system', 'analytics_refresh', '{"refresh_timestamp": "' || NOW() || '"}', '{"component": "materialized_views"}');
END;
$$ LANGUAGE plpgsql;

-- Function to aggregate hourly metrics
CREATE OR REPLACE FUNCTION aggregate_hourly_metrics()
RETURNS void AS $$
DECLARE
    current_hour TIMESTAMP WITH TIME ZONE;
    location RECORD;
BEGIN
    current_hour := DATE_TRUNC('hour', NOW() - INTERVAL '1 hour');

    -- Aggregate for each location
    FOR location IN SELECT DISTINCT location_id FROM fact_lead_interactions WHERE location_id IS NOT NULL
    LOOP
        INSERT INTO agg_hourly_metrics (
            hour_bucket, location_id,
            leads_processed, conversations_active, qualifications_completed, hot_leads_generated,
            jorge_seller_interactions, jorge_buyer_interactions, jorge_avg_qualification_time_ms,
            pipeline_value_added, avg_response_time_ms
        )
        SELECT
            current_hour,
            location.location_id,
            COUNT(*),
            COUNT(CASE WHEN event_type = 'conversation_update' THEN 1 END),
            COUNT(CASE WHEN event_type LIKE '%qualification%' THEN 1 END),
            COUNT(CASE WHEN lead_temperature = 'hot' THEN 1 END),
            COUNT(CASE WHEN bot_type = 'jorge-seller' THEN 1 END),
            COUNT(CASE WHEN bot_type = 'jorge-buyer' THEN 1 END),
            AVG(CASE WHEN bot_type LIKE 'jorge%' THEN processing_time_ms END),
            COALESCE(SUM((jorge_metrics->>'pipeline_value')::DECIMAL), 0),
            AVG(processing_time_ms)
        FROM fact_lead_interactions
        WHERE timestamp >= current_hour
          AND timestamp < current_hour + INTERVAL '1 hour'
          AND location_id = location.location_id
        ON CONFLICT (hour_bucket, location_id) DO UPDATE SET
            leads_processed = EXCLUDED.leads_processed,
            conversations_active = EXCLUDED.conversations_active,
            qualifications_completed = EXCLUDED.qualifications_completed,
            hot_leads_generated = EXCLUDED.hot_leads_generated,
            jorge_seller_interactions = EXCLUDED.jorge_seller_interactions,
            jorge_buyer_interactions = EXCLUDED.jorge_buyer_interactions,
            jorge_avg_qualification_time_ms = EXCLUDED.jorge_avg_qualification_time_ms,
            pipeline_value_added = EXCLUDED.pipeline_value_added,
            avg_response_time_ms = EXCLUDED.avg_response_time_ms,
            computed_at = NOW();
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ====================
-- SCHEDULED JOBS - Automated Maintenance
-- ====================

-- Note: These would typically be set up with pg_cron extension or external scheduler

-- Example cron jobs (for reference):
-- SELECT cron.schedule('refresh-analytics', '*/5 * * * *', 'SELECT refresh_analytics_views();');
-- SELECT cron.schedule('aggregate-hourly', '5 * * * *', 'SELECT aggregate_hourly_metrics();');

-- ====================
-- GRANTS - Security
-- ====================

-- Grant read access to analytics tables for BI service account
-- GRANT SELECT ON fact_lead_interactions, fact_commission_events, fact_bot_performance TO bi_readonly;
-- GRANT SELECT ON agg_daily_metrics, agg_hourly_metrics TO bi_readonly;
-- GRANT SELECT ON mv_real_time_dashboard, mv_weekly_trends TO bi_readonly;

-- ====================
-- COMMENTS - Documentation
-- ====================

COMMENT ON TABLE fact_lead_interactions IS 'Central fact table for all lead interactions with Jorge bot ecosystem';
COMMENT ON TABLE fact_commission_events IS 'Commission pipeline tracking for Jorge''s 6% revenue model';
COMMENT ON TABLE fact_bot_performance IS 'Bot performance metrics for monitoring and optimization';
COMMENT ON TABLE agg_daily_metrics IS 'Pre-aggregated daily metrics for fast dashboard loading';
COMMENT ON TABLE agg_hourly_metrics IS 'Real-time hourly aggregations for live dashboard updates';

COMMENT ON MATERIALIZED VIEW mv_real_time_dashboard IS 'Real-time dashboard metrics updated every 5 minutes';
COMMENT ON MATERIALIZED VIEW mv_weekly_trends IS 'Weekly performance trends for Jorge bot ecosystem';

COMMENT ON FUNCTION refresh_analytics_views() IS 'Refresh all materialized views for BI dashboard';
COMMENT ON FUNCTION aggregate_hourly_metrics() IS 'Aggregate hourly metrics for real-time analytics';