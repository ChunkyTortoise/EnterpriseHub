-- Service 6 Database Initialization - Step 2: Core Tables
-- PostgreSQL 15+ compatible
-- Creates all core tables for the Lead Recovery & Nurture Engine

-- Setup tracking table (must be first)
CREATE TABLE IF NOT EXISTS setup_log (
    step VARCHAR(50) PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    details TEXT,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Core leads table - central entity
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic contact information
    email email_address UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone phone_number,
    company VARCHAR(200),

    -- Lead metadata
    source VARCHAR(100) NOT NULL DEFAULT 'unknown',
    lead_score percentage_score DEFAULT 0,
    temperature lead_temperature DEFAULT 'unknown',
    status lead_status DEFAULT 'new',
    priority priority_level DEFAULT 'medium',

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
    timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',

    -- Location data
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(50) DEFAULT 'US',
    postal_code VARCHAR(20),

    -- Scoring and intelligence
    scoring_reasoning TEXT,
    data_quality data_quality DEFAULT 'basic',
    last_score_update TIMESTAMP WITH TIME ZONE,

    -- Assignment and routing
    assigned_agent_id UUID,
    assigned_at TIMESTAMP WITH TIME ZONE,
    assignment_reason TEXT,

    -- Behavioral tracking
    website_visits INTEGER DEFAULT 0,
    email_opens INTEGER DEFAULT 0,
    email_clicks INTEGER DEFAULT 0,
    form_submissions INTEGER DEFAULT 0,
    call_attempts INTEGER DEFAULT 0,
    social_engagement INTEGER DEFAULT 0,

    -- Conversion tracking
    conversion_event VARCHAR(100),
    conversion_value DECIMAL(10,2),
    conversion_date TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    enriched_at TIMESTAMP WITH TIME ZONE,
    last_contacted TIMESTAMP WITH TIME ZONE,

    -- Soft delete support
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_reason TEXT,

    -- Data constraints
    CONSTRAINT leads_email_check CHECK (email IS NOT NULL AND length(email) > 5),
    CONSTRAINT leads_name_check CHECK (length(first_name) > 0 AND length(last_name) > 0),
    CONSTRAINT leads_score_reasoning CHECK (
        (lead_score > 50 AND scoring_reasoning IS NOT NULL) OR lead_score <= 50
    )
);

-- Lead intelligence details table - stores enrichment data
CREATE TABLE lead_intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Apollo/enrichment data (JSON for flexibility)
    apollo_data JSONB,
    enrichment_data JSONB,
    behavioral_data JSONB,

    -- Scoring details
    behavior_score percentage_score,
    intent_score percentage_score,
    fit_score percentage_score,
    engagement_score percentage_score,
    temperature lead_temperature NOT NULL,
    
    -- Detailed reasoning
    reasoning TEXT,
    score_factors JSONB, -- Array of scoring factors with weights
    prediction_confidence DECIMAL(5,2), -- ML model confidence

    -- Source and timing
    enrichment_source VARCHAR(50) DEFAULT 'apollo',
    model_version VARCHAR(20),
    enriched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Performance tracking
    enrichment_duration_ms INTEGER,
    api_calls_made INTEGER DEFAULT 1,
    cost_cents INTEGER,

    -- Uniqueness constraint per source
    UNIQUE(lead_id, enrichment_source, enriched_at)
);

-- Communication history table - tracks all interactions
CREATE TABLE communications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Communication details
    channel communication_channel NOT NULL,
    direction communication_direction NOT NULL,
    subject VARCHAR(500),
    content TEXT,
    content_snippet VARCHAR(200), -- First 200 chars for quick display

    -- Status and tracking
    status communication_status DEFAULT 'sent',
    external_id VARCHAR(100), -- ID from Twilio, SendGrid, etc.
    thread_id VARCHAR(100), -- For grouping related communications

    -- Timing
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE,

    -- Response tracking
    response_time_minutes INTEGER, -- Time to respond if inbound
    sentiment_score DECIMAL(3,2), -- -1 to 1, from sentiment analysis
    
    -- Campaign and automation
    template_id VARCHAR(100),
    campaign_id VARCHAR(100),
    automation_id VARCHAR(100),
    sequence_step INTEGER,

    -- Metadata
    metadata JSONB, -- Provider-specific data, tracking pixels, etc.
    attachments JSONB, -- File attachments info

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Performance
    processing_time_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Data quality constraints
    CONSTRAINT comms_content_check CHECK (
        (content IS NOT NULL AND length(content) > 0) OR 
        (channel = 'call' AND content IS NULL)
    ),
    CONSTRAINT comms_timing_check CHECK (
        (direction = 'outbound' AND sent_at IS NOT NULL) OR
        (direction = 'inbound')
    )
);

