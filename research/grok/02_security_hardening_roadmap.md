# Security Hardening Roadmap

**Generated**: 2026-03-19
**Codebase**: EnterpriseHub — `ghl_real_estate_ai/`
**Analyst**: Claude Code (claude-sonnet-4-6)

---

## Critical Vulnerabilities (P0)

### SQL Injection — `transaction_service.py`

**Location**: `ghl_real_estate_ai/services/transaction_service.py`

Two raw f-string SQL executions interpolate an untrusted `transaction_id` value (received from an external webhook/API caller) directly into SQL strings with no escaping or parameterization. Both are inside `get_milestone_timeline()`.

#### Vulnerable Query 1 — Lines 445–452

```python
result = await session.execute(f"""
    SELECT * FROM milestone_timeline_view
    WHERE transaction_id = (
        SELECT id FROM real_estate_transactions
        WHERE transaction_id = '{transaction_id}'
    )
    ORDER BY order_sequence
""")
```

**Injection vector**: A value like `' OR '1'='1` for `transaction_id` would return all rows. A value like `'; DROP TABLE real_estate_transactions; --` would destroy production data.

#### Vulnerable Query 2 — Lines 495–503

```python
celebration_check = await session.execute(f"""
    SELECT COUNT(*) FROM transaction_celebrations
    WHERE transaction_id = (
        SELECT id FROM real_estate_transactions
        WHERE transaction_id = '{transaction_id}'
    )
    AND milestone_type = '{milestone[1]}'
    AND triggered_at >= NOW() - INTERVAL '1 hour'
""")
```

**Two injection points**: `transaction_id` AND `milestone[1]` (a value read from the database row — but its origin is user-controlled data at write time, enabling second-order injection).

#### Parameterized Fix — Query 1

```python
from sqlalchemy import text

result = await session.execute(
    text("""
        SELECT * FROM milestone_timeline_view
        WHERE transaction_id = (
            SELECT id FROM real_estate_transactions
            WHERE transaction_id = :transaction_id
        )
        ORDER BY order_sequence
    """),
    {"transaction_id": transaction_id},
)
```

#### Parameterized Fix — Query 2

```python
from sqlalchemy import text

celebration_check = await session.execute(
    text("""
        SELECT COUNT(*) FROM transaction_celebrations
        WHERE transaction_id = (
            SELECT id FROM real_estate_transactions
            WHERE transaction_id = :transaction_id
        )
        AND milestone_type = :milestone_type
        AND triggered_at >= NOW() - INTERVAL '1 hour'
    """),
    {"transaction_id": transaction_id, "milestone_type": milestone[1]},
)
```

**Additional hardening**: Add a UUID/format validator on `transaction_id` at the API boundary (FastAPI path/query param with `regex="^[a-zA-Z0-9_-]{1,64}$"`) so malformed values are rejected before reaching the service layer.

---

### Webhook Authentication Gaps — `webhook.py`

**Location**: `ghl_real_estate_ai/api/routes/webhook.py`

Of the 4 `@router` route handlers found in the file:

| Route | Has `@verify_webhook` | Auth Status |
|---|---|---|
| `POST /tag-webhook` (line 497) | Yes — `@verify_webhook("ghl")` | Protected |
| `POST /webhook` (line 595) | Yes — `@verify_webhook("ghl")` | Protected |
| `POST /initiate-qualification` (line 2383) | Yes — `@verify_webhook("ghl")` | Protected |
| `GET /health` (line 2436) | No | **Intentionally public** (health check) |

**Finding**: The `GET /health` endpoint is the only unauthenticated route, and health checks are a legitimate public endpoint. No critical auth gap exists in webhook.py itself.

**However, two secondary risks exist in the `@verify_webhook` decorator implementation** (`security_framework.py` lines 632–670):

1. **New `SecurityFramework()` per request** (line 654): Each webhook call instantiates a fresh `SecurityFramework`, which creates a new Redis connection pool. Under sustained traffic this leaks connections. The `finally: await security.close_redis()` partially mitigates but creates pool churn.

2. **GHL bypass flag** (`security_framework.py` lines 337–342): `GHL_ALLOW_UNSIGNED_WEBHOOKS=true` silently accepts all GHL webhooks without signature verification. This flag must never be set in production. There is no startup assertion to enforce this.

#### Fix Pattern — Startup Guard

