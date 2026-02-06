# Jorge Feature Engineering Pipeline

## Overview

The Jorge Feature Engineering Pipeline is a comprehensive, production-ready system that extracts **28 machine learning features** from real estate lead data with **<30ms performance targets**. It integrates seamlessly with existing Jorge components including `LeadIntelligenceOptimized` and `JorgeBusinessRules` while maintaining sklearn compatibility for XGBoost models.

## Architecture

```
Lead Data → Feature Engineering → 28 ML Features → ML Models
    ↓              ↓                    ↓              ↓
Raw Text    Text Analysis        Numerical         XGBoost
History     Market Context       Categorical       Predictions
Budget      Business Rules       Boolean           Recommendations
Location    Engagement           Features          Actions
```

## Key Features

### 🎯 Performance Targets
- **<30ms** feature extraction per lead
- **Sklearn compatibility** for ML pipelines  
- **Caching enabled** for sub-100ms cache hits
- **Batch processing** for high-throughput scenarios

### 📊 Feature Categories (28 Total)

#### Numerical Features (8)
1. `avg_response_time_minutes` - Communication responsiveness
2. `budget_specificity_score` - Budget precision level
3. `location_specificity_count` - Number of location preferences
4. `message_length_variance` - Communication pattern variance
5. `urgency_keyword_frequency` - Urgency signal strength
6. `market_timing_awareness` - Market condition understanding
7. `financing_readiness_score` - Financial preparation level
8. `jorge_fit_alignment` - Alignment with Jorge's criteria

#### Categorical Features (12)
1. `timeline_category` - Buying timeline classification
2. `budget_range_category` - Budget range grouping
3. `primary_location_area` - Primary location preference
4. `financing_status_category` - Financing situation
5. `communication_style` - Communication approach
6. `lead_source_type` - Lead origin classification
7. `property_type_preference` - Property type interest
8. `market_segment` - Market category classification
9. `seasonal_timing` - Seasonal market context
10. `engagement_pattern` - Interaction engagement level
11. `decision_stage` - Decision-making phase
12. `jorge_priority_level` - Jorge's priority assignment

#### Boolean Features (8)
1. `has_specific_budget` - Budget specificity indicator
2. `has_location_preference` - Location preference indicator
3. `is_pre_approved` - Financing approval status
4. `meets_jorge_criteria` - Jorge's criteria compliance
5. `shows_urgency_signals` - Urgency indicator presence
6. `in_service_area` - Service area inclusion
7. `repeat_interaction` - Repeat contact indicator
8. `market_timing_optimal` - Optimal market timing

## Quick Start

### Installation

```python
# Required dependencies
pip install scikit-learn numpy pandas anthropic

# Import the pipeline
from bots.shared.feature_engineering import FeatureEngineering, JorgeFeaturePipeline
```

### Basic Usage

```python
# Initialize the feature engineering pipeline
feature_engineer = FeatureEngineering()

# Sample lead data
lead_data = {
    'message': "Pre-approved for $600k, looking in Plano within 30 days",
    'timestamp': datetime.now(),
    'source': 'website_form',
    'contact_history': [
        {
            'direction': 'inbound', 
            'timestamp': datetime.now().isoformat(), 
            'body': 'Initial inquiry'
        }
    ]
}

# Extract features (returns 28 numerical values)
features = feature_engineer.extract_features_from_record(lead_data)
print(f"Extracted {len(features)} features in <30ms")

# Get feature names for interpretation
feature_names = feature_engineer.get_feature_names()
feature_dict = dict(zip(feature_names, features))
```

### Sklearn Pipeline Integration

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

# Create complete ML pipeline
pipeline = Pipeline([
    ('feature_engineering', FeatureEngineering()),
    ('scaling', StandardScaler()),
    ('classifier', RandomForestClassifier())
])

# Train with lead data
X = [lead_data1, lead_data2, lead_data3]  # List of lead dictionaries
y = [1, 0, 1]  # Target labels

pipeline.fit(X, y)

# Make predictions
new_lead = {'message': '...', 'timestamp': datetime.now()}
prediction = pipeline.predict([new_lead])
```

### Batch Processing

```python
# Process multiple leads efficiently
jorge_pipeline = JorgeFeaturePipeline()
leads = [lead1, lead2, lead3, ...]  # List of lead dictionaries

# Extract features for all leads
features_df = jorge_pipeline.extract_features_batch(leads)
print(f"Processed {len(leads)} leads")
print(f"Feature matrix shape: {features_df.shape}")

