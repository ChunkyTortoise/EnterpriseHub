"""
Tests for ResponseGenerator tone variant functionality.

Validates that tone_variant parameter affects message generation across all methods:
- construct_intelligent_day3_message
- construct_adaptive_day14_message
- construct_intelligent_day30_message
"""

import pytest

from ghl_real_estate_ai.agents.lead.response_generator import ResponseGenerator


class TestToneVariants:
    """Test suite for tone variant application."""

    def test_tone_formal(self):
        """Test formal tone transformations."""
        base_msg = "Hey John, hope you're doing well! Any questions about the market?"
        formal_msg = ResponseGenerator._apply_tone_variant(base_msg, "formal")

        assert "Hello John" in formal_msg
        assert "Hey John" not in formal_msg
        assert "I trust this finds you well" in formal_msg
        assert "Should you have any questions" in formal_msg

    def test_tone_casual(self):
        """Test casual tone transformations."""
        base_msg = "Hi John, I trust this finds you well. Should you have any questions, I would be happy to help."
        casual_msg = ResponseGenerator._apply_tone_variant(base_msg, "casual")

        assert "Hey John" in casual_msg
        assert "Hi John" not in casual_msg
        assert "Hope you're doing great" in casual_msg
        assert "Got any questions" in casual_msg
        assert "happy to help" in casual_msg

    def test_tone_empathetic_nochange(self):
        """Test empathetic tone is pass-through (no transformations)."""
        base_msg = "Hi John, checking in about your property search."
        empathetic_msg = ResponseGenerator._apply_tone_variant(base_msg, "empathetic")

        assert empathetic_msg == base_msg

    def test_day3_message_with_formal_tone(self):
        """Test Day 3 message with formal tone."""
        msg = ResponseGenerator.construct_intelligent_day3_message(
            lead_name="John",
            intelligence_context=None,
            personalized_insights=None,
            critical_scenario=None,
            tone_variant="formal",
        )

        assert "Hello John" in msg
        assert "Should you have any questions" in msg

    def test_day3_message_with_casual_tone(self):
        """Test Day 3 message with casual tone."""
        msg = ResponseGenerator.construct_intelligent_day3_message(
            lead_name="John",
            intelligence_context=None,
            personalized_insights=None,
            critical_scenario=None,
            tone_variant="casual",
        )

        # Verify casual tone transformations
        assert "Hey John" in msg
        # "Any questions" is already casual - no need for "Got any questions" transformation
        assert "Any questions" in msg or "Got any questions" in msg

    def test_day3_message_with_empathetic_tone(self):
        """Test Day 3 message with empathetic tone (default)."""
        msg = ResponseGenerator.construct_intelligent_day3_message(
            lead_name="John",
            intelligence_context=None,
            personalized_insights=None,
            critical_scenario=None,
            tone_variant="empathetic",
        )

        # Empathetic uses original "Hi" greeting
        assert "Hi John" in msg
        assert "Any questions" in msg

    def test_day14_message_with_tones(self):
        """Test Day 14 message applies tone variants."""
        for tone in ["formal", "casual", "empathetic"]:
            msg = ResponseGenerator.construct_adaptive_day14_message(
                lead_name="John",
                intelligence_context=None,
                preferred_channel="Email",
                content_adaptation_applied=False,
                tone_variant=tone,
            )

            # Verify message was generated
            assert len(msg) > 0
            assert "John" in msg

            # Verify tone-specific transformations
            if tone == "formal":
                assert "Hello" in msg or "Please let me know" in msg
            elif tone == "casual":
                assert "Hey" in msg

    def test_day30_message_with_tones(self):
        """Test Day 30 message applies tone variants."""
        for tone in ["formal", "casual", "empathetic"]:
            msg = ResponseGenerator.construct_intelligent_day30_message(
                lead_name="John",
                final_strategy="nurture",
                intelligence_score=0.5,
                handoff_reasoning=[],
                tone_variant=tone,
            )

            # Verify message was generated
            assert len(msg) > 0
            assert "John" in msg

            # Verify tone-specific transformations
            if tone == "formal":
                assert "Hello" in msg or "I would be happy" in msg
            elif tone == "casual":
                assert "Hey" in msg

    def test_default_tone_is_empathetic(self):
        """Test that default tone is empathetic when not specified."""
        msg = ResponseGenerator.construct_intelligent_day3_message(
            lead_name="John",
            intelligence_context=None,
            personalized_insights=None,
            critical_scenario=None,
        )

        # Default should match empathetic (no tone transformations)
        msg_explicit = ResponseGenerator.construct_intelligent_day3_message(
            lead_name="John",
            intelligence_context=None,
            personalized_insights=None,
            critical_scenario=None,
            tone_variant="empathetic",
        )

        assert msg == msg_explicit
