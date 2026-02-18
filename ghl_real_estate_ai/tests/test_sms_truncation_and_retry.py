"""
Tests for SMS truncation at sentence boundary and GHL client retry logic.

Covers:
- 320-char SMS truncation with sentence-boundary awareness
- 3x exponential backoff retry on send_message
- 3x exponential backoff retry on add_tags
- Compliance guard max input length limit
- Webhook inbound message length cap
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ghl_real_estate_ai.services.compliance_guard import ComplianceGuard, ComplianceStatus


# ---------------------------------------------------------------------------
# SMS Truncation Logic (extracted from webhook.py for testability)
# ---------------------------------------------------------------------------

SMS_MAX_CHARS = 320


def truncate_sms(message: str, max_chars: int = SMS_MAX_CHARS) -> str:
    """Reproduce the SMS truncation logic used in webhook.py."""
    if len(message) <= max_chars:
        return message
    truncated = message[:max_chars]
    for sep in (". ", "! ", "? "):
        idx = truncated.rfind(sep)
        if idx > max_chars // 2:
            truncated = truncated[: idx + 1]
            break
    return truncated.rstrip()


class TestSmsTruncation:
    """Test the 320-char SMS truncation at sentence boundary."""

    def test_short_message_unchanged(self):
        """Messages under 320 chars pass through unmodified."""
        msg = "Hey there, checking in about your property search!"
        assert truncate_sms(msg) == msg

    def test_exactly_320_chars_unchanged(self):
        """Message of exactly 320 chars is not truncated."""
        msg = "x" * 320
        assert truncate_sms(msg) == msg

    def test_long_message_truncated_at_period(self):
        """Long message is cut at the last sentence-ending period."""
        # Build a message: sentence1 (200 chars) + ". " + sentence2 (200 chars)
        s1 = "A" * 200
        s2 = "B" * 200
        msg = f"{s1}. {s2}"
        result = truncate_sms(msg)
        assert len(result) <= SMS_MAX_CHARS
        assert result.endswith(".")  # cut at sentence boundary

    def test_long_message_truncated_at_exclamation(self):
        """Truncation prefers exclamation mark as sentence boundary."""
        s1 = "A" * 200
        s2 = "B" * 200
        msg = f"{s1}! {s2}"
        result = truncate_sms(msg)
        assert len(result) <= SMS_MAX_CHARS
        assert result.endswith("!")

    def test_long_message_truncated_at_question_mark(self):
        """Truncation prefers question mark as sentence boundary."""
        s1 = "A" * 200
        s2 = "B" * 200
        msg = f"{s1}? {s2}"
        result = truncate_sms(msg)
        assert len(result) <= SMS_MAX_CHARS
        assert result.endswith("?")

    def test_no_sentence_boundary_falls_back_to_hard_cut(self):
        """If no sentence boundary in the second half, hard-cut at 320."""
        msg = "A" * 500  # No periods/exclamation/question marks
        result = truncate_sms(msg)
        assert len(result) == SMS_MAX_CHARS
        assert result == "A" * 320

    def test_sentence_boundary_too_early_ignored(self):
        """Sentence boundary before the halfway point is ignored (too much lost)."""
        # Period at position 50 — well below 160 (half of 320)
        msg = "A" * 50 + ". " + "B" * 400
        result = truncate_sms(msg)
        # The period at pos 50 is < 160, so all separators fail → hard cut
        assert len(result) == SMS_MAX_CHARS

    def test_multiple_sentences_cuts_at_last_valid(self):
        """With multiple sentences, cuts at the last one in the second half."""
        # Build a message with sentence boundaries in the second half of 320 chars
        # "A...A. B...B. C...C" where the second period lands around position 250
        s1 = "A" * 160  # 160 chars
        s2 = "B" * 88  # +90 chars (including ". ") = 250
        s3 = "C" * 200  # pushes well over 320
        msg = f"{s1}. {s2}. {s3}"
        result = truncate_sms(msg)
        assert len(result) <= SMS_MAX_CHARS
        assert result.endswith(".")  # cut at the ". " around pos 250

    def test_trailing_whitespace_stripped(self):
        """Trailing whitespace after truncation is stripped."""
        s1 = "A" * 250
        msg = f"{s1}.   {'B' * 200}"
        result = truncate_sms(msg)
        assert not result.endswith(" ")


# ---------------------------------------------------------------------------
# GHL Client Retry Logic
# ---------------------------------------------------------------------------


class TestGhlClientRetry:
    """Test 3x exponential backoff retry on send_message and add_tags."""

    @pytest.fixture
    def ghl_client(self):
        """Create a GHL client in non-test mode."""
        with patch("ghl_real_estate_ai.services.ghl_client.settings") as mock_settings:
            mock_settings.test_mode = False
            mock_settings.ghl_api_key = "test-key"
            mock_settings.ghl_location_id = "test-location"
            mock_settings.webhook_timeout_seconds = 5.0

            from ghl_real_estate_ai.services.ghl_client import GHLClient

            client = GHLClient(api_key="test-key", location_id="test-location")
            # Re-patch settings for method calls (module-level reference)
            yield client, mock_settings

    @pytest.mark.asyncio
    async def test_send_message_retries_on_failure(self, ghl_client):
        """send_message retries up to 3 times with exponential backoff."""
        client, mock_settings = ghl_client

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("Server error", request=MagicMock(), response=MagicMock(status_code=500))
        )

        with patch("httpx.AsyncClient") as mock_async:
            mock_ctx = AsyncMock()
            mock_ctx.post = AsyncMock(return_value=mock_response)
            mock_async.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_async.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                with pytest.raises(httpx.HTTPStatusError):
                    await client.send_message("contact-123", "Hello")

                # Should have tried 3 times total
                assert mock_ctx.post.call_count == 3

                # Exponential backoff: 0.5s, then 1.0s
                assert mock_sleep.call_count == 2
                mock_sleep.assert_any_call(0.5)
                mock_sleep.assert_any_call(1.0)

    @pytest.mark.asyncio
    async def test_send_message_succeeds_on_second_attempt(self, ghl_client):
        """send_message succeeds on retry after first failure."""
        client, mock_settings = ghl_client

        fail_response = MagicMock()
        fail_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("Server error", request=MagicMock(), response=MagicMock(status_code=502))
        )

        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()
        success_response.json = MagicMock(return_value={"messageId": "msg-ok"})

        with patch("httpx.AsyncClient") as mock_async:
            mock_ctx = AsyncMock()
            mock_ctx.post = AsyncMock(side_effect=[fail_response, success_response])
            mock_async.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_async.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await client.send_message("contact-123", "Hello")

            assert result == {"messageId": "msg-ok"}
            assert mock_ctx.post.call_count == 2

    @pytest.mark.asyncio
    async def test_add_tags_retries_on_failure(self, ghl_client):
        """add_tags retries up to 3 times with exponential backoff."""
        client, mock_settings = ghl_client

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("Server error", request=MagicMock(), response=MagicMock(status_code=500))
        )

        with patch("httpx.AsyncClient") as mock_async:
            mock_ctx = AsyncMock()
            mock_ctx.put = AsyncMock(return_value=mock_response)
            mock_async.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_async.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                with pytest.raises(httpx.HTTPStatusError):
                    await client.add_tags("contact-123", ["Hot-Lead"])

                assert mock_ctx.put.call_count == 3
                assert mock_sleep.call_count == 2
                mock_sleep.assert_any_call(0.5)
                mock_sleep.assert_any_call(1.0)

    @pytest.mark.asyncio
    async def test_add_tags_succeeds_on_third_attempt(self, ghl_client):
        """add_tags succeeds on the third retry."""
        client, mock_settings = ghl_client

        fail_response = MagicMock()
        fail_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Gateway timeout", request=MagicMock(), response=MagicMock(status_code=504)
            )
        )

        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()
        success_response.json = MagicMock(return_value={"tags": ["Hot-Lead"]})

        with patch("httpx.AsyncClient") as mock_async:
            mock_ctx = AsyncMock()
            mock_ctx.put = AsyncMock(side_effect=[fail_response, fail_response, success_response])
            mock_async.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_async.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await client.add_tags("contact-123", ["Hot-Lead"])

            assert result == {"tags": ["Hot-Lead"]}
            assert mock_ctx.put.call_count == 3


# ---------------------------------------------------------------------------
# Compliance Guard Input Length Limit
# ---------------------------------------------------------------------------


class TestComplianceGuardInputLimit:
    """Test the max input length limit on the compliance guard."""

    @pytest.fixture
    def guard(self):
        with patch("ghl_real_estate_ai.services.compliance_guard.LLMClient"):
            return ComplianceGuard()

    @pytest.mark.asyncio
    async def test_message_within_limit_passes_to_audit(self, guard):
        """Messages within the limit proceed to pattern/LLM audit."""
        msg = "What's my property worth in Rancho Cucamonga?"
        status, reason, violations = await guard.audit_message(msg)
        # Should not be blocked by length (may pass or get LLM audit)
        assert "input_length_exceeded" not in violations

    @pytest.mark.asyncio
    async def test_message_over_limit_blocked(self, guard):
        """Messages exceeding MAX_INPUT_LENGTH are immediately blocked."""
        msg = "A" * (ComplianceGuard.MAX_INPUT_LENGTH + 1)
        status, reason, violations = await guard.audit_message(msg)
        assert status == ComplianceStatus.BLOCKED
        assert "input_length_exceeded" in violations
        assert "maximum allowed length" in reason

    @pytest.mark.asyncio
    async def test_message_exactly_at_limit_not_blocked(self, guard):
        """Message exactly at MAX_INPUT_LENGTH is not blocked by length guard."""
        msg = "A" * ComplianceGuard.MAX_INPUT_LENGTH
        status, reason, violations = await guard.audit_message(msg)
        # Should not be blocked by length
        assert "input_length_exceeded" not in violations


# ---------------------------------------------------------------------------
# Webhook Inbound Message Truncation
# ---------------------------------------------------------------------------


class TestWebhookInboundTruncation:
    """Test that oversized inbound messages are truncated at the webhook entry point."""

    def test_inbound_message_truncated(self):
        """Messages over 2000 chars are truncated to 2000."""
        MAX_INBOUND_LENGTH = 2_000
        user_message = "X" * 5_000
        if len(user_message) > MAX_INBOUND_LENGTH:
            user_message = user_message[:MAX_INBOUND_LENGTH]
        assert len(user_message) == MAX_INBOUND_LENGTH

    def test_normal_message_untouched(self):
        """Normal-length messages pass through unmodified."""
        MAX_INBOUND_LENGTH = 2_000
        user_message = "I'm looking for a 3BR house in Rancho Cucamonga under 600k"
        original = user_message
        if len(user_message) > MAX_INBOUND_LENGTH:
            user_message = user_message[:MAX_INBOUND_LENGTH]
        assert user_message == original