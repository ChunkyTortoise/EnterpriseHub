"""Tests for query API endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rag_service.api.queries import QueryRequest, QueryResponse, router
from rag_service.core.rag_engine import RAGResponse, SourceReference


@pytest.fixture
def app():
    """FastAPI app with query router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_rag_engine():
    """Mock RAG engine."""
    engine = AsyncMock()
    return engine


@pytest.fixture
def mock_usage_tracker():
    """Mock usage tracker."""
    tracker = AsyncMock()
    tracker.check_quota = AsyncMock(return_value=True)
    tracker.increment_queries = AsyncMock()
    return tracker


@pytest.fixture
def mock_billing_service():
    """Mock billing service."""
    billing = AsyncMock()
    billing.report_query_usage = AsyncMock()
    return billing


@pytest.fixture
def mock_audit_logger():
    """Mock audit logger."""
    logger = AsyncMock()
    logger.log = AsyncMock()
    return logger


@pytest.fixture
def client(app, mock_rag_engine, mock_usage_tracker, mock_billing_service, mock_audit_logger):
    """Test client with mocked dependencies."""
    app.state.rag_engine = mock_rag_engine
    app.state.usage_tracker = mock_usage_tracker
    app.state.billing_service = mock_billing_service
    app.state.audit_logger = mock_audit_logger
    app.state.pii_detector = None  # No PII detection by default

    # Mock middleware that sets tenant info
    @app.middleware("http")
    async def add_tenant_info(request, call_next):
        request.state.tenant_id = "tenant-123"
        request.state.tenant_tier = "pro"
        response = await call_next(request)
        return response

    return TestClient(app)


