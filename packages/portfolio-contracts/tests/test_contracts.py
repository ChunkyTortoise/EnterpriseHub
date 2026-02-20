"""Tests for portfolio-contracts shared types."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from portfolio_contracts import (
    AgentAction,
    AgentStatus,
    APIError,
    CostEstimate,
    DocumentChunk,
    DocumentMetadata,
    DocumentType,
    ErrorDetail,
    LLMProvider,
    LLMResponse,
    PaginationMeta,
    TokenUsage,
)

# ---------------------------------------------------------------------------
# LLM contracts
# ---------------------------------------------------------------------------


class TestLLMProvider:
    def test_all_providers(self):
        assert LLMProvider.ANTHROPIC == "anthropic"
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.GOOGLE == "google"
        assert LLMProvider.MOCK == "mock"

    def test_from_string(self):
        assert LLMProvider("anthropic") is LLMProvider.ANTHROPIC


class TestTokenUsage:
    def test_defaults(self):
        usage = TokenUsage()
        assert usage.input_tokens == 0
        assert usage.total_tokens == 0

    def test_total_computed(self):
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150

    def test_cache_tokens(self):
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            cache_creation_tokens=20,
            cache_read_tokens=80,
        )
        assert usage.total_tokens == 150
        assert usage.cache_creation_tokens == 20

    def test_serialization(self):
        usage = TokenUsage(input_tokens=10, output_tokens=20)
        data = usage.model_dump()
        assert data["total_tokens"] == 30
        restored = TokenUsage.model_validate(data)
        assert restored.input_tokens == 10


class TestCostEstimate:
    def test_total_computed(self):
        cost = CostEstimate(input_cost=0.01, output_cost=0.03)
        assert cost.total_cost == pytest.approx(0.04)
        assert cost.currency == "USD"

    def test_json_round_trip(self):
        cost = CostEstimate(input_cost=0.005, output_cost=0.015)
        raw = cost.model_dump_json()
        restored = CostEstimate.model_validate_json(raw)
        assert restored.total_cost == pytest.approx(0.02)


class TestLLMResponse:
    def test_minimal(self):
        resp = LLMResponse(
            content="Hello",
            provider=LLMProvider.ANTHROPIC,
            model="claude-opus-4-6",
        )
        assert resp.content == "Hello"
        assert resp.usage is None
        assert resp.elapsed_ms == 0.0
        assert resp.metadata == {}

    def test_full(self):
        resp = LLMResponse(
            content="Answer",
            provider=LLMProvider.GOOGLE,
            model="gemini-2.0-flash",
            usage=TokenUsage(input_tokens=50, output_tokens=100),
            cost=CostEstimate(input_cost=0.001, output_cost=0.003),
            finish_reason="stop",
            tool_calls=[{"name": "search", "args": {}}],
            elapsed_ms=234.5,
            metadata={"request_id": "abc"},
        )
        assert resp.usage.total_tokens == 150
        assert resp.cost.total_cost == pytest.approx(0.004)
        assert resp.finish_reason == "stop"
        assert len(resp.tool_calls) == 1

    def test_json_round_trip(self):
        resp = LLMResponse(
            content="test",
            provider="anthropic",
            model="claude-opus-4-6",
            usage=TokenUsage(input_tokens=10, output_tokens=20),
        )
        raw = resp.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["provider"] == "anthropic"
        assert parsed["usage"]["total_tokens"] == 30
        restored = LLMResponse.model_validate_json(raw)
        assert restored.content == "test"

    def test_provider_string_coercion(self):
        resp = LLMResponse(content="x", provider="mock", model="test")
        assert resp.provider is LLMProvider.MOCK


# ---------------------------------------------------------------------------
# Document contracts
# ---------------------------------------------------------------------------


class TestDocumentType:
    def test_all_types(self):
        assert DocumentType.PDF == "pdf"
        assert DocumentType.CSV == "csv"
        assert DocumentType.DOCX == "docx"


class TestDocumentChunk:
    def test_defaults(self):
        chunk = DocumentChunk(content="Hello world")
        assert chunk.id  # auto-generated UUID
        assert chunk.chunk_index == 0
        assert chunk.embedding is None
        assert chunk.metadata == {}

    def test_with_embedding(self):
        chunk = DocumentChunk(
            content="test",
            doc_id="doc-1",
            chunk_index=3,
            embedding=[0.1, 0.2, 0.3],
        )
        assert chunk.embedding == [0.1, 0.2, 0.3]
        assert chunk.doc_id == "doc-1"

    def test_unique_ids(self):
        a = DocumentChunk(content="a")
        b = DocumentChunk(content="b")
        assert a.id != b.id


class TestDocumentMetadata:
    def test_defaults(self):
        meta = DocumentMetadata()
        assert meta.language == "en"
        assert meta.doc_type == DocumentType.TEXT
        assert meta.source is None

    def test_extra_fields_allowed(self):
        meta = DocumentMetadata(source="file.pdf", custom_tag="important")
        assert meta.source == "file.pdf"
        assert meta.model_extra.get("custom_tag") == "important"

    def test_with_datetime(self):
        now = datetime.now(timezone.utc)
        meta = DocumentMetadata(created_at=now, doc_type=DocumentType.PDF)
        assert meta.created_at == now


# ---------------------------------------------------------------------------
# API contracts
# ---------------------------------------------------------------------------


class TestAPIError:
    def test_simple(self):
        err = APIError(error="not_found", message="Resource not found", status_code=404)
        assert err.status_code == 404
        assert err.details == []

    def test_with_details(self):
        err = APIError(
            error="validation_error",
            message="Invalid input",
            details=[
                ErrorDetail(code="required", message="Field is required", field="name"),
            ],
            status_code=422,
        )
        assert len(err.details) == 1
        assert err.details[0].field == "name"


class TestPaginationMeta:
    def test_has_more_true(self):
        meta = PaginationMeta(total=100, limit=10, offset=0)
        assert meta.has_more is True

    def test_has_more_false(self):
        meta = PaginationMeta(total=10, limit=10, offset=0)
        assert meta.has_more is False

    def test_last_page(self):
        meta = PaginationMeta(total=25, limit=10, offset=20)
        assert meta.has_more is False


# ---------------------------------------------------------------------------
# Agent contracts
# ---------------------------------------------------------------------------


class TestAgentAction:
    def test_defaults(self):
        action = AgentAction(agent_id="agent-1", action_type="search")
        assert action.action_id  # auto-generated
        assert action.status == AgentStatus.IDLE
        assert action.input_data == {}
        assert action.output_data is None
        assert action.error is None

    def test_full_lifecycle(self):
        now = datetime.now(timezone.utc)
        action = AgentAction(
            agent_id="agent-1",
            action_type="query",
            input_data={"q": "test"},
            output_data={"result": "found"},
            status=AgentStatus.COMPLETED,
            started_at=now,
            completed_at=now,
        )
        assert action.status == AgentStatus.COMPLETED
        assert action.output_data["result"] == "found"

    def test_json_round_trip(self):
        action = AgentAction(
            agent_id="a1",
            action_type="tool_call",
            status=AgentStatus.RUNNING,
        )
        raw = action.model_dump_json()
        restored = AgentAction.model_validate_json(raw)
        assert restored.agent_id == "a1"
        assert restored.status is AgentStatus.RUNNING


class TestAgentStatus:
    def test_all_statuses(self):
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.RUNNING == "running"
        assert AgentStatus.COMPLETED == "completed"
        assert AgentStatus.FAILED == "failed"
        assert AgentStatus.CANCELLED == "cancelled"
