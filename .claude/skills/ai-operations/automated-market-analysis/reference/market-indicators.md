# Market Indicators Reference

Comprehensive guide to market condition indicators and their interpretation.

## Key Market Indicators

### 1. Months of Supply (Inventory)

**Definition**: The number of months it would take to sell all current inventory at the current sales pace.

```python
def calculate_months_supply(active_listings: int, closed_last_month: int) -> float:
    """
    Calculate months of inventory.

    Formula: Active Listings / Monthly Closings
    """
    if closed_last_month == 0:
        return float("inf")
    return active_listings / closed_last_month
```

**Interpretation**:

| Months Supply | Market Type | Implication |
|---------------|-------------|-------------|
| < 3 months | Strong Seller's | Prices rising, quick sales |
| 3-4 months | Seller's | Advantage to sellers |
| 4-6 months | Balanced | Fair for both parties |
| 6-8 months | Buyer's | Advantage to buyers |
| > 8 months | Strong Buyer's | Prices may decline |

### 2. Days on Market (DOM)

**Definition**: Average number of days from listing to contract.

```python
def calculate_avg_dom(sales: List[Dict]) -> float:
    """
    Calculate average days on market.

    Uses sales from specified period.
    """
    if not sales:
        return 0

    total_days = sum(
        (parse_date(s["contract_date"]) - parse_date(s["list_date"])).days
        for s in sales
    )
    return total_days / len(sales)
```

**Interpretation**:

| DOM | Market Velocity | Implication |
|-----|-----------------|-------------|
| < 14 days | Very Fast | Multiple offers common |
| 14-30 days | Fast | Competitive market |
| 30-60 days | Normal | Standard negotiations |
| 60-90 days | Slow | Price reductions common |
| > 90 days | Very Slow | Heavy buyer negotiating power |

### 3. List-to-Sale Price Ratio

**Definition**: Percentage of asking price achieved at sale.

```python
def calculate_lsp_ratio(sales: List[Dict]) -> float:
    """
    Calculate average list-to-sale price ratio.

    Formula: Sale Price / List Price (at time of offer)
    """
    if not sales:
        return 0

    ratios = [s["sale_price"] / s["list_price"] for s in sales]
    return sum(ratios) / len(ratios)
```

**Interpretation**:

| Ratio | Market Condition | Implication |
|-------|------------------|-------------|
| > 102% | Very Hot | Bidding wars, over-ask offers |
| 100-102% | Hot | Full price or above offers |
| 98-100% | Balanced | Minor negotiation expected |
| 95-98% | Soft | Significant negotiation |
| < 95% | Weak | Large price reductions |

### 4. Absorption Rate

**Definition**: Rate at which available homes are sold in a specific market.

```python
def calculate_absorption_rate(
    new_listings: int,
    sold: int,
    period_months: int = 1
) -> float:
    """
    Calculate absorption rate.

    Formula: Sold / New Listings per period
    > 1.0 = inventory shrinking (seller's market)
    < 1.0 = inventory growing (buyer's market)
    """
    if new_listings == 0:
        return float("inf") if sold > 0 else 1.0
    return (sold / new_listings)
```

**Interpretation**:

| Absorption Rate | Trend | Implication |
|-----------------|-------|-------------|
| > 1.2 | Shrinking fast | Prices rising |
| 1.0-1.2 | Stable to shrinking | Healthy market |
| 0.8-1.0 | Stable to growing | Balanced |
| < 0.8 | Growing fast | Price pressure down |

## Market Health Score

### Composite Index Calculation

