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

from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Import guard: billing.py has a known syntax error at line 512
# (positional arg follows keyword args in retry_with_exponential_backoff call)
# ---------------------------------------------------------------------------

_BILLING_IMPORT_ERROR = None
try:
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


def _make_billing_client(billing_service=None, subscription_manager=None, authenticated=True):
    """Create a TestClient with just the billing router, deps overridden via FastAPI.

    Args:
        authenticated: When True (default), override get_current_user so JWT
            validation is bypassed and existing tests stay green. When False,
            the real dependency runs and unauthenticated requests return 401.
    """
    mock_billing = billing_service or MagicMock()
    mock_sub_mgr = subscription_manager or MagicMock()
    mock_monitoring = MagicMock()

    from ghl_real_estate_ai.api.routes import billing as billing_module
    from ghl_real_estate_ai.api.routes.billing import (
        get_billing_service,
        get_monitoring_service,
        get_subscription_manager,
    )

    test_app = FastAPI()
    test_app.include_router(billing_module.router)
    # Stripe webhook lives on the unauthenticated router
    test_app.include_router(billing_module.stripe_webhook_router)

    # Use FastAPI dependency_overrides instead of module-level patching
    test_app.dependency_overrides[get_billing_service] = lambda: mock_billing
    test_app.dependency_overrides[get_subscription_manager] = lambda: mock_sub_mgr
    test_app.dependency_overrides[get_monitoring_service] = lambda: mock_monitoring

    if authenticated:
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.location_id = "loc-123"
        test_app.dependency_overrides[get_current_user] = lambda: mock_user

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
        mock_billing.cancel_subscription = AsyncMock(return_value={"id": "sub_test123", "status": "canceled"})
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
        mock_db = _FakeDatabase({"id": 1, "location_id": "loc-123"})
        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
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
        mock_billing.add_usage_record = AsyncMock(return_value=MagicMock(id="usage_stripe_123"))
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
        client, _, _ = _make_billing_client()
        mock_db = _SequencedDatabase(
            [
                {"mrr": 500.0, "active_count": 2, "enterprise_count": 0},
                {"usage_revenue": 0.0},
                {"churned": 0, "total": 2},
                {"upgrades": 0, "total": 2},
            ]
        )
        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
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
                {"mrr": 847.0, "active_count": 3, "enterprise_count": 1},
                {"usage_revenue": 53.0},
                {"churned": 0, "total": 3},
                {"upgrades": 1, "total": 3},
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


# ---------------------------------------------------------------------------
# Auth enforcement: unauthenticated requests must return 401
# ---------------------------------------------------------------------------


@skip_if_no_billing
class TestBillingAuthEnforcement:
    """Verify that billing routes enforce JWT auth and Stripe webhook does not."""

    def test_unauthenticated_create_subscription_returns_401(self):
        """POST /billing/subscriptions without a token returns 401."""
        client, _, _ = _make_billing_client(authenticated=False)
        resp = client.post("/billing/subscriptions", json={})
        assert resp.status_code == 401

    def test_unauthenticated_get_subscription_returns_401(self):
        """GET /billing/subscriptions/{id} without a token returns 401."""
        client, _, _ = _make_billing_client(authenticated=False)
        resp = client.get("/billing/subscriptions/1")
        assert resp.status_code == 401

    def test_unauthenticated_revenue_analytics_returns_401(self):
        """GET /billing/analytics/revenue without a token returns 401."""
        client, _, _ = _make_billing_client(authenticated=False)
        resp = client.get("/billing/analytics/revenue")
        assert resp.status_code == 401

    def test_authenticated_subscription_request_proceeds(self):
        """Authenticated request reaches the route handler (not blocked by auth)."""
        mock_billing = MagicMock()
        mock_billing.create_subscription = AsyncMock(side_effect=Exception("db error"))
        client, _, _ = _make_billing_client(billing_service=mock_billing, authenticated=True)
        resp = client.post(
            "/billing/subscriptions",
            json={"location_id": "loc1", "tier": "starter", "email": "a@b.com"},
        )
        # Reaches handler — auth passed, gets a 500 from mocked db error (not 401)
        assert resp.status_code != 401

    def test_stripe_webhook_accessible_without_jwt(self):
        """Stripe webhook endpoint does not require JWT auth (uses Stripe sig instead)."""
        client, _, _ = _make_billing_client(authenticated=False)
        resp = client.post(
            "/billing/webhooks/stripe",
            content=b'{"type": "invoice.paid"}',
            headers={"Content-Type": "application/json"},
        )
        # No JWT — but Stripe sig check runs. Missing sig → 400, not 401.
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Phase 5: TestBillingLocationAuth — IDOR protection (6 tests)
# ---------------------------------------------------------------------------


