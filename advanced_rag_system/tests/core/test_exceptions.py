"""Tests for core exceptions."""

import pytest
from src.core.exceptions import (
    CacheError,
    ConfigurationError,
    DuplicateError,
    EmbeddingError,
    NotFoundError,
    RAGException,
    RateLimitError,
    VectorStoreError,
)


class TestRAGException:
    """Test cases for base RAGException."""

    def test_basic_creation(self) -> None:
        """Test creating basic exception."""
        exc = RAGException("Test message")
        assert exc.message == "Test message"
        assert exc.error_code == "RAG_ERROR"
        assert str(exc) == "[RAG_ERROR] Test message"

    def test_with_details(self) -> None:
        """Test exception with details."""
        exc = RAGException(
            "Test message",
            details={"key": "value"},
            error_code="CUSTOM_ERROR",
        )
        assert exc.error_code == "CUSTOM_ERROR"
        assert exc.details == {"key": "value"}
        assert "key" in str(exc)

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        exc = RAGException(
            "Test",
            details={"foo": "bar"},
            error_code="TEST",
        )
        result = exc.to_dict()
        assert result["message"] == "Test"
        assert result["error_code"] == "TEST"
        assert result["details"] == {"foo": "bar"}


class TestConfigurationError:
    """Test cases for ConfigurationError."""

    def test_creation(self) -> None:
        """Test configuration error creation."""
        exc = ConfigurationError("Missing config")
        assert exc.error_code == "CONFIG_ERROR"
        assert "Missing config" in str(exc)


class TestEmbeddingError:
    """Test cases for EmbeddingError."""

    def test_creation(self) -> None:
        """Test embedding error creation."""
        exc = EmbeddingError(
            "API failed",
            provider="openai",
            details={"retry_count": 3},
        )
        assert exc.error_code == "EMBEDDING_ERROR"
        assert exc.provider == "openai"


class TestVectorStoreError:
    """Test cases for VectorStoreError."""

    def test_creation(self) -> None:
        """Test vector store error creation."""
        exc = VectorStoreError(
            "Connection failed",
            store_type="chroma",
        )
        assert exc.error_code == "VECTOR_STORE_ERROR"
        assert exc.store_type == "chroma"


class TestCacheError:
    """Test cases for CacheError."""

    def test_creation(self) -> None:
        """Test cache error creation."""
        exc = CacheError(
            "Redis connection failed",
            cache_layer="L2",
        )
        assert exc.error_code == "CACHE_ERROR"
        assert exc.cache_layer == "L2"


class TestRateLimitError:
    """Test cases for RateLimitError."""

    def test_creation(self) -> None:
        """Test rate limit error creation."""
        exc = RateLimitError(
            "Too many requests",
            retry_after=60,
        )
        assert exc.error_code == "RATE_LIMIT_ERROR"
        assert exc.retry_after == 60


class TestNotFoundError:
    """Test cases for NotFoundError."""

    def test_creation(self) -> None:
        """Test not found error creation."""
        exc = NotFoundError(
            "Document not found",
            resource_type="document",
            resource_id="doc-123",
        )
        assert exc.error_code == "NOT_FOUND"
        assert exc.resource_type == "document"
        assert exc.resource_id == "doc-123"


class TestDuplicateError:
    """Test cases for DuplicateError."""

    def test_creation(self) -> None:
        """Test duplicate error creation."""
        exc = DuplicateError(
            "Document already exists",
            resource_type="document",
            resource_id="doc-123",
        )
        assert exc.error_code == "DUPLICATE_ERROR"
        assert exc.resource_type == "document"
        assert exc.resource_id == "doc-123"
