# ADR 0009: Dual-Mode Webhook Signature Verification

## Status

Accepted

## Context

GoHighLevel (GHL) sends webhooks to EnterpriseHub for lead events, tag changes, and contact updates. Without verification, any party that discovers the webhook endpoint can inject arbitrary lead data, trigger bot conversations, or spam the qualification workflow.

GHL supports two webhook signing mechanisms:
- **HMAC-SHA256**: Available to all GHL accounts. The platform signs the request body with a shared secret, included in the `X-GHL-Signature` header.
- **Ed25519**: Available to GHL Marketplace apps only. Asymmetric signing with GHL's private key; the app verifies against GHL's published public key. Stronger security posture since the signing key never leaves GHL's infrastructure.

Two webhook routes (`POST /ghl/webhook` and `POST /ghl/tag-webhook`) handle all lead events. A third (`POST /ghl/initiate-qualification`) handles manual bot activation. All three must be protected; the health check (`GET /ghl/health`) is intentionally unprotected.

An escape hatch for local development is required: developers cannot easily obtain valid GHL signatures in sandbox environments.

## Decision

Implement dual-mode verification in `services/security_framework.py` (`_verify_ghl_signature`):

1. **Ed25519 mode** (activated when `GHL_WEBHOOK_PUBLIC_KEY` is set): Parse the Ed25519 public key from env, verify the request body signature from the `X-GHL-Signature` header. This is the production mode for Marketplace deployments.

2. **HMAC-SHA256 mode** (default fallback): Compute `HMAC-SHA256(secret, body)` using `GHL_WEBHOOK_SECRET`, compare against the `X-GHL-Signature` header using `hmac.compare_digest` (constant-time comparison to prevent timing attacks).

3. **Replay protection**: Verify `X-GHL-Timestamp` header is within a 5-minute window of server time. Requests outside this window are rejected with 401 regardless of signature validity.

4. **Development bypass**: `GHL_ALLOW_UNSIGNED_WEBHOOKS=true` skips verification. The startup check in `api/main.py` prevents this flag from being active when `ENVIRONMENT` matches any production variant (`production`, `prod`, `PRODUCTION`, `PROD`, or any case-insensitive match).

Applied as `@verify_webhook("ghl")` decorator on each protected route. The decorator is not a FastAPI `Depends()` — it wraps the route function directly and locates the `Request` object from the function's arguments.

## Consequences

### Positive
- Ed25519 offers stronger security than HMAC: the signing key never appears in application config
- HMAC mode ensures backward compatibility with non-Marketplace GHL deployments
- Replay protection blocks injection attacks that replay captured valid payloads
- Constant-time comparison prevents timing-based signature oracle attacks
- Development bypass is time-limited: startup guard catches misconfiguration before deployment

### Negative
- The decorator approach (vs. `Depends()`) is non-standard for FastAPI; new route authors must remember to apply the decorator manually. Router-level dependency injection would eliminate this risk.
- The startup guard uses string matching against `ENVIRONMENT` — if a deployment uses a non-standard value (e.g., `"live"`, `"prd"`), the guard will not fire and the bypass flag could reach production silently.
- `SecurityFramework()` is instantiated per request in the decorator (line 704) rather than as an application-level singleton. This adds minor overhead per webhook call.
