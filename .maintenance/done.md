# Maintenance done: EnterpriseHub

**Date:** 2026-05-17
**Branch:** chore/maintenance-2026-05-17 (1 commit, forked from clean `main`)
**Triage:** Public-safety=1 → rubric says `private`; user chose **targeted visible-surface scrub, stay public, deep de-id → spec**

## What was done (fast, deadline-aware pass)
Scrubbed real-client identity from the **hiring-visible surface only** — the files a reviewer opens first:
- `CASE_STUDY.md` — "Rancho Cucamonga" → "Southern California" (the actual hiring doc; now 0 client ids)
- `README.md` — ADR-0003 label "Jorge Handoff Architecture" → "Multi-Bot Handoff Architecture" (link path unchanged; README now 0 client ids)
- `GEMINI.md` — dropped "(Jorge Salas / Lyrio.io)"
- `CHANGELOG.md` — city refs → "Southern California"
- `.gitignore` — ignore `.maintenance/`, `.kilo/`, `uv.lock`

Verification: CASE_STUDY/README/GEMINI = 0 client identifiers; CHANGELOG city refs = 0.

## Honest scope boundary — NOT done (routed to the de-identification spec)
This pass did **not** resolve full public-safety. Still exposed in the public repo until the spawned spec executes:
- **~572 files** with `Jorge Salas`/`Acuity Real Estate`/`Rancho Cucamonga` (source, tests, eval data, internal runbooks)
- `ghl_real_estate_ai/` subsystem, `agents/jorge_*_bot.py`, `services/jorge/`, `deploy-jorge.yml`, `monitor-jorge.yml`
- `docs/adr/0003-jorge-handoff-architecture.md` — content + filename (rename needs README link update)
- 7 bare "Jorge" in `CHANGELOG.md` + ~18 in `PROMPT_CHANGELOG.md` (quoted prompt-persona history)
- `.claude/CLAUDE.md` (architecturally names the client/market throughout)
- git history (1,140 commits) — likely contains the identifiers; history rewrite is a separate high-risk decision
- GitHub repo metadata / `deploy-jorge` workflow names

**Action:** extend the spawned jorge de-identification spec to cover EnterpriseHub (same client engagement, absorbed). Until then, EnterpriseHub remains public with a residual professionalism exposure in non-first-glance files.

## Secrets
gitleaks: 474 findings, **no confirmed live leak**. Sampled non-test paths: tracked `deploy/*.env` = `[REPLACE...]` placeholders; `register_tenant.py` = argparse refs; the alarming `.env.*.production` / tenant-data / `.mcp.json` are **untracked + gitignored, not public**. Test-heavy noise (incl. `tests/test_secret_scan.py`). Recommend a tuned `.gitleaksignore` (spec follow-up).

## Phase 7
HM-persona dispatch intentionally skipped: the dominant issue (deep client footprint) is known and routed to the spec; the visible README is now verified clean, so a first-glance score adds little for the token cost. (Deliberate scope reduction.)

## Next user action
1. Review: `git -C /Users/cave/Projects/EnterpriseHub diff main..chore/maintenance-2026-05-17`
2. If satisfied: `git checkout main && git merge chore/maintenance-2026-05-17` (do NOT push until you've decided on the deep de-id, since history/remaining files still expose the client)
3. **Important:** the first-glance red flag is fixed, but treat full publication as gated on the de-identification spec. Consider whether to fold EnterpriseHub into that spec now.
4. `AGENT_MEMORY_STRATEGY.md` left untracked/untouched as agreed — your call to keep/commit/remove.
