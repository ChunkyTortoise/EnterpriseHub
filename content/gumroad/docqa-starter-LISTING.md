# DocQA Engine Starter - Gumroad Product Listing

**Product Title**: DocQA Engine Starter - Production RAG Pipeline
**Short Description**: Build production-ready document Q&A with hybrid retrieval, 5 chunking strategies, citation scoring. 500+ tests, Docker ready, zero external APIs. MIT licensed.
**Price**: $59 (Pay What You Want, minimum $59)
**URL Slug**: docqa-starter
**Category**: Software > Developer Tools
**Tags**: `rag, retrieval-augmented-generation, document-qa, hybrid-search, bm25, vector-search, semantic-search, chatbot, knowledge-base, fastapi, streamlit, self-hosted, production-ready, python, citation, embeddings`

---

## Full Product Description

# DocQA Engine - Production RAG in Hours, Not Weeks

Stop paying $300-$1,200 for custom RAG builds. Get a complete, tested, production-grade Retrieval-Augmented Generation pipeline you own forever.

## Why DocQA Engine?

| Feature | DocQA Engine | LangChain RAG | Custom Build |
|---------|-------------|---------------|--------------|
| **Core Size** | ~15KB deps | 50MB+ | Varies |
| **External APIs** | Zero required | OpenAI/Pinecone | $50-500/mo |
| **Tests** | 500+ (80%+ coverage) | Minimal | You write them |
| **Evaluation** | Built-in metrics | Manual | DIY |
| **Citation System** | Confidence-scored | Black box | Build yourself |
| **Time to Production** | Hours | Days-weeks | Weeks-months |
| **Ongoing Cost** | $0 (self-hosted) | $50-500/month | Varies |

## What You Get

### Hybrid Retrieval System
Combines BM25 keyword search with dense vector similarity for the best of both worlds. Handles short queries AND semantic understanding without compromise.

### 5 Chunking Strategies
- **Fixed-size**: Fast, predictable chunks for structured docs
- **Sentence-based**: Natural language boundaries
- **Paragraph**: Document structure preservation
- **Recursive**: Hierarchical splitting for complex docs
- **Semantic**: Meaning-based chunking for highest quality

### Citation Scoring
Every answer includes source citations with confidence scores. Essential for compliance, auditing, and building user trust.

### Production REST API
FastAPI-powered with JWT authentication, rate limiting (100 req/min), and usage metering. Deploy behind your load balancer today.

### Streamlit Demo UI
Test documents and queries immediately with the included web interface. Show stakeholders what the system can do before writing a line of integration code.

### Built-in Evaluation
Precision, recall, and F1 metrics for continuous retrieval quality assessment. Know exactly how good your pipeline is, and track improvements over time.

## Tech Stack
- Python 3.11+
- FastAPI (async API)
- Streamlit (demo UI)
- ChromaDB (vector store, included)
- scikit-learn + PyPDF2
- Docker ready

## What's in the ZIP

```
docqa-engine/
  README.md, requirements.txt, Dockerfile, docker-compose.yml
  config/ (pipeline config, chunking profiles)
  src/
    api/ (FastAPI routes, auth, rate limiting)
    core/ (pipeline orchestration, config, types)
    retrieval/ (hybrid search, embedder, reranker)
    chunking/ (5 strategies)
    evaluation/ (metrics, evaluator)
    utils/ (PDF parser, citation generator)
  ui/ (Streamlit app, components, pages)
  tests/ (500+ tests)
  CUSTOMIZATION.md, API_REFERENCE.md, DEPLOYMENT.md, ARCHITECTURE.md
```

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run API
uvicorn src.api.main:app --reload

# Run UI
streamlit run ui/app.py
```

## Perfect For
- Startups building AI-powered documentation search
- Enterprises migrating off legacy search systems
- Developers creating domain-specific Q&A bots
- Teams that need accurate, cited answers from document corpora
- Anyone who wants RAG without the $50-500/month SaaS bill

## Want More?
- **DocQA Pro** ($249): + RAG optimization guide, 3 domain case studies, 30-min expert consultation, priority support
- **DocQA Enterprise** ($1,499): + custom domain tuning, 60-min deep-dive, Slack support, white-label rights

30-day money-back guarantee. MIT License — use in unlimited projects.
