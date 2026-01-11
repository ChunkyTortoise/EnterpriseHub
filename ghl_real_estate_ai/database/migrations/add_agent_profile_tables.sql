-- Multi-Tenant Agent Profile System Database Schema
-- Building on existing EnterpriseHub multi-tenant architecture
-- Supports shared agent pool with location-based access control

-- Table: agent_profiles
-- Core agent profile information with multi-tenant shared pool support
CREATE TABLE agent_profiles (
    -- Identity
    agent_id VARCHAR(255) PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),

    -- Multi-tenant support (builds on existing location_id pattern)
    primary_location_id VARCHAR(255) NOT NULL,
    accessible_locations JSONB DEFAULT '[]'::jsonb,
    role_permissions JSONB DEFAULT '{}'::jsonb,

    -- Professional details (User Requirements: Seller/Buyer/Transaction Coordinator)
    primary_role VARCHAR(50) NOT NULL CHECK (
        primary_role IN ('seller_agent', 'buyer_agent', 'transaction_coordinator', 'dual_agent')
    ),
    secondary_roles JSONB DEFAULT '[]'::jsonb,
    years_experience INTEGER DEFAULT 0 CHECK (years_experience >= 0),
    specializations JSONB DEFAULT '[]'::jsonb,

    -- Claude AI preferences (User Requirements: Response/Strategy/Process/Performance)
    preferred_guidance_types JSONB DEFAULT '[]'::jsonb,
    coaching_style_preference VARCHAR(50) DEFAULT 'balanced' CHECK (
        coaching_style_preference IN ('aggressive', 'balanced', 'supportive')
    ),
    communication_style VARCHAR(50) DEFAULT 'professional' CHECK (
        communication_style IN ('casual', 'professional', 'formal')
    ),

    -- Session management (User Requirement: Session-based context)
    current_session_id VARCHAR(255),
    active_conversations JSONB DEFAULT '[]'::jsonb,

    -- Performance and context
    skill_levels JSONB DEFAULT '{}'::jsonb,
    performance_metrics_summary JSONB DEFAULT '{}'::jsonb,
    notification_preferences JSONB DEFAULT '{}'::jsonb,

    -- System fields
    timezone VARCHAR(50) DEFAULT 'UTC',
    language_preference VARCHAR(10) DEFAULT 'en-US',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    profile_version VARCHAR(20) DEFAULT '1.0',
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0

    -- Note: Foreign key to locations table will be added after table creation
    -- to ensure compatibility with existing schema
);

-- Table: agent_sessions
-- Session-based context management for agent interactions
CREATE TABLE agent_sessions (
    -- Session identity
    session_id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,

    -- Current interaction context
    current_lead_id VARCHAR(255),
    conversation_stage VARCHAR(50) DEFAULT 'discovery' CHECK (
        conversation_stage IN ('discovery', 'qualification', 'presentation', 'objection_handling', 'closing', 'follow_up')
    ),
    workflow_context JSONB DEFAULT '{}'::jsonb,

    -- Claude AI context (Session-based requirement)
    system_prompt_version VARCHAR(20) DEFAULT '1.0',
    conversation_history_summary TEXT DEFAULT '',
    active_guidance_types JSONB DEFAULT '[]'::jsonb,

    -- Performance tracking
    session_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_duration_seconds INTEGER DEFAULT 0,
    messages_exchanged INTEGER DEFAULT 0,
    guidance_requests INTEGER DEFAULT 0,
    coaching_effectiveness_score FLOAT DEFAULT 0.0 CHECK (coaching_effectiveness_score >= 0.0 AND coaching_effectiveness_score <= 1.0),

    -- Context metadata
    client_info JSONB DEFAULT '{}'::jsonb,
    property_context JSONB DEFAULT '{}'::jsonb,
    market_context JSONB DEFAULT '{}'::jsonb,

    -- Session state
    is_active BOOLEAN DEFAULT true,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end_time TIMESTAMP,

    -- Integration points
    ghl_contact_id VARCHAR(255),
    qualification_flow_id VARCHAR(255),
    opportunity_id VARCHAR(255),

    -- Foreign keys
    FOREIGN KEY (agent_id) REFERENCES agent_profiles(agent_id) ON DELETE CASCADE
    -- Note: location_id foreign key will be added after table creation
);

