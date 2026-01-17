---
name: Defense in Depth
description: This skill should be used when implementing "multi-layer validation", "comprehensive error handling", "input sanitization", "security testing", "data validation layers", "fault tolerance", or when building robust systems with multiple validation checkpoints.
version: 1.0.0
---

# Defense in Depth: Multi-Layer Validation and Security

## Overview

This skill implements comprehensive defense-in-depth strategies for robust applications. It provides multiple layers of validation, security checks, and error handling to ensure system resilience against various failure modes and attack vectors.

## When to Use This Skill

Use this skill when implementing:
- **Multi-layer input validation**
- **Comprehensive error handling strategies**
- **Security hardening with multiple checkpoints**
- **Data integrity validation across system layers**
- **Fault-tolerant system architectures**
- **API security with multiple validation stages**
- **Database security and data protection**

## Core Defense Layers

### Layer 1: Input Validation and Sanitization

```python
"""
First line of defense: Input validation and sanitization
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import re
import html
import bleach
from decimal import Decimal, InvalidOperation
import ipaddress
from datetime import datetime
import json


class ValidationSeverity(Enum):
    """Severity levels for validation failures."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_data: Optional[Any] = None
    severity: ValidationSeverity = ValidationSeverity.INFO


class InputValidator:
    """Comprehensive input validation with multiple strategies."""

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.validation_rules = {}

    def validate_email(self, email: str) -> ValidationResult:
        """Multi-layer email validation."""
        errors = []
        warnings = []

        # Layer 1: Basic format validation
        if not email or not isinstance(email, str):
            errors.append("Email must be a non-empty string")
            return ValidationResult(False, errors, warnings)

        email = email.strip().lower()

        # Layer 2: Length validation
        if len(email) > 254:  # RFC 5321 limit
            errors.append("Email too long (max 254 characters)")

        if len(email) < 5:  # Minimum reasonable email
            errors.append("Email too short (minimum 5 characters)")

        # Layer 3: Format validation with regex
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        if not email_pattern.match(email):
            errors.append("Invalid email format")

        # Layer 4: Domain validation
        if '@' in email:
            local_part, domain = email.split('@', 1)

            # Local part validation
            if len(local_part) > 64:
                errors.append("Email local part too long (max 64 characters)")

            # Domain validation
            if len(domain) > 253:
                errors.append("Email domain too long (max 253 characters)")

            # Check for dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
            if any(char in email for char in dangerous_chars):
                errors.append("Email contains potentially dangerous characters")

        # Layer 5: Disposable email detection (optional)
        if self.strict_mode and self._is_disposable_email(email):
            warnings.append("Disposable email domain detected")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data=email if len(errors) == 0 else None
        )

    def validate_password(self, password: str) -> ValidationResult:
        """Multi-layer password validation."""
        errors = []
        warnings = []

        if not password or not isinstance(password, str):
            errors.append("Password must be a non-empty string")
            return ValidationResult(False, errors, warnings)

        # Layer 1: Length validation
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if len(password) > 128:
            errors.append("Password too long (max 128 characters)")

        # Layer 2: Character complexity
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not has_lower:
            errors.append("Password must contain at least one lowercase letter")
        if not has_upper:
            errors.append("Password must contain at least one uppercase letter")
        if not has_digit:
            errors.append("Password must contain at least one digit")
        if not has_special:
            warnings.append("Password should contain at least one special character")

        # Layer 3: Common password detection
        if self._is_common_password(password):
            errors.append("Password is too common and easily guessable")

        # Layer 4: Pattern detection
        if self._has_simple_pattern(password):
            warnings.append("Password contains simple patterns")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=ValidationSeverity.CRITICAL if errors else ValidationSeverity.INFO
        )

    def validate_numeric_input(
        self,
        value: Any,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        allow_decimal: bool = True
    ) -> ValidationResult:
        """Multi-layer numeric input validation."""
        errors = []
        warnings = []

        # Layer 1: Type and existence validation
        if value is None:
            errors.append("Numeric value cannot be None")
            return ValidationResult(False, errors, warnings)

        # Layer 2: String to number conversion with safety
        try:
            if isinstance(value, str):
                # Check for dangerous input
                if any(char in value for char in ['<', '>', "'", '"', '&']):
                    errors.append("Numeric input contains dangerous characters")
                    return ValidationResult(False, errors, warnings)

                value = value.strip()
                if allow_decimal:
                    numeric_value = Decimal(value)
                else:
                    numeric_value = int(value)
            else:
                numeric_value = Decimal(str(value)) if allow_decimal else int(value)

        except (ValueError, InvalidOperation) as e:
            errors.append(f"Invalid numeric format: {e}")
            return ValidationResult(False, errors, warnings)

        # Layer 3: Range validation
        if min_value is not None and numeric_value < min_value:
            errors.append(f"Value {numeric_value} below minimum {min_value}")

        if max_value is not None and numeric_value > max_value:
            errors.append(f"Value {numeric_value} above maximum {max_value}")

        # Layer 4: Reasonable bounds check
        if abs(numeric_value) > 1e15:
            warnings.append("Extremely large numeric value detected")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data=float(numeric_value) if allow_decimal else int(numeric_value)
        )

    def sanitize_html_input(self, html_input: str) -> ValidationResult:
        """Multi-layer HTML sanitization."""
        errors = []
        warnings = []

        if not isinstance(html_input, str):
            errors.append("HTML input must be a string")
            return ValidationResult(False, errors, warnings)

        # Layer 1: Basic HTML escaping
        escaped_html = html.escape(html_input)

        # Layer 2: Bleach sanitization with whitelist
        allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
        allowed_attributes = {}

        cleaned_html = bleach.clean(
            html_input,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )

        # Layer 3: Check for potential XSS patterns
        xss_patterns = [
            r'javascript:',
            r'on\w+\s*=',
            r'<\s*script',
            r'eval\s*\(',
            r'expression\s*\('
        ]

        for pattern in xss_patterns:
            if re.search(pattern, html_input, re.IGNORECASE):
                warnings.append(f"Potential XSS pattern detected: {pattern}")

        # Layer 4: Length validation
        if len(cleaned_html) > 10000:
            warnings.append("HTML content is very long")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data=cleaned_html
        )

    def _is_disposable_email(self, email: str) -> bool:
        """Check against list of disposable email domains."""
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com'
        ]
        domain = email.split('@')[1].lower()
        return domain in disposable_domains

    def _is_common_password(self, password: str) -> bool:
        """Check against common passwords."""
        common_passwords = [
            'password', '123456', 'password123', 'admin', 'qwerty',
            'letmein', 'welcome', 'monkey', '12345678', 'password1'
        ]
        return password.lower() in common_passwords

    def _has_simple_pattern(self, password: str) -> bool:
        """Detect simple patterns in passwords."""
        # Consecutive characters
        for i in range(len(password) - 2):
            chars = password[i:i+3]
            if (chars.isdigit() and
                int(chars[1]) == int(chars[0]) + 1 and
                int(chars[2]) == int(chars[1]) + 1):
                return True
        return False
```

