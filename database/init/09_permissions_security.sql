-- Service 6 Database Initialization - Step 9: Permissions and Security
-- PostgreSQL 15+ compatible
-- Creates database users, roles, and security configurations

-- Create application roles
CREATE ROLE service6_app_role;
CREATE ROLE service6_readonly_role;
CREATE ROLE service6_admin_role;
CREATE ROLE service6_compliance_role;
CREATE ROLE service6_analytics_role;

-- Create specific users (passwords should be changed in production)
-- Note: In production, these would be created by the DBA with secure passwords
DO $$
BEGIN
    -- Application user for the main Service 6 application
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'service6_user') THEN
        CREATE USER service6_user WITH PASSWORD 'service6_secure_password_change_in_production';
    END IF;
    
    -- Read-only user for reporting and analytics
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'service6_readonly') THEN
        CREATE USER service6_readonly WITH PASSWORD 'readonly_secure_password_change_in_production';
    END IF;
    
    -- Admin user for maintenance and migrations
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'service6_admin') THEN
        CREATE USER service6_admin WITH PASSWORD 'admin_secure_password_change_in_production';
    END IF;
    
    -- Compliance user for GDPR and audit access
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'service6_compliance') THEN
        CREATE USER service6_compliance WITH PASSWORD 'compliance_secure_password_change_in_production';
    END IF;
    
    -- Analytics user for metrics and reporting
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'service6_analytics') THEN
        CREATE USER service6_analytics WITH PASSWORD 'analytics_secure_password_change_in_production';
    END IF;
END
$$;

-- Assign users to roles
GRANT service6_app_role TO service6_user;
GRANT service6_readonly_role TO service6_readonly;
GRANT service6_admin_role TO service6_admin;
GRANT service6_compliance_role TO service6_compliance;
GRANT service6_analytics_role TO service6_analytics;

-- Application role permissions (full CRUD access to application tables)
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE 
    leads, lead_intelligence, communications, nurture_sequences, 
    agents, workflow_executions, metrics_hourly,
    consent_logs, data_retention, error_queue, 
    system_health_checks, performance_metrics, alerts, 
    sla_tracking, resource_utilization, setup_log
TO service6_app_role;

-- Grant access to views
GRANT SELECT ON 
    v_lead_summary, v_agent_performance, v_communication_effectiveness,
    v_lead_funnel, v_system_health
TO service6_app_role;

-- Grant access to materialized views
GRANT SELECT ON mv_hourly_metrics TO service6_app_role;

-- Grant sequence permissions for auto-increment fields
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service6_app_role;

-- Grant function execution permissions
GRANT EXECUTE ON FUNCTION 
    update_updated_at_column(), update_lead_activity(), 
    update_agent_capacity(), calculate_lead_composite_score(),
    create_audit_log(), calculate_response_time(),
    enforce_data_retention(), validate_schema_health()
TO service6_app_role;

-- Read-only role permissions (for reporting and analytics)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO service6_readonly_role;
GRANT SELECT ON ALL VIEWS IN SCHEMA public TO service6_readonly_role;
GRANT SELECT ON mv_hourly_metrics TO service6_readonly_role;
GRANT EXECUTE ON FUNCTION validate_schema_health() TO service6_readonly_role;

-- Admin role permissions (full access for maintenance)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service6_admin_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service6_admin_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service6_admin_role;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA public TO service6_admin_role;
GRANT ALL PRIVILEGES ON mv_hourly_metrics TO service6_admin_role;

-- Grant ability to refresh materialized views
GRANT SELECT, INSERT, UPDATE, DELETE ON mv_hourly_metrics TO service6_admin_role;

-- Compliance role permissions (access to audit and GDPR data)
GRANT SELECT, INSERT, UPDATE ON TABLE 
    consent_logs, data_retention, data_subject_requests, 
    audit_log, processing_activities, data_breaches
TO service6_compliance_role;

GRANT SELECT ON TABLE 
    leads, communications, agents, workflow_executions
TO service6_compliance_role;

GRANT EXECUTE ON FUNCTION 
    enforce_data_retention(), validate_schema_health()
TO service6_compliance_role;

-- Analytics role permissions (metrics and performance data)
GRANT SELECT ON TABLE 
    metrics_hourly, performance_metrics, system_health_checks,
    sla_tracking, resource_utilization, workflow_executions,
    leads, communications, nurture_sequences, agents
