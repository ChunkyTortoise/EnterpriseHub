"""
Instant CMA (Comparative Market Analysis) Generator
Create professional market analysis reports in 2 minutes

This service generates comprehensive CMA reports including:
- Comparable properties analysis
- Market trends and statistics
- Price recommendations
- Beautiful PDF exports for client presentations
"""

import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class ComparableProperty:
    """Comparable property data"""

    address: str
    bedrooms: int
    bathrooms: float
    sqft: int
    price: int
    sold_date: str
    days_on_market: int
    price_per_sqft: float
    distance_miles: float
    similarity_score: float


class InstantCMAGenerator:
    """Service for generating Comparative Market Analysis reports"""

    def __init__(self):
        pass

    def generate_cma(
        self,
        subject_property: Dict[str, Any],
        comparables: List[Dict[str, Any]] = None,
        analysis_type: str = "listing",
        market_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive CMA report

        Args:
            subject_property: Property being analyzed
            comparables: List of comparable properties (auto-generated if None)
            analysis_type: "listing" or "buying"
            market_data: Optional market statistics

        Returns:
            Complete CMA report with analysis and recommendations
        """
        # Generate comparables if not provided
        if comparables is None:
            comparables = self._generate_sample_comparables(subject_property)

        # Calculate price recommendation
        price_analysis = self._analyze_pricing(subject_property, comparables)

        # Market analysis
        market_analysis = self._analyze_market_trends(market_data or {})

        # Generate insights
        insights = self._generate_insights(subject_property, comparables, price_analysis, market_analysis)

        # Compile report
        report = {
            "report_id": f"CMA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "subject_property": subject_property,
            "comparables": comparables,
            "price_analysis": price_analysis,
            "market_analysis": market_analysis,
            "insights": insights,
            "recommendations": self._generate_recommendations(price_analysis, market_analysis, analysis_type),
            "executive_summary": self._generate_executive_summary(subject_property, price_analysis, market_analysis),
        }

        return report

    def _generate_sample_comparables(self, subject_property: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate sample comparable properties"""

        base_price = subject_property.get("price", 500000)
        base_sqft = subject_property.get("sqft", 2000)
        bedrooms = subject_property.get("bedrooms", 3)
        bathrooms = subject_property.get("bathrooms", 2)

        comparables = []

        # Generate 5-8 comparables
        for i in range(6):
            # Vary properties slightly
            sqft_variance = base_sqft * (0.9 + (i * 0.05))
            price_variance = base_price * (0.92 + (i * 0.04))

            comp = {
                "address": f"{100 + i * 10} {['Oak', 'Maple', 'Pine', 'Elm', 'Cedar', 'Birch'][i]} Street",
                "bedrooms": bedrooms + (1 if i % 3 == 0 else 0),
                "bathrooms": bathrooms + (0.5 if i % 2 == 0 else 0),
                "sqft": int(sqft_variance),
                "price": int(price_variance),
                "sold_date": (datetime.utcnow() - timedelta(days=15 + i * 10)).strftime("%Y-%m-%d"),
                "days_on_market": 20 + i * 5,
                "price_per_sqft": price_variance / sqft_variance,
                "distance_miles": 0.5 + (i * 0.2),
                "similarity_score": 95 - (i * 2),
            }
            comparables.append(comp)

        return comparables

    def _analyze_pricing(self, subject_property: Dict[str, Any], comparables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze pricing based on comparables"""

        # Get comparable prices
        comp_prices = [c["price"] for c in comparables]
        comp_price_per_sqft = [c.get("price_per_sqft", c["price"] / c["sqft"]) for c in comparables]

        # Calculate statistics
        avg_price = statistics.mean(comp_prices)
        median_price = statistics.median(comp_prices)
        avg_price_per_sqft = statistics.mean(comp_price_per_sqft)

        # Price range
        min_price = min(comp_prices)
        max_price = max(comp_prices)

        # Calculate subject property value
        subject_sqft = subject_property.get("sqft", 2000)
        estimated_value = avg_price_per_sqft * subject_sqft

        # Confidence ranges
        low_estimate = estimated_value * 0.95
        high_estimate = estimated_value * 1.05

        return {
            "estimated_value": int(estimated_value),
            "price_range": {
                "low": int(low_estimate),
                "mid": int(estimated_value),
                "high": int(high_estimate),
            },
            "price_per_sqft": round(avg_price_per_sqft, 2),
            "comparables_analysis": {
                "average_price": int(avg_price),
                "median_price": int(median_price),
                "price_range": f"${min_price:,} - ${max_price:,}",
                "sample_size": len(comparables),
            },
            "confidence_level": "High" if len(comparables) >= 5 else "Medium",
        }

    def _analyze_market_trends(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current market trends"""

        # Use provided data or generate sample
        days_on_market = market_data.get("avg_days_on_market", 35)
        inventory_levels = market_data.get("inventory_months", 2.5)
        price_trend = market_data.get("price_trend_percentage", 5.2)

        # Determine market type
        if inventory_levels < 3:
            market_type = "Seller's Market"
            market_strength = "Strong"
        elif inventory_levels > 6:
            market_type = "Buyer's Market"
            market_strength = "Weak"
        else:
            market_type = "Balanced Market"
            market_strength = "Moderate"

        return {
            "market_type": market_type,
            "market_strength": market_strength,
            "avg_days_on_market": days_on_market,
            "inventory_months": inventory_levels,
            "price_trend": {
                "percentage": price_trend,
                "direction": "increasing" if price_trend > 0 else "decreasing",
                "timeframe": "12 months",
            },
            "market_velocity": ("Fast" if days_on_market < 30 else "Moderate" if days_on_market < 60 else "Slow"),
            "competition_level": ("High" if inventory_levels < 3 else "Moderate" if inventory_levels < 6 else "Low"),
        }

    def _generate_insights(
        self,
        subject_property: Dict[str, Any],
        comparables: List[Dict[str, Any]],
        price_analysis: Dict[str, Any],
        market_analysis: Dict[str, Any],
    ) -> List[str]:
        """Generate actionable insights"""

        insights = []

        # Price positioning insight
        estimated_value = price_analysis["estimated_value"]
        asking_price = subject_property.get("price", estimated_value)

        if asking_price > estimated_value * 1.05:
            insights.append(
                f"⚠️ Property is priced {((asking_price / estimated_value - 1) * 100):.1f}% above market value. Consider adjusting to ${estimated_value:,} for faster sale."
            )
        elif asking_price < estimated_value * 0.95:
            insights.append(
                f"💰 Property is priced {((1 - asking_price / estimated_value) * 100):.1f}% below market value. Great opportunity for buyers!"
            )
        else:
            insights.append(f"✅ Property is priced competitively at market value (${estimated_value:,}).")

        # Market condition insight
        if market_analysis["market_type"] == "Seller's Market":
            insights.append(
                f"🔥 Strong seller's market with only {market_analysis['inventory_months']} months of inventory. Expect multiple offers."
            )
        elif market_analysis["market_type"] == "Buyer's Market":
            insights.append(
                f"🎯 Buyer's market with {market_analysis['inventory_months']} months of inventory. Pricing and marketing critical."
            )

        # Days on market insight
        avg_dom = market_analysis["avg_days_on_market"]
        insights.append(
            f"📅 Properties are selling in an average of {avg_dom} days. Price competitively to meet this benchmark."
        )

        # Price trend insight
        price_trend = market_analysis["price_trend"]["percentage"]
        if price_trend > 3:
            insights.append(f"📈 Market appreciating at {price_trend}% annually. Prices expected to continue rising.")
        elif price_trend < -3:
            insights.append(f"📉 Market declining {abs(price_trend)}% annually. Act quickly to secure value.")

        # Competitive positioning
        comp_count = len(comparables)
        insights.append(f"🏘️ {comp_count} highly comparable properties analyzed. Strong data confidence.")

        return insights

    def _generate_recommendations(
        self,
        price_analysis: Dict[str, Any],
        market_analysis: Dict[str, Any],
        analysis_type: str,
    ) -> Dict[str, Any]:
        """Generate pricing and strategy recommendations"""

        recommendations = {"pricing": {}, "timing": {}, "strategy": []}

        estimated_value = price_analysis["estimated_value"]
        price_range = price_analysis["price_range"]

        if analysis_type == "listing":
            # Listing recommendations
            if market_analysis["market_type"] == "Seller's Market":
                recommendations["pricing"] = {
                    "list_price": price_range["high"],
                    "rationale": "Strong market - list at higher end of range",
                    "flexibility": "Expect offers at or above asking",
                }
            else:
                recommendations["pricing"] = {
                    "list_price": price_range["mid"],
                    "rationale": "Competitive pricing for current market",
                    "flexibility": "Be prepared to negotiate",
                }

            recommendations["timing"] = {
                "best_time": "Spring (March-May) typically sees highest activity",
                "days_to_sell": market_analysis["avg_days_on_market"],
                "urgency": ("High" if market_analysis["market_velocity"] == "Fast" else "Moderate"),
            }

            recommendations["strategy"] = [
                "Professional photos and staging recommended",
                "Price competitively from day one",
                f"Plan for {market_analysis['avg_days_on_market']} days on market",
                "Consider pre-inspection to address issues upfront",
            ]

        else:  # buying
            recommendations["pricing"] = {
                "offer_price": price_range["low"],
                "rationale": "Start with competitive offer",
                "max_price": price_range["high"],
            }

            recommendations["timing"] = {
                "best_time": "Off-season (Nov-Jan) for better negotiating",
                "urgency": ("High" if market_analysis["market_type"] == "Seller's Market" else "Low"),
            }

            recommendations["strategy"] = [
                "Get pre-approved before making offers",
                "Act quickly in competitive situations",
                "Consider escalation clause if needed",
                "Professional inspection is essential",
            ]

        return recommendations

    def _generate_executive_summary(
        self,
        subject_property: Dict[str, Any],
        price_analysis: Dict[str, Any],
        market_analysis: Dict[str, Any],
    ) -> str:
        """Generate executive summary for the report"""

        address = subject_property.get("address", "Subject Property")
        estimated_value = price_analysis["estimated_value"]
        price_range = price_analysis["price_range"]
        market_type = market_analysis["market_type"]

        summary = f"**Comparative Market Analysis for {address}**\n\n"
        summary += f"**Estimated Market Value:** ${estimated_value:,}\n"
        summary += f"**Value Range:** ${price_range['low']:,} - ${price_range['high']:,}\n"
        summary += f"**Market Conditions:** {market_type}\n\n"

        summary += "**Key Findings:**\n"
        summary += (
            f"• Based on analysis of {price_analysis['comparables_analysis']['sample_size']} comparable properties\n"
        )
        summary += f"• Average price per sq ft: ${price_analysis['price_per_sqft']:.2f}\n"
        summary += f"• Properties selling in {market_analysis['avg_days_on_market']} days on average\n"
        summary += f"• Market trending {market_analysis['price_trend']['direction']} at {market_analysis['price_trend']['percentage']}% annually\n"

        return summary

    def export_to_pdf_data(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare report data for PDF export

        Args:
            report: CMA report

        Returns:
            PDF-ready data structure
        """
        return {
            "title": f"Comparative Market Analysis",
            "subtitle": report["subject_property"].get("address", ""),
            "date": datetime.utcnow().strftime("%B %d, %Y"),
            "sections": [
                {"title": "Executive Summary", "content": report["executive_summary"]},
                {"title": "Price Analysis", "content": report["price_analysis"]},
                {"title": "Market Trends", "content": report["market_analysis"]},
                {"title": "Comparable Properties", "content": report["comparables"]},
                {
                    "title": "Insights & Recommendations",
                    "content": {
                        "insights": report["insights"],
                        "recommendations": report["recommendations"],
                    },
                },
            ],
        }


# Demo function
def demo_cma_generator():
    """Demonstrate CMA generator"""
    service = InstantCMAGenerator()

    print("📊 Instant CMA Generator Demo\n")

    # Sample property
    subject_property = {
        "address": "456 Oak Avenue",
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1800,
        "price": 485000,
        "property_type": "single_family",
    }

    # Generate CMA
    report = service.generate_cma(subject_property, analysis_type="listing")

    print("=" * 70)
    print("COMPARATIVE MARKET ANALYSIS REPORT")
    print("=" * 70)
    print(f"\nReport ID: {report['report_id']}")
    print(f"Generated: {report['generated_at'][:19]}")

    print("\n" + "=" * 70)
    print("EXECUTIVE SUMMARY")
    print("=" * 70)
    print(report["executive_summary"])

    print("\n" + "=" * 70)
    print("PRICE ANALYSIS")
    print("=" * 70)
    pa = report["price_analysis"]
    print(f"Estimated Value: ${pa['estimated_value']:,}")
    print(f"Price Range: ${pa['price_range']['low']:,} - ${pa['price_range']['high']:,}")
    print(f"Price per Sq Ft: ${pa['price_per_sqft']:.2f}")
    print(f"Confidence: {pa['confidence_level']}")

    print("\n" + "=" * 70)
    print("MARKET ANALYSIS")
    print("=" * 70)
    ma = report["market_analysis"]
    print(f"Market Type: {ma['market_type']}")
    print(f"Market Strength: {ma['market_strength']}")
    print(f"Avg Days on Market: {ma['avg_days_on_market']}")
    print(f"Inventory: {ma['inventory_months']} months")
    print(f"Price Trend: {ma['price_trend']['percentage']}% {ma['price_trend']['direction']}")

    print("\n" + "=" * 70)
    print("KEY INSIGHTS")
    print("=" * 70)
    for insight in report["insights"]:
        print(f"  {insight}")

    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    rec = report["recommendations"]
    print(f"\nPricing:")
    print(f"  List Price: ${rec['pricing']['list_price']:,}")
    print(f"  Rationale: {rec['pricing']['rationale']}")

    print(f"\nStrategy:")
    for strategy in rec["strategy"]:
        print(f"  • {strategy}")

    print(f"\n{'=' * 70}\n")

    return service


if __name__ == "__main__":
    demo_cma_generator()
