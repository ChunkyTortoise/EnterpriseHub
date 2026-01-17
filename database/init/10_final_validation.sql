-- Service 6 Database Initialization - Step 10: Final Validation and Optimization
-- PostgreSQL 15+ compatible
-- Final validation, optimization, and cleanup

-- Create comprehensive validation function
CREATE OR REPLACE FUNCTION validate_complete_setup()
RETURNS TABLE(
    category TEXT,
    check_name TEXT, 
    status TEXT, 
    details TEXT, 
    recommendations TEXT
) AS $$
BEGIN
    -- 1. Schema Validation
    RETURN QUERY
    SELECT
        'SCHEMA'::TEXT,
        'table_count'::TEXT,
        CASE WHEN COUNT(*) >= 15 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' tables (expected 15+)',
        CASE WHEN COUNT(*) < 15 THEN 'Check for missing tables' ELSE 'All required tables present' END
    FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

    -- 2. Index Validation
    RETURN QUERY
    SELECT
        'PERFORMANCE'::TEXT,
        'index_count'::TEXT,
        CASE WHEN COUNT(*) >= 40 THEN 'PASS' ELSE 'WARN' END,
        'Found ' || COUNT(*) || ' indexes (expected 40+)',
        CASE WHEN COUNT(*) < 40 THEN 'Consider adding more indexes for performance' ELSE 'Adequate index coverage' END
    FROM pg_indexes 
    WHERE schemaname = 'public' AND indexname LIKE 'idx_%';

    -- 3. Function Validation
    RETURN QUERY
    SELECT
        'FUNCTIONALITY'::TEXT,
        'function_count'::TEXT,
        CASE WHEN COUNT(*) >= 8 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' custom functions (expected 8+)',
        CASE WHEN COUNT(*) < 8 THEN 'Check for missing functions' ELSE 'All required functions present' END
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public' AND p.prokind = 'f';

    -- 4. Trigger Validation
    RETURN QUERY
    SELECT
        'AUTOMATION'::TEXT,
        'trigger_count'::TEXT,
        CASE WHEN COUNT(*) >= 10 THEN 'PASS' ELSE 'WARN' END,
        'Found ' || COUNT(*) || ' triggers (expected 10+)',
        'Triggers provide automated data management'
    FROM pg_trigger 
    WHERE tgname NOT LIKE '%_oid';

    -- 5. View Validation
    RETURN QUERY
    SELECT
        'REPORTING'::TEXT,
        'view_count'::TEXT,
        CASE WHEN COUNT(*) >= 5 THEN 'PASS' ELSE 'WARN' END,
        'Found ' || COUNT(*) || ' views (expected 5+)',
        'Views provide optimized queries for applications'
    FROM information_schema.views 
    WHERE table_schema = 'public';

    -- 6. Sample Data Validation
    RETURN QUERY
    SELECT
        'DATA'::TEXT,
        'sample_leads'::TEXT,
        CASE WHEN COUNT(*) >= 5 THEN 'PASS' ELSE 'WARN' END,
        'Found ' || COUNT(*) || ' sample leads',
        CASE WHEN COUNT(*) < 5 THEN 'Add sample data for testing' ELSE 'Adequate sample data for development' END
    FROM leads WHERE deleted_at IS NULL;

    -- 7. Security Validation
    RETURN QUERY
    SELECT
        'SECURITY'::TEXT,
        'rls_policies'::TEXT,
        CASE WHEN COUNT(*) >= 3 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' RLS policies (expected 3+)',
        CASE WHEN COUNT(*) < 3 THEN 'Enable Row Level Security policies' ELSE 'RLS properly configured' END
    FROM pg_policies 
    WHERE schemaname = 'public';

    -- 8. Role Validation
    RETURN QUERY
    SELECT
        'SECURITY'::TEXT,
        'database_roles'::TEXT,
        CASE WHEN COUNT(*) >= 5 THEN 'PASS' ELSE 'WARN' END,
        'Found ' || COUNT(*) || ' Service 6 roles',
        'Ensure all application roles are properly configured'
    FROM pg_roles 
    WHERE rolname LIKE 'service6_%';

    -- 9. Extension Validation
    RETURN QUERY
    SELECT
        'INFRASTRUCTURE'::TEXT,
        'extensions'::TEXT,
        CASE WHEN COUNT(*) >= 4 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' required extensions',
        CASE WHEN COUNT(*) < 4 THEN 'Install required PostgreSQL extensions' ELSE 'All required extensions installed' END
    FROM pg_extension 
    WHERE extname IN ('uuid-ossp', 'pgcrypto', 'btree_gin', 'pg_stat_statements');

    -- 10. Data Quality Validation
    RETURN QUERY
    SELECT
        'DATA_QUALITY'::TEXT,
        'lead_data_integrity'::TEXT,
        CASE WHEN invalid_count = 0 THEN 'PASS' ELSE 'WARN' END,
        invalid_count || ' leads with data quality issues',
        CASE WHEN invalid_count > 0 THEN 'Clean up invalid email/phone data' ELSE 'Data quality is good' END
    FROM (
        SELECT COUNT(*) as invalid_count
        FROM leads
        WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
           OR (phone IS NOT NULL AND phone !~ '^[0-9+\-() ]{10,20}$')
    ) subq;

    -- 11. Performance Validation
    RETURN QUERY
    SELECT
        'PERFORMANCE'::TEXT,
        'materialized_views'::TEXT,
        CASE WHEN COUNT(*) >= 1 THEN 'PASS' ELSE 'WARN' END,
        'Found ' || COUNT(*) || ' materialized views',
        'Materialized views improve query performance'
    FROM pg_matviews 
    WHERE schemaname = 'public';

    -- 12. Compliance Validation
    RETURN QUERY
    SELECT
        'COMPLIANCE'::TEXT,
        'audit_logging'::TEXT,
        CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END,
        'Audit log has ' || COUNT(*) || ' entries',
        CASE WHEN COUNT(*) = 0 THEN 'Configure audit logging for compliance' ELSE 'Audit logging is active' END
    FROM audit_log;

