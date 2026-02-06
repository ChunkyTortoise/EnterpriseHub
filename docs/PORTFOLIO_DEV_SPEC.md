# Portfolio Development Specification — Client Appeal Focus

**Owner**: ChunkyTortoise | **Created**: 2026-02-06 | **Status**: Active

Make every repo immediately impressive when someone lands on it.
Clients spend 30 seconds on a README, check if CI is green, and maybe click one file.
This spec optimizes for that reality.

> **Rule**: Existing repo-specific specs are referenced, never duplicated.
> See [Existing Specs Reference Index](#10-existing-specs-reference-index) for links.

---

## 1. Portfolio Snapshot

| Repo | Tests | CI | Visibility | Client First Impression |
|------|-------|----|------------|------------------------|
| `EnterpriseHub` | ~764 defined | Yes (11 workflows) | Public | **B-** — decent structure, 15 screenshots in `assets/screenshots/` but zero embedded in README |
| `jorge_real_estate_bots` | 270/279 (96.8%) | None | Private | **B-** — good mermaid diagram, no CI badge, no visuals, no problem statement |
| `Revenue-Sprint` | 238/238 (100%) | None | Private | **D+** — `<your-username>` placeholder in clone URL, confused identity (tool vs template vs product), stale "Codex" reference |
| `ai-orchestrator` | 27/27 (100%) | Yes (`ci.yml`) | Public | **B-** — great LLM comparison table but buried at line 149, broken `your-org` badge URLs |

**What clients actually evaluate** (in order):
1. README above the fold (problem statement + visual proof)
2. CI status badge (green = credible)
3. Demo they can run in <60 seconds
4. Code quality of 1-2 files they click into

---

## 2. Phase 0: Git Housekeeping (15 min)

> **Prerequisite**: Blocks all other phases. Complete in order.

### 2a. EnterpriseHub — Commit + Push

```bash
cd /Users/cave/Documents/GitHub/EnterpriseHub
git add docs/JORGE_BOTS_COMPREHENSIVE_DEV_SPEC.md docs/PORTFOLIO_DEV_SPEC.md
git commit -m "docs: add jorge bots dev spec and portfolio dev spec"
git push origin main
```

**Verify**:
```bash
git status                         # nothing to commit, working tree clean
git log --oneline origin/main..HEAD  # 0 commits
```

### 2b. jorge_real_estate_bots — Merge Feature Branch

The feature branch has 8 commits ahead of main: security fixes, bug fixes,
production hardening, datetime deprecation fixes, and SPEC.md/EVAL_PROMPT.md docs.

```bash
cd /Users/cave/Documents/GitHub/jorge_real_estate_bots
git checkout main
git merge feature/integrate-production-phase1
git push origin main
git branch -d feature/integrate-production-phase1
git push origin --delete feature/integrate-production-phase1
```

**Verify**:
```bash
git branch -a    # only "* main" locally, only "remotes/origin/main" remote
git log --oneline -3
```

### 2c. Revenue-Sprint — Commit Untracked Files + Merge to Main

Two untracked files on `dev`: `AGENTS.md` and `README.md`.

```bash
cd /Users/cave/Documents/GitHub/Revenue-Sprint
git add AGENTS.md README.md
git commit -m "docs: add AGENTS.md and finalize README"
git push origin dev

git checkout main
git merge dev
git push origin main
```

**Verify**:
```bash
git status                   # clean
git log --oneline main..dev  # 0 commits (fully merged)
```

### 2d. ai-orchestrator — No Action

Already clean on `main`.

```bash
cd /Users/cave/Documents/GitHub/ai-orchestrator
git status  # "nothing to commit, working tree clean"
```

---

## 3. Phase 1: Credibility Killers (30 min, blocks Phase 2)

Highest ROI. Five-minute changes that eliminate instant dealbreakers.

### 3a. ai-orchestrator — Fix Badge URLs

Replace `your-org` with `ChunkyTortoise` in 2 badge URLs (README lines 9-10):

```bash
cd /Users/cave/Documents/GitHub/ai-orchestrator
sed -i '' 's|your-org/ai-orchestrator|ChunkyTortoise/ai-orchestrator|g' README.md
```

### 3b. Revenue-Sprint — Fix Placeholder URL

Replace `<your-username>` with `ChunkyTortoise` in clone URL (README line 143):

```bash
cd /Users/cave/Documents/GitHub/Revenue-Sprint
sed -i '' 's|<your-username>|ChunkyTortoise|g' README.md
```

### 3c. Revenue-Sprint — Update Stale Test Count

Update test count from "212" to "238" in 3 locations (README lines 3, 19, 169):

```bash
sed -i '' 's/212 tests/238 tests/g; s/212 Tests/238 Tests/g; s/212\/212/238\/238/g' README.md
```

### 3d. Revenue-Sprint — Remove Stale "Codex" Reference

Line 238 references deprecated "Codex" model. Rewrite as "parallel AI agent development."

### 3e. jorge — Fix 9 Failing Tests

Well-documented root causes in `docs/SPEC.md` section 4.2:

| # | Test | Root Cause | Fix |
|---|------|-----------|-----|
| 1 | `test_global_filters_render_smoke` | `streamlit_stub.py` missing `st.title` | Add `title = MagicMock()` to stub |
| 2 | `test_mobile_dashboard_integration_render` | Mock DataFrame column mismatch | Fix mock data columns |
| 3 | `test_get_active_conversations_pagination` | Wrong patch target (`_fetch_real_conversation_data` instead of `_fetch_active_conversations`) | Fix patch target |
| 4 | `test_conversation_stage_distribution` | Same wrong patch target | Same fix |
| 5 | `test_conversation_temperature_distribution` | Same wrong patch target | Same fix |
| 6 | `test_get_budget_distribution_success` | Missing mock `LeadModel` query data | Add mock lead data with budget fields |
| 7 | `test_get_timeline_distribution_success` | Missing mock lead data | Add mock lead data with timeline fields |
| 8 | `test_get_commission_metrics_success` | Missing mock lead data | Add mock lead data with commission fields |
| 9 | `test_initial_greeting` | Test ordering pollution (passes alone) | Add explicit state reset in setup/teardown |

**Acceptance**: `pytest -v` shows 279/279 passed.

### 3f. Verify Phase 1

```bash
# Zero placeholder URLs across all READMEs
for repo in EnterpriseHub jorge_real_estate_bots Revenue-Sprint ai-orchestrator; do
  echo "=== $repo ==="
  grep -iE "your-org|your-username|<your-" /Users/cave/Documents/GitHub/$repo/README.md \
    || echo "Clean"
done

# jorge tests all pass
cd /Users/cave/Documents/GitHub/jorge_real_estate_bots && pytest -v
# Expected: 279/279 passed
```

---

## 4. Phase 2: README Rewrites (2-3 hours, blocks Phase 4)

Every README follows the same converting structure (research-backed order):

```
1. Title + one-line business problem statement
2. Badges (CI, tests, Python, license — 5 or fewer)
3. Demo GIF or screenshot (placeholder initially, replaced in Phase 4)
4. "What This Solves" (2-3 bullets in business value language)
5. Architecture diagram
6. Quick Start (including demo mode — 3-5 commands)
7. Tech stack
8. Related Projects (cross-links to other portfolio repos)
```

### 4a. EnterpriseHub

**Problem statement**: Real estate teams lose 40% of leads because response time exceeds the 5-minute SLA. This platform automates lead qualification, follow-up, and CRM sync.

**Embed existing screenshots** (already in `assets/screenshots/`):
- `platform-overview.png` — main dashboard view
- `market-pulse.png` — market analytics
- `jorge_dashboard_01.png` — bot command center
- `design-system.png` — UI component library

**Quick Start** must reference `make demo` (see Phase 3).

### 4b. jorge_real_estate_bots

**Problem statement**: 40% of real estate leads go cold because agents take >5 minutes to respond. Three specialized bots handle lead qualification, buyer matching, and seller CMAs in real time.

**Keep** the existing mermaid architecture diagram (it's good).

**Add**: CI badge placeholder (enabled after Phase 5 CI workflow).

**Quick Start** must reference `--demo` flag (see Phase 3).

### 4c. Revenue-Sprint

**Complete identity rewrite**. Current README can't decide if it's a tool, template, or product.

**Position as**: AI-powered freelance automation — scans job feeds, scores opportunities, generates proposals, and tests for prompt injection vulnerabilities.

**Problem statement**: Freelancers spend 15+ hours/week finding and applying to contracts. This pipeline automates the hunt-to-proposal workflow.

**Remove**: "7-day sprint" framing (commit history shows 2-day build). Fix clone URL.

### 4d. ai-orchestrator

**Problem statement**: Switching LLM providers means rewriting API calls. AgentForge provides a unified async interface across Claude, Gemini, OpenAI, and Perplexity with one code change.

**Move** the LangChain/LiteLLM comparison table higher (currently buried at line 149 — it's the strongest differentiator).

**Quick Start** must reference `--provider mock` (see Phase 3) and the `benchmark` command (see Phase 5).

### 4e. Honesty Audit

```bash
# Zero inflated claims across all READMEs
for repo in EnterpriseHub jorge_real_estate_bots Revenue-Sprint ai-orchestrator; do
  echo "=== $repo ==="
  grep -ciE "enterprise-grade|production-ready|battle-tested|industry-leading" \
    /Users/cave/Documents/GitHub/$repo/README.md
done
# Expected: all 0
```

---

## 5. Phase 3: Demo Modes (6-8 hours, blocks Phase 4)

Zero-friction evaluation — each repo works with zero API keys.

### 5a. EnterpriseHub — `DEMO_MODE=true`

**Infrastructure already exists**:
- `ghl_real_estate_ai/streamlit_demo/demo_scenarios/` — hot_lead.json, warm_lead.json, cold_lead.json
- `ghl_real_estate_ai/streamlit_demo/mock_services/` — mock_claude.py, mock_rag.py, conversation_state.py

**Implementation**:
- Add `DEMO_MODE` env var check in `ghl_real_estate_ai/streamlit_demo/app.py`
- When active: skip DB/Redis/API connections, load from JSON fixtures and mock services
- Add `make demo` target to existing root `Makefile`:
  ```makefile
  demo:
  	DEMO_MODE=true streamlit run ghl_real_estate_ai/streamlit_demo/app.py
  ```

**Verify**: `make demo` launches dashboard with populated charts, zero external deps.

### 5b. jorge_real_estate_bots — `--demo` Flag

- Add `--demo` flag to `jorge_launcher.py`
- Skip health checks, use SQLite in-memory instead of PostgreSQL
- Create `scripts/seed_demo_data.py` — seeds 50 realistic leads with Rancho Cucamonga addresses
- Dashboard shows populated charts immediately on launch

**Verify**: `python jorge_launcher.py --demo` starts 3 bots + dashboard, zero config.

### 5c. Revenue-Sprint — `--demo` Flag

- Add `--demo` flag to `scripts/run_pipeline.py`
- Chain: load `scanner/tests/sample_feed.xml` → score jobs → generate 3 proposals via keyword fallback (already works without API key per README line 91-92) → save to `output/demo/`
- Add `__main__` to `product_1_launch_kit/injection_tester.py` for zero-setup risk matrix demo

**Verify**: `python scripts/run_pipeline.py --demo` produces colored terminal output, zero API keys.

### 5d. ai-orchestrator — `mock` Provider

- Add `mock` provider to `agentforge/providers/` returning canned responses with realistic timing (50-200ms jitter)
- `agentforge "Hello" --provider mock` works with zero keys
- Document `--provider mock` as the first Quick Start step

**Verify**: `agentforge "Explain quantum computing" --provider mock` returns a coherent canned response.

### 5e. Verify All Demo Modes

```bash
# Fresh-clone simulation per repo:
# 1. cd into repo
# 2. pip install -e . (or pip install -r requirements.txt)
# 3. Run demo command
# 4. Confirm meaningful visual output with zero config

# EnterpriseHub
cd /Users/cave/Documents/GitHub/EnterpriseHub && make demo
# → Streamlit dashboard with charts

# jorge
cd /Users/cave/Documents/GitHub/jorge_real_estate_bots && python jorge_launcher.py --demo
# → 3 bots running + dashboard with 50 seeded leads

# Revenue-Sprint
cd /Users/cave/Documents/GitHub/Revenue-Sprint && python scripts/run_pipeline.py --demo
# → Colored pipeline output + 3 proposals in output/demo/

# ai-orchestrator
cd /Users/cave/Documents/GitHub/ai-orchestrator && agentforge "Hello" --provider mock
# → Canned response with timing metadata
```

---

## 6. Phase 4: Demo Assets (2-3 hours, blocks Phase 6)

Record GIFs and screenshots, embed in READMEs from Phase 2.

### 6a. Recording Tool

Use `vhs` (charmbracelet/vhs) for terminal GIFs, screen recording for Streamlit.

```bash
brew install vhs  # terminal GIF recorder
```

### 6b. Per-Repo Assets

| Repo | Asset | Content | Save As |
|------|-------|---------|---------|
| EnterpriseHub | GIF | Streamlit dashboard cycling 2-3 hub views | `assets/demo.gif` |
| jorge | GIF | Launcher starting 3 bots + Command Center with emoji output | `assets/demo.gif` |
| Revenue-Sprint | GIF | `run_pipeline.py --demo` colored output + injection tester risk matrix | `assets/demo.gif` |
| ai-orchestrator | GIF | CLI sending same prompt to multiple providers, response comparison | `assets/demo.gif` |

### 6c. Embed in READMEs

Each README gets the demo GIF right below the badges:

```markdown
![Demo](assets/demo.gif)
```

EnterpriseHub additionally embeds 3-4 existing screenshots in an expandable section:

```markdown
<details>
<summary>Screenshots</summary>

![Platform Overview](assets/screenshots/platform-overview.png)
![Market Pulse](assets/screenshots/market-pulse.png)
![Bot Dashboard](assets/screenshots/jorge_dashboard_01.png)

</details>
```

---

## 7. Phase 5: Feature Enhancements (8-12 hours, parallel with Phases 3-4)

Deeper functionality that impresses evaluators who dig into the code.

### 7a. CI Workflows (jorge + Revenue-Sprint)

Both repos currently have zero CI.

**jorge** — `.github/workflows/ci.yml`:
- Triggers: push/PR to main
- Job: `pytest -v`, Python 3.11
- Enables real CI badge in README

**Revenue-Sprint** — `.github/workflows/ci.yml`:
- Triggers: push/PR to main
- Jobs: `ruff check . && ruff format --check .`, `pytest tests/ -v`
- Matrix: Python 3.10, 3.11, 3.12
- Enables real CI badge in README

### 7b. EnterpriseHub — FastAPI `/demo` Routes

Add demo API routes (no auth required, hardcoded Rancho Cucamonga sample data):

- `GET /demo/leads` — 10 sample leads with realistic data
- `GET /demo/pipeline` — sample pipeline snapshot showing lead flow
- Swagger UI at `/docs` is a strong demo by itself — embed screenshot in README

### 7c. jorge — Health Aggregation Endpoint

- `GET /health/aggregate` on lead bot checks all 3 bots + Redis + Postgres
- Returns unified status JSON: `{"lead_bot": "ok", "buyer_bot": "ok", ...}`
- Add `make health` Makefile target

### 7d. Revenue-Sprint — Standalone Injection Tester

- `python -m product_1_launch_kit.injection_tester` runs built-in test cases
- Prints colored risk matrix with pass/fail indicators
- Zero deps beyond stdlib, zero API keys
- Most impressive instant demo in the portfolio

### 7e. ai-orchestrator — `agentforge benchmark` Command

New subcommand in `agentforge/cli.py`:

- Sends same prompt to all configured providers (falls back to `mock` for unconfigured ones)
- Prints comparison table: response time, token count, cost estimate
- Shows the value proposition in action:
  ```
  Provider     | Time   | Tokens | Est. Cost
  -------------|--------|--------|----------
  claude       | 1.2s   | 847    | $0.0042
  gemini       | 0.8s   | 923    | $0.0018
  mock         | 0.1s   | 156    | $0.0000
  ```

### 7f. Makefiles

| Repo | Targets | Notes |
|------|---------|-------|
| EnterpriseHub | Add `make demo` | Existing Makefile at root |
| jorge | Create `Makefile` | `make demo`, `make test`, `make health` |
| Revenue-Sprint | Create `Makefile` | `make demo`, `make test`, `make verify` |

### 7g. Docker Improvements

- **jorge**: Convert single-stage Dockerfile to multi-stage with non-root user
- **Revenue-Sprint**: Add `.dockerignore` (exclude `.git`, `__pycache__`, `.env`, `venv/`, `output/`)

---

## 8. Phase 6: Profile README + Cross-Repo Polish (1-2 hours, final)

### 8a. GitHub Profile README

Create/update `ChunkyTortoise/ChunkyTortoise` repo with `README.md`:

- Professional headline (value proposition, not "Hi I'm...")
- Tech stack icons: Python, FastAPI, Streamlit, PostgreSQL, Redis, Claude AI
- 4 featured projects with one-line business descriptions
- No stats widgets, no animated headers, no cliches

### 8b. Pin Repos

Pin all 4 repos on GitHub profile, ordered by impressiveness:
1. EnterpriseHub
2. ai-orchestrator
3. jorge_real_estate_bots
4. Revenue-Sprint

### 8c. Topics/Tags per Repo

| Repo | Topics |
|------|--------|
| EnterpriseHub | `real-estate`, `ai`, `fastapi`, `streamlit`, `llm`, `chatbot`, `crm` |
| jorge | `real-estate`, `ai-agents`, `fastapi`, `lead-qualification`, `chatbot` |
| Revenue-Sprint | `freelancing`, `ai-agents`, `automation`, `prompt-injection` |
| ai-orchestrator | `llm`, `ai`, `async`, `multi-provider`, `claude`, `gemini`, `openai` |

### 8d. Cross-Link All Repos

Add a "Related Projects" section to each repo's README:

```markdown
## Related Projects

- [EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub) — Real estate AI platform with BI dashboards and CRM integration
- [jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots) — Three-bot lead qualification system (Lead, Buyer, Seller)
- [Revenue-Sprint](https://github.com/ChunkyTortoise/Revenue-Sprint) — AI-powered freelance pipeline automation
- [ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator) — AgentForge: unified async LLM interface
```

### 8e. Visibility — Make Private Repos Public

**Security review first**:
```bash
for repo in jorge_real_estate_bots Revenue-Sprint; do
  echo "=== $repo ==="
  cd /Users/cave/Documents/GitHub/$repo
  git log --all -p | grep -iE "sk-|api[_-]?key\s*=\s*['\"][a-zA-Z0-9]" | head -20
done
# Must return empty for both repos before proceeding
```

**If clean**:
```bash
gh repo edit ChunkyTortoise/jorge_real_estate_bots --visibility public
gh repo edit ChunkyTortoise/Revenue-Sprint --visibility public
```

### 8f. Final Honesty Audit

```bash
# Zero inflated claims
for repo in EnterpriseHub jorge_real_estate_bots Revenue-Sprint ai-orchestrator; do
  echo "=== $repo ==="
  grep -ciE "enterprise-grade|production-ready|battle-tested|industry-leading" \
    /Users/cave/Documents/GitHub/$repo/README.md
done
# Expected: all 0

# Zero placeholder URLs
for repo in EnterpriseHub jorge_real_estate_bots Revenue-Sprint ai-orchestrator; do
  grep -iE "your-org|your-username|<your-" /Users/cave/Documents/GitHub/$repo/README.md \
    && echo "FAIL: $repo" || echo "PASS: $repo"
done

# All test counts match reality
cd /Users/cave/Documents/GitHub/jorge_real_estate_bots && pytest --co -q | tail -1
cd /Users/cave/Documents/GitHub/Revenue-Sprint && pytest --co -q | tail -1
cd /Users/cave/Documents/GitHub/ai-orchestrator && pytest --co -q | tail -1
```

---

## 9. Verification Matrix

### Per-Repo Checklists

#### EnterpriseHub

| Check | Command | Expected |
|-------|---------|----------|
| Clean working tree | `git status` | Nothing to commit |
| Pushed to origin | `git log origin/main..HEAD --oneline` | 0 commits |
| Demo mode works | `make demo` | Streamlit launches with charts |
| Demo GIF embedded | `grep "demo.gif" README.md` | Match found |
| Screenshots embedded | `grep "screenshots/" README.md` | 3+ matches |
| Problem statement | `head -5 README.md` | Business problem visible |
| Cross-links | `grep "Related Projects" README.md` | Section exists |
| CI green | `gh run list -w ci.yml -L 1` | `completed success` |

#### jorge_real_estate_bots

| Check | Command | Expected |
|-------|---------|----------|
| All tests pass | `pytest -v` | 279/279 passed |
| No feature branches | `git branch -a` | Only `main` |
| CI exists | `ls .github/workflows/ci.yml` | File exists |
| CI green | `gh run list -w ci.yml -L 1` | `completed success` |
| Demo mode works | `python jorge_launcher.py --demo` | 3 bots + dashboard |
| Demo GIF embedded | `grep "demo.gif" README.md` | Match found |
| Problem statement | `head -5 README.md` | Business problem visible |
| Cross-links | `grep "Related Projects" README.md` | Section exists |
| Public | `gh repo view --json visibility -q .visibility` | `PUBLIC` |

#### Revenue-Sprint

| Check | Command | Expected |
|-------|---------|----------|
| All tests pass | `pytest tests/ -v` | 238/238 passed |
| CI exists | `ls .github/workflows/ci.yml` | File exists |
| CI green | `gh run list -w ci.yml -L 1` | `completed success` |
| No placeholder URLs | `grep -iE "your-org\|your-username\|<your-" README.md` | No matches |
| Test count accurate | `grep "238" README.md` | Matches actual count |
| Demo mode works | `python scripts/run_pipeline.py --demo` | Pipeline output |
| Injection tester | `python -m product_1_launch_kit.injection_tester` | Risk matrix |
| Demo GIF embedded | `grep "demo.gif" README.md` | Match found |
| Problem statement | `head -5 README.md` | Business problem visible |
| Cross-links | `grep "Related Projects" README.md` | Section exists |
| Public | `gh repo view --json visibility -q .visibility` | `PUBLIC` |

#### ai-orchestrator

| Check | Command | Expected |
|-------|---------|----------|
| All tests pass | `pytest -v` | 27/27 passed |
| No placeholder URLs | `grep -iE "your-org" README.md` | No matches |
| Badges resolve | Manual check | CI + Python badges load |
| Mock provider works | `agentforge "Hello" --provider mock` | Canned response |
| Benchmark command | `agentforge benchmark` | Comparison table |
| Demo GIF embedded | `grep "demo.gif" README.md` | Match found |
| Problem statement | `head -5 README.md` | Business problem visible |
| Cross-links | `grep "Related Projects" README.md` | Section exists |

### Portfolio-Wide Success Metrics

| Signal | Current | After |
|--------|---------|-------|
| Problem statement above fold | 0/4 | 4/4 |
| Working CI badges | 0/4 (ai-orch has broken URL) | 4/4 |
| Demo GIF in README | 0/4 | 4/4 |
| Zero-friction demo mode | 0/4 | 4/4 |
| Placeholder URLs | 2 repos (ai-orch + Revenue-Sprint) | 0 |
| All tests passing | 3/4 (jorge has 9 failures) | 4/4 |
| Public repos | 2/4 (ai-orch + EnterpriseHub) | 4/4 |
| Cross-linked READMEs | 0/4 | 4/4 |
| GitHub profile README | No | Yes |
| Embedded screenshots | 0/4 | 1/4 (EnterpriseHub) |

---

## 10. Existing Specs Reference Index

Do not duplicate content from these documents. Reference them by path.

| Document | Repo | Path | Content |
|----------|------|------|---------|
| Jorge Technical Spec | jorge_real_estate_bots | `docs/SPEC.md` | Architecture, module map, DB schema, 27 known issues, test status |
| Jorge Agent Eval Prompts | jorge_real_estate_bots | `docs/EVAL_PROMPT.md` | Task-specific prompts for test fixes, coverage, hardening |
| Revenue-Sprint Finalization | Revenue-Sprint | `CODEX_FINALIZE.md` | 6 parallel agent tasks (F1-F6) for project completion |
| Revenue-Sprint Launch Guide | Revenue-Sprint | `INTEGRATION_AND_LAUNCH.md` | Launch sequence and integration instructions |
| EnterpriseHub API Spec | EnterpriseHub | `docs/API_SPEC.md` | API endpoint documentation |
| EnterpriseHub Architecture | EnterpriseHub | `docs/ARCHITECTURE.md` | System architecture and design decisions |
| Jorge Dev Spec (detailed) | EnterpriseHub | `docs/JORGE_BOTS_COMPREHENSIVE_DEV_SPEC.md` | Comprehensive jorge bots development specification |

---

## Execution Order Summary

```
Phase 0: Git Housekeeping (15 min)         ← BLOCKS EVERYTHING
  ├── 2a. EnterpriseHub commit + push
  ├── 2b. jorge merge feature → main
  ├── 2c. Revenue-Sprint commit + merge
  └── 2d. ai-orchestrator (no-op)

Phase 1: Credibility Killers (30 min)      ← BLOCKS PHASE 2
  ├── 3a. ai-orchestrator: fix badge URLs
  ├── 3b-d. Revenue-Sprint: placeholder, test count, Codex ref
  └── 3e. jorge: fix 9 failing tests

Phase 2: README Rewrites (2-3 hours)       ← BLOCKS PHASE 4
  ├── 4a. EnterpriseHub: embed screenshots, problem statement
  ├── 4b. jorge: add CI badge placeholder, problem statement
  ├── 4c. Revenue-Sprint: complete identity rewrite
  └── 4d. ai-orchestrator: move comparison table up

Phase 3: Demo Modes (6-8 hours)            ← BLOCKS PHASE 4
  ├── 5a. EnterpriseHub: DEMO_MODE env var + make demo
  ├── 5b. jorge: --demo flag + seed data
  ├── 5c. Revenue-Sprint: --demo flag + injection tester
  └── 5d. ai-orchestrator: mock provider

Phase 4: Demo Assets (2-3 hours)           ← BLOCKS PHASE 6
  ├── 6a-b. Record GIFs per repo
  └── 6c. Embed in READMEs

Phase 5: Feature Enhancements (8-12 hours) ← PARALLEL WITH 3-4
  ├── 7a. CI workflows (jorge + Revenue-Sprint)
  ├── 7b. EnterpriseHub /demo routes
  ├── 7c. jorge health endpoint
  ├── 7d. Revenue-Sprint injection tester CLI
  ├── 7e. ai-orchestrator benchmark command
  ├── 7f. Makefiles
  └── 7g. Docker improvements

Phase 6: Profile + Polish (1-2 hours)      ← FINAL
  ├── 8a. GitHub profile README
  ├── 8b. Pin repos
  ├── 8c. Topics/tags
  ├── 8d. Cross-link READMEs
  ├── 8e. Make private repos public
  └── 8f. Final honesty audit
```

**Total estimated effort**: 20-30 hours across all phases.

**Dependency chain**: 0 → 1 → 2 → (3 ∥ 5) → 4 → 6
