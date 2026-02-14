# RAG / Document AI Proposal Template

**Target Jobs**: RAG pipelines, document search, knowledge base Q&A, embedding systems, semantic search, internal search tools

**Avg Win Rate**: 15-25% (industry standard: 10-15%)

**Typical Budget**: $3K-$8K fixed-price OR $75-100/hr hourly

---

## Template

Hi [CLIENT NAME],

[HOOK — Reference their specific document type, volume, and pain point. Examples below.]

I've built RAG systems from scratch and optimized existing ones for accuracy and cost. Here's what's directly relevant to your project:

[BULLET 1 — Choose most relevant from proof points library]

[BULLET 2 — Secondary technical capability]

[BULLET 3 — Cost/performance metric if they mentioned budget concerns]

The architecture I'd propose: [EMBEDDING MODEL] for vectors, [VECTOR DB] for storage, FastAPI for the API layer, and Redis for caching frequent queries. I tune chunking strategy and retrieval method to the document type — what works for legal contracts is different from what works for technical manuals.

[CTA — Choose from library based on client engagement level]

— Cayman Roden

---

## Hook Examples (Pick One, Customize)

### 1. High Volume + Accuracy Concerns
> "Searching 10,000+ PDF contracts with natural language queries is a perfect RAG use case — and the accuracy issues you mentioned with basic embeddings are exactly why hybrid retrieval (BM25 + dense vectors) matters."

**When to use**: Client mentions >1K documents, accuracy/precision problems, or frustration with basic vector search.

### 2. Technical Depth + Specific Stack
> "Your requirements (OpenAI embeddings, pgvector, <2s response time) match exactly what I built for [similar domain]. Chunking strategy for [their document type] is critical to keep retrieval precision high without ballooning costs."

**When to use**: Client specifies tech stack and performance SLAs. Shows you read carefully.

### 3. Cost-Conscious Client
> "Building a RAG system that balances answer quality with token costs is tricky — I've reduced embedding API costs by 89% using smart caching without sacrificing accuracy. Happy to walk through the approach."

**When to use**: Client mentions budget explicitly, asks about cost per query, or says "need to keep costs low."

### 4. Enterprise/Compliance Context
> "RAG for [regulated industry] requires extra attention to citation accuracy, data privacy, and audit trails. I've built document Q&A systems with source tracking, PII redaction, and GDPR-compliant data handling."

**When to use**: Healthcare, legal, finance domains. Client mentions compliance, privacy, or audit requirements.

### 5. Integration-Heavy Project
> "Connecting RAG outputs to [Slack/Teams/Zendesk/Salesforce] is where most POCs fail in production. I've integrated document Q&A systems with real-time webhooks, rate limiting, and graceful fallback when LLMs are down."

**When to use**: Client mentions existing tools, wants chatbot interface, or describes workflow automation.

---

## Proof Point Selection (Choose 2-3)

Rank these based on job post emphasis. Lead with the most relevant.