TO service6_analytics_role;

GRANT SELECT ON ALL VIEWS IN SCHEMA public TO service6_analytics_role;
GRANT SELECT ON mv_hourly_metrics TO service6_analytics_role;

-- Row Level Security (RLS) policies for multi-tenant support
-- Enable RLS on sensitive tables
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_intelligence ENABLE ROW LEVEL SECURITY;
ALTER TABLE communications ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for agent-based access control
-- Agents can only see their own assigned leads (unless they're managers)
CREATE POLICY lead_agent_access ON leads
    FOR ALL TO service6_app_role
    USING (
        assigned_agent_id = current_setting('app.current_agent_id', true)::UUID
        OR 
        current_setting('app.current_agent_role', true) IN ('manager', 'admin')
        OR 
        assigned_agent_id IS NULL  -- Unassigned leads visible to all
    );

-- Communications access based on lead access
CREATE POLICY communication_agent_access ON communications
    FOR ALL TO service6_app_role
    USING (
        lead_id IN (
            SELECT id FROM leads 
            WHERE assigned_agent_id = current_setting('app.current_agent_id', true)::UUID
               OR current_setting('app.current_agent_role', true) IN ('manager', 'admin')
               OR assigned_agent_id IS NULL
        )
    );

-- Lead intelligence access based on lead access
CREATE POLICY intelligence_agent_access ON lead_intelligence
    FOR ALL TO service6_app_role
    USING (
        lead_id IN (
            SELECT id FROM leads 
            WHERE assigned_agent_id = current_setting('app.current_agent_id', true)::UUID
               OR current_setting('app.current_agent_role', true) IN ('manager', 'admin')
        )
    );

-- Consent logs access for compliance
CREATE POLICY consent_compliance_access ON consent_logs
    FOR ALL TO service6_compliance_role
    USING (true);  -- Full access for compliance team

-- Create security functions for application use
CREATE OR REPLACE FUNCTION set_current_agent(agent_id UUID, agent_role TEXT DEFAULT 'junior')
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_agent_id', agent_id::text, true);
    PERFORM set_config('app.current_agent_role', agent_role, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execution to application role
GRANT EXECUTE ON FUNCTION set_current_agent(UUID, TEXT) TO service6_app_role;

-- Create connection limit and security settings
ALTER ROLE service6_app_role CONNECTION LIMIT 50;
ALTER ROLE service6_readonly_role CONNECTION LIMIT 10;
ALTER ROLE service6_admin_role CONNECTION LIMIT 5;
ALTER ROLE service6_compliance_role CONNECTION LIMIT 5;
ALTER ROLE service6_analytics_role CONNECTION LIMIT 10;

-- Set security parameters for roles
ALTER ROLE service6_app_role SET statement_timeout = '30s';
ALTER ROLE service6_readonly_role SET statement_timeout = '60s';
ALTER ROLE service6_analytics_role SET statement_timeout = '300s';

-- Prevent certain operations for non-admin users
ALTER ROLE service6_app_role SET log_statement = 'mod';
ALTER ROLE service6_readonly_role SET log_statement = 'all';
ALTER ROLE service6_compliance_role SET log_statement = 'all';

-- Create audit trigger for security-sensitive tables
CREATE OR REPLACE FUNCTION security_audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Log all changes to sensitive tables with additional security context
    INSERT INTO audit_log (
        table_name,
        record_id,
        operation,
        old_values,
        new_values,
        user_id,
        user_email,
        ip_address,
        change_reason,
        automated,
        business_justification,
        gdpr_lawful_basis,
        session_id,
        api_endpoint
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE((to_jsonb(NEW)->>'id')::UUID, (to_jsonb(OLD)->>'id')::UUID),
        TG_OP,
        CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE to_jsonb(OLD) END,
        CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE to_jsonb(NEW) END,
        current_setting('app.current_agent_id', true)::UUID,
        current_setting('app.current_user_email', true),
        inet_client_addr(),
        current_setting('app.change_reason', true),
        false,  -- Manual changes
        current_setting('app.business_justification', true),
        current_setting('app.gdpr_lawful_basis', true),
        current_setting('app.session_id', true),
        current_setting('app.api_endpoint', true)
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply security audit triggers to sensitive tables
CREATE TRIGGER security_audit_agents 
    AFTER INSERT OR UPDATE OR DELETE ON agents 
    FOR EACH ROW 
    EXECUTE FUNCTION security_audit_trigger();

CREATE TRIGGER security_audit_consent_logs 
    AFTER INSERT OR UPDATE OR DELETE ON consent_logs 
    FOR EACH ROW 
    EXECUTE FUNCTION security_audit_trigger();

CREATE TRIGGER security_audit_data_retention 
    AFTER INSERT OR UPDATE OR DELETE ON data_retention 
    FOR EACH ROW 
    EXECUTE FUNCTION security_audit_trigger();

-- Create function to check user permissions
CREATE OR REPLACE FUNCTION check_user_permissions(user_name text)
RETURNS TABLE(
    role_name text,
    table_name text,
    privilege_type text,
    is_grantable boolean
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.rolname::text as role_name,
        c.relname::text as table_name,
        p.privilege_type::text,
        p.is_grantable::boolean
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN aclexplode(c.relacl) AS p(grantor, grantee, privilege_type, is_grantable)
         ON TRUE
    JOIN pg_roles r ON r.oid = p.grantee
    WHERE n.nspname = 'public'
      AND c.relkind IN ('r', 'v', 'm')  -- tables, views, materialized views
      AND r.rolname = user_name
    ORDER BY r.rolname, c.relname, p.privilege_type;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execution to admin role
GRANT EXECUTE ON FUNCTION check_user_permissions(text) TO service6_admin_role;

-- Create database security validation function
CREATE OR REPLACE FUNCTION validate_database_security()
RETURNS TABLE(check_name TEXT, status TEXT, details TEXT, recommendation TEXT) AS $$
BEGIN
    -- Check for default passwords
    RETURN QUERY
    SELECT
        'password_security'::TEXT,
        'WARNING'::TEXT,
        'Default passwords detected - must be changed in production'::TEXT,
        'Change all default passwords before production deployment'::TEXT;

    -- Check RLS policies
    RETURN QUERY
    SELECT
        'row_level_security'::TEXT,
        CASE WHEN COUNT(*) >= 4 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' RLS policies active',
        CASE WHEN COUNT(*) < 4 THEN 'Enable RLS policies on all sensitive tables' ELSE 'RLS policies properly configured' END
    FROM pg_policies 
    WHERE schemaname = 'public';

    -- Check role assignments
    RETURN QUERY
    SELECT
        'role_assignments'::TEXT,
        CASE WHEN COUNT(*) >= 5 THEN 'PASS' ELSE 'WARN' END,
        'Found ' || COUNT(*) || ' users with role assignments',
        'Ensure all users have appropriate role assignments'
    FROM pg_auth_members m
    JOIN pg_roles r ON r.oid = m.member
    WHERE r.rolname LIKE 'service6_%';

    -- Check connection limits
    RETURN QUERY
    SELECT
        'connection_limits'::TEXT,
        CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'WARN' END,
        'Connection limits configured for ' || COUNT(*) || ' roles',
        'Set appropriate connection limits for all roles'
    FROM pg_roles 
    WHERE rolconnlimit > 0 AND rolname LIKE 'service6_%';

END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execution to admin and compliance roles
GRANT EXECUTE ON FUNCTION validate_database_security() TO service6_admin_role, service6_compliance_role;

-- Create schema version tracking for security updates
INSERT INTO schema_versions (version, description) VALUES
('1.1.0', 'Added comprehensive security model with RLS, roles, and audit triggers');

-- Log successful completion
INSERT INTO setup_log (step, status, details, completed_at) 
VALUES (
    '09_permissions_security', 
    'SUCCESS', 
    'Security configuration completed: 5 roles created, RLS policies enabled, audit triggers configured, connection limits set',
    NOW()
) ON CONFLICT (step) DO UPDATE SET 
    status = EXCLUDED.status,
    details = EXCLUDED.details,
    completed_at = EXCLUDED.completed_at;

-- Final security check
SELECT 
    'Database security configured' as status,
    (SELECT COUNT(*) FROM pg_roles WHERE rolname LIKE 'service6_%') as roles_created,
    (SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public') as rls_policies,
    (SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE 'security_audit_%') as security_triggers,
    NOW() as timestamp;
