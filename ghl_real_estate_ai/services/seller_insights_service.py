"""
Seller Insights Service for Real Estate AI.

Provides intelligent market analysis, pricing recommendations, and listing
optimization insights for seller leads using Claude and market data.

Key Features:
- Market analysis with comparable sales data
- Pricing recommendations based on home condition and market trends
- Listing optimization suggestions
- Seller motivation analysis
- Timeline and pathway recommendations (wholesale vs listing)
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

try:
    from ghl_real_estate_ai.core.llm_client import LLMClient
    from ghl_real_estate_ai.ghl_utils.config import settings
    from ghl_real_estate_ai.ghl_utils.logger import get_logger
except ImportError:
    # Fallback for streamlit demo context
    from core.llm_client import LLMClient
    from ghl_utils.config import settings
    from ghl_utils.logger import get_logger

logger = get_logger(__name__)


class SellingPathway(Enum):
    """Selling pathway options."""
    WHOLESALE = "wholesale"  # Quick cash sale, as-is
    LISTING = "listing"      # MLS listing for top dollar
    HYBRID = "hybrid"        # Try listing first, wholesale as backup


class HomeCondition(Enum):
    """Home condition categories."""
    EXCELLENT = "excellent"     # Move-in ready
    GOOD = "good"              # Minor cosmetic updates needed
    FAIR = "fair"              # Some repairs needed
    POOR = "poor"              # Major repairs/renovations needed


class MarketCondition(Enum):
    """Market condition categories."""
    BUYERS_MARKET = "buyers_market"     # High inventory, lower prices
    SELLERS_MARKET = "sellers_market"   # Low inventory, higher prices
    BALANCED = "balanced"               # Equilibrium


@dataclass
class ComparableSale:
    """Represents a comparable property sale."""
    address: str
    sale_price: int
    sale_date: datetime
    bedrooms: int
    bathrooms: int
    square_feet: int
    days_on_market: int
    price_per_sqft: float
    similarities: List[str]
    adjustments: Dict[str, int]


@dataclass
class MarketAnalysis:
    """Complete market analysis for seller property."""
    estimated_value_range: Tuple[int, int]  # (min, max)
    comparable_sales: List[ComparableSale]
    market_condition: MarketCondition
    days_on_market_estimate: int
    pricing_confidence: float  # 0.0 to 1.0
    market_trends: Dict[str, Any]
    neighborhood_insights: Dict[str, Any]


@dataclass
class PricingRecommendation:
    """Pricing strategy recommendation."""
    list_price: int
    price_range: Tuple[int, int]
    pricing_strategy: str
    reasoning: str
    expected_timeline: str
    confidence_level: float


@dataclass
class ListingOptimization:
    """Listing optimization recommendations."""
    recommended_improvements: List[Dict[str, Any]]
    staging_suggestions: List[str]
    photography_tips: List[str]
    marketing_highlights: List[str]
    potential_roi: Dict[str, int]


@dataclass
class SellerInsights:
    """Complete seller insights package."""
    market_analysis: MarketAnalysis
    pricing_recommendation: PricingRecommendation
    pathway_recommendation: SellingPathway
    listing_optimization: Optional[ListingOptimization]
    timeline_analysis: Dict[str, Any]
    claude_summary: str
    confidence_score: float
    next_steps: List[str]


class SellerInsightsService:
    """
    Provides intelligent insights and recommendations for seller leads.

    Integrates market data analysis with Claude-powered insights to help
    sellers understand their options and make informed decisions.
    """

    def __init__(self, tenant_id: str, llm_client: Optional[LLMClient] = None):
        """
        Initialize seller insights service.

        Args:
            tenant_id: Tenant identifier for multi-tenant support
            llm_client: Optional LLM client for testing
        """
        self.tenant_id = tenant_id
        self.llm_client = llm_client or LLMClient(
            provider="claude",
            model=settings.claude_model
        )

        # Market data cache (would be real data in production)
        self.market_data_cache = {}

        logger.info(f"Seller insights service initialized for tenant {tenant_id}")

    async def generate_seller_insights(
        self,
        contact_id: str,
        extracted_preferences: Dict[str, Any],
        conversation_context: Optional[Dict[str, Any]] = None,
        property_details: Optional[Dict[str, Any]] = None
    ) -> SellerInsights:
        """
        Generate comprehensive insights for a seller lead.

        Args:
            contact_id: Contact identifier
            extracted_preferences: Lead's stated preferences and details
            conversation_context: Conversation history and context
            property_details: Optional property details if available

        Returns:
            SellerInsights with market analysis and recommendations
        """
        try:
            # 1. Analyze seller motivation and timeline
            motivation_analysis = await self._analyze_seller_motivation(
                extracted_preferences,
                conversation_context
            )

            # 2. Determine home condition and features
            home_condition = self._determine_home_condition(extracted_preferences)

            # 3. Generate market analysis
            market_analysis = await self._generate_market_analysis(
                extracted_preferences,
                property_details,
                home_condition
            )

            # 4. Calculate pricing recommendations
            pricing_recommendation = await self._calculate_pricing_recommendation(
                market_analysis,
                home_condition,
                motivation_analysis
            )

            # 5. Recommend optimal selling pathway
            pathway_recommendation = await self._recommend_selling_pathway(
                market_analysis,
                home_condition,
                motivation_analysis,
                pricing_recommendation
            )

            # 6. Generate listing optimization (if applicable)
            listing_optimization = None
            if pathway_recommendation in [SellingPathway.LISTING, SellingPathway.HYBRID]:
                listing_optimization = await self._generate_listing_optimization(
                    extracted_preferences,
                    home_condition,
                    market_analysis
                )

            # 7. Analyze timeline expectations
            timeline_analysis = await self._analyze_timeline_expectations(
                pathway_recommendation,
                market_analysis,
                motivation_analysis
            )

            # 8. Generate Claude-powered summary
            claude_summary = await self._generate_claude_summary(
                market_analysis,
                pricing_recommendation,
                pathway_recommendation,
                motivation_analysis,
                extracted_preferences
            )

            # 9. Calculate overall confidence score
            confidence_score = self._calculate_confidence_score(
                market_analysis,
                pricing_recommendation,
                extracted_preferences
            )

            # 10. Generate next steps
            next_steps = self._generate_next_steps(
                pathway_recommendation,
                market_analysis,
                motivation_analysis
            )

            return SellerInsights(
                market_analysis=market_analysis,
                pricing_recommendation=pricing_recommendation,
                pathway_recommendation=pathway_recommendation,
                listing_optimization=listing_optimization,
                timeline_analysis=timeline_analysis,
                claude_summary=claude_summary,
                confidence_score=confidence_score,
                next_steps=next_steps
            )

        except Exception as e:
            logger.error(f"Failed to generate seller insights: {str(e)}")
            return await self._fallback_seller_insights(extracted_preferences)

    async def _analyze_seller_motivation(
        self,
        extracted_preferences: Dict[str, Any],
        conversation_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze seller's motivation and urgency level."""
        motivation = extracted_preferences.get("motivation", "").lower()
        timeline = extracted_preferences.get("timeline", "").lower()

        # Determine urgency level
        urgency_indicators = [
            "asap", "urgent", "immediately", "soon", "quickly",
            "relocating", "divorce", "foreclosure", "financial"
        ]

        urgency_level = "medium"
        if any(indicator in motivation + timeline for indicator in urgency_indicators):
            urgency_level = "high"
        elif any(indicator in motivation + timeline for indicator in ["eventually", "someday", "future", "maybe"]):
            urgency_level = "low"

        # Determine motivation category
        motivation_categories = {
            "relocation": ["moving", "relocating", "job", "transfer", "new city"],
            "financial": ["financial", "cash", "debt", "money", "afford"],
            "family": ["family", "kids", "school", "growing", "downsizing"],
            "lifestyle": ["lifestyle", "change", "retirement", "upgrade"],
            "distress": ["divorce", "foreclosure", "death", "illness", "emergency"]
        }

        motivation_category = "general"
        for category, keywords in motivation_categories.items():
            if any(keyword in motivation for keyword in keywords):
                motivation_category = category
                break

        return {
            "urgency_level": urgency_level,
            "motivation_category": motivation_category,
            "raw_motivation": motivation,
            "timeline_preference": timeline,
            "flexibility_score": self._calculate_flexibility_score(urgency_level, motivation_category)
        }

    def _determine_home_condition(self, extracted_preferences: Dict[str, Any]) -> HomeCondition:
        """Determine home condition from extracted preferences."""
        home_condition = extracted_preferences.get("home_condition", "").lower()

        if any(word in home_condition for word in ["excellent", "perfect", "move-in", "updated", "new"]):
            return HomeCondition.EXCELLENT
        elif any(word in home_condition for word in ["good", "well-maintained", "minor"]):
            return HomeCondition.GOOD
        elif any(word in home_condition for word in ["fair", "some work", "cosmetic", "dated"]):
            return HomeCondition.FAIR
        elif any(word in home_condition for word in ["poor", "needs work", "fixer", "repairs", "renovation"]):
            return HomeCondition.POOR
        else:
            return HomeCondition.GOOD  # Default assumption

    async def _generate_market_analysis(
        self,
        extracted_preferences: Dict[str, Any],
        property_details: Optional[Dict[str, Any]],
        home_condition: HomeCondition
    ) -> MarketAnalysis:
        """Generate market analysis with comparable sales."""
        location = extracted_preferences.get("location", "")

        # In production, this would fetch real market data
        # For now, we'll generate realistic sample data
        comparable_sales = await self._fetch_comparable_sales(location, extracted_preferences)

        # Determine market condition
        market_condition = await self._assess_market_condition(location)

        # Calculate value range from comparables
        if comparable_sales:
            prices = [comp.sale_price for comp in comparable_sales]
            avg_price = sum(prices) / len(prices)
            price_variance = 0.1  # 10% variance

            estimated_min = int(avg_price * (1 - price_variance))
            estimated_max = int(avg_price * (1 + price_variance))

            # Adjust for home condition
            condition_multipliers = {
                HomeCondition.EXCELLENT: 1.05,
                HomeCondition.GOOD: 1.0,
                HomeCondition.FAIR: 0.95,
                HomeCondition.POOR: 0.85
            }

            multiplier = condition_multipliers[home_condition]
            estimated_min = int(estimated_min * multiplier)
            estimated_max = int(estimated_max * multiplier)
        else:
            # Fallback estimates
            estimated_min = 300000
            estimated_max = 400000

        # Calculate days on market estimate
        if comparable_sales:
            avg_dom = sum(comp.days_on_market for comp in comparable_sales) / len(comparable_sales)
            days_on_market_estimate = int(avg_dom)
        else:
            days_on_market_estimate = 45  # Default

        return MarketAnalysis(
            estimated_value_range=(estimated_min, estimated_max),
            comparable_sales=comparable_sales,
            market_condition=market_condition,
            days_on_market_estimate=days_on_market_estimate,
            pricing_confidence=0.8 if comparable_sales else 0.5,
            market_trends=await self._analyze_market_trends(location),
            neighborhood_insights=await self._analyze_neighborhood_insights(location)
        )

    async def _calculate_pricing_recommendation(
        self,
        market_analysis: MarketAnalysis,
        home_condition: HomeCondition,
        motivation_analysis: Dict[str, Any]
    ) -> PricingRecommendation:
        """Calculate optimal pricing strategy."""
        min_value, max_value = market_analysis.estimated_value_range
        urgency = motivation_analysis["urgency_level"]

        # Base pricing strategy
        if urgency == "high":
            # Price aggressively for quick sale
            list_price = int(min_value + (max_value - min_value) * 0.2)
            strategy = "aggressive"
            timeline = "2-4 weeks"
        elif urgency == "low":
            # Price optimistically for maximum value
            list_price = int(min_value + (max_value - min_value) * 0.8)
            strategy = "optimistic"
            timeline = "3-6 months"
        else:
            # Balanced pricing
            list_price = int((min_value + max_value) / 2)
            strategy = "balanced"
            timeline = "1-3 months"

        # Adjust for market conditions
        if market_analysis.market_condition == MarketCondition.SELLERS_MARKET:
            list_price = int(list_price * 1.05)
            strategy += "_sellers_market"
        elif market_analysis.market_condition == MarketCondition.BUYERS_MARKET:
            list_price = int(list_price * 0.95)
            strategy += "_buyers_market"

        price_range = (int(list_price * 0.95), int(list_price * 1.05))

        reasoning = await self._generate_pricing_reasoning(
            list_price,
            market_analysis,
            home_condition,
            motivation_analysis
        )

        return PricingRecommendation(
            list_price=list_price,
            price_range=price_range,
            pricing_strategy=strategy,
            reasoning=reasoning,
            expected_timeline=timeline,
            confidence_level=market_analysis.pricing_confidence
        )

    async def _recommend_selling_pathway(
        self,
        market_analysis: MarketAnalysis,
        home_condition: HomeCondition,
        motivation_analysis: Dict[str, Any],
        pricing_recommendation: PricingRecommendation
    ) -> SellingPathway:
        """Recommend optimal selling pathway."""
        urgency = motivation_analysis["urgency_level"]
        condition = home_condition

        # High urgency or poor condition favors wholesale
        if urgency == "high" or condition == HomeCondition.POOR:
            return SellingPathway.WHOLESALE

        # Excellent condition with low urgency favors listing
        elif condition == HomeCondition.EXCELLENT and urgency == "low":
            return SellingPathway.LISTING

        # Market conditions influence decision
        elif market_analysis.market_condition == MarketCondition.SELLERS_MARKET:
            return SellingPathway.LISTING

        elif market_analysis.market_condition == MarketCondition.BUYERS_MARKET and urgency == "high":
            return SellingPathway.WHOLESALE

        else:
            # Hybrid approach for balanced situations
            return SellingPathway.HYBRID

    async def _generate_listing_optimization(
        self,
        extracted_preferences: Dict[str, Any],
        home_condition: HomeCondition,
        market_analysis: MarketAnalysis
    ) -> ListingOptimization:
        """Generate listing optimization recommendations."""
        improvements = []
        staging_suggestions = []
        photography_tips = []
        marketing_highlights = []

        # Condition-based improvements
        if home_condition == HomeCondition.FAIR:
            improvements.extend([
                {"improvement": "Fresh paint", "cost": 2000, "roi": 150, "priority": "high"},
                {"improvement": "Professional cleaning", "cost": 300, "roi": 120, "priority": "high"},
                {"improvement": "Landscaping touchups", "cost": 500, "roi": 130, "priority": "medium"}
            ])
        elif home_condition == HomeCondition.POOR:
            improvements.extend([
                {"improvement": "Major repairs", "cost": 15000, "roi": 110, "priority": "critical"},
                {"improvement": "HVAC service", "cost": 500, "roi": 120, "priority": "high"},
                {"improvement": "Flooring updates", "cost": 8000, "roi": 125, "priority": "high"}
            ])

        # Universal suggestions
        staging_suggestions.extend([
            "Declutter and depersonalize all spaces",
            "Maximize natural light by opening curtains/blinds",
            "Add fresh flowers or plants for warmth",
            "Ensure all light bulbs work and are bright",
            "Create inviting entry with clean welcome mat"
        ])

        photography_tips.extend([
            "Schedule during golden hour for best lighting",
            "Capture wide angles to show space",
            "Include outdoor spaces and neighborhood",
            "Highlight unique features and upgrades",
            "Consider drone shots for property overview"
        ])

        marketing_highlights.extend([
            "Emphasize location advantages",
            "Highlight recent improvements",
            "Showcase neighborhood amenities",
            "Include local school information",
            "Feature energy-efficient upgrades"
        ])

        potential_roi = {
            "total_investment": sum(imp["cost"] for imp in improvements),
            "expected_return": sum(imp["cost"] * (imp["roi"] / 100) for imp in improvements),
            "net_gain": sum(imp["cost"] * (imp["roi"] / 100) - imp["cost"] for imp in improvements)
        }

        return ListingOptimization(
            recommended_improvements=improvements,
            staging_suggestions=staging_suggestions,
            photography_tips=photography_tips,
            marketing_highlights=marketing_highlights,
            potential_roi=potential_roi
        )

    async def _generate_claude_summary(
        self,
        market_analysis: MarketAnalysis,
        pricing_recommendation: PricingRecommendation,
        pathway_recommendation: SellingPathway,
        motivation_analysis: Dict[str, Any],
        extracted_preferences: Dict[str, Any]
    ) -> str:
        """Generate Claude-powered summary of insights."""
        claude_prompt = f"""Generate a concise, personalized summary for a seller lead based on this analysis:

SELLER SITUATION:
- Location: {extracted_preferences.get('location', 'Not specified')}
- Motivation: {motivation_analysis['motivation_category']} ({motivation_analysis['urgency_level']} urgency)
- Timeline: {extracted_preferences.get('timeline', 'Not specified')}
- Home Condition: {market_analysis.estimated_value_range}

MARKET ANALYSIS:
- Estimated Value: ${market_analysis.estimated_value_range[0]:,} - ${market_analysis.estimated_value_range[1]:,}
- Market Condition: {market_analysis.market_condition.value}
- Expected Days on Market: {market_analysis.days_on_market_estimate}

RECOMMENDATIONS:
- Recommended Path: {pathway_recommendation.value}
- Suggested Price: ${pricing_recommendation.list_price:,}
- Expected Timeline: {pricing_recommendation.expected_timeline}

Create a 2-3 sentence summary that:
1. Acknowledges their situation and motivation
2. Provides the key market insight
3. Explains the recommended approach and why

Keep it under 200 characters for SMS compatibility. Be encouraging but realistic."""

        try:
            response = await self.llm_client.agenerate(
                prompt=claude_prompt,
                system_prompt="You are a trusted real estate advisor. Be encouraging, professional, and concise.",
                temperature=0.7,
                max_tokens=150
            )

            summary = response.content.strip()

            # Ensure SMS length limit
            if len(summary) > 200:
                summary = summary[:197] + "..."

            return summary

        except Exception as e:
            logger.error(f"Claude summary generation failed: {str(e)}")
            return self._generate_fallback_summary(pricing_recommendation, pathway_recommendation)

    def _generate_fallback_summary(
        self,
        pricing_recommendation: PricingRecommendation,
        pathway_recommendation: SellingPathway
    ) -> str:
        """Generate fallback summary when Claude fails."""
        if pathway_recommendation == SellingPathway.WHOLESALE:
            return f"For a quick sale, we can get you ${pricing_recommendation.list_price:,} with a cash offer in {pricing_recommendation.expected_timeline}."
        elif pathway_recommendation == SellingPathway.LISTING:
            return f"Your home could list for ${pricing_recommendation.list_price:,} and sell in {pricing_recommendation.expected_timeline} in this market."
        else:
            return f"We recommend listing at ${pricing_recommendation.list_price:,} with wholesale backup for maximum flexibility."

    # Helper methods for data fetching (would use real APIs in production)

    async def _fetch_comparable_sales(
        self,
        location: str,
        property_details: Dict[str, Any]
    ) -> List[ComparableSale]:
        """Fetch comparable sales data."""
        # Mock data - would fetch from MLS or real estate APIs
        return [
            ComparableSale(
                address="123 Similar St",
                sale_price=385000,
                sale_date=datetime.now() - timedelta(days=30),
                bedrooms=3,
                bathrooms=2,
                square_feet=1800,
                days_on_market=25,
                price_per_sqft=214,
                similarities=["Same neighborhood", "Similar size", "Recent sale"],
                adjustments={"condition": 5000, "upgrades": -3000}
            ),
            ComparableSale(
                address="456 Nearby Ave",
                sale_price=395000,
                sale_date=datetime.now() - timedelta(days=45),
                bedrooms=3,
                bathrooms=2,
                square_feet=1850,
                days_on_market=35,
                price_per_sqft=214,
                similarities=["Same school district", "Similar layout"],
                adjustments={"location": 8000, "age": -2000}
            ),
            ComparableSale(
                address="789 Close Blvd",
                sale_price=375000,
                sale_date=datetime.now() - timedelta(days=60),
                bedrooms=3,
                bathrooms=2,
                square_feet=1750,
                days_on_market=40,
                price_per_sqft=214,
                similarities=["Same builder", "Similar age"],
                adjustments={"size": -5000, "condition": 3000}
            )
        ]

    async def _assess_market_condition(self, location: str) -> MarketCondition:
        """Assess current market condition."""
        # Mock assessment - would use real market data
        return MarketCondition.BALANCED

    async def _analyze_market_trends(self, location: str) -> Dict[str, Any]:
        """Analyze market trends for location."""
        return {
            "price_trend": "increasing",
            "inventory_level": "balanced",
            "absorption_rate": "normal",
            "seasonal_factors": "spring_market_positive"
        }

    async def _analyze_neighborhood_insights(self, location: str) -> Dict[str, Any]:
        """Analyze neighborhood-specific insights."""
        return {
            "school_rating": "A",
            "walkability_score": 75,
            "crime_rate": "low",
            "appreciation_rate": "5.2%",
            "key_amenities": ["parks", "shopping", "restaurants"]
        }

    async def _analyze_timeline_expectations(
        self,
        pathway: SellingPathway,
        market_analysis: MarketAnalysis,
        motivation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze timeline expectations for different pathways."""
        base_timeline = {
            SellingPathway.WHOLESALE: {"min_days": 7, "max_days": 21, "typical_days": 14},
            SellingPathway.LISTING: {"min_days": 30, "max_days": 120, "typical_days": market_analysis.days_on_market_estimate},
            SellingPathway.HYBRID: {"min_days": 14, "max_days": 90, "typical_days": 45}
        }

        timeline = base_timeline[pathway].copy()

        # Adjust for market conditions
        if market_analysis.market_condition == MarketCondition.SELLERS_MARKET:
            timeline["typical_days"] = int(timeline["typical_days"] * 0.8)
        elif market_analysis.market_condition == MarketCondition.BUYERS_MARKET:
            timeline["typical_days"] = int(timeline["typical_days"] * 1.2)

        return {
            "pathway": pathway.value,
            "timeline_estimate": timeline,
            "factors_affecting_timeline": [
                "Market conditions",
                "Pricing strategy",
                "Home condition",
                "Seasonal factors"
            ],
            "urgency_alignment": motivation_analysis["urgency_level"]
        }

    async def _generate_pricing_reasoning(
        self,
        list_price: int,
        market_analysis: MarketAnalysis,
        home_condition: HomeCondition,
        motivation_analysis: Dict[str, Any]
    ) -> str:
        """Generate reasoning for pricing recommendation."""
        reasoning_parts = [
            f"Based on comparable sales ranging ${market_analysis.estimated_value_range[0]:,}-${market_analysis.estimated_value_range[1]:,}"
        ]

        if home_condition == HomeCondition.EXCELLENT:
            reasoning_parts.append("premium pricing justified by excellent condition")
        elif home_condition == HomeCondition.POOR:
            reasoning_parts.append("discounted for needed repairs")

        if motivation_analysis["urgency_level"] == "high":
            reasoning_parts.append("aggressive pricing for quick sale")
        elif motivation_analysis["urgency_level"] == "low":
            reasoning_parts.append("optimistic pricing to maximize value")

        return "; ".join(reasoning_parts)

    def _calculate_flexibility_score(self, urgency_level: str, motivation_category: str) -> float:
        """Calculate how flexible seller is on price/timeline."""
        base_scores = {
            "high": 0.8,    # High urgency = more flexible
            "medium": 0.5,  # Medium urgency = somewhat flexible
            "low": 0.2      # Low urgency = less flexible
        }

        flexibility = base_scores.get(urgency_level, 0.5)

        # Adjust based on motivation
        if motivation_category == "distress":
            flexibility += 0.2
        elif motivation_category == "lifestyle":
            flexibility -= 0.1

        return max(0.0, min(1.0, flexibility))

    def _calculate_confidence_score(
        self,
        market_analysis: MarketAnalysis,
        pricing_recommendation: PricingRecommendation,
        extracted_preferences: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence in recommendations."""
        confidence_factors = [
            market_analysis.pricing_confidence,
            pricing_recommendation.confidence_level,
            0.8 if extracted_preferences.get("location") else 0.4,  # Location specified
            0.9 if extracted_preferences.get("home_condition") else 0.5,  # Condition known
            0.7 if len(market_analysis.comparable_sales) >= 3 else 0.4  # Sufficient comps
        ]

        return sum(confidence_factors) / len(confidence_factors)

    def _generate_next_steps(
        self,
        pathway: SellingPathway,
        market_analysis: MarketAnalysis,
        motivation_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable next steps."""
        steps = []

        if pathway == SellingPathway.WHOLESALE:
            steps.extend([
                "Schedule property evaluation for cash offer",
                "Gather property documents (deed, tax records)",
                "Consider quick repairs that add value"
            ])
        elif pathway == SellingPathway.LISTING:
            steps.extend([
                "Complete pre-listing home preparation",
                "Schedule professional photography",
                "Review and sign listing agreement",
                "Prepare for showings and open houses"
            ])
        else:  # HYBRID
            steps.extend([
                "Prepare property for MLS listing",
                "Get cash offer as backup option",
                "Set up dual-track timeline",
                "Review both pathway agreements"
            ])

        # Add universal steps
        if motivation_analysis["urgency_level"] == "high":
            steps.insert(0, "Priority: Fast-track all preparation steps")

        return steps

    async def _fallback_seller_insights(
        self,
        extracted_preferences: Dict[str, Any]
    ) -> SellerInsights:
        """Generate fallback insights when main process fails."""
        # Simple fallback with basic estimates
        estimated_value = 400000  # Default estimate
        location = extracted_preferences.get("location", "your area")

        fallback_market_analysis = MarketAnalysis(
            estimated_value_range=(int(estimated_value * 0.9), int(estimated_value * 1.1)),
            comparable_sales=[],
            market_condition=MarketCondition.BALANCED,
            days_on_market_estimate=45,
            pricing_confidence=0.3,
            market_trends={"status": "analysis_unavailable"},
            neighborhood_insights={"status": "data_unavailable"}
        )

        fallback_pricing = PricingRecommendation(
            list_price=estimated_value,
            price_range=(int(estimated_value * 0.95), int(estimated_value * 1.05)),
            pricing_strategy="conservative",
            reasoning="Estimated based on regional averages",
            expected_timeline="6-12 weeks",
            confidence_level=0.3
        )

        return SellerInsights(
            market_analysis=fallback_market_analysis,
            pricing_recommendation=fallback_pricing,
            pathway_recommendation=SellingPathway.LISTING,
            listing_optimization=None,
            timeline_analysis={"status": "basic_estimates"},
            claude_summary=f"We can help you sell your {location} property. Let's discuss your goals and timeline to provide better recommendations.",
            confidence_score=0.3,
            next_steps=[
                "Schedule property consultation",
                "Gather more property details",
                "Discuss your timeline and goals"
            ]
        )