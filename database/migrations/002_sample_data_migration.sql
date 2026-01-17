-- Migration 002: Sample Data for Development/Testing
-- Version: 1.0.1
-- Description: Adds sample data for development and testing environments
-- Apply to: Development/staging databases only (NOT production)

-- Check if this migration has already been applied
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '002') THEN
        RAISE EXCEPTION 'Migration 002 has already been applied';
    END IF;
END $$;

-- Check if this is a production environment (should be set by deployment script)
DO $$
BEGIN
    IF COALESCE(current_setting('app.environment', true), 'development') = 'production' THEN
        RAISE EXCEPTION 'Sample data migration should not be applied to production environment';
    END IF;
END $$;

-- Record migration start
INSERT INTO schema_migrations (version, description, applied_at, applied_by) 
VALUES ('002', 'Sample data for development and testing', NOW(), current_user);

-- Execute sample data script
\ir '../init/08_sample_data.sql'

-- Update migration record with completion
UPDATE schema_migrations 
SET execution_time_ms = EXTRACT(EPOCH FROM (NOW() - applied_at)) * 1000,
    checksum = md5('002_sample_data_complete')
WHERE version = '002';

-- Verify sample data
SELECT 
    'Migration 002 completed - Sample data loaded' as status,
    (SELECT COUNT(*) FROM agents) as sample_agents,
    (SELECT COUNT(*) FROM leads) as sample_leads,
    (SELECT COUNT(*) FROM communications) as sample_communications
FROM schema_migrations 
WHERE version = '002';
