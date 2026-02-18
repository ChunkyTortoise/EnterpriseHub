-- ============================================================================
-- Row-Level Security (RLS) Migration Template for Multi-Tenant Isolation
-- ============================================================================
-- 
-- This migration enables PostgreSQL Row-Level Security for tenant isolation.
-- Each tenant can only access their own data through automatic query filtering.
--
-- Usage:
--   1. Replace {table_name} with your actual table name
--   2. Run this migration for each tenant-scoped table
--   3. Ensure all models include tenant_id column
--
-- Prerequisites:
--   - PostgreSQL 9.5+ (RLS introduced)
--   - PostgreSQL 12+ recommended (improved RLS performance)
--   - All tenant-scoped tables must have tenant_id UUID column
--
-- ============================================================================

-- ============================================================================
-- STEP 1: Create the app.current_tenant_id session variable function
-- ============================================================================

-- This function allows setting tenant context per session
-- It's used by the application to set the current tenant

CREATE OR REPLACE FUNCTION set_current_tenant_id(tenant_id UUID)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('SET app.current_tenant_id = %L', tenant_id::text);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current tenant ID (returns NULL if not set)
CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS UUID AS $$
DECLARE
    tenant_id TEXT;
BEGIN
    BEGIN
        tenant_id := current_setting('app.current_tenant_id', true);
        IF tenant_id IS NULL OR tenant_id = '' THEN
            RETURN NULL;
        END IF;
        RETURN tenant_id::UUID;
    EXCEPTION WHEN OTHERS THEN
        RETURN NULL;
    END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- STEP 2: Enable RLS on the target table
-- ============================================================================

-- Replace {table_name} with your actual table name
-- Example: ALTER TABLE users ENABLE ROW LEVEL SECURITY;

ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;

-- Force RLS for table owner (optional but recommended for extra security)
-- By default, table owner bypasses RLS; this forces even owner to comply
ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;

-- ============================================================================
-- STEP 3: Create RLS policies for tenant isolation
-- ============================================================================

-- Policy for SELECT operations
-- Only allows reading rows where tenant_id matches current session tenant
CREATE POLICY {table_name}_tenant_select ON {table_name}
    FOR SELECT
    USING (tenant_id = get_current_tenant_id());

-- Policy for INSERT operations
-- Only allows inserting rows with the current session tenant_id
CREATE POLICY {table_name}_tenant_insert ON {table_name}
    FOR INSERT
    WITH CHECK (tenant_id = get_current_tenant_id());

-- Policy for UPDATE operations
-- Only allows updating rows where tenant_id matches current session tenant
CREATE POLICY {table_name}_tenant_update ON {table_name}
    FOR UPDATE
    USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

-- Policy for DELETE operations
-- Only allows deleting rows where tenant_id matches current session tenant
CREATE POLICY {table_name}_tenant_delete ON {table_name}
    FOR DELETE
    USING (tenant_id = get_current_tenant_id());

-- ============================================================================
-- STEP 4: Create indexes for RLS performance
-- ============================================================================

-- Index on tenant_id for efficient RLS filtering
-- This is critical for query performance with RLS
CREATE INDEX IF NOT EXISTS idx_{table_name}_tenant_id ON {table_name}(tenant_id);

-- Composite index for common query patterns
-- Uncomment and modify based on your query patterns:
-- CREATE INDEX IF NOT EXISTS idx_{table_name}_tenant_created 
--     ON {table_name}(tenant_id, created_at DESC);

-- ============================================================================
-- STEP 5: Create bypass policy for super-admin (optional)
-- ============================================================================

-- Create a role for super-admins who need cross-tenant access
-- Uncomment if you need super-admin functionality:

-- CREATE ROLE IF NOT EXISTS super_admin;
-- 
-- -- Policy allowing super_admin role to bypass tenant filtering
-- CREATE POLICY {table_name}_super_admin_all ON {table_name}
--     FOR ALL
--     TO super_admin
--     USING (true)
--     WITH CHECK (true);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Run these queries to verify RLS is properly configured:

-- Check RLS is enabled:
-- SELECT relname, relrowsecurity, relforcerowsecurity 
-- FROM pg_class 
-- WHERE relname = '{table_name}';

-- List all policies on the table:
-- SELECT policyname, cmd, qual, with_check 
-- FROM pg_policies 
-- WHERE tablename = '{table_name}';

-- Test RLS (should return 0 rows if tenant context not set):
-- SET app.current_tenant_id = '00000000-0000-0000-0000-000000000000';
-- SELECT COUNT(*) FROM {table_name};

-- ============================================================================
-- ROLLBACK SCRIPT
-- ============================================================================

-- To rollback this migration, run:
/*
DROP POLICY IF EXISTS {table_name}_tenant_select ON {table_name};
DROP POLICY IF EXISTS {table_name}_tenant_insert ON {table_name};
DROP POLICY IF EXISTS {table_name}_tenant_update ON {table_name};
DROP POLICY IF EXISTS {table_name}_tenant_delete ON {table_name};
DROP POLICY IF EXISTS {table_name}_super_admin_all ON {table_name};
ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
ALTER TABLE {table_name} NO FORCE ROW LEVEL SECURITY;
DROP INDEX IF EXISTS idx_{table_name}_tenant_id;
DROP FUNCTION IF EXISTS set_current_tenant_id(UUID);
DROP FUNCTION IF EXISTS get_current_tenant_id();
*/

-- ============================================================================
-- EXAMPLE: Complete migration for 'users' table
-- ============================================================================

/*
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY users_tenant_select ON users
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY users_tenant_insert ON users
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY users_tenant_update ON users
    FOR UPDATE 
    USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY users_tenant_delete ON users
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- Create index
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
*/
