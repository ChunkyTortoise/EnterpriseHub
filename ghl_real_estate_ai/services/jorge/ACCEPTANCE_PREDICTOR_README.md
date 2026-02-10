# Seller Offer Acceptance Predictor Service

**Status**: ✅ Production-ready (Rule-based mode) | 🚧 XGBoost model pending training data

**Purpose**: Predict the probability that a seller will accept a given offer price using machine learning and rule-based heuristics.

## Quick Start

```python
from ghl_real_estate_ai.services.jorge.acceptance_predictor import get_acceptance_predictor

# Initialize service
predictor = get_acceptance_predictor(
    enable_caching=True,
    force_rule_based=True  # Use until ML model trained
)

# Prepare seller state
seller_state = {
    "seller_id": "seller_123",
    "psychological_commitment": 75.0,  # PCS score (0-100)
    "listing_price_recommendation": 500000.0,
    "estimated_value": 495000.0,
    "seller_intent_profile": {
        "motivation_strength": 70.0,
        "listing_urgency": 65.0,
    }
}

# Predict acceptance probability
prediction = await predictor.predict_acceptance_probability(
    seller_id="seller_123",
    offer_price=475000,  # $475k offer
    seller_state=seller_state
)

print(f"Acceptance probability: {prediction.acceptance_probability:.1%}")
print(f"Confidence: {prediction.confidence_level.value}")
print(f"Recommended offer: ${prediction.recommended_offer:,.0f}")
print(f"Key factors: {prediction.key_factors}")
```

**Output:**
```
Acceptance probability: 78.3%
Confidence: medium
Recommended offer: $480,000
Key factors: ['Strong offer (95.0% of asking price)', 'High seller engagement (PCS: 75/100)', 'Strong motivation to sell']
```

## Features

### 1. Acceptance Probability Prediction

Predicts the likelihood (0.0-1.0) that a seller will accept an offer:

```python
prediction = await predictor.predict_acceptance_probability(
    seller_id="seller_123",
    offer_price=475000,
    seller_state=seller_state
)

# Returns: AcceptancePrediction object
# - acceptance_probability: float (0.0-1.0)
# - confidence_level: HIGH | MEDIUM | LOW
# - feature_importances: List[FeatureImportance]
# - key_factors: List[str]
# - optimal_price_range: (min, max)
# - recommended_offer: float
# - expected_value: probability * offer_price
```

### 2. Optimal Price Range Calculation

Find the price range that achieves a target acceptance probability:

```python
price_range = await predictor.get_optimal_price_range(
    seller_id="seller_123",
    target_probability=0.75,  # Target 75% acceptance
    seller_state=seller_state
)

print(f"Optimal range: ${price_range.min_price:,.0f} - ${price_range.max_price:,.0f}")
print(f"Recommended: ${price_range.recommended_price:,.0f}")
print(f"Confidence: {price_range.confidence_score:.2f}")
```

### 3. Prediction Explanation

Get human-readable explanations with feature importance:

```python
explanation = await predictor.explain_prediction(
    seller_id="seller_123",
    offer_price=475000,
    seller_state=seller_state
)

print(explanation["explanation_text"])
print("\nFeature importances:")
for fi in explanation["feature_importances"]:
    print(f"  {fi['feature_name']}: {fi['importance_score']:.2%}")
```

## Rule-Based Scoring (Current Mode)

Until sufficient training data is collected, the service uses sophisticated rule-based heuristics:

### Scoring Formula
```
acceptance_prob = (price_ratio × 0.40) + (PCS × 0.30) + (motivation × 0.20) + (timeline × 0.10)
```

### Components

1. **Price Ratio (40% weight)**
   - Offer price ÷ Listing price (or property value)
   - Sigmoid curve: 95%+ ratio → high score, <80% ratio → low score

2. **Psychological Commitment Score (30% weight)**
   - Extracted from `seller_state["psychological_commitment"]`
   - Normalized 0-1 scale

3. **Motivation Strength (20% weight)**
   - Extracted from `seller_intent_profile["motivation_strength"]`
   - Normalized 0-1 scale

4. **Timeline Urgency (10% weight)**
   - Extracted from `seller_intent_profile["listing_urgency"]`
   - Normalized 0-1 scale

### Feature Extraction

The service intelligently extracts features from seller state with multiple fallback paths:

```python
# PCS score extraction tries:
# 1. seller_state["psychological_commitment"]
# 2. seller_state["pcs"]
# 3. seller_state["intent_profile"]["pcs"]["total_score"]
# Default: 50.0 (neutral)

# Listing price extraction tries:
# 1. seller_state["listing_price_recommendation"]
# 2. seller_state["listing_price"]
# 3. seller_state["price_expectation"]
# Default: None (uses property value or offer price)

# Property value extraction tries:
# 1. seller_state["estimated_value"]
# 2. seller_state["property_value"]
# 3. seller_state["zestimate"]
# Default: None
```

