# EnterpriseHub Repo Map

Last updated: 2026-05-06

EnterpriseHub is a portfolio monorepo. This map explains what matters to reviewers and what is supporting material, generated output, or historical context.

## Reviewer Path

Start with current, reviewer-facing evidence:

- `README.md`
- `HIRING_REVIEW_GUIDE.md`
- `docs/CLAIM_LEDGER.md`
- `docs/evidence/demo-evidence-pack.md`
- `docs/security/env-and-secret-policy.md`
- `docs/adr/`

Then inspect the main implementation in `ghl_real_estate_ai/`, the eval surface in `evals/`, and targeted tests in `tests/`.

Use historical or generated material only after the current path is clear:

- `docs/project_status/` contains historical implementation logs, handoffs, client drafts, and older generated status reports.
- `docs/handoffs/`, `docs/delivery/`, `docs/reports/`, `docs/swarm/`, and older project specs are preserved context, not current proof.
- `reports/`, older benchmark outputs, and sandbox artifacts are dated outputs, not current verification unless cited by the claim ledger.
- `content/` and commercial proposal materials are business context, not engineering proof.

## Top-Level Map

| Path | Category | Reviewer note |
|---|---|---|
| `ghl_real_estate_ai/` | Core app | Main AI lead-qualification platform: agents, FastAPI routes, services, Streamlit demo, compliance, CRM logic. |
| `portal_api/` | Core/API package | Smaller FastAPI portal and accelerator API surface with focused tests. |
| `streamlit_cloud/` | Public demo | Streamlit Cloud demo entrypoint and components. Treat demo access as separate from local API auth. |
| `evals/` | Evidence | Golden dataset, evaluator, baseline, and eval docs. Strong reviewer signal. |
| `tests/` | Evidence | Large pytest suite and targeted security/API/eval tests. Use current collection count, not stale README numbers. |
| `docs/adr/` | Evidence | Architecture Decision Records for non-obvious system choices. |
| `docs/evidence/` | Evidence | Curated, dated proof packs for demo status, screenshots, and reviewer-visible claims. Prefer these over older generated reports. |
| `docs/security/` | Evidence | Reviewer-facing security and secret-handling policy. |
| `docs/specs/audits/` | Audit history | Prior hiring/security/architecture audits. Useful context, not current verification unless dated. |
| `docs/project_status/` | Historical status | Archived implementation notes, handoffs, client drafts, and generated status reports. Start with `docs/project_status/README.md`; do not treat these files as current public claim sources. |
| `docs/handoffs/` and `docs/delivery/` | Historical delivery context | Preserved session handoffs and client delivery packages. Useful for timeline/provenance; verify any readiness claims against current evidence before quoting. |
| `docs/reports/` | Historical/generated reports | Older evaluation and status reports. Treat as dated context unless a current reviewer doc explicitly cites them. |
| `docs/swarm/` and `docs/modular-agentic-powerhouse/` | Generated/speculative planning | Agent-swarm plans and architecture explorations. Useful for design history, not current verification. |
| `docs/gumroad/`, `docs/PORTFOLIO_*`, `docs/SPEC_*` | Commercial/speculative collateral | Portfolio, product, and packaging materials. These may contain marketing language and should not be used as engineering proof. |
| `CASE_STUDY.md` | Evidence | Case-study narrative. Claims should remain labeled case-study reported unless backed by public raw data. |
| `BENCHMARKS.md` and `benchmarks/` | Evidence/modeling | Synthetic and local benchmark scripts. Do not present as live production measurements. |
| `advanced_rag_system/` | Supporting package | RAG subsystem and experiments. Important for retrieval review, but not the main app entrypoint. |
| `agentforge/`, `ai-devops-suite/`, `rag-as-a-service/`, `voice-ai-platform/`, `mcp-server-toolkit/` | Portfolio packages | Related packages preserved in the monorepo. Review only after the main path unless evaluating breadth. |
| `packages/` and `shared-schemas/` | Shared libraries | Reusable schemas/contracts and packaging experiments. |
| `frontend/` | Supporting UI | Next.js frontend surface; not the main public demo. |
| `scripts/` | Local tooling | Deployment, validation, demo, and portfolio automation scripts. Some are historical and should be audited before public use. |
| `reports/` | Generated evidence | Proof-pack and sandbox reports. Dated outputs, not always current verification. |
| `content/` | Business/portfolio assets | Outreach, Gumroad, proposal, and marketing material. Not core engineering review. |
| `data/` | Fixtures and local data | Contains fixtures plus local/generated data. Secret-shaped files require owner review before editing. |
| `infrastructure/`, `k8s/`, `deployment/`, `deploy/`, `docker/`, `nginx/`, `monitoring/`, `grafana/`, `observability/` | Infra | Deployment and observability assets. Some are templates or historical platform work. |
| `.claude/` | Local agent tooling | Project-specific Claude agents, skills, hooks, and memory. Useful maintainer context, but not product runtime code. |
| `.beads/` | Backlog | Local issue/backlog state. Treat as project management data. |

## Artifact Policy

- Keep: source code, tests, docs, templates, intentionally curated screenshots, reproducible benchmark scripts, eval data, ADRs.
- Remove from git: virtual environments, browser trace screenshots, debug vector stores, coverage outputs, generated caches, local model artifacts, database dumps, and raw credential files.
- Keep as templates only: sanitized deploy env examples and production secret manifests with `.template` names.
- Flag for owner decision: bundled product ZIPs, generated model artifacts, and any secret-shaped placeholder that could confuse scanners or reviewers.

## Claim Policy

Use `docs/CLAIM_LEDGER.md` as the source of truth for public wording.

- Measured: command output, CI run, production export, or reproducible report.
- Case-study reported: client or project narrative where raw data is not public.
- Synthetic benchmark: generated by a script under stated assumptions.
- Design target: architecture goal; not observed behavior.
- Projection: business estimate; include assumptions.
