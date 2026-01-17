-- Service 6 Database Initialization - Step 4: Monitoring and Error Handling Tables
-- PostgreSQL 15+ compatible
-- Creates tables for system monitoring, error tracking, and operational intelligence

-- Error tracking and dead letter queue
CREATE TABLE error_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Error classification
    error_category VARCHAR(50) NOT NULL, -- 'workflow', 'api', 'database', 'external_service'
    error_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'

    -- Source information
    workflow_name VARCHAR(100),
    node_name VARCHAR(100),
    workflow_execution_id UUID REFERENCES workflow_executions(id),
    api_endpoint VARCHAR(200),
    
    -- Error details
    error_message TEXT NOT NULL,
    error_code VARCHAR(50),
    error_stack TEXT,
    
    -- Context data
    original_data JSONB NOT NULL,
    execution_context JSONB,
    environment_info JSONB,
    
    -- Impact assessment
    affected_leads UUID[], -- Array of lead IDs affected
    business_impact TEXT,
    user_facing BOOLEAN DEFAULT false,

    -- Retry mechanism
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    retry_strategy VARCHAR(50) DEFAULT 'exponential_backoff', -- 'immediate', 'linear', 'exponential_backoff'
    backoff_factor DECIMAL(3,2) DEFAULT 2.0,

    -- Resolution tracking
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'retrying', 'resolved', 'abandoned', 'escalated'
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_method VARCHAR(100), -- 'auto_retry', 'manual_fix', 'data_correction', 'workflow_update'
    resolution_notes TEXT,
    resolved_by_agent_id UUID REFERENCES agents(id),

    -- Escalation
    escalated_at TIMESTAMP WITH TIME ZONE,
    escalated_to VARCHAR(100), -- 'engineering', 'management', 'external_vendor'
    escalation_reason TEXT,

    -- Performance impact
    downtime_minutes INTEGER,
    affected_operations INTEGER,
    revenue_impact_cents INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- SLA tracking
    sla_target_minutes INTEGER DEFAULT 60, -- Target resolution time
    sla_breach BOOLEAN GENERATED ALWAYS AS (
        (resolved_at IS NULL AND created_at + INTERVAL '1 minute' * sla_target_minutes < NOW()) OR
        (resolved_at IS NOT NULL AND resolved_at > created_at + INTERVAL '1 minute' * sla_target_minutes)
    ) STORED,

    -- Constraints
    CONSTRAINT error_retry_check CHECK (retry_count <= max_retries),
    CONSTRAINT error_resolution_check CHECK (
        (status != 'resolved') OR 
        (status = 'resolved' AND resolved_at IS NOT NULL)
    ),
    CONSTRAINT error_escalation_check CHECK (
        (escalated_at IS NULL) OR 
        (escalated_at >= created_at AND escalation_reason IS NOT NULL)
    )
);

-- System health monitoring
CREATE TABLE system_health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Check identification
    check_name VARCHAR(100) NOT NULL,
    check_category VARCHAR(50) NOT NULL, -- 'database', 'api', 'external_service', 'workflow'
    check_type VARCHAR(30) NOT NULL, -- 'availability', 'performance', 'data_quality'
    
    -- Check configuration
    check_config JSONB,
    expected_result JSONB,
    tolerance_config JSONB, -- Thresholds for warnings/errors
    
    -- Results
    status VARCHAR(20) NOT NULL, -- 'healthy', 'warning', 'critical', 'unknown'
    result_data JSONB,
    response_time_ms INTEGER,
    
    -- Alerting
    alert_sent BOOLEAN DEFAULT false,
    alert_channels TEXT[], -- 'email', 'slack', 'pagerduty'
    alert_recipients TEXT[],
    
    -- Trends
    previous_status VARCHAR(20),
    status_changed BOOLEAN DEFAULT false,
    consecutive_failures INTEGER DEFAULT 0,
    uptime_percentage DECIMAL(5,2),
    
    -- Dependencies
    dependent_services TEXT[], -- Services that depend on this check
    dependency_of TEXT[], -- Services this check depends on
    
    -- Timestamps
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    next_check_due TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    check_version VARCHAR(10),
    automated BOOLEAN DEFAULT true
);