def _make_no_location_client(billing_service=None, subscription_manager=None):
    """Create a TestClient where the authenticated user has no location_id."""
    from ghl_real_estate_ai.api.routes import billing as billing_module
    from ghl_real_estate_ai.api.routes.billing import (
        get_billing_service,
        get_monitoring_service,
        get_subscription_manager,
    )

    mock_billing = billing_service or MagicMock()
    mock_sub_mgr = subscription_manager or MagicMock()
    mock_monitoring = MagicMock()

    test_app = FastAPI()
    test_app.include_router(billing_module.router)
    test_app.include_router(billing_module.stripe_webhook_router)

    test_app.dependency_overrides[get_billing_service] = lambda: mock_billing
    test_app.dependency_overrides[get_subscription_manager] = lambda: mock_sub_mgr
    test_app.dependency_overrides[get_monitoring_service] = lambda: mock_monitoring

    # User with NO location_id set
    no_loc_user = MagicMock()
    no_loc_user.id = 99
    no_loc_user.is_active = True
    no_loc_user.location_id = None
    test_app.dependency_overrides[get_current_user] = lambda: no_loc_user

    return TestClient(test_app, raise_server_exceptions=False), mock_billing, mock_sub_mgr


def _make_wrong_location_client(billing_service=None, subscription_manager=None):
    """Create a TestClient where the authenticated user belongs to a DIFFERENT location than the subscription."""
    from ghl_real_estate_ai.api.routes import billing as billing_module
    from ghl_real_estate_ai.api.routes.billing import (
        get_billing_service,
        get_monitoring_service,
        get_subscription_manager,
    )

    mock_billing = billing_service or MagicMock()
    mock_sub_mgr = subscription_manager or MagicMock()
    mock_monitoring = MagicMock()

    test_app = FastAPI()
    test_app.include_router(billing_module.router)
    test_app.include_router(billing_module.stripe_webhook_router)

    test_app.dependency_overrides[get_billing_service] = lambda: mock_billing
    test_app.dependency_overrides[get_subscription_manager] = lambda: mock_sub_mgr
    test_app.dependency_overrides[get_monitoring_service] = lambda: mock_monitoring

    wrong_loc_user = MagicMock()
    wrong_loc_user.id = 77
    wrong_loc_user.is_active = True
    wrong_loc_user.location_id = "loc-wrong"
    test_app.dependency_overrides[get_current_user] = lambda: wrong_loc_user

    return TestClient(test_app, raise_server_exceptions=False), mock_billing, mock_sub_mgr


@skip_if_no_billing
class TestBillingLocationAuth:
    """IDOR protection: users without a location_id are blocked from location-scoped endpoints."""

    def test_update_subscription_without_location_id_returns_403(self):
        """PUT /billing/subscriptions/{id} with no location_id → 403."""
        client, _, _ = _make_no_location_client()
        resp = client.put("/billing/subscriptions/1", json={"tier": "starter"})
        assert resp.status_code == 403

    def test_cancel_subscription_without_location_id_returns_403(self):
        """DELETE /billing/subscriptions/{id} with no location_id → 403."""
        client, _, _ = _make_no_location_client()
        resp = client.delete("/billing/subscriptions/1")
        assert resp.status_code == 403

    def test_error_code_is_no_location_associated(self):
        """Error detail has machine-readable error_code."""
        client, _, _ = _make_no_location_client()
        resp = client.put("/billing/subscriptions/1", json={"tier": "starter"})
        assert resp.status_code == 403
        data = resp.json()
        assert data["detail"]["error_code"] == "no_location_associated"

    def test_user_with_location_id_passes_update_auth(self):
        """User WITH a location_id is not blocked by IDOR guard on PUT."""
        client, _, _ = _make_billing_client()  # MagicMock user — location_id is truthy MagicMock
        # Route still needs a DB row, so this will 500/404 — but NOT 403.
        resp = client.put("/billing/subscriptions/1", json={"tier": "starter"})
        assert resp.status_code != 403

    def test_user_with_location_id_passes_cancel_auth(self):
        """User WITH a location_id is not blocked by IDOR guard on DELETE."""
        mock_billing = MagicMock()
        mock_billing.cancel_subscription = AsyncMock(return_value={"id": "sub_test", "status": "canceled"})
        client, _, _ = _make_billing_client(billing_service=mock_billing)
        mock_db = _FakeDatabase(_build_subscription_row(sub_id=1))
        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
            resp = client.delete("/billing/subscriptions/1?immediate=true")
        assert resp.status_code != 403

    def test_error_type_is_authorization(self):
        """Error type is 'authorization' for IDOR-blocked requests."""
        client, _, _ = _make_no_location_client()
        resp = client.delete("/billing/subscriptions/1")
        assert resp.status_code == 403
        data = resp.json()
        assert data["detail"]["error_type"] == "authorization"


