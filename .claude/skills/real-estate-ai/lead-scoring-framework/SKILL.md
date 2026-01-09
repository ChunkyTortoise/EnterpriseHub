# Lead Scoring Framework

## Description
A comprehensive real estate lead scoring system that combines Jorge's proven question-count methodology with machine learning predictions and dynamic adaptive weights. This framework unifies multiple scoring approaches with intelligent fallback mechanisms and A/B testing capabilities.

## Key Features
- **Jorge's Question-Count System**: Production-tested 7-question qualification with Hot/Warm/Cold classification
- **ML-Enhanced Scoring**: Predictive models trained on behavioral patterns and conversion data
- **Dynamic Weight Adaptation**: Real-time weight adjustment based on market conditions and performance
- **Hybrid Orchestration**: Intelligent combination of all scoring methods with fallback hierarchy
- **A/B Testing Framework**: Compare different scoring approaches and optimize for conversion
- **Circuit Breaker Pattern**: Graceful degradation when components fail
- **Performance Monitoring**: Track accuracy, response times, and business impact

## When to Use This Skill
- Implementing multi-faceted lead qualification systems
- Upgrading from simple scoring to ML-enhanced approaches
- Building A/B testing frameworks for lead scoring optimization
- Creating robust production systems with fallback mechanisms
- Integrating multiple data sources for comprehensive lead analysis
- Building scalable lead scoring for high-volume real estate operations

## Core Components

### 1. Jorge's Original Framework (Proven Foundation)
- **7 Qualification Questions**: Budget, location, bedrooms, timeline, preapproval, motivation, seller condition
- **Simple Classification**: Hot (3+ answers), Warm (2 answers), Cold (≤1 answer)
- **Production Results**: 45% conversion for Hot leads, 22% for Warm, 8% for Cold
- **Conversation Integration**: Natural question progression in SMS/chat workflows

### 2. Machine Learning Enhancement
- **Behavioral Analysis**: Page views, email engagement, response patterns
- **Feature Engineering**: Communication quality, response timing, engagement depth
- **Predictive Scoring**: 0-100 score with confidence intervals
- **Model Updates**: Continuous learning from conversion outcomes

### 3. Dynamic Weight System
- **Market Adaptation**: Adjust weights based on seasonal trends, inventory levels
- **Segment-Specific**: Different weights for first-time buyers, investors, luxury segment
- **Performance Feedback**: Optimize weights based on actual conversion data
- **Real-Time Updates**: Redis-backed weight caching for instant updates

### 4. Unified Orchestration
- **Scoring Mode Selection**: Choose between Jorge-only, ML-enhanced, or Hybrid approaches
- **Intelligent Fallback**: Graceful degradation when AI services are unavailable
- **Circuit Breaker**: Prevent cascade failures in production systems
- **Performance Tracking**: Monitor response times, accuracy, fallback rates

## Scoring Methodologies

### Jorge's Question-Count Algorithm
```python
def calculate_jorge_score(answers: Dict[str, Any]) -> Tuple[int, str]:
    """
    Simple, proven approach based on meaningful answer count

    Classification:
    - Hot: 3+ meaningful answers (ready for agent handoff)
    - Warm: 2 meaningful answers (continue nurturing)
    - Cold: ≤1 meaningful answers (needs more engagement)
    """
    meaningful_count = count_meaningful_answers(answers)

    if meaningful_count >= 3:
        return meaningful_count, "hot"
    elif meaningful_count == 2:
        return meaningful_count, "warm"
    else:
        return meaningful_count, "cold"
```

### ML-Enhanced Prediction
```python
def calculate_ml_score(lead_data: Dict) -> MLScoringResult:
    """
    Machine learning model considering:
    - Communication patterns
    - Behavioral engagement
    - Response timing and quality
    - Source and traffic patterns
    - Market context

    Returns 0-100 score with feature explanations
    """
    features = extract_behavioral_features(lead_data)
    score = ml_model.predict(features)
    explanations = model.explain_prediction(features)

    return MLScoringResult(
        score=score,
        confidence=calculate_confidence(features),
        features=explanations,
        model_version=model.version
    )
```

