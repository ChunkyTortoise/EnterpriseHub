-- Service 6 Database Initialization - Step 3: GDPR and Compliance Tables
-- PostgreSQL 15+ compatible
-- Creates tables for data privacy, consent management, and compliance tracking

-- GDPR/compliance consent tracking
CREATE TABLE consent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Consent details
    consent_type VARCHAR(50) NOT NULL, -- 'email', 'sms', 'calls', 'data_processing', 'marketing'
    granted BOOLEAN NOT NULL,
    consent_level VARCHAR(20) DEFAULT 'explicit', -- 'explicit', 'implied', 'legitimate_interest'

    -- Legal basis (GDPR Article 6)
    legal_basis VARCHAR(50), -- 'consent', 'contract', 'legal_obligation', 'vital_interests', 'public_task', 'legitimate_interests'
    legal_basis_details TEXT,

    -- Context and evidence
    ip_address INET,
    user_agent TEXT,
    source_url TEXT,
    source_campaign VARCHAR(100),
    consent_text TEXT, -- The actual consent language shown
    consent_method VARCHAR(50), -- 'web_form', 'email_link', 'phone_call', 'in_person', 'api'
    
    -- Double opt-in tracking
    confirmation_token VARCHAR(100),
    confirmed_at TIMESTAMP WITH TIME ZONE,
    confirmation_ip INET,

    -- Withdrawal tracking
    withdrawal_reason TEXT,
    withdrawal_method VARCHAR(50),

    -- Timestamps
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- For time-limited consent
    last_confirmed TIMESTAMP WITH TIME ZONE,

    -- Legal tracking
    privacy_policy_version VARCHAR(20),
    terms_version VARCHAR(20),
    gdpr_version VARCHAR(20) DEFAULT 'current',
    
    -- Audit trail
    processed_by_agent_id UUID REFERENCES agents(id),
    processing_notes TEXT,

    -- Data retention
    retain_until TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT consent_expiry_check CHECK (
        (expires_at IS NULL) OR (expires_at > granted_at)
    ),
    CONSTRAINT consent_confirmation_check CHECK (
        (consent_level != 'explicit') OR 
        (confirmed_at IS NOT NULL AND confirmation_token IS NOT NULL)
    )
);

-- Data retention policies and tracking
CREATE TABLE data_retention (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    
    -- Retention configuration
    retention_days INTEGER NOT NULL,
    retention_reason VARCHAR(200),
    delete_after TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Legal requirements
    legal_hold BOOLEAN DEFAULT false,
    legal_hold_reason TEXT,
    legal_hold_expires TIMESTAMP WITH TIME ZONE,
    
    -- Processing status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'on_hold'
    last_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deletion_attempts INTEGER DEFAULT 0,
    
    -- Metadata
    created_by_agent_id UUID REFERENCES agents(id),
    created_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT retention_days_check CHECK (retention_days > 0 AND retention_days <= 3650),
    CONSTRAINT retention_legal_hold_check CHECK (
        (legal_hold = false) OR 
        (legal_hold = true AND legal_hold_reason IS NOT NULL)
    ),
    
    -- Unique constraint per record
    UNIQUE(table_name, record_id)
);

-- Data subject requests (GDPR Article 15-22)
CREATE TABLE data_subject_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Request identification
    request_id VARCHAR(50) UNIQUE NOT NULL, -- Human-readable ID for tracking
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    
    -- Requester information
    requester_email email_address NOT NULL,
    requester_name VARCHAR(200),
    identity_verified BOOLEAN DEFAULT false,
    verification_method VARCHAR(50),
    verification_notes TEXT,
    
    -- Request details
    request_type VARCHAR(30) NOT NULL, -- 'access', 'rectification', 'erasure', 'restriction', 'portability', 'objection'
    request_description TEXT,
    specific_data_requested TEXT,
    
    -- Processing status
    status VARCHAR(20) DEFAULT 'received', -- 'received', 'verifying', 'processing', 'completed', 'rejected', 'extended'
    priority priority_level DEFAULT 'medium',
    
    -- Legal timeline (GDPR: 30 days, can extend to 90)
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    extended_date TIMESTAMP WITH TIME ZONE,
    extension_reason TEXT,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Processing details
    assigned_to_agent_id UUID REFERENCES agents(id),
    processing_notes TEXT,
    legal_review_required BOOLEAN DEFAULT false,
    legal_review_notes TEXT,
    
    -- Response details
    response_method VARCHAR(20), -- 'email', 'postal', 'secure_portal'
    response_sent_at TIMESTAMP WITH TIME ZONE,
    response_data JSONB, -- Summary of data provided/actions taken
    
    -- Compliance tracking
    sla_met BOOLEAN,
    escalation_level INTEGER DEFAULT 0,
    compliance_notes TEXT,
    
    -- Communication trail
    communications_log JSONB, -- Array of communication records
    
    CONSTRAINT dsr_due_date_check CHECK (due_date > received_at),
    CONSTRAINT dsr_extension_check CHECK (
        (extended_date IS NULL) OR 
        (extended_date > due_date AND extension_reason IS NOT NULL)
    )
);

