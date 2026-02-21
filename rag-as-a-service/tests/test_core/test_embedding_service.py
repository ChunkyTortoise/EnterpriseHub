"""Unit tests for EmbeddingService — local embeddings, batching, providers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag_service.core.embedding_service import EmbeddingResult, EmbeddingService


class TestLocalEmbeddings:
    @pytest.mark.asyncio
    async def test_local_embed_returns_correct_dimension(self):
        svc = EmbeddingService(provider="local", dimension=128)
        result = await svc.embed_texts(["Hello world"])
        assert len(result.embeddings) == 1
        assert len(result.embeddings[0]) == 128

    @pytest.mark.asyncio
    async def test_local_embed_deterministic(self):
        svc = EmbeddingService(provider="local", dimension=64)
        r1 = await svc.embed_texts(["test"])
        r2 = await svc.embed_texts(["test"])
        assert r1.embeddings[0] == r2.embeddings[0]

    @pytest.mark.asyncio
    async def test_local_embed_different_texts_differ(self):
        svc = EmbeddingService(provider="local", dimension=64)
        r1 = await svc.embed_texts(["hello"])
        r2 = await svc.embed_texts(["world"])
        assert r1.embeddings[0] != r2.embeddings[0]

    @pytest.mark.asyncio
    async def test_local_embed_multiple_texts(self):
        svc = EmbeddingService(provider="local", dimension=32)
        result = await svc.embed_texts(["text1", "text2", "text3"])
        assert len(result.embeddings) == 3
        assert result.token_count == 3
        assert result.token_count == 3

    @pytest.mark.asyncio
    async def test_embed_query_returns_single_vector(self):
        svc = EmbeddingService(provider="local", dimension=32)
        vec = await svc.embed_query("What is AI?")
        assert isinstance(vec, list)
        assert len(vec) == 32

    @pytest.mark.asyncio
    async def test_values_in_zero_one_range(self):
        svc = EmbeddingService(provider="local", dimension=32)
        result = await svc.embed_texts(["test"])
        for val in result.embeddings[0]:
            assert 0.0 <= val <= 1.0


class TestBatching:
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        svc = EmbeddingService(provider="local", dimension=16, batch_size=2)
        texts = ["a", "b", "c", "d", "e"]
        result = await svc.embed_texts(texts)
        assert len(result.embeddings) == 5

    @pytest.mark.asyncio
    async def test_single_item_batch(self):
        svc = EmbeddingService(provider="local", dimension=16, batch_size=1)
        result = await svc.embed_texts(["only one"])
        assert len(result.embeddings) == 1


class TestEmbeddingResult:
    def test_result_fields(self):
        r = EmbeddingResult(embeddings=[[0.1, 0.2]], model="test-model", token_count=5)
        assert r.model == "test-model"
        assert r.token_count == 5
        assert len(r.embeddings) == 1


class TestProviderRouting:
    @pytest.mark.asyncio
    async def test_openai_provider_calls_api(self):
        svc = EmbeddingService(provider="openai", api_key="test")
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1] * 10}],
                "usage": {"total_tokens": 5},
            }
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await svc.embed_texts(["test"])
            assert len(result.embeddings) == 1
            assert result.token_count == 5
