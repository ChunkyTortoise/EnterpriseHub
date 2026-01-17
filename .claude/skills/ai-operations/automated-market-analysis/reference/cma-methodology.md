# CMA Methodology Reference

Comprehensive methodology for Comparative Market Analysis (CMA) generation.

## Overview

A Comparative Market Analysis (CMA) is a systematic approach to estimating a property's market value by comparing it to similar properties that have recently sold, are currently listed, or were listed but didn't sell.

## Comparable Selection Process

### Step 1: Define Search Criteria

```python
DEFAULT_SEARCH_CRITERIA = {
    # Geographic constraints
    "max_distance_miles": 1.5,
    "same_neighborhood_preferred": True,
    "same_subdivision_bonus": 0.1,  # Score boost

    # Physical characteristics
    "sqft_variance_percent": 20,    # +/- 20%
    "bedroom_variance": 1,           # +/- 1 bedroom
    "bathroom_variance": 1,          # +/- 1 bathroom
    "year_built_variance": 15,       # +/- 15 years
    "lot_size_variance_percent": 30, # +/- 30%

    # Temporal constraints
    "sale_recency_months": 6,        # Prefer last 6 months
    "max_sale_age_months": 12,       # Absolute max

    # Quantity requirements
    "min_comps_required": 3,
    "ideal_comps": 5,
    "max_comps": 8
}
```

### Step 2: Score Comparable Quality

```python
def score_comparable(subject: Dict, comp: Dict) -> float:
    """
    Score how comparable a property is to the subject.

    Score Components:
    - Location similarity (30%)
    - Physical characteristics (40%)
    - Sale recency (20%)
    - Property condition (10%)

    Returns: Score 0.0 - 1.0
    """
    scores = {}

    # Location similarity (30%)
    distance = calculate_distance(subject["coordinates"], comp["coordinates"])
    if distance <= 0.5:
        location_score = 1.0
    elif distance <= 1.0:
        location_score = 0.9
    elif distance <= 1.5:
        location_score = 0.7
    else:
        location_score = max(0, 1 - distance / 5)

    # Same subdivision bonus
    if subject.get("subdivision") == comp.get("subdivision"):
        location_score = min(1.0, location_score + 0.1)

    scores["location"] = location_score

    # Physical characteristics (40%)
    sqft_ratio = min(subject["sqft"], comp["sqft"]) / max(subject["sqft"], comp["sqft"])
    sqft_score = sqft_ratio

    bed_diff = abs(subject["bedrooms"] - comp["bedrooms"])
    bed_score = max(0, 1 - bed_diff * 0.3)

    bath_diff = abs(subject["bathrooms"] - comp["bathrooms"])
    bath_score = max(0, 1 - bath_diff * 0.2)

    year_diff = abs(subject["year_built"] - comp["year_built"])
    year_score = max(0, 1 - year_diff / 30)

    scores["physical"] = (sqft_score * 0.4 + bed_score * 0.25 +
                          bath_score * 0.15 + year_score * 0.2)

    # Sale recency (20%)
    months_ago = calculate_months_since(comp["sale_date"])
    if months_ago <= 3:
        recency_score = 1.0
    elif months_ago <= 6:
        recency_score = 0.9
    elif months_ago <= 9:
        recency_score = 0.7
    elif months_ago <= 12:
        recency_score = 0.5
    else:
        recency_score = max(0, 0.5 - (months_ago - 12) / 24)

    scores["recency"] = recency_score

    # Property condition (10%)
    condition_map = {"excellent": 1.0, "good": 0.8, "average": 0.6, "fair": 0.4, "poor": 0.2}
    subject_cond = condition_map.get(subject.get("condition", "average"), 0.6)
    comp_cond = condition_map.get(comp.get("condition", "average"), 0.6)
    condition_score = 1 - abs(subject_cond - comp_cond)
    scores["condition"] = condition_score

    # Weighted total
    total = (
        scores["location"] * 0.30 +
        scores["physical"] * 0.40 +
        scores["recency"] * 0.20 +
        scores["condition"] * 0.10
    )

    return round(total, 3)
```

### Step 3: Rank and Select Comparables

