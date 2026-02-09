"""Tests for PII redaction utility."""

import pytest

from ghl_real_estate_ai.utils.pii_redactor import PIIRedactor

@pytest.mark.unit


class TestPIIRedactor:
    """Tests for the PIIRedactor class."""

    def test_redact_phone_formats(self):
        """Phone numbers in xxx-xxx-xxxx, (xxx) xxx-xxxx, and xxxxxxxxxx formats are redacted."""
        # Dashed format
        assert PIIRedactor.redact_phone("Call me at 555-123-4567") == "Call me at ***-***-4567"

        # Parenthesized format
        assert PIIRedactor.redact_phone("Call me at (555) 123-4567") == "Call me at ***-***-4567"

        # Continuous digits
        assert PIIRedactor.redact_phone("Call me at 5551234567") == "Call me at ***-***-4567"

        # Dotted format
        assert PIIRedactor.redact_phone("Call me at 555.123.4567") == "Call me at ***-***-4567"

    def test_redact_email(self):
        """Standard and subdomain email addresses are redacted."""
        # Standard email
        assert PIIRedactor.redact_email("Email jane.doe@example.com") == "Email j***@***.com"

        # Subdomain email
        assert PIIRedactor.redact_email("Contact admin@mail.corp.org") == "Contact a***@***.org"

        # Short local part
        assert PIIRedactor.redact_email("Reach a@test.net") == "Reach a***@***.net"

    def test_redact_ssn(self):
        """SSN in xxx-xx-xxxx format is redacted, preserving last 4 digits."""
        assert PIIRedactor.redact_ssn("SSN: 123-45-6789") == "SSN: ***-**-6789"
        assert PIIRedactor.redact_ssn("My SSN is 000-00-0001 ok") == "My SSN is ***-**-0001 ok"

    def test_redact_all_mixed(self):
        """Text with phone, email, and SSN all redacted in a single pass."""
        text = (
            "Contact John at 555-123-4567, email john@example.com, SSN 123-45-6789."
        )
        result = PIIRedactor.redact_all(text)

        assert "555-123-4567" not in result
        assert "john@example.com" not in result
        assert "123-45-6789" not in result

        # Verify the masked values are present
        assert "***-***-4567" in result
        assert "j***@***.com" in result
        assert "***-**-6789" in result

    def test_safe_log_deep_copy(self):
        """safe_log returns a redacted copy and leaves the original dict unchanged."""
        original = {
            "name": "Jane",
            "phone": "555-123-4567",
            "email": "jane@example.com",
        }
        original_copy = original.copy()

        redacted = PIIRedactor.safe_log(original)

        # Original must be unchanged
        assert original == original_copy

        # Redacted version must have masked values
        assert redacted["phone"] == "***-***-4567"
        assert redacted["email"] == "j***@***.com"

        # Non-PII fields pass through
        assert redacted["name"] == "Jane"

    def test_safe_log_nested_dicts(self):
        """safe_log handles nested dict structures and lists of strings."""
        original = {
            "contact": {
                "phone": "555-123-4567",
                "email": "jane@example.com",
            },
            "notes": ["Call 555-999-0000 for info", "No PII here"],
            "score": 85,
        }

        redacted = PIIRedactor.safe_log(original)

        # Nested dict values redacted
        assert redacted["contact"]["phone"] == "***-***-4567"
        assert redacted["contact"]["email"] == "j***@***.com"

        # List string values redacted
        assert "***-***-0000" in redacted["notes"][0]
        assert redacted["notes"][1] == "No PII here"

        # Non-string values preserved
        assert redacted["score"] == 85

    def test_no_false_positives(self):
        """Dollar amounts and date strings are NOT redacted as phone numbers or SSNs."""
        text = "Listed at $500,000 on 2026-02-08 with 3.5% rate"
        result = PIIRedactor.redact_all(text)

        assert "$500,000" in result
        assert "2026-02-08" in result
        assert "3.5%" in result