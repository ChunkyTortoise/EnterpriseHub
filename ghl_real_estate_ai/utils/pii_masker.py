"""PII masking utilities for log sanitization."""

import re

_PHONE_PATTERN = re.compile(r"\b(\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def mask_phone(text: str) -> str:
    """Replace phone numbers with masked version (keeps last 4 digits)."""

    def _replace(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group())
        return f"***-***-{digits[-4:]}" if len(digits) >= 4 else "***-***-****"

    return _PHONE_PATTERN.sub(_replace, text)


def mask_email(text: str) -> str:
    """Replace email addresses with masked version (keeps domain)."""

    def _replace(m: re.Match) -> str:
        parts = m.group().split("@")
        return f"***@{parts[1]}" if len(parts) == 2 else "***@***.***"

    return _EMAIL_PATTERN.sub(_replace, text)


def mask_ssn(text: str) -> str:
    """Replace SSN patterns with masked version."""
    return _SSN_PATTERN.sub("***-**-****", text)


def mask_pii(text: str) -> str:
    """Apply all PII masks to text."""
    text = mask_phone(text)
    text = mask_email(text)
    text = mask_ssn(text)
    return text
