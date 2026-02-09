# Next Session Execution Spec — Agent Swarm
**Date**: February 9, 2026
**Goal**: Close all automatable beads, get 11/11 CI green, deploy AgentForge, fix content, push everything

---

## Current State

### CI Status (as of session start)
| Repo | CI | Issue |
|------|----|-------|
| ai-orchestrator | GREEN | — |
| docqa-engine | GREEN | — |
| prompt-engineering-lab | GREEN | — |
| jorge_real_estate_bots | GREEN | — |
| insight-engine | GREEN | — |
| scrape-and-serve | GREEN | — |
| mcp-toolkit | GREEN | — |
| Revenue-Sprint | GREEN | — |
| chunkytortoise.github.io | GREEN | — |
| **llm-integration-starter** | **FAILING** | `ruff format` — 15 files need formatting |
| **EnterpriseHub** | **IN PROGRESS** | Latest run still running; prior run failed |

### Open Beads (11 total)
| Bead | Priority | Type | Description | Blocked By |
|------|----------|------|-------------|------------|
| `m88a` | P0 | bug | Fix llm-integration-starter CI (ruff format 15 files) | — |
| `qaiq` | P0 | task | Fiverr: Create account + list 3 gigs | — |
| `asn8` | P0 | task | Gumroad: Create account + list 4 products | — |
| `247w` | P1 | bug | Content QA: fix fake data in social posts + empty article | — |
| `632f` | P1 | task | Portfolio polish Phase 2: themes, exec(), data warnings | — |
| `5xf2` | P1 | task | Commit all untracked content files | `247w` |
| `9fkl` | P1 | task | Deploy AgentForge to Streamlit Cloud | `m88a` |
| `4j2` | P2 | task | Upwork: Purchase 80 Connects + submit proposals | — (human) |
| `9je` | P2 | task | LinkedIn: Send 3-5 recommendation requests | — (human) |
| `vp9` | P3 | task | Upwork: Complete remaining profile improvements | — (human) |
| `pbz` | P3 | task | LinkedIn: Weekly content cadence | — (human) |

### Untracked Files (need commit after QA)
```
?? content/devto/article1-rag-without-vector-db.md   ← EMPTY, delete
?? content/fiverr/gig1-rag-qa-system.md              ← ready
?? content/fiverr/gig2-ai-chatbot.md                 ← ready
?? content/fiverr/gig3-data-dashboard.md              ← ready
?? content/gumroad/product1-docqa-engine.md           ← ready
?? content/gumroad/product2-agentforge.md             ← ready
?? content/gumroad/product3-scrape-and-serve.md       ← ready
?? content/gumroad/product4-insight-engine.md         ← ready
?? content/social/reddit-post1-11-repos.md            ← NEEDS QA (fake repos)
?? content/social/reddit-post2-rag-pipeline.md        ← ready
 M content/social/hn-show-agentforge.md               ← NEEDS QA (wrong repo URL)
?? plans/PORTFOLIO_POLISH_PROMPT.md                   ← ready
```

---

## Agent Team Plan — 3 Waves

### Wave 1: Critical Fixes (4 parallel agents)

#### Agent 1: CI Fixer (`m88a`)
- **Type**: `general-purpose` | **Model**: `sonnet`
- **Repo**: `/Users/cave/Documents/GitHub/llm-integration-starter`
- **Task**:
  ```bash
  cd /Users/cave/Documents/GitHub/llm-integration-starter
  git pull
  ruff format .
  git add -A
  git commit -m "fix: ruff format 15 files for CI"
  git push
  ```
- **Then**: Also check EnterpriseHub CI status. If EnterpriseHub CI is failing, diagnose and fix.
- **Close**: `bd close m88a`

#### Agent 2: Content QA (`247w`)
- **Type**: `general-purpose` | **Model**: `sonnet`
- **Repo**: `/Users/cave/Documents/GitHub/EnterpriseHub`
- **Task**: Fix 3 content issues:

  **Issue 1: `content/social/reddit-post1-11-repos.md`** — Contains FAKE repos
  - Current post lists fake repos: `claude-orchestrator`, `lead-intelligence`, `jorge-bot`, `churn-predictor`, `sentiment-analyzer`, `portfolio-template`
  - Rewrite with REAL repos and REAL test counts:
    | Repo | Tests | Live Demo |
    |------|-------|-----------|
    | EnterpriseHub | ~4,937 | ct-enterprise-ai.streamlit.app |
    | docqa-engine | 322 | ct-document-engine.streamlit.app |
    | jorge_real_estate_bots | 279 | — |
    | Revenue-Sprint | 240 | — |
    | scrape-and-serve | 236 | ct-scrape-and-serve.streamlit.app |
    | ai-orchestrator (AgentForge) | 214 | ct-agentforge.streamlit.app |
    | insight-engine | 313 | ct-insight-engine.streamlit.app |
    | mcp-toolkit | 158 | ct-mcp-toolkit.streamlit.app |
    | llm-integration-starter | 149 | — |
    | prompt-engineering-lab | 127 | — |
    | chunkytortoise.github.io | — | chunkytortoise.github.io |
  - Total: **7,016+ tests** across **11 repos**, **6 live Streamlit demos**
  - Keep the same tone/structure, just replace the table and totals

  **Issue 2: `content/social/hn-show-agentforge.md`** — Wrong repo URL
  - Line 5: `**URL:** https://github.com/ChunkyTortoise/agentforge`
  - Should be: `**URL:** https://github.com/ChunkyTortoise/ai-orchestrator`
  - Also verify any other links in the file reference the correct repo name

  **Issue 3: `content/devto/article1-rag-without-vector-db.md`** — Empty file
  - This is a duplicate of `article1-production-rag.md` (which already has 12KB of content)
  - Delete the empty file: `rm content/devto/article1-rag-without-vector-db.md`

