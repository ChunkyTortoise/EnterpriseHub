# Preference Extraction Reference

Guide for extracting buyer preferences from conversations and behavioral data.

## Extraction Sources

### 1. Explicit Preferences (Direct Statements)

**Budget Expressions**
```
Pattern: "budget is $X", "can afford $X", "spending up to $X", "max $X"
Confidence: High (0.9)

Examples:
- "Our budget is around $750,000" → budget: {target: 750000, flexibility: "moderate"}
- "We can't go over $500K" → budget: {max: 500000, flexibility: "firm"}
- "Ideally under $600K but could stretch to $650K" → budget: {target: 600000, max: 650000, flexibility: "flexible"}
```

**Location Preferences**
```
Pattern: "looking in [area]", "want to be near [landmark]", "school district"
Confidence: High (0.9)

Examples:
- "We want to be in Round Rock" → locations: ["Round Rock"], priority: 1
- "Near downtown but not in it" → locations: ["Downtown Adjacent"], exclude: ["Downtown Core"]
- "Good schools are a must" → school_priority: "high", school_rating_min: 8
```

**Feature Requirements**
```
Pattern: "need X bedrooms", "must have [feature]", "can't live without"
Confidence: High (0.9)

Examples:
- "Need at least 4 bedrooms" → bedrooms: {min: 4}
- "Must have a pool" → features_required: ["pool"]
- "Home office is essential" → features_required: ["home_office"]
```

### 2. Implicit Preferences (Behavioral Signals)

**Viewing Patterns**
```python
def extract_from_viewing_behavior(viewing_history: List[Dict]) -> Dict:
    """
    Infer preferences from properties viewed.

    Signal Strength:
    - Viewed 3+ times: Strong preference
    - Viewed 2 times: Moderate preference
    - Viewed 1 time: Weak signal
    """
    feature_counts = defaultdict(int)
    price_range = {"min": float("inf"), "max": 0}

    for view in viewing_history:
        # Track price range actually viewed
        price_range["min"] = min(price_range["min"], view["price"])
        price_range["max"] = max(price_range["max"], view["price"])

        # Count feature occurrences
        for feature in view.get("features", []):
            feature_counts[feature] += view.get("view_count", 1)

    # Features viewed 3+ times are likely important
    inferred_preferences = {
        feature: count for feature, count in feature_counts.items()
        if count >= 3
    }

    return {
        "inferred_price_range": price_range,
        "inferred_features": inferred_preferences,
        "confidence": "medium"
    }
```

**Time Spent Analysis**
```python
def analyze_time_patterns(engagement_data: List[Dict]) -> Dict:
    """
    Longer time spent indicates higher interest.

    Thresholds:
    - > 5 minutes: High interest
    - 2-5 minutes: Moderate interest
    - < 2 minutes: Low interest / browsing
    """
    high_interest_features = []

    for engagement in engagement_data:
        if engagement["time_seconds"] > 300:  # 5+ minutes
            high_interest_features.extend(
                engagement.get("property_features", [])
            )

    return {
        "high_interest_features": list(set(high_interest_features)),
        "confidence": "medium"
    }
```

**Question Analysis**
```python
def extract_from_questions(questions: List[str]) -> Dict:
    """
    Questions reveal priorities and concerns.

    Question Categories:
    - Price/financing questions → Budget sensitivity
    - School questions → Family-focused
    - Commute questions → Location priority
    - Feature questions → Specific requirements
    """
    priorities = {}

    school_patterns = ["school", "district", "education", "kids"]
    commute_patterns = ["commute", "traffic", "work", "downtown"]
    price_patterns = ["price", "cost", "afford", "payment", "rate"]

    for question in questions:
        q_lower = question.lower()

        if any(p in q_lower for p in school_patterns):
            priorities["school_importance"] = priorities.get("school_importance", 0) + 1
        if any(p in q_lower for p in commute_patterns):
            priorities["commute_sensitivity"] = priorities.get("commute_sensitivity", 0) + 1
        if any(p in q_lower for p in price_patterns):
            priorities["budget_sensitivity"] = priorities.get("budget_sensitivity", 0) + 1

    return {
        "inferred_priorities": priorities,
        "confidence": "medium"
    }
```

### 3. Feedback-Based Preferences

**Post-Showing Feedback**
```python
def update_preferences_from_feedback(
    current_preferences: Dict,
    feedback: Dict
) -> Dict:
    """
    Adjust preferences based on showing feedback.

    Feedback Types:
    - liked: Reinforce matching features
    - disliked: Add to negative preferences
    - offer_made: Strong signal for all features
    """
    updated = current_preferences.copy()

    if feedback.get("liked"):
        property_features = feedback.get("property_features", [])
        for feature in property_features:
            current_weight = updated.get("feature_weights", {}).get(feature, 0.5)
            updated.setdefault("feature_weights", {})[feature] = min(1.0, current_weight * 1.2)

    if feedback.get("objections"):
        for objection in feedback["objections"]:
            # Add to negative preferences
            updated.setdefault("negative_preferences", []).append(objection)

    if feedback.get("interests"):
        for interest in feedback["interests"]:
            updated.setdefault("discovered_interests", []).append(interest)

    return updated
```

## Preference Weighting

### Weight Assignment Algorithm

