-- ============================================================================
-- Predictive Lead Behavior Tables - Phase 2.1
-- Extends Jorge's Real Estate AI Platform with behavioral prediction capabilities
-- ============================================================================

-- Behavioral Predictions Storage
-- Primary table for storing comprehensive behavioral predictions
CREATE TABLE IF NOT EXISTS behavioral_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255),

    -- Prediction Results
    behavior_category VARCHAR(50) NOT NULL,           -- highly_engaged, moderately_engaged, etc.
    category_confidence DECIMAL(5,4) NOT NULL,        -- 0-1 confidence in category
    engagement_score_7d DECIMAL(5,2) NOT NULL,        -- 0-100 7-day engagement score
    churn_risk_score DECIMAL(5,2) NOT NULL,           -- 0-100 churn risk (100 = high risk)
    conversion_readiness_score DECIMAL(5,2) NOT NULL, -- 0-100 conversion readiness

    -- Next Actions (JSONB for flexibility)
    next_actions JSONB NOT NULL,                      -- Top 3 predicted actions with probabilities

    -- Engagement Analysis
    engagement_trend JSONB,                           -- Trend analysis data
    communication_preferences JSONB,                  -- Channel preferences (sms, email, call)
    optimal_contact_windows JSONB,                    -- Best contact time windows

    -- Risk Assessment
    churn_risk_factors TEXT[],                        -- Array of risk factors
    objection_patterns TEXT[],                        -- Array of objection patterns

    -- Response Predictions
    response_probability_24h DECIMAL(5,4),            -- Probability of response in 24h
    expected_response_time_hours DECIMAL(8,2),        -- Expected response time
    estimated_conversion_days INTEGER,                -- Expected conversion timeline
    decision_velocity VARCHAR(20),                    -- fast, moderate, slow

    -- Prediction Metadata
    feature_count INTEGER,                            -- Number of features used
    prediction_latency_ms DECIMAL(8,2),               -- Prediction computation time
    model_version VARCHAR(50) DEFAULT 'v1.0',         -- Model version used
    prediction_accuracy_recent DECIMAL(5,4),          -- Recent accuracy for this lead
    feedback_count INTEGER DEFAULT 0,                 -- Number of feedback events

    -- Timestamps
    predicted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,              -- Cache expiry
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Multi-tenant isolation
    CONSTRAINT behavioral_predictions_tenant_key UNIQUE (location_id, lead_id, predicted_at)
);

-- Indexes for performance (multi-tenant aware)
CREATE INDEX idx_behavioral_predictions_lead ON behavioral_predictions(lead_id, location_id, predicted_at DESC);
CREATE INDEX idx_behavioral_predictions_category ON behavioral_predictions(behavior_category, location_id);
CREATE INDEX idx_behavioral_predictions_churn_risk ON behavioral_predictions(churn_risk_score DESC, location_id);
CREATE INDEX idx_behavioral_predictions_engagement ON behavioral_predictions(engagement_score_7d DESC, location_id);
CREATE INDEX idx_behavioral_predictions_expires ON behavioral_predictions(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_behavioral_predictions_recent ON behavioral_predictions(location_id, predicted_at DESC) WHERE predicted_at > NOW() - INTERVAL '7 days';

-- ============================================================================
-- Behavioral Events History
-- Tracks individual behavioral events for trend analysis
-- ============================================================================

CREATE TABLE IF NOT EXISTS behavioral_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255),

    -- Event Details
    event_type VARCHAR(100) NOT NULL,                 -- response, engagement, objection, ghost, etc.
    event_data JSONB NOT NULL,                        -- Flexible event data structure

    -- Context
    conversation_id VARCHAR(255),                     -- Associated conversation
    message_id VARCHAR(255),                          -- Associated message
    channel VARCHAR(50),                              -- sms, email, call, etc.
    source_system VARCHAR(50) DEFAULT 'jorge',        -- Which system generated event

    -- Metrics
    response_time_ms BIGINT,                          -- Response time in milliseconds
    sentiment_score DECIMAL(5,4),                     -- -1 to 1 sentiment
    engagement_score DECIMAL(5,2),                    -- 0-100 engagement level
    message_length INTEGER,                           -- Length of message
    complexity_score DECIMAL(5,2),                    -- Message complexity (0-100)

    -- Behavioral Signals
    contains_question BOOLEAN DEFAULT FALSE,          -- Message contains questions
    contains_objection BOOLEAN DEFAULT FALSE,         -- Message contains objections
    contains_urgency BOOLEAN DEFAULT FALSE,           -- Message shows urgency
    contains_positive_signal BOOLEAN DEFAULT FALSE,   -- Message shows buying signals

    -- Timestamps
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Multi-tenant isolation
    CONSTRAINT behavioral_events_tenant_key UNIQUE (location_id, lead_id, event_timestamp, event_type)
);

