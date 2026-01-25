"""
Enhanced Intent Decoder Service - Phase 4 Implementation
Multi-Modal Conversation Intelligence Engine for Real Estate AI Platform
"""

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor

from ghl_real_estate_ai.models.intelligence_context import (
    IntentClassification,
    ConversationContext,
    CustomerProfile
)

logger = logging.getLogger(__name__)


class IntentCategory(Enum):
    """Primary intent classifications with confidence thresholds"""
    IMMEDIATE_BUYER = "immediate_buyer"
    IMMEDIATE_SELLER = "immediate_seller"
    RESEARCH_PHASE = "research_phase"
    INVESTMENT_OPPORTUNITY = "investment_opportunity"
    RENTAL_INQUIRY = "rental_inquiry"
    REFINANCE_INTEREST = "refinance_interest"
    UNKNOWN = "unknown"


class UrgencyLevel(Enum):
    """Timeline urgency classification"""
    IMMEDIATE = "immediate"  # <30 days
    MODERATE = "moderate"    # 1-6 months
    FLEXIBLE = "flexible"    # 6+ months
    UNDETERMINED = "undetermined"


class PriceSensitivity(Enum):
    """Customer price sensitivity levels"""
    HIGH = "high"           # Negotiates aggressively
    MEDIUM = "medium"       # Standard negotiations
    LOW = "low"             # Price less important than other factors


@dataclass
class IntentAnalysisResult:
    """Comprehensive intent analysis results"""
    primary_intent: IntentCategory
    confidence_score: float
    urgency_level: UrgencyLevel
    price_sensitivity: PriceSensitivity
    predicted_timeline: Optional[str]
    budget_range: Optional[Tuple[int, int]]
    location_preferences: List[str]
    key_motivators: List[str]
    risk_factors: List[str]
    recommended_agent: str
    handoff_context: Dict[str, Any]
    analysis_timestamp: datetime


@dataclass
class VoiceAnalysisResult:
    """Voice pattern analysis results"""
    sentiment_score: float  # -1.0 to 1.0
    confidence_level: float  # 0.0 to 1.0
    urgency_indicators: List[str]
    emotional_state: str
    speaking_pace: str  # fast, normal, slow
    voice_stress_level: float  # 0.0 to 1.0


@dataclass
class BehavioralSignals:
    """Customer behavioral pattern data"""
    website_session_duration: Optional[int]  # seconds
    pages_visited: Optional[int]
    search_patterns: List[str]
    email_engagement: Optional[float]  # 0.0 to 1.0
    phone_response_time: Optional[int]  # hours
    previous_contact_attempts: Optional[int]


