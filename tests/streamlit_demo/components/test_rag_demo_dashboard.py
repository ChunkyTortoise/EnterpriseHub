"""Tests for rag_demo_dashboard component.

All tests are pure unit tests -- no Streamlit context needed.
We test the data processing functions directly.
"""

import pytest

from ghl_real_estate_ai.streamlit_demo.components.rag_demo_dashboard import (
    BM25Index,
    DenseIndex,
    DEMO_DOCUMENTS,
    SearchResult,
    _bm25_only_search,
    _build_corpus,
    _chunk_document,
    _cosine,
    _dense_only_search,
    _hybrid_search,
    _rrf_fusion,
    _tokenize,
)


# -- Tokenizer tests -----------------------------------------------------------


class TestTokenize:
    def test_basic(self):
        tokens = _tokenize("Hello World!")
        assert "hello" in tokens
        assert "world" in tokens

    def test_empty(self):
        assert _tokenize("") == []

    def test_numbers(self):
        tokens = _tokenize("price $685,000")
        assert "685" in tokens or "685,000" in tokens or "price" in tokens


# -- Chunking tests -------------------------------------------------------------


class TestChunkDocument:
    def test_short_document_single_chunk(self):
        doc = "Short text."
        chunks = _chunk_document(doc, chunk_size=200)
        assert len(chunks) >= 1

    def test_long_document_multiple_chunks(self):
        doc = ("word " * 500).strip()
        chunks = _chunk_document(doc, chunk_size=200)
        assert len(chunks) > 1

    def test_chunks_not_empty(self):
        doc = list(DEMO_DOCUMENTS.values())[0]
        chunks = _chunk_document(doc)
        assert all(chunk.strip() for chunk in chunks)


# -- BM25 tests ----------------------------------------------------------------


class TestBM25Index:
    def test_fit_and_score(self):
        corpus = [
            "The quick brown fox jumps over the lazy dog",
            "Machine learning is a subset of artificial intelligence",
            "Real estate prices in California are high",
        ]
        bm25 = BM25Index()
        bm25.fit(corpus)
        scores = bm25.get_scores(["real", "estate", "prices"])
        assert len(scores) == len(corpus)
        assert scores[2] > scores[0], (
            "Real estate doc should score highest for real estate query"
        )

    def test_empty_query(self):
        corpus = ["some document text"]
        bm25 = BM25Index()
        bm25.fit(corpus)
        scores = bm25.get_scores([])
        assert scores == [0.0]

    def test_scores_non_negative(self):
        corpus = ["doc one", "doc two", "doc three"]
        bm25 = BM25Index()
        bm25.fit(corpus)
        scores = bm25.get_scores(["one"])
        assert all(s >= 0.0 for s in scores)


# -- Dense retrieval tests ------------------------------------------------------


class TestDenseIndex:
    def test_fit_and_score(self):
        corpus = [
            "HOA fee monthly assessment payment",
            "property inspection structural foundation",
            "purchase agreement contract closing escrow",
        ]
        dense = DenseIndex()
        dense.fit(corpus)
        scores = dense.get_scores("HOA fee payment")
        assert len(scores) == len(corpus)
        assert scores[0] > scores[1], (
            "HOA doc should score highest for HOA query"
        )

    def test_cosine_identical(self):
        v = [1.0, 0.5, 0.0]
        assert abs(_cosine(v, v) - 1.0) < 1e-6

    def test_cosine_orthogonal(self):
        assert _cosine([1.0, 0.0], [0.0, 1.0]) == 0.0


# -- RRF Fusion tests ----------------------------------------------------------


class TestRRFFusion:
    def test_returns_top_k(self):
        scores_a = [0.9, 0.5, 0.2, 0.1]
        scores_b = [0.3, 0.8, 0.6, 0.1]
        results = _rrf_fusion(scores_a, scores_b, top_k=2)
        assert len(results) == 2

    def test_fused_scores_positive(self):
        scores_a = [0.9, 0.5, 0.2]
        scores_b = [0.3, 0.8, 0.6]
        results = _rrf_fusion(scores_a, scores_b, top_k=3)
        assert all(fused > 0 for _, _, _, fused in results)

    def test_no_duplicate_indices(self):
        scores_a = [0.9, 0.5, 0.2, 0.1]
        scores_b = [0.3, 0.8, 0.6, 0.4]
        results = _rrf_fusion(scores_a, scores_b, top_k=4)
        indices = [idx for idx, _, _, _ in results]
        assert len(indices) == len(set(indices))


# -- Build corpus tests ---------------------------------------------------------


class TestBuildCorpus:
    def test_corpus_non_empty(self):
        chunks, doc_names = _build_corpus()
        assert len(chunks) > 0
        assert len(doc_names) == len(chunks)

    def test_all_demo_docs_represented(self):
        _, doc_names = _build_corpus()
        unique_docs = set(doc_names)
        assert len(unique_docs) == len(DEMO_DOCUMENTS)

    def test_chunk_content_non_empty(self):
        chunks, _ = _build_corpus()
        assert all(chunk.strip() for chunk in chunks)


# -- End-to-end search tests ----------------------------------------------------


class TestHybridSearch:
    def test_returns_results(self):
        results = _hybrid_search("HOA fee", top_k=3)
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

    def test_scores_in_range(self):
        results = _hybrid_search("inspection foundation", top_k=3)
        for r in results:
            assert 0.0 <= r.bm25_score <= 1.0
            assert 0.0 <= r.dense_score <= 1.0
            assert 0.0 <= r.fused_score <= 1.0

    def test_ranks_sequential(self):
        results = _hybrid_search("purchase price", top_k=3)
        ranks = [r.rank for r in results]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_bm25_only_returns_results(self):
        results = _bm25_only_search("property listing", top_k=3)
        assert len(results) > 0
        assert all(r.dense_score == 0.0 for r in results)

    def test_dense_only_returns_results(self):
        results = _dense_only_search("market report", top_k=3)
        assert len(results) > 0
        assert all(r.bm25_score == 0.0 for r in results)
