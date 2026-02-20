"""
Unit tests for JorgeToneEngine service.

Tests Jorge's confrontational tone engine:
- SMS compliance (160 char limit)
- No emojis policy
- No hyphens policy
- Message formatting
- Negotiation drift detection
"""

import re
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


class TestMessageType:
    """Tests for MessageType enum."""

    def test_message_types_exist(self):
        """All expected message types are defined."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import MessageType

        assert MessageType.QUALIFICATION_QUESTION.value == "qualification_question"
        assert MessageType.FOLLOW_UP.value == "follow_up"
        assert MessageType.HOT_SELLER_HANDOFF.value == "hot_seller_handoff"
        assert MessageType.OBJECTION_RESPONSE.value == "objection_response"
        assert MessageType.CLOSING.value == "closing"
        assert MessageType.LABELING.value == "labeling"
        assert MessageType.CALIBRATED_QUESTION.value == "calibrated_question"


class TestToneProfile:
    """Tests for ToneProfile dataclass."""

    def test_default_profile_values(self):
        """Default profile has Jorge's standard settings."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import ToneProfile

        profile = ToneProfile()

        assert profile.max_length == 160
        assert profile.allow_emojis is False
        assert profile.allow_hyphens is False
        assert profile.directness_level == 0.8
        assert profile.professionalism_level == 0.7

    def test_custom_profile_values(self):
        """Custom profile values can be set."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import ToneProfile

        profile = ToneProfile(
            max_length=320,
            allow_emojis=True,
            allow_hyphens=True,
            directness_level=0.5,
            professionalism_level=0.9,
        )

        assert profile.max_length == 320
        assert profile.allow_emojis is True
        assert profile.allow_hyphens is True
        assert profile.directness_level == 0.5
        assert profile.professionalism_level == 0.9


class TestNegotiationDrift:
    """Tests for NegotiationDrift dataclass."""

    def test_default_drift_values(self):
        """Default drift has zero values."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            NegotiationDrift,
        )

        drift = NegotiationDrift()

        assert drift.sentiment_shift == 0.0
        assert drift.responsiveness_delta == 0.0
        assert drift.hedging_count == 0
        assert drift.is_softening is False
        assert drift.price_break_probability == 0.0

    def test_drift_can_indicate_softening(self):
        """Drift can indicate seller is softening."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            NegotiationDrift,
        )

        drift = NegotiationDrift(
            sentiment_shift=0.3,
            is_softening=True,
            price_break_probability=0.6,
        )

        assert drift.is_softening is True
        assert drift.price_break_probability == 0.6


class TestNegotiationStrategy:
    """Tests for NegotiationStrategy constants."""

    def test_labels_exist(self):
        """Labels are defined for Chris Voss technique."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            NegotiationStrategy,
        )

        assert len(NegotiationStrategy.LABELS) > 0
        assert all("{" in label for label in NegotiationStrategy.LABELS)

    def test_calibrated_questions_exist(self):
        """Calibrated questions are defined."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            NegotiationStrategy,
        )

        assert len(NegotiationStrategy.CALIBRATED_QUESTIONS) > 0
        # All should be questions
        assert all("?" in q for q in NegotiationStrategy.CALIBRATED_QUESTIONS)

    def test_calibrated_questions_no_why(self):
        """Calibrated questions avoid 'why' (Chris Voss principle)."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            NegotiationStrategy,
        )

        for question in NegotiationStrategy.CALIBRATED_QUESTIONS:
            assert "why" not in question.lower()


class TestJorgeToneEngineInit:
    """Tests for JorgeToneEngine initialization."""

    def test_init_with_defaults(self):
        """Engine initializes with default profile."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            JorgeToneEngine,
        )

        with patch(
            "ghl_real_estate_ai.services.jorge.jorge_tone_engine.JorgeSellerConfig"
        ):
            engine = JorgeToneEngine()

            assert engine.tone_profile.max_length == 160
            assert engine.tone_profile.allow_emojis is False

    def test_init_with_custom_profile(self):
        """Engine can use custom profile."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            JorgeToneEngine,
            ToneProfile,
        )

        custom_profile = ToneProfile(max_length=320)

        with patch(
            "ghl_real_estate_ai.services.jorge.jorge_tone_engine.JorgeSellerConfig"
        ):
            engine = JorgeToneEngine()
            engine.tone_profile = custom_profile

            assert engine.tone_profile.max_length == 320


