-- Migration 001: Initial Service 6 Database Schema
-- Version: 1.0.0
-- Description: Creates the complete Service 6 Lead Recovery & Nurture Engine database schema
-- Apply to: Fresh PostgreSQL 15+ database

-- Check PostgreSQL version
DO $$
BEGIN
    IF current_setting('server_version_num')::integer < 150000 THEN
        RAISE EXCEPTION 'PostgreSQL version 15.0 or higher required. Current version: %', version();
    END IF;
END $$;

-- Create migration tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by TEXT DEFAULT current_user,
    checksum VARCHAR(64),
    execution_time_ms INTEGER
);

-- Check if this migration has already been applied
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '001') THEN
        RAISE EXCEPTION 'Migration 001 has already been applied';
    END IF;
END $$;

-- Record migration start
INSERT INTO schema_migrations (version, description, applied_at, applied_by) 
VALUES ('001', 'Initial Service 6 database schema creation', NOW(), current_user);

-- Start timing
\timing on

-- Execute all initialization scripts in order
\ir '../init/01_setup_extensions.sql'
\ir '../init/02_create_tables.sql'
\ir '../init/03_create_compliance_tables.sql'
\ir '../init/04_create_monitoring_tables.sql'
\ir '../init/05_create_indexes.sql'
\ir '../init/06_create_functions_triggers.sql'
\ir '../init/07_create_views.sql'
\ir '../init/09_permissions_security.sql'
\ir '../init/10_final_validation.sql'

-- Update migration record with completion time
UPDATE schema_migrations 
SET execution_time_ms = EXTRACT(EPOCH FROM (NOW() - applied_at)) * 1000,
    checksum = md5('001_initial_migration_complete')
WHERE version = '001';

-- Log completion
SELECT 
    'Migration 001 completed successfully' as status,
    version,
    description,
    applied_at,
    execution_time_ms || ' ms' as execution_time
FROM schema_migrations 
WHERE version = '001';

-- Verify migration success
SELECT * FROM validate_complete_setup() 
WHERE status = 'FAIL' 
ORDER BY category, check_name;
