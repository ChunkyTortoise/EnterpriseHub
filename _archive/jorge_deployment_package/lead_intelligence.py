#!/usr/bin/env python3
"""
Standalone Lead Intelligence for Jorge's Bot System

Simplified lead analysis without external AI dependencies.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LeadIntelligence:
    """
    Simplified lead intelligence system for Jorge's bots.

    Provides basic lead analysis using keyword matching and pattern recognition.
    In production, this would use Claude AI for more sophisticated analysis.
    """

    def __init__(self):
        """Initialize lead intelligence"""
        self.logger = logging.getLogger(__name__)

    async def analyze_lead_comprehensive(
        self,
        lead_id: str,
        message_text: str,
        lead_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze lead message and return comprehensive analysis"""

        try:
            analysis = {
                "intent": self._detect_intent(message_text),
                "urgency_signals": self._detect_urgency(message_text),
                "motivation": self._extract_motivation(message_text),
                "sentiment": self._analyze_sentiment(message_text),
                "lead_quality": self._assess_lead_quality(message_text, lead_context),
                "next_actions": self._suggest_next_actions(message_text, lead_context)
            }

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing lead {lead_id}: {e}")
            return self._get_default_analysis()

    def _detect_intent(self, message: str) -> str:
        """Detect the intent of the message"""

        message_lower = message.lower()

        # Buying intent
        buy_keywords = ["buy", "buying", "purchase", "looking for", "house hunt", "home search"]
        if any(keyword in message_lower for keyword in buy_keywords):
            return "buying_intent"

        # Selling intent
        sell_keywords = ["sell", "selling", "list", "listing", "market value", "what's my house worth"]
        if any(keyword in message_lower for keyword in sell_keywords):
            return "selling_intent"

        # Investment intent
        invest_keywords = ["invest", "investment", "rental", "flip", "portfolio", "cash flow"]
        if any(keyword in message_lower for keyword in invest_keywords):
            return "investment_intent"

        # Information seeking
        info_keywords = ["information", "details", "tell me", "explain", "how", "what", "when"]
        if any(keyword in message_lower for keyword in info_keywords):
            return "information_seeking"

        return "general_inquiry"

    def _detect_urgency(self, message: str) -> List[str]:
        """Detect urgency signals in the message"""

        message_lower = message.lower()
        urgency_signals = []

        # Time-based urgency
        urgent_time = ["asap", "immediately", "urgent", "right away", "this week", "by friday"]
        for signal in urgent_time:
            if signal in message_lower:
                urgency_signals.append(f"time_urgency: {signal}")

        # Financial urgency
        financial_urgent = ["pre-approved", "cash buyer", "must sell", "foreclosure", "need money"]
        for signal in financial_urgent:
            if signal in message_lower:
                urgency_signals.append(f"financial_urgency: {signal}")

        # Emotional urgency
        emotional_urgent = ["desperate", "help", "emergency", "stressed", "worried"]
        for signal in emotional_urgent:
            if signal in message_lower:
                urgency_signals.append(f"emotional_urgency: {signal}")

        return urgency_signals

    def _extract_motivation(self, message: str) -> str:
        """Extract motivation from the message"""

        message_lower = message.lower()

        # Family motivations
        if any(phrase in message_lower for phrase in ["growing family", "new baby", "kids", "school district"]):
            return "family_growth"

        # Relocation motivations
        if any(phrase in message_lower for phrase in ["job", "work", "relocating", "transfer", "moving"]):
            return "relocation"

        # Lifestyle motivations
        if any(phrase in message_lower for phrase in ["upgrade", "bigger", "smaller", "downsize", "luxury"]):
            return "lifestyle_change"

        # Financial motivations
        if any(phrase in message_lower for phrase in ["investment", "rent", "income", "profit", "money"]):
            return "financial"

        # Life events
        if any(phrase in message_lower for phrase in ["divorce", "death", "inherited", "retirement"]):
            return "life_event"

        return "general"

    def _analyze_sentiment(self, message: str) -> str:
        """Analyze sentiment of the message"""

        message_lower = message.lower()

        # Positive indicators
        positive_words = ["excited", "love", "great", "perfect", "amazing", "wonderful", "happy"]
        positive_count = sum(1 for word in positive_words if word in message_lower)

        # Negative indicators
        negative_words = ["hate", "terrible", "awful", "worried", "stressed", "frustrated", "disappointed"]
        negative_count = sum(1 for word in negative_words if word in message_lower)

        # Neutral/inquiry indicators
        neutral_words = ["looking", "searching", "considering", "thinking", "maybe", "possibly"]
        neutral_count = sum(1 for word in neutral_words if word in message_lower)

        if positive_count > negative_count and positive_count > 0:
            return "positive"
        elif negative_count > positive_count and negative_count > 0:
            return "negative"
        elif neutral_count > 0:
            return "neutral"
        else:
            return "neutral"

    def _assess_lead_quality(self, message: str, context: Dict[str, Any]) -> float:
        """Assess lead quality on a scale of 0-1"""

        quality_score = 0.5  # Start with neutral

        message_lower = message.lower()

        # Positive quality indicators
        if any(phrase in message_lower for phrase in ["pre-approved", "cash", "ready to buy"]):
            quality_score += 0.2

        if any(phrase in message_lower for phrase in ["specific location", "budget", "timeline"]):
            quality_score += 0.1

        if len(message) > 50:  # Detailed messages indicate engagement
            quality_score += 0.1

        # Negative quality indicators
        if any(phrase in message_lower for phrase in ["just looking", "no rush", "maybe someday"]):
            quality_score -= 0.2

        if len(message) < 10:  # Very short messages
            quality_score -= 0.1

        # Context-based adjustments
        if context.get("conversation_history"):
            history_count = len(context["conversation_history"])
            if history_count > 3:  # Engaged conversation
                quality_score += 0.1

        return max(0.0, min(1.0, quality_score))

    def _suggest_next_actions(self, message: str, context: Dict[str, Any]) -> List[str]:
        """Suggest next actions based on analysis"""

        actions = []
        message_lower = message.lower()

        # Intent-based actions
        if "buying_intent" in self._detect_intent(message):
            actions.append("qualify_buyer")
            actions.append("capture_budget")

        elif "selling_intent" in self._detect_intent(message):
            actions.append("qualify_seller")
            actions.append("schedule_listing_consultation")

        # Urgency-based actions
        urgency_signals = self._detect_urgency(message)
        if urgency_signals:
            actions.append("escalate_to_agent")
            actions.append("schedule_immediate_call")

        # Default actions
        if not actions:
            actions.append("continue_qualification")
            actions.append("nurture_lead")

        return actions

    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when processing fails"""

        return {
            "intent": "general_inquiry",
            "urgency_signals": [],
            "motivation": "general",
            "sentiment": "neutral",
            "lead_quality": 0.5,
            "next_actions": ["continue_qualification"]
        }


class PredictiveLeadScorer:
    """
    Simplified predictive lead scoring system.

    Provides basic lead scoring without complex ML models.
    """

    def __init__(self):
        """Initialize predictive scorer"""
        self.logger = logging.getLogger(__name__)

    async def calculate_predictive_score(
        self,
        context: Dict[str, Any],
        location: str = ""
    ) -> Any:
        """Calculate predictive lead score"""

        try:
            # Extract relevant factors
            qualification = context.get("qualification", {})
            extracted_data = context.get("extracted_data", {})

            # Calculate base score
            base_score = 50.0

            # Budget factor
            if qualification.get("budget_range"):
                base_score += 15

            # Timeline factor
            timeline = qualification.get("timeline", "")
            if "immediate" in timeline.lower():
                base_score += 20
            elif any(term in timeline.lower() for term in ["week", "month"]):
                base_score += 10

            # Location factor
            if qualification.get("location_preference"):
                base_score += 10

            # Engagement factor
            urgency_score = qualification.get("urgency_score", 0)
            base_score += urgency_score * 15

            # Conversation quality
            if context.get("conversation_history"):
                history_length = len(context["conversation_history"])
                base_score += min(10, history_length * 2)

            # Clamp score
            final_score = max(0, min(100, base_score))

            # Determine priority level
            if final_score >= 80:
                priority = "high"
            elif final_score >= 60:
                priority = "medium"
            else:
                priority = "low"

            # Calculate closing probability
            closing_probability = final_score / 100.0

            # Create result object
            class ScoreResult:
                def __init__(self):
                    self.overall_score = final_score
                    self.priority_level = priority
                    self.closing_probability = closing_probability
                    self.overall_priority_score = final_score
                    self.net_yield_estimate = 0.15  # Default 15% yield

            return ScoreResult()

        except Exception as e:
            self.logger.error(f"Error calculating predictive score: {e}")

            # Return default score
            class DefaultResult:
                def __init__(self):
                    self.overall_score = 50.0
                    self.priority_level = "medium"
                    self.closing_probability = 0.5
                    self.overall_priority_score = 50.0
                    self.net_yield_estimate = 0.15

            return DefaultResult()


# Factory functions for easy instantiation
def get_enhanced_lead_intelligence() -> LeadIntelligence:
    """Get enhanced lead intelligence instance"""
    return LeadIntelligence()


def get_enhanced_lead_intelligence_async() -> LeadIntelligence:
    """Get enhanced lead intelligence instance (async compatible)"""
    return LeadIntelligence()


class PredictiveLeadScorerV2(PredictiveLeadScorer):
    """Alias for compatibility"""
    pass