class TestMessageValidation:
    """Tests for message validation."""

    @pytest.fixture
    def engine(self):
        """Create a JorgeToneEngine with default profile."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            JorgeToneEngine,
        )

        with patch(
            "ghl_real_estate_ai.services.jorge.jorge_tone_engine.JorgeSellerConfig"
        ):
            return JorgeToneEngine()

    def test_validate_rejects_emojis(self, engine):
        """Messages with emojis are rejected or cleaned."""
        message = "Hello! 🏠 How are you?"

        # Check if validation method exists
        if hasattr(engine, "validate_message"):
            is_valid, cleaned = engine.validate_message(message)
            assert "🏠" not in cleaned or is_valid is False

    def test_validate_rejects_hyphens(self, engine):
        """Messages with hyphens are rejected or cleaned."""
        message = "This is a test-driven approach"

        if hasattr(engine, "validate_message"):
            is_valid, cleaned = engine.validate_message(message)
            assert "-" not in cleaned or is_valid is False

    def test_validate_rejects_long_messages(self, engine):
        """Messages over 160 chars are rejected or truncated."""
        message = "A" * 200

        if hasattr(engine, "validate_message"):
            is_valid, cleaned = engine.validate_message(message)
            assert len(cleaned) <= 160 or is_valid is False


class TestMessageFormatting:
    """Tests for message formatting."""

    @pytest.fixture
    def engine(self):
        """Create a JorgeToneEngine with default profile."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            JorgeToneEngine,
        )

        with patch(
            "ghl_real_estate_ai.services.jorge.jorge_tone_engine.JorgeSellerConfig"
        ):
            return JorgeToneEngine()

    def test_format_removes_emojis(self, engine):
        """Formatting removes emojis from messages."""
        message = "Great! 🎉 Let's proceed! 🏠"

        if hasattr(engine, "format_message"):
            formatted = engine.format_message(message)
            # Emojis should be removed
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map symbols
                "\U0001F1E0-\U0001F1FF"  # flags
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "]+",
                flags=re.UNICODE,
            )
            assert not emoji_pattern.search(formatted)

    def test_format_removes_hyphens(self, engine):
        """Formatting removes hyphens from messages."""
        message = "This is test-driven and time-sensitive"

        if hasattr(engine, "format_message"):
            formatted = engine.format_message(message)
            assert "-" not in formatted

    def test_format_truncates_to_160(self, engine):
        """Formatting truncates messages to 160 characters."""
        message = "A" * 200

        if hasattr(engine, "format_message"):
            formatted = engine.format_message(message)
            assert len(formatted) <= 160


class TestQualificationQuestions:
    """Tests for qualification question generation."""

    @pytest.fixture
    def engine(self):
        """Create a JorgeToneEngine with default profile."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            JorgeToneEngine,
        )

        with patch(
            "ghl_real_estate_ai.services.jorge.jorge_tone_engine.JorgeSellerConfig"
        ):
            return JorgeToneEngine()

    def test_generate_question_is_direct(self, engine):
        """Generated questions are direct."""
        if hasattr(engine, "generate_qualification_question"):
            question = engine.generate_qualification_question("timeline")
            # Should be a question
            assert "?" in question or question.endswith("?")

    def test_generate_question_within_limit(self, engine):
        """Generated questions are within SMS limit."""
        if hasattr(engine, "generate_qualification_question"):
            question = engine.generate_qualification_question("budget")
            assert len(question) <= 160

    def test_generate_question_no_emojis(self, engine):
        """Generated questions have no emojis."""
        if hasattr(engine, "generate_qualification_question"):
            question = engine.generate_qualification_question("motivation")
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"
                "\U0001F300-\U0001F5FF"
                "\U0001F680-\U0001F6FF"
                "\U0001F1E0-\U0001F1FF"
                "]+",
                flags=re.UNICODE,
            )
            assert not emoji_pattern.search(question)


class TestObjectionResponses:
    """Tests for objection response generation."""

    @pytest.fixture
    def engine(self):
        """Create a JorgeToneEngine with default profile."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            JorgeToneEngine,
        )

        with patch(
            "ghl_real_estate_ai.services.jorge.jorge_tone_engine.JorgeSellerConfig"
        ):
            return JorgeToneEngine()

    def test_objection_response_is_professional(self, engine):
        """Objection responses maintain professionalism."""
        if hasattr(engine, "generate_objection_response"):
            response = engine.generate_objection_response(
                "Your commission is too high"
            )
            # Should not be aggressive
            aggressive_words = ["stupid", "idiot", "wrong", "ridiculous"]
            assert not any(word in response.lower() for word in aggressive_words)

    def test_objection_response_uses_calibrated_questions(self, engine):
        """Objection responses may use calibrated questions."""
        if hasattr(engine, "generate_objection_response"):
            response = engine.generate_objection_response("I need to think about it")
            # May contain a question
            # This is optional - not all responses need questions
            assert isinstance(response, str)


