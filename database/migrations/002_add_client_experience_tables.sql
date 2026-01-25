-- Client Experience Tables (Track B) - Phase 1 Foundation
-- Creates database schema for Client Journey Mapping and Experience Optimization
-- Follows multi-tenant isolation with (location_id, client_id) compound keys

-- Client Journey Data
-- Core journey tracking with stages and progression
CREATE TABLE client_journey_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Journey State
    current_stage VARCHAR(50) NOT NULL, -- qualified, property_search, viewing, etc.
    journey_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    journey_end_date TIMESTAMP WITH TIME ZONE,
    expected_completion_date TIMESTAMP WITH TIME ZONE,

    -- Progress Metrics
    overall_progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    milestones_completed INTEGER DEFAULT 0,
    milestones_total INTEGER DEFAULT 0,
    milestones_overdue INTEGER DEFAULT 0,

    -- Timing Analysis
    journey_duration_days INTEGER DEFAULT 0,
    velocity_score DECIMAL(5,2) DEFAULT 0.00, -- Progress rate vs expected
    projected_delay_days INTEGER DEFAULT 0,

    -- Health Assessment
    health_status VARCHAR(20) NOT NULL DEFAULT 'good', -- excellent, good, at_risk, critical, stalled
    health_score DECIMAL(5,2) DEFAULT 75.00,
    risk_factors TEXT[], -- Array of identified risk factors
    last_health_assessment TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Engagement Metrics
    client_engagement_score DECIMAL(5,2) DEFAULT 0.00,
    communication_responsiveness DECIMAL(5,2) DEFAULT 0.00,
    satisfaction_indicators TEXT[], -- Array of satisfaction signals

    -- Automation & Optimization
    automation_triggers_active TEXT[], -- Array of active automation triggers
    optimization_opportunities TEXT[], -- Array of optimization opportunities
    escalation_needed BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_stage_change TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT pk_client_journey PRIMARY KEY (location_id, client_id),
    INDEX idx_journey_stage (location_id, current_stage, updated_at DESC),
    INDEX idx_journey_health (location_id, health_status, health_score DESC),
    INDEX idx_journey_progress (location_id, overall_progress_percentage DESC),
    INDEX idx_journey_risk (location_id, escalation_needed, health_status)
);

-- Journey Milestones
-- Individual milestones within client journey stages
CREATE TABLE journey_milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    milestone_id VARCHAR(100) NOT NULL,
    client_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Milestone Classification
    milestone_type VARCHAR(50) NOT NULL, -- qualification, property_match, viewing_scheduled, etc.
    stage VARCHAR(50) NOT NULL, -- qualified, property_search, viewing, etc.
    priority_level VARCHAR(20) DEFAULT 'normal', -- low, normal, high, critical

    -- Milestone Content
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- Scheduling & Progress
    expected_completion TIMESTAMP WITH TIME ZONE,
    actual_completion TIMESTAMP WITH TIME ZONE,
    completion_status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, skipped, failed
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,

    -- Dependencies & Blockers
    blocking_issues TEXT[], -- Array of blocking issues
    dependencies TEXT[], -- Array of dependency IDs
    next_actions TEXT[], -- Array of next actions needed

    -- Automation & Personalization
    automated_actions_triggered TEXT[], -- Array of triggered automation
    personalization_applied JSONB, -- Personalization data applied
    engagement_score DECIMAL(5,2) DEFAULT 0.00,

    -- Timing
    estimated_duration_days INTEGER,
    actual_duration_days INTEGER,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT pk_journey_milestones PRIMARY KEY (location_id, milestone_id),
    INDEX idx_milestones_client (location_id, client_id, stage, milestone_type),
    INDEX idx_milestones_status (location_id, completion_status, expected_completion),
    INDEX idx_milestones_overdue (location_id, completion_status, expected_completion),
    INDEX idx_milestones_priority (location_id, priority_level, created_at DESC),

    -- Foreign key to journey data
    CONSTRAINT fk_milestones_journey FOREIGN KEY (location_id, client_id)
        REFERENCES client_journey_data(location_id, client_id) ON DELETE CASCADE
);

