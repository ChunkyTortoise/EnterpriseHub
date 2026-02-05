w-- ============================================================================
-- SMS Compliance Audit Trail Database Schema
-- ============================================================================
-- This migration creates the database tables required for TCPA compliance
-- including opt-out storage, SMS send audit logging, consent tracking,
-- and compliance violation detection.
--
-- TCPA Compliance Requirements:
-- - All SMS sends must be logged with complete audit trail
-- - Opt-out requests must be permanently stored with timestamps
-- - Consent status must be tracked and verified before each send
-- - Audit logs must be immutable and queryable for compliance reporting
-- - Retention policies must be enforced for compliance data
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SMS Opt-Out Storage Table
-- ----------------------------------------------------------------------------
-- Stores all SMS opt-out requests with complete audit trail.
-- This table is critical for TCPA compliance - once opted out, no SMS
-- should be sent to that number unless explicitly re-opted-in.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sms_opt_outs (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Phone number (normalized to E.164 format)
    phone_number VARCHAR(20) NOT NULL,
    
    -- Opt-out details
    opt_out_reason VARCHAR(50) NOT NULL,  -- user_request, stop_keyword, compliance_violation, admin_block, frequency_abuse
    opt_out_method VARCHAR(50) NOT NULL,   -- sms, web, api, admin
    opt_out_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Original message content (if opt-out via SMS)
    original_message TEXT,
    
    -- Location/tenant context
    location_id VARCHAR(255),
    
    -- Confirmation details
    confirmation_sent BOOLEAN DEFAULT FALSE,
    confirmation_timestamp TIMESTAMP WITH TIME ZONE,
    confirmation_method VARCHAR(50),
    
    -- Re-opt-in tracking (if user opts back in)
    re_opted_in BOOLEAN DEFAULT FALSE,
    re_opt_in_timestamp TIMESTAMP WITH TIME ZONE,
    re_opt_in_method VARCHAR(50),
    re_opt_in_reason TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT uq_sms_opt_outs_phone_active UNIQUE (phone_number, re_opted_in)
);

-- Indexes for opt-out lookups
CREATE INDEX idx_sms_opt_outs_phone ON sms_opt_outs(phone_number);
CREATE INDEX idx_sms_opt_outs_timestamp ON sms_opt_outs(opt_out_timestamp DESC);
CREATE INDEX idx_sms_opt_outs_location ON sms_opt_outs(location_id);
CREATE INDEX idx_sms_opt_outs_active ON sms_opt_outs(phone_number) WHERE re_opted_in = FALSE;

-- ----------------------------------------------------------------------------
-- SMS Send Audit Log Table
-- ----------------------------------------------------------------------------
-- Logs all SMS send attempts with complete compliance information.
-- This table provides the immutable audit trail required for TCPA compliance.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sms_send_audit_log (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Phone number (normalized to E.164 format)
    phone_number VARCHAR(20) NOT NULL,
    
    -- Message details
    message_content TEXT NOT NULL,
    message_length INTEGER NOT NULL,
    message_type VARCHAR(50) DEFAULT 'transactional',  -- transactional, marketing, compliance
    
    -- Send attempt details
    send_attempted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    send_completed_at TIMESTAMP WITH TIME ZONE,
    delivery_status VARCHAR(50) NOT NULL,  -- pending, sent, delivered, failed, blocked
    delivery_error TEXT,
    
    -- Compliance verification
    consent_status VARCHAR(50) NOT NULL,  -- consented, opted_out, expired, unknown
    consent_source VARCHAR(100),          -- web_form, phone_call, written, prior_business
    consent_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Opt-out check
    opted_out_at_send BOOLEAN NOT NULL DEFAULT FALSE,
    opt_out_check_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Frequency limits check
    daily_count_at_send INTEGER NOT NULL DEFAULT 0,
    monthly_count_at_send INTEGER NOT NULL DEFAULT 0,
    daily_limit_exceeded BOOLEAN NOT NULL DEFAULT FALSE,
    monthly_limit_exceeded BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Business hours check
    sent_during_business_hours BOOLEAN NOT NULL DEFAULT TRUE,
    local_hour_at_send INTEGER,
    
    -- Location/tenant context
    location_id VARCHAR(255),
    campaign_id VARCHAR(255),
    lead_id VARCHAR(255),
    
    -- Source and attribution
    send_source VARCHAR(100),              -- api, webhook, dashboard, automated
    user_id VARCHAR(255),
    source_ip VARCHAR(45),
    
    -- Provider details
    sms_provider VARCHAR(50),              -- twilio, plivo, etc.
    provider_message_id VARCHAR(255),
    provider_status TEXT,
    
    -- Cost tracking
    message_cost DECIMAL(10, 4),
    cost_currency VARCHAR(3) DEFAULT 'USD',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_sms_send_audit_log_status CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed', 'blocked')),
    CONSTRAINT chk_sms_send_audit_log_consent CHECK (consent_status IN ('consented', 'opted_out', 'expired', 'unknown')),
    CONSTRAINT chk_sms_send_audit_log_type CHECK (message_type IN ('transactional', 'marketing', 'compliance'))
);

