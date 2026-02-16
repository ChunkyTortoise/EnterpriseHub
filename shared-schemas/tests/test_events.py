"""Tests for domain events."""

from uuid import UUID
from datetime import datetime

from shared_schemas.events import (
    BillingEvent,
    DomainEvent,
    TenantCreated,
    UsageThresholdReached,
)


class TestDomainEvent:
    def test_base_event(self):
        e = DomainEvent(tenant_id="t1")
        assert isinstance(e.event_id, UUID)
        assert isinstance(e.timestamp, datetime)
        assert e.metadata == {}

    def test_metadata_preserved(self):
        e = DomainEvent(tenant_id="t1", metadata={"source": "test"})
        assert e.metadata["source"] == "test"


class TestTenantCreated:
    def test_event_type(self):
        e = TenantCreated(
            tenant_id="t1",
            tenant_name="Acme Corp",
            tier="pro",
            email="admin@acme.com",
        )
        assert e.event_type == "TenantCreated"
        assert e.tenant_name == "Acme Corp"

    def test_serialization(self):
        e = TenantCreated(
            tenant_id="t1", tenant_name="Test", tier="free", email="t@t.com"
        )
        d = e.model_dump()
        assert d["event_type"] == "TenantCreated"
        assert d["tenant_name"] == "Test"


class TestBillingEvent:
    def test_billing_event(self):
        e = BillingEvent(
            tenant_id="t1",
            action="subscription_created",
            stripe_event_id="evt_123",
            amount_cents=4900,
        )
        assert e.event_type == "BillingEvent"
        assert e.amount_cents == 4900

    def test_optional_fields(self):
        e = BillingEvent(tenant_id="t1", action="payment_failed")
        assert e.stripe_event_id is None
        assert e.amount_cents is None


class TestUsageThresholdReached:
    def test_threshold_event(self):
        e = UsageThresholdReached(
            tenant_id="t1",
            metric="rag_query",
            current_usage=900,
            limit=1000,
            percentage=90.0,
        )
        assert e.event_type == "UsageThresholdReached"
        assert e.percentage == 90.0
