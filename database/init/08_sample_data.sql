-- Service 6 Database Initialization - Step 8: Sample and Test Data
-- PostgreSQL 15+ compatible
-- Creates sample data for development and testing

-- Insert sample agents first (needed for lead assignments)
INSERT INTO agents (id, first_name, last_name, email, role, department, specializations, territory, capacity, is_active, is_available) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Sarah', 'Chen', 'sarah.chen@service6.com', 'senior', 'Sales', 
 '["residential", "first_time_buyers", "luxury_condos"]', 
 '{"zip_codes": ["90210", "90211", "90212"], "max_price": 2000000}', 25, true, true),
 
('550e8400-e29b-41d4-a716-446655440002', 'Mike', 'Rodriguez', 'mike.rodriguez@service6.com', 'lead', 'Sales',
 '["commercial", "luxury", "investment_properties"]', 
 '{"zip_codes": ["90213", "90214", "90215"], "min_price": 500000}', 20, true, true),

('550e8400-e29b-41d4-a716-446655440003', 'Jennifer', 'Kim', 'jennifer.kim@service6.com', 'junior', 'Sales',
 '["residential", "relocation", "starter_homes"]', 
 '{"zip_codes": ["90216", "90217", "90218"], "max_price": 800000}', 30, true, true),

('550e8400-e29b-41d4-a716-446655440004', 'David', 'Thompson', 'david.thompson@service6.com', 'manager', 'Sales Management',
 '["team_management", "high_value_clients", "strategic_accounts"]', 
 '{"region": "west_coast", "min_deal_size": 1000000}', 15, true, true),

('550e8400-e29b-41d4-a716-446655440005', 'Lisa', 'Wang', 'lisa.wang@service6.com', 'senior', 'Sales',
 '["luxury", "international_clients", "corporate_relocations"]', 
 '{"zip_codes": ["90219", "90220", "90221"], "languages": ["english", "mandarin", "cantonese"]}', 22, true, false);

-- Insert sample leads with various statuses and temperatures
INSERT INTO leads (id, email, first_name, last_name, phone, company, source, lead_score, temperature, status, priority, job_title, company_industry, company_size, assigned_agent_id, created_at, last_activity) VALUES

