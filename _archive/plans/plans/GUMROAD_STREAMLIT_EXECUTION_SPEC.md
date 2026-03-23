# Gumroad + Streamlit Execution Spec

**Created**: 2026-02-14 | **Status**: Ready for execution | **Est. Total**: ~8h agent + ~6h human

---

## Executive Summary

**Two parallel workstreams** to unlock revenue:
1. **Streamlit**: Deploy 3 demo apps (8-10 min, all code-ready)
2. **Gumroad**: Upload 24 product listings across 7 products x 3 tiers + 3 bundles

**Revenue unlock**: $75K-$125K annual potential from Gumroad alone, plus live demos for cold outreach and Fiverr/Upwork proposals.

---

## Workstream A: Streamlit Deployments (Agent-Led)

### Status: ALL 3 APPS READY TO DEPLOY

| App | Repo | Entry Point | Target URL | Secrets | Risk |
|-----|------|------------|------------|---------|------|
| AgentForge | ai-orchestrator | `streamlit_app.py` | ct-agentforge.streamlit.app | None (mock data) | LOW |
| Prompt Lab | prompt-engineering-lab | `app.py` | ct-prompt-lab.streamlit.app | None | LOW |
| LLM Starter | llm-integration-starter | `app.py` | ct-llm-starter.streamlit.app | None (mock data) | LOW |

**All repos have**: `requirements.txt` committed, `.streamlit/config.toml` (dark theme), pushed to remote, zero external deps.

### Deploy Sequence
1. **Prompt Lab** (simplest, fewest deps)
2. **LLM Starter** (has demo_data/ dir, still self-contained)
3. **AgentForge** (most deps but clean)

### Deploy Steps (per app)
1. Go to share.streamlit.io
2. Select repo: `ChunkyTortoise/{repo-name}`
3. Branch: `main`
4. Main file: entry point from table above
5. Click Deploy
6. Verify all tabs render correctly

### Post-Deploy Verification Checklist

**AgentForge** (6 tabs):
- [ ] Provider Comparison dropdown works
- [ ] Cost Dashboard bar charts render
- [ ] ROI Calculator before/after cards display
- [ ] Trace Viewer shows Mermaid code
- [ ] Testimonials render
- [ ] Advanced Features showcase loads

**Prompt Lab** (4 tabs):
- [ ] Pattern Library: browse patterns, view templates
- [ ] Evaluate: enter text, get 4 metrics
- [ ] A/B Compare: select two patterns, compare
- [ ] Benchmarks: run and view results

**LLM Starter** (5 tabs):
- [ ] Completion: prompt -> mock response + token metrics
- [ ] Streaming: chunked display animation
- [ ] Function Calling: math expression -> calculator result
- [ ] RAG: "Ingested N chunks" message, Q&A works
- [ ] Dashboard: cost/latency P50/P95/P99 metrics

---

## Workstream B: Gumroad Product Uploads

### Phase 1: Agent Prep (Before Human Upload)

#### B1. Build ZIP Packages (6 products need scripts)

Only AgentForge has ZIPs built (`content/gumroad/zips/`). Need packaging for:

| Product | Repo | Starter Contents | Pro Adds | Enterprise Adds |
|---------|------|-----------------|----------|-----------------|
| DocQA | docqa-engine | Source + Docker + README + LICENSE | + CI/CD templates, optimization guide | + Custom tuning, migration guide |
| Insight | insight-engine | Source + Docker + README + LICENSE | + SHAP guide, advanced analytics | + Custom dashboards, BigQuery connector |
| Scraper | scrape-and-serve | Source + Docker + README + LICENSE | + Proxy guide, 15 YAML templates | + Custom configs, pipeline guide |
| Prompt Toolkit | prompt-engineering-lab | Source + Docker + README + LICENSE | + Advanced patterns guide | + Benchmark runner, report generator |
| AI Integration | llm-integration-starter | Source + Docker + README + LICENSE | + Architecture guide, deployment | + Orchestration, observability, K8s |
| Dashboard Templates | insight-engine (subset) | Extracted Streamlit components | + Additional chart types | + Custom styling, data connectors |

