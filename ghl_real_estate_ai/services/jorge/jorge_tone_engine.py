#!/usr/bin/env python3
"""
Jorge's Confrontational Tone Engine

This module implements Jorge's specific messaging requirements:
- No emojis (professional only)
- No hyphens (SMS compatibility)
- <160 characters (SMS limit compliance)
- Confrontational but professional tone
- Direct question delivery

Author: Claude Code Assistant
Created: 2026-01-19
"""

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig


class MessageType(Enum):
    """Types of messages Jorge sends"""
    QUALIFICATION_QUESTION = "qualification_question"
    FOLLOW_UP = "follow_up"
    HOT_SELLER_HANDOFF = "hot_seller_handoff"
    OBJECTION_RESPONSE = "objection_response"
    CLOSING = "closing"


@dataclass
class ToneProfile:
    """Jorge's tone configuration"""
    max_length: int = 160  # SMS character limit
    allow_emojis: bool = False  # Jorge never uses emojis
    allow_hyphens: bool = False  # No hyphens for SMS compatibility
    directness_level: float = 0.8  # High directness (0.0-1.0)
    professionalism_level: float = 0.7  # Balanced professionalism


class JorgeToneEngine:
    """
    Generates messages matching Jorge's confrontational yet professional tone.

    Key Requirements:
    1. Direct and to the point
    2. No softening language ("maybe", "perhaps", "possibly")
    3. Clear expectations and urgency
    4. Professional but not overly friendly
    5. SMS-compliant formatting
    """

    def __init__(self):
        self.tone_profile = ToneProfile()
        self.config = JorgeSellerConfig()

    def generate_qualification_message(
        self,
        question_number: int,
        seller_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Jorge's confrontational qualification question.

        Args:
            question_number: Which of the 4 questions (1-4)
            seller_name: Optional seller name for personalization
            context: Additional context for message customization

        Returns:
            SMS-compliant message with confrontational tone
        """
        # Get base question from config
        base_question = self.config.SELLER_QUESTIONS.get(question_number, "")

        if not base_question:
            raise ValueError(f"Invalid question number: {question_number}")

        # Apply confrontational tone modifications
        message = self._apply_confrontational_tone(base_question, seller_name)

        # Ensure SMS compliance
        message = self._ensure_sms_compliance(message)

        return message

    def generate_follow_up_message(
        self,
        last_response: str,
        question_number: int,
        seller_name: Optional[str] = None
    ) -> str:
        """
        Generate follow-up when seller doesn't respond to question.

        Args:
            last_response: Seller's last response (or empty if no response)
            question_number: Current question number
            seller_name: Seller name for personalization

        Returns:
            Confrontational follow-up message
        """
        if not last_response.strip():
            # No response - direct follow-up
            message = self._generate_no_response_followup(question_number)
        else:
            # Inadequate response - push for specifics
            message = self._generate_inadequate_response_followup(question_number, last_response)

        if seller_name:
            message = f"{seller_name}, {message.lower()}"

        return self._ensure_sms_compliance(message)

    def generate_hot_seller_handoff(
        self,
        seller_name: Optional[str] = None,
        agent_name: str = "our team"
    ) -> str:
        """
        Generate message for hot seller handoff to agent.

        Args:
            seller_name: Seller name
            agent_name: Agent or team name for handoff

        Returns:
            Direct handoff message
        """
        base_message = f"Based on your responses, {agent_name} needs to speak with you today. What time works best for a quick call?"

        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"

        return self._ensure_sms_compliance(base_message)

    def generate_objection_response(
        self,
        objection_type: str,
        seller_name: Optional[str] = None
    ) -> str:
        """
        Generate response to common seller objections.

        Args:
            objection_type: Type of objection (timeline, price, condition, etc.)
            seller_name: Seller name for personalization

        Returns:
            Direct objection handling message
        """
        objection_responses = {
            "timeline_too_fast": "I understand. What timeline would work for you to sell?",
            "price_too_low": "What price would make you comfortable selling today?",
            "need_repairs": "How much work are we talking about? Basic cleaning or major renovations?",
            "not_ready": "What would need to change for you to be ready to sell?",
            "just_looking": "Fair enough. What would it take to move from looking to selling?",
            "market_timing": "What market conditions are you waiting for specifically?"
        }

        message = objection_responses.get(objection_type,
                                        "I understand. Help me understand what's holding you back.")

        if seller_name:
            message = f"{seller_name}, {message.lower()}"

        return self._ensure_sms_compliance(message)

    def _apply_confrontational_tone(self, base_message: str, seller_name: Optional[str] = None) -> str:
        """Apply Jorge's confrontational tone to base message."""

        # Remove softening language
        message = self._remove_softening_language(base_message)

        # Make more direct
        message = self._increase_directness(message)

        # Add personalization if name provided
        if seller_name:
            message = f"{seller_name}, {message.lower()}"

        return message

    def _remove_softening_language(self, message: str) -> str:
        """Remove words that soften the confrontational tone."""

        softening_words = [
            "please", "perhaps", "maybe", "possibly", "might",
            "could", "would you mind", "if you don't mind",
            "sorry", "excuse me", "pardon", "I hope"
        ]

        for word in softening_words:
            # Remove softening words (case insensitive)
            pattern = r'\b' + re.escape(word) + r'\b'
            message = re.sub(pattern, '', message, flags=re.IGNORECASE)

        # Clean up extra spaces
        message = re.sub(r'\s+', ' ', message).strip()

        return message

    def _increase_directness(self, message: str) -> str:
        """Make message more direct and confrontational."""

        # Replace indirect constructions with direct ones
        replacements = {
            r'\bwould you\b': 'do you',
            r'\bcould you\b': 'can you',
            r'\bmight you\b': 'will you',
            r'\bwould it be possible\b': 'will you',
            r'\bI was wondering if\b': '',
            r'\bI would like to know\b': 'tell me'
        }

        for pattern, replacement in replacements.items():
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

        # Clean up extra spaces
        message = re.sub(r'\s+', ' ', message).strip()

        return message

    def _ensure_sms_compliance(self, message: str) -> str:
        """Ensure message meets SMS compliance requirements."""

        # Remove emojis (Jorge never uses them)
        message = self._remove_emojis(message)

        # Remove hyphens (SMS compatibility)
        message = self._remove_hyphens(message)

        # Ensure under 160 characters
        if len(message) > self.tone_profile.max_length:
            message = self._truncate_message(message)

        return message

    def _remove_emojis(self, message: str) -> str:
        """Remove all emojis from message."""
        # Unicode emoji pattern
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', message)

    def _remove_hyphens(self, message: str) -> str:
        """Remove hyphens for SMS compatibility."""
        # Replace common hyphenated constructions
        replacements = {
            r'\bmove-in ready\b': 'move in ready',
            r'\bup-to-date\b': 'up to date',
            r'\bwell-maintained\b': 'well maintained',
            r'\btop-tier\b': 'top tier',
            r'\bhigh-end\b': 'high end',
            r'\breal-estate\b': 'real estate',
            r'\bmulti-family\b': 'multi family',
            r'\bco-op\b': 'coop',
            r'\bre-sale\b': 'resale'
        }

        for pattern, replacement in replacements.items():
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

        # Remove any remaining hyphens
        message = message.replace('-', ' ')

        # Clean up extra spaces
        message = re.sub(r'\s+', ' ', message).strip()

        return message

    def _truncate_message(self, message: str) -> str:
        """Truncate message to SMS length limit while preserving meaning."""

        if len(message) <= self.tone_profile.max_length:
            return message

        # Try to truncate at sentence boundary
        sentences = message.split('. ')
        if len(sentences) > 1:
            truncated = sentences[0]
            if len(truncated) <= self.tone_profile.max_length:
                return truncated + ('.' if not truncated.endswith('?') else '')

        # Truncate at word boundary
        words = message.split()
        truncated_words = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= self.tone_profile.max_length:
                truncated_words.append(word)
                current_length += len(word) + 1
            else:
                break

        result = ' '.join(truncated_words)

        # Ensure it ends properly
        if result and not result[-1] in '.!?':
            result += '.'

        return result

    def _generate_no_response_followup(self, question_number: int) -> str:
        """Generate follow-up for when seller doesn't respond."""

        followups = {
            1: "I need to know what's motivating you to sell and where you're moving.",
            2: "The timeline question is important. Would 30 to 45 days work or not?",
            3: "I need to know the condition of your home. Move in ready or needs work?",
            4: "What price would get you to sell? Give me a number."
        }

        return followups.get(question_number, "I need an answer to move forward.")

    def _generate_inadequate_response_followup(self, question_number: int, response: str) -> str:
        """Generate follow-up for inadequate responses."""

        # Detect vague responses
        vague_indicators = ["maybe", "not sure", "don't know", "thinking", "considering"]

        if any(indicator in response.lower() for indicator in vague_indicators):
            push_for_specifics = {
                1: "I need specifics. What exactly is driving you to sell and where are you moving to?",
                2: "Yes or no: would selling in 30 to 45 days work for your situation?",
                3: "Be specific about your home condition. What exactly needs to be done?",
                4: "I need a dollar amount. What price would make you sell today?"
            }
            return push_for_specifics.get(question_number, "I need a specific answer, not maybe.")

        # Default pushback for unclear responses
        return f"That doesn't answer my question. {self._generate_no_response_followup(question_number)}"

    def validate_message_compliance(self, message: str) -> Dict[str, Any]:
        """
        Validate message against Jorge's tone requirements.

        Returns:
            Dict with compliance status and violations
        """
        violations = []

        # Check length
        if len(message) > self.tone_profile.max_length:
            violations.append(f"Message too long: {len(message)}/{self.tone_profile.max_length} characters")

        # Check for emojis
        if re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]', message):
            violations.append("Contains emojis")

        # Check for hyphens
        if '-' in message:
            violations.append("Contains hyphens")

        # Check for softening language
        softening_words = ["please", "perhaps", "maybe", "possibly", "sorry"]
        found_softening = [word for word in softening_words if word.lower() in message.lower()]
        if found_softening:
            violations.append(f"Contains softening language: {', '.join(found_softening)}")

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "character_count": len(message),
            "directness_score": self._calculate_directness_score(message)
        }

    def _calculate_directness_score(self, message: str) -> float:
        """Calculate directness score (0.0-1.0) for message."""

        # Higher score = more direct/confrontational
        score = 0.5  # Base score

        # Add points for direct constructions
        direct_indicators = ["what", "when", "where", "how much", "yes or no", "tell me", "I need"]
        for indicator in direct_indicators:
            if indicator.lower() in message.lower():
                score += 0.1

        # Subtract points for indirect constructions
        indirect_indicators = ["would you", "could you", "might you", "perhaps", "maybe"]
        for indicator in indirect_indicators:
            if indicator.lower() in message.lower():
                score -= 0.15

        # Ensure score is in valid range
        return max(0.0, min(1.0, score))