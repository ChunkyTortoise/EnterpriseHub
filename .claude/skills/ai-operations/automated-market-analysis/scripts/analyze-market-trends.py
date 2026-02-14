#!/usr/bin/env python3
"""
Analyze Market Trends Script

Zero-context execution script for analyzing real estate market trends.

Usage:
    python analyze-market-trends.py --area "Teravista" --period 12
    python analyze-market-trends.py --area "Round Rock" --output json
"""

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics
import math
from collections import defaultdict


@dataclass
class PriceTrend:
    """Price trend data."""
    current_median: int
    previous_median: int
    mom_change: float
    yoy_change: float
    trend_direction: str
    momentum: str


@dataclass
class InventoryMetrics:
    """Inventory and supply metrics."""
    active_listings: int
    new_listings_month: int
    sold_month: int
    months_supply: float
    absorption_rate: float


@dataclass
class VelocityMetrics:
    """Sales velocity metrics."""
    avg_dom: int
    median_dom: int
    dom_trend: str
    list_to_sale_ratio: float


@dataclass
class MarketHealth:
    """Overall market health assessment."""
    score: float
    classification: str
    buyer_seller_index: float
    market_type: str


@dataclass
class Forecast:
    """Price forecast."""
    months_ahead: int
    projected_median: int
    confidence_low: int
    confidence_high: int
    confidence_level: float


@dataclass
class MarketTrendReport:
    """Complete market trend report."""
    area: str
    report_date: str
    period_months: int
    price_trends: PriceTrend
    inventory: InventoryMetrics
    velocity: VelocityMetrics
    market_health: MarketHealth
    forecasts: List[Forecast]
    seasonal_factor: float
    recommendations: Dict[str, str]


# Seasonal factors (Rancho Cucamonga Metro)
SEASONAL_FACTORS = {
    1: 0.97, 2: 0.98, 3: 1.00, 4: 1.02, 5: 1.03, 6: 1.03,
    7: 1.02, 8: 1.01, 9: 1.00, 10: 0.99, 11: 0.98, 12: 0.97
}


def generate_mock_sales_data(area: str, months: int) -> List[Dict]:
    """Generate mock historical sales data."""
    sales = []
    base_price = 625000
    base_date = datetime.now()

    for month_offset in range(months, 0, -1):
        sale_date = base_date - timedelta(days=month_offset * 30)
        month = sale_date.month

        # Apply seasonal factor and growth
        seasonal = SEASONAL_FACTORS.get(month, 1.0)
        growth_factor = 1 + (0.004 * (months - month_offset))  # ~5% annual

        # Generate 15-25 sales per month
        num_sales = 15 + (month % 10)

        for i in range(num_sales):
            variance = 0.8 + (i % 5) * 0.1  # Price variance
            price = int(base_price * seasonal * growth_factor * variance)

            dom = max(5, 30 + ((i * 7) % 40) - (20 if month in [4, 5, 6] else 0))

            sales.append({
                "sale_date": sale_date.strftime("%Y-%m-%d"),
                "sale_price": price,
                "list_price": int(price * (1.01 + (i % 3) * 0.01)),
                "dom": dom,
                "sqft": 2200 + (i * 100) % 1500
            })

    return sales


def generate_mock_inventory(area: str) -> Dict:
    """Generate mock current inventory data."""
    return {
        "active_listings": 145,
        "new_listings_30d": 52,
        "sold_30d": 48,
        "pending": 38,
        "price_reduced_30d": 28,
        "avg_list_price": 659000,
        "median_list_price": 625000
    }