### Dynamic Weight Adaptation
```python
def calculate_dynamic_score(
    jorge_score: int,
    ml_score: float,
    market_conditions: Dict,
    lead_segment: str
) -> DynamicScoringResult:
    """
    Intelligently blend scoring methods based on:
    - Current market conditions
    - Lead segment characteristics
    - Historical performance data
    - A/B testing assignments
    """
    weights = get_adaptive_weights(market_conditions, lead_segment)

    final_score = (
        jorge_score * weights.jorge_weight +
        ml_score * weights.ml_weight +
        market_adjustments * weights.market_weight
    )

    return DynamicScoringResult(
        score=final_score,
        weights_used=weights,
        market_context=market_conditions
    )
```

## Implementation Architecture

### Unified Scoring Service
```python
class EnhancedLeadScorer:
    """
    Orchestrates all scoring methods with intelligent fallbacks

    Modes:
    - JORGE_ORIGINAL: Question-count only
    - ML_ENHANCED: ML + questions combined
    - DYNAMIC_ADAPTIVE: Full dynamic system
    - HYBRID: All methods with intelligent blending
    """

    async def score_lead(
        self,
        lead_id: str,
        context: Dict[str, Any],
        mode: ScoringMode = ScoringMode.HYBRID
    ) -> EnhancedScoringResult:
        """
        Main scoring entry point with fallback hierarchy:
        1. Try requested mode
        2. Fall back to simpler modes on failure
        3. Track performance and failures
        4. Return comprehensive results
        """
```

### Fallback Management
```python
class ScoringFallbackManager:
    """
    Manages graceful degradation with circuit breaker pattern

    Hierarchy:
    1. Dynamic Adaptive (full AI system)
    2. ML Enhanced (ML + Jorge)
    3. Jorge Original (question count only)
    4. Static Fallback (basic heuristics)
    """

    def is_circuit_open(self, component: str) -> bool:
        """Circuit breaker logic to prevent cascade failures"""

    def record_failure(self, component: str):
        """Track failures for circuit breaker decisions"""
```

### A/B Testing Framework
```python
class ScoringABTestManager:
    """
    A/B test different scoring approaches

    Features:
    - Traffic splitting by lead characteristics
    - Performance tracking by test group
    - Statistical significance calculation
    - Automated winner promotion
    """

    def assign_test_group(self, lead_id: str) -> str:
        """Assign lead to test group based on hashing"""

    def track_conversion(self, lead_id: str, converted: bool):
        """Track conversion outcomes by test group"""
```

## Data Sources and Integration

### Lead Context Data
- **Conversation History**: Messages, response patterns, engagement timing
- **Extracted Preferences**: Budget, location, timeline, property requirements
- **Behavioral Metrics**: Page views, email opens, document downloads
- **Source Information**: Traffic source, campaign attribution, referrer data

### External Data Integration
- **Market Conditions**: Inventory levels, seasonal trends, interest rates
- **Property Data**: Listings viewed, favorites, showing requests
- **CRM Integration**: Contact history, agent notes, previous interactions
- **Communication Platform**: SMS engagement, email responses, call logs

### Performance Metrics
- **Accuracy Metrics**: Prediction accuracy vs. actual conversions
- **Speed Metrics**: Response times, throughput, system availability
- **Business Metrics**: Lead conversion rates, revenue attribution
- **Quality Metrics**: Agent feedback, client satisfaction scores

## Configuration and Customization

### Scoring Weights Configuration
```python
SCORING_WEIGHTS = {
    "jorge_baseline": 0.4,      # Base question-count weight
    "ml_enhancement": 0.35,     # ML model contribution
    "market_timing": 0.15,      # Market condition adjustments
    "behavioral_boost": 0.10    # Engagement pattern bonus
}

SEGMENT_MODIFIERS = {
    "first_time_buyer": {"jorge": 1.2, "ml": 0.8},     # Trust simple approach
    "investor": {"jorge": 0.8, "ml": 1.3},             # Complex behavior patterns
    "luxury": {"market_timing": 1.5},                   # Market timing crucial
}
```

### Fallback Configuration
```python
FALLBACK_CONFIG = {
    "circuit_breaker_threshold": 3,        # Failures before opening circuit
    "circuit_recovery_time": 300,          # Seconds before retry
    "max_response_time": 5000,             # Max milliseconds before fallback
    "min_confidence_threshold": 0.7        # Min confidence for ML results
}
```

