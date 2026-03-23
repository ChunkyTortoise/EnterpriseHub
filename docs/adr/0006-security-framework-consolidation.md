# ADR 0006: Security Framework Consolidation

## Status

Accepted (partial — canonical system identified; full consolidation in progress)

## Context

EnterpriseHub grew three independent auth implementations across different development phases:

1. **`api/middleware/jwt_auth.py` (JWTAuth class)** — The primary system. JWT access tokens (30-min expiry), refresh tokens (7-day), bcrypt password hashing, JTI revocation tracking via Redis. Secret loaded from `JWT_SECRET_KEY` env var; raises `ValueError` at import if missing or under 32 characters. Used by all billing and user-facing routes via `Depends(get_current_user)`.

2. **`services/auth_service.py` (AuthService class)** — An older file-based system from the initial prototype. Uses HMAC-SHA256 for password hashing with a static salt derived from the application secret key (not per-user salts). Stores the JWT secret in `data/.jwt_secret` instead of environment variables. Not wired into production routes.

3. **`services/security_framework.py` (SecurityFramework class)** — A third implementation focused on webhook signature verification (GHL, Twilio, SendGrid, Vapi, Apollo) and Redis-backed rate limiting. Its token generation logic overlaps with JWTAuth but is only used for webhook auth, not user sessions.

Having three implementations creates several risks:
- Divergent logic for what should be identical token validation
- `auth_service.py`'s static password salt pattern is weaker than bcrypt with per-user salts (OWASP recommendation)
- Developers adding new routes may import from the wrong auth module
- `SecurityFramework` creates a new instance per request (line 704, `security_framework.py`), which is wasteful and prevents singleton-level state

## Decision

**Designate `api/middleware/jwt_auth.py` as the single canonical auth system.** All user authentication must go through `get_current_user` (a FastAPI `Depends()`). No route may import from `auth_service.py` for authentication.

Specific decisions:
- `auth_service.py` is deprecated. It remains in the codebase only for the data migration helper (`seed_historical_data`) until that utility is extracted.
- `SecurityFramework` retains responsibility for webhook signature verification only. Its token methods are dead code and will be removed in a follow-up.
- Webhook verification is refactored to a proper FastAPI dependency (`Depends(verify_ghl_webhook)`) rather than a custom decorator that searches `args/kwargs` for the `Request` object. This ensures all new routes on the webhook router inherit verification automatically.
- The `GHL_ALLOW_UNSIGNED_WEBHOOKS` startup guard performs a case-insensitive check on the `ENVIRONMENT` variable (not just `"production"` and `"prod"`).

## Consequences

### Positive
- Single authoritative source for auth logic — new routes only need to know about `jwt_auth.py`
- Eliminates the static-salt password hashing vulnerability in `auth_service.py`
- Router-level `dependencies=` for webhook routes prevents future auth bypass through missed decorator
- Webhook bypass guard handles case variations (`PRODUCTION`, `Production`, `prod`)

### Negative
- Migration requires auditing all existing imports of `auth_service.py` before removing
- Extracting the data migration utility from `auth_service.py` adds short-term work
- The decorator-to-dependency refactor for webhook routes requires updating route function signatures
