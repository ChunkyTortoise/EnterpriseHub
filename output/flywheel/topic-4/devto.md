---
title: "Building a Production RAG Pipeline That Actually Works: Hybrid Retrieval + Benchmarks"
published: false
tags: python, ai, rag, machinelearning
cover_image:
canonical_url:
---

# Building a Production RAG Pipeline That Actually Works: Hybrid Retrieval + Benchmarks

I spent 6 months building a production RAG system for a real estate AI platform managing a $50M+ pipeline. 50K+ documents, 200+ concurrent conversations, sub-second response requirements, and 94%+ citation accuracy for legal compliance.

After testing LangChain, multiple vector databases, and 3 different retrieval strategies, here's what actually works in production -- with benchmarks.

---

## Why LangChain Didn't Cut It

We started with LangChain. Prototype was running in 2 days. Great DX. Then we hit production reality:

- **50+ dependencies** with conflicting version requirements
- **Performance wall at 30 concurrent users** (P95 latency spiked to 800ms+)
- **No fine-grained retrieval control** (the abstraction layers prevented tuning)
- **Debugging nightmare** (12+ layers deep to find where a query went wrong)

We needed <200ms P95 at 10 req/sec with 94%+ citation accuracy. LangChain's abstractions were fighting us at every step.

Decision: rebuild the retrieval pipeline from scratch, keeping only the core dependencies (embedding model, vector store, LLM client).

## The #1 RAG Failure Mode: Confidently Wrong

Before discussing the solution, let me explain the problem that drove the architecture.

Pure semantic search returns results that are semantically similar but factually wrong. A user searching for "FHA loan requirements" would get results about "VA loan benefits" -- the embeddings are close (both are government-backed mortgage programs), but the facts are completely different.

In a legal compliance context, returning VA loan info when someone asks about FHA loans is not just unhelpful -- it's potentially a liability.

This is the most common RAG failure mode in production, and pure vector search has no solution for it.

## The Architecture: Hybrid Retrieval

```
User Query
    |
    v
Query Expansion (LLM generates 3-4 search variants)
    |
    v
Parallel Retrieval:
    [BM25 keyword search]
    [TF-IDF statistical search]
    [Dense embedding semantic search]
    |
    v
Reciprocal Rank Fusion (merge + re-rank)
    |
    v
Citation Extraction (source doc, page number, passage)
    |
    v
Answer Generation (grounded, with inline citations)
```

### Query Expansion

A single user query becomes 3-4 search variants:

```python
async def expand_query(query: str) -> list[str]:
    """Generate search variants for better recall."""
    variants = await llm.generate(
        f"Generate 3 alternative search queries for: {query}"
    )
    return [query] + variants  # Original + expansions
```

"What are FHA loan requirements?" becomes:
- "FHA loan requirements" (original)
- "FHA mortgage eligibility criteria"
- "Federal Housing Administration loan qualifications"
- "FHA down payment and credit score requirements"

This improves recall by catching documents that use different terminology.

### Parallel Hybrid Retrieval

Three search strategies run in parallel:

**BM25 (keyword-exact):** Best for precise terminology. "FHA" matches "FHA", not "VA". Catches exact terms that embeddings might blur.

**TF-IDF (statistical):** Good for document-level relevance. Weights rare terms higher. Complements BM25 by considering document context.

**Dense Embeddings (semantic):** Catches paraphrases and conceptual matches. "home valuation" matches "CMA" (Comparative Market Analysis).

### Reciprocal Rank Fusion

Results from all three strategies are merged using RRF:

```python
def reciprocal_rank_fusion(results: list[list[Document]], k: int = 60) -> list[Document]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion."""
    scores = defaultdict(float)
    for result_list in results:
        for rank, doc in enumerate(result_list):
            scores[doc.id] += 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

RRF is simple, parameter-light (only `k`), and consistently outperforms learned re-ranking in our benchmarks.

### Citation Extraction

Every answer includes source references:

```python
@dataclass
class Citation:
    document_name: str
    page_number: int
    passage: str  # The exact text passage used
    confidence: float
```

Users see: *"Based on MLS Report #4521 (Page 3): The median home price in Rancho Cucamonga increased 4.2% year-over-year..."*

This isn't just UX polish. In regulated industries, sourced answers are a compliance requirement.

## Benchmarks

### Retrieval Quality

| Strategy | Precision@5 | Recall@10 | MRR |
|----------|-------------|-----------|-----|
| BM25 only | 0.72 | 0.64 | 0.68 |
| Dense only | 0.69 | 0.78 | 0.71 |
| Hybrid (BM25+Dense) | 0.84 | 0.82 | 0.86 |
| **Hybrid (BM25+TF-IDF+Dense)** | **0.89** | **0.85** | **0.91** |

Adding TF-IDF to the hybrid mix improved Precision@5 by 5 points over BM25+Dense alone.

### Performance Under Load

| Concurrent Users | P50 | P95 | P99 |
|-----------------|-----|-----|-----|
| 10 | 45ms | 120ms | 180ms |
| 50 | 62ms | 155ms | 210ms |
| 100 | 78ms | 185ms | 260ms |
| 200 | 95ms | 198ms | 310ms |

P95 stays under 200ms up to 200 concurrent users.

### Citation Accuracy

- **Overall**: 94.2% (measured against human-labeled test set of 500 queries)
- **Keyword queries** ("FHA requirements"): 97.1%
- **Semantic queries** ("help me understand my mortgage options"): 89.8%
- **Multi-document queries** ("compare FHA vs. VA loans"): 91.3%

### Cost

3-tier caching (L1 in-process, L2 Redis, L3 Postgres) achieves 88% hit rate, reducing LLM costs by 89%.

## Key Lessons

### 1. Hybrid search is non-negotiable for production

Pure vector search will confidently return wrong results. BM25 catches exact terminology that embeddings blur. You need both.

### 2. Citations are a product feature

Users trust answers when they see the source. "According to [document], [page]..." transforms RAG from a black box into a research assistant. In regulated industries, it's a compliance requirement.

### 3. Query expansion is high-ROI

Generating 3-4 search variants per query improved recall by 18% with minimal latency cost (the LLM call is fast, and it parallelizes with retrieval).

### 4. LangChain for prototyping, custom for production

LangChain gets you to demo in 2 days. Custom pipelines get you to production. The middle ground -- LangChain in production with workarounds -- is the worst of both worlds.

### 5. Cache at every layer

Each pipeline stage has its own cache: query expansion results, retrieval results, and generated answers. 88% overall hit rate means most queries never touch the LLM.

## Try It

Full source code with benchmark scripts: [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub)

```bash
git clone https://github.com/ChunkyTortoise/EnterpriseHub.git
cd EnterpriseHub
docker compose up -d
python benchmarks/rag_performance.py
```

---

*Building RAG systems? Connect on [LinkedIn](https://linkedin.com/in/caymanroden) or check my [other projects](https://github.com/ChunkyTortoise). Currently working on a lightweight multi-LLM orchestration framework (AgentForge) launching Feb 24.*
