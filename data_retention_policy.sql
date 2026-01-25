-- Jorge's BI Dashboard Data Retention Policies
-- Manages data lifecycle for OLAP warehouse

CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS TABLE(cleanup_action VARCHAR, rows_affected BIGINT, table_name VARCHAR) AS $$
DECLARE
    deleted_rows BIGINT;
BEGIN
    -- Archive old lead interactions (keep 2 years, delete 3+ years old)
    DELETE FROM fact_lead_interactions
    WHERE timestamp < NOW() - INTERVAL '3 years';

    GET DIAGNOSTICS deleted_rows = ROW_COUNT;
    RETURN QUERY SELECT 'deleted_old_interactions'::VARCHAR, deleted_rows, 'fact_lead_interactions'::VARCHAR;

    -- Archive old commission events (keep 5 years for tax/audit purposes)
    DELETE FROM fact_commission_events
    WHERE timestamp < NOW() - INTERVAL '5 years';

    GET DIAGNOSTICS deleted_rows = ROW_COUNT;
    RETURN QUERY SELECT 'deleted_old_commissions'::VARCHAR, deleted_rows, 'fact_commission_events'::VARCHAR;

    -- Cleanup old bot performance data (keep 1 year)
    DELETE FROM fact_bot_performance
    WHERE timestamp < NOW() - INTERVAL '1 year';

    GET DIAGNOSTICS deleted_rows = ROW_COUNT;
    RETURN QUERY SELECT 'deleted_old_performance'::VARCHAR, deleted_rows, 'fact_bot_performance'::VARCHAR;

    -- Archive old hourly metrics (keep 90 days, aggregate into daily)
    INSERT INTO agg_daily_metrics (date, location_id, bot_performance, lead_funnel, revenue_pipeline, system_performance)
    SELECT
        DATE(hour_bucket) as date,
        location_id,
        jsonb_build_object(
            'jorge_seller_interactions', SUM(jorge_seller_interactions),
            'jorge_buyer_interactions', SUM(jorge_buyer_interactions),
            'avg_qualification_time_ms', AVG(jorge_avg_qualification_time_ms)
        ) as bot_performance,
        jsonb_build_object(
            'leads_processed', SUM(leads_processed),
            'qualifications_completed', SUM(qualifications_completed),
            'hot_leads_generated', SUM(hot_leads_generated)
        ) as lead_funnel,
        jsonb_build_object(
            'pipeline_value_added', SUM(pipeline_value_added),
            'commission_pipeline', SUM(commission_pipeline)
        ) as revenue_pipeline,
        jsonb_build_object(
            'avg_response_time_ms', AVG(avg_response_time_ms),
            'avg_error_rate', AVG(error_rate),
            'avg_cache_hit_rate', AVG(cache_hit_rate)
        ) as system_performance
    FROM agg_hourly_metrics
    WHERE hour_bucket < NOW() - INTERVAL '90 days'
    GROUP BY DATE(hour_bucket), location_id
    ON CONFLICT (date, location_id) DO UPDATE SET
        bot_performance = EXCLUDED.bot_performance,
        lead_funnel = EXCLUDED.lead_funnel,
        revenue_pipeline = EXCLUDED.revenue_pipeline,
        system_performance = EXCLUDED.system_performance,
        computed_at = NOW();

    -- Now delete the archived hourly data
    DELETE FROM agg_hourly_metrics
    WHERE hour_bucket < NOW() - INTERVAL '90 days';

    GET DIAGNOSTICS deleted_rows = ROW_COUNT;
    RETURN QUERY SELECT 'archived_hourly_to_daily'::VARCHAR, deleted_rows, 'agg_hourly_metrics'::VARCHAR;

    -- Cleanup old monitoring data (keep 30 days)
    DELETE FROM db_monitoring
    WHERE timestamp < NOW() - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_rows = ROW_COUNT;
    RETURN QUERY SELECT 'deleted_old_monitoring'::VARCHAR, deleted_rows, 'db_monitoring'::VARCHAR;

    -- Vacuum and analyze tables for performance
    VACUUM ANALYZE fact_lead_interactions;
    VACUUM ANALYZE fact_commission_events;
    VACUUM ANALYZE fact_bot_performance;
    VACUUM ANALYZE agg_daily_metrics;
    VACUUM ANALYZE agg_hourly_metrics;

    RETURN QUERY SELECT 'vacuum_analyzed'::VARCHAR, 0::BIGINT, 'all_tables'::VARCHAR;

END;
$$ LANGUAGE plpgsql;

-- Performance monitoring function
CREATE OR REPLACE FUNCTION log_performance_metrics()
RETURNS void AS $$
DECLARE
    db_size_mb DECIMAL;
    active_conns INTEGER;
    table_count INTEGER;
BEGIN
    -- Get database metrics
    SELECT pg_database_size('enterprise_hub') / 1024.0 / 1024.0 INTO db_size_mb;
    SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active' INTO active_conns;
    SELECT COUNT(*) FROM fact_lead_interactions WHERE timestamp >= NOW() - INTERVAL '1 hour' INTO table_count;

    -- Log to monitoring table
    INSERT INTO db_monitoring (metric_name, metric_value, details) VALUES
        ('database_size_mb', db_size_mb, '{"category": "storage"}'),
        ('active_connections', active_conns, '{"category": "performance"}'),
        ('hourly_lead_interactions', table_count, '{"category": "business_metrics"}');

    -- Log table sizes
    INSERT INTO db_monitoring (metric_name, metric_value, details)
    SELECT
        'table_size_mb_' || schemaname || '_' || tablename,
        pg_total_relation_size(schemaname||'.'||tablename) / 1024.0 / 1024.0,
        jsonb_build_object('category', 'storage', 'schema', schemaname, 'table', tablename)
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename LIKE 'fact_%' OR tablename LIKE 'agg_%';

END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_data() IS 'Automated data retention and archival for Jorge BI Dashboard';
COMMENT ON FUNCTION log_performance_metrics() IS 'Log database performance metrics for monitoring';