```python
def calculate_market_health_score(metrics: Dict) -> Dict:
    """
    Calculate comprehensive market health score.

    Components:
    - Supply/demand balance (30%)
    - Price momentum (25%)
    - Sales velocity (25%)
    - Affordability (20%)

    Returns score 0-100 and classification.
    """
    scores = {}

    # Supply/Demand (30%)
    months_supply = metrics["months_supply"]
    if months_supply <= 2:
        supply_score = 95
    elif months_supply <= 4:
        supply_score = 85
    elif months_supply <= 6:
        supply_score = 70
    elif months_supply <= 8:
        supply_score = 50
    else:
        supply_score = max(20, 100 - months_supply * 8)
    scores["supply_demand"] = supply_score

    # Price Momentum (25%)
    yoy_appreciation = metrics.get("yoy_appreciation", 0)
    if 0.03 <= yoy_appreciation <= 0.08:
        price_score = 90  # Healthy appreciation
    elif 0 <= yoy_appreciation < 0.03:
        price_score = 70  # Slow but positive
    elif 0.08 < yoy_appreciation <= 0.12:
        price_score = 75  # Fast but sustainable
    elif yoy_appreciation > 0.12:
        price_score = 50  # Overheating risk
    else:
        price_score = max(30, 60 + yoy_appreciation * 300)  # Declining
    scores["price_momentum"] = price_score

    # Sales Velocity (25%)
    avg_dom = metrics.get("avg_dom", 60)
    if avg_dom <= 21:
        velocity_score = 90
    elif avg_dom <= 45:
        velocity_score = 80
    elif avg_dom <= 60:
        velocity_score = 65
    elif avg_dom <= 90:
        velocity_score = 45
    else:
        velocity_score = max(20, 100 - avg_dom)
    scores["velocity"] = velocity_score

    # Affordability (20%)
    price_to_income = metrics.get("price_to_income_ratio", 5)
    if price_to_income <= 4:
        afford_score = 90
    elif price_to_income <= 5:
        afford_score = 75
    elif price_to_income <= 6:
        afford_score = 60
    elif price_to_income <= 7:
        afford_score = 45
    else:
        afford_score = max(20, 120 - price_to_income * 10)
    scores["affordability"] = afford_score

    # Calculate weighted total
    total_score = (
        scores["supply_demand"] * 0.30 +
        scores["price_momentum"] * 0.25 +
        scores["velocity"] * 0.25 +
        scores["affordability"] * 0.20
    )

    # Classify market
    if total_score >= 80:
        classification = "very_healthy"
    elif total_score >= 65:
        classification = "healthy"
    elif total_score >= 50:
        classification = "moderate"
    elif total_score >= 35:
        classification = "soft"
    else:
        classification = "weak"

    return {
        "total_score": round(total_score, 1),
        "classification": classification,
        "component_scores": scores,
        "metrics_used": metrics
    }
```

## Buyer vs Seller Market Index

### Index Calculation

```python
def calculate_buyer_seller_index(metrics: Dict) -> Dict:
    """
    Calculate buyer-seller market index.

    Returns index from -1.0 (strong buyer's) to +1.0 (strong seller's)
    with 0.0 being balanced.
    """
    factors = []

    # Months of supply factor
    months = metrics.get("months_supply", 6)
    # 6 months = 0, less = positive (seller), more = negative (buyer)
    supply_factor = max(-1, min(1, (6 - months) / 6))
    factors.append(("supply", supply_factor, 0.30))

    # DOM factor
    dom = metrics.get("avg_dom", 45)
    # 45 days = 0, less = positive (seller), more = negative (buyer)
    dom_factor = max(-1, min(1, (45 - dom) / 45))
    factors.append(("velocity", dom_factor, 0.25))

    # List-to-sale ratio factor
    lsp = metrics.get("list_to_sale_ratio", 1.0)
    # 1.0 = 0, higher = positive (seller), lower = negative (buyer)
    lsp_factor = max(-1, min(1, (lsp - 1.0) * 10))
    factors.append(("price_strength", lsp_factor, 0.25))

    # Absorption rate factor
    absorption = metrics.get("absorption_rate", 1.0)
    # 1.0 = 0, higher = positive (seller), lower = negative (buyer)
    absorption_factor = max(-1, min(1, (absorption - 1.0) * 2))
    factors.append(("absorption", absorption_factor, 0.20))

    # Calculate weighted index
    index = sum(f * w for _, f, w in factors)

    # Classify
    if index >= 0.5:
        market_type = "strong_seller"
    elif index >= 0.2:
        market_type = "seller"
    elif index >= -0.2:
        market_type = "balanced"
    elif index >= -0.5:
        market_type = "buyer"
    else:
        market_type = "strong_buyer"

    return {
        "index": round(index, 3),
        "market_type": market_type,
        "factors": {name: round(factor, 3) for name, factor, _ in factors}
    }
```

