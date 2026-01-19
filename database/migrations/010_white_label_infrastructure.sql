-- ===================================================================
-- White-Label Platform Infrastructure Migration
-- Creates comprehensive agency and domain management for $500K ARR foundation
-- Supports multi-tenant white-label deployments with custom domains
-- ===================================================================

-- ===================================================================
-- 1. AGENCY MANAGEMENT TABLES
-- ===================================================================

-- Agencies (white-label partners)
CREATE TABLE agencies (
    id BIGSERIAL PRIMARY KEY,
    agency_id VARCHAR(255) NOT NULL UNIQUE,
    agency_name VARCHAR(500) NOT NULL,
    agency_slug VARCHAR(255) NOT NULL UNIQUE,  -- Used in subdomains
    contact_email VARCHAR(255) NOT NULL,
    contract_value DECIMAL(10, 2) NOT NULL,    -- $50K/year contracts
    platform_fee_rate DECIMAL(5, 4) NOT NULL DEFAULT 0.20,  -- 20% platform fee
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'pending', 'suspended', 'terminated')),
    tier VARCHAR(50) NOT NULL DEFAULT 'professional' CHECK (tier IN ('basic', 'professional', 'enterprise')),

    -- Contract details
    contract_start_date DATE NOT NULL,
    contract_end_date DATE NOT NULL,
    auto_renewal BOOLEAN DEFAULT true,

    -- Agency settings
    max_clients INTEGER DEFAULT 50,
    max_custom_domains INTEGER DEFAULT 10,

    -- Metadata
    onboarding_completed BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agency clients (agencies manage multiple clients)
CREATE TABLE agency_clients (
    id BIGSERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL UNIQUE,
    agency_id VARCHAR(255) NOT NULL,
    client_name VARCHAR(500) NOT NULL,
    client_slug VARCHAR(255) NOT NULL,  -- Used in URLs

    -- GHL Integration
    ghl_location_id VARCHAR(255) UNIQUE,  -- Links to existing tenants
    ghl_access_token TEXT,
    ghl_refresh_token TEXT,
    ghl_token_expires_at TIMESTAMP WITH TIME ZONE,

    -- Client settings
    is_active BOOLEAN DEFAULT true,
    client_type VARCHAR(50) DEFAULT 'real_estate' CHECK (client_type IN ('real_estate', 'mortgage', 'insurance', 'general')),
    monthly_volume_limit INTEGER DEFAULT 1000,
    current_monthly_volume INTEGER DEFAULT 0,

    -- Billing
    monthly_fee DECIMAL(10, 2),
    billing_status VARCHAR(50) DEFAULT 'active' CHECK (billing_status IN ('active', 'past_due', 'suspended', 'canceled')),
    last_billing_date DATE,
    next_billing_date DATE,

    -- Metadata
    client_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_agency FOREIGN KEY (agency_id)
        REFERENCES agencies(agency_id) ON DELETE CASCADE,
    CONSTRAINT unique_client_per_agency UNIQUE(agency_id, client_slug)
);

-- ===================================================================
-- 2. DOMAIN CONFIGURATION TABLES
-- ===================================================================