## XGBoost Model (Future)

Once sufficient historical data is collected (MIN_TRAINING_SAMPLES = 50), the service will automatically switch to XGBoost mode:

### Model Architecture
- **Algorithm**: XGBoost binary classifier
- **Calibration**: Isotonic regression for probability calibration
- **Hyperparameters**:
  ```python
  {
      "max_depth": 6,
      "n_estimators": 100,
      "learning_rate": 0.1,
      "min_child_weight": 3,
      "subsample": 0.8,
      "colsample_bytree": 0.8,
      "objective": "binary:logistic",
      "eval_metric": "auc"
  }
  ```

### Model Training (Task #11 Integration)

```python
# Feature extraction from SellerAcceptanceFeatureExtractor
from ghl_real_estate_ai.services.jorge.feature_extractor import SellerAcceptanceFeatureExtractor

feature_extractor = SellerAcceptanceFeatureExtractor()

# Extract features for training
features = await feature_extractor.extract_features(
    seller_id="seller_123",
    offer_price=475000,
    seller_state=seller_state
)

# Train model (when data available)
# TODO: Implement model training pipeline
# - Collect historical acceptance outcomes
# - Extract features for all historical offers
# - Train XGBoost with 5-fold cross-validation
# - Calibrate probabilities with isotonic regression
# - Save model to models/acceptance_predictor.pkl
```

### Performance Targets
- **AUC-ROC**: > 0.80 (validation set)
- **Brier Score**: < 0.15 (calibration quality)
- **Latency**: <200ms (cached), <1s (fresh)

## Confidence Classification

| Probability Range | Data Sufficiency | Confidence Level |
|-------------------|------------------|------------------|
| ≥ 0.80 or ≤ 0.20  | Sufficient       | HIGH             |
| 0.60-0.80 or 0.20-0.40 | Sufficient  | MEDIUM           |
| 0.40-0.60         | Sufficient       | LOW              |
| Any               | Limited          | LOW              |
| Any               | Insufficient     | LOW              |

### Data Sufficiency Assessment

- **Sufficient**: 3+ non-default data points (PCS, price, motivation)
- **Limited**: 2 non-default data points
- **Insufficient**: 0-1 non-default data points

## Caching Strategy

Predictions are cached for 1 hour with price rounding to nearest $1,000 for cache efficiency:

```python
# Cache key generation
def _generate_cache_key(seller_id: str, offer_price: float) -> str:
    rounded_price = round(offer_price / 1000) * 1000  # Round to $1k
    raw_key = f"acceptance_prediction:{seller_id}:{rounded_price}"
    return hashlib.sha256(raw_key.encode()).hexdigest()[:32]
```

**Example**: Offers of $475,000, $475,200, and $475,800 all use the same cache key ($475,000) to reduce redundant predictions.

## Integration with Seller Bot

### Use Case 1: Offer Evaluation

```python
from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine
from ghl_real_estate_ai.services.jorge.acceptance_predictor import get_acceptance_predictor

predictor = get_acceptance_predictor()

async def evaluate_offer(seller_id: str, offer_price: float, seller_state: dict):
    """Evaluate incoming offer and provide recommendation."""
    prediction = await predictor.predict_acceptance_probability(
        seller_id=seller_id,
        offer_price=offer_price,
        seller_state=seller_state
    )

    if prediction.acceptance_probability >= 0.75:
        recommendation = "ACCEPT - High acceptance probability"
    elif prediction.acceptance_probability >= 0.50:
        recommendation = "NEGOTIATE - Counter with recommended price"
    else:
        recommendation = "DECLINE - Offer significantly below expectations"

    return {
        "recommendation": recommendation,
        "probability": prediction.acceptance_probability,
        "counter_offer": prediction.recommended_offer,
        "reasoning": prediction.key_factors
    }
```

### Use Case 2: Buyer Guidance

```python
async def guide_buyer_offer(seller_id: str, seller_state: dict, buyer_budget: float):
    """Help buyer craft competitive offer."""
    # Find optimal price for 75% acceptance probability
    price_range = await predictor.get_optimal_price_range(
        seller_id=seller_id,
        target_probability=0.75,
        seller_state=seller_state
    )

    # Adjust for buyer budget
    if buyer_budget < price_range.min_price:
        return {
            "status": "budget_insufficient",
            "message": f"Property likely requires ${price_range.min_price:,.0f}+ offer",
            "probability_at_budget": await get_probability_at_price(buyer_budget)
        }

    # Recommend strongest offer within budget
    recommended = min(buyer_budget, price_range.recommended_price)

    return {
        "status": "offer_recommended",
        "recommended_offer": recommended,
        "acceptance_probability": await get_probability_at_price(recommended),
        "price_range": (price_range.min_price, price_range.max_price)
    }
```

### Use Case 3: Market Intelligence