### Core RAG Capability
> **Document Q&A engine** — Built a RAG pipeline with BM25 + dense hybrid retrieval, chunking strategies for 8 document types, and answer quality scoring. Includes cost tracking per query. 500+ tests. ([docqa-engine](https://github.com/ChunkyTortoise/docqa-engine))

**When to emphasize**: All RAG jobs. This is the flagship proof point.

### Performance + Caching
> **Production RAG with caching** — Implemented 3-tier cache (L1/L2/L3) that reduced redundant embedding calls by 89% and kept P95 response latency under 300ms. Handles 10 queries/sec with <$0.02/query average cost. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Client mentions scale, cost, or performance targets.

### Cost Optimization
> **RAG cost analysis tooling** — Built instrumentation to track token usage, chunk sizing impact on accuracy, and retrieval precision vs. cost trade-offs. Helped reduce LLM API bills by 60% without degrading answer quality. ([Revenue-Sprint](https://github.com/ChunkyTortoise/Revenue-Sprint))

**When to emphasize**: Budget-conscious clients, startups, or posts mentioning "need to keep costs low."

### Multi-Hop Retrieval
> **Advanced retrieval patterns** — Implemented cross-encoder re-ranking, query expansion, and multi-hop retrieval for complex questions that need context from multiple documents. Improved answer accuracy from 72% to 91% (evaluated on domain Q&A benchmark). ([docqa-engine](https://github.com/ChunkyTortoise/docqa-engine))

**When to emphasize**: Complex documents (research papers, technical manuals, legal), clients frustrated with "simple but wrong" answers.

### CRM/Tool Integration
> **RAG + CRM workflow** — Connected document Q&A outputs to GoHighLevel CRM with automated lead scoring, webhook triggers, and Slack notifications. Real-time sync, <200ms overhead. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Client mentions Salesforce, HubSpot, Zendesk, or workflow automation. Swap "GoHighLevel" for their tool.

---

## Architecture Paragraph (Customize)

Base version:
> "The architecture I'd propose: [EMBEDDING MODEL] for vectors, [VECTOR DB] for storage, FastAPI for the API layer, and Redis for caching frequent queries. I tune chunking strategy and retrieval method to the document type — what works for legal contracts is different from what works for technical manuals."

### Embedding Model Options

| Model | When to Use | Cost | Quality |
|-------|-------------|------|---------|
| `text-embedding-3-small` (OpenAI) | Default choice — fast, cheap, good quality | Low | Good |
| `text-embedding-3-large` (OpenAI) | High accuracy requirements, complex queries | Medium | Excellent |
| `voyage-02` (Voyage AI) | Claude-native workflows, domain-specific tuning | Medium | Excellent |
| `all-MiniLM-L6-v2` (open-source) | Client wants self-hosted, privacy-sensitive | Free | Good |

**Recommendation**: Default to `text-embedding-3-small` unless client explicitly needs higher accuracy or privacy.

### Vector DB Options

| Database | When to Use | Tradeoffs |
|----------|-------------|-----------|
| **pgvector** (PostgreSQL extension) | Small-to-medium scale (<1M docs), want simplicity, already use Postgres | Simple, cheap, slower at massive scale |
| **Pinecone** | Need managed service, >1M vectors, want zero ops overhead | Fast, expensive, vendor lock-in |
| **Weaviate** | Want hybrid search built-in, GraphQL API, or object storage | Flexible, complex setup |
| **Chroma** | POC/MVP, local development, want embedded DB | Easy, not production-ready |

**Recommendation**: Suggest pgvector for most jobs (simple, cost-effective). Mention Pinecone if client says "millions of documents" or "we don't want to manage infrastructure."

---

## CTA Options (Choose Based on Client Engagement)

### 1. Architecture Sketch (Most Effective for Technical Clients)
> "Want me to sketch out an architecture for [their specific document type]? I can send over a quick diagram + cost estimate based on your query volume."

**When to use**: P1 jobs, technical hiring managers, posts with clear specs.

### 2. Cost Estimate (Budget-Conscious Clients)
> "Happy to put together a cost breakdown (infrastructure + API costs + dev time) once I understand your query volume and accuracy requirements."

**When to use**: Startups, clients who mention "need to stay under $X/month," posts asking for pricing.

### 3. Quick Call (Enterprise Clients)
> "I'm available for a 15-minute call [this week] to discuss your specific use case and proposed approach."

**When to use**: Large budgets ($10K+), enterprise clients, posts mentioning "need to discuss architecture."

### 4. Timeline (Time-Sensitive Projects)
> "I can start [this week / Monday] and typically scope RAG MVPs at 2-4 weeks for initial deployment."

**When to use**: Posts mentioning deadlines, "need this soon," or competitive bidding.

### 5. Portfolio Link (Ask for More Context)
> "I'm available [this week] if you'd like to discuss. Here's my full portfolio: https://chunkytortoise.github.io"

**When to use**: P2 jobs, vague posts, or when you need more info before committing to detailed proposal.

---

## Customization Checklist

Before sending, verify:

- [ ] Hook mentions their specific document type (contracts, manuals, tickets, etc.)
- [ ] Proof points ordered by relevance (most important first)
- [ ] If they specify a tool (Pinecone, OpenAI, etc.), mention it explicitly
- [ ] CTA matches their urgency and budget level
- [ ] Total word count <275 (Upwork proposals should be skimmable)
- [ ] No typos in client name, company, or technical terms
- [ ] Rate quoted aligns with scorecard ($75-100/hr for RAG work)

---

## Rate Guidance

| Job Complexity | Suggested Rate |
|----------------|----------------|
| Simple Q&A (1 doc type, basic retrieval) | $75/hr or $2.5K-$4K fixed |
| Hybrid retrieval + caching | $85/hr or $4K-$6K fixed |
| Multi-hop, re-ranking, custom chunking | $95/hr or $6K-$10K fixed |
| Enterprise (compliance, audit trails, integrations) | $100/hr or $10K-$20K fixed |

**Fixed-price tip**: Estimate hours conservatively (RAG systems have hidden complexity in chunking tuning). Add 20% buffer. If client balks at price, offer phased approach: MVP first, then optimization.

---

**Last Updated**: February 14, 2026
