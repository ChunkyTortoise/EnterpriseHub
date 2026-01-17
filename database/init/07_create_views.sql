-- Service 6 Database Initialization - Step 7: Views and Materialized Views
-- PostgreSQL 15+ compatible
-- Creates optimized views for common queries and reporting

-- Lead summary view with comprehensive information
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
    l.priority,
    l.job_title,
    l.company_industry,
    l.company_size,
    l.assigned_agent_id,
    l.created_at,
    l.last_activity,
    l.last_contacted,

    -- Latest intelligence data
    li.reasoning as score_reasoning,
    li.behavior_score,
    li.intent_score,
    li.fit_score,
    li.engagement_score,
    li.prediction_confidence,
    li.enriched_at,

    -- Agent information
    a.first_name as agent_first_name,
    a.last_name as agent_last_name,
    a.email as agent_email,
    a.role as agent_role,

    -- Communication statistics
    comm_stats.total_communications,
    comm_stats.last_communication,
    comm_stats.response_rate,
    comm_stats.avg_sentiment,
    comm_stats.total_opens,
    comm_stats.total_clicks,

    -- Nurture sequence status
    ns.sequence_name as current_sequence,
    ns.current_step,
    ns.total_steps,
    ns.next_action_due,
    ns.engagement_rate as sequence_engagement,

    -- Calculated fields
    CASE 
        WHEN l.last_activity > NOW() - INTERVAL '7 days' THEN 'active'
        WHEN l.last_activity > NOW() - INTERVAL '30 days' THEN 'moderate'
        WHEN l.last_activity > NOW() - INTERVAL '90 days' THEN 'low'
        ELSE 'dormant'
    END as activity_level,

    -- Days since creation and last activity
    EXTRACT(DAY FROM NOW() - l.created_at) as days_since_creation,
    EXTRACT(DAY FROM NOW() - l.last_activity) as days_since_activity,

    -- Conversion probability (if available)
    CASE 
        WHEN l.temperature = 'hot' AND l.lead_score > 80 THEN 'very_high'
        WHEN l.temperature = 'hot' AND l.lead_score > 60 THEN 'high'
        WHEN l.temperature = 'warm' AND l.lead_score > 70 THEN 'high'
        WHEN l.temperature = 'warm' AND l.lead_score > 50 THEN 'medium'
        WHEN l.temperature = 'cold' AND l.lead_score > 60 THEN 'medium'
        ELSE 'low'
    END as conversion_probability

FROM leads l
LEFT JOIN (
    SELECT DISTINCT ON (lead_id) 
        lead_id, reasoning, behavior_score, intent_score, 
        fit_score, engagement_score, prediction_confidence, enriched_at
    FROM lead_intelligence 
    ORDER BY lead_id, enriched_at DESC
) li ON l.id = li.lead_id

LEFT JOIN agents a ON l.assigned_agent_id = a.id

LEFT JOIN (
    SELECT
        lead_id,
        COUNT(*) as total_communications,
        MAX(sent_at) as last_communication,
        (COUNT(*) FILTER (WHERE status IN ('delivered', 'opened', 'clicked', 'replied'))::FLOAT /
         NULLIF(COUNT(*), 0))::DECIMAL(5,2) as response_rate,
        AVG(sentiment_score)::DECIMAL(3,2) as avg_sentiment,
        COUNT(*) FILTER (WHERE status = 'opened') as total_opens,
        COUNT(*) FILTER (WHERE status = 'clicked') as total_clicks
    FROM communications
    WHERE direction = 'outbound'
    GROUP BY lead_id
) comm_stats ON l.id = comm_stats.lead_id

LEFT JOIN (
    SELECT DISTINCT ON (lead_id)
        lead_id, sequence_name, current_step, total_steps, 
        next_action_due, engagement_rate
    FROM nurture_sequences 
    WHERE status = 'active'
    ORDER BY lead_id, enrolled_at DESC
) ns ON l.id = ns.lead_id

WHERE l.deleted_at IS NULL;