```python
# app.py or lifespan handler
import os
from ghl_real_estate_ai.ghl_utils.config import settings

if settings.environment == "production" and settings.ghl_allow_unsigned_webhooks:
    raise RuntimeError(
        "SECURITY: GHL_ALLOW_UNSIGNED_WEBHOOKS must not be enabled in production"
    )
```

#### Fix Pattern — Singleton SecurityFramework

```python
# api/deps.py
from functools import lru_cache
from ghl_real_estate_ai.services.security_framework import SecurityFramework

@lru_cache(maxsize=1)
def get_security_framework() -> SecurityFramework:
    return SecurityFramework()
```

Then inject via `Depends(get_security_framework)` rather than instantiating inside the decorator.

---

### Unauthenticated Billing Routes — `billing.py`

**Location**: `ghl_real_estate_ai/api/routes/billing.py`

The entire billing router (`/billing` prefix) has **zero authentication dependencies** on any endpoint. There are 11 route handlers:

| Route | Method | Auth | Risk |
|---|---|---|---|
| `POST /subscriptions` | Create subscription | None | **Critical** — creates Stripe charges |
| `GET /subscriptions/{id}` | Read subscription | None | High — exposes billing PII |
| `PUT /subscriptions/{id}` | Modify subscription | None | **Critical** — modifies Stripe plan |
| `DELETE /subscriptions/{id}` | Cancel subscription | None | **Critical** — terminates service |
| `POST /usage` | Record usage | None | High — manipulates metered billing |
| `GET /usage/{id}` | Read usage | None | Medium — business data leak |
| `POST /invoices/{id}/pay` | Trigger payment | None | **Critical** — initiates charges |
| `GET /invoices` | List invoices | None | High — financial record leak |
| `GET /billing-history/{id}` | Billing history | None | High — financial record leak |
| `POST /webhooks/stripe` | Stripe webhook | Stripe sig only | Acceptable (external callback) |
| `GET /analytics/revenue` | Revenue analytics | None | High — ARR/MRR data exposed |
| `GET /analytics/tiers` | Tier distribution | None | Medium |

**Note on `/webhooks/stripe`**: This endpoint does perform Stripe signature verification inline (lines 1210–1217) but uses no other auth. This is the correct pattern for webhook callbacks from Stripe's servers — it is acceptable.

**Note on ruff**: `billing.py` is explicitly excluded from all ruff linting (`pyproject.toml` lines 155 and 201: `"ghl_real_estate_ai/api/routes/billing.py"` in both `exclude` and `extend-per-file-ignores = ["ALL"]`). This means linting would not have caught missing auth patterns.

#### Fix Pattern — JWT Dependency Injection

```python
# api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ghl_real_estate_ai.services.security_framework import SecurityFramework, SecurityLevel

security_bearer = HTTPBearer()

async def require_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
) -> dict:
    framework = SecurityFramework()
    return await framework.validate_jwt_token(credentials.credentials)

async def require_admin_jwt(
    claims: dict = Depends(require_jwt),
) -> dict:
    if claims.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return claims
```

Apply to all write endpoints:

```python
# billing.py
from ghl_real_estate_ai.api.deps import require_admin_jwt

@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    background_tasks: BackgroundTasks,
    _claims: dict = Depends(require_admin_jwt),   # <-- add this
):
    ...
```

Read endpoints (GET) should at minimum use `require_jwt` (any authenticated user). Revenue analytics should use `require_admin_jwt`.

---

## High Priority (P1)

### Type Safety — mypy Suppression

**Location**: `pyproject.toml` lines 74–118

The `[tool.mypy]` block has 9 rules disabled at the global level:

| Setting | Value | What it disables |
|---|---|---|
| `ignore_missing_imports` | `true` | Missing stub errors for all third-party packages |
| `warn_return_any` | `false` | Functions returning `Any` silently allowed |
| `disallow_untyped_defs` | `false` | Functions without type annotations pass |
| `disallow_incomplete_defs` | `false` | Partially annotated functions pass |
| `check_untyped_defs` | `false` | Bodies of untyped functions not checked at all |
| `no_implicit_optional` | `false` | `param: str = None` doesn't warn (should be `Optional[str]`) |
| `warn_redundant_casts` | `false` | Useless `cast()` calls not flagged |
| `warn_unused_ignores` | `false` | Stale `# type: ignore` comments not flagged |
| `warn_no_return` | `false` | Functions that don't return on all paths allowed |
| `strict_equality` | `false` | Trivially false equality comparisons allowed |

