# Enterprise Security & Compliance Guide

## 1. Secrets Detection (Semgrep)

We use `semgrep` to prevent secrets from entering the codebase.

**Setup:**
`pip install semgrep`

**Run Scan:**
```bash
semgrep --config=p/secrets .
```

**Policy:**
*   Any finding from `p/secrets` blocks deployment.
*   False positives must be explicitly ignored with `# nosemgrep` comments and documented justification.

## 2. Supply Chain Security

**Tool:** `safety`

**Run Scan:**
```bash
safety check -r requirements.txt
```

**Policy:**
*   Critical vulnerabilities must be patched immediately.
*   Low/Medium vulnerabilities are reviewed during sprint planning.

## 3. Data Privacy (GDPR/CCPA)

*   **Data Minimization:** `InventoryManager` stores only necessary lead info.
*   **Deletion:** We must implement a `purge_user(user_id)` function in `InventoryManager` to comply with "Right to be Forgotten".
*   **Encryption:** All PII in Postgres should be encrypted at rest (using PG crypto extensions or application-level encryption).
