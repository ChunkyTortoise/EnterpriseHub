"""
Lead scoring service for real estate AI.

Calculates lead quality scores based on NUMBER OF QUALIFYING QUESTIONS ANSWERED.
This is Jorge's requirement: count questions, not points.

Scoring Methodology (Question Count):
- Budget confirmed: +1 question
- Location specified: +1 question
- Timeline confirmed: +1 question
- Property requirements (beds/baths/must-haves): +1 question
- Financing status: +1 question
- Motivation (why buying/selling now): +1 question
- Home condition (sellers only): +1 question

Lead Classifications (Jorge's Criteria):
- Hot Lead: 3+ questions answered (immediate action required)
- Warm Lead: 2 questions answered (follow up within 24 hours)
- Cold Lead: 0-1 questions answered (nurture campaign)
"""
from typing import Dict, Any, List
from datetime import datetime
import re
from typing import Dict, Any, List

try:
    from ghl_real_estate_ai.ghl_utils.config import settings
except ImportError:
    # Fallback settings for standalone deployment
    class Settings:
        hot_lead_threshold = 3
        warm_lead_threshold = 2
        cold_lead_threshold = 1
    settings = Settings()


class LeadScorer:
    """Calculate lead quality scores based on conversation analysis."""

    def __init__(self):
        """Initialize lead scorer with thresholds from config."""
        self.hot_threshold = settings.hot_lead_threshold
        self.warm_threshold = settings.warm_lead_threshold

    def calculate(self, context: Dict[str, Any]) -> int:
        """
        Calculate lead score based on NUMBER OF QUESTIONS ANSWERED.
        
        Jorge's Requirement: Count questions answered, not points.
        
        Qualifying Questions:
        1. Budget: Did they provide a budget/price range?
        2. Location: Did they specify a location/area?
        3. Timeline: Did they share when they want to buy/sell?
        4. Property Requirements: Beds/baths/must-haves?
        5. Financing: Pre-approval status?
        6. Motivation: Why buying/selling now?
        7. Home Condition: (Sellers only) Condition of their home?

        Args:
            context: Conversation context containing:
                - extracted_preferences: Dict of user preferences
                - conversation_history: List of messages
                - created_at: Conversation start time

        Returns:
            Number of questions answered (0-7)
        """
        questions_answered = 0
        prefs = context.get("extracted_preferences", {})

        # Question 1: Budget/Price Range
        if prefs.get("budget"):
            questions_answered += 1

        # Question 2: Location Preference
        if prefs.get("location"):
            questions_answered += 1

        # Question 3: Timeline
        if prefs.get("timeline"):
            questions_answered += 1

        # Question 4: Property Requirements (beds/baths/must-haves)
        if prefs.get("bedrooms") or prefs.get("bathrooms") or prefs.get("must_haves"):
            questions_answered += 1

        # Question 5: Financing Status
        if prefs.get("financing"):
            questions_answered += 1

        # Question 6: Motivation (why buying/selling now)
        if prefs.get("motivation"):
            questions_answered += 1

        # Question 7: Home Condition (sellers only)
        if prefs.get("home_condition"):
            questions_answered += 1

        return questions_answered

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
        Classify lead based on number of questions answered.
        
        Jorge's Rules:
        - Hot: 3+ questions answered
        - Warm: 2 questions answered
        - Cold: 0-1 questions answered

        Args:
            score: Number of questions answered (0-7)

        Returns:
            Lead classification: "hot", "warm", or "cold"
        """
        if score >= self.hot_threshold:  # 3+
            return "hot"
        elif score >= self.warm_threshold:  # 2
            return "warm"
        else:  # 0-1
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
        
        Returns question count (0-7) instead of points (0-100).

        Args:
            context: Conversation context

        Returns:
            Dict containing score, classification, reasoning, and recommended actions
        """
        score = self.calculate(context)
        classification = self.classify(score)
        actions = self.get_recommended_actions(score)

        # Build reasoning breakdown - show which questions were answered
        prefs = context.get("extracted_preferences", {})
        questions_answered = []

        if prefs.get("budget"):
            questions_answered.append(f"Budget: ${prefs.get('budget'):,}" if isinstance(prefs.get('budget'), (int, float)) else f"Budget: {prefs.get('budget')}")
        if prefs.get("location"):
            questions_answered.append(f"Location: {prefs.get('location')}")
        if prefs.get("timeline"):
            questions_answered.append(f"Timeline: {prefs.get('timeline')}")
        if prefs.get("bedrooms") or prefs.get("bathrooms") or prefs.get("must_haves"):
            prop_details = []
            if prefs.get("bedrooms"):
                prop_details.append(f"{prefs.get('bedrooms')} bed")
            if prefs.get("bathrooms"):
                prop_details.append(f"{prefs.get('bathrooms')} bath")
            if prefs.get("must_haves"):
                must_haves = prefs.get("must_haves")
                if isinstance(must_haves, list):
                    prop_details.append(", ".join(str(m) for m in must_haves))
                else:
                    prop_details.append(str(must_haves))
            
            # Ensure all items in prop_details are strings
            safe_prop_details = [str(p) for p in prop_details]
            questions_answered.append(f"Property: {', '.join(safe_prop_details)}")
        if prefs.get("financing"):
            questions_answered.append(f"Financing: {prefs.get('financing')}")
        if prefs.get("motivation"):
            questions_answered.append(f"Motivation: {prefs.get('motivation')}")
        if prefs.get("home_condition"):
            questions_answered.append(f"Home Condition: {prefs.get('home_condition')}")

        reasoning = (
            " | ".join([str(q) for q in questions_answered])
            if questions_answered
            else "No qualifying questions answered yet"
        )

        return {
            "score": score,
            "questions_answered": score,  # Make it explicit this is question count
            "classification": classification,
            "reasoning": reasoning,
            "recommended_actions": actions
        }
