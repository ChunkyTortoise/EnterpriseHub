# AI Document Q&A Engine — $59 / $249 / $1,499 (3-tier)

## Tagline
**Build production-ready RAG pipelines in hours, not weeks**

## Description

The AI Document Q&A Engine is a complete, self-hosted Retrieval-Augmented Generation solution that empowers developers to create intelligent document question-answering systems without relying on external APIs or expensive SaaS subscriptions.

This engine delivers a production-grade RAG pipeline with hybrid retrieval (combining BM25's precision with dense vector similarity), 5 configurable chunking strategies, and built-in citation scoring. Whether you're building an internal knowledge base, customer support system, or research assistant, this engine provides the foundation you need to go live in hours, not months.

The included REST API handles authentication, rate limiting, and usage metering out of the box. The Streamlit UI provides an instant interface for testing and demonstration, while the evaluation metrics help you continuously improve your retrieval quality.

**Perfect for**: Startups building AI-powered documentation, enterprises migrating off legacy search, developers creating domain-specific Q&A systems, and any team that needs accurate, cited answers from their document corpus.

---

## Key Features

- **Hybrid Retrieval System**: Combines BM25 (keyword-based) with dense vector similarity for optimal precision-recall balance
- **5 Chunking Strategies**: Fixed-size, sentence-based, paragraph, recursive, and semantic chunking for different document types
- **Citation Scoring**: Each answer includes source citations with confidence scores for traceability
- **Production REST API**: FastAPI-powered endpoints with JWT authentication, rate limiting (100 req/min), and usage metering
- **Streamlit Demo UI**: Ready-to-use interface for testing documents and queries immediately
- **Built-in Evaluation**: Precision, recall, and F1 metrics for continuous retrieval quality assessment
- **Zero External Dependencies**: Core retrieval runs entirely offline—no OpenAI, Pinecone, or other SaaS required
- **Configurable Pipeline**: Easy YAML-based configuration for all retrieval parameters

---

## Tech Stack

- **Language**: Python 3.11+
- **UI Framework**: Streamlit
- **API Framework**: FastAPI
- **ML/NLP**: scikit-learn, PyPDF2
- **Vector Database**: ChromaDB (included) or optional Qdrant/Weaviate
- **Authentication**: PyJWT
- **Configuration**: YAML

---

## Differentiators

| Aspect | This Engine | Typical Alternatives |
|--------|-------------|---------------------|
| **Core Size** | ~15KB dependencies | LangChain's 50MB+ |
| **External APIs** | Zero required | OpenAI/Pinecone costs |
| **Evaluation** | Built-in metrics | Manual testing only |
| **Citation System** | Confidence-scored sources | Black-box outputs |
| **Production Ready** | Auth + rate limiting + metering | Research-grade only |
| **Deployment** | Docker-ready, self-hosted | Cloud lock-in |

---

## What's Included in Your ZIP

```
docqa-engine/
├── README.md                    # Getting started guide
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container deployment
├── docker-compose.yml           # Local development stack
├── config/
│   ├── config.yaml             # Main pipeline configuration
│   └── chunking_profiles.yaml  # 5 chunking strategies
├── src/
│   ├── api/
│   │   ├── main.py             # FastAPI application entry point
│   │   ├── routes/
│   │   │   ├── documents.py    # Document upload/management endpoints
│   │   │   ├── query.py        # Q&A endpoints with citations
│   │   │   └── health.py       # Health check endpoints
│   │   └── middleware/
│   │       ├── auth.py         # JWT authentication
│   │       └── rate_limit.py   # Rate limiting middleware
│   ├── core/
│   │   ├── pipeline.py         # RAG pipeline orchestration
│   │   ├── config.py           # Configuration loader
│   │   └── types.py            # Type definitions
│   ├── retrieval/
│   │   ├── hybrid_search.py    # BM25 + dense hybrid retrieval
│   │   ├── embedder.py         # Sentence transformers embedder
│   │   └── reranker.py         # Cross-encoder reranking
│   ├── chunking/
│   │   ├── base.py             # Base chunker interface
│   │   ├── fixed_size.py       # Fixed-size chunking
│   │   ├── sentence.py         # Sentence-based chunking
│   │   ├── paragraph.py         # Paragraph chunking
│   │   ├── recursive.py        # Recursive chunking
│   │   └── semantic.py         # Semantic chunking
│   ├── evaluation/
│   │   ├── metrics.py          # Precision, recall, F1
│   │   └── evaluator.py        # Evaluation runner
│   └── utils/
│       ├── pdf_parser.py       # PDF text extraction
│       └── citation.py          # Citation generation
├── ui/
│   ├── app.py                  # Streamlit demo application
│   ├── components/
│   │   ├── document_upload.py  # Document upload component
│   │   ├── query_interface.py  # Q&A input/output
│   │   └── results_display.py  # Answer display with citations
│   └── pages/
│       ├── home.py             # Landing page
│       ├── upload.py           # Document management
│       └── evaluate.py         # Evaluation dashboard
├── tests/
│   ├── test_retrieval.py       # Retrieval tests
│   ├── test_chunking.py        # Chunking tests
│   └── test_evaluation.py       # Evaluation tests
├── CUSTOMIZATION.md            # Deep customization guide
├── API_REFERENCE.md            # REST API documentation
├── DEPLOYMENT.md               # Production deployment guide
└── ARCHITECTURE.md             # System architecture overview
```

---

## Suggested Thumbnail Screenshot

**Primary**: Screenshot of the Streamlit UI showing a document Q&A session with highlighted citations and confidence scores

**Secondary options**:
- Architecture diagram showing the RAG pipeline flow
- API documentation page showing endpoint examples
- Evaluation dashboard with precision/recall metrics

---

## Tags for Discoverability

`rag`, `retrieval-augmented-generation`, `document-qa`, `question-answering`, `hybrid-search`, `bm25`, `vector-search`, `semantic-search`, `chatbot`, `knowledge-base`, `fastapi`, `streamlit`, `self-hosted`, `production-ready`, `python`, `machine-learning`, `nlp`, `document-processing`, `citation`, `embeddings`

---

## Related Products (Upsell)

| Product | Price | Rationale |
|---------|-------|-----------|
| [AgentForge — Multi-LLM Orchestrator](/products/product2-agentforge.md) | $39 | Combine with DocQA for full Q&A pipeline with LLM generation |
| [Data Intelligence Dashboard](/products/product4-insight-engine.md) | $39 | Analyze usage metrics and document patterns |
| [Web Scraper & Price Monitor Toolkit](/products/product3-scrape-and-serve.md) | $29 | Enrich documents with scraped web data |

---

## Live Demo

**Try before you buy**: [ct-document-engine.streamlit.app](https://ct-document-engine.streamlit.app)

---

## Support

- Documentation: See `README.md` and `CUSTOMIZATION.md` in your ZIP
- Issues: Create an issue on the GitHub repository
- Email: caymanroden@gmail.com

---

**License**: MIT License — Use in unlimited projects

**Refund Policy**: 30-day money-back guarantee if the product doesn't meet your requirements