END;
$$ LANGUAGE plpgsql;

-- Run comprehensive validation
SELECT * FROM validate_complete_setup() ORDER BY category, check_name;

-- Create database statistics and optimization recommendations
CREATE OR REPLACE FUNCTION analyze_database_performance()
RETURNS TABLE(
    analysis_type TEXT,
    metric_name TEXT,
    current_value TEXT,
    recommendation TEXT
) AS $$
BEGIN
    -- Table sizes
    RETURN QUERY
    SELECT
        'TABLE_SIZE'::TEXT,
        'largest_tables'::TEXT,
        (SELECT string_agg(relname || ' (' || pg_size_pretty(pg_relation_size(oid)) || ')', ', ' ORDER BY pg_relation_size(oid) DESC)
         FROM pg_class 
         WHERE relkind = 'r' AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
         LIMIT 5),
        'Monitor table growth and consider partitioning for large tables'::TEXT;

    -- Index usage
    RETURN QUERY
    SELECT
        'INDEX_USAGE'::TEXT,
        'unused_indexes'::TEXT,
        (SELECT COALESCE(string_agg(indexname, ', '), 'None')
         FROM pg_stat_user_indexes 
         WHERE idx_scan = 0 AND schemaname = 'public'),
        'Consider dropping unused indexes to improve write performance'::TEXT;

    -- Connection stats
    RETURN QUERY
    SELECT
        'CONNECTIONS'::TEXT,
        'active_connections'::TEXT,
        (SELECT count(*)::TEXT FROM pg_stat_activity WHERE state = 'active'),
        'Monitor connection usage and tune max_connections if needed'::TEXT;

    -- Query performance
    RETURN QUERY
    SELECT
        'QUERY_PERFORMANCE'::TEXT,
        'slow_queries'::TEXT,
        CASE 
            WHEN (SELECT count(*) FROM pg_stat_statements WHERE mean_exec_time > 1000) > 0 
            THEN (SELECT count(*)::TEXT FROM pg_stat_statements WHERE mean_exec_time > 1000)
            ELSE 'No slow queries detected'
        END,
        'Review and optimize queries taking longer than 1 second'::TEXT;

END;
$$ LANGUAGE plpgsql;

-- Refresh materialized views
REFRESH MATERIALIZED VIEW mv_hourly_metrics;

