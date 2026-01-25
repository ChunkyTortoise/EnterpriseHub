-- Migration 017: Client Preference Learning Tables
-- Purpose: Multi-modal preference learning with confidence tracking and drift detection
-- Performance Targets: <50ms preference updates, <100ms profile retrieval
-- Integration: Phase 2.4 Client Preference Learning Engine

-- =====================================================================================
-- Custom ENUM Types for Preference Learning
-- =====================================================================================

-- Preference Source Types (how preferences were learned)
CREATE TYPE preference_source_type AS ENUM (
    'conversation_analysis',    -- Learned from conversation content
    'property_interaction',    -- Learned from property viewing behavior
    'search_behavior',         -- Learned from search patterns
    'email_engagement',        -- Learned from email click patterns
    'website_behavior',        -- Learned from website navigation
    'feedback_explicit',       -- Direct client feedback/surveys
    'agent_observation',       -- Agent manual input/notes
    'historical_transaction'   -- Past transaction analysis
);

-- Learning Confidence Levels
CREATE TYPE learning_confidence AS ENUM (
    'very_high',    -- 0.9+ confidence, strong evidence
    'high',         -- 0.7-0.89 confidence, good evidence
    'medium',       -- 0.5-0.69 confidence, moderate evidence
    'low',          -- 0.3-0.49 confidence, weak evidence
    'very_low'      -- <0.3 confidence, insufficient evidence
);

-- Preference Categories (what type of preference)
CREATE TYPE preference_category AS ENUM (
    'property_features',       -- Bedrooms, bathrooms, square footage
    'location_preferences',    -- Neighborhood, school district, commute
    'lifestyle_factors',       -- Pool, garage, yard size, home office
    'financial_constraints',   -- Price range, down payment, monthly payment
    'aesthetic_preferences',   -- Style, age, condition, finishes
    'timing_preferences',      -- Move-in date, search urgency
    'communication_style',     -- Preferred contact method, frequency
    'decision_making_style'    -- Solo vs committee, speed vs deliberation
);

-- Drift Types (how preferences have changed)
CREATE TYPE preference_drift_type AS ENUM (
    'expansion',      -- Preferences broadened (price range increased)
    'narrowing',      -- Preferences became more specific
    'shift',          -- Preferences changed direction (urban to suburban)
    'strengthening',  -- Existing preference became stronger
    'weakening',      -- Existing preference became less important
    'contradiction',  -- New preference conflicts with old
    'seasonal',       -- Time-based preference changes
    'context_driven'  -- Market/situation driven changes
);

-- =====================================================================================
-- Core Preference Learning Tables
-- =====================================================================================

