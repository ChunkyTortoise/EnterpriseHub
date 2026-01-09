# 🎯 Dynamic Scoring Weights System Guide

## Overview

The Dynamic Scoring Weights system is an advanced lead scoring solution that automatically adapts to different lead segments, market conditions, and performance data. It provides intelligent weight optimization through A/B testing and machine learning.

## Key Features

### 🎭 Segment-Adaptive Weights
- **Automatic Segment Detection**: First-time buyers, investors, luxury, sellers
- **Tailored Scoring**: Each segment uses optimized weight profiles
- **Behavioral Adaptation**: Weights adjust based on conversion patterns

### 🌡️ Market Condition Adjustments
- **Real-time Market Data**: Inventory levels, price trends, seasonality
- **Contextual Weighting**: Weights adapt to sellers/buyers markets
- **Geographic Awareness**: Location-specific adjustments

### 🧪 A/B Testing Framework
- **Weight Optimization**: Test different scoring approaches
- **Statistical Rigor**: Proper sample sizes and significance testing
- **Automatic Promotion**: Best-performing variants can auto-promote

### ⚡ Performance Optimization
- **Continuous Learning**: Weights improve based on conversion outcomes
- **Feature Importance**: Automatic detection of most predictive factors
- **Confidence Scoring**: Higher confidence as more data is collected

## Quick Start

### Basic Usage

```python
from ghl_real_estate_ai.services.enhanced_lead_scorer import EnhancedLeadScorer, ScoringMode

# Initialize enhanced scorer
scorer = EnhancedLeadScorer()

# Score a lead using all systems
result = await scorer.score_lead(
    lead_id="lead_123",
    context={
        'extracted_preferences': {
            'budget': '$750,000',
            'location': 'Austin, TX',
            'timeline': 'next 2 months',
            'bedrooms': 3,
            'financing': 'pre-approved'
        },
        'conversation_history': [
            {'content': 'Looking for a 3-bedroom house'},
            {'content': 'Budget around $750k'}
        ]
    },
    tenant_id="your_tenant_id",
    mode=ScoringMode.HYBRID  # Uses all scoring methods
)

print(f"Score: {result.final_score}/100")
print(f"Classification: {result.classification}")
print(f"Segment: {result.segment}")
print(f"Confidence: {result.confidence:.1%}")
```

### Scoring Modes

#### 1. Jorge Original (Backwards Compatible)
```python
# Question-count scoring (0-7 questions)
result = await scorer.score_lead(lead_id, context, mode=ScoringMode.JORGE_ORIGINAL)
```

#### 2. ML Enhanced
```python
# Combines question scoring with ML predictions
result = await scorer.score_lead(lead_id, context, mode=ScoringMode.ML_ENHANCED)
```

#### 3. Dynamic Adaptive
```python
# Full dynamic system with market adjustments
result = await scorer.score_lead(lead_id, context, mode=ScoringMode.DYNAMIC_ADAPTIVE)
```

#### 4. Hybrid (Recommended)
```python
# Intelligently combines all methods
result = await scorer.score_lead(lead_id, context, mode=ScoringMode.HYBRID)
```

## Advanced Configuration

### Environment Setup

```python
from ghl_real_estate_ai.services.scoring_config import ScoringConfigManager, ScoringEnvironment

# Production configuration
config = ScoringConfigManager(ScoringEnvironment.PRODUCTION)

# Enable/disable features
config.update_feature_flag("ml_scoring", True)
config.update_feature_flag("ab_testing", False)

# Adjust performance settings
config.update_performance_setting("max_scoring_time_ms", 200)
```

### Tenant-Specific Configuration

```python
# Create tenant-specific overrides
tenant_config = config.create_tenant_config(
    tenant_id="luxury_realty",
    overrides={
        "tier_thresholds": {"hot": 80, "warm": 65},
        "segment_weights.luxury": {
            "communication_quality": 0.30,
            "property_matches": 0.25,
            "engagement_score": 0.15
        }
    }
)
```

## A/B Testing

### Creating Tests