-- Journey Stage History
-- Historical record of stage progressions
CREATE TABLE journey_stage_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Stage Transition
    from_stage VARCHAR(50), -- NULL for initial stage
    to_stage VARCHAR(50) NOT NULL,
    transition_reason VARCHAR(100),

    -- Timing
    entered_at TIMESTAMP WITH TIME ZONE NOT NULL,
    exited_at TIMESTAMP WITH TIME ZONE,
    stage_duration_days INTEGER,

    -- Context
    milestone_triggers TEXT[], -- Milestones that triggered this transition
    agent_notes TEXT,
    client_feedback TEXT,

    -- Performance Analysis
    expected_duration_days INTEGER,
    performance_rating VARCHAR(20), -- ahead_of_schedule, on_track, behind_schedule
    completion_quality_score DECIMAL(5,2),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT pk_stage_history PRIMARY KEY (location_id, client_id, entered_at),
    INDEX idx_stage_history_client (location_id, client_id, entered_at DESC),
    INDEX idx_stage_history_stage (location_id, to_stage, entered_at DESC),
    INDEX idx_stage_history_duration (location_id, stage_duration_days DESC),

    -- Foreign key to journey data
    CONSTRAINT fk_stage_history_journey FOREIGN KEY (location_id, client_id)
        REFERENCES client_journey_data(location_id, client_id) ON DELETE CASCADE
);

-- Journey Personalization Settings
-- Client-specific journey personalization preferences
CREATE TABLE journey_personalization (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Communication Preferences
    preferred_communication_channel VARCHAR(50) DEFAULT 'email', -- email, sms, phone, app
    communication_frequency VARCHAR(20) DEFAULT 'standard', -- minimal, standard, frequent
    communication_timing VARCHAR(30) DEFAULT 'business_hours', -- anytime, business_hours, evenings
    communication_style VARCHAR(20) DEFAULT 'professional', -- casual, professional, formal

    -- Content Preferences
    content_detail_level VARCHAR(20) DEFAULT 'detailed', -- brief, standard, detailed
    market_update_interest BOOLEAN DEFAULT TRUE,
    property_alert_frequency VARCHAR(20) DEFAULT 'daily', -- real_time, daily, weekly
    educational_content_interest BOOLEAN DEFAULT TRUE,

    -- Journey Customization
    milestone_notification_preferences JSONB, -- Notification settings per milestone type
    automated_check_in_frequency VARCHAR(20) DEFAULT 'weekly', -- daily, weekly, biweekly, milestone_based
    priority_focus_areas TEXT[], -- Array of focus areas

    -- Experience Preferences
    preferred_agent_characteristics TEXT[], -- Array of preferred characteristics
    stress_level_indicators TEXT[], -- Array of stress indicators
    support_intensity_preference VARCHAR(20) DEFAULT 'standard', -- minimal, standard, high_touch
    decision_making_style VARCHAR(20) DEFAULT 'collaborative', -- independent, collaborative, guided

    -- Property Preferences Integration
    property_alert_criteria JSONB, -- Structured property criteria
    viewing_preferences JSONB, -- Viewing scheduling preferences
    negotiation_style VARCHAR(20) DEFAULT 'balanced', -- aggressive, balanced, conservative

    -- Learning & Adaptation
    successful_interaction_patterns TEXT[], -- Array of successful patterns
    journey_satisfaction_feedback JSONB, -- Satisfaction feedback by stage
    adaptation_insights TEXT[], -- Array of insights for improvement

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_preference_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT pk_journey_personalization PRIMARY KEY (location_id, client_id),
    INDEX idx_personalization_updated (location_id, updated_at DESC),
    INDEX idx_personalization_communication (location_id, preferred_communication_channel),

    -- Foreign key to journey data
    CONSTRAINT fk_personalization_journey FOREIGN KEY (location_id, client_id)
        REFERENCES client_journey_data(location_id, client_id) ON DELETE CASCADE
);

