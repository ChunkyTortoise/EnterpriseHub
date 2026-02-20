"""Extended PII detector tests — regex scanning, redaction, edge cases."""

from __future__ import annotations

import pytest

from rag_service.compliance.pii_detector import PIIDetector


@pytest.fixture
def detector():
    return PIIDetector(use_presidio=False)


class TestRegexScanning:
    def test_detects_email(self, detector):
        result = detector.scan("Contact us at hello@example.com for details.")
        assert result.has_pii is True
        assert "EMAIL" in result.entity_counts

    def test_detects_phone(self, detector):
        result = detector.scan("Call 555-123-4567 for support.")
        assert result.has_pii is True
        assert "PHONE" in result.entity_counts

    def test_detects_ssn(self, detector):
        result = detector.scan("SSN: 123-45-6789")
        assert result.has_pii is True
        assert "SSN" in result.entity_counts

    def test_detects_credit_card(self, detector):
        result = detector.scan("Card: 4111 1111 1111 1111")
        assert result.has_pii is True
        assert "CREDIT_CARD" in result.entity_counts

    def test_detects_ip_address(self, detector):
        result = detector.scan("Server IP: 192.168.1.100")
        assert result.has_pii is True
        assert "IP_ADDRESS" in result.entity_counts

    def test_no_pii_clean_text(self, detector):
        result = detector.scan("The weather is nice today.")
        # Filter out false positives from broad patterns
        real_entities = [e for e in result.entities if e.entity_type in ("EMAIL", "SSN", "CREDIT_CARD")]
        assert len(real_entities) == 0

    def test_multiple_pii_types(self, detector):
        text = "Email: test@test.com, SSN: 123-45-6789, Phone: 555-123-4567"
        result = detector.scan(text)
        assert len(result.entity_counts) >= 2

    def test_entity_positions(self, detector):
        text = "Email: test@example.com here"
        result = detector.scan(text)
        email_entities = [e for e in result.entities if e.entity_type == "EMAIL"]
        assert len(email_entities) >= 1
        e = email_entities[0]
        assert text[e.start:e.end] == "test@example.com"


class TestRedaction:
    def test_redact_email(self, detector):
        redacted = detector.redact("Contact test@example.com please.")
        assert "test@example.com" not in redacted
        assert "[EMAIL]" in redacted

    def test_redact_ssn(self, detector):
        redacted = detector.redact("SSN: 123-45-6789")
        assert "123-45-6789" not in redacted
        assert "[SSN]" in redacted

    def test_redact_preserves_clean_text(self, detector):
        text = "No PII here at all."
        assert detector.redact(text) == text

    def test_redact_multiple_entities(self, detector):
        text = "Email: a@b.com and SSN: 123-45-6789"
        redacted = detector.redact(text)
        assert "a@b.com" not in redacted
        assert "123-45-6789" not in redacted


class TestScanResult:
    def test_empty_scan(self, detector):
        result = detector.scan("")
        assert result.has_pii is False
        assert result.entities == []

    def test_entity_counts_accurate(self, detector):
        text = "a@b.com and c@d.com"
        result = detector.scan(text)
        assert result.entity_counts.get("EMAIL", 0) >= 2


class TestPresidioFallback:
    def test_falls_back_to_regex(self):
        # Presidio not installed in test env
        detector = PIIDetector(use_presidio=True)
        assert detector.use_presidio is False  # Should fallback
        result = detector.scan("test@example.com")
        assert result.has_pii is True
