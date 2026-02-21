"""
Personality Adapter for adapting messaging based on lead personality and preferences.
"""

from typing import Dict, List

from ghl_real_estate_ai.agents.lead.config import ResponsePattern
from ghl_real_estate_ai.agents.lead.constants import PERSONALITY_PROFILES
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class PersonalityAdapter:
    """Adapts messaging based on lead personality and preferences"""

    def __init__(self):
        self.personality_profiles = PERSONALITY_PROFILES

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

        # Add personality-specific prefix
        prefix = profile.get("prefix", "")
        if prefix:
            adapted_message = f"{prefix}{adapted_message}"

        return adapted_message

    def get_personality_profile(self, personality_type: str) -> Dict:
        """Get the profile for a specific personality type."""
        return self.personality_profiles.get(personality_type, self.personality_profiles["relationship"])

    def list_personality_types(self) -> List[str]:
        """List all available personality types."""
        return list(self.personality_profiles.keys())
