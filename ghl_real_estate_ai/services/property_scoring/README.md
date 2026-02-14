# Property Scoring Strategy Pattern Implementation

## Overview

This package implements the Strategy Pattern for property scoring algorithms in the GHL Real Estate AI system. It provides a flexible, extensible architecture that supports multiple scoring algorithms while maintaining SOLID principles and enterprise-grade standards.

## Architecture

```
property_scoring/
├── interfaces/           # Strategy Pattern Interfaces
│   ├── property_scorer.py      # Core Strategy Interface
│   └── scoring_context.py      # Data Models & Context
├── strategies/           # Concrete Strategy Implementations
│   ├── basic_property_scorer.py         # Simple rule-based
│   ├── enhanced_property_scorer.py      # Advanced rule-based
│   ├── ml_property_scorer.py            # ML-enhanced
│   └── behavioral_adaptive_scorer.py    # Learning-based
├── context/              # Strategy Context & Factory
│   ├── property_matcher_context.py     # Strategy Context
│   └── scoring_factory.py              # Factory Pattern
├── models/               # Data Models
│   ├── scoring_models.py               # Core Models
│   └── preference_models.py            # Preference Models
└── utils/                # Utilities
    ├── scorer_registry.py             # Registry Pattern
    └── validation.py                  # Input Validation
```

## Key Components

### 1. Strategy Interface (`PropertyScorer`)

The core interface that all scoring algorithms must implement:

```python
from property_scoring.interfaces import PropertyScorer, ScoringResult

class CustomScorer(PropertyScorer):
    def calculate_score(self, property_data, lead_preferences):
        # Implement scoring logic
        return ScoringResult(...)
```

### 2. Concrete Strategies

#### BasicPropertyScorer
- Simple rule-based matching
- Fast performance (< 50ms per property)
- Suitable for high-volume scenarios
- Features: Basic budget/location/feature matching

#### EnhancedPropertyScorer
- Advanced rule-based algorithms
- Moderate performance (50-200ms per property)
- Sophisticated market analysis
- Features: Geographic scoring, market timing, risk assessment

#### MLPropertyScorer
- Machine learning-enhanced scoring
- Performance varies (100-500ms per property)
- Requires training data
- Features: Predictive modeling, feature learning

#### BehavioralAdaptiveScorer
- Learning-based adaptation
- Improves over time with feedback
- Performance: 200-800ms per property
- Features: User feedback integration, personalization

### 3. Strategy Context

The `PropertyMatcherContext` orchestrates strategy usage:

```python
from property_scoring.context import PropertyMatcherContext
from property_scoring.strategies import EnhancedPropertyScorer

# Create context with strategy
context = PropertyMatcherContext()
context.set_strategy(EnhancedPropertyScorer())

# Score properties
result = context.score_property(property_data, lead_preferences)
```

### 4. Factory Pattern

The `ScoringFactory` manages strategy creation and configuration:

```python
from property_scoring.context import ScoringFactory

factory = ScoringFactory()

# Get recommended strategy
strategy_name = factory.recommend_strategy({
    'performance_priority': 'accuracy',
    'complexity_tolerance': 'high'
})

strategy = factory.create_strategy(strategy_name)
```

## Integration with Existing PropertyMatcher

### Migration Steps

1. **Install Strategy System**:
   ```python
   # Add to existing property_matcher_ai.py
   from property_scoring.context import PropertyMatcherContext, ScoringFactory
   ```

2. **Modify generate_property_matches()**:
   ```python
   def generate_property_matches(lead_context: Dict) -> List[Dict]:
       # Create scoring context
       factory = ScoringFactory()
       strategy = factory.get_default_strategy()
       context = PropertyMatcherContext(strategy)

       # Score properties using new system
       scored_properties = context.score_multiple_properties(
           properties=available_properties,
           lead_preferences=lead_context['extracted_preferences'],
           limit=5
       )

       # Convert to legacy format
       return [prop for prop in scored_properties]
   ```

