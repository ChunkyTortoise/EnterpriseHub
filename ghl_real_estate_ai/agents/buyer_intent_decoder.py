"""
Buyer Intent Decoder Engine - Buyer Bot Component
Calculates buyer-specific Financial Readiness Score (FRS) and Motivation Score (MS).
Designed to identify 'Serious Buyers' and filter 'Window Shoppers'.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile

logger = logging.getLogger(__name__)

class BuyerIntentDecoder:
    """
    Decodes buyer intent using linguistic markers and behavioral signals.
    Implements buyer-specific FRS and Motivation scoring for purchase qualification.
    """

    def __init__(self):
        # Financial Readiness Markers
        self.high_finance_readiness = ["pre-approved", "cash buyer", "loan approved", "down payment ready", "financing secured"]
        self.medium_finance_readiness = ["getting pre-approved", "working with lender", "checking financing"]
        self.low_finance_readiness = ["need to talk to bank", "not sure about financing", "what's my budget"]

        # Budget Clarity Markers
        self.clear_budget = ["budget is", "can afford", "max price", "price range", "up to"]
        self.flexible_budget = ["around", "approximately", "roughly", "ballpark"]
        self.vague_budget = ["not sure", "depends", "varies", "flexible"]

        # Urgency Markers
        self.immediate_urgency = ["need to move", "lease ending", "must buy", "urgent", "this month"]
        self.medium_urgency = ["looking seriously", "want to move", "ready to buy", "3 months"]
        self.low_urgency = ["just looking", "browsing", "might buy", "eventually", "someday"]

        # Timeline Markers
        self.committed_timeline = ["by", "before", "deadline", "need to close", "must move"]
        self.flexible_timeline = ["soon", "this year", "when we find the right one"]
        self.vague_timeline = ["eventually", "when the time is right", "no rush"]

        # Property Preference Markers
        self.specific_preferences = ["must have", "required", "need", "specific", "exact"]
        self.flexible_preferences = ["prefer", "would like", "hoping for", "ideally"]
        self.vague_preferences = ["open", "flexible", "whatever", "not picky"]

        # Decision Authority Markers
        self.full_authority = ["I decide", "my choice", "my decision", "I'm buying"]
        self.shared_authority = ["we decide", "both of us", "need to discuss", "talk to spouse"]
        self.limited_authority = ["need approval", "have to ask", "my wife decides", "not my decision"]

    def analyze_buyer(self, buyer_id: str, conversation_history: List[Dict[str, str]]) -> BuyerIntentProfile:
        """
        Analyze buyer intent from conversation history.

        Args:
            buyer_id: The buyer's unique identifier
            conversation_history: List of conversation messages

        Returns:
            BuyerIntentProfile: Complete buyer analysis with scores and classification
        """
        try:
            # Extract text content
            conversation_text = " ".join([
                msg.get("content", "").lower()
                for msg in conversation_history
                if msg.get("role") == "user"
            ])

            # Calculate component scores
            financial_readiness = self._score_financial_readiness(conversation_text)
            budget_clarity = self._score_budget_clarity(conversation_text)
            financing_status = self._score_financing_status(conversation_text)

            urgency_score = self._score_urgency(conversation_text)
            timeline_pressure = self._score_timeline_commitment(conversation_text)
            consequence_awareness = self._score_consequence_awareness(conversation_text)

            preference_clarity = self._score_preference_clarity(conversation_text)
            market_realism = self._score_market_realism(conversation_text)
            decision_authority = self._score_decision_authority(conversation_text)

            # Calculate overall buyer temperature
            overall_score = (
                (financial_readiness + budget_clarity + financing_status) / 3 * 0.4 +
                (urgency_score + timeline_pressure + consequence_awareness) / 3 * 0.35 +
                (preference_clarity + market_realism + decision_authority) / 3 * 0.25
            )

            buyer_temperature = self._classify_buyer_temperature(overall_score)
            next_step = self._determine_next_qualification_step(
                financial_readiness, urgency_score, preference_clarity, decision_authority
            )

            return BuyerIntentProfile(
                financial_readiness=financial_readiness,
                budget_clarity=budget_clarity,
                financing_status_score=financing_status,
                urgency_score=urgency_score,
                timeline_pressure=timeline_pressure,
                consequence_awareness=consequence_awareness,
                preference_clarity=preference_clarity,
                market_realism=market_realism,
                decision_authority=decision_authority,
                buyer_temperature=buyer_temperature,
                confidence_level=min(95.0, len(conversation_history) * 10),
                conversation_turns=len(conversation_history),
                key_insights=self._extract_key_insights(conversation_text),
                next_qualification_step=next_step
            )

        except Exception as e:
            logger.error(f"Error analyzing buyer intent for {buyer_id}: {str(e)}", exc_info=True)
            return self._create_default_profile(buyer_id)

    def _score_financial_readiness(self, text: str) -> float:
        """Score financial readiness based on linguistic markers (0-100)."""
        score = 30  # Base score

        # High readiness markers (+20 each, max 3)
        high_matches = sum(1 for marker in self.high_finance_readiness if marker in text)
        score += min(high_matches * 20, 60)

        # Medium readiness markers (+10 each, max 2)
        medium_matches = sum(1 for marker in self.medium_finance_readiness if marker in text)
        score += min(medium_matches * 10, 20)

        # Low readiness markers (-10 each, max 2)
        low_matches = sum(1 for marker in self.low_finance_readiness if marker in text)
        score -= min(low_matches * 10, 20)

        return max(0, min(100, score))

    def _score_budget_clarity(self, text: str) -> float:
        """Score budget clarity based on specific price mentions and ranges."""
        score = 20  # Base score

        # Look for specific dollar amounts
        dollar_pattern = r'\$[\d,]+'
        dollar_mentions = len(re.findall(dollar_pattern, text))
        score += min(dollar_mentions * 15, 45)  # Max 3 mentions

        # Clear budget markers
        clear_matches = sum(1 for marker in self.clear_budget if marker in text)
        score += min(clear_matches * 10, 30)

        # Vague budget markers (penalty)
        vague_matches = sum(1 for marker in self.vague_budget if marker in text)
        score -= min(vague_matches * 10, 20)

        return max(0, min(100, score))

    def _score_financing_status(self, text: str) -> float:
        """Score financing status and preparedness."""
        score = 25  # Base score

        if any(marker in text for marker in ["pre-approved", "approved", "cash"]):
            score += 50
        elif any(marker in text for marker in ["working with lender", "getting approved"]):
            score += 30
        elif any(marker in text for marker in ["need financing", "first time buyer"]):
            score += 15
        elif any(marker in text for marker in ["don't know", "not sure about financing"]):
            score -= 20

        return max(0, min(100, score))

    def _score_urgency(self, text: str) -> float:
        """Score buyer urgency based on timeline markers."""
        score = 25  # Base score

        # Immediate urgency markers
        immediate_matches = sum(1 for marker in self.immediate_urgency if marker in text)
        score += min(immediate_matches * 25, 50)

        # Medium urgency markers
        medium_matches = sum(1 for marker in self.medium_urgency if marker in text)
        score += min(medium_matches * 15, 30)

        # Low urgency markers (penalty)
        low_matches = sum(1 for marker in self.low_urgency if marker in text)
        score -= min(low_matches * 15, 30)

        return max(0, min(100, score))

    def _score_timeline_commitment(self, text: str) -> float:
        """Score timeline commitment and specific deadlines."""
        score = 30  # Base score

        # Look for specific dates or deadlines
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(january|february|march|april|may|june|july|august|september|october|november|december)\b'
        date_mentions = len(re.findall(date_pattern, text, re.IGNORECASE))
        score += min(date_mentions * 20, 40)

        # Committed timeline markers
        committed_matches = sum(1 for marker in self.committed_timeline if marker in text)
        score += min(committed_matches * 15, 30)

        return max(0, min(100, score))

    def _score_consequence_awareness(self, text: str) -> float:
        """Score awareness of market consequences and timing."""
        score = 40  # Base score

        market_awareness_markers = ["rates", "interest", "market", "prices going up", "competition"]
        awareness_matches = sum(1 for marker in market_awareness_markers if marker in text)
        score += min(awareness_matches * 12, 60)

        return max(0, min(100, score))

    def _score_preference_clarity(self, text: str) -> float:
        """Score clarity of property preferences."""
        score = 20  # Base score

        # Count specific property features mentioned
        features = ["bedroom", "bathroom", "garage", "yard", "pool", "schools", "location"]
        feature_mentions = sum(1 for feature in features if feature in text)
        score += min(feature_mentions * 10, 60)

        # Specific preference markers
        specific_matches = sum(1 for marker in self.specific_preferences if marker in text)
        score += min(specific_matches * 8, 32)

        return max(0, min(100, score))

    def _score_market_realism(self, text: str) -> float:
        """Score realistic expectations vs market conditions."""
        score = 50  # Base score

        # Reality markers (positive)
        reality_markers = ["realistic", "understand", "market conditions", "competitive"]
        reality_matches = sum(1 for marker in reality_markers if marker in text)
        score += min(reality_matches * 15, 45)

        # Unrealistic markers (negative)
        unrealistic_markers = ["steal", "bargain", "way below", "perfect deal"]
        unrealistic_matches = sum(1 for marker in unrealistic_markers if marker in text)
        score -= min(unrealistic_matches * 15, 30)

        return max(0, min(100, score))

    def _score_decision_authority(self, text: str) -> float:
        """Score decision-making authority."""
        score = 40  # Base score

        # Full authority indicators
        if any(marker in text for marker in self.full_authority):
            score += 40
        # Shared authority indicators
        elif any(marker in text for marker in self.shared_authority):
            score += 20
        # Limited authority indicators
        elif any(marker in text for marker in self.limited_authority):
            score -= 20

        return max(0, min(100, score))

    def _classify_buyer_temperature(self, overall_score: float) -> str:
        """Classify buyer temperature based on overall score."""
        if overall_score >= 75:
            return "hot"
        elif overall_score >= 50:
            return "warm"
        elif overall_score >= 35:
            return "lukewarm"
        elif overall_score >= 20:
            return "cold"
        else:
            return "ice_cold"

    def _determine_next_qualification_step(self, financial: float, urgency: float,
                                         preferences: float, authority: float) -> str:
        """Determine next qualification step based on scores."""
        if financial < 50:
            return "budget"
        elif urgency < 50:
            return "timeline"
        elif preferences < 50:
            return "preferences"
        elif authority < 50:
            return "decision_makers"
        else:
            return "property_search"

    def _extract_key_insights(self, text: str) -> Dict[str, Any]:
        """Extract key insights from conversation."""
        insights = {
            "has_specific_timeline": any(marker in text for marker in self.committed_timeline),
            "mentions_financing": any(marker in text for marker in self.high_finance_readiness + self.medium_finance_readiness),
            "has_clear_preferences": len([f for f in ["bedroom", "bathroom", "garage"] if f in text]) >= 2,
            "shows_urgency": any(marker in text for marker in self.immediate_urgency),
            "decision_maker_identified": any(marker in text for marker in self.full_authority + self.shared_authority)
        }
        return insights

    def _create_default_profile(self, buyer_id: str) -> BuyerIntentProfile:
        """Create default profile for error cases."""
        return BuyerIntentProfile(
            financial_readiness=25.0,
            budget_clarity=25.0,
            financing_status_score=25.0,
            urgency_score=25.0,
            timeline_pressure=25.0,
            consequence_awareness=25.0,
            preference_clarity=25.0,
            market_realism=50.0,
            decision_authority=25.0,
            buyer_temperature="cold",
            confidence_level=10.0,
            conversation_turns=0,
            key_insights={},
            next_qualification_step="budget"
        )