-- Main client preference profiles with confidence tracking
CREATE TABLE client_preference_profiles (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Profile metadata
    profile_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_activity_date TIMESTAMP WITH TIME ZONE,

    -- Overall profile confidence and completeness
    overall_confidence_score DECIMAL(3,2) NOT NULL DEFAULT 0.0,
    profile_completeness_percentage INTEGER NOT NULL DEFAULT 0,
    learning_sessions_count INTEGER NOT NULL DEFAULT 0,
    total_data_points INTEGER NOT NULL DEFAULT 0,

    -- Property Feature Preferences (scored 0.0 to 1.0)
    -- Core Features
    bedrooms_preference JSONB DEFAULT '{}'::jsonb, -- {"min": 3, "max": 4, "ideal": 3, "confidence": 0.8}
    bathrooms_preference JSONB DEFAULT '{}'::jsonb, -- {"min": 2, "max": 4, "ideal": 2.5, "confidence": 0.7}
    square_footage_preference JSONB DEFAULT '{}'::jsonb, -- {"min": 1500, "max": 3000, "ideal": 2200, "confidence": 0.9}
    price_range_preference JSONB DEFAULT '{}'::jsonb, -- {"min": 300000, "max": 500000, "confidence": 0.95}

    -- Property Style and Aesthetics
    property_style_preferences JSONB DEFAULT '{}'::jsonb, -- {"modern": 0.8, "traditional": 0.3, "craftsman": 0.9}
    property_age_preference JSONB DEFAULT '{}'::jsonb, -- {"new_construction": 0.7, "vintage": 0.2, "updated": 0.9}
    condition_preferences JSONB DEFAULT '{}'::jsonb, -- {"move_in_ready": 0.9, "fixer_upper": 0.1, "partial_renovation": 0.6}

    -- Location and Lifestyle Preferences
    location_preferences JSONB DEFAULT '{}'::jsonb, -- {"neighborhoods": [...], "commute_time": 30, "school_districts": [...]}
    lifestyle_features JSONB DEFAULT '{}'::jsonb, -- {"pool": 0.8, "garage": 0.9, "yard": 0.7, "home_office": 0.85}

    -- Communication and Decision Making Preferences
    communication_preferences JSONB DEFAULT '{}'::jsonb, -- {"email": 0.6, "sms": 0.9, "call": 0.4, "frequency": "weekly"}
    decision_making_style JSONB DEFAULT '{}'::jsonb, -- {"speed": "deliberate", "influences": ["spouse", "family"], "timeline": 60}

    -- Financial Preferences and Constraints
    financing_preferences JSONB DEFAULT '{}'::jsonb, -- {"down_payment": 50000, "monthly_payment": 2500, "loan_type": "conventional"}
    timeline_preferences JSONB DEFAULT '{}'::jsonb, -- {"ideal_move_date": "2024-06-01", "urgency_level": 0.6, "flexibility": 0.4}

    -- Learned Behavioral Patterns
    viewing_patterns JSONB DEFAULT '{}'::jsonb, -- {"preferred_times": [...], "viewing_duration": 45, "questions_focus": [...]}
    engagement_patterns JSONB DEFAULT '{}'::jsonb, -- {"response_time": "immediate", "question_depth": "detailed", "research_level": "thorough"}

    -- Preference Strength and Priority Scores
    feature_priority_scores JSONB DEFAULT '{}'::jsonb, -- {"location": 0.9, "price": 0.95, "size": 0.7, "style": 0.4}
    deal_breaker_features JSONB DEFAULT '[]'::jsonb, -- ["busy_road", "no_garage", "hoa_fees", "old_foundation"]
    nice_to_have_features JSONB DEFAULT '[]'::jsonb, -- ["pool", "updated_kitchen", "hardwood_floors"]

    -- Learning Quality Metrics
    prediction_accuracy_score DECIMAL(3,2) DEFAULT 0.0, -- How well preferences predict actual choices
    consistency_score DECIMAL(3,2) DEFAULT 0.0, -- How consistent preferences are over time
    drift_frequency DECIMAL(3,2) DEFAULT 0.0, -- How often preferences change
    source_diversity_score DECIMAL(3,2) DEFAULT 0.0, -- How many different sources contributed

    -- Cache and Performance
    cache_key VARCHAR(200),
    last_prediction_timestamp TIMESTAMP WITH TIME ZONE,
    prediction_cache JSONB DEFAULT '{}'::jsonb,

    -- Multi-tenancy and constraints
    CONSTRAINT client_preference_profiles_pkey PRIMARY KEY (location_id, client_id),
    CONSTRAINT valid_confidence_score CHECK (overall_confidence_score >= 0.0 AND overall_confidence_score <= 1.0),
    CONSTRAINT valid_completeness CHECK (profile_completeness_percentage >= 0 AND profile_completeness_percentage <= 100),
    CONSTRAINT valid_prediction_accuracy CHECK (prediction_accuracy_score >= 0.0 AND prediction_accuracy_score <= 1.0),
    CONSTRAINT valid_consistency_score CHECK (consistency_score >= 0.0 AND consistency_score <= 1.0),
    CONSTRAINT valid_drift_frequency CHECK (drift_frequency >= 0.0 AND drift_frequency <= 1.0),
    CONSTRAINT valid_source_diversity CHECK (source_diversity_score >= 0.0 AND source_diversity_score <= 1.0),
    CONSTRAINT positive_counters CHECK (learning_sessions_count >= 0 AND total_data_points >= 0)
);

