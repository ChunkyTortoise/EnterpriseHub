# Layer 4: API Security Layer

## Complete Implementation Reference

This layer secures API endpoints with authentication, rate limiting, and request validation.

### JWT Authentication and Validation

```python
"""
API security layer with JWT authentication and rate limiting.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import jwt
from functools import wraps
from fastapi import Request, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import time
from collections import defaultdict


class APISecurityLayer:
    """Comprehensive API security with multiple defense layers."""

    def __init__(self, secret_key: str, config: Optional[Dict] = None):
        self.secret_key = secret_key
        self.config = config or {}
        self.rate_limit_store = defaultdict(list)
        self.blacklisted_tokens = set()
        self.security = HTTPBearer()

    def validate_jwt_token(self, token: str) -> ValidationResult:
        """Multi-layer JWT token validation."""
        errors = []
        warnings = []

        try:
            # Layer 1: Basic token format validation
            if not token or not isinstance(token, str):
                errors.append("Invalid token format")
                return ValidationResult(False, errors, warnings)

            # Layer 2: Check token blacklist
            if token in self.blacklisted_tokens:
                errors.append("Token has been revoked")
                return ValidationResult(
                    False, errors, warnings,
                    severity=ValidationSeverity.CRITICAL
                )

            # Layer 3: Decode and verify token
            try:
                payload = jwt.decode(
                    token,
                    self.secret_key,
                    algorithms=['HS256']
                )
            except jwt.ExpiredSignatureError:
                errors.append("Token has expired")
                return ValidationResult(False, errors, warnings)
            except jwt.InvalidTokenError as e:
                errors.append(f"Invalid token: {str(e)}")
                return ValidationResult(False, errors, warnings)

            # Layer 4: Validate payload structure
            required_claims = ['sub', 'exp', 'iat']
            missing_claims = [claim for claim in required_claims if claim not in payload]
            if missing_claims:
                errors.append(f"Token missing required claims: {', '.join(missing_claims)}")

            # Layer 5: Validate expiration
            exp = payload.get('exp')
            if exp and datetime.fromtimestamp(exp) < datetime.now():
                errors.append("Token has expired")

            # Layer 6: Validate token age
            iat = payload.get('iat')
            if iat:
                token_age = datetime.now() - datetime.fromtimestamp(iat)
                max_age = timedelta(hours=self.config.get('max_token_age_hours', 24))
                if token_age > max_age:
                    warnings.append("Token is older than recommended maximum age")

            # Layer 7: Validate user permissions
            if 'permissions' in payload:
                perm_result = self._validate_permissions(payload['permissions'])
                if not perm_result.is_valid:
                    errors.extend(perm_result.errors)

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                sanitized_data=payload
            )

        except Exception as e:
            errors.append(f"Token validation error: {str(e)}")
            return ValidationResult(False, errors, warnings)

    def _validate_permissions(self, permissions: List[str]) -> ValidationResult:
        """Validate permission structure."""
        errors = []
        warnings = []

        if not isinstance(permissions, list):
            errors.append("Permissions must be a list")
            return ValidationResult(False, errors, warnings)

        # Validate each permission
        valid_permission_pattern = re.compile(r'^[a-z_]+:[a-z_]+$')
        for perm in permissions:
            if not valid_permission_pattern.match(perm):
                errors.append(f"Invalid permission format: {perm}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def generate_jwt_token(
        self,
        user_id: str,
        permissions: List[str],
        expires_in_hours: int = 24
    ) -> ValidationResult:
        """Generate secure JWT token."""
        errors = []
        warnings = []

        try:
            # Layer 1: Validate inputs
            if not user_id:
                errors.append("User ID is required")

            if expires_in_hours > 168:  # 7 days
                warnings.append("Token expiration exceeds recommended maximum (7 days)")

            if len(errors) > 0:
                return ValidationResult(False, errors, warnings)

            # Layer 2: Create payload
            now = datetime.now()
            payload = {
                'sub': user_id,
                'iat': now,
                'exp': now + timedelta(hours=expires_in_hours),
                'permissions': permissions,
                'jti': hashlib.sha256(f"{user_id}{now}".encode()).hexdigest()[:16]
            }

            # Layer 3: Generate token
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')

            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                sanitized_data={'token': token, 'expires_at': payload['exp']}
            )

        except Exception as e:
            errors.append(f"Token generation error: {str(e)}")
            return ValidationResult(False, errors, warnings)

    def revoke_token(self, token: str) -> ValidationResult:
        """Revoke a JWT token."""
        errors = []
        warnings = []

        # Validate token first
        validation_result = self.validate_jwt_token(token)
        if not validation_result.is_valid:
            errors.append("Cannot revoke invalid token")
            return ValidationResult(False, errors, warnings)

        # Add to blacklist
        self.blacklisted_tokens.add(token)

        return ValidationResult(True, errors, warnings)
```

### Rate Limiting

