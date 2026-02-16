#!/usr/bin/env python3
"""
Jorge's Consultative Tone Engine

This module implements Jorge's seller messaging requirements:
- No emojis (professional only)
- No hyphens (SMS compatibility)
- <160 characters (SMS limit compliance)
- Consultative, friendly, and professional tone
- Clear question delivery

Author: Claude Code Assistant
Created: 2026-01-19
"""

import re
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
    directness_level: float = 0.6  # Clear but supportive (0.0-1.0)
    professionalism_level: float = 0.9  # High professionalism


class JorgeToneEngine:
    """
    Generates messages matching Jorge's consultative and friendly tone.

    Key Requirements:
    1. Clear and concise
    2. Friendly and respectful
    3. Professional urgency without pressure
    4. Helpful guidance and next step clarity
    5. SMS-compliant formatting
    """

    def __init__(self):
        self.tone_profile = ToneProfile()
        self.config = JorgeSellerConfig()

    def generate_qualification_message(
        self, question_number: int, seller_name: Optional[str] = None, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Jorge's consultative qualification question.

        Args:
            question_number: Which qualification question (1-12)
            seller_name: Optional seller name for personalization
            context: Additional context for message customization

        Returns:
            SMS-compliant message with consultative tone
        """
        # Get base question from config
        base_question = self.config.SELLER_QUESTIONS.get(question_number, "")

        if not base_question:
            raise ValueError(f"Invalid question number: {question_number}")

        # Apply consultative tone modifications
        message = self._apply_consultative_tone(base_question, seller_name)

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
            Consultative follow-up message
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

    def generate_hot_seller_handoff(self, seller_name: Optional[str] = None, agent_name: str = "our team") -> str:
        """
        Generate message for hot seller handoff to agent.

        Args:
            seller_name: Seller name
            agent_name: Agent or team name for handoff

        Returns:
            Direct handoff message
        """
        base_message = (
            f"Thanks for sharing that. {agent_name} can help you map out next steps today. "
            "What time works best for a quick call?"
        )

        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"

        return self._ensure_sms_compliance(base_message)

    def generate_take_away_close(
        self, seller_name: Optional[str] = None, reason: Optional[str] = None, psychology_profile: Any = None
    ) -> str:
        """
        Generate a gentle pause-or-continue message for low-confidence or vague leads.

        Args:
            seller_name: Seller name
            reason: Specific reason for the take-away close (e.g., 'vague', 'low_probability')
            psychology_profile: Optional psychological profile for tone tuning

        Returns:
            Consultative pause message
        """
        if psychology_profile and getattr(psychology_profile, "emotional_attachment_score", 0) > 70:
            base_message = (
                "Totally understandable. Selling can be emotional. We can pause for now and check back later, "
                "or keep going if you want clearer numbers."
            )
        elif reason == "low_probability":
            base_message = (
                "No pressure at all. If now is not the right time, I can pause this and check back later. "
                "Would that be better?"
            )
        else:
            base_message = (
                "If the timing is not right yet, that is completely okay. Would you like to pause for now or keep going?"
            )

        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"

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
        Generate a consultative net-yield guidance message when seller is firm on price but repairs are needed.

        Args:
            price_expectation: Seller's expected price
            ai_valuation: AI's valuation (ARV or current market)
            net_yield: Calculated net yield percentage (0.0-1.0)
            repair_estimate: Estimated repair costs
            seller_name: Seller name for personalization
            psychology_profile: Optional psychological profile

        Returns:
            SMS-compliant ROI guidance message
        """
        if psychology_profile and getattr(psychology_profile, "motivation_type", "") == "distressed":
            base_message = (
                f"I want to be transparent: with current condition and costs, "
                f"${price_expectation:,.0f} is above where buyers are likely to land. "
                f"Our estimate is around ${ai_valuation:,.0f}. What feels workable for you?"
            )
        elif repair_estimate > 0:
            base_message = (
                f"Thanks for sharing your number. Based on repairs and comps, ${ai_valuation:,.0f} is closer to market. "
                "What flexibility do you have so we can make this workable?"
            )
        else:
            base_message = (
                f"At ${price_expectation:,.0f}, net yield is about {net_yield:.1%}. "
                f"Our valuation is closer to ${ai_valuation:,.0f}. "
                "Where would you like to be to move forward confidently?"
            )

        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"

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
            "timeline_too_fast": "That makes sense. What timeline would feel realistic for you?",
            "price_too_low": "Understood. What price range would feel right for you right now?",
            "need_repairs": "Got it. Is it mostly cosmetic work or larger repairs?",
            "not_ready": "No problem. What would need to change before you feel ready?",
            "just_looking": "Totally fair. What information would help you evaluate your options?",
            "market_timing": "Good question. What market signal are you waiting for specifically?",
        }

        message = objection_responses.get(objection_type, "I understand. Help me understand what's holding you back.")

        if seller_name:
            message = f"{seller_name}, {message.lower()}"

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
            Consultative urgency message
        """
        if "rate" in market_trend.lower():
            base_message = (
                "Rates are moving and that can affect what buyers can pay. "
                "If helpful, I can show the tradeoffs of selling now versus waiting."
            )
        else:
            base_message = (
                "Inventory is shifting, which can impact timing and net proceeds. "
                "Would you like a quick breakdown of now versus waiting?"
            )

        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"

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
            Technical, data-driven consultative message
        """
        if yield_spread > 0:
            base_message = (
                f"Market data shows about a {yield_spread:.1f}% yield spread in {market_area}. "
                "If useful, I can walk through what that means for your options."
            )
        else:
            base_message = (
                "We are tracking sub markets where yield spreads are outperforming city averages. "
                "What outcome are you aiming for so I can tailor the strategy?"
            )

        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"

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
            label = f"{seller_name}, {label.lower()}"

        return self._ensure_sms_compliance(label)

    def generate_calibrated_question(self, index: int = 2, seller_name: Optional[str] = None) -> str:
        """Apply Voss-style 'Calibrated Question'."""
        question = NegotiationStrategy.CALIBRATED_QUESTIONS[index % len(NegotiationStrategy.CALIBRATED_QUESTIONS)]

        if seller_name:
            question = f"{seller_name}, {question.lower()}"

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
        """Backward-compatible wrapper; now applies consultative tone."""
        return self._apply_consultative_tone(base_message, seller_name)

    def _apply_consultative_tone(self, base_message: str, seller_name: Optional[str] = None) -> str:
        """Apply consultative and friendly tone while keeping clarity."""
        message = self._normalize_language(base_message)
        message = self._increase_clarity(message)

        if seller_name:
            message = f"{seller_name}, {message.lower()}"

        return message

    def _normalize_language(self, message: str) -> str:
        """Normalize language while preserving warmth."""
        message = re.sub(r"\s+", " ", message).strip()
        return message

    def _increase_clarity(self, message: str) -> str:
        """Improve clarity without aggressive wording."""
        replacements = {
            r"\bI was wondering if\b": "",
            r"\bI would like to know\b": "Could you share",
        }

        for pattern, replacement in replacements.items():
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

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
            1: "When you have a second, could you share what is motivating the move and where you might go next?",
            2: "When convenient, would a 30 to 45 day timeline work for you, or would you prefer longer?",
            3: "Could you describe condition at a high level: move in ready, needs work, or major repairs?",
            4: "What price range would make a sale feel right for you?",
        }

        return followups.get(question_number, "Whenever you are ready, share what feels right so I can guide next steps.")

    def _generate_inadequate_response_followup(self, question_number: int, response: str) -> str:
        """Generate follow-up for inadequate responses."""

        # Detect vague responses
        vague_indicators = ["maybe", "not sure", "don't know", "idk", "thinking", "considering"]

        if any(indicator in response.lower() for indicator in vague_indicators):
            push_for_specifics = {
                1: "Can you share a bit more specific detail on what is driving the sale and where you may move next?",
                2: "Could you share a specific timeline that works best for you, such as 30 to 45 days or longer?",
                3: "Can you be more specific on condition so we can guide pricing accurately?",
                4: "Could you share a specific target number or range that would make sense for you?",
            }
            return push_for_specifics.get(
                question_number, "Could you share a bit more detail so I can give you accurate guidance?"
            )

        # Default pushback for unclear responses
        return f"I may have missed your point. {self._generate_no_response_followup(question_number)}"

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

        # Check for aggressive language
        aggressive_phrases = [
            "pipe dream",
            "not serious",
            "close your file",
            "do you want in or not",
            "lose more",
            "last chance",
            "stop wasting time",
            "take it or leave it",
            "now or never",
        ]
        found_aggressive = [phrase for phrase in aggressive_phrases if phrase in message.lower()]
        if found_aggressive:
            violations.append(f"Contains aggressive language: {', '.join(found_aggressive)}")

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "character_count": len(message),
            "directness_score": self._calculate_directness_score(message),
        }

    def _calculate_directness_score(self, message: str) -> float:
        """Calculate directness score (0.0-1.0) for message."""

        # Higher score = clear and action-oriented
        score = 0.5  # Base score

        # Add points for direct constructions
        direct_indicators = ["what", "when", "where", "how much", "could you", "share", "help me understand"]
        for indicator in direct_indicators:
            if indicator.lower() in message.lower():
                score += 0.1

        # Subtract points for ambiguity
        indirect_indicators = ["perhaps", "maybe", "not sure", "whatever", "anything works"]
        for indicator in indirect_indicators:
            if indicator.lower() in message.lower():
                score -= 0.15

        # Ensure score is in valid range
        return max(0.0, min(1.0, score))
