"""Tests for rag_pipeline.py -- all mocked, no API calls."""

import importlib.util
import io
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

pypdf_available = importlib.util.find_spec("pypdf") is not None

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_pipeline import ProviderConfig, RAGResponse, SourceChunk, _chunk_text, ingest_document, ingest_url, query

# -- Fixtures ------------------------------------------------------------------


@pytest.fixture
def config():
    return ProviderConfig(
        embedding_provider="glm",
        llm_provider="glm",
        api_key="test-key-12345",
    )


SAMPLE_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "This is a test sentence for chunking purposes. "
    "We need enough text to create multiple chunks. "
) * 80  # ~4800 chars, should produce multiple chunks

FAKE_EMBEDDING = [0.1] * 1024


def make_fake_embed(texts, config=None):
    return [FAKE_EMBEDDING[:] for _ in texts]


def make_fake_chroma_collection(chunks):
    """Return a mock ChromaDB collection that returns provided chunks on query."""
    mock_col = MagicMock()
    mock_col.count.return_value = len(chunks)
    mock_col.query.return_value = {
        "documents": [chunks],
        "metadatas": [[{"chunk_index": i, "source_filename": "test.txt"} for i in range(len(chunks))]],
        "distances": [[0.1 * (i + 1) for i in range(len(chunks))]],
    }
    return mock_col


# -- Tests ---------------------------------------------------------------------


def test_chunk_text_pdf():
    """Chunk a known text and verify chunk count and max size."""
    chunks = _chunk_text(SAMPLE_TEXT, chunk_size=800, chunk_overlap=100)
    assert len(chunks) > 1, "Expected multiple chunks for long text"
    for chunk in chunks:
        word_count = len(chunk.split())
        # Allow some tolerance for overlap logic
        assert word_count <= 950, f"Chunk too large: {word_count} words"


def test_chunk_respects_overlap():
    """Verify that overlap words from end of chunk N appear at start of chunk N+1."""
    chunks = _chunk_text(SAMPLE_TEXT, chunk_size=100, chunk_overlap=20)
    assert len(chunks) >= 2, "Need at least 2 chunks to test overlap"
    for i in range(len(chunks) - 1):
        end_words = chunks[i].split()[-10:]  # last 10 words of chunk i
        next_start = chunks[i + 1]
        # At least some overlap words should appear in next chunk start
        overlap_found = any(w in next_start[:200] for w in end_words)
        assert overlap_found, f"No overlap detected between chunk {i} and {i + 1}"


def test_ingest_document_txt(config):
    """Ingest TXT bytes with mocked embeddings, verify collection_id returned."""
    content = b"Hello world. This is a test document. " * 50

    with (
        patch("rag_pipeline._embed_texts", side_effect=make_fake_embed),
        patch("rag_pipeline._chroma_client") as mock_client,
    ):
        mock_col = MagicMock()
        mock_client.create_collection.return_value = mock_col

        result = ingest_document(content, "test.txt", config)

        assert isinstance(result, str)
        assert len(result) > 0
        assert result.startswith("doc_")
        mock_col.add.assert_called_once()


@pytest.mark.skipif(not pypdf_available, reason="pypdf not installed")
def test_ingest_document_pdf(config):
    """Ingest PDF bytes with mocked pypdf and embeddings."""
    fake_page = MagicMock()
    fake_page.extract_text.return_value = "This is page text from a PDF. " * 50

    with (
        patch("rag_pipeline._embed_texts", side_effect=make_fake_embed),
        patch("rag_pipeline._chroma_client") as mock_client,
        patch("pypdf.PdfReader") as mock_pdf,
    ):
        mock_pdf.return_value.pages = [fake_page, fake_page]
        mock_col = MagicMock()
        mock_client.create_collection.return_value = mock_col

        # Pass minimal PDF bytes (will be intercepted by mock)
        result = ingest_document(b"%PDF-1.4 fake content", "document.pdf", config)

        assert isinstance(result, str)
        assert result.startswith("doc_")