```python
async def analyze_market_position(seller_id: str, listing_price: float, seller_state: dict):
    """Analyze seller's market position and pricing strategy."""
    # Test multiple price points
    test_prices = [
        listing_price * 0.85,  # Low offer
        listing_price * 0.90,  # Below asking
        listing_price * 0.95,  # Near asking
        listing_price * 1.00,  # Full price
    ]

    predictions = []
    for price in test_prices:
        pred = await predictor.predict_acceptance_probability(
            seller_id=seller_id,
            offer_price=price,
            seller_state=seller_state
        )
        predictions.append((price, pred.acceptance_probability))

    return {
        "price_sensitivity": predictions,
        "listing_competitiveness": classify_pricing(predictions),
        "recommendation": generate_pricing_strategy(predictions)
    }
```

## Error Handling

```python
try:
    prediction = await predictor.predict_acceptance_probability(
        seller_id="seller_123",
        offer_price=475000,
        seller_state=seller_state
    )
except ValueError as e:
    # Invalid input (empty seller_id, negative price, etc.)
    logger.error(f"Invalid input: {e}")
except Exception as e:
    # Unexpected error (log and fallback)
    logger.error(f"Prediction failed: {e}", exc_info=True)
    # Fallback to conservative estimate
    prediction = create_conservative_fallback(offer_price)
```

## Monitoring & Metrics

Key metrics to track in production:

1. **Prediction Accuracy**
   - Compare predicted probabilities to actual acceptance outcomes
   - Track calibration quality (Brier score)
   - Monitor AUC-ROC over time

2. **Service Performance**
   - P50/P95/P99 latency
   - Cache hit rate
   - Error rate

3. **Model Drift**
   - Feature distribution changes
   - Prediction drift over time
   - Data sufficiency trends

4. **Business Impact**
   - Offer acceptance rate for "high probability" predictions
   - Negotiation success rate
   - Time to close (correlation with predictions)

## Testing

Comprehensive test suite with 35 tests covering:

```bash
# Run all tests
python3 -m pytest ghl_real_estate_ai/tests/services/jorge/test_acceptance_predictor.py -v

# Run specific test category
python3 -m pytest ghl_real_estate_ai/tests/services/jorge/test_acceptance_predictor.py -k "optimal_price"

# Run with coverage
python3 -m pytest ghl_real_estate_ai/tests/services/jorge/test_acceptance_predictor.py --cov
```

Test categories:
- Basic prediction tests (hot/cold sellers, minimal data)
- Price ratio impact tests
- Optimal price range tests
- Explanation generation tests
- Feature extraction tests
- Confidence classification tests
- Data sufficiency tests
- Caching tests
- Validation tests
- Integration tests

## Configuration

Environment variables (optional):

```bash
# Force rule-based mode (bypass ML model)
ACCEPTANCE_PREDICTOR_FORCE_RULE_BASED=true

# Disable caching
ACCEPTANCE_PREDICTOR_DISABLE_CACHE=true

# Model path (default: models/acceptance_predictor.pkl)
ACCEPTANCE_PREDICTOR_MODEL_PATH=/path/to/model.pkl

# Minimum training samples before using ML model
ACCEPTANCE_PREDICTOR_MIN_SAMPLES=50
```

## Future Enhancements

1. **Model Training Pipeline** (Task #11 + model training)
   - Automated data collection from historical offers
   - Feature engineering with SellerAcceptanceFeatureExtractor
   - 5-fold cross-validation with hyperparameter tuning
   - Probability calibration with isotonic regression
   - Automated model retraining on schedule

2. **SHAP Explanations**
   - Replace rule-based feature importance with SHAP values
   - Provide individual prediction explanations
   - Identify key drivers for each prediction

3. **Model Ensemble**
   - Combine XGBoost + LightGBM + CatBoost
   - Weighted voting for robust predictions
   - Confidence-based model selection

4. **Real-time Learning**
   - Online learning from new acceptance outcomes
   - Continuous model updates without full retraining
   - Adaptive threshold tuning based on recent performance

5. **Multi-model Strategy**
   - Separate models for different seller segments
   - Property type-specific models
   - Market condition-aware models

## Support

- **Documentation**: This README + inline code comments
- **Tests**: `ghl_real_estate_ai/tests/services/jorge/test_acceptance_predictor.py`
- **Source**: `ghl_real_estate_ai/services/jorge/acceptance_predictor.py`
- **Owner**: ml-predictor-dev agent
- **Created**: 2026-02-10

---

**Status Summary**:
- ✅ Rule-based prediction (production-ready)
- ✅ Optimal price range calculation
- ✅ Prediction explanations
- ✅ Caching (1-hour TTL)
- ✅ Comprehensive test coverage (35 tests)
- 🚧 XGBoost model (pending training data)
- 🚧 SHAP explanations (pending XGBoost)
- 🚧 Feature extractor integration (Task #11)
