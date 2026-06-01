# Automated Market Analysis

Real-time market intelligence and automated CMA (Comparative Market Analysis) generation.

## Description

Provide comprehensive market analysis including competitive market analysis (CMA), price trend predictions, investment opportunity detection, and automated market report generation. This skill combines real estate data APIs with AI analysis to deliver actionable market intelligence.

## Triggers

- "generate CMA"
- "analyze market trends"
- "detect investment opportunities"
- "create market report"
- "market analysis"
- "property valuation"
- "comparable sales"

## Model Configuration

- **Model**: sonnet (balanced analysis)
- **Thinking**: enabled for trend analysis
- **Temperature**: 0.3 (consistent analytical output)

## Workflow

### Phase 1: Data Collection
```
1. Fetch subject property details
2. Identify comparable properties
   - Same neighborhood/area
   - Similar size (+/- 20%)
   - Similar age (+/- 10 years)
   - Similar features

3. Gather market data
   - Recent sales (last 6 months)
   - Active listings
   - Days on market trends
   - Price per sqft trends
```

### Phase 2: Comparable Analysis
```
1. Score comparability of each comp
2. Apply adjustments
   - Location adjustments
   - Condition adjustments
   - Feature adjustments
   - Time adjustments

3. Calculate adjusted sale prices
```

### Phase 3: Market Trend Analysis
```
1. Analyze price trends
   - Month-over-month changes
   - Year-over-year appreciation
   - Seasonal patterns

2. Assess market conditions
   - Inventory levels
   - Days on market trends
   - List-to-sale price ratios
   - Buyer vs seller market indicators
```

### Phase 4: Report Generation
```
1. Compile CMA report
2. Generate valuation range
3. Create market summary
4. Identify investment opportunities
```

## Scripts (Zero-Context Execution)

### scripts/fetch-comparables.py
Fetches comparable properties for CMA analysis.
```bash
python scripts/fetch-comparables.py --address "123 Main St, Rancho Cucamonga, CA" --radius 1
```

### scripts/generate-cma-report.py
Generates complete CMA report.
```bash
python scripts/generate-cma-report.py --property-id <id> --output pdf|json
```

### scripts/analyze-market-trends.py
Analyzes market trends for an area.
```bash
python scripts/analyze-market-trends.py --area "Teravista" --period 12
```

### scripts/detect-opportunities.py
Detects investment opportunities in the market.
```bash
python scripts/detect-opportunities.py --criteria <criteria.json>
```

## References

- @reference/cma-methodology.md - CMA calculation standards
- @reference/adjustment-factors.md - Property adjustment guidelines
- @reference/market-indicators.md - Market condition indicators
- @reference/valuation-models.md - Valuation model documentation

## Integration Points

### Primary Services
```python
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
from ghl_real_estate_ai.services.competitive_intelligence import CompetitiveIntelligenceService
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
```

### Data Sources
- **MLS Data**: Property listings and sales (via API)
- **Public Records**: Tax assessments, sale history
- **Market Data**: Trends, inventory, pricing

### Output Destinations
- **PDF Reports**: Professional CMA documents
- **GHL Notes**: Market insights attached to contacts
- **Email Delivery**: Automated report distribution

## Example Usage

### Generate CMA Report
```python
from ghl_real_estate_ai.services.market_analysis import MarketAnalysisService

analysis = MarketAnalysisService()

# Generate CMA for subject property
cma = await analysis.generate_cma(
    subject_property={
        "address": "123 Teravista Pkwy, Round Rock, TX",
        "bedrooms": 4,
        "bathrooms": 3,
        "sqft": 2800,
        "year_built": 2018,
        "features": ["pool", "updated kitchen"]
    },
    comp_radius_miles=1.5,
    sale_period_months=6
)

print(f"Estimated Value: ${cma.estimated_value:,}")
print(f"Value Range: ${cma.value_low:,} - ${cma.value_high:,}")
print(f"Confidence: {cma.confidence:.0%}")
```

### Analyze Market Trends
```python
# Get market trends for an area
trends = await analysis.analyze_market_trends(
    area="Teravista",
    metrics=["median_price", "days_on_market", "inventory", "appreciation"]
)

print(f"Median Price: ${trends.median_price:,}")
print(f"YoY Appreciation: {trends.yoy_appreciation:.1%}")
print(f"Days on Market: {trends.avg_dom}")
print(f"Market Type: {trends.market_type}")  # buyer's / seller's / balanced
```