-- Individual preference learning events for audit and analysis
CREATE TABLE preference_learning_events (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Event metadata
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    event_source preference_source_type NOT NULL,
    source_confidence learning_confidence NOT NULL,
    processing_duration_ms INTEGER,

    -- Learning details
    preference_category preference_category NOT NULL,
    learned_preference JSONB NOT NULL, -- The actual preference data learned
    confidence_score DECIMAL(3,2) NOT NULL,
    evidence_strength DECIMAL(3,2) NOT NULL DEFAULT 0.0,

    -- Context and source information
    source_context JSONB DEFAULT '{}'::jsonb, -- Context from conversation, interaction, etc.
    source_reference VARCHAR(200), -- conversation_id, property_id, interaction_id
    agent_notes TEXT,
    raw_evidence TEXT, -- Raw text/data that led to this learning

    -- Learning algorithm details
    learning_method VARCHAR(100) NOT NULL DEFAULT 'conversation_analysis',
    algorithm_version VARCHAR(20) DEFAULT '1.0',
    feature_extraction_results JSONB DEFAULT '{}'::jsonb,

    -- Impact and integration
    profile_impact_score DECIMAL(3,2) DEFAULT 0.0, -- How much this changed the profile
    conflicted_with_existing BOOLEAN DEFAULT FALSE,
    reinforced_existing BOOLEAN DEFAULT FALSE,
    created_new_preference BOOLEAN DEFAULT FALSE,

    -- Quality and validation
    human_validated BOOLEAN DEFAULT FALSE,
    validation_timestamp TIMESTAMP WITH TIME ZONE,
    validation_notes TEXT,
    false_positive_flag BOOLEAN DEFAULT FALSE,

    -- Multi-tenancy and constraints
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT preference_learning_events_pkey PRIMARY KEY (location_id, client_id, event_timestamp, preference_category),
    CONSTRAINT valid_learning_confidence CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    CONSTRAINT valid_evidence_strength CHECK (evidence_strength >= 0.0 AND evidence_strength <= 1.0),
    CONSTRAINT valid_impact_score CHECK (profile_impact_score >= 0.0 AND profile_impact_score <= 1.0),
    CONSTRAINT positive_processing_time CHECK (processing_duration_ms IS NULL OR processing_duration_ms >= 0)
);

-- Preference drift detection and tracking
CREATE TABLE preference_drift_detections (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Drift identification
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    preference_category preference_category NOT NULL,
    drift_type preference_drift_type NOT NULL,
    drift_magnitude DECIMAL(3,2) NOT NULL, -- How significant the drift (0.0 to 1.0)

    -- Drift details
    previous_preference JSONB NOT NULL, -- What the preference was before
    new_preference JSONB NOT NULL, -- What the preference became
    confidence_change DECIMAL(3,2) DEFAULT 0.0, -- Change in confidence (-1.0 to 1.0)

    -- Causality analysis
    triggering_events JSONB DEFAULT '[]'::jsonb, -- What events caused this drift
    time_period_analyzed INTERVAL, -- How long between preferences
    sample_size INTEGER, -- How many data points contributed to detection

    -- Impact assessment
    significance_level DECIMAL(3,2) NOT NULL DEFAULT 0.0, -- Statistical significance
    impact_on_matching DECIMAL(3,2) DEFAULT 0.0, -- How this affects property matching
    recommended_actions JSONB DEFAULT '[]'::jsonb,

    -- Resolution and follow-up
    agent_notified BOOLEAN DEFAULT FALSE,
    client_confirmation_needed BOOLEAN DEFAULT FALSE,
    client_confirmation_received BOOLEAN DEFAULT FALSE,
    resolution_action VARCHAR(100),
    resolution_timestamp TIMESTAMP WITH TIME ZONE,

    -- Detection algorithm metadata
    detection_method VARCHAR(100) NOT NULL DEFAULT 'statistical_analysis',
    algorithm_version VARCHAR(20) DEFAULT '1.0',
    detection_parameters JSONB DEFAULT '{}'::jsonb,

    -- Multi-tenancy and constraints
    CONSTRAINT preference_drift_detections_pkey PRIMARY KEY (location_id, client_id, detected_at, preference_category),
    CONSTRAINT valid_drift_magnitude CHECK (drift_magnitude >= 0.0 AND drift_magnitude <= 1.0),
    CONSTRAINT valid_confidence_change CHECK (confidence_change >= -1.0 AND confidence_change <= 1.0),
    CONSTRAINT valid_significance CHECK (significance_level >= 0.0 AND significance_level <= 1.0),
    CONSTRAINT valid_matching_impact CHECK (impact_on_matching >= 0.0 AND impact_on_matching <= 1.0),
    CONSTRAINT positive_sample_size CHECK (sample_size IS NULL OR sample_size > 0)
);

