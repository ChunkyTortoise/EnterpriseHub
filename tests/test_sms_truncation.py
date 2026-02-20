import pytest

pytestmark = pytest.mark.integration

"""
Tests for SMS truncation logic used in webhook handlers.

The truncation logic appears in ghl_real_estate_ai/api/routes/webhook.py
at multiple points (seller mode, buyer mode, lead bot mode). All use the
same algorithm:
  1. If message > 320 chars, truncate to 320
  2. Search backwards for sentence boundary (". ", "! ", "? ")
  3. Only accept a boundary if it's past the halfway point (160 chars)
  4. Strip trailing whitespace
"""

import pytest

SMS_MAX_CHARS = 320


def truncate_sms(message: str) -> str:
    """Replicates the inline SMS truncation logic from webhook.py."""
    if len(message) > SMS_MAX_CHARS:
        truncated = message[:SMS_MAX_CHARS]
        for sep in (". ", "! ", "? "):
            idx = truncated.rfind(sep)
            if idx > SMS_MAX_CHARS // 2:
                truncated = truncated[: idx + 1]
                break
        message = truncated.rstrip()
    return message


class TestSMSTruncation:
    """Test the 320-char SMS truncation logic."""

    def test_message_under_320_chars_unchanged(self):
        """Messages under 320 chars should pass through untouched."""
        short = "Hi! I'd love to help you find your dream home in Rancho Cucamonga."
        assert len(short) < SMS_MAX_CHARS
        assert truncate_sms(short) == short

    def test_message_exactly_320_chars_unchanged(self):
        """Messages exactly at the limit should pass through untouched."""
        exact = "A" * SMS_MAX_CHARS
        assert truncate_sms(exact) == exact

    def test_message_over_320_chars_truncated_at_sentence_boundary(self):
        """Long messages should be truncated at the last sentence boundary."""
        # Build a message with a period boundary in the second half
        prefix = "A" * 200 + ". "  # 202 chars, period at position 200
        suffix = "B" * 200  # pushes total well over 320
        msg = prefix + suffix
        assert len(msg) > SMS_MAX_CHARS

        result = truncate_sms(msg)
        # Should cut at the period boundary (position 201, inclusive of ".")
        assert result == "A" * 200 + "."
        assert len(result) <= SMS_MAX_CHARS

    def test_truncation_prefers_period_over_exclamation(self):
        """The algorithm checks '. ' before '! ', so period wins when both exist."""
        # Place "! " before ". " — both in second half
        # "! " at position 180, ". " at position 250
        msg = "X" * 180 + "! " + "Y" * 68 + ". " + "Z" * 200
        assert len(msg) > SMS_MAX_CHARS

        result = truncate_sms(msg)
        # ". " at 250 is found via rfind first (it's the LAST ". " in [:320])
        # and 250 > 160, so it should cut there
        assert result.endswith(".")
        # Verify it cut at the period, not the exclamation
        assert "Y" in result  # content after "!" should be present

    def test_truncation_wont_cut_below_half_length(self):
        """Sentence boundaries before the halfway point (160) are ignored."""
        # Place only boundary very early, at position 50
        msg = "A" * 50 + ". " + "B" * 400
        assert len(msg) > SMS_MAX_CHARS

        result = truncate_sms(msg)
        # The period is at position 50, which is < 160, so it's ignored.
        # Falls through all separators and uses hard truncation at 320.
        assert len(result) == SMS_MAX_CHARS

    def test_truncation_strips_trailing_whitespace(self):
        """Trailing whitespace after truncation should be stripped."""
        # Place a sentence boundary where the text after the period is spaces
        msg = "A" * 200 + ".   " + "B" * 300
        assert len(msg) > SMS_MAX_CHARS

        result = truncate_sms(msg)
        # Should cut at "." and strip trailing spaces
        assert not result.endswith(" ")
        assert result == "A" * 200 + "."

    def test_question_mark_boundary(self):
        """Truncation should also work with '? ' boundaries."""
        msg = "A" * 200 + "? " + "B" * 200
        assert len(msg) > SMS_MAX_CHARS

        result = truncate_sms(msg)
        # No ". " or "! " in the second half, so "? " at 200 should be used
        assert result == "A" * 200 + "?"

    def test_no_boundary_uses_hard_truncation(self):
        """Without any sentence boundary, message is hard-truncated at 320."""
        msg = "A" * 500  # no separators at all
        result = truncate_sms(msg)
        assert len(result) == SMS_MAX_CHARS
        assert result == "A" * SMS_MAX_CHARS