-- Agent performance view with comprehensive metrics
CREATE VIEW v_agent_performance AS
SELECT
    a.id,
    a.first_name,
    a.last_name,
    a.email,
    a.role,
    a.department,
    a.is_active,
    a.is_available,
    a.current_load,
    a.capacity,
    (a.current_load::FLOAT / NULLIF(a.capacity, 0) * 100)::DECIMAL(5,1) as utilization_percent,

    -- Recent performance (last 30 days)
    recent_stats.leads_assigned_30d,
    recent_stats.leads_converted_30d,
    recent_stats.conversion_rate_30d,
    recent_stats.avg_response_hours_30d,
    recent_stats.total_communications_30d,

    -- Overall lifetime metrics
    a.total_leads_handled,
    a.total_conversions,
    a.conversion_rate as lifetime_conversion_rate,
    a.avg_response_time_minutes,
    a.revenue_generated,

    -- Quality metrics
    a.customer_satisfaction,
    a.call_quality_score,
    a.email_response_quality,

    -- Activity metrics
    a.last_activity,
    a.last_login,
    EXTRACT(DAY FROM NOW() - a.last_activity) as days_since_activity,

    -- Capacity analysis
    CASE 
        WHEN a.current_load >= a.capacity THEN 'at_capacity'
        WHEN a.current_load >= a.capacity * 0.8 THEN 'near_capacity'
        WHEN a.current_load >= a.capacity * 0.5 THEN 'moderate_load'
        ELSE 'available'
    END as capacity_status,

    -- Specializations and territory (for assignment matching)
    a.specializations,
    a.territory,
    a.skills,
    a.languages

FROM agents a
LEFT JOIN (
    SELECT
        assigned_agent_id,
        COUNT(*) as leads_assigned_30d,
        COUNT(*) FILTER (WHERE status = 'converted') as leads_converted_30d,
        (COUNT(*) FILTER (WHERE status = 'converted')::FLOAT /
         NULLIF(COUNT(*), 0) * 100)::DECIMAL(5,2) as conversion_rate_30d,
        AVG(
            EXTRACT(EPOCH FROM (
                SELECT MIN(sent_at) FROM communications c
                WHERE c.lead_id = l.id AND c.direction = 'outbound'
            ) - l.created_at) / 3600
        )::DECIMAL(6,2) as avg_response_hours_30d,
        (
            SELECT COUNT(*) FROM communications c 
            WHERE c.lead_id = l.id AND c.direction = 'outbound'
        ) as total_communications_30d
    FROM leads l
    WHERE l.assigned_at >= NOW() - INTERVAL '30 days'
      AND l.assigned_agent_id IS NOT NULL
      AND l.deleted_at IS NULL
    GROUP BY assigned_agent_id
) recent_stats ON a.id = recent_stats.assigned_agent_id

WHERE a.deleted_at IS NULL;

-- Communication effectiveness view
CREATE VIEW v_communication_effectiveness AS
SELECT
    channel,
    direction,
    
    -- Volume metrics
    COUNT(*) as total_communications,
    COUNT(DISTINCT lead_id) as unique_leads,
    
    -- Effectiveness metrics
    COUNT(*) FILTER (WHERE status = 'delivered') as delivered_count,
    COUNT(*) FILTER (WHERE status = 'opened') as opened_count,
    COUNT(*) FILTER (WHERE status = 'clicked') as clicked_count,
    COUNT(*) FILTER (WHERE status = 'replied') as replied_count,
    
    -- Rates
    (COUNT(*) FILTER (WHERE status = 'delivered')::FLOAT / COUNT(*) * 100)::DECIMAL(5,2) as delivery_rate,
    (COUNT(*) FILTER (WHERE status = 'opened')::FLOAT / 
     NULLIF(COUNT(*) FILTER (WHERE status = 'delivered'), 0) * 100)::DECIMAL(5,2) as open_rate,
    (COUNT(*) FILTER (WHERE status = 'clicked')::FLOAT / 
     NULLIF(COUNT(*) FILTER (WHERE status = 'opened'), 0) * 100)::DECIMAL(5,2) as click_through_rate,
    (COUNT(*) FILTER (WHERE status = 'replied')::FLOAT / 
     NULLIF(COUNT(*) FILTER (WHERE status = 'delivered'), 0) * 100)::DECIMAL(5,2) as response_rate,
    
    -- Timing metrics
    AVG(response_time_minutes) FILTER (WHERE response_time_minutes IS NOT NULL)::DECIMAL(8,2) as avg_response_time_minutes,
    
    -- Sentiment analysis
    AVG(sentiment_score) FILTER (WHERE sentiment_score IS NOT NULL)::DECIMAL(3,2) as avg_sentiment,
    
    -- Error metrics
    COUNT(*) FILTER (WHERE status IN ('failed', 'bounced')) as failed_count,
    (COUNT(*) FILTER (WHERE status IN ('failed', 'bounced'))::FLOAT / COUNT(*) * 100)::DECIMAL(5,2) as failure_rate,
    
    -- Time periods
    DATE_TRUNC('day', sent_at) as date,
    DATE_TRUNC('hour', sent_at) as hour