### Detect Investment Opportunities
```python
# Find undervalued properties
opportunities = await analysis.find_investment_opportunities(
    area="Rancho Cucamonga Metro",
    criteria={
        "min_discount_percent": 5,
        "max_dom": 30,
        "min_cap_rate": 0.06,
        "property_types": ["single_family", "multi_family"]
    }
)

for opp in opportunities:
    print(f"{opp.address}: {opp.discount_percent:.1f}% below market")
    print(f"  Estimated rental yield: {opp.estimated_cap_rate:.1%}")
```

## Output Schema

### CMA Report
```json
{
  "report_id": "string",
  "subject_property": {
    "address": "string",
    "details": {...}
  },
  "valuation": {
    "estimated_value": 0,
    "value_low": 0,
    "value_high": 0,
    "confidence": 0.0-1.0,
    "price_per_sqft": 0
  },
  "comparables": [
    {
      "address": "string",
      "sale_price": 0,
      "sale_date": "ISO8601",
      "adjusted_price": 0,
      "comparability_score": 0.0-1.0,
      "adjustments": {
        "location": 0,
        "condition": 0,
        "features": 0,
        "time": 0
      },
      "distance_miles": 0.0
    }
  ],
  "market_analysis": {
    "median_price": 0,
    "avg_dom": 0,
    "inventory_months": 0.0,
    "list_to_sale_ratio": 0.0,
    "market_type": "buyer|seller|balanced",
    "trend": "appreciating|stable|depreciating"
  },
  "recommendations": {
    "listing_price": 0,
    "price_strategy": "string",
    "timing_advice": "string"
  },
  "generated_at": "ISO8601"
}
```

### Market Trends
```json
{
  "area": "string",
  "period_months": 0,
  "metrics": {
    "median_price": {
      "current": 0,
      "previous": 0,
      "change_percent": 0.0
    },
    "days_on_market": {
      "current": 0,
      "previous": 0,
      "trend": "string"
    },
    "inventory": {
      "active_listings": 0,
      "months_supply": 0.0,
      "trend": "string"
    },
    "appreciation": {
      "monthly": 0.0,
      "annual": 0.0,
      "3_year_compound": 0.0
    }
  },
  "market_indicators": {
    "buyer_seller_index": -1.0-1.0,
    "market_type": "strong_buyer|buyer|balanced|seller|strong_seller",
    "price_momentum": "accelerating|stable|decelerating"
  },
  "forecast": {
    "6_month_appreciation": 0.0,
    "confidence": 0.0-1.0
  },
  "generated_at": "ISO8601"
}
```

### Investment Opportunity
```json
{
  "property_id": "string",
  "address": "string",
  "listing_price": 0,
  "estimated_value": 0,
  "discount_percent": 0.0,
  "opportunity_type": "undervalued|distressed|off_market|price_reduced",
  "investment_metrics": {
    "estimated_cap_rate": 0.0,
    "estimated_monthly_rent": 0,
    "cash_on_cash_return": 0.0,
    "appreciation_potential": 0.0
  },
  "risk_factors": ["string"],
  "opportunity_score": 0.0-1.0,
  "time_sensitivity": "urgent|moderate|low"
}
```

## CMA Methodology

### Comparable Selection Criteria

```python
COMP_CRITERIA = {
    "distance_max_miles": 1.5,
    "sqft_variance_percent": 20,
    "bedroom_variance": 1,
    "bathroom_variance": 1,
    "year_built_variance": 15,
    "sale_recency_months": 6,
    "min_comps_required": 3,
    "ideal_comps": 5
}
```

### Adjustment Factors

