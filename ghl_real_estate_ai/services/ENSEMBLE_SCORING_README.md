# ML Ensemble Lead Scoring System

**Version**: 1.0
**Author**: Claude Code Assistant
**Created**: 2026-02-11

## Overview

Production-ready multi-model ensemble for lead scoring using XGBoost, LightGBM, and Neural Network with stacking meta-learner. Achieves superior accuracy compared to single models through intelligent model combination.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           EnsembleLeadScoringService                    │
├─────────────────────────────────────────────────────────┤
│  Base Models (parallel prediction):                     │
│    ├─ XGBoost Classifier                                │
│    ├─ LightGBM Classifier                               │
│    └─ Neural Network (MLPClassifier: 64→32→16)          │
│                                                          │
│  Meta-Learner (combines base predictions):              │
│    └─ Logistic Regression                               │
│                                                          │
│  Output:                                                 │
│    ├─ Lead Score (0.0 - 1.0)                            │
│    ├─ Classification (hot/warm/lukewarm/cold)           │
│    ├─ Confidence Interval (95% CI)                      │
│    ├─ Model Agreement Score                             │
│    └─ Feature Contributions                             │
└─────────────────────────────────────────────────────────┘
```

## Features (20 Total)

Leverages `SellerAcceptanceFeatureExtractor` for consistent feature engineering:

### Seller Psychology (5 features)
- `psychological_commitment_score` - PCS normalized
- `urgency_score` - Urgency level normalized
- `motivation_intensity` - Motivation strength normalized
- `negotiation_flexibility` - Flexibility score normalized
- `communication_engagement` - Engagement quality normalized

### Pricing Metrics (5 features)
- `list_price_ratio` - List price / market value
- `price_reduction_history` - Total price drops normalized
- `days_on_market_ratio` - DOM vs market avg
- `price_competitiveness` - Price vs comps
- `overpricing_penalty` - Penalty for overpricing

### Market Context (4 features)
- `inventory_pressure` - Market inventory level
- `absorption_rate` - Market absorption rate
- `price_trend_momentum` - Market price trend
- `seasonal_factor` - Seasonal demand factor

### Property Characteristics (3 features)
- `property_appeal_score` - Bed/bath/sqft attractiveness
- `condition_score` - Property condition normalized
- `location_desirability` - Location quality

### Comparables Analysis (3 features)
- `comp_count_confidence` - Number of comps normalized
- `comp_price_variance` - Price variance in comps
- `comp_market_time` - Avg DOM for comps normalized

## Installation

```bash
# Install dependencies
pip install xgboost lightgbm scikit-learn pandas numpy

# Verify installation
python -c "import xgboost, lightgbm; print('OK')"
```

## Usage

### 1. Training the Ensemble

```python
from ghl_real_estate_ai.services.ensemble_lead_scoring import get_ensemble_lead_scoring_service
import pandas as pd

# Load training data
training_data = pd.read_csv("leads_historical.csv")
# Required columns: 20 feature columns + "converted" target

# Initialize service
service = get_ensemble_lead_scoring_service()

# Train ensemble
metrics = service.train_ensemble(
    training_data=training_data,
    target_column="converted",
    test_size=0.2,
    random_state=42,
)

# Review metrics
print(f"Ensemble AUC-ROC: {metrics.ensemble_auc_roc:.4f}")
print(f"Improvement: {metrics.improvement_over_best_base:+.2f}%")
print(f"Brier Score: {metrics.ensemble_brier_score:.4f}")

# Models automatically saved to: models/ensemble_lead_scoring/
```

### 2. Making Predictions

```python
# Predict lead score
prediction = await service.predict_lead_score(
    contact_id="lead_12345",
    features={
        "property_data": {
            "list_price": 800000,
            "beds": 4,
            "baths": 2.5,
            "sqft": 2200,
            "condition": "good",
            "days_on_market": 15,
            "location": {"school_rating": 8, "walkability_score": 75},
        },
        "market_data": {
            "estimated_value": 800000,
            "average_days_on_market": 30,
            "inventory_level": 4.5,
            "absorption_rate": 0.18,
            "price_trend_pct": 5.0,
            "current_month": 5,
            "comparables": [...],
        },
        "psychology_profile": {
            "psychological_commitment_score": 75.0,
            "urgency_level": "high",
            "motivation_type": "relocation",
            "negotiation_flexibility": 0.6,
        },
        "conversation_data": {
            "message_count": 25,
            "avg_response_time_seconds": 1800,
        },
    },
)

# Access results
print(f"Lead Score: {prediction.predicted_score:.3f}")
print(f"Classification: {prediction.predicted_class}")
print(f"Confidence Interval: {prediction.confidence_interval}")
print(f"Model Agreement: {prediction.model_agreement:.3f}")
print(f"Top Features: {prediction.feature_contributions}")
```

### 3. Feature Importance Analysis

```python
# Get feature importance across all models
importance_results = service.get_feature_importance()

