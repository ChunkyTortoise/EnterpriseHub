# Portfolio Polish — Continuation Prompt

Paste this into a new Claude Code session to execute the plan.

---

## Prompt

```
Read `plans/PORTFOLIO_POLISH_SPEC.md` for the full audit and task breakdown. Execute Phases 1-2 in parallel using a team of agents.

## Context
- All repos are at `/Users/cave/Documents/GitHub/`
- 5 CI failures need fixing, 2 theme configs broken, several app.py issues
- AgentForge (ai-orchestrator) needs Streamlit Cloud deployment (manual — flag for me)

## Phase 1: Fix 5 CI Failures (parallel agents)

### Agent 1 — ai-orchestrator (ruff format)
```bash
cd /Users/cave/Documents/GitHub/ai-orchestrator
ruff format agentforge/api.py agentforge/viz/flow_diagram.py agentforge/viz/metrics_dashboard.py
git add agentforge/api.py agentforge/viz/flow_diagram.py agentforge/viz/metrics_dashboard.py
git commit -m "style: ruff format 3 files for CI

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
git push
```

### Agent 2 — docqa-engine (ruff format)
```bash
cd /Users/cave/Documents/GitHub/docqa-engine
ruff format app.py docqa_engine/vector_store.py tests/test_client_demo.py tests/test_retriever.py tests/test_vector_store.py
git add app.py docqa_engine/vector_store.py tests/test_client_demo.py tests/test_retriever.py tests/test_vector_store.py
git commit -m "style: ruff format 5 files for CI

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
git push
```

### Agent 3 — prompt-engineering-lab (ruff check fixes)
```bash
cd /Users/cave/Documents/GitHub/prompt-engineering-lab
```
- Fix `tests/test_cli.py:53` — break the long line (>120 chars). The line is:
  `result = runner.invoke(cli, ["enhance", "Write code", "-p", "role", "--role", "developer", "--expertise", "Python"])`
  Break into multi-line list.
- Fix `tests/test_token_counter.py:32` — change `gemini_tokens = counter.count(text, "gemini")` to `_gemini_tokens = ...` or add an assertion that uses it.
- Run `ruff check .` to verify clean, then commit + push.

### Agent 4 — llm-integration-starter (pyproject.toml fix)
```bash
cd /Users/cave/Documents/GitHub/llm-integration-starter
```
- Edit `pyproject.toml` to add explicit package discovery:
  ```toml
  [tool.setuptools.packages.find]
  include = ["llm_starter*"]
  ```
- This tells setuptools to only package `llm_starter`, ignoring `demo_data` and `llm_integration_starter` directories.
- Run `pip install -e .` locally to verify, then commit + push.

### Agent 5 — jorge_real_estate_bots (mock target fix)
```bash
cd /Users/cave/Documents/GitHub/jorge_real_estate_bots
```
- 3 tests fail because they mock `enhanced_hero_metrics.get_enhanced_lead_intelligence` which no longer exists.
- Read the `enhanced_hero_metrics` module to find what the function was renamed to or where it moved.
- Update the mock targets in the failing tests to match the current API.
- Run `pytest` on the affected tests to verify, then commit + push.

## Phase 2: Theme & UI Polish (parallel agents)

### Agent 6 — Fix Streamlit theme colors (EnterpriseHub + insight-engine)
Both repos have `.streamlit/config.toml` with invalid color keys that Streamlit doesn't recognize:
- `widgetBackgroundColor`, `widgetBorderColor`, `skeletonBackgroundColor` are NOT valid Streamlit theme keys
- Valid keys are: `primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`, `font`
- Remove the invalid keys from `[theme]` section in both repos
- EnterpriseHub: `/Users/cave/Documents/GitHub/EnterpriseHub/.streamlit/config.toml`
- Insight Engine: `/Users/cave/Documents/GitHub/insight-engine/.streamlit/config.toml`
- Commit + push both repos.

### Agent 7 — Fix EnterpriseHub app.py issues
1. **exec() removal** (`app.py:44-53`): Replace `exec(code, global_vars)` with a proper `importlib` or direct import of the streamlit_demo app module.
2. **Favicon**: Change hardcoded `https://raw.githubusercontent.com/ChunkyTortoise/EnterpriseHub/main/assets/favicon.png` to a relative path or emoji fallback.
3. **Footer test count**: Find "4,467 tests" in `ghl_real_estate_ai/streamlit_demo/app.py` and update to ~4,937. Get exact count with: `cd /Users/cave/Documents/GitHub/EnterpriseHub && python -m pytest --collect-only -q 2>/dev/null | tail -1`
4. Commit + push.

### Agent 8 — Fix scrape-and-serve "Infinite extent" warnings
- The Vega-Lite "Infinite extent for field date/price" warnings come from the Price Monitor tab rendering charts with empty/NaN data.
- Read `/Users/cave/Documents/GitHub/scrape-and-serve/app.py` and find the Price Monitor section.
- Add data validation: filter out NaN/None values before passing to `st.vega_lite_chart` or `st.altair_chart`.
- If demo_data/products.csv has empty date/price columns, fill with sensible defaults.
- Commit + push.

## After Phase 1-2 complete:
1. Verify all CI passes: `for repo in ai-orchestrator docqa-engine prompt-engineering-lab llm-integration-starter jorge_real_estate_bots EnterpriseHub; do echo "=== $repo ==="; gh run list -R chunkytortoise/$repo --limit 1; done`
2. Flag me for AgentForge Streamlit Cloud deployment (manual step)
3. Use Playwright MCP to validate each deployed app loads without console errors
4. Update MEMORY.md with final test counts and CI status

## Session Close Protocol
```bash
bd sync
git push  # for each modified repo
```
```

---

## Files Referenced

| File | Purpose |
|------|---------|
| `plans/PORTFOLIO_POLISH_SPEC.md` | Full audit with 30 issues across 9 repos |
| `plans/PORTFOLIO_POLISH_PROMPT.md` | This file — continuation prompt |
| `.streamlit/config.toml` | Theme config (EnterpriseHub + insight-engine) |
| `app.py` | Root entry point (all 8 repos) |
| `ghl_real_estate_ai/streamlit_demo/app.py` | EnterpriseHub main Streamlit app |

## Repos to Modify

| # | Repo | Path | Changes |
|---|------|------|---------|
| 1 | ai-orchestrator | `/Users/cave/Documents/GitHub/ai-orchestrator` | ruff format 3 files |
| 2 | docqa-engine | `/Users/cave/Documents/GitHub/docqa-engine` | ruff format 5 files |
| 3 | prompt-engineering-lab | `/Users/cave/Documents/GitHub/prompt-engineering-lab` | Fix 2 lint errors |
| 4 | llm-integration-starter | `/Users/cave/Documents/GitHub/llm-integration-starter` | Fix pyproject.toml packages |
| 5 | jorge_real_estate_bots | `/Users/cave/Documents/GitHub/jorge_real_estate_bots` | Fix 3 mock targets |
| 6 | EnterpriseHub | `/Users/cave/Documents/GitHub/EnterpriseHub` | Theme + app.py + footer |
| 7 | insight-engine | `/Users/cave/Documents/GitHub/insight-engine` | Theme config |
| 8 | scrape-and-serve | `/Users/cave/Documents/GitHub/scrape-and-serve` | Price Monitor data validation |
