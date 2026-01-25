-- Migration 016: Conversation Intelligence Tables
-- Purpose: Support real-time conversation analysis, objection detection, and coaching opportunities
-- Performance Targets: <500ms conversation processing, <50ms insight retrieval
-- Integration: Phase 2.3 Conversation Intelligence Service

-- =====================================================================================
-- Custom ENUM Types for Conversation Intelligence
-- =====================================================================================

-- Conversation Analysis Types
CREATE TYPE conversation_analysis_type AS ENUM (
    'real_time',           -- Live conversation monitoring
    'post_call',          -- Post-conversation deep analysis
    'historical',         -- Batch historical analysis
    'coaching_review',    -- Manager coaching session review
    'quality_audit'       -- Quality assurance audit
);

-- Objection Categories (8 primary real estate objection types)
CREATE TYPE objection_category AS ENUM (
    'price_concern',       -- Price too high, budget constraints
    'timing_objection',    -- Not ready now, wrong timing
    'location_preference', -- Wrong area, location concerns
    'property_features',   -- Feature mismatches, property concerns
    'financing_concern',   -- Financing, mortgage concerns
    'market_hesitation',   -- Market conditions, economic fears
    'decision_authority',  -- Need to consult spouse/family
    'trust_credibility'    -- Agent credibility, company trust
);

-- Sentiment Classification
CREATE TYPE sentiment_classification AS ENUM (
    'very_positive',       -- Extremely engaged, ready to move
    'positive',           -- Interested, responsive
    'neutral',            -- Balanced, information gathering
    'slightly_negative',   -- Some concerns, hesitation
    'negative',           -- Resistant, objections
    'very_negative'       -- Disengaged, hostile
);

-- Coaching Opportunity Types
CREATE TYPE coaching_opportunity_type AS ENUM (
    'objection_handling',  -- Better objection responses needed
    'rapport_building',    -- Relationship development opportunity
    'closing_technique',   -- Closing skill improvement
    'active_listening',    -- Listening skill enhancement
    'product_knowledge',   -- Property/market knowledge gaps
    'follow_up_timing',    -- Follow-up strategy optimization
    'question_technique',  -- Better questioning strategies
    'value_proposition'    -- Value communication improvement
);

-- =====================================================================================
-- Core Conversation Intelligence Tables
-- =====================================================================================

-- Main conversation insights storage
CREATE TABLE conversation_insights (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR(100) NOT NULL,
    lead_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Analysis metadata
    analysis_type conversation_analysis_type NOT NULL DEFAULT 'real_time',
    analysis_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    conversation_start TIMESTAMP WITH TIME ZONE,
    conversation_end TIMESTAMP WITH TIME ZONE,
    conversation_duration_seconds INTEGER,

    -- Core insight scores (0.0 to 1.0)
    overall_engagement_score DECIMAL(3,2) NOT NULL DEFAULT 0.0,
    interest_level_score DECIMAL(3,2) NOT NULL DEFAULT 0.0,
    objection_intensity_score DECIMAL(3,2) NOT NULL DEFAULT 0.0,
    rapport_quality_score DECIMAL(3,2) NOT NULL DEFAULT 0.0,
    next_step_clarity_score DECIMAL(3,2) NOT NULL DEFAULT 0.0,

    -- Conversation characteristics
    dominant_sentiment sentiment_classification NOT NULL DEFAULT 'neutral',
    sentiment_volatility DECIMAL(3,2) DEFAULT 0.0, -- How much sentiment changed
    speaking_time_ratio DECIMAL(3,2), -- Lead speaking time / Total time
    interruption_count INTEGER DEFAULT 0,
    question_count INTEGER DEFAULT 0,

    -- Key insights (JSON format for flexibility)
    key_topics JSONB DEFAULT '[]'::jsonb, -- ["pricing", "location", "timeline"]
    buying_signals JSONB DEFAULT '[]'::jsonb, -- ["urgency", "specific_questions"]
    concern_indicators JSONB DEFAULT '[]'::jsonb, -- ["budget_hesitation", "location_doubts"]
    engagement_patterns JSONB DEFAULT '{}'::jsonb, -- Response times, enthusiasm markers

    -- Next steps and recommendations
    recommended_next_actions JSONB DEFAULT '[]'::jsonb,
    priority_follow_up_topics JSONB DEFAULT '[]'::jsonb,
    suggested_timeline VARCHAR(100),

    -- Performance tracking
    cache_key VARCHAR(200),
    processing_duration_ms INTEGER,
    confidence_score DECIMAL(3,2) NOT NULL DEFAULT 0.0,

    -- Multi-tenancy and audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT conversation_insights_pkey PRIMARY KEY (location_id, conversation_id, analysis_timestamp),
    CONSTRAINT valid_engagement_score CHECK (overall_engagement_score >= 0.0 AND overall_engagement_score <= 1.0),
    CONSTRAINT valid_interest_score CHECK (interest_level_score >= 0.0 AND interest_level_score <= 1.0),
    CONSTRAINT valid_objection_score CHECK (objection_intensity_score >= 0.0 AND objection_intensity_score <= 1.0),
    CONSTRAINT valid_rapport_score CHECK (rapport_quality_score >= 0.0 AND rapport_quality_score <= 1.0),
    CONSTRAINT valid_clarity_score CHECK (next_step_clarity_score >= 0.0 AND next_step_clarity_score <= 1.0),
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    CONSTRAINT valid_speaking_ratio CHECK (speaking_time_ratio IS NULL OR (speaking_time_ratio >= 0.0 AND speaking_time_ratio <= 1.0)),
    CONSTRAINT valid_duration CHECK (conversation_duration_seconds IS NULL OR conversation_duration_seconds >= 0),
    CONSTRAINT valid_conversation_order CHECK (conversation_end IS NULL OR conversation_start IS NULL OR conversation_end >= conversation_start)
);

