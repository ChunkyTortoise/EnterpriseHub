# Property Scoring Algorithm Reference

Comprehensive documentation of the multi-dimensional property scoring system.

## Scoring Overview

The property recommendation engine uses a weighted multi-dimensional scoring algorithm that evaluates properties against buyer preferences across four key dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Budget Fit** | 25% | How well the price matches buyer's budget |
| **Location Match** | 25% | Proximity to preferred areas and amenities |
| **Features Match** | 30% | Alignment with required and preferred features |
| **Lifestyle Match** | 20% | Schools, commute, neighborhood fit |

## Budget Scoring (25%)

### Algorithm

```python
def calculate_budget_score(
    property_price: float,
    preferences: Dict
) -> Tuple[float, str]:
    """
    Calculate budget fit score.

    Scoring Logic:
    - At or under budget: High score (0.8-1.0)
    - Slightly over (5-10%): Moderate score (0.5-0.7)
    - Significantly over (>10%): Low score (0.0-0.5)
    - Way under budget: Slightly reduced (might indicate quality concerns)
    """
    budget_max = preferences.get("budget", {}).get("max", float("inf"))
    budget_target = preferences.get("budget", {}).get("target", budget_max)
    flexibility = preferences.get("budget", {}).get("flexibility", "moderate")

    if property_price <= budget_target:
        # Under target - check if suspiciously low
        ratio = property_price / budget_target
        if ratio < 0.7:
            # More than 30% under - might indicate issues
            score = 0.7 + (ratio * 0.3)
            reason = "Significantly under budget - verify condition"
        else:
            # Sweet spot: at or near target
            score = 0.9 + (ratio * 0.1)
            reason = "Within target budget"

    elif property_price <= budget_max:
        # Between target and max
        over_target = (property_price - budget_target) / budget_target
        score = 0.8 - (over_target * 0.3)
        reason = f"Above target but within max (+{over_target:.0%})"

    else:
        # Over max budget
        over_max = (property_price - budget_max) / budget_max

        if flexibility == "flexible" and over_max <= 0.1:
            score = 0.6 - (over_max * 2)
            reason = f"Slightly over max (+{over_max:.0%}) - stretch opportunity"
        elif flexibility == "moderate" and over_max <= 0.05:
            score = 0.5 - (over_max * 3)
            reason = f"Just over max (+{over_max:.0%})"
        else:
            score = max(0, 0.4 - (over_max * 2))
            reason = f"Over budget (+{over_max:.0%})"

    return round(score, 3), reason
```

### Budget Score Interpretation

| Score Range | Interpretation | Action |
|-------------|----------------|--------|
| 0.9-1.0 | Perfect budget fit | Highlight as excellent value |
| 0.7-0.89 | Good budget fit | Include with confidence |
| 0.5-0.69 | Acceptable stretch | Include with stretch label |
| 0.3-0.49 | Significant stretch | Include only if exceptional match |
| 0.0-0.29 | Out of budget | Exclude unless requested |

## Location Scoring (25%)

### Algorithm

```python
def calculate_location_score(
    property_data: Dict,
    preferences: Dict
) -> Tuple[float, str]:
    """
    Calculate location match score.

    Components:
    - Area match (40%): Is property in preferred area?
    - Commute time (30%): Time to work location
    - Amenities proximity (20%): Distance to key amenities
    - Neighborhood quality (10%): Crime, walkability, etc.
    """
    preferred_locations = preferences.get("locations", [])
    property_neighborhood = property_data.get("neighborhood", "")
    property_city = property_data.get("city", "")

    # Area match (40% of location score)
    area_score = 0.0
    if any(loc["area"].lower() in property_neighborhood.lower()
           for loc in preferred_locations):
        area_score = 1.0
        area_reason = "In preferred area"
    elif any(loc["area"].lower() in property_city.lower()
             for loc in preferred_locations):
        area_score = 0.7
        area_reason = "In preferred city"
    else:
        # Calculate distance-based score
        distances = calculate_distances(
            property_data["coordinates"],
            [loc["area"] for loc in preferred_locations]
        )
        min_distance = min(distances) if distances else float("inf")
        area_score = max(0, 1 - (min_distance / 20))  # 20 mile decay
        area_reason = f"{min_distance:.1f} miles from preferred area"

    # Commute score (30% of location score)
    commute_to = preferences.get("commute_to")
    commute_max = preferences.get("commute_max_minutes", 60)

    if commute_to:
        commute_minutes = estimate_commute(
            property_data["coordinates"],
            commute_to
        )
        if commute_minutes <= commute_max:
            commute_score = 1 - (commute_minutes / commute_max) * 0.3
        else:
            over_ratio = (commute_minutes - commute_max) / commute_max
            commute_score = max(0, 0.7 - over_ratio)
    else:
        commute_score = 0.7  # Neutral if no commute preference

    # Amenities score (20% of location score)
    amenities_score = calculate_amenities_score(
        property_data["coordinates"],
        preferences.get("amenity_preferences", [])
    )

    # Neighborhood quality (10% of location score)
    neighborhood_score = property_data.get("neighborhood_score", 0.7)

    # Weighted combination
    final_score = (
        area_score * 0.4 +
        commute_score * 0.3 +
        amenities_score * 0.2 +
        neighborhood_score * 0.1
    )

    reason = f"{area_reason}; {commute_minutes:.0f}min commute" if commute_to else area_reason

    return round(final_score, 3), reason
```

