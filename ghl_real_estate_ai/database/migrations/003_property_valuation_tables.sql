-- =====================================================================
-- Property Valuation System Database Migration
-- Migration: 003_property_valuation_tables.sql
-- Created: January 10, 2026
-- Purpose: Add comprehensive property valuation system tables
--
-- Tables Created:
-- - properties: Core property data
-- - property_valuations: Valuation results and analytics
-- - marketing_campaigns: Marketing campaign management
-- - document_packages: Document generation and e-signature
-- - seller_analytics_daily: Performance analytics (materialized view)
-- =====================================================================

BEGIN;

-- =====================================================================
-- 1. PROPERTIES TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Property identification
    mls_number VARCHAR(100) UNIQUE,
    parcel_number VARCHAR(100),

    -- Property location
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state CHAR(2) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    county VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    neighborhood VARCHAR(200),
    school_district VARCHAR(200),

    -- Property classification
    property_type VARCHAR(50) NOT NULL CHECK (property_type IN (
        'single_family', 'condo', 'townhouse', 'multi_family',
        'land', 'commercial', 'investment'
    )),

    -- Property features
    bedrooms INTEGER,
    bathrooms DECIMAL(3, 1),
    square_footage INTEGER,
    lot_size_acres DECIMAL(10, 4),
    year_built INTEGER,
    garage_spaces INTEGER,
    stories INTEGER,

    -- Additional features (JSONB for flexible storage)
    features JSONB DEFAULT '{}',
    amenities TEXT[],

    -- Property condition
    condition VARCHAR(50) CHECK (condition IN (
        'excellent', 'good', 'fair', 'poor', 'needs_repair'
    )),
    recent_renovations TEXT[],

    -- Financial information
    list_price DECIMAL(12, 2),
    tax_assessed_value DECIMAL(12, 2),
    annual_property_taxes DECIMAL(10, 2),
    monthly_hoa_fees DECIMAL(8, 2),

    -- Property description
    description TEXT,
    photos TEXT[], -- Array of photo URLs

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID, -- Reference to users table

    -- Indexes for performance
    CONSTRAINT valid_coordinates CHECK (
        (latitude IS NULL AND longitude IS NULL) OR
        (latitude IS NOT NULL AND longitude IS NOT NULL)
    ),
    CONSTRAINT valid_features CHECK (
        bedrooms IS NULL OR bedrooms >= 0,
        bathrooms IS NULL OR bathrooms >= 0,
        square_footage IS NULL OR square_footage > 0,
        lot_size_acres IS NULL OR lot_size_acres >= 0,
        year_built IS NULL OR (year_built >= 1800 AND year_built <= 2030),
        garage_spaces IS NULL OR garage_spaces >= 0
    )
);

-- Properties indexes
CREATE INDEX IF NOT EXISTS idx_properties_location ON properties (city, state, zip_code);
CREATE INDEX IF NOT EXISTS idx_properties_type ON properties (property_type);
CREATE INDEX IF NOT EXISTS idx_properties_price_range ON properties (list_price);
CREATE INDEX IF NOT EXISTS idx_properties_coordinates ON properties (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_properties_features ON properties
    USING gin(features) WHERE features IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_properties_created_at ON properties (created_at);

-- =====================================================================
-- 2. PROPERTY VALUATIONS TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS property_valuations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    seller_id UUID, -- Reference to sellers/contacts

    -- Valuation results
    estimated_value DECIMAL(12, 2) NOT NULL,
    value_range_low DECIMAL(12, 2) NOT NULL,
    value_range_high DECIMAL(12, 2) NOT NULL,
    confidence_score DECIMAL(5, 4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Valuation methodology
    valuation_method VARCHAR(100) DEFAULT 'comprehensive',
    data_sources TEXT[] NOT NULL,

    -- MLS data integration
    mls_comparable_sales JSONB,
    mls_data_source VARCHAR(100),
    mls_data_fetched_at TIMESTAMP,

    -- ML prediction data
    ml_prediction_value DECIMAL(12, 2),
    ml_model_version VARCHAR(50),
    ml_confidence_score DECIMAL(5, 4),
    ml_feature_importance JSONB,

    -- Third-party estimates
    zillow_estimate DECIMAL(12, 2),
    redfin_estimate DECIMAL(12, 2),
    estimates_fetched_at TIMESTAMP,

    -- Claude AI insights
    claude_insights JSONB,
    claude_processing_time_ms INTEGER,

    -- CMA report
    cma_report_url TEXT,
    cma_generated_at TIMESTAMP,

    -- Performance tracking
    total_processing_time_ms INTEGER,
    api_response_time_ms INTEGER,

    -- Valuation status and metadata
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN (
        'pending', 'in_progress', 'completed', 'failed', 'expired'
    )),
    requested_by UUID, -- Reference to users
    request_context JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP, -- Cache expiration

    -- Business logic constraints
    CONSTRAINT valid_value_range CHECK (value_range_low <= estimated_value AND estimated_value <= value_range_high),
    CONSTRAINT valid_processing_time CHECK (total_processing_time_ms > 0),
    CONSTRAINT valid_expiration CHECK (expires_at IS NULL OR expires_at > created_at)
);

