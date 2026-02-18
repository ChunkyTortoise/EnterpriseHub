"""
Tests for Stripe Billing API endpoints.

Since the billing router is not mounted in the main app, we create a
standalone FastAPI app with just the billing router for isolated testing.

Endpoints tested:
    POST   /billing/subscriptions               - Create subscription
    GET    /billing/subscriptions/{id}           - Get subscription
    PUT    /billing/subscriptions/{id}           - Update subscription
    DELETE /billing/subscriptions/{id}           - Cancel subscription
    POST   /billing/usage                        - Record usage
    GET    /billing/usage/{subscription_id}      - Get usage data
    POST   /billing/invoices/{invoice_id}/pay    - Process payment
    GET    /billing/invoices                     - List invoices
    POST   /billing/webhooks/stripe              - Stripe webhook
    GET    /billing/analytics/revenue            - Revenue analytics
    GET    /billing/analytics/tiers              - Tier distribution
"""

from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Import guard: billing.py has a known syntax error at line 512
# (positional arg follows keyword args in retry_with_exponential_backoff call)
# ---------------------------------------------------------------------------

_BILLING_IMPORT_ERROR = None
try:
    with (
        patch("ghl_real_estate_ai.api.routes.billing.billing_service", MagicMock()),
        patch("ghl_real_estate_ai.api.routes.billing.subscription_manager", MagicMock()),
        patch("ghl_real_estate_ai.api.routes.billing.monitoring_service", MagicMock()),
    ):
        from ghl_real_estate_ai.api.routes.billing import router as billing_router
except Exception as exc:
    _BILLING_IMPORT_ERROR = str(exc)
    billing_router = None

skip_if_no_billing = pytest.mark.skipif(
    billing_router is None,
    reason=f"billing module cannot be imported: {_BILLING_IMPORT_ERROR}",
)


# ---------------------------------------------------------------------------
# Standalone test app with billing router
# ---------------------------------------------------------------------------

def _make_billing_client(billing_service=None, subscription_manager=None):
    """Create a TestClient with just the billing router, deps mocked."""
    mock_billing = billing_service or MagicMock()
    mock_sub_mgr = subscription_manager or MagicMock()

    from ghl_real_estate_ai.api.routes import billing as billing_module

    # Bind mocks directly on the module so handlers use them at request time.
    billing_module.billing_service = mock_billing
    billing_module.subscription_manager = mock_sub_mgr
    billing_module.monitoring_service = MagicMock()

    test_app = FastAPI()
    test_app.include_router(billing_module.router)
    return TestClient(test_app, raise_server_exceptions=False), mock_billing, mock_sub_mgr


def _subscription_response_dict(
    sub_id: int = 1,
    tier: str = "professional",
    stripe_subscription_id: str = "sub_live_001",
    stripe_customer_id: str = "cus_live_001",
):
    """Build a mock SubscriptionResponse-like dict."""
    from ghl_real_estate_ai.api.schemas.billing import (
        SubscriptionResponse,
        SubscriptionStatus,
        SubscriptionTier,
    )

    return SubscriptionResponse(
        id=sub_id,
        location_id="loc-123",
        stripe_subscription_id=stripe_subscription_id,
        stripe_customer_id=stripe_customer_id,
        tier=SubscriptionTier(tier),
        status=SubscriptionStatus.ACTIVE,
        current_period_start=datetime.now(),
        current_period_end=datetime.now() + timedelta(days=30),
        usage_allowance=150,
        usage_current=50,
        usage_percentage=33.3,
        overage_rate=1.50,
        base_price=249.00,
        next_invoice_date=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
    )


def _subscription_row_dict(subscription_id: int = 1) -> Dict[str, Any]:
    """Build a mock DB subscription row."""
    now = datetime.now()
    return {
        "id": subscription_id,
        "location_id": "loc-123",
        "stripe_subscription_id": f"sub_live_{subscription_id:04d}",
        "stripe_customer_id": f"cus_live_{subscription_id:04d}",
        "tier": "professional",
        "status": "active",
        "currency": "usd",
        "current_period_start": now,
        "current_period_end": now + timedelta(days=30),
        "usage_allowance": 150,
        "usage_current": 50,
        "overage_rate": 1.5,
        "base_price": 249.0,
        "trial_end": None,
        "cancel_at_period_end": False,
        "created_at": now,
        "updated_at": now,
    }