def calculate_price_trends(sales: List[Dict]) -> PriceTrend:
    """Calculate price trends from sales data."""
    # Group by month
    monthly = defaultdict(list)
    for sale in sales:
        month_key = sale["sale_date"][:7]
        monthly[month_key].append(sale["sale_price"])

    months = sorted(monthly.keys())

    if len(months) < 2:
        return PriceTrend(
            current_median=0,
            previous_median=0,
            mom_change=0,
            yoy_change=0,
            trend_direction="unknown",
            momentum="unknown"
        )

    # Current and previous month medians
    current_median = int(statistics.median(monthly[months[-1]]))
    previous_median = int(statistics.median(monthly[months[-2]]))

    # Month-over-month change
    mom_change = (current_median - previous_median) / previous_median

    # Year-over-year change
    if len(months) >= 12:
        year_ago = months[-12]
        year_ago_median = statistics.median(monthly[year_ago])
        yoy_change = (current_median - year_ago_median) / year_ago_median
    else:
        # Annualize available data
        oldest = months[0]
        oldest_median = statistics.median(monthly[oldest])
        months_elapsed = len(months)
        total_change = (current_median - oldest_median) / oldest_median
        yoy_change = (1 + total_change) ** (12 / months_elapsed) - 1

    # Determine trend direction
    if len(months) >= 3:
        recent_medians = [statistics.median(monthly[m]) for m in months[-3:]]
        recent_changes = [
            (recent_medians[i] - recent_medians[i-1]) / recent_medians[i-1]
            for i in range(1, len(recent_medians))
        ]
        avg_change = sum(recent_changes) / len(recent_changes)

        if avg_change > 0.005:
            trend = "appreciating"
            momentum = "accelerating" if mom_change > avg_change else "stable"
        elif avg_change < -0.005:
            trend = "depreciating"
            momentum = "accelerating" if mom_change < avg_change else "decelerating"
        else:
            trend = "stable"
            momentum = "flat"
    else:
        trend = "appreciating" if mom_change > 0 else "depreciating" if mom_change < 0 else "stable"
        momentum = "unknown"

    return PriceTrend(
        current_median=current_median,
        previous_median=previous_median,
        mom_change=round(mom_change, 4),
        yoy_change=round(yoy_change, 4),
        trend_direction=trend,
        momentum=momentum
    )


def calculate_inventory_metrics(inventory: Dict, sales: List[Dict]) -> InventoryMetrics:
    """Calculate inventory and supply metrics."""
    active = inventory["active_listings"]
    new_listings = inventory["new_listings_30d"]
    sold = inventory["sold_30d"]

    # Months of supply
    months_supply = active / sold if sold > 0 else float("inf")

    # Absorption rate
    absorption = sold / new_listings if new_listings > 0 else 1.0

    return InventoryMetrics(
        active_listings=active,
        new_listings_month=new_listings,
        sold_month=sold,
        months_supply=round(months_supply, 2),
        absorption_rate=round(absorption, 2)
    )


def calculate_velocity_metrics(sales: List[Dict]) -> VelocityMetrics:
    """Calculate sales velocity metrics."""
    if not sales:
        return VelocityMetrics(
            avg_dom=0,
            median_dom=0,
            dom_trend="unknown",
            list_to_sale_ratio=1.0
        )

    # Recent sales only (last 90 days)
    recent_cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    recent_sales = [s for s in sales if s["sale_date"] >= recent_cutoff]

    if not recent_sales:
        recent_sales = sales[-50:]  # Fallback to last 50 sales

    # DOM metrics
    dom_values = [s["dom"] for s in recent_sales]
    avg_dom = int(sum(dom_values) / len(dom_values))
    median_dom = int(statistics.median(dom_values))

    # DOM trend (compare recent to older)
    if len(sales) >= 100:
        old_dom = sum(s["dom"] for s in sales[:50]) / 50
        new_dom = sum(s["dom"] for s in sales[-50:]) / 50

        if new_dom < old_dom * 0.9:
            dom_trend = "decreasing"
        elif new_dom > old_dom * 1.1:
            dom_trend = "increasing"
        else:
            dom_trend = "stable"
    else:
        dom_trend = "unknown"

    # List-to-sale ratio
    ratios = [s["sale_price"] / s["list_price"] for s in recent_sales]
    lsp_ratio = sum(ratios) / len(ratios)

    return VelocityMetrics(
        avg_dom=avg_dom,
        median_dom=median_dom,
        dom_trend=dom_trend,
        list_to_sale_ratio=round(lsp_ratio, 3)
    )


