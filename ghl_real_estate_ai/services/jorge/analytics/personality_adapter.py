"""Personality detection and message adaptation for Jorge bots.

This module analyzes conversation patterns to detect lead personality types
and adapts messaging style accordingly for better engagement.
"""

from typing import Dict, List

from ghl_real_estate_ai.services.jorge.analytics.models import ResponsePattern


class PersonalityAdapter:
    """Adapts messaging based on lead personality and preferences"""

    def __init__(self):
        self.personality_profiles = {
            "analytical": {
                "style": "data-driven",
                "tone": "professional",
                "format": "bullet points",
                "keywords": ["analysis", "data", "research", "comparison"],
            },
            "relationship": {
                "style": "personal",
                "tone": "warm",
                "format": "conversational",
                "keywords": ["understand", "help", "partnership", "together"],
            },
            "results": {
                "style": "direct",
                "tone": "urgent",
                "format": "brief",
                "keywords": ["action", "results", "quickly", "efficiently"],
            },
            "security": {
                "style": "cautious",
                "tone": "reassuring",
                "format": "detailed",
                "keywords": ["safe", "secure", "guaranteed", "protected"],
            },
        }

    async def detect_personality(self, conversation_history: List[Dict]) -> str:
        """Detect lead personality type from conversation patterns"""
        all_text = " ".join([m.get("content", "").lower() for m in conversation_history])

        personality_scores = {}
        for personality, profile in self.personality_profiles.items():
            score = sum(1 for keyword in profile["keywords"] if keyword in all_text)
            personality_scores[personality] = score

        # Return highest scoring personality or default to 'relationship'
        return (
            max(personality_scores, key=personality_scores.get) if any(personality_scores.values()) else "relationship"
        )

    async def adapt_message(self, base_message: str, personality_type: str, pattern: ResponsePattern) -> str:
        """Adapt message based on personality type and response patterns"""
        profile = self.personality_profiles.get(personality_type, self.personality_profiles["relationship"])

        # Adjust message length based on preference
        if pattern.message_length_preference == "brief" and profile["format"] != "brief":
            # Shorten message for brief preference
            sentences = base_message.split(". ")
            adapted_message = ". ".join(sentences[:2]) + "."
        else:
            adapted_message = base_message

        # Add personality-specific elements
        if personality_type == "analytical":
            adapted_message = f"Based on market data: {adapted_message}"
        elif personality_type == "relationship":
            adapted_message = f"I wanted to personally reach out: {adapted_message}"
        elif personality_type == "results":
            adapted_message = f"Quick update: {adapted_message}"
        elif personality_type == "security":
            adapted_message = f"To ensure we're on the right track: {adapted_message}"

        return adapted_message
