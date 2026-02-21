"""Tests for the EmbeddingProvider abstract base class and EmbeddingConfig."""

import math
from typing import List

import pytest
from src.core.exceptions import EmbeddingError
from src.embeddings.base import EmbeddingConfig, EmbeddingProvider


@pytest.mark.unit

# ---------------------------------------------------------------------------
# Concrete test implementation
# ---------------------------------------------------------------------------


class ConcreteEmbeddingProvider(EmbeddingProvider):
    """Minimal concrete implementation for testing the ABC."""

    async def embed(self, texts: List[str]) -> List[List[float]]:
        self._validate_input(texts)
        return [[1.0, 0.0, 0.0] for _ in texts]

    async def embed_query(self, text: str) -> List[float]:
        results = await self.embed([text])
        return results[0]

    async def health_check(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# TestEmbeddingConfig
# ---------------------------------------------------------------------------


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig dataclass."""

    def test_default_values(self):
        config = EmbeddingConfig()
        assert config.model == "text-embedding-3-small"
        assert config.dimensions == 1536
        assert config.batch_size == 100
        assert config.max_retries == 3
        assert config.timeout_seconds == 30.0
        assert config.normalize is True

    def test_custom_values(self):
        config = EmbeddingConfig(
            model="custom-model",
            dimensions=768,
            batch_size=50,
            max_retries=5,
            timeout_seconds=60.0,
            normalize=False,
        )
        assert config.model == "custom-model"
        assert config.dimensions == 768
        assert config.batch_size == 50
        assert config.max_retries == 5
        assert config.timeout_seconds == 60.0
        assert config.normalize is False


# ---------------------------------------------------------------------------
# TestEmbeddingProvider
# ---------------------------------------------------------------------------


class TestEmbeddingProvider:
    """Tests for the EmbeddingProvider ABC."""

    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            EmbeddingProvider()  # type: ignore[abstract]

    def test_concrete_instantiation(self):
        provider = ConcreteEmbeddingProvider()
        assert provider.config.model == "text-embedding-3-small"
        assert provider._initialized is False

    def test_concrete_with_custom_config(self):
        config = EmbeddingConfig(model="test", dimensions=3)
        provider = ConcreteEmbeddingProvider(config)
        assert provider.config.model == "test"
        assert provider.config.dimensions == 3


class TestValidateInput:
    """Tests for _validate_input."""

    def setup_method(self):
        self.provider = ConcreteEmbeddingProvider()

    def test_empty_list_raises(self):
        with pytest.raises(EmbeddingError, match="Empty text list"):
            self.provider._validate_input([])

    def test_oversized_batch_raises(self):
        config = EmbeddingConfig(batch_size=2)
        provider = ConcreteEmbeddingProvider(config)
        with pytest.raises(EmbeddingError, match="Batch size"):
            provider._validate_input(["a", "b", "c"])

    def test_empty_text_raises(self):
        with pytest.raises(EmbeddingError, match="Empty text at index 1"):
            self.provider._validate_input(["hello", "   ", "world"])

    def test_valid_input(self):
        # Should not raise
        self.provider._validate_input(["hello", "world"])


class TestNormalizeEmbedding:
    """Tests for _normalize_embedding and _normalize_embeddings."""

    def setup_method(self):
        self.provider = ConcreteEmbeddingProvider()

    def test_unit_vector_unchanged(self):
        vec = [1.0, 0.0, 0.0]
        result = self.provider._normalize_embedding(vec)
        assert result == pytest.approx([1.0, 0.0, 0.0])

    def test_zero_vector_unchanged(self):
        vec = [0.0, 0.0, 0.0]
        result = self.provider._normalize_embedding(vec)
        assert result == [0.0, 0.0, 0.0]

    def test_arbitrary_vector_normalized(self):
        vec = [3.0, 4.0]
        result = self.provider._normalize_embedding(vec)
        magnitude = math.sqrt(sum(x * x for x in result))
        assert magnitude == pytest.approx(1.0, abs=1e-9)
        assert result == pytest.approx([0.6, 0.8])

    def test_normalize_disabled(self):
        config = EmbeddingConfig(normalize=False)
        provider = ConcreteEmbeddingProvider(config)
        vec = [3.0, 4.0]
        result = provider._normalize_embedding(vec)
        assert result == [3.0, 4.0]

    def test_batch_normalization(self):
        vecs = [[3.0, 4.0], [0.0, 0.0], [1.0, 0.0]]
        results = self.provider._normalize_embeddings(vecs)
        assert len(results) == 3
        assert results[0] == pytest.approx([0.6, 0.8])
        assert results[1] == [0.0, 0.0]
        assert results[2] == pytest.approx([1.0, 0.0])


class TestLifecycle:
    """Tests for initialize/close lifecycle."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        provider = ConcreteEmbeddingProvider()
        assert provider._initialized is False
        await provider.initialize()
        assert provider._initialized is True

    @pytest.mark.asyncio
    async def test_close(self):
        provider = ConcreteEmbeddingProvider()
        await provider.initialize()
        assert provider._initialized is True
        await provider.close()
        assert provider._initialized is False


class TestGetModelInfo:
    """Tests for get_model_info."""

    def test_output_structure(self):
        config = EmbeddingConfig(model="test-model", dimensions=768, batch_size=50)
        provider = ConcreteEmbeddingProvider(config)
        info = provider.get_model_info()
        assert info["model"] == "test-model"
        assert info["dimensions"] == 768
        assert info["batch_size"] == 50
        assert info["provider"] == "ConcreteEmbeddingProvider"
