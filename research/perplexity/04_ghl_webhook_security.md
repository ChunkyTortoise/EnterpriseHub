# GoHighLevel Webhook Security Best Practices 2025-2026

**Research date**: March 19, 2026
**Context**: EnterpriseHub — FastAPI/PostgreSQL/Redis platform receiving live GHL real estate lead data. Current state: `@verify_webhook("ghl")` applied to 3 of ~4 GHL webhook endpoints in `webhook.py` (all 3 POST routes), but no replay protection, no timestamp validation, and no nonce tracking anywhere in the codebase.

---

## Key Findings

1. **GHL is mid-migration from RSA to Ed25519**: As of 2025, GHL sends two signature headers simultaneously. `X-WH-Signature` (RSA-SHA256, legacy) is deprecated July 1, 2026. `X-GHL-Signature` (Ed25519, current) is the authoritative header. EnterpriseHub's current `_verify_ghl_signature()` uses HMAC-SHA256 against a shared secret — this is appropriate for GHL's **Custom Webhook Workflow Actions** (which do not send public-key signatures) but would fail verification for **Marketplace app webhooks** that use the Ed25519 public key method.

2. **No replay protection exists**: The codebase has no timestamp validation window, no nonce store, and no `webhookId` deduplication. A captured webhook POST could be replayed indefinitely.

3. **Coverage gap is real but narrower than stated**: The 2,715-line `webhook.py` file has only 3 POST routes and 1 GET route. All 3 POST routes have `@verify_webhook("ghl")`. The concern about "3 of 20+ endpoints" may reflect a larger count of sub-functions within handlers rather than distinct routes, but the risk is still real because `initiate-qualification` at line 2383 did not appear to have the decorator applied in earlier versions.

4. **The `GHL_ALLOW_UNSIGNED_WEBHOOKS` bypass flag is a production risk**: The `_verify_ghl_signature()` method logs a warning and returns `True` if this flag is set. This flag must never be `True` in production.

5. **GHL webhook payloads include `webhookId` and `timestamp`** fields in the JSON body that can be used for deduplication and replay prevention without requiring external headers.

---

## GHL Webhook Signature Verification

### Signature Headers (as of 2025-2026)

| Header | Algorithm | Status | Use Case |
|--------|-----------|--------|----------|
| `X-GHL-Signature` | Ed25519 (public key) | Current — preferred | Marketplace app webhooks |
| `X-WH-Signature` | RSA-SHA256 (public key) | Legacy — deprecated July 1, 2026 | Old Marketplace webhooks |
| `X-HighLevel-Signature` | HMAC-SHA256 (shared secret) | Active | SaaS Plan webhooks |
| *(no header)* | Shared secret in body/header | Active | Custom Workflow Webhook Actions |

### GHL Ed25519 Public Key (for `X-GHL-Signature`)

```
-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAi2HR1srL4o18O8BRa7gVJY7G7bupbN3H9AwJrHCDiOg=
-----END PUBLIC KEY-----
```

### Verification Decision Tree

```
Incoming GHL webhook
        |
        v
X-GHL-Signature present?
   YES --> Verify with Ed25519 public key --> PASS/FAIL
   NO  --> X-WH-Signature present?
              YES --> Verify with RSA public key (legacy, pre-July 2026) --> PASS/FAIL
              NO  --> Is this a Custom Workflow Action?
                         YES --> Compare against shared secret (HMAC or raw)
                         NO  --> REJECT (401)
```

### What EnterpriseHub's Current Implementation Does

The existing `_verify_ghl_signature()` in `ghl_real_estate_ai/services/security_framework.py` (line 335):
- Reads `X-GHL-Signature` header
- Computes `HMAC-SHA256(secret, raw_body)` and compares with constant-time `hmac.compare_digest()`
- Falls back to comparing the signature directly against the raw secret (for Custom Webhook Actions that send a static token)
- Raises `HTTPException(401)` on missing signature, `HTTPException(500)` on missing config

This is **correct for Custom Workflow Webhook Actions** which send a static bearer-style token or HMAC, but will fail for Marketplace webhooks that use the Ed25519 public key flow.

