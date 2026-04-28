# Audit D: Security & Compliance — Credentialing Artifacts
**Date**: 2026-04-27  
**Auditor**: Security Auditor Agent (Audit Agent D)  
**Scope**: Hireability signal — missing credentialing artifacts a senior security-conscious engineer would expect

---

## Executive Verdict

Security maturity is **above-average for a solo-built platform**: fail-closed JWT secret loading, HMAC webhook signatures, Fernet PII encryption, parameterized SQL, bandit + semgrep + pip-audit in CI, and 7-stage compliance pipeline with TCPA/FHA/CCPA stages are all visible and testable. The compliance test suite (`tests/compliance/test_fair_housing_audit.py`) is the strongest hireability artifact in the repo.

The gap is entirely on the **documentary and process layer**: no formal threat model, no pen-test scope document, no SOC2/FedRAMP readiness write-up, and no audit-to-decision traceability between the `compliance_platform/engine/audit_tracker.py` system and the Jorge bot pipeline. A hiring manager who reads the code will find evidence of security intent; an auditor who asks for a threat model, a data-flow diagram, or a signed attestation will find nothing. That gap is fixable in one sprint.

---

## What Is Already Strong

**JWT fail-closed loading**: `ghl_real_estate_ai/api/middleware/jwt_auth.py:21-26` raises `ValueError` at startup if `JWT_SECRET_KEY` is unset or shorter than 32 characters. This is the correct pattern; no silent fallback is possible on the main auth path.

**Webhook signature infrastructure**: HMAC verification is implemented and tested. `tests/security/test_webhook_signatures.py` and `tests/security/test_jorge_webhook_security.py` provide coverage visible in the CI `security-scan.yml` workflow.

**Compliance pipeline stages with TCPA/FHA wiring**: `ghl_real_estate_ai/services/jorge/response_pipeline/stages/` contains `compliance_check.py` (wired to `ComplianceMiddleware.enforce()` with FHA/RESPA fallbacks), `tcpa_opt_out.py` (bilingual Spanish opt-out phrases, exact Jorge spec wording), and `ai_disclosure.py`. These stages short-circuit the pipeline on violations and are integration-tested.

**FHA compliance test depth**: `tests/compliance/test_fair_housing_audit.py` has 7 parametrized test classes covering steering detection, protected-class patterns (9 categories including religious buildings and coded language), redlining, false-positive safe messages, CCPA PII non-leakage in error output, CAN-SPAM opt-out case-insensitivity, and multi-tier Tier1/Tier2 escalation. This is portfolio-grade evidence of FHA-by-design.

**CI security workflow breadth**: `.github/workflows/security-scan.yml` runs 7 jobs: secrets detection, bandit, semgrep, pip-audit + safety, SQL injection pattern scan, Docker Compose checkov, and a fair housing compliance grep — on push to main and weekly schedule.

**Audit tracker schema**: `ghl_real_estate_ai/compliance_platform/engine/audit_tracker.py` defines a structured EU AI Act Article 12 / HIPAA-aligned audit event schema (model lifecycle, policy enforcement, human override, data access events).

---

## Credentialing Gaps

**1. No threat model document.** There is no STRIDE or PASTA model covering the system's attack surface: GHL webhook ingress, Claude/Gemini/Perplexity API egress, PostgreSQL PII store, Redis cache, JWT session layer, or the tenant isolation boundary in the enterprise compliance platform. A senior engineer reviewing a CCPA/FHA-regulated AI system expects to find `docs/security/threat-model.md` with at minimum: assets, trust boundaries, and one row per threat category. Without it, "FHA-compliant by design" cannot be externally attested.

