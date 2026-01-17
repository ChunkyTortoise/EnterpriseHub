# Layer 1: Input Validation and Sanitization

## Complete Implementation Reference

This layer provides the first line of defense with comprehensive input validation and sanitization strategies.

### Email Validation

```python
"""
Multi-layer email validation with comprehensive checks.
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

    def _is_disposable_email(self, email: str) -> bool:
        """Check against list of disposable email domains."""
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com'
        ]
        domain = email.split('@')[1].lower()
        return domain in disposable_domains

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

    def validate_url(self, url: str) -> ValidationResult:
        """Multi-layer URL validation."""
        errors = []
        warnings = []

        if not url or not isinstance(url, str):
            errors.append("URL must be a non-empty string")
            return ValidationResult(False, errors, warnings)

        url = url.strip()

        # Layer 1: Protocol validation
        if not url.startswith(('http://', 'https://')):
            errors.append("URL must start with http:// or https://")

        # Layer 2: Length validation
        if len(url) > 2048:
            errors.append("URL too long (max 2048 characters)")

        # Layer 3: Format validation
        url_pattern = re.compile(
            r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?$'
        )
        if not url_pattern.match(url):
            errors.append("Invalid URL format")

        # Layer 4: Dangerous pattern detection
        dangerous_patterns = ['javascript:', 'data:', 'file:', 'vbscript:']
        if any(pattern in url.lower() for pattern in dangerous_patterns):
            errors.append("URL contains dangerous protocol")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data=url if len(errors) == 0 else None
        )
```

## Best Practices

1. **Always sanitize inputs** before any processing
2. **Use type validation** as the first layer
3. **Implement length checks** to prevent buffer overflows
4. **Check for dangerous patterns** (XSS, SQL injection attempts)
5. **Return ValidationResult** with structured error information
6. **Use severity levels** to prioritize security issues
7. **Log all validation failures** for security monitoring