---

## Replay Attack Prevention

A replay attack captures a valid, signed webhook POST and re-sends it to trigger the same action (e.g., creating a duplicate lead, firing a qualification sequence twice). HMAC verification alone does not prevent this.

### Three-Layer Defence

**Layer 1 — Timestamp window validation**
Reject any webhook where the timestamp in the payload (or a dedicated header) is more than 5 minutes old or more than 5 minutes in the future. GHL payloads include an ISO 8601 `timestamp` field.

**Layer 2 — Nonce/ID deduplication via Redis**
Store the `webhookId` from the GHL payload in Redis with a TTL equal to your timestamp window (300 seconds). Use an atomic `SET IF NOT EXISTS` (`SET key value NX EX 300`). If the key already exists, the webhook is a duplicate.

**Layer 3 — Persistent idempotency record in PostgreSQL**
For business-critical actions (lead creation, qualification), record the `webhookId` in a `processed_webhooks` table with a `UNIQUE` constraint. This handles cases where Redis is flushed or unavailable.

### GHL Payload Fields for Replay Prevention

```json
{
  "type": "ContactCreate",
  "timestamp": "2026-03-19T14:32:00.000Z",
  "webhookId": "wh_abc123def456",
  "data": { ... }
}
```

Both `timestamp` and `webhookId` are available without additional headers.

---

## FastAPI Implementation Pattern

### Complete Webhook Security Middleware

```python
# ghl_real_estate_ai/services/ghl_webhook_security.py
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException, Request

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# GHL Ed25519 public key (hardcoded per GHL docs — not a secret)
GHL_ED25519_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAi2HR1srL4o18O8BRa7gVJY7G7bupbN3H9AwJrHCDiOg=
-----END PUBLIC KEY-----"""

TIMESTAMP_TOLERANCE_SECONDS = 300  # 5-minute window
WEBHOOK_ID_TTL_SECONDS = 600       # 10-minute Redis TTL (buffer past tolerance)


def _load_ed25519_public_key() -> Ed25519PublicKey:
    return serialization.load_pem_public_key(GHL_ED25519_PUBLIC_KEY_PEM)


def verify_ghl_ed25519(raw_body: bytes, signature_b64: str) -> bool:
    """Verify X-GHL-Signature using GHL's Ed25519 public key."""
    import base64
    try:
        pub_key = _load_ed25519_public_key()
        sig_bytes = base64.b64decode(signature_b64)
        pub_key.verify(sig_bytes, raw_body)
        return True
    except Exception as e:
        logger.warning(f"Ed25519 verification failed: {e}")
        return False


def verify_ghl_hmac(raw_body: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature (Custom Workflow Actions)."""
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    # Also accept raw secret for static-token Custom Webhook Actions
    return hmac.compare_digest(signature, expected) or hmac.compare_digest(signature, secret)


def validate_timestamp(payload_timestamp: Optional[str]) -> None:
    """Raise 401 if timestamp is outside the 5-minute tolerance window."""
    if not payload_timestamp:
        raise HTTPException(status_code=401, detail="Missing webhook timestamp")
    try:
        # GHL sends ISO 8601: "2026-03-19T14:32:00.000Z"
        ts = datetime.fromisoformat(payload_timestamp.replace("Z", "+00:00"))
        age = abs(time.time() - ts.timestamp())
        if age > TIMESTAMP_TOLERANCE_SECONDS:
            raise HTTPException(
                status_code=401,
                detail=f"Webhook timestamp out of acceptable window ({age:.0f}s old)"
            )
    except ValueError:
        raise HTTPException(status_code=401, detail="Unparseable webhook timestamp")


async def check_and_store_nonce(redis_client: aioredis.Redis, webhook_id: str) -> None:
    """
    Atomic nonce check. Raises 409 if webhook_id was already processed.
    Uses SET NX (set-if-not-exists) to prevent race conditions.
    """
    redis_key = f"wh:nonce:{webhook_id}"
    stored = await redis_client.set(redis_key, "1", nx=True, ex=WEBHOOK_ID_TTL_SECONDS)
    if stored is None:
        # Key already existed — duplicate webhook
        logger.warning(f"Duplicate webhook rejected: {webhook_id}")
        raise HTTPException(status_code=409, detail="Duplicate webhook — already processed")
```

