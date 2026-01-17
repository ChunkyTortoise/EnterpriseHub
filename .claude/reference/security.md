# Security Reference Guide

**Token Budget**: ~3-4k tokens (load on-demand only)
**Trigger**: When implementing authentication, API endpoints, data handling, or security-sensitive features

## OWASP Top 10 Quick Reference

### 1. Injection Prevention
```python
# ✅ GOOD: Parameterized queries
user = session.query(User).filter(User.email == user_input).first()

# ❌ BAD: String interpolation
query = f"SELECT * FROM users WHERE email = '{user_input}'"  # SQL injection!
```

**Checklist**:
- [ ] All database queries use ORM or prepared statements
- [ ] No raw SQL with string concatenation
- [ ] User input validated before queries
- [ ] Special characters escaped in dynamic queries

### 2. Authentication & Session Management

**JWT Implementation**:
```python
from datetime import datetime, timedelta
import jwt

def create_access_token(user_id: str) -> str:
    """Generate short-lived access token (15 min)."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def create_refresh_token(user_id: str) -> str:
    """Generate long-lived refresh token (7 days)."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm='HS256')
```

**Session Security**:
- Access tokens: 15 minutes max
- Refresh tokens: 7 days max, stored in httpOnly cookies
- Token rotation on refresh
- Blacklist for logout
- No sensitive data in token payload

### 3. Sensitive Data Protection

**Encryption at Rest**:
```python
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt_field(self, value: str) -> str:
        """Encrypt sensitive field for database storage."""
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt_field(self, encrypted: str) -> str:
        """Decrypt field from database."""
        return self.cipher.decrypt(encrypted.encode()).decode()

# Use for: SSN, credit cards, API keys, PII
```

**Environment Variables**:
```bash
# .env.example (commit this)
DATABASE_URL=postgresql://user:pass@localhost:5432/db
JWT_SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here

# .env.local (NEVER commit)
DATABASE_URL=postgresql://realuser:realpass@prod.db.com:5432/proddb
JWT_SECRET_KEY=actual-secret-key-8n23kjh4kj23h4kjh23
API_KEY=sk_live_actual_key_here
```

### 4. Access Control (Authorization)

**Role-Based Access Control (RBAC)**:
```python
from enum import Enum
from functools import wraps

class Role(Enum):
    ADMIN = "admin"
    AGENT = "agent"
    CLIENT = "client"

def require_role(*allowed_roles: Role):
    """Decorator to enforce role-based access."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from request context
            user = get_current_user()

            if user.role not in [r.value for r in allowed_roles]:
                raise PermissionError(f"Requires role: {allowed_roles}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@require_role(Role.ADMIN)
async def delete_user(user_id: str):
    # Only admins can delete users
    pass

@require_role(Role.ADMIN, Role.AGENT)
async def view_analytics():
    # Admins and agents can view analytics
    pass
```

**Resource Ownership**:
```python
async def update_listing(listing_id: str, user: User, data: dict):
    """Users can only update their own listings."""
    listing = await get_listing(listing_id)

    # Check ownership
    if listing.owner_id != user.id and user.role != Role.ADMIN:
        raise PermissionError("Not authorized to modify this listing")

    # Proceed with update
    return await listing.update(data)
```

### 5. Security Misconfiguration

**Secure Headers**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Never use "*" in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### 6. Input Validation

**Pydantic Models**:
```python
from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional

class UserRegistration(BaseModel):
    email: EmailStr  # Validates email format
    password: constr(min_length=8, max_length=128)  # Password constraints
    phone: Optional[constr(regex=r'^\+?1?\d{9,15}$')]  # Phone validation

    @validator('password')
    def validate_password_strength(cls, v):
        """Ensure password has required complexity."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v

    @validator('email')
    def validate_email_domain(cls, v):
        """Block disposable email domains."""
        disposable_domains = ['tempmail.com', 'guerrillamail.com']
        domain = v.split('@')[1]
        if domain in disposable_domains:
            raise ValueError('Disposable email addresses not allowed')
        return v
```

**Sanitization**:
```python
import bleach
from html import escape

def sanitize_html(user_input: str) -> str:
    """Remove dangerous HTML/JS from user input."""
    allowed_tags = ['p', 'b', 'i', 'u', 'em', 'strong', 'a']
    allowed_attrs = {'a': ['href', 'title']}

    return bleach.clean(
        user_input,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )

def sanitize_for_display(user_input: str) -> str:
    """Escape HTML entities for safe display."""
    return escape(user_input)
```

### 7. Rate Limiting

**Redis-Backed Rate Limiter**:
```python
from datetime import datetime, timedelta
import redis

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        limit: int = 100,
        window_seconds: int = 900  # 15 minutes
    ) -> bool:
        """Check if request is within rate limit."""
        now = datetime.utcnow()
        window_key = f"rate_limit:{key}:{now.strftime('%Y%m%d%H%M')}"

        # Increment counter
        current = self.redis.incr(window_key)

        # Set expiry on first request
        if current == 1:
            self.redis.expire(window_key, window_seconds)

        # Check limit
        if current > limit:
            return False

        return True

# Middleware usage
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    # Get client IP or user ID
    client_id = request.client.host

    if not await rate_limiter.check_rate_limit(client_id, limit=100):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return await call_next(request)
```

### 8. API Security Checklist

**Before Deploying API Endpoints**:
- [ ] Authentication required? (JWT, API key, OAuth)
- [ ] Authorization checks in place? (RBAC, ownership)
- [ ] Input validation implemented? (Pydantic models)
- [ ] Rate limiting applied? (per IP or per user)
- [ ] SQL injection prevented? (ORM, parameterized queries)
- [ ] XSS protection? (output escaping, CSP headers)
- [ ] CSRF protection? (tokens for form submissions)
- [ ] HTTPS enforced? (redirect HTTP to HTTPS)
- [ ] Sensitive data encrypted? (at rest and in transit)
- [ ] Error messages sanitized? (no stack traces in production)
- [ ] CORS configured? (specific origins, not "*")
- [ ] Security headers set? (X-Frame-Options, CSP, etc.)

## Cryptographic Standards

**Hashing Passwords**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain, hashed)
```

**Secrets Generation**:
```python
import secrets

def generate_api_key(length: int = 32) -> str:
    """Generate cryptographically secure API key."""
    return secrets.token_urlsafe(length)

def generate_session_token() -> str:
    """Generate secure session token."""
    return secrets.token_hex(32)
```

## Security Monitoring

**Logging Sensitive Events**:
```python
import logging
from datetime import datetime

security_logger = logging.getLogger('security')

def log_security_event(event_type: str, user_id: str, details: dict):
    """Log security-relevant events for audit trail."""
    security_logger.info({
        'timestamp': datetime.utcnow().isoformat(),
        'event': event_type,
        'user_id': user_id,
        'ip': details.get('ip'),
        'user_agent': details.get('user_agent'),
        'details': details
    })

# Events to log:
# - Failed login attempts
# - Password changes
# - Permission escalations
# - API key generation/rotation
# - Data exports
# - Administrative actions
```

## Vulnerability Scanning

**Regular Security Checks**:
```bash
# Python dependencies
pip install safety
safety check --json

# Dependency audit
pip-audit

# Static analysis
bandit -r ghl_real_estate_ai/

# Secrets detection
trufflehog git file://. --only-verified
```

---

**Reference Updates**: Review quarterly or when OWASP Top 10 changes
**Last Updated**: 2026-01-16
