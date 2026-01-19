-- ====================================================================
-- Performance Optimization Indexes for Jorge's Revenue Platform
-- ====================================================================
-- Purpose: Optimize database query performance for sub-50ms response times
-- Target: 1000+ concurrent requests with <100ms API response times
-- Author: Claude Code Performance Optimization Agent
-- Created: 2026-01-17
-- ====================================================================

-- ====================================================================
-- 1. GOLDEN LEAD DETECTION OPTIMIZATION
-- ====================================================================

-- Composite index for golden lead filtering (tier + probability + score)
CREATE INDEX IF NOT EXISTS idx_golden_leads_tier_probability_score
ON golden_lead_scores (tier, conversion_probability DESC, overall_score DESC)
WHERE tenant_id IS NOT NULL AND analysis_timestamp > NOW() - INTERVAL '7 days';

-- Index for recent golden lead analysis (time-based queries)
CREATE INDEX IF NOT EXISTS idx_golden_leads_recent_analysis
ON golden_lead_scores (tenant_id, analysis_timestamp DESC)
WHERE tier IN ('platinum', 'gold', 'silver');

-- Index for behavioral signal lookups
CREATE INDEX IF NOT EXISTS idx_golden_leads_behavioral_signals
ON golden_lead_scores USING GIN (behavioral_signals jsonb_path_ops)
WHERE behavioral_signals IS NOT NULL;

-- Partial index for high-priority leads only
CREATE INDEX IF NOT EXISTS idx_golden_leads_high_priority
ON golden_lead_scores (lead_id, tenant_id, conversion_probability DESC)
WHERE conversion_probability >= 0.7 AND tier IN ('platinum', 'gold');


-- ====================================================================
-- 2. DYNAMIC PRICING OPTIMIZATION
-- ====================================================================

-- Index for pricing calculations by contact
CREATE INDEX IF NOT EXISTS idx_pricing_contact_location
ON lead_pricing_history (contact_id, location_id, calculated_at DESC);

-- Index for pricing analytics queries
CREATE INDEX IF NOT EXISTS idx_pricing_analytics_time_range
ON lead_pricing_history (location_id, calculated_at DESC)
WHERE tier IN ('hot', 'warm');

-- Index for ROI calculation queries
CREATE INDEX IF NOT EXISTS idx_pricing_roi_analysis
ON lead_pricing_history (location_id, tier, final_price, expected_roi DESC)
WHERE calculated_at > NOW() - INTERVAL '30 days';


-- ====================================================================
-- 3. PREDICTIVE ANALYTICS OPTIMIZATION
-- ====================================================================

-- Index for lead scoring history lookups
CREATE INDEX IF NOT EXISTS idx_predictive_scores_lead_lookup
ON predictive_lead_scores (lead_id, calculated_at DESC);

-- Index for high-priority lead filtering
CREATE INDEX IF NOT EXISTS idx_predictive_scores_priority
ON predictive_lead_scores (priority_level, closing_probability DESC)
WHERE closing_probability >= 0.5;

-- Index for predictive insights queries
CREATE INDEX IF NOT EXISTS idx_predictive_insights_recent
ON predictive_lead_insights (lead_id, generated_at DESC)
WHERE generated_at > NOW() - INTERVAL '24 hours';


-- ====================================================================
-- 4. USAGE ANALYTICS OPTIMIZATION
-- ====================================================================

-- Index for tenant usage tracking
CREATE INDEX IF NOT EXISTS idx_usage_analytics_tenant_time
ON api_usage_logs (tenant_id, timestamp DESC);

-- Index for endpoint performance monitoring
CREATE INDEX IF NOT EXISTS idx_usage_analytics_endpoint_performance
ON api_usage_logs (endpoint, response_time_ms, timestamp DESC)
WHERE response_time_ms > 100;  -- Track slow requests only

-- Index for error tracking
CREATE INDEX IF NOT EXISTS idx_usage_analytics_errors
ON api_usage_logs (tenant_id, timestamp DESC)
WHERE status_code >= 400;


-- ====================================================================
-- 5. MESSAGE TEMPLATE OPTIMIZATION
-- ====================================================================

-- Index for template lookups by category and intent
CREATE INDEX IF NOT EXISTS idx_message_templates_category_intent
ON message_templates (category, intent, is_active)
WHERE is_active = true;

-- Index for A/B testing queries
CREATE INDEX IF NOT EXISTS idx_message_templates_ab_testing
ON message_templates (category, ab_test_group, performance_score DESC)
WHERE is_active = true AND ab_test_group IS NOT NULL;