-- Performance metrics detailed tracking
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Metric identification
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL, -- 'api_performance', 'lead_processing', 'communication', 'database'
    metric_type VARCHAR(30) NOT NULL, -- 'counter', 'gauge', 'histogram', 'timer'
    
    -- Measurement
    value DECIMAL(15,4) NOT NULL,
    unit VARCHAR(20), -- 'count', 'seconds', 'milliseconds', 'percentage', 'bytes'
    
    -- Context
    labels JSONB, -- Flexible dimensions
    source_component VARCHAR(100), -- Which component generated this metric
    environment VARCHAR(20) DEFAULT 'production',
    
    -- Associated entities
    lead_id UUID REFERENCES leads(id),
    agent_id UUID REFERENCES agents(id),
    workflow_execution_id UUID REFERENCES workflow_executions(id),
    
    -- Statistical context
    sample_rate DECIMAL(5,4), -- If this is a sampled metric
    aggregation_period INTEGER, -- Seconds, if this is pre-aggregated
    
    -- Timestamps
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Data quality
    data_quality_score DECIMAL(3,2) DEFAULT 1.0, -- 0-1 confidence in this measurement
    outlier_score DECIMAL(5,2), -- Statistical outlier detection
    
    -- Indexing hint
    time_bucket TIMESTAMP(0) GENERATED ALWAYS AS (
        DATE_TRUNC('minute', measured_at)
    ) STORED
);

-- Alert configurations and history
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Alert identification
    alert_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'threshold', 'anomaly', 'error_rate', 'sla_breach'
    severity VARCHAR(20) NOT NULL, -- 'info', 'warning', 'error', 'critical'
    
    -- Trigger conditions
    trigger_condition JSONB NOT NULL, -- Configuration for what triggers this alert
    threshold_config JSONB,
    
    -- Alert state
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'acknowledged', 'resolved', 'silenced'
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Context
    source_metric VARCHAR(100),
    source_check VARCHAR(100),
    affected_components TEXT[],
    
    -- Alert details
    description TEXT,
    current_value DECIMAL(15,4),
    expected_range DECIMAL(15,4)[2], -- [min, max]
    impact_assessment TEXT,
    
    -- Response tracking
    acknowledged_by_agent_id UUID REFERENCES agents(id),
    resolved_by_agent_id UUID REFERENCES agents(id),
    resolution_notes TEXT,
    
    -- Notification tracking
    notifications_sent JSONB, -- History of notifications
    escalation_level INTEGER DEFAULT 0,
    escalated_at TIMESTAMP WITH TIME ZONE,
    
    -- Pattern analysis
    similar_alerts_count INTEGER DEFAULT 1,
    root_cause_category VARCHAR(100),
    preventable BOOLEAN,
    
    -- SLA impact
    sla_impact_minutes INTEGER DEFAULT 0,
    business_impact VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT alert_acknowledgment_check CHECK (
        (acknowledged_at IS NULL) OR 
        (acknowledged_at >= triggered_at AND acknowledged_by_agent_id IS NOT NULL)
    ),
    CONSTRAINT alert_resolution_check CHECK (
        (resolved_at IS NULL) OR 
        (resolved_at >= triggered_at AND resolved_by_agent_id IS NOT NULL)
    )
);