Worse, there is a blanket `ignore_errors = true` override (lines 103–118) applied to the entire application codebase:

```toml
[[tool.mypy.overrides]]
# Suppress all errors for legacy/untyped packages; tighten incrementally
module = [
    "ghl_real_estate_ai.*",
    "ghl_integration.*",
    "portal_api.*",
    "utils.*",
    "advanced_rag_system.*",
    "src.*",
    "app",
    "main",
    "mcp_server",
    "production_server",
    "admin_dashboard",
]
ignore_errors = true
```

This means mypy reports zero errors regardless of the actual type state of the application code. Running `mypy` in CI gives a false green.

#### Remediation Plan (incremental, 3 sprints)

**Sprint A — Scaffolding (1 day)**:
- Remove `ignore_errors = true` from the `ghl_real_estate_ai.*` override.
- Enable `disallow_untyped_defs = true` for new files only via per-file-overrides.
- Add `mypy --ignore-missing-imports ghl_real_estate_ai/services/security_framework.py` to CI as a smoke check on the security-critical module.

**Sprint B — Security-critical paths (3 days)**:
- Add type annotations to `security_framework.py`, `billing.py`, `webhook.py`, and `transaction_service.py`.
- Enable `check_untyped_defs = true` globally.
- Enable `warn_return_any = true` globally.

**Sprint C — Full coverage (1 week)**:
- Enable `disallow_untyped_defs = true` globally.
- Enable `no_implicit_optional = true`.
- Work down the mypy error list module by module.

---

### Linter Suppression Issues — Ruff Exclusions

**Location**: `pyproject.toml` lines 148–202

#### File-level exclusions (entire files skip all linting)

The `ruff.exclude` list silently skips 13 files/directories including:

- `ghl_real_estate_ai/api/routes/billing.py` — the file with missing auth (confirmed above)
- `ghl_real_estate_ai/api/schemas/enterprise.py` — schema definitions (type safety risk)
- `ghl_real_estate_ai/services/ultra_fast_ml_engine.py` — ML service
- `ghl_real_estate_ai/streamlit_demo/` — dashboard pages
- `ghl_real_estate_ai/api/routes/market_intelligence.py` — another route file

The `extend-per-file-ignores` block also applies `["ALL"]` to `billing.py` and `enterprise.py`, making them doubly excluded.

#### Rule-level suppressions (apply to all non-excluded files)

| Rule | Code | Risk Level |
|---|---|---|
| `E722` — bare except | ignored | High — swallows all exceptions silently |
| `F403` — `import *` | ignored | Medium — pollutes namespace, masks undefined names |
| `F405` — undefined from `import *` | ignored | Medium — allows using undefined symbols |
| `F821` — undefined name | ignored | Medium — false positives claimed but hides real bugs |
| `F841` — unused variable | ignored | Low — but hides logic errors in prototype code |
| `F401` — unused import | ignored | Low — noisy in `__init__.py` but hides dead code |

#### Fix Priority Order

1. **Remove `billing.py` from ruff exclude** — this is the highest-risk file. Auth bugs are invisible to linting.
2. **Remove `E722` (bare except) suppression** — replace bare `except:` with `except Exception:` throughout.
3. **Remove `F403`/`F405`/`F821`** — audit star imports in the affected modules; replace with explicit imports.
4. **Remove `enterprise.py` from exclude** — review and fix schema file to conform to linting rules.

---

## Implementation Roadmap

### Sprint 1 — P0 SQL Injection (2 days)

1. Fix Query 1 in `transaction_service.py:445`: replace f-string with `sqlalchemy.text()` + bindparams.
2. Fix Query 2 in `transaction_service.py:495`: same fix, parameterize both `transaction_id` and `milestone_type`.
3. Add `transaction_id` format validation at the API layer (UUID regex or explicit allowlist pattern).
4. Add regression test: pass `' OR '1'='1` as `transaction_id` and assert the query returns no rows and raises no DB error.
5. Search entire codebase for additional `execute(f"""` and `execute(f'` patterns and repeat.

```bash
grep -rn "execute(f['\"]" ghl_real_estate_ai/
```

### Sprint 2 — P0 Billing Auth (3 days)

