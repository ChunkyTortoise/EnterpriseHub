"""Smoke tests -- verify rag_pipeline imports and API surface without Streamlit runtime."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_rag_pipeline_imports():
    """rag_pipeline module imports without error."""
    import rag_pipeline  # noqa: F401


def test_dataclasses_importable():
    """All public dataclasses are importable and instantiable."""
    from rag_pipeline import ProviderConfig, RAGResponse, SourceChunk

    cfg = ProviderConfig(embedding_provider="glm", llm_provider="glm", api_key="test")
    assert cfg.embedding_provider == "glm"

    src = SourceChunk(content="test content", score=0.9, chunk_index=0)
    assert src.score == 0.9

    resp = RAGResponse(answer="test answer", sources=[src], latency_ms=100)
    assert resp.latency_ms == 100


def test_public_functions_callable():
    """All public functions exist and are callable."""
    from rag_pipeline import ingest_document, ingest_url, query

    assert callable(ingest_document)
    assert callable(ingest_url)
    assert callable(query)


def test_provider_config_glm_base_url():
    """Default GLM base URL is set correctly."""
    from rag_pipeline import ProviderConfig

    cfg = ProviderConfig(embedding_provider="glm", llm_provider="glm", api_key="x")
    assert cfg.glm_base_url == "https://api.z.ai/api/paas/v4"
    assert cfg.embedding_model == "embedding-3"
    assert cfg.llm_model == "glm-4-flash"
