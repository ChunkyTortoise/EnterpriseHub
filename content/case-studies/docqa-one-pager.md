# DocQA Engine — Enterprise Document Q&A Case Study

## The Challenge

An enterprise client needed accurate document question-answering across thousands of PDFs, Word docs, and text files with verifiable citations. Existing RAG solutions produced hallucinations or failed to provide source attribution, making the system unusable for compliance-sensitive use cases. They required sub-second query response times, support for multi-format document ingestion, and a prompt engineering lab to fine-tune retrieval quality without code changes.

## The Solution

Built a production-grade RAG pipeline with hybrid search combining BM25 keyword matching, TF-IDF statistical ranking, and semantic embeddings (OpenAI text-embedding-3-small). Implemented cross-encoder re-ranking to surface the most relevant chunks, query expansion for better recall, and chunk-level citation tracking. Included a prompt engineering lab for A/B testing system prompts, temperature tuning, and retrieval parameter optimization. REST API wrapper provides authentication (JWT), rate limiting (100 req/min), and usage metering for multi-tenant deployments.

## Key Results

- **91% citation accuracy** — Verified via 500+ test cases with ground-truth annotations
- **<1s query response** — P95 latency of 0.8s for end-to-end question answering (embed + retrieve + re-rank + generate)
- **Multi-format support** — PDF, DOCX, TXT with automatic chunking (512 tokens, 50 overlap)
- **500+ automated tests** — Unit, integration, E2E coverage with CI/CD on every commit
- **Conversation-aware** — Multi-hop reasoning and document graph traversal for complex queries

## Tech Stack

**Backend**: Python 3.11, FastAPI (async), Pydantic validation
**AI**: OpenAI GPT-4, text-embedding-3-small embeddings
**Vector Store**: ChromaDB (persistent storage), FAISS for fast similarity search
**Search**: BM25 (rank_bm25), TF-IDF (scikit-learn), cross-encoder re-ranking
**Document Processing**: PyPDF2, python-docx, tiktoken for token counting
**Prompt Lab**: Streamlit UI with A/B testing, versioning, safety checks
**Deployment**: Docker Compose, GitHub Actions CI

## Timeline & Scope

**Duration**: 6 weeks (solo developer)
**Approach**: TDD with edge-case testing for document formats, citation extraction, hallucination detection
**Testing**: 500+ tests including summarization quality, multi-hop reasoning, answer validation
**Features**: Query expansion, conversation manager, document graph, cross-encoder re-ranker
**Governance**: 4 ADRs (hybrid search, re-ranking, citation strategy, multi-format parsing), SECURITY.md, CHANGELOG.md

---

**Want similar results?** [Schedule a free 15-minute call](mailto:caymanroden@gmail.com) | [View live demo](https://github.com/chunkytortoise/docqa-engine) | [GitHub Repo](https://github.com/chunkytortoise/docqa-engine)
