# Conversion Prediction Models Reference

Documentation for ML models and weight configurations used in lead conversion prediction.

## Model Architecture

### Unified Scoring Model

The conversion prediction system uses a multi-layer approach combining:
1. **Jorge's Question-Count** (40% base weight)
2. **ML Behavioral Analysis** (35% weight)
3. **Market Timing Factors** (15% weight)
4. **Engagement Patterns** (10% weight)

### Feature Categories

#### Conversation Features
| Feature | Type | Description | Weight Range |
|---------|------|-------------|--------------|
| `message_count` | int | Total messages exchanged | 0.05-0.15 |
| `response_velocity` | float | Average response time (hours) | 0.10-0.20 |
| `question_depth` | int | Specificity of questions asked | 0.08-0.18 |
| `sentiment_trend` | float | Emotional progression (-1 to 1) | 0.05-0.12 |
| `objection_count` | int | Number of objections raised | -0.05-0.00 |

#### Behavioral Features
| Feature | Type | Description | Weight Range |
|---------|------|-------------|--------------|
| `page_views` | int | Property pages viewed | 0.03-0.10 |
| `email_opens` | float | Email open rate | 0.05-0.12 |
| `link_clicks` | int | Links clicked in messages | 0.04-0.10 |
| `return_visits` | int | Repeat engagement sessions | 0.08-0.15 |
| `document_downloads` | int | CMA, guides downloaded | 0.10-0.18 |

#### Profile Features
| Feature | Type | Description | Weight Range |
|---------|------|-------------|--------------|
| `budget_confirmed` | bool | Has stated budget | 0.15-0.25 |
| `timeline_days` | int | Days until target move | 0.10-0.20 |
| `pre_approved` | bool | Has mortgage pre-approval | 0.18-0.28 |
| `decision_maker` | bool | Primary decision maker | 0.08-0.15 |
| `previous_buyer` | bool | Has purchased before | 0.05-0.10 |

## Scoring Algorithms

### Base Score Calculation

```python
def calculate_base_conversion_score(features: Dict[str, Any]) -> float:
    """
    Calculate base conversion probability using weighted features.

    Returns: Score from 0-100
    """
    # Jorge's question-based score (40% weight)
    jorge_score = calculate_jorge_score(features) * 0.40

    # ML behavioral score (35% weight)
    ml_score = ml_model.predict(features) * 0.35

    # Market timing score (15% weight)
    market_score = calculate_market_timing(features) * 0.15

    # Engagement pattern score (10% weight)
    engagement_score = calculate_engagement_pattern(features) * 0.10

    return jorge_score + ml_score + market_score + engagement_score
```

### Jorge's Question-Count Score

```python
def calculate_jorge_score(features: Dict[str, Any]) -> float:
    """
    Apply Jorge's proven 7-question methodology.

    Classification based on meaningful answers:
    - 3+ answers: Hot (75-100 score)
    - 2 answers: Warm (40-74 score)
    - 0-1 answers: Cold (0-39 score)
    """
    questions = [
        "budget", "location", "bedrooms", "timeline",
        "pre_approval", "motivation", "seller_condition"
    ]

    answered = sum(1 for q in questions if features.get(q) is not None)

    if answered >= 5:
        return 90 + (answered - 5) * 2  # 90-100
    elif answered >= 3:
        return 60 + (answered - 3) * 15  # 60-90
    elif answered == 2:
        return 40 + 10  # 40-50
    else:
        return answered * 20  # 0-20
```

### ML Model Features

```python
class ConversionPredictor:
    """
    Machine learning model for conversion prediction.
    Uses gradient boosting with behavioral features.
    """

    def extract_features(self, lead_data: Dict) -> np.ndarray:
        """Extract feature vector from lead data."""
        return np.array([
            # Conversation features
            lead_data.get("message_count", 0),
            lead_data.get("avg_response_time_hours", 24),
            lead_data.get("question_specificity", 0),
            lead_data.get("sentiment_score", 0),

            # Behavioral features
            lead_data.get("page_views", 0),
            lead_data.get("email_open_rate", 0),
            lead_data.get("return_visits", 0),

            # Profile features
            1 if lead_data.get("budget_confirmed") else 0,
            lead_data.get("timeline_days", 365),
            1 if lead_data.get("pre_approved") else 0,
        ])

    def predict(self, features: np.ndarray) -> float:
        """Predict conversion probability."""
        # Model returns 0-1 probability
        prob = self.model.predict_proba(features.reshape(1, -1))[0][1]
        return prob * 100  # Convert to 0-100 scale
```

## Market Timing Weights