```python
ADJUSTMENT_FACTORS = {
    # Per unit adjustments
    "bedroom": 15000,      # +/- $15K per bedroom difference
    "bathroom": 10000,     # +/- $10K per bathroom difference
    "garage": 8000,        # +/- $8K per garage space

    # Per sqft adjustments
    "sqft": 75,            # +/- $75 per sqft difference

    # Feature adjustments
    "pool": 25000,         # +$25K for pool
    "updated_kitchen": 20000,
    "updated_bathrooms": 15000,
    "new_roof": 10000,

    # Condition adjustments
    "excellent_vs_good": 0.05,  # 5% premium
    "good_vs_average": 0.03,
    "average_vs_fair": -0.05,

    # Time adjustment (monthly appreciation)
    "monthly_appreciation": 0.004  # 0.4% per month
}
```

### Valuation Calculation

```python
def calculate_adjusted_value(comp: Dict, subject: Dict, market_data: Dict) -> float:
    """
    Calculate adjusted comparable value.

    Adjustments are made to the COMP to make it equivalent to the subject.
    """
    adjusted_value = comp["sale_price"]

    # Size adjustment
    sqft_diff = subject["sqft"] - comp["sqft"]
    adjusted_value += sqft_diff * ADJUSTMENT_FACTORS["sqft"]

    # Bedroom adjustment
    bed_diff = subject["bedrooms"] - comp["bedrooms"]
    adjusted_value += bed_diff * ADJUSTMENT_FACTORS["bedroom"]

    # Feature adjustments
    for feature in subject.get("features", []):
        if feature not in comp.get("features", []):
            adjusted_value += ADJUSTMENT_FACTORS.get(feature, 0)

    for feature in comp.get("features", []):
        if feature not in subject.get("features", []):
            adjusted_value -= ADJUSTMENT_FACTORS.get(feature, 0)

    # Time adjustment
    months_ago = calculate_months_since_sale(comp["sale_date"])
    time_adjustment = 1 + (months_ago * ADJUSTMENT_FACTORS["monthly_appreciation"])
    adjusted_value *= time_adjustment

    return adjusted_value
```

## Market Indicators

### Buyer vs Seller Market

| Indicator | Buyer's Market | Balanced | Seller's Market |
|-----------|---------------|----------|-----------------|
| Months of Inventory | > 6 | 4-6 | < 4 |
| Days on Market | > 60 | 30-60 | < 30 |
| List to Sale Ratio | < 95% | 95-100% | > 100% |
| Price Trend | Declining | Stable | Appreciating |
| Multiple Offers | Rare | Occasional | Common |

### Market Health Score

```python
def calculate_market_health(metrics: Dict) -> Dict:
    """Calculate overall market health indicators."""

    # Months of inventory
    inventory_score = 10 - min(metrics["months_inventory"], 10)

    # Days on market (lower is healthier)
    dom_score = max(0, 10 - metrics["avg_dom"] / 6)

    # Price appreciation (positive is healthier)
    appreciation = metrics["yoy_appreciation"]
    appreciation_score = min(10, max(0, 5 + appreciation * 50))

    # Overall score
    overall = (inventory_score + dom_score + appreciation_score) / 3

    return {
        "overall_health": overall,
        "inventory_score": inventory_score,
        "activity_score": dom_score,
        "price_momentum_score": appreciation_score,
        "market_type": determine_market_type(overall)
    }
```

## Success Metrics

- **CMA Generation Speed**: 90% faster than manual analysis
- **Valuation Accuracy**: Within 3% of actual sale price
- **Report Quality**: Professional-grade output
- **Time Savings**: 4+ hours per CMA saved

## Best Practices

1. **Use recent comps** - Prioritize sales within 3 months when available
2. **Verify adjustments** - Review automated adjustments for reasonableness
3. **Consider market velocity** - Adjust for rapidly changing markets
4. **Include off-market data** - Where available, incorporate pocket listings
5. **Update regularly** - Refresh CMAs if not used within 30 days

## Error Handling

```python
# Handle insufficient comparable data
try:
    cma = await analysis.generate_cma(subject_property)
except InsufficientCompsError as e:
    # Expand search criteria
    cma = await analysis.generate_cma(
        subject_property,
        comp_radius_miles=e.suggested_radius,
        sale_period_months=e.suggested_period
    )
    cma.confidence *= 0.8  # Reduce confidence
    cma.notes.append(f"Expanded search: {e.message}")
```

## Version History

- **1.0.0** (2026-01-16): Initial implementation
  - Automated CMA generation
  - Market trend analysis
  - Investment opportunity detection
  - Comparable property scoring
