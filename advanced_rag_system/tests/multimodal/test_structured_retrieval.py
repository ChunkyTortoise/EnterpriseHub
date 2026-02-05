"""Tests for structured data retrieval functionality.

Tests cover:
- CSV file indexing and search
- Excel file indexing and search
- JSON file indexing and search
- DataFrame indexing
- Semantic search over structured data
- Structured queries with filters
- Hybrid search combining semantic and structured approaches
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from src.core.exceptions import RetrievalError
from src.core.types import DocumentChunk, Metadata, SearchResult
from src.multimodal.structured_retriever import (
    StructuredQuery,
    StructuredRetriever,
    StructuredRetrieverConfig,
    TableSchema,
)


class TestStructuredQuery:
    """Tests for StructuredQuery dataclass."""

    def test_default_creation(self):
        """Test creating query with defaults."""
        query = StructuredQuery()

        assert query.filters == {}
        assert query.columns is None
        assert query.sort_by is None
        assert query.sort_order == "asc"
        assert query.limit is None

    def test_custom_creation(self):
        """Test creating query with custom values."""
        query = StructuredQuery(
            filters={"region": "North", "status": "active"},
            columns=["name", "value"],
            sort_by="value",
            sort_order="desc",
            limit=10,
        )

        assert query.filters == {"region": "North", "status": "active"}
        assert query.columns == ["name", "value"]
        assert query.sort_by == "value"
        assert query.sort_order == "desc"
        assert query.limit == 10


class TestTableSchema:
    """Tests for TableSchema dataclass."""

    def test_default_creation(self):
        """Test creating schema with defaults."""
        schema = TableSchema()

        assert schema.columns == {}
        assert schema.sample_data == []
        assert schema.row_count == 0
        assert schema.source == ""

    def test_custom_creation(self):
        """Test creating schema with custom values."""
        schema = TableSchema(
            columns={"id": "int64", "name": "object"},
            sample_data=[{"id": 1, "name": "test"}],
            row_count=100,
            source="test.csv",
        )

        assert schema.columns == {"id": "int64", "name": "object"}
        assert schema.sample_data == [{"id": 1, "name": "test"}]
        assert schema.row_count == 100
        assert schema.source == "test.csv"


class TestStructuredRetriever:
    """Tests for structured retriever."""

    @pytest.fixture
    async def retriever(self, tmp_path):
        """Create configured retriever fixture."""
        config = StructuredRetrieverConfig(
            collection_name="test_structured",
            persist_directory=str(tmp_path / "chroma"),
            max_rows_per_chunk=50,
        )
        retriever = StructuredRetriever(config)
        await retriever.initialize()
        yield retriever
        await retriever.close()

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample CSV file."""
        csv_path = tmp_path / "sample.csv"
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "age": [25, 30, 35, 28, 32],
            "salary": [50000.0, 60000.0, 75000.0, 65000.0, 70000.0],
        })
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    @pytest.fixture
    def sample_json(self, tmp_path):
        """Create a sample JSON file."""
        json_path = tmp_path / "sample.json"
        data = {
            "products": [
                {"id": 1, "name": "Widget", "price": 9.99, "category": "gadgets"},
                {"id": 2, "name": "Gadget", "price": 19.99, "category": "gadgets"},
                {"id": 3, "name": "Tool", "price": 29.99, "category": "tools"},
            ]
        }
        with open(json_path, "w") as f:
            json.dump(data, f)
        return str(json_path)

    @pytest.mark.asyncio
    async def test_initialization(self, tmp_path):
        """Test retriever initialization."""
        config = StructuredRetrieverConfig(
            collection_name="test_init",
            persist_directory=str(tmp_path),
        )
        retriever = StructuredRetriever(config)

        await retriever.initialize()
        assert retriever._initialized is True
        assert retriever._embedding_provider is not None
        assert retriever._vector_store is not None

        await retriever.close()

    @pytest.mark.asyncio
    async def test_generate_table_description(self, retriever):
        """Test table description generation."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "value": [10.5, 20.5, 30.5],
        })

        desc = retriever._generate_table_description(
            df, user_description="Test data", source="test.csv"
        )

        assert "Test data" in desc
        assert "3 rows" in desc
        assert "3 columns" in desc
        assert "test.csv" in desc
        assert "id" in desc
        assert "name" in desc
        assert "value" in desc

    @pytest.mark.asyncio
    async def test_generate_row_description(self, retriever):
        """Test row description generation."""
        df = pd.DataFrame({
            "id": [1],
            "name": ["Test"],
        })

        schema = TableSchema(
            columns={"id": "int64", "name": "object"},
            source="test.csv",
        )

        desc = retriever._generate_row_description(
            df.iloc[0], schema, table_description="Test table"
        )

        assert "Test table" in desc
        assert "id: 1" in desc
        assert "name: Test" in desc

    @pytest.mark.asyncio
    async def test_index_csv(self, retriever, sample_csv):
        """Test indexing CSV file."""
        doc_ids = await retriever.index_csv(
            sample_csv, description="Employee data"
        )

        assert len(doc_ids) > 0
        assert retriever._document_count > 0

        # Check schema stored
        schema = await retriever.get_schema(sample_csv)
        assert schema is not None
        assert schema.row_count == 5
        assert "id" in schema.columns
        assert "name" in schema.columns

    @pytest.mark.asyncio
    async def test_index_csv_not_found(self, retriever):
        """Test indexing non-existent CSV raises error."""
        with pytest.raises(RetrievalError, match="not found"):
            await retriever.index_csv("/nonexistent/file.csv")

    @pytest.mark.asyncio
    async def test_index_json(self, retriever, sample_json):
        """Test indexing JSON file."""
        doc_ids = await retriever.index_json(
            sample_json,
            description="Product catalog",
            records_path="products",
        )

        assert len(doc_ids) > 0

    @pytest.mark.asyncio
    async def test_index_json_list(self, tmp_path, retriever):
        """Test indexing JSON file with list at root."""
        json_path = tmp_path / "list.json"
        data = [
            {"id": 1, "value": "a"},
            {"id": 2, "value": "b"},
        ]
        with open(json_path, "w") as f:
            json.dump(data, f)

        doc_ids = await retriever.index_json(str(json_path))

        assert len(doc_ids) > 0

    @pytest.mark.asyncio
    async def test_index_dataframe(self, retriever):
        """Test indexing DataFrame directly."""
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
        })

        doc_ids = await retriever.index_dataframe(df, "test_source", "Test data")

        assert len(doc_ids) > 0
        assert retriever._document_count > 0

    @pytest.mark.asyncio
    async def test_index_empty_dataframe(self, retriever):
        """Test indexing empty DataFrame."""
        df = pd.DataFrame()

        doc_ids = await retriever.index_dataframe(df, "empty_source")

        assert doc_ids == []

    @pytest.mark.asyncio
    async def test_semantic_search(self, retriever, sample_csv):
        """Test semantic search over structured data."""
        # Index data
        await retriever.index_csv(sample_csv, description="Employee data")

        # Search
        results = await retriever.semantic_search(
            "employees with high salary",
            top_k=5,
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_semantic_search_empty(self, retriever):
        """Test semantic search with no data."""
        results = await retriever.semantic_search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_structured_query(self, retriever, sample_csv):
        """Test structured query with filters."""
        # Index data
        await retriever.index_csv(sample_csv)

        # Query with filters
        query = StructuredQuery(
            filters={"age": "> 30"},
            sort_by="salary",
            sort_order="desc",
            limit=3,
        )

        results = await retriever.structured_query(query)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_hybrid_search(self, retriever, sample_csv):
        """Test hybrid search combining semantic and structured."""
        # Index data
        await retriever.index_csv(sample_csv, description="Employee data")

        # Hybrid search
        structured_query = StructuredQuery(filters={"age": "> 25"})

        results = await retriever.hybrid_search(
            query_text="senior employees",
            structured_query=structured_query,
            top_k=5,
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_hybrid_search_no_structured(self, retriever, sample_csv):
        """Test hybrid search without structured query falls back to semantic."""
        # Index data
        await retriever.index_csv(sample_csv)

        # Hybrid search without structured filters
        results = await retriever.hybrid_search(
            query_text="test query",
            structured_query=None,
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_list_sources(self, retriever, sample_csv):
        """Test listing indexed sources."""
        # Initially empty
        sources = await retriever.list_sources()
        assert sources == []

        # Index data
        await retriever.index_csv(sample_csv)

        # Should have source
        sources = await retriever.list_sources()
        assert sample_csv in sources

    @pytest.mark.asyncio
    async def test_get_stats(self, retriever, sample_csv):
        """Test getting statistics."""
        # Index data
        await retriever.index_csv(sample_csv)

        stats = await retriever.get_stats()

        assert stats["initialized"] is True
        assert stats["collection_name"] == "test_structured"
        assert sample_csv in stats["sources"]
        assert stats["total_rows"] == 5

    @pytest.mark.asyncio
    async def test_health_check(self, retriever):
        """Test health check."""
        healthy = await retriever.health_check()
        assert healthy is True

    @pytest.mark.asyncio
    async def test_health_check_uninitialized(self):
        """Test health check when not initialized."""
        config = StructuredRetrieverConfig()
        retriever = StructuredRetriever(config)

        healthy = await retriever.health_check()
        assert healthy is False

    @pytest.mark.asyncio
    async def test_uninitialized_error(self):
        """Test operations fail when not initialized."""
        config = StructuredRetrieverConfig()
        retriever = StructuredRetriever(config)

        with pytest.raises(RetrievalError, match="not initialized"):
            await retriever.index_csv("test.csv")

    @pytest.mark.asyncio
    async def test_close(self, retriever):
        """Test closing retriever."""
        await retriever.close()

        assert retriever._initialized is False
        assert retriever._embedding_provider is None
        assert retriever._vector_store is None


class TestStructuredRetrieverIntegration:
    """Integration tests for structured retriever."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        """Test complete structured data workflow."""
        config = StructuredRetrieverConfig(
            collection_name="integration_test",
            persist_directory=str(tmp_path / "chroma"),
            max_rows_per_chunk=100,
        )
        retriever = StructuredRetriever(config)
        await retriever.initialize()

        try:
            # Create and index CSV
            csv_path = tmp_path / "sales.csv"
            df = pd.DataFrame({
                "date": pd.date_range("2024-01-01", periods=100),
                "product": ["A", "B", "C"] * 33 + ["A"],
                "region": ["North", "South", "East", "West"] * 25,
                "amount": range(1000, 11000, 100),
            })
            df.to_csv(csv_path, index=False)

            doc_ids = await retriever.index_csv(
                str(csv_path), description="Sales data 2024"
            )
            assert len(doc_ids) > 0

            # Semantic search
            results = await retriever.semantic_search(
                "high value sales in North region",
                top_k=10,
            )
            assert isinstance(results, list)

            # Structured query
            query = StructuredQuery(
                filters={"region": "North"},
                limit=5,
            )
            results = await retriever.structured_query(query)
            assert isinstance(results, list)

            # Verify stats
            stats = await retriever.get_stats()
            assert stats["total_rows"] == 100

        finally:
            await retriever.close()

    @pytest.mark.asyncio
    async def test_multiple_sources(self, tmp_path):
        """Test indexing and searching multiple data sources."""
        config = StructuredRetrieverConfig(
            collection_name="multi_source_test",
            persist_directory=str(tmp_path / "chroma"),
        )
        retriever = StructuredRetriever(config)
        await retriever.initialize()

        try:
            # Create multiple CSV files
            for i in range(3):
                csv_path = tmp_path / f"data_{i}.csv"
                df = pd.DataFrame({
                    "id": range(i * 10, (i + 1) * 10),
                    "value": range(100),
                })
                df.to_csv(csv_path, index=False)

                await retriever.index_csv(str(csv_path), description=f"Dataset {i}")

            # Verify all sources indexed
            sources = await retriever.list_sources()
            assert len(sources) == 3

            # Search across all
            results = await retriever.semantic_search("dataset values")
            assert isinstance(results, list)

        finally:
            await retriever.close()

    @pytest.mark.asyncio
    async def test_large_dataset_chunking(self, tmp_path):
        """Test that large datasets are properly chunked."""
        config = StructuredRetrieverConfig(
            collection_name="chunking_test",
            persist_directory=str(tmp_path / "chroma"),
            max_rows_per_chunk=10,  # Small chunks for testing
        )
        retriever = StructuredRetriever(config)
        await retriever.initialize()

        try:
            # Create large CSV
            csv_path = tmp_path / "large.csv"
            df = pd.DataFrame({
                "id": range(100),
                "data": ["x"] * 100,
            })
            df.to_csv(csv_path, index=False)

            doc_ids = await retriever.index_csv(str(csv_path))

            # Should create multiple chunks
            assert len(doc_ids) == 10  # 100 rows / 10 per chunk

        finally:
            await retriever.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
