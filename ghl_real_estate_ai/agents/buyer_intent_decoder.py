"""
Buyer Intent Decoder Engine - Buyer Bot Component
Calculates buyer-specific Financial Readiness Score (FRS) and Motivation Score (MS).
Designed to identify 'Serious Buyers' and filter 'Window Shoppers'.
"""

from __future__ import annotations

import logging
import re
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient, GHLContact

from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile

logger = logging.getLogger(__name__)

class BuyerIntentDecoder:
    """
    Decodes buyer intent using linguistic markers and behavioral signals.
    Implements buyer-specific FRS and Motivation scoring for purchase qualification.
    """

    def __init__(self, ghl_client: Optional[EnhancedGHLClient] = None):
        self.ghl_client = ghl_client

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

    async def analyze_buyer_with_ghl(
        self,
        contact_id: str,
        conversation_history: List[Dict[str, str]],
        ghl_contact: Optional[GHLContact] = None,
    ) -> BuyerIntentProfile:
        """
        Enhanced buyer analysis that incorporates GHL contact data for better scoring.

        Pulls GHL contact data for budget, financing status, and property preferences.
        Uses GHL custom fields like budget_range, pre_approval_status, preferred_areas.
        Falls back to the standard analyze_buyer() if GHL data is unavailable.

        Args:
            contact_id: The buyer's GHL contact ID.
            conversation_history: List of conversation messages.
            ghl_contact: Pre-fetched GHLContact object (optional).

        Returns:
            BuyerIntentProfile with GHL-boosted scores.
        """
        # Attempt to fetch GHL contact data if not provided
        if ghl_contact is None and self.ghl_client is not None:
            try:
                ghl_contact = await self.ghl_client.get_contact(contact_id)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch GHL contact {contact_id}: {e}. "
                    "Falling back to conversation-only analysis."
                )

        # Fall back to standard analysis if no GHL data available
        if ghl_contact is None:
            logger.info(f"No GHL data for buyer {contact_id}, using conversation-only analysis")
            return self.analyze_buyer(contact_id, conversation_history)

        # Run standard conversation-based analysis first
        profile = self.analyze_buyer(contact_id, conversation_history)

        # Extract GHL data points
        try:
            ghl_data = {
                "tags": ghl_contact.tags or [],
                "custom_fields": ghl_contact.custom_fields or {},
                "source": ghl_contact.source,
                "date_added": ghl_contact.created_at,
                "last_activity": ghl_contact.last_activity_at or ghl_contact.updated_at,
            }
        except Exception as e:
            logger.warning(f"Error extracting GHL data for buyer {contact_id}: {e}")
            return profile

        # Apply GHL-based boosts
        boosted = self._apply_ghl_buyer_boosts(profile, ghl_data)
        return boosted

    def _apply_ghl_buyer_boosts(
        self,
        profile: BuyerIntentProfile,
        ghl_data: Dict[str, Any],
    ) -> BuyerIntentProfile:
        """
        Apply buyer-specific boosts/penalties based on GHL contact data.

        Boost logic:
        - Pre-approval status in custom fields → +20 financial_readiness, +15 financing_status
        - budget_range custom field present → +10 budget_clarity
        - preferred_areas custom field present → +10 preference_clarity
        - Tags: Active-Buyer → +15 urgency, Tour-Scheduled → +20 urgency
        - Engagement recency: < 3 days → +10 urgency, > 30 days → -10 urgency

        Args:
            profile: Base BuyerIntentProfile from conversation analysis.
            ghl_data: Extracted GHL data dict.

        Returns:
            New BuyerIntentProfile with boosted scores.
        """
        tags = [t.lower() for t in ghl_data.get("tags", [])]
        custom_fields = ghl_data.get("custom_fields", {})

        # Start with existing scores
        financial_readiness = profile.financial_readiness
        budget_clarity = profile.budget_clarity
        financing_status = profile.financing_status_score
        urgency = profile.urgency_score
        timeline_pressure = profile.timeline_pressure
        preference_clarity = profile.preference_clarity

        # --- Pre-approval status from GHL custom fields ---
        pre_approval = custom_fields.get("pre_approval_status", "").lower()
        if pre_approval in ("approved", "pre-approved", "cash"):
            financial_readiness += 20
            financing_status += 15
            logger.info(f"GHL pre-approval boost: +20 financial, +15 financing")
        elif pre_approval in ("in_progress", "applied"):
            financial_readiness += 10
            financing_status += 8
            logger.info(f"GHL pre-approval in-progress boost: +10 financial, +8 financing")

        # --- Budget range from GHL custom fields ---
        if custom_fields.get("budget_range"):
            budget_clarity += 10
            logger.info(f"GHL budget_range field present: +10 budget_clarity")

        # --- Preferred areas from GHL custom fields ---
        if custom_fields.get("preferred_areas"):
            preference_clarity += 10
            logger.info(f"GHL preferred_areas field present: +10 preference_clarity")

        # --- Tag-based urgency boosts ---
        if "tour-scheduled" in tags:
            urgency += 20
            timeline_pressure += 10
            logger.info(f"GHL Tour-Scheduled tag: +20 urgency, +10 timeline")
        if "active-buyer" in tags:
            urgency += 15
            logger.info(f"GHL Active-Buyer tag: +15 urgency")
        if "pre-approved" in tags:
            financial_readiness += 10
            financing_status += 10
            logger.info(f"GHL pre-approved tag: +10 financial, +10 financing")
        if "window-shopper" in tags:
            urgency -= 10
            logger.info(f"GHL Window-Shopper tag: -10 urgency")

        # --- Engagement recency factor ---
        last_activity = ghl_data.get("last_activity")
        if last_activity is not None:
            try:
                now = datetime.now(timezone.utc)
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=timezone.utc)
                days_since = (now - last_activity).days
                if days_since <= 3:
                    urgency += 10
                    logger.info(f"GHL recent activity ({days_since}d): +10 urgency")
                elif days_since <= 7:
                    urgency += 5
                elif days_since > 30:
                    urgency -= 10
                    logger.info(f"GHL stale activity ({days_since}d): -10 urgency")
            except Exception as e:
                logger.debug(f"Could not compute buyer engagement recency: {e}")

        # Clamp all scores to 0-100
        financial_readiness = max(0, min(100, financial_readiness))
        budget_clarity = max(0, min(100, budget_clarity))
        financing_status = max(0, min(100, financing_status))
        urgency = max(0, min(100, urgency))
        timeline_pressure = max(0, min(100, timeline_pressure))
        preference_clarity = max(0, min(100, preference_clarity))

        # Recalculate overall score with boosted components
        overall_score = (
            (financial_readiness + budget_clarity + financing_status) / 3 * 0.4 +
            (urgency + timeline_pressure + profile.consequence_awareness) / 3 * 0.35 +
            (preference_clarity + profile.market_realism + profile.decision_authority) / 3 * 0.25
        )

        buyer_temperature = self._classify_buyer_temperature(overall_score)
        next_step = self._determine_next_qualification_step(
            financial_readiness, urgency, preference_clarity, profile.decision_authority
        )

        return BuyerIntentProfile(
            financial_readiness=financial_readiness,
            budget_clarity=budget_clarity,
            financing_status_score=financing_status,
            urgency_score=urgency,
            timeline_pressure=timeline_pressure,
            consequence_awareness=profile.consequence_awareness,
            preference_clarity=preference_clarity,
            market_realism=profile.market_realism,
            decision_authority=profile.decision_authority,
            buyer_temperature=buyer_temperature,
            confidence_level=min(95.0, profile.confidence_level + 5.0),
            conversation_turns=profile.conversation_turns,
            key_insights=profile.key_insights,
            next_qualification_step=next_step,
        )

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