def calculate_market_health(
    price_trends: PriceTrend,
    inventory: InventoryMetrics,
    velocity: VelocityMetrics
) -> MarketHealth:
    """Calculate overall market health score."""
    scores = {}

    # Supply/Demand (30%)
    months = inventory.months_supply
    if months <= 2:
        supply_score = 95
    elif months <= 4:
        supply_score = 85
    elif months <= 6:
        supply_score = 70
    elif months <= 8:
        supply_score = 50
    else:
        supply_score = max(20, 100 - months * 8)
    scores["supply"] = supply_score

    # Price Momentum (25%)
    yoy = price_trends.yoy_change
    if 0.03 <= yoy <= 0.08:
        price_score = 90
    elif 0 <= yoy < 0.03:
        price_score = 70
    elif 0.08 < yoy <= 0.12:
        price_score = 75
    elif yoy > 0.12:
        price_score = 50
    else:
        price_score = max(30, 60 + yoy * 300)
    scores["price"] = price_score

    # Velocity (25%)
    dom = velocity.avg_dom
    if dom <= 21:
        vel_score = 90
    elif dom <= 45:
        vel_score = 80
    elif dom <= 60:
        vel_score = 65
    elif dom <= 90:
        vel_score = 45
    else:
        vel_score = max(20, 100 - dom)
    scores["velocity"] = vel_score

    # List-to-sale (20%)
    lsp = velocity.list_to_sale_ratio
    if lsp >= 1.0:
        lsp_score = 90
    elif lsp >= 0.98:
        lsp_score = 80
    elif lsp >= 0.95:
        lsp_score = 65
    else:
        lsp_score = max(30, lsp * 100)
    scores["lsp"] = lsp_score

    # Calculate total
    total = (
        scores["supply"] * 0.30 +
        scores["price"] * 0.25 +
        scores["velocity"] * 0.25 +
        scores["lsp"] * 0.20
    )

    # Classification
    if total >= 80:
        classification = "very_healthy"
    elif total >= 65:
        classification = "healthy"
    elif total >= 50:
        classification = "moderate"
    elif total >= 35:
        classification = "soft"
    else:
        classification = "weak"

    # Buyer-seller index
    supply_factor = max(-1, min(1, (6 - months) / 6))
    dom_factor = max(-1, min(1, (45 - dom) / 45))
    lsp_factor = max(-1, min(1, (lsp - 1.0) * 10))

    bs_index = supply_factor * 0.4 + dom_factor * 0.3 + lsp_factor * 0.3

    # Market type
    if bs_index >= 0.5:
        market_type = "strong_seller"
    elif bs_index >= 0.2:
        market_type = "seller"
    elif bs_index >= -0.2:
        market_type = "balanced"
    elif bs_index >= -0.5:
        market_type = "buyer"
    else:
        market_type = "strong_buyer"

    return MarketHealth(
        score=round(total, 1),
        classification=classification,
        buyer_seller_index=round(bs_index, 3),
        market_type=market_type
    )


def generate_forecasts(
    price_trends: PriceTrend,
    months_ahead: List[int] = [3, 6, 12]
) -> List[Forecast]:
    """Generate price forecasts."""
    forecasts = []
    current = price_trends.current_median

    # Monthly growth rate from YoY
    monthly_growth = (1 + price_trends.yoy_change) ** (1/12) - 1

    # Blend with recent momentum
    blended = price_trends.mom_change * 0.3 + monthly_growth * 0.7

    for months in months_ahead:
        future_month = (datetime.now().month + months - 1) % 12 + 1
        seasonal = SEASONAL_FACTORS.get(future_month, 1.0)

        projected = current * ((1 + blended) ** months) * seasonal

        # Confidence decreases with time
        confidence = max(0.5, 0.85 - months * 0.03)
        margin = 1 - confidence

        forecasts.append(Forecast(
            months_ahead=months,
            projected_median=int(round(projected, -3)),
            confidence_low=int(round(projected * (1 - margin), -3)),
            confidence_high=int(round(projected * (1 + margin), -3)),
            confidence_level=round(confidence, 2)
        ))

    return forecasts


