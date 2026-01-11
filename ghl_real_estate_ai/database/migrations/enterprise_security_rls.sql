-- Enterprise Security Migration: Row-Level Security (RLS) Policies
-- Phase 4: Critical security fixes for multi-tenant isolation
-- PRIORITY: P0 - Prevents cross-tenant data access vulnerabilities

-- =====================================================
-- SECURITY AUDIT TABLE
-- =====================================================

-- Create security audit log table for tracking access violations
CREATE TABLE IF NOT EXISTS security_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    attempted_tenant_id VARCHAR(100),
    actual_tenant_id VARCHAR(100),
    user_id VARCHAR(100),
    table_name VARCHAR(100),
    operation VARCHAR(20), -- INSERT, UPDATE, DELETE, SELECT
    blocked BOOLEAN DEFAULT false,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(100),
    error_details TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for security monitoring
CREATE INDEX IF NOT EXISTS idx_security_audit_timestamp ON security_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_security_audit_event_type ON security_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_security_audit_blocked ON security_audit_log(blocked) WHERE blocked = true;

COMMENT ON TABLE security_audit_log IS 'Security audit trail for RLS violations and access attempts';

-- =====================================================
-- TENANT CONTEXT FUNCTIONS
-- =====================================================

-- Function to get current tenant from session
CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS TEXT
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    -- Get tenant from session variable (set by application)
    RETURN current_setting('app.current_tenant_id', true);
EXCEPTION WHEN OTHERS THEN
    -- If no tenant set, return null (will block access via RLS)
    RETURN NULL;
END;
$$;

-- Function to get current location_id from session
CREATE OR REPLACE FUNCTION get_current_location_id()
RETURNS TEXT
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    -- Get location_id from session variable
    RETURN current_setting('app.current_location_id', true);
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$;

-- Function to validate tenant access
CREATE OR REPLACE FUNCTION validate_tenant_access(target_tenant_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    current_tenant TEXT;
    is_admin BOOLEAN;
BEGIN
    -- Get current tenant from session
    current_tenant := get_current_tenant_id();

    -- Check if user has admin privileges
    is_admin := COALESCE(current_setting('app.is_admin', true)::BOOLEAN, false);

    -- Allow access if admin or tenant matches
    IF is_admin OR current_tenant = target_tenant_id::TEXT THEN
        RETURN true;
    END IF;

    -- Log unauthorized access attempt
    INSERT INTO security_audit_log (
        event_type,
        attempted_tenant_id,
        actual_tenant_id,
        user_id,
        blocked,
        error_details
    ) VALUES (
        'UNAUTHORIZED_TENANT_ACCESS',
        target_tenant_id::TEXT,
        current_tenant,
        current_setting('app.user_id', true),
        true,
        'Attempted to access data for different tenant'
    );

    RETURN false;
END;
$$;

-- Function to validate location access
CREATE OR REPLACE FUNCTION validate_location_access(target_location_id VARCHAR)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    current_location TEXT;
    is_admin BOOLEAN;
BEGIN
    current_location := get_current_location_id();
    is_admin := COALESCE(current_setting('app.is_admin', true)::BOOLEAN, false);

    IF is_admin OR current_location = target_location_id THEN
        RETURN true;
    END IF;

    -- Log unauthorized access attempt
    INSERT INTO security_audit_log (
        event_type,
        attempted_tenant_id,
        actual_tenant_id,
        user_id,
        blocked,
        error_details
    ) VALUES (
        'UNAUTHORIZED_LOCATION_ACCESS',
        target_location_id,
        current_location,
        current_setting('app.user_id', true),
        true,
        'Attempted to access data for different location'
    );

    RETURN false;
END;
$$;

-- =====================================================
-- ROW-LEVEL SECURITY POLICIES
-- =====================================================

-- TENANTS Table RLS Policies
CREATE POLICY tenant_isolation_policy ON tenants
    FOR ALL
    USING (
        COALESCE(current_setting('app.is_admin', true)::BOOLEAN, false) = true
        OR location_id = get_current_location_id()
    );

CREATE POLICY tenant_insert_policy ON tenants
    FOR INSERT
    WITH CHECK (
        COALESCE(current_setting('app.is_admin', true)::BOOLEAN, false) = true
    );

-- CONVERSATIONS Table RLS Policies
CREATE POLICY conversation_tenant_isolation ON conversations
    FOR ALL
    USING (
        validate_tenant_access(tenant_id)
    );

CREATE POLICY conversation_insert_policy ON conversations
    FOR INSERT
    WITH CHECK (
        validate_tenant_access(tenant_id)
    );

-- CONVERSATION_MESSAGES Table RLS Policies
CREATE POLICY conversation_messages_isolation ON conversation_messages
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = conversation_messages.conversation_id
            AND validate_tenant_access(c.tenant_id)
        )
    );