class TestQueryEndpoint:
    """Test RAG query endpoint."""

    def test_basic_query(self, client, mock_rag_engine):
        """Test basic RAG query."""
        # Arrange
        mock_rag_engine.query = AsyncMock(
            return_value=RAGResponse(
                answer="Real estate prices vary by location.",
                sources=[
                    SourceReference(
                        chunk_id="chunk1",
                        document_id="doc1",
                        content="Market analysis shows...",
                        score=0.95,
                        metadata={"source": "report.pdf"},
                    )
                ],
                query="What are real estate prices?",
                latency_ms=150,
                metadata={"expanded_queries": 1},
            )
        )

        # Act
        response = client.post(
            "/api/v1/query",
            json={
                "query": "What are real estate prices?",
                "top_k": 5,
                "expand": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Real estate prices vary by location."
        assert len(data["sources"]) == 1
        assert data["sources"][0]["chunk_id"] == "chunk1"
        assert data["latency_ms"] == 150

    def test_query_with_collection_filter(self, client, mock_rag_engine):
        """Test query with collection filter."""
        # Arrange
        collection_id = "col-456"
        mock_rag_engine.query = AsyncMock(
            return_value=RAGResponse(
                answer="Answer",
                sources=[],
                query="test",
                latency_ms=100,
            )
        )

        # Act
        response = client.post(
            "/api/v1/query",
            json={
                "query": "test query",
                "collection_id": collection_id,
                "top_k": 10,
            },
        )

        # Assert
        assert response.status_code == 200
        call_args = mock_rag_engine.query.call_args
        assert call_args.kwargs["collection_id"] == collection_id

    def test_query_with_expansion(self, client, mock_rag_engine):
        """Test query with expansion enabled."""
        # Arrange
        mock_rag_engine.query = AsyncMock(
            return_value=RAGResponse(
                answer="Answer",
                sources=[],
                query="test",
                latency_ms=100,
                metadata={"expanded_queries": 3},
            )
        )

        # Act
        response = client.post(
            "/api/v1/query",
            json={
                "query": "test query",
                "expand": True,
                "expansion_method": "multi_query",
            },
        )

        # Assert
        assert response.status_code == 200
        call_args = mock_rag_engine.query.call_args
        assert call_args.kwargs["expand"] is True
        assert call_args.kwargs["expansion_method"] == "multi_query"

    def test_query_quota_exceeded(self, client, mock_usage_tracker):
        """Test query fails when quota exceeded."""
        # Arrange
        mock_usage_tracker.check_quota = AsyncMock(return_value=False)

        # Act
        response = client.post(
            "/api/v1/query",
            json={"query": "test query"},
        )

        # Assert
        assert response.status_code == 429
        assert "Query limit exceeded" in response.json()["detail"]

    def test_query_empty_string_rejected(self, client):
        """Test that empty queries are rejected."""
        # Act
        response = client.post(
            "/api/v1/query",
            json={"query": ""},
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_query_too_long_rejected(self, client):
        """Test that overly long queries are rejected."""
        # Arrange
        long_query = "test " * 500  # > 2000 chars

        # Act
        response = client.post(
            "/api/v1/query",
            json={"query": long_query},
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_top_k_limits(self, client, mock_rag_engine):
        """Test top_k parameter validation."""
        # Arrange
        mock_rag_engine.query = AsyncMock(
            return_value=RAGResponse(answer="Answer", sources=[], query="test", latency_ms=100)
        )

        # Act - valid range
        response_valid = client.post(
            "/api/v1/query",
            json={"query": "test", "top_k": 25},
        )

        # Act - too high
        response_too_high = client.post(
            "/api/v1/query",
            json={"query": "test", "top_k": 100},
        )

        # Act - too low
        response_too_low = client.post(
            "/api/v1/query",
            json={"query": "test", "top_k": 0},
        )

        # Assert
        assert response_valid.status_code == 200
        assert response_too_high.status_code == 422
        assert response_too_low.status_code == 422

    def test_usage_tracking(
        self, client, mock_rag_engine, mock_usage_tracker, mock_billing_service
    ):
        """Test that usage is tracked and reported."""
        # Arrange
        mock_rag_engine.query = AsyncMock(
            return_value=RAGResponse(answer="Answer", sources=[], query="test", latency_ms=100)
        )

        # Act
        client.post("/api/v1/query", json={"query": "test query"})

        # Assert
        mock_usage_tracker.increment_queries.assert_called_once_with("tenant-123")
        mock_billing_service.report_query_usage.assert_called_once_with("tenant-123")

    def test_audit_logging(self, client, mock_rag_engine, mock_audit_logger):
        """Test that queries are audit logged."""
        # Arrange
        mock_rag_engine.query = AsyncMock(
            return_value=RAGResponse(
                answer="Answer",
                sources=[
                    SourceReference(
                        chunk_id="c1",
                        document_id="d1",
                        content="Content",
                        score=0.9,
                    )
                ],
                query="test",
                latency_ms=100,
            )
        )

        # Act
        client.post("/api/v1/query", json={"query": "test query"})

        # Assert
        mock_audit_logger.log.assert_called_once()
        call_args = mock_audit_logger.log.call_args
        assert call_args.kwargs["tenant_id"] == "tenant-123"
        assert call_args.kwargs["action"] == "query.execute"
        assert call_args.kwargs["resource_type"] == "query"

    def test_pii_redaction_in_query(self, client, mock_rag_engine, app):
        """Test that PII in queries is redacted."""
        # Arrange
        from rag_service.compliance.pii_detector import PIIDetector

        pii_detector = PIIDetector(use_presidio=False)
        app.state.pii_detector = pii_detector

        mock_rag_engine.query = AsyncMock(
            return_value=RAGResponse(answer="Answer", sources=[], query="test", latency_ms=100)
        )

        # Act
        client.post(
            "/api/v1/query",
            json={"query": "What is the price for john@example.com?"},
        )

        # Assert
        call_args = mock_rag_engine.query.call_args
        query_text = call_args.kwargs["query_text"]
        # Email should be redacted
        assert "john@example.com" not in query_text
        assert "[EMAIL]" in query_text


class TestQueryStreamEndpoint:
    """Test streaming query endpoint."""

    def test_stream_query(self, client, mock_rag_engine, mock_usage_tracker):
        """Test streaming RAG query."""

        # Arrange
        async def mock_stream(**kwargs):
            yield "This "
            yield "is "
            yield "streamed "
            yield "response"

        mock_rag_engine.query_stream = mock_stream

        # Act
        response = client.post(
            "/api/v1/query/stream",
            json={"query": "test query", "top_k": 5},
        )

        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        # Check streaming content
        content = response.text
        assert "data: This " in content
        assert "data: [DONE]" in content

    def test_stream_quota_check(self, client, mock_usage_tracker):
        """Test that streaming also checks quota."""
        # Arrange
        mock_usage_tracker.check_quota = AsyncMock(return_value=False)

        # Act
        response = client.post(
            "/api/v1/query/stream",
            json={"query": "test query"},
        )

        # Assert
        assert response.status_code == 429

    def test_stream_usage_tracking(self, client, mock_rag_engine, mock_usage_tracker):
        """Test that streaming queries are tracked."""

        # Arrange
        async def mock_stream(**kwargs):
            yield "response"

        mock_rag_engine.query_stream = mock_stream

        # Act
        client.post("/api/v1/query/stream", json={"query": "test"})

        # Assert
        mock_usage_tracker.increment_queries.assert_called_once()


class TestQueryModels:
    """Test Pydantic models."""

    def test_query_request_defaults(self):
        """Test QueryRequest default values."""
        req = QueryRequest(query="test")

        assert req.query == "test"
        assert req.collection_id is None
        assert req.top_k == 5
        assert req.expand is True
        assert req.expansion_method == "multi_query"

    def test_query_response_creation(self):
        """Test QueryResponse model."""
        from rag_service.api.queries import SourceInfo

        resp = QueryResponse(
            answer="Test answer",
            sources=[
                SourceInfo(
                    chunk_id="c1",
                    document_id="d1",
                    content="Content",
                    score=0.95,
                )
            ],
            query="test query",
            latency_ms=150,
            metadata={"key": "value"},
        )

        assert resp.answer == "Test answer"
        assert len(resp.sources) == 1
        assert resp.latency_ms == 150
        assert resp.metadata["key"] == "value"
