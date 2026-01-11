-- Performance Optimization Indexes Migration
-- Phase 2 Performance Foundation - Week 3 Quick Wins
-- Target: <50ms P90 query performance
--
-- Migration Version: 001
-- Created: 2026-01-10
-- Purpose: Add high-performance indexes for lead and property queries

-- =====================================================
-- LEADS TABLE PERFORMANCE INDEXES
-- =====================================================

-- High-performance composite index for active lead queries
-- Optimizes: SELECT * FROM leads WHERE status = 'active' ORDER BY created_at DESC, ml_score DESC
-- Target: <50ms for 95% of queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_created_scored
    ON leads(created_at DESC, ml_score DESC)
    WHERE status = 'active';

-- Covering index for lead scoring queries with frequently accessed columns
-- Optimizes: Lead dashboard and scoring queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_score_status_created
    ON leads(ml_score DESC, status, created_at DESC)
    INCLUDE (contact_id, name, email, phone);

-- Partial index for hot leads (high-value queries)
-- Optimizes: Hot lead filtering and prioritization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_hot_leads
    ON leads(ml_score DESC, created_at DESC)
    WHERE status = 'active' AND ml_score >= 7;

-- Text search index for lead search functionality
-- Optimizes: Full-text search across lead name, email, phone
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_search_gin
    ON leads USING GIN(to_tsvector('english',
        COALESCE(name, '') || ' ' ||
        COALESCE(email, '') || ' ' ||
        COALESCE(phone, '')
    ));

-- Status and timestamp composite for status-based queries
-- Optimizes: Status filtering with time-based ordering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_status_updated
    ON leads(status, updated_at DESC)
    WHERE status IN ('active', 'qualified', 'contacted');

-- =====================================================
-- PROPERTIES TABLE PERFORMANCE INDEXES
-- =====================================================

-- GiST spatial index for location-based property searches
-- Optimizes: Geographic proximity searches with price filtering
-- Note: Requires PostGIS extension
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_location_price
    ON properties USING GiST (
        ST_MakePoint(longitude, latitude),
        price_range
    )
    WHERE status = 'Active';

-- Alternative B-tree index if PostGIS is not available
-- Optimizes: Location-based queries without spatial functions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_location_btree
    ON properties(latitude, longitude, price)
    WHERE status = 'Active' AND latitude IS NOT NULL AND longitude IS NOT NULL;

-- Composite index for common property search patterns
-- Optimizes: Price + bedrooms + bathrooms filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_search_common
    ON properties(price, bedrooms, bathrooms, property_type, status)
    WHERE status = 'Active';

-- Covering index for property listing pages
-- Includes frequently accessed columns for index-only scans
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_listing_page
    ON properties(created_at DESC, price)
    INCLUDE (address, bedrooms, bathrooms, sqft, property_type, neighborhood)
    WHERE status = 'Active';

-- Partial index for featured/premium properties
-- Optimizes: High-priority property queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_featured
    ON properties(created_at DESC, price)
    WHERE status = 'Active' AND featured = true;

-- GIN index for JSONB amenities search
-- Optimizes: Amenity-based filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_amenities_gin
    ON properties USING GIN(amenities)
    WHERE amenities IS NOT NULL;

-- Neighborhood and city lookup optimization
-- Optimizes: Location-based aggregations and filters
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_properties_location_text
    ON properties(city, neighborhood, zip_code, status)
    WHERE status = 'Active';

-- =====================================================
-- CONVERSATIONS TABLE PERFORMANCE INDEXES
-- =====================================================

-- Optimize conversation lookup by tenant and contact
-- Already exists in schema.sql, but adding INCLUDE for covering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_tenant_contact_enhanced
    ON conversations(tenant_id, contact_id)
    INCLUDE (conversation_stage, lead_score, last_interaction_at);

-- Recent conversations with high lead scores
-- Optimizes: Dashboard queries for high-value recent conversations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_recent_high_score
    ON conversations(tenant_id, last_interaction_at DESC, lead_score DESC)
    WHERE lead_score >= 5 AND conversation_stage NOT IN ('closed', 'inactive');

-- =====================================================
-- PROPERTY INTERACTIONS TABLE PERFORMANCE INDEXES
-- =====================================================

-- Optimize property interaction analysis
-- Supports behavioral learning queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_interactions_analysis
    ON property_interactions(conversation_id, interaction_type, timestamp DESC)
    INCLUDE (property_id, time_on_property, feedback_category);