3. **Backward Compatibility**:
   ```python
   # The new system provides legacy format conversion
   scoring_result = context.score_property(property_data, preferences)
   legacy_format = scoring_result.to_legacy_format()
   ```

### Configuration

```python
# Configure factory for your needs
factory = ScoringFactory()

# For high-performance scenarios
fast_strategy = factory.create_strategy('basic')

# For accuracy-focused scenarios
accurate_strategy = factory.create_strategy('enhanced',
                                          market_data=your_market_data)

# For ML scenarios (requires training)
ml_strategy = factory.create_strategy('ml')
```

## SOLID Principles Compliance

### Single Responsibility Principle (SRP) ✅
- **PropertyScorer**: Only responsible for scoring logic
- **ScoringResult**: Only holds scoring data
- **PropertyMatcherContext**: Only manages strategy orchestration
- **ScoringFactory**: Only creates and manages strategies

### Open/Closed Principle (OCP) ✅
- **Open for Extension**: Easy to add new scoring strategies
- **Closed for Modification**: Existing strategies unchanged when adding new ones
- **Example**: Add ML strategy without modifying basic or enhanced strategies

### Liskov Substitution Principle (LSP) ✅
- **Interchangeable**: All strategies implement same `PropertyScorer` interface
- **Behavior Preservation**: Any strategy can replace another without breaking client code
- **Example**: Context can switch from BasicScorer to MLScorer seamlessly

### Interface Segregation Principle (ISP) ✅
- **Focused Interfaces**: `PropertyScorer` only requires essential methods
- **Optional Features**: `TrainableScorer` and `AdaptiveScorer` extend base interface
- **No Fat Interfaces**: Clients only depend on methods they use

### Dependency Inversion Principle (DIP) ✅
- **Abstractions**: Context depends on `PropertyScorer` interface, not concrete classes
- **Dependency Injection**: Strategies injected into context
- **Loose Coupling**: High-level modules don't depend on low-level implementation details

## Testing Strategy

### Unit Tests
```python
# Test individual strategies
def test_basic_scorer():
    scorer = BasicPropertyScorer()
    result = scorer.calculate_score(test_property, test_preferences)
    assert result.overall_score >= 0
    assert result.overall_score <= 100

# Test strategy context
def test_context_strategy_switching():
    context = PropertyMatcherContext()

    # Test with basic strategy
    context.set_strategy(BasicPropertyScorer())
    basic_result = context.score_property(property_data, preferences)

    # Test with enhanced strategy
    context.set_strategy(EnhancedPropertyScorer())
    enhanced_result = context.score_property(property_data, preferences)

    assert basic_result.scorer_type != enhanced_result.scorer_type
```

### Integration Tests
```python
def test_full_property_matching_flow():
    # Test complete flow from legacy format to new system
    legacy_preferences = {'budget': 800000, 'location': 'Downtown'}
    properties = load_test_properties()

    context = PropertyMatcherContext(EnhancedPropertyScorer())
    results = context.score_multiple_properties(properties, legacy_preferences)

    assert len(results) > 0
    assert all('scoring_result' in prop for prop in results)
```

### Performance Tests
```python
def test_scoring_performance():
    # Test that scoring meets performance requirements
    context = PropertyMatcherContext(BasicPropertyScorer())

    start_time = time.time()
    results = context.score_multiple_properties(large_property_list, preferences)
    duration = time.time() - start_time

    assert duration < 2.0  # Should score 100 properties in < 2 seconds
```

## Performance Considerations

### Strategy Performance Characteristics

| Strategy | Properties/sec | Use Case | Memory |
|----------|----------------|----------|---------|
| Basic | 1000+ | High-volume, real-time | Low |
| Enhanced | 200-500 | Balanced accuracy/speed | Medium |
| ML | 50-200 | Accuracy-focused | High |
| Adaptive | 10-100 | Personalization | High |