-- Custom domains for white-label deployments
CREATE TABLE domain_configurations (
    id BIGSERIAL PRIMARY KEY,
    domain_id VARCHAR(255) NOT NULL UNIQUE,
    agency_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255),  -- NULL for agency-level domains

    -- Domain details
    domain_name VARCHAR(255) NOT NULL UNIQUE,
    subdomain VARCHAR(255),  -- For subdomains like client.agency.com
    is_primary BOOLEAN DEFAULT false,
    domain_type VARCHAR(50) NOT NULL CHECK (domain_type IN ('agency', 'client', 'custom')),

    -- DNS Configuration
    dns_provider VARCHAR(100),  -- cloudflare, route53, etc.
    dns_zone_id VARCHAR(255),
    dns_records JSONB DEFAULT '[]',  -- A, CNAME, TXT records

    -- SSL Configuration
    ssl_enabled BOOLEAN DEFAULT true,
    ssl_provider VARCHAR(100) DEFAULT 'letsencrypt',
    ssl_cert_status VARCHAR(50) DEFAULT 'pending' CHECK (ssl_cert_status IN ('pending', 'issued', 'expired', 'failed')),
    ssl_cert_expires_at TIMESTAMP WITH TIME ZONE,
    ssl_auto_renew BOOLEAN DEFAULT true,

    -- CDN Configuration
    cdn_enabled BOOLEAN DEFAULT false,
    cdn_provider VARCHAR(100),  -- cloudflare, aws_cloudfront, etc.
    cdn_distribution_id VARCHAR(255),
    cdn_endpoint VARCHAR(500),

    -- Validation
    verification_token VARCHAR(255) NOT NULL,
    verification_status VARCHAR(50) DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'failed')),
    verification_method VARCHAR(50) DEFAULT 'dns' CHECK (verification_method IN ('dns', 'file', 'email')),
    verified_at TIMESTAMP WITH TIME ZONE,

    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'error', 'disabled')),
    health_check_url VARCHAR(500),
    last_health_check TIMESTAMP WITH TIME ZONE,
    health_status VARCHAR(50) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'unhealthy', 'unknown')),

    -- Metadata
    configuration_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_domain_agency FOREIGN KEY (agency_id)
        REFERENCES agencies(agency_id) ON DELETE CASCADE,
    CONSTRAINT fk_domain_client FOREIGN KEY (client_id)
        REFERENCES agency_clients(client_id) ON DELETE CASCADE
);

-- ===================================================================
-- 3. BRAND ASSET MANAGEMENT TABLES
-- ===================================================================

-- Brand asset storage and management
CREATE TABLE brand_assets (
    id BIGSERIAL PRIMARY KEY,
    asset_id VARCHAR(255) NOT NULL UNIQUE,
    agency_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255),  -- NULL for agency-level assets

    -- Asset details
    asset_type VARCHAR(100) NOT NULL CHECK (asset_type IN ('logo', 'favicon', 'banner', 'background', 'font', 'css', 'image', 'document')),
    asset_name VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(10) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,

    -- Storage
    storage_provider VARCHAR(100) NOT NULL DEFAULT 's3',  -- s3, gcs, azure, local
    storage_bucket VARCHAR(255),
    storage_path VARCHAR(1000) NOT NULL,
    storage_url VARCHAR(1000) NOT NULL,

    -- CDN Distribution
    cdn_url VARCHAR(1000),
    cdn_cache_control VARCHAR(255) DEFAULT 'max-age=31536000',  -- 1 year cache

    -- File metadata
    file_size_bytes BIGINT NOT NULL,
    image_width INTEGER,
    image_height INTEGER,
    file_hash VARCHAR(255),  -- For duplicate detection

    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    processed_variants JSONB DEFAULT '{}',  -- Different sizes/formats
    processing_error TEXT,

    -- Usage
    is_active BOOLEAN DEFAULT true,
    usage_context VARCHAR(100),  -- header, footer, email, etc.
    display_order INTEGER DEFAULT 0,

    -- Optimization
    optimized_size_bytes BIGINT,
    optimization_ratio DECIMAL(5, 4),  -- Compression ratio
    webp_variant_url VARCHAR(1000),
    avif_variant_url VARCHAR(1000),

    -- Metadata
    asset_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_asset_agency FOREIGN KEY (agency_id)
        REFERENCES agencies(agency_id) ON DELETE CASCADE,
    CONSTRAINT fk_asset_client FOREIGN KEY (client_id)
        REFERENCES agency_clients(client_id) ON DELETE CASCADE
);

