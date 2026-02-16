"""Tests for PII detection and redaction."""

import pytest

from rag_service.compliance.pii_detector import PIIDetector, PIIEntity, PIIScanResult


@pytest.fixture
def pii_detector():
    """PII detector with regex patterns (no Presidio)."""
    return PIIDetector(use_presidio=False)


class TestPIIDetector:
    """Test PII detection using regex patterns."""

    def test_detect_email(self, pii_detector):
        """Test email detection."""
        # Arrange
        text = "Contact me at john.doe@example.com for more info."

        # Act
        result = pii_detector.scan(text)

        # Assert
        assert result.has_pii is True
        assert len(result.entities) == 1
        assert result.entities[0].entity_type == "EMAIL"
        assert result.entities[0].text == "john.doe@example.com"
        assert "john.doe@example.com" not in result.redacted_text
        assert "[EMAIL]" in result.redacted_text

    def test_detect_phone_number(self, pii_detector):
        """Test phone number detection."""
        # Arrange
        text = "Call me at 555-123-4567 or 555-987-6543."

        # Act
        result = pii_detector.scan(text)

        # Assert
        assert result.has_pii is True
        assert len(result.entities) == 2
        assert all(e.entity_type == "PHONE" for e in result.entities)
        assert "555-123-4567" in [e.text for e in result.entities]

    def test_detect_ssn(self, pii_detector):
        """Test SSN detection."""
        # Arrange
        text = "My SSN is 123-45-6789."

        # Act
        result = pii_detector.scan(text)

        # Assert
        assert result.has_pii is True
        assert any(e.entity_type == "SSN" for e in result.entities)
        assert any("123-45-6789" in e.text for e in result.entities)

    def test_detect_credit_card(self, pii_detector):
        """Test credit card detection."""
        # Arrange
        text = "Pay with card 4532-1234-5678-9010."

        # Act
        result = pii_detector.scan(text)

        # Assert
        assert result.has_pii is True
        assert any(e.entity_type == "CREDIT_CARD" for e in result.entities)

    def test_detect_ip_address(self, pii_detector):
        """Test IP address detection."""
        # Arrange
        text = "Server at 192.168.1.100 is down."

        # Act
        result = pii_detector.scan(text)

        # Assert
        assert result.has_pii is True
        assert any(e.entity_type == "IP_ADDRESS" for e in result.entities)
        assert any("192.168.1.100" in e.text for e in result.entities)

    def test_detect_multiple_pii_types(self, pii_detector):
        """Test detecting multiple PII types in one text."""
        # Arrange
        text = "Email: admin@example.com, Phone: 555-123-1234, SSN: 111-22-3333"

        # Act
        result = pii_detector.scan(text)

        # Assert
        assert result.has_pii is True
        assert len(result.entities) >= 3
        entity_types = {e.entity_type for e in result.entities}
        assert "EMAIL" in entity_types
        assert "PHONE" in entity_types
        assert "SSN" in entity_types

    def test_no_pii_detected(self, pii_detector):
        """Test text without PII."""
        # Arrange
        text = "This is a normal sentence about real estate markets."

        # Act
        result = pii_detector.scan(text)

        # Assert
        assert result.has_pii is False
        assert len(result.entities) == 0
        assert result.redacted_text == text

    def test_redaction_preserves_structure(self, pii_detector):
        """Test that redaction maintains text structure."""
        # Arrange
        text = "Contact: john@example.com\nPhone: 555-123-4567"

        # Act
        redacted = pii_detector.redact(text)

        # Assert
        assert "\n" in redacted  # Preserves newline
        assert "[EMAIL]" in redacted
        assert "[PHONE]" in redacted
        assert "john@example.com" not in redacted
        assert "555-123-4567" not in redacted

    def test_entity_counts(self, pii_detector):
        """Test entity count aggregation."""
        # Arrange
        text = """
        User 1: alice@example.com, 555-111-1111
        User 2: bob@example.com, 555-222-2222
        User 3: charlie@example.com, 555-333-3333
        """

        # Act
        result = pii_detector.scan(text)

        # Assert
        assert result.entity_counts["EMAIL"] == 3
        assert result.entity_counts["PHONE"] == 3

    def test_entity_positions(self, pii_detector):
        """Test that entity positions are correctly identified."""
        # Arrange
        text = "Email me at test@example.com today."

        # Act
        result = pii_detector.scan(text)

        # Assert
        entity = result.entities[0]
        assert entity.start == text.index("test@example.com")
        assert entity.end == entity.start + len("test@example.com")
        assert text[entity.start : entity.end] == "test@example.com"

    def test_overlapping_patterns(self, pii_detector):
        """Test handling of potentially overlapping patterns."""
        # Arrange
        text = "123.45.67.89 could be IP or number"

        # Act
        result = pii_detector.scan(text)

        # Assert
        assert result.has_pii is True
        # Should detect as IP address
        assert any(e.entity_type == "IP_ADDRESS" for e in result.entities)


class TestPIIEntity:
    """Test PIIEntity data model."""

    def test_entity_creation(self):
        """Test creating a PII entity."""
        entity = PIIEntity(
            entity_type="EMAIL",
            text="test@example.com",
            start=10,
            end=26,
            score=0.95,
        )

        assert entity.entity_type == "EMAIL"
        assert entity.text == "test@example.com"
        assert entity.start == 10
        assert entity.end == 26
        assert entity.score == 0.95

    def test_entity_default_score(self):
        """Test PII entity with default score."""
        entity = PIIEntity(
            entity_type="PHONE",
            text="555-1234",
            start=0,
            end=8,
        )

        assert entity.score == 1.0


class TestPIIScanResult:
    """Test PIIScanResult data model."""

    def test_scan_result_creation(self):
        """Test creating a scan result."""
        result = PIIScanResult(
            has_pii=True,
            entities=[
                PIIEntity(
                    entity_type="EMAIL",
                    text="test@example.com",
                    start=0,
                    end=16,
                )
            ],
            redacted_text="Contact: [EMAIL]",
            entity_counts={"EMAIL": 1},
        )

        assert result.has_pii is True
        assert len(result.entities) == 1
        assert result.redacted_text == "Contact: [EMAIL]"
        assert result.entity_counts["EMAIL"] == 1

    def test_scan_result_defaults(self):
        """Test scan result with default values."""
        result = PIIScanResult(has_pii=False)

        assert result.entities == []
        assert result.redacted_text == ""
        assert result.entity_counts == {}


class TestPIIDetectorWithPresidio:
    """Test PII detector with Presidio (if available)."""

    def test_presidio_fallback(self):
        """Test fallback to regex when Presidio not available."""
        # Arrange
        detector = PIIDetector(use_presidio=True)

        # Act - if Presidio import fails, should fall back to regex
        text = "Email: test@example.com"
        result = detector.scan(text)

        # Assert - should still work
        assert result.has_pii is True
        assert any(e.entity_type == "EMAIL" for e in result.entities)
