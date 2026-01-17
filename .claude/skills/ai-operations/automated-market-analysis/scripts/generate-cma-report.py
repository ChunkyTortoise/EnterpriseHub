#!/usr/bin/env python3
"""
Generate CMA Report Script

Zero-context execution script for generating Comparative Market Analysis reports.

Usage:
    python generate-cma-report.py --address "123 Main St, Austin, TX" --output json
    python generate-cma-report.py --property-id <id> --output pdf
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics
import math


@dataclass
class PropertyDetails:
    """Subject property details."""
    property_id: str
    address: str
    bedrooms: int
    bathrooms: float
    sqft: int
    lot_size_sqft: int
    year_built: int
    property_type: str
    features: List[str]
    condition: str
    coordinates: Tuple[float, float]


@dataclass
class Comparable:
    """Comparable property with adjustments."""
    property_id: str
    address: str
    sale_price: int
    sale_date: str
    bedrooms: int
    bathrooms: float
    sqft: int
    year_built: int
    distance_miles: float
    comparability_score: float
    adjustments: Dict[str, int]
    adjusted_price: int


@dataclass
class Valuation:
    """Valuation result."""
    estimated_value: int
    value_low: int
    value_high: int
    price_per_sqft: int
    confidence: float


@dataclass
class MarketContext:
    """Market context for the CMA."""
    median_price: int
    avg_dom: int
    months_supply: float
    list_to_sale_ratio: float
    market_type: str
    trend: str


@dataclass
class CMAReport:
    """Complete CMA report."""
    report_id: str
    generated_at: str
    subject_property: PropertyDetails
    valuation: Valuation
    comparables: List[Comparable]
    market_context: MarketContext
    recommendations: Dict[str, str]


# Adjustment factors (Austin Metro 2026)
ADJUSTMENT_FACTORS = {
    "bedroom": {"add": 20000, "subtract": -15000},
    "bathroom": 12000,
    "sqft": 100,  # Per sqft
    "year_built": 500,  # Per year
    "pool": 30000,
    "updated_kitchen": 25000,
    "updated_bathrooms": 12000,
    "garage": 10000,
    "lot_premium": 15000,
    "monthly_appreciation": 0.004,
}


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate distance between coordinates in miles."""
    R = 3959
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def calculate_months_since(date_str: str) -> int:
    """Calculate months since a date."""
    sale_date = datetime.strptime(date_str, "%Y-%m-%d")
    today = datetime.now()
    return (today.year - sale_date.year) * 12 + (today.month - sale_date.month)


def score_comparable(subject: PropertyDetails, comp: Dict) -> float:
    """Score how comparable a property is to the subject."""
    scores = []

    # Location (30%)
    distance = haversine_distance(subject.coordinates, (comp["lat"], comp["lng"]))
    if distance <= 0.5:
        loc_score = 1.0
    elif distance <= 1.0:
        loc_score = 0.9
    elif distance <= 1.5:
        loc_score = 0.7
    else:
        loc_score = max(0.3, 1 - distance / 5)
    scores.append(loc_score * 0.30)

    # Physical (40%)
    sqft_ratio = min(subject.sqft, comp["sqft"]) / max(subject.sqft, comp["sqft"])
    bed_score = max(0, 1 - abs(subject.bedrooms - comp["bedrooms"]) * 0.3)
    bath_score = max(0, 1 - abs(subject.bathrooms - comp["bathrooms"]) * 0.2)
    year_score = max(0, 1 - abs(subject.year_built - comp["year_built"]) / 30)
    physical = sqft_ratio * 0.4 + bed_score * 0.25 + bath_score * 0.15 + year_score * 0.2
    scores.append(physical * 0.40)

    # Recency (20%)
    months = calculate_months_since(comp["sale_date"])
    if months <= 3:
        recency = 1.0
    elif months <= 6:
        recency = 0.9
    elif months <= 9:
        recency = 0.7
    else:
        recency = max(0.3, 1 - months / 24)
    scores.append(recency * 0.20)

    # Condition match (10%)
    cond_map = {"excellent": 1.0, "good": 0.8, "average": 0.6, "fair": 0.4}
    subj_cond = cond_map.get(subject.condition, 0.6)
    comp_cond = cond_map.get(comp.get("condition", "average"), 0.6)
    cond_score = 1 - abs(subj_cond - comp_cond)
    scores.append(cond_score * 0.10)

    return sum(scores)