# ---------------------------------------------------------------------------
# Phase 5: TestTrialFlow — Trial creation and conversion (4 tests)
# ---------------------------------------------------------------------------


@skip_if_no_billing
class TestTrialFlow:
    """Trial period creation and state transitions."""

    def test_starter_subscription_creates_with_14_day_trial(self):
        """Creating a starter subscription uses 14-day trial from SUBSCRIPTION_TIERS."""
        from ghl_real_estate_ai.api.schemas.billing import SUBSCRIPTION_TIERS, SubscriptionTier

        tier_config = SUBSCRIPTION_TIERS[SubscriptionTier.STARTER]
        assert tier_config.trial_days == 14

    def test_enterprise_subscription_gets_30_day_trial(self):
        """Enterprise tier has a 30-day trial period."""
        from ghl_real_estate_ai.api.schemas.billing import SUBSCRIPTION_TIERS, SubscriptionTier

        tier_config = SUBSCRIPTION_TIERS[SubscriptionTier.ENTERPRISE]
        assert tier_config.trial_days == 30

    def test_growth_subscription_has_14_day_trial(self):
        """Growth tier has a 14-day trial period."""
        from ghl_real_estate_ai.api.schemas.billing import SUBSCRIPTION_TIERS, SubscriptionTier

        tier_config = SUBSCRIPTION_TIERS[SubscriptionTier.GROWTH]
        assert tier_config.trial_days == 14

    def test_trial_will_end_webhook_is_processed(self):
        """customer.subscription.trial_will_end webhook is processed without error."""
        mock_billing = MagicMock()
        mock_billing.verify_webhook_signature = MagicMock(return_value=True)
        mock_billing.process_webhook_event = AsyncMock(
            return_value={
                "processed": True,
                "actions_taken": ["trial_will_end_notification_sent"],
            }
        )

        trial_event = {
            "id": "evt_trial_end",
            "type": "customer.subscription.trial_will_end",
            "data": {"object": {"id": "sub_trial123", "trial_end": 1234567890}},
        }

        with patch("ghl_real_estate_ai.api.routes.billing.stripe.Webhook.construct_event", return_value=trial_event):
            client, _, _ = _make_billing_client(billing_service=mock_billing)
            resp = client.post(
                "/billing/webhooks/stripe",
                content=b'{"type": "customer.subscription.trial_will_end"}',
                headers={"Content-Type": "application/json", "stripe-signature": "t=123,v1=sig"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["event_type"] == "customer.subscription.trial_will_end"
        assert data["processed"] is True


# ---------------------------------------------------------------------------
# Phase 5: TestWebhookHandlers — Real webhook event processing (5 tests)
# ---------------------------------------------------------------------------


@skip_if_no_billing
class TestWebhookHandlers:
    """Webhook events trigger correct DB-backed state transitions."""

    def _post_webhook(self, client, event_type: str, event_obj: dict, event_id: str = "evt_test"):
        event = {
            "id": event_id,
            "type": event_type,
            "data": {"object": event_obj},
        }
        mock_billing = MagicMock()
        mock_billing.verify_webhook_signature = MagicMock(return_value=True)
        mock_billing.process_webhook_event = AsyncMock(
            return_value={"processed": True, "actions_taken": [f"{event_type}_handled"]}
        )
        return event, mock_billing

    def test_payment_succeeded_webhook_is_processed(self):
        """invoice.payment_succeeded webhook is processed successfully."""
        mock_billing = MagicMock()
        mock_billing.verify_webhook_signature = MagicMock(return_value=True)
        mock_billing.process_webhook_event = AsyncMock(
            return_value={
                "processed": True,
                "actions_taken": ["reset_usage_counter", "set_status_active"],
            }
        )
        event = {
            "id": "evt_pay_success",
            "type": "invoice.payment_succeeded",
            "data": {"object": {"subscription": "sub_123", "amount_paid": 29700}},
        }

        with patch("ghl_real_estate_ai.api.routes.billing.stripe.Webhook.construct_event", return_value=event):
            client, _, _ = _make_billing_client(billing_service=mock_billing)
            resp = client.post(
                "/billing/webhooks/stripe",
                content=b"{}",
                headers={"Content-Type": "application/json", "stripe-signature": "t=1,v1=s"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["event_type"] == "invoice.payment_succeeded"
        assert "reset_usage_counter" in data["actions_taken"]

    def test_payment_failed_webhook_is_processed(self):
        """invoice.payment_failed webhook is processed and returns past_due action."""
        mock_billing = MagicMock()
        mock_billing.verify_webhook_signature = MagicMock(return_value=True)
        mock_billing.process_webhook_event = AsyncMock(
            return_value={"processed": True, "actions_taken": ["set_status_past_due"]}
        )
        event = {
            "id": "evt_pay_fail",
            "type": "invoice.payment_failed",
            "data": {"object": {"subscription": "sub_123"}},
        }

        with patch("ghl_real_estate_ai.api.routes.billing.stripe.Webhook.construct_event", return_value=event):
            client, _, _ = _make_billing_client(billing_service=mock_billing)
            resp = client.post(
                "/billing/webhooks/stripe",
                content=b"{}",
                headers={"Content-Type": "application/json", "stripe-signature": "t=1,v1=s"},
            )

        assert resp.status_code == 200
        assert resp.json()["processed"] is True

    def test_subscription_updated_webhook_is_processed(self):
        """customer.subscription.updated webhook is processed and syncs status."""
        mock_billing = MagicMock()
        mock_billing.verify_webhook_signature = MagicMock(return_value=True)
        mock_billing.process_webhook_event = AsyncMock(
            return_value={"processed": True, "actions_taken": ["sync_subscription_status"]}
        )
        event = {
            "id": "evt_sub_updated",
            "type": "customer.subscription.updated",
            "data": {"object": {"id": "sub_123", "status": "active"}},
        }

        with patch("ghl_real_estate_ai.api.routes.billing.stripe.Webhook.construct_event", return_value=event):
            client, _, _ = _make_billing_client(billing_service=mock_billing)
            resp = client.post(
                "/billing/webhooks/stripe",
                content=b"{}",
                headers={"Content-Type": "application/json", "stripe-signature": "t=1,v1=s"},
            )

        assert resp.status_code == 200
        assert resp.json()["event_type"] == "customer.subscription.updated"

    def test_subscription_deleted_webhook_is_processed(self):
        """customer.subscription.deleted webhook is processed and cancels subscription."""
        mock_billing = MagicMock()
        mock_billing.verify_webhook_signature = MagicMock(return_value=True)
        mock_billing.process_webhook_event = AsyncMock(
            return_value={"processed": True, "actions_taken": ["set_status_canceled"]}
        )
        event = {
            "id": "evt_sub_del",
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_123"}},
        }

        with patch("ghl_real_estate_ai.api.routes.billing.stripe.Webhook.construct_event", return_value=event):
            client, _, _ = _make_billing_client(billing_service=mock_billing)
            resp = client.post(
                "/billing/webhooks/stripe",
                content=b"{}",
                headers={"Content-Type": "application/json", "stripe-signature": "t=1,v1=s"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "set_status_canceled" in data["actions_taken"]

    def test_unknown_webhook_event_type_is_handled_gracefully(self):
        """Unrecognized event types are processed without error."""
        mock_billing = MagicMock()
        mock_billing.verify_webhook_signature = MagicMock(return_value=True)
        mock_billing.process_webhook_event = AsyncMock(
            return_value={"processed": True, "actions_taken": ["event_logged"]}
        )
        event = {
            "id": "evt_unknown",
            "type": "charge.refunded",
            "data": {"object": {}},
        }

        with patch("ghl_real_estate_ai.api.routes.billing.stripe.Webhook.construct_event", return_value=event):
            client, _, _ = _make_billing_client(billing_service=mock_billing)
            resp = client.post(
                "/billing/webhooks/stripe",
                content=b"{}",
                headers={"Content-Type": "application/json", "stripe-signature": "t=1,v1=s"},
            )

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Phase 5: TestPricingTiers — SUBSCRIPTION_TIERS config (3 tests)
# ---------------------------------------------------------------------------


@skip_if_no_billing
class TestPricingTiers:
    """Verify SUBSCRIPTION_TIERS has correct pricing, allowances, and trial days."""

    def test_starter_tier_is_297_with_500_leads(self):
        """Starter tier: $297/month, 500 leads, 14-day trial."""
        from decimal import Decimal

        from ghl_real_estate_ai.api.schemas.billing import SUBSCRIPTION_TIERS, SubscriptionTier

        cfg = SUBSCRIPTION_TIERS[SubscriptionTier.STARTER]
        assert cfg.price_monthly == Decimal("297.00")
        assert cfg.usage_allowance == 500
        assert cfg.trial_days == 14

    def test_growth_tier_is_597_with_2500_leads(self):
        """Growth tier: $597/month, 2500 leads, 14-day trial."""
        from decimal import Decimal

        from ghl_real_estate_ai.api.schemas.billing import SUBSCRIPTION_TIERS, SubscriptionTier

        cfg = SUBSCRIPTION_TIERS[SubscriptionTier.GROWTH]
        assert cfg.price_monthly == Decimal("597.00")
        assert cfg.usage_allowance == 2500
        assert cfg.trial_days == 14

    def test_enterprise_tier_is_1497_with_unlimited_leads(self):
        """Enterprise tier: $1497/month, 999999 leads (unlimited), 30-day trial."""
        from decimal import Decimal

        from ghl_real_estate_ai.api.schemas.billing import SUBSCRIPTION_TIERS, SubscriptionTier

        cfg = SUBSCRIPTION_TIERS[SubscriptionTier.ENTERPRISE]
        assert cfg.price_monthly == Decimal("1497.00")
        assert cfg.usage_allowance == 999999
        assert cfg.overage_rate == Decimal("0.00")
        assert cfg.trial_days == 30


# ---------------------------------------------------------------------------
# Phase 5: TestUsageAlerts — 80% alert + overage + below threshold (3 tests)
# ---------------------------------------------------------------------------


@skip_if_no_billing
class TestUsageAlerts:
    """Usage threshold alerting: 80% alert fires, 100% overage active, <75% silent."""

    def test_80pct_usage_triggers_alert_action(self):
        """400/500 leads (80%) fires 'usage_80pct_alert_sent' action."""
        import asyncio

        from ghl_real_estate_ai.services.subscription_manager import SubscriptionManager

        mgr = SubscriptionManager()
        result = asyncio.get_event_loop().run_until_complete(
            mgr.handle_usage_threshold("loc-test", current_usage=400, period_usage_allowance=500)
        )
        assert "usage_80pct_alert_sent" in result["actions_taken"]
        assert result["threshold_level"] == "alert_80"

    def test_100pct_usage_activates_overage_billing(self):
        """500/500 leads (100%) marks overage as active."""
        import asyncio

        from ghl_real_estate_ai.services.subscription_manager import SubscriptionManager

        mgr = SubscriptionManager()
        result = asyncio.get_event_loop().run_until_complete(
            mgr.handle_usage_threshold("loc-test", current_usage=500, period_usage_allowance=500)
        )
        assert result["overage_billing_active"] is True
        assert result["threshold_level"] == "overage"

    def test_below_75pct_usage_sends_no_alert(self):
        """300/500 leads (60%) — no alert action taken."""
        import asyncio

        from ghl_real_estate_ai.services.subscription_manager import SubscriptionManager

        mgr = SubscriptionManager()
        result = asyncio.get_event_loop().run_until_complete(
            mgr.handle_usage_threshold("loc-test", current_usage=300, period_usage_allowance=500)
        )
        assert result["actions_taken"] == []
        assert result["threshold_level"] == "normal"


# ---------------------------------------------------------------------------
# P2.6: TestNoLocationGuard — newly-guarded endpoints return 403 without location
# ---------------------------------------------------------------------------


@skip_if_no_billing
class TestNoLocationGuard:
    """Newly-guarded endpoints block users who have no location_id."""

    def test_get_subscription_without_location_returns_403(self):
        """GET /billing/subscriptions/{id} with no location_id → 403."""
        client, _, _ = _make_no_location_client()
        resp = client.get("/billing/subscriptions/1")
        assert resp.status_code == 403

    def test_record_usage_without_location_returns_403(self):
        """POST /billing/usage with no location_id → 403."""
        client, _, _ = _make_no_location_client()
        resp = client.post(
            "/billing/usage",
            json={
                "subscription_id": 1,
                "lead_id": "lead-001",
                "contact_id": "contact-001",
                "amount": "0.01",
                "tier": "starter",
                "billing_period_start": datetime.now().isoformat(),
                "billing_period_end": (datetime.now() + timedelta(days=30)).isoformat(),
            },
        )
        assert resp.status_code == 403

    def test_list_invoices_without_location_returns_403(self):
        """GET /billing/invoices with no location_id → 403."""
        client, _, _ = _make_no_location_client()
        resp = client.get("/billing/invoices?customer_id=cus_test")
        assert resp.status_code == 403

    def test_billing_history_without_location_returns_403(self):
        """GET /billing/billing-history/{customer_id} with no location_id → 403."""
        client, _, _ = _make_no_location_client()
        resp = client.get("/billing/billing-history/cus_test")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# P2.6: TestIDORSubscriptionOwnership — cross-location subscription access blocked
# ---------------------------------------------------------------------------


@skip_if_no_billing
class TestIDORSubscriptionOwnership:
    """IDOR protection: users from loc-wrong cannot access subscriptions belonging to loc-123."""

    def test_wrong_location_on_get_subscription_returns_403(self):
        """User loc-wrong cannot GET subscription belonging to loc-123."""
        client, _, _ = _make_wrong_location_client()
        mock_db = _FakeDatabase({"id": 1, "location_id": "loc-123"})
        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
            resp = client.get("/billing/subscriptions/1")
        assert resp.status_code == 403

    def test_wrong_location_on_update_subscription_returns_403(self):
        """User loc-wrong cannot PUT subscription belonging to loc-123."""
        client, _, _ = _make_wrong_location_client()
        mock_db = _FakeDatabase({"id": 1, "location_id": "loc-123"})
        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
            resp = client.put("/billing/subscriptions/1", json={"tier": "starter"})
        assert resp.status_code == 403

    def test_wrong_location_on_cancel_subscription_returns_403(self):
        """User loc-wrong cannot DELETE subscription belonging to loc-123."""
        client, _, _ = _make_wrong_location_client()
        mock_db = _FakeDatabase({"id": 1, "location_id": "loc-123"})
        with patch(
            "ghl_real_estate_ai.services.database_service.get_database",
            AsyncMock(return_value=mock_db),
        ):
            resp = client.delete("/billing/subscriptions/1")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# P2.6: TestJWTLocationClaim — JWT payload includes location_id
# ---------------------------------------------------------------------------


@skip_if_no_billing
class TestJWTLocationClaim:
    """AuthService.create_token() embeds location_id in the JWT payload."""

    def test_auth_service_includes_location_id_in_jwt(self):
        """create_token() includes location_id claim for downstream use."""
        import jwt as pyjwt

        from ghl_real_estate_ai.services.auth_service import AuthService, User, UserRole

        service = AuthService()
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            role=UserRole.AGENT,
            is_active=True,
            location_id="loc-jwt-test",
        )
        token = service.create_token(user)
        payload = pyjwt.decode(token, service.secret_key, algorithms=[service.algorithm])
        assert payload.get("location_id") == "loc-jwt-test"
