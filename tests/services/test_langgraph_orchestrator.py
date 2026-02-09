import pytest
pytestmark = pytest.mark.integration

"""
Tests for LangGraph Lead Qualification Orchestrator.

Covers:
- Lead type classification (tags + keyword fallback)
- Behavioral signal integration
- Compliance pre-check (deactivation tags)
- Seller / buyer / general qualification routing
- Composite scoring and temperature boosting
"""

import os

os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake_for_testing")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fake")

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.services.langgraph_orchestrator import (

@pytest.mark.integration
    LeadQualificationOrchestrator,
    LeadType,
    QualificationResult,
    QualificationStage,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_orchestrator(behavioral_detector=None):
    return LeadQualificationOrchestrator(
        conversation_manager=MagicMock(),
        behavioral_detector=behavioral_detector,
    )


@dataclass
class FakeAnalysis:
    composite_score: float = 0.0
    hedging_score: float = 0.0
    urgency_score: float = 0.0
    commitment_score: float = 0.0
    drift_direction: str = "stable"
    triggers: list = None

    def __post_init__(self):
        if self.triggers is None:
            self.triggers = []


# ---------------------------------------------------------------------------
# Classification Tests
# ---------------------------------------------------------------------------


class TestLeadClassification:
    """Leads are classified by tag first, then by keyword intent."""

    @pytest.mark.asyncio
    async def test_seller_tag_classification(self):
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c1",
            location_id="loc1",
            message="Hello",
            contact_tags=["Needs Qualifying"],
            contact_info={"first_name": "Maria"},
        )
        assert result.lead_type == LeadType.SELLER.value

    @pytest.mark.asyncio
    async def test_buyer_tag_classification(self):
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c2",
            location_id="loc1",
            message="Hello",
            contact_tags=["Buyer-Lead"],
            contact_info={"first_name": "Carlos"},
        )
        assert result.lead_type == LeadType.BUYER.value

    @pytest.mark.asyncio
    async def test_keyword_seller_fallback(self):
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c3",
            location_id="loc1",
            message="I want to sell my house",
            contact_tags=[],
            contact_info={},
        )
        assert result.lead_type == LeadType.SELLER.value

    @pytest.mark.asyncio
    async def test_keyword_buyer_fallback(self):
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c4",
            location_id="loc1",
            message="I'm looking for a 3 bedroom house to buy",
            contact_tags=[],
            contact_info={},
        )
        assert result.lead_type == LeadType.BUYER.value

    @pytest.mark.asyncio
    async def test_general_fallback(self):
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c5",
            location_id="loc1",
            message="Hi there",
            contact_tags=[],
            contact_info={},
        )
        assert result.lead_type == LeadType.GENERAL.value

    @pytest.mark.asyncio
    async def test_tag_takes_priority_over_keywords(self):
        """Even if message says 'buy', Needs Qualifying tag → seller."""
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c6",
            location_id="loc1",
            message="I want to buy a house",
            contact_tags=["Needs Qualifying"],
            contact_info={},
        )
        assert result.lead_type == LeadType.SELLER.value


# ---------------------------------------------------------------------------
# Seller Qualification Tests
# ---------------------------------------------------------------------------


class TestSellerQualification:
    """Seller temperature is based on questions answered in conversation history."""

    @pytest.mark.asyncio
    async def test_hot_seller_all_questions(self):
        orch = _make_orchestrator()
        history = [
            {
                "seller_preferences": {
                    "motivation": "relocating",
                    "timeline_acceptable": True,
                    "property_condition": "move-in ready",
                    "price_expectation": "650000",
                }
            }
        ]
        result = await orch.process(
            contact_id="c10",
            location_id="loc1",
            message="$650k works",
            contact_tags=["Needs Qualifying"],
            contact_info={},
            conversation_history=history,
        )
        assert result.temperature == "hot"
        assert result.is_qualified is True
        assert any(a["tag"] == "Hot-Seller" for a in result.actions)
        assert any(a["tag"] == "Seller-Qualified" for a in result.actions)

    @pytest.mark.asyncio
    async def test_warm_seller_three_questions(self):
        orch = _make_orchestrator()
        history = [
            {
                "seller_preferences": {
                    "motivation": "downsizing",
                    "timeline_acceptable": True,
                    "property_condition": "needs work",
                    "price_expectation": None,
                }
            }
        ]
        result = await orch.process(
            contact_id="c11",
            location_id="loc1",
            message="I'm not sure on price yet",
            contact_tags=["Needs Qualifying"],
            contact_info={},
            conversation_history=history,
        )
        assert result.temperature == "warm"
        assert result.is_qualified is False

    @pytest.mark.asyncio
    async def test_cold_seller_few_questions(self):
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c12",
            location_id="loc1",
            message="Hello",
            contact_tags=["Needs Qualifying"],
            contact_info={},
            conversation_history=[],
        )
        assert result.temperature == "cold"
        assert result.is_qualified is False