def calculate_adjustments(subject: PropertyDetails, comp: Dict) -> Dict[str, int]:
    """Calculate adjustments needed for comparable."""
    adjustments = {}

    # Bedrooms
    bed_diff = subject.bedrooms - comp["bedrooms"]
    if bed_diff > 0:
        adjustments["bedrooms"] = bed_diff * ADJUSTMENT_FACTORS["bedroom"]["add"]
    elif bed_diff < 0:
        adjustments["bedrooms"] = abs(bed_diff) * ADJUSTMENT_FACTORS["bedroom"]["subtract"]

    # Bathrooms
    bath_diff = subject.bathrooms - comp["bathrooms"]
    if bath_diff != 0:
        adjustments["bathrooms"] = int(bath_diff * ADJUSTMENT_FACTORS["bathroom"])

    # Square footage
    sqft_diff = subject.sqft - comp["sqft"]
    if abs(sqft_diff) > 100:
        adjustments["sqft"] = sqft_diff * ADJUSTMENT_FACTORS["sqft"]

    # Year built
    year_diff = subject.year_built - comp["year_built"]
    if abs(year_diff) > 5:
        adjustments["year_built"] = year_diff * ADJUSTMENT_FACTORS["year_built"]

    # Features
    subject_features = set(subject.features)
    comp_features = set(comp.get("features", []))

    for feature in subject_features - comp_features:
        if feature in ADJUSTMENT_FACTORS:
            adjustments[f"add_{feature}"] = ADJUSTMENT_FACTORS[feature]

    for feature in comp_features - subject_features:
        if feature in ADJUSTMENT_FACTORS:
            adjustments[f"sub_{feature}"] = -ADJUSTMENT_FACTORS[feature]

    # Time adjustment
    months = calculate_months_since(comp["sale_date"])
    if months > 0:
        time_adj = int(comp["sale_price"] * months * ADJUSTMENT_FACTORS["monthly_appreciation"])
        adjustments["time"] = time_adj

    return adjustments


def calculate_valuation(comps: List[Comparable], subject: PropertyDetails) -> Valuation:
    """Calculate valuation from adjusted comparables."""
    adjusted_prices = [c.adjusted_price for c in comps]
    weights = [c.comparability_score for c in comps]

    # Weighted average
    total_weight = sum(weights)
    weighted_avg = sum(p * w for p, w in zip(adjusted_prices, weights)) / total_weight

    # Median
    median_price = statistics.median(adjusted_prices)

    # Price per sqft
    avg_ppsf = sum(c.adjusted_price / subject.sqft for c in comps) / len(comps)
    ppsf_value = avg_ppsf * subject.sqft

    # Final estimate (blended)
    estimated = weighted_avg * 0.5 + median_price * 0.3 + ppsf_value * 0.2

    # Range
    min_price = min(adjusted_prices)
    max_price = max(adjusted_prices)

    # Confidence
    avg_score = sum(weights) / len(weights)
    range_pct = (max_price - min_price) / median_price
    confidence = min(0.95, avg_score * 0.6 + (1 - range_pct) * 0.4)

    return Valuation(
        estimated_value=int(round(estimated, -3)),
        value_low=int(round(min_price * 0.97, -3)),
        value_high=int(round(max_price * 1.03, -3)),
        price_per_sqft=int(round(avg_ppsf)),
        confidence=round(confidence, 2)
    )


def get_market_context(area: str) -> MarketContext:
    """Get market context for the area (mock data)."""
    # In production, this would fetch from market data API
    return MarketContext(
        median_price=625000,
        avg_dom=32,
        months_supply=3.2,
        list_to_sale_ratio=0.99,
        market_type="seller",
        trend="appreciating"
    )


