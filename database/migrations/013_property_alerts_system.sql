-- Migration 013: Real-Time Property Alerts System
-- Version: 3.0.0
-- Description: Creates property alert preferences, history, and notification infrastructure for real-time property matching alerts
-- Purpose: Enable intelligent property alert delivery with scoring thresholds, de-duplication, and multi-channel delivery
-- Apply to: PostgreSQL 15+ with existing Service 6 schema

-- Check PostgreSQL version
DO $$
BEGIN
    IF current_setting('server_version_num')::integer < 150000 THEN
        RAISE EXCEPTION 'PostgreSQL version 15.0 or higher required. Current version: %', version();
    END IF;
END $$;

-- Record migration start
INSERT INTO schema_migrations (version, description, applied_at, applied_by)
VALUES ('013', 'Real-Time Property Alerts System - Preferences, History, Notifications', NOW(), current_user);

-- Start timing
\timing on

-- ================================================================================================
-- PROPERTY ALERT PREFERENCES
-- ================================================================================================

-- Lead alert preferences with multi-tenant support
CREATE TABLE IF NOT EXISTS lead_alert_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,

    -- Basic Price & Property Filters
    min_price DECIMAL(12,2),
    max_price DECIMAL(12,2),
    min_bedrooms INTEGER,
    max_bedrooms INTEGER,
    min_bathrooms DECIMAL(3,1),
    max_bathrooms DECIMAL(3,1),
    min_sqft INTEGER,
    max_sqft INTEGER,

    -- Location Preferences
    preferred_neighborhoods TEXT[],
    max_commute_minutes INTEGER,
    work_location VARCHAR(500),
    school_districts TEXT[],

    -- Property Type & Features
    property_types TEXT[], -- ['single_family', 'condo', 'townhouse']
    must_have_features TEXT[], -- ['garage', 'pool', 'fireplace', 'updated_kitchen']
    exclude_features TEXT[], -- ['hoa', 'stairs']

    -- Alert Configuration
    alert_threshold_score DECIMAL(5,2) DEFAULT 75.00, -- Minimum match score to trigger alert
    max_alerts_per_day INTEGER DEFAULT 5, -- Daily alert limit to prevent fatigue
    alert_frequency VARCHAR(50) DEFAULT 'immediate', -- 'immediate', 'daily_digest', 'weekly_digest'

    -- Notification Channels
    email_notifications BOOLEAN DEFAULT true,
    sms_notifications BOOLEAN DEFAULT false,
    in_app_notifications BOOLEAN DEFAULT true,
    websocket_notifications BOOLEAN DEFAULT true,

    -- Advanced Settings
    price_drop_alerts BOOLEAN DEFAULT true, -- Alert on price drops for matched properties
    new_listing_alerts BOOLEAN DEFAULT true, -- Alert on new listings matching criteria
    market_trend_alerts BOOLEAN DEFAULT false, -- Alert on market condition changes

    -- Scheduling
    quiet_hours_start TIME DEFAULT NULL, -- No alerts during quiet hours
    quiet_hours_end TIME DEFAULT NULL,
    timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',

    -- Status & Tracking
    active BOOLEAN DEFAULT true,
    created_by_user_id UUID, -- User who created the alert criteria
    last_triggered TIMESTAMP WITH TIME ZONE, -- Last time an alert was sent
    total_alerts_sent INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT lead_alert_preferences_tenant_lead_unique UNIQUE(tenant_id, lead_id),
    CONSTRAINT lead_alert_preferences_valid_price_range CHECK (min_price IS NULL OR max_price IS NULL OR min_price <= max_price),
    CONSTRAINT lead_alert_preferences_valid_bedrooms CHECK (min_bedrooms IS NULL OR max_bedrooms IS NULL OR min_bedrooms <= max_bedrooms),
    CONSTRAINT lead_alert_preferences_valid_bathrooms CHECK (min_bathrooms IS NULL OR max_bathrooms IS NULL OR min_bathrooms <= max_bathrooms),
    CONSTRAINT lead_alert_preferences_valid_sqft CHECK (min_sqft IS NULL OR max_sqft IS NULL OR min_sqft <= max_sqft),
    CONSTRAINT lead_alert_preferences_valid_threshold CHECK (alert_threshold_score >= 0 AND alert_threshold_score <= 100),
    CONSTRAINT lead_alert_preferences_valid_daily_limit CHECK (max_alerts_per_day > 0 AND max_alerts_per_day <= 50),
    CONSTRAINT lead_alert_preferences_valid_frequency CHECK (alert_frequency IN ('immediate', 'daily_digest', 'weekly_digest')),
    CONSTRAINT lead_alert_preferences_at_least_one_channel CHECK (
        email_notifications = true OR
        sms_notifications = true OR
        in_app_notifications = true OR
        websocket_notifications = true
    )
);

