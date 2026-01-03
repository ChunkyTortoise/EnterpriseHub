"""
Lead scoring service for real estate AI.

Calculates lead quality scores (0-100) based on conversation context
and extracted preferences. Higher scores indicate more qualified leads.

Scoring Methodology:
- Budget confirmed: +30 points
- Pre-approved financing: +15 bonus
- Timeline confirmed: +25 points
- Urgent timeline: +10 bonus
- Location specified: +15 points
- Specific requirements: +10 points
- High engagement: +10 points

Lead Classifications:
- Hot Lead: 70+ (immediate action required)
- Warm Lead: 40-69 (follow up within 24 hours)
- Cold Lead: 0-39 (nurture campaign)
"""
from typing import Dict, Any, List
from datetime import datetime
import re
from core.config import settings


class LeadScorer:
    """Calculate lead quality scores based on conversation analysis."""

    def __init__(self):
        """Initialize lead scorer with thresholds from config."""
        self.hot_threshold = settings.hot_lead_threshold
        self.warm_threshold = settings.warm_lead_threshold

    def calculate(self, context: Dict[str, Any]) -> int:
        """
        Calculate lead score from conversation context.

        Args:
            context: Conversation context containing:
                - extracted_preferences: Dict of user preferences
                - conversation_history: List of messages
                - created_at: Conversation start time

        Returns:
            Lead score (0-100)
        """
        score = 0
        prefs = context.get("extracted_preferences", {})
        history = context.get("conversation_history", [])

        # Budget confirmed (+30 points)
        if prefs.get("budget"):
            score += 30
            # Pre-approved financing (+15 bonus)
            if prefs.get("financing") in ["pre-approved", "pre-qualified", "cash"]:
                score += 15

        # Timeline confirmed (+25 points)
        timeline = prefs.get("timeline", "")
        if timeline:
            score += 25
            # Urgent timeline (< 3 months) (+10 bonus)
            if self._is_urgent_timeline(timeline):
                score += 10

        # Location specified (+15 points)
        if prefs.get("location"):
            score += 15

        # Specific requirements (+10 points)
        if prefs.get("bedrooms") or prefs.get("bathrooms") or prefs.get("must_haves"):
            score += 10

        # Engagement level (+10 points if > 3 back-and-forth exchanges)
        if len(history) > 6:  # 3 user messages + 3 AI responses
            score += 10

        return min(score, 100)

    def _is_urgent_timeline(self, timeline: str) -> bool:
        """
        Determine if timeline indicates urgency.

        Args:
            timeline: User's timeline preference (e.g., "ASAP", "next month")

        Returns:
            True if timeline is urgent (< 3 months)
        """
        if not timeline:
            return False

        timeline_lower = timeline.lower()

        # Urgent keywords
        urgent_keywords = [
            "asap",
            "immediately",
            "urgent",
            "this month",
            "next month",
            "this week",
            "next week",
            "soon",
            "right away"
        ]

        return any(keyword in timeline_lower for keyword in urgent_keywords)

    def classify(self, score: int) -> str:
        """
        Classify lead based on score.

        Args:
            score: Lead score (0-100)

        Returns:
            Lead classification: "hot", "warm", or "cold"
        """
        if score >= self.hot_threshold:
            return "hot"
        elif score >= self.warm_threshold:
            return "warm"
        else:
            return "cold"

    def get_recommended_actions(self, score: int) -> List[str]:
        """
        Get recommended actions based on lead score.

        Args:
            score: Lead score (0-100)

        Returns:
            List of recommended actions for the agent
        """
        classification = self.classify(score)

        if classification == "hot":
            return [
                "Tag as 'Hot Lead'",
                "Notify agent via SMS immediately",
                "Schedule showing within 24-48 hours",
                "Prioritize in CRM dashboard",
                "Send pre-approval checklist if not completed"
            ]
        elif classification == "warm":
            return [
                "Tag as 'Warm Lead'",
                "Follow up within 24 hours",
                "Send market update email",
                "Add to weekly follow-up sequence"
            ]
        else:
            return [
                "Tag as 'Cold Lead'",
                "Add to nurture campaign",
                "Send educational content",
                "Follow up in 7 days"
            ]

    def calculate_with_reasoning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate score with detailed reasoning breakdown.

        Args:
            context: Conversation context

        Returns:
            Dict containing score, classification, reasoning, and recommended actions
        """
        score = self.calculate(context)
        classification = self.classify(score)
        actions = self.get_recommended_actions(score)

        # Build reasoning breakdown
        prefs = context.get("extracted_preferences", {})
        reasoning_parts = []

        if prefs.get("budget"):
            reasoning_parts.append(f"Budget confirmed: ${prefs.get('budget'):,}")
        if prefs.get("financing"):
            reasoning_parts.append(f"Financing status: {prefs.get('financing')}")
        if prefs.get("timeline"):
            reasoning_parts.append(f"Timeline: {prefs.get('timeline')}")
        if prefs.get("location"):
            reasoning_parts.append(f"Location: {prefs.get('location')}")

        reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Limited information provided"

        return {
            "score": score,
            "classification": classification,
            "reasoning": reasoning,
            "recommended_actions": actions
        }