-- Hot prospects
('660e8400-e29b-41d4-a716-446655440001', 'john.smith@techcorp.com', 'John', 'Smith', '+1-555-0101', 'TechCorp Inc', 'website_form', 85, 'hot', 'contacted', 'high', 'CTO', 'Technology', 250, '550e8400-e29b-41d4-a716-446655440001', NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day'),

('660e8400-e29b-41d4-a716-446655440002', 'emily.johnson@startupx.io', 'Emily', 'Johnson', '+1-555-0102', 'StartupX', 'referral', 78, 'hot', 'qualified', 'high', 'CEO', 'Technology', 50, '550e8400-e29b-41d4-a716-446655440002', NOW() - INTERVAL '1 day', NOW() - INTERVAL '3 hours'),

('660e8400-e29b-41d4-a716-446655440003', 'michael.brown@healthplus.com', 'Michael', 'Brown', '+1-555-0103', 'HealthPlus Medical', 'linkedin', 92, 'hot', 'new', 'urgent', 'Director of Operations', 'Healthcare', 150, NULL, NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours'),

-- Warm prospects
('660e8400-e29b-41d4-a716-446655440004', 'sarah.davis@consulting.biz', 'Sarah', 'Davis', '+1-555-0104', 'Davis Consulting', 'google_ads', 65, 'warm', 'contacted', 'medium', 'Managing Partner', 'Consulting', 25, '550e8400-e29b-41d4-a716-446655440003', NOW() - INTERVAL '5 days', NOW() - INTERVAL '2 days'),

('660e8400-e29b-41d4-a716-446655440005', 'robert.wilson@manufacturing.co', 'Robert', 'Wilson', '+1-555-0105', 'Wilson Manufacturing', 'trade_show', 58, 'warm', 'qualified', 'medium', 'VP of Facilities', 'Manufacturing', 500, '550e8400-e29b-41d4-a716-446655440001', NOW() - INTERVAL '3 days', NOW() - INTERVAL '1 day'),

('660e8400-e29b-41d4-a716-446655440006', 'amanda.taylor@finance.corp', 'Amanda', 'Taylor', '+1-555-0106', 'Taylor Finance Corp', 'webinar', 71, 'warm', 'new', 'medium', 'Chief Financial Officer', 'Financial Services', 100, NULL, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),

-- Cold prospects
('660e8400-e29b-41d4-a716-446655440007', 'james.anderson@retail.com', 'James', 'Anderson', '+1-555-0107', 'Anderson Retail', 'cold_email', 35, 'cold', 'contacted', 'low', 'Store Manager', 'Retail', 75, '550e8400-e29b-41d4-a716-446655440003', NOW() - INTERVAL '10 days', NOW() - INTERVAL '8 days'),

('660e8400-e29b-41d4-a716-446655440008', 'jessica.martinez@education.org', 'Jessica', 'Martinez', '+1-555-0108', 'Martinez Education Foundation', 'partner_referral', 42, 'cold', 'new', 'low', 'Program Director', 'Non-Profit', 30, NULL, NOW() - INTERVAL '15 days', NOW() - INTERVAL '15 days'),

-- Converted leads (for performance metrics)
('660e8400-e29b-41d4-a716-446655440009', 'william.garcia@successful.biz', 'William', 'Garcia', '+1-555-0109', 'Successful Business Solutions', 'referral', 88, 'hot', 'converted', 'high', 'President', 'Business Services', 200, '550e8400-e29b-41d4-a716-446655440002', NOW() - INTERVAL '30 days', NOW() - INTERVAL '5 days'),

('660e8400-e29b-41d4-a716-446655440010', 'maria.lopez@winwin.com', 'Maria', 'Lopez', '+1-555-0110', 'WinWin Enterprises', 'website_form', 82, 'warm', 'converted', 'high', 'COO', 'Technology', 300, '550e8400-e29b-41d4-a716-446655440001', NOW() - INTERVAL '45 days', NOW() - INTERVAL '10 days');

-- Insert lead intelligence data
INSERT INTO lead_intelligence (lead_id, apollo_data, enrichment_data, behavior_score, intent_score, fit_score, engagement_score, temperature, reasoning, enrichment_source, enriched_at) VALUES

('660e8400-e29b-41d4-a716-446655440001', 
 '{"apollo_id": "ap123456", "job_seniority": "c_level", "company_funding": "series_c", "technologies": ["salesforce", "hubspot"]}',
 '{"website_visits": 15, "email_opens": 8, "content_downloads": 3, "demo_requests": 1}',
 85, 90, 80, 85, 'hot', 'High intent signals: multiple demo requests, C-level executive, well-funded company', 'apollo', NOW() - INTERVAL '1 day'),

('660e8400-e29b-41d4-a716-446655440002',
 '{"apollo_id": "ap123457", "job_seniority": "c_level", "company_stage": "startup", "funding_amount": 2000000}',
 '{"website_visits": 12, "email_opens": 6, "pricing_page_views": 4, "case_study_downloads": 2}',
 75, 85, 70, 80, 'hot', 'Strong intent: pricing research, case study engagement, startup CEO with recent funding', 'apollo', NOW() - INTERVAL '2 days'),

('660e8400-e29b-41d4-a716-446655440003',
 '{"apollo_id": "ap123458", "job_seniority": "director", "company_growth_rate": "high", "employee_count": 150}',
 '{"website_visits": 20, "email_opens": 10, "feature_page_views": 8, "competitor_research": true}',
 90, 95, 85, 90, 'hot', 'Extremely high engagement: extensive research, director level, growing company', 'apollo', NOW() - INTERVAL '6 hours');

-- Insert sample communications
INSERT INTO communications (lead_id, channel, direction, subject, content, status, sent_at, opened_at, clicked_at, template_id, campaign_id) VALUES

-- John Smith communications
('660e8400-e29b-41d4-a716-446655440001', 'email', 'outbound', 'Welcome to Service 6 - Your Lead Recovery Solution', 'Hi John, Thank you for your interest in Service 6...', 'opened', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '30 minutes', NULL, 'welcome_email', 'onboarding_sequence'),

('660e8400-e29b-41d4-a716-446655440001', 'email', 'inbound', 'Re: Welcome to Service 6 - Questions about pricing', 'Hi Sarah, Thanks for reaching out. I have some questions about your pricing models...', 'delivered', NOW() - INTERVAL '2 days' + INTERVAL '45 minutes', NULL, NULL, NULL, NULL),

('660e8400-e29b-41d4-a716-446655440001', 'sms', 'outbound', '', 'Hi John, this is Sarah from Service 6. Thanks for your email! I can schedule a quick call to discuss pricing. Are you available tomorrow at 2 PM?', 'delivered', NOW() - INTERVAL '1 day' + INTERVAL '2 hours', NULL, NULL, 'pricing_followup_sms', 'sales_sequence'),

-- Emily Johnson communications
('660e8400-e29b-41d4-a716-446655440002', 'email', 'outbound', 'Startup-Focused Lead Recovery Strategy', 'Hi Emily, I saw that StartupX recently raised funding. Congratulations!...', 'clicked', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '15 minutes', NOW() - INTERVAL '1 day' + INTERVAL '20 minutes', 'startup_outreach', 'targeted_campaign'),

('660e8400-e29b-41d4-a716-446655440002', 'call', 'outbound', '', '30-minute discovery call about lead recovery automation for startups', 'completed', NOW() - INTERVAL '6 hours', NULL, NULL, NULL, 'sales_sequence'),

-- Michael Brown (new hot lead)
('660e8400-e29b-41d4-a716-446655440003', 'email', 'outbound', 'Healthcare Lead Recovery - Immediate ROI Opportunity', 'Hi Michael, I noticed your LinkedIn activity around lead management challenges in healthcare...', 'opened', NOW() - INTERVAL '3 hours', NOW() - INTERVAL '2 hours', NULL, 'healthcare_outreach', 'urgent_followup');

-- Insert nurture sequences
INSERT INTO nurture_sequences (lead_id, sequence_name, sequence_type, current_step, total_steps, status, next_action_due, next_action_type, personalization_data, enrolled_at, total_opens, total_clicks) VALUES

('660e8400-e29b-41d4-a716-446655440001', 'Enterprise Onboarding', 'welcome', 3, 7, 'active', NOW() + INTERVAL '2 hours', 'call', 
 '{"company_size": "mid_market", "use_case": "lead_recovery", "pain_point": "low_conversion_rates"}', 
 NOW() - INTERVAL '3 days', 2, 1),

('660e8400-e29b-41d4-a716-446655440004', 'Warm Lead Nurture', 'follow_up', 2, 5, 'active', NOW() + INTERVAL '1 day', 'email',
 '{"industry": "consulting", "company_size": "small", "interest_level": "moderate"}', 
 NOW() - INTERVAL '5 days', 3, 0),

('660e8400-e29b-41d4-a716-446655440006', 'Finance Industry Sequence', 'industry_specific', 1, 6, 'active', NOW() + INTERVAL '4 hours', 'linkedin',
 '{"role": "cfo", "industry": "financial_services", "compliance_focus": true}', 
 NOW() - INTERVAL '1 day', 1, 0);

-- Insert sample workflow executions
INSERT INTO workflow_executions (workflow_name, execution_id, status, trigger_type, input_data, output_data, duration_ms, nodes_executed, started_at, finished_at, lead_id) VALUES

('lead_scoring_update', 'exec_001_' || extract(epoch from now())::text, 'completed', 'webhook', 
 '{"lead_id": "660e8400-e29b-41d4-a716-446655440001", "trigger": "email_opened"}',
 '{"score_change": 5, "new_score": 85, "actions": ["increase_priority", "schedule_followup"]}',
 2500, 8, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '2 hours' + INTERVAL '2.5 seconds', '660e8400-e29b-41d4-a716-446655440001'),

('apollo_enrichment', 'exec_002_' || extract(epoch from now())::text, 'completed', 'schedule',
 '{"batch_size": 50, "enrichment_type": "basic"}',
 '{"leads_processed": 3, "leads_enriched": 3, "api_calls": 15, "cost_cents": 45}',
 15000, 12, NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours' + INTERVAL '15 seconds', NULL),

('nurture_sequence_trigger', 'exec_003_' || extract(epoch from now())::text, 'completed', 'schedule',
 '{"sequence_type": "follow_up", "due_actions": 3}',
 '{"emails_sent": 2, "calls_scheduled": 1, "sequences_updated": 3}',
 5500, 15, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour' + INTERVAL '5.5 seconds', NULL);

-- Insert sample metrics
INSERT INTO metrics_hourly (hour_bucket, metric_name, metric_value, metric_unit, labels, data_points, min_value, max_value) VALUES

(DATE_TRUNC('hour', NOW() - INTERVAL '1 hour'), 'lead_conversion_rate', 12.5, 'percent', '{"source": "website_form"}', 100, 10.0, 15.0),
(DATE_TRUNC('hour', NOW() - INTERVAL '1 hour'), 'avg_response_time', 45.2, 'minutes', '{"channel": "email"}', 150, 15.0, 180.0),
(DATE_TRUNC('hour', NOW() - INTERVAL '1 hour'), 'email_open_rate', 28.7, 'percent', '{"campaign": "onboarding"}', 200, 20.0, 35.0),
(DATE_TRUNC('hour', NOW() - INTERVAL '1 hour'), 'api_calls_apollo', 1250, 'count', '{"service": "apollo"}', 1, 1250, 1250),
(DATE_TRUNC('hour', NOW() - INTERVAL '1 hour'), 'leads_processed', 47, 'count', '{"status": "new"}', 1, 47, 47);

-- Insert sample consent logs
INSERT INTO consent_logs (lead_id, consent_type, granted, consent_text, ip_address, user_agent, source_url, granted_at) VALUES

('660e8400-e29b-41d4-a716-446655440001', 'email', true, 'I consent to receive marketing emails about Service 6 products and services', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'https://service6.com/contact-form', NOW() - INTERVAL '2 days'),

('660e8400-e29b-41d4-a716-446655440001', 'sms', true, 'I consent to receive SMS updates about my Service 6 inquiry', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'https://service6.com/contact-form', NOW() - INTERVAL '2 days'),

('660e8400-e29b-41d4-a716-446655440002', 'email', true, 'I agree to receive product updates and industry insights via email', '10.0.0.50', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15', 'https://service6.com/startup-demo', NOW() - INTERVAL '1 day');

-- Insert sample system health checks
INSERT INTO system_health_checks (check_name, check_category, check_type, status, result_data, response_time_ms, checked_at) VALUES

('database_connection', 'database', 'availability', 'healthy', '{"connections_active": 15, "connections_max": 100}', 25, NOW()),
('apollo_api', 'external_service', 'availability', 'healthy', '{"rate_limit_remaining": 950, "rate_limit_max": 1000}', 145, NOW()),
('email_delivery_rate', 'communication', 'performance', 'warning', '{"delivery_rate": 92.5, "threshold": 95.0}', 50, NOW()),
('lead_processing_queue', 'workflow', 'performance', 'healthy', '{"queue_size": 12, "processing_rate": 25.5}', 15, NOW());

-- Insert sample performance metrics
INSERT INTO performance_metrics (metric_name, metric_category, metric_type, value, unit, labels, source_component, measured_at) VALUES

('api_response_time', 'api_performance', 'timer', 125.5, 'milliseconds', '{"endpoint": "/api/leads", "method": "GET"}', 'fastapi_server', NOW()),
('lead_scoring_duration', 'lead_processing', 'timer', 2500.0, 'milliseconds', '{"model": "composite_v2", "data_source": "apollo"}', 'scoring_engine', NOW()),
('email_send_rate', 'communication', 'counter', 45.0, 'count', '{"provider": "sendgrid", "template": "welcome"}', 'email_service', NOW()),
('database_query_time', 'database', 'timer', 15.2, 'milliseconds', '{"table": "leads", "operation": "select"}', 'postgresql', NOW());

-- Update agent current_load based on assigned leads
UPDATE agents SET current_load = (
    SELECT COUNT(*) 
    FROM leads 
    WHERE assigned_agent_id = agents.id 
      AND status NOT IN ('converted', 'lost', 'disqualified')
      AND deleted_at IS NULL
);

-- Log successful completion
INSERT INTO setup_log (step, status, details, completed_at) 
VALUES (
    '08_sample_data', 
    'SUCCESS', 
    'Sample data inserted: 5 agents, 10 leads, lead intelligence, communications, nurture sequences, workflow executions, metrics, consent logs, health checks, performance metrics',
    NOW()
) ON CONFLICT (step) DO UPDATE SET 
    status = EXCLUDED.status,
    details = EXCLUDED.details,
    completed_at = EXCLUDED.completed_at;

-- Create development data summary
SELECT 
    'Sample data created successfully' as status,
    (SELECT COUNT(*) FROM agents WHERE deleted_at IS NULL) as agents_created,
    (SELECT COUNT(*) FROM leads WHERE deleted_at IS NULL) as leads_created,
    (SELECT COUNT(*) FROM communications) as communications_created,
    (SELECT COUNT(*) FROM nurture_sequences) as nurture_sequences_created,
    (SELECT COUNT(*) FROM workflow_executions) as workflow_executions_created,
    NOW() as timestamp;