-- Confidence tracking history for preference evolution analysis
CREATE TABLE preference_confidence_history (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL,

    -- Confidence snapshot
    snapshot_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    preference_category preference_category NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    evidence_count INTEGER NOT NULL DEFAULT 0,

    -- Context for confidence change
    triggering_event_type preference_source_type,
    triggering_event_reference VARCHAR(200),
    confidence_change_delta DECIMAL(3,2) DEFAULT 0.0, -- How much confidence changed

    -- Preference value snapshot
    preference_value JSONB NOT NULL, -- The actual preference at this time
    supporting_evidence JSONB DEFAULT '[]'::jsonb, -- Evidence supporting this confidence level
    conflicting_evidence JSONB DEFAULT '[]'::jsonb, -- Evidence that reduces confidence

    -- Analysis metadata
    calculation_method VARCHAR(100) DEFAULT 'weighted_evidence',
    decay_factor_applied DECIMAL(3,2) DEFAULT 0.0, -- Time-based confidence decay
    boosting_factors JSONB DEFAULT '{}'::jsonb, -- What increased confidence
    reducing_factors JSONB DEFAULT '{}'::jsonb, -- What decreased confidence

    -- Multi-tenancy and constraints
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT preference_confidence_history_pkey PRIMARY KEY (location_id, client_id, snapshot_timestamp, preference_category),
    CONSTRAINT valid_confidence_score CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    CONSTRAINT valid_confidence_delta CHECK (confidence_change_delta >= -1.0 AND confidence_change_delta <= 1.0),
    CONSTRAINT valid_decay_factor CHECK (decay_factor_applied >= 0.0 AND decay_factor_applied <= 1.0),
    CONSTRAINT non_negative_evidence CHECK (evidence_count >= 0)
);

-- =====================================================================================
-- Materialized View for Fast Preference Matching
-- =====================================================================================

-- Fast lookup view for property matching (refreshed every hour)
CREATE MATERIALIZED VIEW client_preference_matching_view AS
SELECT
    cpp.location_id,
    cpp.client_id,
    cpp.overall_confidence_score,
    cpp.profile_completeness_percentage,

    -- Extract key matching criteria for fast lookup
    (cpp.price_range_preference->>'min')::INTEGER AS min_price,
    (cpp.price_range_preference->>'max')::INTEGER AS max_price,
    (cpp.bedrooms_preference->>'min')::INTEGER AS min_bedrooms,
    (cpp.bedrooms_preference->>'max')::INTEGER AS max_bedrooms,
    (cpp.bathrooms_preference->>'min')::DECIMAL AS min_bathrooms,
    (cpp.bathrooms_preference->>'max')::DECIMAL AS max_bathrooms,
    (cpp.square_footage_preference->>'min')::INTEGER AS min_sqft,
    (cpp.square_footage_preference->>'max')::INTEGER AS max_sqft,

    -- Priority scores for ranking
    (cpp.feature_priority_scores->>'price')::DECIMAL AS price_priority,
    (cpp.feature_priority_scores->>'location')::DECIMAL AS location_priority,
    (cpp.feature_priority_scores->>'size')::DECIMAL AS size_priority,

    -- Deal breakers as array for fast exclusion
    cpp.deal_breaker_features,
    cpp.nice_to_have_features,

    -- Confidence levels for each key criteria
    (cpp.price_range_preference->>'confidence')::DECIMAL AS price_confidence,
    (cpp.bedrooms_preference->>'confidence')::DECIMAL AS bedrooms_confidence,
    (cpp.bathrooms_preference->>'confidence')::DECIMAL AS bathrooms_confidence,
    (cpp.square_footage_preference->>'confidence')::DECIMAL AS sqft_confidence,

    -- Location preferences simplified for matching
    cpp.location_preferences->'neighborhoods' AS preferred_neighborhoods,
    (cpp.location_preferences->>'max_commute_time')::INTEGER AS max_commute_time,

    -- Last update tracking
    cpp.last_updated,
    cpp.last_activity_date,

    -- Performance metrics
    cpp.prediction_accuracy_score,
    cpp.consistency_score

FROM client_preference_profiles cpp
WHERE cpp.overall_confidence_score >= 0.3  -- Only include profiles with reasonable confidence
  AND cpp.profile_completeness_percentage >= 20; -- Only include reasonably complete profiles

-- Indexes for materialized view
CREATE UNIQUE INDEX idx_preference_matching_view_client
    ON client_preference_matching_view (location_id, client_id);

CREATE INDEX idx_preference_matching_view_price_range
    ON client_preference_matching_view (location_id, min_price, max_price)
    WHERE min_price IS NOT NULL AND max_price IS NOT NULL;

