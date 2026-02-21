"""Tests for multi-tenant schema management."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from rag_service.multi_tenant.schema_manager import SchemaManager


def make_engine_with_conn(mock_conn=None):
    """Create a mock engine with proper async context manager for begin()."""
    if mock_conn is None:
        mock_conn = AsyncMock()

    @asynccontextmanager
    async def fake_begin():
        yield mock_conn

    engine = MagicMock()
    engine.begin = fake_begin
    return engine, mock_conn


@pytest.fixture
def mock_conn():
    """Shared mock connection."""
    return AsyncMock()


@pytest.fixture
def mock_engine(mock_conn):
    """Mock database engine with async context manager."""
    engine, _ = make_engine_with_conn(mock_conn)
    return engine


@pytest.fixture
def schema_manager(mock_engine):
    """Schema manager with mock engine."""
    return SchemaManager(engine=mock_engine)


class TestSchemaManager:
    """Test tenant schema creation and management."""

    async def test_create_tenant_schema(self, schema_manager, mock_conn):
        """Test creating a new tenant schema with all tables."""
        # Act
        schema_name = await schema_manager.create_tenant_schema("acme-corp")

        # Assert
        assert schema_name == "tenant_acme-corp"
        calls = [str(call) for call in mock_conn.execute.call_args_list]
        assert any("CREATE SCHEMA" in c for c in calls)
        assert mock_conn.execute.call_count >= 4

    async def test_create_schema_with_vector_column(self, schema_manager, mock_conn):
        """Test that vector column is added if pgvector available."""
        # Act
        await schema_manager.create_tenant_schema("test-tenant")

        # Assert
        calls = [str(call) for call in mock_conn.execute.call_args_list]
        assert any("embedding vector" in c.lower() for c in calls)

    async def test_create_schema_handles_missing_pgvector(self, mock_engine):
        """Test graceful handling when pgvector extension missing."""
        # Arrange
        mock_conn = AsyncMock()

        async def execute_side_effect(sql, *args, **kwargs):
            if "vector(" in str(sql):
                raise Exception("pgvector extension not available")

        mock_conn.execute = AsyncMock(side_effect=execute_side_effect)
        engine, _ = make_engine_with_conn(mock_conn)
        manager = SchemaManager(engine=engine)

        # Act - should not raise exception
        schema_name = await manager.create_tenant_schema("test-tenant")

        # Assert
        assert schema_name == "tenant_test-tenant"

    async def test_delete_tenant_schema(self, schema_manager, mock_conn):
        """Test deleting a tenant schema."""
        # Act
        await schema_manager.delete_tenant_schema("delete-me")

        # Assert
        calls = [str(call) for call in mock_conn.execute.call_args_list]
        assert any("DROP SCHEMA" in c for c in calls)
        assert any("tenant_delete-me" in c for c in calls)
        assert any("CASCADE" in c for c in calls)

    async def test_run_migrations(self, schema_manager, mock_conn):
        """Test running migrations on existing schema."""
        # Act
        await schema_manager.run_migrations("tenant_existing")

        # Assert
        assert mock_conn.execute.call_count >= 4

    async def test_list_tenant_schemas(self):
        """Test listing all tenant schemas."""
        # Arrange
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall = MagicMock(
            return_value=[
                ("tenant_acme",),
                ("tenant_globex",),
                ("tenant_initech",),
            ]
        )
        mock_conn.execute = AsyncMock(return_value=mock_result)
        engine, _ = make_engine_with_conn(mock_conn)
        manager = SchemaManager(engine=engine)

        # Act
        schemas = await manager.list_tenant_schemas()

        # Assert
        assert len(schemas) == 3
        assert "tenant_acme" in schemas
        assert "tenant_globex" in schemas
        assert "tenant_initech" in schemas

    async def test_list_schemas_empty(self):
        """Test listing schemas when none exist."""
        # Arrange
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall = MagicMock(return_value=[])
        mock_conn.execute = AsyncMock(return_value=mock_result)
        engine, _ = make_engine_with_conn(mock_conn)
        manager = SchemaManager(engine=engine)

        # Act
        schemas = await manager.list_tenant_schemas()

        # Assert
        assert schemas == []

    async def test_schema_name_sanitization(self, schema_manager, mock_conn):
        """Test that schema names are properly sanitized."""
        # Act
        schema_name = await schema_manager.create_tenant_schema("my-company-123")

        # Assert
        assert schema_name == "tenant_my-company-123"

    async def test_no_engine_returns_empty_list(self):
        """Test that listing schemas without engine returns empty."""
        manager = SchemaManager(engine=None)
        schemas = await manager.list_tenant_schemas()
        assert schemas == []


class TestSchemaManagerSQL:
    """Test SQL template generation."""

    def test_collections_table_sql(self):
        """Test collections table SQL includes required columns."""
        sql = SchemaManager.TENANT_TABLES_SQL[0]
        assert "collections" in sql
        assert "id UUID" in sql
        assert "name" in sql
        assert "document_count" in sql
        assert "metadata JSONB" in sql

    def test_documents_table_sql(self):
        """Test documents table SQL includes required columns."""
        sql = SchemaManager.TENANT_TABLES_SQL[1]
        assert "documents" in sql
        assert "collection_id UUID" in sql
        assert "filename" in sql
        assert "content_type" in sql
        assert "size_bytes" in sql
        assert "chunk_count" in sql

    def test_chunks_table_sql(self):
        """Test chunks table SQL includes required columns."""
        sql = SchemaManager.TENANT_TABLES_SQL[2]
        assert "chunks" in sql
        assert "document_id UUID" in sql
        assert "content TEXT" in sql
        assert "chunk_index INT" in sql
        assert "ON DELETE CASCADE" in sql

    def test_query_logs_table_sql(self):
        """Test query logs table SQL includes required columns."""
        sql = SchemaManager.TENANT_TABLES_SQL[3]
        assert "query_logs" in sql
        assert "query_text" in sql
        assert "answer_text" in sql
        assert "latency_ms" in sql

    def test_vector_column_sql(self):
        """Test vector column SQL template."""
        sql = SchemaManager.VECTOR_COLUMN_SQL
        assert "embedding vector(1536)" in sql
        assert "{schema}" in sql

    def test_vector_index_sql(self):
        """Test vector index SQL template."""
        sql = SchemaManager.VECTOR_INDEX_SQL
        assert "ivfflat" in sql
        assert "vector_cosine_ops" in sql
        assert "{schema}" in sql