-- Property valuations indexes
CREATE INDEX IF NOT EXISTS idx_property_valuations_property_id ON property_valuations (property_id);
CREATE INDEX IF NOT EXISTS idx_property_valuations_seller_id ON property_valuations (seller_id)
    WHERE seller_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_property_valuations_created_at ON property_valuations (created_at);
CREATE INDEX IF NOT EXISTS idx_property_valuations_status ON property_valuations (status);
CREATE INDEX IF NOT EXISTS idx_property_valuations_expires_at ON property_valuations (expires_at)
    WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_property_valuations_confidence ON property_valuations (confidence_score);

-- Performance index for analytics queries
CREATE INDEX IF NOT EXISTS idx_property_valuations_analytics ON property_valuations
    (created_at, confidence_score, total_processing_time_ms)
    WHERE status = 'completed';

-- =====================================================================
-- 3. MARKETING CAMPAIGNS TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    seller_id UUID, -- Reference to sellers/contacts

    -- Campaign metadata
    campaign_name VARCHAR(200) NOT NULL,
    campaign_type VARCHAR(50) NOT NULL CHECK (campaign_type IN (
        'standard', 'luxury', 'quick_sale', 'investment', 'new_construction'
    )),
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'active', 'paused', 'completed', 'cancelled'
    )),

    -- Campaign content
    listing_content JSONB NOT NULL, -- descriptions, headlines, etc.
    visual_assets JSONB, -- images, videos, virtual tours
    content_generated_by VARCHAR(50) DEFAULT 'claude_ai',

    -- Publishing channels
    mls_listing_id VARCHAR(100),
    zillow_listing_id VARCHAR(100),
    realtor_com_listing_id VARCHAR(100),

    -- Email marketing integration
    ghl_campaign_id VARCHAR(100),
    email_sequence_status VARCHAR(50),
    email_open_rate DECIMAL(5, 4),
    email_click_rate DECIMAL(5, 4),

    -- Social media integration
    facebook_post_ids JSONB,
    instagram_post_ids JSONB,
    linkedin_post_ids JSONB,
    social_engagement_metrics JSONB,

    -- Performance metrics
    total_views INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_leads INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5, 4),
    cost_per_lead DECIMAL(8, 2),

    -- Campaign optimization
    ab_test_variants JSONB,
    optimization_settings JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_updated TIMESTAMP DEFAULT NOW(),

    -- Analytics tracking
    analytics_last_updated TIMESTAMP,
    roi_calculated DECIMAL(10, 2),

    CONSTRAINT valid_metrics CHECK (
        total_views >= 0 AND total_clicks >= 0 AND total_leads >= 0
    ),
    CONSTRAINT valid_engagement CHECK (
        engagement_rate IS NULL OR (engagement_rate >= 0 AND engagement_rate <= 1)
    ),
    CONSTRAINT valid_email_rates CHECK (
        (email_open_rate IS NULL OR (email_open_rate >= 0 AND email_open_rate <= 1)) AND
        (email_click_rate IS NULL OR (email_click_rate >= 0 AND email_click_rate <= 1))
    )
);

-- Marketing campaigns indexes
CREATE INDEX IF NOT EXISTS idx_marketing_campaigns_property_id ON marketing_campaigns (property_id);
CREATE INDEX IF NOT EXISTS idx_marketing_campaigns_seller_id ON marketing_campaigns (seller_id)
    WHERE seller_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_marketing_campaigns_status ON marketing_campaigns (status);