```python
PREFERENCE_WEIGHTS = {
    # Source-based weights
    "explicit_statement": 1.0,      # Direct from lead
    "repeated_question": 0.8,       # Asked multiple times
    "viewing_behavior": 0.6,        # Inferred from views
    "time_spent": 0.5,              # Engagement time
    "feedback_positive": 0.9,       # Liked properties
    "feedback_negative": 0.95,      # Disliked (important to avoid)

    # Recency weights (decay over time)
    "last_7_days": 1.0,
    "last_30_days": 0.8,
    "last_90_days": 0.5,
    "older": 0.3
}

def calculate_preference_weight(
    preference: Dict,
    source: str,
    days_ago: int
) -> float:
    """Calculate final weight for a preference."""
    base_weight = PREFERENCE_WEIGHTS.get(source, 0.5)

    # Apply recency decay
    if days_ago <= 7:
        recency_factor = PREFERENCE_WEIGHTS["last_7_days"]
    elif days_ago <= 30:
        recency_factor = PREFERENCE_WEIGHTS["last_30_days"]
    elif days_ago <= 90:
        recency_factor = PREFERENCE_WEIGHTS["last_90_days"]
    else:
        recency_factor = PREFERENCE_WEIGHTS["older"]

    return base_weight * recency_factor
```

### Confidence Levels

| Confidence | Description | Use Case |
|------------|-------------|----------|
| **High** (0.8-1.0) | Explicit statement, repeated, recent | Use as hard constraint |
| **Medium** (0.5-0.7) | Behavioral inference, moderate recency | Use as soft preference |
| **Low** (0.2-0.4) | Single observation, old data | Use for exploration |

## Preference Categories

### Must-Haves (Hard Constraints)
Properties MUST meet these to be shown:
- Minimum bedrooms
- Maximum budget
- Required location(s)
- Deal-breaker features to avoid

### Nice-to-Haves (Soft Preferences)
Properties are scored higher with these:
- Preferred features
- Ideal neighborhood
- Style preferences
- Amenities

### Stretch Opportunities
Worth showing despite exceeding preferences:
- Slightly over budget but exceptional value
- Outside preferred area but better features
- Missing one nice-to-have but exceeding others

## Extraction Pipeline

```python
def extract_comprehensive_preferences(
    lead_id: str,
    conversations: List[Dict],
    viewing_history: List[Dict],
    feedback_history: List[Dict]
) -> Dict:
    """
    Complete preference extraction pipeline.

    Returns:
        {
            "explicit": {...},      # Direct statements
            "inferred": {...},      # Behavioral inference
            "feedback_adjusted": {...},  # Post-feedback updates
            "weighted": {...},      # Final weighted preferences
            "confidence_scores": {...}  # Per-preference confidence
        }
    """
    # Step 1: Extract explicit preferences
    explicit = extract_explicit_preferences(conversations)

    # Step 2: Infer from behavior
    behavioral = extract_from_viewing_behavior(viewing_history)
    time_based = analyze_time_patterns(viewing_history)
    question_based = extract_from_questions(
        extract_questions(conversations)
    )

    # Step 3: Combine inferred preferences
    inferred = merge_inferred_preferences([
        behavioral, time_based, question_based
    ])

    # Step 4: Apply feedback adjustments
    feedback_adjusted = explicit.copy()
    for feedback in feedback_history:
        feedback_adjusted = update_preferences_from_feedback(
            feedback_adjusted, feedback
        )

    # Step 5: Calculate final weighted preferences
    weighted = calculate_weighted_preferences(
        explicit, inferred, feedback_adjusted
    )

    # Step 6: Assign confidence scores
    confidence_scores = calculate_confidence_scores(
        explicit, inferred, feedback_adjusted
    )

    return {
        "explicit": explicit,
        "inferred": inferred,
        "feedback_adjusted": feedback_adjusted,
        "weighted": weighted,
        "confidence_scores": confidence_scores,
        "extracted_at": datetime.now().isoformat()
    }
```

## Best Practices

1. **Start with explicit** - Always prioritize direct statements
2. **Validate inferences** - Confirm behavioral inferences when possible
3. **Track changes** - Monitor preference evolution over time
4. **Handle conflicts** - Recent explicit > old explicit > inferred
5. **Respect negatives** - Negative preferences are more reliable than positive

## Output Schema

```json
{
  "lead_id": "string",
  "preferences": {
    "budget": {
      "min": 0,
      "target": 0,
      "max": 0,
      "flexibility": "firm|moderate|flexible",
      "confidence": 0.0-1.0,
      "source": "explicit|inferred|feedback"
    },
    "locations": [
      {
        "area": "string",
        "priority": 1-5,
        "confidence": 0.0-1.0
      }
    ],
    "features": {
      "required": ["string"],
      "preferred": ["string"],
      "avoid": ["string"]
    },
    "property_type": ["single_family", "condo", "townhouse"],
    "lifestyle": {
      "school_importance": 0.0-1.0,
      "commute_sensitivity": 0.0-1.0,
      "investment_focus": 0.0-1.0
    }
  },
  "metadata": {
    "extracted_at": "ISO8601",
    "last_updated": "ISO8601",
    "data_sources": ["conversations", "viewings", "feedback"],
    "overall_confidence": 0.0-1.0
  }
}
```