### FastAPI Dependency for GHL Webhooks

```python
# ghl_real_estate_ai/api/dependencies/ghl_webhook.py
from fastapi import Depends, Header, Request
from typing import Optional
import json

from ghl_real_estate_ai.services.ghl_webhook_security import (
    validate_timestamp,
    verify_ghl_ed25519,
    verify_ghl_hmac,
    check_and_store_nonce,
)
from ghl_real_estate_ai.core.config import settings
from ghl_real_estate_ai.core.redis_client import get_redis


async def ghl_webhook_security(
    request: Request,
    x_ghl_signature: Optional[str] = Header(None, alias="X-GHL-Signature"),
    x_wh_signature: Optional[str] = Header(None, alias="X-WH-Signature"),
    redis=Depends(get_redis),
) -> dict:
    """
    Full GHL webhook security dependency:
    1. Verify signature (Ed25519 preferred, HMAC fallback)
    2. Validate timestamp window
    3. Check nonce (replay prevention)
    Returns parsed payload dict.
    """
    raw_body = await request.body()

    # --- Step 1: Signature verification ---
    if x_ghl_signature:
        if not verify_ghl_ed25519(raw_body, x_ghl_signature):
            raise HTTPException(status_code=401, detail="Invalid X-GHL-Signature")
    else:
        # Fall back to HMAC (Custom Workflow Actions or legacy)
        secret = settings.webhook_signing_secrets.get("ghl")
        if not secret:
            raise HTTPException(status_code=500, detail="GHL webhook secret not configured")
        # Use first available signature header value
        sig = x_wh_signature or request.headers.get("X-HighLevel-Signature", "")
        if not sig or not verify_ghl_hmac(raw_body, sig, secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # --- Step 2: Parse payload ---
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # --- Step 3: Timestamp validation ---
    validate_timestamp(payload.get("timestamp"))

    # --- Step 4: Nonce deduplication ---
    webhook_id = payload.get("webhookId")
    if webhook_id:
        await check_and_store_nonce(redis, webhook_id)
    else:
        logger.warning("GHL webhook missing webhookId — cannot deduplicate")

    return payload


# Usage in route:
# @router.post("/webhook")
# async def handle_ghl_webhook(
#     payload: dict = Depends(ghl_webhook_security),
#     db: AsyncSession = Depends(get_db),
# ):
#     ...
```

### Updating the `verify_webhook` Decorator

The existing decorator in `security_framework.py` can be augmented by adding timestamp and nonce checks after successful signature verification:

```python
# Addition to _verify_ghl_signature() or as post-verification step
async def _check_replay_protection(self, request: Request, payload: dict) -> None:
    """Timestamp + nonce check after signature passes."""
    from ghl_real_estate_ai.services.ghl_webhook_security import (
        validate_timestamp, check_and_store_nonce
    )
    validate_timestamp(payload.get("timestamp"))
    webhook_id = payload.get("webhookId")
    if webhook_id and self.redis:
        await check_and_store_nonce(self.redis, webhook_id)
```

---

## Rate Limiting

The existing `SecurityFramework.rate_limit_middleware()` uses Redis sliding windows and is already available. It is not applied to webhook endpoints by default.

### Recommended Limits for GHL Webhook Endpoints

| Endpoint | Recommended Limit | Rationale |
|----------|-------------------|-----------|
| `/webhook` (main) | 120/min per IP | GHL retries on 5xx; legitimate bursts are rare |
| `/tag-webhook` | 60/min per IP | Tag changes are infrequent in normal operation |
| `/initiate-qualification` | 30/min per IP | Qualification is expensive (AI calls) |

### Applying Rate Limiting to Webhook Routes

GHL webhooks originate from GHL's server IPs, not end-user IPs. Rate limiting by IP is most effective when combined with IP allowlisting.