-- Sentiment timeline for detailed sentiment tracking
CREATE TABLE conversation_sentiment_timeline (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Sentiment data point
    timestamp_offset_seconds INTEGER NOT NULL, -- Seconds from conversation start
    sentiment_score DECIMAL(3,2) NOT NULL, -- -1.0 (very negative) to 1.0 (very positive)
    sentiment_classification sentiment_classification NOT NULL,
    confidence DECIMAL(3,2) NOT NULL DEFAULT 0.0,

    -- Context for this sentiment point
    trigger_phrase TEXT, -- What caused this sentiment
    speaker VARCHAR(20) NOT NULL DEFAULT 'lead', -- 'lead' or 'agent'
    topic_context VARCHAR(100), -- What was being discussed

    -- Analysis metadata
    analysis_method VARCHAR(50) DEFAULT 'ml_classification', -- How sentiment was determined
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Multi-tenancy
    CONSTRAINT sentiment_timeline_pkey PRIMARY KEY (location_id, conversation_id, timestamp_offset_seconds, speaker),
    CONSTRAINT valid_sentiment_score CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    CONSTRAINT valid_sentiment_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT valid_offset CHECK (timestamp_offset_seconds >= 0)
);

-- Objection detection and tracking
CREATE TABLE objection_detections (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    lead_id VARCHAR(100) NOT NULL,

    -- Objection details
    objection_category objection_category NOT NULL,
    objection_text TEXT NOT NULL,
    detected_at_offset_seconds INTEGER NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    severity_level INTEGER NOT NULL DEFAULT 1, -- 1-5 scale

    -- Response analysis
    agent_response TEXT,
    response_effectiveness_score DECIMAL(3,2), -- How well was objection handled
    objection_resolved BOOLEAN DEFAULT FALSE,
    follow_up_needed BOOLEAN DEFAULT TRUE,

    -- Recommended responses
    suggested_responses JSONB DEFAULT '[]'::jsonb,
    coaching_notes TEXT,

    -- Context and metadata
    conversation_context TEXT, -- Surrounding conversation
    detection_method VARCHAR(50) DEFAULT 'ml_classification',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Multi-tenancy
    CONSTRAINT objection_detections_pkey PRIMARY KEY (location_id, conversation_id, detected_at_offset_seconds),
    CONSTRAINT valid_objection_confidence CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    CONSTRAINT valid_effectiveness_score CHECK (response_effectiveness_score IS NULL OR (response_effectiveness_score >= 0.0 AND response_effectiveness_score <= 1.0)),
    CONSTRAINT valid_severity CHECK (severity_level >= 1 AND severity_level <= 5),
    CONSTRAINT valid_detection_offset CHECK (detected_at_offset_seconds >= 0)
);