### Location Components

| Component | Weight | Factors |
|-----------|--------|---------|
| **Area Match** | 40% | In preferred area, adjacent area, distance |
| **Commute** | 30% | Drive time to work, traffic patterns |
| **Amenities** | 20% | Grocery, restaurants, parks, gyms |
| **Neighborhood** | 10% | Safety, walkability, noise level |

## Features Scoring (30%)

### Algorithm

```python
def calculate_features_score(
    property_data: Dict,
    preferences: Dict
) -> Tuple[float, str, List[str], List[str]]:
    """
    Calculate feature match score.

    Categories:
    - Required features: Must have (binary pass/fail)
    - Preferred features: Nice to have (weighted bonus)
    - Avoided features: Deal-breakers (heavy penalty)

    Returns:
        Tuple of (score, reason, highlights, concerns)
    """
    required = preferences.get("features", {}).get("required", [])
    preferred = preferences.get("features", {}).get("preferred", [])
    avoid = preferences.get("features", {}).get("avoid", [])

    property_features = property_data.get("features", [])
    property_features_lower = [f.lower() for f in property_features]

    highlights = []
    concerns = []

    # Check required features (50% of features score)
    required_met = 0
    for feature in required:
        if feature.lower() in property_features_lower:
            required_met += 1
            highlights.append(f"Has required: {feature}")
        else:
            concerns.append(f"Missing required: {feature}")

    if required:
        required_score = required_met / len(required)
    else:
        required_score = 1.0

    # Check preferred features (35% of features score)
    preferred_met = 0
    for feature in preferred:
        if feature.lower() in property_features_lower:
            preferred_met += 1
            highlights.append(f"Has preferred: {feature}")

    if preferred:
        preferred_score = preferred_met / len(preferred)
    else:
        preferred_score = 0.7

    # Check avoided features (15% weight but can eliminate)
    avoided_present = 0
    for feature in avoid:
        if feature.lower() in property_features_lower:
            avoided_present += 1
            concerns.append(f"Has avoided: {feature}")

    if avoid:
        avoid_penalty = avoided_present / len(avoid)
        avoid_score = 1 - avoid_penalty
    else:
        avoid_score = 1.0

    # Bedroom/bathroom matching
    bed_required = preferences.get("bedrooms", {}).get("min", 0)
    bed_ideal = preferences.get("bedrooms", {}).get("ideal", bed_required)
    prop_beds = property_data.get("bedrooms", 0)

    if prop_beds >= bed_ideal:
        bed_score = 1.0
        highlights.append(f"{prop_beds} bedrooms (meets/exceeds ideal)")
    elif prop_beds >= bed_required:
        bed_score = 0.8
        highlights.append(f"{prop_beds} bedrooms (meets minimum)")
    else:
        bed_score = prop_beds / bed_required if bed_required > 0 else 0
        concerns.append(f"Only {prop_beds} bedrooms (need {bed_required})")

    # Square footage matching
    sqft_min = preferences.get("sqft", {}).get("min", 0)
    sqft_ideal = preferences.get("sqft", {}).get("ideal", sqft_min)
    prop_sqft = property_data.get("sqft", 0)

    if prop_sqft >= sqft_ideal:
        sqft_score = 1.0
    elif prop_sqft >= sqft_min:
        sqft_score = 0.7 + 0.3 * ((prop_sqft - sqft_min) / (sqft_ideal - sqft_min))
    else:
        sqft_score = prop_sqft / sqft_min if sqft_min > 0 else 0
        concerns.append(f"{prop_sqft} sqft (want {sqft_min}+)")

    # Weighted combination
    final_score = (
        required_score * 0.35 +
        preferred_score * 0.25 +
        avoid_score * 0.10 +
        bed_score * 0.15 +
        sqft_score * 0.15
    )

    # Heavy penalty if required features missing
    if required and required_score < 1.0:
        final_score *= 0.5

    # Heavy penalty if avoided features present
    if avoid and avoid_score < 1.0:
        final_score *= (0.5 + avoid_score * 0.5)

    reason = f"{required_met}/{len(required)} required, {preferred_met}/{len(preferred)} preferred"

    return round(final_score, 3), reason, highlights, concerns
```

