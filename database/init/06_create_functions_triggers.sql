-- Service 6 Database Initialization - Step 6: Functions and Triggers
-- PostgreSQL 15+ compatible
-- Creates stored functions, triggers, and automated procedures

-- Generic updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Lead activity tracking function
CREATE OR REPLACE FUNCTION update_lead_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- Update last_activity when communications are added
    IF TG_TABLE_NAME = 'communications' THEN
        UPDATE leads 
        SET last_activity = NOW(), updated_at = NOW() 
        WHERE id = NEW.lead_id;
    END IF;

    -- Update last_activity when nurture sequences are updated
    IF TG_TABLE_NAME = 'nurture_sequences' THEN
        UPDATE leads 
        SET last_activity = NOW(), updated_at = NOW() 
        WHERE id = NEW.lead_id;
    END IF;

    -- Update last_contacted for outbound communications
    IF TG_TABLE_NAME = 'communications' AND NEW.direction = 'outbound' THEN
        UPDATE leads 
        SET last_contacted = NEW.sent_at, updated_at = NOW()
        WHERE id = NEW.lead_id;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- Agent capacity management function
CREATE OR REPLACE FUNCTION update_agent_capacity()
RETURNS TRIGGER AS $$
DECLARE
    current_count INTEGER;
BEGIN
    -- Count current active leads for the agent
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Get current load
        SELECT COUNT(*) INTO current_count
        FROM leads 
        WHERE assigned_agent_id = NEW.assigned_agent_id 
          AND status NOT IN ('converted', 'lost', 'disqualified')
          AND deleted_at IS NULL;

        -- Update agent's current load
        UPDATE agents 
        SET current_load = current_count, updated_at = NOW()
        WHERE id = NEW.assigned_agent_id;
    END IF;

    -- Handle lead unassignment or status change
    IF TG_OP = 'UPDATE' AND OLD.assigned_agent_id IS NOT NULL THEN
        -- Update old agent's load
        SELECT COUNT(*) INTO current_count
        FROM leads 
        WHERE assigned_agent_id = OLD.assigned_agent_id 
          AND status NOT IN ('converted', 'lost', 'disqualified')
          AND deleted_at IS NULL;

        UPDATE agents 
        SET current_load = current_count, updated_at = NOW()
        WHERE id = OLD.assigned_agent_id;
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- Lead scoring automation function
CREATE OR REPLACE FUNCTION calculate_lead_composite_score()
RETURNS TRIGGER AS $$
DECLARE
    composite_score INTEGER;
    intelligence_record RECORD;
BEGIN
    -- Get latest intelligence data
    SELECT * INTO intelligence_record
    FROM lead_intelligence 
    WHERE lead_id = NEW.id 
    ORDER BY enriched_at DESC 
    LIMIT 1;

    -- Calculate composite score if intelligence exists
    IF FOUND THEN
        composite_score := (
            COALESCE(intelligence_record.behavior_score, 0) * 0.3 +
            COALESCE(intelligence_record.intent_score, 0) * 0.4 +
            COALESCE(intelligence_record.fit_score, 0) * 0.2 +
            COALESCE(intelligence_record.engagement_score, 0) * 0.1
        )::INTEGER;

        -- Update lead score if significantly different
        IF ABS(composite_score - COALESCE(NEW.lead_score, 0)) > 5 THEN
            NEW.lead_score := composite_score;
            NEW.last_score_update := NOW();
            
            -- Update scoring reasoning
            NEW.scoring_reasoning := format(
                'Composite score: Behavior=%s, Intent=%s, Fit=%s, Engagement=%s',
                COALESCE(intelligence_record.behavior_score, 0),
                COALESCE(intelligence_record.intent_score, 0),
                COALESCE(intelligence_record.fit_score, 0),
                COALESCE(intelligence_record.engagement_score, 0)
            );
        END IF;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- Audit logging function
CREATE OR REPLACE FUNCTION create_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB := '{}';
    new_data JSONB := '{}';
    changed_fields TEXT[] := '{}';
    field_name TEXT;
