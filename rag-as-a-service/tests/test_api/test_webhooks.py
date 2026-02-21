"""Unit tests for RAG Stripe webhook endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from rag_service.api.webhooks import stripe_webhook


class TestStripeWebhook:
    @pytest.mark.asyncio
    async def test_returns_500_without_secret(self):
        mock_request = AsyncMock()
        with patch("os.environ.get", return_value=""):
            result = await stripe_webhook(mock_request)
            assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_returns_400_for_invalid_payload(self):
        mock_request = AsyncMock()
        mock_request.body.return_value = b"bad"
        mock_request.headers = {"stripe-signature": "sig"}

        with patch("os.environ.get", return_value="whsec_test"):
            with patch("stripe.Webhook.construct_event", side_effect=ValueError):
                result = await stripe_webhook(mock_request)
                assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_400_for_bad_signature(self):
        mock_request = AsyncMock()
        mock_request.body.return_value = b"data"
        mock_request.headers = {"stripe-signature": "bad_sig"}

        with patch("os.environ.get", return_value="whsec_test"):
            with patch("stripe.Webhook.construct_event", side_effect=stripe_sig_error()):
                result = await stripe_webhook(mock_request)
                assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_200_for_valid_event(self):
        mock_request = AsyncMock()
        mock_request.body.return_value = b'{"type": "invoice.payment_succeeded"}'
        mock_request.headers = {"stripe-signature": "valid"}

        fake_event = {
            "type": "invoice.payment_succeeded",
            "id": "evt_123",
            "data": {"object": {"customer": "cus_123"}},
        }

        with patch("os.environ.get", return_value="whsec_test"):
            with patch("stripe.Webhook.construct_event", return_value=fake_event):
                result = await stripe_webhook(mock_request)
                assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_handles_subscription_deleted(self):
        mock_request = AsyncMock()
        mock_request.body.return_value = b"{}"
        mock_request.headers = {"stripe-signature": "valid"}

        fake_event = {
            "type": "customer.subscription.deleted",
            "id": "evt_456",
            "data": {"object": {"customer": "cus_456"}},
        }

        with patch("os.environ.get", return_value="whsec_test"):
            with patch("stripe.Webhook.construct_event", return_value=fake_event):
                result = await stripe_webhook(mock_request)
                assert result.status_code == 200


def stripe_sig_error():
    """Helper to create a Stripe signature verification error."""
    import stripe

    return stripe.SignatureVerificationError("bad sig", "header")