### Feature Categories

| Category | Weight | Impact |
|----------|--------|--------|
| **Required** | 35% + penalty | Missing = 50% score reduction |
| **Preferred** | 25% | Bonus for each match |
| **Avoided** | 10% + penalty | Present = 25-50% reduction |
| **Bedrooms** | 15% | Must meet minimum |
| **Square Feet** | 15% | Must meet minimum |

## Lifestyle Scoring (20%)

### Algorithm

```python
def calculate_lifestyle_score(
    property_data: Dict,
    preferences: Dict
) -> Tuple[float, str]:
    """
    Calculate lifestyle match score.

    Components:
    - School quality (if important)
    - Investment potential (if investor)
    - Neighborhood vibe match
    - Future flexibility
    """
    scores = []
    reasons = []

    # School importance
    school_importance = preferences.get("lifestyle", {}).get("school_importance", 0.5)
    if school_importance > 0.3:
        school_rating = property_data.get("school_rating", 5)
        school_min = preferences.get("school_rating_min", 7)

        if school_rating >= school_min:
            school_score = 0.7 + (school_rating - school_min) / 10 * 0.3
            reasons.append(f"Schools: {school_rating}/10")
        else:
            school_score = school_rating / school_min * 0.7
            reasons.append(f"Schools below preference: {school_rating}/10")

        scores.append((school_score, school_importance))

    # Investment focus
    investment_focus = preferences.get("lifestyle", {}).get("investment_focus", 0)
    if investment_focus > 0.3:
        appreciation = property_data.get("appreciation_potential", 0.05)
        rental_yield = property_data.get("rental_yield", 0.04)

        investment_score = min(1.0, appreciation * 10 + rental_yield * 5)
        scores.append((investment_score, investment_focus))
        reasons.append(f"Investment: {appreciation:.0%} appreciation potential")

    # Neighborhood match
    preferred_vibe = preferences.get("lifestyle", {}).get("neighborhood_type", "suburban")
    property_vibe = property_data.get("neighborhood_type", "suburban")

    if preferred_vibe == property_vibe:
        vibe_score = 1.0
    elif are_vibes_compatible(preferred_vibe, property_vibe):
        vibe_score = 0.7
    else:
        vibe_score = 0.4

    scores.append((vibe_score, 0.3))
    reasons.append(f"Neighborhood: {property_vibe}")

    # Calculate weighted average
    if scores:
        total_weight = sum(w for _, w in scores)
        final_score = sum(s * w for s, w in scores) / total_weight
    else:
        final_score = 0.7  # Neutral default

    return round(final_score, 3), "; ".join(reasons)


def are_vibes_compatible(preferred: str, actual: str) -> bool:
    """Check if neighborhood vibes are compatible."""
    compatibility = {
        "urban": ["urban", "downtown"],
        "suburban": ["suburban", "family"],
        "rural": ["rural", "quiet"],
        "downtown": ["downtown", "urban"],
        "family": ["family", "suburban"],
        "quiet": ["quiet", "rural", "suburban"]
    }
    return actual in compatibility.get(preferred, [])
```

## Final Score Calculation

### Combined Algorithm

