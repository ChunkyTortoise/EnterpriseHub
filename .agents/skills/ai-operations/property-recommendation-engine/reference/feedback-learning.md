# Feedback Learning Reference

Continuous improvement system for property recommendations based on user feedback.

## Learning System Overview

The feedback learning system captures showing outcomes and adjusts recommendation weights to improve future matches. This creates a virtuous cycle where each interaction makes recommendations more accurate.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Feedback Learning Loop                        │
│                                                                  │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │ Recommend│ -> │  Show   │ -> │ Collect │ -> │ Update  │      │
│  │ Property │    │ Property│    │ Feedback│    │ Weights │      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
│       ^                                              │           │
│       └──────────────────────────────────────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Feedback Types

### 1. Implicit Feedback

Automatically captured without user action:

```python
@dataclass
class ImplicitFeedback:
    property_id: str
    lead_id: str
    timestamp: str

    # Engagement metrics
    view_count: int          # How many times viewed
    view_duration_seconds: int  # Time spent on listing
    saved_to_favorites: bool
    shared_with_others: bool
    requested_more_info: bool
    clicked_map: bool
    clicked_photos: int      # Number of photos viewed

    # Comparison behavior
    compared_to_other: bool
    comparison_properties: List[str]

    # Return behavior
    return_visits: int       # Came back to view again
    days_between_visits: List[int]
```

### 2. Explicit Feedback

Directly provided by the lead or agent:

```python
@dataclass
class ExplicitFeedback:
    property_id: str
    lead_id: str
    timestamp: str
    feedback_source: str  # "lead", "agent", "system"

    # Showing outcome
    viewed_in_person: bool
    liked: bool
    offer_made: bool
    offer_accepted: bool

    # Detailed feedback
    rating: Optional[int]  # 1-5 stars
    objections: List[str]  # Why they didn't like it
    interests: List[str]   # What they did like
    comments: Optional[str]

    # Comparative feedback
    better_than: List[str]  # Property IDs this was better than
    worse_than: List[str]   # Property IDs this was worse than
```

### 3. Outcome Feedback

Final transaction outcomes:

```python
@dataclass
class OutcomeFeedback:
    lead_id: str
    property_id: str
    outcome: str  # "purchased", "lost_to_competitor", "chose_different", "still_looking"

    # If purchased
    final_price: Optional[float]
    days_to_close: Optional[int]
    satisfaction_score: Optional[int]

    # If not purchased
    reason_not_purchased: Optional[str]
    what_they_chose_instead: Optional[Dict]
```

## Weight Adjustment Algorithm

### Core Learning Algorithm