```python
from ghl_real_estate_ai.services.dynamic_scoring_weights import ScoringWeights, LeadSegment

orchestrator = DynamicScoringOrchestrator()

# Define test variants
variant_a = ScoringWeights(engagement_score=0.30, response_time=0.15, ...)
variant_b = ScoringWeights(engagement_score=0.15, response_time=0.25, ...)

# Create test
test_id = await orchestrator.create_weight_optimization_test(
    tenant_id="test_tenant",
    test_name="Engagement vs Speed",
    segment=LeadSegment.FIRST_TIME_BUYER,
    variant_weights=[variant_a, variant_b],
    duration_days=30
)
```

### Recording Outcomes

```python
# Record conversion for optimization
await scorer.record_conversion(
    lead_id="lead_123",
    converted=True,
    conversion_value=15000.0,
    context=original_context
)
```

## Lead Segments

### Automatic Detection
The system automatically detects lead segments based on:

- **Budget Range**: Luxury vs standard pricing
- **Intent Keywords**: "investment", "first time", "selling"
- **Communication Patterns**: Analytical vs emotional language
- **Timeline Urgency**: Immediate vs exploratory

### Segment Characteristics

#### First-Time Buyer
- Higher engagement weight (need education)
- Lower timeline urgency (take time deciding)
- Focus on location and school districts

#### Investor
- Higher response time weight (speed matters)
- Higher budget match weight (ROI focused)
- Lower communication quality weight (brief, analytical)

#### Luxury
- Higher communication quality weight (relationship focused)
- Higher property match weight (specific requirements)
- Lower timeline urgency (flexible timeline)

#### Seller
- Higher timeline urgency weight (when they need to move)
- Lower property match weight (not browsing properties)
- Focus on motivation and market conditions

## Market Conditions

### Automatic Detection
- **Sellers Market**: Low inventory, high prices, fast sales
- **Buyers Market**: High inventory, price drops, slow sales
- **Balanced**: Stable conditions
- **Seasonal**: Winter slowdown, spring/summer peak
- **Volatile**: Rapid changes, uncertain conditions

### Weight Adjustments
```python
# Market conditions automatically adjust weights
# Example: Sellers market for investors
{
    "response_time": 0.4,      # Speed is everything
    "timeline_urgency": 0.2,   # Act fast or lose out
    "budget_match": 0.15       # Less room for negotiation
}
```

## Performance Monitoring

### Performance Statistics
```python
stats = scorer.get_performance_stats()
print(f"Total Scores: {stats['total_scores']}")
print(f"Average Response Time: {stats['avg_response_time']}ms")
print(f"Fallback Rate: {stats['fallback_rate']:.1%}")
```

### Performance Dashboard
```python
dashboard = await orchestrator.get_performance_dashboard(tenant_id)
print(f"Market Condition: {dashboard['market_conditions']['condition']}")
print(f"Conversion Rates: {dashboard['segment_performance']}")
```

## Error Handling & Fallbacks

### Circuit Breakers
The system includes automatic circuit breakers that detect failures and gracefully degrade:

1. **Dynamic Adaptive** fails → falls back to **ML Enhanced**
2. **ML Enhanced** fails → falls back to **Jorge Original**
3. **Jorge Original** fails → falls back to **Static Heuristics**

### Monitoring Fallbacks
```python
# Check if fallbacks are being used
result = await scorer.score_lead(...)
if result.fallback_used:
    print(f"Fallback used: {result.scoring_mode}")
```

## Integration Examples

### Replace Existing Scorer
```python
# OLD: Direct LeadScorer usage
old_scorer = LeadScorer()
score = old_scorer.calculate(context)

# NEW: Enhanced scorer (backwards compatible)
enhanced_scorer = EnhancedLeadScorer()
score = enhanced_scorer.calculate(context)  # Same API
```

### Advanced Integration
```python
# Use enhanced features
result = await enhanced_scorer.score_with_explanation(
    lead_id="lead_123",
    context=context,
    tenant_id="tenant_123"
)

# Rich result with explanations
print(f"Score: {result['final_score']}")
print(f"Reasoning: {result['reasoning']}")
print(f"Market Impact: {result['market_condition']}")
print(f"Segment: {result['segment']}")
```