CREATE INDEX IF NOT EXISTS idx_marketing_campaigns_type ON marketing_campaigns (campaign_type);
CREATE INDEX IF NOT EXISTS idx_marketing_campaigns_created_at ON marketing_campaigns (created_at);
CREATE INDEX IF NOT EXISTS idx_marketing_campaigns_performance ON marketing_campaigns
    (total_views, total_clicks, total_leads) WHERE status = 'active';

-- =====================================================================
-- 4. DOCUMENT PACKAGES TABLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS document_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID, -- Reference to sellers/contacts
    property_id UUID REFERENCES properties(id) ON DELETE SET NULL,

    -- Package metadata
    package_name VARCHAR(200) NOT NULL,
    package_type VARCHAR(50) NOT NULL CHECK (package_type IN (
        'listing_agreement', 'purchase_contract', 'disclosure_package',
        'closing_documents', 'marketing_materials', 'cma_report'
    )),
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'ready', 'sent', 'partially_signed', 'fully_signed',
        'completed', 'cancelled', 'expired'
    )),

    -- Documents in package
    documents JSONB NOT NULL, -- Array of document objects
    document_templates_used TEXT[], -- Template references

    -- E-signature integration
    docusign_envelope_id VARCHAR(100) UNIQUE,
    hellosign_signature_request_id VARCHAR(100) UNIQUE,
    esignature_provider VARCHAR(50) CHECK (esignature_provider IN (
        'docusign', 'hellosign', 'adobe_sign', 'pandadoc'
    )),
    signature_status VARCHAR(50),

    -- Signers and workflow
    required_signers JSONB NOT NULL,
    completed_signers JSONB DEFAULT '[]',
    signature_order INTEGER[] DEFAULT '{1}',

    -- Legal compliance
    jurisdiction VARCHAR(100) NOT NULL,
    compliance_validation JSONB,
    legal_review_required BOOLEAN DEFAULT false,
    legal_review_completed_at TIMESTAMP,

    -- Document security
    access_control JSONB DEFAULT '{}',
    audit_trail JSONB DEFAULT '[]',
    encryption_enabled BOOLEAN DEFAULT true,

    -- Timestamps and deadlines
    created_at TIMESTAMP DEFAULT NOW(),
    sent_for_signature_at TIMESTAMP,
    fully_signed_at TIMESTAMP,
    deadline TIMESTAMP,
    last_reminder_sent TIMESTAMP,

    -- Performance tracking
    generation_time_ms INTEGER,
    delivery_time_ms INTEGER,
    first_signature_time_hours INTEGER,

    CONSTRAINT valid_deadline CHECK (deadline IS NULL OR deadline > created_at),
    CONSTRAINT valid_signature_timing CHECK (
        sent_for_signature_at IS NULL OR sent_for_signature_at >= created_at
    )
);

-- Document packages indexes
CREATE INDEX IF NOT EXISTS idx_document_packages_seller_id ON document_packages (seller_id)
    WHERE seller_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_document_packages_property_id ON document_packages (property_id)
    WHERE property_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_document_packages_status ON document_packages (status);
CREATE INDEX IF NOT EXISTS idx_document_packages_type ON document_packages (package_type);
CREATE INDEX IF NOT EXISTS idx_document_packages_deadline ON document_packages (deadline)
    WHERE deadline IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_document_packages_esignature ON document_packages
    (esignature_provider, signature_status) WHERE esignature_provider IS NOT NULL;

-- =====================================================================
-- 5. SELLER ANALYTICS MATERIALIZED VIEW
-- =====================================================================

-- First, create a function to refresh analytics
CREATE OR REPLACE FUNCTION refresh_seller_analytics_daily()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY seller_analytics_daily;
END;
$$ LANGUAGE plpgsql;