### Layer 2: Business Logic Validation

```python
"""
Second line of defense: Business logic validation
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio


class BusinessRuleValidator:
    """Validates business rules and constraints."""

    def __init__(self, db_connection):
        self.db = db_connection

    async def validate_user_registration(self, user_data: Dict[str, Any]) -> ValidationResult:
        """Multi-layer user registration validation."""
        errors = []
        warnings = []

        # Layer 1: Required fields validation
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not user_data.get(field):
                errors.append(f"Field '{field}' is required")

        if errors:
            return ValidationResult(False, errors, warnings)

        # Layer 2: Email uniqueness validation
        existing_user = await self._check_email_exists(user_data['email'])
        if existing_user:
            errors.append("Email address already registered")

        # Layer 3: Age validation (if provided)
        if 'birth_date' in user_data:
            age_validation = self._validate_age(user_data['birth_date'])
            if not age_validation.is_valid:
                errors.extend(age_validation.errors)

        # Layer 4: Rate limiting validation
        rate_limit_validation = await self._check_registration_rate_limit(
            user_data.get('ip_address')
        )
        if not rate_limit_validation.is_valid:
            errors.extend(rate_limit_validation.errors)

        # Layer 5: Domain reputation check
        domain_check = await self._check_email_domain_reputation(user_data['email'])
        if not domain_check.is_valid:
            warnings.extend(domain_check.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=ValidationSeverity.ERROR if errors else ValidationSeverity.INFO
        )

    async def validate_financial_transaction(
        self,
        transaction_data: Dict[str, Any]
    ) -> ValidationResult:
        """Multi-layer financial transaction validation."""
        errors = []
        warnings = []

        # Layer 1: Amount validation
        amount = transaction_data.get('amount')
        if not amount or amount <= 0:
            errors.append("Transaction amount must be positive")

        # Layer 2: Account balance validation
        account_id = transaction_data.get('from_account_id')
        if account_id:
            balance_check = await self._validate_account_balance(account_id, amount)
            if not balance_check.is_valid:
                errors.extend(balance_check.errors)

        # Layer 3: Daily transaction limit validation
        daily_limit_check = await self._check_daily_transaction_limit(
            account_id, amount
        )
        if not daily_limit_check.is_valid:
            errors.extend(daily_limit_check.errors)

        # Layer 4: Fraud detection
        fraud_check = await self._detect_fraud_patterns(transaction_data)
        if not fraud_check.is_valid:
            if fraud_check.severity == ValidationSeverity.CRITICAL:
                errors.extend(fraud_check.errors)
            else:
                warnings.extend(fraud_check.warnings)

        # Layer 5: Compliance validation
        compliance_check = await self._validate_compliance_rules(transaction_data)
        if not compliance_check.is_valid:
            errors.extend(compliance_check.errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=ValidationSeverity.CRITICAL if "fraud" in str(errors).lower() else ValidationSeverity.ERROR
        )

    async def _check_email_exists(self, email: str) -> bool:
        """Check if email already exists in database."""
        query = "SELECT id FROM users WHERE email = $1"
        result = await self.db.fetchrow(query, email)
        return result is not None

    def _validate_age(self, birth_date: datetime) -> ValidationResult:
        """Validate user age requirements."""
        errors = []
        today = datetime.now().date()
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )

        if age < 13:
            errors.append("User must be at least 13 years old")
        elif age < 18:
            errors.append("Users under 18 require parental consent")

        return ValidationResult(len(errors) == 0, errors, [])

    async def _check_registration_rate_limit(self, ip_address: str) -> ValidationResult:
        """Check registration rate limiting."""
        if not ip_address:
            return ValidationResult(True, [], [])

        # Check registrations from this IP in the last hour
        query = """
            SELECT COUNT(*) FROM user_registrations
            WHERE ip_address = $1 AND created_at > $2
        """
        one_hour_ago = datetime.now() - timedelta(hours=1)
        result = await self.db.fetchval(query, ip_address, one_hour_ago)

        if result > 3:  # Max 3 registrations per hour per IP
            return ValidationResult(
                False,
                ["Too many registration attempts from this IP address"],
                []
            )

        return ValidationResult(True, [], [])
```