-- Brand configuration templates
CREATE TABLE brand_configurations (
    id BIGSERIAL PRIMARY KEY,
    config_id VARCHAR(255) NOT NULL UNIQUE,
    agency_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255),  -- NULL for agency default

    -- Brand identity
    brand_name VARCHAR(500) NOT NULL,
    primary_logo_asset_id VARCHAR(255),
    secondary_logo_asset_id VARCHAR(255),
    favicon_asset_id VARCHAR(255),

    -- Color palette
    primary_color VARCHAR(7) NOT NULL DEFAULT '#6D28D9',  -- Hex color
    secondary_color VARCHAR(7) NOT NULL DEFAULT '#4C1D95',
    accent_color VARCHAR(7) NOT NULL DEFAULT '#10B981',
    text_color VARCHAR(7) NOT NULL DEFAULT '#1F2937',
    background_color VARCHAR(7) NOT NULL DEFAULT '#F9FAFB',
    error_color VARCHAR(7) NOT NULL DEFAULT '#DC2626',
    success_color VARCHAR(7) NOT NULL DEFAULT '#059669',
    warning_color VARCHAR(7) NOT NULL DEFAULT '#D97706',

    -- Typography
    primary_font_family VARCHAR(255) DEFAULT 'Inter, sans-serif',
    secondary_font_family VARCHAR(255) DEFAULT 'system-ui',
    font_scale DECIMAL(3, 2) DEFAULT 1.00,

    -- Layout settings
    border_radius VARCHAR(10) DEFAULT '8px',
    box_shadow VARCHAR(255) DEFAULT '0 4px 6px rgba(0, 0, 0, 0.1)',
    animation_duration VARCHAR(10) DEFAULT '0.3s',
    container_max_width VARCHAR(10) DEFAULT '1200px',

    -- Custom CSS
    custom_css TEXT,
    css_variables JSONB DEFAULT '{}',

    -- Feature toggles
    feature_flags JSONB DEFAULT '{}',
    navigation_structure JSONB DEFAULT '[]',
    footer_configuration JSONB DEFAULT '{}',

    -- SEO settings
    meta_title_template VARCHAR(255),
    meta_description_template VARCHAR(500),
    meta_keywords TEXT,
    og_image_asset_id VARCHAR(255),

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    version VARCHAR(20) DEFAULT '1.0',

    -- Metadata
    configuration_notes TEXT,
    brand_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_brand_agency FOREIGN KEY (agency_id)
        REFERENCES agencies(agency_id) ON DELETE CASCADE,
    CONSTRAINT fk_brand_client FOREIGN KEY (client_id)
        REFERENCES agency_clients(client_id) ON DELETE CASCADE,
    CONSTRAINT fk_primary_logo FOREIGN KEY (primary_logo_asset_id)
        REFERENCES brand_assets(asset_id) ON DELETE SET NULL,
    CONSTRAINT fk_secondary_logo FOREIGN KEY (secondary_logo_asset_id)
        REFERENCES brand_assets(asset_id) ON DELETE SET NULL,
    CONSTRAINT fk_favicon FOREIGN KEY (favicon_asset_id)
        REFERENCES brand_assets(asset_id) ON DELETE SET NULL
);

-- ===================================================================
-- 4. DEPLOYMENT AND ROUTING TABLES
-- ===================================================================

-- White-label deployment configurations
CREATE TABLE deployment_configurations (
    id BIGSERIAL PRIMARY KEY,
    deployment_id VARCHAR(255) NOT NULL UNIQUE,
    agency_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255),

    -- Domain mapping
    primary_domain_id VARCHAR(255),
    additional_domain_ids JSONB DEFAULT '[]',

    -- Brand configuration
    brand_config_id VARCHAR(255),

    -- Application settings
    app_version VARCHAR(50) DEFAULT '1.0.0',
    deployment_environment VARCHAR(50) DEFAULT 'production' CHECK (deployment_environment IN ('development', 'staging', 'production')),

    -- Feature configuration
    enabled_modules JSONB DEFAULT '[]',  -- ['leads', 'analytics', 'messaging']
    module_configurations JSONB DEFAULT '{}',

    -- Performance settings
    cache_ttl_seconds INTEGER DEFAULT 3600,
    rate_limit_requests_per_minute INTEGER DEFAULT 1000,
    max_concurrent_users INTEGER DEFAULT 100,

    -- Security settings
    csrf_protection BOOLEAN DEFAULT true,
    cors_origins JSONB DEFAULT '[]',
    api_key_required BOOLEAN DEFAULT false,
    ip_whitelist JSONB DEFAULT '[]',

    -- Monitoring
    analytics_enabled BOOLEAN DEFAULT true,
    error_tracking_enabled BOOLEAN DEFAULT true,
    performance_monitoring BOOLEAN DEFAULT true,

    -- Status
    deployment_status VARCHAR(50) DEFAULT 'pending' CHECK (deployment_status IN ('pending', 'deploying', 'active', 'error', 'disabled')),
    last_deployment_at TIMESTAMP WITH TIME ZONE,
    deployment_health VARCHAR(50) DEFAULT 'unknown' CHECK (deployment_health IN ('healthy', 'degraded', 'unhealthy', 'unknown')),

    -- Metadata
    deployment_notes TEXT,
    deployment_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_deployment_agency FOREIGN KEY (agency_id)
        REFERENCES agencies(agency_id) ON DELETE CASCADE,
    CONSTRAINT fk_deployment_client FOREIGN KEY (client_id)
        REFERENCES agency_clients(client_id) ON DELETE CASCADE,
    CONSTRAINT fk_deployment_domain FOREIGN KEY (primary_domain_id)
        REFERENCES domain_configurations(domain_id) ON DELETE SET NULL,
    CONSTRAINT fk_deployment_brand FOREIGN KEY (brand_config_id)
        REFERENCES brand_configurations(config_id) ON DELETE SET NULL
);

