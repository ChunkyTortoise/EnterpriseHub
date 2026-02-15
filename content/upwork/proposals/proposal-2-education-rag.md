# Proposal 2: Education RAG Development Using Open Source Models

**Job**: Education RAG Development Using Open Source Models
**Bid**: $60/hr | **Fit**: 9/10 | **Connects**: 12-16
**Status**: Ready when funded — no Connects available

---

## Cover Letter

Your tech stack reads like the bill of materials for a project I already shipped. I built **docqa-engine** — a RAG pipeline with BM25 + dense hybrid retrieval, reciprocal rank fusion, and a reranking step — specifically for document Q&A across PDFs, Word docs, and plain text. It runs on FastAPI with **500+ automated tests** covering retrieval quality, ingestion edge cases, and cost tracking. The evaluation notebook measures faithfulness, context recall, and precision@k against curated test sets.

For the open-source model serving piece, I've worked with local model inference and built **AgentForge** (my ai-orchestrator repo, 550+ tests) as a unified async interface that abstracts provider differences — switching between hosted APIs and local models is a config change, not a rewrite.

On the education side specifically, I'd prioritize:

1. **Chunking strategy tuned for textbook-style content** where sections reference equations and figures — standard fixed-size chunking destroys these cross-references
2. **Citation-first prompt templates** so students can trace answers back to source material — not just "the AI says so"
3. **BM25 + cross-encoder reranking** for terminology-heavy queries where keyword matching outperforms pure embeddings

I've got Docker + CI/CD set up across all 10 production repos. Happy to walk through the architecture in a call.

### Portfolio Evidence

| Metric | Value | Source |
|--------|-------|--------|
| RAG pipeline (BM25 + dense) | Production-ready | docqa-engine (500+ tests) |
| FastAPI async backend | Multi-service architecture | EnterpriseHub (~5,100 tests) |
| Docker + CI/CD | All 10 repos | GitHub Actions, green CI |
| Multi-provider LLM abstraction | Claude, GPT, Gemini, local | AgentForge (550+ tests) |
| Document parsing | PDF, Word, plain text | PyPDF2 + python-docx pipeline |
| Evaluation framework | Faithfulness, recall, precision@k | Automated test suites |

### Why Contract-to-Hire Works

This is exactly the engagement model I prefer. I bring 20+ years of software engineering experience, work remote-first with async communication, and maintain daily commits with comprehensive documentation. My repos have 33 Architecture Decision Records across the portfolio — I document engineering tradeoffs, not just code.

**Portfolio**: https://chunkytortoise.github.io | **GitHub**: https://github.com/ChunkyTortoise

---

*Ready to submit when Connects are purchased ($12 for 80 Connects).*