```python
def select_best_comparables(
    subject: Dict,
    candidates: List[Dict],
    min_score: float = 0.6,
    target_count: int = 5
) -> List[Dict]:
    """
    Select the best comparables from candidates.

    Process:
    1. Score all candidates
    2. Filter by minimum score
    3. Sort by score descending
    4. Select top N, ensuring diversity
    """
    # Score all candidates
    scored = []
    for comp in candidates:
        score = score_comparable(subject, comp)
        if score >= min_score:
            scored.append({"property": comp, "score": score})

    # Sort by score
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Select with diversity (avoid all from same street/block)
    selected = []
    street_counts = defaultdict(int)

    for item in scored:
        street = extract_street(item["property"]["address"])

        # Limit to 2 comps from same street
        if street_counts[street] < 2:
            selected.append(item)
            street_counts[street] += 1

        if len(selected) >= target_count:
            break

    return selected
```

## Adjustment Methodology

### Standard Adjustment Factors

```python
# Market-specific adjustments (Austin Metro, 2026)
ADJUSTMENT_FACTORS = {
    # Per-unit adjustments
    "bedroom": {
        "add": 20000,      # Subject has more bedrooms
        "subtract": -15000  # Subject has fewer bedrooms
    },
    "bathroom": {
        "full_bath": 12000,
        "half_bath": 6000
    },
    "garage_space": 10000,   # Per car space

    # Per square foot adjustments
    "sqft": {
        "base_rate": 100,           # Base $/sqft adjustment
        "diminishing_threshold": 500,  # After 500 sqft diff, reduce rate
        "diminishing_rate": 75       # Reduced rate
    },

    # Feature adjustments (lump sum)
    "pool": {
        "inground": 30000,
        "above_ground": 8000
    },
    "updated_kitchen": {
        "full_renovation": 25000,
        "partial_update": 15000
    },
    "updated_bathrooms": {
        "per_bathroom": 12000
    },
    "flooring": {
        "hardwood": 10000,
        "tile": 6000,
        "carpet_to_hard": 8000
    },
    "roof": {
        "new_within_5_years": 8000,
        "needs_replacement": -15000
    },
    "hvac": {
        "new_within_5_years": 5000,
        "needs_replacement": -10000
    },

    # Lot adjustments
    "lot_size": {
        "per_acre_over_standard": 20000,
        "premium_lot": 15000,        # Corner, cul-de-sac, etc.
        "inferior_lot": -10000       # Backing to busy road, etc.
    },

    # Condition adjustments (percentage of value)
    "condition": {
        "excellent_vs_good": 0.03,
        "good_vs_average": 0.02,
        "average_vs_fair": -0.04,
        "fair_vs_poor": -0.06
    },

    # Time adjustments (market appreciation)
    "monthly_appreciation": 0.004,   # 0.4% per month (~5% annual)

    # Location adjustments
    "location_premium": {
        "superior": 0.05,            # Better location than comp
        "inferior": -0.05            # Worse location than comp
    }
}
```

### Adjustment Calculation