for result in importance_results[:5]:  # Top 5
    print(f"{result.feature_name}: {result.ensemble_importance:.4f}")
    print(f"  XGBoost: {result.xgboost_importance:.4f}")
    print(f"  LightGBM: {result.lightgbm_importance:.4f}")
    print(f"  Neural Net: {result.neural_net_importance:.4f}")
    print()
```

### 4. Integration with Existing Lead Scoring

```python
from ghl_real_estate_ai.services.lead_scoring_integration import get_lead_scoring_integration

# Initialize integration (automatically loads ensemble if available)
integration = get_lead_scoring_integration()

# Calculate composite + ensemble scores
state = await integration.calculate_and_store_composite_score(
    state=bot_state,
    contact_id="lead_12345",
    use_ml_ensemble=True,
)

# Access both scores
composite_score = state["composite_score"]  # Rule-based: 0-100
ml_score = state.get("ml_ensemble_score")  # ML ensemble: 0-100
ml_class = state.get("ml_ensemble_class")  # hot/warm/lukewarm/cold

# Prioritization uses ensemble if available
should_prioritize = integration.should_prioritize(state)
```

## CLI Training Script

```bash
# Basic usage
python ghl_real_estate_ai/scripts/train_ensemble_model.py \
  --input data/leads_historical.csv \
  --output models/ensemble_lead_scoring

# Advanced options
python ghl_real_estate_ai/scripts/train_ensemble_model.py \
  --input data/leads_historical.csv \
  --output models/ensemble_lead_scoring \
  --test-size 0.2 \
  --random-seed 42 \
  --skip-validation

# View help
python ghl_real_estate_ai/scripts/train_ensemble_model.py --help
```

**Output Files:**
- `ensemble_models.pkl` - Serialized models
- `ensemble_metrics.json` - Performance metrics
- `training_report.txt` - Detailed training report
- `feature_importance.txt` - Feature analysis

## Training Data Requirements

### Minimum Requirements
- **Samples**: 100+ (recommended: 1000+)
- **Format**: CSV with feature columns + "converted" target
- **Features**: 20 features matching `SellerAcceptanceFeatures.feature_names()`
- **Target**: Binary (0 = not converted, 1 = converted)
- **Balance**: 5-95% conversion rate (10-30% ideal)

### Data Preparation

```python
import pandas as pd

# Load raw lead data
leads = pd.read_csv("raw_leads.csv")

# Extract features using feature extractor
from ghl_real_estate_ai.ml.seller_acceptance_features import SellerAcceptanceFeatureExtractor

extractor = SellerAcceptanceFeatureExtractor()

feature_rows = []
for _, lead in leads.iterrows():
    features = extractor.extract_features(
        seller_id=lead["contact_id"],
        property_data=lead["property_data"],
        market_data=lead["market_data"],
        psychology_profile=lead["psychology_profile"],
        conversation_data=lead["conversation_data"],
    )

    feature_dict = dict(zip(features.feature_names(), features.to_feature_vector()))
    feature_dict["converted"] = lead["converted"]
    feature_rows.append(feature_dict)

training_data = pd.DataFrame(feature_rows)
training_data.to_csv("training_data_prepared.csv", index=False)
```

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **AUC-ROC** | > 0.85 | Primary metric |
| **Improvement** | 5%+ | Over best single model |
| **Brier Score** | < 0.15 | Calibration quality |
| **Latency (cached)** | < 200ms | With Redis cache |
| **Latency (fresh)** | < 1s | Without cache |

## Model Persistence

Models are automatically saved/loaded from:

```
models/ensemble_lead_scoring/
├── ensemble_models.pkl      # Serialized models
└── ensemble_metrics.json    # Performance metrics
```

**Versioning**: Each model includes `model_version` field for tracking.

## Caching

Predictions are cached for 1 hour using Redis:

```python
# Cache key format
cache_key = f"ensemble_lead_score:{contact_id}:{features_hash}:{model_version}"

# TTL: 3600 seconds (1 hour)
```

Cache automatically invalidated when:
- Features change
- Model version changes
- TTL expires

## Monitoring

### Performance Metrics

```python
metrics = service.get_ensemble_metrics()

print(f"Ensemble AUC: {metrics.ensemble_auc_roc:.4f}")
print(f"Training Samples: {metrics.training_samples}")
print(f"Validation Samples: {metrics.validation_samples}")

# Per-model metrics
for model_metrics in metrics.base_model_metrics:
    print(f"{model_metrics.model_name}: AUC={model_metrics.auc_roc:.4f}")
```

### Feature Importance Tracking

Monitor feature importance over time to detect:
- **Feature drift**: Changes in feature importance
- **Data quality issues**: Unexpected importance patterns
- **Model degradation**: Declining predictive power

## Error Handling

The service includes graceful error handling:

```python
# Model not trained
try:
    prediction = await service.predict_lead_score(...)
except ValueError as e:
    print(f"Error: {e}")  # "Ensemble models not trained"

# Invalid input
try:
    prediction = await service.predict_lead_score(
        contact_id="lead",
        features=None,
        feature_vector=None,
    )
