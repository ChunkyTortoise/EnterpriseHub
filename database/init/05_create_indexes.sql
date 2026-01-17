-- Service 6 Database Initialization - Step 5: Performance Indexes
-- PostgreSQL 15+ compatible
-- Creates optimized indexes for query performance

-- Core leads table indexes
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_status_created ON leads(status, created_at DESC);
CREATE INDEX idx_leads_score_temp ON leads(lead_score DESC, temperature) WHERE deleted_at IS NULL;
CREATE INDEX idx_leads_assigned_agent ON leads(assigned_agent_id, status) WHERE assigned_agent_id IS NOT NULL;
CREATE INDEX idx_leads_source_created ON leads(source, created_at DESC);
CREATE INDEX idx_leads_last_activity ON leads(last_activity DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_leads_temperature_score ON leads(temperature, lead_score DESC) WHERE status NOT IN ('converted', 'lost', 'disqualified');
CREATE INDEX idx_leads_priority_created ON leads(priority, created_at DESC) WHERE status = 'new';
CREATE INDEX idx_leads_company_industry ON leads(company_industry) WHERE company_industry IS NOT NULL;

-- Composite index for lead assignment queries
CREATE INDEX idx_leads_assignment_ready ON leads(status, temperature, lead_score DESC, created_at) 
WHERE assigned_agent_id IS NULL AND status = 'new';

-- JSONB indexes for lead behavioral data
CREATE INDEX idx_leads_apollo_id ON leads(apollo_id) WHERE apollo_id IS NOT NULL;
CREATE INDEX idx_leads_phone ON leads(phone) WHERE phone IS NOT NULL;

-- Lead intelligence table indexes
CREATE INDEX idx_intelligence_lead_id ON lead_intelligence(lead_id);
CREATE INDEX idx_intelligence_score_desc ON lead_intelligence(behavior_score DESC, intent_score DESC);
CREATE INDEX idx_intelligence_enriched ON lead_intelligence(enriched_at DESC);
CREATE INDEX idx_intelligence_source ON lead_intelligence(enrichment_source, enriched_at DESC);
CREATE INDEX idx_intelligence_confidence ON lead_intelligence(prediction_confidence DESC) WHERE prediction_confidence > 0.7;

-- JSONB indexes for intelligence data
CREATE INDEX idx_intelligence_apollo_data ON lead_intelligence USING GIN(apollo_data) WHERE apollo_data IS NOT NULL;
CREATE INDEX idx_intelligence_score_factors ON lead_intelligence USING GIN(score_factors) WHERE score_factors IS NOT NULL;

-- Communications table indexes
CREATE INDEX idx_communications_lead_id ON communications(lead_id, sent_at DESC);
CREATE INDEX idx_communications_channel_status ON communications(channel, status, sent_at DESC);
CREATE INDEX idx_communications_direction_time ON communications(direction, sent_at DESC);
CREATE INDEX idx_communications_external_id ON communications(external_id) WHERE external_id IS NOT NULL;
CREATE INDEX idx_communications_campaign ON communications(campaign_id, sent_at DESC) WHERE campaign_id IS NOT NULL;
CREATE INDEX idx_communications_thread ON communications(thread_id, sent_at) WHERE thread_id IS NOT NULL;

-- Performance indexes for communications
CREATE INDEX idx_communications_response_time ON communications(response_time_minutes) WHERE response_time_minutes IS NOT NULL;
CREATE INDEX idx_communications_sentiment ON communications(sentiment_score) WHERE sentiment_score IS NOT NULL;

-- Nurture sequences table indexes
CREATE INDEX idx_nurture_lead_active ON nurture_sequences(lead_id, status) WHERE status = 'active';
CREATE INDEX idx_nurture_next_action ON nurture_sequences(next_action_due) WHERE status = 'active' AND next_action_due <= NOW() + INTERVAL '1 hour';
CREATE INDEX idx_nurture_sequence_type ON nurture_sequences(sequence_type, enrolled_at DESC);
CREATE INDEX idx_nurture_performance ON nurture_sequences(sequence_name, engagement_rate DESC) WHERE status = 'completed';

-- Agents table indexes
CREATE INDEX idx_agents_active_available ON agents(is_active, is_available, current_load, capacity) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_specialization ON agents USING GIN(specializations) WHERE specializations IS NOT NULL;
CREATE INDEX idx_agents_territory ON agents USING GIN(territory) WHERE territory IS NOT NULL;
CREATE INDEX idx_agents_performance ON agents(conversion_rate DESC, avg_response_time_minutes ASC) WHERE is_active = true;
CREATE INDEX idx_agents_capacity ON agents(current_load, capacity) WHERE is_active = true AND current_load < capacity;
CREATE INDEX idx_agents_role_department ON agents(role, department) WHERE is_active = true;

-- Workflow executions indexes
CREATE INDEX idx_executions_workflow_time ON workflow_executions(workflow_name, started_at DESC);
CREATE INDEX idx_executions_status_time ON workflow_executions(status, started_at DESC);
CREATE INDEX idx_executions_lead ON workflow_executions(lead_id, started_at DESC) WHERE lead_id IS NOT NULL;
CREATE INDEX idx_executions_performance ON workflow_executions(workflow_name, duration_ms) WHERE status = 'completed';
CREATE INDEX idx_executions_errors ON workflow_executions(workflow_name, started_at DESC) WHERE status = 'failed';

-- Metrics table indexes
CREATE INDEX idx_metrics_name_time ON metrics_hourly(metric_name, hour_bucket DESC);
CREATE INDEX idx_metrics_labels ON metrics_hourly USING GIN(labels) WHERE labels IS NOT NULL;
CREATE INDEX idx_metrics_recent ON metrics_hourly(hour_bucket DESC) WHERE hour_bucket > NOW() - INTERVAL '7 days';

-- Compliance table indexes
CREATE INDEX idx_consent_lead_type ON consent_logs(lead_id, consent_type, granted_at DESC);
CREATE INDEX idx_consent_granted ON consent_logs(granted_at DESC, granted) WHERE granted = true;
CREATE INDEX idx_consent_expires ON consent_logs(expires_at) WHERE expires_at IS NOT NULL AND expires_at > NOW();
CREATE INDEX idx_consent_withdrawal ON consent_logs(lead_id, consent_type) WHERE granted = false;

CREATE INDEX idx_retention_delete_time ON data_retention(delete_after) WHERE delete_after <= NOW() + INTERVAL '7 days';
CREATE INDEX idx_retention_table_record ON data_retention(table_name, record_id);
CREATE INDEX idx_retention_legal_hold ON data_retention(legal_hold, legal_hold_expires) WHERE legal_hold = true;

CREATE INDEX idx_dsr_status_due ON data_subject_requests(status, due_date) WHERE status NOT IN ('completed', 'rejected');
CREATE INDEX idx_dsr_email_status ON data_subject_requests(requester_email, status);
CREATE INDEX idx_dsr_assigned ON data_subject_requests(assigned_to_agent_id, due_date) WHERE assigned_to_agent_id IS NOT NULL;

-- Audit log indexes (for compliance queries)
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id, created_at DESC);
CREATE INDEX idx_audit_user_time ON audit_log(user_id, created_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_operation_time ON audit_log(operation, created_at DESC);
CREATE INDEX idx_audit_recent ON audit_log(created_at DESC) WHERE created_at > NOW() - INTERVAL '30 days';

-- Monitoring table indexes
CREATE INDEX idx_error_queue_status_time ON error_queue(status, created_at DESC);
CREATE INDEX idx_error_queue_retry ON error_queue(next_retry_at) WHERE status = 'pending' AND retry_count < max_retries;
CREATE INDEX idx_error_queue_workflow ON error_queue(workflow_name, created_at DESC);
CREATE INDEX idx_error_queue_severity ON error_queue(severity, created_at DESC) WHERE status IN ('pending', 'retrying');
CREATE INDEX idx_error_queue_sla_breach ON error_queue(sla_breach, created_at DESC) WHERE sla_breach = true;

CREATE INDEX idx_health_checks_status ON system_health_checks(check_name, status, checked_at DESC);
CREATE INDEX idx_health_checks_category ON system_health_checks(check_category, status, checked_at DESC);
CREATE INDEX idx_health_checks_alerts ON system_health_checks(alert_sent, status) WHERE status IN ('warning', 'critical');

CREATE INDEX idx_performance_metrics_name_time ON performance_metrics(metric_name, measured_at DESC);
CREATE INDEX idx_performance_metrics_category ON performance_metrics(metric_category, measured_at DESC);
CREATE INDEX idx_performance_metrics_bucket ON performance_metrics(time_bucket DESC);
CREATE INDEX idx_performance_metrics_labels ON performance_metrics USING GIN(labels) WHERE labels IS NOT NULL;

CREATE INDEX idx_alerts_status_severity ON alerts(status, severity, triggered_at DESC);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged_by_agent_id, acknowledged_at DESC) WHERE acknowledged_by_agent_id IS NOT NULL;
CREATE INDEX idx_alerts_escalation ON alerts(escalation_level, escalated_at DESC) WHERE escalation_level > 0;