-- Journey Optimization Recommendations
-- AI-generated recommendations for journey optimization
CREATE TABLE journey_optimization_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recommendation_id VARCHAR(100) UNIQUE NOT NULL,
    client_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Recommendation Classification
    category VARCHAR(50) NOT NULL, -- timing, communication, automation, personalization
    priority VARCHAR(20) NOT NULL, -- low, medium, high, urgent

    -- Recommendation Content
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    estimated_impact TEXT,
    implementation_effort VARCHAR(20) DEFAULT 'medium', -- low, medium, high
    timeline VARCHAR(50) DEFAULT 'immediate', -- immediate, days, weeks

    -- Implementation Details
    action_items TEXT[], -- Array of specific action items
    expected_outcomes TEXT[], -- Array of expected outcomes
    success_metrics TEXT[], -- Array of success metrics
    risk_mitigation TEXT[], -- Array of risk mitigation strategies

    -- Validation & Confidence
    confidence_score DECIMAL(5,4) NOT NULL,
    data_quality VARCHAR(20) DEFAULT 'good', -- excellent, good, fair, poor
    recommendation_source VARCHAR(50) DEFAULT 'ai_analysis', -- ai_analysis, agent_input, client_feedback

    -- Lifecycle Management
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, implemented, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    implemented_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,

    -- Performance Tracking (if implemented)
    implementation_success BOOLEAN,
    actual_impact_description TEXT,
    client_satisfaction_improvement DECIMAL(5,2),
    journey_velocity_improvement DECIMAL(5,2),

    CONSTRAINT pk_journey_recommendations PRIMARY KEY (location_id, recommendation_id),
    INDEX idx_recommendations_client (location_id, client_id, created_at DESC),
    INDEX idx_recommendations_priority (location_id, priority, status, created_at DESC),
    INDEX idx_recommendations_category (location_id, category, created_at DESC),
    INDEX idx_recommendations_confidence (location_id, confidence_score DESC),

    -- Foreign key to journey data
    CONSTRAINT fk_recommendations_journey FOREIGN KEY (location_id, client_id)
        REFERENCES client_journey_data(location_id, client_id) ON DELETE CASCADE
);

-- Client Engagement Events
-- Detailed tracking of client engagement throughout journey
CREATE TABLE client_engagement_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Event Classification
    event_type VARCHAR(50) NOT NULL, -- communication, milestone_progress, feedback, escalation
    event_category VARCHAR(50), -- email_opened, call_completed, milestone_achieved, etc.
    event_source VARCHAR(50) NOT NULL, -- system, agent, client

    -- Event Content
    event_title VARCHAR(200),
    event_description TEXT,
    event_data JSONB, -- Structured event data

    -- Context
    journey_stage VARCHAR(50),
    milestone_id VARCHAR(100),
    agent_id VARCHAR(100),

    -- Engagement Metrics
    engagement_score DECIMAL(5,2), -- 0-100 score for this event
    response_time_minutes INTEGER,
    interaction_quality_score DECIMAL(5,2),
    client_satisfaction_rating INTEGER, -- 1-5 rating if available

    -- Automation Context
    triggered_by_automation BOOLEAN DEFAULT FALSE,
    automation_rule_id VARCHAR(100),
    personalization_applied JSONB,

    -- Timing
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT pk_engagement_events PRIMARY KEY (location_id, id),
    INDEX idx_engagement_client (location_id, client_id, occurred_at DESC),
    INDEX idx_engagement_type (location_id, event_type, occurred_at DESC),
    INDEX idx_engagement_score (location_id, engagement_score DESC),
    INDEX idx_engagement_milestone (location_id, milestone_id, occurred_at DESC),

    -- Foreign key to journey data
    CONSTRAINT fk_engagement_journey FOREIGN KEY (location_id, client_id)
        REFERENCES client_journey_data(location_id, client_id) ON DELETE CASCADE
);

