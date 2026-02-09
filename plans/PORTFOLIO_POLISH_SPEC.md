# Portfolio Polish Spec — Client-Ready Quality

**Date**: February 9, 2026
**Scope**: 11 repos, 6 deployed Streamlit apps, 1 GitHub Pages site
**Goal**: Fix all broken elements, resolve CI failures, polish UI/UX for client presentations

---

## Audit Summary

### Deployed App Status

| App | URL | Status | Issues Found |
|-----|-----|--------|-------------|
| EnterpriseHub | ct-enterprise-ai.streamlit.app | LIVE | 24+ invalid color warnings, outdated test count (4,467→4,937), exec() in app.py |
| DocQA Engine | ct-document-engine.streamlit.app | LIVE | 9 warnings, ruff format CI failure (5 files) |
| Insight Engine | ct-insight-engine.streamlit.app | LIVE | 9+ invalid color warnings (theme config) |
| Scrape-and-Serve | ct-scrape-and-serve.streamlit.app | LIVE | 8 "Infinite extent" warnings for date/price fields |
| MCP Toolkit | ct-mcp-toolkit.streamlit.app | LIVE | 60 warnings (needs investigation) |
| AgentForge | ct-agentforge.streamlit.app | **404 NOT FOUND** | App not deployed — needs Streamlit Cloud setup |

### CI Status

| Repo | Status | Root Cause |
|------|--------|-----------|
| EnterpriseHub | **PENDING** | Prior run failed (type checking + code quality); new run queued |
| jorge_real_estate_bots | **FAILURE** | 3 test errors — `enhanced_hero_metrics.get_enhanced_lead_intelligence` mock target missing |
| ai-orchestrator | **FAILURE** | `ruff format` — 3 files (api.py, flow_diagram.py, metrics_dashboard.py) |
| insight-engine | SUCCESS | Clean |
| docqa-engine | **FAILURE** | `ruff format` — 5 files (app.py, vector_store.py, 3 test files) |
| scrape-and-serve | SUCCESS | Clean |
| mcp-toolkit | SUCCESS | Clean |
| prompt-engineering-lab | **FAILURE** | `ruff check` — E501 line too long + F841 unused variable |
| llm-integration-starter | **FAILURE** | `pip install -e .` — multiple top-level packages (pyproject.toml misconfigured) |
| Revenue-Sprint | SUCCESS | Clean |
| chunkytortoise.github.io | SUCCESS | Clean |

### Cross-Cutting Issues

1. **Invalid theme colors**: EnterpriseHub + Insight Engine have invalid `widgetBackgroundColor`, `widgetBorderColor`, `skeletonBackgroundColor` in `.streamlit/config.toml`
2. **Outdated test counts**: Footer badges/text show stale numbers
3. **exec() usage**: EnterpriseHub root `app.py` uses `exec(code, global_vars)` — code smell
4. **Hardcoded favicon URL**: EnterpriseHub references raw.githubusercontent.com

---

## Agent Team Structure

### Team: `portfolio-polish`

| Agent Name | Type | Repos Assigned | Tasks |
|------------|------|----------------|-------|
| `ci-fixer` | general-purpose | ai-orchestrator, docqa-engine, prompt-eng-lab, llm-integration-starter, jorge_real_estate_bots | Fix all 5 CI failures |
| `theme-fixer` | general-purpose | EnterpriseHub, insight-engine | Fix invalid Streamlit theme colors |
| `app-polisher` | general-purpose | EnterpriseHub, scrape-and-serve, mcp-toolkit | Fix app.py exec(), update badges, fix data warnings |
| `deploy-agent` | general-purpose | ai-orchestrator (AgentForge) | Deploy to Streamlit Cloud, verify |
| `browser-tester` | general-purpose | All 6 deployed apps | Post-fix browser validation using Playwright |

---

## Task Breakdown

### Phase 1: CI Green (Parallel — all 5 repos simultaneously)

#### Task 1A: Fix ai-orchestrator ruff format (ci-fixer)
- Run `ruff format agentforge/api.py agentforge/viz/flow_diagram.py agentforge/viz/metrics_dashboard.py`
- Commit + push
- Verify CI passes