```python
class FeedbackLearner:
    """
    Adjusts preference weights based on feedback.

    Learning rates:
    - Explicit positive (liked): 0.1
    - Explicit negative (rejected): 0.05
    - Offer made: 0.2 (strong signal)
    - Purchase: 0.3 (strongest signal)
    """

    LEARNING_RATES = {
        "implicit_positive": 0.03,
        "implicit_negative": 0.02,
        "explicit_liked": 0.10,
        "explicit_rejected": 0.05,
        "offer_made": 0.20,
        "offer_accepted": 0.25,
        "purchased": 0.30
    }

    def update_weights(
        self,
        lead_id: str,
        feedback: Union[ImplicitFeedback, ExplicitFeedback, OutcomeFeedback]
    ) -> Dict:
        """
        Update preference weights based on feedback.

        Algorithm:
        1. Determine signal type and strength
        2. Extract features from feedback property
        3. Adjust weights up/down based on outcome
        4. Normalize weights to sum to 1.0
        5. Apply regularization to prevent overfitting
        """
        current_weights = self.load_weights(lead_id)
        property_features = self.get_property_features(feedback.property_id)

        # Determine learning rate and direction
        lr, direction = self._classify_feedback(feedback)

        # Update feature weights
        updated_weights = self._apply_updates(
            current_weights, property_features, lr, direction
        )

        # Normalize and regularize
        final_weights = self._normalize_and_regularize(updated_weights)

        # Save updated weights
        self.save_weights(lead_id, final_weights)

        return {
            "lead_id": lead_id,
            "previous_weights": current_weights,
            "updated_weights": final_weights,
            "learning_rate_used": lr,
            "direction": direction
        }

    def _classify_feedback(
        self,
        feedback: Union[ImplicitFeedback, ExplicitFeedback, OutcomeFeedback]
    ) -> Tuple[float, str]:
        """Classify feedback into learning rate and direction."""

        if isinstance(feedback, OutcomeFeedback):
            if feedback.outcome == "purchased":
                return self.LEARNING_RATES["purchased"], "positive"
            elif feedback.outcome == "chose_different":
                return self.LEARNING_RATES["explicit_rejected"], "negative"

        elif isinstance(feedback, ExplicitFeedback):
            if feedback.offer_accepted:
                return self.LEARNING_RATES["offer_accepted"], "positive"
            elif feedback.offer_made:
                return self.LEARNING_RATES["offer_made"], "positive"
            elif feedback.liked:
                return self.LEARNING_RATES["explicit_liked"], "positive"
            else:
                return self.LEARNING_RATES["explicit_rejected"], "negative"

        elif isinstance(feedback, ImplicitFeedback):
            # Calculate implicit signal strength
            engagement_score = self._calculate_engagement(feedback)
            if engagement_score > 0.7:
                return self.LEARNING_RATES["implicit_positive"], "positive"
            elif engagement_score < 0.3:
                return self.LEARNING_RATES["implicit_negative"], "negative"

        return 0.0, "neutral"

    def _apply_updates(
        self,
        weights: Dict,
        features: Dict,
        learning_rate: float,
        direction: str
    ) -> Dict:
        """Apply weight updates based on feedback."""
        updated = weights.copy()
        multiplier = 1.0 if direction == "positive" else -1.0

        for feature_category, feature_values in features.items():
            if feature_category in updated:
                # Update existing weight
                current = updated[feature_category]
                adjustment = learning_rate * multiplier

                if direction == "positive":
                    # Increase weight, bounded by 1.0
                    updated[feature_category] = min(1.0, current * (1 + adjustment))
                else:
                    # Decrease weight, bounded by 0.1
                    updated[feature_category] = max(0.1, current * (1 - adjustment))

        return updated

    def _normalize_and_regularize(self, weights: Dict) -> Dict:
        """Normalize weights to sum to 1.0 and apply regularization."""
        # Normalize
        total = sum(weights.values())
        normalized = {k: v / total for k, v in weights.items()}

        # Apply L2 regularization to prevent extreme weights
        regularization_factor = 0.01
        mean_weight = 1.0 / len(normalized)

        regularized = {}
        for k, v in normalized.items():
            # Pull weights toward mean
            regularized[k] = v + regularization_factor * (mean_weight - v)

        # Re-normalize after regularization
        total = sum(regularized.values())
        return {k: round(v / total, 4) for k, v in regularized.items()}
```

## Feature Importance Learning

### Identifying Important Features

```python
def learn_feature_importance(
    lead_id: str,
    feedback_history: List[ExplicitFeedback]
) -> Dict[str, float]:
    """
    Learn which features are most important to this lead.

    Uses feedback correlation to identify features that
    correlate with positive/negative outcomes.
    """
    feature_outcomes = defaultdict(list)

    for feedback in feedback_history:
        property_features = get_property_features(feedback.property_id)
        outcome = 1.0 if feedback.liked else 0.0
        if feedback.offer_made:
            outcome = 1.5
        if hasattr(feedback, 'offer_accepted') and feedback.offer_accepted:
            outcome = 2.0

        for feature in property_features:
            feature_outcomes[feature].append(outcome)

    # Calculate feature importance as average outcome correlation
    importance = {}
    for feature, outcomes in feature_outcomes.items():
        if len(outcomes) >= 2:  # Need at least 2 data points
            avg_outcome = sum(outcomes) / len(outcomes)
            # Normalize to 0-1 range
            importance[feature] = min(1.0, avg_outcome / 2.0)

    return importance
```