BEGIN
    -- Prepare old and new data
    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
        old_data := to_jsonb(OLD);
    END IF;
    
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        new_data := to_jsonb(NEW);
    END IF;

    -- Find changed fields for UPDATE operations
    IF TG_OP = 'UPDATE' THEN
        FOR field_name IN SELECT jsonb_object_keys(new_data)
        LOOP
            IF old_data->field_name != new_data->field_name THEN
                changed_fields := array_append(changed_fields, field_name);
            END IF;
        END LOOP;
    END IF;

    -- Insert audit log record
    INSERT INTO audit_log (
        table_name,
        record_id,
        operation,
        old_values,
        new_values,
        changed_fields,
        automated,
        created_at
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE((new_data->>'id')::UUID, (old_data->>'id')::UUID),
        TG_OP,
        CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE old_data END,
        CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE new_data END,
        changed_fields,
        true,
        NOW()
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- Communication response time calculation
CREATE OR REPLACE FUNCTION calculate_response_time()
RETURNS TRIGGER AS $$
DECLARE
    last_outbound_time TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Only calculate for inbound communications
    IF NEW.direction = 'inbound' THEN
        -- Find the last outbound communication to this lead
        SELECT sent_at INTO last_outbound_time
        FROM communications 
        WHERE lead_id = NEW.lead_id 
          AND direction = 'outbound'
          AND sent_at < NEW.sent_at
        ORDER BY sent_at DESC 
        LIMIT 1;

        -- Calculate response time in minutes
        IF last_outbound_time IS NOT NULL THEN
            NEW.response_time_minutes := EXTRACT(EPOCH FROM (NEW.sent_at - last_outbound_time)) / 60;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- Data retention enforcement function
CREATE OR REPLACE FUNCTION enforce_data_retention()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    rec RECORD;
    sql_statement TEXT;
BEGIN
    -- Process expired retention policies
    FOR rec IN 
        SELECT * FROM data_retention 
        WHERE delete_after <= NOW() 
          AND status = 'pending'
          AND legal_hold = false
        ORDER BY delete_after
        LIMIT 1000 -- Process in batches
    LOOP
        -- Build dynamic SQL for different tables
        sql_statement := format(
            'DELETE FROM %I WHERE id = $1',
            rec.table_name
        );
        
        -- Execute deletion
        BEGIN
            EXECUTE sql_statement USING rec.record_id;
            
            -- Update retention record
            UPDATE data_retention 
            SET status = 'completed', 
                deleted_at = NOW(),
                last_check = NOW()
            WHERE id = rec.id;
            
            deleted_count := deleted_count + 1;
            
        EXCEPTION 
            WHEN OTHERS THEN
                -- Log failure
                UPDATE data_retention 
                SET status = 'failed',
                    deletion_attempts = deletion_attempts + 1,
                    last_check = NOW()
                WHERE id = rec.id;
                
                -- Log error
                INSERT INTO error_queue (
                    error_category, error_type, severity,
                    error_message, original_data,
                    created_at
                ) VALUES (
                    'data_retention', 'deletion_failed', 'medium',
                    SQLERRM, 
                    jsonb_build_object(
                        'table_name', rec.table_name,
                        'record_id', rec.record_id,
                        'retention_id', rec.id
                    ),
                    NOW()
                );
        END;
    END LOOP;

    -- Clean up old workflow executions (90 days)
    DELETE FROM workflow_executions 
    WHERE started_at < NOW() - INTERVAL '90 days'
      AND status IN ('completed', 'failed');
    
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;

    -- Clean up old metrics (1 year)
    DELETE FROM metrics_hourly 
    WHERE hour_bucket < NOW() - INTERVAL '1 year';
    
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;

    -- Clean up resolved errors (30 days)
    DELETE FROM error_queue 
    WHERE status = 'resolved' 
      AND resolved_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;

    -- Clean up old audit logs (based on retention policy)
    DELETE FROM audit_log 
    WHERE created_at < NOW() - INTERVAL '2 years';
    
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schema health validation function
CREATE OR REPLACE FUNCTION validate_schema_health()
RETURNS TABLE(check_name TEXT, status TEXT, details TEXT, recommendations TEXT) AS $$
BEGIN
    -- Check for required indexes
    RETURN QUERY
    SELECT
        'indexes_exist'::TEXT,
        CASE WHEN COUNT(*) >= 40 THEN 'PASS' ELSE 'FAIL' END,
        'Found ' || COUNT(*) || ' of expected 40+ indexes',
        CASE WHEN COUNT(*) < 40 THEN 'Review missing indexes for performance' ELSE 'All critical indexes present' END
    FROM pg_indexes
    WHERE schemaname = 'public' AND indexname LIKE 'idx_%';

    -- Check for data quality issues
    RETURN QUERY
    SELECT
        'data_quality'::TEXT,
        CASE WHEN invalid_count = 0 THEN 'PASS' ELSE 'WARN' END,
        'Found ' || invalid_count || ' leads with data quality issues',
        CASE WHEN invalid_count > 0 THEN 'Run data cleanup procedures' ELSE 'Data quality is good' END
    FROM (
        SELECT COUNT(*) as invalid_count
        FROM leads
        WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
           OR (phone IS NOT NULL AND phone !~ '^[0-9+\-() ]{10,20}$')
           OR first_name = '' OR last_name = ''
    ) sq;

    -- Check agent capacity
    RETURN QUERY
    SELECT
        'agent_capacity'::TEXT,
        CASE WHEN overloaded_count = 0 THEN 'PASS' ELSE 'WARN' END,
        overloaded_count || ' agents over capacity',
        CASE WHEN overloaded_count > 0 THEN 'Redistribute leads or increase capacity' ELSE 'Agent capacity is balanced' END
    FROM (
        SELECT COUNT(*) as overloaded_count
        FROM agents
        WHERE current_load > capacity AND is_active = true
    ) sq;

    -- Check for stale data
    RETURN QUERY
    SELECT
        'data_freshness'::TEXT,
        CASE WHEN stale_count = 0 THEN 'PASS' ELSE 'WARN' END,
        stale_count || ' leads without recent activity',
        CASE WHEN stale_count > 0 THEN 'Review dormant lead reactivation strategy' ELSE 'Lead activity is current' END
    FROM (
        SELECT COUNT(*) as stale_count
        FROM leads
        WHERE last_activity < NOW() - INTERVAL '90 days'
          AND status NOT IN ('converted', 'lost', 'disqualified')
          AND deleted_at IS NULL
    ) sq;

    -- Check error queue
    RETURN QUERY
    SELECT
        'error_queue_health'::TEXT,
        CASE WHEN pending_errors = 0 THEN 'PASS' ELSE 'FAIL' END,
        pending_errors || ' unresolved errors in queue',
        CASE WHEN pending_errors > 0 THEN 'Review and resolve pending errors' ELSE 'No pending errors' END
    FROM (
        SELECT COUNT(*) as pending_errors
        FROM error_queue
        WHERE status IN ('pending', 'retrying')
    ) sq;

END;
$$ LANGUAGE plpgsql;

-- Create all triggers
CREATE TRIGGER update_leads_updated_at 
    BEFORE UPDATE ON leads 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at 
    BEFORE UPDATE ON agents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_error_queue_updated_at 
    BEFORE UPDATE ON error_queue 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_breaches_updated_at 
    BEFORE UPDATE ON data_breaches 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_processing_activities_updated_at 
    BEFORE UPDATE ON processing_activities 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alerts_updated_at 
    BEFORE UPDATE ON alerts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Activity tracking triggers
CREATE TRIGGER update_lead_activity_comms 
    AFTER INSERT ON communications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_lead_activity();

CREATE TRIGGER update_lead_activity_nurture 
    AFTER UPDATE ON nurture_sequences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_lead_activity();

-- Agent capacity triggers
CREATE TRIGGER update_agent_capacity_on_assignment 
    AFTER INSERT OR UPDATE OF assigned_agent_id, status ON leads 
    FOR EACH ROW 
    EXECUTE FUNCTION update_agent_capacity();

-- Lead scoring trigger
CREATE TRIGGER calculate_lead_score 
    BEFORE INSERT OR UPDATE ON leads 
    FOR EACH ROW 
    EXECUTE FUNCTION calculate_lead_composite_score();

-- Communication response time trigger
CREATE TRIGGER calculate_comm_response_time 
    BEFORE INSERT ON communications 
    FOR EACH ROW 
    EXECUTE FUNCTION calculate_response_time();

-- Audit logging triggers (for compliance)
CREATE TRIGGER audit_leads_changes 
    AFTER INSERT OR UPDATE OR DELETE ON leads 
    FOR EACH ROW 
    EXECUTE FUNCTION create_audit_log();

CREATE TRIGGER audit_communications_changes 
    AFTER INSERT OR UPDATE OR DELETE ON communications 
    FOR EACH ROW 
    EXECUTE FUNCTION create_audit_log();

CREATE TRIGGER audit_consent_logs_changes 
    AFTER INSERT OR UPDATE OR DELETE ON consent_logs 
    FOR EACH ROW 
    EXECUTE FUNCTION create_audit_log();

-- Log successful completion
INSERT INTO setup_log (step, status, details, completed_at) 
VALUES (
    '06_create_functions_triggers', 
    'SUCCESS', 
    'Functions and triggers created: updated_at tracking, lead activity, agent capacity, lead scoring, response time calculation, audit logging, data retention',
    NOW()
) ON CONFLICT (step) DO UPDATE SET 
    status = EXCLUDED.status,
    details = EXCLUDED.details,
    completed_at = EXCLUDED.completed_at;

-- Success notification
SELECT 
    'Functions and triggers created successfully' as status,
    (SELECT COUNT(*) FROM pg_proc WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')) as functions_created,
    (SELECT COUNT(*) FROM pg_trigger WHERE tgname NOT LIKE '%_oid') as triggers_created,
    NOW() as timestamp;