#### Task 1B: Fix docqa-engine ruff format (ci-fixer)
- Run `ruff format app.py docqa_engine/vector_store.py tests/test_client_demo.py tests/test_retriever.py tests/test_vector_store.py`
- Commit + push
- Verify CI passes

#### Task 1C: Fix prompt-engineering-lab ruff check (ci-fixer)
- Fix `tests/test_cli.py:53` — break long line (E501, >120 chars)
- Fix `tests/test_token_counter.py:32` — prefix unused `gemini_tokens` with `_` or use it (F841)
- Commit + push
- Verify CI passes

#### Task 1D: Fix llm-integration-starter package discovery (ci-fixer)
- Edit `pyproject.toml` to explicitly set `packages` (not rely on auto-discovery)
- Should include only `llm_starter` as the main package, exclude `demo_data`
- Commit + push
- Verify CI passes

#### Task 1E: Fix jorge_real_estate_bots mock target (ci-fixer)
- Tests mock `enhanced_hero_metrics.get_enhanced_lead_intelligence` but module no longer exports it
- Update mock target to match current module API, or update module to export the function
- Commit + push
- Verify CI passes

### Phase 2: Theme & UI Polish (Parallel)

#### Task 2A: Fix Streamlit theme colors (theme-fixer)
- Read `.streamlit/config.toml` in EnterpriseHub and insight-engine
- Fix invalid color values for `widgetBackgroundColor`, `widgetBorderColor`, `skeletonBackgroundColor`
- Use valid hex colors that match the existing theme
- Commit + push to both repos

#### Task 2B: Fix EnterpriseHub app.py (app-polisher)
- Replace `exec(code, global_vars)` pattern with proper module import
- Update hardcoded favicon to use relative path or bundled asset
- Update footer test count from 4,467 to current actual count
- Commit + push

#### Task 2C: Fix scrape-and-serve "Infinite extent" warnings (app-polisher)
- Investigate date/price field data that causes infinite extent in charts
- Add proper data validation/defaults for empty or NaN values
- Commit + push

#### Task 2D: Investigate MCP Toolkit 60 warnings (app-polisher)
- Check console warnings, categorize (Streamlit built-in vs app-specific)
- Fix any app-specific warnings
- Commit + push if needed

### Phase 3: Deploy AgentForge

#### Task 3A: Deploy ai-orchestrator to Streamlit Cloud (deploy-agent)
- Verify `app.py` entry point exists and works locally
- Check `.streamlit/config.toml` exists with proper theme
- Verify `requirements.txt` has all dependencies
- Deploy to ct-agentforge.streamlit.app via Streamlit Cloud
- Verify app loads successfully

### Phase 4: Browser Validation (Sequential — after all fixes pushed)

#### Task 4A: Validate all 6 (now 7) apps via Playwright (browser-tester)
For each deployed app:
1. Navigate to URL, wait for full load
2. Check for 0 console errors
3. Click through all tabs/pages
4. Verify demo data loads correctly
5. Check responsive behavior
6. Document any remaining issues

### Phase 5: Final Sync

#### Task 5A: Update portfolio metadata
- Update MEMORY.md with current test counts
- Update chunkytortoise.github.io portfolio page if test counts are shown
- Run `bd sync` for any beads changes
- Final `git push` on all repos

---

## Execution Order

```
Phase 1 (parallel):  1A + 1B + 1C + 1D + 1E  ← Fix all CI failures
Phase 2 (parallel):  2A + 2B + 2C + 2D  ← Theme & UI fixes
Phase 3 (sequential): 3A                 ← Deploy AgentForge (needs CI green first)
Phase 4 (sequential): 4A                 ← Browser validation sweep
Phase 5 (sequential): 5A                 ← Final metadata sync
```

**Estimated total**: Phases 1-2 run in parallel (~15 min), Phase 3 (~5 min), Phase 4 (~10 min), Phase 5 (~5 min)

---

## Success Criteria