-- Service Level Agreement tracking
CREATE TABLE sla_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- SLA definition
    sla_name VARCHAR(100) NOT NULL,
    sla_category VARCHAR(50) NOT NULL, -- 'response_time', 'availability', 'data_quality', 'lead_processing'
    service_component VARCHAR(100) NOT NULL,
    
    -- SLA targets
    target_value DECIMAL(10,4) NOT NULL,
    target_unit VARCHAR(20) NOT NULL,
    target_period VARCHAR(20) NOT NULL, -- 'minute', 'hour', 'day', 'week', 'month'
    
    -- Measurement period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Results
    actual_value DECIMAL(10,4),
    measurement_count INTEGER DEFAULT 0,
    sla_met BOOLEAN,
    compliance_percentage DECIMAL(5,2),
    
    -- Breach details
    breach_duration_minutes INTEGER,
    breach_reason TEXT,
    breach_impact TEXT,
    
    -- Improvement tracking
    trend_direction VARCHAR(10), -- 'improving', 'degrading', 'stable'
    previous_period_value DECIMAL(10,4),
    variance_percentage DECIMAL(5,2),
    
    -- Business context
    customer_impact_score INTEGER, -- 1-10 scale
    revenue_impact_cents INTEGER,
    reputation_impact VARCHAR(20),
    
    -- Remediation
    action_items JSONB, -- Array of improvement actions
    responsible_team VARCHAR(100),
    target_improvement_date TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    calculation_method VARCHAR(100),
    data_sources TEXT[],
    confidence_level DECIMAL(3,2) DEFAULT 0.95,
    
    -- Constraints
    CONSTRAINT sla_period_check CHECK (period_end > period_start),
    CONSTRAINT sla_compliance_check CHECK (compliance_percentage >= 0 AND compliance_percentage <= 100)
);

-- System capacity and resource tracking
CREATE TABLE resource_utilization (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Resource identification
    resource_type VARCHAR(50) NOT NULL, -- 'cpu', 'memory', 'disk', 'database_connections', 'api_quota'
    resource_name VARCHAR(100) NOT NULL,
    instance_id VARCHAR(100),
    
    -- Utilization metrics
    current_usage DECIMAL(12,4) NOT NULL,
    maximum_capacity DECIMAL(12,4) NOT NULL,
    utilization_percentage DECIMAL(5,2) GENERATED ALWAYS AS (
        ROUND((current_usage / NULLIF(maximum_capacity, 0)) * 100, 2)
    ) STORED,
    
    -- Thresholds
    warning_threshold DECIMAL(5,2) DEFAULT 80.0,
    critical_threshold DECIMAL(5,2) DEFAULT 90.0,
    status VARCHAR(20) GENERATED ALWAYS AS (
        CASE 
            WHEN utilization_percentage >= critical_threshold THEN 'critical'
            WHEN utilization_percentage >= warning_threshold THEN 'warning'
            ELSE 'normal'
        END
    ) STORED,
    
    -- Trends
    previous_usage DECIMAL(12,4),
    usage_trend VARCHAR(10), -- 'increasing', 'decreasing', 'stable'
    predicted_exhaustion TIMESTAMP WITH TIME ZONE,
    
    -- Context
    measurement_period INTEGER DEFAULT 60, -- Seconds over which this was measured
    peak_usage DECIMAL(12,4),
    average_usage DECIMAL(12,4),
    
    -- Associated load
    concurrent_users INTEGER,
    active_workflows INTEGER,
    database_connections INTEGER,
    
    -- Timestamps
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT resource_capacity_check CHECK (maximum_capacity > 0),
    CONSTRAINT resource_usage_check CHECK (current_usage >= 0)
);

-- Log successful completion
INSERT INTO setup_log (step, status, details, completed_at) 
VALUES (
    '04_create_monitoring_tables', 
    'SUCCESS', 
    'Monitoring tables created: error_queue, system_health_checks, performance_metrics, alerts, sla_tracking, resource_utilization',
    NOW()
) ON CONFLICT (step) DO UPDATE SET 
    status = EXCLUDED.status,
    details = EXCLUDED.details,
    completed_at = EXCLUDED.completed_at;

-- Add table comments for monitoring documentation
COMMENT ON TABLE error_queue IS 'Error tracking and retry mechanism for failed operations';
COMMENT ON TABLE system_health_checks IS 'Automated health monitoring for all system components';
COMMENT ON TABLE performance_metrics IS 'Detailed performance measurements and trending';
COMMENT ON TABLE alerts IS 'Alert configuration and incident response tracking';
COMMENT ON TABLE sla_tracking IS 'Service Level Agreement monitoring and compliance';
COMMENT ON TABLE resource_utilization IS 'System resource usage and capacity planning';

-- Success notification
SELECT 
    'Monitoring tables created successfully' as status,
    COUNT(*) as monitoring_tables_created,
    NOW() as timestamp
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
  AND table_name IN ('error_queue', 'system_health_checks', 'performance_metrics', 'alerts', 'sla_tracking', 'resource_utilization');