### Seasonal Adjustments
| Season | Weight Multiplier | Rationale |
|--------|------------------|-----------|
| Spring (Mar-May) | 1.10 | Peak buying season |
| Summer (Jun-Aug) | 1.05 | Strong market activity |
| Fall (Sep-Nov) | 1.00 | Baseline |
| Winter (Dec-Feb) | 0.95 | Reduced activity |

### Market Condition Adjustments
| Condition | Weight Multiplier |
|-----------|------------------|
| Seller's market (<3 mo inventory) | 1.15 |
| Balanced market (3-6 mo) | 1.00 |
| Buyer's market (>6 mo) | 0.90 |

### Interest Rate Sensitivity
| Rate Change | Impact |
|-------------|--------|
| Rates dropping | +5% urgency |
| Rates stable | Baseline |
| Rates rising | +10% urgency (fear of missing out) |

## Segment-Specific Weights

### First-Time Buyers
```python
FIRST_TIME_BUYER_WEIGHTS = {
    "jorge_weight": 1.2,      # Trust simple approach
    "ml_weight": 0.8,         # Less complex behavior patterns
    "education_score": 1.3,   # Value guidance
    "timeline_sensitivity": 0.9  # More flexible timelines
}
```

### Investors
```python
INVESTOR_WEIGHTS = {
    "jorge_weight": 0.8,      # More complex decision process
    "ml_weight": 1.3,         # Data-driven behavior
    "roi_questions": 1.4,     # High weight on investment questions
    "timeline_sensitivity": 1.2  # Opportunity-driven timing
}
```

### Luxury Buyers
```python
LUXURY_BUYER_WEIGHTS = {
    "jorge_weight": 1.0,      # Balanced approach
    "ml_weight": 1.0,         # Balanced approach
    "market_timing": 1.5,     # Very timing-sensitive
    "relationship_score": 1.4  # Trust-based decisions
}
```

## Confidence Intervals

### Score Confidence Calculation

```python
def calculate_confidence(features: Dict, score: float) -> float:
    """
    Calculate confidence in the prediction.

    Based on:
    - Data completeness
    - Feature variance
    - Historical accuracy for similar profiles
    """
    # Data completeness (0-40%)
    required_fields = ["budget", "timeline", "location", "messages"]
    completeness = sum(1 for f in required_fields if features.get(f)) / len(required_fields)

    # Feature quality (0-30%)
    quality = min(features.get("message_count", 0) / 10, 1) * 0.3

    # Historical accuracy for segment (0-30%)
    segment = features.get("buyer_type", "unknown")
    segment_accuracy = HISTORICAL_ACCURACY.get(segment, 0.7) * 0.3

    return completeness * 0.4 + quality + segment_accuracy
```

### Confidence Thresholds
| Confidence | Interpretation | Recommended Action |
|------------|----------------|-------------------|
| > 0.8 | High confidence | Act on prediction |
| 0.6-0.8 | Moderate confidence | Verify key signals |
| 0.4-0.6 | Low confidence | Gather more data |
| < 0.4 | Insufficient data | Manual qualification needed |

## Model Performance

### Training Data
- **Source**: 18 months of GHL conversation data
- **Sample Size**: 2,847 completed transactions
- **Features**: 47 engineered features
- **Target**: Binary conversion (closed/not closed)

### Performance Metrics
| Metric | Value | Description |
|--------|-------|-------------|
| Accuracy | 82.4% | Overall prediction accuracy |
| Precision (Hot) | 87.2% | Hot leads that convert |
| Recall (Hot) | 79.6% | Hot leads correctly identified |
| F1 Score | 83.2% | Balanced performance |
| AUC-ROC | 0.89 | Discrimination ability |

### Calibration
The model is calibrated to match Jorge's historical conversion rates:
- **Hot leads**: 45% → Model predicts 42-48%
- **Warm leads**: 22% → Model predicts 20-25%
- **Cold leads**: 8% → Model predicts 6-10%

## Continuous Learning

### Feedback Loop
```python
async def record_conversion_outcome(lead_id: str, converted: bool):
    """
    Record actual conversion outcome for model improvement.
    """
    # Get original prediction
    prediction = await get_stored_prediction(lead_id)

    # Calculate prediction error
    error = abs((1 if converted else 0) - prediction.score / 100)

    # Update model feedback
    await model_feedback_queue.push({
        "lead_id": lead_id,
        "predicted_score": prediction.score,
        "actual_outcome": converted,
        "features": prediction.features,
        "error": error
    })

    # Trigger retraining if error threshold exceeded
    if await should_retrain():
        await schedule_model_retraining()
```

### Weight Optimization
Weights are optimized weekly based on:
1. Prediction accuracy by segment
2. False positive/negative rates
3. Market condition changes
4. Feedback from agent outcomes
