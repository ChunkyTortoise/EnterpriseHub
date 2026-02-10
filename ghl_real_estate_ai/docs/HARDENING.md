# Production Hardening Recommendations
## GHL Real Estate AI - Multi-Tenant Security Guide

**Document Version:** 1.0
**Date:** January 4, 2026
**Author:** Agent B3 - Security & Multi-Tenant Testing Specialist
**Status:** Production Implementation Guide

---

## Table of Contents

1. [Critical Pre-Launch Requirements](#1-critical-pre-launch-requirements)
2. [API Key Encryption Implementation](#2-api-key-encryption-implementation)
3. [Webhook Security Hardening](#3-webhook-security-hardening)
4. [Rate Limiting Implementation](#4-rate-limiting-implementation)
5. [Analytics Dashboard Authentication](#5-analytics-dashboard-authentication)
6. [PII Detection and Redaction](#6-pii-detection-and-redaction)
7. [GDPR Compliance Implementation](#7-gdpr-compliance-implementation)
8. [Audit Logging Setup](#8-audit-logging-setup)
9. [Environment Security](#9-environment-security)
10. [Monitoring and Alerting](#10-monitoring-and-alerting)

---

## 1. Critical Pre-Launch Requirements

### Priority 0 (MUST FIX BEFORE PRODUCTION)

These items present immediate security risks and MUST be addressed before deploying to production with real customer data.

#### 1.1 Encrypt API Keys at Rest

**Risk Level:** CRITICAL
**Estimated Time:** 2-4 hours
**Implementation Complexity:** Medium

**Current State:**
- Tenant API keys stored as plaintext JSON
- File: `data/tenants/{location_id}.json`
- Anyone with file system access can read all API keys

**Solution:**

<details>
<summary><strong>Step-by-Step Implementation</strong></summary>

**Step 1: Install cryptography library**
```bash
pip install cryptography
```

**Step 2: Generate and store encryption key**
```bash
# Generate a new encryption key (do this ONCE)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to Railway environment variables:
# TENANT_ENCRYPTION_KEY=<generated_key_here>
```

**Step 3: Create encrypted tenant service**

Create file: `services/secure_tenant_service.py`

```python
"""
Secure Tenant Service with Encryption.
Replaces tenant_service.py for production use.
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet

from ghl_utils.config import settings
from ghl_utils.logger import get_logger

logger = get_logger(__name__)


class SecureTenantService:
    """
    Secure tenant service with encrypted API key storage.
    """

    def __init__(self):
        """Initialize secure tenant service."""
        self.tenants_dir = Path("data/tenants")
        self.tenants_dir.mkdir(parents=True, exist_ok=True)

        # Load encryption key from environment
        encryption_key = os.getenv("TENANT_ENCRYPTION_KEY")
        if not encryption_key:
            raise ValueError(
                "TENANT_ENCRYPTION_KEY environment variable not set. "
                "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        self.cipher = Fernet(encryption_key.encode())
        logger.info("Secure tenant service initialized with encryption")

    def _encrypt(self, plaintext: str) -> str:
        """Encrypt a string value."""
        return self.cipher.encrypt(plaintext.encode()).decode()

    def _decrypt(self, ciphertext: str) -> str:
        """Decrypt a string value."""
        try:
            return self.cipher.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            raise ValueError("Invalid or corrupted encrypted data")

    def _get_file_path(self, location_id: str) -> Path:
        """Get file path for a location's tenant info."""
        # Sanitize location_id to prevent path traversal
        if not location_id or not location_id.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Invalid location_id format: {location_id}")
        return self.tenants_dir / f"{location_id}.json"

    async def get_tenant_config(self, location_id: str) -> Dict[str, Any]:
        """
        Retrieve and decrypt configuration for a tenant.
        """
        file_path = self._get_file_path(location_id)

        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    encrypted_config = json.load(f)

                # Decrypt sensitive fields
                decrypted_config = {
                    "location_id": encrypted_config["location_id"],
                    "anthropic_api_key": self._decrypt(encrypted_config["anthropic_api_key_encrypted"]),
                    "ghl_api_key": self._decrypt(encrypted_config["ghl_api_key_encrypted"]),
                    "ghl_calendar_id": encrypted_config.get("ghl_calendar_id"),
                    "updated_at": encrypted_config.get("updated_at")
                }

                logger.info(f"Retrieved and decrypted config for {location_id}")
                return decrypted_config

            except Exception as e:
                logger.error(f"Failed to read/decrypt tenant config for {location_id}: {e}")
                raise

        # Fallback logic (same as original)
        if location_id == settings.ghl_location_id:
            return {
                "location_id": settings.ghl_location_id,
                "anthropic_api_key": settings.anthropic_api_key,
                "ghl_api_key": settings.ghl_api_key
            }

        if settings.ghl_agency_api_key:
            logger.info(f"Using Agency Master Key for location {location_id}")
            return {
                "location_id": location_id,
                "anthropic_api_key": settings.anthropic_api_key,
                "ghl_api_key": settings.ghl_agency_api_key,
                "is_agency_scoped": True
            }

        return {}

    async def save_tenant_config(
        self,
        location_id: str,
        anthropic_api_key: str,
        ghl_api_key: str,
        ghl_calendar_id: Optional[str] = None
    ) -> None:
        """Encrypt and save tenant configuration."""
        # Encrypt sensitive fields
        encrypted_config = {
            "location_id": location_id,
            "anthropic_api_key_encrypted": self._encrypt(anthropic_api_key),
            "ghl_api_key_encrypted": self._encrypt(ghl_api_key),
            "ghl_calendar_id": ghl_calendar_id,
            "updated_at": datetime.utcnow().isoformat(),
            "encryption_version": "v1"  # For future key rotation
        }

        file_path = self._get_file_path(location_id)

        # Set restrictive file permissions (owner read/write only)
        import os
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600  # rw------- (owner only)

        fd = os.open(file_path, flags, mode)
        with os.fdopen(fd, 'w') as f:
            json.dump(encrypted_config, f, indent=2)

        logger.info(f"Saved encrypted tenant config for {location_id}")
```

**Step 4: Update all imports**

Find all references to `TenantService` and replace:

```python
# Old
from services.tenant_service import TenantService

# New
from services.secure_tenant_service import SecureTenantService as TenantService
```

**Step 5: Migrate existing tenant data**

Create migration script: `scripts/migrate_tenant_encryption.py`

```python
"""
Migrate existing tenant configs to encrypted format.
RUN THIS ONCE BEFORE DEPLOYING SECURE VERSION.
"""
import json
import os
from pathlib import Path
from cryptography.fernet import Fernet

# Load encryption key
encryption_key = os.getenv("TENANT_ENCRYPTION_KEY")
if not encryption_key:
    print("ERROR: TENANT_ENCRYPTION_KEY not set")
    exit(1)

cipher = Fernet(encryption_key.encode())

tenants_dir = Path("data/tenants")

for tenant_file in tenants_dir.glob("*.json"):
    if tenant_file.name == "agency_master.json":
        continue  # Skip agency master for now

    print(f"Migrating {tenant_file.name}...")

    with open(tenant_file, "r") as f:
        old_config = json.load(f)

    # Check if already encrypted
    if "anthropic_api_key_encrypted" in old_config:
        print(f"  Already encrypted, skipping")
        continue

    # Encrypt API keys
    new_config = {
        "location_id": old_config["location_id"],
        "anthropic_api_key_encrypted": cipher.encrypt(old_config["anthropic_api_key"].encode()).decode(),
        "ghl_api_key_encrypted": cipher.encrypt(old_config["ghl_api_key"].encode()).decode(),
        "ghl_calendar_id": old_config.get("ghl_calendar_id"),
        "updated_at": old_config.get("updated_at"),
        "encryption_version": "v1"
    }

    # Backup original
    backup_file = tenant_file.with_suffix(".json.backup")
    tenant_file.rename(backup_file)

    # Write encrypted version
    with open(tenant_file, "w") as f:
        json.dump(new_config, f, indent=2)

    print(f"  Migrated successfully (backup: {backup_file.name})")

print("\nMigration complete!")
```

Run migration:
```bash
export TENANT_ENCRYPTION_KEY="<your_key>"
python scripts/migrate_tenant_encryption.py
```

</details>

**Testing:**
```bash
pytest tests/test_security_multitenant.py::TestEncryptionAtRest -v
```

**Rollback Plan:**
Restore `.json.backup` files if migration fails.

---

#### 1.2 Webhook Signature Verification

**Risk Level:** CRITICAL
**Estimated Time:** 1-2 hours
**Implementation Complexity:** Low

**Current State:**
- Webhooks accepted without signature verification
- Anyone with endpoint URL can send fake webhooks

**Solution:**

<details>
<summary><strong>Implementation Code</strong></summary>

**Step 1: Update webhook handler**

Edit `api/routes/webhook.py`:

```python
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Request
import hmac
import hashlib
from hmac import compare_digest

@router.post("/webhook", response_model=GHLWebhookResponse)
async def handle_ghl_webhook(
    request: Request,  # ADD THIS
    background_tasks: BackgroundTasks
):
    """
    Handle incoming webhook from GoHighLevel with signature verification.
    """
    # STEP 1: Verify webhook signature BEFORE parsing body
    if not settings.ghl_webhook_secret:
        logger.warning("GHL_WEBHOOK_SECRET not set - webhooks not verified!")
        # In production, reject if not set:
        # raise HTTPException(status_code=500, detail="Webhook verification not configured")

    if settings.ghl_webhook_secret:
        # Get signature from header
        signature_header = request.headers.get("X-GHL-Signature") or request.headers.get("X-Webhook-Signature")

        if not signature_header:
            logger.warning(f"Webhook received without signature from {request.client.host}")
            raise HTTPException(
                status_code=401,
                detail="Missing webhook signature header"
            )

        # Get raw body (must verify against raw bytes, not parsed JSON)
        body_bytes = await request.body()

        # Calculate expected signature
        expected_signature = hmac.new(
            settings.ghl_webhook_secret.encode(),
            body_bytes,
            hashlib.sha256
        ).hexdigest()

        # Compare signatures (constant-time to prevent timing attacks)
        if not compare_digest(signature_header, expected_signature):
            logger.error(
                f"Invalid webhook signature from {request.client.host}",
                extra={
                    "ip": request.client.host,
                    "received_signature": signature_header[:8] + "...",  # Log prefix only
                    "body_size": len(body_bytes)
                }
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )

        logger.info("Webhook signature verified successfully")

    # STEP 2: Now parse and validate the event
    import json
    try:
        body_json = json.loads(body_bytes.decode())
        event = GHLWebhookEvent(**body_json)
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    # Continue with normal processing...
    contact_id = event.contact_id
    location_id = event.location_id
    # ... rest of existing code
```

**Step 2: Add webhook secret to environment**

```bash
# In Railway or .env file:
GHL_WEBHOOK_SECRET=your_secret_key_from_ghl_dashboard
```

**Step 3: Configure in GHL**

1. Log into GoHighLevel
2. Navigate to Settings > API & Webhooks
3. Edit webhook configuration
4. Set signing secret
5. Choose HMAC-SHA256 algorithm
6. Copy secret to environment variable

</details>

**Testing:**
```bash
# Test with valid signature
curl -X POST http://localhost:8000/ghl/webhook \
  -H "Content-Type: application/json" \
  -H "X-GHL-Signature: $(echo -n '{"contact_id":"test"}' | openssl dgst -sha256 -hmac 'your_secret' -binary | xxd -p)" \
  -d '{"contact_id":"test",...}'

# Test without signature (should fail)
curl -X POST http://localhost:8000/ghl/webhook \
  -H "Content-Type: application/json" \
  -d '{"contact_id":"test",...}'
```

---

#### 1.3 Rate Limiting

**Risk Level:** HIGH
**Estimated Time:** 2-3 hours
**Implementation Complexity:** Medium

**Current State:**
- No rate limiting on API endpoints
- Vulnerable to DoS attacks
- Could rack up unlimited AI API costs

**Solution:**

<details>
<summary><strong>Implementation with SlowAPI</strong></summary>

**Step 1: Install dependencies**
```bash
pip install slowapi
```

**Step 2: Create rate limiter middleware**

Create file: `api/middleware/rate_limiter.py`

```python
"""
Rate limiting middleware for GHL Real Estate AI.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from typing import Callable

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)


def get_tenant_id(request: Request) -> str:
    """
    Extract tenant ID from request for tenant-based rate limiting.
    """
    # Try to get from webhook payload
    if request.url.path == "/ghl/webhook":
        # Parse body to get location_id
        # Note: This is called before body is consumed, so we peek at it
        try:
            import json
            body = request.state._body  # Set by middleware
            data = json.loads(body)
            return f"tenant_{data.get('location_id', 'unknown')}"
        except Exception:
            pass

    # Fallback to IP-based
    return get_remote_address(request)


def tenant_rate_limiter(limit: str) -> Callable:
    """
    Rate limiter that uses tenant ID instead of IP.

    Usage:
        @tenant_rate_limiter("100/minute")
        async def my_endpoint(...):
            ...
    """
    return limiter.limit(limit, key_func=get_tenant_id)
```

**Step 3: Apply to webhook endpoint**

Edit `api/routes/webhook.py`:

```python
from api.middleware.rate_limiter import limiter, tenant_rate_limiter

@router.post("/webhook", response_model=GHLWebhookResponse)
@limiter.limit("120/minute")  # Per IP
@tenant_rate_limiter("100/minute")  # Per tenant
async def handle_ghl_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    # ... existing code
```

**Step 4: Add to FastAPI app**

Edit `api/main.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

app = FastAPI(title=settings.app_name, version=settings.version)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ... rest of app setup
```

**Step 5: Configure tier-based limits**

Create `config/rate_limits.py`:

```python
"""
Tenant tier rate limits configuration.
"""

RATE_LIMITS = {
    "starter": {
        "webhooks_per_minute": 60,
        "webhooks_per_hour": 1000,
        "api_calls_per_minute": 30,
    },
    "professional": {
        "webhooks_per_minute": 120,
        "webhooks_per_hour": 5000,
        "api_calls_per_minute": 100,
    },
    "enterprise": {
        "webhooks_per_minute": 300,
        "webhooks_per_hour": 20000,
        "api_calls_per_minute": 500,
    }
}


def get_tenant_rate_limit(tenant_id: str, resource: str) -> str:
    """
    Get rate limit string for a tenant.

    Args:
        tenant_id: Tenant location ID
        resource: Resource type (webhooks, api_calls, etc.)

    Returns:
        Rate limit string (e.g., "100/minute")
    """
    # In production, look up tenant tier from database
    # For now, use professional as default
    tier = "professional"

    limits = RATE_LIMITS.get(tier, RATE_LIMITS["starter"])

    if resource == "webhooks":
        return f"{limits['webhooks_per_minute']}/minute"
    elif resource == "api_calls":
        return f"{limits['api_calls_per_minute']}/minute"

    return "60/minute"  # Default fallback
```

</details>

**Testing:**
```bash
# Test rate limiting
for i in {1..150}; do
  curl -X POST http://localhost:8000/ghl/webhook \
    -H "Content-Type: application/json" \
    -d '{"contact_id":"test",...}'
  echo "Request $i"
done

# Should see 429 Too Many Requests after limit reached
```

---

#### 1.4 Analytics Dashboard Authentication

**Risk Level:** HIGH
**Estimated Time:** 3-4 hours
**Implementation Complexity:** Medium

**Current State:**
- Streamlit dashboard has no authentication
- Anyone with URL can view all tenant data

**Solution:**

<details>
<summary><strong>Streamlit Authenticator Implementation</strong></summary>

**Step 1: Install dependencies**
```bash
pip install streamlit-authenticator PyJWT
```

**Step 2: Create authentication config**

Create `streamlit_demo/config/auth.yaml`:

```yaml
credentials:
  usernames:
    admin:
      email: admin@example.com
      name: Admin User
      password: $2b$12$hashed_password_here  # Use bcrypt
      roles:
        - admin
      authorized_tenants:
        - "*"  # All tenants

    agent_john:
      email: john@realestate.com
      name: John Agent
      password: $2b$12$hashed_password_here
      roles:
        - agent
      authorized_tenants:
        - loc_123

    analyst_jane:
      email: jane@analytics.com
      name: Jane Analyst
      password: $2b$12$hashed_password_here
      roles:
        - analyst
      authorized_tenants:
        - loc_123
        - loc_456

cookie:
  expiry_days: 1
  key: some_signature_key_change_this  # Change in production
  name: ghl_ai_dashboard_auth

preauthorized:
  emails: []
```

**Step 3: Generate password hashes**

Create `scripts/generate_password_hash.py`:

```python
"""Generate bcrypt password hash for Streamlit auth."""
import bcrypt
import sys

if len(sys.argv) != 2:
    print("Usage: python generate_password_hash.py <password>")
    sys.exit(1)

password = sys.argv[1]
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(f"\nHashed password:\n{hashed.decode()}\n")
print("Add this to config/auth.yaml under the user's password field")
```

Run:
```bash
python scripts/generate_password_hash.py "MySecurePassword123"
```

**Step 4: Add authentication to dashboard**

Edit `streamlit_demo/analytics.py` (add at top, before page config):

```python
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path

# Load authentication config
config_path = Path(__file__).parent / "config" / "auth.yaml"
with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Login form
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('Username/password is incorrect')
    st.stop()

elif authentication_status == None:
    st.warning('Please enter your username and password')
    st.stop()

elif authentication_status:
    # User is authenticated
    st.sidebar.success(f'Welcome {name}!')

    # Add logout button
    authenticator.logout('Logout', 'sidebar')

    # Get user's authorized tenants
    user_config = config['credentials']['usernames'][username]
    authorized_tenants = user_config.get('authorized_tenants', [])
    user_roles = user_config.get('roles', [])

    # Filter tenant list based on authorization
    if "*" not in authorized_tenants and "admin" not in user_roles:
        # Restrict tenant selector
        original_tenant_options = ["All Tenants"] + [t["name"] for t in tenants]
        allowed_tenant_objects = [t for t in tenants if t["location_id"] in authorized_tenants]
        tenant_options = ["All Tenants"] if "All Tenants" in authorized_tenants else []
        tenant_options += [t["name"] for t in allowed_tenant_objects]

        st.sidebar.header("Filters")
        selected_tenant = st.sidebar.selectbox("Select Tenant", tenant_options)

        # Verify authorization for selected tenant
        if selected_tenant != "All Tenants":
            selected_tenant_id = next((t["location_id"] for t in tenants if t["name"] == selected_tenant), None)
            if selected_tenant_id not in authorized_tenants:
                st.error("You are not authorized to view this tenant")
                st.stop()
    else:
        # Admin or full access user - show all tenants
        pass

    # Continue with rest of dashboard...
    st.title("Dashboard Analytics Dashboard")
    # ... existing code
```

**Step 5: Protect with environment variable (production)**

For production, don't commit `auth.yaml`. Instead:

```python
# Load credentials from environment
import os
import json

credentials = json.loads(os.getenv("DASHBOARD_CREDENTIALS", "{}"))
cookie_config = json.loads(os.getenv("DASHBOARD_COOKIE_CONFIG", "{}"))

config = {
    "credentials": credentials,
    "cookie": cookie_config
}
```

In Railway:
```bash
DASHBOARD_CREDENTIALS='{"usernames":{"admin":{"email":"admin@example.com",...}}}'
DASHBOARD_COOKIE_CONFIG='{"name":"ghl_auth","key":"secret","expiry_days":1}'
```

</details>

**Testing:**
1. Access dashboard: `streamlit run streamlit_demo/analytics.py`
2. Try accessing without login (should be blocked)
3. Login with valid credentials
4. Try accessing unauthorized tenant (should be blocked)

---

### Priority 1 (Fix Within 1 Week)

These items don't pose immediate danger but should be addressed quickly.

#### 1.5 Input Validation and Sanitization

See full implementation in `SECURITY_AUDIT_MULTITENANT.md` Section 4.1.

Quick fix for webhook handler:

```python
from pydantic import validator, constr

class GHLWebhookEvent(BaseModel):
    contact_id: constr(min_length=1, max_length=50)
    location_id: constr(min_length=1, max_length=50)

    @validator('message')
    def validate_message_size(cls, v):
        if len(v.body) > 10000:  # 10KB max
            raise ValueError("Message body exceeds size limit")
        return v
```

---

## 2. API Key Encryption Implementation

See Section 1.1 above for complete implementation.

---

## 3. Webhook Security Hardening

See Section 1.2 above for signature verification.

Additional hardening:

### 3.1 Replay Attack Prevention

```python
import time
from cachetools import TTLCache

# Store recent webhook IDs (expires after 5 minutes)
webhook_nonce_cache = TTLCache(maxsize=10000, ttl=300)

@router.post("/webhook")
async def handle_ghl_webhook(request: Request, ...):
    # Get webhook ID or generate nonce
    webhook_id = request.headers.get("X-GHL-Webhook-ID")

    if webhook_id:
        if webhook_id in webhook_nonce_cache:
            logger.warning(f"Duplicate webhook detected: {webhook_id}")
            raise HTTPException(status_code=409, detail="Duplicate webhook")

        webhook_nonce_cache[webhook_id] = time.time()
```

### 3.2 Timestamp Validation

```python
import time
from datetime import datetime

@router.post("/webhook")
async def handle_ghl_webhook(request: Request, ...):
    # Check webhook timestamp
    timestamp_header = request.headers.get("X-GHL-Timestamp")

    if timestamp_header:
        webhook_time = int(timestamp_header)
        current_time = int(time.time())
        age_seconds = current_time - webhook_time

        if age_seconds > 300:  # 5 minutes
            logger.warning(f"Webhook too old: {age_seconds}s")
            raise HTTPException(status_code=400, detail="Webhook expired")
```

---

## 4. Rate Limiting Implementation

See Section 1.3 above for complete SlowAPI implementation.

---

## 5. Analytics Dashboard Authentication

See Section 1.4 above for Streamlit authentication.

---

## 6. PII Detection and Redaction

### 6.1 Automatic PII Detection

Create `services/pii_detector.py`:

```python
"""
PII Detection and Redaction Service.
"""
import re
from typing import Dict, List

class PIIDetector:
    """Detect and redact personally identifiable information."""

    PII_PATTERNS = {
        'ssn': {
            'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
            'replacement': '[REDACTED_SSN]',
            'description': 'Social Security Number'
        },
        'credit_card': {
            'pattern': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            'replacement': '[REDACTED_CREDIT_CARD]',
            'description': 'Credit Card Number'
        },
        'email': {
            'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'replacement': '[REDACTED_EMAIL]',
            'description': 'Email Address'
        },
        'phone': {
            'pattern': r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            'replacement': '[REDACTED_PHONE]',
            'description': 'Phone Number'
        }
    }

    @classmethod
    def detect(cls, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text.

        Args:
            text: Text to scan for PII

        Returns:
            Dict mapping PII type to list of found instances
        """
        findings = {}

        for pii_type, config in cls.PII_PATTERNS.items():
            matches = re.findall(config['pattern'], text)
            if matches:
                findings[pii_type] = matches

        return findings

    @classmethod
    def redact(cls, text: str, redact_email: bool = False) -> str:
        """
        Redact PII from text.

        Args:
            text: Text to redact PII from
            redact_email: Whether to redact email addresses (optional)

        Returns:
            Text with PII redacted
        """
        redacted = text

        for pii_type, config in cls.PII_PATTERNS.items():
            # Skip email if not requested
            if pii_type == 'email' and not redact_email:
                continue

            redacted = re.sub(config['pattern'], config['replacement'], redacted)

        return redacted

    @classmethod
    def has_pii(cls, text: str) -> bool:
        """Check if text contains any PII."""
        return bool(cls.detect(text))
```

### 6.2 Integrate with Memory Service

Edit `services/memory_service.py`:

```python
from services.pii_detector import PIIDetector

class MemoryService:
    async def save_context(
        self,
        contact_id: str,
        context: Dict[str, Any],
        location_id: Optional[str] = None,
        redact_pii: bool = True  # NEW PARAMETER
    ) -> None:
        """Save conversation context with optional PII redaction."""

        if redact_pii:
            # Redact PII from conversation history
            if "conversation_history" in context:
                for message in context["conversation_history"]:
                    if "content" in message:
                        message["content"] = PIIDetector.redact(message["content"])

            # Check for PII in other fields
            for key, value in context.items():
                if isinstance(value, str):
                    if PIIDetector.has_pii(value):
                        logger.warning(
                            f"PII detected in field '{key}' for contact {contact_id}",
                            extra={"contact_id": contact_id, "field": key}
                        )
                        context[key] = PIIDetector.redact(value)

        # Continue with normal save
        context["updated_at"] = datetime.utcnow().isoformat()
        # ... rest of existing code
```

---

## 7. GDPR Compliance Implementation

### 7.1 Right to Access (Article 15)

Create `api/routes/gdpr.py`:

```python
"""
GDPR Compliance API Endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


class DataAccessRequest(BaseModel):
    """Request to access all data for a contact."""
    contact_id: str
    location_id: str
    email: str  # For verification


class DataDeletionRequest(BaseModel):
    """Request to delete all data for a contact."""
    contact_id: str
    location_id: str
    email: str
    confirmation_code: str  # Sent via email


@router.post("/data-access-request")
async def request_data_access(request: DataAccessRequest):
    """
    GDPR Article 15: Right to Access.

    Allows contacts to request all their data.
    """
    # Verify contact email matches
    contact_info = await ghl_client.get_contact(request.contact_id)

    if contact_info.get("email") != request.email:
        raise HTTPException(status_code=403, detail="Email verification failed")

    # Collect all data
    data_export = {
        "request_id": generate_uuid(),
        "contact_id": request.contact_id,
        "request_date": datetime.utcnow().isoformat(),
        "data": {
            "personal_info": {
                "name": f"{contact_info['firstName']} {contact_info['lastName']}",
                "email": contact_info["email"],
                "phone": contact_info["phone"]
            },
            "conversations": await memory_service.get_all_conversations(
                request.contact_id, request.location_id
            ),
            "lead_scores": await analytics_service.get_lead_score_history(
                request.contact_id, request.location_id
            ),
            "tags": contact_info.get("tags", []),
            "data_processing_purposes": [
                "Lead qualification and scoring",
                "Automated conversation management",
                "Real estate property recommendations"
            ]
        }
    }

    # Send email with data export
    await send_data_export_email(request.email, data_export)

    return {
        "message": "Data export sent to your email",
        "request_id": data_export["request_id"]
    }


@router.post("/data-deletion-request")
async def request_data_deletion(request: DataDeletionRequest):
    """
    GDPR Article 17: Right to Erasure.

    Allows contacts to request deletion of all their data.
    """
    # Verify confirmation code (sent via email in first step)
    if not await verify_deletion_code(request.contact_id, request.confirmation_code):
        raise HTTPException(status_code=403, detail="Invalid confirmation code")

    # Delete all data
    await memory_service.delete_all_context(request.contact_id, request.location_id)
    await rag_engine.delete_documents(filter={"contact_id": request.contact_id})
    await analytics_service.delete_contact_data(request.contact_id, request.location_id)

    # Log deletion for audit
    logger.info(
        f"GDPR deletion completed for contact {request.contact_id}",
        extra={
            "contact_id": request.contact_id,
            "location_id": request.location_id,
            "deletion_type": "gdpr_erasure"
        }
    )

    return {
        "message": "All your data has been permanently deleted",
        "deletion_date": datetime.utcnow().isoformat()
    }
```

---

## 8. Audit Logging Setup

### 8.1 Audit Logger

Create `services/audit_logger.py`:

```python
"""
Audit logging for compliance and security.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class AuditLogger:
    """Structured audit logging for critical actions."""

    def __init__(self):
        self.audit_log_dir = Path("data/audit_logs")
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        event_type: str,
        user: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ):
        """
        Log an auditable event.

        Args:
            event_type: Type of event (admin_action, security_event, etc.)
            user: User who performed the action
            resource_type: Type of resource (tenant, contact, etc.)
            resource_id: ID of the resource
            action: Action performed (create, update, delete, etc.)
            success: Whether action succeeded
            details: Additional details about the action
            ip_address: IP address of the user
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user": user,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "success": success,
            "details": details or {},
            "ip_address": ip_address
        }

        # Write to daily log file
        log_file = self.audit_log_dir / f"audit_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"

        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def log_admin_action(self, user: str, action: str, **kwargs):
        """Log an administrative action."""
        self.log_event(
            event_type="admin_action",
            user=user,
            action=action,
            **kwargs
        )

    def log_security_event(self, event_type: str, **kwargs):
        """Log a security event."""
        self.log_event(
            event_type="security_event",
            user="system",
            action=event_type,
            **kwargs
        )


# Global instance
audit_logger = AuditLogger()
```

### 8.2 Integrate with Critical Endpoints

```python
from services.audit_logger import audit_logger

@router.post("/onboard-tenant")
async def onboard_tenant(request: Request, tenant_data: TenantData):
    """Onboard new tenant with audit logging."""

    try:
        # Create tenant
        await tenant_service.save_tenant_config(...)

        # Log success
        audit_logger.log_admin_action(
            user=request.user.email,  # From auth middleware
            action="tenant_created",
            resource_type="tenant",
            resource_id=tenant_data.location_id,
            success=True,
            details={"tenant_name": tenant_data.name},
            ip_address=request.client.host
        )

        return {"success": True}

    except Exception as e:
        # Log failure
        audit_logger.log_admin_action(
            user=request.user.email,
            action="tenant_created",
            resource_type="tenant",
            resource_id=tenant_data.location_id,
            success=False,
            details={"error": str(e)},
            ip_address=request.client.host
        )
        raise
```

---

## 9. Environment Security

### 9.1 Secure Environment Variable Management

**Railway Production Setup:**

```bash
# Set in Railway dashboard (not in code)
TENANT_ENCRYPTION_KEY=<generated_fernet_key>
GHL_WEBHOOK_SECRET=<from_ghl_dashboard>
ANTHROPIC_API_KEY=<your_key>
GHL_API_KEY=<master_key>
GHL_LOCATION_ID=<primary_location>

# Database (Railway auto-provides)
DATABASE_URL=postgresql://...

# Security
ALLOWED_ORIGINS=https://yourdomain.com
CORS_ALLOWED_HOSTS=yourdomain.com
```

### 9.2 Secret Rotation Schedule

1. Quarterly: Rotate `TENANT_ENCRYPTION_KEY`
2. Quarterly: Rotate `GHL_WEBHOOK_SECRET`
3. Annually: Rotate API keys
4. Immediately: If breach suspected

### 9.3 File Permissions Script

Create `scripts/set_secure_permissions.sh`:

```bash
#!/bin/bash
# Set secure file permissions for production

# Set restrictive permissions on sensitive directories
chmod 700 data/tenants
chmod 700 data/memory
chmod 700 data/audit_logs

# Set restrictive permissions on config files
find data/tenants -name "*.json" -exec chmod 600 {} \;
find data/memory -name "*.json" -exec chmod 600 {} \;

# Ensure .env is not world-readable
if [ -f .env ]; then
  chmod 600 .env
fi

echo "Secure permissions set successfully"
```

---

## 10. Monitoring and Alerting

### 10.1 Security Event Monitoring

Create `services/security_monitor.py`:

```python
"""
Real-time security event monitoring and alerting.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict
import asyncio

class SecurityMonitor:
    """Monitor security events and trigger alerts."""

    def __init__(self):
        self.failed_auth_attempts = defaultdict(list)
        self.rate_limit_violations = defaultdict(list)

    def record_failed_auth(self, username: str, ip_address: str):
        """Record a failed authentication attempt."""
        self.failed_auth_attempts[username].append({
            "timestamp": datetime.utcnow(),
            "ip": ip_address
        })

        # Check for brute force
        recent_failures = [
            attempt for attempt in self.failed_auth_attempts[username]
            if datetime.utcnow() - attempt["timestamp"] < timedelta(minutes=5)
        ]

        if len(recent_failures) >= 5:
            self.alert_brute_force(username, ip_address, len(recent_failures))

    async def alert_brute_force(self, username: str, ip_address: str, count: int):
        """Alert on brute force attack."""
        # Send alert (email, Slack, PagerDuty, etc.)
        alert_message = f"""
        SECURITY ALERT: Brute Force Attack Detected

        Username: {username}
        IP Address: {ip_address}
        Failed Attempts: {count}
        Time Window: Last 5 minutes

        Action Taken: Account temporarily locked
        """

        # Send to monitoring service
        await self.send_alert("critical", alert_message)

        # Log to audit
        audit_logger.log_security_event(
            event_type="brute_force_detected",
            resource_type="user_account",
            resource_id=username,
            success=False,
            details={
                "ip_address": ip_address,
                "attempt_count": count
            }
        )

    async def send_alert(self, severity: str, message: str):
        """Send alert to monitoring service."""
        # Implement based on your monitoring stack
        # Examples: Sentry, Datadog, PagerDuty, Email, Slack
        pass
```

### 10.2 Health Check Endpoint

Edit `api/routes/webhook.py`:

```python
@router.get("/health/security")
async def security_health_check():
    """
    Security health check endpoint.

    Returns security posture and recent events.
    """
    return {
        "status": "healthy",
        "encryption": {
            "tenant_configs": "encrypted" if os.getenv("TENANT_ENCRYPTION_KEY") else "plaintext",
            "webhook_signature_verification": "enabled" if settings.ghl_webhook_secret else "disabled"
        },
        "authentication": {
            "dashboard": "enabled",
            "api": "webhook_signature"
        },
        "rate_limiting": {
            "enabled": True,
            "webhooks_per_minute": 120
        },
        "audit_logging": {
            "enabled": True,
            "events_today": get_audit_event_count_today()
        },
        "last_security_audit": "2026-01-04",
        "security_score": "78/100"
    }
```

---

## Implementation Checklist

### Before Production Launch

- [ ] **API Key Encryption** (Section 1.1)
  - [ ] Generate encryption key
  - [ ] Create `SecureTenantService`
  - [ ] Migrate existing tenant data
  - [ ] Test encryption/decryption cycle
  - [ ] Set `TENANT_ENCRYPTION_KEY` in Railway

- [ ] **Webhook Signature Verification** (Section 1.2)
  - [ ] Add signature verification to webhook handler
  - [ ] Set `GHL_WEBHOOK_SECRET` in Railway
  - [ ] Configure in GHL dashboard
  - [ ] Test with valid/invalid signatures

- [ ] **Rate Limiting** (Section 1.3)
  - [ ] Install SlowAPI
  - [ ] Add rate limiter middleware
  - [ ] Apply to webhook endpoint
  - [ ] Test rate limit enforcement

- [ ] **Dashboard Authentication** (Section 1.4)
  - [ ] Install streamlit-authenticator
  - [ ] Create auth config
  - [ ] Generate password hashes
  - [ ] Add auth to dashboard
  - [ ] Test login/logout flow

- [ ] **Security Testing**
  - [ ] Run all security tests: `pytest tests/test_security_multitenant.py -v`
  - [ ] Run security audit: `python scripts/security_audit.py`
  - [ ] Fix any critical findings

- [ ] **Documentation**
  - [ ] Update README with security features
  - [ ] Document incident response plan
  - [ ] Create runbook for security events

### Post-Launch (Within 1 Month)

- [ ] PII Detection and Redaction
- [ ] GDPR Compliance Endpoints
- [ ] Audit Logging for All Admin Actions
- [ ] Security Monitoring and Alerting
- [ ] Dependency Vulnerability Scanning (CI/CD)

---

## Support and Contact

For questions or security concerns:
- **Security Issues:** Report immediately to security@yourdomain.com
- **Implementation Help:** See `SECURITY_AUDIT_MULTITENANT.md`
- **Test Coverage:** Run `pytest tests/test_security_multitenant.py -v`

---

**Document End**
