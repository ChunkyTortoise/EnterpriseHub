# Reddit Post: Production RAG Pipeline

**Topic**: Production RAG Pipeline
**Subreddit**: r/MachineLearning or r/Python
**Format**: Technical discussion with benchmarks
**Flair**: [Project]

---

## Title

I replaced LangChain with a custom RAG pipeline. Hybrid retrieval (BM25 + TF-IDF + dense) improved Precision@5 by 29%. Benchmarks and code included.

## Body

**tl;dr**: Built a production RAG system for 50K+ documents, 200+ concurrent users. Pure vector search was confidently returning wrong results. Hybrid retrieval with Reciprocal Rank Fusion fixed it. P95 <200ms, 94% citation accuracy. Open source.

---

**Context**: Real estate AI platform. 50K+ documents (MLS listings, market reports, client notes). 200+ concurrent conversations. Legal compliance requires 94%+ citation accuracy. Started with LangChain, hit performance walls at 30 concurrent users.

**The core problem with pure semantic search**:

"FHA loan requirements" returned chunks about "VA loan benefits." Both are government-backed mortgage programs. Embeddings are close. Facts are completely different.

This failure mode is invisible in small demos. It shows up at scale when your document set contains semantically similar but factually distinct content.

**Hybrid retrieval architecture**:

```
Query -> Expansion (LLM: 3-4 search variants)
      -> Parallel:
         [BM25 keyword search]
         [TF-IDF statistical search]
         [Dense embedding search]
      -> Reciprocal Rank Fusion
      -> Citation extraction (doc, page, passage)
      -> Grounded answer generation
```

**Retrieval quality benchmarks**:

| Strategy | Precision@5 | Recall@10 | MRR |
|----------|-------------|-----------|-----|
| BM25 only | 0.72 | 0.64 | 0.68 |
| Dense only | 0.69 | 0.78 | 0.71 |
| BM25 + Dense | 0.84 | 0.82 | 0.86 |
| **BM25 + TF-IDF + Dense** | **0.89** | **0.85** | **0.91** |

Adding TF-IDF provided a surprisingly large boost (+5 P@5 points over BM25+Dense alone).

**Performance benchmarks**:

| Concurrent Users | P50 | P95 | P99 |
|-----------------|-----|-----|-----|
| 10 | 45ms | 120ms | 180ms |
| 50 | 62ms | 155ms | 210ms |
| 100 | 78ms | 185ms | 260ms |
| 200 | 95ms | 198ms | 310ms |

LangChain prototype: 800ms+ P95 at 30 users.

**Citation accuracy**: 94.2% overall. Keyword queries: 97.1%. Semantic queries: 89.8%. Multi-doc queries: 91.3%.

**Key design decisions**:

1. **Reciprocal Rank Fusion over learned re-ranking**: RRF is parameter-light (only k=60), consistent, and doesn't require training data. Cross-encoder re-ranking was 200ms+ overhead per query -- unacceptable.

2. **Query expansion**: LLM generates 3-4 search variants per query. Improved recall by 18% with minimal latency cost (parallelizes with retrieval).

3. **Per-stage caching**: Each pipeline stage (expansion, retrieval, generation) has its own cache. 88% overall hit rate. Most queries never touch the LLM.

4. **Citation as first-class feature**: Every chunk tagged with source document, page number, exact passage. Users see inline citations in answers.

**Lessons**:
- Pure vector search WILL hallucinate confidently at scale. Hybrid is non-negotiable.
- LangChain for prototyping, custom for production. The middle ground is painful.
- Cache at every pipeline stage, not just the final output.
- Query expansion is highest-ROI enhancement (18% recall improvement for minimal cost).

**Code**: [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub)

```bash
docker compose up -d && python benchmarks/rag_performance.py
```

Happy to discuss the hybrid retrieval implementation, RRF tuning, or how citation extraction works in practice.
