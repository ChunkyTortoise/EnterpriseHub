"""PII redaction utility for log safety."""

import copy
import re
from typing import Any, Dict

# Patterns
PHONE_PATTERN = re.compile(r"\b(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})\b")
PHONE_PARENS_PATTERN = re.compile(r"\((\d{3})\)\s*(\d{3})[-.\s]?(\d{4})")
EMAIL_PATTERN = re.compile(r"\b([\w])([\w.-]*)@([\w.-]+)\.(\w+)\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-(\d{4})\b")


class PIIRedactor:
    """Redacts personally identifiable information from text and data structures."""

    @staticmethod
    def redact_phone(text: str) -> str:
        """Mask phone numbers to ***-***-XXXX format, preserving last 4 digits."""
        text = PHONE_PARENS_PATTERN.sub(r"***-***-\3", text)
        text = PHONE_PATTERN.sub(r"***-***-\3", text)
        return text

    @staticmethod
    def redact_email(text: str) -> str:
        """Mask emails to first_char***@***.tld format."""

        def _mask_email(match):
            first_char = match.group(1)
            tld = match.group(4)
            return f"{first_char}***@***.{tld}"

        return EMAIL_PATTERN.sub(_mask_email, text)

    @staticmethod
    def redact_ssn(text: str) -> str:
        """Mask SSNs to ***-**-XXXX format, preserving last 4."""
        return SSN_PATTERN.sub(r"***-**-\1", text)

    @classmethod
    def redact_all(cls, text: str) -> str:
        """Apply all PII redactions to text."""
        text = cls.redact_ssn(text)
        text = cls.redact_phone(text)
        text = cls.redact_email(text)
        return text

    @classmethod
    def safe_log(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deep-copy a dict and redact all string values. Original unchanged."""
        result = copy.deepcopy(data)
        cls._redact_dict(result)
        return result

    @classmethod
    def _redact_dict(cls, d: Dict[str, Any]) -> None:
        """Recursively redact string values in a dict (in-place on the copy)."""
        for key, value in d.items():
            if isinstance(value, str):
                d[key] = cls.redact_all(value)
            elif isinstance(value, dict):
                cls._redact_dict(value)
            elif isinstance(value, list):
                d[key] = [cls.redact_all(item) if isinstance(item, str) else item for item in value]
