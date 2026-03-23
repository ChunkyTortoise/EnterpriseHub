# Newsletter Edition: What Production RAG Actually Looks Like

**Topic**: Production RAG Pipeline
**Format**: Email newsletter (800-1,200 words)
**Subject line options**:
- "LangChain broke at 30 users. Here's what replaced it."
- "The RAG failure mode nobody warns you about"
- "94% citation accuracy at 200 concurrent users -- the architecture"

---

Hey,

Everyone is building RAG right now. Most of it breaks in production. Here's what I learned running a RAG pipeline for 6 months at scale.

---

## The Failure Mode Nobody Warns You About

Pure vector search returns results that are semantically similar but factually wrong.

Real example: A user searches "FHA loan requirements." The embedding model returns chunks about "VA loan benefits." Why? Both are government-backed mortgage programs. The embeddings are close. The facts are completely different.

In a legal compliance context, this isn't just unhelpful -- it's a liability.

This is the #1 production RAG failure mode, and you won't catch it in your demo with 10 documents. It shows up at scale when your document set is large enough to have semantically similar but factually distinct content.

## The Fix: Hybrid Retrieval

We run three search strategies in parallel:

**BM25 (keyword-exact)**: "FHA" matches "FHA", not "VA". Catches precise terminology that embeddings blur.

**TF-IDF (statistical)**: Weights rare terms higher. Good for document-level relevance.

**Dense embeddings (semantic)**: Catches paraphrases. "Home valuation" matches "CMA" (Comparative Market Analysis).

Results are fused using Reciprocal Rank Fusion -- a simple algorithm that merges ranked lists by giving credit for high placement across any strategy.

The numbers: Precision@5 improved from 0.69 (dense-only) to 0.89 (hybrid). That's a 29% improvement from adding two parallel search strategies.

## What a Production Pipeline Looks Like

Our full pipeline:

1. **Query expansion**: The LLM generates 3-4 search variants from the user's question. "FHA requirements" becomes ["FHA loan requirements", "FHA mortgage eligibility", "Federal Housing Administration qualifications", "FHA down payment credit score"]. This improved recall by 18%.

2. **Parallel hybrid retrieval**: BM25 + TF-IDF + dense embeddings run simultaneously.

3. **Reciprocal Rank Fusion**: Merge and re-rank results.

4. **Citation extraction**: Every chunk gets tagged with source document, page number, and exact passage.

5. **Grounded answer generation**: The LLM generates an answer with inline citations: "According to MLS Report #4521 (Page 3)..."

Each stage has its own cache layer. 88% overall hit rate. Most queries never touch the LLM.

## The Numbers After 6 Months

- P95 latency: <200ms at 200 concurrent users
- Citation accuracy: 94.2%
- Cache hit rate: 88%
- LLM cost reduction: 89% (from caching)
- 500+ tests, 85% coverage

For context: the LangChain prototype hit 800ms+ P95 at 30 concurrent users. Same queries, same documents.

## Three Lessons

**1. Hybrid search is non-negotiable.** Pure vector search will confidently hallucinate. BM25 catches exact matches that embeddings miss. If you're only using dense retrieval, you're one edge case away from a bad answer.

**2. Citations transform user trust.** When users see "Source: [document], [page]," they trust the answer. When they see a generated paragraph with no source, they don't. In regulated industries, citations are a compliance requirement. In all industries, they're a product feature.

**3. LangChain for prototyping, custom for production.** LangChain gets you to demo in 2 days. But its abstractions fight you in production -- 50+ dependencies, 12+ layers to debug, performance walls at modest scale. Build your prototype with LangChain, then rebuild the retrieval pipeline for production.

## When You Don't Need This

- Under 1,000 documents: Simple vector search is probably fine.
- Non-critical accuracy requirements: If wrong answers are merely inconvenient (not a liability), pure semantic search works.
- Prototype/demo stage: Use LangChain. Don't rebuild until you know what scale looks like.

Full implementation: [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub)

Reply if you're building RAG -- I'm curious what retrieval strategy you're using.

Cayman
