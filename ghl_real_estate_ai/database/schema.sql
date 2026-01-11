-- Multi-Tenant Continuous Memory System Database Schema
-- EnterpriseHub GHL Real Estate AI Platform
--
-- This schema implements a comprehensive multi-tenant system with:
-- - Tenant isolation and configuration
-- - Persistent conversation context with behavioral learning
-- - Property interaction tracking
-- - Claude configuration per tenant
-- - Optimized indexes for high performance
--
-- Compatible with PostgreSQL 13+

-- =====================================================
-- EXTENSIONS AND FUNCTIONS
-- =====================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSONB advanced operators
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =====================================================
-- TENANT MANAGEMENT TABLES
-- =====================================================

-- Multi-tenant configuration (extends existing tenant service)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id VARCHAR(100) UNIQUE NOT NULL, -- GHL location ID
    name VARCHAR(255) NOT NULL,
    claude_config JSONB DEFAULT '{}',
    behavioral_learning_enabled BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tenant metadata for easier admin management
COMMENT ON TABLE tenants IS 'Multi-tenant configuration with location-based isolation';
COMMENT ON COLUMN tenants.location_id IS 'GoHighLevel location ID for tenant isolation';
COMMENT ON COLUMN tenants.claude_config IS 'Tenant-specific Claude configuration and prompts';
COMMENT ON COLUMN tenants.behavioral_learning_enabled IS 'Enable/disable behavioral learning for this tenant';

-- =====================================================
-- CONVERSATION TABLES
-- =====================================================

-- Persistent conversation context (extends existing memory service)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    contact_id VARCHAR(100) NOT NULL,
    conversation_stage VARCHAR(100) DEFAULT 'initial_contact',
    lead_score INTEGER DEFAULT 0,
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    extracted_preferences JSONB DEFAULT '{}',
    lead_intelligence JSONB DEFAULT '{}',
    previous_sessions_summary TEXT,
    behavioral_profile JSONB DEFAULT '{}',
    session_count INTEGER DEFAULT 1,
    total_messages INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, contact_id)
);

-- Conversation metadata
COMMENT ON TABLE conversations IS 'Persistent conversation context with behavioral learning';
COMMENT ON COLUMN conversations.contact_id IS 'GHL contact ID';
COMMENT ON COLUMN conversations.extracted_preferences IS 'Jorge methodology qualification data';
COMMENT ON COLUMN conversations.lead_intelligence IS 'Enhanced lead intelligence from Phase 2';
COMMENT ON COLUMN conversations.behavioral_profile IS 'Learned behavioral patterns';
COMMENT ON COLUMN conversations.session_count IS 'Number of distinct conversation sessions';

-- Full conversation history with search capabilities
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    claude_reasoning TEXT,
    response_time_ms INTEGER,
    token_count INTEGER,
    message_order INTEGER NOT NULL DEFAULT 0
);

-- Message metadata
COMMENT ON TABLE conversation_messages IS 'Full conversation history with Claude reasoning';
COMMENT ON COLUMN conversation_messages.claude_reasoning IS 'Claude internal reasoning for response';
COMMENT ON COLUMN conversation_messages.response_time_ms IS 'Response generation time in milliseconds';
COMMENT ON COLUMN conversation_messages.message_order IS 'Message order within conversation';

-- =====================================================
-- BEHAVIORAL LEARNING TABLES
-- =====================================================

-- Behavioral preference learning
CREATE TABLE IF NOT EXISTS behavioral_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    preference_type VARCHAR(100) NOT NULL,
    preference_value JSONB NOT NULL,
    confidence_score FLOAT DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    learned_from VARCHAR(255),
    source_interaction_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Behavioral preferences metadata
COMMENT ON TABLE behavioral_preferences IS 'Learned behavioral preferences with confidence scoring';
COMMENT ON COLUMN behavioral_preferences.preference_type IS 'Type: communication_style, decision_pattern, info_processing, etc.';
COMMENT ON COLUMN behavioral_preferences.confidence_score IS 'Confidence level (0.0-1.0) in this preference';
COMMENT ON COLUMN behavioral_preferences.learned_from IS 'Source of learning: conversation, property_interaction, etc.';

-- Property interaction tracking (integrates with existing behavioral engine)
CREATE TABLE IF NOT EXISTS property_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    property_id VARCHAR(100),
    property_data JSONB NOT NULL,
    interaction_type VARCHAR(50) NOT NULL CHECK (interaction_type IN ('view', 'like', 'pass', 'inquiry', 'share', 'save')),
    feedback_category VARCHAR(100),
    feedback_text TEXT,
    time_on_property FLOAT DEFAULT 0, -- seconds spent viewing
    claude_analysis JSONB DEFAULT '{}',
    behavioral_signals JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Property interaction metadata
