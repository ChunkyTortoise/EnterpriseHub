# Gumroad Update Package — READY TO APPLY

Last updated: 2026-02-18

## Quick Start Checklist

- [ ] Step 1: Update AgentForge product page — 10 min
- [ ] Step 2: Update EnterpriseHub product page — 10 min
- [ ] Step 3: Update DocQA Engine product page — 10 min
- [ ] Step 4: Update Voice AI Platform product page — 10 min
- [ ] Step 5: Update Revenue-Sprint Prompt Toolkit product page — 10 min

---

## How to Update Each Product

1. Go to gumroad.com > Dashboard > Products
2. Click the product > Edit
3. Scroll to Description
4. Add the "Metrics Block" below at the TOP of the existing description (do not delete existing content)
5. Update the subtitle / one-liner if one is shown
6. Click "Save" (NOT "Publish and continue" unless payment method is configured)
7. Verify on the live product page by clicking "View on Gumroad"

**IMPORTANT**: "Publish and continue" does NOT work if payment method is missing — it shows a red toast error and the product does NOT actually publish. Use "Save" instead.

**ALSO**: The Gumroad content editor uses ProseMirror/Tiptap. If pasting formatted text, paste as plain text first (Ctrl+Shift+V / Cmd+Shift+V) and then apply formatting using the editor toolbar. Direct innerHTML injection does not update editor state and will not save.

---

## Product 1: AgentForge

### Metrics Block (paste at TOP of description)

```
Performance Benchmarks:
- 4.3M dispatches/sec throughput
- P99 latency: 0.095ms
- 540+ automated tests
- 4 LLM providers: Claude, OpenAI, Gemini, Ollama
- Production-grade: circuit breakers, rate limiting, audit logs
```

### One-liner (for subtitle or header)

```
Production-proven: 4.3M dispatches/sec | P99 0.095ms | 540+ tests
```

### Screenshots to Add
| What | Status | Source |
|------|--------|--------|
| AgentForge screenshots (7) | EXISTS | `content/gumroad/screenshots/agentforge/agentforge-screenshot-1.png` through `-7.png` |
| Architecture diagram | NEEDS CREATION | Render Mermaid/Figma showing ReAct loop, 4 providers, circuit breakers |
| Benchmark chart | NEEDS CREATION | Generate from benchmark data: 4.3M dispatches/sec, P99 0.095ms |

---

## Product 2: EnterpriseHub (Jorge Bots + BI Dashboard)

### Metrics Block (paste at TOP of description)

```
Platform Metrics:
- 89% AI cost reduction via 3-tier Redis caching
- 8,500+ automated tests across all modules
- P95 API response: < 2 seconds
- 3 CRM integrations: GoHighLevel, Stripe, Twilio
- 3-bot AI system: Lead, Buyer, Seller qualification
- Real-time BI dashboard with Monte Carlo simulation
```

### One-liner (for subtitle or header)

```
Enterprise-grade: 89% cost reduction | 8,500+ tests | P95 <2s
```

### Screenshots to Add
| What | Status | Source |
|------|--------|--------|
| BI dashboard overview | NEEDS CAPTURE | Visit https://ct-enterprise-ai.streamlit.app, full-page screenshot |
| Bot conversation flow | NEEDS CREATION | Mock SMS-style chat showing Lead > Buyer handoff with temperature tags |
| Contra chatbot cover | EXISTS | `content/contra/covers/service3-chatbot.jpg` |

---

## Product 3: docqa-engine (RAG Document Intelligence)

### Metrics Block (paste at TOP of description)

```
RAG Performance:
- Hybrid search: BM25 + Vector (FAISS)
- P95 retrieval: < 200ms
- Citation tracking: 89% accuracy
- Supports: PDF, DOCX, HTML, Markdown
- Production-ready: auth, rate limiting, monitoring
```

### One-liner (for subtitle or header)

```
RAG-powered: P95 <200ms | Hybrid retrieval | 89% citation accuracy
```

### Screenshots to Add
| What | Status | Source |
|------|--------|--------|
| Architecture diagram (BM25 + TF-IDF + semantic pipeline) | NEEDS CREATION | Render Mermaid: 3-stage retrieval with re-ranking |
| Search results UI with citations | NEEDS CREATION | Deploy Streamlit app or create mockup with cited answers |
| Contra RAG cover | EXISTS | `content/contra/covers/service2-rag.jpg` |

---

## Product 4: voice-ai-platform

### Metrics Block (paste at TOP of description)

```
Voice AI Pipeline:
- Real-time transcription + synthesis
- Multi-provider: Deepgram (STT), ElevenLabs (TTS), Claude (LLM)
- Low-latency WebSocket streaming architecture
- Twilio telephony integration (inbound + outbound)
- Production-ready FastAPI with PII detection and cost tracking
```

### One-liner (for subtitle or header)

```
Voice AI: Real-time pipeline | Multi-provider | Low-latency streaming
```

