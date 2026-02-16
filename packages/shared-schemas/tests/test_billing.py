"""Tests for billing schemas."""

from shared_schemas.billing import BillingInterval, InvoiceLine, SubscriptionPlan, UsageRecord
from shared_schemas.tenant import TenantLimits, TenantTier


class TestBillingInterval:
    def test_intervals(self):
        assert BillingInterval.MONTHLY == "MONTHLY"
        assert BillingInterval.YEARLY == "YEARLY"


class TestSubscriptionPlan:
    def test_create_plan(self):
        plan = SubscriptionPlan(
            id="plan-1",
            name="Pro Monthly",
            stripe_price_id="price_abc123",
            tier=TenantTier.PRO,
            interval=BillingInterval.MONTHLY,
            price_cents=4900,
            features=["Priority support", "10K queries/day"],
            limits=TenantLimits(max_users=25, max_queries_per_day=10_000, max_storage_gb=100.0, max_api_keys=10),
        )
        assert plan.price_cents == 4900
        assert plan.tier == TenantTier.PRO
        assert len(plan.features) == 2

    def test_plan_serialization(self):
        plan = SubscriptionPlan(
            id="plan-2",
            name="Free",
            stripe_price_id="price_free",
            tier=TenantTier.FREE,
            interval=BillingInterval.MONTHLY,
            price_cents=0,
            limits=TenantLimits(),
        )
        data = plan.model_dump()
        assert data["tier"] == "FREE"
        restored = SubscriptionPlan(**data)
        assert restored.id == plan.id


class TestUsageRecord:
    def test_create_record(self):
        record = UsageRecord(tenant_id="t-1", metric="api_calls", quantity=150.0)
        assert record.tenant_id == "t-1"
        assert record.reported_to_stripe is False
        assert record.stripe_subscription_item_id is None
        assert len(record.id) == 36

    def test_record_with_stripe_item(self):
        record = UsageRecord(
            tenant_id="t-1",
            metric="tokens",
            quantity=50000.0,
            stripe_subscription_item_id="si_abc",
            reported_to_stripe=True,
        )
        assert record.reported_to_stripe is True
        assert record.stripe_subscription_item_id == "si_abc"

    def test_unique_ids(self):
        r1 = UsageRecord(tenant_id="t-1", metric="m", quantity=1.0)
        r2 = UsageRecord(tenant_id="t-1", metric="m", quantity=1.0)
        assert r1.id != r2.id


class TestInvoiceLine:
    def test_total_cents_computed(self):
        line = InvoiceLine(description="API calls", quantity=100.0, unit_price_cents=5)
        assert line.total_cents == 500

    def test_fractional_quantity(self):
        line = InvoiceLine(description="Storage GB", quantity=2.5, unit_price_cents=100)
        assert line.total_cents == 250

    def test_default_currency(self):
        line = InvoiceLine(description="Test", quantity=1, unit_price_cents=100)
        assert line.currency == "USD"

    def test_custom_currency(self):
        line = InvoiceLine(description="Test", quantity=1, unit_price_cents=100, currency="EUR")
        assert line.currency == "EUR"

    def test_serialization_includes_computed(self):
        line = InvoiceLine(description="X", quantity=3.0, unit_price_cents=200)
        data = line.model_dump()
        assert data["total_cents"] == 600
