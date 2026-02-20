# YouTube Script: Production RAG Pipeline

**Topic**: Production RAG Pipeline
**Format**: 6-7 minute video script with timestamps
**Target**: AI/ML engineers, Python developers
**Style**: Architecture diagrams + benchmark walkthrough

---

## Video Title Options

- "I Replaced LangChain With a Custom RAG Pipeline (29% Better Retrieval)"
- "Why Pure Vector Search Fails in Production RAG"
- "Building RAG That Actually Works: Hybrid Retrieval + Benchmarks"

## Thumbnail Text

"RAG THAT WORKS" with Precision@5 comparison chart (0.69 -> 0.89)

---

## Script

### [0:00 - 0:30] Hook

"Pure vector search confidently returns wrong results. And it's the number one failure mode in production RAG that nobody warns you about.

I rebuilt our RAG pipeline after LangChain hit a wall at 30 concurrent users. Hybrid retrieval with BM25, TF-IDF, and dense embeddings improved Precision at 5 by 29%. P95 latency under 200ms at 200 concurrent users.

Here's the full architecture and the benchmarks."

### [0:30 - 1:30] The Problem

"Here's what pure semantic search failure looks like.

[Show search example]

A user searches 'FHA loan requirements.' The embedding model returns chunks about 'VA loan benefits.' Why? Both are government-backed mortgage programs. The embeddings are close. The facts are completely different.

In a legal compliance context, returning VA loan info when someone asks about FHA is a liability. In any production context, it's a bad experience.

This failure mode is invisible in demos with 10 documents. It shows up at scale when your document set is large enough to have semantically similar but factually distinct content."

### [1:30 - 3:00] The Architecture

"The fix is hybrid retrieval. Instead of one search strategy, we run three in parallel.

[Show architecture diagram]

First, query expansion. The LLM generates 3 to 4 search variants from the user's question. 'FHA requirements' becomes 'FHA loan requirements', 'FHA mortgage eligibility criteria', 'Federal Housing Administration qualifications.' This improved recall by 18%.

Then three parallel search strategies:

BM25, keyword-exact matching. 'FHA' matches 'FHA', not 'VA'. Catches precise terminology that embeddings blur.

TF-IDF, statistical relevance. Weights rare terms higher. Good for document-level relevance.

Dense embeddings, semantic similarity. Catches paraphrases: 'home valuation' matches 'Comparative Market Analysis.'

Results are fused using Reciprocal Rank Fusion. Simple algorithm: each result gets a score based on its rank in each list, and the final ranking sorts by combined score.

After fusion: citation extraction. Every chunk gets tagged with source document, page number, and the exact passage used. Then the LLM generates an answer with inline citations."

### [3:00 - 4:30] Benchmarks

"Let me show you the numbers.

[Show retrieval quality table]

Precision at 5: BM25 alone gets 0.72. Dense embeddings alone get 0.69. Combining BM25 and dense: 0.84. Adding TF-IDF to the mix: 0.89. That last addition of TF-IDF was a surprisingly large boost.

[Show performance table]

Latency under load: P95 stays under 200 milliseconds up to 200 concurrent users. For context, the LangChain prototype was 800+ milliseconds at 30 users.

[Show citation accuracy]

Citation accuracy: 94.2% overall. Keyword queries like 'FHA requirements' are at 97%. Semantic queries like 'help me understand my mortgage options' are at 90%. Multi-document queries are at 91%.

The cache layer sits across every pipeline stage. 88% overall hit rate. Most queries never generate a new LLM call."

### [4:30 - 5:30] Key Decisions

"Three architecture decisions that mattered most.

Number one: Reciprocal Rank Fusion over cross-encoder re-ranking. Cross-encoders give slightly better ranking quality but add 200+ milliseconds per query. RRF has one parameter, k, and is essentially free in computation. At our latency budget, RRF wins.

Number two: Query expansion before retrieval. Generating 3-4 search variants costs one fast LLM call and runs in parallel with retrieval setup. 18% recall improvement for almost no latency cost.

Number three: Per-stage caching. Each step -- query expansion, retrieval, answer generation -- has its own cache. A repeat query hits the cache at the earliest possible stage. This is why our overall hit rate is 88%, not the 30-40% you'd get from only caching final answers."

### [5:30 - 6:00] When Not to Build This

"Quick reality check.

Under 1,000 documents: simple vector search is probably fine.
Non-critical accuracy: if wrong answers are inconvenient, not a liability, pure semantic works.
Prototype stage: use LangChain. Don't rebuild until you know what scale looks like.

This architecture makes sense when you have tens of thousands of documents, high accuracy requirements, and real concurrent users."

### [6:00 - 6:30] CTA

"Full source code with benchmark scripts is open source, link in the description. Clone the repo, run docker compose up, and run the benchmark suite yourself.

Next video: the 3-tier caching strategy that drives the 89% cost reduction across this pipeline. Thanks for watching."

---

## Description

How I replaced LangChain with a custom RAG pipeline using hybrid retrieval (BM25 + TF-IDF + dense embeddings). 29% improvement in Precision@5, P95 <200ms at 200 users, 94% citation accuracy.

Full source code: https://github.com/ChunkyTortoise/EnterpriseHub

Timestamps:
0:00 - The #1 RAG failure mode
0:30 - Why pure vector search fails
1:30 - Hybrid retrieval architecture
3:00 - Benchmarks (retrieval + performance + citations)
4:30 - Key architecture decisions
5:30 - When NOT to build this
6:00 - Open source code

#RAG #AIEngineering #Python #MachineLearning #InformationRetrieval
