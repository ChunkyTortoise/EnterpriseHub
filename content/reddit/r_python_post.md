# I built 11 Python repos with 7,000+ tests and live demos 🚀

After 8 months of late nights and weekend coding, I'm open-sourcing my entire portfolio of production-ready Python projects. These aren't toy examples—they're battle-tested tools that power real workflows.

---

## 📦 The Collection

### 1. **AgentForge** — Multi-Agent Orchestration Framework
Build, coordinate, and scale AI agent swarms with governance, audit trails, and dead-letter queues.

```python
from agentforge import AgentSwarm

swarm = AgentSwarm(
    agents=[researcher, writer, reviewer],
    coordination_strategy="hierarchical",
    max_retries=3
)
result = swarm.execute("Write a blog post about quantum computing")
```

**Key Features:**
- Agent Mesh Coordinator with automatic scaling
- Structured handoffs between agents
- Comprehensive audit logging
- Conflict resolution for concurrent operations

---

### 2. **Advanced RAG System** — Production-Grade Retrieval
Full pipeline with hybrid search, re-ranking, and citation tracking. 500+ unit tests prove it works.

```python
from advanced_rag import HybridRAGPipeline

pipeline = HybridRAGPipeline(
    vector_store="chroma",
    embedding_model="BAAI/bge-large",
    reranker="cross-encoder/ms-marco-MiniLM"
)
results = pipeline.query("What are the tax implications of real estate investment?")
```

---

### 3. **EnterpriseHub** — AI-Powered Real Estate Platform
The flagship project: Lead qualification, chatbot orchestration, and BI dashboards for Rancho Cucamonga real estate.

**Tech Stack:**
- **Backend:** FastAPI (async) with 22 Claude Code agents
- **Database:** PostgreSQL + Alembic migrations + Redis cache (L1/L2/L3)
- **BI:** Streamlit dashboards with Monte Carlo simulations
- **CRM:** GoHighLevel integration (10 req/s rate limited)
- **AI:** Claude + Gemini + Perplexity orchestration

---

## 🧪 Quality Metrics

| Metric | Value |
|--------|-------|
| Total Tests | 7,000+ |
| Code Coverage | ~85% |
| Type Hints | 100% |
| Docstrings | Complete |
| Docker Support | All repos |

---

## 💡 What I Learned

1. **Async is hard but worth it** — FastAPI's async capabilities cut latency by 40%, but debugging concurrent code requires a mental model shift.

2. **Cache invalidation IS the hard part** — Built a 3-tier caching system (L1/L2/L3) that balances freshness with performance.

3. **Tests save lives** — 7,000 tests caught regressions I would've shipped to production. CI/CD with pytest is non-negotiable.

4. **LLM orchestration is its own discipline** — Prompt engineering, caching, and fallbacks need as much attention as the model itself.

---

## 🔗 Links

- **Main Repo:** [github.com/chunkytortoise](https://github.com/chunkytortoise)
- **Documentation:** See individual repo READMEs
- **Demos:** Streamlit apps deployed via Docker Compose

---

## ❓ AMA

Ask me anything about:
- Multi-agent architectures
- LLM caching strategies
- Production deployment patterns
- Side-project sustainability

*All 11 repos are MIT licensed. Fork, modify, ship.*
