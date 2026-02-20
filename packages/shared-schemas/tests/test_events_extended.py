"""Extended event tests — domain events, serialization, edge cases."""

from __future__ import annotations

from datetime import datetime

from shared_schemas.events import (
    DomainEvent,
    SubscriptionChanged,
    TenantCreated,
    UsageLimitReached,
)
from shared_schemas.tenant import TenantTier


class TestDomainEvent:
    def test_create_base_event(self):
        evt = DomainEvent(event_type="test.event", tenant_id="t-1")
        assert evt.event_type == "test.event"
        assert evt.tenant_id == "t-1"
        assert len(evt.event_id) == 36

    def test_unique_event_ids(self):
        e1 = DomainEvent(event_type="a", tenant_id="t")
        e2 = DomainEvent(event_type="a", tenant_id="t")
        assert e1.event_id != e2.event_id

    def test_default_timestamp(self):
        evt = DomainEvent(event_type="a", tenant_id="t")
        assert isinstance(evt.timestamp, datetime)

    def test_custom_payload(self):
        evt = DomainEvent(
            event_type="custom",
            tenant_id="t",
            payload={"key": "value", "count": 42},
        )
        assert evt.payload["key"] == "value"
        assert evt.payload["count"] == 42

    def test_serialization(self):
        evt = DomainEvent(event_type="test", tenant_id="t-1", payload={"x": 1})
        data = evt.model_dump()
        restored = DomainEvent(**data)
        assert restored.event_type == "test"
        assert restored.payload["x"] == 1


class TestTenantCreated:
    def test_default_event_type(self):
        evt = TenantCreated(tenant_id="t-new")
        assert evt.event_type == "tenant.created"

    def test_serialization(self):
        evt = TenantCreated(tenant_id="t-1")
        data = evt.model_dump()
        assert data["event_type"] == "tenant.created"


class TestSubscriptionChanged:
    def test_tracks_old_and_new_tier(self):
        evt = SubscriptionChanged(
            tenant_id="t-1",
            old_tier=TenantTier.FREE,
            new_tier=TenantTier.PRO,
        )
        assert evt.old_tier == TenantTier.FREE
        assert evt.new_tier == TenantTier.PRO
        assert evt.event_type == "subscription.changed"

    def test_serialization(self):
        evt = SubscriptionChanged(
            tenant_id="t-1",
            old_tier=TenantTier.STARTER,
            new_tier=TenantTier.ENTERPRISE,
        )
        data = evt.model_dump()
        assert data["old_tier"] == "STARTER"
        assert data["new_tier"] == "ENTERPRISE"


class TestUsageLimitReached:
    def test_tracks_metric_and_value(self):
        evt = UsageLimitReached(
            tenant_id="t-1",
            metric="api_calls",
            current_value=10_000,
        )
        assert evt.metric == "api_calls"
        assert evt.current_value == 10_000
        assert evt.event_type == "usage.limit_reached"

    def test_zero_value(self):
        evt = UsageLimitReached(tenant_id="t", metric="storage", current_value=0)
        assert evt.current_value == 0
