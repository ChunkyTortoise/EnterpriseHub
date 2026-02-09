# Continuation Prompt — February 9, 2026 (Service Catalog Sprint 2)

## Session Recovery
Run `bd prime` first, then read this file and `plans/SERVICE_CATALOG_DEV_SPEC.md`.

---

## What Happened Last Session

### Sprint 1 COMPLETED (3 parallel agents)

| Bead | Agent | Deliverable | Status |
|------|-------|-------------|--------|
| `ruy` | A: Vector DB adapter | `docqa-engine/docqa_engine/vector_store.py` — VectorStoreBase ABC + InMemory/ChromaDB/Pinecone implementations, 14 new tests, sidebar selector in app.py | **CLOSED** (committed: `4632146`, `ded0ddf`) |
| `cnq` | B: Industry config | `ghl_real_estate_ai/config/industry_config.py` — 7 dataclasses, 4 YAML configs (real_estate_rancho, real_estate_dallas, dental_practice, hvac_services), 44 tests, bot constructors wired | **CLOSED** |
| `ia3` | C: RAG case study | `plans/case-study-rag-system.md` — 2,200 words, Mermaid diagram, code samples from docqa-engine | **CLOSED** |

### Uncommitted Changes

**docqa-engine** (`/Users/cave/Documents/GitHub/docqa-engine`):
- `app.py` — Vector store sidebar selector (39 insertions)
- All other Sprint 1 changes already committed (`4632146`, `ded0ddf`)

**EnterpriseHub** (this repo):
Modified:
- `ghl_real_estate_ai/agents/jorge_buyer_bot.py` — industry_config param in __init__
- `ghl_real_estate_ai/agents/jorge_seller_bot.py` — industry_config param in __init__
- `ghl_real_estate_ai/agents/lead_bot.py` — industry_config param in __init__
- `ghl_real_estate_ai/agents/buyer_intent_decoder.py` — config integration
- `ghl_real_estate_ai/agents/intent_decoder.py` — config integration
- `ghl_real_estate_ai/agents/seller_intent_decoder.py` — config integration
- `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py` — config integration
- `requirements.txt` — Added Jinja2>=3.1.0

New:
- `ghl_real_estate_ai/config/__init__.py` — IndustryConfig exports
- `ghl_real_estate_ai/config/industry_config.py` — 7 dataclasses, from_yaml(), default_real_estate()
- `ghl_real_estate_ai/config/industries/real_estate_rancho.yaml` — 175 lines
- `ghl_real_estate_ai/config/industries/real_estate_dallas.yaml` — 147 lines
- `ghl_real_estate_ai/config/industries/dental_practice.yaml` — 117 lines
- `ghl_real_estate_ai/config/industries/hvac_services.yaml` — 119 lines
- `ghl_real_estate_ai/agents/bot_personality.py` — personality types
- `ghl_real_estate_ai/agents/personalities/` — personality data
- `ghl_real_estate_ai/agents/personality_config.py` — personality config
- `tests/test_industry_config.py` — 44 tests
- `plans/case-study-rag-system.md` — RAG case study
- `plans/SERVICE_CATALOG_DEV_SPEC.md` — Full execution spec

---

## Step 1: Commit Sprint 1 Changes

```bash
# 1. docqa-engine — commit remaining app.py change
cd /Users/cave/Documents/GitHub/docqa-engine
git add app.py
git commit -m "feat: add vector store selector to Streamlit sidebar"
git push

# 2. EnterpriseHub — commit industry config layer + case study
cd /Users/cave/Documents/GitHub/EnterpriseHub
git add ghl_real_estate_ai/config/ \
        ghl_real_estate_ai/agents/jorge_buyer_bot.py \
        ghl_real_estate_ai/agents/jorge_seller_bot.py \
        ghl_real_estate_ai/agents/lead_bot.py \
        ghl_real_estate_ai/agents/buyer_intent_decoder.py \
        ghl_real_estate_ai/agents/intent_decoder.py \
        ghl_real_estate_ai/agents/seller_intent_decoder.py \
        ghl_real_estate_ai/agents/bot_personality.py \
        ghl_real_estate_ai/agents/personality_config.py \
        ghl_real_estate_ai/agents/personalities/ \
        ghl_real_estate_ai/services/jorge/jorge_handoff_service.py \
        requirements.txt \
        tests/test_industry_config.py \
        plans/case-study-rag-system.md \
        plans/SERVICE_CATALOG_DEV_SPEC.md
git commit -m "feat: industry-agnostic bot config layer + RAG case study (Sprint 1)"
git push

# 3. Sync beads
bd sync
```