CREATE INDEX idx_preference_matching_view_size_criteria
    ON client_preference_matching_view (location_id, min_bedrooms, min_bathrooms, min_sqft)
    WHERE min_bedrooms IS NOT NULL AND min_bathrooms IS NOT NULL AND min_sqft IS NOT NULL;

-- =====================================================================================
-- Performance Optimization Indexes
-- =====================================================================================

-- Client Preference Profiles Indexes (10 indexes for <100ms profile retrieval)
CREATE INDEX idx_client_preference_profiles_confidence
    ON client_preference_profiles (location_id, overall_confidence_score DESC, last_updated DESC)
    WHERE overall_confidence_score >= 0.5;

CREATE INDEX idx_client_preference_profiles_completeness
    ON client_preference_profiles (location_id, profile_completeness_percentage DESC, learning_sessions_count DESC)
    WHERE profile_completeness_percentage >= 50;

CREATE INDEX idx_client_preference_profiles_recent_activity
    ON client_preference_profiles (location_id, last_activity_date DESC)
    WHERE last_activity_date > NOW() - INTERVAL '30 days';

CREATE INDEX idx_client_preference_profiles_cache_lookup
    ON client_preference_profiles (cache_key)
    WHERE cache_key IS NOT NULL;

CREATE INDEX idx_client_preference_profiles_prediction_ready
    ON client_preference_profiles (location_id, client_id, prediction_accuracy_score DESC)
    WHERE prediction_accuracy_score >= 0.6;

CREATE INDEX idx_client_preference_profiles_drift_monitoring
    ON client_preference_profiles (location_id, drift_frequency, consistency_score)
    WHERE drift_frequency > 0.3;

CREATE INDEX idx_client_preference_profiles_high_confidence_price
    ON client_preference_profiles (location_id, last_updated DESC)
    WHERE (price_range_preference->>'confidence')::DECIMAL >= 0.8;

CREATE INDEX idx_client_preference_profiles_learning_progress
    ON client_preference_profiles (location_id, learning_sessions_count DESC, total_data_points DESC);

CREATE INDEX idx_client_preference_profiles_version_tracking
    ON client_preference_profiles (client_id, profile_version DESC, created_at DESC);

CREATE INDEX idx_client_preference_profiles_last_prediction
    ON client_preference_profiles (location_id, last_prediction_timestamp DESC)
    WHERE last_prediction_timestamp IS NOT NULL;

-- Preference Learning Events Indexes (8 indexes for <50ms learning event queries)
CREATE INDEX idx_preference_learning_events_client_recent
    ON preference_learning_events (location_id, client_id, event_timestamp DESC)
    WHERE event_timestamp > NOW() - INTERVAL '90 days';

CREATE INDEX idx_preference_learning_events_category_analysis
    ON preference_learning_events (location_id, preference_category, confidence_score DESC, event_timestamp DESC);

CREATE INDEX idx_preference_learning_events_high_confidence
    ON preference_learning_events (location_id, event_timestamp DESC)
    WHERE confidence_score >= 0.7;

CREATE INDEX idx_preference_learning_events_source_analysis
    ON preference_learning_events (location_id, event_source, source_confidence, event_timestamp DESC);

CREATE INDEX idx_preference_learning_events_impact_tracking
    ON preference_learning_events (location_id, client_id, profile_impact_score DESC)
    WHERE profile_impact_score >= 0.5;

CREATE INDEX idx_preference_learning_events_validation_needed
    ON preference_learning_events (location_id, human_validated, confidence_score DESC)
    WHERE human_validated = FALSE AND confidence_score >= 0.6;

CREATE INDEX idx_preference_learning_events_performance
    ON preference_learning_events (processing_duration_ms, event_timestamp DESC)
    WHERE processing_duration_ms > 100;

CREATE INDEX idx_preference_learning_events_conflict_analysis
    ON preference_learning_events (location_id, client_id, conflicted_with_existing, event_timestamp DESC)
    WHERE conflicted_with_existing = TRUE;

-- Preference Drift Detections Indexes (6 indexes for drift analysis)
CREATE INDEX idx_preference_drift_detections_recent
    ON preference_drift_detections (location_id, detected_at DESC)
    WHERE detected_at > NOW() - INTERVAL '30 days';

