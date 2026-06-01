# Conversation Optimization

Real-time conversation analytics and coaching for sales agents with AI-powered response suggestions.

## Description

Analyze agent-lead conversations in real-time to improve conversion rates through response quality analysis, objection handling suggestions, missed opportunity detection, and personalized agent coaching. This skill integrates with the conversation intelligence engine to provide actionable insights.

## Triggers

- "analyze conversation"
- "improve response quality"
- "detect missed opportunities"
- "coach sales agent"
- "conversation coaching"
- "optimize conversation"
- "agent performance"

## Model Configuration

- **Model**: sonnet (real-time performance)
- **Thinking**: enabled for coaching analysis
- **Temperature**: 0.4 (balanced creativity/consistency)

## Workflow

### Phase 1: Real-Time Analysis
```
1. Stream conversation messages as they arrive
2. Analyze response timing and quality
3. Detect intent changes and emotional shifts
4. Track objection patterns in real-time
```

### Phase 2: Response Quality Analysis
```
1. Evaluate agent responses against best practices
   - Tone and empathy matching
   - Information completeness
   - Question advancement
   - Call-to-action clarity

2. Score response effectiveness (0-100)
   - Relevance to lead's question
   - Persuasiveness
   - Personalization level
   - Closing momentum
```

### Phase 3: Opportunity Detection
```
1. Identify missed buying signals
   - Unaddressed urgency indicators
   - Overlooked budget discussions
   - Ignored timeline mentions

2. Flag conversation gaps
   - Missing qualification questions
   - Skipped objection resolution
   - Incomplete property matching

3. Surface expansion opportunities
   - Upsell moments
   - Referral requests
   - Additional service offers
```

### Phase 4: Objection Handling
```
1. Detect objection type
   - Price/budget concerns
   - Timeline hesitation
   - Feature mismatch
   - Competition comparison
   - Decision authority

2. Provide resolution strategies
   - Proven response templates
   - Reframing techniques
   - Value reinforcement scripts
   - Urgency creation methods
```

### Phase 5: Generate Coaching
```
1. Personalized improvement suggestions
2. Response alternative generation
3. Best practice recommendations
4. Performance trend analysis
```

## Scripts (Zero-Context Execution)

### scripts/analyze-transcript.py
Analyzes full conversation transcript for quality metrics.
```bash
python scripts/analyze-transcript.py --conversation-id <id> --output json
```

### scripts/generate-coaching.py
Generates personalized coaching recommendations.
```bash
python scripts/generate-coaching.py --agent-id <id> --conversations 10
```

### scripts/detect-objections.py
Detects and classifies objections with resolution strategies.
```bash
python scripts/detect-objections.py --message "<message>" --context <context.json>
```

### scripts/suggest-response.py
Generates optimized response suggestions.
```bash
python scripts/suggest-response.py --conversation <conv.json> --style professional
```

## References

- @reference/response-quality-rubric.md - Scoring criteria for responses
- @reference/objection-handling.md - Objection types and resolution strategies
- @reference/coaching-frameworks.md - Agent development methodologies
- @reference/best-practice-responses.md - Template library

## Integration Points

### Primary Services
```python
from ghl_real_estate_ai.services.claude_conversation_intelligence import ConversationIntelligenceEngine
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeOrchestrator
from ghl_real_estate_ai.services.enhanced_conversation_intelligence import EnhancedConversationIntelligence
```

### Real-Time Processing
- **WebSocket Integration**: Live message streaming
- **Redis Pub/Sub**: Event-driven analysis triggers
- **GHL Webhooks**: Conversation event notifications

### Output Destinations
- **Agent Dashboard**: Real-time coaching overlay
- **GHL Notes**: Coaching summaries attached to contacts
- **Training System**: Aggregated performance data

## Example Usage

### Real-Time Coaching
```python
from ghl_real_estate_ai.services.claude_conversation_intelligence import get_conversation_intelligence

engine = get_conversation_intelligence()

# Analyze latest message exchange
analysis = await engine.analyze_conversation_realtime(
    messages=[
        {"role": "lead", "content": "The price seems a bit high..."},
        {"role": "agent", "content": "I understand your concern."}
    ],
    lead_context={"budget": 700000, "timeline": "60_days"}
)

# Get coaching suggestions
if analysis.objection_type == "budget":
    coaching = await engine.generate_response_suggestions(
        context={"objection": "price", "lead_profile": lead_data},
        conversation_analysis=analysis
    )

    print(f"Suggested responses: {coaching}")
```

### Conversation Quality Report
```python
# Generate quality report for conversation
report = await engine.predict_conversation_outcome(
    history=conversation_messages,
    lead_context=lead_profile
)

print(f"Conversation Health: {report['conversation_health']}")
print(f"Engagement Trend: {report['engagement_trend']}")
print(f"Optimization Recommendations: {report['optimization_recommendations']}")
```