## Price Trends Analysis

### Trend Calculation

```python
def analyze_price_trends(sales_history: List[Dict]) -> Dict:
    """
    Analyze price trends from historical sales data.

    Calculates:
    - Month-over-month change
    - Year-over-year change
    - Rolling averages
    - Trend direction
    """
    # Group sales by month
    monthly_median = defaultdict(list)
    for sale in sales_history:
        month_key = sale["sale_date"][:7]  # YYYY-MM
        monthly_median[month_key].append(sale["sale_price"])

    # Calculate median for each month
    medians = {}
    for month, prices in sorted(monthly_median.items()):
        medians[month] = statistics.median(prices)

    months = sorted(medians.keys())

    if len(months) < 2:
        return {"error": "Insufficient data for trend analysis"}

    # Month-over-month change
    current_month = months[-1]
    previous_month = months[-2]
    mom_change = (medians[current_month] - medians[previous_month]) / medians[previous_month]

    # Year-over-year change
    if len(months) >= 12:
        year_ago_month = months[-12] if len(months) >= 12 else months[0]
        yoy_change = (medians[current_month] - medians[year_ago_month]) / medians[year_ago_month]
    else:
        # Annualize the available data
        earliest = months[0]
        months_elapsed = len(months)
        total_change = (medians[current_month] - medians[earliest]) / medians[earliest]
        yoy_change = (1 + total_change) ** (12 / months_elapsed) - 1

    # 3-month rolling average
    if len(months) >= 3:
        recent_3 = [medians[m] for m in months[-3:]]
        rolling_3mo = sum(recent_3) / 3
    else:
        rolling_3mo = medians[current_month]

    # Determine trend direction
    if len(months) >= 3:
        recent_changes = []
        for i in range(-3, 0):
            if i - 1 >= -len(months):
                change = (medians[months[i]] - medians[months[i-1]]) / medians[months[i-1]]
                recent_changes.append(change)

        avg_recent_change = sum(recent_changes) / len(recent_changes) if recent_changes else 0

        if avg_recent_change > 0.01:
            trend = "appreciating"
            momentum = "accelerating" if mom_change > avg_recent_change else "stable"
        elif avg_recent_change < -0.01:
            trend = "depreciating"
            momentum = "accelerating" if mom_change < avg_recent_change else "decelerating"
        else:
            trend = "stable"
            momentum = "flat"
    else:
        trend = "unknown"
        momentum = "unknown"

    return {
        "current_median": medians[current_month],
        "mom_change": round(mom_change, 4),
        "yoy_change": round(yoy_change, 4),
        "rolling_3mo_median": round(rolling_3mo),
        "trend": trend,
        "momentum": momentum,
        "data_points": len(months)
    }
```

## Seasonal Patterns

### Seasonality Analysis