-- Update table statistics for optimal query planning
ANALYZE leads;
ANALYZE communications;
ANALYZE agents;
ANALYZE lead_intelligence;
ANALYZE nurture_sequences;
ANALYZE workflow_executions;
ANALYZE metrics_hourly;
ANALYZE consent_logs;
ANALYZE audit_log;
ANALYZE error_queue;

-- Create maintenance schedule recommendations
CREATE OR REPLACE VIEW v_maintenance_schedule AS
SELECT
    'VACUUM ANALYZE' as operation,
    'Weekly' as frequency,
    'All tables' as target,
    'Maintain query performance and reclaim space' as purpose,
    'VACUUM ANALYZE;' as sql_command

UNION ALL

SELECT
    'REFRESH MATERIALIZED VIEWS' as operation,
    'Hourly' as frequency,
    'mv_hourly_metrics' as target,
    'Keep aggregated metrics current' as purpose,
    'REFRESH MATERIALIZED VIEW mv_hourly_metrics;' as sql_command

UNION ALL

SELECT
    'DATA RETENTION CLEANUP' as operation,
    'Daily' as frequency,
    'All tables with retention policies' as target,
    'Comply with data retention policies' as purpose,
    'SELECT enforce_data_retention();' as sql_command

UNION ALL

SELECT
    'SCHEMA HEALTH CHECK' as operation,
    'Weekly' as frequency,
    'Database schema' as target,
    'Validate database health and integrity' as purpose,
    'SELECT * FROM validate_schema_health();' as sql_command

UNION ALL

SELECT
    'SECURITY AUDIT' as operation,
    'Monthly' as frequency,
    'Security configuration' as target,
    'Ensure security policies are properly configured' as purpose,
    'SELECT * FROM validate_database_security();' as sql_command;

-- Create final setup summary
CREATE OR REPLACE VIEW v_setup_summary AS
SELECT
    step,
    status,
    details,
    completed_at
FROM setup_log
ORDER BY 
    CASE step
        WHEN '01_setup_extensions' THEN 1
        WHEN '02_create_tables' THEN 2
        WHEN '03_create_compliance_tables' THEN 3
        WHEN '04_create_monitoring_tables' THEN 4
        WHEN '05_create_indexes' THEN 5
        WHEN '06_create_functions_triggers' THEN 6
        WHEN '07_create_views' THEN 7
        WHEN '08_sample_data' THEN 8
        WHEN '09_permissions_security' THEN 9
        WHEN '10_final_validation' THEN 10
        ELSE 99
    END;

-- Log successful completion of final validation
INSERT INTO setup_log (step, status, details, completed_at) 
VALUES (
    '10_final_validation', 
    'SUCCESS', 
    'Database initialization complete with validation, optimization, and maintenance procedures',
    NOW()
) ON CONFLICT (step) DO UPDATE SET 
    status = EXCLUDED.status,
    details = EXCLUDED.details,
    completed_at = EXCLUDED.completed_at;

-- Final success summary
WITH setup_summary AS (
    SELECT 
        COUNT(*) as total_steps,
        COUNT(*) FILTER (WHERE status = 'SUCCESS') as successful_steps,
        string_agg(step || ' (' || status || ')', E'\n' ORDER BY completed_at) as step_details
    FROM setup_log
)
SELECT 
    'DATABASE INITIALIZATION COMPLETE' as status,
    'Service 6 Lead Recovery & Nurture Engine' as database_name,
    successful_steps || '/' || total_steps || ' steps completed successfully' as completion_status,
    NOW() as completed_at,
    'Database is ready for Service 6 application deployment' as message,
    step_details as initialization_log
FROM setup_summary;

-- Display maintenance recommendations
SELECT 'MAINTENANCE SCHEDULE' as info_type, operation, frequency, target, purpose 
FROM v_maintenance_schedule;

-- Display setup summary
SELECT 'SETUP SUMMARY' as info_type, step, status, completed_at 
FROM v_setup_summary;

-- Show database size and object counts
SELECT 
    'DATABASE STATISTICS' as info_type,
    'Database Size: ' || pg_size_pretty(pg_database_size(current_database())) as size_info,
    'Tables: ' || (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count,
    'Indexes: ' || (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') as index_count,
    'Functions: ' || (SELECT COUNT(*) FROM pg_proc WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')) as function_count;
