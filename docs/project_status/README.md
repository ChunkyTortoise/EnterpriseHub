# Historical Project Status Logs

This folder is an archive of implementation notes, session handoffs, client-specific drafts, and generated status reports from earlier EnterpriseHub work.

Use these files as historical context only. They are not the source of truth for current reviewer claims, production readiness, security posture, test counts, deployment status, or demo availability.

## Current Sources of Truth

For reviewer-facing evidence, start here instead:

| Question | Current source |
|---|---|
| What should a reviewer inspect first? | `README.md`, `HIRING_REVIEW_GUIDE.md`, `docs/repo-map.md` |
| Which claims are safe to quote publicly? | `docs/CLAIM_LEDGER.md` |
| What evidence is current and dated? | `docs/evidence/demo-evidence-pack.md`, `docs/audits/repo-maintenance/2026-05-06/maintainer-audit.md` |
| How are secrets and env files handled? | `docs/security/env-and-secret-policy.md` |
| What architectural decisions are current? | `docs/adr/` |
| What checks can run without production secrets? | `make verify-public` |

## How To Read This Archive

- Treat "production-ready", "fully validated", "complete", and similar phrasing as historical notes unless the claim also appears in `docs/CLAIM_LEDGER.md` with current evidence.
- Treat old test counts and pass/fail statements as stale unless they include a recent command, date, and environment.
- Treat client delivery, pricing, negotiation, and proposal files as project/business artifacts, not engineering proof.
- Treat setup commands as potentially stale; verify against the current README, Makefile, and deployment docs before using them.
- Do not copy secrets, generated values, or deployment snippets from historical handoff files into live configuration.

## File Groups

| Group | Examples | Reviewer use |
|---|---|---|
| Session handoffs | `SESSION_HANDOFF_*.md`, `HANDOFF_JORGE_COMPLETE.md` | Timeline/context only |
| Implementation completion notes | `*_IMPLEMENTATION_COMPLETE.md`, `*_COMPLETE.md` | Historical implementation notes; verify against code/tests before quoting |
| Client/project delivery drafts | `JORGE_START_HERE.md`, `JORGE_COMPLETE_DELIVERY_PACKAGE.md`, `JORGE_FINAL_EMAIL_READY.md` | Business context only |
| Validation/performance reports | `*_VALIDATION*.md`, `JORGE_PERFORMANCE_*.md` | Historical claims; prefer current evidence docs and reproducible commands |
| Contracts/proposals/strategy | `JORGE_GHL_PROJECT_CONTRACT.md`, `JORGE_EXPANSION_PROPOSAL.md`, `JORGE_FINAL_NEGOTIATION_STRATEGY.md` | Commercial context only |
| Reference snippets/guides | `JORGE_INTEGRATION_SNIPPETS.md`, `JORGE_*_REFERENCE.md`, `JORGE_ADVANCED_*` | Potentially useful notes; audit before reuse |

## Maintenance Policy

Keep this folder available for provenance, but do not expand it with new reviewer proof. New evidence should go under `docs/evidence/`, `docs/audits/`, `docs/security/`, `docs/adr/`, or another clearly scoped current documentation area.

When a historical file contains an important claim that is still useful, restate it in `docs/CLAIM_LEDGER.md` with current evidence and recommended wording instead of relying on the old status report.