# ---------------------------------------------------------------------------
# Buyer Qualification Tests
# ---------------------------------------------------------------------------


class TestBuyerQualification:
    """Buyer temperature is based on financial readiness + buying motivation."""

    @pytest.mark.asyncio
    async def test_hot_buyer(self):
        orch = _make_orchestrator()
        history = [
            {"financial_readiness_score": 80, "buying_motivation_score": 75},
        ]
        result = await orch.process(
            contact_id="c20",
            location_id="loc1",
            message="Ready to buy",
            contact_tags=["Buyer-Lead"],
            contact_info={},
            conversation_history=history,
        )
        assert result.temperature == "hot"
        assert result.is_qualified is True
        assert any(a["tag"] == "Hot-Buyer" for a in result.actions)

    @pytest.mark.asyncio
    async def test_warm_buyer(self):
        orch = _make_orchestrator()
        history = [
            {"financial_readiness_score": 55, "buying_motivation_score": 50},
        ]
        result = await orch.process(
            contact_id="c21",
            location_id="loc1",
            message="Looking around",
            contact_tags=["Buyer-Lead"],
            contact_info={},
            conversation_history=history,
        )
        assert result.temperature == "warm"

    @pytest.mark.asyncio
    async def test_cold_buyer(self):
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c22",
            location_id="loc1",
            message="Hi",
            contact_tags=["Buyer-Lead"],
            contact_info={},
            conversation_history=[],
        )
        assert result.temperature == "cold"
        assert result.is_qualified is False


# ---------------------------------------------------------------------------
# Behavioral Integration Tests
# ---------------------------------------------------------------------------


class TestBehavioralIntegration:
    """Behavioral detector signals integrate into scoring."""

    @pytest.mark.asyncio
    async def test_behavioral_boost_warm_to_hot(self):
        """High composite score upgrades warm → hot."""
        detector = MagicMock()
        detector.analyze_message = AsyncMock(
            return_value=FakeAnalysis(
                composite_score=0.85,
                urgency_score=0.9,
                commitment_score=0.8,
            )
        )
        orch = _make_orchestrator(behavioral_detector=detector)

        # Buyer with warm scores
        history = [
            {"financial_readiness_score": 55, "buying_motivation_score": 50},
        ]
        result = await orch.process(
            contact_id="c30",
            location_id="loc1",
            message="I need to move quickly",
            contact_tags=["Buyer-Lead"],
            contact_info={},
            conversation_history=history,
        )
        assert result.temperature == "hot"
        assert result.behavioral_signals.get("composite_score") == 0.85

    @pytest.mark.asyncio
    async def test_detector_failure_does_not_break_pipeline(self):
        """If behavioral detector raises, pipeline continues with empty signals."""
        detector = MagicMock()
        detector.analyze_message = AsyncMock(side_effect=RuntimeError("boom"))
        orch = _make_orchestrator(behavioral_detector=detector)

        result = await orch.process(
            contact_id="c31",
            location_id="loc1",
            message="Hello",
            contact_tags=["Buyer-Lead"],
            contact_info={},
        )
        assert result.success is True
        assert result.behavioral_signals == {}


# ---------------------------------------------------------------------------
# Compliance Tests
# ---------------------------------------------------------------------------


class TestComplianceGate:
    """Deactivation tags should still allow the pipeline to complete (no crash)."""

    @pytest.mark.asyncio
    async def test_deactivation_tag_passes_through(self):
        """Deactivation tags don't crash the pipeline but mark compliance_passed=False internally."""
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c40",
            location_id="loc1",
            message="Hello",
            contact_tags=["Needs Qualifying", "AI-Off"],
            contact_info={},
        )
        # Pipeline still completes — compliance is informational here
        assert result.success is True


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Orchestrator handles errors gracefully."""

    @pytest.mark.asyncio
    async def test_result_always_returned(self):
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c50",
            location_id="loc1",
            message="Test",
            contact_tags=[],
            contact_info={},
        )
        assert isinstance(result, QualificationResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_empty_message(self):
        orch = _make_orchestrator()
        result = await orch.process(
            contact_id="c51",
            location_id="loc1",
            message="",
            contact_tags=[],
            contact_info={},
        )
        assert result.success is True
        assert result.lead_type == LeadType.GENERAL.value