- **Close**: `bd close 247w`

#### Agent 3: Theme & UI Polish (`632f`)
- **Type**: `general-purpose` | **Model**: `sonnet`
- **Repos**: EnterpriseHub, insight-engine, scrape-and-serve, mcp-toolkit
- **Tasks** (from PORTFOLIO_POLISH_SPEC.md Phase 2):

  **Task 2A: Fix Streamlit theme colors**
  - Read `.streamlit/config.toml` in EnterpriseHub and insight-engine
  - Remove invalid keys: `widgetBackgroundColor`, `widgetBorderColor`, `skeletonBackgroundColor`
  - These are NOT valid Streamlit theme config keys — they cause 24+ console warnings
  - Keep only valid keys: `primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`, `font`
  - Commit + push both repos

  **Task 2B: Fix EnterpriseHub root app.py**
  - File: `/Users/cave/Documents/GitHub/EnterpriseHub/app.py`
  - Replace `exec(code, global_vars)` pattern with proper module import
  - Update hardcoded favicon URL to use relative path
  - Commit + push

  **Task 2C: Update EnterpriseHub test count footer**
  - File: `streamlit_demo/app.py`
  - Find footer text showing old test count (4,467 or similar)
  - Update to: **4,937 tests** (current actual count for EnterpriseHub)
  - Commit + push

  **Task 2D: Fix scrape-and-serve "Infinite extent" warnings**
  - Repo: `/Users/cave/Documents/GitHub/scrape-and-serve`
  - Investigate `app.py` for Plotly/Streamlit charts that produce "Infinite extent" on date/price fields
  - Add data validation: filter NaN/None/empty before charting
  - Commit + push

- **Close**: `bd close 632f`

#### Agent 4: Fiverr + Gumroad Content Prep (assist `qaiq` + `asn8`)
- **Type**: `general-purpose` | **Model**: `haiku`
- **Repo**: `/Users/cave/Documents/GitHub/EnterpriseHub`
- **Task**: Review and update all Gumroad + Fiverr content for accuracy:
  - Update `support@yourdomain.com` → `caymanroden@gmail.com` in all product files
  - Update demo URLs: ensure all Streamlit demo links are correct
  - Verify GitHub repo links use `ChunkyTortoise/{repo}` format
  - Fix `gig1-rag-qa-system.md` line 114: demo URL from placeholder to `ct-document-engine.streamlit.app`
  - Fix `gig1-rag-qa-system.md` line 121: GitHub URL from `enterprisehub/docqa-engine` to `ChunkyTortoise/docqa-engine`
  - Do NOT commit (Agent 5 handles commit after all QA done)

---

### Wave 2: Deploy + Commit (2 parallel agents, after Wave 1)

#### Agent 5: Content Commit (`5xf2`)
- **Type**: `general-purpose` | **Model**: `haiku`
- **Repo**: `/Users/cave/Documents/GitHub/EnterpriseHub`
- **Depends on**: Wave 1 Agents 2 + 4 (content QA + Fiverr/Gumroad review)
- **Task**:
  ```bash
  cd /Users/cave/Documents/GitHub/EnterpriseHub
  git pull
  # Stage all content files
  git add content/fiverr/ content/gumroad/ content/social/reddit-post1-11-repos.md content/social/reddit-post2-rag-pipeline.md content/social/hn-show-agentforge.md
  git commit -m "content: add Fiverr gigs, Gumroad products, and fixed social posts"
  git push
  ```
- **Close**: `bd close 5xf2`

#### Agent 6: Deploy AgentForge (`9fkl`)
- **Type**: `general-purpose` | **Model**: `sonnet`
- **Depends on**: Agent 1 (CI must be green)
- **Repo**: `/Users/cave/Documents/GitHub/ai-orchestrator`
- **Task**:
  - Verify `app.py` entry point exists and runs locally: `cd /Users/cave/Documents/GitHub/ai-orchestrator && python -c "import streamlit; print('ok')"`
  - Verify `.streamlit/config.toml` exists with valid theme
  - Verify `requirements.txt` includes `streamlit>=1.32.0`
  - NOTE: Actual Streamlit Cloud deployment requires browser automation (log into share.streamlit.io)
  - If browser tools available: navigate to share.streamlit.io, connect GitHub, select ai-orchestrator, set main file to app.py, deploy
  - If no browser: prepare deployment instructions and mark bead as "ready for manual deploy"
