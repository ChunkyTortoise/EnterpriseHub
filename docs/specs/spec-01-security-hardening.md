# Spec 01: Security Hardening (P0)

**Agent**: `security-auditor`  
**Estimated scope**: ~15 files modified  
**Priority**: P0 (Critical)  
**Dependencies**: None

---

## Context

Security audit identified 5 critical vulnerabilities in the EnterpriseHub codebase that must be addressed immediately.

---

## 1a. Fix CORS Misconfiguration

### Location
- **File**: `ghl_real_estate_ai/compliance_platform/api/main.py:14-20`

### Problem
`allow_origins=["*"]` combined with `allow_credentials=True` allows any origin to make authenticated requests.

### Fix
Replace wildcard with explicit domain list from environment variable:

```python
import os

CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
if not CORS_ALLOWED_ORIGINS or CORS_ALLOWED_ORIGINS == [""]:
    CORS_ALLOWED_ORIGINS = ["https://yourdomain.com"]  # Safe default

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Acceptance Criteria
- No wildcard origins in any `CORSMiddleware` config across entire codebase
- Environment variable `CORS_ALLOWED_ORIGINS` documented in `.env.example`

---

## 1b. Fix Open Redirect in SSO

### Location
- **File**: `ghl_real_estate_ai/api/routes/enterprise_partnerships.py:189-196`
- **File**: `ghl_real_estate_ai/api/enterprise/auth.py`

### Problem
`redirect_uri` query param accepted without validation, enabling open redirect attacks.

### Fix
Add URL validation against configurable allowlist:

```python
import os
from urllib.parse import urlparse

ALLOWED_REDIRECT_DOMAINS = os.environ.get("ALLOWED_REDIRECT_DOMAINS", "").split(",")

def validate_redirect_uri(redirect_uri: str) -> bool:
    if not redirect_uri:
        return False
    try:
        parsed = urlparse(redirect_uri)
        return parsed.netloc in ALLOWED_REDIRECT_DOMAINS
    except Exception:
        return False

# In route handler:
if not validate_redirect_uri(redirect_uri):
    raise HTTPException(status_code=400, detail="Invalid redirect URI")
```

### Acceptance Criteria
- All `redirect_uri` params validated against allowlist
- Test covers malicious redirect attempt (e.g., `redirect_uri=https://evil.com`)
- Environment variable `ALLOWED_REDIRECT_DOMAINS` documented

---

## 1c. Fix Input Validation Bypass

### Location
- **File**: `ghl_real_estate_ai/api/middleware/input_validation.py:231-253`

### Problem
SQL injection and XSS validation disabled for conversation endpoints via exemption list.

### Fix
1. Keep validation enabled for conversation params
2. Use parameterized queries downstream (verify no raw SQL string concatenation)
3. Add HTML sanitization for rendered conversation content

```python
# Remove conversation endpoints from exemption list
# Instead, use appropriate validation that allows natural language but prevents injection

def sanitize_conversation_input(text: str) -> str:
    """Sanitize conversation input while preserving natural language."""
    import html
    # Escape HTML entities to prevent XSS
    return html.escape(text)
```

### Acceptance Criteria
- No validation bypasses in exemption list
- Conversation endpoints still accept natural language input
- Add integration test verifying SQL injection attempts are blocked

---

## 1d. Fix Password Truncation

### Location
- **File**: `ghl_real_estate_ai/api/middleware/enhanced_auth.py:383-389`

### Problem
Passwords > 72 bytes silently truncated due to bcrypt limitation, leading to potential security weakness and user confusion.

### Fix
Return HTTP 422 with clear error message when password exceeds 72 characters:

```python
MAX_PASSWORD_LENGTH = 72

def validate_password_length(password: str) -> None:
    if len(password.encode('utf-8')) > MAX_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"Password must be {MAX_PASSWORD_LENGTH} characters or fewer"
        )

# Call before hashing
validate_password_length(password)
```

### Acceptance Criteria
- API returns 422 error for passwords > 72 characters
- Clear error message explains the limitation
- Existing auth tests still pass

---

## 1e. Remove Hardcoded Test Secrets

### Location
- **File**: `ghl_real_estate_ai/compliance_platform/tests/test_multitenancy.py`
- **File**: `ghl_real_estate_ai/compliance_platform/tests/test_api.py`

### Problem
Hardcoded secrets in test files (e.g., `SECRET_KEY = "test-secret-key"`).

### Fix
Replace hardcoded secrets with pytest fixtures using environment variables:

```python
import os
import pytest

@pytest.fixture
def test_secret_key():
    return os.environ.get("TEST_SECRET_KEY", "test-secret-key-for-ci")

@pytest.fixture
def test_api_key():
    return os.environ.get("TEST_API_KEY", "test-api-key-for-ci")
```

### Acceptance Criteria
- `grep -r "SECRET_KEY.*=.*\"" tests/` returns zero matches
- Tests still pass with default values in CI

---

## Verification Commands

```bash
# CORS check - should return 0 results
grep -rn "allow_origins.*\*" ghl_real_estate_ai/ --include="*.py"

# Open redirect check - should have validation
grep -rn "redirect_uri.*Query" ghl_real_estate_ai/ --include="*.py"

# Secrets check - should return 0 results
grep -rn "SECRET_KEY.*=.*\".*\"" tests/ --include="*.py"

# Run security-related tests
pytest tests/ -k "security or auth or sso" -v

# Full test suite to verify no regressions
pytest tests/ -x --timeout=60
```

---

## Files to Modify

| File | Change Type |
|------|-------------|
| `ghl_real_estate_ai/compliance_platform/api/main.py` | CORS fix |
| `ghl_real_estate_ai/api/routes/enterprise_partnerships.py` | Redirect validation |
| `ghl_real_estate_ai/api/enterprise/auth.py` | Redirect validation |
| `ghl_real_estate_ai/api/middleware/input_validation.py` | Remove bypass |
| `ghl_real_estate_ai/api/middleware/enhanced_auth.py` | Password validation |
| `ghl_real_estate_ai/compliance_platform/tests/test_multitenancy.py` | Remove secrets |
| `ghl_real_estate_ai/compliance_platform/tests/test_api.py` | Remove secrets |
| `.env.example` | Document new env vars |
