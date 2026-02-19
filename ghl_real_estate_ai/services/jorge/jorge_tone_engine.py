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
import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig


class MessageType(Enum):
    """Types of messages Jorge sends"""

    QUALIFICATION_QUESTION = "qualification_question"
    FOLLOW_UP = "follow_up"
    HOT_SELLER_HANDOFF = "hot_seller_handoff"
    OBJECTION_RESPONSE = "objection_response"
    CLOSING = "closing"
    LABELING = "labeling"
    CALIBRATED_QUESTION = "calibrated_question"


@dataclass
class NegotiationDrift:
    """Tracks shifts in seller's negotiation stance"""

    sentiment_shift: float = 0.0  # Positive = softening, Negative = firming
    responsiveness_delta: float = 0.0  # Change in response time
    hedging_count: int = 0  # Number of tentative words used
    is_softening: bool = False
    price_break_probability: float = 0.0  # Probability (0-1) that seller will accept lower price


class NegotiationStrategy:
    """Chris Voss / Spin Selling strategic patterns"""

    LABELS = [
        "It seems like {emotion} is important to you.",
        "It sounds like you're {feeling} about this.",
        "It looks like {situation} is the main priority.",
        "It seems like you feel {feeling} about the timeline.",
    ]

    CALIBRATED_QUESTIONS = [
        "How am I supposed to do that?",
        "What is it that brought us to this point?",
        "What about this is important to you?",
        "How does this affect your goal of moving?",
        "What happens if you don't sell?",
    ]


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

    def _personalize(self, name: str, message: str) -> str:
        """Prepend seller name, lowercasing only the first char for natural flow."""
        return f"{name}, {message[0].lower()}{message[1:]}" if message else f"{name},"

    def generate_qualification_message(
        self, question_number: int, seller_name: Optional[str] = None, context: Optional[Dict[str, Any]] = None
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
        self, last_response: str, question_number: int, seller_name: Optional[str] = None
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
            message = self._personalize(seller_name, message)

        return self._ensure_sms_compliance(message)

    def generate_hot_seller_handoff(self, seller_name: Optional[str] = None, agent_name: str = "our team") -> str:
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
            base_message = self._personalize(seller_name, base_message)

        return self._ensure_sms_compliance(base_message)

    def generate_take_away_close(
        self, seller_name: Optional[str] = None, reason: Optional[str] = None, psychology_profile: Any = None
    ) -> str:
        """
        Generate a "Take-Away Close" message for low-probability or vague leads.

        Args:
            seller_name: Seller name
            reason: Specific reason for the take-away close (e.g., 'vague', 'low_probability')
            psychology_profile: Optional psychological profile for tone tuning

        Returns:
            Confrontational take-away close message

        .. deprecated::
            Use friendly/consultative tone methods instead. See TONE_DEPRECATION.md.
        """
        warnings.warn(
            "generate_take_away_close is deprecated. Use friendly/consultative tone methods instead. "
            "See services/jorge/TONE_DEPRECATION.md.",
            DeprecationWarning,
            stacklevel=2,
        )
        # If seller has high emotional attachment, use loss aversion
        if psychology_profile and getattr(psychology_profile, "emotional_attachment_score", 0) > 70:
            base_message = "It seems you are too attached to the property to see the market reality. I'm going to close your file. Let me know if you decide to be a seller instead of a homeowner."
        elif reason == "low_probability":
            base_message = "It doesn't seem like you are serious about selling right now. I'm going to close your file so we can focus on active sellers. Reach out if things change."
        else:
            base_message = (
                "It sounds like you aren't ready to sell right now. Should we close your file and stop the process?"
            )

        if seller_name:
            base_message = self._personalize(seller_name, base_message)

        return self._ensure_sms_compliance(base_message)

    def generate_net_yield_justification(
        self,
        price_expectation: float,
        ai_valuation: float,
        net_yield: float,
        repair_estimate: float = 0,
        seller_name: Optional[str] = None,
        psychology_profile: Any = None,
    ) -> str:
        """
        Generate a "Net Yield" justification message when seller is firm on price but repairs needed.

        Args:
            price_expectation: Seller's expected price
            ai_valuation: AI's valuation (ARV or current market)
            net_yield: Calculated net yield percentage (0.0-1.0)
            repair_estimate: Estimated repair costs
            seller_name: Seller name for personalization
            psychology_profile: Optional psychological profile

        Returns:
            SMS-compliant ROI justification message

        .. deprecated::
            Use friendly/consultative tone methods instead. See TONE_DEPRECATION.md.
        """
        warnings.warn(
            "generate_net_yield_justification is deprecated. Use friendly/consultative tone methods instead. "
            "See services/jorge/TONE_DEPRECATION.md.",
            DeprecationWarning,
            stacklevel=2,
        )
        # If distressed, be even more direct about the financial reality
        if psychology_profile and getattr(psychology_profile, "motivation_type", "") == "distressed":
            base_message = f"Financial reality check: ${price_expectation:,.0f} is a pipe dream given the condition. Our max is ${ai_valuation:,.0f}. Are you ready to solve this problem or not?"
        elif repair_estimate > 0:
            base_message = f"Your ${price_expectation:,.0f} is above our ${ai_valuation:,.0f} valuation. With the repairs needed, the net yield is too low. How did you come up with that number?"
        else:
            base_message = f"At ${price_expectation:,.0f}, the net yield is only {net_yield:.1%}. Our valuation is closer to ${ai_valuation:,.0f}. What is your bottom dollar?"

        if seller_name:
            base_message = self._personalize(seller_name, base_message)

        return self._ensure_sms_compliance(base_message)

    def generate_objection_response(self, objection_type: str, seller_name: Optional[str] = None) -> str:
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
            "market_timing": "What market conditions are you waiting for specifically?",
        }

        message = objection_responses.get(objection_type, "I understand. Help me understand what's holding you back.")

        if seller_name:
            message = self._personalize(seller_name, message)

        return self._ensure_sms_compliance(message)

    def generate_cost_of_waiting_message(
        self, seller_name: Optional[str] = None, market_trend: str = "rising inventory"
    ) -> str:
        """
        Generate a 'Cost of Waiting' message for Loss Aversion personas.

        Args:
            seller_name: Seller name
            market_trend: Specific market trend to emphasize (e.g., 'rising inventory', 'interest rates')

        Returns:
            Confrontational urgency message

        .. deprecated::
            Use friendly/consultative tone methods instead. See TONE_DEPRECATION.md.
        """
        warnings.warn(
            "generate_cost_of_waiting_message is deprecated. Use friendly/consultative tone methods instead. "
            "See services/jorge/TONE_DEPRECATION.md.",
            DeprecationWarning,
            stacklevel=2,
        )
        if "rate" in market_trend.lower():
            base_message = "Yield spreads are tightening due to rate volatility. If you wait, your equity position will be diluted. Are you prepared to take that loss?"
        else:
            base_message = "Inventory velocity is slowing. Every week you wait increases your holding costs and lowers your net exit. Do you want to sell now or lose more?"

        if seller_name:
            base_message = self._personalize(seller_name, base_message)

        return self._ensure_sms_compliance(base_message)

    def generate_arbitrage_pitch(
        self, seller_name: Optional[str] = None, yield_spread: float = 0.0, market_area: str = "adjacent zones"
    ) -> str:
        """
        Generate an elite arbitrage pitch for investor personas.

        Args:
            seller_name: Seller name
            yield_spread: Calculated yield spread percentage
            market_area: Target market area

        Returns:
            Technical, data-driven arbitrage message

        .. deprecated::
            Use friendly/consultative tone methods instead. See TONE_DEPRECATION.md.
        """
        warnings.warn(
            "generate_arbitrage_pitch is deprecated. Use friendly/consultative tone methods instead. "
            "See services/jorge/TONE_DEPRECATION.md.",
            DeprecationWarning,
            stacklevel=2,
        )
        if yield_spread > 0:
            base_message = f"Market data indicates a {yield_spread:.1f}% yield spread in {market_area}. We are currently exploiting this pricing arbitrage. Do you want in or not?"
        else:
            base_message = f"We are tracking sub markets where yield spreads are outpacing city averages. This is an elite opportunity for capital deployment. What is your goal?"

        if seller_name:
            base_message = self._personalize(seller_name, base_message)

        return self._ensure_sms_compliance(base_message)

    def generate_labeled_question(self, emotion_or_situation: str, seller_name: Optional[str] = None) -> str:
        """Apply Voss-style 'Labeling' to a concern."""
        import random

        template = random.choice(NegotiationStrategy.LABELS)
        # Simplified mapping: emotion vs feeling vs situation
        label = template.format(
            emotion=emotion_or_situation, feeling=emotion_or_situation, situation=emotion_or_situation
        )

        if seller_name:
            label = self._personalize(seller_name, label)

        return self._ensure_sms_compliance(label)

    def generate_calibrated_question(self, index: int = 2, seller_name: Optional[str] = None) -> str:
        """Apply Voss-style 'Calibrated Question'."""
        question = NegotiationStrategy.CALIBRATED_QUESTIONS[index % len(NegotiationStrategy.CALIBRATED_QUESTIONS)]

        if seller_name:
            question = self._personalize(seller_name, question)

        return self._ensure_sms_compliance(question)

    def detect_negotiation_drift(self, history: List[Dict[str, Any]]) -> NegotiationDrift:
        """
        Analyze linguistic nuance to detect if a seller is moving from 'Firm' to 'Flexible'.

        Indicators:
        - Decrease in directness score
        - Increase in hedging ('maybe', 'possibly', 'we'll see')
        - Use of softening keywords ('flexible', 'bottom line', 'negotiable', 'OBO')
        - Change in response latency
        """
        drift = NegotiationDrift()
        if len(history) < 1:
            return drift

        hedging_words = ["maybe", "possibly", "think", "might", "could", "considering", "we'll see", "depends"]
        softening_words = [
            "flexible",
            "negotiable",
            "bottom line",
            "obo",
            "or best offer",
            "make an offer",
            "willing to talk",
        ]
        firming_words = ["firm", "fixed", "not moving", "final", "absolute", "won't take a penny less"]

        # Analyze last message
        last_msg = history[-1].get("content", "").lower()

        for word in hedging_words:
            if word in last_msg:
                drift.hedging_count += 1
                drift.sentiment_shift += 0.1

        for word in softening_words:
            if word in last_msg:
                drift.sentiment_shift += 0.3
                drift.is_softening = True

        for word in firming_words:
            if word in last_msg:
                drift.sentiment_shift -= 0.3

        # Simple drift logic: if hedging increases or softening words used
        if drift.hedging_count >= 2 or drift.sentiment_shift > 0.2:
            drift.is_softening = True

        # Calculate Price Break Probability
        # Base: sentiment shift + (hedging count * 0.1)
        base_prob = drift.sentiment_shift + (drift.hedging_count * 0.1)
        drift.price_break_probability = max(0.0, min(0.95, base_prob))

        return drift

    def _apply_confrontational_tone(self, base_message: str, seller_name: Optional[str] = None) -> str:
        """Apply Jorge's confrontational tone to base message."""

        # Remove softening language
        message = self._remove_softening_language(base_message)

        # Make more direct
        message = self._increase_directness(message)

        # Add personalization if name provided
        if seller_name:
            message = self._personalize(seller_name, message)

        return message

    def _remove_softening_language(self, message: str) -> str:
        """Remove words that soften the confrontational tone."""

        softening_words = [
            "please",
            "perhaps",
            "maybe",
            "possibly",
            "might",
            "could",
            "would you mind",
            "if you don't mind",
            "sorry",
            "excuse me",
            "pardon",
            "I hope",
        ]

        for word in softening_words:
            # Remove softening words (case insensitive)
            pattern = r"\b" + re.escape(word) + r"\b"
            message = re.sub(pattern, "", message, flags=re.IGNORECASE)

        # Clean up extra spaces
        message = re.sub(r"\s+", " ", message).strip()

        return message

    def _increase_directness(self, message: str) -> str:
        """Make message more direct and confrontational."""

        # Replace indirect constructions with direct ones
        replacements = {
            r"\bwould you\b": "do you",
            r"\bcould you\b": "can you",
            r"\bmight you\b": "will you",
            r"\bwould it be possible\b": "will you",
            r"\bI was wondering if\b": "",
            r"\bI would like to know\b": "tell me",
        }

        for pattern, replacement in replacements.items():
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

        # Clean up extra spaces
        message = re.sub(r"\s+", " ", message).strip()

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
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub("", message)

    def _remove_hyphens(self, message: str) -> str:
        """Remove hyphens for SMS compatibility."""
        # Replace common hyphenated constructions
        replacements = {
            r"\bmove-in ready\b": "move in ready",
            r"\bup-to-date\b": "up to date",
            r"\bwell-maintained\b": "well maintained",
            r"\btop-tier\b": "top tier",
            r"\bhigh-end\b": "high end",
            r"\breal-estate\b": "real estate",
            r"\bmulti-family\b": "multi family",
            r"\bco-op\b": "coop",
            r"\bre-sale\b": "resale",
        }

        for pattern, replacement in replacements.items():
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

        # Remove any remaining hyphens
        message = message.replace("-", " ")

        # Clean up extra spaces
        message = re.sub(r"\s+", " ", message).strip()

        return message

    def _truncate_message(self, message: str) -> str:
        """
        Truncate message to SMS length limit while preserving the CTA (Tail-Preserving).

        Strategy:
        1. Always keep the last sentence (The Question/CTA).
        2. Fill remaining space with the start of the message.
        3. If we must cut, cut from the middle/end of the context section.
        """
        if len(message) <= self.tone_profile.max_length:
            return message

        # Split into sentences (handling . ? !)
        # Simple split by punctuation followed by space
        sentences = re.split(r"(?<=[.?!])\s+", message)

        if not sentences:
            return message[: self.tone_profile.max_length - 3] + "..."

        # Identify CTA (Last sentence)
        cta = sentences[-1]

        # If CTA alone is too long (rare), truncate it directly
        if len(cta) > self.tone_profile.max_length:
            return cta[: self.tone_profile.max_length - 3] + "..."

        # Calculate remaining space
        # -4 for " ... " separator
        remaining_space = self.tone_profile.max_length - len(cta) - 4

        if remaining_space < 10:
            # Only enough space for CTA basically
            return cta

        # Construct the context (everything before CTA)
        context_sentences = sentences[:-1]
        if not context_sentences:
            return cta

        # Try to fit as many context sentences as possible from the start
        context_str = ""
        for i, sent in enumerate(context_sentences):
            # +1 for space
            if len(context_str) + len(sent) + 1 <= remaining_space:
                context_str += sent + " "
            else:
                # Can't fit this full sentence.
                # If it's the first sentence, truncate it.
                if i == 0:
                    available = remaining_space - len(context_str)
                    if available > 10:
                        context_str += sent[:available]
                break

        # Combine
        if context_str:
            final_msg = f"{context_str.strip()}... {cta}"
        else:
            final_msg = cta

        # Double check length (paranoid check)
        if len(final_msg) > self.tone_profile.max_length:
            return final_msg[: self.tone_profile.max_length]

        return final_msg

    def _generate_no_response_followup(self, question_number: int) -> str:
        """Generate follow-up for when seller doesn't respond."""

        followups = {
            1: "I need to know what's motivating you to sell and where you're moving.",
            2: "The timeline question is important. Would 30 to 45 days work or not?",
            3: "I need to know the condition of your home. Move in ready or needs work?",
            4: "What price would get you to sell? Give me a number.",
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
                4: "I need a dollar amount. What price would make you sell today?",
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
        if re.search(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]",
            message,
        ):
            violations.append("Contains emojis")

        # Check for hyphens
        if "-" in message:
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
            "directness_score": self._calculate_directness_score(message),
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