CREATE INDEX idx_sla_tracking_component ON sla_tracking(service_component, period_start DESC);
CREATE INDEX idx_sla_tracking_breaches ON sla_tracking(sla_met, compliance_percentage) WHERE sla_met = false;
CREATE INDEX idx_sla_tracking_period ON sla_tracking(period_start DESC, period_end DESC);

CREATE INDEX idx_resource_utilization_status ON resource_utilization(resource_type, status, measured_at DESC);
CREATE INDEX idx_resource_utilization_critical ON resource_utilization(utilization_percentage DESC, measured_at DESC) WHERE status = 'critical';

-- Specialized indexes for common query patterns

-- Lead scoring and assignment queries
CREATE INDEX idx_leads_scoring_profile ON leads(temperature, lead_score DESC, company_industry, created_at) 
WHERE status = 'new' AND deleted_at IS NULL;

-- Communication effectiveness analysis
CREATE INDEX idx_communications_effectiveness ON communications(lead_id, channel, status, sent_at DESC) 
WHERE direction = 'outbound' AND status IN ('delivered', 'opened', 'clicked', 'replied');

-- Agent performance queries
CREATE INDEX idx_agents_performance_metrics ON agents(
    conversion_rate DESC, 
    avg_response_time_minutes ASC, 
    current_load,
    last_activity DESC
) WHERE is_active = true AND deleted_at IS NULL;