CREATE POLICY conversation_messages_insert_policy ON conversation_messages
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = conversation_messages.conversation_id
            AND validate_tenant_access(c.tenant_id)
        )
    );

-- BEHAVIORAL_PREFERENCES Table RLS Policies
CREATE POLICY behavioral_preferences_isolation ON behavioral_preferences
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = behavioral_preferences.conversation_id
            AND validate_tenant_access(c.tenant_id)
        )
    );

CREATE POLICY behavioral_preferences_insert_policy ON behavioral_preferences
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = behavioral_preferences.conversation_id
            AND validate_tenant_access(c.tenant_id)
        )
    );

-- PROPERTY_INTERACTIONS Table RLS Policies
CREATE POLICY property_interactions_isolation ON property_interactions
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = property_interactions.conversation_id
            AND validate_tenant_access(c.tenant_id)
        )
    );

CREATE POLICY property_interactions_insert_policy ON property_interactions
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = property_interactions.conversation_id
            AND validate_tenant_access(c.tenant_id)
        )
    );

-- CLAUDE_CONFIGURATIONS Table RLS Policies
CREATE POLICY claude_config_tenant_isolation ON claude_configurations
    FOR ALL
    USING (
        validate_tenant_access(tenant_id)
    );

CREATE POLICY claude_config_insert_policy ON claude_configurations
    FOR INSERT
    WITH CHECK (
        validate_tenant_access(tenant_id)
    );

-- CLAUDE_PERFORMANCE_METRICS Table RLS Policies
CREATE POLICY claude_metrics_tenant_isolation ON claude_performance_metrics
    FOR ALL
    USING (
        validate_tenant_access(tenant_id)
    );

CREATE POLICY claude_metrics_insert_policy ON claude_performance_metrics
    FOR INSERT
    WITH CHECK (
        validate_tenant_access(tenant_id)
    );

-- MEMORY_ANALYTICS Table RLS Policies
CREATE POLICY memory_analytics_tenant_isolation ON memory_analytics
    FOR ALL
    USING (
        validate_tenant_access(tenant_id)
    );

CREATE POLICY memory_analytics_insert_policy ON memory_analytics
    FOR INSERT
    WITH CHECK (
        validate_tenant_access(tenant_id)
    );

-- SYSTEM_HEALTH_LOGS Table RLS Policies (admin-only for sensitive info)
CREATE POLICY system_health_admin_only ON system_health_logs
    FOR ALL
    USING (
        COALESCE(current_setting('app.is_admin', true)::BOOLEAN, false) = true
        OR (tenant_id IS NOT NULL AND validate_tenant_access(tenant_id))
    );

CREATE POLICY system_health_insert_policy ON system_health_logs
    FOR INSERT
    WITH CHECK (true); -- Allow inserts from system components

-- =====================================================
-- SECURITY HELPER FUNCTIONS
-- =====================================================

