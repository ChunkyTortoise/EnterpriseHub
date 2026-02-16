"""Tests for Stripe billing service (mocked)."""

import pytest
from unittest.mock import patch, MagicMock

from shared_schemas.billing import UsageEvent, UsageEventType
from shared_infra.stripe_billing import StripeBillingService


@pytest.fixture
def billing_service():
    return StripeBillingService(api_key="sk_test_123", webhook_secret="whsec_test123")


class TestCreateCustomer:
    @patch("shared_infra.stripe_billing.stripe")
    async def test_create_customer(self, mock_stripe, billing_service):
        mock_stripe.Customer.create.return_value = {
            "id": "cus_test",
            "email": "test@example.com",
        }
        result = await billing_service.create_customer("test@example.com", "Test Corp")
        mock_stripe.Customer.create.assert_called_once_with(
            email="test@example.com", name="Test Corp", metadata={}
        )
        assert result["id"] == "cus_test"

    @patch("shared_infra.stripe_billing.stripe")
    async def test_create_customer_with_metadata(self, mock_stripe, billing_service):
        mock_stripe.Customer.create.return_value = {"id": "cus_test"}
        await billing_service.create_customer(
            "test@example.com", "Test", metadata={"tier": "pro"}
        )
        mock_stripe.Customer.create.assert_called_once_with(
            email="test@example.com", name="Test", metadata={"tier": "pro"}
        )


class TestCreateSubscription:
    @patch("shared_infra.stripe_billing.stripe")
    async def test_create_subscription(self, mock_stripe, billing_service):
        mock_stripe.Subscription.create.return_value = {
            "id": "sub_test",
            "status": "active",
        }
        result = await billing_service.create_subscription("cus_test", "price_abc")
        assert result["status"] == "active"


class TestReportUsage:
    @patch("shared_infra.stripe_billing.stripe")
    async def test_report_usage(self, mock_stripe, billing_service):
        mock_stripe.billing.MeterEvent.create.return_value = {"identifier": "evt_test"}
        event = UsageEvent(
            tenant_id="cus_test", event_type=UsageEventType.RAG_QUERY, quantity=5.0
        )
        result = await billing_service.report_usage(event)
        assert result["identifier"] == "evt_test"
        mock_stripe.billing.MeterEvent.create.assert_called_once()


class TestCheckoutSession:
    @patch("shared_infra.stripe_billing.stripe")
    async def test_create_checkout_session(self, mock_stripe, billing_service):
        mock_stripe.checkout.Session.create.return_value = MagicMock(
            url="https://checkout.stripe.com/session"
        )
        url = await billing_service.create_checkout_session(
            "cus_test", "price_abc", "https://app.com/success", "https://app.com/cancel"
        )
        assert url == "https://checkout.stripe.com/session"


class TestWebhook:
    @patch("shared_infra.stripe_billing.stripe")
    def test_handle_webhook(self, mock_stripe, billing_service):
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "invoice.paid",
            "id": "evt_123",
            "data": {},
        }
        result = billing_service.handle_webhook(b"payload", "sig_header")
        assert result["type"] == "invoice.paid"

    @patch("shared_infra.stripe_billing.stripe")
    def test_webhook_invalid_signature(self, mock_stripe, billing_service):
        mock_stripe.error.SignatureVerificationError = type(
            "SignatureVerificationError", (Exception,), {}
        )
        mock_stripe.Webhook.construct_event.side_effect = (
            mock_stripe.error.SignatureVerificationError("bad sig")
        )
        with pytest.raises(ValueError, match="Invalid webhook signature"):
            billing_service.handle_webhook(b"payload", "bad_sig")

    def test_webhook_no_secret(self):
        svc = StripeBillingService(api_key="sk_test")
        with pytest.raises(ValueError, match="Webhook secret not configured"):
            svc.handle_webhook(b"payload", "sig")