-- Domain routing cache for fast lookups
CREATE TABLE domain_routing_cache (
    id BIGSERIAL PRIMARY KEY,
    domain_name VARCHAR(255) NOT NULL UNIQUE,
    agency_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255),
    deployment_id VARCHAR(255) NOT NULL,
    brand_config_id VARCHAR(255),

    -- Cached configuration for fast access
    routing_config JSONB NOT NULL,  -- Complete routing configuration
    brand_config JSONB,  -- Cached brand configuration
    feature_flags JSONB DEFAULT '{}',

    -- Cache metadata
    cache_version VARCHAR(20) DEFAULT '1.0',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '1 hour',

    CONSTRAINT fk_routing_agency FOREIGN KEY (agency_id)
        REFERENCES agencies(agency_id) ON DELETE CASCADE,
    CONSTRAINT fk_routing_client FOREIGN KEY (client_id)
        REFERENCES agency_clients(client_id) ON DELETE CASCADE,
    CONSTRAINT fk_routing_deployment FOREIGN KEY (deployment_id)
        REFERENCES deployment_configurations(deployment_id) ON DELETE CASCADE
);

-- ===================================================================
-- 5. AUDIT AND ANALYTICS TABLES
-- ===================================================================

-- Agency activity audit log
CREATE TABLE agency_audit_log (
    id BIGSERIAL PRIMARY KEY,
    audit_id VARCHAR(255) NOT NULL UNIQUE,
    agency_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255),
    user_email VARCHAR(255),

    -- Action details
    action_type VARCHAR(100) NOT NULL,  -- domain_added, brand_updated, etc.
    resource_type VARCHAR(100) NOT NULL,  -- domain, brand, asset, etc.
    resource_id VARCHAR(255) NOT NULL,

    -- Change tracking
    old_values JSONB,
    new_values JSONB,
    change_summary TEXT,

    -- Request metadata
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),

    -- Status
    action_status VARCHAR(50) DEFAULT 'success' CHECK (action_status IN ('success', 'failed', 'partial')),
    error_message TEXT,

    -- Metadata
    audit_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_audit_agency FOREIGN KEY (agency_id)
        REFERENCES agencies(agency_id) ON DELETE CASCADE
);

-- White-label platform analytics
CREATE TABLE platform_analytics (
    id BIGSERIAL PRIMARY KEY,
    metric_id VARCHAR(255) NOT NULL UNIQUE,
    agency_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255),

    -- Metric details
    metric_type VARCHAR(100) NOT NULL,  -- page_views, api_calls, user_sessions
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15, 4) NOT NULL,
    metric_unit VARCHAR(50),

    -- Dimensions
    time_bucket TIMESTAMP WITH TIME ZONE NOT NULL,  -- Hourly/daily bucket
    granularity VARCHAR(20) DEFAULT 'hour' CHECK (granularity IN ('minute', 'hour', 'day', 'week', 'month')),

    -- Segmentation
    segment_dimensions JSONB DEFAULT '{}',  -- browser, location, etc.

    -- Attribution
    source_domain VARCHAR(255),
    source_deployment VARCHAR(255),

    -- Metadata
    analytics_metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_analytics_agency FOREIGN KEY (agency_id)
        REFERENCES agencies(agency_id) ON DELETE CASCADE,
    CONSTRAINT fk_analytics_client FOREIGN KEY (client_id)
        REFERENCES agency_clients(client_id) ON DELETE CASCADE
);