def generate_recommendations(
    valuation: Valuation,
    market: MarketContext
) -> Dict[str, str]:
    """Generate recommendations based on valuation and market."""
    recommendations = {}

    # Listing price recommendation
    if market.market_type in ["strong_seller", "seller"]:
        listing_price = int(valuation.estimated_value * 1.02)
        recommendations["listing_price"] = f"${listing_price:,}"
        recommendations["price_strategy"] = (
            "Consider pricing slightly above estimated value. "
            "Current seller's market conditions support strong pricing."
        )
    elif market.market_type == "balanced":
        listing_price = valuation.estimated_value
        recommendations["listing_price"] = f"${listing_price:,}"
        recommendations["price_strategy"] = (
            "Price at or near estimated value for balanced market conditions."
        )
    else:
        listing_price = int(valuation.estimated_value * 0.98)
        recommendations["listing_price"] = f"${listing_price:,}"
        recommendations["price_strategy"] = (
            "Consider competitive pricing below estimated value to attract buyers "
            "in current market conditions."
        )

    # Timing advice
    if market.avg_dom < 30:
        recommendations["timing_advice"] = (
            f"Excellent time to list. Properties averaging {market.avg_dom} days on market."
        )
    elif market.avg_dom < 60:
        recommendations["timing_advice"] = (
            f"Good market activity with {market.avg_dom} average days on market."
        )
    else:
        recommendations["timing_advice"] = (
            f"Slower market with {market.avg_dom} average days. "
            "Consider strategic timing or pricing."
        )

    # Confidence note
    if valuation.confidence >= 0.8:
        recommendations["confidence_note"] = (
            "High confidence valuation based on strong comparable data."
        )
    elif valuation.confidence >= 0.6:
        recommendations["confidence_note"] = (
            "Moderate confidence. Consider additional market research."
        )
    else:
        recommendations["confidence_note"] = (
            "Lower confidence due to limited comparable data. "
            "Professional appraisal recommended."
        )

    return recommendations


def generate_mock_comps(subject: PropertyDetails) -> List[Dict]:
    """Generate mock comparable properties."""
    # In production, this would query MLS data
    base_lat, base_lng = subject.coordinates

    mock_comps = [
        {
            "property_id": "comp_001",
            "address": "456 Oak St, Round Rock, TX",
            "sale_price": 620000,
            "sale_date": "2025-11-15",
            "bedrooms": subject.bedrooms,
            "bathrooms": subject.bathrooms,
            "sqft": subject.sqft - 150,
            "year_built": subject.year_built - 2,
            "lat": base_lat + 0.005,
            "lng": base_lng + 0.003,
            "features": ["pool"],
            "condition": "good"
        },
        {
            "property_id": "comp_002",
            "address": "789 Elm Ave, Round Rock, TX",
            "sale_price": 645000,
            "sale_date": "2025-12-01",
            "bedrooms": subject.bedrooms,
            "bathrooms": subject.bathrooms + 0.5,
            "sqft": subject.sqft + 200,
            "year_built": subject.year_built + 1,
            "lat": base_lat - 0.004,
            "lng": base_lng + 0.002,
            "features": ["updated_kitchen"],
            "condition": "excellent"
        },
        {
            "property_id": "comp_003",
            "address": "321 Pine Dr, Round Rock, TX",
            "sale_price": 598000,
            "sale_date": "2025-10-20",
            "bedrooms": subject.bedrooms - 1,
            "bathrooms": subject.bathrooms,
            "sqft": subject.sqft - 300,
            "year_built": subject.year_built - 5,
            "lat": base_lat + 0.003,
            "lng": base_lng - 0.004,
            "features": [],
            "condition": "average"
        },
        {
            "property_id": "comp_004",
            "address": "654 Maple Ln, Round Rock, TX",
            "sale_price": 675000,
            "sale_date": "2026-01-05",
            "bedrooms": subject.bedrooms + 1,
            "bathrooms": subject.bathrooms + 1,
            "sqft": subject.sqft + 400,
            "year_built": subject.year_built,
            "lat": base_lat - 0.002,
            "lng": base_lng - 0.003,
            "features": ["pool", "updated_kitchen"],
            "condition": "excellent"
        },
        {
            "property_id": "comp_005",
            "address": "987 Cedar Way, Round Rock, TX",
            "sale_price": 635000,
            "sale_date": "2025-11-28",
            "bedrooms": subject.bedrooms,
            "bathrooms": subject.bathrooms,
            "sqft": subject.sqft + 100,
            "year_built": subject.year_built - 3,
            "lat": base_lat + 0.006,
            "lng": base_lng + 0.001,
            "features": ["garage"],
            "condition": "good"
        }
    ]

    return mock_comps


