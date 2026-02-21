"""Shared pytest fixtures for all tests."""

from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def sample_tenant():
    """Sample tenant data."""
    return {
        "id": "tenant-123",
        "slug": "acme-corp",
        "name": "Acme Corporation",
        "email": "admin@acme.com",
        "status": "active",
        "tier": "pro",
        "schema_name": "tenant_acme-corp",
    }


@pytest.fixture
def sample_api_key():
    """Sample API key."""
    return "rag_test_key_12345678901234567890"


@pytest.fixture
def sample_document():
    """Sample document data."""
    return {
        "id": "doc-123",
        "collection_id": "col-456",
        "filename": "test_document.pdf",
        "content_type": "application/pdf",
        "size_bytes": 102400,
        "chunk_count": 10,
        "storage_key": "s3://bucket/doc-123.pdf",
        "metadata": {"author": "John Doe", "pages": 25},
    }


@pytest.fixture
def sample_collection():
    """Sample collection data."""
    return {
        "id": "col-123",
        "name": "Test Collection",
        "description": "A collection for testing",
        "document_count": 5,
        "metadata": {"category": "technical"},
    }


@pytest.fixture
def sample_chunk():
    """Sample document chunk."""
    return {
        "id": "chunk-123",
        "document_id": "doc-456",
        "content": "This is a sample text chunk for testing retrieval.",
        "chunk_index": 0,
        "metadata": {"page": 1},
    }


@pytest.fixture
def sample_query():
    """Sample RAG query."""
    return {
        "query_text": "What are the real estate market trends?",
        "collection_id": None,
        "top_k": 5,
        "expand": True,
    }
