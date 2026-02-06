# Advanced RAG System - Phase 2 Continuation Prompt

**Project**: Advanced RAG System (Principal AI Engineer Portfolio)  
**Current Phase**: Phase 1 Complete → Phase 2: Hybrid Retrieval  
**Last Updated**: 2026-02-01

---

## 📋 Project Context

### What Was Completed in Phase 1 (Foundation Layer)

Phase 1 established the foundational infrastructure for the Advanced RAG System:

1. **Project Structure & Tooling**
   - Complete Python project setup with modern tooling
   - Makefile with standardized commands (`install`, `test`, `typecheck`, `format`, `lint`)
   - pytest configuration with coverage reporting
   - Docker-ready structure

2. **Core Type System** ([`src/core/types.py`](src/core/types.py))
   - [`DocumentChunk`](src/core/types.py:75) - Pydantic model for document chunks with embedding support
   - [`Metadata`](src/core/types.py:39) - Flexible metadata with validation
   - [`SearchResult`](src/core/types.py) - Unified search result structure
   - [`QueryType`](src/core/types.py:29) / [`DocumentType`](src/core/types.py:18) - Enumeration types

3. **Embedding Service** ([`src/embeddings/`](src/embeddings/))
   - [`EmbeddingProvider`](src/embeddings/base.py:37) abstract base class
   - [`OpenAIEmbeddingProvider`](src/embeddings/openai_provider.py:20) with batching, retries, rate limiting
   - [`EmbeddingConfig`](src/embeddings/base.py:16) dataclass for configuration
   - Embedding cache layer ([`src/embeddings/cache.py`](src/embeddings/cache.py))

4. **Vector Store Integration** ([`src/vector_store/`](src/vector_store/))
   - [`VectorStore`](src/vector_store/base.py:53) abstract interface
   - [`ChromaVectorStore`](src/vector_store/chroma_store.py:22) production implementation
   - [`SearchOptions`](src/vector_store/base.py:34) / [`VectorStoreConfig`](src/vector_store/base.py:17) configuration
   - Metadata filtering and batch operations

5. **Configuration & Utilities**
   - [`src/core/config.py`](src/core/config.py) - Pydantic settings with env var support
   - [`src/core/exceptions.py`](src/core/exceptions.py) - Custom exception hierarchy
   - [`src/utils/logging.py`](src/utils/logging.py) - Structured JSON logging

6. **Testing Infrastructure**
   - 95%+ test coverage target established
   - Comprehensive test suite in [`tests/`](tests/)
   - Benchmark framework in [`tests/benchmarks/`](tests/benchmarks/)

### Architecture Decisions Made

1. **Async-First Design**: All I/O operations use `async/await` for optimal performance
2. **Abstract Base Classes**: Clean interfaces allow swapping implementations (OpenAI ↔ Local, ChromaDB ↔ Pinecone)
3. **Pydantic v2 Models**: Strict validation and serialization across all data structures
4. **Type Safety**: 100% type hints with mypy strict mode enforcement
5. **Error Handling**: Custom exception hierarchy with error codes for observability

---

## 🎯 Phase 2: Hybrid Retrieval (Days 6-10)

### Goals
- Implement BM25 sparse retrieval for keyword-based search
- Build hybrid search with Reciprocal Rank Fusion (RRF)
- Add query expansion and rewriting capabilities
- Create cross-encoder re-ranking layer

### Deliverables

#### Day 6: Sparse Retrieval
- [ ] BM25 index implementation
- [ ] TF-IDF fallback
- [ ] Text preprocessing pipeline
- [ ] Inverted index optimization

**New Files to Create:**
- `src/retrieval/sparse/bm25_index.py` - BM25 implementation using `rank-bm25` or custom
- `src/retrieval/sparse/tfidf_index.py` - TF-IDF fallback using `scikit-learn`
- `src/retrieval/sparse/preprocessing.py` - Text normalization, stemming, stopword removal

