-- Enhanced Leads Table - Cross-Track Integration
-- Extends existing leads table with cross-track columns for Phase 1 integration
-- Maintains backward compatibility while adding enhanced capabilities

-- Add new columns to existing leads table for enhanced capabilities
ALTER TABLE leads ADD COLUMN IF NOT EXISTS enhanced_scoring_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_enhanced_score DECIMAL(5,2);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_enhanced_score_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS source_quality_score DECIMAL(5,2);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS behavioral_engagement_score DECIMAL(5,2);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS conversion_readiness_score DECIMAL(5,2);

-- Journey Integration Columns
ALTER TABLE leads ADD COLUMN IF NOT EXISTS journey_stage VARCHAR(50);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS journey_health_status VARCHAR(20);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS journey_start_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS milestone_completion_rate DECIMAL(5,2);

-- Attribution and Source Enhancement
ALTER TABLE leads ADD COLUMN IF NOT EXISTS source_attribution_data JSONB;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS attribution_confidence DECIMAL(3,2) DEFAULT 1.00;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS multi_touch_attribution JSONB;

-- AI Enhancement Integration
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_insights_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_ai_analysis TIMESTAMP WITH TIME ZONE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_recommendations JSONB;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS automation_triggers JSONB;

-- Performance Optimization
ALTER TABLE leads ADD COLUMN IF NOT EXISTS priority_score DECIMAL(5,2) DEFAULT 0.00;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS optimization_flags JSONB;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_optimization_check TIMESTAMP WITH TIME ZONE;

-- Cross-Track Coordination
ALTER TABLE leads ADD COLUMN IF NOT EXISTS cross_track_context JSONB; -- Context shared between Track A and Track B
ALTER TABLE leads ADD COLUMN IF NOT EXISTS handoff_metadata JSONB; -- Lead-to-Client handoff data
ALTER TABLE leads ADD COLUMN IF NOT EXISTS experience_personalization JSONB; -- Personalization settings

-- Add indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_leads_enhanced_score ON leads(location_id, last_enhanced_score DESC, last_enhanced_score_date DESC);
CREATE INDEX IF NOT EXISTS idx_leads_journey_stage ON leads(location_id, journey_stage, journey_health_status);
CREATE INDEX IF NOT EXISTS idx_leads_priority ON leads(location_id, priority_score DESC, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_ai_analysis ON leads(location_id, ai_insights_enabled, last_ai_analysis DESC);
CREATE INDEX IF NOT EXISTS idx_leads_source_quality ON leads(location_id, source_quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_journey_health ON leads(location_id, journey_health_status, milestone_completion_rate DESC);

-- Add partial indexes for optimization (only for active records)
CREATE INDEX IF NOT EXISTS idx_leads_enhanced_active ON leads(location_id, last_enhanced_score DESC)
    WHERE enhanced_scoring_enabled = TRUE AND status NOT IN ('closed_lost', 'archived');

CREATE INDEX IF NOT EXISTS idx_leads_journey_active ON leads(location_id, journey_stage, journey_health_status)
    WHERE journey_stage IS NOT NULL AND journey_health_status IS NOT NULL;

-- Comments for new columns
COMMENT ON COLUMN leads.enhanced_scoring_enabled IS 'Whether enhanced AI scoring is enabled for this lead';
COMMENT ON COLUMN leads.last_enhanced_score IS 'Most recent enhanced AI lead score (0-100)';
COMMENT ON COLUMN leads.last_enhanced_score_date IS 'When the enhanced score was last calculated';
COMMENT ON COLUMN leads.source_quality_score IS 'Quality score of the lead source (0-100)';
COMMENT ON COLUMN leads.behavioral_engagement_score IS 'Behavioral engagement score based on interactions (0-100)';
COMMENT ON COLUMN leads.conversion_readiness_score IS 'ML-based conversion readiness score (0-100)';
COMMENT ON COLUMN leads.journey_stage IS 'Current stage in client journey (qualified, property_search, etc.)';
COMMENT ON COLUMN leads.journey_health_status IS 'Health status of client journey (excellent, good, at_risk, critical, stalled)';
COMMENT ON COLUMN leads.journey_start_date IS 'When the client journey began (post-qualification)';
COMMENT ON COLUMN leads.milestone_completion_rate IS 'Percentage of journey milestones completed (0-100)';
COMMENT ON COLUMN leads.source_attribution_data IS 'JSON data for multi-touch attribution analysis';
COMMENT ON COLUMN leads.attribution_confidence IS 'Confidence level in source attribution (0-1)';
COMMENT ON COLUMN leads.multi_touch_attribution IS 'Multi-touch attribution touchpoint data';
COMMENT ON COLUMN leads.ai_insights_enabled IS 'Whether AI insights and recommendations are enabled';
COMMENT ON COLUMN leads.last_ai_analysis IS 'When AI analysis was last performed';
COMMENT ON COLUMN leads.ai_recommendations IS 'Current AI recommendations and insights';
COMMENT ON COLUMN leads.automation_triggers IS 'Active automation triggers and rules';
COMMENT ON COLUMN leads.priority_score IS 'Overall priority score for lead handling (0-100)';
COMMENT ON COLUMN leads.optimization_flags IS 'Optimization flags and settings';
COMMENT ON COLUMN leads.last_optimization_check IS 'When optimization analysis was last performed';
COMMENT ON COLUMN leads.cross_track_context IS 'Shared context data between Track A and Track B services';
COMMENT ON COLUMN leads.handoff_metadata IS 'Metadata for lead-to-client journey handoff';
COMMENT ON COLUMN leads.experience_personalization IS 'Client experience personalization settings and preferences';