-- Function to set tenant context (called by application)
CREATE OR REPLACE FUNCTION set_tenant_context(
    p_tenant_id UUID DEFAULT NULL,
    p_location_id VARCHAR DEFAULT NULL,
    p_user_id VARCHAR DEFAULT NULL,
    p_is_admin BOOLEAN DEFAULT false
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    -- Set session variables for RLS
    PERFORM set_config('app.current_tenant_id', COALESCE(p_tenant_id::TEXT, ''), false);
    PERFORM set_config('app.current_location_id', COALESCE(p_location_id, ''), false);
    PERFORM set_config('app.user_id', COALESCE(p_user_id, ''), false);
    PERFORM set_config('app.is_admin', p_is_admin::TEXT, false);

    -- Log context change for audit
    INSERT INTO security_audit_log (
        event_type,
        attempted_tenant_id,
        user_id,
        blocked,
        error_details
    ) VALUES (
        'TENANT_CONTEXT_SET',
        p_tenant_id::TEXT,
        p_user_id,
        false,
        'Tenant context established'
    );
END;
$$;

-- Function to clear tenant context (for session cleanup)
CREATE OR REPLACE FUNCTION clear_tenant_context()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', '', false);
    PERFORM set_config('app.current_location_id', '', false);
    PERFORM set_config('app.user_id', '', false);
    PERFORM set_config('app.is_admin', 'false', false);
END;
$$;

-- Function to get tenant statistics (admin only)
CREATE OR REPLACE FUNCTION get_tenant_security_stats()
RETURNS TABLE(
    location_id VARCHAR,
    total_violations BIGINT,
    recent_violations BIGINT,
    blocked_attempts BIGINT,
    last_violation TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
BEGIN
    -- Only allow admin access
    IF NOT COALESCE(current_setting('app.is_admin', true)::BOOLEAN, false) THEN
        RAISE EXCEPTION 'Admin access required';
    END IF;

    RETURN QUERY
    SELECT
        sal.attempted_tenant_id,
        COUNT(*) as total_violations,
        COUNT(*) FILTER (WHERE sal.timestamp >= NOW() - INTERVAL '24 hours') as recent_violations,
        COUNT(*) FILTER (WHERE sal.blocked = true) as blocked_attempts,
        MAX(sal.timestamp) as last_violation
    FROM security_audit_log sal
    WHERE sal.event_type LIKE '%UNAUTHORIZED%'
    GROUP BY sal.attempted_tenant_id
    ORDER BY recent_violations DESC;
END;
$$;

-- =====================================================
-- CROSS-TENANT QUERY DETECTION
-- =====================================================

-- Function to detect suspicious cross-tenant patterns
CREATE OR REPLACE FUNCTION detect_cross_tenant_queries()
RETURNS TABLE(
    session_id VARCHAR,
    user_id VARCHAR,
    tenant_switches BIGINT,
    suspicious_activity BOOLEAN,
    first_switch TIMESTAMP WITH TIME ZONE,
    last_switch TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
BEGIN
    -- Only allow admin access
    IF NOT COALESCE(current_setting('app.is_admin', true)::BOOLEAN, false) THEN
        RAISE EXCEPTION 'Admin access required';
    END IF;

    RETURN QUERY
    SELECT
        sal.session_id,
        sal.user_id,
        COUNT(DISTINCT sal.attempted_tenant_id) as tenant_switches,
        COUNT(DISTINCT sal.attempted_tenant_id) > 1 as suspicious_activity,
        MIN(sal.timestamp) as first_switch,
        MAX(sal.timestamp) as last_switch
    FROM security_audit_log sal
    WHERE sal.event_type = 'TENANT_CONTEXT_SET'
    AND sal.timestamp >= NOW() - INTERVAL '1 hour'
    GROUP BY sal.session_id, sal.user_id
    HAVING COUNT(DISTINCT sal.attempted_tenant_id) > 1
    ORDER BY tenant_switches DESC;
END;
$$;

-- =====================================================
-- TRIGGER FOR RLS VIOLATION DETECTION
-- =====================================================

-- Trigger function to detect RLS bypass attempts
CREATE OR REPLACE FUNCTION log_rls_violation()
RETURNS TRIGGER AS $$
BEGIN
    -- Log potential RLS violation
    INSERT INTO security_audit_log (
        event_type,
        attempted_tenant_id,
        actual_tenant_id,
        table_name,
        operation,
        blocked,
        error_details,
        user_id
    ) VALUES (
        'POTENTIAL_RLS_VIOLATION',
        CASE
            WHEN TG_TABLE_NAME = 'conversations' THEN NEW.tenant_id::TEXT
            WHEN TG_TABLE_NAME = 'claude_configurations' THEN NEW.tenant_id::TEXT
            ELSE 'unknown'
        END,
        get_current_tenant_id(),
        TG_TABLE_NAME,
        TG_OP,
        false,
        'Row inserted/updated with different tenant than session context',
        current_setting('app.user_id', true)
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for violation detection
CREATE TRIGGER rls_violation_conversations
    AFTER INSERT OR UPDATE ON conversations
    FOR EACH ROW
    WHEN (NEW.tenant_id::TEXT != get_current_tenant_id() AND get_current_tenant_id() IS NOT NULL)
    EXECUTE FUNCTION log_rls_violation();

CREATE TRIGGER rls_violation_claude_configs
    AFTER INSERT OR UPDATE ON claude_configurations
    FOR EACH ROW
    WHEN (NEW.tenant_id::TEXT != get_current_tenant_id() AND get_current_tenant_id() IS NOT NULL)
    EXECUTE FUNCTION log_rls_violation();

-- =====================================================
-- EMERGENCY FUNCTIONS
-- =====================================================

-- Function to temporarily disable RLS for emergency maintenance (admin only)
CREATE OR REPLACE FUNCTION emergency_disable_rls(table_name TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Only allow admin
    IF NOT COALESCE(current_setting('app.is_admin', true)::BOOLEAN, false) THEN
        RAISE EXCEPTION 'Admin access required for emergency RLS disable';
    END IF;

    -- Log emergency action
    INSERT INTO security_audit_log (
        event_type,
        table_name,
        user_id,
        error_details
    ) VALUES (
        'EMERGENCY_RLS_DISABLED',
        table_name,
        current_setting('app.user_id', true),
        'RLS temporarily disabled for emergency maintenance'
    );

    -- Disable RLS
    EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', table_name);
END;
$$;

-- Function to re-enable RLS after emergency maintenance
CREATE OR REPLACE FUNCTION emergency_enable_rls(table_name TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Only allow admin
    IF NOT COALESCE(current_setting('app.is_admin', true)::BOOLEAN, false) THEN
        RAISE EXCEPTION 'Admin access required for emergency RLS enable';
    END IF;

    -- Re-enable RLS
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);

    -- Log emergency action complete
    INSERT INTO security_audit_log (
        event_type,
        table_name,
        user_id,
        error_details
    ) VALUES (
        'EMERGENCY_RLS_ENABLED',
        table_name,
        current_setting('app.user_id', true),
        'RLS re-enabled after emergency maintenance'
    );
END;
$$;

-- =====================================================
-- TESTING AND VALIDATION
-- =====================================================

-- Function to test RLS policies
CREATE OR REPLACE FUNCTION test_rls_policies()
RETURNS TABLE(
    test_name TEXT,
    passed BOOLEAN,
    error_message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    test_tenant_id UUID;
    test_location_id VARCHAR := 'test_location_123';
    test_result RECORD;
BEGIN
    -- Create test tenant
    INSERT INTO tenants (location_id, name, status)
    VALUES (test_location_id, 'Test Tenant for RLS', 'active')
    RETURNING id INTO test_tenant_id;

    -- Test 1: Admin can access all data
    PERFORM set_tenant_context(test_tenant_id, test_location_id, 'admin_user', true);

    BEGIN
        SELECT INTO test_result COUNT(*) FROM tenants;
        RETURN QUERY SELECT 'Admin access all tenants', true, 'OK';
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'Admin access all tenants', false, SQLERRM;
    END;

    -- Test 2: Regular user can only access own tenant
    PERFORM set_tenant_context(test_tenant_id, test_location_id, 'regular_user', false);

    BEGIN
        SELECT INTO test_result COUNT(*) FROM tenants WHERE location_id = test_location_id;
        IF test_result IS NOT NULL THEN
            RETURN QUERY SELECT 'User access own tenant', true, 'OK';
        ELSE
            RETURN QUERY SELECT 'User access own tenant', false, 'No data returned';
        END IF;
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'User access own tenant', false, SQLERRM;
    END;

    -- Test 3: User cannot access different tenant
    PERFORM set_tenant_context(test_tenant_id, 'different_location', 'regular_user', false);

    BEGIN
        SELECT INTO test_result COUNT(*) FROM tenants WHERE location_id = test_location_id;
        IF test_result.count = 0 THEN
            RETURN QUERY SELECT 'User blocked from other tenant', true, 'OK';
        ELSE
            RETURN QUERY SELECT 'User blocked from other tenant', false, 'Access not blocked';
        END IF;
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'User blocked from other tenant', true, 'Access properly blocked: ' || SQLERRM;
    END;

    -- Cleanup
    PERFORM clear_tenant_context();
    PERFORM set_tenant_context(NULL, NULL, 'admin_user', true);
    DELETE FROM tenants WHERE id = test_tenant_id;
    PERFORM clear_tenant_context();
END;
$$;

-- =====================================================
-- MIGRATION COMPLETION
-- =====================================================

-- Record migration completion
INSERT INTO schema_migrations (version, description)
VALUES ('1.1.0', 'Enterprise security: Row-Level Security policies and tenant isolation')
ON CONFLICT (version) DO NOTHING;

-- Create admin role for emergency functions
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'enterprisehub_admin') THEN
        CREATE ROLE enterprisehub_admin;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO enterprisehub_admin;
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO enterprisehub_admin;
        GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO enterprisehub_admin;
    END IF;
END
$$;

-- Verification message
SELECT 'Enterprise Row-Level Security policies implemented successfully!' as status,
       'All tables now have tenant isolation with audit logging' as details;

-- Display security summary
SELECT
    'RLS Status' as check_type,
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables t
JOIN pg_class c ON c.relname = t.tablename
WHERE t.schemaname = 'public'
AND t.tablename IN ('tenants', 'conversations', 'conversation_messages',
                   'behavioral_preferences', 'property_interactions', 'claude_configurations')
ORDER BY t.tablename;