-- Time-series optimized indexes for behavioral analysis
CREATE INDEX idx_behavioral_events_lead_time ON behavioral_events(lead_id, location_id, event_timestamp DESC);
CREATE INDEX idx_behavioral_events_type ON behavioral_events(event_type, location_id, event_timestamp DESC);
CREATE INDEX idx_behavioral_events_timestamp ON behavioral_events(event_timestamp DESC);
CREATE INDEX idx_behavioral_events_channel ON behavioral_events(channel, location_id);
CREATE INDEX idx_behavioral_events_recent ON behavioral_events(location_id, event_timestamp DESC) WHERE event_timestamp > NOW() - INTERVAL '30 days';

-- ============================================================================
-- Behavioral Feedback (Learning Loop)
-- Stores feedback on prediction accuracy for model improvement
-- ============================================================================

CREATE TABLE IF NOT EXISTS behavioral_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES behavioral_predictions(id) ON DELETE CASCADE,
    lead_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,

    -- Prediction vs Reality
    predicted_action VARCHAR(100) NOT NULL,           -- What was predicted
    actual_action VARCHAR(100) NOT NULL,              -- What actually happened
    prediction_accuracy DECIMAL(5,4) NOT NULL,        -- Accuracy score (0-1)
    feedback_type VARCHAR(50) NOT NULL,               -- correct, incorrect, partial

    -- Context
    context_data JSONB,                               -- Additional context
    time_to_action_hours DECIMAL(8,2),               -- Actual time to action
    prediction_confidence DECIMAL(5,4),               -- Original prediction confidence

    -- Learning Metadata
    model_version VARCHAR(50),                        -- Model version when prediction made
    feedback_source VARCHAR(50) DEFAULT 'system',    -- system, agent, manual
    correction_applied BOOLEAN DEFAULT FALSE,        -- Whether correction was applied

    -- Timestamps
    action_occurred_at TIMESTAMP WITH TIME ZONE,     -- When actual action occurred
    feedback_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for feedback analysis and learning
CREATE INDEX idx_behavioral_feedback_prediction ON behavioral_feedback(prediction_id);
CREATE INDEX idx_behavioral_feedback_lead ON behavioral_feedback(lead_id, location_id);
CREATE INDEX idx_behavioral_feedback_accuracy ON behavioral_feedback(prediction_accuracy, feedback_type);
CREATE INDEX idx_behavioral_feedback_model ON behavioral_feedback(model_version, feedback_type);
CREATE INDEX idx_behavioral_feedback_recent ON behavioral_feedback(feedback_timestamp DESC);

-- ============================================================================
-- Behavioral Trends (Aggregated Analytics)
-- Pre-computed trend analysis for fast dashboard queries
-- ============================================================================

CREATE TABLE IF NOT EXISTS behavioral_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id VARCHAR(255) NOT NULL,

    -- Trend Analysis
    trend_type VARCHAR(100) NOT NULL,                 -- engagement, churn, conversion, response_rate
    cohort_segment VARCHAR(100),                      -- Optional: industry, source, agent

    -- Metrics
    trend_direction VARCHAR(50) NOT NULL,             -- increasing, decreasing, stable
    velocity DECIMAL(8,4) NOT NULL,                   -- Rate of change
    confidence DECIMAL(5,4) NOT NULL,                 -- Trend confidence (0-1)
    data_points INTEGER NOT NULL,                     -- Number of observations
    baseline_value DECIMAL(10,4),                     -- Starting value
    current_value DECIMAL(10,4),                      -- Current value
    projected_value DECIMAL(10,4),                    -- Projected future value

    -- Statistical Metrics
    standard_deviation DECIMAL(10,4),                 -- Data variance
    correlation_coefficient DECIMAL(5,4),             -- Trend correlation
    statistical_significance DECIMAL(5,4),            -- p-value

    -- Time Window
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    time_window_hours INTEGER NOT NULL,

    -- Metadata
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for trend analysis and reporting
CREATE INDEX idx_behavioral_trends_location ON behavioral_trends(location_id, trend_type);
CREATE INDEX idx_behavioral_trends_window ON behavioral_trends(window_start, window_end);
CREATE INDEX idx_behavioral_trends_significance ON behavioral_trends(statistical_significance DESC, confidence DESC);
CREATE INDEX idx_behavioral_trends_recent ON behavioral_trends(location_id, detected_at DESC);