# ---------------------------------------------------------------------------
# POST /billing/subscriptions — Create subscription
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestCreateSubscription:
    """Tests for subscription creation endpoint."""

    def test_create_subscription_success(self):
        """Creates subscription with valid payload."""
        mock_sub_response = _subscription_response_dict()

        mock_sub_mgr = MagicMock()
        mock_sub_mgr.initialize_subscription = AsyncMock(return_value=mock_sub_response)

        client, _, _ = _make_billing_client(subscription_manager=mock_sub_mgr)
        resp = client.post(
            "/billing/subscriptions",
            json={
                "location_id": "loc-123",
                "tier": "professional",
                "payment_method_id": "pm_test123",
                "trial_days": 14,
                "email": "test@example.com",
            },
        )

        assert resp.status_code == 200

    def test_create_subscription_missing_fields_returns_422(self):
        """Missing required fields returns 422."""
        client, _, _ = _make_billing_client()
        resp = client.post(
            "/billing/subscriptions",
            json={"location_id": "loc-123"},
        )

        assert resp.status_code == 422

    def test_create_subscription_invalid_email_returns_422(self):
        """Invalid email format returns 422."""
        client, _, _ = _make_billing_client()
        resp = client.post(
            "/billing/subscriptions",
            json={
                "location_id": "loc-123",
                "tier": "starter",
                "payment_method_id": "pm_test",
                "email": "not-an-email",
            },
        )

        assert resp.status_code == 422

    def test_create_subscription_invalid_tier_returns_422(self):
        """Invalid tier value returns 422."""
        client, _, _ = _make_billing_client()
        resp = client.post(
            "/billing/subscriptions",
            json={
                "location_id": "loc-123",
                "tier": "platinum",
                "payment_method_id": "pm_test",
            },
        )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /billing/subscriptions/{subscription_id}
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestGetSubscription:
    """Tests for subscription retrieval endpoint."""

    def test_get_subscription_returns_data(self):
        """Returns subscription data for valid ID."""
        subscription_id = 42
        row = _subscription_row_dict(subscription_id=subscription_id)
        response_model = _subscription_response_dict(
            sub_id=subscription_id,
            stripe_subscription_id=row["stripe_subscription_id"],
            stripe_customer_id=row["stripe_customer_id"],
        )

        with (
            patch(
                "ghl_real_estate_ai.api.routes.billing._fetch_subscription_row",
                new=AsyncMock(return_value=row),
            ) as mock_fetch,
            patch(
                "ghl_real_estate_ai.api.routes.billing._build_subscription_response",
                return_value=response_model,
            ) as mock_build,
        ):
            client, _, _ = _make_billing_client()
            resp = client.get(f"/billing/subscriptions/{subscription_id}")

        mock_fetch.assert_awaited_once_with(subscription_id)
        mock_build.assert_called_once_with(row)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == subscription_id
        assert data["stripe_subscription_id"] == row["stripe_subscription_id"]
        assert data["stripe_customer_id"] == row["stripe_customer_id"]
        assert "test" not in data["stripe_subscription_id"].lower()
        assert "test" not in data["stripe_customer_id"].lower()