```python
TYPICAL_SEASONAL_FACTORS = {
    # Month: (price factor, volume factor)
    1: (0.97, 0.75),   # January - slow
    2: (0.98, 0.80),   # February - picking up
    3: (1.00, 0.90),   # March - spring starts
    4: (1.02, 1.05),   # April - strong
    5: (1.03, 1.15),   # May - peak season
    6: (1.03, 1.10),   # June - peak season
    7: (1.02, 1.00),   # July - summer slowdown
    8: (1.01, 0.95),   # August - back to school
    9: (1.00, 0.90),   # September - fall
    10: (0.99, 0.85),  # October - slowing
    11: (0.98, 0.75),  # November - holiday slowdown
    12: (0.97, 0.65),  # December - slowest
}

def apply_seasonal_adjustment(price: float, month: int) -> float:
    """Adjust price for seasonal factors."""
    factor = TYPICAL_SEASONAL_FACTORS.get(month, (1.0, 1.0))[0]
    return price / factor


def forecast_seasonal_timing(current_month: int) -> Dict:
    """Provide timing recommendations based on seasonality."""
    current_factor = TYPICAL_SEASONAL_FACTORS[current_month][0]

    best_months = sorted(
        TYPICAL_SEASONAL_FACTORS.items(),
        key=lambda x: x[1][0],
        reverse=True
    )[:3]

    worst_months = sorted(
        TYPICAL_SEASONAL_FACTORS.items(),
        key=lambda x: x[1][0]
    )[:3]

    return {
        "current_price_factor": current_factor,
        "best_selling_months": [m for m, _ in best_months],
        "worst_selling_months": [m for m, _ in worst_months],
        "recommendation": generate_timing_recommendation(current_month)
    }
```

## Forecasting

### Simple Trend Projection

```python
def forecast_prices(
    historical_data: List[Dict],
    forecast_months: int = 6
) -> Dict:
    """
    Project future prices based on historical trends.

    Uses weighted average of:
    - Recent momentum (40%)
    - Seasonal patterns (30%)
    - Historical average (30%)
    """
    trend_data = analyze_price_trends(historical_data)

    if "error" in trend_data:
        return trend_data

    current_price = trend_data["current_median"]
    monthly_change = trend_data["mom_change"]
    yoy_change = trend_data["yoy_change"]

    # Calculate monthly growth rate from YoY
    monthly_growth = (1 + yoy_change) ** (1/12) - 1

    # Weight between recent momentum and historical average
    blended_growth = monthly_change * 0.4 + monthly_growth * 0.6

    forecasts = []
    projected_price = current_price

    for i in range(1, forecast_months + 1):
        future_month = (datetime.now().month + i - 1) % 12 + 1
        seasonal_factor = TYPICAL_SEASONAL_FACTORS[future_month][0]

        # Apply growth and seasonal adjustment
        projected_price *= (1 + blended_growth)
        seasonally_adjusted = projected_price * seasonal_factor

        forecasts.append({
            "months_ahead": i,
            "projected_price": int(round(seasonally_adjusted, -3)),
            "confidence_low": int(round(seasonally_adjusted * 0.95, -3)),
            "confidence_high": int(round(seasonally_adjusted * 1.05, -3))
        })

    return {
        "base_price": current_price,
        "monthly_growth_rate": round(blended_growth, 4),
        "forecasts": forecasts,
        "methodology": "weighted_trend_with_seasonality"
    }
```

## Output Schema

### Market Analysis Report

```json
{
  "area": "string",
  "report_date": "YYYY-MM-DD",
  "period_analyzed": "string",

  "key_metrics": {
    "months_supply": 0.0,
    "avg_dom": 0,
    "list_to_sale_ratio": 0.00,
    "absorption_rate": 0.0,
    "median_price": 0,
    "price_per_sqft": 0
  },

  "market_health": {
    "total_score": 0-100,
    "classification": "string",
    "component_scores": {}
  },

  "buyer_seller_index": {
    "index": -1.0 to 1.0,
    "market_type": "string",
    "factors": {}
  },

  "price_trends": {
    "mom_change": 0.00,
    "yoy_change": 0.00,
    "trend": "string",
    "momentum": "string"
  },

  "forecast": {
    "6_month": {
      "projected_price": 0,
      "confidence_range": [0, 0]
    },
    "12_month": {
      "projected_price": 0,
      "confidence_range": [0, 0]
    }
  },

  "recommendations": {
    "for_sellers": "string",
    "for_buyers": "string",
    "timing_advice": "string"
  }
}
```
