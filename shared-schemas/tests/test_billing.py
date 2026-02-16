"""Tests for billing schemas."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from pydantic import ValidationError

from shared_schemas.billing import (
    BillingPlan,
    InvoiceLine,
    SubscriptionPlan,
    UsageEvent,
    UsageEventType,
    UsageRecord,
)


class TestUsageEventType:
    def test_all_types(self):
        assert UsageEventType.VOICE_MINUTE == "voice_minute"
        assert UsageEventType.RAG_QUERY == "rag_query"
        assert UsageEventType.SCRAPE_REQUEST == "scrape_request"
        assert UsageEventType.PROMPT_EVALUATION == "prompt_evaluation"
        assert UsageEventType.AGENT_INVOCATION == "agent_invocation"


class TestUsageEvent:
    def test_valid_event(self):
        e = UsageEvent(
            tenant_id="t1",
            event_type=UsageEventType.RAG_QUERY,
            quantity=1.0,
        )
        assert e.metadata == {}
        assert e.timestamp is None

    def test_zero_quantity_rejected(self):
        with pytest.raises(ValidationError):
            UsageEvent(tenant_id="t1", event_type=UsageEventType.RAG_QUERY, quantity=0)

    def test_negative_quantity_rejected(self):
        with pytest.raises(ValidationError):
            UsageEvent(tenant_id="t1", event_type=UsageEventType.RAG_QUERY, quantity=-1)

    def test_with_metadata(self):
        e = UsageEvent(
            tenant_id="t1",
            event_type=UsageEventType.VOICE_MINUTE,
            quantity=5.5,
            metadata={"call_id": "c1"},
        )
        assert e.metadata["call_id"] == "c1"


class TestBillingPlan:
    def test_valid_plan(self):
        p = BillingPlan(
            name="Pro",
            stripe_price_id="price_abc",
            features={"voice": True},
            limits={"voice_minutes": 500},
        )
        assert p.limits["voice_minutes"] == 500


class TestSubscriptionPlan:
    def test_valid_plan(self):
        p = SubscriptionPlan(
            name="Starter",
            stripe_price_id="price_xyz",
            tier="starter",
            monthly_price_cents=4900,
            included_usage={"rag_queries": 10000},
        )
        assert p.monthly_price_cents == 4900

    def test_negative_price_rejected(self):
        with pytest.raises(ValidationError):
            SubscriptionPlan(
                name="Bad", stripe_price_id="p", tier="free", monthly_price_cents=-100
            )


class TestUsageRecord:
    def test_valid_record(self):
        now = datetime.now(timezone.utc)
        r = UsageRecord(
            tenant_id=uuid4(),
            metric=UsageEventType.RAG_QUERY,
            quantity=150.0,
            period_start=now,
            period_end=now,
        )
        assert r.reported_to_stripe is False

    def test_negative_quantity_rejected(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            UsageRecord(
                tenant_id=uuid4(),
                metric=UsageEventType.RAG_QUERY,
                quantity=-1.0,
                period_start=now,
                period_end=now,
            )


class TestInvoiceLine:
    def test_valid_line(self):
        line = InvoiceLine(
            description="RAG queries (1000 @ $0.005)",
            quantity=1000,
            unit_price_cents=0,
            total_cents=500,
            metric=UsageEventType.RAG_QUERY,
        )
        assert line.total_cents == 500

    def test_no_metric(self):
        line = InvoiceLine(
            description="Platform fee",
            quantity=1,
            unit_price_cents=4900,
            total_cents=4900,
        )
        assert line.metric is None