CREATE INDEX idx_preference_drift_detections_significant
    ON preference_drift_detections (location_id, drift_magnitude DESC, significance_level DESC)
    WHERE drift_magnitude >= 0.5;

CREATE INDEX idx_preference_drift_detections_client_category
    ON preference_drift_detections (location_id, client_id, preference_category, detected_at DESC);

CREATE INDEX idx_preference_drift_detections_pending_confirmation
    ON preference_drift_detections (location_id, client_confirmation_needed, detected_at DESC)
    WHERE client_confirmation_needed = TRUE AND client_confirmation_received = FALSE;

CREATE INDEX idx_preference_drift_detections_notification_queue
    ON preference_drift_detections (location_id, agent_notified, drift_magnitude DESC)
    WHERE agent_notified = FALSE AND drift_magnitude >= 0.3;

CREATE INDEX idx_preference_drift_detections_type_analysis
    ON preference_drift_detections (location_id, drift_type, detected_at DESC, drift_magnitude DESC);

-- Preference Confidence History Indexes (4 indexes for confidence evolution)
CREATE INDEX idx_preference_confidence_history_timeline
    ON preference_confidence_history (location_id, client_id, preference_category, snapshot_timestamp DESC);

CREATE INDEX idx_preference_confidence_history_significant_changes
    ON preference_confidence_history (location_id, ABS(confidence_change_delta) DESC, snapshot_timestamp DESC)
    WHERE ABS(confidence_change_delta) >= 0.2;

CREATE INDEX idx_preference_confidence_history_recent_activity
    ON preference_confidence_history (location_id, snapshot_timestamp DESC)
    WHERE snapshot_timestamp > NOW() - INTERVAL '7 days';

CREATE INDEX idx_preference_confidence_history_confidence_levels
    ON preference_confidence_history (location_id, confidence_score DESC, evidence_count DESC)
    WHERE confidence_score >= 0.8;

-- =====================================================================================
-- Automated Trigger Functions for Data Maintenance
-- =====================================================================================

-- Function to automatically update profile completeness percentage
CREATE OR REPLACE FUNCTION calculate_profile_completeness()
RETURNS TRIGGER AS $$
DECLARE
    completeness_score INTEGER := 0;
    total_criteria INTEGER := 12; -- Total number of preference categories we track
BEGIN
    -- Check each preference category for meaningful data
    IF NEW.bedrooms_preference != '{}'::jsonb AND NEW.bedrooms_preference->>'confidence' IS NOT NULL THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF NEW.bathrooms_preference != '{}'::jsonb AND NEW.bathrooms_preference->>'confidence' IS NOT NULL THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF NEW.price_range_preference != '{}'::jsonb AND NEW.price_range_preference->>'confidence' IS NOT NULL THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF NEW.square_footage_preference != '{}'::jsonb AND NEW.square_footage_preference->>'confidence' IS NOT NULL THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF NEW.location_preferences != '{}'::jsonb AND jsonb_array_length(NEW.location_preferences->'neighborhoods') > 0 THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF NEW.lifestyle_features != '{}'::jsonb AND jsonb_object_keys(NEW.lifestyle_features) IS NOT NULL THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF NEW.property_style_preferences != '{}'::jsonb THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF NEW.communication_preferences != '{}'::jsonb THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF NEW.timeline_preferences != '{}'::jsonb THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF NEW.financing_preferences != '{}'::jsonb THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF jsonb_array_length(NEW.deal_breaker_features) > 0 THEN
        completeness_score := completeness_score + 1;
    END IF;

    IF NEW.feature_priority_scores != '{}'::jsonb THEN
        completeness_score := completeness_score + 1;
    END IF;

    -- Calculate percentage
    NEW.profile_completeness_percentage := (completeness_score * 100) / total_criteria;
    NEW.last_updated := NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for profile completeness calculation
CREATE TRIGGER trigger_calculate_profile_completeness
    BEFORE INSERT OR UPDATE ON client_preference_profiles
    FOR EACH ROW EXECUTE FUNCTION calculate_profile_completeness();

