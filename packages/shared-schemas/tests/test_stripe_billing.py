"""Tests for Stripe billing service."""

from unittest.mock import MagicMock, patch

import pytest

from shared_infra.stripe_billing import StripeBillingError, StripeBillingService


@pytest.fixture
def service():
    return StripeBillingService(stripe_api_key="sk_test_fake")


class TestCreateCustomer:
    @pytest.mark.asyncio
    async def test_success(self, service):
        mock_customer = MagicMock()
        mock_customer.id = "cus_123"
        with patch("stripe.Customer.create", return_value=mock_customer):
            result = await service.create_customer("t-1", "test@example.com", "Test User")
        assert result == "cus_123"

    @pytest.mark.asyncio
    async def test_stripe_error_raises(self, service):
        import stripe

        with patch("stripe.Customer.create", side_effect=stripe.StripeError("fail")):
            with pytest.raises(StripeBillingError, match="Failed to create customer"):
                await service.create_customer("t-1", "x@x.com", "X")


class TestCreateSubscription:
    @pytest.mark.asyncio
    async def test_success(self, service):
        mock_sub = MagicMock()
        mock_sub.id = "sub_abc"
        mock_sub.status = "active"
        mock_sub.current_period_end = 1700000000
        with patch("stripe.Subscription.create", return_value=mock_sub):
            result = await service.create_subscription("cus_123", "price_abc")
        assert result["subscription_id"] == "sub_abc"
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_stripe_error_raises(self, service):
        import stripe

        with patch("stripe.Subscription.create", side_effect=stripe.StripeError("fail")):
            with pytest.raises(StripeBillingError, match="Failed to create subscription"):
                await service.create_subscription("cus_123", "price_abc")


class TestRecordUsage:
    @pytest.mark.asyncio
    async def test_success(self, service):
        mock_event = MagicMock()
        mock_event.identifier = "mevt_123"
        with patch("stripe.billing.MeterEvent.create", return_value=mock_event):
            result = await service.record_usage("api_calls", "t-1", 100)
        assert result == "mevt_123"

    @pytest.mark.asyncio
    async def test_with_idempotency_key(self, service):
        mock_event = MagicMock()
        mock_event.identifier = "mevt_456"
        with patch("stripe.billing.MeterEvent.create", return_value=mock_event) as mock_create:
            await service.record_usage("api_calls", "t-1", 50, idempotency_key="key-1")
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["payload"]["idempotency_key"] == "key-1"

    @pytest.mark.asyncio
    async def test_stripe_error_raises(self, service):
        import stripe

        with patch("stripe.billing.MeterEvent.create", side_effect=stripe.StripeError("fail")):
            with pytest.raises(StripeBillingError, match="Failed to record usage"):
                await service.record_usage("api_calls", "t-1", 100)


class TestHandleWebhook:
    @pytest.mark.asyncio
    async def test_subscription_updated(self, service):
        mock_event = {
            "id": "evt_123",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "metadata": {"tenant_id": "t-1"},
                }
            },
        }
        with patch("stripe.Webhook.construct_event", return_value=mock_event):
            result = await service.handle_webhook(b"payload", "sig", "whsec_123")
        assert result is not None
        assert result.event_type == "subscription.changed"
        assert result.tenant_id == "t-1"

    @pytest.mark.asyncio
    async def test_payment_failed(self, service):
        mock_event = {
            "id": "evt_456",
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "metadata": {"tenant_id": "t-2"},
                }
            },
        }
        with patch("stripe.Webhook.construct_event", return_value=mock_event):
            result = await service.handle_webhook(b"payload", "sig", "whsec_123")
        assert result is not None
        assert result.event_type == "billing.payment_failed"

    @pytest.mark.asyncio
    async def test_unhandled_event_returns_none(self, service):
        mock_event = {
            "id": "evt_789",
            "type": "charge.succeeded",
            "data": {"object": {"metadata": {}}},
        }
        with patch("stripe.Webhook.construct_event", return_value=mock_event):
            result = await service.handle_webhook(b"payload", "sig", "whsec_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_signature_raises(self, service):
        import stripe

        with patch(
            "stripe.Webhook.construct_event",
            side_effect=stripe.SignatureVerificationError("bad", "sig"),
        ):
            with pytest.raises(StripeBillingError, match="Invalid webhook signature"):
                await service.handle_webhook(b"payload", "bad_sig", "whsec_123")