### Layer 3: Database Security and Data Integrity

```python
"""
Third line of defense: Database security and data integrity
"""

import asyncpg
import logging
from typing import Any, Dict, List, Optional, Union
import hashlib
import secrets
from contextlib import asynccontextmanager


class DatabaseSecurityLayer:
    """Database security and integrity validation."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def secure_transaction(self):
        """Secure database transaction with logging."""
        async with self.db_pool.acquire() as conn:
            transaction = conn.transaction()
            await transaction.start()

            try:
                self.logger.info("Starting secure database transaction")
                yield conn
                await transaction.commit()
                self.logger.info("Transaction committed successfully")

            except Exception as e:
                await transaction.rollback()
                self.logger.error(f"Transaction rolled back due to error: {e}")
                raise

    async def validate_sql_injection(self, query: str, params: List[Any]) -> ValidationResult:
        """Multi-layer SQL injection prevention."""
        errors = []
        warnings = []

        # Layer 1: Parameterized query validation
        if not params and any(op in query.lower() for op in ['where', 'update', 'delete']):
            warnings.append("Query without parameters detected")

        # Layer 2: Dangerous pattern detection
        dangerous_patterns = [
            r"';.*--",  # Comment injection
            r"union\s+select",  # Union-based injection
            r"or\s+1\s*=\s*1",  # Always true condition
            r"drop\s+table",  # Drop table
            r"exec\s*\(",  # Stored procedure execution
            r"xp_cmdshell"  # Command execution
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                errors.append(f"Potentially dangerous SQL pattern detected: {pattern}")

        # Layer 3: Parameter validation
        for i, param in enumerate(params):
            if isinstance(param, str):
                # Check for SQL injection in parameters
                if any(char in param for char in ["'", '"', ';', '--']):
                    warnings.append(f"Parameter {i} contains potentially dangerous characters")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def secure_user_lookup(self, user_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Secure user lookup with multiple validation layers."""
        # Layer 1: Input validation
        if not user_id:
            raise ValueError("User ID cannot be empty")

        # Layer 2: Type validation and conversion
        try:
            if isinstance(user_id, str):
                user_id = int(user_id)
        except ValueError:
            raise ValueError("User ID must be a valid integer")

        # Layer 3: Range validation
        if user_id <= 0:
            raise ValueError("User ID must be positive")

        # Layer 4: Secure database query
        async with self.secure_transaction() as conn:
            # Use parameterized query to prevent SQL injection
            query = """
                SELECT id, email, first_name, last_name, created_at, is_active
                FROM users
                WHERE id = $1 AND is_deleted = FALSE
            """

            # Layer 5: Audit logging
            self.logger.info(f"Performing secure user lookup for ID: {user_id}")

            result = await conn.fetchrow(query, user_id)

            if result:
                # Layer 6: Data sanitization before return
                return {
                    'id': result['id'],
                    'email': result['email'].lower(),
                    'first_name': result['first_name'],
                    'last_name': result['last_name'],
                    'created_at': result['created_at'],
                    'is_active': result['is_active']
                }

            return None

    async def secure_password_storage(self, user_id: int, password: str) -> ValidationResult:
        """Secure password storage with multiple layers."""
        errors = []

        # Layer 1: Password validation
        password_validation = InputValidator().validate_password(password)
        if not password_validation.is_valid:
            errors.extend(password_validation.errors)
            return ValidationResult(False, errors, [])

        # Layer 2: Password hashing with salt
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()

        # Layer 3: Secure database storage
        async with self.secure_transaction() as conn:
            # Layer 4: Update with audit trail
            update_query = """
                UPDATE users
                SET password_hash = $1, password_salt = $2, password_updated_at = NOW()
                WHERE id = $3
            """

            # Layer 5: Audit logging
            self.logger.info(f"Updating password for user ID: {user_id}")

            await conn.execute(update_query, password_hash, salt, user_id)

            # Layer 6: Record password change in audit log
            audit_query = """
                INSERT INTO audit_log (user_id, action, details, created_at)
                VALUES ($1, 'password_change', 'Password updated', NOW())
            """
            await conn.execute(audit_query, user_id)

        return ValidationResult(True, [], [])

    async def validate_data_integrity(self, table_name: str) -> ValidationResult:
        """Multi-layer data integrity validation."""
        errors = []
        warnings = []

        async with self.db_pool.acquire() as conn:
            # Layer 1: Check for orphaned records
            orphan_checks = {
                'user_profiles': 'SELECT COUNT(*) FROM user_profiles WHERE user_id NOT IN (SELECT id FROM users)',
                'posts': 'SELECT COUNT(*) FROM posts WHERE author_id NOT IN (SELECT id FROM users)',
                'comments': 'SELECT COUNT(*) FROM comments WHERE post_id NOT IN (SELECT id FROM posts)'
            }

            if table_name in orphan_checks:
                orphan_count = await conn.fetchval(orphan_checks[table_name])
                if orphan_count > 0:
                    errors.append(f"Found {orphan_count} orphaned records in {table_name}")

            # Layer 2: Check for data consistency
            if table_name == 'users':
                # Check for users with invalid email formats
                invalid_emails = await conn.fetchval("""
                    SELECT COUNT(*) FROM users
                    WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
                """)
                if invalid_emails > 0:
                    errors.append(f"Found {invalid_emails} users with invalid email formats")

            # Layer 3: Check for suspicious data patterns
            if table_name == 'transactions':
                # Check for transactions with unusual amounts
                suspicious_transactions = await conn.fetchval("""
                    SELECT COUNT(*) FROM transactions
                    WHERE amount > 100000 OR amount < 0
                """)
                if suspicious_transactions > 0:
                    warnings.append(f"Found {suspicious_transactions} transactions with unusual amounts")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

### Layer 4: API Security and Rate Limiting

```python
"""
Fourth line of defense: API security and rate limiting
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import redis.asyncio as redis
import time
from typing import Optional, Dict, Any
import ipaddress
from datetime import datetime, timedelta


class APISecurityLayer:
    """API security with multiple protection layers."""

    def __init__(self, redis_client: redis.Redis, jwt_secret: str):
        self.redis = redis_client
        self.jwt_secret = jwt_secret
        self.security = HTTPBearer()

    async def validate_request_rate_limit(
        self,
        request: Request,
        max_requests: int = 100,
        window_minutes: int = 15
    ) -> ValidationResult:
        """Multi-layer rate limiting."""
        errors = []
        warnings = []

        # Layer 1: Get client identifier
        client_ip = self._get_client_ip(request)
        if not client_ip:
            errors.append("Cannot identify client IP")
            return ValidationResult(False, errors, warnings)

        # Layer 2: Check if IP is in whitelist
        if await self._is_whitelisted_ip(client_ip):
            return ValidationResult(True, [], ["IP is whitelisted"])

        # Layer 3: Check if IP is blacklisted
        if await self._is_blacklisted_ip(client_ip):
            errors.append("IP address is blacklisted")
            return ValidationResult(False, errors, warnings)

        # Layer 4: Rate limit enforcement
        window_key = f"rate_limit:{client_ip}:{window_minutes}m"
        current_requests = await self.redis.get(window_key)

        if current_requests is None:
            # First request in window
            await self.redis.setex(window_key, window_minutes * 60, 1)
            current_requests = 1
        else:
            current_requests = int(current_requests)
            if current_requests >= max_requests:
                errors.append(f"Rate limit exceeded: {current_requests}/{max_requests} requests")
                return ValidationResult(False, errors, warnings)

            # Increment counter
            await self.redis.incr(window_key)
            current_requests += 1

        # Layer 5: Warning threshold
        if current_requests > max_requests * 0.8:
            warnings.append(f"Approaching rate limit: {current_requests}/{max_requests}")

        return ValidationResult(True, [], warnings)

    async def validate_jwt_token(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> ValidationResult:
        """Multi-layer JWT token validation."""
        errors = []
        warnings = []

        if not credentials or not credentials.credentials:
            errors.append("No authorization token provided")
            return ValidationResult(False, errors, warnings)

        token = credentials.credentials

        try:
            # Layer 1: Token format validation
            if len(token.split('.')) != 3:
                errors.append("Invalid JWT token format")
                return ValidationResult(False, errors, warnings)

            # Layer 2: Token decoding and signature verification
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])

            # Layer 3: Token expiration validation
            exp_timestamp = payload.get('exp')
            if not exp_timestamp:
                errors.append("Token missing expiration time")
            elif datetime.utcfromtimestamp(exp_timestamp) < datetime.utcnow():
                errors.append("Token has expired")

            # Layer 4: Token revocation check
            jti = payload.get('jti')  # JWT ID for tracking
            if jti and await self._is_token_revoked(jti):
                errors.append("Token has been revoked")

            # Layer 5: User validation
            user_id = payload.get('user_id')
            if user_id and not await self._is_user_active(user_id):
                errors.append("User account is inactive")

            # Layer 6: Permission validation
            permissions = payload.get('permissions', [])
            if not permissions:
                warnings.append("Token has no permissions assigned")

        except jwt.ExpiredSignatureError:
            errors.append("Token signature has expired")
        except jwt.InvalidTokenError as e:
            errors.append(f"Invalid token: {e}")
        except Exception as e:
            errors.append(f"Token validation error: {e}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data=payload if len(errors) == 0 else None
        )

    async def validate_api_input(
        self,
        request: Request,
        max_payload_size: int = 1024 * 1024  # 1MB
    ) -> ValidationResult:
        """Multi-layer API input validation."""
        errors = []
        warnings = []

        # Layer 1: Content-Type validation
        content_type = request.headers.get("content-type", "")
        allowed_types = ["application/json", "application/x-www-form-urlencoded"]

        if content_type and not any(ct in content_type for ct in allowed_types):
            warnings.append(f"Unexpected content type: {content_type}")

        # Layer 2: Payload size validation
        content_length = request.headers.get("content-length")
        if content_length:
            size = int(content_length)
            if size > max_payload_size:
                errors.append(f"Payload too large: {size} bytes (max {max_payload_size})")

        # Layer 3: Request headers validation
        suspicious_headers = ['x-forwarded-for', 'x-real-ip']
        for header in suspicious_headers:
            if header in request.headers:
                warnings.append(f"Suspicious header detected: {header}")

        # Layer 4: User-Agent validation
        user_agent = request.headers.get("user-agent", "")
        if not user_agent:
            warnings.append("Missing User-Agent header")
        elif len(user_agent) > 500:
            warnings.append("Unusually long User-Agent header")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Get client IP with multiple fallbacks."""
        # Try different headers for client IP
        ip_headers = [
            request.headers.get("x-forwarded-for"),
            request.headers.get("x-real-ip"),
            request.headers.get("x-client-ip"),
            getattr(request.client, 'host', None)
        ]

        for ip in ip_headers:
            if ip:
                # Handle comma-separated IPs (from proxies)
                ip = ip.split(',')[0].strip()
                try:
                    # Validate IP format
                    ipaddress.ip_address(ip)
                    return ip
                except ValueError:
                    continue

        return None

    async def _is_whitelisted_ip(self, ip: str) -> bool:
        """Check if IP is in whitelist."""
        return await self.redis.sismember("ip_whitelist", ip)

    async def _is_blacklisted_ip(self, ip: str) -> bool:
        """Check if IP is blacklisted."""
        return await self.redis.sismember("ip_blacklist", ip)

    async def _is_token_revoked(self, jti: str) -> bool:
        """Check if token is revoked."""
        return await self.redis.sismember("revoked_tokens", jti)

    async def _is_user_active(self, user_id: str) -> bool:
        """Check if user account is active."""
        # This would typically query the database
        return True  # Simplified for example