-- Coaching opportunities identified from conversations
CREATE TABLE coaching_opportunities (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    lead_id VARCHAR(100) NOT NULL,
    agent_user_id VARCHAR(100), -- GHL user ID of the agent

    -- Coaching opportunity details
    opportunity_type coaching_opportunity_type NOT NULL,
    priority_level INTEGER NOT NULL DEFAULT 3, -- 1-5 scale (5 = highest priority)
    opportunity_description TEXT NOT NULL,
    specific_example TEXT, -- Specific conversation excerpt

    -- Improvement recommendations
    recommended_approach TEXT NOT NULL,
    suggested_scripts JSONB DEFAULT '[]'::jsonb,
    training_resources JSONB DEFAULT '[]'::jsonb,
    practice_scenarios JSONB DEFAULT '[]'::jsonb,

    -- Context and timing
    occurred_at_offset_seconds INTEGER,
    impact_on_outcome TEXT, -- How this affected the conversation
    missed_opportunity_cost VARCHAR(100), -- What was potentially lost

    -- Tracking and follow-up
    coaching_status VARCHAR(20) DEFAULT 'identified', -- identified, planned, in_progress, completed
    manager_notified BOOLEAN DEFAULT FALSE,
    follow_up_scheduled TIMESTAMP WITH TIME ZONE,
    improvement_measured BOOLEAN DEFAULT FALSE,

    -- Metadata
    confidence_score DECIMAL(3,2) NOT NULL DEFAULT 0.0,
    detection_method VARCHAR(50) DEFAULT 'automated_analysis',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Multi-tenancy and constraints
    CONSTRAINT coaching_opportunities_pkey PRIMARY KEY (location_id, conversation_id, opportunity_type),
    CONSTRAINT valid_priority CHECK (priority_level >= 1 AND priority_level <= 5),
    CONSTRAINT valid_coaching_confidence CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    CONSTRAINT valid_occurrence_offset CHECK (occurred_at_offset_seconds IS NULL OR occurred_at_offset_seconds >= 0),
    CONSTRAINT valid_coaching_status CHECK (coaching_status IN ('identified', 'planned', 'in_progress', 'completed', 'dismissed'))
);

-- =====================================================================================
-- Performance Optimization Indexes
-- =====================================================================================

-- Conversation Insights Indexes (8 indexes for <500ms query performance)
CREATE INDEX idx_conversation_insights_lead_recent
    ON conversation_insights (location_id, lead_id, analysis_timestamp DESC)
    WHERE analysis_timestamp > NOW() - INTERVAL '30 days';

CREATE INDEX idx_conversation_insights_engagement_high
    ON conversation_insights (location_id, overall_engagement_score DESC, analysis_timestamp DESC)
    WHERE overall_engagement_score >= 0.7;

CREATE INDEX idx_conversation_insights_objection_analysis
    ON conversation_insights (location_id, objection_intensity_score DESC, analysis_timestamp DESC)
    WHERE objection_intensity_score > 0.3;

CREATE INDEX idx_conversation_insights_cache_lookup
    ON conversation_insights (cache_key)
    WHERE cache_key IS NOT NULL;

CREATE INDEX idx_conversation_insights_processing_performance
    ON conversation_insights (processing_duration_ms)
    WHERE processing_duration_ms > 200;

CREATE INDEX idx_conversation_insights_conversation_lookup
    ON conversation_insights (location_id, conversation_id, analysis_type);

CREATE INDEX idx_conversation_insights_lead_timeline
    ON conversation_insights (lead_id, conversation_start DESC)
    WHERE conversation_start IS NOT NULL;

CREATE INDEX idx_conversation_insights_real_time
    ON conversation_insights (location_id, analysis_type, created_at DESC)
    WHERE analysis_type = 'real_time';

-- Sentiment Timeline Indexes (5 indexes for real-time sentiment tracking)
CREATE INDEX idx_sentiment_timeline_conversation
    ON conversation_sentiment_timeline (location_id, conversation_id, timestamp_offset_seconds);