-- Audit log for all data changes (GDPR Article 5.2 - accountability)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What changed
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    
    -- Change details
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[], -- Array of field names that changed
    
    -- Who made the change
    user_id UUID,
    user_email VARCHAR(255),
    user_agent TEXT,
    ip_address INET,
    
    -- Why it changed
    change_reason VARCHAR(200),
    business_justification TEXT,
    automated BOOLEAN DEFAULT false,
    api_endpoint VARCHAR(200),
    
    -- When
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional context
    session_id VARCHAR(100),
    transaction_id VARCHAR(100),
    
    -- Compliance
    gdpr_lawful_basis VARCHAR(50),
    retention_period INTEGER, -- Days to retain this audit record
    
    -- Performance
    processing_time_ms INTEGER
);

-- Data processing activities register (GDPR Article 30)
CREATE TABLE processing_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Activity identification
    activity_name VARCHAR(200) NOT NULL,
    activity_description TEXT NOT NULL,
    activity_category VARCHAR(100), -- 'marketing', 'sales', 'support', 'analytics'
    
    -- Legal basis
    lawful_basis VARCHAR(50) NOT NULL,
    special_category_basis VARCHAR(50), -- If processing special category data
    
    -- Data details
    data_categories TEXT[], -- Types of personal data processed
    data_subjects TEXT[], -- Categories of data subjects
    data_sources TEXT[], -- Where data comes from
    
    -- Retention
    retention_period INTEGER, -- Days
    retention_criteria TEXT,
    
    -- Recipients and transfers
    recipients TEXT[], -- Who receives the data
    third_country_transfers BOOLEAN DEFAULT false,
    transfer_safeguards TEXT,
    
    -- Technical and organizational measures
    security_measures JSONB,
    data_protection_measures JSONB,
    
    -- Ownership
    controller_name VARCHAR(200),
    controller_contact VARCHAR(255),
    dpo_contact VARCHAR(255), -- Data Protection Officer
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    review_required_by TIMESTAMP WITH TIME ZONE,
    last_reviewed TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data breach incidents (GDPR Article 33-34)
CREATE TABLE data_breaches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Incident identification
    incident_id VARCHAR(50) UNIQUE NOT NULL,
    incident_type VARCHAR(50) NOT NULL, -- 'confidentiality', 'integrity', 'availability'
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    
    -- Incident details
    description TEXT NOT NULL,
    affected_records_count INTEGER,
    affected_data_categories TEXT[],
    affected_individuals UUID[], -- Array of lead IDs
    
    -- Discovery and notification
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL,
    discovered_by VARCHAR(200),
    reported_to_dpa BOOLEAN DEFAULT false,
    dpa_notification_date TIMESTAMP WITH TIME ZONE,
    individuals_notified BOOLEAN DEFAULT false,
    notification_date TIMESTAMP WITH TIME ZONE,
    
    -- Impact assessment
    likely_consequences TEXT,
    risk_to_rights_freedoms VARCHAR(20), -- 'low', 'medium', 'high'
    measures_taken TEXT,
    measures_planned TEXT,
    
    -- Investigation
    root_cause TEXT,
    investigation_notes TEXT,
    investigation_completed BOOLEAN DEFAULT false,
    
    -- Legal requirements
    notification_required BOOLEAN,
    notification_reasoning TEXT,
    
    -- Resolution
    status VARCHAR(20) DEFAULT 'investigating', -- 'investigating', 'contained', 'resolved', 'closed'
    resolved_at TIMESTAMP WITH TIME ZONE,
    lessons_learned TEXT,
    
    -- Accountability
    assigned_to UUID REFERENCES agents(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Log successful completion
INSERT INTO setup_log (step, status, details, completed_at) 
VALUES (
    '03_create_compliance_tables', 
    'SUCCESS', 
    'Compliance tables created: consent_logs, data_retention, data_subject_requests, audit_log, processing_activities, data_breaches',
    NOW()
) ON CONFLICT (step) DO UPDATE SET 
    status = EXCLUDED.status,
    details = EXCLUDED.details,
    completed_at = EXCLUDED.completed_at;

-- Add table comments for compliance documentation
COMMENT ON TABLE consent_logs IS 'GDPR consent tracking with legal basis and audit trail';
COMMENT ON TABLE data_retention IS 'Automated data retention and deletion management';
COMMENT ON TABLE data_subject_requests IS 'GDPR Article 15-22 data subject rights requests';
COMMENT ON TABLE audit_log IS 'Complete audit trail for accountability (GDPR Article 5.2)';
COMMENT ON TABLE processing_activities IS 'Record of processing activities (GDPR Article 30)';
COMMENT ON TABLE data_breaches IS 'Data breach incident management (GDPR Article 33-34)';

-- Create compliance role for restricted access
-- Note: This would typically be done by DBA in production
-- CREATE ROLE compliance_officer;
-- GRANT SELECT, INSERT, UPDATE ON consent_logs, data_subject_requests, audit_log TO compliance_officer;
-- GRANT ALL ON data_retention, processing_activities, data_breaches TO compliance_officer;

-- Success notification
SELECT 
    'Compliance tables created successfully' as status,
    COUNT(*) as compliance_tables_created,
    NOW() as timestamp
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
  AND table_name IN ('consent_logs', 'data_retention', 'data_subject_requests', 'audit_log', 'processing_activities', 'data_breaches');