```python
def calculate_final_score(
    property_data: Dict,
    preferences: Dict,
    feedback_history: List[Dict] = None
) -> Dict:
    """
    Calculate comprehensive property match score.

    Returns complete scoring breakdown with explanations.
    """
    # Calculate individual dimensions
    budget_score, budget_reason = calculate_budget_score(
        property_data["price"], preferences
    )

    location_score, location_reason = calculate_location_score(
        property_data, preferences
    )

    features_score, features_reason, highlights, concerns = calculate_features_score(
        property_data, preferences
    )

    lifestyle_score, lifestyle_reason = calculate_lifestyle_score(
        property_data, preferences
    )

    # Weighted combination
    base_score = (
        budget_score * 0.25 +
        location_score * 0.25 +
        features_score * 0.30 +
        lifestyle_score * 0.20
    )

    # Apply behavioral boost from feedback
    behavioral_boost = 0.0
    if feedback_history:
        behavioral_boost = calculate_behavioral_boost(
            property_data, feedback_history
        )
        base_score = min(1.0, base_score + behavioral_boost * 0.1)

    # Generate overall reasoning
    reasoning = generate_match_reasoning(
        budget_score, location_score, features_score, lifestyle_score,
        budget_reason, location_reason, features_reason, lifestyle_reason
    )

    return {
        "property_id": property_data.get("id"),
        "match_score": round(base_score, 3),
        "score_breakdown": {
            "budget_fit": budget_score,
            "location_match": location_score,
            "features_match": features_score,
            "lifestyle_match": lifestyle_score,
            "behavioral_boost": behavioral_boost
        },
        "reasoning": {
            "budget": budget_reason,
            "location": location_reason,
            "features": features_reason,
            "lifestyle": lifestyle_reason
        },
        "highlights": highlights,
        "concerns": concerns,
        "match_reasoning": reasoning
    }
```

### Score Interpretation

| Final Score | Classification | Action |
|-------------|----------------|--------|
| 0.85-1.00 | Excellent Match | Prioritize, highlight strongly |
| 0.70-0.84 | Good Match | Include in recommendations |
| 0.55-0.69 | Moderate Match | Include with caveats |
| 0.40-0.54 | Weak Match | Show only if requested |
| 0.00-0.39 | Poor Match | Exclude from results |

## Behavioral Boost

### Learning from Feedback

```python
def calculate_behavioral_boost(
    property_data: Dict,
    feedback_history: List[Dict]
) -> float:
    """
    Calculate bonus score based on similarity to liked properties.

    Boost Factors:
    - Similar to liked: +0.1 to +0.2
    - Similar to offer-made: +0.2 to +0.3
    - Similar to rejected: -0.1 (concern flag)
    """
    boost = 0.0
    property_features = set(property_data.get("features", []))

    for feedback in feedback_history:
        feedback_features = set(feedback.get("property_features", []))
        similarity = len(property_features & feedback_features) / max(
            len(property_features | feedback_features), 1
        )

        if feedback.get("offer_made"):
            boost += similarity * 0.3
        elif feedback.get("liked"):
            boost += similarity * 0.15
        elif feedback.get("rejected"):
            boost -= similarity * 0.1

    return max(-0.2, min(0.3, boost))  # Clamp to reasonable range
```

## Performance Optimization

### Caching Strategy

```python
# Cache expensive calculations
SCORE_CACHE = TTLCache(maxsize=1000, ttl=3600)  # 1 hour TTL

def get_cached_score(property_id: str, preferences_hash: str) -> Optional[Dict]:
    """Retrieve cached score if preferences haven't changed."""
    cache_key = f"{property_id}:{preferences_hash}"
    return SCORE_CACHE.get(cache_key)

def cache_score(property_id: str, preferences_hash: str, score: Dict):
    """Cache score for reuse."""
    cache_key = f"{property_id}:{preferences_hash}"
    SCORE_CACHE[cache_key] = score
```

### Batch Processing

```python
async def score_properties_batch(
    properties: List[Dict],
    preferences: Dict,
    batch_size: int = 50
) -> List[Dict]:
    """
    Score multiple properties efficiently.

    Uses batch processing for database lookups and parallel scoring.
    """
    results = []

    for i in range(0, len(properties), batch_size):
        batch = properties[i:i + batch_size]

        # Parallel scoring
        scores = await asyncio.gather(*[
            asyncio.to_thread(calculate_final_score, prop, preferences)
            for prop in batch
        ])

        results.extend(scores)

    # Sort by score descending
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results
```