def generate_recommendations(
    market_health: MarketHealth,
    price_trends: PriceTrend,
    inventory: InventoryMetrics
) -> Dict[str, str]:
    """Generate market-specific recommendations."""
    recommendations = {}

    # Seller recommendations
    if market_health.market_type in ["strong_seller", "seller"]:
        recommendations["for_sellers"] = (
            f"Excellent time to list. Strong seller's market with {inventory.months_supply:.1f} "
            f"months of supply. Properties selling at {price_trends.yoy_change:.1%} YoY appreciation."
        )
    elif market_health.market_type == "balanced":
        recommendations["for_sellers"] = (
            "Balanced market conditions. Price competitively and present property well. "
            "Consider strategic timing in spring months for best results."
        )
    else:
        recommendations["for_sellers"] = (
            f"Buyer's market with {inventory.months_supply:.1f} months of supply. "
            "Consider competitive pricing and offering incentives to attract buyers."
        )

    # Buyer recommendations
    if market_health.market_type in ["strong_seller", "seller"]:
        recommendations["for_buyers"] = (
            "Competitive market - be prepared to act quickly. "
            "Get pre-approved and consider offering above asking in hot areas. "
            "Escalation clauses may be necessary."
        )
    elif market_health.market_type == "balanced":
        recommendations["for_buyers"] = (
            "Balanced conditions provide good negotiating opportunities. "
            "Take time to find the right property but don't delay on good matches."
        )
    else:
        recommendations["for_buyers"] = (
            f"Great time to buy with {inventory.active_listings} active listings. "
            "Negotiate confidently and consider asking for seller concessions."
        )

    # Investment recommendations
    if price_trends.trend_direction == "appreciating" and market_health.score >= 65:
        recommendations["for_investors"] = (
            f"Healthy appreciation of {price_trends.yoy_change:.1%} makes this area attractive. "
            "Focus on properties with value-add potential or strong rental demand."
        )
    elif price_trends.trend_direction == "stable":
        recommendations["for_investors"] = (
            "Stable market suitable for cash-flow focused investments. "
            "Look for below-market deals and focus on rental yield."
        )
    else:
        recommendations["for_investors"] = (
            "Exercise caution in current market conditions. "
            "Focus on deeply discounted properties with clear exit strategies."
        )

    return recommendations


def analyze_market(area: str, period_months: int) -> MarketTrendReport:
    """Perform complete market analysis."""
    # Get data
    sales = generate_mock_sales_data(area, period_months)
    inventory = generate_mock_inventory(area)

    # Calculate metrics
    price_trends = calculate_price_trends(sales)
    inv_metrics = calculate_inventory_metrics(inventory, sales)
    velocity = calculate_velocity_metrics(sales)
    health = calculate_market_health(price_trends, inv_metrics, velocity)
    forecasts = generate_forecasts(price_trends)
    recommendations = generate_recommendations(health, price_trends, inv_metrics)

    # Current seasonal factor
    current_month = datetime.now().month
    seasonal = SEASONAL_FACTORS.get(current_month, 1.0)

    return MarketTrendReport(
        area=area,
        report_date=datetime.now().strftime("%Y-%m-%d"),
        period_months=period_months,
        price_trends=price_trends,
        inventory=inv_metrics,
        velocity=velocity,
        market_health=health,
        forecasts=forecasts,
        seasonal_factor=seasonal,
        recommendations=recommendations
    )


