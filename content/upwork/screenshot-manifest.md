# Screenshot Manifest for Upwork Portfolio

Generated: 2026-02-18

## Existing Visual Assets

### Gumroad AgentForge Screenshots (7 files)
- `content/gumroad/screenshots/agentforge/agentforge-screenshot-1.png`
- `content/gumroad/screenshots/agentforge/agentforge-screenshot-2.png`
- `content/gumroad/screenshots/agentforge/agentforge-screenshot-3.png`
- `content/gumroad/screenshots/agentforge/agentforge-screenshot-4.png`
- `content/gumroad/screenshots/agentforge/agentforge-screenshot-5.png`
- `content/gumroad/screenshots/agentforge/agentforge-screenshot-6.png`
- `content/gumroad/screenshots/agentforge/agentforge-screenshot-7.png`

### Contra Cover Images (3 files)
- `content/contra/covers/service1-dashboard.jpg`
- `content/contra/covers/service2-rag.jpg`
- `content/contra/covers/service3-chatbot.jpg`

### Screenshot Spec Docs (detailed annotation guides)
- `content/visual/agentforge-screenshots.md` — 7 screenshot specs
- `content/visual/docqa-screenshots.md` — 7 screenshot specs
- `content/visual/enterprisehub-screenshots.md` — 7 screenshot specs
- `content/visual/insight-screenshots.md` — 7 screenshot specs
- `content/visual/metrics-graphics-spec.md` — 8 before/after and ROI graphics

---

## Item 1: AgentForge

| Screenshot | Status | Source | Notes |
|-----------|--------|--------|-------|
| Architecture diagram (Agent > Dispatcher > LLM Provider flow) | NEEDS CREATION | Render from Mermaid or Figma | Show ReAct loop, 4 providers, circuit breakers |
| Benchmark chart (throughput + latency numbers) | NEEDS CREATION | Generate from benchmark data | 4.3M dispatches/sec, P99 0.095ms |
| Test results terminal screenshot | NEEDS CAPTURE | `pytest agentforge/tests/ -q` | Run and capture terminal with 540+ passed |
| Gumroad screenshots 1-7 | EXISTS | `content/gumroad/screenshots/agentforge/` | May be reusable for Upwork portfolio |

**Recommended Upwork images**:
1. Reuse best Gumroad screenshot as primary (dashboard hero or architecture)
2. Create fresh benchmark chart with clear 4.3M/sec callout
3. Terminal screenshot of test suite passing

---

## Item 2: EnterpriseHub Jorge Bots

| Screenshot | Status | Source | Notes |
|-----------|--------|--------|-------|
| Bot conversation flow (Lead > Buyer handoff) | NEEDS CREATION | Mock conversation or Streamlit demo | Show SMS-style chat with temperature tagging |
| BI dashboard overview | NEEDS CAPTURE | https://ct-enterprise-ai.streamlit.app | Lead metrics, temperature distribution, funnel |
| Jorge bot status cards | NEEDS CAPTURE | Streamlit app bot dashboard page | 3 bot cards with latency and handoff stats |
| GHL CRM sync panel | NEEDS CAPTURE | Streamlit app CRM page | Real-time sync status, tag distribution |
| Contra chatbot cover | EXISTS | `content/contra/covers/service3-chatbot.jpg` | May work as supplementary |

**Recommended Upwork images**:
1. BI dashboard hero (capture from live Streamlit app)
2. Bot conversation flow mockup showing handoff
3. Reuse Contra chatbot cover as supplementary

---

## Item 3: docqa-engine (RAG)

| Screenshot | Status | Source | Notes |
|-----------|--------|--------|-------|
| Search results UI with citations | NEEDS CREATION | Deploy Streamlit app or mock | Show query > cited answer with confidence score |
| Architecture diagram (BM25 + TF-IDF + semantic pipeline) | NEEDS CREATION | Render from Mermaid | 3-stage retrieval flow with re-ranking |
| Vector search visualization (t-SNE scatter) | NEEDS CREATION | Generate from test embeddings | Cluster plot with query point highlighted |
| Test coverage terminal | NEEDS CAPTURE | `pytest` on docqa-engine repo | 500+ tests passing |
| Contra RAG cover | EXISTS | `content/contra/covers/service2-rag.jpg` | Can reuse as supplementary |

**Recommended Upwork images**:
1. Architecture diagram showing hybrid retrieval pipeline
2. Search results UI with citation confidence scores
3. Reuse Contra RAG cover as supplementary

---

## Item 4: Revenue-Sprint AI Prompt Toolkit

| Screenshot | Status | Source | Notes |
|-----------|--------|--------|-------|
| Template preview (sample prompt) | NEEDS CREATION | Render a sample template in clean format | Show structured prompt with variables |
| Gumroad product page | NEEDS CAPTURE | https://cavemindset.gumroad.com | Capture the product listing page |
| Template index / table of contents | NEEDS CREATION | Render TOC showing 50+ template categories | Prove breadth of coverage |

**Recommended Upwork images**:
1. Clean template preview showing a RAG prompt template
2. Product page screenshot from Gumroad

---

## Item 5: Streamlit BI Analytics Dashboard

| Screenshot | Status | Source | Notes |
|-----------|--------|--------|-------|
| Dashboard overview (full page) | NEEDS CAPTURE | https://ct-enterprise-ai.streamlit.app | Main metrics strip + charts |
| Monte Carlo simulation panel | NEEDS CAPTURE | Streamlit app Monte Carlo page | Pipeline forecasting with confidence bands |
| Churn detection view | NEEDS CAPTURE | Streamlit app churn page | Predictive scoring chart |
| Sentiment analysis panel | NEEDS CAPTURE | Streamlit app sentiment page | Sentiment over time trend |
| Contra dashboard cover | EXISTS | `content/contra/covers/service1-dashboard.jpg` | Can reuse as supplementary |

**Recommended Upwork images**:
1. Dashboard overview hero (capture from live app)
2. Monte Carlo forecasting panel with confidence intervals
3. Reuse Contra dashboard cover as supplementary

---

## Creation Priority

| Priority | Screenshot | Effort | Impact |
|----------|-----------|--------|--------|
| P0 | BI Dashboard overview (Item 2 + 5) | Low — capture from live app | High — used in 2 portfolio items |
| P0 | AgentForge architecture diagram (Item 1) | Medium — Mermaid or Figma | High — primary differentiator |
| P0 | DocQA architecture diagram (Item 3) | Medium — Mermaid or Figma | High — explains hybrid retrieval |
| P1 | Benchmark chart for AgentForge (Item 1) | Medium — generate from data | High — proves performance claim |
| P1 | Monte Carlo panel capture (Item 5) | Low — capture from live app | Medium — proves analytics depth |
| P1 | Bot conversation flow mockup (Item 2) | Medium — design mockup | Medium — shows handoff in action |
| P2 | Gumroad product page capture (Item 4) | Low — browser screenshot | Low — supplementary |
| P2 | Test suite terminal captures (Items 1-3) | Low — run pytest, capture | Low — trust signal |

---

## Capture Checklist

- [ ] Set browser viewport to 1920x1080
- [ ] Use dark mode for all Streamlit captures
- [ ] Disable browser extensions during capture
- [ ] Use Chrome DevTools "Capture screenshot" for clean output
- [ ] Crop to remove OS chrome (taskbar, dock, URL bar)
- [ ] Compress PNGs with pngquant (target < 500KB per image)
- [ ] Name files: `upwork-{item}-{description}.png`