-- Nurture sequences table - manages automated follow-up
CREATE TABLE nurture_sequences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Sequence configuration
    sequence_name VARCHAR(100) NOT NULL,
    sequence_version VARCHAR(20) DEFAULT '1.0',
    sequence_type VARCHAR(50) NOT NULL, -- 'welcome', 'follow-up', 'reengagement', etc.
    current_step INTEGER DEFAULT 1,
    total_steps INTEGER,
    
    -- Conditional logic
    conditions_met JSONB, -- Track which conditions triggered this sequence
    exit_conditions JSONB, -- Conditions that would stop the sequence

    -- Status and timing
    status nurture_status DEFAULT 'active',
    next_action_due TIMESTAMP WITH TIME ZONE,
    next_action_type communication_channel,
    
    -- Personalization
    personalization_data JSONB, -- Data for personalizing templates
    language_preference VARCHAR(10) DEFAULT 'en',

    -- Performance tracking
    sequence_config JSONB, -- Full configuration snapshot
    enrollment_reason VARCHAR(200),
    completion_reason VARCHAR(200),
    
    -- Statistics
    total_opens INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_replies INTEGER DEFAULT 0,
    total_unsubscribes INTEGER DEFAULT 0,
    
    -- Effectiveness metrics
    engagement_rate DECIMAL(5,2), -- Calculated periodically
    conversion_probability DECIMAL(5,2), -- ML prediction

    -- Timestamps
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_action_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    paused_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT nurture_steps_check CHECK (current_step <= total_steps),
    CONSTRAINT nurture_dates_check CHECK (
        (completed_at IS NULL) OR 
        (completed_at >= enrolled_at)
    )
);

-- Agents/team members table - manages sales team
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic info
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email email_address UNIQUE NOT NULL,
    phone phone_number,
    employee_id VARCHAR(50),
    
    -- Role and permissions
    role agent_role DEFAULT 'junior',
    department VARCHAR(100),
    manager_id UUID REFERENCES agents(id),

    -- Agent configuration
    is_active BOOLEAN DEFAULT true,
    is_available BOOLEAN DEFAULT true,
    specializations JSONB, -- Array of specializations
    territory JSONB, -- Geographic or segment territory
    capacity INTEGER DEFAULT 100, -- Max active leads
    current_load INTEGER DEFAULT 0, -- Current active leads
    
    -- Skills and certifications
    skills JSONB, -- Technical skills, certifications
    languages JSONB, -- Languages spoken
    
    -- Performance metrics (calculated periodically)
    avg_response_time_minutes INTEGER,
    conversion_rate DECIMAL(5,2), -- Percentage
    total_leads_handled INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12,2) DEFAULT 0,
    
    -- Quality metrics
    customer_satisfaction DECIMAL(3,2), -- 1-5 rating
    call_quality_score DECIMAL(5,2),
    email_response_quality DECIMAL(5,2),

    -- Availability and scheduling
    working_hours JSONB, -- Schedule definition
    timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',
    vacation_start TIMESTAMP WITH TIME ZONE,
    vacation_end TIMESTAMP WITH TIME ZONE,
    
    -- Compensation (if tracking)
    base_salary DECIMAL(10,2),
    commission_rate DECIMAL(5,2),
    bonus_target DECIMAL(10,2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Soft delete
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT agents_capacity_check CHECK (capacity > 0 AND capacity <= 1000),
    CONSTRAINT agents_load_check CHECK (current_load >= 0 AND current_load <= capacity),
    CONSTRAINT agents_vacation_check CHECK (
        (vacation_start IS NULL AND vacation_end IS NULL) OR
        (vacation_start IS NOT NULL AND vacation_end IS NOT NULL AND vacation_end > vacation_start)
    )
);