-- Journey Analytics Summary
-- Aggregated analytics for journey performance analysis
CREATE TABLE journey_analytics_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id VARCHAR(50) NOT NULL,

    -- Time Period
    analysis_date DATE NOT NULL,
    analysis_period_days INTEGER NOT NULL,

    -- Volume Metrics
    total_active_journeys INTEGER DEFAULT 0,
    journeys_completed INTEGER DEFAULT 0,
    journeys_stalled INTEGER DEFAULT 0,
    new_journeys_started INTEGER DEFAULT 0,

    -- Performance Metrics
    average_journey_duration_days DECIMAL(6,2) DEFAULT 0.00,
    average_completion_rate DECIMAL(5,2) DEFAULT 0.00,
    average_client_satisfaction DECIMAL(5,2) DEFAULT 0.00,
    average_velocity_score DECIMAL(5,2) DEFAULT 0.00,

    -- Health Distribution
    excellent_health_count INTEGER DEFAULT 0,
    good_health_count INTEGER DEFAULT 0,
    at_risk_health_count INTEGER DEFAULT 0,
    critical_health_count INTEGER DEFAULT 0,
    stalled_health_count INTEGER DEFAULT 0,

    -- Stage Performance
    stage_performance_data JSONB, -- Performance by stage
    milestone_completion_rates JSONB, -- Completion rates by milestone type

    -- Optimization Insights
    top_risk_factors TEXT[], -- Most common risk factors
    optimization_opportunities TEXT[], -- Top optimization opportunities
    successful_personalization_patterns TEXT[], -- Effective personalization patterns

    -- Trend Analysis
    period_over_period_change DECIMAL(6,2) DEFAULT 0.00, -- percentage change
    trend_direction VARCHAR(20) DEFAULT 'stable', -- improving, declining, stable
    trend_confidence DECIMAL(3,2) DEFAULT 0.00,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT pk_journey_analytics PRIMARY KEY (location_id, analysis_date),
    INDEX idx_analytics_period (location_id, analysis_date DESC),
    INDEX idx_analytics_performance (location_id, average_completion_rate DESC),
    INDEX idx_analytics_health (location_id, critical_health_count DESC, at_risk_health_count DESC)
);

-- Client Experience Insights Cache
-- Caches computed client experience insights for performance
CREATE TABLE client_experience_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id VARCHAR(50) NOT NULL,
    insight_type VARCHAR(50) NOT NULL, -- journey_health, personalization_effectiveness, completion_trends

    -- Insight Content
    insight_data JSONB NOT NULL, -- Structured insight data
    summary_text TEXT,
    confidence_level DECIMAL(5,4) NOT NULL,

    -- Scope
    client_id VARCHAR(100), -- NULL for aggregate insights
    stage_filter VARCHAR(50), -- NULL for all stages

    -- Metadata
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    version VARCHAR(10) DEFAULT 'v1.0',

    -- Performance tracking
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,

    CONSTRAINT pk_experience_insights PRIMARY KEY (location_id, insight_type, generated_at),
    INDEX idx_experience_insights_current (location_id, insight_type, expires_at DESC),
    INDEX idx_experience_insights_client (location_id, client_id, insight_type),
    INDEX idx_experience_insights_confidence (location_id, confidence_level DESC)
);

-- Comments for documentation
COMMENT ON TABLE client_journey_data IS 'Core client journey tracking with stages, health, and progress metrics';
COMMENT ON TABLE journey_milestones IS 'Individual milestones within client journey stages with progress tracking';
COMMENT ON TABLE journey_stage_history IS 'Historical record of journey stage progressions and transitions';
COMMENT ON TABLE journey_personalization IS 'Client-specific personalization preferences and settings';
COMMENT ON TABLE journey_optimization_recommendations IS 'AI-generated recommendations for journey optimization';
COMMENT ON TABLE client_engagement_events IS 'Detailed tracking of client engagement events throughout journey';
COMMENT ON TABLE journey_analytics_summary IS 'Aggregated analytics for journey performance analysis';
COMMENT ON TABLE client_experience_insights IS 'Cached client experience insights and analytics for performance';