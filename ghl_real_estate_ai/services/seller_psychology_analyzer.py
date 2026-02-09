"""
Seller Psychology Analyzer

Analyzes seller behavior, motivation patterns, and psychological indicators
to understand negotiation positioning and emotional state.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.api.schemas.negotiation import (
    ListingBehaviorPattern,
    ListingHistory,
    SellerMotivationType,
    SellerPsychologyProfile,
    UrgencyLevel,
)
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant

logger = logging.getLogger(__name__)


class SellerPsychologyAnalyzer:
    """
    Analyzes seller psychology through listing behavior, communication patterns,
    and market responses to determine negotiation approach.
    """

    def __init__(self):
        self.cache_service = get_cache_service()
        self.claude_assistant = ClaudeAssistant()

    async def analyze_seller_psychology(
        self,
        property_id: str,
        listing_history: ListingHistory,
        communication_data: Optional[Dict[str, Any]] = None,
        market_context: Optional[Dict[str, Any]] = None,
    ) -> SellerPsychologyProfile:
        """
        Comprehensive seller psychology analysis combining behavioral patterns,
        communication analysis, and market response indicators.
        """
        cache_key = f"seller_psychology:{property_id}:v2"
        cached_result = await self.cache_service.get(cache_key)

        if cached_result:
            logger.info(f"Returning cached seller psychology analysis for {property_id}")
            return SellerPsychologyProfile.model_validate(cached_result)

        logger.info(f"Analyzing seller psychology for property {property_id}")

        # Parallel analysis of different psychological indicators
        behavioral_analysis = await self._analyze_listing_behavior(listing_history)
        urgency_analysis = await self._analyze_urgency_indicators(listing_history, communication_data)
        motivation_analysis = await self._analyze_seller_motivation(listing_history, communication_data)
        flexibility_analysis = await self._analyze_negotiation_flexibility(listing_history, market_context)

        # AI-enhanced insights
        ai_insights = await self._get_ai_psychological_insights(
            listing_history, behavioral_analysis, communication_data
        )

        # Synthesize comprehensive profile
        psychology_profile = self._synthesize_psychology_profile(
            behavioral_analysis=behavioral_analysis,
            urgency_analysis=urgency_analysis,
            motivation_analysis=motivation_analysis,
            flexibility_analysis=flexibility_analysis,
            ai_insights=ai_insights,
            communication_data=communication_data,
        )

        # Cache result for 4 hours (seller psychology changes slowly)
        await self.cache_service.set(cache_key, psychology_profile.model_dump(), ttl=14400)

        logger.info(
            f"Seller psychology analysis complete: {psychology_profile.motivation_type}, urgency: {psychology_profile.urgency_level}"
        )
        return psychology_profile

    async def _analyze_listing_behavior(self, listing_history: ListingHistory) -> Dict[str, Any]:
        """Analyze behavioral patterns from listing history"""

        price_drop_analysis = self._analyze_price_drops(listing_history.price_drops)
        market_response_analysis = self._analyze_market_response(listing_history)

        # Determine behavioral pattern
        behavioral_pattern = self._classify_behavioral_pattern(listing_history, price_drop_analysis)

        return {
            "behavioral_pattern": behavioral_pattern,
            "price_drop_analysis": price_drop_analysis,
            "market_response": market_response_analysis,
            "listing_persistence": self._calculate_listing_persistence(listing_history),
        }

    def _analyze_price_drops(self, price_drops: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze price reduction patterns for psychological insights"""

        if not price_drops:
            return {
                "pattern": "no_drops",
                "psychological_indicator": "stubborn_or_realistic",
                "flexibility_signal": 0.2,
            }

        total_reduction = sum(drop.get("percentage", 0) for drop in price_drops)
        avg_drop_size = total_reduction / len(price_drops) if price_drops else 0
        drop_frequency = len(price_drops)

        # Analyze drop timing patterns
        rapid_drops = sum(1 for drop in price_drops if drop.get("percentage", 0) > 5)
        small_drops = sum(1 for drop in price_drops if drop.get("percentage", 0) <= 2)

        # Psychological pattern classification
        if total_reduction > 15:
            pattern = "aggressive_reducer"
            psychological_indicator = "highly_motivated"
        elif avg_drop_size < 2 and drop_frequency > 3:
            pattern = "incremental_reducer"
            psychological_indicator = "testing_market"
        elif rapid_drops > 0:
            pattern = "panic_reducer"
            psychological_indicator = "distressed_seller"
        else:
            pattern = "strategic_reducer"
            psychological_indicator = "calculated_seller"

        return {
            "pattern": pattern,
            "psychological_indicator": psychological_indicator,
            "total_reduction_pct": total_reduction,
            "avg_drop_size": avg_drop_size,
            "drop_frequency": drop_frequency,
            "flexibility_signal": min(total_reduction / 10, 1.0),  # 0-1 scale
        }

    def _analyze_market_response(self, listing_history: ListingHistory) -> Dict[str, Any]:
        """Analyze seller's response to market feedback"""

        days_on_market = listing_history.days_on_market
        views = listing_history.listing_views or 0
        showings = listing_history.showing_requests or 0
        offers = listing_history.offers_received or 0

        # Calculate response ratios
        view_to_showing_ratio = showings / max(views, 1)
        showing_to_offer_ratio = offers / max(showings, 1)

        # Market feedback quality
        if days_on_market > 60 and offers == 0:
            market_feedback = "poor"
            seller_awareness = "low" if not listing_history.price_drops else "learning"
        elif offers > 0 and days_on_market > 30:
            market_feedback = "mixed"
            seller_awareness = "moderate"
        else:
            market_feedback = "positive"
            seller_awareness = "high"

        return {
            "market_feedback": market_feedback,
            "seller_awareness": seller_awareness,
            "view_to_showing_ratio": view_to_showing_ratio,
            "showing_to_offer_ratio": showing_to_offer_ratio,
            "engagement_quality": self._assess_engagement_quality(view_to_showing_ratio, showing_to_offer_ratio),
        }

    def _classify_behavioral_pattern(
        self, listing_history: ListingHistory, price_analysis: Dict[str, Any]
    ) -> ListingBehaviorPattern:
        """Classify overall behavioral pattern"""

        days_on_market = listing_history.days_on_market
        price_pattern = price_analysis["pattern"]

        # Pattern classification logic
        if days_on_market > 90 and not listing_history.price_drops:
            return ListingBehaviorPattern.OVERPRICED_STUBBORN
        elif price_pattern in ["aggressive_reducer", "panic_reducer"]:
            return ListingBehaviorPattern.PRICE_DROPPER
        elif days_on_market < 30 or price_pattern == "strategic_reducer":
            return ListingBehaviorPattern.REALISTIC_PRICING
        elif listing_history.offers_received and listing_history.offers_received > 0:
            return ListingBehaviorPattern.MOTIVATED_SELLER
        else:
            return ListingBehaviorPattern.TESTING_MARKET

    async def _analyze_urgency_indicators(
        self, listing_history: ListingHistory, communication_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze indicators of seller urgency"""

        urgency_signals = []
        urgency_score = 0.0

        # Time-based urgency
        days_on_market = listing_history.days_on_market
        if days_on_market > 120:
            urgency_signals.append("extended_market_time")
            urgency_score += 30
        elif days_on_market > 60:
            urgency_score += 15

        # Price reduction urgency
        if listing_history.price_drops:
            recent_drops = [
                d
                for d in listing_history.price_drops
                if (datetime.now() - datetime.fromisoformat(d.get("date", "2024-01-01"))).days < 30
            ]
            if recent_drops:
                urgency_signals.append("recent_price_reduction")
                urgency_score += 25

        # Communication urgency indicators
        if communication_data:
            response_time = communication_data.get("avg_response_time_hours", 24)
            if response_time < 2:
                urgency_signals.append("quick_response_times")
                urgency_score += 20

            if "urgent" in communication_data.get("communication_tone", "").lower():
                urgency_signals.append("urgent_language")
                urgency_score += 15

        # Multiple listing attempts
        if listing_history.previous_listing_attempts and listing_history.previous_listing_attempts > 1:
            urgency_signals.append("multiple_listing_attempts")
            urgency_score += 35

        # Determine urgency level
        if urgency_score >= 70:
            urgency_level = UrgencyLevel.CRITICAL
        elif urgency_score >= 45:
            urgency_level = UrgencyLevel.HIGH
        elif urgency_score >= 20:
            urgency_level = UrgencyLevel.MODERATE
        else:
            urgency_level = UrgencyLevel.LOW

        return {
            "urgency_level": urgency_level,
            "urgency_score": min(urgency_score, 100),
            "urgency_signals": urgency_signals,
            "time_pressure_factor": days_on_market / 365,  # Normalized time pressure
        }

    async def _analyze_seller_motivation(
        self, listing_history: ListingHistory, communication_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Determine primary seller motivation type"""

        motivation_scores = {
            SellerMotivationType.EMOTIONAL: 0,
            SellerMotivationType.FINANCIAL: 0,
            SellerMotivationType.STRATEGIC: 0,
            SellerMotivationType.DISTRESSED: 0,
        }

        # Financial motivation indicators
        if listing_history.price_drops:
            total_reduction = sum(drop.get("percentage", 0) for drop in listing_history.price_drops)
            if total_reduction > 10:
                motivation_scores[SellerMotivationType.FINANCIAL] += 30

        # Distressed seller indicators
        if listing_history.days_on_market > 120:
            motivation_scores[SellerMotivationType.DISTRESSED] += 40

        if listing_history.previous_listing_attempts and listing_history.previous_listing_attempts > 1:
            motivation_scores[SellerMotivationType.DISTRESSED] += 30

        # Strategic motivation (good market timing)
        if listing_history.days_on_market < 30 and not listing_history.price_drops:
            motivation_scores[SellerMotivationType.STRATEGIC] += 40

        # Communication-based motivation analysis
        if communication_data:
            tone = communication_data.get("communication_tone", "").lower()
            if any(word in tone for word in ["family", "memories", "home"]):
                motivation_scores[SellerMotivationType.EMOTIONAL] += 25
            if any(word in tone for word in ["investment", "profit", "financial"]):
                motivation_scores[SellerMotivationType.FINANCIAL] += 25

        # Determine primary motivation
        primary_motivation = max(motivation_scores.keys(), key=lambda k: motivation_scores[k])

        return {
            "primary_motivation": primary_motivation,
            "motivation_scores": motivation_scores,
            "motivation_confidence": motivation_scores[primary_motivation] / 100,
        }

    async def _analyze_negotiation_flexibility(
        self, listing_history: ListingHistory, market_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze seller's flexibility in negotiations"""

        flexibility_score = 50.0  # Start neutral
        flexibility_indicators = []

        # Price flexibility based on history
        if listing_history.price_drops:
            total_reduction = sum(drop.get("percentage", 0) for drop in listing_history.price_drops)
            flexibility_score += min(total_reduction * 2, 30)  # Max 30 points
            flexibility_indicators.append("price_reduction_history")

        # Market pressure flexibility
        if listing_history.days_on_market > 60:
            flexibility_score += 20
            flexibility_indicators.append("market_pressure")

        # Multiple offers handling
        if listing_history.offers_received and listing_history.offers_received > 1:
            flexibility_score -= 15  # Less flexible with multiple offers
            flexibility_indicators.append("multiple_offers_received")

        # Market context adjustments
        if market_context:
            market_condition = market_context.get("market_condition")
            if market_condition == "buyers_market":
                flexibility_score += 15
                flexibility_indicators.append("buyers_market_pressure")
            elif market_condition == "sellers_market":
                flexibility_score -= 10
                flexibility_indicators.append("sellers_market_strength")

        return {
            "flexibility_score": max(0, min(100, flexibility_score)),
            "flexibility_indicators": flexibility_indicators,
            "negotiation_openness": "high"
            if flexibility_score > 70
            else "moderate"
            if flexibility_score > 40
            else "low",
        }

    async def _get_ai_psychological_insights(
        self,
        listing_history: ListingHistory,
        behavioral_analysis: Dict[str, Any],
        communication_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Get AI-enhanced psychological insights using Claude"""

        context = f"""
        Analyze this seller's psychology based on their listing behavior:
        
        Listing Details:
        - Days on Market: {listing_history.days_on_market}
        - Original Price: ${listing_history.original_list_price}
        - Current Price: ${listing_history.current_price}
        - Price Drops: {len(listing_history.price_drops)}
        - Shows/Views: {listing_history.showing_requests}/{listing_history.listing_views}
        
        Behavioral Pattern: {behavioral_analysis.get("behavioral_pattern")}
        
        Communication Data: {communication_data or "None available"}
        
        Provide psychological insights focusing on:
        1. Emotional state and attachment
        2. Financial pressure indicators
        3. Relationship building potential
        4. Negotiation hot buttons
        5. Primary concerns
        """

        try:
            ai_response = await self.claude_assistant.analyze_with_context(context)

            # Parse AI insights into structured data
            return {
                "ai_emotional_assessment": ai_response.get("emotional_state", "neutral"),
                "ai_relationship_potential": ai_response.get("relationship_importance", 50),
                "ai_concerns": ai_response.get("primary_concerns", []),
                "ai_hot_buttons": ai_response.get("hot_buttons", []),
                "ai_confidence": ai_response.get("confidence", 75),
            }
        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return {
                "ai_emotional_assessment": "unknown",
                "ai_relationship_potential": 50,
                "ai_concerns": [],
                "ai_hot_buttons": [],
                "ai_confidence": 0,
            }

    def _synthesize_psychology_profile(
        self,
        behavioral_analysis: Dict[str, Any],
        urgency_analysis: Dict[str, Any],
        motivation_analysis: Dict[str, Any],
        flexibility_analysis: Dict[str, Any],
        ai_insights: Dict[str, Any],
        communication_data: Optional[Dict[str, Any]],
    ) -> SellerPsychologyProfile:
        """Synthesize all analyses into comprehensive psychology profile"""

        # Extract communication patterns
        response_time = None
        communication_style = "professional"
        if communication_data:
            response_time = communication_data.get("avg_response_time_hours")
            communication_style = communication_data.get("communication_tone", "professional").lower()

        # Calculate composite scores
        emotional_attachment = self._calculate_emotional_attachment(
            motivation_analysis, ai_insights, behavioral_analysis
        )

        financial_pressure = self._calculate_financial_pressure(
            motivation_analysis, urgency_analysis, behavioral_analysis
        )

        # Combine AI insights with rule-based analysis
        primary_concerns = ai_insights.get("ai_concerns", [])
        if urgency_analysis["urgency_score"] > 70:
            primary_concerns.append("time_pressure")
        if financial_pressure > 70:
            primary_concerns.append("financial_constraints")

        negotiation_hot_buttons = ai_insights.get("ai_hot_buttons", [])
        if flexibility_analysis["flexibility_score"] < 40:
            negotiation_hot_buttons.append("pricing_sensitivity")

        return SellerPsychologyProfile(
            motivation_type=motivation_analysis["primary_motivation"],
            urgency_level=urgency_analysis["urgency_level"],
            urgency_score=urgency_analysis["urgency_score"],
            behavioral_pattern=behavioral_analysis["behavioral_pattern"],
            emotional_attachment_score=emotional_attachment,
            financial_pressure_score=financial_pressure,
            flexibility_score=flexibility_analysis["flexibility_score"],
            response_time_hours=response_time,
            communication_style=communication_style,
            primary_concerns=primary_concerns[:5],  # Top 5 concerns
            negotiation_hot_buttons=negotiation_hot_buttons[:5],  # Top 5 hot buttons
            relationship_importance=ai_insights.get("ai_relationship_potential", 50),
        )

    def _calculate_emotional_attachment(
        self, motivation_analysis: Dict, ai_insights: Dict, behavioral_analysis: Dict
    ) -> float:
        """Calculate emotional attachment score (0-100)"""

        base_score = 30.0

        # Motivation-based adjustment
        if motivation_analysis["primary_motivation"] == SellerMotivationType.EMOTIONAL:
            base_score += 40
        elif motivation_analysis["primary_motivation"] == SellerMotivationType.STRATEGIC:
            base_score -= 15

        # AI assessment adjustment
        ai_emotional = ai_insights.get("ai_emotional_assessment", "neutral")
        if "high" in ai_emotional.lower() or "strong" in ai_emotional.lower():
            base_score += 25
        elif "low" in ai_emotional.lower() or "detached" in ai_emotional.lower():
            base_score -= 20

        # Behavioral indicators
        if behavioral_analysis["behavioral_pattern"] == ListingBehaviorPattern.OVERPRICED_STUBBORN:
            base_score += 20  # Often indicates emotional attachment

        return max(0, min(100, base_score))

    def _calculate_financial_pressure(
        self, motivation_analysis: Dict, urgency_analysis: Dict, behavioral_analysis: Dict
    ) -> float:
        """Calculate financial pressure score (0-100)"""

        base_score = 20.0

        # Motivation-based adjustment
        if motivation_analysis["primary_motivation"] == SellerMotivationType.FINANCIAL:
            base_score += 40
        elif motivation_analysis["primary_motivation"] == SellerMotivationType.DISTRESSED:
            base_score += 60

        # Urgency indicators
        base_score += urgency_analysis["urgency_score"] * 0.3

        # Behavioral pressure indicators
        if behavioral_analysis["behavioral_pattern"] == ListingBehaviorPattern.PRICE_DROPPER:
            base_score += 25

        return max(0, min(100, base_score))

    def _calculate_listing_persistence(self, listing_history: ListingHistory) -> Dict[str, Any]:
        """Calculate how persistent seller has been with listing"""

        persistence_score = 50.0  # Base persistence

        if listing_history.days_on_market > 90:
            persistence_score += 30
        elif listing_history.days_on_market < 30:
            persistence_score -= 20

        if listing_history.previous_listing_attempts and listing_history.previous_listing_attempts > 1:
            persistence_score += 40

        return {
            "persistence_score": max(0, min(100, persistence_score)),
            "listing_commitment": "high" if persistence_score > 70 else "moderate" if persistence_score > 40 else "low",
        }

    def _assess_engagement_quality(self, view_to_showing_ratio: float, showing_to_offer_ratio: float) -> str:
        """Assess quality of market engagement"""

        if view_to_showing_ratio > 0.15 and showing_to_offer_ratio > 0.3:
            return "high_quality"
        elif view_to_showing_ratio > 0.08 and showing_to_offer_ratio > 0.15:
            return "moderate_quality"
        else:
            return "low_quality"


# Singleton instance
_seller_psychology_analyzer = None


def get_seller_psychology_analyzer() -> SellerPsychologyAnalyzer:
    """Get singleton instance of SellerPsychologyAnalyzer"""
    global _seller_psychology_analyzer
    if _seller_psychology_analyzer is None:
        _seller_psychology_analyzer = SellerPsychologyAnalyzer()
    return _seller_psychology_analyzer