```python
def calculate_adjustments(subject: Dict, comp: Dict, market_data: Dict) -> Dict:
    """
    Calculate all adjustments needed to make comp equivalent to subject.

    Rule: Adjust the COMP to match the SUBJECT
    - If subject has more, ADD to comp value
    - If subject has less, SUBTRACT from comp value
    """
    adjustments = {}
    total_adjustment = 0

    # Bedroom adjustment
    bed_diff = subject["bedrooms"] - comp["bedrooms"]
    if bed_diff != 0:
        if bed_diff > 0:
            adj = bed_diff * ADJUSTMENT_FACTORS["bedroom"]["add"]
        else:
            adj = abs(bed_diff) * ADJUSTMENT_FACTORS["bedroom"]["subtract"]
        adjustments["bedrooms"] = adj
        total_adjustment += adj

    # Bathroom adjustment
    bath_diff = subject["bathrooms"] - comp["bathrooms"]
    if bath_diff != 0:
        adj = bath_diff * ADJUSTMENT_FACTORS["bathroom"]["full_bath"]
        adjustments["bathrooms"] = adj
        total_adjustment += adj

    # Square footage adjustment
    sqft_diff = subject["sqft"] - comp["sqft"]
    if abs(sqft_diff) > 100:  # Only adjust if > 100 sqft difference
        if abs(sqft_diff) <= ADJUSTMENT_FACTORS["sqft"]["diminishing_threshold"]:
            rate = ADJUSTMENT_FACTORS["sqft"]["base_rate"]
        else:
            # Blend of base and diminishing rate
            base_portion = ADJUSTMENT_FACTORS["sqft"]["diminishing_threshold"]
            extra_portion = abs(sqft_diff) - base_portion
            rate = (base_portion * ADJUSTMENT_FACTORS["sqft"]["base_rate"] +
                   extra_portion * ADJUSTMENT_FACTORS["sqft"]["diminishing_rate"]) / abs(sqft_diff)

        adj = sqft_diff * rate
        adjustments["sqft"] = int(adj)
        total_adjustment += adj

    # Feature adjustments
    subject_features = set(subject.get("features", []))
    comp_features = set(comp.get("features", []))

    # Subject has features comp doesn't
    for feature in subject_features - comp_features:
        feature_adj = get_feature_adjustment(feature)
        if feature_adj:
            adjustments[f"add_{feature}"] = feature_adj
            total_adjustment += feature_adj

    # Comp has features subject doesn't
    for feature in comp_features - subject_features:
        feature_adj = get_feature_adjustment(feature)
        if feature_adj:
            adjustments[f"sub_{feature}"] = -feature_adj
            total_adjustment -= feature_adj

    # Time adjustment
    months_ago = calculate_months_since(comp["sale_date"])
    if months_ago > 0:
        time_adj = comp["sale_price"] * months_ago * ADJUSTMENT_FACTORS["monthly_appreciation"]
        adjustments["time"] = int(time_adj)
        total_adjustment += time_adj

    # Location adjustment (if applicable)
    location_factor = compare_locations(subject, comp, market_data)
    if location_factor != 0:
        loc_adj = comp["sale_price"] * location_factor
        adjustments["location"] = int(loc_adj)
        total_adjustment += loc_adj

    adjustments["total"] = int(total_adjustment)

    return adjustments
```

## Valuation Calculation

### Reconciliation Process

```python
def calculate_value_estimate(
    subject: Dict,
    comps: List[Dict],
    adjustments: List[Dict]
) -> Dict:
    """
    Calculate final value estimate from adjusted comparables.

    Methods:
    1. Weighted average (by comparability score)
    2. Median of adjusted prices
    3. Range analysis
    """
    adjusted_prices = []

    for i, comp in enumerate(comps):
        adjusted_price = comp["sale_price"] + adjustments[i]["total"]
        comparability = comp.get("comparability_score", 0.7)

        adjusted_prices.append({
            "price": adjusted_price,
            "weight": comparability,
            "price_per_sqft": adjusted_price / subject["sqft"]
        })

    # Weighted average
    total_weight = sum(ap["weight"] for ap in adjusted_prices)
    weighted_avg = sum(ap["price"] * ap["weight"] for ap in adjusted_prices) / total_weight

    # Median
    sorted_prices = sorted(ap["price"] for ap in adjusted_prices)
    median = sorted_prices[len(sorted_prices) // 2]

    # Range
    min_price = min(ap["price"] for ap in adjusted_prices)
    max_price = max(ap["price"] for ap in adjusted_prices)

    # Price per sqft analysis
    avg_ppsf = sum(ap["price_per_sqft"] for ap in adjusted_prices) / len(adjusted_prices)

    # Final estimate (blend of methods)
    # Weighted avg: 50%, Median: 30%, PPSF method: 20%
    ppsf_value = avg_ppsf * subject["sqft"]
    final_estimate = weighted_avg * 0.50 + median * 0.30 + ppsf_value * 0.20

    return {
        "estimated_value": int(round(final_estimate, -3)),  # Round to $1000
        "value_low": int(round(min_price * 0.97, -3)),
        "value_high": int(round(max_price * 1.03, -3)),
        "weighted_average": int(round(weighted_avg, -3)),
        "median": int(round(median, -3)),
        "price_per_sqft": int(round(avg_ppsf)),
        "confidence": calculate_confidence(comps, adjustments)
    }
```

