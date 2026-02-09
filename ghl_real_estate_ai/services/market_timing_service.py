"""
Market Timing Service for Enhanced Property Matching

Analyzes market conditions and timing opportunities:
- Days on market trends and negotiation opportunities
- Price reduction history and seller motivation
- Inventory scarcity by neighborhood and price segment
- Competition level assessment
- Optimal timing recommendations
- Seasonal market patterns
"""

import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.matching_models import MarketTimingScore

logger = get_logger(__name__)


class MarketTimingService:
    """
    Service for analyzing market timing and opportunity factors.

    Provides insights on:
    - Property market position (hot vs. stale listings)
    - Negotiation opportunities
    - Market urgency indicators
    - Competitive environment analysis
    - Optimal buyer timing recommendations
    """

    def __init__(self):
        """Initialize the market timing service."""
        self._load_property_data()
        self._load_market_history()
        self._calculate_market_benchmarks()

    def calculate_market_timing_score(
        self, property_data: Dict[str, Any], market_context: Optional[Dict[str, Any]] = None
    ) -> MarketTimingScore:
        """
        Calculate comprehensive market timing score for a property.

        Args:
            property_data: Property information including days on market, price history
            market_context: Optional market conditions context

        Returns:
            MarketTimingScore with detailed timing analysis
        """
        property_id = property_data.get("id", "unknown")
        logger.info(f"Calculating market timing score for property {property_id}")

        # Extract key timing factors
        days_on_market = property_data.get("days_on_market", 0)
        current_price = property_data.get("price", 0)
        neighborhood = property_data.get("address", {}).get("neighborhood", "")
        property_type = property_data.get("property_type", "")

        # Calculate individual timing factors
        dom_score = self._calculate_dom_score(days_on_market)
        price_trend_score = self._calculate_price_trend_score(property_data)
        inventory_score = self._calculate_inventory_scarcity_score(neighborhood, property_type, current_price)

        # Assess competition level
        competition_level = self._assess_competition_level(days_on_market, neighborhood, property_type)

        # Calculate overall timing score
        optimal_timing_score = self._calculate_optimal_timing_score(dom_score, price_trend_score, inventory_score)

        # Determine urgency indicator
        urgency_indicator = self._determine_urgency_indicator(days_on_market, competition_level, inventory_score)

        # Generate reasoning
        reasoning = self._generate_timing_reasoning(
            days_on_market, competition_level, price_trend_score, inventory_score
        )

        return MarketTimingScore(
            days_on_market_score=dom_score,
            price_trend_score=price_trend_score,
            inventory_scarcity_score=inventory_score,
            competition_level=competition_level,
            optimal_timing_score=optimal_timing_score,
            urgency_indicator=urgency_indicator,
            reasoning=reasoning,
        )

    def get_market_opportunity_insights(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed market opportunity insights for agent use.

        Returns:
            Dict with negotiation strategies, timing advice, and market context
        """
        timing_score = self.calculate_market_timing_score(property_data)

        days_on_market = property_data.get("days_on_market", 0)
        current_price = property_data.get("price", 0)

        insights = {
            "negotiation_opportunity": self._assess_negotiation_opportunity(days_on_market),
            "seller_motivation": self._assess_seller_motivation(days_on_market, property_data),
            "market_position": self._assess_market_position(timing_score),
            "recommended_actions": self._get_recommended_actions(timing_score),
            "price_guidance": self._get_price_guidance(property_data, timing_score),
            "timing_advice": self._get_timing_advice(timing_score),
        }

        return insights

    def analyze_neighborhood_market(
        self, neighborhood: str, property_type: str = "", price_range: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Analyze market conditions for a specific neighborhood.

        Args:
            neighborhood: Target neighborhood
            property_type: Optional property type filter
            price_range: Optional price range filter (min, max)

        Returns:
            Neighborhood market analysis
        """
        # Filter properties for this neighborhood
        neighborhood_props = [
            prop
            for prop in self.property_data
            if prop.get("address", {}).get("neighborhood", "").lower() == neighborhood.lower()
        ]

        if property_type:
            neighborhood_props = [
                prop for prop in neighborhood_props if property_type.lower() in prop.get("property_type", "").lower()
            ]

        if price_range:
            min_price, max_price = price_range
            neighborhood_props = [prop for prop in neighborhood_props if min_price <= prop.get("price", 0) <= max_price]

        if not neighborhood_props:
            return self._create_empty_market_analysis(neighborhood)

        # Calculate market metrics
        avg_dom = statistics.mean([prop.get("days_on_market", 0) for prop in neighborhood_props])
        median_price = statistics.median([prop.get("price", 0) for prop in neighborhood_props])
        inventory_count = len(neighborhood_props)

        # Market velocity assessment
        velocity = self._calculate_market_velocity(neighborhood_props)

        # Price trend analysis
        price_trend = self._analyze_neighborhood_price_trend(neighborhood_props)

        return {
            "neighborhood": neighborhood,
            "property_type": property_type or "All Types",
            "inventory_count": inventory_count,
            "avg_days_on_market": round(avg_dom, 1),
            "median_price": median_price,
            "market_velocity": velocity,
            "price_trend": price_trend,
            "market_temperature": self._assess_market_temperature(avg_dom, inventory_count),
            "buyer_advantage": self._assess_buyer_advantage(avg_dom, inventory_count),
            "last_updated": datetime.utcnow().isoformat(),
        }

    # Core calculation methods

    def _calculate_dom_score(self, days_on_market: int) -> float:
        """
        Calculate days on market opportunity score.

        Logic:
        - 0-7 days: Hot property, low negotiation power (0.2-0.4)
        - 8-21 days: Normal market time, moderate opportunity (0.5-0.6)
        - 22-60 days: Extended time, good opportunity (0.7-0.8)
        - 60+ days: Stale listing, high negotiation potential (0.9-1.0)
        """
        if days_on_market <= 7:
            # Hot property - limited negotiation opportunity
            return 0.2 + (days_on_market / 7) * 0.2
        elif days_on_market <= 21:
            # Normal market time
            return 0.4 + ((days_on_market - 7) / 14) * 0.2
        elif days_on_market <= 60:
            # Extended time - increasing opportunity
            return 0.6 + ((days_on_market - 21) / 39) * 0.2
        else:
            # Stale listing - high opportunity
            return min(1.0, 0.8 + ((days_on_market - 60) / 120) * 0.2)

    def _calculate_price_trend_score(self, property_data: Dict[str, Any]) -> float:
        """
        Calculate price trend opportunity score.

        For now, uses basic heuristics. In production, would analyze:
        - Price reduction history
        - Original listing price vs. current
        - Time since last price change
        """
        days_on_market = property_data.get("days_on_market", 0)
        current_price = property_data.get("price", 0)

        # Estimate price reductions based on DOM (heuristic)
        if days_on_market > 45:
            # Likely price reduced
            estimated_reductions = min(3, days_on_market // 30)
            return 0.7 + (estimated_reductions * 0.1)
        elif days_on_market > 21:
            # Possibly price reduced
            return 0.6
        else:
            # Likely original price
            return 0.3

    def _calculate_inventory_scarcity_score(self, neighborhood: str, property_type: str, price: int) -> float:
        """
        Calculate inventory scarcity score for the market segment.

        Higher scarcity = higher score = more urgency to act
        """
        # Filter similar properties
        similar_props = self._find_similar_properties(neighborhood, property_type, price)

        inventory_count = len(similar_props)

        # Scarcity scoring
        if inventory_count <= 2:
            return 1.0  # Very scarce
        elif inventory_count <= 5:
            return 0.8  # Scarce
        elif inventory_count <= 10:
            return 0.6  # Moderate supply
        elif inventory_count <= 20:
            return 0.4  # Good supply
        else:
            return 0.2  # Abundant supply

    def _assess_competition_level(self, days_on_market: int, neighborhood: str, property_type: str) -> str:
        """Assess competition level for the property."""
        # Get market benchmarks for this area
        benchmark_dom = self.market_benchmarks.get("avg_dom_by_neighborhood", {}).get(neighborhood.lower(), 30)

        if days_on_market < benchmark_dom * 0.5:
            return "high"  # Moving much faster than average
        elif days_on_market < benchmark_dom:
            return "medium"
        else:
            return "low"

    def _calculate_optimal_timing_score(
        self, dom_score: float, price_trend_score: float, inventory_score: float
    ) -> float:
        """
        Calculate overall optimal timing score.

        Weights:
        - DOM score: 50% (negotiation opportunity)
        - Price trend: 30% (price reduction opportunity)
        - Inventory scarcity: 20% (market urgency)
        """
        return dom_score * 0.5 + price_trend_score * 0.3 + inventory_score * 0.2

    def _determine_urgency_indicator(self, days_on_market: int, competition_level: str, inventory_score: float) -> str:
        """Determine buyer urgency indicator."""
        # High inventory scarcity or high competition = act fast
        if inventory_score >= 0.8 or competition_level == "high":
            return "act_fast"
        # Extended DOM with moderate inventory = good time to buy
        elif days_on_market >= 21 and inventory_score <= 0.6:
            return "good_time"
        # Abundant supply or very long DOM = can wait
        else:
            return "can_wait"

    def _generate_timing_reasoning(
        self, days_on_market: int, competition_level: str, price_trend_score: float, inventory_score: float
    ) -> str:
        """Generate human-readable timing reasoning."""
        reasoning_parts = []

        # Days on market analysis
        if days_on_market < 7:
            reasoning_parts.append(f"Fresh listing ({days_on_market} days) - expect multiple offers")
        elif days_on_market < 21:
            reasoning_parts.append(f"Normal market time ({days_on_market} days)")
        elif days_on_market < 60:
            reasoning_parts.append(f"Extended time on market ({days_on_market} days) - negotiation opportunity")
        else:
            reasoning_parts.append(f"Long time on market ({days_on_market} days) - high negotiation potential")

        # Competition analysis
        if competition_level == "high":
            reasoning_parts.append("high competition in area")
        elif competition_level == "low":
            reasoning_parts.append("low competition - buyer's market")

        # Inventory analysis
        if inventory_score >= 0.8:
            reasoning_parts.append("limited similar inventory")
        elif inventory_score <= 0.3:
            reasoning_parts.append("abundant similar options")

        # Price trend analysis
        if price_trend_score >= 0.7:
            reasoning_parts.append("likely price reductions")

        return "; ".join(reasoning_parts)

    # Market analysis helper methods

    def _find_similar_properties(self, neighborhood: str, property_type: str, price: int) -> List[Dict[str, Any]]:
        """Find similar properties for inventory analysis."""
        price_range = 0.15  # ±15% price range
        min_price = price * (1 - price_range)
        max_price = price * (1 + price_range)

        similar_properties = []
        for prop in self.property_data:
            prop_neighborhood = prop.get("address", {}).get("neighborhood", "").lower()
            prop_type = prop.get("property_type", "").lower()
            prop_price = prop.get("price", 0)

            # Match criteria
            neighborhood_match = neighborhood.lower() in prop_neighborhood
            type_match = property_type.lower() in prop_type
            price_match = min_price <= prop_price <= max_price

            if neighborhood_match and type_match and price_match:
                similar_properties.append(prop)

        return similar_properties

    def _calculate_market_velocity(self, properties: List[Dict[str, Any]]) -> str:
        """Calculate market velocity (how fast properties sell)."""
        if not properties:
            return "unknown"

        avg_dom = statistics.mean([prop.get("days_on_market", 0) for prop in properties])

        if avg_dom < 14:
            return "very_fast"
        elif avg_dom < 28:
            return "fast"
        elif avg_dom < 45:
            return "moderate"
        else:
            return "slow"

    def _analyze_neighborhood_price_trend(self, properties: List[Dict[str, Any]]) -> str:
        """Analyze price trends in the neighborhood."""
        # Simplified trend analysis based on DOM distribution
        dom_values = [prop.get("days_on_market", 0) for prop in properties]

        if not dom_values:
            return "stable"

        # If most properties are moving quickly, prices may be trending up
        fast_movers = sum(1 for dom in dom_values if dom < 21)
        slow_movers = sum(1 for dom in dom_values if dom > 45)

        fast_ratio = fast_movers / len(dom_values)
        slow_ratio = slow_movers / len(dom_values)

        if fast_ratio > 0.6:
            return "rising"
        elif slow_ratio > 0.4:
            return "declining"
        else:
            return "stable"

    def _assess_market_temperature(self, avg_dom: float, inventory_count: int) -> str:
        """Assess overall market temperature."""
        if avg_dom < 14 and inventory_count < 10:
            return "hot"
        elif avg_dom < 28 and inventory_count < 20:
            return "warm"
        elif avg_dom > 45 or inventory_count > 30:
            return "cold"
        else:
            return "balanced"

    def _assess_buyer_advantage(self, avg_dom: float, inventory_count: int) -> str:
        """Assess buyer advantage level."""
        if avg_dom > 45 and inventory_count > 20:
            return "high"
        elif avg_dom > 30 or inventory_count > 15:
            return "moderate"
        else:
            return "low"

    # Market opportunity analysis methods

    def _assess_negotiation_opportunity(self, days_on_market: int) -> Dict[str, Any]:
        """Assess negotiation opportunity and strategies."""
        if days_on_market < 7:
            return {
                "level": "low",
                "strategies": ["Full asking price", "Attractive terms", "Quick close"],
                "expected_discount": "0-1%",
            }
        elif days_on_market < 21:
            return {
                "level": "moderate",
                "strategies": ["Reasonable offer", "Ask for repairs", "Negotiate closing costs"],
                "expected_discount": "1-3%",
            }
        elif days_on_market < 60:
            return {
                "level": "good",
                "strategies": ["Below asking price", "Request concessions", "Inspect everything"],
                "expected_discount": "3-8%",
            }
        else:
            return {
                "level": "high",
                "strategies": ["Aggressive pricing", "Major concessions", "Take your time"],
                "expected_discount": "8-15%",
            }

    def _assess_seller_motivation(self, days_on_market: int, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess seller motivation level."""
        motivation_score = 0
        factors = []

        # Days on market factor
        if days_on_market > 60:
            motivation_score += 3
            factors.append("Extended time on market")
        elif days_on_market > 30:
            motivation_score += 2
            factors.append("Longer than average DOM")

        # Property features that suggest motivation
        description = property_data.get("description", "").lower()
        features = property_data.get("features", [])
        all_text = " ".join([description] + features).lower()

        motivation_indicators = {
            "motivated": 2,
            "priced to sell": 2,
            "must sell": 3,
            "relocated": 2,
            "job transfer": 2,
            "bring offers": 1,
        }

        for indicator, score in motivation_indicators.items():
            if indicator in all_text:
                motivation_score += score
                factors.append(f"'{indicator}' mentioned")

        # Determine motivation level
        if motivation_score >= 5:
            level = "very_high"
        elif motivation_score >= 3:
            level = "high"
        elif motivation_score >= 1:
            level = "moderate"
        else:
            level = "low"

        return {"level": level, "score": motivation_score, "factors": factors}

    def _assess_market_position(self, timing_score: MarketTimingScore) -> str:
        """Assess the property's position in the market."""
        if timing_score.competition_level == "high" and timing_score.days_on_market_score < 0.4:
            return "hot_property"
        elif timing_score.optimal_timing_score > 0.8:
            return "great_opportunity"
        elif timing_score.optimal_timing_score > 0.6:
            return "good_opportunity"
        elif timing_score.optimal_timing_score > 0.4:
            return "fair_opportunity"
        else:
            return "competitive_market"

    def _get_recommended_actions(self, timing_score: MarketTimingScore) -> List[str]:
        """Get recommended actions based on market timing."""
        actions = []

        if timing_score.urgency_indicator == "act_fast":
            actions.extend(
                [
                    "Schedule showing immediately",
                    "Prepare competitive offer",
                    "Get pre-approval ready",
                    "Consider waiving contingencies",
                ]
            )
        elif timing_score.urgency_indicator == "good_time":
            actions.extend(
                [
                    "Schedule showing this week",
                    "Prepare reasonable offer",
                    "Include standard contingencies",
                    "Plan negotiation strategy",
                ]
            )
        else:  # can_wait
            actions.extend(
                [
                    "Take time to evaluate",
                    "Compare with other options",
                    "Plan strategic offer",
                    "Include buyer-favorable terms",
                ]
            )

        if timing_score.days_on_market_score > 0.7:
            actions.append("Negotiate price reduction")

        return actions

    def _get_price_guidance(self, property_data: Dict[str, Any], timing_score: MarketTimingScore) -> Dict[str, Any]:
        """Get price guidance based on market timing."""
        asking_price = property_data.get("price", 0)

        # Calculate suggested offer range
        if timing_score.days_on_market_score > 0.8:
            # High negotiation opportunity
            offer_range = (0.85, 0.95)
        elif timing_score.days_on_market_score > 0.6:
            # Good negotiation opportunity
            offer_range = (0.92, 0.98)
        elif timing_score.competition_level == "high":
            # Competitive market
            offer_range = (0.98, 1.02)
        else:
            # Normal market
            offer_range = (0.95, 1.0)

        min_offer = int(asking_price * offer_range[0])
        max_offer = int(asking_price * offer_range[1])

        return {
            "asking_price": asking_price,
            "suggested_range": f"${min_offer:,} - ${max_offer:,}",
            "min_offer": min_offer,
            "max_offer": max_offer,
            "rationale": f"Based on {timing_score.days_on_market_score:.1%} negotiation opportunity",
        }

    def _get_timing_advice(self, timing_score: MarketTimingScore) -> str:
        """Get timing advice based on market analysis."""
        if timing_score.urgency_indicator == "act_fast":
            return "Move quickly - limited inventory and high competition"
        elif timing_score.urgency_indicator == "good_time":
            return "Good opportunity - reasonable timeline for due diligence"
        else:
            return "Take your time - buyer-favorable market conditions"

    # Data loading and setup methods

    def _load_property_data(self):
        """Load property listings data."""
        try:
            listings_path = Path(__file__).parent.parent / "data" / "knowledge_base" / "property_listings.json"
            with open(listings_path, "r") as f:
                data = json.load(f)
                self.property_data = data.get("listings", [])
        except Exception as e:
            logger.error(f"Failed to load property data: {e}")
            self.property_data = []

    def _load_market_history(self):
        """Load historical market data (placeholder for real implementation)."""
        # In production, this would load from:
        # - MLS historical data
        # - Price change history
        # - Seasonal patterns
        # - Economic indicators

        self.market_history = {
            "price_changes": {},  # property_id -> list of price changes
            "seasonal_patterns": {
                "spring": {"multiplier": 1.1, "description": "Peak buying season"},
                "summer": {"multiplier": 1.05, "description": "Active market"},
                "fall": {"multiplier": 0.95, "description": "Cooling market"},
                "winter": {"multiplier": 0.9, "description": "Slowest season"},
            },
        }

    def _calculate_market_benchmarks(self):
        """Calculate market benchmarks from current data."""
        if not self.property_data:
            self.market_benchmarks = {}
            return

        # Calculate average DOM by neighborhood
        neighborhood_dom = {}
        for prop in self.property_data:
            neighborhood = prop.get("address", {}).get("neighborhood", "").lower()
            dom = prop.get("days_on_market", 0)

            if neighborhood not in neighborhood_dom:
                neighborhood_dom[neighborhood] = []
            neighborhood_dom[neighborhood].append(dom)

        avg_dom_by_neighborhood = {
            neighborhood: statistics.mean(doms) for neighborhood, doms in neighborhood_dom.items() if doms
        }

        # Calculate overall market benchmarks
        all_doms = [prop.get("days_on_market", 0) for prop in self.property_data]
        all_prices = [prop.get("price", 0) for prop in self.property_data if prop.get("price")]

        self.market_benchmarks = {
            "avg_dom_by_neighborhood": avg_dom_by_neighborhood,
            "overall_avg_dom": statistics.mean(all_doms) if all_doms else 30,
            "median_price": statistics.median(all_prices) if all_prices else 500000,
            "total_inventory": len(self.property_data),
        }

    def _create_empty_market_analysis(self, neighborhood: str) -> Dict[str, Any]:
        """Create empty market analysis when no data is available."""
        return {
            "neighborhood": neighborhood,
            "inventory_count": 0,
            "avg_days_on_market": 0,
            "median_price": 0,
            "market_velocity": "unknown",
            "price_trend": "unknown",
            "market_temperature": "unknown",
            "buyer_advantage": "unknown",
            "error": "No data available for this area",
            "last_updated": datetime.utcnow().isoformat(),
        }


# Demo function
def demo_market_timing():
    """Demo the market timing service."""
    print("⏰ Market Timing Service Demo\n")

    service = MarketTimingService()

    # Test with different properties showing various market conditions
    test_properties = [
        {
            "id": "test_hot",
            "address": {"neighborhood": "Hyde Park"},
            "property_type": "Single Family",
            "price": 675000,
            "days_on_market": 5,
            "description": "Charming home in desirable area",
        },
        {
            "id": "test_stale",
            "address": {"neighborhood": "Steiner Ranch"},
            "property_type": "Single Family",
            "price": 725000,
            "days_on_market": 78,
            "description": "Luxury home, motivated seller, bring offers",
        },
        {
            "id": "test_normal",
            "address": {"neighborhood": "Circle C Ranch"},
            "property_type": "Single Family",
            "price": 520000,
            "days_on_market": 24,
            "description": "Well-maintained family home",
        },
    ]

    for prop in test_properties:
        print(f"\n{'=' * 60}")
        print(f"Property: {prop['address']['neighborhood']} - {prop['days_on_market']} DOM")
        print(f"Price: ${prop['price']:,}")
        print(f"{'=' * 60}")

        timing_score = service.calculate_market_timing_score(prop)

        print(f"\n⏱️  Days on Market Score: {timing_score.days_on_market_score:.2f}")
        print(f"📈 Price Trend Score: {timing_score.price_trend_score:.2f}")
        print(f"📦 Inventory Scarcity: {timing_score.inventory_scarcity_score:.2f}")
        print(f"🏆 Overall Timing Score: {timing_score.optimal_timing_score:.2f}")
        print(f"🚨 Urgency: {timing_score.urgency_indicator.replace('_', ' ').title()}")
        print(f"🔥 Competition: {timing_score.competition_level.title()}")
        print(f"💡 Reasoning: {timing_score.reasoning}")

        # Get market insights
        insights = service.get_market_opportunity_insights(prop)

        print(f"\n📊 Negotiation Opportunity: {insights['negotiation_opportunity']['level'].title()}")
        print(f"   Expected Discount: {insights['negotiation_opportunity']['expected_discount']}")

        print(f"\n💰 Price Guidance:")
        print(f"   Suggested Offer Range: {insights['price_guidance']['suggested_range']}")

        print(f"\n🎯 Recommended Actions:")
        for action in insights["recommended_actions"][:3]:
            print(f"   • {action}")


if __name__ == "__main__":
    demo_market_timing()
