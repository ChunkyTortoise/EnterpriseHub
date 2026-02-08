# Agent Team Execution Spec — February 8, 2026

**Purpose**: Comprehensive specification for a team of parallel agents to execute all remaining work across the EnterpriseHub ecosystem.

**Current State**: All 7 repos have green CI. 3,955 tests collected (26 collection errors). A/B testing persistence committed. Portfolio site deployed.

---

## Quick Reference: Repo Locations

| Repo | Local Path | Remote |
|------|-----------|--------|
| EnterpriseHub | `/Users/cave/Documents/GitHub/EnterpriseHub` | `ChunkyTortoise/EnterpriseHub` |
| jorge | `/Users/cave/Documents/GitHub/jorge_real_estate_bots` | `ChunkyTortoise/jorge_real_estate_bots` |
| Revenue-Sprint | `/Users/cave/Documents/GitHub/Revenue-Sprint` | `ChunkyTortoise/Revenue-Sprint` |
| ai-orchestrator | `/Users/cave/Documents/GitHub/ai-orchestrator` | `ChunkyTortoise/ai-orchestrator` |
| insight-engine | `/Users/cave/Documents/GitHub/insight-engine` | `ChunkyTortoise/insight-engine` |
| docqa-engine | `/Users/cave/Documents/GitHub/docqa-engine` | `ChunkyTortoise/docqa-engine` |
| scrape-and-serve | `/Users/cave/Documents/GitHub/scrape-and-serve` | `ChunkyTortoise/scrape-and-serve` |
| Portfolio Site | `/Users/cave/Documents/GitHub/chunkytortoise.github.io` | `ChunkyTortoise/chunkytortoise.github.io` |

---

## Phase 1: Test Collection Error Fix (EnterpriseHub)

**Priority**: P1 — blocks accurate test count reporting
**Estimated Complexity**: Medium
**Parallelizable**: No (single repo, shared root cause)

### Problem

26 test files fail to collect due to `ModuleNotFoundError: No module named 'bots'`. This is a cross-repo dependency — 10+ source files in `ghl_real_estate_ai/` import from `bots.shared.ml_analytics_engine` (the jorge repo).

### Root Cause

These files import at module level from `bots.shared.ml_analytics_engine`:
```
ghl_real_estate_ai/agents/jorge_seller_bot.py:35
ghl_real_estate_ai/agents/predictive_lead_bot.py:22
ghl_real_estate_ai/services/client_preference_learning_engine.py:32
```

And via lazy imports (try/except or TYPE_CHECKING):
```
ghl_real_estate_ai/api/routes/ml_scoring.py:58 (inside try/except)
ghl_real_estate_ai/agents/jorge_buyer_bot.py:71 (inside try)
ghl_real_estate_ai/agents/lead_bot.py:33 (inside try)
ghl_real_estate_ai/services/predictive_lead_behavior_service.py:246 (inside try)
ghl_real_estate_ai/services/proactive_conversation_intelligence.py:70 (inside try)
```

### Fix Strategy

**Option A (Recommended)**: Create a local stub module `ghl_real_estate_ai/stubs/bots_stub.py` that provides mock `MLAnalyticsEngine` and `get_ml_analytics_engine` when `bots` package is unavailable. Convert all top-level imports to try/except with fallback:

```python
try:
    from bots.shared.ml_analytics_engine import MLAnalyticsEngine, get_ml_analytics_engine
except ImportError:
    from ghl_real_estate_ai.stubs.bots_stub import MLAnalyticsEngine, get_ml_analytics_engine
```

**Option B**: Add `conftest.py` mock that patches `sys.modules['bots']` before test collection.

### Affected Files (26 test files)

```
tests/agents/test_advanced_agent_ecosystem.py
tests/agents/test_feature_integration.py
tests/agents/test_jorge_seller_bot.py
tests/agents/test_seller_bot_features.py
tests/api/mobile/test_ar_integration.py
tests/api/mobile/test_mobile_endpoints.py
tests/api/mobile/test_voice_integration.py
tests/api/test_attribution_reports.py
tests/api/test_jorge_advanced_routes.py
tests/api/test_predictive_analytics.py
tests/api/test_pricing_optimization_routes.py
tests/command_center/test_chart_builders.py
tests/integration/test_bi_integration.py
tests/integration/test_buyer_bot_integration.py
tests/integration/test_jorge_revenue_platform_e2e.py
tests/integration/test_lead_attribution_integration.py
tests/ml/test_ml_analytics_engine_track3.py
tests/performance/test_jorge_platform_load_testing.py
tests/security/test_enterprise_security_comprehensive.py
tests/security/test_jorge_webhook_security.py
ghl_real_estate_ai/tests/test_api_analytics.py
ghl_real_estate_ai/tests/test_api_lead_lifecycle.py
ghl_real_estate_ai/tests/test_api_team.py
ghl_real_estate_ai/tests/test_health_endpoint.py
ghl_real_estate_ai/tests/test_jorge_seller_bot.py
ghl_real_estate_ai/tests/test_portal_api.py
```