```python
# In the @verify_webhook decorator or as a separate dependency
from ghl_real_estate_ai.services.security_framework import SecurityFramework, RateLimitType

async def ghl_webhook_rate_limit(request: Request):
    security = SecurityFramework()
    await security.rate_limit_middleware(
        request,
        limit=120,
        limit_type=RateLimitType.PER_IP
    )
```

### GHL IP Allowlisting (Defence in Depth)

GHL publishes a set of server IPs for webhook delivery. Rejecting requests from unknown IPs before any cryptographic verification reduces load and eliminates opportunistic scanning:

```python
GHL_WEBHOOK_IPS = {
    "34.68.241.126",
    "34.136.154.106",
    # Add additional IPs from GHL's current published list
}

async def verify_ghl_source_ip(request: Request) -> None:
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if client_ip not in GHL_WEBHOOK_IPS:
        logger.warning(f"GHL webhook from unexpected IP: {client_ip}")
        # Log but do not hard-reject — IPs can change. Signature is the authoritative check.
```

---

## Idempotency

### Why GHL Webhooks Need Idempotency

GHL uses **at-least-once delivery**. It will retry a webhook on 5xx responses, network timeouts, or responses that exceed its timeout window. The same `ContactCreate` or `TagUpdate` event can arrive 2-3 times.

### Two-Tier Idempotency

**Tier 1 — Redis (fast, short TTL)**
Already covered by nonce tracking above. Handles duplicate deliveries within the 10-minute window.

**Tier 2 — PostgreSQL (durable, long TTL)**

```sql
-- Migration: add processed_webhooks table
CREATE TABLE IF NOT EXISTS processed_webhooks (
    id              BIGSERIAL PRIMARY KEY,
    webhook_id      TEXT        NOT NULL,
    event_type      TEXT        NOT NULL,
    contact_id      TEXT,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,
    status          TEXT        NOT NULL DEFAULT 'pending',
    CONSTRAINT uq_webhook_id UNIQUE (webhook_id)
);
CREATE INDEX idx_processed_webhooks_received_at ON processed_webhooks (received_at);
```

```python
# In the webhook handler, before processing business logic:
async def record_webhook(db: AsyncSession, webhook_id: str, event_type: str, contact_id: str) -> bool:
    """
    Returns True if this webhook should be processed (first time seen).
    Returns False if duplicate (already processed).
    Uses PostgreSQL unique constraint as the source of truth.
    """
    from sqlalchemy.exc import IntegrityError
    try:
        record = ProcessedWebhook(
            webhook_id=webhook_id,
            event_type=event_type,
            contact_id=contact_id,
        )
        db.add(record)
        await db.flush()  # Raises IntegrityError on duplicate before commit
        return True
    except IntegrityError:
        await db.rollback()
        logger.info(f"Duplicate webhook skipped: {webhook_id}")
        return False
```

### Async Processing Pattern (Acknowledge First, Process Later)

```python
@router.post("/webhook", response_model=GHLWebhookResponse)
@verify_webhook("ghl")
async def handle_ghl_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()
    payload = json.loads(raw_body)
    webhook_id = payload.get("webhookId", "")
    event_type = payload.get("type", "unknown")

    # Fast idempotency check
    should_process = await record_webhook(db, webhook_id, event_type, payload.get("data", {}).get("id"))
    await db.commit()

    if not should_process:
        # Return 200 immediately — GHL should not retry
        return GHLWebhookResponse(status="duplicate", message="Already processed")

    # Acknowledge to GHL immediately, process in background
    background_tasks.add_task(process_ghl_event, payload, db)
    return GHLWebhookResponse(status="accepted", message="Processing")
```

---

## Code Examples

### Full Verification Stack (Drop-in for security_framework.py Enhancement)