**Agent task**: Create `package-zips.sh` per product (or generalize AgentForge's script).

#### B2. Generate Cover Images Spec

All 24 listings need 1600x1200px cover images. Agent can create specs/templates:

| Product | Color Scheme | Hero Visual |
|---------|-------------|-------------|
| AgentForge | Blue/Purple gradient | Multi-provider routing diagram |
| DocQA | Green/Teal gradient | Document -> Answer flow |
| Insight | Orange/Amber gradient | Dashboard with charts |
| Scraper | Red/Coral gradient | Web -> Data pipeline |
| Prompt Toolkit | Cyan/Blue gradient | Prompt template editor |
| AI Integration | Indigo/Violet gradient | LLM connection diagram |
| Dashboard Templates | Gold/Orange gradient | Streamlit component grid |

**Human task**: Create in Canva/Figma using specs (or use AI image generation).

#### B3. Fill Placeholder Content

| Item | Status | Action |
|------|--------|--------|
| Case studies (Pro tiers) | Placeholder "Coming Soon" | Agent can draft from repo metrics |
| Optimization guides (Pro) | Not created | Agent can generate |
| Compliance docs (Enterprise) | Not created | Agent can generate |
| Calendly links | Not created | Human: create 3 event types |
| Google Form (custom examples) | Placeholder URL | Human: create Google Form |
| Slack workspace | Not created | Create on first Enterprise sale |

### Phase 2: Human Upload (24 listings)

#### Upload Order (Revenue-Optimized)

**Day 1 -- AgentForge (ZIPs ready, fastest to market)**:
| # | Product | Tier | Price | Content File |
|---|---------|------|-------|-------------|
| 1 | AgentForge | Starter | $49 | `agentforge-starter-LISTING.md` |
| 2 | AgentForge | Pro | $199 | `agentforge-pro-LISTING.md` |
| 3 | AgentForge | Enterprise | $999 | `agentforge-enterprise-LISTING.md` |

**Day 2 -- Revenue-Sprint (fast new revenue, low prices = low friction)**:
| # | Product | Tier | Price | Content File |
|---|---------|------|-------|-------------|
| 4 | Prompt Toolkit | Starter | $29 | `revenue-sprint-1-prompt-toolkit-LISTING.md` |
| 5 | Prompt Toolkit | Pro | $79 | (in manifest) |
| 6 | Prompt Toolkit | Enterprise | $199 | (in manifest) |
| 7 | AI Integration | Starter | $39 | `revenue-sprint-2-llm-starter-LISTING.md` |
| 8 | AI Integration | Pro | $99 | (in manifest) |
| 9 | AI Integration | Enterprise | $249 | (in manifest) |
| 10 | Dashboard Templates | Starter | $49 | `revenue-sprint-3-dashboard-templates-LISTING.md` |
| 11 | Dashboard Templates | Pro | $99 | (in manifest) |
| 12 | Dashboard Templates | Enterprise | $249 | (in manifest) |
| 13 | Revenue-Sprint Bundle | -- | $99 | (in manifest) |

**Day 3-4 -- High-Value Products (need ZIPs built first)**:
| # | Product | Tier | Price | Content File |
|---|---------|------|-------|-------------|
| 14 | DocQA | Starter | $59 | `docqa-starter-LISTING.md` |
| 15 | DocQA | Pro | $249 | `docqa-pro-LISTING.md` |
| 16 | DocQA | Enterprise | $1,499 | `docqa-enterprise-LISTING.md` |
| 17 | Insight | Starter | $49 | `insight-starter-LISTING.md` |
| 18 | Insight | Pro | $199 | `insight-pro-LISTING.md` |
| 19 | Insight | Enterprise | $999 | `insight-enterprise-LISTING.md` |
| 20 | Scraper | Starter | $49 | `scraper-starter-LISTING.md` |
| 21 | Scraper | Pro | $149 | `scraper-pro-LISTING.md` |
| 22 | Scraper | Enterprise | $699 | `scraper-enterprise-LISTING.md` |
| 23 | All Starters Bundle | -- | $149 | (in manifest, save 28%) |
| 24 | All Pro Bundle | -- | $549 | (in manifest, save 31%) |

### Per-Listing Upload Checklist
For each Gumroad product:
- [ ] Title (from listing file)
- [ ] Description (copy from listing file -- supports markdown)
- [ ] Price
- [ ] Cover image (1600x1200)
- [ ] Product file (ZIP attachment)
- [ ] URL slug (e.g., `agentforge-starter`)
- [ ] Tags (5-8 SEO tags from spec)
- [ ] Cross-sell links (after all products created)
- [ ] Preview enabled

---

## Parallel Execution Lanes

```
Timeline:  ──────────────────────────────────────────────────────────►

AGENT LANE 1 (Streamlit):
  [Deploy Prompt Lab] [Deploy LLM Starter] [Deploy AgentForge] [Verify All 3]
  ~~~~ 10 min total ~~~~

AGENT LANE 2 (ZIP Packaging):
  [Generalize package script] [Build 6x product ZIPs] [Validate contents]
  ~~~~~~~~~ 2-3 hours ~~~~~~~~~

AGENT LANE 3 (Content Generation):
  [Draft case studies] [Write optimization guides] [Generate compliance docs]
  ~~~~~~~~~ 3-4 hours ~~~~~~~~~

HUMAN LANE (After Agent Prep):
  [Set up Gumroad payment] [Create Calendly events] [Create cover images]
  [Upload Day 1: AgentForge 3 listings] [Upload Day 2: Sprint 10 listings]
  [Upload Day 3-4: High-value 11 listings] [Add cross-sell links]
  ~~~~~~~~~ 6-8 hours over 4 days ~~~~~~~~~
```

---

## Blockers & Prerequisites

### Must Do Before Upload (Critical)
| Blocker | Owner | Est. Time | Notes |
|---------|-------|-----------|-------|
| Gumroad payment method | Human | 5 min | Publishing fails without it |
| Calendly event types (3) | Human | 15 min | 30-min consult, 60-min deep-dive, team training |
| Cover images (7 base + tier variants) | Human | 3-4 hrs | Use Canva/AI. Can upload products without and add later |

### Nice-to-Have (Can Add Post-Launch)
| Item | Owner | Notes |
|------|-------|-------|
| Google Form for custom examples | Human | Placeholder OK for now |
| Slack workspace | Human | Create on first Enterprise sale |
| Video demos | Human/Agent | Increases conversion 15-30% |
| Screenshots (5 products missing) | Agent | Can capture from Streamlit deploys |

---

## Beads Task Breakdown

### Agent Tasks (Parallelize)
```
bd create --title="Deploy 3 Streamlit apps to Streamlit Cloud" --type=task --priority=1
bd create --title="Build ZIP packaging scripts for 6 Gumroad products" --type=task --priority=1
bd create --title="Draft case studies for Pro tier products (4)" --type=task --priority=2
bd create --title="Write optimization/deployment guides for Pro tiers" --type=task --priority=2
bd create --title="Capture screenshots from deployed Streamlit apps" --type=task --priority=3
bd create --title="Generate Gumroad SEO tags and cross-sell link map" --type=task --priority=3
```

### Human Tasks
```
bd create --title="Set up Gumroad payment method" --type=task --priority=0
bd create --title="Create 3 Calendly event types" --type=task --priority=1
bd create --title="Create cover images for 7 products (Canva)" --type=task --priority=2
bd create --title="Upload AgentForge 3 tiers to Gumroad (Day 1)" --type=task --priority=1
bd create --title="Upload Revenue-Sprint 9 tiers + bundle to Gumroad (Day 2)" --type=task --priority=1
bd create --title="Upload DocQA/Insight/Scraper 9 tiers + 2 bundles (Day 3-4)" --type=task --priority=1
```

---

## Revenue Projections

| Scenario | Monthly | Annual | Assumption |
|----------|---------|--------|------------|
| Conservative | $2K-$4K | $24K-$48K | 5-10 Starter sales/mo, 1-2 Pro |
| Moderate | $6K-$10K | $72K-$120K | + Enterprise sales quarterly |
| Optimistic | $10K-$18K | $120K-$216K | + consulting upsells, bundles |

**Break-even on time investment**: 1-2 Starter sales covers the effort.

---

## Success Metrics

| Metric | Target | Measure |
|--------|--------|---------|
| Streamlit apps live | 3/3 | All URLs accessible |
| Gumroad products listed | 24/24 | All visible on profile |
| First Gumroad sale | Within 7 days | Revenue tracker |
| Streamlit daily visitors | >10/day within 30 days | Streamlit analytics |
| Gumroad page views | >100/week within 30 days | Gumroad analytics |