### A/B Testing Setup
```python
AB_TEST_CONFIG = {
    "test_traffic_percentage": 0.2,        # 20% in A/B tests
    "min_sample_size": 100,                # Min conversions for significance
    "significance_threshold": 0.95,        # 95% confidence for winner
    "test_duration_days": 30               # Max test duration
}
```

## Production Deployment Patterns

### Microservice Architecture
```yaml
# Lead Scoring Service
leadscoring-service:
  replicas: 3
  environment:
    - REDIS_URL=redis://redis-cluster:6379
    - ML_MODEL_ENDPOINT=http://ml-service:8000
    - JORGE_FALLBACK=enabled
  health_checks:
    - /health/ready
    - /health/live
```

### Redis Caching Strategy
```python
# Cache frequently accessed data
CACHE_PATTERNS = {
    "lead_scores": "lead:score:{lead_id}",           # TTL: 1 hour
    "market_weights": "weights:market:{date}",        # TTL: 6 hours
    "ml_predictions": "ml:pred:{lead_hash}",          # TTL: 30 minutes
    "conversion_stats": "stats:conv:{segment}:{date}" # TTL: 24 hours
}
```

### Monitoring and Alerting
```python
# Key metrics to monitor
MONITORING_METRICS = {
    "scoring_requests_per_second": "gauge",
    "scoring_response_time_p95": "histogram",
    "fallback_rate_by_component": "counter",
    "conversion_accuracy_by_model": "gauge",
    "circuit_breaker_status": "gauge"
}
```

## Business Impact Measurement

### Lead Qualification Metrics
- **Qualification Accuracy**: How well scores predict actual conversions
- **Agent Efficiency**: Time saved with better-qualified leads
- **Response Time**: Speed of initial lead qualification
- **Handoff Quality**: Agent satisfaction with lead scoring accuracy

### Revenue Attribution
- **Conversion Rate by Score**: Track Hot/Warm/Cold conversion rates
- **Revenue per Lead**: Average revenue attributed to scored leads
- **Time to Close**: Average days from scoring to contract signing
- **Cost per Conversion**: Marketing cost efficiency by lead score

### System Performance
- **Availability**: 99.9% uptime with graceful fallbacks
- **Accuracy**: >85% prediction accuracy for Hot/Warm classification
- **Speed**: <500ms average response time for scoring requests
- **Scalability**: Handle 1000+ concurrent scoring requests

## Integration Examples

### CRM Integration
```python
# Sync scores with CRM systems
async def sync_score_to_crm(lead_id: str, score_result: EnhancedScoringResult):
    """Update CRM with latest lead score and reasoning"""

    crm_data = {
        "lead_score": score_result.final_score,
        "classification": score_result.classification,
        "score_reasoning": score_result.reasoning,
        "next_action": determine_next_action(score_result),
        "agent_notes": generate_agent_notes(score_result)
    }

    await crm_client.update_contact(lead_id, crm_data)
```

### Marketing Automation
```python
# Trigger marketing actions based on scores
async def trigger_marketing_actions(lead_id: str, score: EnhancedScoringResult):
    """Automate follow-up based on lead score"""

    if score.classification == "hot":
        await schedule_immediate_agent_call(lead_id)
    elif score.classification == "warm":
        await enroll_in_nurture_sequence(lead_id, "warm_leads")
    else:
        await add_to_long_term_drip_campaign(lead_id)
```

## Advanced Features

### Predictive Analytics
- **Conversion Probability**: Likelihood of lead converting within 30/60/90 days
- **Revenue Prediction**: Expected revenue value from lead
- **Optimal Contact Timing**: Best times to contact based on behavioral patterns
- **Churn Risk Assessment**: Probability of lead going cold

### Behavioral Insights
- **Engagement Patterns**: Identify high-intent behaviors
- **Communication Preferences**: Email vs. SMS vs. phone preferences
- **Decision Timeline**: Predict how long lead will take to decide
- **Price Sensitivity**: Analyze budget flexibility indicators

### Market Intelligence
- **Seasonal Adjustments**: Adapt scoring for market seasonality
- **Inventory Impact**: Adjust urgency based on available properties
- **Competition Analysis**: Factor in market competition levels
- **Economic Indicators**: Incorporate interest rates, economic trends

---

*This framework represents the evolution from simple lead scoring to comprehensive AI-powered qualification systems. It preserves the simplicity and proven results of Jorge's methodology while adding the sophistication needed for modern real estate operations at scale.*