-- Indexes for audit log queries
CREATE INDEX idx_sms_audit_log_phone ON sms_send_audit_log(phone_number);
CREATE INDEX idx_sms_audit_log_timestamp ON sms_send_audit_log(send_attempted_at DESC);
CREATE INDEX idx_sms_audit_log_status ON sms_send_audit_log(delivery_status);
CREATE INDEX idx_sms_audit_log_location ON sms_send_audit_log(location_id);
CREATE INDEX idx_sms_audit_log_consent ON sms_send_audit_log(consent_status);
CREATE INDEX idx_sms_audit_log_opted_out ON sms_send_audit_log(opted_out_at_send) WHERE opted_out_at_send = TRUE;
CREATE INDEX idx_sms_audit_log_lead ON sms_send_audit_log(lead_id);
CREATE INDEX idx_sms_audit_log_campaign ON sms_send_audit_log(campaign_id);

-- Composite index for common compliance queries
CREATE INDEX idx_sms_audit_log_compliance ON sms_send_audit_log(phone_number, send_attempted_at DESC, delivery_status);

-- ----------------------------------------------------------------------------
-- SMS Consent Tracking Table
-- ----------------------------------------------------------------------------
-- Tracks consent status and history for all phone numbers.
-- Required for TCPA compliance - explicit consent must be obtained before
-- sending marketing messages.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sms_consent_tracking (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Phone number (normalized to E.164 format)
    phone_number VARCHAR(20) NOT NULL,
    
    -- Consent details
    consent_status VARCHAR(50) NOT NULL,  -- active, revoked, expired, never_obtained
    consent_type VARCHAR(50) NOT NULL,    -- express, implied, prior_business
    consent_source VARCHAR(100) NOT NULL, -- web_form, phone_call, written, text_message
    
    -- Consent timestamps
    consent_obtained_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    consent_revoked_at TIMESTAMP WITH TIME ZONE,
    consent_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Consent details
    consent_text TEXT,                     -- The actual consent text shown to user
    consent_method VARCHAR(50),           -- checkbox, signature, verbal, text_reply
    consent_ip_address VARCHAR(45),
    consent_user_agent TEXT,
    
    -- Location/tenant context
    location_id VARCHAR(255),
    lead_id VARCHAR(255),
    
    -- Consent scope
    consent_scope VARCHAR(50) DEFAULT 'all',  -- all, transactional_only, marketing_only
    message_categories JSONB,                  -- Array of message types consented to
    
    -- Verification
    verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    verification_method VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_sms_consent_status CHECK (consent_status IN ('active', 'revoked', 'expired', 'never_obtained')),
    CONSTRAINT chk_sms_consent_type CHECK (consent_type IN ('express', 'implied', 'prior_business')),
    CONSTRAINT chk_sms_consent_scope CHECK (consent_scope IN ('all', 'transactional_only', 'marketing_only'))
);

-- Indexes for consent lookups
CREATE INDEX idx_sms_consent_phone ON sms_consent_tracking(phone_number);
CREATE INDEX idx_sms_consent_status ON sms_consent_tracking(consent_status);
CREATE INDEX idx_sms_consent_location ON sms_consent_tracking(location_id);
CREATE INDEX idx_sms_consent_lead ON sms_consent_tracking(lead_id);
CREATE INDEX idx_sms_consent_expires ON sms_consent_tracking(consent_expires_at) WHERE consent_expires_at IS NOT NULL;

-- Unique constraint for active consent per phone number
CREATE UNIQUE INDEX uq_sms_consent_active ON sms_consent_tracking(phone_number) 
WHERE consent_status = 'active';