-- Workflow monitoring and debugging
CREATE INDEX idx_workflow_debugging ON workflow_executions(
    workflow_name, 
    status, 
    started_at DESC, 
    duration_ms
) WHERE started_at > NOW() - INTERVAL '24 hours';

-- Time-series optimizations for metrics
CREATE INDEX idx_metrics_time_series ON metrics_hourly(metric_name, hour_bucket DESC)
WHERE hour_bucket > NOW() - INTERVAL '90 days';

-- Partial indexes for hot data
CREATE INDEX idx_leads_hot_prospects ON leads(lead_score DESC, last_activity DESC)
WHERE temperature IN ('hot', 'warm') AND status NOT IN ('converted', 'lost', 'disqualified') AND deleted_at IS NULL;

CREATE INDEX idx_communications_recent_activity ON communications(lead_id, sent_at DESC)
WHERE sent_at > NOW() - INTERVAL '30 days';

CREATE INDEX idx_nurture_active_urgent ON nurture_sequences(next_action_due, lead_id)
WHERE status = 'active' AND next_action_due <= NOW() + INTERVAL '2 hours';

-- Log successful completion
INSERT INTO setup_log (step, status, details, completed_at) 
VALUES (
    '05_create_indexes', 
    'SUCCESS', 
    'Performance indexes created for all tables with query optimization',
    NOW()
) ON CONFLICT (step) DO UPDATE SET 
    status = EXCLUDED.status,
    details = EXCLUDED.details,
    completed_at = EXCLUDED.completed_at;

-- Create index usage tracking view for monitoring
CREATE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        WHEN idx_scan < 1000 THEN 'MODERATE_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_category
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Success notification with index count
SELECT 
    'Performance indexes created successfully' as status,
    COUNT(*) as total_indexes_created,
    NOW() as timestamp
FROM pg_indexes 
WHERE schemaname = 'public' AND indexname LIKE 'idx_%';
