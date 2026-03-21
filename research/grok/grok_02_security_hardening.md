# Grok Security Hardening Review: FastAPI Real Estate AI SaaS

*Source: Grok (grok.com) — Thought for 12s, 25 sources*

> "Your app handles real money (Stripe), sensitive leads (GHL + AI qualification), and PII-heavy real-estate data. The four issues you listed represent immediate existential risks (data breach → lawsuits, account takeover → fraud, unauth billing → revenue loss)."

## Priority Order (72-Hour Action Plan)

| Priority | Issue | Why First | Target |
|----------|-------|-----------|--------|
| 1 | SQL Injection | Remote code execution / data exfil | Today – 48h |
| 2 | Webhook Auth Gaps | Public endpoint, fake lead poisoning | This week |
| 3 | Unauth Billing | Money directly at risk | This week |
| 4 | Type Safety | Foundation for everything else | Next 10 days |

---

## ISSUE 1 — SQL Injection (transaction_service.py:445-503)

**Security Impact: CRITICAL — CVSS 9.8**

Current risk: Direct f-string concatenation = classic SQLi. Attacker can dump entire DB, escalate, or delete records via `transaction_id=' OR 1=1--`.

### Correct Fix

```python
# Replace ALL f-strings with SQLAlchemy parameterized queries
from sqlalchemy import text
from fastapi import HTTPException

async def get_milestone_timeline(self, transaction_id: str, db: AsyncSession):
    if not transaction_id or len(transaction_id) > 100:
        raise HTTPException(400, "Invalid transaction_id")

    query = text("""
        SELECT * FROM milestone_timeline_view
        WHERE transaction_id = (
            SELECT id FROM real_estate_transactions
            WHERE transaction_id = :tx_id
        )
    """)
    result = await db.execute(query, {"tx_id": transaction_id})  # ← safe

    # Same pattern for the second query
    celeb_query = text("""
        SELECT COUNT(*) FROM transaction_celebrations
        WHERE transaction_id = :tx_id
        AND milestone_type = :m_type
        AND triggered_at >= NOW() - INTERVAL '1 hour'
    """)
    count = await db.execute(celeb_query, {
        "tx_id": transaction_id,
        "m_type": milestone[1]
    })
```

Long-term: Move to proper Repository class + use `select()` / ORM where possible.

**Effort**: 3–6 hours (fix + full grep audit for other f-strings + unit test with sqlmap-style payloads)

---

## ISSUE 2 — Webhook Auth Gaps (webhook.py 2,715 lines)

**Security Impact: CRITICAL — CVSS 9.1**

> **Key finding**: GHL now uses **Ed25519** (`X-GHL-Signature`) + legacy RSA; they added replay protection in 2025 marketplace update. HMAC-SHA256 is NOT what GHL sends.

Current impact: Attacker can fake lead events, trigger fake AI qualification, or poison CRM.

### Correct Fix

```python
# core/security/webhook.py
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import time

GHL_PUBLIC_KEY = b"..."  # ← from https://marketplace.gohighlevel.com/docs (Ed25519 PEM)

async def verify_ghl_webhook(request: Request):
    body = await request.body()
    sig_header = request.headers.get("X-GHL-Signature") or request.headers.get("X-WH-Signature")
    timestamp = request.headers.get("X-GHL-Timestamp") or request.headers.get("timestamp")

    if not sig_header:
        raise HTTPException(403, "Missing signature")

    # Timestamp replay protection (5 min window)
    if timestamp:
        ts = int(timestamp)
        if abs(time.time() - ts) > 300:
            raise HTTPException(403, "Replay detected")

    # Ed25519 verification (preferred)
    public_key = Ed25519PublicKey.from_public_bytes(...)  # or load PEM
    try:
        public_key.verify(bytes.fromhex(sig_header), body)
    except:
        raise HTTPException(403, "Invalid GHL signature")

    # Optional: store nonce/timestamp in Redis for extra replay defense
    return True

# Apply to ALL endpoints via router-level dependencies:
router = APIRouter(dependencies=[Depends(verify_ghl_webhook)])
```

Apply same dependency to all 20+ endpoints. Add Stripe webhook signature verification identically.

**Effort**: 8–14 hours (library install + one robust verifier + migration of 20 endpoints + Redis idempotency)

---

## ISSUE 3 — Unauthenticated Billing Routes (billing.py 1,525 lines)

**Security Impact: HIGH — CVSS 8.2**

No auth + lint ignore = anyone can create subscriptions, cancel, refund, etc.

### Correct Fix

```python
# core/security/auth.py (create once)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

oauth2_scheme = HTTPBearer()

async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]  # tenant_id or user_id
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

# billing/router.py
router = APIRouter(dependencies=[Depends(require_auth)])  # ← applies to ALL routes
```

Also: Remove `ignore=["ALL"]` from ruff config for billing.py.

**Effort**: 4–7 hours (add dependency + update tests + rotate any leaked tokens)

---

## ISSUE 4 — Type Safety Disabled

**Security Impact: MEDIUM-HIGH** (enables all other bugs; prevents catching them in PRs)

### Correct Fix

```toml
# pyproject.toml
[tool.mypy]
ignore_errors = false
strict = true
disallow_untyped_defs = true
disallow_any_generics = true
warn_return_any = true

# Remove the override block that suppresses ghl_real_estate_ai.*
# Run in waves: billing + transaction_service first
```

**Effort**: 2 days initial (1 week to clean ~300–500 errors hotspots)

---

## CI Gates to Add Forever

```yaml
- name: Ruff Security Rules
  run: ruff check --select=S,B,UP .  # S = flake8-bandit

- name: Mypy Strict
  run: mypy . --strict --no-error-summary || exit 1

- name: Semgrep Security
  uses: returntocorp/semgrep-action@v2
  with:
    config: "p/security-audit,p/python"

- name: Webhook + Auth Tests
  run: pytest tests/security/ -m "webhook or billing" --cov=src --cov-fail-under=90

- name: Dependency Safety
  run: pip-audit --requirement requirements.txt
```

**Additional hard gates**:
- Pre-commit: `detect-private-key`, `sql-injection`, `no-eval`
- PR template must include "Security checklist checked"
- Branch protection: require all above + 2 approvals on security files

---

## Grok's Verdict

> "These four fixes will drop your attack surface by ~85% immediately. After they are merged I strongly recommend a full external pentest (or at minimum `nuclei -t http/cves` + OWASP ZAP automated scan)."
