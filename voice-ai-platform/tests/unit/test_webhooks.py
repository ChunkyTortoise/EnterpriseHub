"""Unit tests for webhook endpoints — Twilio status and Stripe."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from voice_ai.api.webhooks import TWILIO_STATUS_MAP, stripe_webhook, twilio_status_callback


class TestTwilioStatusMap:
    """Test Twilio status mapping."""

    def test_initiated_maps(self):
        assert TWILIO_STATUS_MAP["initiated"] == "initiated"

    def test_ringing_maps(self):
        assert TWILIO_STATUS_MAP["ringing"] == "ringing"

    def test_in_progress_maps(self):
        assert TWILIO_STATUS_MAP["in-progress"] == "in_progress"

    def test_completed_maps(self):
        assert TWILIO_STATUS_MAP["completed"] == "completed"

    def test_failed_maps(self):
        assert TWILIO_STATUS_MAP["failed"] == "failed"

    def test_busy_maps_to_failed(self):
        assert TWILIO_STATUS_MAP["busy"] == "failed"

    def test_no_answer_maps(self):
        assert TWILIO_STATUS_MAP["no-answer"] == "no_answer"

    def test_canceled_maps_to_failed(self):
        assert TWILIO_STATUS_MAP["canceled"] == "failed"

    def test_unknown_status_returns_none(self):
        assert TWILIO_STATUS_MAP.get("unknown") is None


class TestTwilioStatusCallback:
    """Test Twilio status callback endpoint."""

    @pytest.mark.asyncio
    async def test_returns_ok_for_valid_status(self):
        mock_request = AsyncMock()
        mock_form = {"CallSid": "CA123", "CallStatus": "completed", "CallDuration": "120"}
        mock_request.form.return_value = mock_form

        result = await twilio_status_callback(mock_request)
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_handles_missing_fields(self):
        mock_request = AsyncMock()
        mock_request.form.return_value = {}

        result = await twilio_status_callback(mock_request)
        assert result == {"status": "ok"}


class TestStripeWebhook:
    """Test Stripe webhook endpoint."""

    @pytest.mark.asyncio
    async def test_returns_500_without_webhook_secret(self):
        mock_request = AsyncMock()
        with patch.dict("os.environ", {}, clear=False):
            with patch("os.environ.get", return_value=""):
                result = await stripe_webhook(mock_request)
                assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_returns_400_for_invalid_payload(self):
        mock_request = AsyncMock()
        mock_request.body.return_value = b"invalid"
        mock_request.headers = {"stripe-signature": "sig_test"}

        with patch("os.environ.get", return_value="whsec_test"):
            with patch("stripe.Webhook.construct_event", side_effect=ValueError("bad")):
                result = await stripe_webhook(mock_request)
                assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_200_for_valid_event(self):
        mock_request = AsyncMock()
        mock_request.body.return_value = b'{"type": "invoice.payment_succeeded"}'
        mock_request.headers = {"stripe-signature": "sig_test"}

        fake_event = {
            "type": "invoice.payment_succeeded",
            "id": "evt_123",
            "data": {"object": {"customer": "cus_123"}},
        }

        with patch("os.environ.get", return_value="whsec_test"):
            with patch("stripe.Webhook.construct_event", return_value=fake_event):
                result = await stripe_webhook(mock_request)
                assert result.status_code == 200
