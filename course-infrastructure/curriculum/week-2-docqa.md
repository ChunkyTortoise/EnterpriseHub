# Week 2: RAG Systems (DocQA)

## Overview

This week covers Retrieval-Augmented Generation from ingestion to evaluation. Students build a document Q&A system with hybrid search and measurable retrieval quality.

**Repo**: DocQA-Insight
**Lab**: Build a document Q&A system with hybrid search and evaluation

## Learning Objectives

By the end of this week, students will be able to:
1. Design a document ingestion pipeline with appropriate chunking strategies
2. Implement hybrid search combining BM25 keyword and vector semantic retrieval
3. Apply score fusion techniques to merge results from multiple retrievers
4. Build evaluation metrics (precision@k, recall@k, MRR) for retrieval quality
5. Optimize chunk size and overlap based on evaluation results

## Session A: Concepts + Live Coding (Tuesday)

### Part 1: RAG Architecture (15 min)

**The RAG pipeline:**
```
Documents → Chunk → Embed → Index → Query → Retrieve → Re-rank → Generate → Respond
```

**Key decisions at each stage:**
- Chunking: fixed-size vs semantic vs recursive (trade-offs)
- Embedding: OpenAI ada-002 vs local models vs domain-specific
- Index: pgvector (PostgreSQL) vs FAISS vs Pinecone (trade-offs)
- Retrieval: dense (vector) vs sparse (BM25) vs hybrid
- Re-ranking: cross-encoder vs LLM-based vs none

### Part 2: Live Coding — Document Ingestion Pipeline (45 min)

1. **Document loading** (10 min)
   - Parse PDF, markdown, and plain text
   - Extract metadata (title, author, date, source)
   - Handle encoding issues and malformed documents

2. **Chunking strategies** (15 min)
   - Fixed-size: 512 tokens with 50-token overlap
   - Recursive: split by headings, then paragraphs, then sentences
   - Semantic: group sentences by embedding similarity
   - Live demo: compare chunk quality across strategies

3. **Embedding and indexing** (10 min)
   - Generate embeddings with batch processing
   - Store in PostgreSQL with pgvector extension
   - Create HNSW index for fast approximate nearest neighbor search

4. **Hybrid retrieval** (10 min)
   - BM25: keyword matching with tf-idf scoring
   - Vector: cosine similarity on embeddings
   - Score fusion: Reciprocal Rank Fusion (RRF) to merge results

### Part 3: Lab Introduction (15 min)

- Lab 2 README walkthrough
- Codespace with pgvector pre-configured
- Sample document corpus provided (technical documentation)
- Autograder tests: retrieval quality thresholds

### Part 4: Q&A (15 min)

## Session B: Lab Review + Deep Dive (Thursday)

### Part 1: Lab Solution Review (20 min)

Common patterns and mistakes:
- Chunk sizes too large (low precision) or too small (lost context)
- Not normalizing scores before fusion (BM25 and vector scores on different scales)
- Missing metadata in retrieval results (no source attribution)
- Evaluation on training data instead of held-out test set

### Part 2: Deep Dive — Hybrid Search (40 min)

**BM25 in-depth:**
- Term frequency, inverse document frequency, document length normalization
- When BM25 beats vector search: exact keyword matching, technical terms, proper nouns
- Implementation: rank-bm25 library or PostgreSQL full-text search

**Vector search in-depth:**
- Embedding space geometry: cosine similarity vs L2 distance
- When vectors beat BM25: paraphrases, semantic queries, cross-language
- Index types: flat (exact), IVF (approximate), HNSW (approximate, fast)

**Fusion strategies:**
- Reciprocal Rank Fusion (RRF): `score = sum(1 / (k + rank_i))` across retrievers
- Weighted linear combination: `score = w1 * bm25_norm + w2 * vector_norm`
- How to tune weights: grid search on evaluation set

**Evaluation metrics:**
- Precision@k: Of the top-k results, how many are relevant?
- Recall@k: Of all relevant documents, how many appear in top-k?
- Mean Reciprocal Rank: How high is the first relevant result?
- Building a test set: manually label 50-100 query-document pairs

### Part 3: Production Case Study (20 min)

How DocQA handles 1000+ documents in production:
- Incremental ingestion (don't re-embed unchanged documents)
- Cache frequently-asked queries
- Monitor retrieval quality over time (drift detection)
- A/B test retrieval strategies in production

### Part 4: Week 3 Preview (10 min)

## Key Takeaways

1. RAG quality depends more on retrieval than generation
2. Hybrid search (BM25 + vector) outperforms either alone for most use cases
3. Always evaluate retrieval quality with labeled test data
4. Chunk size is the most impactful hyperparameter — tune it empirically
5. Production RAG needs incremental updates, caching, and monitoring

## Resources

- DocQA-Insight repository
- pgvector documentation
- "Hybrid Search" research paper references (provided in Discord)
- rank-bm25 library documentation
