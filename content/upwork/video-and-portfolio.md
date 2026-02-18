# Video Intro & Portfolio Items
Generated: 2026-02-17

---

## Video Intro Script (90 seconds)

**Approximate word count**: 232 words | **Target pace**: ~2.5 words/second

---

[0:00–0:10] **HOOK**

[LOOK DIRECTLY AT CAMERA, MEASURED PACE]

Most AI integrations look impressive in a demo and fall apart in production.
I build the ones that don't.

---

[0:10–0:25] **WHAT YOU BUILD + WHO YOU HELP**

[SLIGHT LEAN FORWARD]

I'm Cayman — I build production AI systems for startups and engineering teams:
RAG pipelines that answer questions from your actual documents,
multi-agent orchestrators that run autonomous workflows,
and AI chatbots that integrate directly with your CRM — GoHighLevel, HubSpot, Salesforce.

---

[0:25–0:50] **CONCRETE EXAMPLE WITH METRIC**

[CALM, SPECIFIC — NOT RUSHING]

One example: I built a multi-agent orchestration engine — AgentForge —
that handles 4.3 million tool dispatches per second with less than 200 milliseconds
of orchestration overhead at P99.

[BRIEF PAUSE]

Another: a three-tier Redis caching layer on top of an LLM pipeline
that hit an 88 percent cache hit rate — cutting API costs by 89 percent.

These aren't lab numbers. They're benchmarked under load.

---

[0:50–1:10] **YOUR PROCESS — WHAT MAKES YOU DIFFERENT**

[CONFIDENT, UNHURRIED]

What makes my work different is the testing discipline.
Every system I ship has a full test suite — 8,500 automated tests across my portfolio,
all CI green.

I write tests before I write features. That means when something breaks — and in AI systems,
things break — you have a safety net, not a mystery.

---

[1:10–1:25] **SOCIAL PROOF**

[NATURAL, NOT LISTING — CONVERSATIONAL]

I've published a package on PyPI, built five live demos you can try right now,
and documented every major architecture decision with ADRs across ten repos.

The demos aren't slides. They're running systems.

---

[1:25–1:30] **CTA**

[DIRECT, WARM]

If you're building something with AI and you need it to actually work in production —
I'd love to hear about it.

---

## Thumbnail Text

**AI That Works in Production** — not just demos

*(7 words — overlay on first frame or a clean code-on-screen still)*

---

## Recording Tips

- **Lighting**: Single key light at 45 degrees, slightly above eye level. Natural window light works. Avoid overhead fluorescents — they flatten your face and look unprofessional.
- **Background**: Neutral wall or a clean desk setup. A monitor with code visible in the background reads as credible. Avoid busy backgrounds that compete with your face.
- **Camera**: Phone propped at eye level is fine. Laptop camera pointed slightly upward reads as less confident — raise it. Eye level or very slightly above is ideal.
- **Pace**: Speak slower than feels natural. 90 seconds is not a rush — it is a deliberate pace. Pause after each section marker. Pauses read as confidence on camera.
- **Delivery**: Record 2–3 takes. The first take is almost always the most authentic. Do not try to be polished — direct and unhurried wins over slick and fast.

---

## Portfolio Items

---

### 1. AgentForge — Multi-Agent AI Orchestration

**Problem solved**: Engineering teams building autonomous AI workflows have no reliable framework for coordinating multiple agents at production throughput without cascading failures.

**What I built**: AgentForge is a production-grade multi-agent orchestration engine built in Python. It implements a ReAct-loop architecture with a central dispatcher that routes tool calls across a mesh of specialized agents. The system includes circuit breakers to prevent cascade failures, token cost tracking per agent run, and a full evaluation framework for testing non-deterministic agent behavior. I designed it from the ground up for load — not just correctness.

**Results/metrics**:
- 4.3 million tool dispatches per second (benchmarked)
- P99 orchestration overhead: 0.095ms (under 200ms target)
- Full test suite with CI green on every commit
- Live demo running on Streamlit Cloud

**Tech used**: Python, FastAPI, asyncio, Redis, PostgreSQL, Claude API, pytest, Docker, GitHub Actions

**Live demo**: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/
**Repo**: github.com/ChunkyTortoise/ai-orchestrator

---

### 2. Document Q&A Engine (RAG)

**Problem solved**: Businesses with large document libraries — contracts, manuals, knowledge bases — need accurate, fast answers without hallucination, and without sending every query to an expensive LLM.

**What I built**: A hybrid retrieval-augmented generation engine that combines BM25 keyword search, TF-IDF scoring, and dense semantic embeddings into a single retrieval pipeline. Queries are routed through a three-stage retrieval process, reranked by relevance, and passed to the LLM with precise source citation tracking — so every answer is grounded and auditable. The system was built for both accuracy and cost efficiency, with caching at the retrieval layer to reduce redundant embedding calls.

