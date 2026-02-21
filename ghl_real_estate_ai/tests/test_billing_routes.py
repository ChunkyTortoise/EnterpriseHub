"""
Integration tests for billing API routes (ROADMAP-008 through ROADMAP-012).

Tests directly invoke the route handler functions with mocked DB and Stripe
dependencies, verifying the SQL queries and business logic without needing
the full FastAPI app import chain (which has broken infra deps being fixed
by infra-agent).

Tests cover:
- ROADMAP-008: Subscription DB lookup (get_subscription)
- ROADMAP-009: Payment method + cancellation modifications (update_subscription)
- ROADMAP-010: DB validation before Stripe cancel + double-cancel prevention (cancel_subscription)
- ROADMAP-011: Usage records DB insert (record_usage)
- ROADMAP-012: Location ID resolution from customer (get_billing_history)
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Patch target for function-local `from ...database_service import get_database`
DB_PATCH = "ghl_real_estate_ai.services.database_service.get_database"


# ---------------------------------------------------------------------------
# Helpers: fake asyncpg rows and DB connection
# ---------------------------------------------------------------------------


class FakeRecord(dict):
    """Dict subclass that supports attribute-style access like asyncpg.Record."""

    pass


def _sub_row(**overrides):
    """Build a fake subscription row with sensible defaults."""
    now = datetime.now()
    defaults = {
        "id": 1,
        "location_id": "loc_test_123",
        "stripe_subscription_id": "sub_stripe_abc",
        "stripe_customer_id": "cus_stripe_xyz",
        "tier": "professional",
        "status": "active",
        "currency": "usd",
        "current_period_start": now - timedelta(days=15),
        "current_period_end": now + timedelta(days=15),
        "usage_allowance": 150,
        "usage_current": 42,
        "overage_rate": Decimal("1.50"),
        "base_price": Decimal("249.00"),
        "trial_end": None,
        "cancel_at_period_end": False,
        "created_at": now - timedelta(days=60),
        "updated_at": now - timedelta(days=1),
        "customer_email": "test@example.com",
        "customer_name": "Test Customer",
    }
    defaults.update(overrides)
    return FakeRecord(defaults)


class FakeConn:
    """Async context manager that mocks an asyncpg connection."""

    def __init__(self, fetchrow_result=None, fetch_result=None, fetchval_result=None):
        self.fetchrow_result = fetchrow_result
        self.fetch_result = fetch_result or []
        self.fetchval_result = fetchval_result
        self.executed = []

    async def fetchrow(self, query, *args):
        return self.fetchrow_result

    async def fetch(self, query, *args):
        return self.fetch_result

    async def fetchval(self, query, *args):
        return self.fetchval_result

    async def execute(self, query, *args):
        self.executed.append((query, args))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeDB:
    def __init__(self, conn):
        self._conn = conn

    def get_connection(self):
        return self._conn


# ---------------------------------------------------------------------------
# ROADMAP-008: get_subscription — real DB query
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_008_get_subscription_returns_db_data():
    """ROADMAP-008: get_subscription queries subscriptions table and returns real data."""
    row = _sub_row()
    conn = FakeConn(fetchrow_result=row)
    db = FakeDB(conn)

    with patch(DB_PATCH, new_callable=AsyncMock, return_value=db):
        from ghl_real_estate_ai.api.routes.billing import get_subscription

        result = await get_subscription(1)

    assert result.id == 1
    assert result.location_id == "loc_test_123"
    assert result.tier.value == "professional"
    assert result.status.value == "active"
    assert result.usage_allowance == 150
    assert result.usage_current == 42


@pytest.mark.asyncio
async def test_roadmap_008_get_subscription_not_found_raises_404():
    """ROADMAP-008: Returns HTTPException 404 when subscription not in DB."""
    conn = FakeConn(fetchrow_result=None)
    db = FakeDB(conn)

    with patch(DB_PATCH, new_callable=AsyncMock, return_value=db):
        from fastapi import HTTPException

        from ghl_real_estate_ai.api.routes.billing import get_subscription

        with pytest.raises(HTTPException) as exc_info:
            await get_subscription(9999)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# ROADMAP-009: update_subscription — payment method + cancellation schedule
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_009_payment_method_update():
    """ROADMAP-009: update_subscription attaches payment method via Stripe and returns DB state."""
    row = _sub_row()
    conn = FakeConn(fetchrow_result=row)
    db = FakeDB(conn)

    with (
        patch(DB_PATCH, new_callable=AsyncMock, return_value=db),
        patch("ghl_real_estate_ai.api.routes.billing.stripe") as mock_stripe,
    ):
        mock_stripe.PaymentMethod.attach = MagicMock()
        mock_stripe.Customer.modify = MagicMock()

        from fastapi import BackgroundTasks

        from ghl_real_estate_ai.api.routes.billing import update_subscription
        from ghl_real_estate_ai.api.schemas.billing import ModifySubscriptionRequest

        request = ModifySubscriptionRequest(payment_method_id="pm_new_card")
        bg = BackgroundTasks()
        result = await update_subscription(1, request, bg)

    assert result.id == 1
    assert result.location_id == "loc_test_123"
    mock_stripe.PaymentMethod.attach.assert_called_once_with("pm_new_card", customer="cus_stripe_xyz")
    mock_stripe.Customer.modify.assert_called_once()


@pytest.mark.asyncio
async def test_roadmap_009_cancel_at_period_end():
    """ROADMAP-009: Scheduling cancellation updates Stripe + DB."""
    row = _sub_row()
    conn = FakeConn(fetchrow_result=row)
    db = FakeDB(conn)

    with (
        patch(DB_PATCH, new_callable=AsyncMock, return_value=db),
        patch("ghl_real_estate_ai.api.routes.billing.stripe") as mock_stripe,
    ):
        mock_stripe.Subscription.modify = MagicMock()

        from fastapi import BackgroundTasks

        from ghl_real_estate_ai.api.routes.billing import update_subscription
        from ghl_real_estate_ai.api.schemas.billing import ModifySubscriptionRequest

        request = ModifySubscriptionRequest(cancel_at_period_end=True)
        bg = BackgroundTasks()
        result = await update_subscription(1, request, bg)

    assert result.id == 1
    mock_stripe.Subscription.modify.assert_called_once_with("sub_stripe_abc", cancel_at_period_end=True)
    assert any("cancel_at_period_end" in q for q, _ in conn.executed)


@pytest.mark.asyncio
async def test_roadmap_009_update_not_found():
    """ROADMAP-009: update_subscription returns 404 when subscription not found."""
    conn = FakeConn(fetchrow_result=None)
    db = FakeDB(conn)

    with patch(DB_PATCH, new_callable=AsyncMock, return_value=db):
        from fastapi import BackgroundTasks, HTTPException

        from ghl_real_estate_ai.api.routes.billing import update_subscription
        from ghl_real_estate_ai.api.schemas.billing import ModifySubscriptionRequest

        request = ModifySubscriptionRequest(payment_method_id="pm_new_card")
        bg = BackgroundTasks()

        with pytest.raises(HTTPException) as exc_info:
            await update_subscription(9999, request, bg)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# ROADMAP-010: cancel_subscription — double-cancel prevention
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_010_double_cancel_returns_409():
    """ROADMAP-010: Canceling an already-canceled subscription returns 409."""
    row = _sub_row(status="canceled")
    conn = FakeConn(fetchrow_result=row)
    db = FakeDB(conn)

    with patch(DB_PATCH, new_callable=AsyncMock, return_value=db):
        from fastapi import BackgroundTasks, HTTPException

        from ghl_real_estate_ai.api.routes.billing import cancel_subscription

        bg = BackgroundTasks()

        with pytest.raises(HTTPException) as exc_info:
            await cancel_subscription(1, bg, immediate=False)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["error_code"] == "subscription_already_canceled"


@pytest.mark.asyncio
async def test_roadmap_010_cancel_valid_calls_stripe():
    """ROADMAP-010: Valid cancel calls Stripe and updates local DB status."""
    row = _sub_row()
    conn = FakeConn(fetchrow_result=row)
    db = FakeDB(conn)

    with (
        patch(DB_PATCH, new_callable=AsyncMock, return_value=db),
        patch(
            "ghl_real_estate_ai.api.routes.billing.billing_service",
        ) as mock_svc,
    ):
        mock_svc.cancel_subscription = AsyncMock(return_value={"id": "sub_stripe_abc", "status": "canceled"})

        from fastapi import BackgroundTasks

        from ghl_real_estate_ai.api.routes.billing import cancel_subscription

        bg = BackgroundTasks()
        result = await cancel_subscription(1, bg, immediate=True)

    assert result["success"] is True
    assert result["immediate"] is True
    mock_svc.cancel_subscription.assert_called_once_with("sub_stripe_abc", True)
    assert any("canceled" in str(q) for q, _ in conn.executed)


@pytest.mark.asyncio
async def test_roadmap_010_cancel_not_found_returns_404():
    """ROADMAP-010: Cancel returns 404 when subscription not in local DB."""
    conn = FakeConn(fetchrow_result=None)
    db = FakeDB(conn)

    with patch(DB_PATCH, new_callable=AsyncMock, return_value=db):
        from fastapi import BackgroundTasks, HTTPException

        from ghl_real_estate_ai.api.routes.billing import cancel_subscription

        bg = BackgroundTasks()

        with pytest.raises(HTTPException) as exc_info:
            await cancel_subscription(9999, bg, immediate=False)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# ROADMAP-011: record_usage — DB insert for usage records
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_011_usage_record_stored_in_db():
    """ROADMAP-011: record_usage inserts into usage_records + increments usage_current."""
    conn = FakeConn()
    db = FakeDB(conn)

    fake_stripe_record = MagicMock()
    fake_stripe_record.id = "si_usage_abc"

    with (
        patch(DB_PATCH, new_callable=AsyncMock, return_value=db),
        patch(
            "ghl_real_estate_ai.api.routes.billing.retry_with_exponential_backoff",
            new_callable=AsyncMock,
            return_value=fake_stripe_record,
        ),
    ):
        from fastapi import BackgroundTasks

        from ghl_real_estate_ai.api.routes.billing import record_usage
        from ghl_real_estate_ai.api.schemas.billing import UsageRecordRequest

        now = datetime.now()
        request = UsageRecordRequest(
            subscription_id=1,
            lead_id="lead_001",
            contact_id="contact_001",
            amount=Decimal("4.99"),
            tier="hot",
            billing_period_start=now,
            billing_period_end=now + timedelta(days=30),
        )
        bg = BackgroundTasks()
        result = await record_usage(request, bg)

    assert result["success"] is True
    assert result["stripe_usage_record_id"] == "si_usage_abc"

    # Verify DB INSERT into usage_records
    insert_queries = [q for q, _ in conn.executed if "INSERT INTO usage_records" in q]
    assert len(insert_queries) == 1

    # Verify usage_current was incremented
    update_queries = [q for q, _ in conn.executed if "usage_current = usage_current + 1" in q]
    assert len(update_queries) == 1


# ---------------------------------------------------------------------------
# ROADMAP-012: get_billing_history — location_id resolution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_012_resolves_location_id_from_customers():
    """ROADMAP-012: get_billing_history resolves location_id from stripe_customers."""
    customer_row = FakeRecord(
        {
            "location_id": "loc_resolved_456",
            "stripe_customer_id": "cus_stripe_xyz",
        }
    )
    conn = FakeConn(fetchrow_result=customer_row)
    db = FakeDB(conn)

    with (
        patch(DB_PATCH, new_callable=AsyncMock, return_value=db),
        patch(
            "ghl_real_estate_ai.api.routes.billing.billing_service",
        ) as mock_svc,
        patch("ghl_real_estate_ai.api.routes.billing.stripe") as mock_stripe,
    ):
        mock_svc.get_customer_invoices = AsyncMock(return_value=[])
        mock_customer = MagicMock()
        mock_customer.sources.data = []
        mock_stripe.Customer.retrieve = MagicMock(return_value=mock_customer)

        from ghl_real_estate_ai.api.routes.billing import get_billing_history

        result = await get_billing_history("cus_stripe_xyz")

    assert result.location_id == "loc_resolved_456"


@pytest.mark.asyncio
async def test_roadmap_012_fallback_when_no_customer_row():
    """ROADMAP-012: Falls back to customer_id when not in stripe_customers table."""
    conn = FakeConn(fetchrow_result=None)
    db = FakeDB(conn)

    with (
        patch(DB_PATCH, new_callable=AsyncMock, return_value=db),
        patch(
            "ghl_real_estate_ai.api.routes.billing.billing_service",
        ) as mock_svc,
        patch("ghl_real_estate_ai.api.routes.billing.stripe") as mock_stripe,
    ):
        mock_svc.get_customer_invoices = AsyncMock(return_value=[])
        mock_customer = MagicMock()
        mock_customer.sources.data = []
        mock_stripe.Customer.retrieve = MagicMock(return_value=mock_customer)

        from ghl_real_estate_ai.api.routes.billing import get_billing_history

        result = await get_billing_history("cus_unknown")

    assert result.location_id == "cus_unknown"


# ---------------------------------------------------------------------------
# ROADMAP-013: get_revenue_analytics — real DB queries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_013_revenue_analytics_from_db():
    """ROADMAP-013: get_revenue_analytics calculates MRR, churn, ARPU from DB."""
    call_count = 0

    async def _mock_fetchrow(query, *args):
        nonlocal call_count
        call_count += 1
        if "SUM(base_price)" in query:
            return FakeRecord({"mrr": Decimal("997.00"), "active_count": 5, "enterprise_count": 1})
        if "usage_records" in query:
            return FakeRecord({"usage_revenue": Decimal("150.00")})
        if "churned" in query:
            return FakeRecord({"churned": 1, "total": 20})
        if "upgrades" in query:
            return FakeRecord({"upgrades": 3, "total": 20})
        return None

    conn = FakeConn()
    conn.fetchrow = _mock_fetchrow
    db = FakeDB(conn)

    with (
        patch(DB_PATCH, new_callable=AsyncMock, return_value=db),
        patch(
            "ghl_real_estate_ai.api.routes.billing.subscription_manager",
        ) as mock_mgr,
    ):
        mock_mgr.get_tier_distribution = AsyncMock()

        from ghl_real_estate_ai.api.routes.billing import get_revenue_analytics

        result = await get_revenue_analytics()

    assert result.monthly_revenue == Decimal("997.00")
    assert result.total_arr == Decimal("997.00") * 12
    assert result.total_active_subscriptions == 5
    assert result.top_tier_customers == 1
    assert result.churn_rate == 5.0  # 1/20 * 100
    assert result.upgrade_rate == 15.0  # 3/20 * 100
    assert call_count == 4  # 4 DB queries executed


@pytest.mark.asyncio
async def test_roadmap_013_revenue_analytics_zero_subscriptions():
    """ROADMAP-013: Handles zero active subscriptions gracefully."""

    async def _mock_fetchrow(query, *args):
        if "SUM(base_price)" in query:
            return FakeRecord({"mrr": Decimal("0"), "active_count": 0, "enterprise_count": 0})
        if "usage_records" in query:
            return FakeRecord({"usage_revenue": Decimal("0")})
        if "churned" in query:
            return FakeRecord({"churned": 0, "total": 0})
        if "upgrades" in query:
            return FakeRecord({"upgrades": 0, "total": 0})
        return None

    conn = FakeConn()
    conn.fetchrow = _mock_fetchrow
    db = FakeDB(conn)

    with patch(DB_PATCH, new_callable=AsyncMock, return_value=db):
        from ghl_real_estate_ai.api.routes.billing import get_revenue_analytics

        result = await get_revenue_analytics()

    assert result.monthly_revenue == 0
    assert result.average_arpu == 0
    assert result.total_active_subscriptions == 0


# ---------------------------------------------------------------------------
# ROADMAP-014: _track_billing_event — DB insert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_014_billing_event_stored_in_db():
    """ROADMAP-014: _track_billing_event inserts into billing_analytics_events."""
    conn = FakeConn()
    db = FakeDB(conn)

    with patch(DB_PATCH, new_callable=AsyncMock, return_value=db):
        from ghl_real_estate_ai.api.routes.billing import _track_billing_event

        await _track_billing_event("subscription_created", {"subscription_id": 42})

    insert_queries = [q for q, _ in conn.executed if "billing_analytics_events" in q]
    assert len(insert_queries) == 1
    assert "INSERT INTO billing_analytics_events" in insert_queries[0]


@pytest.mark.asyncio
async def test_roadmap_014_billing_event_db_error_does_not_raise():
    """ROADMAP-014: DB error in analytics tracking does not propagate."""
    with patch(DB_PATCH, new_callable=AsyncMock, side_effect=Exception("analytics DB down")):
        from ghl_real_estate_ai.api.routes.billing import _track_billing_event

        # Should not raise — analytics failure is non-critical
        await _track_billing_event("usage_recorded", {"amount": 4.99})


# ---------------------------------------------------------------------------
# ROADMAP-015: _store_webhook_event — DB insert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_015_webhook_event_stored_in_db():
    """ROADMAP-015: _store_webhook_event inserts into billing_events table."""
    conn = FakeConn()
    db = FakeDB(conn)

    event_data = {"id": "evt_test_123", "type": "invoice.paid", "data": {"object": {}}}
    processing_result = {"processed": True, "action": "payment_recorded"}

    with patch(DB_PATCH, new_callable=AsyncMock, return_value=db):
        from ghl_real_estate_ai.api.routes.billing import _store_webhook_event

        await _store_webhook_event(event_data, processing_result)

    insert_queries = [q for q, _ in conn.executed if "billing_events" in q]
    assert len(insert_queries) == 1
    assert "INSERT INTO billing_events" in insert_queries[0]
    assert "ON CONFLICT (event_id) DO NOTHING" in insert_queries[0]


@pytest.mark.asyncio
async def test_roadmap_015_webhook_event_db_error_does_not_raise():
    """ROADMAP-015: DB error in webhook storage does not propagate."""
    event_data = {"id": "evt_fail", "type": "charge.failed"}
    processing_result = {"processed": False}

    with patch(DB_PATCH, new_callable=AsyncMock, side_effect=Exception("DB timeout")):
        from ghl_real_estate_ai.api.routes.billing import _store_webhook_event

        # Should not raise — audit failure is non-critical
        await _store_webhook_event(event_data, processing_result)
