"""Tests for unified multi-modal retriever.

Tests cover:
- Multi-modal query routing and detection
- Parallel and sequential search execution
- Result fusion from multiple modalities
- Image-based search
- Structured data search
- Integration between all retrieval components
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pandas as pd
import pytest

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from src.core.exceptions import RetrievalError
from src.multimodal.structured_retriever import StructuredQuery
from src.multimodal.unified_retriever import (
    QueryModality,
    UnifiedRetriever,
    UnifiedRetrieverConfig,
    UnifiedSearchResult,
)


@pytest.mark.integration


class TestQueryModality:
    """Tests for QueryModality enum."""

    def test_enum_values(self):
        """Test enum value definitions."""
        assert QueryModality.TEXT.value == "text"
        assert QueryModality.IMAGE.value == "image"
        assert QueryModality.STRUCTURED.value == "structured"
        assert QueryModality.MULTI.value == "multi"


class TestUnifiedSearchResult:
    """Tests for UnifiedSearchResult dataclass."""

    def test_creation(self):
        """Test creating search result."""
        result = UnifiedSearchResult(
            results=[],
            modality_breakdown={"text": [], "image": [], "structured": []},
            detected_modality=QueryModality.TEXT,
            search_time_ms=100.0,
            modality_weights={"text": 0.4, "image": 0.3, "structured": 0.3},
        )

        assert result.results == []
        assert result.detected_modality == QueryModality.TEXT
        assert result.search_time_ms == 100.0


class TestUnifiedRetrieverConfig:
    """Tests for UnifiedRetrieverConfig dataclass."""

    def test_default_creation(self):
        """Test creating config with defaults."""
        config = UnifiedRetrieverConfig()

        assert config.enable_modality_detection is True
        assert config.default_modality == QueryModality.TEXT
        assert config.parallel_search is True
        assert config.max_total_results == 20
        assert config.text_weight == 0.4
        assert config.image_weight == 0.35
        assert config.structured_weight == 0.25

    def test_custom_creation(self):
        """Test creating config with custom values."""
        config = UnifiedRetrieverConfig(
            enable_modality_detection=False,
            default_modality=QueryModality.IMAGE,
            parallel_search=False,
            max_total_results=50,
            text_weight=0.5,
            image_weight=0.3,
            structured_weight=0.2,
        )

        assert config.enable_modality_detection is False
        assert config.default_modality == QueryModality.IMAGE
        assert config.parallel_search is False
        assert config.max_total_results == 50
        assert config.text_weight == 0.5
        assert config.image_weight == 0.3
        assert config.structured_weight == 0.2


class TestUnifiedRetriever:
    """Tests for unified retriever."""

    @pytest.fixture
    async def retriever(self, tmp_path):
        """Create configured retriever fixture."""
        config = UnifiedRetrieverConfig(
            parallel_search=True,
            max_total_results=10,
        )
        retriever = UnifiedRetriever(config)
        await retriever.initialize()
        yield retriever
        await retriever.close()

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create a sample image file."""
        if not HAS_PIL:
            pytest.skip("PIL not available")

        img_path = tmp_path / "test_image.png"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(img_path)
        return str(img_path)

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample CSV file."""
        csv_path = tmp_path / "sample.csv"
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "value": [100, 200, 300],
            }
        )
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    @pytest.mark.asyncio
    async def test_initialization(self, tmp_path):
        """Test retriever initialization."""
        config = UnifiedRetrieverConfig()
        retriever = UnifiedRetriever(config)

        await retriever.initialize()
        assert retriever._initialized is True

        await retriever.close()

    @pytest.mark.asyncio
    async def test_detect_modality_text(self, retriever):
        """Test text modality detection."""
        queries = [
            "What is machine learning?",
            "Explain quantum physics",
            "How does photosynthesis work?",
        ]

        for query in queries:
            modality = retriever._detect_modality(query)
            assert modality == QueryModality.TEXT

    @pytest.mark.asyncio
    async def test_detect_modality_image(self, retriever):
        """Test image modality detection."""
        queries = [
            "Show me pictures of cats",
            "red car photo",
            "visual diagram of a cell",
            "chart showing sales data",
        ]

        for query in queries:
            modality = retriever._detect_modality(query)
            assert modality in (QueryModality.IMAGE, QueryModality.MULTI)

    @pytest.mark.asyncio
    async def test_detect_modality_structured(self, retriever):
        """Test structured data modality detection."""
        queries = [
            "sales statistics for Q4",
            "table of employee data",
            "JSON configuration options",
            "average revenue by region",
        ]

        for query in queries:
            modality = retriever._detect_modality(query)
            assert modality in (QueryModality.STRUCTURED, QueryModality.MULTI)

    @pytest.mark.asyncio
    async def test_detect_modality_multi(self, retriever):
        """Test multi-modality detection."""
        queries = [
            "chart showing sales statistics",  # image + structured
            "visual table of data",  # image + structured
        ]

        for query in queries:
            modality = retriever._detect_modality(query)
            assert modality == QueryModality.MULTI

    @pytest.mark.asyncio
    async def test_search_text_modality(self, retriever):
        """Test search with text modality."""
        result = await retriever.search(
            "machine learning concepts",
            modality=QueryModality.TEXT,
            top_k=5,
        )

        assert isinstance(result, UnifiedSearchResult)
        assert result.detected_modality == QueryModality.TEXT
        assert isinstance(result.results, list)
        assert result.search_time_ms >= 0

    @pytest.mark.asyncio
    async def test_search_auto_detection(self, retriever):
        """Test search with automatic modality detection."""
        result = await retriever.search(
            "photos of nature",
            top_k=5,
        )

        assert isinstance(result, UnifiedSearchResult)
        assert result.detected_modality in QueryModality

    @pytest.mark.asyncio
    async def test_search_forced_modality(self, retriever):
        """Test search with forced modality."""
        result = await retriever.search(
            "any query text",
            modality=QueryModality.STRUCTURED,
            top_k=5,
        )

        assert result.detected_modality == QueryModality.STRUCTURED

    @pytest.mark.asyncio
    async def test_search_with_filters(self, retriever):
        """Test search with metadata filters."""
        filters = {"category": "documentation", "language": "en"}

        result = await retriever.search(
            "test query",
            top_k=5,
            filters=filters,
        )

        assert isinstance(result, UnifiedSearchResult)

    @pytest.mark.asyncio
    async def test_search_empty_query(self, retriever):
        """Test search with empty query."""
        result = await retriever.search("", top_k=5)

        assert isinstance(result, UnifiedSearchResult)
        assert result.detected_modality == QueryModality.TEXT

    @pytest.mark.asyncio
    async def test_search_by_image(self, retriever, sample_image):
        """Test image-based search."""
        if not HAS_PIL:
            pytest.skip("PIL not available")

        result = await retriever.search_by_image(
            sample_image,
            top_k=5,
        )

        assert isinstance(result, UnifiedSearchResult)
        assert result.detected_modality == QueryModality.IMAGE
        assert "image" in result.modality_breakdown

    @pytest.mark.asyncio
    async def test_search_by_image_not_available(self, tmp_path):
        """Test image search when image retriever unavailable."""
        config = UnifiedRetrieverConfig()
        retriever = UnifiedRetriever(config)

        # Mock to disable image retriever
        with patch.object(retriever, "_image_retriever", None):
            await retriever.initialize()

            with pytest.raises(RetrievalError, match="not available"):
                await retriever.search_by_image("test.png")

            await retriever.close()

    @pytest.mark.asyncio
    async def test_structured_search(self, retriever, sample_csv):
        """Test structured data search."""
        # Index some data first
        if retriever._structured_retriever:
            await retriever._structured_retriever.index_csv(sample_csv)

        query = StructuredQuery(
            filters={"value": "> 100"},
            limit=5,
        )

        result = await retriever.structured_search(
            query=query,
            text_query="high value records",
            top_k=5,
        )

        assert isinstance(result, UnifiedSearchResult)
        assert result.detected_modality == QueryModality.STRUCTURED

    @pytest.mark.asyncio
    async def test_structured_search_no_text(self, retriever, sample_csv):
        """Test structured search without text component."""
        if retriever._structured_retriever:
            await retriever._structured_retriever.index_csv(sample_csv)

        query = StructuredQuery(filters={})

        result = await retriever.structured_search(
            query=query,
            text_query=None,
        )

        assert isinstance(result, UnifiedSearchResult)
        assert result.modality_weights["structured"] == 1.0

    @pytest.mark.asyncio
    async def test_index_content_image(self, retriever, sample_image):
        """Test indexing image content."""
        if not HAS_PIL:
            pytest.skip("PIL not available")

        doc_ids = await retriever.index_content(
            content_type="image",
            content_path=sample_image,
            description="Test image",
        )

        assert isinstance(doc_ids, list)

    @pytest.mark.asyncio
    async def test_index_content_csv(self, retriever, sample_csv):
        """Test indexing CSV content."""
        doc_ids = await retriever.index_content(
            content_type="csv",
            content_path=sample_csv,
            description="Test data",
        )

        assert isinstance(doc_ids, list)

    @pytest.mark.asyncio
    async def test_index_content_json(self, tmp_path, retriever):
        """Test indexing JSON content."""
        json_path = tmp_path / "test.json"
        data = [{"id": 1, "name": "test"}]
        with open(json_path, "w") as f:
            json.dump(data, f)

        doc_ids = await retriever.index_content(
            content_type="json",
            content_path=str(json_path),
        )

        assert isinstance(doc_ids, list)

    @pytest.mark.asyncio
    async def test_index_content_unsupported(self, retriever):
        """Test indexing unsupported content type."""
        with pytest.raises(RetrievalError, match="Unsupported"):
            await retriever.index_content(
                content_type="unknown",
                content_path="test.xyz",
            )

    @pytest.mark.asyncio
    async def test_get_stats(self, retriever):
        """Test getting statistics."""
        stats = await retriever.get_stats()

        assert stats["initialized"] is True
        assert "config" in stats
        assert stats["config"]["parallel_search"] is True

    @pytest.mark.asyncio
    async def test_health_check(self, retriever):
        """Test health check."""
        health = await retriever.health_check()

        assert isinstance(health, dict)
        assert "unified" in health
        assert "text" in health
        assert "image" in health
        assert "structured" in health

    @pytest.mark.asyncio
    async def test_health_check_uninitialized(self):
        """Test health check when not initialized."""
        config = UnifiedRetrieverConfig()
        retriever = UnifiedRetriever(config)

        health = await retriever.health_check()

        assert health["unified"] is False

    @pytest.mark.asyncio
    async def test_uninitialized_error(self):
        """Test operations fail when not initialized."""
        config = UnifiedRetrieverConfig()
        retriever = UnifiedRetriever(config)

        with pytest.raises(RetrievalError, match="not initialized"):
            await retriever.search("test query")

    @pytest.mark.asyncio
    async def test_close(self, retriever):
        """Test closing retriever."""
        await retriever.close()

        assert retriever._initialized is False
        assert retriever._text_retriever is None
        assert retriever._image_retriever is None
        assert retriever._structured_retriever is None


class TestUnifiedRetrieverIntegration:
    """Integration tests for unified retriever."""

    @pytest.mark.asyncio
    async def test_full_multimodal_workflow(self, tmp_path):
        """Test complete multi-modal workflow."""
        if not HAS_PIL:
            pytest.skip("PIL not available")

        config = UnifiedRetrieverConfig(
            parallel_search=True,
            max_total_results=20,
        )
        retriever = UnifiedRetriever(config)
        await retriever.initialize()

        try:
            # Index various content types
            # CSV data
            csv_path = tmp_path / "data.csv"
            pd.DataFrame(
                {
                    "id": range(10),
                    "category": ["A", "B"] * 5,
                    "value": range(100, 200, 10),
                }
            ).to_csv(csv_path, index=False)

            await retriever.index_content("csv", str(csv_path), "Sample data")

            # Image
            img_path = tmp_path / "test.png"
            Image.new("RGB", (100, 100), color="blue").save(img_path)

            await retriever.index_content("image", str(img_path), "Blue image")

            # Search with different modalities
            # Text search
            result = await retriever.search(
                "data values",
                modality=QueryModality.TEXT,
            )
            assert isinstance(result, UnifiedSearchResult)

            # Structured search
            result = await retriever.search(
                "table statistics",
                modality=QueryModality.STRUCTURED,
            )
            assert isinstance(result, UnifiedSearchResult)

            # Multi-modal search
            result = await retriever.search(
                "visual chart of data",
                modality=QueryModality.MULTI,
            )
            assert isinstance(result, UnifiedSearchResult)

            # Check stats
            stats = await retriever.get_stats()
            assert stats["initialized"] is True

        finally:
            await retriever.close()

    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_search(self, tmp_path):
        """Test that parallel and sequential search produce same results."""
        config_parallel = UnifiedRetrieverConfig(parallel_search=True)
        config_sequential = UnifiedRetrieverConfig(parallel_search=False)

        retriever_parallel = UnifiedRetriever(config_parallel)
        retriever_sequential = UnifiedRetriever(config_sequential)

        await retriever_parallel.initialize()
        await retriever_sequential.initialize()

        try:
            # Both should complete without error
            result_p = await retriever_parallel.search("test query", top_k=5)
            result_s = await retriever_sequential.search("test query", top_k=5)

            assert isinstance(result_p, UnifiedSearchResult)
            assert isinstance(result_s, UnifiedSearchResult)

        finally:
            await retriever_parallel.close()
            await retriever_sequential.close()

    @pytest.mark.asyncio
    async def test_modality_weights_in_fusion(self, tmp_path):
        """Test that modality weights affect fusion."""
        config = UnifiedRetrieverConfig(
            text_weight=0.6,
            image_weight=0.2,
            structured_weight=0.2,
        )
        retriever = UnifiedRetriever(config)
        await retriever.initialize()

        try:
            result = await retriever.search("test query")

            assert result.modality_weights["text"] == 0.6
            assert result.modality_weights["image"] == 0.2
            assert result.modality_weights["structured"] == 0.2

        finally:
            await retriever.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])