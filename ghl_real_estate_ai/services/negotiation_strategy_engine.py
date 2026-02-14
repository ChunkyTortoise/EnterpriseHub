"""
Negotiation Strategy Engine

Synthesizes seller psychology and market leverage analysis into actionable
negotiation strategies with specific tactics and talking points.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List

from ghl_real_estate_ai.api.schemas.negotiation import (
    MarketCondition,
    MarketLeverage,
    NegotiationStrategy,
    NegotiationTactic,
    SellerMotivationType,
    SellerPsychologyProfile,
    UrgencyLevel,
)
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.negotiation.mia_rvelous import get_mia_optimizer

logger = logging.getLogger(__name__)


class NegotiationStrategyEngine:
    """
    Generates comprehensive negotiation strategies by combining seller psychology
    insights with market leverage analysis and AI-generated tactical guidance.
    """

    def __init__(self):
        self.cache_service = get_cache_service()
        self.claude_assistant = ClaudeAssistant()

    async def generate_negotiation_strategy(
        self,
        property_id: str,
        seller_psychology: SellerPsychologyProfile,
        market_leverage: MarketLeverage,
        property_data: Dict[str, Any],
        buyer_profile: Dict[str, Any],
    ) -> NegotiationStrategy:
        """
        Generate comprehensive negotiation strategy based on psychology and market analysis.
        """
        cache_key = f"negotiation_strategy:{property_id}:v2"
        cached_result = await self.cache_service.get(cache_key)

        if cached_result:
            logger.info(f"Returning cached negotiation strategy for {property_id}")
            return NegotiationStrategy.model_validate(cached_result)

        logger.info(f"Generating negotiation strategy for property {property_id}")

        # Calculate optimal offer pricing
        offer_analysis = await self._calculate_optimal_offer(property_data, seller_psychology, market_leverage)

        # Determine primary negotiation tactic
        primary_tactic = self._determine_primary_tactic(seller_psychology, market_leverage, buyer_profile)

        # Generate strategic elements
        strategic_elements = await self._generate_strategic_elements(seller_psychology, market_leverage, primary_tactic)

        # Create tactical guidance
        tactical_guidance = await self._generate_tactical_guidance(
            seller_psychology, market_leverage, primary_tactic, offer_analysis
        )

        # AI-enhanced strategy refinement
        ai_strategy_insights = await self._get_ai_strategy_insights(
            seller_psychology, market_leverage, offer_analysis, primary_tactic
        )

        # Calculate strategy confidence
        confidence_score = self._calculate_strategy_confidence(seller_psychology, market_leverage, offer_analysis)

        # VANGUARD 3: MIA-RVelous Optimization
        optimizer = get_mia_optimizer()
        bid_sequence = optimizer.calculate_optimal_sequence(
            agent_walkaway=float(offer_analysis["offer_range"]["min"]),
            buyer_range_estimate=(
                float(offer_analysis["offer_range"]["min"]),
                float(offer_analysis["offer_range"]["max"]),
            ),
            max_rounds=5,
            time_pressure_factor=seller_psychology.urgency_score / 100.0,
        )
        strategy_blend = optimizer.get_strategy_blend(
            warmth=seller_psychology.flexibility_score / 100.0, dominance=market_leverage.overall_leverage_score / 100.0
        )

        # Synthesize complete strategy
        strategy = NegotiationStrategy(
            primary_tactic=primary_tactic,
            confidence_score=confidence_score,
            recommended_offer_price=offer_analysis["recommended_price"],
            offer_range=offer_analysis["offer_range"],
            key_terms_to_emphasize=strategic_elements["key_terms"],
            concessions_to_request=strategic_elements["concessions"],
            relationship_building_approach=strategic_elements["relationship_approach"],
            opening_strategy=tactical_guidance["opening_strategy"],
            response_to_counter=tactical_guidance["counter_response"],
            negotiation_timeline=tactical_guidance["timeline"],
            primary_talking_points=ai_strategy_insights.get("talking_points", []),
            objection_responses=ai_strategy_insights.get("objection_responses", {}),
            optimal_bid_sequence=bid_sequence,
            strategy_blend=strategy_blend,
        )

        # Cache strategy for 2 hours
        await self.cache_service.set(cache_key, strategy.model_dump(), ttl=7200)

        logger.info(f"Negotiation strategy generated: {primary_tactic} approach with {confidence_score}% confidence")
        return strategy

    async def _calculate_optimal_offer(
        self, property_data: Dict[str, Any], seller_psychology: SellerPsychologyProfile, market_leverage: MarketLeverage
    ) -> Dict[str, Any]:
        """Calculate optimal offer pricing based on psychology and market factors"""

        list_price = Decimal(str(property_data.get("list_price", 500000)))

        # Base offer calculation (start conservative)
        base_offer_pct = 0.95  # Start at 95% of list price

        # Psychology-based adjustments
        psychology_adjustment = self._calculate_psychology_pricing_adjustment(seller_psychology)

        # Market leverage adjustments
        market_adjustment = self._calculate_market_pricing_adjustment(market_leverage)

        # Combine adjustments
        total_adjustment = psychology_adjustment + market_adjustment
        final_offer_pct = base_offer_pct + total_adjustment

        # Ensure reasonable bounds
        final_offer_pct = max(0.80, min(1.05, final_offer_pct))

        recommended_price = list_price * Decimal(str(final_offer_pct))

        # Calculate offer range
        min_offer = recommended_price * Decimal("0.97")
        max_offer = recommended_price * Decimal("1.03")

        # Adjust range based on market conditions
        if market_leverage.market_condition == MarketCondition.BUYERS_MARKET:
            min_offer *= Decimal("0.95")  # More aggressive low end
        elif market_leverage.market_condition == MarketCondition.SELLERS_MARKET:
            max_offer *= Decimal("1.02")  # Less aggressive high end

        return {
            "recommended_price": recommended_price,
            "offer_range": {"min": min_offer, "target": recommended_price, "max": max_offer},
            "list_price_percentage": float(final_offer_pct),
            "psychology_adjustment": psychology_adjustment,
            "market_adjustment": market_adjustment,
            "pricing_rationale": self._generate_pricing_rationale(
                psychology_adjustment, market_adjustment, seller_psychology, market_leverage
            ),
        }

    def _calculate_psychology_pricing_adjustment(self, psychology: SellerPsychologyProfile) -> float:
        """Calculate pricing adjustment based on seller psychology"""

        adjustment = 0.0

        # Urgency-based adjustments
        if psychology.urgency_level == UrgencyLevel.CRITICAL:
            adjustment -= 0.08  # 8% more aggressive
        elif psychology.urgency_level == UrgencyLevel.HIGH:
            adjustment -= 0.05  # 5% more aggressive
        elif psychology.urgency_level == UrgencyLevel.LOW:
            adjustment += 0.02  # 2% less aggressive

        # Motivation-based adjustments
        if psychology.motivation_type == SellerMotivationType.DISTRESSED:
            adjustment -= 0.06  # 6% more aggressive
        elif psychology.motivation_type == SellerMotivationType.FINANCIAL:
            adjustment -= 0.03  # 3% more aggressive
        elif psychology.motivation_type == SellerMotivationType.EMOTIONAL:
            adjustment += 0.03  # 3% less aggressive (relationship matters)

        # Flexibility adjustments
        if psychology.flexibility_score > 80:
            adjustment -= 0.04  # Very flexible seller
        elif psychology.flexibility_score < 30:
            adjustment += 0.04  # Inflexible seller

        # Financial pressure adjustments
        if psychology.financial_pressure_score > 80:
            adjustment -= 0.05  # High financial pressure

        return max(-0.15, min(0.05, adjustment))  # Cap at -15% to +5%

    def _calculate_market_pricing_adjustment(self, leverage: MarketLeverage) -> float:
        """Calculate pricing adjustment based on market leverage"""

        adjustment = 0.0

        # Overall leverage adjustment
        leverage_adjustment = (leverage.overall_leverage_score - 50) / 1000  # Scale to percentage
        adjustment += leverage_adjustment

        # Market condition adjustments
        if leverage.market_condition == MarketCondition.BUYERS_MARKET:
            adjustment -= 0.03  # 3% more aggressive
        elif leverage.market_condition == MarketCondition.SELLERS_MARKET:
            adjustment += 0.03  # 3% less aggressive

        # Price positioning adjustments
        if leverage.price_positioning == "overpriced":
            adjustment -= 0.06  # 6% more aggressive
        elif leverage.price_positioning == "underpriced":
            adjustment += 0.02  # 2% less aggressive

        # Competitive pressure adjustments
        if leverage.competitive_pressure > 80:
            adjustment -= 0.02  # High competition = more aggressive
        elif leverage.competitive_pressure < 30:
            adjustment += 0.02  # Low competition = less aggressive

        # Cash offer and quick close bonuses
        adjustment -= leverage.cash_offer_boost / 100  # Convert to decimal
        adjustment -= leverage.quick_close_advantage / 100

        return max(-0.12, min(0.08, adjustment))  # Cap at -12% to +8%

    def _determine_primary_tactic(
        self, psychology: SellerPsychologyProfile, leverage: MarketLeverage, buyer_profile: Dict[str, Any]
    ) -> NegotiationTactic:
        """Determine the primary negotiation tactic to employ"""

        tactic_scores = {
            NegotiationTactic.PRICE_FOCUSED: 0,
            NegotiationTactic.TIMELINE_FOCUSED: 0,
            NegotiationTactic.TERMS_FOCUSED: 0,
            NegotiationTactic.RELATIONSHIP_BUILDING: 0,
            NegotiationTactic.COMPETITIVE_PRESSURE: 0,
        }

        # Psychology-based tactic scoring
        if psychology.motivation_type == SellerMotivationType.FINANCIAL:
            tactic_scores[NegotiationTactic.PRICE_FOCUSED] += 40
        elif psychology.motivation_type == SellerMotivationType.EMOTIONAL:
            tactic_scores[NegotiationTactic.RELATIONSHIP_BUILDING] += 40
        elif psychology.motivation_type == SellerMotivationType.DISTRESSED:
            tactic_scores[NegotiationTactic.TIMELINE_FOCUSED] += 30
            tactic_scores[NegotiationTactic.PRICE_FOCUSED] += 20

        # Urgency influences tactics
        if psychology.urgency_level in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]:
            tactic_scores[NegotiationTactic.TIMELINE_FOCUSED] += 30

        # Relationship importance
        if psychology.relationship_importance > 70:
            tactic_scores[NegotiationTactic.RELATIONSHIP_BUILDING] += 25

        # Market leverage influences
        if leverage.overall_leverage_score > 70:
            tactic_scores[NegotiationTactic.PRICE_FOCUSED] += 25
            tactic_scores[NegotiationTactic.COMPETITIVE_PRESSURE] += 20
        elif leverage.overall_leverage_score < 30:
            tactic_scores[NegotiationTactic.RELATIONSHIP_BUILDING] += 30
            tactic_scores[NegotiationTactic.TERMS_FOCUSED] += 20

        # Competitive pressure
        if leverage.competitive_pressure > 70:
            tactic_scores[NegotiationTactic.COMPETITIVE_PRESSURE] += 30

        # Buyer profile influences
        if buyer_profile.get("cash_offer", False):
            tactic_scores[NegotiationTactic.TIMELINE_FOCUSED] += 25
            tactic_scores[NegotiationTactic.TERMS_FOCUSED] += 20

        if buyer_profile.get("flexible_timeline", False):
            tactic_scores[NegotiationTactic.TERMS_FOCUSED] += 15

        # Return highest scoring tactic
        return max(tactic_scores.keys(), key=lambda k: tactic_scores[k])

    async def _generate_strategic_elements(
        self, psychology: SellerPsychologyProfile, leverage: MarketLeverage, primary_tactic: NegotiationTactic
    ) -> Dict[str, Any]:
        """Generate key strategic elements for negotiation"""

        key_terms = []
        concessions = []
        relationship_approach = ""

        # Tactic-specific strategic elements
        if primary_tactic == NegotiationTactic.PRICE_FOCUSED:
            key_terms.extend(["competitive_price", "market_value_analysis", "comparable_sales"])
            concessions.extend(["quick_close", "flexible_inspection", "as_is_acceptance"])
            relationship_approach = "professional_analytical"

        elif primary_tactic == NegotiationTactic.TIMELINE_FOCUSED:
            key_terms.extend(["flexible_closing_date", "quick_close", "seller_timeline"])
            concessions.extend(["price_premium", "inspection_waiver", "appraisal_gap_coverage"])
            relationship_approach = "accommodating_flexible"

        elif primary_tactic == NegotiationTactic.TERMS_FOCUSED:
            key_terms.extend(["favorable_contingencies", "inspection_terms", "financing_terms"])
            concessions.extend(["closing_cost_assistance", "home_warranty", "appliances_included"])
            relationship_approach = "collaborative_creative"

        elif primary_tactic == NegotiationTactic.RELATIONSHIP_BUILDING:
            key_terms.extend(["personal_connection", "home_appreciation", "care_commitment"])
            concessions.extend(["personal_letter", "seller_needs_accommodation", "emotional_value"])
            relationship_approach = "personal_empathetic"

        elif primary_tactic == NegotiationTactic.COMPETITIVE_PRESSURE:
            key_terms.extend(["market_competition", "alternative_properties", "timing_pressure"])
            concessions.extend(["escalation_clause", "backup_offer_position", "decision_deadline"])
            relationship_approach = "confident_assertive"

        # Psychology-specific adjustments
        if psychology.motivation_type == SellerMotivationType.EMOTIONAL:
            key_terms.append("emotional_connection")
            concessions.append("personal_touch")

        if psychology.urgency_level in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]:
            key_terms.append("timeline_accommodation")
            concessions.append("quick_decision")

        # Leverage-specific adjustments
        if leverage.overall_leverage_score > 70:
            key_terms.append("buyer_strength")
            concessions.append("market_positioning")

        return {
            "key_terms": key_terms[:6],  # Top 6 terms
            "concessions": concessions[:6],  # Top 6 concessions
            "relationship_approach": relationship_approach,
        }

    async def _generate_tactical_guidance(
        self,
        psychology: SellerPsychologyProfile,
        leverage: MarketLeverage,
        primary_tactic: NegotiationTactic,
        offer_analysis: Dict[str, Any],
    ) -> Dict[str, str]:
        """Generate specific tactical guidance for negotiation execution"""

        # Opening strategy based on tactic and psychology
        opening_strategies = {
            NegotiationTactic.PRICE_FOCUSED: self._generate_price_focused_opening(psychology, offer_analysis),
            NegotiationTactic.TIMELINE_FOCUSED: self._generate_timeline_focused_opening(psychology),
            NegotiationTactic.TERMS_FOCUSED: self._generate_terms_focused_opening(psychology),
            NegotiationTactic.RELATIONSHIP_BUILDING: self._generate_relationship_opening(psychology),
            NegotiationTactic.COMPETITIVE_PRESSURE: self._generate_competitive_opening(leverage),
        }

        # Counter-response strategy
        counter_responses = {
            NegotiationTactic.PRICE_FOCUSED: "Focus on market data and comparable sales. Use factual analysis to justify position.",
            NegotiationTactic.TIMELINE_FOCUSED: "Emphasize timeline flexibility and accommodation. Offer scheduling advantages.",
            NegotiationTactic.TERMS_FOCUSED: "Present creative alternatives. Show win-win term modifications.",
            NegotiationTactic.RELATIONSHIP_BUILDING: "Acknowledge seller concerns. Build personal connection and trust.",
            NegotiationTactic.COMPETITIVE_PRESSURE: "Reference market alternatives. Maintain confident but respectful position.",
        }

        # Timeline strategy
        timeline_strategies = {
            UrgencyLevel.CRITICAL: "accelerated_timeline",
            UrgencyLevel.HIGH: "standard_timeline",
            UrgencyLevel.MODERATE: "flexible_timeline",
            UrgencyLevel.LOW: "patient_timeline",
        }

        return {
            "opening_strategy": opening_strategies[primary_tactic],
            "counter_response": counter_responses[primary_tactic],
            "timeline": timeline_strategies[psychology.urgency_level],
        }

    def _generate_price_focused_opening(self, psychology: SellerPsychologyProfile, offer_analysis: Dict) -> str:
        """Generate price-focused opening strategy"""
        percentage = offer_analysis["list_price_percentage"] * 100

        if psychology.flexibility_score > 70:
            return f"Present {percentage:.1f}% offer with strong market analysis supporting valuation. Emphasize comparable sales data."
        else:
            return (
                f"Present {percentage:.1f}% offer as market-driven, not negotiation tactic. Use third-party validation."
            )

    def _generate_timeline_focused_opening(self, psychology: SellerPsychologyProfile) -> str:
        """Generate timeline-focused opening strategy"""
        if psychology.urgency_level == UrgencyLevel.CRITICAL:
            return (
                "Lead with ability to close quickly and accommodate seller timeline. Price as secondary consideration."
            )
        else:
            return "Present timeline flexibility as key value proposition. Show accommodation for seller needs."

    def _generate_terms_focused_opening(self, psychology: SellerPsychologyProfile) -> str:
        """Generate terms-focused opening strategy"""
        return "Present creative terms package addressing seller concerns. Frame as comprehensive solution."

    def _generate_relationship_opening(self, psychology: SellerPsychologyProfile) -> str:
        """Generate relationship-building opening strategy"""
        if psychology.motivation_type == SellerMotivationType.EMOTIONAL:
            return "Share personal connection to home. Demonstrate appreciation for property and seller investment."
        else:
            return "Build professional rapport. Show respect for seller position and timeline."

    def _generate_competitive_opening(self, leverage: MarketLeverage) -> str:
        """Generate competitive pressure opening strategy"""
        return f"Present strong offer with confidence. Reference market position and buyer qualifications as competitive advantages."

    async def _get_ai_strategy_insights(
        self,
        psychology: SellerPsychologyProfile,
        leverage: MarketLeverage,
        offer_analysis: Dict[str, Any],
        primary_tactic: NegotiationTactic,
    ) -> Dict[str, Any]:
        """Get AI-enhanced strategic insights and talking points"""

        context = f"""
        Generate strategic negotiation guidance for this situation:
        
        Seller Psychology:
        - Motivation: {psychology.motivation_type}
        - Urgency: {psychology.urgency_level} ({psychology.urgency_score}/100)
        - Flexibility: {psychology.flexibility_score}/100
        - Primary Concerns: {psychology.primary_concerns}
        - Hot Buttons: {psychology.negotiation_hot_buttons}
        
        Market Leverage:
        - Overall Leverage: {leverage.overall_leverage_score}/100
        - Market Condition: {leverage.market_condition}
        - Price Positioning: {leverage.price_positioning}
        - Competitive Pressure: {leverage.competitive_pressure}/100
        
        Recommended Offer: {offer_analysis["list_price_percentage"] * 100:.1f}% of list price
        Primary Tactic: {primary_tactic}
        
        Provide:
        1. 5 key talking points for this strategy
        2. Responses to likely objections
        3. Tactical refinements
        """

        try:
            ai_response = await self.claude_assistant.analyze_with_context(context)

            return {
                "talking_points": ai_response.get("talking_points", []),
                "objection_responses": ai_response.get("objection_responses", {}),
                "tactical_refinements": ai_response.get("refinements", []),
                "ai_confidence": ai_response.get("confidence", 75),
            }
        except Exception as e:
            logger.error(f"AI strategy insights generation failed: {e}")
            return {
                "talking_points": self._generate_fallback_talking_points(primary_tactic),
                "objection_responses": self._generate_fallback_objections(primary_tactic),
                "tactical_refinements": [],
                "ai_confidence": 0,
            }

    def _generate_fallback_talking_points(self, tactic: NegotiationTactic) -> List[str]:
        """Generate fallback talking points if AI fails"""

        fallback_points = {
            NegotiationTactic.PRICE_FOCUSED: [
                "Market analysis supports our valuation approach",
                "Comparable sales data indicates fair market value",
                "Recent market trends favor this pricing position",
            ],
            NegotiationTactic.TIMELINE_FOCUSED: [
                "Flexible timeline accommodates your specific needs",
                "Quick closing capability provides certainty",
                "Scheduling flexibility reduces transaction stress",
            ],
            NegotiationTactic.TERMS_FOCUSED: [
                "Creative terms create win-win outcome",
                "Favorable contingencies protect both parties",
                "Comprehensive package addresses key concerns",
            ],
            NegotiationTactic.RELATIONSHIP_BUILDING: [
                "Personal connection to your property",
                "Appreciation for your investment in the home",
                "Commitment to smooth transaction process",
            ],
            NegotiationTactic.COMPETITIVE_PRESSURE: [
                "Strong buyer qualifications ensure reliable closing",
                "Market positioning provides negotiation confidence",
                "Alternative opportunities available if needed",
            ],
        }

        return fallback_points.get(tactic, [])

    def _generate_fallback_objections(self, tactic: NegotiationTactic) -> Dict[str, str]:
        """Generate fallback objection responses if AI fails"""

        return {
            "price_too_low": "Market data supports this valuation approach",
            "timing_issues": "We can accommodate your preferred timeline",
            "terms_concerns": "Let's discuss creative solutions that work for both parties",
        }

    def _calculate_strategy_confidence(
        self, psychology: SellerPsychologyProfile, leverage: MarketLeverage, offer_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the negotiation strategy"""

        confidence = 50.0  # Base confidence

        # Psychology certainty boosts confidence
        if psychology.urgency_score > 80:
            confidence += 15  # High certainty in urgency
        if psychology.flexibility_score > 80 or psychology.flexibility_score < 20:
            confidence += 10  # Clear flexibility position

        # Market leverage clarity
        if leverage.overall_leverage_score > 80 or leverage.overall_leverage_score < 20:
            confidence += 15  # Clear leverage position

        # Price positioning confidence
        if leverage.price_positioning in ["overpriced", "underpriced"]:
            confidence += 10  # Clear pricing position

        # Market condition clarity
        if leverage.market_condition != MarketCondition.BALANCED:
            confidence += 10  # Clear market direction

        # Data quality adjustments
        if leverage.comparable_sales_strength > 80:
            confidence += 10  # Strong comps data
        elif leverage.comparable_sales_strength < 40:
            confidence -= 10  # Weak comps data

        return max(0, min(100, confidence))

    def _generate_pricing_rationale(
        self, psychology_adj: float, market_adj: float, psychology: SellerPsychologyProfile, leverage: MarketLeverage
    ) -> str:
        """Generate rationale for pricing strategy"""

        rationale_parts = []

        if psychology_adj < -0.03:
            rationale_parts.append(f"Seller {psychology.motivation_type} motivation suggests pricing flexibility")
        if market_adj < -0.03:
            rationale_parts.append(
                f"Market leverage ({leverage.overall_leverage_score}%) supports aggressive positioning"
            )
        if leverage.price_positioning == "overpriced":
            rationale_parts.append("Property appears overpriced relative to market comparables")

        return "; ".join(rationale_parts) if rationale_parts else "Balanced approach based on market analysis"


# Singleton instance
_negotiation_strategy_engine = None


def get_negotiation_strategy_engine() -> NegotiationStrategyEngine:
    """Get singleton instance of NegotiationStrategyEngine"""
    global _negotiation_strategy_engine
    if _negotiation_strategy_engine is None:
        _negotiation_strategy_engine = NegotiationStrategyEngine()
    return _negotiation_strategy_engine