def process_comparables(subject: PropertyDetails, raw_comps: List[Dict]) -> List[Comparable]:
    """Process raw comparable data into Comparable objects."""
    processed = []

    for comp in raw_comps:
        # Calculate score
        score = score_comparable(subject, comp)

        # Skip if score too low
        if score < 0.5:
            continue

        # Calculate adjustments
        adjustments = calculate_adjustments(subject, comp)

        # Calculate adjusted price
        total_adjustment = sum(adjustments.values())
        adjusted_price = comp["sale_price"] + total_adjustment

        # Calculate distance
        distance = haversine_distance(
            subject.coordinates,
            (comp["lat"], comp["lng"])
        )

        processed.append(Comparable(
            property_id=comp["property_id"],
            address=comp["address"],
            sale_price=comp["sale_price"],
            sale_date=comp["sale_date"],
            bedrooms=comp["bedrooms"],
            bathrooms=comp["bathrooms"],
            sqft=comp["sqft"],
            year_built=comp["year_built"],
            distance_miles=round(distance, 2),
            comparability_score=round(score, 3),
            adjustments=adjustments,
            adjusted_price=adjusted_price
        ))

    # Sort by score and return top 5
    processed.sort(key=lambda x: x.comparability_score, reverse=True)
    return processed[:5]


def generate_report(subject: PropertyDetails, area: str) -> CMAReport:
    """Generate complete CMA report."""
    # Get comparables
    raw_comps = generate_mock_comps(subject)
    comparables = process_comparables(subject, raw_comps)

    if len(comparables) < 3:
        raise ValueError("Insufficient comparable properties found")

    # Calculate valuation
    valuation = calculate_valuation(comparables, subject)

    # Get market context
    market = get_market_context(area)

    # Generate recommendations
    recommendations = generate_recommendations(valuation, market)

    # Create report
    report = CMAReport(
        report_id=f"CMA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        generated_at=datetime.now().isoformat(),
        subject_property=subject,
        valuation=valuation,
        comparables=comparables,
        market_context=market,
        recommendations=recommendations
    )

    return report


