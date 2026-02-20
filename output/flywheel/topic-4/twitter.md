# Twitter/X Thread: Production RAG Pipeline

**Topic**: Production RAG Pipeline
**Format**: 7-tweet thread
**CTA**: GitHub repo link

---

## Tweet 1 (Hook)

LangChain broke at 30 concurrent users.

We rebuilt our RAG pipeline from scratch for 200+ concurrent conversations, 50K+ documents, and sub-second response times.

Here's the architecture and the benchmarks:

[thread]

---

## Tweet 2 (The Problem)

LangChain was great for prototyping. In production:

- 50+ dependencies with version conflicts
- Performance wall at 30 users
- No fine-grained retrieval control
- 12+ abstraction layers to debug

We needed <200ms P95 at 10 req/sec with 94%+ citation accuracy.

---

## Tweet 3 (Key Insight)

Pure semantic search confidently returns wrong results.

"FHA loan requirements" matched "VA loan benefits" -- semantically close, factually wrong.

This is the #1 RAG failure mode nobody warns you about.

---

## Tweet 4 (Hybrid Retrieval)

The fix: hybrid retrieval with 3 strategies in parallel.

- BM25: Keyword-exact matching
- TF-IDF: Statistical relevance
- Dense embeddings: Semantic similarity

Fused with Reciprocal Rank Fusion.

Result: Precision@5 improved 34%.

---

## Tweet 5 (Full Pipeline)

Full pipeline:

1. Query expansion (LLM generates 3-4 search variants)
2. Parallel hybrid retrieval (BM25 + TF-IDF + dense)
3. Reciprocal Rank Fusion
4. Citation extraction (doc, page, passage)
5. Grounded answer generation

Each step has its own cache layer. 88% overall hit rate.

---

## Tweet 6 (Benchmarks)

Production benchmarks (200+ concurrent users):

- P95 latency: <200ms @ 10 req/sec
- Citation accuracy: 94.2%
- Cache hit rate: 88%
- Tests: 500+, 85% coverage

LangChain prototype: 800ms+ P95 @ 30 users.
Custom pipeline: <200ms P95 @ 200+ users.

---

## Tweet 7 (CTA)

3 RAG lessons from production:

1. Hybrid search is non-negotiable. Pure vector = confident hallucinations.
2. Citations are a feature, not debugging. Users trust sourced answers.
3. LangChain for prototyping, custom for production.

Full code: github.com/ChunkyTortoise/EnterpriseHub

What's your RAG stack?