### Confidence Calculation

```python
def calculate_confidence(comps: List[Dict], adjustments: List[Dict]) -> float:
    """
    Calculate confidence level of the CMA estimate.

    Factors that increase confidence:
    - More comparables
    - Higher comparability scores
    - Smaller adjustments
    - Tighter price range
    - Recent sales
    """
    confidence = 0.5  # Base confidence

    # Number of comps bonus
    num_comps = len(comps)
    if num_comps >= 5:
        confidence += 0.15
    elif num_comps >= 3:
        confidence += 0.10

    # Average comparability score
    avg_score = sum(c.get("comparability_score", 0.7) for c in comps) / num_comps
    confidence += (avg_score - 0.7) * 0.5  # Adjust based on quality

    # Adjustment magnitude penalty
    avg_adjustment_pct = sum(
        abs(adj["total"]) / comp["sale_price"]
        for adj, comp in zip(adjustments, comps)
    ) / num_comps

    if avg_adjustment_pct < 0.05:
        confidence += 0.10
    elif avg_adjustment_pct < 0.10:
        confidence += 0.05
    elif avg_adjustment_pct > 0.20:
        confidence -= 0.10

    # Price range tightness
    prices = [c["sale_price"] + adj["total"] for c, adj in zip(comps, adjustments)]
    range_pct = (max(prices) - min(prices)) / ((max(prices) + min(prices)) / 2)

    if range_pct < 0.05:
        confidence += 0.10
    elif range_pct < 0.10:
        confidence += 0.05
    elif range_pct > 0.20:
        confidence -= 0.10

    # Recency bonus
    avg_months = sum(
        calculate_months_since(c["sale_date"]) for c in comps
    ) / num_comps

    if avg_months <= 3:
        confidence += 0.10
    elif avg_months <= 6:
        confidence += 0.05
    elif avg_months > 9:
        confidence -= 0.05

    return max(0.3, min(0.95, confidence))
```

## Quality Control Checks

### Adjustment Reasonability

```python
ADJUSTMENT_LIMITS = {
    "max_single_adjustment_pct": 0.10,  # No single adjustment > 10% of value
    "max_total_adjustment_pct": 0.25,   # Total adjustments < 25%
    "max_adjustments_count": 8,          # Don't make more than 8 adjustments
    "required_comparability": 0.55       # Minimum comp score to use
}

def validate_adjustments(comp: Dict, adjustments: Dict) -> List[str]:
    """Validate adjustments are within reasonable limits."""
    warnings = []
    sale_price = comp["sale_price"]

    # Check single adjustments
    for key, value in adjustments.items():
        if key == "total":
            continue
        if abs(value) / sale_price > ADJUSTMENT_LIMITS["max_single_adjustment_pct"]:
            warnings.append(f"Large adjustment for {key}: {value:,} ({abs(value)/sale_price:.1%})")

    # Check total adjustments
    total_pct = abs(adjustments["total"]) / sale_price
    if total_pct > ADJUSTMENT_LIMITS["max_total_adjustment_pct"]:
        warnings.append(f"High total adjustment: {total_pct:.1%}")

    # Check adjustment count
    adj_count = len([k for k in adjustments.keys() if k != "total" and adjustments[k] != 0])
    if adj_count > ADJUSTMENT_LIMITS["max_adjustments_count"]:
        warnings.append(f"Many adjustments needed: {adj_count}")

    return warnings
```

## Best Practices

### Do's

1. **Use recent sales** - Prioritize sales within 3 months
2. **Verify data** - Confirm sale prices and dates from MLS
3. **Walk the neighborhood** - Understand location nuances
4. **Consider market trends** - Adjust for appreciating/depreciating markets
5. **Document reasoning** - Explain each adjustment clearly

### Don'ts

1. **Over-adjust** - Keep total adjustments under 25%
2. **Ignore negatives** - Include comps that sold below asking
3. **Cherry-pick comps** - Select objectively, not to hit target value
4. **Use foreclosures blindly** - Note distressed sales separately
5. **Skip verification** - Always verify MLS data accuracy