### Agent Performance Analysis
```python
# Analyze agent performance over multiple conversations
from ghl_real_estate_ai.services.conversation_optimization import AgentCoach

coach = AgentCoach()

performance = await coach.analyze_agent_performance(
    agent_id="agent_123",
    conversation_ids=recent_conversations,
    time_period="7_days"
)

print(f"Response Quality Score: {performance.avg_response_quality}")
print(f"Objection Resolution Rate: {performance.objection_resolution_rate}")
print(f"Conversion Impact: {performance.conversion_attribution}")
print(f"Top Improvement Areas: {performance.improvement_priorities}")
```

## Output Schema

### Response Analysis
```json
{
  "conversation_id": "string",
  "analysis_type": "response_quality",
  "quality_score": 0.0-100.0,
  "quality_factors": {
    "relevance": 0.0-1.0,
    "empathy": 0.0-1.0,
    "completeness": 0.0-1.0,
    "persuasiveness": 0.0-1.0,
    "personalization": 0.0-1.0
  },
  "missed_opportunities": [
    {
      "type": "string",
      "context": "string",
      "suggested_action": "string"
    }
  ],
  "improvement_suggestions": ["string"],
  "timestamp": "ISO8601"
}
```

### Objection Analysis
```json
{
  "objection_detected": true,
  "objection_type": "budget|timeline|features|competition|authority",
  "severity": "low|medium|high",
  "resolution_status": "unaddressed|partial|resolved",
  "suggested_responses": [
    {
      "response": "string",
      "strategy": "string",
      "confidence": 0.0-1.0
    }
  ],
  "handling_tips": ["string"]
}
```

### Coaching Report
```json
{
  "agent_id": "string",
  "period": "string",
  "performance_summary": {
    "conversations_analyzed": 0,
    "avg_quality_score": 0.0-100.0,
    "improvement_trend": "string"
  },
  "strengths": ["string"],
  "improvement_areas": [
    {
      "area": "string",
      "priority": "high|medium|low",
      "specific_feedback": "string",
      "training_resources": ["string"]
    }
  ],
  "recommended_actions": ["string"],
  "benchmark_comparison": {
    "vs_team_avg": "+/-X%",
    "vs_top_performer": "+/-X%"
  }
}
```

## Success Metrics

- **Conversion Rate Improvement**: 60% increase in qualified leads
- **Response Time Optimization**: 25% faster agent responses
- **Objection Resolution**: 45% improvement in successful handling
- **Agent Skill Development**: Measurable coaching impact

## Response Quality Rubric

### Scoring Criteria (0-100)

#### Relevance (25 points)
- **25**: Directly addresses lead's question with specific information
- **20**: Addresses question with minor tangents
- **15**: Partially addresses question
- **10**: Related but doesn't answer directly
- **5**: Off-topic response

#### Empathy (20 points)
- **20**: Acknowledges emotions, validates concerns, shows understanding
- **15**: Shows understanding but limited emotional connection
- **10**: Neutral tone, factual only
- **5**: Cold or dismissive tone
- **0**: Antagonistic or condescending

#### Completeness (20 points)
- **20**: Provides all necessary information, anticipates follow-ups
- **15**: Answers main question, minor gaps
- **10**: Basic answer, requires follow-up
- **5**: Incomplete, leaves significant questions
- **0**: Fails to provide meaningful information

#### Persuasiveness (20 points)
- **20**: Builds value, addresses concerns proactively, strong CTA
- **15**: Good value proposition, decent CTA
- **10**: Some value communication, weak CTA
- **5**: Minimal persuasion attempt
- **0**: No persuasive elements

#### Personalization (15 points)
- **15**: References specific lead details, customized approach
- **10**: Some personalization, generic elements
- **5**: Mostly template response
- **0**: Fully generic response

## Best Practices

1. **Real-time feedback** - Deliver coaching while conversation is active
2. **Non-intrusive suggestions** - Provide options without overwhelming agent
3. **Context preservation** - Consider full conversation history
4. **Positive reinforcement** - Highlight strengths alongside improvements
5. **Actionable specifics** - Give concrete examples, not vague advice

## Error Handling

```python
# Graceful degradation for real-time analysis
try:
    analysis = await engine.analyze_conversation_realtime(messages)
    coaching = await engine.generate_response_suggestions(context, analysis)
except AnalysisTimeoutError:
    # Provide cached/template suggestions
    coaching = get_template_suggestions(objection_type)
except InsufficientContextError:
    # Request more information
    return {"status": "need_more_context", "missing": ["lead_profile"]}
```

## Version History

- **1.0.0** (2026-01-16): Initial implementation
  - Real-time response quality analysis
  - Objection detection and handling
  - Missed opportunity detection
  - Agent coaching recommendations
