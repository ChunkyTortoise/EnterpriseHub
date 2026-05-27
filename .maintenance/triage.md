# Triage: EnterpriseHub

**Date:** 2026-05-17
**Path:** /Users/cave/Projects/EnterpriseHub
**GitHub:** PUBLIC · 2 stars · 1,140 commits · 317MB · 9 local branches

## Scores

| Dimension | Score | Notes |
|---|---|---|
| Hire-relevance | 3 | Deepest platform: multi-agent orchestration, 3-tier cache, eval-driven delivery, 17 CI workflows, 6,714 test fns |
| Code quality | 3 | Extensive tests + CI; ADR-driven. (Not the blocker.) |
| Completeness | 3 | Live demo, many deploy paths. (Not the blocker.) |
| Public-safety | **1** | PUBLIC repo embeds real client identity at scale: **572 files** with `Jorge Salas`/`Acuity Real Estate`/`Rancho Cucamonga`, a `ghl_real_estate_ai/` subsystem, `deploy-jorge.yml`/`monitor-jorge.yml`. Rubric dim-4 = 1 (identifying info that must be scrubbed). Secrets: 474 gitleaks hits reviewed — all sampled are test fixtures / `[REPLACE...]` placeholders / argparse refs / **untracked-gitignored** local files; NO confirmed live leak in tracked/public files. |
| Originality | 3 | Original platform architecture. |

**Total:** 11/15 — but **decision matrix rule 1 fires first**.

## Recommendation: `private` (or fold into the de-identification spec)

Decision matrix rule 1: **Public-safety (1) < 2 → `private`**, regardless of other scores. EnterpriseHub has the same embedded-client-identity exposure that was just escalated to a dedicated de-identification spec for `jorge-real-estate-bots` — at larger scale and in a public, starred repo.

A cosmetic maintenance commit (gitignore/description) is explicitly **NOT** appropriate here: it would falsely signal "hiring-ready" while the client exposure is unresolved. No Phase 5 cosmetic ops performed.

## Real remediation (not a hygiene pass)
1. Reduce exposure now: take repo `private` until de-identified (fastest, given 2 stars + job-hunt timeline), OR
2. Extend the spawned jorge de-identification spec to cover EnterpriseHub's `ghl_real_estate_ai/` subsystem + 572 client-id files + `deploy-jorge`/`monitor-jorge` workflows (the EnterpriseHub client work IS the absorbed jorge engagement — same problem, one spec).
3. Secret hygiene follow-up (lower priority, no live leak found): add a tuned `.gitleaksignore` for the secret-scanning test corpus so future scans aren't 474-noisy.

## Safe-op note (deferred, not executed)
`.kilo/` + `uv.lock` gitignore and the stale-metric description fixes are real but trivial; they are intentionally NOT done this pass because shipping a "polished ✓" commit on a repo with unresolved public client exposure is misleading. Bundle them into the de-id remediation.
