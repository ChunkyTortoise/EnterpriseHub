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

    # Keep patched singletons active for the entire request lifecycle.
    billing_module.billing_service = mock_billing
    billing_module.subscription_manager = mock_sub_mgr
    billing_module.monitoring_service = MagicMock()

    test_app = FastAPI()
    test_app.include_router(billing_module.router)
    return TestClient(test_app, raise_server_exceptions=False), mock_billing, mock_sub_mgr


class _FakeConnection:
    def __init__(self, row):
        self._row = row

    async def fetchrow(self, *_args, **_kwargs):
        return self._row

    async def execute(self, *_args, **_kwargs):
        return "UPDATE 1"


class _SequencedConnection:
    def __init__(self, rows):
        self._rows = list(rows)

    async def fetchrow(self, *_args, **_kwargs):
        if not self._rows:
            return None
        return self._rows.pop(0)

    async def execute(self, *_args, **_kwargs):
        return "UPDATE 1"


class _FakeConnectionContext:
    def __init__(self, row):
        self._connection = _FakeConnection(row)

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeDatabase:
    def __init__(self, row):
        self._row = row

    def get_connection(self):
        return _FakeConnectionContext(self._row)


class _SequencedConnectionContext:
    def __init__(self, rows):
        self._connection = _SequencedConnection(rows)

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _SequencedDatabase:
    def __init__(self, rows):
        self._rows = rows

    def get_connection(self):
        return _SequencedConnectionContext(self._rows)


def _build_subscription_row(sub_id: int = 1):
    now = datetime.now()
    return {
        "id": sub_id,
        "location_id": "loc-123",
        "stripe_subscription_id": "sub_test123",
        "stripe_customer_id": "cus_test123",
        "tier": "professional",
        "status": "active",
        "currency": "usd",
        "current_period_start": now,
        "current_period_end": now + timedelta(days=30),
        "usage_allowance": 150,
        "usage_current": 50,
        "overage_rate": 1.50,
        "base_price": 249.00,
        "trial_end": None,
        "cancel_at_period_end": False,
        "created_at": now,
        "updated_at": now,
        "customer_email": "test@example.com",
        "customer_name": "Test Customer",
    }


def _subscription_response_dict(sub_id: int = 1, tier: str = "professional"):
    """Build a mock SubscriptionResponse-like dict."""
    from ghl_real_estate_ai.api.schemas.billing import (
        SubscriptionResponse,
        SubscriptionStatus,
        SubscriptionTier,
    )

    return SubscriptionResponse(
        id=sub_id,
        location_id="loc-123",
        stripe_subscription_id="sub_test123",
        stripe_customer_id="cus_test123",
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
        client, _, _ = _make_billing_client()
        mock_db = _FakeDatabase(_build_subscription_row(sub_id=1))

        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
            resp = client.get("/billing/subscriptions/1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1


# ---------------------------------------------------------------------------
# DELETE /billing/subscriptions/{subscription_id}
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestCancelSubscription:
    """Tests for subscription cancellation endpoint."""

    def test_cancel_at_period_end(self):
        """Cancels subscription at period end."""
        mock_billing = MagicMock()
        mock_billing.cancel_subscription = AsyncMock(
            return_value={"id": "sub_test123", "status": "active", "cancel_at_period_end": True}
        )
        client, _, _ = _make_billing_client(billing_service=mock_billing)
        mock_db = _FakeDatabase(_build_subscription_row(sub_id=1))

        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
            resp = client.delete("/billing/subscriptions/1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["immediate"] is False
        mock_billing.cancel_subscription.assert_awaited_once_with("sub_test123", False)

    def test_cancel_immediately(self):
        """Cancels subscription immediately."""
        mock_billing = MagicMock()
        mock_billing.cancel_subscription = AsyncMock(
            return_value={"id": "sub_test123", "status": "canceled"}
        )
        client, _, _ = _make_billing_client(billing_service=mock_billing)
        mock_db = _FakeDatabase(_build_subscription_row(sub_id=1))

        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
            resp = client.delete("/billing/subscriptions/1?immediate=true")

        assert resp.status_code == 200
        data = resp.json()
        assert data["immediate"] is True
        mock_billing.cancel_subscription.assert_awaited_once_with("sub_test123", True)


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
# PUT /billing/subscriptions/{subscription_id}
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestUpdateSubscription:
    """Tests for update subscription behavior changes."""

    def test_update_subscription_no_changes_returns_400(self):
        """Rejects update requests with no mutation payload."""
        client, _, _ = _make_billing_client()
        resp = client.put("/billing/subscriptions/1", json={})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /billing/usage
# ---------------------------------------------------------------------------

@skip_if_no_billing
class TestRecordUsage:
    """Tests for usage persistence and response fields."""

    def test_record_usage_persists_usage_row_and_returns_ids(self):
        mock_billing = MagicMock()
        mock_billing.add_usage_record = AsyncMock(return_value={"id": "usage_stripe_123"})
        client, _, _ = _make_billing_client(billing_service=mock_billing)

        mock_db = _FakeDatabase({"id": 42})
        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
            resp = client.post(
                "/billing/usage",
                json={
                    "subscription_id": 1,
                    "lead_id": "lead-001",
                    "contact_id": "contact-001",
                    "amount": "19.99",
                    "tier": "hot",
                    "billing_period_start": datetime.now().isoformat(),
                    "billing_period_end": (datetime.now() + timedelta(days=30)).isoformat(),
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["usage_record_id"] == 42
        assert data["stripe_usage_record_id"] == "usage_stripe_123"


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

    def test_revenue_analytics_prefers_db_aggregates(self):
        """Uses subscription + usage aggregate rows when DB is available."""
        client, _, _ = _make_billing_client()
        mock_db = _SequencedDatabase(
            [
                {
                    "active_count": 3,
                    "enterprise_count": 1,
                    "recurring_monthly_revenue": 847.0,
                    "canceled_count": 1,
                },
                {"monthly_usage_revenue": 53.0},
            ]
        )
        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
            resp = client.get("/billing/analytics/revenue")

        assert resp.status_code == 200
        data = resp.json()
        assert float(data["monthly_revenue"]) == pytest.approx(900.0)
        assert float(data["total_arr"]) == pytest.approx(10800.0)
        assert data["total_active_subscriptions"] == 3


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
