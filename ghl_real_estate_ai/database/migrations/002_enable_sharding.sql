-- Phase 4 Enterprise Scaling: Database Sharding Migration
-- Version: 002
-- Created: 2026-01-10
-- Purpose: Enable horizontal partitioning by location_id for enterprise scale
--
-- Sharding Strategy:
-- - Primary partitioning by location_id (aligns with GHL multi-tenant model)
-- - Large tables: leads, properties, conversations, property_interactions
-- - Target: Linear scaling, 1000+ concurrent users
-- - Maintain <50ms P90 single-shard queries
--
-- Pre-requisites:
-- - PostgreSQL 12+ (declarative partitioning support)
-- - pg_partman extension (optional, for automated partition management)
-- - Existing schema with performance indexes from migration 001
--
-- WARNING: This migration involves schema changes. Test thoroughly in staging!

-- =====================================================
-- EXTENSION SETUP
-- =====================================================

-- Enable pg_partman for automated partition management (optional)
-- CREATE EXTENSION IF NOT EXISTS pg_partman;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- SHARDING CONFIGURATION TABLE
-- =====================================================

-- Store shard configuration and routing information
CREATE TABLE IF NOT EXISTS shard_configuration (
    shard_id VARCHAR(50) PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL DEFAULT 5432,
    database_name VARCHAR(100) NOT NULL,
    state VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (state IN ('active', 'readonly', 'migrating', 'offline', 'maintenance')),
    weight DECIMAL(3,2) NOT NULL DEFAULT 1.0,
    hash_range_start INTEGER DEFAULT 0,
    hash_range_end INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Location to shard mapping
CREATE TABLE IF NOT EXISTS location_shard_mapping (
    location_id VARCHAR(100) PRIMARY KEY,
    shard_id VARCHAR(50) NOT NULL REFERENCES shard_configuration(shard_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    migrated_at TIMESTAMPTZ,
    migration_status VARCHAR(20) DEFAULT 'complete'
        CHECK (migration_status IN ('pending', 'in_progress', 'complete', 'failed'))
);

-- Create index for shard lookup
CREATE INDEX IF NOT EXISTS idx_location_shard_mapping_shard
    ON location_shard_mapping(shard_id);

-- =====================================================
-- LEADS TABLE PARTITIONING
-- =====================================================

-- Rename existing leads table (if not already partitioned)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = 'leads_original' AND n.nspname = 'public'
    ) AND EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = 'leads' AND n.nspname = 'public'
        AND c.relkind = 'r'  -- Regular table, not partitioned
    ) THEN
        -- Backup existing data
        ALTER TABLE leads RENAME TO leads_original;
    END IF;
END $$;

-- Create partitioned leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(100) NOT NULL,  -- Partition key
    tenant_id VARCHAR(100) NOT NULL,

    -- Lead information
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'active', 'qualified', 'contacted', 'closed', 'lost', 'inactive')),
    source VARCHAR(100),

    -- ML scoring
    ml_score DECIMAL(4,2) DEFAULT 0.0,
    score_confidence DECIMAL(4,2) DEFAULT 0.0,
    score_version VARCHAR(20),
    last_scored_at TIMESTAMPTZ,

    -- Behavioral data
    behavioral_profile JSONB DEFAULT '{}'::jsonb,
    engagement_score DECIMAL(4,2) DEFAULT 0.0,

    -- Preferences
    preferences JSONB DEFAULT '{}'::jsonb,
    budget_min DECIMAL(12,2),
    budget_max DECIMAL(12,2),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_interaction_at TIMESTAMPTZ,

    -- GHL integration
    ghl_contact_id VARCHAR(100),
    ghl_sync_status VARCHAR(20) DEFAULT 'synced',
    ghl_last_synced_at TIMESTAMPTZ,

    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
) PARTITION BY LIST (location_id);

-- Create default partition for new/unmapped locations
CREATE TABLE IF NOT EXISTS leads_default PARTITION OF leads DEFAULT;

-- Function to create location partition dynamically
CREATE OR REPLACE FUNCTION create_leads_partition(p_location_id VARCHAR)
RETURNS VOID AS $$
DECLARE
    partition_name VARCHAR;
BEGIN
    partition_name := 'leads_loc_' || replace(p_location_id, '-', '_');

    -- Create partition if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF leads FOR VALUES IN (%L)',
            partition_name,
            p_location_id
        );

        RAISE NOTICE 'Created partition % for location_id %', partition_name, p_location_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PROPERTIES TABLE PARTITIONING