-- ================================================================================================
-- PROPERTY ALERT HISTORY
-- ================================================================================================

-- Property alert history with delivery tracking and engagement metrics
CREATE TABLE IF NOT EXISTS property_alert_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_preference_id UUID NOT NULL REFERENCES lead_alert_preferences(id) ON DELETE CASCADE,
    lead_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    property_id VARCHAR(255) NOT NULL,

    -- Alert Categorization
    alert_type VARCHAR(100) NOT NULL, -- 'new_match', 'price_drop', 'market_opportunity'
    alert_priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'

    -- Alert Content
    alert_title VARCHAR(500) NOT NULL,
    alert_message TEXT NOT NULL,
    alert_summary VARCHAR(1000), -- Short summary for digest modes

    -- Property Match Data
    match_score DECIMAL(5,2) NOT NULL, -- The match score that triggered the alert
    match_reasoning JSONB, -- Detailed reasoning from property matcher
    property_data JSONB NOT NULL, -- Snapshot of property data at time of alert

    -- Property Details (for quick queries without JSON parsing)
    property_address VARCHAR(500),
    property_price DECIMAL(12,2),
    property_bedrooms INTEGER,
    property_bathrooms DECIMAL(3,1),
    property_sqft INTEGER,
    property_type VARCHAR(50),
    days_on_market_at_alert INTEGER,

    -- Alert Processing
    processing_time_ms INTEGER, -- Time taken to generate alert
    duplicate_of UUID REFERENCES property_alert_history(id), -- Reference to original if this is a duplicate
    dedup_reason VARCHAR(200), -- Reason for de-duplication

    -- Delivery Tracking
    channels_sent TEXT[], -- ['websocket', 'email', 'sms'] - which channels were attempted
    channels_delivered TEXT[], -- Channels that successfully delivered
    channels_failed TEXT[], -- Channels that failed delivery
    delivery_errors JSONB, -- Error details for failed deliveries

    -- Engagement Metrics
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    first_opened_at TIMESTAMP WITH TIME ZONE, -- First time alert was viewed
    clicked_at TIMESTAMP WITH TIME ZONE, -- First time property link was clicked
    total_opens INTEGER DEFAULT 0, -- Number of times alert was opened
    total_clicks INTEGER DEFAULT 0, -- Number of times property was clicked

    -- User Actions
    bookmarked_at TIMESTAMP WITH TIME ZONE, -- If user saved/bookmarked property
    inquired_at TIMESTAMP WITH TIME ZONE, -- If user contacted about property
    dismissed_at TIMESTAMP WITH TIME ZONE, -- If user dismissed the alert
    feedback_rating INTEGER, -- 1-5 rating on alert relevance
    feedback_reason VARCHAR(500), -- User feedback on alert quality

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT property_alert_history_valid_score CHECK (match_score >= 0 AND match_score <= 100),
    CONSTRAINT property_alert_history_valid_priority CHECK (alert_priority IN ('low', 'normal', 'high', 'urgent')),
    CONSTRAINT property_alert_history_valid_alert_type CHECK (alert_type IN ('new_match', 'price_drop', 'market_opportunity', 'back_on_market', 'price_increase', 'status_change')),
    CONSTRAINT property_alert_history_valid_feedback CHECK (feedback_rating IS NULL OR (feedback_rating >= 1 AND feedback_rating <= 5)),
    CONSTRAINT property_alert_history_positive_metrics CHECK (
        total_opens >= 0 AND
        total_clicks >= 0 AND
        total_clicks <= total_opens
    )
);

-- ================================================================================================
-- ALERT PROCESSING QUEUE
-- ================================================================================================

-- Queue for processing property alerts with batching and retry logic
CREATE TABLE IF NOT EXISTS property_alert_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    property_id VARCHAR(255) NOT NULL,

    -- Alert Data
    alert_type VARCHAR(100) NOT NULL,
    match_score DECIMAL(5,2) NOT NULL,
    property_data JSONB NOT NULL,
    alert_content JSONB NOT NULL, -- Pre-generated alert title, message, etc.

    -- Processing Status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'sent', 'failed', 'duplicate', 'rate_limited'
    processing_attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    -- Scheduling
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When to process this alert
    batch_key VARCHAR(200), -- Key for batching similar alerts together
    priority INTEGER DEFAULT 100, -- Lower number = higher priority

    -- Error Handling
    error_message TEXT,
    last_error TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT property_alert_queue_valid_status CHECK (status IN ('pending', 'processing', 'sent', 'failed', 'duplicate', 'rate_limited')),
    CONSTRAINT property_alert_queue_valid_attempts CHECK (processing_attempts >= 0 AND processing_attempts <= max_attempts)
);

-- ================================================================================================
-- NOTIFICATION PREFERENCES (Phase 2 Foundation)
-- ================================================================================================