```python
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Optional

from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException, Request


GHL_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAi2HR1srL4o18O8BRa7gVJY7G7bupbN3H9AwJrHCDiOg=
-----END PUBLIC KEY-----"""

REPLAY_WINDOW_SECONDS = 300


def verify_signature_ed25519(body: bytes, sig_b64: str) -> bool:
    pub_key = serialization.load_pem_public_key(GHL_PUBLIC_KEY_PEM)
    try:
        pub_key.verify(base64.b64decode(sig_b64), body)
        return True
    except Exception:
        return False


def verify_signature_hmac(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected) or hmac.compare_digest(signature, secret)


def assert_timestamp_fresh(payload: dict) -> None:
    ts_str: Optional[str] = payload.get("timestamp")
    if not ts_str:
        raise HTTPException(401, "Missing timestamp in webhook payload")
    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    age = abs(time.time() - ts.timestamp())
    if age > REPLAY_WINDOW_SECONDS:
        raise HTTPException(401, f"Webhook expired: {age:.0f}s old (max {REPLAY_WINDOW_SECONDS}s)")


async def assert_nonce_unused(redis, webhook_id: str) -> None:
    if not webhook_id:
        return  # Cannot deduplicate without ID; rely on PostgreSQL tier
    key = f"ghl:wh:{webhook_id}"
    result = await redis.set(key, 1, nx=True, ex=REPLAY_WINDOW_SECONDS * 2)
    if result is None:
        raise HTTPException(409, "Duplicate webhook delivery")
```

### Test Coverage for Security Functions

```python
# tests/unit/test_ghl_webhook_security.py
import pytest
import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock


def test_hmac_accepts_valid_signature():
    secret = "test-secret"
    body = b'{"type":"ContactCreate"}'
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature_hmac(body, sig, secret) is True


def test_hmac_rejects_tampered_body():
    secret = "test-secret"
    body = b'{"type":"ContactCreate"}'
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    tampered = b'{"type":"ContactCreate","injected":true}'
    assert verify_signature_hmac(tampered, sig, secret) is False


def test_timestamp_rejects_old_webhook():
    payload = {"timestamp": "2020-01-01T00:00:00.000Z"}
    with pytest.raises(HTTPException) as exc:
        assert_timestamp_fresh(payload)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_nonce_rejects_duplicate():
    redis = AsyncMock()
    redis.set = AsyncMock(return_value=None)  # None means key already existed
    with pytest.raises(HTTPException) as exc:
        await assert_nonce_unused(redis, "wh_abc123")
    assert exc.value.status_code == 409
```

---

## Common Webhook Security Vulnerabilities

| Vulnerability | Risk | Mitigation |
|---------------|------|------------|
| No signature verification | Critical — any actor can POST fake lead events | Apply `@verify_webhook("ghl")` to every GHL endpoint |
| Timing attack on signature comparison | High — allows signature forgery via timing | Use `hmac.compare_digest()` (already in codebase) |
| Replay attacks | High — same webhook re-fires lead qualification | Timestamp window + Redis nonce + PG unique constraint |
| Body re-parsing after verification | Medium — JSON re-serialization can differ from raw bytes | Always verify against `await request.body()`, not `json.loads()` |
| `GHL_ALLOW_UNSIGNED_WEBHOOKS=True` in prod | Critical — bypasses all verification | Enforce via CI env check; alert on startup if True |
| No rate limiting on webhook endpoints | Medium — DoS via flood | Apply rate limiter; add IP allowlist |
| Silent 200 on error | Medium — GHL stops retrying; events lost silently | Return 5xx for transient failures so GHL retries |
| Missing idempotency | Medium — duplicate lead records, double qualification | Two-tier idempotency (Redis + PostgreSQL) |

---

## Recommendations for EnterpriseHub

### Priority 1 — Immediate (Production Risk)

1. **Add Ed25519 verification path** to `_verify_ghl_signature()`. The current HMAC approach works for Custom Workflow Actions but not Marketplace webhooks. Accept both; prefer Ed25519 when `X-GHL-Signature` is present.

2. **Audit `GHL_ALLOW_UNSIGNED_WEBHOOKS`**: Add a startup assertion that this flag is `False` in production. Log a `CRITICAL` alert if it is `True` on startup.