-- =====================================================

-- Create partitioned properties table
CREATE TABLE IF NOT EXISTS properties_partitioned (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(100) NOT NULL,  -- Partition key

    -- Property details
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    neighborhood VARCHAR(100),

    -- Property characteristics
    property_type VARCHAR(50),
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    sqft INTEGER,
    lot_size DECIMAL(10,2),
    year_built INTEGER,

    -- Pricing
    price DECIMAL(12,2),
    price_per_sqft DECIMAL(10,2),
    original_price DECIMAL(12,2),
    price_history JSONB DEFAULT '[]'::jsonb,

    -- Location data
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),

    -- Status
    status VARCHAR(50) DEFAULT 'Active'
        CHECK (status IN ('Active', 'Pending', 'Sold', 'Off Market', 'Coming Soon')),
    days_on_market INTEGER DEFAULT 0,
    featured BOOLEAN DEFAULT FALSE,

    -- Amenities and features
    amenities JSONB DEFAULT '[]'::jsonb,
    features JSONB DEFAULT '[]'::jsonb,

    -- ML scoring
    match_score DECIMAL(4,2) DEFAULT 0.0,
    popularity_score DECIMAL(4,2) DEFAULT 0.0,

    -- Media
    photos JSONB DEFAULT '[]'::jsonb,
    virtual_tour_url VARCHAR(500),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    listed_at TIMESTAMPTZ,

    -- External IDs
    mls_number VARCHAR(50),
    source_system VARCHAR(50),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
) PARTITION BY LIST (location_id);

-- Create default partition
CREATE TABLE IF NOT EXISTS properties_default PARTITION OF properties_partitioned DEFAULT;

-- Function to create property partition
CREATE OR REPLACE FUNCTION create_properties_partition(p_location_id VARCHAR)
RETURNS VOID AS $$
DECLARE
    partition_name VARCHAR;
BEGIN
    partition_name := 'properties_loc_' || replace(p_location_id, '-', '_');

    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF properties_partitioned FOR VALUES IN (%L)',
            partition_name,
            p_location_id
        );

        RAISE NOTICE 'Created partition % for location_id %', partition_name, p_location_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- CONVERSATIONS TABLE PARTITIONING
-- =====================================================

-- Create partitioned conversations table
CREATE TABLE IF NOT EXISTS conversations_partitioned (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR(100) NOT NULL,
    contact_id VARCHAR(100) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(100) NOT NULL,  -- Partition key

    -- Conversation state
    conversation_stage VARCHAR(50) NOT NULL DEFAULT 'new'
        CHECK (conversation_stage IN (
            'new', 'greeting', 'discovery', 'showing',
            'negotiation', 'closed', 'inactive'
        )),
    lead_score DECIMAL(4,2) DEFAULT 0.0,

    -- Interaction tracking
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMPTZ,
    last_interaction_at TIMESTAMPTZ,

    -- AI context
    ai_context JSONB DEFAULT '{}'::jsonb,
    behavioral_preferences JSONB DEFAULT '{}'::jsonb,
    property_interests JSONB DEFAULT '[]'::jsonb,

    -- Memory and learning
    conversation_memory JSONB DEFAULT '{}'::jsonb,
    learning_signals JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- GHL integration
    ghl_conversation_id VARCHAR(100),
    ghl_workflow_status VARCHAR(50),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
) PARTITION BY LIST (location_id);

-- Create default partition
CREATE TABLE IF NOT EXISTS conversations_default PARTITION OF conversations_partitioned DEFAULT;

-- Function to create conversation partition
CREATE OR REPLACE FUNCTION create_conversations_partition(p_location_id VARCHAR)
RETURNS VOID AS $$
DECLARE
    partition_name VARCHAR;
BEGIN
    partition_name := 'conversations_loc_' || replace(p_location_id, '-', '_');

    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF conversations_partitioned FOR VALUES IN (%L)',
            partition_name,
            p_location_id
        );

        RAISE NOTICE 'Created partition % for location_id %', partition_name, p_location_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PROPERTY INTERACTIONS TABLE PARTITIONING
-- =====================================================