```

### Layer 5: Application Layer Security

```python
"""
Fifth line of defense: Application-level security controls
"""

from typing import Any, Dict, List, Optional
import asyncio
import json
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager


class ApplicationSecurityLayer:
    """Application-level security controls and monitoring."""

    def __init__(self, redis_client, db_pool):
        self.redis = redis_client
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def security_context(self, user_id: str, action: str, resource: str):
        """Security context manager with comprehensive logging."""
        session_id = self._generate_session_id()
        start_time = datetime.utcnow()

        # Log action start
        await self._log_security_event({
            'session_id': session_id,
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'event_type': 'action_start',
            'timestamp': start_time,
            'ip_address': self._get_current_ip()
        })

        try:
            yield session_id
            # Log successful completion
            await self._log_security_event({
                'session_id': session_id,
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'event_type': 'action_success',
                'timestamp': datetime.utcnow(),
                'duration': (datetime.utcnow() - start_time).total_seconds()
            })

        except Exception as e:
            # Log failure
            await self._log_security_event({
                'session_id': session_id,
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'event_type': 'action_failure',
                'timestamp': datetime.utcnow(),
                'error': str(e),
                'duration': (datetime.utcnow() - start_time).total_seconds()
            })
            raise

    async def validate_user_permissions(
        self,
        user_id: str,
        required_permissions: List[str],
        resource_id: Optional[str] = None
    ) -> ValidationResult:
        """Multi-layer permission validation."""
        errors = []
        warnings = []

        # Layer 1: User existence validation
        user_active = await self._is_user_active(user_id)
        if not user_active:
            errors.append("User account is not active")
            return ValidationResult(False, errors, warnings)

        # Layer 2: Permission cache check
        cache_key = f"user_permissions:{user_id}"
        cached_permissions = await self.redis.get(cache_key)

        if cached_permissions:
            user_permissions = json.loads(cached_permissions)
        else:
            # Layer 3: Database permission lookup
            user_permissions = await self._get_user_permissions(user_id)
            # Cache for 15 minutes
            await self.redis.setex(cache_key, 900, json.dumps(user_permissions))

        # Layer 4: Required permission validation
        missing_permissions = []
        for required_perm in required_permissions:
            if required_perm not in user_permissions:
                missing_permissions.append(required_perm)

        if missing_permissions:
            errors.append(f"Missing permissions: {', '.join(missing_permissions)}")

        # Layer 5: Resource-specific permission validation
        if resource_id:
            resource_access = await self._validate_resource_access(
                user_id, resource_id, required_permissions
            )
            if not resource_access.is_valid:
                errors.extend(resource_access.errors)

        # Layer 6: Time-based permission validation
        time_validation = await self._validate_time_based_permissions(
            user_id, required_permissions
        )
        if not time_validation.is_valid:
            errors.extend(time_validation.errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def detect_anomalous_behavior(
        self,
        user_id: str,
        action: str,
        metadata: Dict[str, Any]
    ) -> ValidationResult:
        """Multi-layer anomaly detection."""
        errors = []
        warnings = []

        # Layer 1: Unusual activity pattern detection
        activity_check = await self._check_unusual_activity_pattern(user_id, action)
        if not activity_check.is_valid:
            warnings.extend(activity_check.warnings)

        # Layer 2: Geographical anomaly detection
        current_ip = metadata.get('ip_address')
        if current_ip:
            geo_check = await self._check_geographical_anomaly(user_id, current_ip)
            if not geo_check.is_valid:
                warnings.extend(geo_check.warnings)

        # Layer 3: Device fingerprint validation
        device_fingerprint = metadata.get('device_fingerprint')
        if device_fingerprint:
            device_check = await self._check_device_anomaly(user_id, device_fingerprint)
            if not device_check.is_valid:
                warnings.extend(device_check.warnings)

        # Layer 4: Time-based anomaly detection
        time_check = await self._check_time_anomaly(user_id, action)
        if not time_check.is_valid:
            warnings.extend(time_check.warnings)

        # Layer 5: Volume anomaly detection
        volume_check = await self._check_volume_anomaly(user_id, action)
        if not volume_check.is_valid:
            if volume_check.severity == ValidationSeverity.CRITICAL:
                errors.extend(volume_check.errors)
            else:
                warnings.extend(volume_check.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=ValidationSeverity.WARNING if warnings else ValidationSeverity.INFO
        )

    async def _log_security_event(self, event: Dict[str, Any]):
        """Log security events for monitoring and analysis."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO security_events (
                    session_id, user_id, action, resource, event_type,
                    timestamp, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """,
                event.get('session_id'),
                event.get('user_id'),
                event.get('action'),
                event.get('resource'),
                event.get('event_type'),
                event.get('timestamp'),
                json.dumps(event)
            )

    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions from database."""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetch("""
                SELECT p.name
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = $1 AND ur.is_active = TRUE
            """, user_id)

            return [row['name'] for row in result]

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return secrets.token_urlsafe(32)

    def _get_current_ip(self) -> Optional[str]:
        """Get current request IP (simplified)."""
        return "127.0.0.1"  # Placeholder
```

## Project-Specific Implementation for EnterpriseHub

### For GHL Real Estate AI

```python
"""
Defense in depth implementation for GHL Real Estate AI project
"""

class GHLRealEstateSecurityLayer:
    """Security layer specific to GHL Real Estate AI."""

    def __init__(self, ghl_api_client, db_pool, redis_client):
        self.ghl_api = ghl_api_client
        self.db_pool = db_pool
        self.redis = redis_client
        self.input_validator = InputValidator(strict_mode=True)

    async def validate_property_search_input(
        self,
        search_criteria: Dict[str, Any]
    ) -> ValidationResult:
        """Multi-layer property search validation."""
        errors = []
        warnings = []

        # Layer 1: Required fields validation
        required_fields = ['budget_max', 'location']
        for field in required_fields:
            if field not in search_criteria:
                errors.append(f"Required field '{field}' missing")

        # Layer 2: Budget validation
        if 'budget_max' in search_criteria:
            budget_validation = self.input_validator.validate_numeric_input(
                search_criteria['budget_max'],
                min_value=50000,
                max_value=10000000
            )
            if not budget_validation.is_valid:
                errors.extend(budget_validation.errors)

        # Layer 3: Location validation
        if 'location' in search_criteria:
            location_validation = await self._validate_location(
                search_criteria['location']
            )
            if not location_validation.is_valid:
                errors.extend(location_validation.errors)

        # Layer 4: Search frequency validation (prevent abuse)
        user_id = search_criteria.get('user_id')
        if user_id:
            frequency_check = await self._check_search_frequency(user_id)
            if not frequency_check.is_valid:
                errors.extend(frequency_check.errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def validate_ghl_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: str
    ) -> ValidationResult:
        """Multi-layer GHL webhook validation."""
        errors = []
        warnings = []

        # Layer 1: Signature validation
        signature_validation = await self._validate_ghl_signature(
            webhook_data, signature
        )
        if not signature_validation.is_valid:
            errors.extend(signature_validation.errors)

        # Layer 2: Webhook structure validation
        required_fields = ['type', 'data', 'timestamp']
        for field in required_fields:
            if field not in webhook_data:
                errors.append(f"Webhook missing required field: {field}")

        # Layer 3: Timestamp validation (prevent replay attacks)
        if 'timestamp' in webhook_data:
            timestamp_validation = self._validate_webhook_timestamp(
                webhook_data['timestamp']
            )
            if not timestamp_validation.is_valid:
                errors.extend(timestamp_validation.errors)

        # Layer 4: Data validation based on webhook type
        webhook_type = webhook_data.get('type')
        if webhook_type:
            type_validation = await self._validate_webhook_by_type(
                webhook_type, webhook_data.get('data', {})
            )
            if not type_validation.is_valid:
                errors.extend(type_validation.errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def validate_ai_model_input(
        self,
        model_input: Dict[str, Any]
    ) -> ValidationResult:
        """Multi-layer AI model input validation."""
        errors = []
        warnings = []

        # Layer 1: Input size validation
        input_str = json.dumps(model_input)
        if len(input_str) > 100000:  # 100KB limit
            errors.append("AI model input too large")

        # Layer 2: Content validation
        if 'prompt' in model_input:
            content_validation = self.input_validator.sanitize_html_input(
                model_input['prompt']
            )
            if not content_validation.is_valid:
                errors.extend(content_validation.errors)

        # Layer 3: Rate limiting for AI requests
        user_id = model_input.get('user_id')
        if user_id:
            ai_rate_limit = await self._check_ai_request_rate_limit(user_id)
            if not ai_rate_limit.is_valid:
                errors.extend(ai_rate_limit.errors)

        # Layer 4: Content policy validation
        if 'prompt' in model_input:
            policy_check = await self._validate_content_policy(
                model_input['prompt']
            )
            if not policy_check.is_valid:
                errors.extend(policy_check.errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def _validate_location(self, location: str) -> ValidationResult:
        """Validate location input for property search."""
        errors = []

        # Basic validation
        if len(location) < 2:
            errors.append("Location too short")

        if len(location) > 100:
            errors.append("Location too long")

        # Check for valid location format (simplified)
        location_pattern = re.compile(r'^[a-zA-Z0-9\s,.-]+$')
        if not location_pattern.match(location):
            errors.append("Location contains invalid characters")

        return ValidationResult(len(errors) == 0, errors, [])

    async def _check_search_frequency(self, user_id: str) -> ValidationResult:
        """Check property search frequency to prevent abuse."""
        key = f"search_frequency:{user_id}"
        current_count = await self.redis.get(key)

        if current_count is None:
            await self.redis.setex(key, 3600, 1)  # 1 hour window
            return ValidationResult(True, [], [])

        current_count = int(current_count)
        if current_count >= 50:  # Max 50 searches per hour
            return ValidationResult(
                False,
                ["Search frequency limit exceeded"],
                []
            )

        await self.redis.incr(key)
        return ValidationResult(True, [], [])

    async def _validate_ghl_signature(
        self,
        webhook_data: Dict[str, Any],
        signature: str
    ) -> ValidationResult:
        """Validate GHL webhook signature."""
        # Implementation would verify webhook signature
        # This is a simplified example
        if not signature:
            return ValidationResult(False, ["Missing webhook signature"], [])

        return ValidationResult(True, [], [])

    def _validate_webhook_timestamp(self, timestamp: int) -> ValidationResult:
        """Validate webhook timestamp to prevent replay attacks."""
        current_time = int(time.time())
        time_diff = abs(current_time - timestamp)

        # Allow 5 minutes tolerance
        if time_diff > 300:
            return ValidationResult(
                False,
                ["Webhook timestamp too old or invalid"],
                []
            )

        return ValidationResult(True, [], [])
```

## Best Practices

1. **Layer Independence**: Each validation layer should be independent and not rely on previous layers
2. **Fail Fast**: Return early on critical validation failures
3. **Comprehensive Logging**: Log all validation events for security monitoring
4. **Rate Limiting**: Implement rate limiting at multiple levels
5. **Input Sanitization**: Sanitize all inputs before processing
6. **Principle of Least Privilege**: Grant minimum necessary permissions
7. **Regular Security Audits**: Regularly review and update validation rules

This defense-in-depth approach provides comprehensive protection against various attack vectors and system failures by implementing multiple independent layers of validation and security controls.