```python
def check_rate_limit(
    self,
    identifier: str,
    max_requests: int = 100,
    window_seconds: int = 60
) -> ValidationResult:
    """Multi-layer rate limiting."""
    errors = []
    warnings = []

    # Layer 1: Get request history
    now = time.time()
    request_times = self.rate_limit_store[identifier]

    # Layer 2: Clean old requests outside window
    cutoff_time = now - window_seconds
    request_times = [t for t in request_times if t > cutoff_time]
    self.rate_limit_store[identifier] = request_times

    # Layer 3: Check rate limit
    if len(request_times) >= max_requests:
        errors.append(
            f"Rate limit exceeded: {len(request_times)}/{max_requests} "
            f"requests in {window_seconds} seconds"
        )
        return ValidationResult(
            False, errors, warnings,
            severity=ValidationSeverity.WARNING
        )

    # Layer 4: Warn if approaching limit
    if len(request_times) >= max_requests * 0.8:
        warnings.append(
            f"Approaching rate limit: {len(request_times)}/{max_requests} requests"
        )

    # Layer 5: Record this request
    request_times.append(now)

    return ValidationResult(
        is_valid=True,
        errors=errors,
        warnings=warnings,
        sanitized_data={'remaining': max_requests - len(request_times)}
    )

def get_rate_limit_identifier(self, request: Request) -> str:
    """Get identifier for rate limiting (IP + user)."""
    # Combine IP and user for more granular rate limiting
    client_ip = request.client.host
    user_id = getattr(request.state, 'user_id', 'anonymous')
    return f"{client_ip}:{user_id}"
```

### API Request Validation

```python
def validate_api_request(
    self,
    request: Request,
    required_permissions: Optional[List[str]] = None
) -> ValidationResult:
    """Comprehensive API request validation."""
    errors = []
    warnings = []

    # Layer 1: Validate request method
    allowed_methods = self.config.get('allowed_methods', ['GET', 'POST', 'PUT', 'DELETE'])
    if request.method not in allowed_methods:
        errors.append(f"Method {request.method} not allowed")

    # Layer 2: Validate content type
    if request.method in ['POST', 'PUT', 'PATCH']:
        content_type = request.headers.get('content-type', '')
        if 'application/json' not in content_type:
            errors.append("Content-Type must be application/json")

    # Layer 3: Validate request size
    content_length = request.headers.get('content-length')
    if content_length:
        max_size = self.config.get('max_request_size_bytes', 1024 * 1024)  # 1MB
        if int(content_length) > max_size:
            errors.append(f"Request size exceeds maximum: {max_size} bytes")

    # Layer 4: Extract and validate token
    auth_header = request.headers.get('authorization', '')
    if not auth_header.startswith('Bearer '):
        errors.append("Missing or invalid Authorization header")
        return ValidationResult(False, errors, warnings)

    token = auth_header.replace('Bearer ', '')
    token_result = self.validate_jwt_token(token)
    if not token_result.is_valid:
        errors.extend(token_result.errors)
        return ValidationResult(False, errors, warnings)

    # Layer 5: Check permissions
    if required_permissions:
        user_permissions = token_result.sanitized_data.get('permissions', [])
        missing_perms = [p for p in required_permissions if p not in user_permissions]
        if missing_perms:
            errors.append(f"Missing required permissions: {', '.join(missing_perms)}")

    # Layer 6: Rate limiting
    rate_limit_id = self.get_rate_limit_identifier(request)
    rate_result = self.check_rate_limit(rate_limit_id)
    if not rate_result.is_valid:
        errors.extend(rate_result.errors)

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        sanitized_data=token_result.sanitized_data
    )
```

### FastAPI Dependency

```python
async def require_auth(
    self,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    required_permissions: Optional[List[str]] = None
):
    """FastAPI dependency for authentication."""
    token = credentials.credentials

    # Validate token
    result = self.validate_jwt_token(token)
    if not result.is_valid:
        raise HTTPException(
            status_code=401,
            detail=result.errors[0] if result.errors else "Unauthorized"
        )

    # Check permissions
    if required_permissions:
        user_permissions = result.sanitized_data.get('permissions', [])
        missing_perms = [p for p in required_permissions if p not in user_permissions]
        if missing_perms:
            raise HTTPException(
                status_code=403,
                detail=f"Missing permissions: {', '.join(missing_perms)}"
            )

    return result.sanitized_data


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator for rate limiting endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get identifier
            identifier = f"{request.client.host}:{request.url.path}"

            # Check rate limit
            security_layer = APISecurityLayer(secret_key="your-secret")
            result = security_layer.check_rate_limit(
                identifier, max_requests, window_seconds
            )

            if not result.is_valid:
                raise HTTPException(
                    status_code=429,
                    detail=result.errors[0] if result.errors else "Rate limit exceeded"
                )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

## Best Practices

1. **Always validate JWT tokens** on protected endpoints
2. **Implement rate limiting** to prevent abuse
3. **Use HTTPS only** for API communication
4. **Validate request size** to prevent DoS attacks
5. **Check permissions** for every sensitive operation
6. **Log authentication failures** for security monitoring
7. **Rotate JWT secrets** regularly
8. **Implement token blacklisting** for logout/revocation