-- Workflow executions tracking table - n8n integration
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Workflow identification
    workflow_name VARCHAR(100) NOT NULL,
    workflow_version VARCHAR(20) DEFAULT '1.0',
    execution_id VARCHAR(100) UNIQUE NOT NULL, -- n8n execution ID
    parent_execution_id UUID REFERENCES workflow_executions(id),

    -- Execution details
    status workflow_status DEFAULT 'running',
    trigger_type VARCHAR(50), -- 'webhook', 'schedule', 'manual', etc.
    trigger_data JSONB,

    -- Data and results
    input_data JSONB,
    output_data JSONB,
    error_details JSONB,
    
    -- Environment info
    server_instance VARCHAR(100),
    n8n_version VARCHAR(20),

    -- Performance metrics
    duration_ms INTEGER,
    nodes_executed INTEGER,
    nodes_failed INTEGER,
    memory_used_mb INTEGER,
    cpu_time_ms INTEGER,

    -- Cost tracking
    api_calls_made INTEGER DEFAULT 0,
    external_costs_cents INTEGER DEFAULT 0,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE,
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Associations
    lead_id UUID REFERENCES leads(id), -- If related to specific lead
    triggered_by_lead_event BOOLEAN DEFAULT false,
    triggered_by_schedule BOOLEAN DEFAULT false,
    
    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    CONSTRAINT workflow_duration_check CHECK (
        (finished_at IS NULL) OR 
        (duration_ms IS NULL) OR
        (EXTRACT(EPOCH FROM (finished_at - started_at)) * 1000 >= duration_ms - 1000)
    )
);

-- System metrics aggregated by hour
CREATE TABLE metrics_hourly (
    hour_bucket TIMESTAMP(0) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(12,4) NOT NULL,
    metric_unit VARCHAR(20), -- 'count', 'percent', 'dollars', 'ms', etc.
    labels JSONB, -- Flexible labels for segmentation

    -- Aggregation metadata
    data_points INTEGER DEFAULT 1,
    min_value DECIMAL(12,4),
    max_value DECIMAL(12,4),
    std_dev DECIMAL(12,4),

    PRIMARY KEY (hour_bucket, metric_name, labels),

    -- Ensure hour boundaries
    CHECK (EXTRACT(minute FROM hour_bucket) = 0 AND EXTRACT(second FROM hour_bucket) = 0),
    
    -- Data quality checks
    CONSTRAINT metrics_value_check CHECK (
        metric_value IS NOT NULL AND 
        (min_value IS NULL OR metric_value >= min_value) AND
        (max_value IS NULL OR metric_value <= max_value)
    )
);

-- Log successful completion
INSERT INTO setup_log (step, status, details, completed_at) 
VALUES (
    '02_create_tables', 
    'SUCCESS', 
    'Core tables created: leads, lead_intelligence, communications, nurture_sequences, agents, workflow_executions, metrics_hourly',
    NOW()
) ON CONFLICT (step) DO UPDATE SET 
    status = EXCLUDED.status,
    details = EXCLUDED.details,
    completed_at = EXCLUDED.completed_at;

-- Add table comments for documentation
COMMENT ON TABLE leads IS 'Core lead records with contact info, scoring, and assignment';
COMMENT ON TABLE lead_intelligence IS 'Enriched data and AI scoring for leads';
COMMENT ON TABLE communications IS 'All communications (email, SMS, calls) with leads';
COMMENT ON TABLE nurture_sequences IS 'Automated follow-up sequences and campaigns';
COMMENT ON TABLE agents IS 'Sales team members and their performance metrics';
COMMENT ON TABLE workflow_executions IS 'n8n workflow execution tracking';
COMMENT ON TABLE metrics_hourly IS 'System performance metrics aggregated by hour';

-- Success notification
SELECT 
    'Core tables created successfully' as status,
    COUNT(*) as tables_created,
    NOW() as timestamp
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
  AND table_name IN ('leads', 'lead_intelligence', 'communications', 'nurture_sequences', 'agents', 'workflow_executions', 'metrics_hourly');
