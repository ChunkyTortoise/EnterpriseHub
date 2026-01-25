# Lead Analysis Skill

## Overview
Advanced lead qualification and analysis using Jorge's GoHighLevel CRM integration.

## Commands

### `/analyze-lead`
Deep lead qualification analysis with scoring and recommendations.

**Usage**: `/analyze-lead [lead_id] [analysis_type]`
**Example**: `/analyze-lead jorge_lead_456 full-qualification`

**Implementation**:
- Queries Jorge's GHL via MCP for lead details
- Analyzes lead behavior and engagement patterns
- Uses Sequential Thinking for qualification logic
- Generates lead score with detailed reasoning
- Stores analysis in PostgreSQL for BI tracking

### `/score-leads`
Batch scoring of multiple leads with ranking.

**Usage**: `/score-leads [pipeline] [criteria]`
**Example**: `/score-leads buyer-pipeline budget-timeline-ready`

**Implementation**:
- Fetches lead batch from Jorge's GHL account
- Applies ML scoring algorithms (28-feature pipeline)
- Ranks leads by conversion probability
- Generates prioritized follow-up list
- Updates lead scores in GHL CRM

### `/qualification-workflow`
Automated lead qualification workflow optimization.

**Usage**: `/qualification-workflow [pipeline_id] [optimization_target]`
**Example**: `/qualification-workflow buyer-pipe conversion-rate`

**Implementation**:
- Analyzes current Jorge pipeline performance
- Identifies bottlenecks and drop-off points
- Uses Sequential Thinking for workflow optimization
- Generates improved qualification flow
- Provides implementation recommendations

### `/lead-insights`
Generate comprehensive lead intelligence reports.

**Usage**: `/lead-insights [timeframe] [segment]`
**Example**: `/lead-insights last-30-days luxury-buyers`

**Implementation**:
- Aggregates lead data from Jorge's GHL
- Analyzes conversion patterns and trends
- Identifies high-value lead characteristics
- Creates actionable insights dashboard
- Exports findings to BI systems

### `/follow-up-strategy`
Personalized follow-up strategy generation.

**Usage**: `/follow-up-strategy [lead_id] [context]`
**Example**: `/follow-up-strategy jorge_lead_789 property-viewing-scheduled`

**Implementation**:
- Retrieves lead history from GHL
- Analyzes previous interactions and responses
- Uses Sequential Thinking for strategy planning
- Generates personalized outreach plan
- Schedules automated follow-ups

## Jorge's GHL Integration

### Account Details
- **Location ID**: `3xt4qayAh35BIDLaUv7P`
- **Realtor**: Jorge Salas (`realtorjorgesalas@gmail.com`)
- **Access Level**: Full CRM permissions
- **Pipelines**: Buyer, Seller, Lead Qualification

### Data Sources
- Contact information and preferences
- Interaction history and engagement
- Pipeline stage and progression
- Custom fields and lead scoring
- Communication logs and responses

### Update Capabilities
- Lead score modifications
- Pipeline stage advancement
- Custom field updates
- Task and follow-up creation
- Notes and interaction logging

## Lead Scoring Algorithm

### Core Factors (28-feature pipeline)
1. **Budget Qualification** (25% weight)
   - Stated budget vs. market reality
   - Pre-approval status
   - Down payment availability

2. **Timeline Urgency** (20% weight)
   - Stated timeline to purchase/sell
   - Current housing situation
   - Market timing awareness

3. **Engagement Level** (20% weight)
   - Response rate to communications
   - Website interaction patterns
   - Property viewing requests

4. **Geographic Focus** (15% weight)
   - Preferred area specificity
   - Realistic area expectations
   - Local market knowledge

5. **Behavioral Indicators** (20% weight)
   - Communication style and tone
   - Question quality and specificity
   - Referral source and quality

### Scoring Output
- **A-Grade (9-10)**: Hot leads ready to transact
- **B-Grade (7-8)**: Warm leads needing nurturing
- **C-Grade (5-6)**: Qualified prospects with longer timeline
- **D-Grade (3-4)**: Requires significant qualification
- **F-Grade (1-2)**: Not qualified or likely unviable

## Performance Tracking

### Metrics
- Lead scoring accuracy vs. actual conversions
- Pipeline velocity improvements
- Qualification time reduction
- Follow-up response rate increases
- Overall conversion rate optimization

### Success Targets
- >85% scoring accuracy correlation
- 30% reduction in qualification time
- 25% increase in follow-up response rates
- 20% improvement in lead-to-appointment conversion

---
**Ready to optimize Jorge's lead qualification empire!**