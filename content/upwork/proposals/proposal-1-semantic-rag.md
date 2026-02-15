# Proposal 1: Senior GenAI Engineer for Semantic RAG and Word-Sense Disambiguation

**Job**: Senior GenAI Engineer for Semantic RAG and Word-Sense Disambiguation
**Bid**: $65/hr | **Fit**: 9/10 | **Connects**: 12-16
**Status**: Ready when funded — no Connects available

---

## Cover Letter

The distinction you draw between "RAG for chatbots" and "RAG for meaning-critical systems" is exactly right, and it's the same distinction I've been building around in production.

I built **docqa-engine** — a hybrid retrieval pipeline (BM25 + dense embeddings with reciprocal rank fusion) specifically because pure semantic search returns chunks that are *similar* but not *correct*. For your word-sense disambiguation problem, that precision gap is the whole ballgame. I've tested retrieval quality across **94 automated scenarios** measuring precision@k, recall@k, and MRR at each pipeline stage.

On the constrained LLM orchestration side, my production platform (**EnterpriseHub**, ~5,100 tests) runs a multi-strategy parser with JSON-only outputs, confidence scoring, and explicit fallback chains. The system decides rules-vs-LLM per request based on input characteristics — not a blanket "send everything to GPT." I've also built deterministic variant assignment and enum-based decision routing in my bot orchestration layer.

For your ASR-to-gesture pipeline, I'd focus on:

1. **Embedding strategy tuned for short, ambiguous phrases** rather than document chunks — standard 512-token chunking destroys context for 3-5 word ASR outputs
2. **Confidence-gated LLM calls** so noisy ASR input doesn't produce hallucinated gestures — my system uses a 0.7 confidence threshold before escalating to more expensive models
3. **Fast FAISS index for sub-50ms nearest-meaning lookup** — I've benchmarked P50/P95/P99 latency across all my retrieval pipelines

### Portfolio Evidence

| Metric | Value | Source |
|--------|-------|--------|
| Hybrid retrieval pipeline | BM25 + dense + RRF | docqa-engine (500+ tests) |
| JSON-only LLM orchestration | Multi-strategy parser | EnterpriseHub (~5,100 tests) |
| Cache-driven cost reduction | 89% fewer LLM calls | 3-tier Redis (88% hit rate) |
| Retrieval quality testing | 94 automated scenarios | precision@k, recall@k, MRR |
| Production latency | P99 < 0.1ms orchestration | Benchmarked with P50/P95/P99 |

**Portfolio**: https://chunkytortoise.github.io | **GitHub**: https://github.com/ChunkyTortoise

---

*Ready to submit when Connects are purchased ($12 for 80 Connects).*
