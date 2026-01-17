-- Lead Recovery & Nurture Engine Database Schema
-- PostgreSQL 15+ compatible
-- Created: January 16, 2026

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
CREATE TYPE lead_status AS ENUM ('new', 'contacted', 'qualified', 'disqualified', 'converted', 'lost');
CREATE TYPE lead_temperature AS ENUM ('hot', 'warm', 'cold', 'unknown');
CREATE TYPE communication_channel AS ENUM ('email', 'sms', 'call', 'voicemail', 'linkedin', 'other');
CREATE TYPE communication_direction AS ENUM ('inbound', 'outbound');
CREATE TYPE communication_status AS ENUM ('sent', 'delivered', 'opened', 'clicked', 'replied', 'failed', 'bounced');
CREATE TYPE nurture_status AS ENUM ('active', 'paused', 'completed', 'cancelled');
CREATE TYPE workflow_status AS ENUM ('running', 'completed', 'failed', 'cancelled');
CREATE TYPE data_quality AS ENUM ('basic', 'enriched', 'validated', 'premium');

-- Core leads table
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic contact information
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    company VARCHAR(200),

    -- Lead metadata
    source VARCHAR(100) NOT NULL DEFAULT 'unknown',
    lead_score INTEGER CHECK (lead_score >= 0 AND lead_score <= 100) DEFAULT 0,
    temperature lead_temperature DEFAULT 'unknown',
    status lead_status DEFAULT 'new',

    -- Enriched data from Apollo/other sources
    apollo_id VARCHAR(50),
    linkedin_url TEXT,
    job_title VARCHAR(200),
    seniority VARCHAR(50),
    company_linkedin TEXT,
    company_industry VARCHAR(100),
    company_size INTEGER,
    company_revenue BIGINT,
    company_website TEXT,

    -- Scoring and intelligence
    scoring_reasoning TEXT,
    data_quality data_quality DEFAULT 'basic',

    -- Assignment and routing
    assigned_agent_id UUID,
    assigned_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    enriched_at TIMESTAMP WITH TIME ZONE,

    -- Indexes for performance
    CONSTRAINT valid_email CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_phone CHECK (phone IS NULL OR phone ~ '^[0-9+\-() ]{10,20}$')
);

-- Lead intelligence details table
CREATE TABLE lead_intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Apollo/enrichment data (JSON for flexibility)
    apollo_data JSONB,
    enrichment_data JSONB,

    -- Scoring details
    behavior_score INTEGER CHECK (behavior_score >= 0 AND behavior_score <= 100),
    temperature lead_temperature NOT NULL,
    reasoning TEXT,
    score_factors JSONB, -- Array of scoring factors

    -- Source and timing
    enrichment_source VARCHAR(50) DEFAULT 'apollo',
    enriched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Uniqueness constraint
    UNIQUE(lead_id, enrichment_source)
);

-- Communication history table
CREATE TABLE communications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Communication details
    channel communication_channel NOT NULL,
    direction communication_direction NOT NULL,
    subject VARCHAR(255),
    content TEXT,

    -- Status and tracking
    status communication_status DEFAULT 'sent',
    external_id VARCHAR(100), -- ID from Twilio, SendGrid, etc.

    -- Timing
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    template_id VARCHAR(100),
    campaign_id VARCHAR(100),
    metadata JSONB, -- Flexible storage for provider-specific data

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Nurture sequences table
CREATE TABLE nurture_sequences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Sequence configuration
    sequence_name VARCHAR(100) NOT NULL,
    sequence_type VARCHAR(50) NOT NULL, -- 'welcome', 'follow-up', 'reengagement', etc.
    current_step INTEGER DEFAULT 1,
    total_steps INTEGER,

    -- Status and timing
    status nurture_status DEFAULT 'active',
    next_action_due TIMESTAMP WITH TIME ZONE,

    -- Metadata
    sequence_config JSONB, -- Flexible configuration
    enrollment_reason VARCHAR(200),

    -- Timestamps
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_action_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Performance tracking
    total_opens INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_replies INTEGER DEFAULT 0
);

