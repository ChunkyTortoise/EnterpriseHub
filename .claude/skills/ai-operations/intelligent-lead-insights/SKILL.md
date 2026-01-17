# Intelligent Lead Insights

AI-powered lead behavior analysis with conversion predictions and buying signal detection.

## Description

Analyze lead interactions to predict conversion probability, detect buying signals, identify churn risk, and recommend optimal follow-up timing. This skill integrates with existing lead intelligence and scoring services to provide comprehensive behavioral analysis.

## Triggers

- "analyze lead behavior"
- "predict conversion probability"
- "detect buying signals"
- "identify churn risk"
- "optimal follow-up timing"
- "lead behavior analysis"
- "conversion prediction"

## Model Configuration

- **Model**: sonnet (balanced quality/cost)
- **Thinking**: enabled for complex analysis
- **Temperature**: 0.3 (consistent analytical output)

## Workflow

### Phase 1: Gather Lead Data
```
1. Fetch conversation history from GHL or memory service
2. Retrieve lead context and extracted preferences
3. Load behavioral timeline (page views, email engagement, response patterns)
4. Pull scoring history from enhanced lead scorer
```

### Phase 2: Analyze Behavioral Patterns
```
1. Run conversation pattern analysis
   - Message frequency and response times
   - Question types and depth of engagement
   - Emotional progression tracking

2. Extract buying signals
   - Budget/timeline discussions
   - Property-specific questions
   - Urgency indicators
   - Commitment language patterns

3. Identify risk factors
   - Declining engagement
   - Objection patterns
   - Competitive mentions
   - Ghosting indicators
```

### Phase 3: Calculate Conversion Probability
```
1. Weight behavioral factors using ML model
2. Apply Jorge's question-count methodology
3. Combine with dynamic market weights
4. Generate confidence intervals
```

### Phase 4: Generate Insights
```
1. Synthesize buying signal strength (0-100)
2. Calculate churn risk score (0-100)
3. Determine optimal contact timing
4. Generate strategic recommendations
```

### Phase 5: Recommend Actions
```
1. Prioritize next best action
2. Generate personalized follow-up script
3. Schedule optimal outreach window
4. Flag urgent interventions
```

## Scripts (Zero-Context Execution)

### scripts/analyze-conversations.py
Analyzes conversation patterns without loading full history into context.
```bash
python scripts/analyze-conversations.py --lead-id <lead_id> --output json
```

### scripts/calculate-conversion-score.py
Calculates conversion probability using ML model.
```bash
python scripts/calculate-conversion-score.py --lead-id <lead_id> --include-reasoning
```

### scripts/detect-buying-signals.py
Extracts buying signals from conversation history.
```bash
python scripts/detect-buying-signals.py --lead-id <lead_id> --threshold 0.6
```

### scripts/churn-risk-analysis.py
Identifies churn risk indicators and generates intervention recommendations.
```bash
python scripts/churn-risk-analysis.py --lead-id <lead_id> --days 14
```

## References

- @reference/buying-signals.md - Comprehensive buying signal patterns
- @reference/conversion-models.md - ML model documentation and weights
- @reference/churn-indicators.md - Risk factor identification guide
- @reference/follow-up-timing.md - Optimal contact timing research

## Integration Points

### Primary Services
```python
from ghl_real_estate_ai.services.enhanced_lead_intelligence import EnhancedLeadIntelligence
from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import ClaudeEnhancedLeadScorer
from ghl_real_estate_ai.services.claude_conversation_intelligence import ConversationIntelligenceEngine
```

### Data Sources
- **Conversation History**: GHL API via `ghl_conversation_bridge.py`
- **Behavioral Data**: `memory_service.py` for interaction history
- **Scoring Data**: `predictive_lead_scorer.py` for ML predictions

### Output Destinations
- **GHL Contact Notes**: Update with insights
- **Dashboard Display**: Real-time intelligence panels
- **Automation Triggers**: Hot lead fast-lane routing

## Example Usage

### Analyze Single Lead
```python
from ghl_real_estate_ai.services.enhanced_lead_intelligence import get_enhanced_lead_intelligence

intelligence = get_enhanced_lead_intelligence()

# Get comprehensive analysis
result = await intelligence.get_comprehensive_lead_analysis(
    lead_name="Sarah Chen",
    lead_context={
        "lead_id": "lead_12345",
        "conversations": [...],
        "extracted_preferences": {
            "budget": 750000,
            "location": "Teravista",
            "bedrooms": 4,
            "timeline": "90_days"
        }
    }
)

# Access insights
print(f"Conversion Probability: {result.success_probability}%")
print(f"Classification: {result.classification}")
print(f"Risk Factors: {result.risk_factors}")
print(f"Next Best Action: {result.next_best_action}")
```

### Batch Analysis for Hot Lead Detection
```python
# Identify hot leads requiring immediate attention
hot_leads = []
for lead in active_leads:
    analysis = await intelligence.get_comprehensive_lead_analysis(
        lead_name=lead["name"],
        lead_context=lead["context"]
    )
    if analysis.classification == "hot" and analysis.success_probability > 70:
        hot_leads.append({
            "lead": lead,
            "analysis": analysis,
            "priority": "immediate"
        })

# Route to fast-lane
for hot_lead in hot_leads:
    await fast_lane_router.route_hot_lead(hot_lead)
```

## Output Schema

```json
{
  "lead_id": "string",
  "analysis_timestamp": "ISO8601",
  "conversion_probability": {
    "score": 0.0-100.0,
    "confidence": 0.0-1.0,
    "trend": "increasing|stable|declining"
  },
  "buying_signals": {
    "strength": 0.0-100.0,
    "signals_detected": ["budget_discussed", "timeline_urgent", ...],
    "commitment_indicators": [...]
  },
  "churn_risk": {
    "score": 0.0-100.0,
    "indicators": ["declining_engagement", "long_gap", ...],
    "intervention_urgency": "low|medium|high|critical"
  },
  "behavioral_insights": {
    "engagement_pattern": "string",
    "communication_style": "string",
    "decision_timeline": "string"
  },
  "recommendations": {
    "next_best_action": "string",
    "optimal_contact_time": "ISO8601",
    "follow_up_script": "string",
    "priority": "low|medium|high|urgent"
  }
}
```

## Success Metrics

- **Lead Qualification Speed**: 75% faster than manual analysis
- **Conversion Prediction Accuracy**: Target >80%
- **Churn Prevention Rate**: 30% reduction in lead loss
- **Agent Time Saved**: 2+ hours per day on lead prioritization

## Best Practices

1. **Always verify data freshness** - Check conversation recency before analysis
2. **Use caching** - Leverage 5-minute analysis cache for repeated queries
3. **Combine signals** - Don't rely on single indicators; use holistic view
4. **Track accuracy** - Monitor prediction accuracy for model improvement
5. **Human-in-loop** - Flag uncertain classifications for agent review

## Error Handling

```python
# Graceful degradation pattern
try:
    analysis = await intelligence.get_comprehensive_lead_analysis(...)
except ServiceUnavailableError:
    # Fallback to basic scoring
    analysis = basic_scorer.score_lead(lead_context)
except InsufficientDataError:
    # Request more information
    return {"status": "needs_more_data", "missing": ["conversation_history"]}
```

## Version History

- **1.0.0** (2026-01-16): Initial implementation
  - Conversation pattern analysis
  - Buying signal detection
  - Churn risk identification
  - Conversion probability prediction