---

## Step 2: Clean Up Stale WS Beads

These in-progress beads are from a prior WS plan and overlap with Sprint 1 work:

| Bead | Description | Overlap | Action |
|------|-------------|---------|--------|
| `hji` | WS1.5: Bot personality tests | Covered by cnq (44 tests) | Close |
| `irr` | WS1.4: Dental vertical | Covered by cnq (dental_practice.yaml) | Close |
| `ach` | WS2.4: docqa-engine client demo tests | Partially done, Sprint 2 lcx will cover | Close |

```bash
bd close hji irr ach --reason="Superseded by Sprint 1 service catalog beads (cnq, ruy)"
```

---

## Step 3: Launch Sprint 2 (3 Parallel Agents)

Sprint 2 is now **unblocked** — `ruy` and `cnq` are both CLOSED.

### Agent D: Client Demo Mode (bead `lcx`)

```
Launch with: Task subagent_type=general-purpose run_in_background=true

PROMPT:
You are adding a client demo mode to the docqa-engine Streamlit app.

REPO: /Users/cave/Documents/GitHub/docqa-engine
BEAD: lcx — "docqa-engine: Client demo mode — upload & query flow"
DEPENDS ON: bead ruy (vector_store.py with VectorStoreBase already exists)

CONTEXT:
- app.py has 5 tabs: Documents, Ask Questions, Prompt Lab, Chunking Lab, Stats
- Plus a new vector store sidebar selector (just committed)
- DocQAPipeline in pipeline.py orchestrates the full RAG flow
- Pipeline stored in st.session_state
- run_async() helper wraps asyncio for Streamlit
- Demo docs in demo_docs/ (python_guide.md, etc.)
- VectorStoreBase ABC in docqa_engine/vector_store.py
- InMemoryVectorStore, ChromaDBVectorStore, PineconeVectorStore available

IMPLEMENTATION:
1. Add a new "Try It" tab as the FIRST tab in app.py:
   - st.file_uploader for PDF/DOCX/TXT/CSV (max 10MB)
   - Chunking strategy dropdown (default: semantic_tfidf)
   - Vector store selector (In-Memory / ChromaDB)
   - After upload: auto-ingest, show chunk count + processing time
   - Question input with st.text_input
   - Answer display with citations (source doc, chunk text, relevance score)
   - Expandable "Debug" section showing retrieved chunks, scores, timing
2. Add a sidebar "Quick Start" guide with 3 sample questions
3. Add progress indicators during ingestion and search
4. Write 10-15 tests in tests/test_demo_mode.py

CONSTRAINTS:
- Must work without API keys (use mock LLM in demo mode)
- File uploads stored in st.session_state (no disk persistence)
- Max 10MB per file, max 5 files
- Show processing time for each step
- Follow existing Streamlit patterns in app.py
- Run tests after to verify: pytest tests/ -v
```

### Agent E: Interactive Chatbot Widget (bead `s7y`)

```
Launch with: Task subagent_type=general-purpose run_in_background=true

PROMPT:
You are building an interactive chatbot demo widget for EnterpriseHub's Streamlit demo.

REPO: /Users/cave/Documents/GitHub/EnterpriseHub
BEAD: s7y — "EnterpriseHub: Interactive chatbot demo widget"
DEPENDS ON: bead cnq (IndustryConfig in ghl_real_estate_ai/config/industry_config.py)

CONTEXT:
- Streamlit demo at ghl_real_estate_ai/streamlit_demo/
- Admin dashboard at ghl_real_estate_ai/streamlit_demo/admin_dashboard.py
- Bot classes: LeadBotWorkflow, JorgeBuyerBot, JorgeSellerBot
- Bots return dicts with: response, temperature, handoff_signals, scores
- IndustryConfig loads from YAML, provides personality, intents, questions
- IndustryConfig dataclass in ghl_real_estate_ai/config/industry_config.py
- 4 YAML configs in ghl_real_estate_ai/config/industries/ (rancho, dallas, dental, hvac)
- Demo mode uses mock LLM (no API keys required)

IMPLEMENTATION:
1. Create ghl_real_estate_ai/streamlit_demo/components/chatbot_widget.py:
   - render_chatbot_widget(industry_config: IndustryConfig) function
   - st.chat_message for bot/user messages
   - st.chat_input for user text
   - Sidebar: industry selector, intent scores, temperature gauge
   - Conversation history in st.session_state
   - Process messages through LeadBotWorkflow (mock mode)
   - Show real-time: FRS score, PCS score, temperature tag
   - Highlight handoff triggers when detected
2. Add "Talk to the Bot" as first tab in admin_dashboard.py
3. Pre-seed with 3 example conversations (buyer, seller, cold lead)
4. Write 10-15 tests in tests/test_chatbot_widget.py

CONSTRAINTS:
- Must work in demo mode (USE_MOCK_LLM=true)
- No API keys required
- Use st.chat_message (Streamlit native chat UI)
- Show processing time per response
- Follow existing component patterns in streamlit_demo/components/
- Run tests after: python -m pytest tests/test_chatbot_widget.py -v
```