FROM communications
WHERE sent_at >= NOW() - INTERVAL '30 days'
GROUP BY channel, direction, DATE_TRUNC('day', sent_at), DATE_TRUNC('hour', sent_at)
ORDER BY date DESC, hour DESC;

-- Lead funnel analysis view
CREATE VIEW v_lead_funnel AS
SELECT
    source,
    
    -- Lead counts by status
    COUNT(*) as total_leads,
    COUNT(*) FILTER (WHERE status = 'new') as new_leads,
    COUNT(*) FILTER (WHERE status = 'contacted') as contacted_leads,
    COUNT(*) FILTER (WHERE status = 'qualified') as qualified_leads,
    COUNT(*) FILTER (WHERE status = 'converted') as converted_leads,
    COUNT(*) FILTER (WHERE status = 'lost') as lost_leads,
    COUNT(*) FILTER (WHERE status = 'disqualified') as disqualified_leads,
    
    -- Conversion rates
    (COUNT(*) FILTER (WHERE status = 'contacted')::FLOAT / COUNT(*) * 100)::DECIMAL(5,2) as contact_rate,
    (COUNT(*) FILTER (WHERE status = 'qualified')::FLOAT / 
     NULLIF(COUNT(*) FILTER (WHERE status = 'contacted'), 0) * 100)::DECIMAL(5,2) as qualification_rate,
    (COUNT(*) FILTER (WHERE status = 'converted')::FLOAT / 
     NULLIF(COUNT(*) FILTER (WHERE status = 'qualified'), 0) * 100)::DECIMAL(5,2) as conversion_rate,
    
    -- Overall metrics
    (COUNT(*) FILTER (WHERE status = 'converted')::FLOAT / COUNT(*) * 100)::DECIMAL(5,2) as overall_conversion_rate,
    
    -- Average scores and times
    AVG(lead_score)::DECIMAL(5,2) as avg_lead_score,
    AVG(EXTRACT(DAY FROM COALESCE(last_contacted, NOW()) - created_at))::DECIMAL(8,2) as avg_days_to_contact,
    
    -- Time grouping
    DATE_TRUNC('month', created_at) as month,
    DATE_TRUNC('week', created_at) as week

FROM leads
WHERE deleted_at IS NULL
  AND created_at >= NOW() - INTERVAL '12 months'
GROUP BY source, DATE_TRUNC('month', created_at), DATE_TRUNC('week', created_at)
ORDER BY month DESC, source;

