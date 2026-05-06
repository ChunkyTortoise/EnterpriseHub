# EnterpriseHub Demo Evidence Pack

Last updated: 2026-05-06

This pack keeps demo claims honest for hiring managers and client reviewers. It explains what the demo proves, what it does not prove, and which screenshots are curated evidence rather than live production exports.

## Demo Access

| Surface | Status | Notes |
|---|---|---|
| Streamlit Cloud | Available as a hosted demo surface | URL: https://ct-enterprise-ai.streamlit.app. Viewer access may require allowlist depending on deployment settings. |
| Local Streamlit demo | Reproducible from source | Run `make demo` for the local synthetic-data demo. |
| Local/API demo auth | Synthetic demo credentials only | `demo_user` / `Demo1234!` and `admin` / `Admin1234!` are demo auth values, not production credentials. See `docs/security/env-and-secret-policy.md`. |
| API docs | Local/staging surface | Swagger UI is available when the FastAPI app is running. Do not claim public API docs unless a public deployment is verified. |

## What The Demo Proves

- The project has a reviewer-visible UI for exploring the platform narrative and synthetic workflows.
- The repo contains AI/backend systems behind the demo: FastAPI services, eval harnesses, CRM/webhook boundaries, orchestration, cache design, and compliance processing.
- The demo is suitable for portfolio inspection when paired with `README.md`, `HIRING_REVIEW_GUIDE.md`, and `docs/CLAIM_LEDGER.md`.

## What The Demo Does Not Prove

- It does not prove live production traffic, current CRM exports, or billing savings.
- It does not prove every historical screenshot is current.
- It does not prove public unauthenticated access unless the Streamlit Cloud deployment is checked at review time.
- It does not make deploy env files or secret-shaped fixtures safe to publish; those remain owner-decision items in the maintainer audit.
- It does not require production secrets for `make verify-public` or `make verify-focused`.

## Curated Screenshots

Use these as visual evidence only after confirming they still match the current demo:

| Screenshot | Purpose |
|---|---|
| `assets/screenshots/banner.png` | README banner and first impression. |
| `assets/screenshots/platform-overview.png` | Platform overview visual. |
| `assets/screenshots/jorge_dashboard_01.png` | Jorge bot dashboard evidence. |
| `assets/screenshots/cache-performance.png` | Cache/performance narrative visual. |
| `assets/screenshots/reliability-diagram.png` | Reliability/architecture narrative visual. |
| `docs/screenshots/home_dashboard.png` | Historical home dashboard screenshot. |
| `docs/screenshots/MODULE_SCREENSHOTS.md` | Screenshot inventory; dated historical context, not automatically current proof. |

## Reviewer Verification

```bash
make verify-public
make verify-focused
```

`make verify-public` is the fast trust gate. `make verify-focused` runs targeted evidence tests for evals, orchestration, SQL safety, and the Jorge response pipeline.

## Refresh Checklist

- Re-open the Streamlit Cloud URL and record whether allowlist access is required.
- Run `make demo` locally and capture fresh screenshots if the UI has materially changed.
- Update this pack with the exact date and command output for any newly quoted demo status.
- Keep screenshots free of real customer data, raw API keys, private emails, and production identifiers.