# Prepare for ML training
features_matrix, feature_names = jorge_pipeline.prepare_training_data(leads)
```

## Integration with Jorge Components

### LeadIntelligenceOptimized Integration

The pipeline automatically integrates with Jorge's existing lead intelligence:

```python
# Automatic integration - no additional code needed
from jorge_deployment_package.lead_intelligence_optimized import get_enhanced_lead_intelligence

# The feature engineering pipeline internally calls:
intelligence = get_enhanced_lead_intelligence(message)
# Then extracts ML features from the intelligence results
```

### Business Rules Integration

```python
from bots.shared.business_rules import JorgeBusinessRulesEngine

# Initialize Jorge's business rules
rules_engine = JorgeBusinessRulesEngine()

# Qualify leads using Jorge's criteria
qualification = rules_engine.qualify_lead_for_jorge(lead_intelligence)

# Automatic integration with feature engineering
jorge_features = integrate_with_feature_engineering(qualification)
```

## Performance Monitoring

### Performance Metrics

```python
# Get performance metrics
metrics = feature_engineer.get_performance_metrics()

print(f"Average extraction time: {metrics['avg_extraction_time_ms']:.1f}ms")
print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")
print(f"Performance target met: {metrics['performance_target_met']}")
print(f"Success rate: {metrics['extraction_success_rate']:.1%}")
```

### Benchmarking

```python
from bots.shared.feature_engineering import benchmark_feature_extraction

# Run performance benchmark
results = benchmark_feature_extraction(num_samples=100)

print(f"Throughput: {results['throughput_per_second']:.1f} leads/second")
print(f"Meets 30ms target: {'✅' if results['meets_30ms_target'] else '❌'}")
```

## Advanced Features

### Caching for Performance

```python
# Enable intelligent caching (default: enabled)
feature_engineer = FeatureEngineering(
    enable_caching=True,
    performance_tracking=True
)

# Cache automatically handles:
# - Message content hashing
# - TTL-based expiration
# - Memory + disk caching
# - Cache hit optimization
```

### Feature Validation

```python
# Enable strict feature validation
feature_engineer = FeatureEngineering(validation_strict=True)

# Validate feature schema manually
features_dict = {...}  # Extracted features as dictionary
validation_result = feature_engineer.validate_schema(features_dict)

if not validation_result['valid']:
    print("Validation issues:", validation_result['missing_features'])
```

### Custom Market Context

```python
from bots.shared.feature_engineering import MarketContextAnalyzer

analyzer = MarketContextAnalyzer()

# Analyze seasonal patterns
seasonal_context = analyzer.get_seasonal_context(datetime.now())
print(f"Current season: {seasonal_context['season']}")
print(f"Activity score: {seasonal_context['seasonal_activity_score']:.2f}")

# Assess market timing
timing_score = analyzer.assess_market_timing('immediate')
print(f"Market timing alignment: {timing_score:.2f}")
```

## Production Deployment

### Environment Setup

```python
# Production configuration
feature_engineer = FeatureEngineering(
    enable_caching=True,          # Essential for performance
    performance_tracking=True,    # Monitor production metrics
    validation_strict=True        # Ensure data quality
)

# Set up monitoring
import logging
logging.basicConfig(level=logging.INFO)
```

### Error Handling

The pipeline includes comprehensive error handling:

- **Graceful degradation** on missing data
- **Default feature values** for error cases  
- **Comprehensive logging** for debugging
- **Fallback mechanisms** for system failures

```python
# Error handling is automatic - pipeline never fails
try:
    features = feature_engineer.extract_features_from_record(invalid_data)
    # Always returns 28 features, even with errors
except Exception as e:
    # Pipeline handles all exceptions internally
    pass
```

### XGBoost Integration

```python
import xgboost as xgb

# Prepare data for XGBoost
features_matrix, feature_names = jorge_pipeline.prepare_training_data(train_leads)
X_train = features_matrix
y_train = [...]  # Target labels

# Train XGBoost model
model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42
)

model.fit(X_train, y_train, feature_names=feature_names)

# Feature importance analysis
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("Top 10 Most Important Features:")
print(importance_df.head(10))
```

## Testing

### Run Comprehensive Tests

```bash
# Run all tests
cd bots/shared
python test_feature_engineering.py

# Expected output:
# ✅ ALL TESTS PASSED! Feature engineering pipeline ready for production.
# 📈 Performance Results:
#    - Average extraction time: 12.3ms
#    - Meets 30ms target: ✅
#    - Throughput: 81.3 leads/second
```

### Individual Test Categories

```python
# Test performance specifically
python -c "from bots.shared.test_feature_engineering import TestPerformanceBenchmarks; 
import unittest; unittest.main(module=TestPerformanceBenchmarks, verbosity=2)"

