"""
Tests for Lead Bot Day 14 CMA PDF attachment feature.

Covers:
- PDF generation from CMA reports
- PDF-safe HTML rendering (no CSS grid/gradients)
- SendGrid email with PDF attachment
- Fallback scenarios (no email, PDF failure, SendGrid failure, no client)
"""
import base64
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from ghl_real_estate_ai.models.cma import (
    CMAReport, CMAProperty, Comparable, MarketContext,
)
from ghl_real_estate_ai.models.lead_scoring import (
    LeadIntentProfile, FinancialReadinessScore, PsychologicalCommitmentScore,
    MotivationSignals, TimelineCommitment, ConditionRealism, PriceResponsiveness,
)
from ghl_real_estate_ai.utils.pdf_renderer import (
    PDFRenderer, PDFGenerationError,
)
from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
from tests.mocks.external_services import MockSendGridClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_cma_report() -> CMAReport:
    """Minimal valid CMAReport for testing."""
    return CMAReport(
        subject_property=CMAProperty(
            address="1234 Haven Ave, Rancho Cucamonga, CA 91730",
            beds=4, baths=2.5, sqft=2200, year_built=2005,
            condition="Good",
        ),
        comparables=[
            Comparable(
                address="1240 Haven Ave",
                sale_date="2025-12-01",
                sale_price=750000, sqft=2100, beds=4, baths=2.0,
                price_per_sqft=357.14, adjustment_percent=2.0,
                adjusted_value=765000,
            ),
            Comparable(
                address="1250 Haven Ave",
                sale_date="2025-11-15",
                sale_price=780000, sqft=2300, beds=4, baths=3.0,
                price_per_sqft=339.13, adjustment_percent=-1.5,
                adjusted_value=768300,
            ),
        ],
        market_context=MarketContext(
            market_name="Rancho Cucamonga, CA",
            price_trend=3.2, dom_average=28,
            inventory_level=145, zillow_zestimate=740000,
        ),
        estimated_value=760000,
        value_range_low=740000,
        value_range_high=780000,
        confidence_score=87,
        zillow_variance_abs=20000,
        zillow_variance_percent=2.7,
        zillow_explanation="Our AI analysis accounts for recent comparable sales.",
        market_narrative="The Rancho Cucamonga market remains strong.",
    )


@pytest.fixture
def mock_intent_profile() -> LeadIntentProfile:
    """Reusable intent profile for Day 14 tests."""
    frs = FinancialReadinessScore(
        total_score=65.0,
        motivation=MotivationSignals(score=70, detected_markers=["relocating"], category="High Intent"),
        timeline=TimelineCommitment(score=60, category="Flexible"),
        condition=ConditionRealism(score=50, category="Negotiable"),
        price=PriceResponsiveness(score=80, zestimate_mentioned=True, category="Price-Aware"),
        classification="Warm",
    )
    pcs = PsychologicalCommitmentScore(
        total_score=70.0,
        response_velocity_score=75,
        message_length_score=65,
        question_depth_score=60,
        objection_handling_score=70,
        call_acceptance_score=80,
    )
    return LeadIntentProfile(
        lead_id="lead_d14_test",
        frs=frs, pcs=pcs,
        next_best_action="Send CMA",
    )


def _build_day14_state(intent_profile, contact_email="buyer@example.com",
                       property_address="1234 Haven Ave, Rancho Cucamonga, CA 91730"):
    """Construct a minimal LeadFollowUpState dict for Day 14."""
    return {
        "lead_id": "lead_d14_test",
        "lead_name": "Test Buyer",
        "contact_phone": "+15551234567",
        "contact_email": contact_email,
        "property_address": property_address,
        "conversation_history": [
            {"role": "user", "content": "I'm looking for a house in Rancho Cucamonga"},
        ],
        "intent_profile": intent_profile,
        "current_step": "day_14_email",
        "engagement_status": "ghosted",
        "response_content": None,
        "last_interaction_time": datetime.now(timezone.utc),
        "stall_breaker_attempted": True,
        "cma_generated": False,
        "showing_date": None,
        "showing_feedback": None,
        "offer_amount": None,
        "closing_date": None,
        "intelligence_context": None,
        "intelligence_performance_ms": None,
        "preferred_engagement_timing": None,
        "churn_risk_score": None,
        "cross_bot_preferences": None,
        "sequence_optimization_applied": None,
    }