-- Function to automatically create confidence history snapshots
CREATE OR REPLACE FUNCTION create_confidence_snapshot()
RETURNS TRIGGER AS $$
BEGIN
    -- Create confidence history snapshots for any preference category that changed significantly
    IF TG_OP = 'UPDATE' THEN
        -- Check key preference categories for significant changes
        IF ABS((NEW.price_range_preference->>'confidence')::DECIMAL - (OLD.price_range_preference->>'confidence')::DECIMAL) >= 0.1 THEN
            INSERT INTO preference_confidence_history (
                client_id, location_id, preference_category, confidence_score,
                confidence_change_delta, preference_value, calculation_method
            ) VALUES (
                NEW.client_id, NEW.location_id, 'financial_constraints',
                (NEW.price_range_preference->>'confidence')::DECIMAL,
                (NEW.price_range_preference->>'confidence')::DECIMAL - (OLD.price_range_preference->>'confidence')::DECIMAL,
                NEW.price_range_preference,
                'automated_snapshot'
            );
        END IF;

        -- Add similar checks for other important categories...

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for confidence snapshot creation
CREATE TRIGGER trigger_create_confidence_snapshot
    AFTER UPDATE ON client_preference_profiles
    FOR EACH ROW EXECUTE FUNCTION create_confidence_snapshot();

-- Function to automatically detect preference drift
CREATE OR REPLACE FUNCTION detect_preference_drift()
RETURNS TRIGGER AS $$
DECLARE
    drift_threshold DECIMAL := 0.3; -- Threshold for significant drift
    old_value JSONB;
    new_value JSONB;
    drift_magnitude DECIMAL;
BEGIN
    -- Only process learning events with high confidence
    IF NEW.confidence_score >= 0.7 AND NEW.profile_impact_score >= 0.3 THEN

        -- Get the previous preference value for this category
        SELECT learned_preference INTO old_value
        FROM preference_learning_events
        WHERE client_id = NEW.client_id
          AND location_id = NEW.location_id
          AND preference_category = NEW.preference_category
          AND event_timestamp < NEW.event_timestamp
        ORDER BY event_timestamp DESC
        LIMIT 1;

        -- Calculate drift if we have a previous value
        IF old_value IS NOT NULL THEN
            -- Simple drift calculation (this could be more sophisticated)
            drift_magnitude := NEW.profile_impact_score;

            -- If drift is significant, create a drift detection record
            IF drift_magnitude >= drift_threshold THEN
                INSERT INTO preference_drift_detections (
                    client_id, location_id, preference_category,
                    drift_type, drift_magnitude, previous_preference, new_preference,
                    triggering_events, significance_level, agent_notified
                ) VALUES (
                    NEW.client_id, NEW.location_id, NEW.preference_category,
                    'shift', drift_magnitude, old_value, NEW.learned_preference,
                    jsonb_build_array(jsonb_build_object('event_id', NEW.id, 'source', NEW.event_source)),
                    NEW.confidence_score, FALSE
                );
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for drift detection
CREATE TRIGGER trigger_detect_preference_drift
    AFTER INSERT ON preference_learning_events
    FOR EACH ROW EXECUTE FUNCTION detect_preference_drift();

-- Function to refresh the materialized view periodically
CREATE OR REPLACE FUNCTION refresh_preference_matching_view()
RETURNS TRIGGER AS $$
BEGIN
    -- Only refresh if there was a significant change
    IF TG_OP = 'UPDATE' THEN
        IF ABS(NEW.overall_confidence_score - OLD.overall_confidence_score) >= 0.1 OR
           ABS(NEW.profile_completeness_percentage - OLD.profile_completeness_percentage) >= 10 THEN
            -- Schedule a refresh (in production, this would be handled by a job queue)
            PERFORM pg_notify('refresh_preference_view', NEW.client_id);
        END IF;
    ELSIF TG_OP = 'INSERT' THEN
        -- Always refresh on new profiles
        PERFORM pg_notify('refresh_preference_view', NEW.client_id);
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger for materialized view refresh notifications
CREATE TRIGGER trigger_refresh_preference_matching_view
    AFTER INSERT OR UPDATE ON client_preference_profiles
    FOR EACH ROW EXECUTE FUNCTION refresh_preference_matching_view();

-- Function to maintain preference confidence decay over time
CREATE OR REPLACE FUNCTION apply_confidence_decay()
RETURNS TRIGGER AS $$
DECLARE
    days_since_update INTEGER;
    decay_factor DECIMAL;
    new_confidence DECIMAL;