#### Day 7: Hybrid Search
- [ ] Reciprocal Rank Fusion (RRF) algorithm
- [ ] Weighted score fusion option
- [ ] Parallel retrieval execution (dense + sparse concurrently)
- [ ] Result deduplication logic

**New Files to Create:**
- `src/retrieval/hybrid/fusion.py` - RRF and weighted fusion algorithms
- `src/retrieval/hybrid/hybrid_searcher.py` - Orchestrator combining dense + sparse

#### Day 8: Query Enhancement
- [ ] Query expansion (synonym generation)
- [ ] HyDE (Hypothetical Document Embedding) implementation
- [ ] Query classification for routing
- [ ] Multi-query generation

**New Files to Create:**
- `src/retrieval/query/expansion.py` - Synonym-based expansion
- `src/retrieval/query/hyde.py` - HyDE generator using LLM
- `src/retrieval/query/classifier.py` - Query type classification

#### Day 9: Re-ranking
- [ ] Cross-encoder integration (sentence-transformers)
- [ ] Cohere rerank API support
- [ ] Local reranker option
- [ ] Async batch reranking for efficiency

**New Files to Create:**
- `src/reranking/base.py` - Abstract reranker interface
- `src/reranking/cross_encoder.py` - Cross-encoder implementation
- `src/reranking/cohere_reranker.py` - Cohere API integration

#### Day 10: Integration & Testing
- [ ] End-to-end hybrid search tests
- [ ] Latency benchmarks (<100ms target)
- [ ] Accuracy evaluation (>85% retrieval accuracy)
- [ ] Documentation updates

**New Test Files:**
- `tests/retrieval/test_hybrid_search.py`
- `tests/retrieval/test_sparse_retrieval.py`
- `tests/reranking/test_rerankers.py`
- `tests/benchmarks/test_retrieval_perf.py`

### Success Criteria
- [ ] Hybrid search working end-to-end
- [ ] Retrieval accuracy >85%
- [ ] End-to-end latency <100ms
- [ ] Fusion algorithm validated with benchmarks

---

## 🔑 Key Files Reference

### Core Types & Interfaces
| File | Purpose |
|------|---------|
| [`src/core/types.py`](src/core/types.py) | DocumentChunk, SearchResult, Metadata models |
| [`src/embeddings/base.py`](src/embeddings/base.py) | EmbeddingProvider ABC, EmbeddingConfig |
| [`src/embeddings/openai_provider.py`](src/embeddings/openai_provider.py) | OpenAI embedding implementation |
| [`src/vector_store/base.py`](src/vector_store/base.py) | VectorStore ABC, SearchOptions |
| [`src/vector_store/chroma_store.py`](src/vector_store/chroma_store.py) | ChromaDB implementation |

### Configuration & Exceptions
| File | Purpose |
|------|---------|
| [`src/core/config.py`](src/core/config.py) | Settings management with env vars |
| [`src/core/exceptions.py`](src/core/exceptions.py) | Custom exception hierarchy |

### Existing Retrieval Structure
| File | Purpose |
|------|---------|
| [`src/retrieval/__init__.py`](src/retrieval/__init__.py) | Retrieval module exports |

---

## 🏗️ Implementation Guidelines

### Development Standards

1. **Type Hints**: 100% coverage required, mypy strict mode
   ```python
   async def search(
       self, 
       query: str, 
       options: SearchOptions
   ) -> List[SearchResult]:
   ```

2. **Docstrings**: Google-style with Args/Returns/Raises
   ```python
   """Perform hybrid search combining dense and sparse retrieval.
   
   Args:
       query: Search query string
       options: Search configuration options
       
   Returns:
       List of search results ranked by relevance
       
   Raises:
       RetrievalError: If search operation fails
   """
   ```

3. **Test Coverage**: 95%+ required
   ```python
   # Test structure
   def test_bm25_search_returns_ranked_results():
       # Arrange
       # Act
       # Assert
   ```

