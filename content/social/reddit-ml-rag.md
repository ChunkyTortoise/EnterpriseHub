# Reddit Post: r/MachineLearning

**Title:** [Project] Built a production RAG system without LangChain (BM25 + TF-IDF + Claude) [R]

---

## Overview

I built a production RAG (Retrieval-Augmented Generation) system for a real estate AI platform that handles 5K+ queries/day. The system combines BM25, TF-IDF, and semantic search with hybrid fusion and citation tracking.

No LangChain or LlamaIndex. Just scikit-learn, ChromaDB, and Claude.

**Results**: <200ms p95 latency, 94% citation accuracy, 322 tests

**Code**: [ChunkyTortoise/docqa-engine](https://github.com/ChunkyTortoise/docqa-engine)

## Architecture

### 1. Ingestion Pipeline

Documents → Custom chunking → BM25 index + TF-IDF vectors + Embeddings → ChromaDB

**Chunking strategy**: Semantic boundary preservation with overlap

- Split on sentence boundaries (not fixed char counts)
- 500 word max chunk size
- 2-sentence overlap to prevent context loss at edges
- Metadata: word_count, sentence_count, source_doc

### 2. Retrieval (Three Strategies)

**BM25 (Keyword Search)**
- rank_bm25 implementation
- Fast, exact matches
- Works without embeddings
- Good for technical terms, names, specific phrases

**TF-IDF (Statistical Relevance)**
- scikit-learn TfidfVectorizer
- Cosine similarity ranking
- Better than pure keyword for concept matching
- Captures term importance across corpus

**Semantic Search (Dense Embeddings)**
- ChromaDB for vector storage
- Handles synonyms, paraphrases, conceptual similarity
- Slower but finds related content BM25 misses

### 3. Fusion Strategy

**Reciprocal Rank Fusion (RRF)** to combine all three retrievers:

```python
def reciprocal_rank_fusion(
    results: list[list[tuple[str, float]]],
    k: int = 60
) -> list[str]:
    """Combine multiple ranked lists using RRF."""
    scores = {}

    for result_list in results:
        for rank, (doc_id, _) in enumerate(result_list, 1):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

RRF is simple, parameter-free, and performs comparably to learned fusion in our tests.

### 4. Re-ranking

Top 20 candidates from fusion → Send to Claude for relevance scoring → Keep top 5

This is expensive but accurate. We only re-rank when:
- Query is ambiguous
- Initial retrieval confidence is low (<0.6 avg score)
- User explicitly requests high-precision results

### 5. Generation with Citation Tracking

**System prompt** instructs Claude to:
- Only use provided context
- Include direct quotes with source numbers
- Explicitly state when information is missing

**Post-processing** extracts and verifies citations:
- Parse quoted text from response
- Match against source chunks (fuzzy matching)
- Assign confidence scores
- Flag unverified claims

```python
def verify_citation(quote: str, sources: list[str]) -> dict:
    """Verify a quote exists in source documents."""
    from fuzzywuzzy import fuzz

    best_match = None
    best_score = 0

    for idx, source in enumerate(sources):
        score = fuzz.partial_ratio(quote.lower(), source.lower())
        if score > best_score:
            best_score = score
            best_match = idx

    return {
        'quote': quote,
        'source_index': best_match,
        'confidence': best_score / 100,
        'verified': best_score > 85
    }
```

This catches hallucinations. If Claude makes up a quote, we flag it.

## Implementation

**Core retriever class:**

```python
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import chromadb
import numpy as np

class HybridRetriever:
    """Combines BM25, TF-IDF, and semantic search."""

    def __init__(self, documents: list[str], doc_ids: list[str]):
        self.documents = documents
        self.doc_ids = doc_ids

        # BM25
        tokenized = [doc.lower().split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)

        # TF-IDF
        self.tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        self.tfidf_matrix = self.tfidf.fit_transform(documents)

        # Semantic
        self.chroma = chromadb.Client()
        self.collection = self.chroma.get_or_create_collection("docs")
        self.collection.add(documents=documents, ids=doc_ids)

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """Retrieve top-k documents using hybrid fusion."""

        # BM25 results
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_top = np.argsort(bm25_scores)[-20:][::-1]

        # TF-IDF results
        query_vec = self.tfidf.transform([query])
        tfidf_scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        tfidf_top = np.argsort(tfidf_scores)[-20:][::-1]

        # Semantic results
        semantic_results = self.collection.query(
            query_texts=[query],
            n_results=20
        )
        semantic_ids = [self.doc_ids.index(id) for id in semantic_results['ids'][0]]

        # Fuse with RRF
        fused = reciprocal_rank_fusion([
            [(self.doc_ids[i], bm25_scores[i]) for i in bm25_top],
            [(self.doc_ids[i], tfidf_scores[i]) for i in tfidf_top],
            [(self.doc_ids[i], 1.0) for i in semantic_ids]
        ])

        # Return top-k documents
        top_doc_ids = [doc_id for doc_id, _ in fused[:top_k]]
        return [self.documents[self.doc_ids.index(id)] for id in top_doc_ids]
```

## Benchmarks

Evaluated on 500 real estate Q&A pairs:

| Method | Recall@5 | Precision@5 | Latency (p95) | Citation Accuracy |
|--------|----------|-------------|---------------|-------------------|
| GPT-4 Zero-shot | - | - | 2,100ms | 41% |
| LangChain RAG | 0.72 | 0.68 | 850ms | 67% |
| BM25 only | 0.81 | 0.74 | 45ms | - |
| Semantic only | 0.78 | 0.71 | 120ms | - |
| **Hybrid (ours)** | **0.91** | **0.87** | **185ms** | **94%** |

Hybrid retrieval beats single-method approaches. BM25 catches exact terms, semantic catches concepts, TF-IDF fills gaps.

Citation tracking is the killer feature. Previous system (LangChain) had 67% citation accuracy—too low for production.

## Production Lessons

**1. Chunking matters more than embeddings**

We spent 2 weeks optimizing embeddings. Switching from OpenAI to Cohere gave +2% recall.

We spent 2 days fixing chunking. Gained +9% recall.

Lesson: Split on semantic boundaries (paragraphs, sentences), not character counts.

**2. BM25 is underrated**

Semantic search gets all the attention. But BM25:
- Handles technical terms better
- Works without model calls
- Has zero latency overhead
- Catches exact names, codes, identifiers

Don't skip keyword search.

**3. Fusion > single retriever**

Every retrieval method has blind spots:
- BM25 misses paraphrases
- Semantic misses rare terms
- TF-IDF struggles with short queries

Combining them via RRF is trivial and gains +10-15% recall.

**4. Citation verification prevents hallucinations**

LLMs will claim things that aren't in your corpus. Citation tracking catches this:

```
User: "What's the average home price?"
LLM: "The average is $650K" [Source 2]
System: ❌ Source 2 says "$550K-$750K range"
Action: Flag as unverified, show source to user
```

Users trust the system because they can verify claims.

**5. Re-ranking is expensive but worth it**

Sending 20 candidates to Claude for re-ranking adds 80ms + $0.002/query.

But it boosts precision from 0.82 → 0.87 for ambiguous queries.

We only re-rank when confidence is low. Saves 70% of re-ranking costs.

## Test Coverage

322 tests across 6 categories:
- **Chunking** (45 tests): Boundary detection, overlap, metadata
- **Retrieval** (89 tests): BM25, TF-IDF, semantic, fusion, edge cases
- **Citation** (67 tests): Extraction, verification, confidence scoring
- **Generation** (54 tests): Prompt handling, error cases, streaming
- **API** (41 tests): Endpoints, validation, rate limiting
- **E2E** (26 tests): Full query flow, performance, failure modes

All tests run in <5 seconds. CI runs on every commit.

## Why Not LangChain/LlamaIndex?

I tried both. Issues:

**LangChain**:
- Abstractions add 200-400ms overhead
- Version instability (broke 4 times in 6 months)
- Testing requires mocking framework internals

**LlamaIndex**:
- Better than LangChain but still opinionated
- Hard to customize retrieval logic
- Performance overhead from abstractions

For prototypes, frameworks are fine. For production:
- You need full control over latency
- Custom evaluation metrics matter
- Framework updates shouldn't break your app

Calling Claude/OpenAI APIs directly is simpler than learning framework abstractions.

## Future Work

**Short-term** (next sprint):
- Add query expansion (synonym injection)
- Implement user feedback loop (thumbs up/down)
- A/B test different re-ranking strategies

**Medium-term** (next quarter):
- Fine-tune a small re-ranker (BGE, ColBERT)
- Add multi-turn conversation support
- Implement semantic caching (avoid redundant generations)

**Research questions**:
- Can we replace RRF with a learned fusion model?
- What's the optimal chunk size for different document types?
- How much does re-ranking actually help on well-formed queries?

## Discussion

**Q: Why not use LlamaIndex's query engines?**

A: We need custom fusion logic. LlamaIndex's abstractions made it harder to plug in BM25 + TF-IDF alongside semantic search. Direct implementation gave us full control.

**Q: How do you handle document updates?**

A: Incremental reindexing. New docs get added to all three indexes. Old docs are versioned, not deleted. We rebuild indexes weekly to optimize.

**Q: What's your embedding model?**

A: text-embedding-3-small from OpenAI. Tried Cohere, Voyage, BGE. OpenAI was best balance of cost/performance for our domain. May fine-tune later.

**Q: How much does this cost?**

A: At 5K queries/day:
- Claude API: ~$45/day ($1,350/mo)
- Embedding API: ~$3/day ($90/mo)
- Infrastructure: ~$50/mo

Total: ~$1,500/mo. Acceptable for a production service.

**Q: Open source?**

A: Core engine is MIT licensed on GitHub. Production deployment configs and proprietary agents are closed-source.

## Try It

- **GitHub**: [ChunkyTortoise/docqa-engine](https://github.com/ChunkyTortoise/docqa-engine)
- **Live demo**: [ct-document-engine.streamlit.app](https://ct-document-engine.streamlit.app)
- **Paper** (if there's interest): I can write up a more formal evaluation with ablation studies

Happy to answer questions about implementation, evaluation, or production deployment.

---

**TL;DR**: Built production RAG with BM25 + TF-IDF + semantic search + RRF fusion + citation tracking. <200ms latency, 94% citation accuracy, 322 tests. No LangChain. Code on GitHub.