-- Agents/team members table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic info
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),

    -- Agent configuration
    is_active BOOLEAN DEFAULT true,
    specializations JSONB, -- Array of specializations (industry, lead type, etc.)
    territory JSONB, -- Geographic or other territory definition
    capacity INTEGER DEFAULT 100, -- Max active leads
    current_load INTEGER DEFAULT 0, -- Current active leads

    -- Performance metrics
    avg_response_time INTEGER, -- In minutes
    conversion_rate DECIMAL(5,2), -- Percentage
    total_leads_handled INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,

    -- Availability
    working_hours JSONB, -- Schedule definition
    timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',
    is_available BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow executions tracking table
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Workflow identification
    workflow_name VARCHAR(100) NOT NULL,
    workflow_version VARCHAR(20) DEFAULT '1.0',
    execution_id VARCHAR(100) UNIQUE NOT NULL, -- n8n execution ID

    -- Execution details
    status workflow_status DEFAULT 'running',
    trigger_type VARCHAR(50), -- 'webhook', 'schedule', 'manual', etc.

    -- Data and results
    input_data JSONB,
    output_data JSONB,
    error_details JSONB,

    -- Performance metrics
    duration_ms INTEGER,
    nodes_executed INTEGER,
    nodes_failed INTEGER,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE,

    -- Associations
    lead_id UUID REFERENCES leads(id), -- If related to specific lead
    triggered_by UUID REFERENCES workflow_executions(id) -- If triggered by another workflow
);

-- System metrics aggregated by hour
CREATE TABLE metrics_hourly (
    hour_bucket TIMESTAMP(0) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(12,4) NOT NULL,
    labels JSONB, -- Flexible labels for segmentation

    PRIMARY KEY (hour_bucket, metric_name, labels),

    -- Ensure hour boundaries
    CHECK (EXTRACT(minute FROM hour_bucket) = 0 AND EXTRACT(second FROM hour_bucket) = 0)
);

-- GDPR/compliance tables
CREATE TABLE consent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Consent details
    consent_type VARCHAR(50) NOT NULL, -- 'email', 'sms', 'calls', 'data_processing'
    granted BOOLEAN NOT NULL,

    -- Context
    ip_address INET,
    user_agent TEXT,
    source_url TEXT,
    consent_text TEXT, -- The actual consent language shown

    -- Timestamps
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- For time-limited consent

    -- Legal tracking
    privacy_policy_version VARCHAR(20),
    terms_version VARCHAR(20)
);

-- Data retention policies
CREATE TABLE data_retention (
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    retention_days INTEGER NOT NULL,
    delete_after TIMESTAMP WITH TIME ZONE NOT NULL,
    reason VARCHAR(200),

    PRIMARY KEY (table_name, record_id)
);

-- Error tracking for dead letter queue
CREATE TABLE error_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Error details
    workflow_name VARCHAR(100) NOT NULL,
    node_name VARCHAR(100),
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    error_stack TEXT,

    -- Original data
    original_data JSONB NOT NULL,
    execution_id VARCHAR(100),

    -- Retry tracking
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,

    -- Resolution
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'retrying', 'resolved', 'abandoned'
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_score_temp ON leads(lead_score DESC, temperature);
CREATE INDEX idx_leads_assigned ON leads(assigned_agent_id) WHERE assigned_agent_id IS NOT NULL;
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_status ON leads(status);

CREATE INDEX idx_intelligence_lead_id ON lead_intelligence(lead_id);
CREATE INDEX idx_intelligence_score ON lead_intelligence(behavior_score DESC);
CREATE INDEX idx_intelligence_enriched ON lead_intelligence(enriched_at);

CREATE INDEX idx_communications_lead_id ON communications(lead_id);
CREATE INDEX idx_communications_channel ON communications(channel);
CREATE INDEX idx_communications_sent_at ON communications(sent_at);
CREATE INDEX idx_communications_status ON communications(status);

CREATE INDEX idx_nurture_next_action ON nurture_sequences(next_action_due) WHERE status = 'active';
CREATE INDEX idx_nurture_lead_status ON nurture_sequences(lead_id, status);
CREATE INDEX idx_nurture_sequence_type ON nurture_sequences(sequence_type);

CREATE INDEX idx_agents_active ON agents(is_active, is_available);
CREATE INDEX idx_agents_capacity ON agents(current_load, capacity);

CREATE INDEX idx_executions_workflow ON workflow_executions(workflow_name, started_at);
CREATE INDEX idx_executions_status ON workflow_executions(status, started_at);
CREATE INDEX idx_executions_lead ON workflow_executions(lead_id) WHERE lead_id IS NOT NULL;

