"""
Tests for Lead Bot Day 14 CMA PDF Email Attachment (Stream B).

Validates:
- PDF generation from CMA report via PDFRenderer
- Email delivery with PDF attachment via SendGrid
- Fallback behavior when PDF generation fails
- Day 14 flow integration with cma_attached flag
"""

import base64
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import date

from ghl_real_estate_ai.models.cma import CMAReport, CMAProperty, Comparable, MarketContext
from ghl_real_estate_ai.utils.pdf_renderer import PDFRenderer, PDFGenerationError


# ================================
# FIXTURES
# ================================

@pytest.fixture
def sample_cma_report():
    """Create a realistic CMA report for testing."""
    return CMAReport(
        subject_property=CMAProperty(
            address="123 Main St, Rancho Cucamonga, CA 91730",
            beds=4,
            baths=3.0,
            sqft=2800,
            year_built=2015,
            condition="Good",
            updates=["Kitchen Remodel (2024)"],
            features=["Pool", "Corner Lot"]
        ),
        comparables=[
            Comparable(
                address="125 Main St",
                sale_date=date(2026, 1, 15),
                sale_price=882000.0,
                sqft=2900,
                beds=4,
                baths=3.0,
                price_per_sqft=305.0,
                adjustment_percent=-2.0,
                adjusted_value=864360.0,
            ),
            Comparable(
                address="200 Elm Ave",
                sale_date=date(2026, 1, 10),
                sale_price=810000.0,
                sqft=2600,
                beds=4,
                baths=2.5,
                price_per_sqft=311.0,
                adjustment_percent=3.0,
                adjusted_value=834300.0,
            ),
        ],
        market_context=MarketContext(
            market_name="Rancho Cucamonga, CA",
            price_trend=12.5,
            dom_average=28,
            inventory_level=1450,
            zillow_zestimate=850000.0,
        ),
        estimated_value=855000.0,
        value_range_low=825000.0,
        value_range_high=885000.0,
        confidence_score=82,
        zillow_variance_abs=5000.0,
        zillow_variance_percent=0.6,
        zillow_explanation="Minor variance due to recent kitchen remodel not reflected in Zestimate.",
        market_narrative="The Rancho Cucamonga market remains competitive with 12.5% YoY appreciation.",
        generated_at="2026-02-02",
    )


@pytest.fixture
def mock_lead_bot_deps():
    """Mock all lead bot dependencies for isolated testing."""
    with patch.multiple(
        'ghl_real_estate_ai.agents.lead_bot',
        LeadIntentDecoder=Mock,
        CMAGenerator=Mock,
        RetellClient=Mock,
        LyrioClient=Mock,
        get_ghost_followup_engine=Mock,
        get_event_publisher=Mock,
        get_sequence_service=Mock,
        get_lead_scheduler=Mock,
        sync_service=Mock,
    ), patch(
        'ghl_real_estate_ai.services.national_market_intelligence.get_national_market_intelligence',
        Mock()
    ):
        yield


# ================================
# PDF RENDERER TESTS
# ================================

class TestPDFRendererCMA:
    """Tests for CMA PDF generation via PDFRenderer."""

    def test_render_cma_html_for_pdf_returns_html(self, sample_cma_report):
        """PDF-safe HTML is generated from CMA report."""
        html = PDFRenderer.render_cma_html_for_pdf(sample_cma_report)

        assert "Comparative Market Analysis" in html
        assert "123 Main St" in html
        assert "$855,000" in html
        assert "Rancho Cucamonga" in html
        # Verify PDF-safe layout (no CSS grid, no emoji)
        assert "grid-template-columns" not in html
        assert "@page" in html

    def test_render_cma_html_contains_comparables(self, sample_cma_report):
        """CMA HTML includes comparable property rows."""
        html = PDFRenderer.render_cma_html_for_pdf(sample_cma_report)

        assert "125 Main St" in html
        assert "200 Elm Ave" in html

    def test_render_cma_html_contains_zillow_comparison(self, sample_cma_report):
        """CMA HTML includes Zillow comparison section."""
        html = PDFRenderer.render_cma_html_for_pdf(sample_cma_report)

        assert "Zillow" in html
        assert "$850,000" in html  # Zestimate

    def test_generate_pdf_bytes_produces_valid_pdf(self, sample_cma_report):
        """PDFRenderer.generate_pdf_bytes returns valid PDF bytes."""
        try:
            from xhtml2pdf import pisa  # noqa: F401
        except ImportError:
            pytest.skip("xhtml2pdf not installed")

        pdf_bytes = PDFRenderer.generate_pdf_bytes(sample_cma_report)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # PDF magic bytes
        assert pdf_bytes[:4] == b'%PDF'

    def test_generate_pdf_bytes_under_size_limit(self, sample_cma_report):
        """Generated PDF is under the 2MB size limit."""
        try:
            from xhtml2pdf import pisa  # noqa: F401
        except ImportError:
            pytest.skip("xhtml2pdf not installed")

        pdf_bytes = PDFRenderer.generate_pdf_bytes(sample_cma_report)

        assert len(pdf_bytes) < 2 * 1024 * 1024  # 2MB