### Objection Pattern Recognition

```python
def learn_from_objections(
    lead_id: str,
    objection_history: List[Dict]
) -> Dict:
    """
    Learn from stated objections to prevent future mismatches.

    Objection Categories:
    - Price-related: Adjust budget sensitivity
    - Size-related: Adjust space requirements
    - Location-related: Adjust location priorities
    - Feature-related: Add to avoid list
    - Condition-related: Adjust quality expectations
    """
    objection_patterns = {
        "price": [],
        "size": [],
        "location": [],
        "features": [],
        "condition": []
    }

    price_keywords = ["expensive", "price", "afford", "budget", "cost"]
    size_keywords = ["small", "big", "space", "room", "sqft", "yard"]
    location_keywords = ["far", "commute", "neighborhood", "area", "schools"]
    condition_keywords = ["old", "dated", "needs work", "renovation", "condition"]

    for objection_record in objection_history:
        for objection in objection_record.get("objections", []):
            objection_lower = objection.lower()

            if any(kw in objection_lower for kw in price_keywords):
                objection_patterns["price"].append(objection)
            elif any(kw in objection_lower for kw in size_keywords):
                objection_patterns["size"].append(objection)
            elif any(kw in objection_lower for kw in location_keywords):
                objection_patterns["location"].append(objection)
            elif any(kw in objection_lower for kw in condition_keywords):
                objection_patterns["condition"].append(objection)
            else:
                objection_patterns["features"].append(objection)

    # Generate preference adjustments
    adjustments = {}

    if len(objection_patterns["price"]) >= 2:
        adjustments["increase_budget_weight"] = True
        adjustments["reduce_max_price"] = 0.05  # 5% reduction

    if len(objection_patterns["size"]) >= 2:
        adjustments["increase_size_minimum"] = True

    if len(objection_patterns["location"]) >= 2:
        adjustments["tighten_location_constraint"] = True

    return {
        "objection_patterns": objection_patterns,
        "suggested_adjustments": adjustments
    }
```

## Feedback Collection Strategies

### Automated Collection Points

```python
COLLECTION_TRIGGERS = {
    # Implicit collection
    "page_view": {
        "trigger": "property_detail_viewed",
        "delay_seconds": 0,
        "data": ["view_duration", "photos_clicked", "map_clicked"]
    },
    "engagement": {
        "trigger": "property_saved_or_shared",
        "delay_seconds": 0,
        "data": ["action_type", "shared_with"]
    },
    "return_visit": {
        "trigger": "same_property_viewed_again",
        "delay_seconds": 0,
        "data": ["days_since_last_view", "visit_count"]
    },

    # Explicit collection
    "post_showing": {
        "trigger": "showing_completed",
        "delay_hours": 2,
        "method": "sms_or_email",
        "questions": [
            "Did you like the property? (1-5 stars)",
            "What did you like most?",
            "What concerns do you have?"
        ]
    },
    "weekly_summary": {
        "trigger": "weekly_schedule",
        "method": "email",
        "questions": [
            "Which properties from this week interested you most?",
            "Are we on the right track with recommendations?"
        ]
    },

    # Outcome collection
    "offer_made": {
        "trigger": "offer_submitted",
        "delay_seconds": 0,
        "data": ["offer_amount", "property_id", "competing_offers"]
    },
    "purchase_complete": {
        "trigger": "closing_complete",
        "delay_days": 7,
        "method": "email",
        "questions": [
            "How satisfied are you? (1-10)",
            "What could we have done better?",
            "Would you recommend us?"
        ]
    }
}
```

### Feedback Quality Scoring