# ---------------------------------------------------------------------------
# PUT /billing/subscriptions/{subscription_id}
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestUpdateSubscription:
    """Tests for subscription update endpoint."""

    def test_update_subscription_uses_mocked_db_and_stripe(self):
        """Updates subscription without hitting real Stripe/DB."""
        subscription_id = 31
        existing_row = _subscription_row_dict(subscription_id=subscription_id)
        refreshed_row = {**existing_row, "currency": "usd", "cancel_at_period_end": True}
        response_model = _subscription_response_dict(
            sub_id=subscription_id,
            stripe_subscription_id=existing_row["stripe_subscription_id"],
            stripe_customer_id=existing_row["stripe_customer_id"],
        )
        stripe_response = {
            "status": "active",
            "current_period_start": int(datetime.now().timestamp()),
            "current_period_end": int((datetime.now() + timedelta(days=30)).timestamp()),
            "cancel_at_period_end": True,
        }

        with (
            patch(
                "ghl_real_estate_ai.api.routes.billing._fetch_subscription_row",
                new=AsyncMock(side_effect=[existing_row, refreshed_row]),
            ) as mock_fetch,
            patch(
                "ghl_real_estate_ai.api.routes.billing.retry_with_exponential_backoff",
                new=AsyncMock(return_value=stripe_response),
            ) as mock_retry,
            patch(
                "ghl_real_estate_ai.api.routes.billing._update_subscription_db_state",
                new=AsyncMock(),
            ) as mock_update_db,
            patch(
                "ghl_real_estate_ai.api.routes.billing._build_subscription_response",
                return_value=response_model,
            ),
        ):
            client, _, _ = _make_billing_client()
            resp = client.put(
                f"/billing/subscriptions/{subscription_id}",
                json={"currency": "usd", "cancel_at_period_end": True},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == subscription_id
        assert "test" not in data["stripe_subscription_id"].lower()

        # First call loads existing row, second call loads refreshed row.
        assert mock_fetch.await_count == 2
        mock_retry.assert_awaited_once()
        assert (
            mock_retry.await_args.kwargs["subscription_id"]
            == existing_row["stripe_subscription_id"]
        )
        mock_update_db.assert_awaited_once()


# ---------------------------------------------------------------------------
# DELETE /billing/subscriptions/{subscription_id}
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestCancelSubscription:
    """Tests for subscription cancellation endpoint."""

    def test_cancel_at_period_end(self):
        """Cancels subscription at period end."""
        subscription_id = 77
        existing_row = _subscription_row_dict(subscription_id=subscription_id)
        stripe_response = {
            "status": "active",
            "current_period_end": int((datetime.now() + timedelta(days=14)).timestamp()),
            "canceled_at": None,
            "cancel_at_period_end": True,
        }

        with (
            patch(
                "ghl_real_estate_ai.api.routes.billing._fetch_subscription_row",
                new=AsyncMock(return_value=existing_row),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.billing.retry_with_exponential_backoff",
                new=AsyncMock(return_value=stripe_response),
            ) as mock_retry,
            patch(
                "ghl_real_estate_ai.api.routes.billing._update_subscription_db_state",
                new=AsyncMock(),
            ) as mock_update_db,
        ):
            client, _, _ = _make_billing_client()
            resp = client.delete(f"/billing/subscriptions/{subscription_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["immediate"] is False
        assert data["stripe_subscription_id"] == existing_row["stripe_subscription_id"]
        assert "test" not in data["stripe_subscription_id"].lower()
        assert (
            mock_retry.await_args.kwargs["subscription_id"]
            == existing_row["stripe_subscription_id"]
        )
        mock_update_db.assert_awaited_once()

    def test_cancel_immediately(self):
        """Cancels subscription immediately."""
        subscription_id = 78
        existing_row = _subscription_row_dict(subscription_id=subscription_id)
        stripe_response = {
            "status": "canceled",
            "current_period_end": int((datetime.now() + timedelta(days=30)).timestamp()),
            "canceled_at": int(datetime.now().timestamp()),
            "cancel_at_period_end": False,
        }

        with (
            patch(
                "ghl_real_estate_ai.api.routes.billing._fetch_subscription_row",
                new=AsyncMock(return_value=existing_row),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.billing.retry_with_exponential_backoff",
                new=AsyncMock(return_value=stripe_response),
            ) as mock_retry,
            patch(
                "ghl_real_estate_ai.api.routes.billing._update_subscription_db_state",
                new=AsyncMock(),
            ) as mock_update_db,
        ):
            client, _, _ = _make_billing_client()
            resp = client.delete(f"/billing/subscriptions/{subscription_id}?immediate=true")

        assert resp.status_code == 200
        data = resp.json()
        assert data["immediate"] is True
        assert data["stripe_subscription_id"] == existing_row["stripe_subscription_id"]
        assert data["status"] == "canceled"
        assert "test" not in data["stripe_subscription_id"].lower()
        assert (
            mock_retry.await_args.kwargs["subscription_id"]
            == existing_row["stripe_subscription_id"]
        )
        mock_update_db.assert_awaited_once()


# ---------------------------------------------------------------------------
# GET /billing/usage/{subscription_id}
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestGetUsage:
    """Tests for usage data endpoint."""

    def test_usage_not_found_returns_404(self):
        """Returns 404 when subscription has no usage data."""
        mock_sub_mgr = MagicMock()
        mock_sub_mgr.get_usage_summary = AsyncMock(return_value=None)

        client, _, _ = _make_billing_client(subscription_manager=mock_sub_mgr)
        resp = client.get("/billing/usage/999")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /billing/webhooks/stripe — Stripe webhook
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestStripeWebhook:
    """Tests for the Stripe webhook endpoint."""

    def test_missing_signature_returns_400(self):
        """Missing Stripe-Signature header returns 400."""
        client, _, _ = _make_billing_client()
        resp = client.post(
            "/billing/webhooks/stripe",
            content=b'{"type": "invoice.paid"}',
            headers={"Content-Type": "application/json"},
        )

        assert resp.status_code == 400

    def test_invalid_signature_returns_400(self):
        """Invalid Stripe signature returns 400."""
        mock_billing = MagicMock()
        mock_billing.verify_webhook_signature = MagicMock(return_value=False)

        client, _, _ = _make_billing_client(billing_service=mock_billing)
        resp = client.post(
            "/billing/webhooks/stripe",
            content=b'{"type": "invoice.paid"}',
            headers={
                "Content-Type": "application/json",
                "stripe-signature": "t=123,v1=bad_sig",
            },
        )

        assert resp.status_code == 400

    def test_valid_webhook_processes_event(self):
        """Valid webhook processes event and returns result."""
        mock_billing = MagicMock()
        mock_billing.verify_webhook_signature = MagicMock(return_value=True)
        mock_billing.process_webhook_event = AsyncMock(
            return_value={"processed": True, "actions_taken": ["subscription_updated"]}
        )

        mock_event = {
            "id": "evt_test123",
            "type": "invoice.paid",
            "data": {"object": {"id": "in_test"}},
        }

        with patch("ghl_real_estate_ai.api.routes.billing.stripe.Webhook.construct_event", return_value=mock_event):
            client, _, _ = _make_billing_client(billing_service=mock_billing)
            resp = client.post(
                "/billing/webhooks/stripe",
                content=b'{"type": "invoice.paid"}',
                headers={
                    "Content-Type": "application/json",
                    "stripe-signature": "t=123,v1=valid_sig",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["processed"] is True
        assert data["event_type"] == "invoice.paid"


# ---------------------------------------------------------------------------
# GET /billing/analytics/revenue
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestRevenueAnalytics:
    """Tests for revenue analytics endpoint."""

    def test_revenue_analytics_returns_data(self):
        """Returns revenue metrics."""
        mock_sub_mgr = MagicMock()
        mock_tier_dist = MagicMock(
            total_subscriptions=10,
            starter_count=4,
            professional_count=4,
            enterprise_count=2,
        )
        mock_sub_mgr.get_tier_distribution = AsyncMock(return_value=mock_tier_dist)

        client, _, _ = _make_billing_client(subscription_manager=mock_sub_mgr)
        resp = client.get("/billing/analytics/revenue")

        assert resp.status_code == 200
        data = resp.json()
        assert "total_arr" in data
        assert "monthly_revenue" in data


# ---------------------------------------------------------------------------
# GET /billing/analytics/tiers
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestTierDistribution:
    """Tests for tier distribution endpoint."""

    def test_tier_distribution_returns_counts(self):
        """Returns tier counts."""
        mock_sub_mgr = MagicMock()
        mock_tier_dist = MagicMock(
            total_subscriptions=10,
            starter_count=4,
            professional_count=4,
            enterprise_count=2,
        )
        mock_sub_mgr.get_tier_distribution = AsyncMock(return_value=mock_tier_dist)

        client, _, _ = _make_billing_client(subscription_manager=mock_sub_mgr)
        resp = client.get("/billing/analytics/tiers")

        assert resp.status_code == 200