### Agent F: Agent Flow Visualizer (bead `tml`)

```
Launch with: Task subagent_type=general-purpose run_in_background=true

PROMPT:
You are building a Streamlit agent flow visualizer for the ai-orchestrator (AgentForge) project.

REPO: /Users/cave/Documents/GitHub/ai-orchestrator
BEAD: tml — "ai-orchestrator: Streamlit agent flow visualizer demo"

CONTEXT:
- AIOrchestrator is the core class (orchestrator.py): chat(), stream(), compare()
- ProviderBase ABC (providers/base.py): chat(), stream(), is_configured()
- 5 providers: Claude, OpenAI, Gemini, Perplexity, Mock
- MockProvider returns canned responses (no API keys needed)
- AIResponse dataclass: content, provider, model, elapsed_ms, metadata
- ToolRegistry + ToolExecutor for tool chaining
- TemplateRegistry for prompt templates
- CLI via Click: agentforge "prompt" --provider mock
- Dependencies: httpx, python-dotenv (minimal)

IMPLEMENTATION:
1. Create app.py at repo root with 4 tabs:
   Tab 1 "Dashboard": Provider status grid (configured vs not), rate limiter status
   Tab 2 "Chat": Prompt input + provider dropdown + execute → show AIResponse
     - Streaming mode toggle (word-by-word display)
     - Show elapsed_ms, model, metadata
   Tab 3 "Compare": Run same prompt across selected providers
     - Side-by-side results table
     - Latency bar chart (st.bar_chart)
     - Cost comparison if available
   Tab 4 "Tool Chain": Visual tool chain builder
     - Tool list from ToolRegistry
     - Drag-and-drop chain builder (simplified: ordered list)
     - Execute chain → show step-by-step results
     - Generate Mermaid flow diagram of execution
2. Create requirements-demo.txt: streamlit>=1.31.0
3. Create .streamlit/config.toml (port 8505, dark theme)
4. Add Makefile target: demo: streamlit run app.py
5. Write 10-15 tests in tests/test_app.py

CONSTRAINTS:
- Must work with MockProvider only (no API keys required)
- Use AIOrchestrator as the main interface (don't bypass to providers)
- Follow existing code patterns (async, dataclasses, type hints)
- Streamlit chat UI for the Chat tab
- Show real-time streaming with st.write_stream
- Run tests after: pytest tests/test_app.py -v
```

---

## Step 4: Post-Sprint 2 Verification & Commit

After all 3 agents complete:

```bash
# Verify tests
cd /Users/cave/Documents/GitHub/docqa-engine && pytest tests/ -v
cd /Users/cave/Documents/GitHub/EnterpriseHub && python -m pytest tests/test_chatbot_widget.py -v
cd /Users/cave/Documents/GitHub/ai-orchestrator && pytest tests/test_app.py -v

# Commit per repo
cd /Users/cave/Documents/GitHub/docqa-engine
git add app.py tests/test_demo_mode.py
git commit -m "feat: client demo mode with upload & query flow"
git push

cd /Users/cave/Documents/GitHub/EnterpriseHub
git add ghl_real_estate_ai/streamlit_demo/components/chatbot_widget.py tests/test_chatbot_widget.py
git commit -m "feat: interactive chatbot demo widget with industry selector"
git push

cd /Users/cave/Documents/GitHub/ai-orchestrator
git add app.py requirements-demo.txt .streamlit/ tests/test_app.py Makefile
git commit -m "feat: Streamlit agent flow visualizer with 4 tabs"
git push

# Close beads
bd close lcx s7y tml
bd sync
```