-- ===================================================================
-- 6. PERFORMANCE INDEXES
-- ===================================================================

-- Agency indexes
CREATE INDEX idx_agencies_status_tier ON agencies(status, tier);
CREATE INDEX idx_agencies_contract_dates ON agencies(contract_start_date, contract_end_date);
CREATE INDEX idx_agencies_slug_lookup ON agencies(agency_slug) WHERE status = 'active';

-- Client indexes
CREATE INDEX idx_agency_clients_agency_active ON agency_clients(agency_id, is_active);
CREATE INDEX idx_agency_clients_ghl_location ON agency_clients(ghl_location_id) WHERE ghl_location_id IS NOT NULL;
CREATE INDEX idx_agency_clients_billing_status ON agency_clients(billing_status, next_billing_date);

-- Domain configuration indexes
CREATE INDEX idx_domain_configs_domain_lookup ON domain_configurations(domain_name, status);
CREATE INDEX idx_domain_configs_agency_type ON domain_configurations(agency_id, domain_type, is_primary);
CREATE INDEX idx_domain_configs_verification ON domain_configurations(verification_status, ssl_cert_status);
CREATE INDEX idx_domain_configs_health ON domain_configurations(health_status, last_health_check);

-- Brand asset indexes
CREATE INDEX idx_brand_assets_agency_type ON brand_assets(agency_id, asset_type, is_active);
CREATE INDEX idx_brand_assets_client_type ON brand_assets(client_id, asset_type) WHERE client_id IS NOT NULL;
CREATE INDEX idx_brand_assets_storage_lookup ON brand_assets(storage_path);
CREATE INDEX idx_brand_assets_file_hash ON brand_assets(file_hash) WHERE file_hash IS NOT NULL;

-- Brand configuration indexes
CREATE INDEX idx_brand_configs_agency_active ON brand_configurations(agency_id, is_active);
CREATE INDEX idx_brand_configs_client_active ON brand_configurations(client_id, is_active) WHERE client_id IS NOT NULL;
CREATE INDEX idx_brand_configs_default ON brand_configurations(agency_id, is_default) WHERE is_default = true;

-- Deployment indexes
CREATE INDEX idx_deployments_agency_status ON deployment_configurations(agency_id, deployment_status);
CREATE INDEX idx_deployments_health ON deployment_configurations(deployment_health, last_deployment_at);

-- Domain routing cache indexes (critical for performance)
CREATE INDEX idx_domain_routing_lookup ON domain_routing_cache(domain_name, expires_at) WHERE expires_at > NOW();
CREATE INDEX idx_domain_routing_agency ON domain_routing_cache(agency_id, last_updated);

-- Audit log indexes
CREATE INDEX idx_audit_log_agency_time ON agency_audit_log(agency_id, created_at DESC);
CREATE INDEX idx_audit_log_action_type ON agency_audit_log(action_type, created_at DESC);
CREATE INDEX idx_audit_log_resource ON agency_audit_log(resource_type, resource_id);

-- Analytics indexes
CREATE INDEX idx_platform_analytics_agency_time ON platform_analytics(agency_id, time_bucket DESC);
CREATE INDEX idx_platform_analytics_metric ON platform_analytics(metric_type, time_bucket DESC);
CREATE INDEX idx_platform_analytics_granularity ON platform_analytics(granularity, time_bucket DESC);

-- ===================================================================
-- 7. TRIGGERS FOR AUTOMATIC UPDATES
-- ===================================================================