1. Create `ghl_real_estate_ai/api/deps.py` with `require_jwt` and `require_admin_jwt` dependency functions.
2. Add `Depends(require_admin_jwt)` to all write endpoints: `POST /subscriptions`, `PUT /subscriptions/{id}`, `DELETE /subscriptions/{id}`, `POST /invoices/{id}/pay`, `POST /usage`.
3. Add `Depends(require_jwt)` to all read endpoints: `GET /subscriptions/{id}`, `GET /usage/{id}`, `GET /invoices`, `GET /billing-history/{id}`, `GET /analytics/revenue`, `GET /analytics/tiers`.
4. Remove `billing.py` from ruff `exclude` and `extend-per-file-ignores`.
5. Write tests: unauthenticated call to `POST /subscriptions` must return 401; valid admin JWT must return 200.

### Sprint 3 — P1 Webhook Security Hardening (1 day)

1. Add startup assertion in `app.py` lifespan to block `GHL_ALLOW_UNSIGNED_WEBHOOKS=true` in production.
2. Refactor `SecurityFramework` instantiation in `verify_webhook` decorator to use a module-level singleton or FastAPI dependency injection pattern to prevent Redis connection pool churn.
3. Document the `GHL_ALLOW_UNSIGNED_WEBHOOKS` flag in `DEPLOYMENT_CHECKLIST.md` as a dev-only flag with an explicit warning.

### Sprint 4 — P1 Type Safety (1 week)

1. Remove `ignore_errors = true` from mypy override block.
2. Run `mypy ghl_real_estate_ai/` and triage output.
3. Annotate `security_framework.py`, `billing.py`, `webhook.py`, `transaction_service.py` first (security-critical path).
4. Enable `check_untyped_defs = true` and `warn_return_any = true` globally.
5. Add mypy to CI gate: fail build on new type errors in the security path modules.

### Sprint 5 — P1 Linter Cleanup (3 days)

1. Remove file-level ruff exclusions for `billing.py` and `enterprise.py`.
2. Fix `E722` bare excepts found by enabling the rule.
3. Replace star imports in the modules that use `F403`/`F405`.
4. Remove `F821` suppression and fix any genuine undefined-name errors surfaced.

---

## Effort Estimates

| Issue | Severity | Estimated Effort | Complexity |
|---|---|---|---|
| SQL injection — Query 1 (`transaction_service.py:445`) | P0 Critical | 30 min | Low |
| SQL injection — Query 2 (`transaction_service.py:495`) | P0 Critical | 30 min | Low |
| Scan for additional f-string SQL codebase-wide | P0 Critical | 2 hr | Low |
| Billing route auth — deps.py creation | P0 Critical | 1 hr | Low |
| Billing route auth — apply to 11 routes | P0 Critical | 2 hr | Low |
| Billing auth test coverage | P0 Critical | 3 hr | Medium |
| GHL bypass flag startup guard | P0 High | 30 min | Low |
| SecurityFramework singleton refactor | P1 High | 2 hr | Medium |
| mypy — remove `ignore_errors` override | P1 High | 30 min | Low |
| mypy — annotate 4 security-critical files | P1 High | 1–2 days | High |
| mypy — global `check_untyped_defs` | P1 Medium | 3–5 days | High |
| Ruff — remove `billing.py` exclusion + fix | P1 Medium | 2 hr | Low |
| Ruff — fix `E722` bare excepts | P1 Medium | 4 hr | Low |
| Ruff — remove star import suppressions | P1 Medium | 1 day | Medium |
| **Total P0** | | **~1.5 days** | |
| **Total P1** | | **~2 weeks** | |

---

## Key Files Referenced

| File | Issue |
|---|---|
| `ghl_real_estate_ai/services/transaction_service.py` (lines 445, 495) | SQL injection — two f-string queries |
| `ghl_real_estate_ai/api/routes/billing.py` (all route handlers) | Missing authentication on all 10 non-webhook endpoints |
| `ghl_real_estate_ai/api/routes/webhook.py` (line 2436) | Health endpoint is public (intentional, no action needed) |
| `ghl_real_estate_ai/services/security_framework.py` (lines 337–342, 654) | GHL bypass flag; per-request SecurityFramework instantiation |
| `pyproject.toml` (lines 74–118, 148–202) | 9 mypy rules disabled; `ignore_errors = true` on all app modules; billing.py excluded from ruff |