# Test Jorge integration
python -c "from bots.shared.test_feature_engineering import TestIntegrationWithJorgeComponents;
import unittest; unittest.main(module=TestIntegrationWithJorgeComponents, verbosity=2)"
```

## Feature Engineering Details

### Text Analysis Features

The pipeline includes advanced text analysis:

```python
from bots.shared.feature_engineering import AdvancedTextAnalyzer

analyzer = AdvancedTextAnalyzer()

# Communication style analysis
style = analyzer.analyze_communication_style("Dear sir, I would like to inquire...")
# Returns: {'style': 'formal', 'formality_score': 0.85}

# Urgency signal detection
urgency = analyzer.extract_urgency_signals("Need house ASAP!")
# Returns: {'urgency_score': 0.9, 'has_urgency_signals': True}

# Decision stage identification
stage = analyzer.identify_decision_stage("Ready to make an offer")
# Returns: 'commitment'
```

### Market Context Analysis

```python
from bots.shared.feature_engineering import MarketContextAnalyzer

analyzer = MarketContextAnalyzer()

# Seasonal market patterns
context = analyzer.get_seasonal_context(datetime(2026, 6, 15))
# Summer timing analysis

# Market timing assessment
timing = analyzer.assess_market_timing('immediate', context)
# Combines seasonal and urgency factors
```

### Jorge-Specific Features

Features specifically designed for Jorge's business:

- **Service area alignment** with Dallas/Plano/Frisco focus
- **Budget range optimization** for $200K-$800K targets
- **Commission potential analysis** with 6% rate calculations
- **Timeline preference scoring** for Jorge's 60-day preference

## Troubleshooting

### Common Issues

1. **Slow Performance (>30ms)**
   ```python
   # Check cache status
   metrics = feature_engineer.get_performance_metrics()
   if metrics['cache_hit_rate'] < 0.5:
       # Cache may need warming up
       pass
   ```

2. **Missing Features**
   ```python
   # Validate schema
   validation = feature_engineer.validate_schema(features_dict)
   print("Missing:", validation['missing_features'])
   ```

3. **Integration Errors**
   ```python
   # Check Jorge component imports
   try:
       from jorge_deployment_package.lead_intelligence_optimized import get_enhanced_lead_intelligence
       print("✅ Lead intelligence available")
   except ImportError as e:
       print(f"❌ Import error: {e}")
   ```

### Performance Optimization

- **Enable caching** for repeated extractions
- **Use batch processing** for multiple leads
- **Monitor metrics** to identify bottlenecks
- **Clear cache periodically** to prevent memory growth

```python
# Clear cache if needed
feature_engineer.clear_cache()

# Disable caching for testing
test_engineer = FeatureEngineering(enable_caching=False)
```

## API Reference

### FeatureEngineering Class

```python
class FeatureEngineering(BaseEstimator, TransformerMixin):
    def __init__(self, enable_caching=True, performance_tracking=True, validation_strict=True)
    def fit(self, X, y=None) -> self
    def transform(self, X: Union[List[Dict], pd.DataFrame]) -> np.ndarray
    def extract_features_from_record(self, lead_data: Dict) -> List[float]
    def get_feature_names(self) -> List[str]
    def get_performance_metrics(self) -> Dict[str, Any]
    def clear_cache(self) -> None
```

### JorgeFeaturePipeline Class

```python
class JorgeFeaturePipeline:
    def __init__(self)
    def extract_features_batch(self, leads: List[Dict]) -> pd.DataFrame
    def prepare_training_data(self, lead_data: List[Dict]) -> Tuple[np.ndarray, List[str]]
    def create_sklearn_pipeline(self) -> Pipeline
```

### Utility Functions

```python
def create_sample_lead_data() -> List[Dict]
def benchmark_feature_extraction(num_samples: int = 100) -> Dict[str, Any]
```

## Contributing

To extend the feature engineering pipeline:

1. **Add new features** to `FeatureSchema` class
2. **Implement extraction logic** in `_extract_all_features`
3. **Add validation rules** for new features  
4. **Update tests** in `test_feature_engineering.py`
5. **Benchmark performance** to ensure <30ms target

## License

This feature engineering pipeline is part of the Jorge Real Estate AI system and follows the project's licensing terms.

---

**Version**: 1.0.0  
**Performance Target**: <30ms extraction  
**Feature Count**: 28 features  
**Compatibility**: sklearn, XGBoost, pandas, numpy