### Batch Processing
```python
# Score multiple leads efficiently
leads = [
    {'id': 'lead_1', 'context': context1},
    {'id': 'lead_2', 'context': context2}
]

results = await scorer.batch_score_leads(leads, tenant_id="batch_tenant")
for result in results:
    print(f"{result.lead_id}: {result.final_score}")
```

## Best Practices

### 1. Choose the Right Mode
- **Production**: Use `HYBRID` mode for best results
- **Demo**: Use `JORGE_ORIGINAL` for simplicity
- **Testing**: Use `DYNAMIC_ADAPTIVE` to test new features

### 2. Monitor Performance
- Track response times and fallback rates
- Review segment performance regularly
- Adjust configurations based on conversion data

### 3. Configure for Your Market
- Set appropriate tier thresholds for your market
- Consider market-specific segment weights
- Enable features gradually in production

### 4. Record Outcomes
- Always record conversion outcomes for optimization
- Include conversion values for ROI-based optimization
- Use realistic test durations (30+ days)

### 5. A/B Testing
- Start with small traffic splits (10-20%)
- Ensure minimum sample sizes (100+ leads per variant)
- Test one variable at a time for clear results

## Troubleshooting

### Common Issues

#### Slow Response Times
```python
# Check performance settings
config.update_performance_setting("max_scoring_time_ms", 200)
config.update_performance_setting("redis_timeout_ms", 50)
```

#### Inconsistent Scores
```python
# Check if circuit breakers are triggering
stats = scorer.get_performance_stats()
print(stats['circuit_breakers'])
```

#### Configuration Errors
```python
# Validate configuration
issues = config.validate_configuration()
for issue in issues:
    print(f"Issue: {issue}")
```

### Debug Mode
```python
# Enable detailed logging for debugging
import logging
logging.getLogger('dynamic_scoring').setLevel(logging.DEBUG)
```

## Environment Variables

```bash
# Core settings
SCORING_ENVIRONMENT=production
REDIS_URL=redis://localhost:6379

# Performance tuning
SCORING_MAX_TIME_MS=300
SCORING_CACHE_TTL=300

# Feature flags
ENABLE_DYNAMIC_WEIGHTS=true
ENABLE_ML_SCORING=true
ENABLE_AB_TESTING=true

# Scoring mode weights
JORGE_WEIGHT=0.4
ML_WEIGHT=0.3
DYNAMIC_WEIGHT=0.3
```

## Migration Guide

### From Basic LeadScorer

1. **Install Dependencies**
```bash
pip install redis>=5.0.0 pydantic>=2.0.0
```

2. **Update Imports**
```python
# OLD
from ghl_real_estate_ai.services.lead_scorer import LeadScorer

# NEW
from ghl_real_estate_ai.services.enhanced_lead_scorer import EnhancedLeadScorer
```

3. **Update Usage** (Optional)
```python
# Keep existing API
scorer = EnhancedLeadScorer()
score = scorer.calculate(context)  # Works exactly as before

# OR use enhanced API
result = await scorer.score_lead(lead_id, context)
```

### Gradual Rollout

1. **Start with Jorge Mode**: Verify backwards compatibility
2. **Add ML Enhanced**: Test improved accuracy
3. **Enable Dynamic**: Test market adaptations
4. **Full Hybrid**: Use all features together

## Support

### Documentation
- [API Reference](./API_REFERENCE.md)
- [Configuration Guide](./CONFIGURATION.md)
- [Performance Tuning](./PERFORMANCE.md)

### Testing
```bash
# Run integration tests
python -m pytest ghl_real_estate_ai/tests/test_dynamic_scoring_integration.py -v
```

### Questions?
For technical support or questions about the Dynamic Scoring Weights system, please:

1. Check the troubleshooting section above
2. Review the integration test examples
3. Examine the configuration validation output
4. Contact the development team with specific error messages

---

**🎯 Ready to revolutionize your lead scoring with intelligent, adaptive weights that automatically optimize for maximum conversion rates!**