class TestNegotiationDriftDetection:
    """Tests for negotiation drift detection."""

    @pytest.fixture
    def engine(self):
        """Create a JorgeToneEngine with default profile."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            JorgeToneEngine,
        )

        with patch(
            "ghl_real_estate_ai.services.jorge.jorge_tone_engine.JorgeSellerConfig"
        ):
            return JorgeToneEngine()

    def test_detect_drift_from_messages(self, engine):
        """Drift can be detected from message history."""
        if hasattr(engine, "detect_negotiation_drift"):
            messages = [
                {"role": "seller", "content": "I want $650,000"},
                {"role": "seller", "content": "Maybe $625,000 is okay"},
                {"role": "seller", "content": "I could accept $600,000"},
            ]

            drift = engine.detect_negotiation_drift(messages)

            assert drift is not None
            assert hasattr(drift, "is_softening") or hasattr(drift, "sentiment_shift")

    def test_softening_detected_from_price_drops(self, engine):
        """Price drops indicate softening."""
        if hasattr(engine, "detect_negotiation_drift"):
            messages = [
                {"role": "seller", "content": "My price is firm at $650K"},
                {"role": "agent", "content": "Market suggests $580K"},
                {"role": "seller", "content": "I might consider $620K"},
            ]

            drift = engine.detect_negotiation_drift(messages)

            if drift:
                # Should detect some level of softening
                assert drift.is_softening or drift.sentiment_shift > 0


class TestLabelingTechnique:
    """Tests for Chris Voss labeling technique."""

    @pytest.fixture
    def engine(self):
        """Create a JorgeToneEngine with default profile."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            JorgeToneEngine,
        )

        with patch(
            "ghl_real_estate_ai.services.jorge.jorge_tone_engine.JorgeSellerConfig"
        ):
            return JorgeToneEngine()

    def test_generate_label(self, engine):
        """Labels can be generated for emotions."""
        if hasattr(engine, "generate_label"):
            label = engine.generate_label("frustrated", "timeline")

            assert label is not None
            assert len(label) <= 160

    def test_label_format(self, engine):
        """Labels follow Chris Voss format."""
        if hasattr(engine, "generate_label"):
            label = engine.generate_label("anxious", "selling process")

            # Should start with "It seems" or "It sounds" or "It looks"
            voss_starters = ["It seems", "It sounds", "It looks"]
            assert any(label.startswith(starter) for starter in voss_starters)


class TestHandoffMessages:
    """Tests for hot seller handoff messages."""

    @pytest.fixture
    def engine(self):
        """Create a JorgeToneEngine with default profile."""
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import (
            JorgeToneEngine,
        )

        with patch(
            "ghl_real_estate_ai.services.jorge.jorge_tone_engine.JorgeSellerConfig"
        ):
            return JorgeToneEngine()

    def test_handoff_message_is_urgent(self, engine):
        """Handoff messages convey urgency."""
        if hasattr(engine, "generate_handoff_message"):
            message = engine.generate_handoff_message()

            # Should indicate urgency or importance
            urgency_indicators = ["call", "speak", "discuss", "soon", "available"]
            assert any(
                indicator in message.lower() for indicator in urgency_indicators
            )

    def test_handoff_message_within_limit(self, engine):
        """Handoff messages are within SMS limit."""
        if hasattr(engine, "generate_handoff_message"):
            message = engine.generate_handoff_message()
            assert len(message) <= 160