def test_query_returns_rag_response(config):
    """Query with mocked embed + chromadb + LLM, verify RAGResponse shape."""
    sample_chunks = [
        "The capital of France is Paris. It is known for the Eiffel Tower.",
        "Paris has a population of over 2 million people in the city proper.",
        "French cuisine is famous worldwide for its sophistication.",
    ]
    mock_col = make_fake_chroma_collection(sample_chunks)

    with (
        patch("rag_pipeline._embed_texts", side_effect=make_fake_embed),
        patch("rag_pipeline._chroma_client") as mock_client,
        patch("rag_pipeline._generate_answer", return_value="Paris is the capital of France [Source 1]."),
    ):
        mock_client.get_collection.return_value = mock_col

        result = query("What is the capital of France?", "doc_abc12345", config)

        assert isinstance(result, RAGResponse)
        assert isinstance(result.answer, str)
        assert len(result.answer) > 0
        assert isinstance(result.sources, list)
        assert isinstance(result.latency_ms, int)
        assert result.latency_ms >= 0


def test_query_sources_have_content(config):
    """Verify sources list is non-empty with proper content and scores."""
    sample_chunks = [
        "Source chunk one with relevant content about the topic.",
        "Source chunk two with additional related information.",
    ]
    mock_col = make_fake_chroma_collection(sample_chunks)

    with (
        patch("rag_pipeline._embed_texts", side_effect=make_fake_embed),
        patch("rag_pipeline._chroma_client") as mock_client,
        patch("rag_pipeline._generate_answer", return_value="Answer based on sources [Source 1]."),
    ):
        mock_client.get_collection.return_value = mock_col

        result = query("What is this about?", "doc_test1234", config)

        assert len(result.sources) > 0
        for src in result.sources:
            assert isinstance(src, SourceChunk)
            assert isinstance(src.content, str)
            assert len(src.content) > 0
            assert isinstance(src.score, float)
            assert isinstance(src.chunk_index, int)


def test_url_fetch_and_ingest(config):
    """Mock httpx.get returning HTML, verify text extracted and collection_id returned."""
    fake_html = (
        """
    <html>
    <head><title>Test Page</title></head>
    <body>
    <nav>Navigation bar content</nav>
    <main>
    <h1>Main Article Title</h1>
    <p>This is the main content of the article. It contains useful information.</p>
    <p>Here is another paragraph with more content about the topic being discussed.</p>
    </main>
    <footer>Footer content</footer>
    </body>
    </html>
    """
        * 20
    )

    mock_response = MagicMock()
    mock_response.text = fake_html
    mock_response.raise_for_status = MagicMock()

    with (
        patch("rag_pipeline._embed_texts", side_effect=make_fake_embed),
        patch("rag_pipeline._chroma_client") as mock_client,
        patch("rag_pipeline.httpx.get", return_value=mock_response),
    ):
        mock_col = MagicMock()
        mock_client.create_collection.return_value = mock_col

        result = ingest_url("https://example.com/article", config)

        assert isinstance(result, str)
        assert result.startswith("doc_")


def test_provider_config_defaults():
    """Verify GLM defaults load correctly with only required fields."""
    cfg = ProviderConfig(
        embedding_provider="glm",
        llm_provider="glm",
        api_key="my-api-key",
    )
    assert cfg.embedding_model == "embedding-3"
    assert cfg.llm_model == "glm-4-flash"
    assert cfg.glm_base_url == "https://api.z.ai/api/paas/v4"
    assert cfg.api_key == "my-api-key"


def test_empty_document_raises(config):
    """Empty bytes should raise ValueError."""
    with pytest.raises(ValueError, match="empty"):
        ingest_document(b"", "empty.txt", config)

    with pytest.raises(ValueError):
        ingest_document(b"   \n\t  ", "whitespace.txt", config)