class EnhancedIntentDecoder:
    """
    Advanced Intent Decoder with multi-modal conversation intelligence

    Features:
    - Multi-modal analysis (voice, text, behavioral)
    - Austin market context understanding
    - Predictive intent modeling
    - Real-time decision engine
    """

    def __init__(self):
        self.austin_neighborhoods = {
            "high_value": ["west lake hills", "tarrytown", "rollingwood", "westlake"],
            "emerging": ["mueller", "east austin", "riverside", "govalle"],
            "family_focused": ["cedar park", "round rock", "pflugerville", "lakeway"],
            "urban_core": ["downtown", "soco", "rainey street", "south first"],
            "tech_corridor": ["domain", "arboretum", "northwest hills"],
            "creative": ["south austin", "east cesar chavez", "holly"]
        }

        self.intent_patterns = {
            IntentCategory.IMMEDIATE_BUYER: [
                "pre-approved", "ready to buy", "need to close", "looking to purchase",
                "house hunting", "want to make offer", "closing date", "already sold"
            ],
            IntentCategory.IMMEDIATE_SELLER: [
                "need to sell", "listing my house", "market my property", "quick sale",
                "already moved", "job transfer", "divorce", "estate sale"
            ],
            IntentCategory.RESEARCH_PHASE: [
                "thinking about", "considering", "maybe", "exploring options",
                "just curious", "what if", "someday", "future"
            ],
            IntentCategory.INVESTMENT_OPPORTUNITY: [
                "investment property", "rental income", "cash flow", "fix and flip",
                "multiple properties", "portfolio", "ROI", "cap rate"
            ]
        }

        self.urgency_indicators = {
            UrgencyLevel.IMMEDIATE: [
                "urgent", "ASAP", "immediately", "this month", "by end of",
                "deadline", "closing soon", "need to move"
            ],
            UrgencyLevel.MODERATE: [
                "within", "by summer", "next few months", "before end of year",
                "spring market", "fall market"
            ],
            UrgencyLevel.FLEXIBLE: [
                "eventually", "no rush", "when the time is right", "flexible",
                "watching market", "waiting for"
            ]
        }

        self.price_sensitivity_patterns = {
            PriceSensitivity.HIGH: [
                "best deal", "negotiate", "discount", "lowest price", "can't afford",
                "too expensive", "budget constraints", "need to save"
            ],
            PriceSensitivity.MEDIUM: [
                "fair price", "reasonable", "competitive", "market value",
                "good deal", "worth it"
            ],
            PriceSensitivity.LOW: [
                "price is fine", "don't care about", "quality matters", "best in area",
                "premium", "luxury", "whatever it takes"
            ]
        }

    async def analyze_customer_interaction(
        self,
        text_content: str,
        conversation_history: List[Dict[str, Any]],
        voice_data: Optional[bytes] = None,
        behavioral_signals: Optional[BehavioralSignals] = None,
        customer_profile: Optional[CustomerProfile] = None
    ) -> IntentAnalysisResult:
        """
        Comprehensive multi-modal intent analysis

        Args:
            text_content: Current conversation text
            conversation_history: Previous interaction history
            voice_data: Audio data for voice analysis (optional)
            behavioral_signals: Website/app behavioral data (optional)
            customer_profile: Existing customer profile data (optional)

        Returns:
            IntentAnalysisResult with comprehensive analysis
        """
        start_time = datetime.now()

        try:
            # Run analysis components in parallel for performance
            tasks = [
                self._analyze_text_intent(text_content, conversation_history),
                self._analyze_urgency_level(text_content, conversation_history),
                self._analyze_price_sensitivity(text_content, conversation_history),
                self._extract_location_preferences(text_content),
                self._identify_motivators_and_risks(text_content, conversation_history)
            ]

            # Add voice analysis if available
            if voice_data:
                tasks.append(self._analyze_voice_patterns(voice_data))

            results = await asyncio.gather(*tasks)

            # Unpack core analysis results
            intent_result = results[0]
            urgency_result = results[1]
            price_sensitivity_result = results[2]
            location_preferences = results[3]
            motivators, risks = results[4]

            # Voice analysis if available
            voice_analysis = results[5] if len(results) > 5 else None

            # Apply behavioral signals analysis
            behavioral_adjustment = 0.0
            if behavioral_signals:
                behavioral_adjustment = self._analyze_behavioral_signals(behavioral_signals)

            # Calculate final confidence with all inputs
            final_confidence = self._calculate_composite_confidence(
                intent_result[1],  # base text confidence
                voice_analysis.confidence_level if voice_analysis else 0.5,
                behavioral_adjustment,
                len(conversation_history)
            )

            # Predict timeline and budget
            predicted_timeline = self._predict_timeline(urgency_result, conversation_history)
            budget_range = self._estimate_budget_range(text_content, conversation_history)

            # Determine optimal agent routing
            recommended_agent = self._determine_agent_routing(
                intent_result[0], final_confidence, urgency_result, budget_range
            )

            # Prepare handoff context
            handoff_context = self._prepare_handoff_context(
                intent_result[0], motivators, risks, location_preferences,
                voice_analysis, behavioral_signals
            )

            analysis_result = IntentAnalysisResult(
                primary_intent=intent_result[0],
                confidence_score=final_confidence,
                urgency_level=urgency_result,
                price_sensitivity=price_sensitivity_result,
                predicted_timeline=predicted_timeline,
                budget_range=budget_range,
                location_preferences=location_preferences,
                key_motivators=motivators,
                risk_factors=risks,
                recommended_agent=recommended_agent,
                handoff_context=handoff_context,
                analysis_timestamp=datetime.now()
            )

            # Log performance metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"Intent analysis completed in {processing_time:.1f}ms, "
                       f"confidence: {final_confidence:.2f}, agent: {recommended_agent}")

            return analysis_result

        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}", exc_info=True)
            # Return safe fallback result
            return self._create_fallback_result()

    async def _analyze_text_intent(
        self,
        text_content: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Tuple[IntentCategory, float]:
        """Analyze text content for primary intent classification"""

        text_lower = text_content.lower()
        all_text = " ".join([text_lower] +
                           [msg.get("content", "").lower() for msg in conversation_history[-5:]])

        intent_scores = {}

        for intent_category, patterns in self.intent_patterns.items():
            score = 0.0
            pattern_matches = 0

            for pattern in patterns:
                if pattern in all_text:
                    score += 1.0
                    pattern_matches += 1

                    # Boost score for recent mentions
                    if pattern in text_lower:
                        score += 0.5

            # Normalize by number of patterns
            if len(patterns) > 0:
                intent_scores[intent_category] = score / len(patterns)

        # Find highest scoring intent
        if not intent_scores:
            return IntentCategory.UNKNOWN, 0.3

        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(intent_scores[best_intent], 1.0)

        # Boost confidence for clear indicators
        if confidence > 0.3:
            confidence = min(confidence * 1.2, 1.0)

        return best_intent, confidence

    async def _analyze_urgency_level(
        self,
        text_content: str,
        conversation_history: List[Dict[str, Any]]
    ) -> UrgencyLevel:
        """Analyze timeline urgency from conversation"""

        text_lower = text_content.lower()
        all_text = " ".join([text_lower] +
                           [msg.get("content", "").lower() for msg in conversation_history[-3:]])

        urgency_scores = {}

        for urgency_level, indicators in self.urgency_indicators.items():
            score = sum(1 for indicator in indicators if indicator in all_text)
            urgency_scores[urgency_level] = score

        if not urgency_scores or max(urgency_scores.values()) == 0:
            return UrgencyLevel.UNDETERMINED

        return max(urgency_scores, key=urgency_scores.get)

    async def _analyze_price_sensitivity(
        self,
        text_content: str,
        conversation_history: List[Dict[str, Any]]
    ) -> PriceSensitivity:
        """Analyze customer price sensitivity patterns"""

        text_lower = text_content.lower()
        all_text = " ".join([text_lower] +
                           [msg.get("content", "").lower() for msg in conversation_history[-3:]])

        sensitivity_scores = {}

        for sensitivity_level, patterns in self.price_sensitivity_patterns.items():
            score = sum(1 for pattern in patterns if pattern in all_text)
            sensitivity_scores[sensitivity_level] = score

        if not sensitivity_scores or max(sensitivity_scores.values()) == 0:
            return PriceSensitivity.MEDIUM  # Default assumption

        return max(sensitivity_scores, key=sensitivity_scores.get)

    async def _extract_location_preferences(self, text_content: str) -> List[str]:
        """Extract Austin-specific location preferences"""

        text_lower = text_content.lower()
        found_locations = []

        for category, neighborhoods in self.austin_neighborhoods.items():
            for neighborhood in neighborhoods:
                if neighborhood in text_lower:
                    found_locations.append(neighborhood)

        # Also look for zip codes
        zip_pattern = r'\b787\d{2}\b'
        zip_codes = re.findall(zip_pattern, text_content)
        found_locations.extend(zip_codes)

        return found_locations

    async def _identify_motivators_and_risks(
        self,
        text_content: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Identify key motivating factors and risk indicators"""

        text_lower = text_content.lower()
        all_text = " ".join([text_lower] +
                           [msg.get("content", "").lower() for msg in conversation_history[-5:]])

        motivators = []
        risks = []

        # Common motivating factors
        motivator_patterns = {
            "job_transfer": ["new job", "relocating", "transfer", "work"],
            "growing_family": ["baby", "expecting", "kids", "family", "schools"],
            "investment": ["investment", "rental", "income", "portfolio"],
            "downsizing": ["empty nest", "too big", "smaller", "maintenance"],
            "upgrade": ["bigger", "nicer", "luxury", "dream home"]
        }

        for motivator, patterns in motivator_patterns.items():
            if any(pattern in all_text for pattern in patterns):
                motivators.append(motivator)

        # Risk factors
        risk_patterns = {
            "financing_issues": ["credit", "pre-approval", "loan", "financing"],
            "timeline_pressure": ["deadline", "urgent", "need to sell"],
            "market_uncertainty": ["market", "prices", "timing", "waiting"],
            "first_time_buyer": ["first time", "never bought", "don't know"]
        }

        for risk, patterns in risk_patterns.items():
            if any(pattern in all_text for pattern in patterns):
                risks.append(risk)

        return motivators, risks

    async def _analyze_voice_patterns(self, voice_data: bytes) -> VoiceAnalysisResult:
        """
        Analyze voice patterns for emotional state and urgency

        Note: This is a placeholder for voice analysis integration.
        In production, this would integrate with a voice analysis service.
        """
        # Placeholder implementation
        return VoiceAnalysisResult(
            sentiment_score=0.0,
            confidence_level=0.5,
            urgency_indicators=[],
            emotional_state="neutral",
            speaking_pace="normal",
            voice_stress_level=0.3
        )

    def _analyze_behavioral_signals(self, signals: BehavioralSignals) -> float:
        """Analyze behavioral patterns for intent confidence adjustment"""

        adjustment = 0.0

        # High engagement indicators
        if signals.website_session_duration and signals.website_session_duration > 300:  # >5 minutes
            adjustment += 0.1

        if signals.pages_visited and signals.pages_visited > 5:
            adjustment += 0.1

        if signals.email_engagement and signals.email_engagement > 0.7:
            adjustment += 0.15

        if signals.phone_response_time and signals.phone_response_time < 2:  # <2 hours
            adjustment += 0.1

        # Search pattern analysis
        if signals.search_patterns:
            high_intent_searches = ["mortgage", "pre-approval", "real estate agent", "buy house"]
            if any(search in " ".join(signals.search_patterns).lower()
                   for search in high_intent_searches):
                adjustment += 0.1

        return min(adjustment, 0.3)  # Cap at 30% adjustment

    def _calculate_composite_confidence(
        self,
        text_confidence: float,
        voice_confidence: float,
        behavioral_adjustment: float,
        conversation_length: int
    ) -> float:
        """Calculate final confidence score from multiple sources"""

        # Base confidence from text analysis (weighted 60%)
        composite_score = text_confidence * 0.6

        # Voice analysis contribution (weighted 25%)
        composite_score += voice_confidence * 0.25

        # Conversation history bonus (weighted 15%)
        history_bonus = min(conversation_length / 10.0, 1.0) * 0.15
        composite_score += history_bonus

        # Apply behavioral adjustment
        composite_score += behavioral_adjustment

        # Ensure bounds
        return max(0.0, min(composite_score, 1.0))

    def _predict_timeline(self, urgency: UrgencyLevel, conversation_history: List[Dict]) -> str:
        """Predict customer timeline based on urgency and conversation context"""

        timeline_map = {
            UrgencyLevel.IMMEDIATE: "1-4 weeks",
            UrgencyLevel.MODERATE: "1-6 months",
            UrgencyLevel.FLEXIBLE: "6+ months",
            UrgencyLevel.UNDETERMINED: "3-12 months"
        }

        base_timeline = timeline_map[urgency]

        # Adjust based on conversation context
        if len(conversation_history) > 5:
            # Multiple interactions suggest more serious intent
            if urgency == UrgencyLevel.FLEXIBLE:
                return "3-6 months"

        return base_timeline

    def _estimate_budget_range(
        self,
        text_content: str,
        conversation_history: List[Dict]
    ) -> Optional[Tuple[int, int]]:
        """Estimate budget range from conversation content"""

        all_text = text_content + " " + " ".join(
            msg.get("content", "") for msg in conversation_history[-5:]
        )

        # Look for explicit price mentions
        price_patterns = [
            r'\$(\d+(?:,\d{3})*(?:k|K)?)',
            r'(\d+(?:,\d{3})*(?:k|K)?) dollars?',
            r'around (\d+(?:,\d{3})*(?:k|K)?)',
            r'budget.{0,10}(\d+(?:,\d{3})*(?:k|K)?)'
        ]

        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            for match in matches:
                try:
                    # Handle 'k' suffix
                    if match.lower().endswith('k'):
                        price = int(match[:-1].replace(',', '')) * 1000
                    else:
                        price = int(match.replace(',', ''))

                    # Only consider realistic Austin price ranges
                    if 100000 <= price <= 5000000:
                        prices.append(price)
                except ValueError:
                    continue

        if prices:
            min_price = min(prices)
            max_price = max(prices)
            # Add reasonable buffer around mentioned prices
            return (int(min_price * 0.9), int(max_price * 1.1))

        return None

    def _determine_agent_routing(
        self,
        intent: IntentCategory,
        confidence: float,
        urgency: UrgencyLevel,
        budget_range: Optional[Tuple[int, int]]
    ) -> str:
        """Determine optimal agent routing based on analysis results"""

        # High-value leads (>$1M) get specialized routing
        if budget_range and budget_range[0] > 1000000:
            return "luxury_specialist_agent"

        # High confidence immediate intents get specialized agents
        if confidence >= 0.9:
            if intent == IntentCategory.IMMEDIATE_BUYER:
                return "jorge_buyer_bot"
            elif intent == IntentCategory.IMMEDIATE_SELLER:
                return "jorge_seller_bot"
            elif intent == IntentCategory.INVESTMENT_OPPORTUNITY:
                return "investment_specialist_agent"

        # Medium confidence or research phase leads go to lead bot
        if confidence >= 0.6 or intent == IntentCategory.RESEARCH_PHASE:
            return "lead_bot"

        # Complex or uncertain cases get human routing
        if urgency == UrgencyLevel.IMMEDIATE and confidence < 0.6:
            return "human_agent"

        # Default fallback
        return "lead_bot"

    def _prepare_handoff_context(
        self,
        intent: IntentCategory,
        motivators: List[str],
        risks: List[str],
        locations: List[str],
        voice_analysis: Optional[VoiceAnalysisResult],
        behavioral_signals: Optional[BehavioralSignals]
    ) -> Dict[str, Any]:
        """Prepare comprehensive context for agent handoff"""

        context = {
            "intent_summary": {
                "category": intent.value,
                "key_motivators": motivators,
                "risk_factors": risks,
                "preferred_locations": locations
            },
            "conversation_insights": {
                "engagement_level": "high" if behavioral_signals and
                                              behavioral_signals.website_session_duration and
                                              behavioral_signals.website_session_duration > 300 else "medium",
                "response_urgency": voice_analysis.urgency_indicators if voice_analysis else [],
                "emotional_state": voice_analysis.emotional_state if voice_analysis else "neutral"
            },
            "recommended_approach": self._get_approach_recommendations(intent, motivators, risks),
            "escalation_triggers": self._get_escalation_triggers(intent, risks),
            "rapport_builders": self._get_rapport_builders(motivators, locations)
        }

        return context

    def _get_approach_recommendations(
        self,
        intent: IntentCategory,
        motivators: List[str],
        risks: List[str]
    ) -> List[str]:
        """Generate recommended conversation approaches"""

        recommendations = []

        if intent == IntentCategory.IMMEDIATE_BUYER:
            recommendations.extend([
                "Focus on available inventory matching their criteria",
                "Discuss pre-approval status and financing readiness",
                "Emphasize competitive market conditions"
            ])

        elif intent == IntentCategory.IMMEDIATE_SELLER:
            recommendations.extend([
                "Start with market analysis and pricing discussion",
                "Assess property condition and preparation needs",
                "Discuss timeline and marketing strategy"
            ])

        if "financing_issues" in risks:
            recommendations.append("Address financing options and lender connections")

        if "first_time_buyer" in risks:
            recommendations.append("Provide educational content and process guidance")

        return recommendations

    def _get_escalation_triggers(self, intent: IntentCategory, risks: List[str]) -> List[str]:
        """Define when to escalate to human agent"""

        triggers = []

        if "financing_issues" in risks and intent == IntentCategory.IMMEDIATE_BUYER:
            triggers.append("Complex financing situation requiring expert consultation")

        if "timeline_pressure" in risks:
            triggers.append("Urgent timeline requiring immediate human attention")

        if intent == IntentCategory.INVESTMENT_OPPORTUNITY:
            triggers.append("Investment analysis requiring specialized expertise")

        return triggers

    def _get_rapport_builders(self, motivators: List[str], locations: List[str]) -> List[str]:
        """Suggest conversation elements for building rapport"""

        builders = []

        if "growing_family" in motivators:
            builders.append("Discuss school districts and family-friendly amenities")

        if "job_transfer" in motivators:
            builders.append("Acknowledge stress of relocation and offer local insights")

        if locations:
            for location in locations[:2]:  # First few mentioned locations
                builders.append(f"Share knowledge about {location} neighborhood")

        return builders

    def _create_fallback_result(self) -> IntentAnalysisResult:
        """Create safe fallback result when analysis fails"""

        return IntentAnalysisResult(
            primary_intent=IntentCategory.UNKNOWN,
            confidence_score=0.3,
            urgency_level=UrgencyLevel.UNDETERMINED,
            price_sensitivity=PriceSensitivity.MEDIUM,
            predicted_timeline="3-12 months",
            budget_range=None,
            location_preferences=[],
            key_motivators=[],
            risk_factors=["analysis_error"],
            recommended_agent="lead_bot",
            handoff_context={
                "intent_summary": {"category": "unknown"},
                "recommended_approach": ["Use general qualification questions"],
                "escalation_triggers": ["Agent unable to determine intent"],
                "rapport_builders": ["Ask about their real estate needs"]
            },
            analysis_timestamp=datetime.now()
        )


# Factory functions for easy integration

async def create_enhanced_intent_decoder() -> EnhancedIntentDecoder:
    """Factory function to create configured intent decoder"""
    return EnhancedIntentDecoder()


async def analyze_customer_intent(
    text_content: str,
    conversation_history: List[Dict[str, Any]] = None,
    voice_data: Optional[bytes] = None,
    behavioral_data: Optional[Dict[str, Any]] = None
) -> IntentAnalysisResult:
    """
    Convenience function for quick intent analysis

    Args:
        text_content: Customer's text input
        conversation_history: Previous conversation messages
        voice_data: Optional voice recording data
        behavioral_data: Optional behavioral tracking data

    Returns:
        IntentAnalysisResult with comprehensive analysis
    """
    decoder = await create_enhanced_intent_decoder()

    # Convert behavioral data to BehavioralSignals object if provided
    behavioral_signals = None
    if behavioral_data:
        behavioral_signals = BehavioralSignals(
            website_session_duration=behavioral_data.get('session_duration'),
            pages_visited=behavioral_data.get('pages_visited'),
            search_patterns=behavioral_data.get('search_patterns', []),
            email_engagement=behavioral_data.get('email_engagement'),
            phone_response_time=behavioral_data.get('phone_response_time'),
            previous_contact_attempts=behavioral_data.get('contact_attempts')
        )

    return await decoder.analyze_customer_interaction(
        text_content=text_content,
        conversation_history=conversation_history or [],
        voice_data=voice_data,
        behavioral_signals=behavioral_signals
    )


if __name__ == "__main__":
    # Example usage
    async def main():
        # Test the enhanced intent decoder
        sample_text = "Hi, I'm pre-approved for a $650k mortgage and looking to buy in West Lake Hills. Need to close before my lease ends in 6 weeks."

        result = await analyze_customer_intent(sample_text)

        print(f"Intent: {result.primary_intent.value}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Recommended Agent: {result.recommended_agent}")
        print(f"Timeline: {result.predicted_timeline}")
        print(f"Budget Range: {result.budget_range}")

    asyncio.run(main())