CREATE INDEX idx_metrics_name_time ON metrics_hourly(metric_name, hour_bucket DESC);

CREATE INDEX idx_consent_lead_type ON consent_logs(lead_id, consent_type);
CREATE INDEX idx_consent_granted ON consent_logs(granted_at);

CREATE INDEX idx_retention_delete_time ON data_retention(delete_after) WHERE delete_after <= NOW();

CREATE INDEX idx_error_queue_status ON error_queue(status, created_at);
CREATE INDEX idx_error_queue_retry ON error_queue(next_retry_at) WHERE status = 'pending' AND retry_count < max_retries;

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_error_queue_updated_at BEFORE UPDATE ON error_queue FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for lead activity updates
CREATE OR REPLACE FUNCTION update_lead_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- Update last_activity when communications are added
    IF TG_TABLE_NAME = 'communications' THEN
        UPDATE leads SET last_activity = NOW() WHERE id = NEW.lead_id;
    END IF;

    -- Update last_activity when nurture sequences are updated
    IF TG_TABLE_NAME = 'nurture_sequences' THEN
        UPDATE leads SET last_activity = NOW() WHERE id = NEW.lead_id;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_lead_activity_comms AFTER INSERT ON communications FOR EACH ROW EXECUTE FUNCTION update_lead_activity();
CREATE TRIGGER update_lead_activity_nurture AFTER UPDATE ON nurture_sequences FOR EACH ROW EXECUTE FUNCTION update_lead_activity();

-- Create view for lead summary with latest intelligence
CREATE VIEW v_lead_summary AS
SELECT
    l.id,
    l.email,
    l.first_name,
    l.last_name,
    l.phone,
    l.company,
    l.source,
    l.lead_score,
    l.temperature,
    l.status,
    l.job_title,
    l.company_industry,
    l.company_size,
    l.assigned_agent_id,
    l.created_at,
    l.last_activity,

    -- Latest intelligence
    li.reasoning as score_reasoning,
    li.enriched_at,

    -- Agent details
    a.first_name as agent_first_name,
    a.last_name as agent_last_name,
    a.email as agent_email,

    -- Communication stats
    comm_stats.total_communications,
    comm_stats.last_communication,
    comm_stats.response_rate,

    -- Nurture status
    ns.sequence_name as current_sequence,
    ns.current_step,
    ns.next_action_due

FROM leads l
LEFT JOIN lead_intelligence li ON l.id = li.lead_id
LEFT JOIN agents a ON l.assigned_agent_id = a.id
LEFT JOIN (
    SELECT
        lead_id,
        COUNT(*) as total_communications,
        MAX(sent_at) as last_communication,
        (COUNT(*) FILTER (WHERE status IN ('delivered', 'opened', 'clicked', 'replied'))::FLOAT /
         NULLIF(COUNT(*), 0))::DECIMAL(5,2) as response_rate
    FROM communications
    WHERE direction = 'outbound'
    GROUP BY lead_id
) comm_stats ON l.id = comm_stats.lead_id
LEFT JOIN nurture_sequences ns ON l.id = ns.lead_id AND ns.status = 'active';

-- Create view for agent performance metrics
CREATE VIEW v_agent_performance AS
SELECT
    a.id,
    a.first_name,
    a.last_name,
    a.email,
    a.current_load,
    a.capacity,
    (a.current_load::FLOAT / a.capacity * 100)::DECIMAL(5,1) as utilization_percent,

    -- Lead metrics (last 30 days)
    recent_stats.leads_assigned,
    recent_stats.leads_converted,
    recent_stats.conversion_rate,
    recent_stats.avg_response_hours,

    -- Overall metrics
    a.total_leads_handled,
    a.total_conversions,
    a.conversion_rate as lifetime_conversion_rate

FROM agents a
LEFT JOIN (
    SELECT
        assigned_agent_id,
        COUNT(*) as leads_assigned,
        COUNT(*) FILTER (WHERE status = 'converted') as leads_converted,
        (COUNT(*) FILTER (WHERE status = 'converted')::FLOAT /
         NULLIF(COUNT(*), 0) * 100)::DECIMAL(5,2) as conversion_rate,
        AVG(EXTRACT(EPOCH FROM (
            SELECT MIN(sent_at) FROM communications c
            WHERE c.lead_id = l.id AND c.direction = 'outbound'
        ) - l.created_at) / 3600)::DECIMAL(6,2) as avg_response_hours
    FROM leads l
    WHERE assigned_at >= NOW() - INTERVAL '30 days'
      AND assigned_agent_id IS NOT NULL
    GROUP BY assigned_agent_id
) recent_stats ON a.id = recent_stats.assigned_agent_id
WHERE a.is_active = true;