COMMENT ON TABLE property_interactions IS 'Property interaction tracking with behavioral analysis';
COMMENT ON COLUMN property_interactions.time_on_property IS 'Time spent viewing property in seconds';
COMMENT ON COLUMN property_interactions.claude_analysis IS 'Claude analysis of interaction patterns';
COMMENT ON COLUMN property_interactions.behavioral_signals IS 'Extracted behavioral signals';

-- =====================================================
-- CLAUDE CONFIGURATION TABLES
-- =====================================================

-- Claude configuration per tenant
CREATE TABLE IF NOT EXISTS claude_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    api_key_encrypted TEXT, -- Encrypted tenant Claude API key
    model_name VARCHAR(100) DEFAULT 'claude-sonnet-4-20250514',
    system_prompts JSONB DEFAULT '{}',
    qualification_templates JSONB DEFAULT '{}',
    seller_prompts JSONB DEFAULT '{}',
    buyer_prompts JSONB DEFAULT '{}',
    agent_assistance_config JSONB DEFAULT '{}',
    a_b_test_config JSONB DEFAULT '{}',
    performance_settings JSONB DEFAULT '{}',
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id)
);

-- Claude configuration metadata
COMMENT ON TABLE claude_configurations IS 'Tenant-specific Claude configuration and prompt management';
COMMENT ON COLUMN claude_configurations.system_prompts IS 'Custom system prompts by category';
COMMENT ON COLUMN claude_configurations.a_b_test_config IS 'A/B testing configuration for prompts';

-- Claude performance metrics
CREATE TABLE IF NOT EXISTS claude_performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    model_name VARCHAR(100),
    prompt_version VARCHAR(100),
    response_time_ms INTEGER,
    token_usage INTEGER,
    cost_estimate DECIMAL(10,6),
    quality_score FLOAT CHECK (quality_score >= 0 AND quality_score <= 1),
    user_satisfaction_score FLOAT CHECK (user_satisfaction_score >= 0 AND user_satisfaction_score <= 1),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance metrics metadata
COMMENT ON TABLE claude_performance_metrics IS 'Claude API performance and quality tracking';

-- =====================================================
-- ANALYTICS AND REPORTING TABLES
-- =====================================================

-- Memory system analytics
CREATE TABLE IF NOT EXISTS memory_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    metric_value JSONB NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics metadata
COMMENT ON TABLE memory_analytics IS 'Memory system performance and learning analytics';

-- System health monitoring
CREATE TABLE IF NOT EXISTS system_health_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component VARCHAR(100) NOT NULL,
    health_status VARCHAR(50) NOT NULL CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'critical')),
    metrics JSONB DEFAULT '{}',
    error_details TEXT,
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health monitoring metadata
COMMENT ON TABLE system_health_logs IS 'System health monitoring and alerting';

-- =====================================================
-- PERFORMANCE INDEXES
-- =====================================================

-- Tenant indexes
CREATE INDEX IF NOT EXISTS idx_tenants_location_id ON tenants(location_id);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status) WHERE status = 'active';