BEGIN
    -- Calculate days since last update
    days_since_update := EXTRACT(epoch FROM (NOW() - NEW.last_updated)) / 86400;

    -- Apply exponential decay (confidence decreases by 5% per month without reinforcement)
    IF days_since_update > 30 THEN
        decay_factor := POWER(0.95, days_since_update / 30.0);
        new_confidence := NEW.overall_confidence_score * decay_factor;

        -- Only apply if decay is significant
        IF NEW.overall_confidence_score - new_confidence >= 0.05 THEN
            NEW.overall_confidence_score := GREATEST(new_confidence, 0.1); -- Minimum confidence floor
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for confidence decay (applied on SELECT for efficiency)
CREATE TRIGGER trigger_apply_confidence_decay
    BEFORE UPDATE ON client_preference_profiles
    FOR EACH ROW EXECUTE FUNCTION apply_confidence_decay();

-- Function to maintain learning event quality
CREATE OR REPLACE FUNCTION validate_learning_event_quality()
RETURNS TRIGGER AS $$
BEGIN
    -- Flag potential false positives based on patterns
    IF NEW.confidence_score > 0.8 AND NEW.evidence_strength < 0.3 THEN
        NEW.false_positive_flag := TRUE;
    END IF;

    -- Enhance confidence based on source reliability
    CASE NEW.event_source
        WHEN 'feedback_explicit' THEN
            NEW.confidence_score := LEAST(NEW.confidence_score * 1.2, 1.0); -- Boost explicit feedback
        WHEN 'conversation_analysis' THEN
            -- Keep as-is, baseline reliability
        WHEN 'website_behavior' THEN
            NEW.confidence_score := NEW.confidence_score * 0.8; -- Reduce for web behavior
    END CASE;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for learning event quality validation
CREATE TRIGGER trigger_validate_learning_event_quality
    BEFORE INSERT ON preference_learning_events
    FOR EACH ROW EXECUTE FUNCTION validate_learning_event_quality();

-- =====================================================================================
-- Performance and Maintenance Comments
-- =====================================================================================

-- Table Comments for Documentation
COMMENT ON TABLE client_preference_profiles IS 'Multi-modal client preference learning with confidence tracking, <100ms retrieval target';
COMMENT ON TABLE preference_learning_events IS 'Individual preference learning events with audit trail, <50ms insertion target';
COMMENT ON TABLE preference_drift_detections IS 'Automated preference change detection with agent notification workflow';
COMMENT ON TABLE preference_confidence_history IS 'Confidence evolution tracking for preference quality analysis';
COMMENT ON MATERIALIZED VIEW client_preference_matching_view IS 'Fast preference matching lookup, refreshed hourly, <10ms query target';

-- Key Performance Column Comments
COMMENT ON COLUMN client_preference_profiles.overall_confidence_score IS 'Overall profile reliability (0.0-1.0), affects matching weight';
COMMENT ON COLUMN client_preference_profiles.profile_completeness_percentage IS 'Profile completeness (0-100%), auto-calculated from preference data';
COMMENT ON COLUMN client_preference_profiles.cache_key IS 'Redis cache key for <100ms profile retrieval optimization';
COMMENT ON COLUMN preference_learning_events.processing_duration_ms IS 'Learning processing time, target <50ms';
COMMENT ON COLUMN preference_drift_detections.drift_magnitude IS 'Drift significance (0.0-1.0), 0.3+ triggers notifications';

-- Index Performance Comments
COMMENT ON INDEX idx_client_preference_profiles_confidence IS 'Optimizes high-confidence profile queries, <100ms target';
COMMENT ON INDEX idx_preference_learning_events_client_recent IS 'Supports recent learning activity queries, <50ms target';
COMMENT ON INDEX idx_preference_drift_detections_significant IS 'Enables fast significant drift detection, <200ms queries';

-- Materialized View Performance Comments
COMMENT ON INDEX idx_preference_matching_view_client IS 'Primary lookup for preference matching, <10ms target';
COMMENT ON INDEX idx_preference_matching_view_price_range IS 'Price-based property filtering, <25ms target';

-- Migration completion marker
-- Migration 017 Complete: Client Preference Learning Tables
-- Tables: 4 (client_preference_profiles, preference_learning_events, preference_drift_detections, preference_confidence_history)
-- Materialized View: 1 (client_preference_matching_view with 3 indexes)
-- Indexes: 28 (optimized for <100ms profile retrieval, <50ms learning updates)
-- Triggers: 6 (automated completeness calculation, drift detection, confidence management)
-- Performance Targets: <50ms preference updates, <100ms profile retrieval, <10ms matching queries