"""Extended billing tests — edge cases, serialization, usage events."""

from __future__ import annotations

from shared_schemas.billing import (
    InvoiceLine,
    UsageEvent,
    UsageEventType,
)


class TestUsageEvent:
    def test_create_event(self):
        evt = UsageEvent(tenant_id="t-1", event_type=UsageEventType.RAG_QUERY)
        assert evt.tenant_id == "t-1"
        assert evt.quantity == 1.0
        assert len(evt.id) == 36

    def test_unique_ids(self):
        e1 = UsageEvent(tenant_id="t", event_type=UsageEventType.VOICE_MINUTE)
        e2 = UsageEvent(tenant_id="t", event_type=UsageEventType.VOICE_MINUTE)
        assert e1.id != e2.id

    def test_all_event_types(self):
        for et in UsageEventType:
            evt = UsageEvent(tenant_id="t", event_type=et, quantity=5.0)
            assert evt.event_type == et

    def test_metadata(self):
        evt = UsageEvent(
            tenant_id="t",
            event_type=UsageEventType.MCP_CALL,
            metadata={"tool": "query_db"},
        )
        assert evt.metadata["tool"] == "query_db"

    def test_serialization(self):
        evt = UsageEvent(tenant_id="t", event_type=UsageEventType.PIPELINE_RUN, quantity=3.0)
        data = evt.model_dump()
        restored = UsageEvent(**data)
        assert restored.tenant_id == "t"
        assert restored.quantity == 3.0


class TestInvoiceLineEdgeCases:
    def test_zero_quantity(self):
        line = InvoiceLine(description="Nothing", quantity=0, unit_price_cents=100)
        assert line.total_cents == 0

    def test_large_quantity(self):
        line = InvoiceLine(description="Big", quantity=1_000_000, unit_price_cents=1)
        assert line.total_cents == 1_000_000

    def test_zero_price(self):
        line = InvoiceLine(description="Free", quantity=10, unit_price_cents=0)
        assert line.total_cents == 0


class TestUsageEventType:
    def test_rag_query(self):
        assert UsageEventType.RAG_QUERY.value == "rag_query"

    def test_voice_minute(self):
        assert UsageEventType.VOICE_MINUTE.value == "voice_minute"

    def test_mcp_call(self):
        assert UsageEventType.MCP_CALL.value == "mcp_call"

    def test_pipeline_run(self):
        assert UsageEventType.PIPELINE_RUN.value == "pipeline_run"

    def test_count(self):
        assert len(UsageEventType) == 4