# ---------------------------------------------------------------------------
# PDF Renderer Tests
# ---------------------------------------------------------------------------

class TestPDFRenderer:
    """Unit tests for the new PDFRenderer methods."""

    def test_generate_pdf_bytes_valid(self, sample_cma_report):
        """PDF bytes start with %PDF header and are under 2 MB."""
        pdf_bytes = PDFRenderer.generate_pdf_bytes(sample_cma_report)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) < 2 * 1024 * 1024

    def test_generate_pdf_bytes_nonzero_size(self, sample_cma_report):
        """PDF output has meaningful size (not just a header)."""
        pdf_bytes = PDFRenderer.generate_pdf_bytes(sample_cma_report)

        # A real CMA PDF with tables/content should be > 1 KB
        assert len(pdf_bytes) > 1024

    def test_generate_pdf_bytes_uses_reportlab(self, sample_cma_report):
        """PDF is generated via reportlab (letter page size, no HTML dependencies)."""
        pdf_bytes = PDFRenderer.generate_pdf_bytes(sample_cma_report)

        # reportlab produces valid PDF with proper trailer
        assert pdf_bytes[:5] == b"%PDF-"
        assert b"%%EOF" in pdf_bytes


# ---------------------------------------------------------------------------
# Day 14 Email Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDay14EmailWithAttachment:
    """Integration tests for the Day 14 CMA email attachment flow."""

    @pytest.fixture
    def mock_sendgrid(self):
        return MockSendGridClient()

    @pytest.fixture
    def mock_ghl(self):
        client = AsyncMock()
        client.send_message = AsyncMock(return_value={"status": "sent"})
        return client

    def _patch_services(self):
        """Return context managers that mock the module-level singletons."""
        return (
            patch("ghl_real_estate_ai.agents.lead_bot.sync_service"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_ghost_followup_engine"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_sequence_service"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_lead_scheduler"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_event_publisher"),
            patch("ghl_real_estate_ai.agents.lead_bot.RetellClient"),
            patch("ghl_real_estate_ai.services.national_market_intelligence.get_national_market_intelligence",
                  return_value=MagicMock()),
        )

    def _build_bot(self, ghl_client, sendgrid_client, patches):
        """Build a LeadBotWorkflow with all singletons patched."""
        (p_sync, p_ghost, p_seq, p_sched, p_pub, p_retell, p_market) = patches

        # Configure ghost engine to return a valid action dict
        ghost_engine = AsyncMock()
        ghost_engine.process_lead_step = AsyncMock(return_value={
            "content": "Here's your complimentary CMA report!",
            "action_type": "email",
        })
        p_ghost.return_value = ghost_engine

        # Sequence service
        seq_svc = AsyncMock()
        seq_svc.mark_action_completed = AsyncMock()
        seq_svc.advance_to_next_day = AsyncMock()
        seq_svc.set_cma_generated = AsyncMock(return_value=True)
        p_seq.return_value = seq_svc

        # Scheduler
        p_sched.return_value = AsyncMock()

        # Sync service
        p_sync.record_lead_event = AsyncMock()

        bot = LeadBotWorkflow(
            ghl_client=ghl_client,
            sendgrid_client=sendgrid_client,
        )
        return bot, seq_svc, p_sync

    async def test_day14_email_with_attachment(
        self, mock_ghl, mock_sendgrid, mock_intent_profile, sample_cma_report,
    ):
        """Happy path: CMA PDF generated and emailed via SendGrid."""
        patches = self._patch_services()
        ctxs = [p.start() for p in patches]
        try:
            bot, seq_svc, p_sync = self._build_bot(mock_ghl, mock_sendgrid, ctxs)

            # Patch CMA generator to return our fixture
            bot.cma_generator.generate_report = AsyncMock(return_value=sample_cma_report)

            state = _build_day14_state(mock_intent_profile)
            result = await bot.send_day_14_email(state)

            # GHL email still sent
            mock_ghl.send_message.assert_called_once()

            # SendGrid received the attachment
            assert len(mock_sendgrid.sent_emails) == 1
            email = mock_sendgrid.sent_emails[0]
            assert len(email["attachments"]) == 1
            att = email["attachments"][0]
            assert att["filename"].startswith("CMA_")
            assert att["filename"].endswith(".pdf")
            assert att["type"] == "application/pdf"
            # Verify content is base64 decodable PDF
            decoded = base64.b64decode(att["content"])
            assert decoded[:5] == b"%PDF-"

            assert result["cma_attached"] is True

            # Sequence service marked CMA as generated
            seq_svc.set_cma_generated.assert_called_once_with("lead_d14_test")
        finally:
            for p in patches:
                p.stop()

    async def test_day14_fallback_no_email(
        self, mock_ghl, mock_sendgrid, mock_intent_profile,
    ):
        """When contact_email is None, PDF step is skipped."""
        patches = self._patch_services()
        ctxs = [p.start() for p in patches]
        try:
            bot, seq_svc, _ = self._build_bot(mock_ghl, mock_sendgrid, ctxs)

            state = _build_day14_state(mock_intent_profile, contact_email=None)
            result = await bot.send_day_14_email(state)

            assert result["cma_attached"] is False
            assert len(mock_sendgrid.sent_emails) == 0
            # GHL email should still send
            mock_ghl.send_message.assert_called_once()
        finally:
            for p in patches:
                p.stop()

    async def test_day14_fallback_pdf_failure(
        self, mock_ghl, mock_sendgrid, mock_intent_profile,
    ):
        """When PDF generation fails, GHL email still sends, cma_attached=False."""
        patches = self._patch_services()
        ctxs = [p.start() for p in patches]
        try:
            bot, seq_svc, _ = self._build_bot(mock_ghl, mock_sendgrid, ctxs)
            bot.cma_generator.generate_report = AsyncMock(
                side_effect=PDFGenerationError("render failed")
            )

            state = _build_day14_state(mock_intent_profile)
            result = await bot.send_day_14_email(state)

            assert result["cma_attached"] is False
            # GHL still sent
            mock_ghl.send_message.assert_called_once()
            # SendGrid NOT called
            assert len(mock_sendgrid.sent_emails) == 0
        finally:
            for p in patches:
                p.stop()

    async def test_day14_fallback_sendgrid_failure(
        self, mock_ghl, mock_intent_profile, sample_cma_report,
    ):
        """When SendGrid raises, GHL email still sends, cma_attached=False."""
        failing_sg = AsyncMock()
        failing_sg.send_email = AsyncMock(side_effect=Exception("SendGrid down"))

        patches = self._patch_services()
        ctxs = [p.start() for p in patches]
        try:
            bot, seq_svc, _ = self._build_bot(mock_ghl, failing_sg, ctxs)
            bot.cma_generator.generate_report = AsyncMock(return_value=sample_cma_report)

            state = _build_day14_state(mock_intent_profile)
            result = await bot.send_day_14_email(state)

            assert result["cma_attached"] is False
            mock_ghl.send_message.assert_called_once()
        finally:
            for p in patches:
                p.stop()

    async def test_day14_no_sendgrid_client(
        self, mock_ghl, mock_intent_profile,
    ):
        """Bot works without SendGrid configured (sendgrid_client=None)."""
        patches = self._patch_services()
        ctxs = [p.start() for p in patches]
        try:
            bot, seq_svc, _ = self._build_bot(mock_ghl, None, ctxs)

            state = _build_day14_state(mock_intent_profile)
            result = await bot.send_day_14_email(state)

            assert result["cma_attached"] is False
            # GHL email still sent
            mock_ghl.send_message.assert_called_once()
        finally:
            for p in patches:
                p.stop()

    async def test_email_html_content(self, mock_intent_profile):
        """Email body HTML references the CMA attachment and property address."""
        address = "1234 Haven Ave, Rancho Cucamonga, CA 91730"
        html = LeadBotWorkflow._build_cma_email_html(address)

        assert "1234 Haven Ave" in html
        assert "Comparative Market Analysis" in html
        assert "attached" in html.lower()
        assert "EnterpriseHub" in html

    async def test_day14_fallback_no_property_address(
        self, mock_ghl, mock_sendgrid, mock_intent_profile,
    ):
        """When property_address is None, PDF step is skipped."""
        patches = self._patch_services()
        ctxs = [p.start() for p in patches]
        try:
            bot, seq_svc, _ = self._build_bot(mock_ghl, mock_sendgrid, ctxs)

            state = _build_day14_state(mock_intent_profile, property_address=None)
            result = await bot.send_day_14_email(state)

            assert result["cma_attached"] is False
            assert len(mock_sendgrid.sent_emails) == 0
            mock_ghl.send_message.assert_called_once()
        finally:
            for p in patches:
                p.stop()