3. **Verify `initiate-qualification` endpoint is decorated**: Confirm `@verify_webhook("ghl")` is present on line 2383 of `webhook.py` and has not been removed during refactors.

### Priority 2 — High (Replay Attack Surface)

4. **Add timestamp validation** inside `_verify_ghl_signature()` or as a second step in the `verify_webhook` decorator. Parse `payload.get("timestamp")` from the decoded body and reject if outside 300s window.

5. **Add Redis nonce tracking**: Use existing Redis infrastructure (already in `SecurityFramework`) to store `webhookId` with 600s TTL using `SET NX`. This prevents replay within the validation window.

### Priority 3 — Medium (Reliability)

6. **Create `processed_webhooks` PostgreSQL table**: Use existing Alembic migration pipeline. Add `UNIQUE (webhook_id)` constraint. Wire into the 3 main GHL webhook handlers to prevent duplicate business logic execution.

7. **Add rate limiting to webhook routes**: Apply `security.rate_limit_middleware()` at 120/min on `/webhook`, 60/min on `/tag-webhook`, 30/min on `/initiate-qualification`.

8. **Return `5xx` for transient failures, `2xx` only on success**: Review current response codes. GHL will retry on `5xx`; returning `200` on database errors silently drops events.

### Priority 4 — Long-term

9. **Migrate fully to Ed25519 before July 1, 2026**: GHL drops `X-WH-Signature` on that date. Ed25519 verification (`cryptography` library, stdlib `hashlib` not needed) must be production-ready before then.

10. **Write direct unit tests for `verify_webhook_signature()`**: The `COMPREHENSIVE_CODEBASE_SPEC.md` already identifies this as a test gap. Target: `test_ghl_webhook_signature_valid`, `test_ghl_webhook_signature_missing`, `test_ghl_webhook_signature_tampered`, `test_ghl_allow_unsigned_bypasses_in_dev_only`.

---

## Sources

- [Webhook Integration Guide — HighLevel API Marketplace](https://marketplace.gohighlevel.com/docs/webhook/WebhookIntegrationGuide/index.html)
- [App Marketplace Security Update — Webhook Authentication Changelog](https://ideas.gohighlevel.com/changelog/app-marketplace-security-update-webhook-authentication)
- [Webhook Verification — HighLevel Ideas/Voters](https://ideas.gohighlevel.com/apis/p/webhook-verification)
- [Receive Webhooks with Python (FastAPI) — Svix](https://www.svix.com/guides/receiving/receive-webhooks-with-python-fastapi/)
- [Implementing Webhooks with FastAPI and Neon Postgres](https://neon.com/guides/fastapi-webhooks)
- [Preventing Replay Attacks: Timestamps and Nonces in Webhook Handlers](https://dohost.us/index.php/2026/02/15/preventing-replay-attacks-implementing-timestamps-and-nonces-in-webhook-handlers/)
- [Protecting API Requests Using Nonce, Redis, and Time-Based Validation](https://dev.to/raselmahmuddev/protecting-api-requests-using-nonce-redis-and-time-based-validation-11nd)
- [How to Implement Webhook Idempotency — Hookdeck](https://hookdeck.com/webhooks/guides/implement-webhook-idempotency)
- [How to Generate and Verify HMAC Signatures in Python — Authgear](https://www.authgear.com/post/generate-verify-hmac-signatures)
- [Webhook Signature Verification: How to Secure Your Integrations — ApiDog](https://apidog.com/blog/webhook-signature-verification/)
- [How to Secure APIs with HMAC Signing in Python — OneUptime](https://oneuptime.com/blog/post/2026-01-22-hmac-signing-python-api/view)
- [How to Build Webhook Handlers in Python — OneUptime](https://oneuptime.com/blog/post/2026-01-25-webhook-handlers-python/view)
- [Replay Prevention — webhooks.fyi](https://webhooks.fyi/security/replay-prevention)
- [Unable to Verify GoHighLevel Webhook Signature with Public Key — n8n Community](https://community.n8n.io/t/unable-to-verify-gohighlevel-webhook-signature-with-public-key-using-n8n/94396)