### Screenshots to Add
| What | Status | Source |
|------|--------|--------|
| Architecture diagram (STT > LLM > TTS pipeline) | NEEDS CREATION | Render Mermaid: Deepgram > Claude > ElevenLabs flow with Twilio |
| WebSocket latency chart | NEEDS CREATION | Generate showing streaming latency profile |

---

## Product 5: Revenue-Sprint Prompt Toolkit

### Metrics Block (paste at TOP of description)

```
Delivery Guarantee:
- 14-hour turnaround
- 50+ proven prompt templates
- Optimized for Claude + GPT-4
- Battle-tested on real client projects
- Copy-paste ready deployment
```

### One-liner (for subtitle or header)

```
Fast delivery: 14h guarantee | 50+ templates | Claude + GPT-4 optimized
```

### Screenshots to Add
| What | Status | Source |
|------|--------|--------|
| Template preview (sample prompt) | NEEDS CREATION | Render a clean, formatted sample template showing variables and chain-of-thought structure |
| Template index / TOC | NEEDS CREATION | Render table of contents showing 50+ template categories to prove breadth |
| Gumroad product page | NEEDS CAPTURE | Screenshot the live product listing page at https://cavemindset.gumroad.com |

---

## Pricing Update (Optional but Recommended)

Based on market analysis (February 2026), all products are significantly below market rates. Consider updating prices after adding metrics blocks.

| Product | Current Price | Recommended | Market Rate | Gap |
|---------|--------------|-------------|-------------|-----|
| AgentForge | $39 | $99-$149 | $149-$249 | 74-84% |
| EnterpriseHub | — | $149-$199 | $199-$349 | — |
| DocQA Engine | $49 | $149-$199 | $199-$349 | 75-86% |
| Voice AI Platform | — | $99-$149 | $149-$249 | — |
| Revenue-Sprint | — | $29-$49 | $49-$99 | — |

### 3-Tier Pricing Strategy (Implement per product)

For each product, consider creating three tiers:

| Tier | What's Included | Pricing Multiple |
|------|----------------|-----------------|
| **Starter** | Source code + README + basic docs | 1x (current price) |
| **Pro** | Starter + video walkthrough + architecture docs + email support (30 days) | 2-3x current price |
| **Enterprise** | Pro + 1-hour setup call + custom integration guide + priority support (90 days) | 5-8x current price |

### How to Create Tiers on Gumroad
1. Go to the product > Edit
2. Scroll to "Pricing" section
3. Select "Offer multiple versions"
4. Add three versions with names: Starter, Pro, Enterprise
5. Set prices according to the table above
6. Add a brief description for each tier explaining what's included
7. Save

### Revenue Projections (Conservative)

| Product | Monthly (Starter only) | Monthly (3-tier) | Annual (3-tier) |
|---------|----------------------|-------------------|-----------------|
| AgentForge | $200-$400 | $600-$1,500 | $7K-$18K |
| DocQA | $200-$400 | $600-$1,200 | $7K-$14K |
| Dashboard | $150-$300 | $400-$900 | $5K-$11K |
| Voice AI | $150-$300 | $400-$900 | $5K-$11K |
| Revenue-Sprint | $100-$200 | $200-$500 | $2K-$6K |
| **TOTAL** | **$800-$1,600** | **$2,200-$5,000** | **$26K-$60K** |

---

## Screenshot Creation Checklist

For screenshots that need to be created or captured:

### Capture Settings
- Browser viewport: 1920x1080
- Theme: Dark mode for Streamlit apps
- Disable browser extensions during capture
- Use Chrome DevTools > More tools > "Capture full size screenshot" for clean output
- Crop to remove OS chrome (taskbar, dock, URL bar)
- Compress PNGs with `pngquant` (target < 500KB per image)

### Priority Order for Screenshot Creation

| Priority | Screenshot | Products | Effort |
|----------|-----------|----------|--------|
| P0 | BI Dashboard overview capture | EnterpriseHub, BI Dashboard | Low — capture from live Streamlit app |
| P0 | AgentForge architecture diagram | AgentForge | Medium — Mermaid or Figma |
| P0 | DocQA architecture diagram | DocQA | Medium — Mermaid or Figma |
| P1 | Voice AI pipeline diagram | Voice AI | Medium — Mermaid or Figma |
| P1 | Benchmark chart for AgentForge | AgentForge | Medium — generate from data |
| P1 | Template preview render | Revenue-Sprint | Medium — design clean layout |
| P2 | Search results UI mockup | DocQA | Medium — Streamlit app or mockup |
| P2 | Monte Carlo panel capture | BI Dashboard | Low — capture from live app |

---

## Verification After Updates

After updating each product, verify:

- [ ] Metrics block appears at the top of the description on the live page
- [ ] One-liner subtitle is visible in search results / product card
- [ ] Existing description content below the metrics block is intact
- [ ] Product page loads correctly (no broken formatting)
- [ ] Price is correct (if updated)
- [ ] Screenshots display properly (if added)