-- ============================================================================
-- Materialized View for Performance (Refreshed every 15 minutes)
-- Fast queries for dashboard and analytics
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS behavioral_analytics_summary AS
SELECT
    location_id,
    behavior_category,
    COUNT(*) as prediction_count,
    AVG(engagement_score_7d) as avg_engagement,
    AVG(churn_risk_score) as avg_churn_risk,
    AVG(conversion_readiness_score) as avg_conversion_readiness,
    AVG(prediction_latency_ms) as avg_latency_ms,
    AVG(category_confidence) as avg_confidence,
    AVG(response_probability_24h) as avg_response_probability,
    COUNT(CASE WHEN churn_risk_score > 70 THEN 1 END) as high_churn_risk_count,
    COUNT(CASE WHEN conversion_readiness_score > 80 THEN 1 END) as high_conversion_ready_count,
    DATE_TRUNC('hour', predicted_at) as hour_bucket,
    MIN(predicted_at) as first_prediction,
    MAX(predicted_at) as last_prediction
FROM behavioral_predictions
WHERE predicted_at > NOW() - INTERVAL '7 days'
GROUP BY location_id, behavior_category, DATE_TRUNC('hour', predicted_at);

-- Unique index for materialized view
CREATE UNIQUE INDEX idx_behavioral_summary_unique
ON behavioral_analytics_summary(location_id, behavior_category, hour_bucket);

-- Additional indexes for common queries
CREATE INDEX idx_behavioral_summary_location ON behavioral_analytics_summary(location_id, hour_bucket DESC);
CREATE INDEX idx_behavioral_summary_engagement ON behavioral_analytics_summary(avg_engagement DESC, location_id);
CREATE INDEX idx_behavioral_summary_churn ON behavioral_analytics_summary(avg_churn_risk DESC, location_id);

-- ============================================================================
-- Behavioral Model Performance Tracking
-- Tracks model accuracy and performance over time
-- ============================================================================

CREATE TABLE IF NOT EXISTS behavioral_model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id VARCHAR(255) NOT NULL,
    model_version VARCHAR(50) NOT NULL,

    -- Performance Metrics
    overall_accuracy DECIMAL(5,4) NOT NULL,           -- Overall prediction accuracy
    category_accuracy JSONB,                          -- Accuracy by behavior category
    action_accuracy JSONB,                            -- Accuracy by action type

    -- Volume Metrics
    total_predictions INTEGER DEFAULT 0,
    total_feedback INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,

    -- Latency Metrics
    avg_prediction_latency_ms DECIMAL(8,2),
    p95_prediction_latency_ms DECIMAL(8,2),
    p99_prediction_latency_ms DECIMAL(8,2),

    -- Time Window
    measurement_start TIMESTAMP WITH TIME ZONE NOT NULL,
    measurement_end TIMESTAMP WITH TIME ZONE NOT NULL,
    measurement_period_hours INTEGER NOT NULL,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_model_performance_location ON behavioral_model_performance(location_id, model_version);
CREATE INDEX idx_model_performance_accuracy ON behavioral_model_performance(overall_accuracy DESC);
CREATE INDEX idx_model_performance_recent ON behavioral_model_performance(measurement_end DESC);

-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- Function to refresh behavioral analytics materialized view
CREATE OR REPLACE FUNCTION refresh_behavioral_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY behavioral_analytics_summary;

    -- Log refresh
    INSERT INTO system_logs (log_level, message, created_at)
    VALUES ('INFO', 'Behavioral analytics summary refreshed', NOW());
EXCEPTION
    WHEN OTHERS THEN
        -- Log error but don't fail
        INSERT INTO system_logs (log_level, message, error_details, created_at)
        VALUES ('ERROR', 'Failed to refresh behavioral analytics', SQLERRM, NOW());
END;
$$ LANGUAGE plpgsql;

-- Function to calculate prediction accuracy
CREATE OR REPLACE FUNCTION calculate_prediction_accuracy(
    predicted_action TEXT,
    actual_action TEXT
) RETURNS DECIMAL(5,4) AS $$
BEGIN
    -- Simple string similarity - can be enhanced with more sophisticated matching
    IF predicted_action = actual_action THEN
        RETURN 1.0;
    ELSIF predicted_action IS NULL OR actual_action IS NULL THEN
        RETURN 0.0;
    ELSIF LOWER(predicted_action) = LOWER(actual_action) THEN
        RETURN 0.9;
    ELSIF
        (LOWER(predicted_action) LIKE '%' || LOWER(actual_action) || '%') OR
        (LOWER(actual_action) LIKE '%' || LOWER(predicted_action) || '%')
    THEN
        RETURN 0.7;
    ELSE
        RETURN 0.0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate accuracy when feedback is inserted