**Results/metrics**:
- Hybrid retrieval: BM25 + TF-IDF + semantic embeddings (three-stage pipeline)
- P95 query latency: under 200ms
- 500+ automated tests covering retrieval accuracy and edge cases
- Source citation included with every answer — no black-box outputs

**Tech used**: Python, FastAPI, ChromaDB, FAISS, SentenceTransformers, Redis, PostgreSQL, pytest

**Repo**: github.com/ChunkyTortoise/docqa-engine

---

### 3. Enterprise CRM AI Integration (EnterpriseHub)

**Problem solved**: Companies using multiple CRMs — GoHighLevel, HubSpot, Salesforce — face fragmented data and no unified layer for AI-powered workflows across platforms.

**What I built**: EnterpriseHub is a unified CRM integration platform with a single adapter protocol that normalizes data models across GoHighLevel, HubSpot, and Salesforce. On top of this layer, I added an AI chatbot orchestration engine that qualifies leads, logs conversation summaries to the CRM, and triggers downstream workflows automatically. The architecture uses a plugin-style adapter pattern so adding a fourth CRM requires no changes to the core orchestration logic.

**Results/metrics**:
- 3 production CRM adapters: GoHighLevel, HubSpot, Salesforce — unified protocol
- ~5,100 automated tests across the integration layer
- AI chatbot with full CRM read/write: logs interactions, updates contact records, triggers workflows
- P95 latency under 300ms at 10 req/sec load

**Tech used**: Python, FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Redis, Claude API, GoHighLevel API, HubSpot API, Salesforce API, Docker, GitHub Actions

**Repo**: github.com/ChunkyTortoise/EnterpriseHub

---

### 4. Real Estate AI Bot System (Jorge Bots)

**Problem solved**: Real estate agencies have thousands of leads that go cold because human agents can't respond fast enough or consistently qualify buyer vs. seller intent at scale.

**What I built**: A three-bot AI system — Lead Bot, Buyer Bot, and Seller Bot — that qualifies real estate prospects via SMS/chat, routes them to the right agent, and syncs everything to GoHighLevel CRM in real time. Each bot has a distinct persona and scoring model: the Lead Bot computes Financial Readiness Score (FRS) and Psychological Commitment Score (PCS), and hands off to Buyer or Seller Bot when confidence thresholds are met. The handoff system includes circular-prevention logic, rate limiting, and pattern learning from outcome history.

**Results/metrics**:
- 3 production bots with distinct qualification logic (Lead, Buyer, Seller)
- Handoff confidence threshold: 0.7 — tuned against real conversion data
- 360+ automated tests covering bot logic, handoff routing, and CRM sync
- Full GHL CRM integration: contact tagging, workflow triggers, calendar booking

**Tech used**: Python, FastAPI, PostgreSQL, Redis, Claude API, GoHighLevel API, SQLAlchemy, pytest, Docker

**Repo**: github.com/ChunkyTortoise/EnterpriseHub (jorge_real_estate_bots module)

---

### 5. LLM Integration Starter + MCP Server Toolkit (PyPI Package)

**Problem solved**: Developers adding LLM capabilities to Python applications write the same brittle wrappers over and over — no circuit breakers, no streaming, no fallback chains, no cost tracking.

**What I built**: Two complementary libraries. The LLM Integration Starter is a production-ready template for integrating Claude, GPT-4, or Gemini into any Python application — with streaming responses, automatic retry with exponential backoff, fallback chains across providers, and per-request token cost tracking. The MCP Server Toolkit is a FastMCP v2-based server framework for building Model Context Protocol servers, published as `mcp-server-toolkit` on PyPI. Both are designed to be dropped into existing projects with minimal configuration.

**Results/metrics**:
- Published on PyPI: `pip install mcp-server-toolkit`
- Circuit breaker pattern: prevents cascade failures on LLM provider outages
- Streaming support: token-by-token output with backpressure handling
- 250+ automated tests across both libraries
- Fallback chains: automatic provider switching on failure (Claude → GPT-4 → Gemini)

**Tech used**: Python, FastMCP v2, asyncio, Claude API, OpenAI API, Google Gemini API, pytest, PyPI packaging, GitHub Actions CI/CD

**Repo**: github.com/ChunkyTortoise/mcp-toolkit | github.com/ChunkyTortoise/llm-integration-starter

---

## Human Action Checklist

- [ ] Record video intro using script above (phone camera is fine — good lighting matters most)
- [ ] Upload to Upwork: Profile > Video Introduction > Upload
- [ ] Add portfolio items: Profile > Portfolio > Add Work
- [ ] For each item: paste title, description, and a screenshot of the live demo or repo README
- [ ] Link live demo URL in each portfolio item (AgentForge and Prompt Lab have live Streamlit demos)
- [ ] For PyPI package item: screenshot the PyPI page as the portfolio image