- [ ] All 11 repos CI green (0 failures)
- [ ] All 7 Streamlit apps load without console errors
- [ ] No invalid theme color warnings
- [ ] No "Infinite extent" data warnings
- [ ] No exec() usage in any app.py
- [ ] Test counts in footers/badges match actual counts
- [ ] AgentForge deployed and accessible at ct-agentforge.streamlit.app
- [ ] All changes committed, synced, and pushed

---

## Detailed Code Audit Findings (Per Repo)

### EnterpriseHub
| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | `exec(code, global_vars)` — security risk, code smell | HIGH | `app.py:44-53` |
| 2 | Hardcoded favicon URL (raw.githubusercontent.com) | MEDIUM | `app.py` |
| 3 | Try/except for `async_utils` import — fragile optional dep | LOW | `streamlit_demo/app.py:32-37` |
| 4 | Hardcoded "Austin, TX" default market data | LOW | `streamlit_demo/app.py` |
| 5 | Footer says "4,467 tests" — should be ~4,937 | MEDIUM | `streamlit_demo/app.py` |
| 6 | 24+ invalid theme color console warnings | HIGH | `.streamlit/config.toml` |

### DocQA Engine
| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | `tempfile.NamedTemporaryFile(delete=False)` — files leak on disk | MEDIUM | `app.py:188` |
| 2 | Fragile `asyncio.get_event_loop()` wrapper in Streamlit | LOW | `app.py:126-137` |
| 3 | No error handling for PDF/DOCX parsing | MEDIUM | `app.py` |
| 4 | No `page_icon` set in page config | LOW | `app.py` |
| 5 | CI failure: ruff format on 5 files | HIGH | multiple |

### Insight Engine
| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | Invalid theme colors (9+ console warnings) | HIGH | `.streamlit/config.toml` |
| 2 | No graceful handling if `demo_data/` directory missing | MEDIUM | `app.py:58` |
| 3 | No minimum sample size check before training models | LOW | `app.py` |

### Scrape-and-Serve
| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | "Infinite extent" warnings for date/price fields in charts | HIGH | `app.py` |
| 2 | Hardcoded demo URL `https://demo.local` | LOW | `app.py:56` |
| 3 | `tempfile.NamedTemporaryFile(delete=False)` — leak | MEDIUM | `app.py:121` |
| 4 | No validation on CSS selectors (could throw) | LOW | `app.py` |

### MCP Toolkit
| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | 60 console warnings (needs categorization) | MEDIUM | runtime |
| 2 | Fragile type hint parsing via `str(hint)` | LOW | `app.py:103-140` |
| 3 | Unsafe `json.loads()` with generic error | LOW | `app.py:128` |

### AI-Orchestrator (AgentForge)
| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | CI failure: ruff format on 3 files | HIGH | `api.py`, `viz/flow_diagram.py`, `viz/metrics_dashboard.py` |
| 2 | App **not deployed** to Streamlit Cloud (404) | CRITICAL | deployment |
| 3 | No sidebar state persistence across reloads | LOW | `app.py` |

### Prompt-Engineering-Lab
| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | CI failure: E501 + F841 lint errors | HIGH | `tests/test_cli.py:53`, `tests/test_token_counter.py:32` |
| 2 | No mock/fallback data — tabs show nothing if empty | MEDIUM | `app.py` |
| 3 | A/B test logic evaluates both patterns on same output (not truly comparing) | LOW | `app.py:80-91` |
| 4 | App **not deployed** to Streamlit Cloud | MEDIUM | deployment |

### LLM-Integration-Starter
| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | CI failure: `pip install -e .` — multiple top-level packages | CRITICAL | `pyproject.toml` |
| 2 | `time.sleep()` for visual effect — blocks Streamlit | LOW | `app.py:140` |
| 3 | No error handling for `open(fpath)` file reads | MEDIUM | `app.py:59` |
| 4 | App **not deployed** to Streamlit Cloud | MEDIUM | deployment |

---

## Issue Count Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 2 | AgentForge not deployed, llm-starter build broken |
| HIGH | 8 | CI failures (5 + EnterpriseHub pending), invalid theme colors (2) |
| MEDIUM | 9 | Tempfile leaks, outdated badges, missing error handling |
| LOW | 11 | Hardcoded defaults, fragile parsing, minor UX |
| **Total** | **30** | Across 9 repos |