### Verification

```bash
# Before: 3,955 collected, 26 errors
python -m pytest --co -q 2>&1 | tail -3

# After: should see 3,955+ collected, 0 errors
python -m pytest --co -q 2>&1 | tail -3

# CI must still be green
```

---

## Phase 2: Portfolio Site Updates (4 parallel sub-tasks)

**Priority**: P1
**Parallelizable**: Yes — 4 agents can work on separate HTML files simultaneously
**Repo**: `/Users/cave/Documents/GitHub/chunkytortoise.github.io`

### 2A: Services Page — Add LLMOps Service

**File**: `services.html`

Add "LLMOps & Cost Optimization" as a **Strategic tier** service ($90-150/hr):
- 89% token cost reduction methodology (proven in EnterpriseHub L1/L2/L3 cache)
- Cache layer design (L1 in-memory, L2 Redis, L3 PostgreSQL)
- Prompt optimization and model routing
- Multi-provider orchestration (Claude, Gemini, Perplexity)
- Proof link: [EnterpriseHub orchestrator](https://github.com/ChunkyTortoise/EnterpriseHub)

Match existing service card HTML structure in the file. Place after "AI Agent Development" card.

### 2B: Case Studies Page — Add 2 New Case Studies

**File**: `case-studies.html`

Currently has 3 case studies. Add 2 more:

**Case Study 4 — Jorge Bot Platform**:
- Problem: 40% lead loss from slow manual response (>15 min avg)
- Solution: 3-bot system (Lead/Buyer/Seller) with cross-bot handoff, A/B testing (4 experiments), GHL CRM integration, intent decoding with GHL score boosts
- Architecture: FastAPI + PostgreSQL + Redis + Claude AI, shared services layer
- Results: 279 tests passing, 0.7 confidence threshold, circular prevention, rate limiting (3/hr, 10/day), deterministic variant assignment via hash bucketing
- Tech: Python, FastAPI, PostgreSQL, Redis, Claude API, GoHighLevel

**Case Study 5 — Revenue Sprint**:
- Problem: 15+ hours/week on manual prospecting and proposal writing
- Solution: AI job scanner with 105-point scoring rubric, 4-agent proposal pipeline, prompt injection tester (60+ attack patterns)
- Architecture: 3 products — Injection Tester, RAG Cost Optimizer, Agent Orchestrator
- Results: 240 tests passing, security-first design, automated qualification pipeline
- Tech: Python, FastAPI, Claude API, BeautifulSoup, Pandas

Match existing case study HTML card structure.

### 2C: Footer Social Links on All 5 Pages

**Files**: `index.html`, `projects.html`, `services.html`, `certifications.html`, `case-studies.html`

Add social links to footer alongside existing GitHub link:
- LinkedIn: `https://linkedin.com/in/cayman-roden`
- Upwork: `https://www.upwork.com/freelancers/~01ee20599d13f4c8c9`
- Email: `mailto:caymanroden@gmail.com`

Use appropriate icons (FontAwesome or inline SVG matching existing style).

### 2D: Certifications + Projects Data Updates

**Files**: `certifications.html`, `projects.html`

1. **Certifications**: Change ALL "In Progress" badges (blue) to "Completed" (green). All 19 certifications are now completed.
2. **Projects**: Update Revenue-Sprint test count from 238 to 240.
3. **Certifications**: Add clickable Coursera course page links on certification names (`target="_blank"`). These are public course pages, not verification URLs. Search for the actual Coursera URLs for each cert name listed on the page.

### Verification

```bash
# Open locally to verify layout
open index.html
# Check all 5 files for footer consistency
grep -l "linkedin.com/in/cayman-roden" *.html | wc -l  # Should be 5
# Check certifications
grep -c "In Progress" certifications.html  # Should be 0
```

### Commit & Push

Single commit for all portfolio changes:
```bash
git add -A && git commit -m "feat: add LLMOps service, 2 case studies, footer social links, cert updates" && git push
```

---

## Phase 3: README Badge Standardization (4 repos, parallel)

**Priority**: P2
**Parallelizable**: Yes — 4 agents, one per repo

### 3A: Revenue-Sprint

**File**: `/Users/cave/Documents/GitHub/Revenue-Sprint/README.md`

Current badges: Python, Tests 238, License
- Add CI workflow badge: `![CI](https://github.com/ChunkyTortoise/Revenue-Sprint/actions/workflows/ci.yml/badge.svg)`
- Update test count: 238 → 240

### 3B: insight-engine

**File**: `/Users/cave/Documents/GitHub/insight-engine/README.md`

Current badges: CI, Python, License
- Add test count badge: `![Tests](https://img.shields.io/badge/tests-63-green)`

### 3C: docqa-engine

**File**: `/Users/cave/Documents/GitHub/docqa-engine/README.md`

Current badges: CI, Python, License
- Add test count badge: `![Tests](https://img.shields.io/badge/tests-94-green)`

### 3D: scrape-and-serve

**File**: `/Users/cave/Documents/GitHub/scrape-and-serve/README.md`

Current badges: CI only
- Add: `![Python](https://img.shields.io/badge/python-3.11+-blue)` `![License](https://img.shields.io/badge/license-MIT-green)` `![Tests](https://img.shields.io/badge/tests-62-green)`

### Verification (each repo)

```bash
# Check badges render (shields.io format)
head -5 README.md
git diff README.md
git add README.md && git commit -m "docs: standardize README badges" && git push
```

---

## Phase 4: Scrape-and-Serve README Upgrade

**Priority**: P2
**Parallelizable**: No (single file)
**Repo**: `/Users/cave/Documents/GitHub/scrape-and-serve`
**File**: `README.md`

Current quality: 6/10 (weakest README). Bring to parity with docqa-engine/insight-engine (8-9/10).

### Additions Required

1. **Quantified problem statement**: "Teams spend X hours/week manually checking competitor prices, reformatting spreadsheets for web, and optimizing content for SEO"
2. **Expanded module descriptions** with concrete details for each of the 4 modules:
   - Scraper: YAML-config, change detection, CSS/XPath selectors, diff tracking
   - Price Monitor: threshold alerts, CSV export, historical trend analysis
   - Excel Converter: .xlsx→SQLite+Streamlit CRUD app in one command
   - SEO Content: outline generation, readability scoring 0-100, keyword density
3. **Testing section**: `pytest tests/ -v` with test count (62)
4. **Tech Stack table** (match insight-engine format):
   | Component | Technology |
   |-----------|-----------|
   | Scraping | BeautifulSoup, httpx |
   | Data | Pandas, SQLite |
   | UI | Streamlit |
   | Config | YAML |
5. **Related Projects section** linking all 6 sibling repos + portfolio site
6. **Project Structure tree** showing `src/` layout

### Verification

```bash
# Word count should increase significantly
wc -l README.md  # Target: 150+ lines (currently ~60)
git diff --stat README.md
git add README.md && git commit -m "docs: comprehensive README upgrade" && git push
```

---

## Phase 5: Cross-Link READMEs to Portfolio Site (7 repos)

**Priority**: P2
**Parallelizable**: Yes — can be done in the same agent pass as Phase 3/4

Add to the "Related Projects" or bottom section of each repo's README:
```markdown
- [Portfolio](https://chunkytortoise.github.io) — Project showcase and services
```

**Repos**: EnterpriseHub, jorge, Revenue-Sprint, ai-orchestrator, insight-engine, docqa-engine, scrape-and-serve

For repos that don't have a "Related Projects" section, add one before the License section.

### Verification

```bash
for repo in EnterpriseHub jorge_real_estate_bots Revenue-Sprint ai-orchestrator insight-engine docqa-engine scrape-and-serve; do
  grep -l "chunkytortoise.github.io" /Users/cave/Documents/GitHub/$repo/README.md && echo "$repo: OK" || echo "$repo: MISSING"
done
```

---

## Phase 6: Streamlit Cloud Deployment Prep (3 repos)

**Priority**: P2
**Beads**: EnterpriseHub-9ws
**Parallelizable**: Yes — 3 agents, one per repo

### Target Repos

1. **insight-engine** — Data analytics dashboard
2. **docqa-engine** — Document Q&A interface
3. **scrape-and-serve** — Excel converter / price monitor UI

### Per-Repo Tasks

Each repo needs:

1. **`.streamlit/config.toml`** — Theme and server config:
   ```toml
   [theme]
   primaryColor = "#667eea"
   backgroundColor = "#ffffff"
   secondaryBackgroundColor = "#f0f2f6"
   textColor = "#262730"

   [server]
   headless = true
   port = 8501
   ```

2. **`requirements.txt` audit** — Ensure all Streamlit dependencies are listed, remove any OS-specific packages (no `pywin32`, etc.), pin versions to avoid breakage.

3. **Entry point verification** — Confirm the main Streamlit file is at the repo root or clearly documented:
   - insight-engine: `src/insight_engine/app.py` or `app.py`
   - docqa-engine: `src/docqa_engine/app.py` or `app.py`
   - scrape-and-serve: `src/scrape_and_serve/app.py` or `app.py`

4. **Demo mode default** — Ensure the app works without external API keys (mock/demo data). All 3 repos already have `make demo` support.

5. **README update** — Add "Deploy to Streamlit Cloud" section with badge:
   ```markdown
   ## Deploy

   [![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/chunkytortoise/{repo}/main/app.py)
   ```

### Verification

```bash
# For each repo:
streamlit run app.py --server.headless true &
sleep 5
curl -s http://localhost:8501 | head -5
kill %1
```

### Commit & Push (per repo)

```bash
git add .streamlit/ requirements.txt README.md
git commit -m "feat: prepare for Streamlit Cloud deployment"
git push
```

---

## Phase 7: AgentForge Provider Benchmark

**Priority**: P3
**Beads**: EnterpriseHub-ifu
**Parallelizable**: No (requires sequential API calls)
**Repo**: `/Users/cave/Documents/GitHub/ai-orchestrator`

### Task

Run the AgentForge benchmark comparing all available providers and capture results:

```bash
cd /Users/cave/Documents/GitHub/ai-orchestrator
agentforge benchmark
```

### Expected Output

Comparison table across providers: Claude, Gemini, OpenAI, Perplexity, Mock. Metrics: latency, token count, cost estimate.

### Documentation

1. Save benchmark output to `docs/BENCHMARK_RESULTS.md` with date
2. Update README.md with benchmark results table
3. Commit and push

### Note

This requires API keys for non-mock providers. If keys unavailable, run mock-only benchmark and document which providers need keys.

---

## Phase 8: Uncommitted Work Cleanup

**Priority**: P1 (do first)
**Parallelizable**: No

### Current Uncommitted Files

```
M  .beads/issues.jsonl
?? plans/UPWORK_PROPOSALS_FEB8.md
```

### Actions

1. Commit Upwork proposals:
   ```bash
   git add plans/UPWORK_PROPOSALS_FEB8.md
   git commit -m "docs: add Upwork proposal drafts for Feb 8"
   ```

2. Sync beads:
   ```bash
   bd sync
   ```

3. Push:
   ```bash
   git push
   ```

---

## Execution Order & Dependencies

```
Phase 8 (Uncommitted cleanup) ──┐
                                 ├──► Phase 1 (Test collection fix) ──► Phase 5 (Cross-links, EH)
Phase 2A-D (Portfolio site)  ────┘         │
Phase 3A-D (Badge standardization) ────────┤
Phase 4 (scrape-and-serve README) ─────────┤
Phase 5 (Cross-links, other 6 repos) ─────┤
Phase 6 (Streamlit Cloud) ────────────────►│
Phase 7 (AgentForge benchmark) ───────────►│
                                           ▼
                                    Final Verification
```

### Recommended Parallel Agent Allocation

| Agent | Phases | Est. Scope |
|-------|--------|-----------|
| Agent 1 | Phase 8 → Phase 1 (EH test fix) | 10 source files + conftest |
| Agent 2 | Phase 2A + 2B (Portfolio services + case studies) | 2 HTML files |
| Agent 3 | Phase 2C + 2D (Portfolio footer + certs) | 5 HTML files |
| Agent 4 | Phase 3A-D + Phase 5 (Badges + cross-links, 4 repos) | 4 READMEs |
| Agent 5 | Phase 4 + Phase 5 (scrape-and-serve README + cross-link) | 1 README |
| Agent 6 | Phase 6 (Streamlit Cloud prep, 3 repos) | 3 repos, config + README |
| Agent 7 | Phase 7 (AgentForge benchmark) | 1 repo, benchmark run |

### Session Close Protocol

After all phases complete:
```bash
# Per repo that was modified:
git status
git add <specific files>
git commit -m "type: description"
git push

# Beads sync
bd close <completed-issue-ids>
bd sync
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| EH test collection errors | 0 (currently 26) |
| EH tests collected | 3,955+ |
| Portfolio site pages with footer social links | 5/5 |
| Certifications marked "Completed" | 19/19 |
| Repos with standardized badges | 7/7 |
| Repos with portfolio cross-link | 7/7 |
| Streamlit Cloud-ready repos | 3/3 |
| CI status all repos | GREEN |
| All uncommitted work | Committed + pushed |