CREATE INDEX idx_sentiment_timeline_negative_tracking
    ON conversation_sentiment_timeline (location_id, conversation_id, sentiment_score)
    WHERE sentiment_score < -0.3;

CREATE INDEX idx_sentiment_timeline_volatility_analysis
    ON conversation_sentiment_timeline (conversation_id, timestamp_offset_seconds)
    WHERE ABS(sentiment_score) > 0.5;

CREATE INDEX idx_sentiment_timeline_speaker_analysis
    ON conversation_sentiment_timeline (location_id, conversation_id, speaker, sentiment_score DESC);

CREATE INDEX idx_sentiment_timeline_recent_analysis
    ON conversation_sentiment_timeline (location_id, created_at DESC)
    WHERE created_at > NOW() - INTERVAL '24 hours';

-- Objection Detections Indexes (4 indexes for objection analysis)
CREATE INDEX idx_objection_detections_category_analysis
    ON objection_detections (location_id, objection_category, confidence_score DESC, created_at DESC);

CREATE INDEX idx_objection_detections_unresolved
    ON objection_detections (location_id, lead_id, objection_resolved, follow_up_needed)
    WHERE objection_resolved = FALSE OR follow_up_needed = TRUE;

CREATE INDEX idx_objection_detections_severity_tracking
    ON objection_detections (location_id, severity_level DESC, confidence_score DESC)
    WHERE severity_level >= 3;

CREATE INDEX idx_objection_detections_conversation_timeline
    ON objection_detections (conversation_id, detected_at_offset_seconds);

-- Coaching Opportunities Indexes (5 indexes for coaching workflow)
CREATE INDEX idx_coaching_opportunities_priority
    ON coaching_opportunities (location_id, priority_level DESC, coaching_status, created_at DESC)
    WHERE coaching_status IN ('identified', 'planned');

CREATE INDEX idx_coaching_opportunities_agent_tracking
    ON coaching_opportunities (location_id, agent_user_id, opportunity_type, priority_level DESC)
    WHERE agent_user_id IS NOT NULL;

CREATE INDEX idx_coaching_opportunities_pending_notification
    ON coaching_opportunities (location_id, manager_notified, priority_level DESC)
    WHERE manager_notified = FALSE;

CREATE INDEX idx_coaching_opportunities_follow_up_due
    ON coaching_opportunities (location_id, follow_up_scheduled)
    WHERE follow_up_scheduled IS NOT NULL AND follow_up_scheduled <= NOW() + INTERVAL '7 days';

CREATE INDEX idx_coaching_opportunities_conversation_analysis
    ON coaching_opportunities (conversation_id, occurred_at_offset_seconds, priority_level DESC);

-- =====================================================================================
-- Automated Trigger Functions for Data Maintenance
-- =====================================================================================

-- Function to automatically update conversation insights updated_at timestamp
CREATE OR REPLACE FUNCTION update_conversation_insights_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for conversation insights timestamp updates
CREATE TRIGGER trigger_update_conversation_insights_timestamp
    BEFORE UPDATE ON conversation_insights
    FOR EACH ROW EXECUTE FUNCTION update_conversation_insights_timestamp();

-- Function to automatically update coaching opportunities timestamp
CREATE OR REPLACE FUNCTION update_coaching_opportunities_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for coaching opportunities timestamp updates
CREATE TRIGGER trigger_update_coaching_opportunities_timestamp
    BEFORE UPDATE ON coaching_opportunities
    FOR EACH ROW EXECUTE FUNCTION update_coaching_opportunities_timestamp();

-- Function to automatically calculate sentiment volatility
CREATE OR REPLACE FUNCTION calculate_sentiment_volatility()
RETURNS TRIGGER AS $$
DECLARE
    volatility_score DECIMAL(3,2);
BEGIN
    -- Calculate standard deviation of sentiment scores for this conversation
    SELECT COALESCE(STDDEV(sentiment_score)::DECIMAL(3,2), 0.0) INTO volatility_score
    FROM conversation_sentiment_timeline
    WHERE conversation_id = NEW.conversation_id;

    -- Update conversation insights with calculated volatility
    UPDATE conversation_insights
    SET sentiment_volatility = LEAST(volatility_score, 1.0)
    WHERE conversation_id = NEW.conversation_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic sentiment volatility calculation