### Optimization Techniques

1. **Caching**: Results cached by property + preferences hash
2. **Lazy Loading**: Strategies loaded only when needed
3. **Batch Processing**: Score multiple properties efficiently
4. **Strategy Warm-up**: Pre-initialize expensive resources

### Monitoring

```python
# Get performance metrics
context = PropertyMatcherContext(strategy)
metrics = context.get_performance_metrics()

print(f"Average scoring time: {metrics['enhanced']['avg_time']:.3f}s")
print(f"Success rate: {metrics['enhanced']['success_rate']:.2%}")
```

## Configuration Examples

### Production Configuration
```python
# High-performance production setup
factory = ScoringFactory()
factory.set_default_strategy('enhanced')

# Configure with real market data
market_data = load_market_data()
strategy = factory.create_strategy('enhanced', market_data=market_data)
```

### Development/Testing Configuration
```python
# Fast development setup
factory = ScoringFactory()
factory.set_default_strategy('basic')

# Test with multiple strategies
strategies = factory.create_strategy_chain(['basic', 'enhanced'])
```

### ML Training Configuration
```python
# ML model training setup
ml_strategy = factory.create_strategy('ml')
training_results = ml_strategy.train(training_data, validation_data)
ml_strategy.save_model('models/property_scorer_v1.pkl')
```

## Error Handling

### Input Validation
```python
try:
    result = context.score_property(property_data, preferences)
except ValueError as e:
    # Handle validation errors
    logger.error(f"Invalid input data: {e}")
    fallback_result = create_fallback_score()
```

### Strategy Fallback
```python
# Automatic fallback on strategy failure
try:
    result = ml_strategy.calculate_score(property_data, preferences)
except Exception as e:
    logger.warning(f"ML strategy failed: {e}, falling back to enhanced")
    result = enhanced_strategy.calculate_score(property_data, preferences)
```

### Performance Degradation
```python
# Monitor and switch strategies based on performance
if context.get_performance_metrics()['ml']['avg_time'] > 1.0:
    logger.warning("ML strategy too slow, switching to enhanced")
    context.set_strategy(factory.get_strategy('enhanced'))
```

## Extension Points

### Adding New Strategies
1. Inherit from `PropertyScorer`
2. Implement `calculate_score()` and `validate_inputs()`
3. Register with factory
4. Add tests

### Custom Scoring Context
1. Extend `ScoringContext` for ontario_mills-specific context
2. Modify `PropertyMatcherContext` to handle custom context
3. Update strategies to use new context data

### Integration with External Systems
1. Implement strategy that calls external APIs
2. Add caching and error handling
3. Configure timeouts and fallbacks

## Monitoring and Analytics

### Scoring Analytics
- Track strategy usage patterns
- Monitor performance metrics
- Analyze scoring accuracy
- Identify optimization opportunities

### Business Metrics
- Conversion rate by scoring strategy
- Lead engagement by match quality
- Agent satisfaction with recommendations
- Property viewing rates

## Migration Timeline

### Phase 1: Foundation (Week 1-2)
- [ ] Implement core interfaces and basic strategy
- [ ] Add factory pattern and context
- [ ] Create integration layer with existing code
- [ ] Add comprehensive tests

### Phase 2: Enhanced Features (Week 3-4)
- [ ] Implement enhanced strategy with market analysis
- [ ] Add performance monitoring and caching
- [ ] Integrate with existing PropertyMatcher
- [ ] Performance testing and optimization

### Phase 3: Advanced Features (Week 5-6)
- [ ] Implement ML strategy (if data available)
- [ ] Add adaptive learning capabilities
- [ ] Advanced analytics and monitoring
- [ ] Production deployment and validation

### Phase 4: Optimization (Week 7-8)
- [ ] Performance optimization based on production data
- [ ] Strategy recommendation tuning
- [ ] Advanced error handling and resilience
- [ ] Documentation and training