-- ----------------------------------------------------------------------------
-- SMS Compliance Violations Table
-- ----------------------------------------------------------------------------
-- Tracks compliance violations and alerts for monitoring and remediation.
-- Critical for proactive compliance management and audit preparation.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sms_compliance_violations (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Violation details
    violation_type VARCHAR(100) NOT NULL,  -- send_to_opted_out, no_consent, frequency_exceeded, outside_hours
    violation_severity VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    violation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Phone number involved
    phone_number VARCHAR(20) NOT NULL,
    
    -- Violation context
    violation_description TEXT NOT NULL,
    attempted_action TEXT,
    
    -- Location/tenant context
    location_id VARCHAR(255),
    lead_id VARCHAR(255),
    
    -- Detection details
    detected_by VARCHAR(50) NOT NULL,      -- automated, manual, audit
    detection_rule VARCHAR(255),
    
    -- Resolution details
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    resolution_notes TEXT,
    
    -- Impact assessment
    messages_blocked INTEGER DEFAULT 0,
    potential_fines DECIMAL(10, 2),
    risk_level VARCHAR(20) DEFAULT 'medium',
    
    -- Alert details
    alert_sent BOOLEAN DEFAULT FALSE,
    alert_sent_at TIMESTAMP WITH TIME ZONE,
    alert_recipients JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_sms_violation_severity CHECK (violation_severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_sms_violation_risk CHECK (risk_level IN ('low', 'medium', 'high', 'critical'))
);

-- Indexes for violation tracking
CREATE INDEX idx_sms_violations_type ON sms_compliance_violations(violation_type);
CREATE INDEX idx_sms_violations_timestamp ON sms_compliance_violations(violation_timestamp DESC);
CREATE INDEX idx_sms_violations_severity ON sms_compliance_violations(violation_severity);
CREATE INDEX idx_sms_violations_phone ON sms_compliance_violations(phone_number);
CREATE INDEX idx_sms_violations_location ON sms_compliance_violations(location_id);
CREATE INDEX idx_sms_violations_resolved ON sms_compliance_violations(resolved) WHERE resolved = FALSE;

-- ----------------------------------------------------------------------------
-- SMS Opt-Out Confirmation Messages Table
-- ----------------------------------------------------------------------------
-- Tracks opt-out confirmation messages sent to users.
-- Required for TCPA compliance - users must receive confirmation of opt-out.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sms_opt_out_confirmations (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Phone number
    phone_number VARCHAR(20) NOT NULL,
    
    -- Opt-out reference
    opt_out_id UUID NOT NULL REFERENCES sms_opt_outs(id) ON DELETE CASCADE,
    
    -- Confirmation message details
    confirmation_message TEXT NOT NULL,
    confirmation_sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    confirmation_method VARCHAR(50) NOT NULL,  -- sms, email, webhook
    
    -- Delivery status
    delivery_status VARCHAR(50) NOT NULL,  -- pending, sent, delivered, failed
    delivery_error TEXT,
    delivery_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Provider details
    sms_provider VARCHAR(50),
    provider_message_id VARCHAR(255),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_sms_opt_out_conf_status CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed'))
);

-- Indexes for confirmation tracking
CREATE INDEX idx_sms_opt_out_conf_phone ON sms_opt_out_confirmations(phone_number);
CREATE INDEX idx_sms_opt_out_conf_opt_out ON sms_opt_out_confirmations(opt_out_id);
CREATE INDEX idx_sms_opt_out_conf_timestamp ON sms_opt_out_confirmations(confirmation_sent_at DESC);

-- ----------------------------------------------------------------------------
-- Functions and Triggers for Audit Trail Immutability
-- ----------------------------------------------------------------------------

-- Function to prevent updates to audit log records (immutability)
CREATE OR REPLACE FUNCTION prevent_audit_log_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Cannot update immutable audit log record (id: %)', OLD.id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to prevent updates to sms_send_audit_log
CREATE TRIGGER trg_sms_send_audit_log_immutable
    BEFORE UPDATE ON sms_send_audit_log
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_log_update();

-- Function to prevent updates to opt-out records (except re-opt-in fields)
CREATE OR REPLACE FUNCTION prevent_opt_out_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Allow updates to re_opted_in, re_opt_in_timestamp, re_opt_in_method, re_opt_in_reason, updated_at
    IF (
        NEW.re_opted_in IS DISTINCT FROM OLD.re_opted_in OR
        NEW.re_opt_in_timestamp IS DISTINCT FROM OLD.re_opt_in_timestamp OR
        NEW.re_opt_in_method IS DISTINCT FROM OLD.re_opt_in_method OR
        NEW.re_opt_in_reason IS DISTINCT FROM OLD.re_opt_in_reason OR
        NEW.updated_at IS DISTINCT FROM OLD.updated_at
    ) THEN
        RETURN NEW;
    END IF;
    
    RAISE EXCEPTION 'Cannot update opt-out record (id: %) except re-opt-in fields', OLD.id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to prevent updates to sms_opt_outs (except re-opt-in fields)
CREATE TRIGGER trg_sms_opt_outs_immutable
    BEFORE UPDATE ON sms_opt_outs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_opt_out_update();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at timestamps
CREATE TRIGGER trg_sms_opt_outs_updated_at
    BEFORE UPDATE ON sms_opt_outs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_sms_consent_tracking_updated_at
    BEFORE UPDATE ON sms_consent_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_sms_compliance_violations_updated_at
    BEFORE UPDATE ON sms_compliance_violations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- Views for Compliance Reporting
-- ----------------------------------------------------------------------------

-- View for active opt-outs (excluding re-opted-in)
CREATE OR REPLACE VIEW sms_active_opt_outs AS
SELECT 
    id,
    phone_number,
    opt_out_reason,
    opt_out_method,
    opt_out_timestamp,
    location_id,
    confirmation_sent,
    confirmation_timestamp,
    created_at
FROM sms_opt_outs
WHERE re_opted_in = FALSE;

-- View for compliance summary by phone number
CREATE OR REPLACE VIEW sms_compliance_summary AS
SELECT 
    phone_number,
    -- Opt-out status
    (SELECT COUNT(*) FROM sms_opt_outs WHERE phone_number = s.phone_number AND re_opted_in = FALSE) as opt_out_count,
    (SELECT MAX(opt_out_timestamp) FROM sms_opt_outs WHERE phone_number = s.phone_number AND re_opted_in = FALSE) as last_opt_out_at,
    -- Consent status
    (SELECT consent_status FROM sms_consent_tracking WHERE phone_number = s.phone_number AND consent_status = 'active' LIMIT 1) as current_consent_status,
    (SELECT consent_expires_at FROM sms_consent_tracking WHERE phone_number = s.phone_number AND consent_status = 'active' LIMIT 1) as consent_expires_at,
    -- Send statistics
    (SELECT COUNT(*) FROM sms_send_audit_log WHERE phone_number = s.phone_number) as total_sends,
    (SELECT COUNT(*) FROM sms_send_audit_log WHERE phone_number = s.phone_number AND delivery_status = 'delivered') as delivered_count,
    (SELECT COUNT(*) FROM sms_send_audit_log WHERE phone_number = s.phone_number AND delivery_status = 'failed') as failed_count,
    (SELECT MAX(send_attempted_at) FROM sms_send_audit_log WHERE phone_number = s.phone_number) as last_send_at,
    -- Violation count
    (SELECT COUNT(*) FROM sms_compliance_violations WHERE phone_number = s.phone_number AND resolved = FALSE) as active_violations
FROM (SELECT DISTINCT phone_number FROM sms_send_audit_log 
      UNION SELECT DISTINCT phone_number FROM sms_opt_outs 
      UNION SELECT DISTINCT phone_number FROM sms_consent_tracking) s;

-- View for daily compliance metrics
CREATE OR REPLACE VIEW sms_daily_compliance_metrics AS
SELECT 
    DATE(send_attempted_at) as metric_date,
    location_id,
    -- Send metrics
    COUNT(*) as total_send_attempts,
    COUNT(*) FILTER (WHERE delivery_status = 'delivered') as delivered_count,
    COUNT(*) FILTER (WHERE delivery_status = 'failed') as failed_count,
    COUNT(*) FILTER (WHERE opted_out_at_send = TRUE) as attempted_to_opted_out,
    -- Consent metrics
    COUNT(*) FILTER (WHERE consent_status = 'consented') as with_consent,
    COUNT(*) FILTER (WHERE consent_status = 'opted_out') as without_consent,
    COUNT(*) FILTER (WHERE consent_status = 'unknown') as unknown_consent,
    -- Frequency metrics
    COUNT(*) FILTER (WHERE daily_limit_exceeded = TRUE) as daily_limit_blocks,
    COUNT(*) FILTER (WHERE monthly_limit_exceeded = TRUE) as monthly_limit_blocks,
    -- Business hours metrics
    COUNT(*) FILTER (WHERE sent_during_business_hours = FALSE) as outside_business_hours
FROM sms_send_audit_log
GROUP BY DATE(send_attempted_at), location_id;

-- ----------------------------------------------------------------------------
-- Comments for documentation
-- ----------------------------------------------------------------------------

COMMENT ON TABLE sms_opt_outs IS 'Stores all SMS opt-out requests with complete audit trail for TCPA compliance';
COMMENT ON TABLE sms_send_audit_log IS 'Immutable audit log of all SMS send attempts with compliance verification';
COMMENT ON TABLE sms_consent_tracking IS 'Tracks consent status and history for TCPA compliance';
COMMENT ON TABLE sms_compliance_violations IS 'Tracks compliance violations and alerts for monitoring';
COMMENT ON TABLE sms_opt_out_confirmations IS 'Tracks opt-out confirmation messages sent to users';

COMMENT ON VIEW sms_active_opt_outs IS 'View of currently active opt-outs (excluding re-opted-in)';
COMMENT ON VIEW sms_compliance_summary IS 'Summary view of compliance status by phone number';
COMMENT ON VIEW sms_daily_compliance_metrics IS 'Daily compliance metrics for reporting';

-- ============================================================================
-- Migration Complete
-- ============================================================================
-- All SMS compliance tables have been created with proper indexes,
-- constraints, triggers, and views for TCPA compliance.
-- ============================================================================