CREATE TRIGGER trigger_calculate_sentiment_volatility
    AFTER INSERT OR UPDATE ON conversation_sentiment_timeline
    FOR EACH ROW EXECUTE FUNCTION calculate_sentiment_volatility();

-- Function to auto-notify managers of high-priority coaching opportunities
CREATE OR REPLACE FUNCTION notify_high_priority_coaching()
RETURNS TRIGGER AS $$
BEGIN
    -- For priority level 4 or 5, automatically schedule follow-up
    IF NEW.priority_level >= 4 AND NEW.follow_up_scheduled IS NULL THEN
        NEW.follow_up_scheduled = NOW() + INTERVAL '2 days';
        NEW.manager_notified = FALSE; -- Will trigger notification system
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for high-priority coaching opportunity notifications
CREATE TRIGGER trigger_notify_high_priority_coaching
    BEFORE INSERT ON coaching_opportunities
    FOR EACH ROW EXECUTE FUNCTION notify_high_priority_coaching();

-- Function to maintain objection resolution tracking
CREATE OR REPLACE FUNCTION track_objection_resolution()
RETURNS TRIGGER AS $$
BEGIN
    -- If objection is marked as resolved, update follow-up status
    IF NEW.objection_resolved = TRUE AND OLD.objection_resolved = FALSE THEN
        NEW.follow_up_needed = FALSE;
    END IF;

    -- If response effectiveness is high (>0.7), consider objection resolved
    IF NEW.response_effectiveness_score > 0.7 AND NEW.objection_resolved = FALSE THEN
        NEW.objection_resolved = TRUE;
        NEW.follow_up_needed = FALSE;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for objection resolution tracking
CREATE TRIGGER trigger_track_objection_resolution
    BEFORE UPDATE ON objection_detections
    FOR EACH ROW EXECUTE FUNCTION track_objection_resolution();

-- =====================================================================================
-- Performance and Maintenance Comments
-- =====================================================================================

-- Table Comments for Documentation
COMMENT ON TABLE conversation_insights IS 'Core conversation analysis with real-time insights, <500ms processing target';
COMMENT ON TABLE conversation_sentiment_timeline IS 'Detailed sentiment tracking throughout conversations for volatility analysis';
COMMENT ON TABLE objection_detections IS 'Real estate objection detection and resolution tracking with coaching integration';
COMMENT ON TABLE coaching_opportunities IS 'Automated coaching opportunity identification with manager workflow integration';

-- Column Comments for Key Performance Fields
COMMENT ON COLUMN conversation_insights.overall_engagement_score IS 'Lead engagement level (0.0-1.0), influences routing decisions';
COMMENT ON COLUMN conversation_insights.processing_duration_ms IS 'Analysis processing time, target <500ms for real-time use';
COMMENT ON COLUMN conversation_insights.cache_key IS 'Redis cache key for <50ms insight retrieval optimization';
COMMENT ON COLUMN objection_detections.response_effectiveness_score IS 'How well agent handled objection (0.0-1.0), coaching trigger';
COMMENT ON COLUMN coaching_opportunities.priority_level IS 'Coaching priority (1-5), level 4+ auto-schedules manager review';

-- Index Comments for Performance Monitoring
COMMENT ON INDEX idx_conversation_insights_lead_recent IS 'Optimizes recent conversation lookup for lead dashboard, <100ms target';
COMMENT ON INDEX idx_conversation_insights_cache_lookup IS 'Enables <50ms cache key retrieval for real-time insights';
COMMENT ON INDEX idx_objection_detections_unresolved IS 'Supports coaching workflow for unresolved objections, <200ms queries';

-- Migration completion marker
-- Migration 016 Complete: Conversation Intelligence Tables
-- Tables: 4 (conversation_insights, conversation_sentiment_timeline, objection_detections, coaching_opportunities)
-- Indexes: 22 (optimized for <500ms conversation processing)
-- Triggers: 5 (automated data maintenance and coaching workflows)
-- Performance Targets: <500ms conversation analysis, <50ms insight retrieval, <200ms coaching queries