---

## Sprint 3 Reference

After Sprint 2, launch Sprint 3 (beads `58t`, `gwn`, `hfi`). Full agent prompts are in `plans/SERVICE_CATALOG_DEV_SPEC.md` lines 731-849.

| Bead | Description | Repo |
|------|-------------|------|
| `58t` | REST API + auth for docqa-engine | docqa-engine |
| `gwn` | HubSpot CRM adapter | EnterpriseHub |
| `hfi` | Agent templates + REST API | ai-orchestrator |

---

## Current Bead State

### Closed (Sprint 1)
- `ruy` — Vector DB adapter (docqa-engine)
- `cnq` — Industry config layer (EnterpriseHub)
- `ia3` — RAG case study (portfolio)

### Open — Sprint 2 (ready to launch)
- `lcx` (P1) — Client demo mode (docqa-engine) — was blocked by ruy, NOW UNBLOCKED
- `s7y` (P1) — Chatbot widget (EnterpriseHub) — was blocked by cnq, NOW UNBLOCKED
- `tml` (P2) — Agent visualizer (ai-orchestrator) — no blockers

### Open — Sprint 3 (blocked by Sprint 2)
- `58t` (P2) — REST API + auth (docqa-engine) — blocked by ruy (CLOSED, ready when Sprint 2 done)
- `gwn` (P2) — HubSpot adapter (EnterpriseHub) — no blockers (can start anytime)
- `hfi` (P2) — Agent templates (ai-orchestrator) — blocked by tml

### Open — Non-dev (human action required)
- `4j2` (P2) — Upwork: Buy connects + proposals
- `9je` (P2) — LinkedIn: Recommendation requests
- `pbz` (P3) — LinkedIn: Content cadence
- `vp9` (P3) — Upwork: Profile improvements

### Stale — Close these first
- `hji` — WS1.5: Bot personality tests (superseded by cnq)
- `irr` — WS1.4: Dental vertical (superseded by cnq)
- `ach` — WS2.4: Demo tests (superseded by lcx)

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `plans/SERVICE_CATALOG_DEV_SPEC.md` | Full 9-bead execution spec with all agent prompts |
| `plans/case-study-rag-system.md` | RAG case study (Sprint 1 output) |
| `ghl_real_estate_ai/config/industry_config.py` | IndustryConfig dataclass (Sprint 1 output) |
| `ghl_real_estate_ai/config/industries/*.yaml` | 4 industry YAML configs (Sprint 1 output) |

---

## Application Tracker (14 Opportunities)

| # | Company | Role | Platform | Status | Rate |
|---|---------|------|----------|--------|------|
| 1 | Customer AI Q&A | AI Setup | Upwork | Submitted | $250 fixed |
| 2 | Code Intelligence | RAG/LLM Engineer | Upwork | **Viewed by client** | $500 fixed |
| 3 | Plush AI | Bug Fix | Upwork | Submitted | $70/hr |
| 4 | FloPro Jamaica (Chase) | AI Secretary SaaS | Upwork | **Active — awaiting contract offer** | $75/hr |
| 5 | AI Consultant CRMS | Enhancement | Upwork | Submitted (Jan 21) | -- |
| 6 | Kialash Persad | Sr AI Agent Eng | Upwork | **Active — call Tue 4 PM EST** | -- |
| 7 | Prompt Health | Sr AI Engineer | Ashby | Submitted (listing active) | $160K-$220K |
| 8 | Rula | Principal AI Eng | Ashby | Submitted (listing active) | $229K-$284K |
| 9 | Concourse | Founding AI/ML | YC/WAAS | **Signup form filled — needs password** | $150K-$250K |
| 10-14 | Round 2 (5 jobs) | RAG/AI roles | Upwork | **BLOCKED ($12 Connects)** | $55-65/hr |

**Key dates:**
- **Tue Feb 10, 4 PM EST**: Call with Kialash Persad (confirmed)
- **Thu Feb 12**: Availability offered to Chase Ashley