-- Updated timestamp triggers (reuse existing function)
CREATE TRIGGER update_agencies_updated_at
    BEFORE UPDATE ON agencies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agency_clients_updated_at
    BEFORE UPDATE ON agency_clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_domain_configurations_updated_at
    BEFORE UPDATE ON domain_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_brand_assets_updated_at
    BEFORE UPDATE ON brand_assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_brand_configurations_updated_at
    BEFORE UPDATE ON brand_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deployment_configurations_updated_at
    BEFORE UPDATE ON deployment_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Domain routing cache invalidation trigger
CREATE OR REPLACE FUNCTION invalidate_domain_routing_cache()
RETURNS TRIGGER AS $$
BEGIN
    -- Invalidate cache entries for affected domains
    UPDATE domain_routing_cache
    SET expires_at = NOW()
    WHERE agency_id = COALESCE(NEW.agency_id, OLD.agency_id)
       OR client_id = COALESCE(NEW.client_id, OLD.client_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply cache invalidation triggers
CREATE TRIGGER invalidate_cache_on_domain_change
    AFTER INSERT OR UPDATE OR DELETE ON domain_configurations
    FOR EACH ROW EXECUTE FUNCTION invalidate_domain_routing_cache();

CREATE TRIGGER invalidate_cache_on_brand_change
    AFTER INSERT OR UPDATE OR DELETE ON brand_configurations
    FOR EACH ROW EXECUTE FUNCTION invalidate_domain_routing_cache();

CREATE TRIGGER invalidate_cache_on_deployment_change
    AFTER INSERT OR UPDATE OR DELETE ON deployment_configurations
    FOR EACH ROW EXECUTE FUNCTION invalidate_domain_routing_cache();

-- ===================================================================
-- 8. UTILITY FUNCTIONS
-- ===================================================================

-- Function to get agency summary statistics
CREATE OR REPLACE FUNCTION get_agency_statistics(p_agency_id VARCHAR(255) DEFAULT NULL)
RETURNS TABLE (
    agency_id VARCHAR(255),
    agency_name VARCHAR(500),
    client_count BIGINT,
    active_domains BIGINT,
    total_assets BIGINT,
    monthly_revenue DECIMAL(10, 2),
    platform_fees DECIMAL(10, 2),
    contract_status VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.agency_id,
        a.agency_name,
        COUNT(DISTINCT ac.id) as client_count,
        COUNT(DISTINCT dc.id) as active_domains,
        COUNT(DISTINCT ba.id) as total_assets,
        COALESCE(SUM(ac.monthly_fee), 0) as monthly_revenue,
        COALESCE(SUM(ac.monthly_fee * a.platform_fee_rate), 0) as platform_fees,
        CASE
            WHEN a.contract_end_date < CURRENT_DATE THEN 'expired'
            WHEN a.contract_end_date < CURRENT_DATE + INTERVAL '30 days' THEN 'expiring'
            ELSE 'active'
        END as contract_status
    FROM agencies a
    LEFT JOIN agency_clients ac ON a.agency_id = ac.agency_id AND ac.is_active = true
    LEFT JOIN domain_configurations dc ON a.agency_id = dc.agency_id AND dc.status = 'active'
    LEFT JOIN brand_assets ba ON a.agency_id = ba.agency_id AND ba.is_active = true
    WHERE (p_agency_id IS NULL OR a.agency_id = p_agency_id)
        AND a.status = 'active'
    GROUP BY a.agency_id, a.agency_name, a.contract_end_date, a.platform_fee_rate;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh domain routing cache
CREATE OR REPLACE FUNCTION refresh_domain_routing_cache(p_domain_name VARCHAR(255))
RETURNS BOOLEAN AS $$
DECLARE
    routing_data RECORD;
    brand_data RECORD;
BEGIN
    -- Get complete routing configuration
    SELECT
        dc.domain_name,
        dc.agency_id,
        dc.client_id,
        dep.deployment_id,
        dep.brand_config_id,
        dep.enabled_modules,
        dep.module_configurations,
        dep.rate_limit_requests_per_minute,
        dep.max_concurrent_users
    INTO routing_data
    FROM domain_configurations dc
    JOIN deployment_configurations dep ON dc.domain_id = dep.primary_domain_id
    WHERE dc.domain_name = p_domain_name
      AND dc.status = 'active'
      AND dep.deployment_status = 'active';

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Get brand configuration
    SELECT
        config_id,
        brand_name,
        primary_color,
        secondary_color,
        accent_color,
        primary_font_family,
        custom_css,
        feature_flags
    INTO brand_data
    FROM brand_configurations
    WHERE config_id = routing_data.brand_config_id
      AND is_active = true;

    -- Insert or update cache
    INSERT INTO domain_routing_cache (
        domain_name,
        agency_id,
        client_id,
        deployment_id,
        brand_config_id,
        routing_config,
        brand_config,
        feature_flags,
        last_updated,
        expires_at
    )
    VALUES (
        routing_data.domain_name,
        routing_data.agency_id,
        routing_data.client_id,
        routing_data.deployment_id,
        routing_data.brand_config_id,
        jsonb_build_object(
            'modules', routing_data.enabled_modules,
            'module_config', routing_data.module_configurations,
            'rate_limit', routing_data.rate_limit_requests_per_minute,
            'max_users', routing_data.max_concurrent_users
        ),
        CASE WHEN brand_data.config_id IS NOT NULL THEN
            jsonb_build_object(
                'brand_name', brand_data.brand_name,
                'primary_color', brand_data.primary_color,
                'secondary_color', brand_data.secondary_color,
                'accent_color', brand_data.accent_color,
                'font_family', brand_data.primary_font_family,
                'custom_css', brand_data.custom_css
            )
        ELSE '{}' END,
        COALESCE(brand_data.feature_flags, '{}'),
        NOW(),
        NOW() + INTERVAL '1 hour'
    )
    ON CONFLICT (domain_name) DO UPDATE SET
        routing_config = EXCLUDED.routing_config,
        brand_config = EXCLUDED.brand_config,
        feature_flags = EXCLUDED.feature_flags,
        last_updated = EXCLUDED.last_updated,
        expires_at = EXCLUDED.expires_at;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
-- 9. SAMPLE DATA FOR DEVELOPMENT
-- ===================================================================

-- Insert sample agency
INSERT INTO agencies (
    agency_id, agency_name, agency_slug, contact_email, contract_value,
    platform_fee_rate, contract_start_date, contract_end_date, tier, max_clients
) VALUES (
    'agency_001', 'Premium Real Estate Solutions', 'premium-realty', 'admin@premiumrealty.com', 50000.00,
    0.20, '2026-01-01', '2026-12-31', 'professional', 100
);

-- Insert sample client
INSERT INTO agency_clients (
    client_id, agency_id, client_name, client_slug, client_type,
    monthly_fee, next_billing_date, ghl_location_id
) VALUES (
    'client_001', 'agency_001', 'Downtown Properties LLC', 'downtown-props', 'real_estate',
    2500.00, '2026-02-01', 'ghl_loc_12345'
);

-- Insert sample domain configuration
INSERT INTO domain_configurations (
    domain_id, agency_id, client_id, domain_name, domain_type,
    verification_token, ssl_enabled, cdn_enabled, status
) VALUES (
    'domain_001', 'agency_001', 'client_001', 'downtown.premiumrealty.com', 'client',
    'verify_token_12345', true, true, 'pending'
);

-- ===================================================================
-- 10. MIGRATION COMPLETION
-- ===================================================================

-- Record migration completion
INSERT INTO schema_migrations (version, description, applied_at)
VALUES (
    '010',
    'White-label platform infrastructure for agency partnerships',
    NOW()
)
ON CONFLICT (version) DO NOTHING;

-- Summary statistics
SELECT
    'White-Label Infrastructure Migration Complete' as status,
    COUNT(*) FILTER (WHERE table_name LIKE 'agencies') as agency_tables,
    COUNT(*) FILTER (WHERE table_name LIKE '%domain%') as domain_tables,
    COUNT(*) FILTER (WHERE table_name LIKE '%brand%') as brand_tables,
    COUNT(*) FILTER (WHERE indexname LIKE 'idx_%') as performance_indexes
FROM (
    SELECT tablename as table_name, NULL as indexname FROM pg_tables WHERE schemaname = 'public'
    UNION ALL
    SELECT NULL as table_name, indexname FROM pg_indexes WHERE schemaname = 'public'
) t;