# ================================
# CMA EMAIL ATTACHMENT TESTS
# ================================

class TestSendCMAEmailWithAttachment:
    """Tests for _send_cma_email_with_attachment method."""

    @pytest.mark.asyncio
    async def test_cma_email_sends_with_pdf_attachment(self, mock_lead_bot_deps):
        """CMA email sends PDF attachment via SendGrid."""
        from ghl_real_estate_ai.agents.lead_bot import JorgeLeadBot

        mock_sendgrid = AsyncMock()
        bot = JorgeLeadBot(sendgrid_client=mock_sendgrid)
        bot.sequence_service = AsyncMock()

        # Mock CMA generator to return a report
        mock_report = MagicMock()
        mock_report.subject_property.address = "123 Main St"
        bot.cma_generator.generate_report = AsyncMock(return_value=mock_report)

        # Mock PDFRenderer to return fake PDF bytes
        fake_pdf = b'%PDF-1.4 fake content'
        with patch.object(PDFRenderer, 'generate_pdf_bytes', return_value=fake_pdf):
            result = await bot._send_cma_email_with_attachment(
                lead_id="lead_123",
                contact_email="buyer@example.com",
                property_address="123 Main St, Rancho Cucamonga, CA"
            )

        assert result is True
        mock_sendgrid.send_email.assert_called_once()
        call_kwargs = mock_sendgrid.send_email.call_args
        assert call_kwargs.kwargs["to_email"] == "buyer@example.com"
        assert "CMA" in call_kwargs.kwargs["subject"]

        # Verify attachment
        attachments = call_kwargs.kwargs["attachments"]
        assert len(attachments) == 1
        assert attachments[0]["type"] == "application/pdf"
        assert attachments[0]["filename"].startswith("CMA_")
        assert attachments[0]["filename"].endswith(".pdf")
        # Verify content is base64 encoded PDF
        decoded = base64.b64decode(attachments[0]["content"])
        assert decoded == fake_pdf

    @pytest.mark.asyncio
    async def test_cma_email_fallback_when_pdf_fails(self, mock_lead_bot_deps):
        """Email still handled gracefully when PDF generation fails."""
        from ghl_real_estate_ai.agents.lead_bot import JorgeLeadBot

        mock_sendgrid = AsyncMock()
        bot = JorgeLeadBot(sendgrid_client=mock_sendgrid)

        bot.cma_generator.generate_report = AsyncMock(return_value=MagicMock())

        with patch.object(PDFRenderer, 'generate_pdf_bytes',
                          side_effect=PDFGenerationError("Render failed")):
            result = await bot._send_cma_email_with_attachment(
                lead_id="lead_456",
                contact_email="buyer@example.com",
                property_address="456 Oak Ave"
            )

        assert result is False
        mock_sendgrid.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_cma_email_fallback_when_sendgrid_fails(self, mock_lead_bot_deps):
        """Returns False when SendGrid email delivery fails."""
        from ghl_real_estate_ai.agents.lead_bot import JorgeLeadBot

        mock_sendgrid = AsyncMock()
        mock_sendgrid.send_email.side_effect = Exception("SendGrid unavailable")
        bot = JorgeLeadBot(sendgrid_client=mock_sendgrid)
        bot.cma_generator.generate_report = AsyncMock(return_value=MagicMock())

        with patch.object(PDFRenderer, 'generate_pdf_bytes', return_value=b'%PDF-1.4 fake'):
            result = await bot._send_cma_email_with_attachment(
                lead_id="lead_789",
                contact_email="buyer@example.com",
                property_address="789 Pine St"
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_cma_email_filename_sanitization(self, mock_lead_bot_deps):
        """PDF filename is sanitized from property address."""
        from ghl_real_estate_ai.agents.lead_bot import JorgeLeadBot

        mock_sendgrid = AsyncMock()
        bot = JorgeLeadBot(sendgrid_client=mock_sendgrid)
        bot.sequence_service = AsyncMock()
        bot.cma_generator.generate_report = AsyncMock(return_value=MagicMock())

        with patch.object(PDFRenderer, 'generate_pdf_bytes', return_value=b'%PDF-1.4 fake'):
            await bot._send_cma_email_with_attachment(
                lead_id="lead_fn",
                contact_email="buyer@example.com",
                property_address="123 Main St, Rancho Cucamonga, CA 91730"
            )

        attachments = mock_sendgrid.send_email.call_args.kwargs["attachments"]
        filename = attachments[0]["filename"]
        # No special chars in filename
        assert "," not in filename
        assert " " not in filename
        assert filename.endswith(".pdf")


# ================================
# DAY 14 FLOW INTEGRATION TESTS
# ================================

class TestDay14EmailFlow:
    """Tests for the full send_day_14_email workflow node."""

    @pytest.mark.asyncio
    async def test_day_14_email_returns_cma_attached_true(self, mock_lead_bot_deps):
        """Day 14 flow sets cma_attached=True when PDF sends successfully."""
        from ghl_real_estate_ai.agents.lead_bot import JorgeLeadBot

        mock_sendgrid = AsyncMock()
        bot = JorgeLeadBot(sendgrid_client=mock_sendgrid)
        bot.ghost_engine.process_lead_step = AsyncMock(return_value={"content": "CMA email"})
        bot.sequence_service = AsyncMock()
        bot.scheduler = AsyncMock()
        bot.ghl_client = None  # Skip GHL path

        # Mock CMA attachment to succeed
        bot._send_cma_email_with_attachment = AsyncMock(return_value=True)

        mock_profile = MagicMock()
        mock_profile.frs.total_score = 75.0

        state = {
            "lead_id": "lead_d14",
            "contact_email": "buyer@example.com",
            "property_address": "123 Main St, RC, CA",
            "intent_profile": mock_profile,
            "conversation_history": [],
        }

        result = await bot.send_day_14_email(state)

        assert result["cma_attached"] is True
        assert result["current_step"] == "day_30_nudge"
        bot._send_cma_email_with_attachment.assert_called_once_with(
            lead_id="lead_d14",
            contact_email="buyer@example.com",
            property_address="123 Main St, RC, CA",
        )

    @pytest.mark.asyncio
    async def test_day_14_email_returns_cma_attached_false_without_sendgrid(self, mock_lead_bot_deps):
        """Day 14 flow sets cma_attached=False when no SendGrid client configured."""
        from ghl_real_estate_ai.agents.lead_bot import JorgeLeadBot

        bot = JorgeLeadBot(sendgrid_client=None)
        bot.ghost_engine.process_lead_step = AsyncMock(return_value={"content": "CMA email"})
        bot.sequence_service = AsyncMock()
        bot.scheduler = AsyncMock()
        bot.ghl_client = None

        mock_profile = MagicMock()
        mock_profile.frs.total_score = 50.0

        state = {
            "lead_id": "lead_nosendgrid",
            "contact_email": "buyer@example.com",
            "property_address": "456 Oak Ave",
            "intent_profile": mock_profile,
            "conversation_history": [],
        }

        result = await bot.send_day_14_email(state)

        assert result["cma_attached"] is False

    @pytest.mark.asyncio
    async def test_day_14_email_returns_cma_attached_false_without_email(self, mock_lead_bot_deps):
        """Day 14 flow skips PDF when contact_email is missing."""
        from ghl_real_estate_ai.agents.lead_bot import JorgeLeadBot

        mock_sendgrid = AsyncMock()
        bot = JorgeLeadBot(sendgrid_client=mock_sendgrid)
        bot.ghost_engine.process_lead_step = AsyncMock(return_value={"content": "CMA email"})
        bot.sequence_service = AsyncMock()
        bot.scheduler = AsyncMock()
        bot.ghl_client = None

        mock_profile = MagicMock()
        mock_profile.frs.total_score = 60.0

        state = {
            "lead_id": "lead_noemail",
            "contact_email": None,
            "property_address": "789 Pine St",
            "intent_profile": mock_profile,
            "conversation_history": [],
        }

        result = await bot.send_day_14_email(state)

        assert result["cma_attached"] is False


# ================================
# EMAIL TEMPLATE TEST
# ================================

class TestCMAEmailTemplate:
    """Tests for the CMA email HTML template."""

    def test_build_cma_email_html_contains_key_sections(self, mock_lead_bot_deps):
        """Email HTML template contains all key sections."""
        from ghl_real_estate_ai.agents.lead_bot import JorgeLeadBot

        bot = JorgeLeadBot()
        html = bot._build_cma_email_html("123 Main St, Rancho Cucamonga, CA")

        assert "123 Main St" in html
        assert "Comparative Market Analysis" in html
        assert "attached" in html.lower() or "PDF" in html
        assert "Jorge" in html