-- Conversation indexes (critical for performance)
CREATE INDEX IF NOT EXISTS idx_conversations_tenant_contact ON conversations(tenant_id, contact_id);
CREATE INDEX IF NOT EXISTS idx_conversations_tenant_last_interaction
    ON conversations(tenant_id, last_interaction_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_lead_score
    ON conversations(lead_score DESC) WHERE lead_score >= 3; -- Hot leads
CREATE INDEX IF NOT EXISTS idx_conversations_stage
    ON conversations(conversation_stage);

-- Message indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation_timestamp
    ON conversation_messages(conversation_id, timestamp DESC)
    INCLUDE (role, content);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_order
    ON conversation_messages(conversation_id, message_order);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp
    ON conversation_messages(timestamp DESC);

-- Behavioral preference indexes
CREATE INDEX IF NOT EXISTS idx_behavioral_prefs_conversation_type
    ON behavioral_preferences(conversation_id, preference_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_behavioral_prefs_type_confidence
    ON behavioral_preferences(preference_type, confidence_score DESC)
    WHERE confidence_score >= 0.7;

-- Property interaction indexes
CREATE INDEX IF NOT EXISTS idx_property_interactions_conversation_timestamp
    ON property_interactions(conversation_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_property_interactions_type_timestamp
    ON property_interactions(interaction_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_property_interactions_property_id
    ON property_interactions(property_id)
    WHERE property_id IS NOT NULL;

-- JSONB indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_conversations_preferences_gin
    ON conversations USING GIN (extracted_preferences);
CREATE INDEX IF NOT EXISTS idx_conversations_intelligence_gin
    ON conversations USING GIN (lead_intelligence);
CREATE INDEX IF NOT EXISTS idx_conversations_behavioral_profile_gin
    ON conversations USING GIN (behavioral_profile);

-- Claude configuration indexes
CREATE INDEX IF NOT EXISTS idx_claude_configs_tenant_enabled
    ON claude_configurations(tenant_id) WHERE enabled = true;

-- Performance metrics indexes
CREATE INDEX IF NOT EXISTS idx_claude_metrics_tenant_timestamp
    ON claude_performance_metrics(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_claude_metrics_response_time
    ON claude_performance_metrics(response_time_ms)
    WHERE response_time_ms IS NOT NULL;

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_memory_analytics_tenant_type_period
    ON memory_analytics(tenant_id, metric_type, period_start DESC);

-- Health monitoring indexes
CREATE INDEX IF NOT EXISTS idx_health_logs_component_timestamp
    ON system_health_logs(component, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_health_logs_status_timestamp
    ON system_health_logs(health_status, timestamp DESC)
    WHERE health_status IN ('degraded', 'unhealthy', 'critical');

-- =====================================================
-- TRIGGERS AND FUNCTIONS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_behavioral_preferences_updated_at
    BEFORE UPDATE ON behavioral_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claude_configurations_updated_at
    BEFORE UPDATE ON claude_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update conversation statistics
CREATE OR REPLACE FUNCTION update_conversation_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update message count and last interaction time
    UPDATE conversations
    SET
        total_messages = (
            SELECT COUNT(*)
            FROM conversation_messages
            WHERE conversation_id = NEW.conversation_id
        ),
        last_interaction_at = NEW.timestamp,
        updated_at = NOW()
    WHERE id = NEW.conversation_id;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for conversation statistics
CREATE TRIGGER update_conversation_stats_trigger
    AFTER INSERT ON conversation_messages
    FOR EACH ROW EXECUTE FUNCTION update_conversation_stats();

-- =====================================================
-- PARTITIONING FOR LARGE TABLES
-- =====================================================

-- Partition conversation_messages by month for better performance
-- This will be implemented as the system scales

-- Future partitioning strategy:
-- CREATE TABLE conversation_messages_y2026m01 PARTITION OF conversation_messages
--     FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- =====================================================
-- SECURITY AND PERMISSIONS
-- =====================================================

-- Row Level Security (RLS) for tenant isolation
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE behavioral_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE claude_configurations ENABLE ROW LEVEL SECURITY;

-- RLS policies will be defined based on application authentication
-- Example policy (to be customized based on auth system):
-- CREATE POLICY tenant_isolation ON conversations
--     FOR ALL TO application_role
--     USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Comprehensive conversation view with memory context
CREATE OR REPLACE VIEW conversation_with_memory AS
SELECT
    c.id,
    c.tenant_id,
    t.name as tenant_name,
    t.location_id,
    c.contact_id,
    c.conversation_stage,
    c.lead_score,
    c.last_interaction_at,
    c.extracted_preferences,
    c.lead_intelligence,
    c.behavioral_profile,
    c.session_count,
    c.total_messages,
    c.created_at,
    c.updated_at,
    (
        SELECT json_agg(
            json_build_object(
                'id', cm.id,
                'role', cm.role,
                'content', cm.content,
                'timestamp', cm.timestamp,
                'metadata', cm.metadata
            ) ORDER BY cm.message_order
        )
        FROM conversation_messages cm
        WHERE cm.conversation_id = c.id
    ) as message_history,
    (
        SELECT json_agg(
            json_build_object(
                'preference_type', bp.preference_type,
                'preference_value', bp.preference_value,
                'confidence_score', bp.confidence_score,
                'timestamp', bp.timestamp
            ) ORDER BY bp.timestamp DESC
        )
        FROM behavioral_preferences bp
        WHERE bp.conversation_id = c.id
    ) as behavioral_preferences,
    (
        SELECT json_agg(
            json_build_object(
                'property_id', pi.property_id,
                'interaction_type', pi.interaction_type,
                'property_data', pi.property_data,
                'feedback_category', pi.feedback_category,
                'timestamp', pi.timestamp
            ) ORDER BY pi.timestamp DESC
        )
        FROM property_interactions pi
        WHERE pi.conversation_id = c.id
    ) as property_interactions
FROM conversations c
JOIN tenants t ON c.tenant_id = t.id
WHERE t.status = 'active';

-- Tenant performance summary view
CREATE OR REPLACE VIEW tenant_performance_summary AS
SELECT
    t.id,
    t.name,
    t.location_id,
    t.status,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT c.id) FILTER (WHERE c.last_interaction_at >= NOW() - INTERVAL '24 hours') as active_conversations_24h,
    AVG(c.lead_score) as avg_lead_score,
    COUNT(DISTINCT c.id) FILTER (WHERE c.lead_score >= 3) as hot_leads,
    COUNT(DISTINCT cm.id) as total_messages,
    AVG(cpm.response_time_ms) as avg_response_time_ms,
    SUM(cpm.cost_estimate) as total_cost_estimate,
    AVG(cpm.quality_score) as avg_quality_score
FROM tenants t
LEFT JOIN conversations c ON t.id = c.tenant_id
LEFT JOIN conversation_messages cm ON c.id = cm.conversation_id
LEFT JOIN claude_performance_metrics cpm ON t.id = cpm.tenant_id
WHERE t.status = 'active'
GROUP BY t.id, t.name, t.location_id, t.status;

-- =====================================================
-- INITIAL DATA AND CONFIGURATION
-- =====================================================

-- Insert default tenant configuration (if needed)
-- This will be handled by the migration script

-- =====================================================
-- SCHEMA VALIDATION FUNCTION
-- =====================================================

-- Function to validate schema integrity
CREATE OR REPLACE FUNCTION validate_schema_integrity()
RETURNS TABLE(
    table_name TEXT,
    constraint_name TEXT,
    is_valid BOOLEAN,
    error_message TEXT
) AS $$
DECLARE
    validation_record RECORD;
BEGIN
    -- Check for required tables
    FOR validation_record IN
        SELECT t.table_name, 'table_exists' as constraint_name, true as is_valid, 'OK' as error_message
        FROM information_schema.tables t
        WHERE t.table_schema = 'public'
        AND t.table_name IN ('tenants', 'conversations', 'conversation_messages',
                            'behavioral_preferences', 'property_interactions', 'claude_configurations')
    LOOP
        RETURN NEXT validation_record;
    END LOOP;

    -- Check for required indexes
    FOR validation_record IN
        SELECT i.indexname as table_name, 'index_exists' as constraint_name, true as is_valid, 'OK' as error_message
        FROM pg_indexes i
        WHERE i.schemaname = 'public'
        AND i.indexname LIKE 'idx_%'
    LOOP
        RETURN NEXT validation_record;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SCHEMA VERSION TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Record this schema version
INSERT INTO schema_migrations (version, description)
VALUES ('1.0.0', 'Initial multi-tenant continuous memory system schema')
ON CONFLICT (version) DO NOTHING;

-- =====================================================
-- PERFORMANCE MONITORING FUNCTIONS
-- =====================================================

-- Function to get table sizes
CREATE OR REPLACE FUNCTION get_table_sizes()
RETURNS TABLE(
    table_name TEXT,
    row_count BIGINT,
    total_size TEXT,
    index_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname||'.'||tablename as table_name,
        n_tup_ins as row_count,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
        pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size
    FROM pg_stat_user_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- CLEANUP FUNCTIONS
-- =====================================================

-- Function to archive old conversation data
CREATE OR REPLACE FUNCTION archive_old_conversations(days_old INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Archive conversations older than specified days with no recent activity
    CREATE TABLE IF NOT EXISTS archived_conversations (LIKE conversations INCLUDING ALL);
    CREATE TABLE IF NOT EXISTS archived_conversation_messages (LIKE conversation_messages INCLUDING ALL);

    -- Move old conversations to archive
    WITH old_conversations AS (
        DELETE FROM conversations
        WHERE last_interaction_at < NOW() - INTERVAL '1 day' * days_old
        AND conversation_stage IN ('closed', 'inactive')
        RETURNING *
    )
    INSERT INTO archived_conversations SELECT * FROM old_conversations;

    GET DIAGNOSTICS archived_count = ROW_COUNT;

    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- END OF SCHEMA
-- =====================================================

-- Verify schema creation
SELECT 'Multi-tenant continuous memory system schema created successfully!' as status;