4. **Async/Await**: All I/O operations must be async
   ```python
   async def embed(self, texts: List[str]) -> List[List[float]]:
       async with self._semaphore:
           return await self._client.embeddings.create(...)
   ```

### Code Patterns to Follow

#### Abstract Base Class Pattern
```python
from abc import ABC, abstractmethod

class SparseRetriever(ABC):
    """Abstract base for sparse retrieval implementations."""
    
    @abstractmethod
    async def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        pass
```

#### Configuration Dataclass Pattern
```python
from dataclasses import dataclass

@dataclass
class BM25Config:
    """Configuration for BM25 retriever."""
    k1: float = 1.5  # Term frequency saturation
    b: float = 0.75  # Length normalization
    top_k: int = 100
```

#### Error Handling Pattern
```python
from src.core.exceptions import RetrievalError

try:
    results = await self._collection.query(...)
except Exception as e:
    raise RetrievalError(
        message=f"BM25 search failed: {str(e)}",
        error_code="BM25_SEARCH_ERROR",
        query=query
    ) from e
```

---

## 🧪 Commands to Verify Setup

```bash
# Navigate to project
cd advanced_rag_system

# Install dependencies
make install

# Run tests (should pass with Phase 1 code)
make test

# Type checking (should pass with zero errors)
make typecheck

# Run benchmarks
make benchmark

# Check test coverage
make coverage
```

### Expected Test Results
```
========================== test session starts ==========================
platform darwin -- Python 3.11.x
 collected 50+ items

 tests/core/test_config.py ..........
 tests/core/test_exceptions.py .......
 tests/embeddings/test_base.py .......
 tests/embeddings/test_cache.py ......
 tests/vector_store/test_base.py .....
 tests/vector_store/test_chroma_store.py .......

 ====================== 50+ passed in 5.0s =======================
```

---

## 📦 Dependencies to Add (Phase 2)

Add to [`requirements.txt`](requirements.txt):

```txt
# Sparse Retrieval
rank-bm25>=0.2.2
scikit-learn>=1.3.0

# Re-ranking
sentence-transformers>=2.2.2
cohere>=4.0.0

# Text Processing
nltk>=3.8.1
spacy>=3.7.0

# Async Utilities
aiocache>=0.12.0
```

---

## 🎯 Immediate Next Steps

1. **Create Directory Structure**
   ```bash
   mkdir -p src/retrieval/sparse src/retrieval/hybrid src/retrieval/query src/reranking
   touch src/retrieval/sparse/__init__.py src/retrieval/hybrid/__init__.py
   touch src/retrieval/query/__init__.py src/reranking/__init__.py
   ```

2. **Install New Dependencies**
   ```bash
   pip install rank-bm25 scikit-learn sentence-transformers nltk
   ```

3. **Implement BM25 Index** (Start Here)
   - Create `src/retrieval/sparse/bm25_index.py`
   - Implement `BM25Index` class with `add_documents()` and `search()` methods
   - Follow patterns from [`src/vector_store/chroma_store.py`](src/vector_store/chroma_store.py)

4. **Write Tests First**
   - Create `tests/retrieval/test_sparse_retrieval.py`
   - Write test cases before implementation
   - Run `make test` to verify

---

## 📚 Reference Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Complete 30-day plan
- [TECHNICAL_SPECIFICATION.md](TECHNICAL_SPECIFICATION.md) - API specifications
- [BENCHMARKS.md](BENCHMARKS.md) - Performance targets and results
- [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md) - Code organization

---

## ⚠️ Important Notes

1. **Keep Phase 1 Code Intact**: All Phase 1 functionality should continue working
2. **Backward Compatibility**: New retrieval components should integrate with existing [`DocumentChunk`](src/core/types.py:75) and [`SearchResult`](src/core/types.py) types
3. **Performance First**: Benchmark after each major component - target <20ms for sparse retrieval
4. **Test Coverage**: Never drop below 95% coverage when adding new code

---

**Ready to start Phase 2? Begin with BM25 implementation in `src/retrieval/sparse/bm25_index.py`.**