-- Insert sample data for testing
INSERT INTO agents (id, first_name, last_name, email, specializations, territory, capacity) VALUES
(uuid_generate_v4(), 'Sarah', 'Chen', 'sarah.chen@company.com', '["residential", "first-time-buyers"]', '{"zip_codes": ["90210", "90211", "90212"]}', 25),
(uuid_generate_v4(), 'Mike', 'Rodriguez', 'mike.rodriguez@company.com', '["commercial", "luxury"]', '{"zip_codes": ["90213", "90214", "90215"]}', 20),
(uuid_generate_v4(), 'Jennifer', 'Kim', 'jennifer.kim@company.com', '["investment", "relocation"]', '{"zip_codes": ["90216", "90217", "90218"]}', 30);

-- Create function for automatic data cleanup (GDPR compliance)
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    rec RECORD;
BEGIN
    -- Process data retention policies
    FOR rec IN SELECT * FROM data_retention WHERE delete_after <= NOW()
    LOOP
        CASE rec.table_name
            WHEN 'leads' THEN
                DELETE FROM leads WHERE id = rec.record_id;
            WHEN 'communications' THEN
                DELETE FROM communications WHERE id = rec.record_id;
            WHEN 'workflow_executions' THEN
                DELETE FROM workflow_executions WHERE id = rec.record_id;
            -- Add other tables as needed
        END CASE;

        DELETE FROM data_retention WHERE table_name = rec.table_name AND record_id = rec.record_id;
        deleted_count := deleted_count + 1;
    END LOOP;

    -- Clean up old workflow executions (keep 90 days)
    DELETE FROM workflow_executions WHERE started_at < NOW() - INTERVAL '90 days';

    -- Clean up old metrics (keep 1 year)
    DELETE FROM metrics_hourly WHERE hour_bucket < NOW() - INTERVAL '1 year';

    -- Clean up resolved errors (keep 30 days)
    DELETE FROM error_queue WHERE status = 'resolved' AND resolved_at < NOW() - INTERVAL '30 days';

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schema validation and health check
CREATE OR REPLACE FUNCTION validate_schema()
RETURNS TABLE(check_name TEXT, status TEXT, details TEXT) AS $$
BEGIN
    -- Check for required indexes
    RETURN QUERY
    SELECT
        'indexes_exist'::TEXT,
        CASE WHEN COUNT(*) = 16 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' of 16 required indexes'
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND indexname LIKE 'idx_%';

    -- Check for valid lead data
    RETURN QUERY
    SELECT
        'lead_data_quality'::TEXT,
        CASE WHEN invalid_count = 0 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || invalid_count || ' leads with invalid data'
    FROM (
        SELECT COUNT(*) as invalid_count
        FROM leads
        WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
           OR (phone IS NOT NULL AND phone !~ '^[0-9+\-() ]{10,20}$')
    ) sq;

    -- Check agent capacity
    RETURN QUERY
    SELECT
        'agent_capacity'::TEXT,
        CASE WHEN overloaded_count = 0 THEN 'PASS' ELSE 'WARN' END,
        overloaded_count || ' agents over capacity'
    FROM (
        SELECT COUNT(*) as overloaded_count
        FROM agents
        WHERE current_load > capacity AND is_active = true
    ) sq;

END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your environment)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO n8n_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO n8n_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO n8n_user;

-- Create monitoring user with read-only access
-- CREATE USER monitoring_user WITH PASSWORD 'secure_monitoring_password';
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_user;

COMMENT ON DATABASE lead_recovery_engine IS 'Service 6: Lead Recovery & Nurture Engine - Production Database';

-- Schema version for migrations
CREATE TABLE schema_versions (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_versions (version, description) VALUES
('1.0.0', 'Initial schema for Lead Recovery & Nurture Engine');

-- Final schema summary
SELECT
    'Schema created successfully' as status,
    COUNT(*) as total_tables,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') as total_indexes,
    NOW() as created_at
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';