CREATE OR REPLACE FUNCTION auto_calculate_feedback_accuracy()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate accuracy if not provided
    IF NEW.prediction_accuracy IS NULL THEN
        NEW.prediction_accuracy = calculate_prediction_accuracy(
            NEW.predicted_action,
            NEW.actual_action
        );
    END IF;

    -- Determine feedback type if not provided
    IF NEW.feedback_type IS NULL THEN
        NEW.feedback_type = CASE
            WHEN NEW.prediction_accuracy >= 0.8 THEN 'correct'
            WHEN NEW.prediction_accuracy >= 0.3 THEN 'partial'
            ELSE 'incorrect'
        END;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_auto_calculate_feedback_accuracy
    BEFORE INSERT OR UPDATE ON behavioral_feedback
    FOR EACH ROW
    EXECUTE FUNCTION auto_calculate_feedback_accuracy();

-- Trigger to update behavioral_predictions.updated_at
CREATE OR REPLACE FUNCTION update_behavioral_predictions_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_behavioral_predictions_timestamp
    BEFORE UPDATE ON behavioral_predictions
    FOR EACH ROW
    EXECUTE FUNCTION update_behavioral_predictions_timestamp();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE behavioral_predictions IS 'Stores comprehensive ML-generated behavioral predictions for leads with engagement, churn risk, and conversion readiness scoring';
COMMENT ON TABLE behavioral_events IS 'Time-series tracking of individual behavioral events for pattern analysis and trend detection';
COMMENT ON TABLE behavioral_feedback IS 'Learning feedback loop data for continuous model improvement and accuracy tracking';
COMMENT ON TABLE behavioral_trends IS 'Pre-computed trend analysis for fast dashboard queries and business intelligence';
COMMENT ON MATERIALIZED VIEW behavioral_analytics_summary IS 'High-performance aggregated analytics refreshed every 15 minutes for dashboard display';
COMMENT ON TABLE behavioral_model_performance IS 'Model accuracy and performance metrics tracking for MLOps monitoring';

-- Column comments for key fields
COMMENT ON COLUMN behavioral_predictions.behavior_category IS 'ML-classified behavioral category (highly_engaged, moderately_engaged, low_engagement, dormant, churning, converting)';
COMMENT ON COLUMN behavioral_predictions.next_actions IS 'JSONB array of top 3 predicted actions with probabilities, timing, and confidence scores';
COMMENT ON COLUMN behavioral_predictions.churn_risk_score IS 'ML-calculated churn risk score (0-100, where 100 indicates imminent churn)';
COMMENT ON COLUMN behavioral_predictions.optimal_contact_windows IS 'JSONB array of optimal contact time windows based on historical response patterns';

COMMENT ON COLUMN behavioral_events.event_data IS 'Flexible JSONB structure for event-specific data (response time, sentiment, message content analysis)';
COMMENT ON COLUMN behavioral_events.response_time_ms IS 'Lead response time in milliseconds for velocity analysis';

COMMENT ON COLUMN behavioral_feedback.prediction_accuracy IS 'Calculated accuracy score (0-1) comparing predicted vs actual actions for learning loop';
COMMENT ON COLUMN behavioral_feedback.feedback_type IS 'Classification: correct (>0.8), partial (0.3-0.8), incorrect (<0.3)';

-- ============================================================================
-- Performance Optimization Commands
-- ============================================================================

-- Analyze tables for query planner optimization
ANALYZE behavioral_predictions;
ANALYZE behavioral_events;
ANALYZE behavioral_feedback;
ANALYZE behavioral_trends;

-- Set autovacuum parameters for high-insert tables
ALTER TABLE behavioral_events SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

ALTER TABLE behavioral_feedback SET (
    autovacuum_vacuum_scale_factor = 0.2,
    autovacuum_analyze_scale_factor = 0.1
);

-- ============================================================================
-- Initial Data Setup
-- ============================================================================

-- Create initial system log entry
INSERT INTO system_logs (log_level, message, created_at)
VALUES ('INFO', 'Behavioral prediction tables created successfully', NOW())
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust as needed for your user roles)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON behavioral_predictions TO application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON behavioral_events TO application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON behavioral_feedback TO application_user;
-- GRANT SELECT ON behavioral_analytics_summary TO readonly_user;