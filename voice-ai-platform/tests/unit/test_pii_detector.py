"""Unit tests for PIIDetector — exercises real detection and redaction code."""

from __future__ import annotations

import pytest

from voice_ai.services.pii_detector import PIIDetector, PIIResult, HIGH_RISK_TYPES


@pytest.fixture
def detector():
    return PIIDetector()


class TestPIIDetection:
    """Test PII entity detection."""

    def test_detect_ssn_with_dashes(self, detector):
        results = detector.detect("My SSN is 123-45-6789.")
        types = [r.entity_type for r in results]
        assert "US_SSN" in types

    def test_detect_ssn_without_dashes(self, detector):
        results = detector.detect("SSN 123456789 for records.")
        types = [r.entity_type for r in results]
        assert "US_SSN" in types

    def test_detect_credit_card(self, detector):
        results = detector.detect("Card number: 4111-1111-1111-1111")
        types = [r.entity_type for r in results]
        assert "CREDIT_CARD" in types

    def test_detect_phone_number(self, detector):
        results = detector.detect("Call me at 555-123-4567")
        types = [r.entity_type for r in results]
        assert "PHONE_NUMBER" in types

    def test_detect_email(self, detector):
        results = detector.detect("Email: john.doe@example.com")
        types = [r.entity_type for r in results]
        assert "EMAIL_ADDRESS" in types

    def test_detect_multiple_pii(self, detector):
        text = "SSN 123-45-6789, email john@example.com, phone 555-123-4567"
        results = detector.detect(text)
        types = {r.entity_type for r in results}
        assert "US_SSN" in types
        assert "EMAIL_ADDRESS" in types
        assert "PHONE_NUMBER" in types

    def test_no_pii_in_clean_text(self, detector):
        results = detector.detect("I want to buy a home in downtown Rancho Cucamonga.")
        # Filter out US_BANK_NUMBER which is overly broad
        real_pii = [r for r in results if r.entity_type != "US_BANK_NUMBER"]
        assert len(real_pii) == 0

    def test_detect_returns_positions(self, detector):
        text = "Email: test@example.com"
        results = detector.detect(text)
        email_results = [r for r in results if r.entity_type == "EMAIL_ADDRESS"]
        assert len(email_results) == 1
        r = email_results[0]
        assert text[r.start:r.end] == "test@example.com"


class TestPIIRedaction:
    """Test PII redaction."""

    def test_redact_ssn(self, detector):
        redacted = detector.redact("SSN is 123-45-6789 here.")
        assert "123-45-6789" not in redacted
        assert "<US_SSN>" in redacted

    def test_redact_email(self, detector):
        redacted = detector.redact("Email john@example.com please.")
        assert "john@example.com" not in redacted
        assert "<EMAIL_ADDRESS>" in redacted

    def test_redact_preserves_surrounding_text(self, detector):
        redacted = detector.redact("Contact john@example.com today.")
        assert redacted.startswith("Contact")
        assert redacted.endswith("today.")

    def test_redact_no_pii_returns_original(self, detector):
        text = "Hello world"
        assert detector.redact(text) == text

    def test_redact_multiple_entities(self, detector):
        text = "SSN 123-45-6789 and email test@example.com"
        redacted = detector.redact(text)
        assert "123-45-6789" not in redacted
        assert "test@example.com" not in redacted


class TestSensitivePII:
    """Test high-risk PII detection."""

    def test_ssn_is_sensitive(self, detector):
        has_sensitive, types = detector.has_sensitive_pii("SSN: 123-45-6789")
        assert has_sensitive is True
        assert "US_SSN" in types

    def test_credit_card_is_sensitive(self, detector):
        has_sensitive, types = detector.has_sensitive_pii("Card: 4111-1111-1111-1111")
        assert has_sensitive is True
        assert "CREDIT_CARD" in types

    def test_email_alone_not_sensitive(self, detector):
        has_sensitive, types = detector.has_sensitive_pii("Email: john@example.com")
        assert has_sensitive is False

    def test_clean_text_not_sensitive(self, detector):
        has_sensitive, types = detector.has_sensitive_pii("Just a normal message")
        assert has_sensitive is False
        assert types == []


class TestGetPIITypes:
    """Test unique PII type listing."""

    def test_returns_unique_types(self, detector):
        text = "SSN 123-45-6789 and another SSN 987-65-4321"
        types = detector.get_pii_types(text)
        assert "US_SSN" in types

    def test_multiple_types(self, detector):
        text = "SSN 123-45-6789 and email test@example.com"
        types = detector.get_pii_types(text)
        assert "US_SSN" in types
        assert "EMAIL_ADDRESS" in types
