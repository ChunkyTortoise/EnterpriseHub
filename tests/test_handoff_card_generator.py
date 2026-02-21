"""Tests for Warm Handoff Card Generator

Tests PDF generation, performance, content validation, and integration
with handoff service data structures.
"""

import io
import time
from datetime import datetime, timezone
from typing import Any, Dict

import pytest

# Skip all tests in this module if PyPDF2 is not installed
pytest.importorskip("PyPDF2")

from PyPDF2 import PdfReader

from ghl_real_estate_ai.services.jorge.handoff_card_generator import (
    HandoffCardGenerator,
    generate_card,
)
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    EnrichedHandoffContext as HandoffContext,
)


@pytest.fixture
def sample_handoff_data() -> Dict[str, Any]:
    """Sample handoff data for testing."""
    return {
        "contact_id": "test_contact_123",
        "contact_name": "John Doe",
        "contact_email": "john.doe@example.com",
        "contact_phone": "+1-555-0123",
        "source_bot": "lead",
        "target_bot": "buyer",
        "confidence": 0.85,
        "enriched_context": {
            "source_qualification_score": 78.5,
            "source_temperature": "warm",
            "budget_range": {"min": 400000, "max": 550000},
            "property_address": None,
            "cma_summary": None,
            "conversation_summary": "Interested buyer looking for 3BR home in Rancho Cucamonga. Pre-approved with local lender. Timeline: 3-6 months.",
            "key_insights": {
                "budget_confirmed": True,
                "timeline": "3-6 months",
                "bedrooms": 3,
                "location_preference": "Rancho Cucamonga",
                "pre_approval": True,
            },
            "urgency_level": "3_months",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@pytest.fixture
def sample_enriched_context() -> HandoffContext:
    """Sample EnrichedHandoffContext dataclass."""
    return HandoffContext(
        source_qualification_score=78.5,
        source_temperature="warm",
        budget_range={"min": 400000, "max": 550000},
        property_address=None,
        cma_summary=None,
        conversation_summary="Interested buyer looking for 3BR home in Rancho Cucamonga. Pre-approved with local lender. Timeline: 3-6 months.",
        key_insights={
            "budget_confirmed": True,
            "timeline": "3-6 months",
            "bedrooms": 3,
            "location_preference": "Rancho Cucamonga",
            "pre_approval": True,
        },
        urgency_level="3_months",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


class TestHandoffCardGenerator:
    """Test HandoffCardGenerator class."""

    def test_generate_card_returns_pdf_bytes(self, sample_handoff_data):
        """Test that generate_card returns valid PDF bytes."""
        pdf_bytes = generate_card(sample_handoff_data)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")  # PDF signature

    def test_generate_card_performance_under_2s(self, sample_handoff_data):
        """Test that card generation completes in <2 seconds."""

        start = time.time()
        pdf_bytes = generate_card(sample_handoff_data)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Card generation took {elapsed:.2f}s (target: <2s)"
        assert len(pdf_bytes) > 0

    def test_generate_card_with_enriched_context_dataclass(self, sample_enriched_context):
        """Test card generation with EnrichedHandoffContext dataclass."""

        handoff_data = {
            "contact_id": "test_123",
            "contact_name": "Jane Smith",
            "contact_email": "jane@example.com",
            "contact_phone": "+1-555-9999",
            "source_bot": "lead",
            "target_bot": "seller",
            "confidence": 0.75,
            "enriched_context": sample_enriched_context,
        }

        pdf_bytes = generate_card(handoff_data)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_generate_card_content_validation(self, sample_handoff_data):
        """Test that generated PDF contains expected content."""
        pdf_bytes = generate_card(sample_handoff_data)

        # Parse PDF and extract text
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        page_text = pdf_reader.pages[0].extract_text()

        # Verify key content is present
        assert "John Doe" in page_text
        assert "john.doe@example.com" in page_text
        assert "+1-555-0123" in page_text
        assert "Lead → Buyer" in page_text or "lead" in page_text.lower() and "buyer" in page_text.lower()
        assert "78.5" in page_text or "78" in page_text  # Qualification score
        assert "warm" in page_text.lower()
        assert "3-6 months" in page_text or "3" in page_text

    def test_generate_card_handles_missing_optional_fields(self):
        """Test card generation with minimal data (missing optional fields)."""
        minimal_data = {
            "contact_id": "min_123",
            "contact_name": "Minimal Contact",
            "source_bot": "lead",
            "target_bot": "buyer",
            "confidence": 0.7,
            "enriched_context": {
                "source_qualification_score": 65.0,
                "source_temperature": "cold",
                "conversation_summary": "",
                "key_insights": {},
                "urgency_level": "browsing",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        pdf_bytes = generate_card(minimal_data)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_generate_card_with_seller_data(self):
        """Test card generation for seller handoff with CMA data."""
        seller_data = {
            "contact_id": "seller_123",
            "contact_name": "Bob Seller",
            "contact_email": "bob@example.com",
            "contact_phone": "+1-555-7777",
            "source_bot": "lead",
            "target_bot": "seller",
            "confidence": 0.82,
            "enriched_context": {
                "source_qualification_score": 85.0,
                "source_temperature": "hot",
                "property_address": "123 Main St, Rancho Cucamonga, CA 91730",
                "cma_summary": {
                    "estimated_value": 625000,
                    "value_range": {"min": 600000, "max": 650000},
                    "comparable_sales": 5,
                },
                "conversation_summary": "Seller interested in listing property. Motivated by job relocation.",
                "key_insights": {
                    "motivation": "relocation",
                    "timeline": "immediate",
                    "property_condition": "excellent",
                },
                "urgency_level": "immediate",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        pdf_bytes = generate_card(seller_data)

        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        page_text = pdf_reader.pages[0].extract_text()

        assert "Bob Seller" in page_text
        assert "123 Main St" in page_text
        assert "625000" in page_text or "625,000" in page_text


class TestGenerateCardFunction:
    """Test the standalone generate_card() function."""

    def test_generate_card_function(self, sample_handoff_data):
        """Test standalone generate_card() function."""
        pdf_bytes = generate_card(sample_handoff_data)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    def test_generate_card_function_performance(self, sample_handoff_data):
        """Test function-level performance."""
        start = time.time()
        pdf_bytes = generate_card(sample_handoff_data)
        elapsed = time.time() - start

        assert elapsed < 2.0
        assert len(pdf_bytes) > 0


class TestPDFStructure:
    """Test PDF structure and formatting."""

    def test_pdf_has_single_page(self, sample_handoff_data):
        """Test that generated PDF has exactly one page."""
        pdf_bytes = generate_card(sample_handoff_data)

        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(pdf_reader.pages) == 1

    def test_pdf_has_metadata(self, sample_handoff_data):
        """Test that PDF includes proper metadata."""
        pdf_bytes = generate_card(sample_handoff_data)

        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        metadata = pdf_reader.metadata

        # ReportLab sets some metadata automatically
        assert metadata is not None


class TestIntegrationWithHandoffService:
    """Test integration with JorgeHandoffService data structures."""

    def test_enriched_handoff_context_compatibility(self):
        """Test compatibility with EnrichedHandoffContext from handoff service."""
        # Create EnrichedHandoffContext as it would be created by handoff service
        context = HandoffContext(
            source_qualification_score=90.0,
            source_temperature="hot",
            budget_range={"min": 500000, "max": 700000},
            property_address="456 Oak Ave, Rancho Cucamonga, CA 91730",
            cma_summary={"estimated_value": 680000},
            conversation_summary="Highly qualified buyer, pre-approved, ready to move.",
            key_insights={
                "pre_approval": True,
                "down_payment_ready": True,
                "agent_referral": True,
            },
            urgency_level="immediate",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        handoff_data = {
            "contact_id": "integ_123",
            "contact_name": "Integration Test",
            "contact_email": "test@example.com",
            "source_bot": "lead",
            "target_bot": "buyer",
            "confidence": 0.95,
            "enriched_context": context,
        }

        pdf_bytes = generate_card(handoff_data)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

        # Validate content
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        page_text = pdf_reader.pages[0].extract_text()

        assert "90" in page_text  # Qualification score
        assert "hot" in page_text.lower()
        assert "500000" in page_text or "500,000" in page_text


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_contact_name(self):
        """Test handling of missing contact name."""
        data = {
            "contact_id": "no_name_123",
            "source_bot": "lead",
            "target_bot": "buyer",
            "confidence": 0.7,
            "enriched_context": {
                "source_qualification_score": 70.0,
                "source_temperature": "warm",
                "conversation_summary": "Test",
                "key_insights": {},
                "urgency_level": "browsing",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        pdf_bytes = generate_card(data)

        # Should still generate PDF with placeholder or contact_id
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_very_long_conversation_summary(self):
        """Test handling of very long conversation summaries."""
        long_summary = " ".join(["This is a very long conversation summary."] * 50)

        data = {
            "contact_id": "long_123",
            "contact_name": "Long Summary Contact",
            "source_bot": "lead",
            "target_bot": "buyer",
            "confidence": 0.8,
            "enriched_context": {
                "source_qualification_score": 75.0,
                "source_temperature": "warm",
                "conversation_summary": long_summary,
                "key_insights": {},
                "urgency_level": "3_months",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        start = time.time()
        pdf_bytes = generate_card(data)
        elapsed = time.time() - start

        # Should still complete in <2s even with long text
        assert elapsed < 2.0
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_special_characters_in_names(self):
        """Test handling of special characters in contact names."""
        data = {
            "contact_id": "special_123",
            "contact_name": "José María O'Brien-García",
            "contact_email": "josé@example.com",
            "source_bot": "lead",
            "target_bot": "buyer",
            "confidence": 0.75,
            "enriched_context": {
                "source_qualification_score": 72.0,
                "source_temperature": "warm",
                "conversation_summary": "Contact with special characters",
                "key_insights": {},
                "urgency_level": "browsing",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        pdf_bytes = generate_card(data)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