-- Create materialized view for performance analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS seller_analytics_daily AS
SELECT
    DATE(pv.created_at) as analysis_date,

    -- Valuation metrics
    COUNT(DISTINCT pv.id) as total_valuations,
    COUNT(DISTINCT pv.property_id) as unique_properties_valued,
    AVG(pv.total_processing_time_ms) as avg_processing_time_ms,
    AVG(pv.confidence_score) as avg_confidence_score,
    AVG(pv.estimated_value) as avg_property_value,

    -- Performance by confidence level
    COUNT(CASE WHEN pv.confidence_score >= 0.9 THEN 1 END) as high_confidence_valuations,
    COUNT(CASE WHEN pv.confidence_score BETWEEN 0.7 AND 0.89 THEN 1 END) as medium_confidence_valuations,
    COUNT(CASE WHEN pv.confidence_score < 0.7 THEN 1 END) as low_confidence_valuations,

    -- Geographic distribution
    COUNT(DISTINCT CONCAT(p.city, ', ', p.state)) as unique_markets_served,

    -- Data source utilization
    SUM(CASE WHEN 'mls_comparables' = ANY(pv.data_sources) THEN 1 ELSE 0 END) as mls_data_usage,
    SUM(CASE WHEN 'ml_prediction' = ANY(pv.data_sources) THEN 1 ELSE 0 END) as ml_prediction_usage,
    SUM(CASE WHEN 'claude_ai' = ANY(pv.data_sources) THEN 1 ELSE 0 END) as claude_insights_usage,

    -- Marketing campaign metrics
    COUNT(DISTINCT mc.id) as campaigns_created,
    COUNT(DISTINCT CASE WHEN mc.status = 'active' THEN mc.id END) as active_campaigns,
    AVG(mc.total_leads) as avg_leads_per_campaign,
    AVG(mc.engagement_rate) as avg_campaign_engagement,

    -- Document package metrics
    COUNT(DISTINCT dp.id) as document_packages_created,
    COUNT(DISTINCT CASE WHEN dp.status = 'fully_signed' THEN dp.id END) as packages_fully_signed,
    AVG(dp.generation_time_ms) as avg_document_generation_time_ms,

    -- Business impact calculations
    SUM(pv.estimated_value) FILTER (WHERE pv.status = 'completed') as total_estimated_value,
    COUNT(DISTINCT pv.seller_id) FILTER (WHERE pv.seller_id IS NOT NULL) as unique_sellers_served

FROM property_valuations pv
LEFT JOIN properties p ON pv.property_id = p.id
LEFT JOIN marketing_campaigns mc ON pv.property_id = mc.property_id
    AND DATE(mc.created_at) = DATE(pv.created_at)
LEFT JOIN document_packages dp ON pv.property_id = dp.property_id
    AND DATE(dp.created_at) = DATE(pv.created_at)
WHERE pv.created_at >= CURRENT_DATE - INTERVAL '90 days' -- Last 90 days
GROUP BY DATE(pv.created_at)
ORDER BY analysis_date DESC;

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_seller_analytics_daily_date
    ON seller_analytics_daily (analysis_date);

-- =====================================================================
-- 6. PERFORMANCE MONITORING TRIGGERS
-- =====================================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_properties_updated_at
    BEFORE UPDATE ON properties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_property_valuations_updated_at
    BEFORE UPDATE ON property_valuations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_marketing_campaigns_updated_at
    BEFORE UPDATE ON marketing_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- 7. SAMPLE DATA FOR DEVELOPMENT/TESTING
-- =====================================================================

-- Insert sample property (only in development)
-- This can be removed in production
INSERT INTO properties (
    id, address, city, state, zip_code, property_type,
    bedrooms, bathrooms, square_footage, year_built,
    list_price, features
) VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    '123 Sample Street', 'San Francisco', 'CA', '94105', 'single_family',
    3, 2.5, 2000, 2010,
    850000.00, '{"has_pool": false, "has_fireplace": true, "has_ac": true}'
) ON CONFLICT (id) DO NOTHING;

-- Insert sample property valuation
INSERT INTO property_valuations (
    property_id, estimated_value, value_range_low, value_range_high,
    confidence_score, data_sources, valuation_method, status
) VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    850000.00, 765000.00, 935000.00,
    0.85, ARRAY['mls_comparables', 'ml_prediction', 'claude_ai'],
    'comprehensive', 'completed'
) ON CONFLICT DO NOTHING;

-- =====================================================================
-- 8. PERFORMANCE OPTIMIZATION
-- =====================================================================