```python
def score_feedback_quality(feedback: Dict) -> float:
    """
    Score the quality/usefulness of feedback for learning.

    High quality feedback:
    - Explicit and detailed
    - Recent
    - From outcome events (purchases, offers)
    - Includes specific reasons

    Low quality feedback:
    - Implicit only
    - Old
    - No specific details
    """
    score = 0.0

    # Feedback type weight
    if feedback.get("outcome"):
        score += 0.4  # Outcomes are most valuable
    elif feedback.get("explicit"):
        score += 0.3
    else:
        score += 0.1  # Implicit only

    # Specificity bonus
    if feedback.get("objections") or feedback.get("interests"):
        score += 0.2
    if feedback.get("comments"):
        score += 0.1

    # Recency bonus
    days_old = (datetime.now() - parse_date(feedback["timestamp"])).days
    if days_old <= 7:
        score += 0.2
    elif days_old <= 30:
        score += 0.1

    return min(1.0, score)
```

## Learning Metrics

### Model Performance Tracking

```python
@dataclass
class LearningMetrics:
    lead_id: str
    period: str  # "weekly", "monthly", "all_time"

    # Accuracy metrics
    recommendations_made: int
    recommendations_liked: int
    recommendations_viewed: int
    offers_from_recommendations: int

    # Learning progress
    preference_stability: float  # How much weights changed
    prediction_accuracy: float   # Liked rate for high-scored properties

    # Improvement over time
    accuracy_trend: str  # "improving", "stable", "declining"
    average_match_score_of_liked: float


def calculate_learning_effectiveness(lead_id: str) -> LearningMetrics:
    """Calculate how well the learning system is performing."""
    feedback_history = load_feedback_history(lead_id)
    recommendation_history = load_recommendation_history(lead_id)

    # Calculate hit rate: liked / recommended
    liked_count = sum(1 for f in feedback_history if f.get("liked"))
    recommended_count = len(recommendation_history)

    # Calculate accuracy: did high scores correlate with likes?
    high_score_liked = sum(
        1 for r in recommendation_history
        if r["match_score"] > 0.7 and was_liked(r["property_id"], feedback_history)
    )
    high_score_count = sum(1 for r in recommendation_history if r["match_score"] > 0.7)

    prediction_accuracy = high_score_liked / high_score_count if high_score_count > 0 else 0

    return LearningMetrics(
        lead_id=lead_id,
        period="all_time",
        recommendations_made=recommended_count,
        recommendations_liked=liked_count,
        recommendations_viewed=len(feedback_history),
        offers_from_recommendations=sum(1 for f in feedback_history if f.get("offer_made")),
        preference_stability=calculate_weight_stability(lead_id),
        prediction_accuracy=prediction_accuracy,
        accuracy_trend=calculate_trend(lead_id),
        average_match_score_of_liked=calculate_avg_score_of_liked(lead_id, feedback_history)
    )
```

## Best Practices

### Do's

1. **Collect feedback at natural points** - After showings, not during
2. **Weight recent feedback higher** - Preferences evolve
3. **Combine implicit and explicit** - Neither alone is complete
4. **Track confidence levels** - Know when to trust the model
5. **Allow manual overrides** - Agents can adjust weights

### Don'ts

1. **Don't over-learn from single feedback** - Use regularization
2. **Don't ignore negative feedback** - It's often more informative
3. **Don't assume stability** - Re-evaluate weights periodically
4. **Don't ignore context** - Market conditions affect preferences
5. **Don't forget cold start** - New leads need different handling

## Cold Start Strategy

```python
def handle_cold_start(lead_id: str, initial_preferences: Dict) -> Dict:
    """
    Handle new leads with no feedback history.

    Strategy:
    1. Use segment-based defaults
    2. Apply demographic heuristics
    3. Use conservative weights
    4. Prioritize exploration
    """
    segment = classify_lead_segment(initial_preferences)

    # Load segment defaults
    segment_weights = SEGMENT_DEFAULTS.get(segment, DEFAULT_WEIGHTS)

    # Apply demographic adjustments
    if initial_preferences.get("has_children"):
        segment_weights["school_importance"] *= 1.3

    if initial_preferences.get("investor"):
        segment_weights["investment_focus"] *= 1.5

    # Conservative confidence
    for key in segment_weights:
        segment_weights[key] = segment_weights[key] * 0.8 + 0.2 / len(segment_weights)

    return {
        "weights": segment_weights,
        "confidence": "low",
        "strategy": "exploration_priority",
        "segment": segment
    }
```
