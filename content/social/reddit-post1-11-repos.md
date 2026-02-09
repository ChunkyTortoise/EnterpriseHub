# Reddit Post: r/Python + r/SideProject

**Title:** I built 11 Python repos with 7,000+ tests and live demos

---

Hey r/Python and r/SideProject!

Over the past year, I built 11 open-source Python projects. Combined, they have 7,016+ tests, and 6 live Streamlit demos you can try right now.

Here's what I built and what I learned.

## The 11 Projects

| Project | Focus | Tests | Demo |
|---------|-------|-------|------|
| EnterpriseHub | Real estate AI + multi-agent chatbots | ~4,937 | [Live](https://ct-enterprise-ai.streamlit.app) |
| docqa-engine | RAG pipeline with hybrid retrieval | 322 | [Live](https://ct-document-engine.streamlit.app) |
| insight-engine | Auto-dashboard from CSV | 313 | [Live](https://ct-insight-engine.streamlit.app) |
| jorge_real_estate_bots | Real estate AI assistant | 279 | — |
| Revenue-Sprint | AI security + cost optimization | 240 | — |
| scrape-and-serve | Web scraping infrastructure | 236 | [Live](https://ct-scrape-and-serve.streamlit.app) |
| ai-orchestrator (AgentForge) | Multi-LLM orchestrator (15KB) | 214 | [Live](https://ct-agentforge.streamlit.app) |
| mcp-toolkit | FastMCP tool server framework | 158 | [Live](https://ct-mcp-toolkit.streamlit.app) |
| llm-integration-starter | Minimal LLM client | 149 | [GitHub](https://github.com/ChunkyTortoise/llm-integration-starter) |
| prompt-engineering-lab | Prompt patterns + A/B testing | 127 | [GitHub](https://github.com/ChunkyTortoise/prompt-engineering-lab) |
| chunkytortoise.github.io | Portfolio site | — | [Live](https://chunkytortoise.github.io) |

**Total: 7,016+ tests | 11 repos | 6 live Streamlit demos**

## What I Learned

### 1. Testing Changes Everything

EnterpriseHub started with ~1,200 tests and grew to nearly 5,000 as the codebase matured:
- Debugging went from hours to minutes (tests pinpoint failures)
- Refactoring became routine (tests catch regressions instantly)
- Production confidence is high (comprehensive coverage across 22+ domain-agnostic agents)

### 2. Minimal Dependencies Win

Each project uses only essential packages:

```
docqa-engine:  rank_bm25, sklearn, httpx (no ChromaDB in prod)
ai-orchestrator: httpx, pytest, asyncio (stdlib only)
insight-engine: streamlit, pandas, plotly
EnterpriseHub: FastAPI, SQLAlchemy, Redis, Claude/Gemini SDKs
```

No LangChain. No LlamaIndex. No heavy frameworks. Direct API calls, custom orchestration.

### 3. Async Is Worth It

All FastAPI projects use Python asyncio for concurrency:

```python
# Sync: 800ms for 3 API calls
results = [call_api(x) for x in items]

# Async: 150ms for 3 API calls
results = await asyncio.gather(*[call_api(x) for x in items])
```

EnterpriseHub's Claude orchestrator achieves <200ms overhead with L1/L2/L3 Redis caching.

### 4. FastAPI + Streamlit = Production Combo

- **FastAPI**: REST APIs, webhooks, async orchestration, CRM integrations
- **Streamlit**: BI dashboards, interactive demos, data exploration

Together they cover 90% of AI/ML use cases without complex frameworks.

## Live Demos You Can Try

1. **EnterpriseHub**: [ct-enterprise-ai.streamlit.app](https://ct-enterprise-ai.streamlit.app)
   - Real estate AI platform with multi-bot orchestration, CRM adapters, and BI dashboards

2. **DocQA Engine**: [ct-document-engine.streamlit.app](https://ct-document-engine.streamlit.app)
   - Upload documents, ask questions, get answers with citations (hybrid BM25 + TF-IDF + Dense retrieval)

3. **AgentForge**: [ct-agentforge.streamlit.app](https://ct-agentforge.streamlit.app)
   - Multi-LLM orchestrator in 15KB with tracing and visualization

4. **Insight Engine**: [ct-insight-engine.streamlit.app](https://ct-insight-engine.streamlit.app)
   - Upload CSV, get auto-generated dashboard with forecasting and clustering

5. **Scrape & Serve**: [ct-scrape-and-serve.streamlit.app](https://ct-scrape-and-serve.streamlit.app)
   - Web scraping infrastructure with scheduler and validators

6. **MCP Toolkit**: [ct-mcp-toolkit.streamlit.app](https://ct-mcp-toolkit.streamlit.app)
   - FastMCP tool server framework for building Claude integrations

## GitHub Repos

All projects are MIT licensed:

- [ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub) - Real estate AI platform
- [ChunkyTortoise/docqa-engine](https://github.com/ChunkyTortoise/docqa-engine) - RAG pipeline without vector DBs
- [ChunkyTortoise/insight-engine](https://github.com/ChunkyTortoise/insight-engine) - Auto-dashboard generator
- [ChunkyTortoise/jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots) - Real estate AI assistant
- [ChunkyTortoise/Revenue-Sprint](https://github.com/ChunkyTortoise/Revenue-Sprint) - AI security & cost optimization
- [ChunkyTortoise/scrape-and-serve](https://github.com/ChunkyTortoise/scrape-and-serve) - Web scraping infrastructure
- [ChunkyTortoise/ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator) - Multi-LLM orchestrator (15KB)
- [ChunkyTortoise/mcp-toolkit](https://github.com/ChunkyTortoise/mcp-toolkit) - FastMCP tool server framework
- [ChunkyTortoise/llm-integration-starter](https://github.com/ChunkyTortoise/llm-integration-starter) - Minimal LLM client
- [ChunkyTortoise/prompt-engineering-lab](https://github.com/ChunkyTortoise/prompt-engineering-lab) - Prompt patterns & A/B testing
- [ChunkyTortoise/chunkytortoise.github.io](https://github.com/ChunkyTortoise/chunkytortoise.github.io) - Portfolio site

## What I'm Working On Next

1. **CRM adapter framework**: Unified protocol for GHL, HubSpot, Salesforce integrations
2. **Agent swarm coordination**: Multi-agent mesh with governance and auto-scaling
3. **Production RAG patterns**: Chunking strategies, hybrid retrieval, citation accuracy

## Questions?

AMA about:
- Project architecture
- Testing strategies
- Production deployment
- Performance optimization
- Building in public

---

**TL;DR**: Built 11 Python projects with 7,016+ tests, 6 live Streamlit demos. All open source. Real estate AI, RAG pipelines, LLM orchestration, auto-dashboards, and more. Try them at the links above.

**GitHub**: [github.com/ChunkyTortoise](https://github.com/ChunkyTortoise)

---
#python #opensourcelevelup #sideproject #programming