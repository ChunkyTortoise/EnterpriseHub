# DocQA Engine RAG Optimization Guide

## A Comprehensive Guide to Building Production-Ready RAG Pipelines

This guide covers every stage of a Retrieval-Augmented Generation pipeline, from document ingestion to answer quality measurement. Based on DocQA Engine's architecture (550+ tests, 26 test files) and production deployment experience.

---

## Table of Contents

1. [RAG Pipeline Architecture](#1-rag-pipeline-architecture)
2. [Document Ingestion Best Practices](#2-document-ingestion-best-practices)
3. [Chunking Strategies](#3-chunking-strategies)
4. [Embedding Selection](#4-embedding-selection)
5. [Retrieval Methods](#5-retrieval-methods)
6. [Hybrid Search with RRF](#6-hybrid-search-with-rrf)
7. [Query Expansion Techniques](#7-query-expansion-techniques)
8. [Re-Ranking for Precision](#8-re-ranking-for-precision)
9. [Context Compression](#9-context-compression)
10. [Answer Generation](#10-answer-generation)
11. [Citation Scoring](#11-citation-scoring)
12. [Multi-Turn Conversations](#12-multi-turn-conversations)
13. [Evaluation Metrics](#13-evaluation-metrics)
14. [Cost Optimization](#14-cost-optimization)
15. [Production Deployment](#15-production-deployment)

---

## 1. RAG Pipeline Architecture

DocQA Engine implements a multi-stage RAG pipeline:

```
Document Upload -> Chunking -> Embedding -> Vector Store -> Retrieval -> Re-Ranking -> Answer Generation -> Citation Scoring
```

### The DocQAPipeline Class

The simplest way to use the full pipeline:

```python
from docqa_engine.pipeline import DocQAPipeline

pipeline = DocQAPipeline(vector_backend="memory")

# Ingest documents
pipeline.ingest("contracts/master_agreement.pdf")
pipeline.ingest_text("Additional context here", filename="context.txt")

# Ask questions
answer = await pipeline.ask("What are the termination clauses?", top_k=10)
print(answer.text)
print(answer.citations)
```

The pipeline automatically:
- Detects file format (PDF, DOCX, TXT, MD, CSV)
- Chunks documents using configurable strategies
- Fits TF-IDF embeddings (refits lazily when new documents are added)
- Builds hybrid retrieval index (BM25 + Dense)
- Generates answers with citations

---

## 2. Document Ingestion Best Practices

### Supported Formats

DocQA Engine's ingest module handles five document formats:

```python
from docqa_engine.ingest import ingest_file, ingest_txt

# File-based ingestion (auto-detects format)
result = ingest_file("document.pdf")   # PDF (PyPDF2)
result = ingest_file("document.docx")  # Word (python-docx)
result = ingest_file("document.txt")   # Plain text
result = ingest_file("document.md")    # Markdown
result = ingest_file("data.csv")       # CSV (tabular)

# Text-based ingestion
result = ingest_txt("Raw text content here", filename="notes.txt")

# Result contains:
print(result.filename)      # Original filename
print(result.content)       # Full extracted text
print(len(result.chunks))   # Number of chunks
```

### Ingestion Tips

| Tip | Why |
|-----|-----|
| Ingest PDFs with selectable text | Scanned PDFs require OCR preprocessing |
| Remove headers/footers before ingestion | Page numbers and footers add noise to chunks |
| Preserve document structure | Section headings improve semantic chunking |
| Track source metadata | Store filename, page number, section for citations |

---

## 3. Chunking Strategies

Chunking quality directly impacts retrieval accuracy. DocQA Engine offers three strategies:

### Fixed-Size Chunking

Best for uniform documents (logs, transcripts):

```python
from docqa_engine.chunking import Chunker

chunker = Chunker()

result = chunker.fixed_size(
    text=document_text,
    chunk_size=500,   # Characters per chunk
    overlap=50        # Character overlap between chunks
)

print(f"Strategy: {result.strategy}")
print(f"Total chunks: {result.total_chunks}")
print(f"Avg chunk size: {result.avg_chunk_size:.0f} chars")
```

The fixed-size chunker respects word boundaries -- it will not split mid-word. It backs up to the last whitespace character when a chunk boundary falls inside a word.

### Sentence-Boundary Chunking

Best for narrative documents (reports, articles):

```python
result = chunker.sentence_boundary(
    text=document_text,
    max_chunk_size=800,
    min_chunk_size=100
)
# Chunks break at sentence endings (., !, ?)
# Never splits mid-sentence
```

### Semantic Chunking

Best for structured documents (contracts, guidelines):

```python
result = chunker.semantic(
    text=document_text,
    max_chunk_size=800,
    min_chunk_size=100
)
# Chunks break at section boundaries (headings, paragraph breaks)
# Keeps related content together
```

### Strategy Comparison

Use the built-in comparison feature:

```python
comparison = chunker.compare_strategies(document_text, chunk_size=500)
print(f"Best strategy: {comparison.best_strategy}")
print(f"Best avg size: {comparison.best_avg_size:.0f} chars")

for name, result in comparison.results.items():
    print(f"{name}: {result.total_chunks} chunks, avg {result.avg_chunk_size:.0f} chars")
```

### Chunking Guidelines

| Document Type | Recommended Strategy | Chunk Size | Overlap |
|--------------|---------------------|------------|---------|
| Legal contracts | Semantic | 800 chars | 100 |
| Research papers | Sentence-boundary | 600 chars | 75 |
| Technical docs | Semantic | 500 chars | 50 |
| Chat transcripts | Fixed-size | 400 chars | 50 |
| CSV/tabular | Fixed-size (by rows) | 20 rows | 2 |

### Impact on Retrieval

From production deployments:

| Chunking Strategy | Precision@5 Impact | Notes |
|-------------------|-------------------|-------|
| Fixed-size (no overlap) | Baseline | Splits mid-concept |
| Fixed-size (50 char overlap) | +5-8% | Overlap recovers context |
| Sentence-boundary | +10-15% | Natural breaks |
| Semantic | +15-20% | Section-aware splits |

---

## 4. Embedding Selection

### TF-IDF: The Zero-Cost Option

DocQA Engine uses TF-IDF embeddings by default -- no external API required:

```python
from docqa_engine.embedder import TfidfEmbedder, embed_fn_factory

embedder = TfidfEmbedder(max_features=5000)

# Fit on your corpus
texts = [chunk.content for chunk in all_chunks]
embedder.fit(texts)

# Generate embeddings
embeddings = embedder.embed(texts)
# Shape: (num_chunks, 5000)

# Create reusable embed function
embed_fn = embed_fn_factory(embedder)
query_embedding = embed_fn("What are the payment terms?")
```

### TF-IDF vs Cloud Embeddings

| Feature | TF-IDF (DocQA) | OpenAI ada-002 | Cohere embed-v3 |
|---------|---------------|----------------|-----------------|
| Cost | $0.00 | $0.10/1M tokens | $0.10/1M tokens |
| Latency | <1ms | 50-200ms | 50-200ms |
| Data privacy | 100% local | Data sent to API | Data sent to API |
| Quality (general) | Good | Excellent | Excellent |
| Quality (domain-specific) | Very good (after fitting) | Good | Good |
| Dimension | Configurable (default 5000) | 1536 | 1024 |

Key insight: TF-IDF embeddings fitted on your specific corpus often outperform general-purpose cloud embeddings for domain-specific retrieval, because they learn the vocabulary of your documents.

---

## 5. Retrieval Methods

DocQA Engine supports three retrieval methods:

### BM25 (Keyword Retrieval)

Okapi BM25 excels at exact keyword matching:

```python
from docqa_engine.retriever import BM25Index

bm25 = BM25Index(k1=1.5, b=0.75)
bm25.add_chunks(chunks)

results = bm25.search("indemnification clause", top_k=10)
for r in results:
    print(f"Score: {r.score:.3f} | {r.chunk.content[:100]}")
```

BM25 scoring formula:
```
score(q, d) = sum(IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl)))
```

Where:
- `k1=1.5`: Term frequency saturation parameter
- `b=0.75`: Document length normalization
- `IDF`: Inverse document frequency (log-scaled)

### Dense Retrieval (Semantic)

TF-IDF cosine similarity captures semantic relationships:

```python
from docqa_engine.vector_store import create_vector_store

store = create_vector_store("memory")
store.add(embeddings, chunks)

results = store.search(query_embedding, top_k=10)
```

### Hybrid Retrieval (BM25 + Dense + RRF)

The recommended approach combines both methods:

```python
from docqa_engine.retriever import HybridRetriever

retriever = HybridRetriever(embed_fn=embed_fn, dense_backend=store)
retriever.add_chunks(chunks, embeddings)

results = retriever.search(
    query="maximum financial exposure",
    top_k=10,
    method="hybrid"  # "bm25", "dense", or "hybrid"
)
```

---

## 6. Hybrid Search with RRF

Reciprocal Rank Fusion (RRF) is the key to DocQA Engine's retrieval quality.

### How RRF Works

RRF combines rankings from multiple retrieval methods without needing to normalize scores:

```
RRF_score(d) = sum(1 / (k + rank_i(d))) for each retrieval method i
```

Where `k = 60` is a constant that prevents top-ranked documents from dominating.

### Why RRF Outperforms Individual Methods

| Query Type | BM25 | Dense | Hybrid (RRF) | Winner |
|-----------|------|-------|-------------|--------|
| Exact keyword | Excellent | Good | Excellent | BM25 ≈ Hybrid |
| Semantic/synonym | Poor | Excellent | Very Good | Dense ≈ Hybrid |
| Mixed (keyword + concept) | Good | Good | Excellent | **Hybrid wins** |

### Benchmark Results (from DocQA Engine)

| Metric | BM25 Only | Hybrid (BM25 + Dense + RRF) | Improvement |
|--------|-----------|------------------------------|-------------|
| Precision@5 | 24.0% | 29.3% | **+22%** |
| Semantic Query Hit Rate | 67% | 89% | **+33%** |
| Keyword Query Hit Rate | 95%+ | 95%+ | Maintained |

The +33% improvement on semantic queries is the main value of hybrid search. It means queries using different terminology than the source documents still find relevant passages.

---

## 7. Query Expansion Techniques

DocQA Engine's query expansion module enriches queries before retrieval:

### Synonym Expansion

```python
from docqa_engine.query_expansion import expand_query, ExpansionStrategy

expanded = expand_query(
    "liability cap",
    strategy=ExpansionStrategy.SYNONYM
)
# "liability cap maximum exposure aggregate damages ceiling"
```

### Pseudo-Relevance Feedback (PRF)

PRF retrieves top results, extracts key terms, and re-queries:

```python
expanded = expand_query(
    "revenue recognition",
    strategy=ExpansionStrategy.PRF,
    retriever=retriever,
    top_k_feedback=3  # Use top 3 results for expansion
)
# Adds terms from top results: "ASC 606", "performance obligation", etc.
```

### Query Decomposition

For complex questions, decompose into sub-queries:

```python
expanded = expand_query(
    "What is the buyer's maximum recovery after applying indemnification cap and insurance offset?",
    strategy=ExpansionStrategy.DECOMPOSE
)
# Sub-queries:
# 1. "indemnification cap amount"
# 2. "insurance offset provision"
# 3. "buyer recovery calculation"
```

---

## 8. Re-Ranking for Precision

After initial retrieval, re-ranking reorders results for better precision:

```python
from docqa_engine.reranker import CrossEncoderReranker

reranker = CrossEncoderReranker()

# Re-rank top 20 results to find best 5
initial_results = retriever.search(query, top_k=20)
reranked = reranker.rerank(query, initial_results, top_k=5)
```

### Re-Ranking Performance Impact (from BENCHMARKS.md)

| Metric | Without Re-Ranking | With Re-Ranking | Improvement |
|--------|-------------------|-----------------|-------------|
| Relevance | Baseline | +8-12% | Significant |
| Ranking quality (Kendall tau) | 0.65 | 0.82 | +26% |

### When to Re-Rank

| Scenario | Re-Rank? | Why |
|----------|----------|-----|
| Top-5 results, small corpus | No | Overhead not worth it |
| Top-5 from top-20, large corpus | Yes | Significant precision gain |
| Latency-critical (<50ms budget) | No | Re-ranking adds 10-30ms |
| Quality-critical (legal, medical) | Yes | +8-12% relevance improvement |

---

## 9. Context Compression

When retrieved passages exceed the LLM's context window or token budget:

```python
from docqa_engine.context_compressor import ContextCompressor

compressor = ContextCompressor(max_tokens=4096)

# Compress 20 retrieved passages to fit budget
compressed = compressor.compress(
    passages=retrieved_results,
    query=query,
    strategy="relevance"  # Keep most relevant, trim others
)
```

### Compression Strategies

| Strategy | Behavior | Best For |
|----------|----------|----------|
| Relevance | Keep highest-scoring passages | General use |
| Summary | Summarize each passage | Long documents |
| Truncate | Cut passages to fit | Speed-critical |

### Token Budget Guidelines

| LLM Model | Max Context | Recommended Budget | Reasoning Headroom |
|-----------|-------------|-------------------|-------------------|
| GPT-4o Mini | 128K | 8K context | 2K output |
| Claude 3.5 Sonnet | 200K | 16K context | 4K output |
| Gemini 1.5 Pro | 1M | 32K context | 8K output |

---

## 10. Answer Generation

DocQA Engine's answer module generates cited answers from retrieved context:

```python
from docqa_engine.answer import generate_answer, build_context

# Build context from retrieved passages
context = build_context(retrieved_results)

# Generate answer with citations
answer = generate_answer(
    question="What are the payment terms?",
    context=context,
    model="claude-3-5-sonnet"  # Or any supported model
)

print(answer.text)
print(answer.citations)  # Source passages with page/section references
```

### Answer Quality Scoring

```python
from docqa_engine.answer_quality import score_answer_quality

quality = score_answer_quality(answer)
print(f"Completeness: {quality.completeness:.2f}")
print(f"Conciseness: {quality.conciseness:.2f}")
print(f"Relevance: {quality.relevance:.2f}")
```

---

## 11. Citation Scoring

DocQA Engine's citation scoring framework measures three dimensions:

```python
from docqa_engine.citation_scorer import score_citations

scores = score_citations(answer.citations, answer.text)

print(f"Faithfulness: {scores.faithfulness:.2f}")  # Answer supported by sources?
print(f"Coverage: {scores.coverage:.2f}")           # Sources address full question?
print(f"Redundancy: {scores.redundancy:.2f}")       # Sources diverse (low = good)?
```

### Benchmark Results (200 query-answer-citation pairs)

| Document Type | Faithfulness | Coverage | Redundancy | Overall |
|--------------|--------------|----------|------------|---------|
| Legal Contracts | 0.91 | 0.87 | 0.18 | **0.86** |
| Technical Docs | 0.88 | 0.82 | 0.22 | **0.82** |
| Financial Reports | 0.85 | 0.79 | 0.25 | **0.78** |
| Research Papers | 0.89 | 0.84 | 0.20 | **0.84** |

### Confidence Calibration

| Score Range | Human Agreement Rate |
|-------------|---------------------|
| 0.9 - 1.0 | 94% |
| 0.8 - 0.9 | 87% |
| 0.7 - 0.8 | 76% |
| < 0.7 | 61% |

### Setting Citation Thresholds

```python
# Production recommendation: set thresholds per use case
THRESHOLDS = {
    "legal": 0.85,       # High bar for legal answers
    "medical": 0.85,     # High bar for clinical decisions
    "financial": 0.80,   # Moderate bar for financial analysis
    "general": 0.70,     # Lower bar for internal knowledge base
}

if scores.faithfulness < THRESHOLDS[use_case]:
    display_low_confidence_warning()
```

---

## 12. Multi-Turn Conversations

DocQA Engine's conversation manager handles multi-turn context:

```python
from docqa_engine.conversation_manager import ConversationManager

conv = ConversationManager(pipeline=pipeline)

# Turn 1
a1 = await conv.ask("What are the payment terms?")
# Turn 2 (uses context from Turn 1)
a2 = await conv.ask("What happens if payment is late?")
# Turn 3 (full context chain)
a3 = await conv.ask("Are there any exceptions?")
```

The conversation manager rewrites follow-up queries to include context from previous turns, ensuring the retriever finds relevant passages even for ambiguous follow-ups like "Are there any exceptions?"

---

## 13. Evaluation Metrics

### Standard IR Metrics

DocQA Engine's evaluator supports all standard information retrieval metrics:

```python
from docqa_engine.evaluator import RetrievalEvaluator

evaluator = RetrievalEvaluator()
metrics = evaluator.evaluate(pipeline, eval_cases)

# Available metrics:
metrics.mrr           # Mean Reciprocal Rank
metrics.ndcg_at_5     # Normalized Discounted Cumulative Gain @5
metrics.precision_at_5  # Precision @5
metrics.recall_at_5    # Recall @5
metrics.hit_rate_at_5  # Hit Rate @5
```

### Metric Interpretation

| Metric | What It Measures | Good Value | Action if Low |
|--------|------------------|-----------|---------------|
| MRR | Rank of first relevant result | >0.7 | Improve re-ranking |
| NDCG@5 | Quality of top-5 ranking | >0.6 | Tune hybrid weights |
| Precision@5 | Relevant results in top 5 | >0.4 | Better chunking |
| Recall@5 | Coverage of relevant results | >0.6 | Increase top_k |
| Hit Rate@5 | Queries with any relevant result | >0.85 | Query expansion |

### Benchmarking Pipeline

```python
from docqa_engine.benchmark_runner import BenchmarkRunner

runner = BenchmarkRunner(pipeline=pipeline)
report = runner.run_all(
    queries=benchmark_queries,
    methods=["bm25", "dense", "hybrid"]
)
runner.save_report("benchmarks/RESULTS.md")
```

---

## 14. Cost Optimization

### Embedding Costs: $0 with TF-IDF

By using local TF-IDF instead of cloud embeddings:

| Corpus Size | OpenAI ada-002 Cost | TF-IDF Cost | Savings |
|-------------|--------------------|-----------|---------|
| 10K chunks | $0.50 | $0.00 | 100% |
| 100K chunks | $5.00 | $0.00 | 100% |
| 1M chunks | $50.00 | $0.00 | 100% |

### Query Cost Optimization

```python
from docqa_engine.cost_tracker import CostTracker

tracker = CostTracker()

# Technique 1: Cache identical queries
# Technique 2: Use cheaper models for low-stakes queries
# Technique 3: Reduce context window with compression
# Technique 4: Batch similar queries
```

### Model Selection by Use Case

| Use Case | Model | Cost/1K tokens | Faithfulness |
|----------|-------|----------------|-------------|
| High-stakes (legal/medical) | Claude 3.5 Sonnet | $0.003 | 0.91 |
| Balanced | GPT-4o | $0.005 | 0.89 |
| High-volume, lower stakes | GPT-4o Mini | $0.0006 | 0.84 |
| Long context | Gemini 1.5 Pro | $0.00125 | 0.87 |

---

## 15. Production Deployment

### Docker Deployment

```bash
# Clone and deploy
git clone https://github.com/ChunkyTortoise/docqa-engine.git
cd docqa-engine
docker-compose up -d
# Open http://localhost:8501
```

Image size: Under 500MB (multi-stage build).

### REST API with Authentication

DocQA Engine includes a FastAPI wrapper with JWT auth and rate limiting:

```python
from docqa_engine.api import create_app

app = create_app(
    jwt_secret="your-secret",
    rate_limit_per_minute=100,
    enable_metering=True
)

# Endpoints:
# POST /ingest - Upload documents
# POST /query - Ask questions
# GET /health - Health check
# GET /metrics - Usage metrics
```

### Production Checklist

- [ ] **Vector backend**: Use FAISS for >100K chunks (in-memory for smaller)
- [ ] **Chunking strategy**: Benchmark with your document types
- [ ] **Citation threshold**: Set per use case (0.70-0.85)
- [ ] **Rate limiting**: Configure per-user via API middleware
- [ ] **Cost tracking**: Enable per-query metering
- [ ] **Monitoring**: Track MRR/NDCG weekly with evaluation suite
- [ ] **Backup**: Export vector store regularly

### Performance Targets

| Metric | Target | DocQA Benchmark |
|--------|--------|-----------------|
| Query latency (10K docs) | <100ms | 85ms |
| Ingestion speed | >100 docs/min | Configurable batch size |
| Citation faithfulness | >0.85 | 0.88 average |
| Hybrid vs BM25 improvement | >15% | +22% Precision@5 |

---

## Quick Reference: Pipeline Configuration

```python
from docqa_engine.pipeline import DocQAPipeline

# Minimal setup
pipeline = DocQAPipeline()
pipeline.ingest("document.pdf")
answer = await pipeline.ask("Your question here")

# Production setup
pipeline = DocQAPipeline(
    vector_backend="faiss",          # FAISS for large corpora
    vector_kwargs={"nlist": 100}     # FAISS index parameters
)

# Ingest with progress tracking
for doc in documents:
    result = pipeline.ingest(doc)
    print(f"{result.filename}: {len(result.chunks)} chunks")

# Query with full options
answer = await pipeline.ask(
    question="Your question",
    top_k=10,                        # Retrieve top 10 passages
    method="hybrid",                 # BM25 + Dense + RRF
    rerank=True,                     # Apply cross-encoder re-ranking
    expand_query=True,               # Enable query expansion
    compress_context=True,           # Compress to fit token budget
    max_context_tokens=4096          # Token budget for context
)
```

---

## About DocQA Engine

DocQA Engine: 550+ automated tests, 26 test files, hybrid retrieval (BM25 + Dense + RRF), citation scoring, batch processing, evaluator metrics, prompt engineering lab, conversation manager, document graph, multi-hop reasoning, and REST API with JWT authentication.

- **Repository**: [github.com/ChunkyTortoise/docqa-engine](https://github.com/ChunkyTortoise/docqa-engine)
- **Live Demo**: [ct-document-engine.streamlit.app](https://ct-document-engine.streamlit.app)
- **Formats**: PDF, DOCX, TXT, MD, CSV
- **Embeddings**: Local TF-IDF (zero external API cost)
- **Query latency**: <100ms for 10K document corpus
