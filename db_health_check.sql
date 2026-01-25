CREATE OR REPLACE FUNCTION db_health_check()
RETURNS TABLE(metric VARCHAR, value DECIMAL, status VARCHAR) AS $$
BEGIN
    -- Database size
    RETURN QUERY SELECT
        'db_size_mb'::VARCHAR,
        (pg_database_size('enterprise_hub') / 1024.0 / 1024.0)::DECIMAL,
        'normal'::VARCHAR;

    -- Active connections
    RETURN QUERY SELECT
        'active_connections'::VARCHAR,
        (SELECT COUNT(*)::DECIMAL FROM pg_stat_activity WHERE state = 'active')::DECIMAL,
        CASE
            WHEN (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') > 20
            THEN 'warning'::VARCHAR
            ELSE 'normal'::VARCHAR
        END;

    -- Table sizes for key OLAP tables
    RETURN QUERY SELECT
        'fact_lead_interactions_rows'::VARCHAR,
        (SELECT COUNT(*)::DECIMAL FROM fact_lead_interactions),
        'normal'::VARCHAR;

    RETURN QUERY SELECT
        'fact_commission_events_rows'::VARCHAR,
        (SELECT COUNT(*)::DECIMAL FROM fact_commission_events),
        'normal'::VARCHAR;

    RETURN QUERY SELECT
        'fact_bot_performance_rows'::VARCHAR,
        (SELECT COUNT(*)::DECIMAL FROM fact_bot_performance),
        'normal'::VARCHAR;
END;
$$ LANGUAGE plpgsql;