-- ====================================================================
-- 6. TENANT DATA OPTIMIZATION
-- ====================================================================

-- Index for active tenant lookups
CREATE INDEX IF NOT EXISTS idx_tenants_active_lookup
ON tenants (location_id, is_active)
WHERE is_active = true;

-- Index for tenant feature access
CREATE INDEX IF NOT EXISTS idx_tenants_features
ON tenants USING GIN (enabled_features jsonb_path_ops)
WHERE is_active = true;


-- ====================================================================
-- 7. LEAD DATA OPTIMIZATION
-- ====================================================================

-- Composite index for lead filtering (status + score + updated_at)
CREATE INDEX IF NOT EXISTS idx_leads_status_score_updated
ON leads (status, lead_score DESC, updated_at DESC)
WHERE tenant_id IS NOT NULL;

-- Index for lead conversation history lookups
CREATE INDEX IF NOT EXISTS idx_leads_conversation_recent
ON leads (lead_id, updated_at DESC)
WHERE conversation_history IS NOT NULL;

-- Partial index for high-score leads
CREATE INDEX IF NOT EXISTS idx_leads_high_score
ON leads (tenant_id, lead_id, lead_score DESC)
WHERE lead_score >= 70;


-- ====================================================================
-- 8. CACHE OPTIMIZATION TABLES
-- ====================================================================

-- Create table for tracking cache performance
CREATE TABLE IF NOT EXISTS cache_performance_metrics (
    id SERIAL PRIMARY KEY,
    key_prefix VARCHAR(255) NOT NULL,
    hit_count BIGINT DEFAULT 0,
    miss_count BIGINT DEFAULT 0,
    avg_access_interval_seconds FLOAT,
    recommended_ttl_seconds INT,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(key_prefix)
);

-- Index for cache metrics lookups
CREATE INDEX IF NOT EXISTS idx_cache_metrics_prefix
ON cache_performance_metrics (key_prefix, last_updated DESC);


-- ====================================================================
-- 9. QUERY PERFORMANCE MONITORING
-- ====================================================================

