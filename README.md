# EnterpriseHub

**Real estate teams lose 40% of leads because response time exceeds the 5-minute SLA.** This platform automates lead qualification, follow-up scheduling, and CRM sync so no lead goes cold.

[![CI](https://img.shields.io/github/actions/workflow/status/ChunkyTortoise/EnterpriseHub/ci.yml?label=CI)](https://github.com/ChunkyTortoise/EnterpriseHub/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F1C40F.svg)](LICENSE)

![Demo](assets/demo.gif)

## What This Solves

- **Slow lead response** -- Three AI bots (Lead, Buyer, Seller) qualify prospects in real time using a Q0-Q4 framework, enforcing the 5-minute response rule
- **Disconnected tools** -- Qualification results, CRM updates, and analytics live in one platform instead of spreadsheets + separate dashboards
- **No visibility into pipeline health** -- Streamlit BI dashboard surfaces lead flow, conversion rates, commission tracking, and bot performance metrics

<details>
<summary>Screenshots</summary>

![Platform Overview](assets/screenshots/platform-overview.png)
![Market Pulse](assets/screenshots/market-pulse.png)
![Bot Dashboard](assets/screenshots/jorge_dashboard_01.png)
![Design System](assets/screenshots/design-system.png)

</details>

## Architecture

```
                          +---------------------------+
                          |    Streamlit BI Dashboard  |
                          |  (Command Center)          |
                          +------------+--------------+
                                       |
+------------------+     +-------------+-------------+     +-------------------+
|   Jorge Bots     |     |       FastAPI Core         |     | GoHighLevel CRM   |
|                  +---->+    (Orchestration Layer)    +<----+   Integration     |
|  Lead Bot :8001  |     |                             |     |                   |
|  Seller Bot :8002|     |  Claude Orchestrator        |     |  Webhooks         |
|  Buyer Bot :8003 |     |  Agent Mesh Coordinator     |     |  Contact Sync     |
+------------------+     +-------------+---------------+     +-------------------+
                                       |
              +------------------------+------------------------+
              |                        |                        |
    +---------+--------+    +----------+---------+    +---------+---------+
    |   PostgreSQL     |    |      Redis         |    |  AI Providers     |
    |   (Leads, Props, |    |  (Cache, Sessions, |    |  Claude, Gemini,  |
    |    Analytics)    |    |   Rate Limiting)   |    |  OpenRouter       |
    +------------------+    +--------------------+    +-------------------+
```

## Quick Start

```bash
git clone https://github.com/ChunkyTortoise/EnterpriseHub.git
cd EnterpriseHub
pip install -r requirements.txt

# Demo mode — no API keys, no database, pre-populated dashboards
make demo
```

### Full Setup (with external services)

```bash
cp .env.example .env
# Edit .env with your API keys

docker-compose up -d postgres redis
uvicorn app:app --reload --port 8000

# BI Dashboard (separate terminal)
streamlit run admin_dashboard.py --server.port 8501
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (async), Pydantic validation |
| UI | Streamlit, Plotly |
| Database | PostgreSQL, Alembic migrations |
| Cache | Redis (L1), Application memory (L2), Database (L3) |
| AI/ML | Claude (primary), Gemini (analysis), OpenRouter (fallback) |
| CRM | GoHighLevel (webhooks, contacts, workflows) |
| Search | ChromaDB vector store, BM25, hybrid retrieval |
| Payments | Stripe (subscriptions, webhooks) |
| Infrastructure | Docker Compose |

## Project Structure

```
EnterpriseHub/
├── ghl_real_estate_ai/           # Main application
│   ├── agents/                   # Bot implementations (Lead, Buyer, Seller)
│   ├── api/routes/               # FastAPI endpoints
│   ├── services/                 # Business logic layer
│   │   ├── claude_orchestrator.py    # Multi-LLM coordination + caching
│   │   ├── agent_mesh_coordinator.py # Agent fleet management
│   │   └── enhanced_ghl_client.py    # CRM integration (rate-limited)
│   ├── models/                   # SQLAlchemy models, Pydantic schemas
│   └── streamlit_demo/           # Dashboard UI components
├── advanced_rag_system/          # RAG pipeline (BM25, dense search, ChromaDB)
├── tests/                        # Test suite
├── app.py                        # FastAPI entry point
├── admin_dashboard.py            # Streamlit BI dashboard
└── docker-compose.yml            # Container orchestration
```

## Testing

```bash
python -m pytest tests/ -v
python -m pytest --cov=ghl_real_estate_ai --cov-report=term-missing
```

## Related Projects

- [jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots) -- Standalone 3-bot lead qualification system extracted from this platform
- [ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator) -- AgentForge: unified async LLM interface (Claude, Gemini, OpenAI, Perplexity)
- [Revenue-Sprint](https://github.com/ChunkyTortoise/Revenue-Sprint) -- AI-powered freelance pipeline: job scanning, proposal generation, prompt injection testing

## License

MIT -- see [LICENSE](LICENSE) for details.