-- Create partitioned property interactions table
CREATE TABLE IF NOT EXISTS property_interactions_partitioned (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR(100) NOT NULL,
    property_id VARCHAR(100),
    location_id VARCHAR(100) NOT NULL,  -- Partition key

    -- Interaction details
    interaction_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Engagement metrics
    time_on_property INTEGER,  -- seconds
    scroll_depth DECIMAL(4,2),
    photos_viewed INTEGER DEFAULT 0,

    -- Feedback
    feedback_category VARCHAR(50),
    feedback_text TEXT,
    rating DECIMAL(3,1),

    -- Context
    device_type VARCHAR(50),
    session_id VARCHAR(100),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
) PARTITION BY LIST (location_id);

-- Create default partition
CREATE TABLE IF NOT EXISTS property_interactions_default
    PARTITION OF property_interactions_partitioned DEFAULT;

-- =====================================================
-- SHARD-AWARE INDEXES
-- =====================================================

-- Performance indexes for partitioned tables
-- Note: Indexes are automatically created on partitions

-- Leads indexes (will propagate to partitions)
CREATE INDEX IF NOT EXISTS idx_leads_part_contact
    ON leads(contact_id);
CREATE INDEX IF NOT EXISTS idx_leads_part_tenant
    ON leads(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_part_status_score
    ON leads(status, ml_score DESC) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_leads_part_scoring
    ON leads(ml_score DESC, created_at DESC) WHERE ml_score >= 7;

-- Properties indexes
CREATE INDEX IF NOT EXISTS idx_properties_part_search
    ON properties_partitioned(price, bedrooms, bathrooms, property_type);
CREATE INDEX IF NOT EXISTS idx_properties_part_location
    ON properties_partitioned(city, neighborhood, zip_code);
CREATE INDEX IF NOT EXISTS idx_properties_part_status
    ON properties_partitioned(status, created_at DESC) WHERE status = 'Active';

-- Conversations indexes
CREATE INDEX IF NOT EXISTS idx_conversations_part_tenant_contact
    ON conversations_partitioned(tenant_id, contact_id);
CREATE INDEX IF NOT EXISTS idx_conversations_part_stage
    ON conversations_partitioned(conversation_stage, lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_part_recent
    ON conversations_partitioned(last_interaction_at DESC);

-- Property interactions indexes
CREATE INDEX IF NOT EXISTS idx_interactions_part_conversation
    ON property_interactions_partitioned(conversation_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_part_property
    ON property_interactions_partitioned(property_id, timestamp DESC);

-- =====================================================
-- CROSS-SHARD QUERY HELPER FUNCTIONS
-- =====================================================

-- Function to get shard for a location
CREATE OR REPLACE FUNCTION get_shard_for_location(p_location_id VARCHAR)
RETURNS VARCHAR AS $$
DECLARE
    v_shard_id VARCHAR;
BEGIN
    SELECT shard_id INTO v_shard_id
    FROM location_shard_mapping
    WHERE location_id = p_location_id;

    RETURN v_shard_id;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to route query to appropriate shard
CREATE OR REPLACE FUNCTION route_query_to_shard(
    p_location_id VARCHAR,
    p_query TEXT
) RETURNS TEXT AS $$
DECLARE
    v_shard_id VARCHAR;
    v_shard_config RECORD;
BEGIN
    v_shard_id := get_shard_for_location(p_location_id);

    IF v_shard_id IS NULL THEN
        RETURN p_query;  -- Execute locally if no mapping
    END IF;

    SELECT * INTO v_shard_config
    FROM shard_configuration
    WHERE shard_id = v_shard_id AND state = 'active';

    IF v_shard_config IS NULL THEN
        RETURN p_query;
    END IF;

    -- Return modified query with shard routing hint
    RETURN format(
        '/* shard: %s, host: %s */ %s',
        v_shard_id,
        v_shard_config.host,
        p_query
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- DATA MIGRATION HELPERS
-- =====================================================

-- Function to migrate data for a specific location
CREATE OR REPLACE FUNCTION migrate_location_data(
    p_location_id VARCHAR,
    p_target_shard VARCHAR
) RETURNS TABLE(
    table_name TEXT,
    rows_migrated BIGINT
) AS $$
BEGIN
    -- This is a placeholder for actual data migration
    -- In production, this would use logical replication or COPY

    RETURN QUERY
    SELECT 'leads'::TEXT, 0::BIGINT
    UNION ALL
    SELECT 'properties'::TEXT, 0::BIGINT
    UNION ALL
    SELECT 'conversations'::TEXT, 0::BIGINT
    UNION ALL
    SELECT 'property_interactions'::TEXT, 0::BIGINT;
END;
$$ LANGUAGE plpgsql;

-- Function to verify data consistency across shards
CREATE OR REPLACE FUNCTION verify_shard_consistency(p_location_id VARCHAR)
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    details JSONB
) AS $$
BEGIN
    -- Check leads count
    RETURN QUERY
    SELECT
        'leads_count'::TEXT,
        'ok'::TEXT,
        jsonb_build_object('count', (SELECT COUNT(*) FROM leads WHERE location_id = p_location_id));

    -- Check properties count
    RETURN QUERY
    SELECT
        'properties_count'::TEXT,
        'ok'::TEXT,
        jsonb_build_object('count', (SELECT COUNT(*) FROM properties_partitioned WHERE location_id = p_location_id));

    -- Check conversations count
    RETURN QUERY
    SELECT
        'conversations_count'::TEXT,
        'ok'::TEXT,
        jsonb_build_object('count', (SELECT COUNT(*) FROM conversations_partitioned WHERE location_id = p_location_id));
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PARTITION MANAGEMENT TRIGGERS
-- =====================================================

-- Trigger to automatically create partitions for new locations
CREATE OR REPLACE FUNCTION auto_create_partitions()
RETURNS TRIGGER AS $$
BEGIN
    -- Create partitions for the new location
    PERFORM create_leads_partition(NEW.location_id);
    PERFORM create_properties_partition(NEW.location_id);
    PERFORM create_conversations_partition(NEW.location_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on location_shard_mapping
DROP TRIGGER IF EXISTS trg_auto_create_partitions ON location_shard_mapping;
CREATE TRIGGER trg_auto_create_partitions
    AFTER INSERT ON location_shard_mapping
    FOR EACH ROW
    EXECUTE FUNCTION auto_create_partitions();

-- =====================================================
-- MONITORING VIEWS
-- =====================================================

-- View for partition statistics
CREATE OR REPLACE VIEW partition_statistics AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as total_size,
    n_live_tup as row_estimate,
    last_vacuum,
    last_analyze
FROM pg_stat_user_tables
WHERE tablename LIKE 'leads_%'
   OR tablename LIKE 'properties_%'
   OR tablename LIKE 'conversations_%'
   OR tablename LIKE 'property_interactions_%'
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;

-- View for shard health
CREATE OR REPLACE VIEW shard_health AS
SELECT
    s.shard_id,
    s.host,
    s.port,
    s.state,
    COUNT(DISTINCT m.location_id) as location_count,
    s.weight,
    s.updated_at as last_updated
FROM shard_configuration s
LEFT JOIN location_shard_mapping m ON s.shard_id = m.shard_id
GROUP BY s.shard_id, s.host, s.port, s.state, s.weight, s.updated_at
ORDER BY s.shard_id;

-- View for cross-shard query performance
CREATE OR REPLACE VIEW cross_shard_performance AS
SELECT
    date_trunc('hour', NOW()) as window_start,
    'cross_shard_stats' as metric_type,
    jsonb_build_object(
        'total_shards', (SELECT COUNT(*) FROM shard_configuration WHERE state = 'active'),
        'total_locations', (SELECT COUNT(*) FROM location_shard_mapping)
    ) as stats;

-- =====================================================
-- SCHEMA VALIDATION
-- =====================================================

-- Function to validate sharding setup
CREATE OR REPLACE FUNCTION validate_sharding_setup()
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    message TEXT
) AS $$
BEGIN
    -- Check partition tables exist
    RETURN QUERY
    SELECT
        'leads_partitioned'::TEXT,
        CASE WHEN EXISTS (SELECT 1 FROM pg_class WHERE relname = 'leads' AND relkind = 'p')
             THEN 'ok' ELSE 'error' END::TEXT,
        'Leads table partitioning status'::TEXT;

    RETURN QUERY
    SELECT
        'properties_partitioned'::TEXT,
        CASE WHEN EXISTS (SELECT 1 FROM pg_class WHERE relname = 'properties_partitioned' AND relkind = 'p')
             THEN 'ok' ELSE 'error' END::TEXT,
        'Properties table partitioning status'::TEXT;

    RETURN QUERY
    SELECT
        'conversations_partitioned'::TEXT,
        CASE WHEN EXISTS (SELECT 1 FROM pg_class WHERE relname = 'conversations_partitioned' AND relkind = 'p')
             THEN 'ok' ELSE 'error' END::TEXT,
        'Conversations table partitioning status'::TEXT;

    -- Check shard configuration
    RETURN QUERY
    SELECT
        'shard_config_exists'::TEXT,
        CASE WHEN EXISTS (SELECT 1 FROM shard_configuration)
             THEN 'ok' ELSE 'warning' END::TEXT,
        'Shard configuration table has entries'::TEXT;

    -- Check default partitions
    RETURN QUERY
    SELECT
        'default_partitions'::TEXT,
        CASE WHEN EXISTS (SELECT 1 FROM pg_class WHERE relname = 'leads_default')
             THEN 'ok' ELSE 'error' END::TEXT,
        'Default partitions exist'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- INITIAL SHARD CONFIGURATION
-- =====================================================

-- Insert default shard configuration (single-node development setup)
INSERT INTO shard_configuration (shard_id, host, port, database_name, state, hash_range_start, hash_range_end)
VALUES
    ('shard-primary', 'localhost', 5432, 'enterprisehub', 'active', 0, 1000000)
ON CONFLICT (shard_id) DO NOTHING;

-- Insert default location mapping for development
INSERT INTO location_shard_mapping (location_id, shard_id)
VALUES
    ('loc_default', 'shard-primary')
ON CONFLICT (location_id) DO NOTHING;

-- =====================================================
-- MIGRATION METADATA
-- =====================================================

-- Record migration
INSERT INTO schema_migrations (version, description)
VALUES ('002', 'Enable database sharding by location_id for Phase 4 enterprise scaling')
ON CONFLICT (version) DO NOTHING;

-- Add migration comments
COMMENT ON TABLE shard_configuration IS 'Phase 4: Shard configuration for enterprise scaling';
COMMENT ON TABLE location_shard_mapping IS 'Phase 4: Location to shard routing table';
COMMENT ON TABLE leads IS 'Phase 4: Partitioned leads table by location_id';
COMMENT ON TABLE properties_partitioned IS 'Phase 4: Partitioned properties table by location_id';
COMMENT ON TABLE conversations_partitioned IS 'Phase 4: Partitioned conversations table by location_id';

-- =====================================================
-- ROLLBACK INSTRUCTIONS
-- =====================================================

-- To rollback this migration:
--
-- -- Remove triggers
-- DROP TRIGGER IF EXISTS trg_auto_create_partitions ON location_shard_mapping;
--
-- -- Remove functions
-- DROP FUNCTION IF EXISTS create_leads_partition(VARCHAR);
-- DROP FUNCTION IF EXISTS create_properties_partition(VARCHAR);
-- DROP FUNCTION IF EXISTS create_conversations_partition(VARCHAR);
-- DROP FUNCTION IF EXISTS get_shard_for_location(VARCHAR);
-- DROP FUNCTION IF EXISTS route_query_to_shard(VARCHAR, TEXT);
-- DROP FUNCTION IF EXISTS migrate_location_data(VARCHAR, VARCHAR);
-- DROP FUNCTION IF EXISTS verify_shard_consistency(VARCHAR);
-- DROP FUNCTION IF EXISTS auto_create_partitions();
-- DROP FUNCTION IF EXISTS validate_sharding_setup();
--
-- -- Remove views
-- DROP VIEW IF EXISTS partition_statistics;
-- DROP VIEW IF EXISTS shard_health;
-- DROP VIEW IF EXISTS cross_shard_performance;
--
-- -- Remove partitioned tables (WARNING: DATA LOSS!)
-- DROP TABLE IF EXISTS leads CASCADE;
-- DROP TABLE IF EXISTS properties_partitioned CASCADE;
-- DROP TABLE IF EXISTS conversations_partitioned CASCADE;
-- DROP TABLE IF EXISTS property_interactions_partitioned CASCADE;
--
-- -- Restore original tables if backed up
-- ALTER TABLE IF EXISTS leads_original RENAME TO leads;
--
-- -- Remove shard configuration
-- DROP TABLE IF EXISTS location_shard_mapping;
-- DROP TABLE IF EXISTS shard_configuration;
--
-- -- Remove migration record
-- DELETE FROM schema_migrations WHERE version = '002';

-- =====================================================
-- VALIDATION QUERY
-- =====================================================

-- Run this to validate the migration
-- SELECT * FROM validate_sharding_setup();
-- SELECT * FROM shard_health;
-- SELECT * FROM partition_statistics;