-- System health dashboard view
CREATE VIEW v_system_health AS
SELECT
    -- Error metrics
    (SELECT COUNT(*) FROM error_queue WHERE status IN ('pending', 'retrying')) as pending_errors,
    (SELECT COUNT(*) FROM error_queue WHERE created_at >= NOW() - INTERVAL '24 hours') as errors_24h,
    
    -- Performance metrics
    (SELECT COUNT(*) FROM workflow_executions WHERE status = 'running') as active_workflows,
    (SELECT COUNT(*) FROM workflow_executions WHERE status = 'failed' AND started_at >= NOW() - INTERVAL '1 hour') as failed_workflows_1h,
    
    -- Data health metrics
    (SELECT COUNT(*) FROM leads WHERE deleted_at IS NULL) as total_active_leads,
    (SELECT COUNT(*) FROM leads WHERE created_at >= NOW() - INTERVAL '24 hours') as new_leads_24h,
    (SELECT COUNT(*) FROM communications WHERE sent_at >= NOW() - INTERVAL '1 hour') as communications_1h,
    
    -- Agent metrics
    (SELECT COUNT(*) FROM agents WHERE is_active = true AND is_available = true) as available_agents,
    (SELECT COUNT(*) FROM agents WHERE current_load >= capacity AND is_active = true) as overloaded_agents,
    
    -- Alert metrics
    (SELECT COUNT(*) FROM alerts WHERE status = 'active' AND severity IN ('error', 'critical')) as critical_alerts,
    (SELECT COUNT(*) FROM system_health_checks WHERE status IN ('warning', 'critical')) as health_check_issues,
    
    -- Resource utilization
    (SELECT COUNT(*) FROM resource_utilization WHERE status = 'critical' AND measured_at >= NOW() - INTERVAL '5 minutes') as resource_critical,
    
    -- Compliance metrics
    (SELECT COUNT(*) FROM data_subject_requests WHERE status NOT IN ('completed', 'rejected') AND due_date < NOW()) as overdue_dsr,
    (SELECT COUNT(*) FROM data_retention WHERE delete_after <= NOW() AND status = 'pending') as pending_deletions,
    
    -- Current timestamp
    NOW() as last_updated;

-- Create materialized view for performance metrics (refreshed hourly)
CREATE MATERIALIZED VIEW mv_hourly_metrics AS
SELECT
    DATE_TRUNC('hour', measured_at) as hour_bucket,
    metric_category,
    metric_name,
    COUNT(*) as measurement_count,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    STDDEV(value) as stddev_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as median_value,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95_value,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY value) as p99_value
FROM performance_metrics
WHERE measured_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', measured_at), metric_category, metric_name
ORDER BY hour_bucket DESC, metric_category, metric_name;

-- Create unique index on materialized view
CREATE UNIQUE INDEX idx_mv_hourly_metrics_unique 
ON mv_hourly_metrics(hour_bucket, metric_category, metric_name);

-- Log successful completion
INSERT INTO setup_log (step, status, details, completed_at) 
VALUES (
    '07_create_views', 
    'SUCCESS', 
    'Views created: v_lead_summary, v_agent_performance, v_communication_effectiveness, v_lead_funnel, v_system_health, mv_hourly_metrics',
    NOW()
) ON CONFLICT (step) DO UPDATE SET 
    status = EXCLUDED.status,
    details = EXCLUDED.details,
    completed_at = EXCLUDED.completed_at;

-- Add view comments
COMMENT ON VIEW v_lead_summary IS 'Comprehensive lead information with intelligence and communication stats';
COMMENT ON VIEW v_agent_performance IS 'Agent performance metrics and capacity analysis';
COMMENT ON VIEW v_communication_effectiveness IS 'Communication channel effectiveness and engagement metrics';
COMMENT ON VIEW v_lead_funnel IS 'Lead conversion funnel analysis by source and time period';
COMMENT ON VIEW v_system_health IS 'Real-time system health dashboard metrics';
COMMENT ON MATERIALIZED VIEW mv_hourly_metrics IS 'Aggregated hourly performance metrics (refreshed hourly)';

-- Success notification
SELECT 
    'Views and materialized views created successfully' as status,
    COUNT(*) as views_created,
    NOW() as timestamp
FROM information_schema.views 
WHERE table_schema = 'public' AND table_name LIKE 'v_%'

UNION ALL

SELECT 
    'Materialized views created' as status,
    COUNT(*) as materialized_views_created,
    NOW() as timestamp
FROM pg_matviews 
WHERE schemaname = 'public';