-- Enable parallel processing for analytics
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;

-- Optimize for property valuation workload
ALTER SYSTEM SET effective_cache_size = '4GB';
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET work_mem = '256MB';

-- Enable query performance insights
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- =====================================================================
-- 9. SECURITY AND ACCESS CONTROL
-- =====================================================================

-- Row Level Security (RLS) for multi-tenant data
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_valuations ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketing_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_packages ENABLE ROW LEVEL SECURITY;

-- Sample RLS policies (customize based on your authentication system)
-- These would be expanded with actual user/role logic

-- Properties access policy
CREATE POLICY properties_access_policy ON properties
    FOR ALL USING (
        -- Allow access if user created the property or is assigned to it
        created_by = current_setting('app.current_user_id')::uuid OR
        -- Add additional access logic based on your auth system
        true -- Placeholder - replace with actual access logic
    );

-- Property valuations access policy
CREATE POLICY property_valuations_access_policy ON property_valuations
    FOR ALL USING (
        -- Allow access if user requested the valuation or owns the property
        requested_by = current_setting('app.current_user_id')::uuid OR
        EXISTS (
            SELECT 1 FROM properties p
            WHERE p.id = property_valuations.property_id
            AND p.created_by = current_setting('app.current_user_id')::uuid
        )
    );

-- =====================================================================
-- 10. MONITORING AND ALERTING SETUP
-- =====================================================================

-- Create function to monitor valuation performance
CREATE OR REPLACE FUNCTION monitor_valuation_performance()
RETURNS TABLE (
    metric_name TEXT,
    metric_value DECIMAL,
    threshold_status TEXT,
    recommendation TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'avg_processing_time_ms'::TEXT,
        AVG(total_processing_time_ms),
        CASE
            WHEN AVG(total_processing_time_ms) < 500 THEN 'GREEN'
            WHEN AVG(total_processing_time_ms) < 1000 THEN 'YELLOW'
            ELSE 'RED'
        END,
        CASE
            WHEN AVG(total_processing_time_ms) > 1000 THEN 'Consider performance optimization'
            ELSE 'Performance within targets'
        END
    FROM property_valuations
    WHERE created_at > NOW() - INTERVAL '1 hour'
    AND status = 'completed'

    UNION ALL

    SELECT
        'avg_confidence_score'::TEXT,
        AVG(confidence_score),
        CASE
            WHEN AVG(confidence_score) > 0.8 THEN 'GREEN'
            WHEN AVG(confidence_score) > 0.6 THEN 'YELLOW'
            ELSE 'RED'
        END,
        CASE
            WHEN AVG(confidence_score) < 0.6 THEN 'Review model accuracy'
            ELSE 'Confidence scores healthy'
        END
    FROM property_valuations
    WHERE created_at > NOW() - INTERVAL '1 hour'
    AND status = 'completed';
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 11. CLEANUP AND MAINTENANCE
-- =====================================================================

-- Function to clean up expired valuations
CREATE OR REPLACE FUNCTION cleanup_expired_valuations()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM property_valuations
    WHERE expires_at IS NOT NULL
    AND expires_at < NOW() - INTERVAL '7 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Log cleanup activity
    INSERT INTO system_logs (level, message, created_at) VALUES (
        'INFO',
        'Cleaned up ' || deleted_count || ' expired property valuations',
        NOW()
    ) ON CONFLICT DO NOTHING;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule daily cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-expired-valuations', '0 2 * * *', 'SELECT cleanup_expired_valuations();');

COMMIT;

-- =====================================================================
-- MIGRATION VERIFICATION
-- =====================================================================

-- Verify all tables were created successfully
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('properties', 'property_valuations', 'marketing_campaigns', 'document_packages');

    IF table_count = 4 THEN
        RAISE NOTICE 'SUCCESS: All 4 property valuation tables created successfully';
    ELSE
        RAISE EXCEPTION 'ERROR: Expected 4 tables, but created %', table_count;
    END IF;

    -- Verify materialized view
    IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'seller_analytics_daily') THEN
        RAISE NOTICE 'SUCCESS: Seller analytics materialized view created';
    ELSE
        RAISE EXCEPTION 'ERROR: Seller analytics materialized view not created';
    END IF;
END;
$$;