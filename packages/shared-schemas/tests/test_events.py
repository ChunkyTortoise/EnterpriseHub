"""Tests for domain event schemas."""

from shared_schemas.events import DomainEvent, SubscriptionChanged, TenantCreated, UsageLimitReached
from shared_schemas.tenant import TenantTier


class TestDomainEvent:
    def test_create_event(self):
        event = DomainEvent(event_type="test.event", tenant_id="t-1")
        assert event.event_type == "test.event"
        assert event.tenant_id == "t-1"
        assert event.payload == {}
        assert len(event.event_id) == 36

    def test_event_with_payload(self):
        event = DomainEvent(event_type="custom", tenant_id="t-1", payload={"key": "value"})
        assert event.payload["key"] == "value"


class TestTenantCreated:
    def test_default_event_type(self):
        event = TenantCreated(tenant_id="t-new")
        assert event.event_type == "tenant.created"

    def test_payload_passthrough(self):
        event = TenantCreated(tenant_id="t-1", payload={"plan": "pro"})
        assert event.payload["plan"] == "pro"


class TestSubscriptionChanged:
    def test_tier_change(self):
        event = SubscriptionChanged(
            tenant_id="t-1",
            old_tier=TenantTier.FREE,
            new_tier=TenantTier.PRO,
        )
        assert event.event_type == "subscription.changed"
        assert event.old_tier == TenantTier.FREE
        assert event.new_tier == TenantTier.PRO

    def test_serialization(self):
        event = SubscriptionChanged(
            tenant_id="t-1",
            old_tier=TenantTier.STARTER,
            new_tier=TenantTier.ENTERPRISE,
        )
        data = event.model_dump()
        assert data["old_tier"] == "STARTER"
        assert data["new_tier"] == "ENTERPRISE"


class TestUsageLimitReached:
    def test_limit_event(self):
        event = UsageLimitReached(
            tenant_id="t-1",
            metric="api_calls",
            current_value=10001.0,
        )
        assert event.event_type == "usage.limit_reached"
        assert event.metric == "api_calls"
        assert event.current_value == 10001.0