**2. No formal security audit document for current architecture.** `docs/security-audit-report.md` is dated 2026-02-13 and covers a five-item fix list from spec-01. It does not constitute an ongoing audit document. There is no attestation from an independent reviewer, no OWASP Top 10 mapping against the live codebase (the report's OWASP table covers only 6 of 10 categories), and no signed-off remediation ledger. The audit_tracker system (`compliance_platform/engine/audit_tracker.py`) is not wired into the Jorge bot pipeline at all — it exists in a parallel compliance platform with no grep evidence connecting it to Jorge bot decisions.

**3. No pen-test scope document.** Nothing in `docs/` describes what is in scope for external penetration testing: webhook endpoints, SSO flow, enterprise partnership routes, JWT token endpoints, or the Stripe billing integration. An enterprise buyer or senior engineer asking "have you scoped a pen test?" has no artifact to review.

**4. Incomplete OWASP Top 10 coverage documentation.** The existing audit report maps 6 of 10 categories but omits: A06 (Vulnerable and Outdated Components — covered in CI but not documented as a living baseline), A08 (Software and Data Integrity Failures — supply chain, no SBOM), A09 (Security Logging and Monitoring Failures — structured logging exists but no alerting SLA document), and A10 (Server-Side Request Forgery — no explicit test coverage of SSRF on the GHL proxy layer).

**5. No SOC2 or FedRAMP readiness narrative.** The platform handles PII (CCPA-regulated), makes automated qualification decisions (FHA exposure), and processes payments (Stripe). A sentence in a proposal saying "SOC2 Type I readiness" requires at least a written control mapping. Nothing exists.

---

## Wave 4 Build Spec

**Threat model template (fill in one session):**

Create `docs/security/threat-model.md` with sections: System Overview (data-flow diagram), Trust Boundaries (Jorge bot → GHL webhook, API → DB, Redis cache layer), Asset Inventory (PII fields, JWT signing key, GHL API key, Fernet encryption key), STRIDE table (one row per boundary × threat category, with current mitigation or OPEN), and Residual Risk sign-off. The STRIDE table needs approximately 15–20 rows for this surface area. Cite existing controls by `file:line`.

**CVE dependency baseline command (record and commit output):**

```bash
pip-audit --format json -r requirements.txt | tee docs/security/dep-audit-$(date +%Y-%m-%d).json
```

Run this after every `requirements.txt` change. Store one dated baseline in `docs/security/`. This converts the CI ephemeral artifact into a versioned, audit-readable record.

**Pen-test scope document structure:**

Create `docs/security/pentest-scope.md` with: In-Scope Endpoints (all `/api/*` routes, `/api/webhooks/contact`, `/auth/sso/*`, `/api/analytics/*`), Out-of-Scope (Render infrastructure, GHL platform, Stripe), Test Types (authentication bypass, IDOR on tenant isolation, webhook replay, JWT algorithm confusion), Data Classification (no real PII in test environment), and Rules of Engagement (coordinate with Render before any load testing).

**Wire audit_tracker to Jorge compliance decisions:**

In `ghl_real_estate_ai/services/jorge/response_pipeline/stages/compliance_check.py:59+`, after a BLOCKED or FLAGGED result, emit an audit event to the compliance platform tracker. Without this, the `compliance_platform/engine/audit_tracker.py` EU AI Act Article 12 claim has no coverage on the highest-risk decision path.

---

## P0 / P1 Findings

**P0 — Weak fallback secret in `api_monetization.py:518`:**
```python
api_key = jwt.encode(payload, os.environ.get("API_KEY_SIGNING_SECRET", "change-me-in-production"), algorithm="HS256")
```
This is the opposite of the fail-closed pattern at `jwt_auth.py:21-26`. If `API_KEY_SIGNING_SECRET` is unset in any environment, every API key issued by the monetization tier is signed with a known-public string. The fix is to apply the same `raise ValueError` guard. This is a direct inconsistency introduced by the f9ddcad5 commit — the commit replaced `"your-secret-key"` but chose a soft default rather than the hard failure already established elsewhere in the codebase.

**P1 — Dual password-hashing implementations with inconsistent bcrypt-72 handling:**
`ghl_real_estate_ai/api/middleware/jwt_auth.py:252-275` silently truncates passwords at 72 bytes. `ghl_real_estate_ai/api/middleware/enhanced_auth.py:377-393` (per `docs/security-audit-report.md`) raises HTTP 422. The live auth path imports from `jwt_auth` (confirmed by 14 import sites in `api/`; `enhanced_auth` is only used by 3 optional-auth routes). The truncation behavior on the canonical path means a user with a password `>72 bytes` can authenticate with any 72-byte prefix. The `security-audit-report.md` claim that this is fixed is incorrect for the live path. Single canonical `hash_password` in `jwt_auth.py` should raise 422 matching the enhanced_auth behavior.

**P1 — `ALGORITHM = "HS256"` with no algorithm confusion guard (`jwt_auth.py:28`):** The `jwt.decode` calls at lines 118 and 194 pass `algorithms=[ALGORITHM]` as a list, which is correct. However, the codebase uses `python-jose` (not `PyJWT`) for decoding. Confirm the bumped `python-jose>=3.4.0` from f9ddcad5 is actually installed and resolves CVE-2024-33663 (algorithm confusion allowing `none` alg bypass). The security-scan workflow should pin an explicit lower-bound test.

**P1 — `audit_tracker` not wired to Jorge pipeline:** `compliance_platform/engine/audit_tracker.py` references EU AI Act Article 12 compliance, but grep finds zero usage outside the `compliance_platform/` directory. Every BLOCKED compliance decision in the Jorge bot pipeline (`stages/compliance_check.py:59`) is unlogged to the structured audit store. For CCPA/FHA regulatory exposure, every automated decision touching a protected class pattern must be traceable.

---

## Compounding Leverage

**"FHA-compliant by design" case study claim** requires the threat model (showing the compliance check stage in the data flow), the compliance test suite (already exists — strongest artifact), and a one-page attestation document tying the pipeline stages to the specific FHA steering categories. The test suite alone is 60-70% of the way there; the threat model and attestation are the missing 30%.

**Recruiter scorecard unlock:** The existing CI security workflow (7 jobs) plus the compliance test depth is enough to answer "how do you handle security in your solo projects?" credibly. Adding `docs/security/threat-model.md` and `docs/security/dep-audit-<date>.json` converts "I have security tests" to "I have a documented security posture" — a distinct tier on a senior engineer hiring rubric. The pentest scope doc signals enterprise readiness: it shows awareness that security is an external attestation problem, not just a code problem.

**The incident response playbook** (`docs/INCIDENT_RESPONSE_PLAYBOOK.md`) is strong operationally but contains `[BACKEND_URL]` and `REDACTED_LOCATION_ID` placeholders (lines 358-361, 362-363), which read as unfinished to an auditor. Completing those with template variables (`${BACKEND_HEALTH_URL}`) removes the ambiguity about whether the playbook has been validated against a real deployment.