-- Create table for tracking slow queries
CREATE TABLE IF NOT EXISTS slow_query_log (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT,
    execution_time_ms FLOAT NOT NULL,
    rows_returned INT,
    table_name VARCHAR(255),
    tenant_id VARCHAR(255),
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Index for slow query analysis
CREATE INDEX IF NOT EXISTS idx_slow_queries_time_analysis
ON slow_query_log (execution_time_ms DESC, recorded_at DESC)
WHERE execution_time_ms > 50;

-- Index for slow query by table
CREATE INDEX IF NOT EXISTS idx_slow_queries_by_table
ON slow_query_log (table_name, execution_time_ms DESC);


-- ====================================================================
-- 10. CONNECTION POOL OPTIMIZATION
-- ====================================================================

-- Create table for tracking database connection pool metrics
CREATE TABLE IF NOT EXISTS connection_pool_metrics (
    id SERIAL PRIMARY KEY,
    active_connections INT NOT NULL,
    idle_connections INT NOT NULL,
    waiting_requests INT NOT NULL,
    avg_checkout_time_ms FLOAT,
    max_checkout_time_ms FLOAT,
    pool_exhaustion_count INT DEFAULT 0,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Index for connection pool monitoring
CREATE INDEX IF NOT EXISTS idx_connection_pool_recent
ON connection_pool_metrics (recorded_at DESC);


-- ====================================================================
-- 11. MATERIALIZED VIEWS FOR ANALYTICS
-- ====================================================================

-- Materialized view for golden lead tier distribution
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_golden_lead_tier_distribution AS
SELECT
    tenant_id,
    tier,
    COUNT(*) as lead_count,
    AVG(conversion_probability) as avg_probability,
    AVG(overall_score) as avg_score,
    DATE_TRUNC('hour', analysis_timestamp) as hour_bucket
FROM golden_lead_scores
WHERE analysis_timestamp > NOW() - INTERVAL '24 hours'
GROUP BY tenant_id, tier, hour_bucket;

-- Index on materialized view
CREATE INDEX IF NOT EXISTS idx_mv_golden_tier_tenant_hour
ON mv_golden_lead_tier_distribution (tenant_id, hour_bucket DESC);

-- Materialized view for pricing performance
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_pricing_performance_hourly AS
SELECT
    location_id,
    tier,
    COUNT(*) as pricing_calculations,
    AVG(final_price) as avg_price,
    AVG(expected_roi) as avg_roi,
    DATE_TRUNC('hour', calculated_at) as hour_bucket
FROM lead_pricing_history
WHERE calculated_at > NOW() - INTERVAL '24 hours'
GROUP BY location_id, tier, hour_bucket;

-- Index on pricing performance view
CREATE INDEX IF NOT EXISTS idx_mv_pricing_performance_location_hour
ON mv_pricing_performance_hourly (location_id, hour_bucket DESC);


-- ====================================================================
-- 12. PARTITIONING FOR LARGE TABLES (Future-proofing)
-- ====================================================================

-- Note: Partitioning setup for when tables grow beyond 10M rows
-- Uncomment and modify when needed:

-- Example: Partition api_usage_logs by month
-- CREATE TABLE api_usage_logs_y2026m01 PARTITION OF api_usage_logs
--     FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');


-- ====================================================================
-- 13. VACUUM AND ANALYZE OPTIMIZATIONS
-- ====================================================================

-- Set autovacuum settings for high-traffic tables
ALTER TABLE golden_lead_scores SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE lead_pricing_history SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE api_usage_logs SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);


-- ====================================================================
-- 14. STATISTICS COLLECTION
-- ====================================================================

-- Update statistics for query planner optimization
ANALYZE golden_lead_scores;
ANALYZE lead_pricing_history;
ANALYZE predictive_lead_scores;
ANALYZE api_usage_logs;
ANALYZE message_templates;
ANALYZE leads;
ANALYZE tenants;


-- ====================================================================
-- 15. PERFORMANCE MONITORING FUNCTIONS
-- ====================================================================

-- Function to get table statistics
CREATE OR REPLACE FUNCTION get_table_performance_stats(table_name_param TEXT)
RETURNS TABLE (
    table_name TEXT,
    total_rows BIGINT,
    table_size TEXT,
    index_size TEXT,
    total_size TEXT,
    last_vacuum TIMESTAMP,
    last_analyze TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname || '.' || relname AS table_name,
        n_live_tup AS total_rows,
        pg_size_pretty(pg_total_relation_size(schemaname || '.' || relname)) AS table_size,
        pg_size_pretty(pg_indexes_size(schemaname || '.' || relname)) AS index_size,
        pg_size_pretty(pg_total_relation_size(schemaname || '.' || relname) + pg_indexes_size(schemaname || '.' || relname)) AS total_size,
        last_vacuum,
        last_analyze
    FROM pg_stat_user_tables
    WHERE relname = table_name_param;
END;
$$ LANGUAGE plpgsql;

-- Function to get slow queries
CREATE OR REPLACE FUNCTION get_recent_slow_queries(min_duration_ms FLOAT DEFAULT 50.0, limit_count INT DEFAULT 20)
RETURNS TABLE (
    query_hash VARCHAR(64),
    query_text TEXT,
    execution_time_ms FLOAT,
    table_name VARCHAR(255),
    recorded_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        slow_query_log.query_hash,
        slow_query_log.query_text,
        slow_query_log.execution_time_ms,
        slow_query_log.table_name,
        slow_query_log.recorded_at
    FROM slow_query_log
    WHERE slow_query_log.execution_time_ms >= min_duration_ms
    ORDER BY slow_query_log.execution_time_ms DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_golden_lead_tier_distribution;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_pricing_performance_hourly;
END;
$$ LANGUAGE plpgsql;


-- ====================================================================
-- 16. SCHEDULED MAINTENANCE (via pg_cron if available)
-- ====================================================================

-- Note: Requires pg_cron extension
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule materialized view refresh every hour
-- SELECT cron.schedule('refresh-performance-views', '0 * * * *', 'SELECT refresh_performance_views();');

-- Schedule vacuum analyze for critical tables daily
-- SELECT cron.schedule('vacuum-golden-leads', '0 2 * * *', 'VACUUM ANALYZE golden_lead_scores;');
-- SELECT cron.schedule('vacuum-pricing', '0 2 * * *', 'VACUUM ANALYZE lead_pricing_history;');


-- ====================================================================
-- MIGRATION COMPLETE
-- ====================================================================

-- Record migration completion
INSERT INTO schema_migrations (version, description, applied_at)
VALUES (
    '009',
    'Performance optimization indexes and monitoring',
    NOW()
)
ON CONFLICT (version) DO NOTHING;

-- Performance optimization summary
SELECT
    'Performance Optimization Migration Complete' as status,
    COUNT(*) FILTER (WHERE indexrelname LIKE 'idx_%') as indexes_created,
    COUNT(*) FILTER (WHERE relkind = 'm') as materialized_views_created
FROM pg_stat_user_indexes
WHERE schemaname = 'public';