def report_to_dict(report: MarketTrendReport) -> Dict:
    """Convert report to dictionary."""
    return {
        "area": report.area,
        "report_date": report.report_date,
        "period_months": report.period_months,
        "price_trends": {
            "current_median": report.price_trends.current_median,
            "previous_median": report.price_trends.previous_median,
            "mom_change": report.price_trends.mom_change,
            "yoy_change": report.price_trends.yoy_change,
            "trend_direction": report.price_trends.trend_direction,
            "momentum": report.price_trends.momentum
        },
        "inventory": {
            "active_listings": report.inventory.active_listings,
            "new_listings_month": report.inventory.new_listings_month,
            "sold_month": report.inventory.sold_month,
            "months_supply": report.inventory.months_supply,
            "absorption_rate": report.inventory.absorption_rate
        },
        "velocity": {
            "avg_dom": report.velocity.avg_dom,
            "median_dom": report.velocity.median_dom,
            "dom_trend": report.velocity.dom_trend,
            "list_to_sale_ratio": report.velocity.list_to_sale_ratio
        },
        "market_health": {
            "score": report.market_health.score,
            "classification": report.market_health.classification,
            "buyer_seller_index": report.market_health.buyer_seller_index,
            "market_type": report.market_health.market_type
        },
        "forecasts": [
            {
                "months_ahead": f.months_ahead,
                "projected_median": f.projected_median,
                "confidence_low": f.confidence_low,
                "confidence_high": f.confidence_high,
                "confidence_level": f.confidence_level
            }
            for f in report.forecasts
        ],
        "seasonal_factor": report.seasonal_factor,
        "recommendations": report.recommendations
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Market Trends"
    )
    parser.add_argument(
        "--area",
        default="Round Rock",
        help="Market area to analyze"
    )
    parser.add_argument(
        "--period",
        type=int,
        default=12,
        help="Analysis period in months"
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output format"
    )

    args = parser.parse_args()

    report = analyze_market(args.area, args.period)

    if args.output == "json":
        print(json.dumps(report_to_dict(report), indent=2))
    else:
        print("\n" + "=" * 70)
        print("MARKET TREND ANALYSIS")
        print("=" * 70)
        print(f"\nArea: {report.area}")
        print(f"Report Date: {report.report_date}")
        print(f"Analysis Period: {report.period_months} months")

        print("\n" + "-" * 70)
        print("PRICE TRENDS")
        print("-" * 70)
        p = report.price_trends
        print(f"  Current Median Price: ${p.current_median:,}")
        print(f"  Previous Month: ${p.previous_median:,}")
        print(f"  Month-over-Month: {p.mom_change:+.2%}")
        print(f"  Year-over-Year: {p.yoy_change:+.2%}")
        print(f"  Trend: {p.trend_direction.title()} | Momentum: {p.momentum.title()}")

        print("\n" + "-" * 70)
        print("INVENTORY")
        print("-" * 70)
        i = report.inventory
        print(f"  Active Listings: {i.active_listings}")
        print(f"  New Listings (30d): {i.new_listings_month}")
        print(f"  Sold (30d): {i.sold_month}")
        print(f"  Months of Supply: {i.months_supply:.1f}")
        print(f"  Absorption Rate: {i.absorption_rate:.2f}")

        print("\n" + "-" * 70)
        print("SALES VELOCITY")
        print("-" * 70)
        v = report.velocity
        print(f"  Average Days on Market: {v.avg_dom}")
        print(f"  Median Days on Market: {v.median_dom}")
        print(f"  DOM Trend: {v.dom_trend.title()}")
        print(f"  List-to-Sale Ratio: {v.list_to_sale_ratio:.1%}")

        print("\n" + "-" * 70)
        print("MARKET HEALTH")
        print("-" * 70)
        h = report.market_health
        print(f"  Health Score: {h.score}/100")
        print(f"  Classification: {h.classification.replace('_', ' ').title()}")
        print(f"  Buyer-Seller Index: {h.buyer_seller_index:+.2f}")
        print(f"  Market Type: {h.market_type.replace('_', ' ').title()}'s Market")

        print("\n" + "-" * 70)
        print("PRICE FORECASTS")
        print("-" * 70)
        for f in report.forecasts:
            print(f"\n  {f.months_ahead} Months:")
            print(f"    Projected: ${f.projected_median:,}")
            print(f"    Range: ${f.confidence_low:,} - ${f.confidence_high:,}")
            print(f"    Confidence: {f.confidence_level:.0%}")

        print("\n" + "-" * 70)
        print("RECOMMENDATIONS")
        print("-" * 70)
        for key, value in report.recommendations.items():
            print(f"\n  {key.replace('_', ' ').title()}:")
            # Wrap long lines
            words = value.split()
            line = "    "
            for word in words:
                if len(line) + len(word) > 70:
                    print(line)
                    line = "    " + word + " "
                else:
                    line += word + " "
            if line.strip():
                print(line)

        print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