-- Table: agent_coaching_history
-- Track coaching effectiveness and agent improvements
CREATE TABLE agent_coaching_history (
    id BIGSERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    location_id VARCHAR(255) NOT NULL,

    -- Coaching details
    coaching_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guidance_type VARCHAR(50) NOT NULL CHECK (
        guidance_type IN ('response_suggestions', 'strategy_coaching', 'process_navigation', 'performance_insights')
    ),
    user_message TEXT NOT NULL,
    claude_response JSONB NOT NULL,

    -- Effectiveness tracking
    agent_followed_suggestion BOOLEAN,
    outcome_rating INTEGER CHECK (outcome_rating >= 1 AND outcome_rating <= 5),
    improvement_notes TEXT,

    -- Context
    lead_stage VARCHAR(50),
    property_type VARCHAR(50),

    -- Foreign keys
    FOREIGN KEY (agent_id) REFERENCES agent_profiles(agent_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES agent_sessions(session_id) ON DELETE SET NULL
);

-- Indexes for optimal performance (critical for multi-tenant queries)

-- Agent profiles indexes
CREATE INDEX idx_agent_profiles_primary_location ON agent_profiles(primary_location_id, is_active);
CREATE INDEX idx_agent_profiles_accessible_locations ON agent_profiles USING gin(accessible_locations);
CREATE INDEX idx_agent_profiles_role_permissions ON agent_profiles USING gin(role_permissions);
CREATE INDEX idx_agent_profiles_active_updated ON agent_profiles(is_active, updated_at);
CREATE INDEX idx_agent_profiles_primary_role ON agent_profiles(primary_role, is_active);
CREATE INDEX idx_agent_profiles_email_active ON agent_profiles(email, is_active);

-- Agent sessions indexes
CREATE INDEX idx_agent_sessions_agent_active ON agent_sessions(agent_id, is_active, last_activity);
CREATE INDEX idx_agent_sessions_location_active ON agent_sessions(location_id, is_active, last_activity);
CREATE INDEX idx_agent_sessions_lead ON agent_sessions(current_lead_id, is_active);
CREATE INDEX idx_agent_sessions_stage ON agent_sessions(conversation_stage, is_active);
CREATE INDEX idx_agent_sessions_start_time ON agent_sessions(session_start_time DESC);

-- Coaching history indexes
CREATE INDEX idx_coaching_history_agent ON agent_coaching_history(agent_id, coaching_timestamp DESC);
CREATE INDEX idx_coaching_history_session ON agent_coaching_history(session_id, coaching_timestamp DESC);
CREATE INDEX idx_coaching_history_location ON agent_coaching_history(location_id, coaching_timestamp DESC);
CREATE INDEX idx_coaching_history_guidance_type ON agent_coaching_history(guidance_type, coaching_timestamp DESC);

-- Row-level security for multi-tenancy (extends existing RLS patterns)
ALTER TABLE agent_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_coaching_history ENABLE ROW LEVEL SECURITY;

-- Policies for agent_profiles (shared agent pool support)
CREATE POLICY agent_profile_location_access ON agent_profiles
    FOR ALL TO authenticated_users
    USING (
        -- Agent can access their own profile
        agent_id = current_setting('app.current_agent_id', true) OR
        -- Location admin can access agents in their primary location
        primary_location_id = current_setting('app.current_location_id', true) OR
        -- Location admin can access agents who have access to their location
        accessible_locations ? current_setting('app.current_location_id', true) OR
        -- Super admin access (when location_id is 'admin')
        current_setting('app.current_location_id', true) = 'admin'
    );

-- Policies for agent_sessions
CREATE POLICY agent_session_location_access ON agent_sessions
    FOR ALL TO authenticated_users
    USING (
        -- Agent can access their own sessions
        agent_id = current_setting('app.current_agent_id', true) OR
        -- Location admin can access sessions in their location
        location_id = current_setting('app.current_location_id', true) OR
        -- Super admin access
        current_setting('app.current_location_id', true) = 'admin'
    );

-- Policies for coaching_history
CREATE POLICY agent_coaching_history_access ON agent_coaching_history
    FOR ALL TO authenticated_users
    USING (
        -- Agent can access their own coaching history
        agent_id = current_setting('app.current_agent_id', true) OR
        -- Location admin can access coaching history in their location
        location_id = current_setting('app.current_location_id', true) OR
        -- Super admin access
        current_setting('app.current_location_id', true) = 'admin'
    );

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agent_profiles_updated_at
    BEFORE UPDATE ON agent_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for session duration calculation
CREATE OR REPLACE FUNCTION update_session_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.session_end_time IS NOT NULL AND OLD.session_end_time IS NULL THEN
        NEW.session_duration_seconds = EXTRACT(EPOCH FROM (NEW.session_end_time - NEW.session_start_time));
    END IF;
    NEW.last_activity = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agent_sessions_duration
    BEFORE UPDATE ON agent_sessions
    FOR EACH ROW EXECUTE FUNCTION update_session_duration();

-- Functions for multi-tenant queries

-- Function: Get agents accessible to a location (Shared Agent Pool)
CREATE OR REPLACE FUNCTION get_agents_for_location(
    p_location_id VARCHAR(255),
    p_role_filter VARCHAR(50) DEFAULT NULL
) RETURNS TABLE (
    agent_id VARCHAR(255),
    agent_name VARCHAR(255),
    email VARCHAR(255),
    primary_role VARCHAR(50),
    secondary_roles JSONB,
    years_experience INTEGER,
    specializations JSONB,
    accessible_locations JSONB,
    is_active BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ap.agent_id,
        ap.agent_name,
        ap.email,
        ap.primary_role,
        ap.secondary_roles,
        ap.years_experience,
        ap.specializations,
        ap.accessible_locations,
        ap.is_active
    FROM agent_profiles ap
    WHERE ap.is_active = true
    AND (
        ap.primary_location_id = p_location_id OR
        ap.accessible_locations ? p_location_id
    )
    AND (
        p_role_filter IS NULL OR
        ap.primary_role = p_role_filter OR
        ap.secondary_roles ? p_role_filter
    )
    ORDER BY ap.agent_name;
END;
$$ LANGUAGE plpgsql;

-- Function: Get active sessions for location
CREATE OR REPLACE FUNCTION get_active_sessions_for_location(
    p_location_id VARCHAR(255)
) RETURNS TABLE (
    session_id VARCHAR(255),
    agent_id VARCHAR(255),
    agent_name VARCHAR(255),
    current_lead_id VARCHAR(255),
    conversation_stage VARCHAR(50),
    session_start_time TIMESTAMP,
    last_activity TIMESTAMP,
    messages_exchanged INTEGER,
    guidance_requests INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.session_id,
        s.agent_id,
        ap.agent_name,
        s.current_lead_id,
        s.conversation_stage,
        s.session_start_time,
        s.last_activity,
        s.messages_exchanged,
        s.guidance_requests
    FROM agent_sessions s
    JOIN agent_profiles ap ON s.agent_id = ap.agent_id
    WHERE s.location_id = p_location_id
    AND s.is_active = true
    ORDER BY s.last_activity DESC;
END;
$$ LANGUAGE plpgsql;

-- Sample data for testing (will be removed in production)
-- Demo agent profiles for different roles
INSERT INTO agent_profiles (
    agent_id, agent_name, email, primary_location_id, accessible_locations,
    primary_role, secondary_roles, years_experience, specializations,
    preferred_guidance_types, coaching_style_preference, communication_style
) VALUES
(
    'demo_buyer_agent_001',
    'Sarah Johnson',
    'sarah.johnson@demo.com',
    'demo_location_001',
    '["demo_location_001", "demo_location_002"]'::jsonb,
    'buyer_agent',
    '["transaction_coordinator"]'::jsonb,
    5,
    '["first_time_buyers", "luxury_homes", "investment_properties"]'::jsonb,
    '["response_suggestions", "strategy_coaching", "process_navigation"]'::jsonb,
    'balanced',
    'professional'
),
(
    'demo_seller_agent_001',
    'Michael Chen',
    'michael.chen@demo.com',
    'demo_location_001',
    '["demo_location_001", "demo_location_003"]'::jsonb,
    'seller_agent',
    '["dual_agent"]'::jsonb,
    8,
    '["luxury_market", "commercial_properties", "market_analysis"]'::jsonb,
    '["strategy_coaching", "performance_insights", "process_navigation"]'::jsonb,
    'aggressive',
    'professional'
),
(
    'demo_tc_agent_001',
    'Jennifer Davis',
    'jennifer.davis@demo.com',
    'demo_location_002',
    '["demo_location_002"]'::jsonb,
    'transaction_coordinator',
    '[]'::jsonb,
    3,
    '["compliance", "documentation", "closing_coordination"]'::jsonb,
    '["process_navigation", "performance_insights"]'::jsonb,
    'supportive',
    'formal'
);

-- Comments for documentation
COMMENT ON TABLE agent_profiles IS 'Multi-tenant agent profiles with shared agent pool support';
COMMENT ON TABLE agent_sessions IS 'Session-based context management for agent interactions with Claude AI';
COMMENT ON TABLE agent_coaching_history IS 'Historical tracking of Claude coaching effectiveness and agent improvements';

COMMENT ON COLUMN agent_profiles.accessible_locations IS 'JSONB array of location_ids where agent can work (shared pool)';
COMMENT ON COLUMN agent_profiles.role_permissions IS 'JSONB object mapping location_id to allowed roles in that location';
COMMENT ON COLUMN agent_profiles.preferred_guidance_types IS 'Array of preferred Claude guidance types: response_suggestions, strategy_coaching, process_navigation, performance_insights';

COMMENT ON COLUMN agent_sessions.active_guidance_types IS 'JSONB array of guidance types active for current session';
COMMENT ON COLUMN agent_sessions.workflow_context IS 'JSONB object containing current workflow state and context information';

-- Grant permissions (adjust based on your user roles)
GRANT SELECT, INSERT, UPDATE, DELETE ON agent_profiles TO authenticated_users;
GRANT SELECT, INSERT, UPDATE, DELETE ON agent_sessions TO authenticated_users;
GRANT SELECT, INSERT, UPDATE, DELETE ON agent_coaching_history TO authenticated_users;

-- Grant usage on sequences
GRANT USAGE, SELECT ON SEQUENCE agent_coaching_history_id_seq TO authenticated_users;

-- Performance monitoring queries (for optimization)
-- These can be used to monitor query performance and optimize indexes

-- Query to check index usage
/*
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('agent_profiles', 'agent_sessions', 'agent_coaching_history')
ORDER BY tablename, indexname;
*/

-- Query to check table statistics
/*
SELECT
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE tablename IN ('agent_profiles', 'agent_sessions', 'agent_coaching_history');
*/

-- Migration complete message
SELECT 'Agent Profile System database schema created successfully!' as migration_status;