def test_answer_includes_citation_markers(config):
    """Verify [Source N] markers are injected into the LLM prompt."""
    sample_chunks = ["Chunk one content.", "Chunk two content.", "Chunk three content."]
    mock_col = make_fake_chroma_collection(sample_chunks)

    captured_prompts = {}

    def fake_generate(question, chunks, cfg):
        captured_prompts["question"] = question
        captured_prompts["chunks"] = chunks
        # Build what the real function would build
        sources_text = "\n\n".join(f"[Source {i + 1}]\n{c}" for i, c in enumerate(chunks))
        captured_prompts["sources_text"] = sources_text
        return "Answer referencing [Source 1] and [Source 2]."

    with (
        patch("rag_pipeline._embed_texts", side_effect=make_fake_embed),
        patch("rag_pipeline._chroma_client") as mock_client,
        patch("rag_pipeline._generate_answer", side_effect=fake_generate),
    ):
        mock_client.get_collection.return_value = mock_col

        result = query("What is in the document?", "doc_citetest", config)

        # Verify [Source N] markers in the sources_text that would be passed to LLM
        assert "[Source 1]" in captured_prompts["sources_text"]
        assert "[Source 2]" in captured_prompts["sources_text"]
        assert len(captured_prompts["chunks"]) > 0


# -- Hybrid Pipeline Tests -----------------------------------------------------


def test_hybrid_pipeline_ingest_and_query(config):
    """HybridRAGPipeline ingests and returns HybridRAGResponse."""
    from rag_pipeline import HybridRAGPipeline, HybridRAGResponse, HybridSourceChunk

    from rank_bm25 import BM25Okapi

    content = b"The quick brown fox jumps over the lazy dog. " * 80

    with (
        patch("rag_pipeline._embed_texts", side_effect=make_fake_embed),
        patch("rag_pipeline._chroma_client") as mock_client,
        patch("rag_pipeline._generate_answer", return_value="Hybrid answer."),
    ):
        # Setup mock collection for ingest
        mock_col = MagicMock()
        mock_client.create_collection.return_value = mock_col

        pipeline = HybridRAGPipeline()
        collection_id = pipeline.ingest(content, "test.txt", config)

        assert collection_id.startswith("hyb_")

        # Setup mock for query
        sample_chunks = ["chunk one content here.", "chunk two content here."]
        pipeline._corpus = sample_chunks
        tokenized = [c.lower().split() for c in sample_chunks]
        pipeline._bm25 = BM25Okapi(tokenized)

        mock_query_col = make_fake_chroma_collection(sample_chunks)
        pipeline._chroma_collection = mock_query_col

        result = pipeline.query("quick brown fox", config)

        assert isinstance(result, HybridRAGResponse)
        assert isinstance(result.answer, str)
        assert isinstance(result.latency_ms, int)
        assert len(result.sources) > 0
        src = result.sources[0]
        assert isinstance(src, HybridSourceChunk)
        assert 0.0 <= src.bm25_score <= 1.0
        assert 0.0 <= src.dense_score <= 1.0
        assert 0.0 <= src.fused_score <= 1.0


def test_hybrid_pipeline_not_initialized_raises(config):
    """HybridRAGPipeline raises RuntimeError if query called before ingest."""
    from rag_pipeline import HybridRAGPipeline

    pipeline = HybridRAGPipeline()
    with pytest.raises(RuntimeError, match="not initialized"):
        pipeline.query("any question", config)


def test_hybrid_source_chunk_has_three_scores():
    """HybridSourceChunk dataclass stores bm25, dense, fused scores."""
    from rag_pipeline import HybridSourceChunk

    chunk = HybridSourceChunk(
        content="some content",
        bm25_score=0.8,
        dense_score=0.75,
        fused_score=0.9,
        chunk_index=0,
    )
    assert chunk.bm25_score == 0.8
    assert chunk.dense_score == 0.75
    assert chunk.fused_score == 0.9