except ValueError as e:
    print(f"Error: {e}")  # "Either features or feature_vector must be provided"

# Integration fallback
integration = get_lead_scoring_integration()
# If ensemble fails, automatically falls back to rule-based scoring
```

## Testing

```bash
# Run all tests
pytest tests/test_ensemble_lead_scoring.py -v

# Run specific test class
pytest tests/test_ensemble_lead_scoring.py::TestEnsembleTraining -v

# Run with coverage
pytest tests/test_ensemble_lead_scoring.py --cov=ghl_real_estate_ai.services.ensemble_lead_scoring
```

**Test Coverage**: 19 tests covering:
- Model training
- Prediction accuracy
- Feature importance
- Performance benchmarks
- Integration
- Caching

## Production Deployment

### 1. Collect Training Data

```bash
# Export historical leads with conversion data
python scripts/export_training_data.py --output data/leads_historical.csv
```

### 2. Train Production Model

```bash
python ghl_real_estate_ai/scripts/train_ensemble_model.py \
  --input data/leads_historical.csv \
  --output models/ensemble_lead_scoring \
  --test-size 0.2
```

### 3. Validate Performance

```bash
# Review training_report.txt
cat models/ensemble_lead_scoring/training_report.txt

# Check AUC > 0.85
# Check improvement > 5%
```

### 4. Enable in Production

```python
# In LeadScoringIntegration initialization
integration = LeadScoringIntegration(enable_ml_ensemble=True)

# Or via environment variable
export ENABLE_ML_ENSEMBLE=true
```

### 5. A/B Testing

```python
from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService

ab_service = ABTestingService()

# Create experiment
await ab_service.create_experiment(
    experiment_id="ml_ensemble_vs_rule_based",
    description="Compare ML ensemble to rule-based scoring",
    variants=["control", "ensemble"],
    traffic_allocation={"control": 0.5, "ensemble": 0.5},
)

# Assign variant
variant = await ab_service.assign_variant(
    experiment_id="ml_ensemble_vs_rule_based",
    contact_id=contact_id,
)

# Use ensemble only for treatment group
use_ensemble = (variant == "ensemble")
state = await integration.calculate_and_store_composite_score(
    state=state,
    contact_id=contact_id,
    use_ml_ensemble=use_ensemble,
)
```

## Troubleshooting

### Model Training Fails

**Issue**: `ValueError: Insufficient training data`
**Solution**: Need at least 100 samples. Collect more historical data.

**Issue**: `ModuleNotFoundError: No module named 'lightgbm'`
**Solution**: `pip install lightgbm xgboost scikit-learn`

### Low AUC Performance

**Issue**: AUC < 0.85 on validation set
**Causes**:
- Insufficient training data
- Poor feature quality
- Class imbalance

**Solutions**:
- Collect 1000+ training samples
- Improve feature engineering
- Use SMOTE for class balancing

### Predictions Too Slow

**Issue**: Latency > 1s
**Solutions**:
- Enable Redis caching
- Increase cache TTL
- Use feature vectors instead of feature extraction

## API Reference

### EnsembleLeadScoringService

#### `train_ensemble(training_data, target_column='converted', test_size=0.2, random_state=42)`

Train ensemble model with cross-validation.

**Returns**: `EnsembleMetrics`

#### `predict_lead_score(contact_id, features=None, feature_vector=None)`

Predict lead score with confidence intervals.

**Returns**: `LeadScorePrediction`

#### `get_feature_importance()`

Get feature importance across all models.

**Returns**: `List[FeatureImportanceResult]`

#### `get_ensemble_metrics()`

Get ensemble performance metrics.

**Returns**: `Optional[EnsembleMetrics]`

### LeadScorePrediction

```python
@dataclass
class LeadScorePrediction:
    contact_id: str
    predicted_score: float              # 0.0 - 1.0
    confidence_interval: Tuple[float, float]  # 95% CI
    predicted_class: str                # hot/warm/lukewarm/cold
    model_agreement: float              # 0.0 - 1.0
    feature_contributions: Dict[str, float]
    prediction_timestamp: datetime
    model_version: str
    cached: bool
```

### EnsembleMetrics

```python
@dataclass
class EnsembleMetrics:
    ensemble_auc_roc: float
    ensemble_accuracy: float
    ensemble_precision: float
    ensemble_recall: float
    ensemble_f1_score: float
    ensemble_brier_score: float
    base_model_metrics: List[ModelPerformanceMetrics]
    improvement_over_best_base: float
    training_samples: int
    validation_samples: int
    training_date: datetime
    model_version: str
```

## Dependencies

```
xgboost>=2.0.0
lightgbm>=4.0.0
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
```

## License

Internal use only - EnterpriseHub Real Estate AI Platform

## Support

For issues or questions:
- Check test suite: `tests/test_ensemble_lead_scoring.py`
- Review CLAUDE.md for project context
- Contact: ML team

---

**Last Updated**: 2026-02-11
**Status**: Production Ready (pending training data)