def report_to_dict(report: CMAReport) -> Dict:
    """Convert report to dictionary for JSON serialization."""
    return {
        "report_id": report.report_id,
        "generated_at": report.generated_at,
        "subject_property": {
            "property_id": report.subject_property.property_id,
            "address": report.subject_property.address,
            "bedrooms": report.subject_property.bedrooms,
            "bathrooms": report.subject_property.bathrooms,
            "sqft": report.subject_property.sqft,
            "lot_size_sqft": report.subject_property.lot_size_sqft,
            "year_built": report.subject_property.year_built,
            "property_type": report.subject_property.property_type,
            "features": report.subject_property.features,
            "condition": report.subject_property.condition
        },
        "valuation": {
            "estimated_value": report.valuation.estimated_value,
            "value_low": report.valuation.value_low,
            "value_high": report.valuation.value_high,
            "price_per_sqft": report.valuation.price_per_sqft,
            "confidence": report.valuation.confidence
        },
        "comparables": [
            {
                "property_id": c.property_id,
                "address": c.address,
                "sale_price": c.sale_price,
                "sale_date": c.sale_date,
                "bedrooms": c.bedrooms,
                "bathrooms": c.bathrooms,
                "sqft": c.sqft,
                "year_built": c.year_built,
                "distance_miles": c.distance_miles,
                "comparability_score": c.comparability_score,
                "adjustments": c.adjustments,
                "adjusted_price": c.adjusted_price
            }
            for c in report.comparables
        ],
        "market_context": {
            "median_price": report.market_context.median_price,
            "avg_dom": report.market_context.avg_dom,
            "months_supply": report.market_context.months_supply,
            "list_to_sale_ratio": report.market_context.list_to_sale_ratio,
            "market_type": report.market_context.market_type,
            "trend": report.market_context.trend
        },
        "recommendations": report.recommendations
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate CMA Report"
    )
    parser.add_argument(
        "--address",
        help="Subject property address"
    )
    parser.add_argument(
        "--property-id",
        help="Subject property ID"
    )
    parser.add_argument(
        "--bedrooms",
        type=int,
        default=4,
        help="Number of bedrooms"
    )
    parser.add_argument(
        "--bathrooms",
        type=float,
        default=3.0,
        help="Number of bathrooms"
    )
    parser.add_argument(
        "--sqft",
        type=int,
        default=2800,
        help="Square footage"
    )
    parser.add_argument(
        "--year-built",
        type=int,
        default=2018,
        help="Year built"
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output format"
    )

    args = parser.parse_args()

    # Create subject property
    address = args.address or "123 Teravista Pkwy, Round Rock, TX 78665"

    subject = PropertyDetails(
        property_id=args.property_id or "subject_001",
        address=address,
        bedrooms=args.bedrooms,
        bathrooms=args.bathrooms,
        sqft=args.sqft,
        lot_size_sqft=8500,
        year_built=args.year_built,
        property_type="single_family",
        features=["pool", "updated_kitchen"],
        condition="good",
        coordinates=(30.508, -97.678)
    )

    try:
        report = generate_report(subject, "Round Rock")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.output == "json":
        print(json.dumps(report_to_dict(report), indent=2))
    else:
        print("\n" + "=" * 70)
        print("COMPARATIVE MARKET ANALYSIS REPORT")
        print("=" * 70)
        print(f"\nReport ID: {report.report_id}")
        print(f"Generated: {report.generated_at}")

        print("\n" + "-" * 70)
        print("SUBJECT PROPERTY")
        print("-" * 70)
        s = report.subject_property
        print(f"  Address: {s.address}")
        print(f"  Bedrooms: {s.bedrooms} | Bathrooms: {s.bathrooms}")
        print(f"  Square Feet: {s.sqft:,} | Year Built: {s.year_built}")
        print(f"  Features: {', '.join(s.features)}")
        print(f"  Condition: {s.condition.title()}")

        print("\n" + "-" * 70)
        print("VALUATION")
        print("-" * 70)
        v = report.valuation
        print(f"  Estimated Value: ${v.estimated_value:,}")
        print(f"  Value Range: ${v.value_low:,} - ${v.value_high:,}")
        print(f"  Price per Sqft: ${v.price_per_sqft}")
        print(f"  Confidence: {v.confidence:.0%}")

        print("\n" + "-" * 70)
        print("COMPARABLE SALES")
        print("-" * 70)
        for i, c in enumerate(report.comparables, 1):
            print(f"\n  {i}. {c.address}")
            print(f"     Sale Price: ${c.sale_price:,} | Sale Date: {c.sale_date}")
            print(f"     {c.bedrooms}bd/{c.bathrooms}ba | {c.sqft:,} sqft | Built {c.year_built}")
            print(f"     Distance: {c.distance_miles} mi | Score: {c.comparability_score:.0%}")

            if c.adjustments:
                adj_str = ", ".join(f"{k}: ${v:+,}" for k, v in c.adjustments.items())
                print(f"     Adjustments: {adj_str}")

            print(f"     Adjusted Price: ${c.adjusted_price:,}")

        print("\n" + "-" * 70)
        print("MARKET CONTEXT")
        print("-" * 70)
        m = report.market_context
        print(f"  Median Price: ${m.median_price:,}")
        print(f"  Avg Days on Market: {m.avg_dom}")
        print(f"  Months of Supply: {m.months_supply:.1f}")
        print(f"  List-to-Sale Ratio: {m.list_to_sale_ratio:.0%}")
        print(f"  Market Type: {m.market_type.title()}'s Market")
        print(f"  Trend: {m.trend.title()}")

        print("\n" + "-" * 70)
        print("RECOMMENDATIONS")
        print("-" * 70)
        for key, value in report.recommendations.items():
            print(f"\n  {key.replace('_', ' ').title()}:")
            print(f"    {value}")

        print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