- **Close**: `bd close 9fkl` (or update with status if manual step needed)

---

### Wave 3: Browser Automation (after Waves 1-2)

#### Agent 7: Gumroad Account Setup (`asn8`)
- **Type**: `general-purpose` | **Model**: `sonnet`
- **Tool**: `claude-in-chrome` or `playwright` browser automation
- **Task**:
  1. Navigate to gumroad.com
  2. Create seller account (or log in if exists) — email: caymanroden@gmail.com
  3. Create 4 digital products from `content/gumroad/`:
     | Product | Price | Content File |
     |---------|-------|-------------|
     | AI Document Q&A Engine | $49 | `content/gumroad/product1-docqa-engine.md` |
     | AgentForge Multi-LLM Orchestrator | $39 | `content/gumroad/product2-agentforge.md` |
     | Web Scraper & Price Monitor | $29 | `content/gumroad/product3-scrape-and-serve.md` |
     | Data Intelligence Dashboard | $39 | `content/gumroad/product4-insight-engine.md` |
  4. For each: set title, description, price, tags, digital download type
  5. Enable "Pay what you want" with minimum = listed price
- **Close**: `bd close asn8`

#### Agent 8: Fiverr Account Setup (`qaiq`)
- **Type**: `general-purpose` | **Model**: `sonnet`
- **Tool**: `claude-in-chrome` or `playwright` browser automation
- **Task**:
  1. Navigate to fiverr.com
  2. Create seller account (or log in if exists) — email: caymanroden@gmail.com
  3. Create 3 gigs from `content/fiverr/`:
     | Gig | Packages | Content File |
     |-----|----------|-------------|
     | RAG Document Q&A System | $100 / $250 / $500 | `content/fiverr/gig1-rag-qa-system.md` |
     | Multi-Agent AI Chatbot | $200 / $350 / $500 | `content/fiverr/gig2-ai-chatbot.md` |
     | CSV/Excel Dashboard | $50 / $100 / $200 | `content/fiverr/gig3-data-dashboard.md` |
  4. For each: set title, category, 3 packages, description, FAQ, tags, delivery times
- **Close**: `bd close qaiq`

---

## Execution Summary

```
Wave 1 (parallel, ~10 min):
  Agent 1: CI fix (llm-integration-starter ruff format)     → m88a
  Agent 2: Content QA (fix fake repos, wrong URLs, empty)   → 247w
  Agent 3: Theme + UI polish (4 repos)                      → 632f
  Agent 4: Fiverr/Gumroad content review (update emails/URLs)

Wave 2 (parallel, after Wave 1, ~5 min):
  Agent 5: Commit all content files                          → 5xf2
  Agent 6: Deploy AgentForge to Streamlit Cloud              → 9fkl

Wave 3 (browser automation, after Wave 2, ~15 min):
  Agent 7: Gumroad account + 4 products                     → asn8
  Agent 8: Fiverr account + 3 gigs                           → qaiq
```

### Expected Outcome
- **11/11 CI green**
- **7 Streamlit apps live** (including AgentForge)
- **0 theme/console warnings** in deployed apps
- **All content committed and pushed**
- **Gumroad store live with 4 products**
- **Fiverr profile live with 3 gigs**
- **7 beads closed** (m88a, 247w, 632f, 5xf2, 9fkl, asn8, qaiq)

### Remaining After This Session (4 — human only)
| Bead | Description |
|------|-------------|
| `4j2` | Upwork: Purchase Connects + submit proposals |
| `9je` | LinkedIn: Send recommendation requests |
| `vp9` | Upwork: Profile improvements |
| `pbz` | LinkedIn: Content cadence |

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `content/gumroad/product{1-4}*.md` | Gumroad product listings (4 products) |
| `content/fiverr/gig{1-3}*.md` | Fiverr gig descriptions (3 gigs) |
| `content/social/reddit-post1-11-repos.md` | Reddit post — NEEDS QA FIX |
| `content/social/reddit-post2-rag-pipeline.md` | Reddit post — ready |
| `content/social/hn-show-agentforge.md` | HN post — NEEDS URL FIX |
| `content/devto/article1-rag-without-vector-db.md` | EMPTY — DELETE |
| `plans/PORTFOLIO_POLISH_SPEC.md` | Full audit of all app issues |
| `plans/PLATFORM_PROFILES.md` | 4 platform profiles (Freelancer, Toptal, Arc.dev, Contra) |
| `plans/OUTREACH_TARGETS.md` | 30 cold email targets |

---

## Session Startup Prompt

```
Run `bd prime` to load beads context, then execute the agent swarm spec at
plans/NEXT_SESSION_SPEC.md. Deploy 3 waves of agents:

Wave 1 (4 parallel): CI fix (m88a), Content QA (247w), Theme/UI polish (632f),
Fiverr/Gumroad content review.

Wave 2 (2 parallel, after Wave 1): Content commit (5xf2), AgentForge deploy (9fkl).

Wave 3 (2 parallel, after Wave 2): Gumroad browser setup (asn8), Fiverr browser setup (qaiq).

Read the full spec for detailed agent prompts. Close beads as each completes.
After all waves: bd sync && git push.
```