-- User-level notification preferences (foundation for Phase 2)
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- References users table
    tenant_id VARCHAR(255), -- Multi-tenant support

    -- Channel Preferences
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    push_enabled BOOLEAN DEFAULT TRUE,
    websocket_enabled BOOLEAN DEFAULT TRUE,

    -- Category Filters (matching existing notification categories)
    lead_notifications BOOLEAN DEFAULT TRUE,
    commission_notifications BOOLEAN DEFAULT TRUE,
    system_notifications BOOLEAN DEFAULT TRUE,
    performance_notifications BOOLEAN DEFAULT TRUE,
    property_alert_notifications BOOLEAN DEFAULT TRUE, -- New category

    -- Severity Filters (matching existing notification severities)
    critical_enabled BOOLEAN DEFAULT TRUE,
    error_enabled BOOLEAN DEFAULT TRUE,
    warning_enabled BOOLEAN DEFAULT TRUE,
    info_enabled BOOLEAN DEFAULT TRUE,
    success_enabled BOOLEAN DEFAULT TRUE,

    -- Advanced Scheduling
    quiet_hours_start TIME DEFAULT NULL,
    quiet_hours_end TIME DEFAULT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Frequency Controls
    digest_enabled BOOLEAN DEFAULT FALSE,
    digest_frequency VARCHAR(20) DEFAULT 'daily', -- 'daily', 'weekly'
    max_notifications_per_hour INTEGER DEFAULT 50,

    -- Property Alert Specific Settings
    property_alert_digest_enabled BOOLEAN DEFAULT FALSE,
    property_alert_max_per_day INTEGER DEFAULT 10,
    property_alert_min_score INTEGER DEFAULT 75, -- Global minimum score filter

    -- Auto-dismiss Settings (extending current session-based logic)
    auto_dismiss_info_seconds INTEGER DEFAULT 5,
    auto_dismiss_warning_seconds INTEGER DEFAULT 10,
    auto_dismiss_error_seconds INTEGER DEFAULT 0, -- 0 = manual dismissal only
    auto_dismiss_success_seconds INTEGER DEFAULT 3,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT user_notification_preferences_user_unique UNIQUE(user_id, tenant_id),
    CONSTRAINT user_notification_preferences_valid_frequency CHECK (digest_frequency IN ('daily', 'weekly')),
    CONSTRAINT user_notification_preferences_positive_limits CHECK (
        max_notifications_per_hour > 0 AND
        property_alert_max_per_day > 0 AND
        property_alert_min_score >= 0 AND
        property_alert_min_score <= 100
    )
);

-- ================================================================================================
-- PERFORMANCE INDEXES
-- ================================================================================================

-- Lead alert preferences indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_alert_preferences_tenant_active
    ON lead_alert_preferences(tenant_id, active, updated_at)
    WHERE active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_alert_preferences_lead_active
    ON lead_alert_preferences(lead_id)
    WHERE active = true;

-- Property alert history indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_alert_history_lead_recent
    ON property_alert_history(lead_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_alert_history_property_recent
    ON property_alert_history(property_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_alert_history_tenant_date
    ON property_alert_history(tenant_id, DATE(created_at));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_alert_history_engagement
    ON property_alert_history(sent_at, clicked_at)
    WHERE sent_at IS NOT NULL;

-- Property alert queue indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_alert_queue_processing
    ON property_alert_queue(status, scheduled_for, priority)
    WHERE status IN ('pending', 'processing');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_alert_queue_batch
    ON property_alert_queue(batch_key, scheduled_for)
    WHERE batch_key IS NOT NULL;

-- User notification preferences indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_notification_preferences_user
    ON user_notification_preferences(user_id, tenant_id);

-- ================================================================================================
-- TRIGGERS AND FUNCTIONS
-- ================================================================================================

-- Update timestamp function for updated_at fields
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER trigger_lead_alert_preferences_updated_at
    BEFORE UPDATE ON lead_alert_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_user_notification_preferences_updated_at
    BEFORE UPDATE ON user_notification_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================================================================
-- INITIAL DATA
-- ================================================================================================

-- Insert default notification preferences for existing users (if any)
-- This will be handled by the application on first user access

-- ================================================================================================
-- MIGRATION COMPLETION
-- ================================================================================================

-- Update migration record
UPDATE schema_migrations
SET
    applied_at = NOW(),
    execution_time_ms = extract(epoch from (NOW() - applied_at)) * 1000
WHERE version = '013';

-- Stop timing
\timing off

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 013 completed successfully: Real-Time Property Alerts System';
    RAISE NOTICE 'Created tables: lead_alert_preferences, property_alert_history, property_alert_queue, user_notification_preferences';
    RAISE NOTICE 'Created indexes for optimal query performance';
    RAISE NOTICE 'Ready for PropertyAlertEngine integration';
END $$;