-- Property engagement metrics
-- Optimizes: Property popularity and engagement analytics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_interactions_popularity
    ON property_interactions(property_id, interaction_type, timestamp DESC)
    WHERE property_id IS NOT NULL;

-- =====================================================
-- ANALYTICS AND PERFORMANCE MONITORING
-- =====================================================

-- Create statistics for query planner optimization
-- Ensures accurate query plans for new indexes
ANALYZE leads;
ANALYZE properties;
ANALYZE conversations;
ANALYZE property_interactions;

-- =====================================================
-- INDEX VALIDATION AND METRICS
-- =====================================================

-- Query to validate index creation and size
-- Run this after migration to verify indexes
CREATE OR REPLACE FUNCTION validate_performance_indexes()
RETURNS TABLE(
    index_name TEXT,
    table_name TEXT,
    index_size TEXT,
    index_valid BOOLEAN,
    index_usage_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.indexrelname::TEXT as index_name,
        t.relname::TEXT as table_name,
        pg_size_pretty(pg_relation_size(i.indexrelid)) as index_size,
        idx.indisvalid as index_valid,
        COALESCE(s.idx_scan, 0) as index_usage_count
    FROM pg_index idx
    JOIN pg_class i ON i.oid = idx.indexrelid
    JOIN pg_class t ON t.oid = idx.indrelid
    LEFT JOIN pg_stat_user_indexes s ON s.indexrelid = i.oid
    WHERE i.indexrelname LIKE 'idx_leads_%'
       OR i.indexrelname LIKE 'idx_properties_%'
       OR i.indexrelname LIKE 'idx_conversations_%'
       OR i.indexrelname LIKE 'idx_property_interactions_%'
    ORDER BY table_name, index_name;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- QUERY PERFORMANCE VALIDATION
-- =====================================================

-- Example queries to test index performance
-- Run with EXPLAIN ANALYZE to verify <50ms target

-- Test 1: Active leads with scoring
-- EXPLAIN ANALYZE
-- SELECT * FROM leads
-- WHERE status = 'active'
-- ORDER BY created_at DESC, ml_score DESC
-- LIMIT 50;

-- Test 2: Property location search
-- EXPLAIN ANALYZE
-- SELECT * FROM properties
-- WHERE status = 'Active'
--   AND price BETWEEN 300000 AND 500000
--   AND bedrooms >= 3
-- ORDER BY created_at DESC
-- LIMIT 20;

-- Test 3: Hot leads for dashboard
-- EXPLAIN ANALYZE
-- SELECT * FROM leads
-- WHERE status = 'active' AND ml_score >= 7
-- ORDER BY ml_score DESC, created_at DESC
-- LIMIT 25;

-- =====================================================
-- MIGRATION METADATA
-- =====================================================

-- Record migration in schema_migrations table
INSERT INTO schema_migrations (version, description)
VALUES ('001', 'Performance indexes for <50ms P90 query performance')
ON CONFLICT (version) DO NOTHING;

-- Performance Index Summary
COMMENT ON INDEX idx_leads_created_scored IS 'Phase 2 Week 3: High-performance composite index for active lead queries - Target <50ms P90';
COMMENT ON INDEX idx_properties_location_price IS 'Phase 2 Week 3: GiST spatial index for location-based searches - Target <50ms P90';
COMMENT ON INDEX idx_leads_hot_leads IS 'Phase 2 Week 3: Partial index for high-value lead queries - Target <30ms P90';
COMMENT ON INDEX idx_properties_search_common IS 'Phase 2 Week 3: Composite index for common property search patterns - Target <50ms P90';

-- =====================================================
-- ROLLBACK INSTRUCTIONS
-- =====================================================

-- To rollback this migration:
-- DROP INDEX CONCURRENTLY IF EXISTS idx_leads_created_scored;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_leads_score_status_created;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_leads_hot_leads;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_leads_search_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_leads_status_updated;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_properties_location_price;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_properties_location_btree;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_properties_search_common;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_properties_listing_page;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_properties_featured;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_properties_amenities_gin;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_properties_location_text;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_conversations_tenant_contact_enhanced;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_conversations_recent_high_score;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_property_interactions_analysis;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_property_interactions_popularity;
-- DROP FUNCTION IF EXISTS validate_performance_indexes();
-- DELETE FROM schema_migrations WHERE version = '001';
