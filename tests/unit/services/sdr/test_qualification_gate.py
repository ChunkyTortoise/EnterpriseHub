"""Unit tests for SDR QualificationGate.

Tests the FRS/PCS threshold logic, lead_type routing, and handoff_target selection.
Uses mocked LeadIntentDecoder — pure gate logic, no external dependencies.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


def _make_frs(total_score: float):
    """Build a minimal FinancialReadinessScore with the given total."""
    from ghl_real_estate_ai.models.lead_scoring import (
        ConditionRealism,
        FinancialReadinessScore,
        MotivationSignals,
        PriceResponsiveness,
        TimelineCommitment,
    )
    return FinancialReadinessScore(
        total_score=total_score,
        motivation=MotivationSignals(score=70, category="High Intent"),
        timeline=TimelineCommitment(score=70, category="High Commitment"),
        condition=ConditionRealism(score=70, category="Realistic"),
        price=PriceResponsiveness(score=70, category="Price-Aware"),
        classification="Warm" if total_score < 80 else "Hot",
    )


def _make_pcs(total_score: float = 65.0):
    """Build a minimal PsychologicalCommitmentScore."""
    from ghl_real_estate_ai.models.lead_scoring import PsychologicalCommitmentScore
    return PsychologicalCommitmentScore(
        total_score=total_score,
        response_velocity_score=65,
        message_length_score=65,
        question_depth_score=65,
        objection_handling_score=65,
        call_acceptance_score=65,
    )


def _make_intent_profile(
    lead_id: str = "test-001",
    frs_score: float = 65.0,
    buyer_confidence: float = 0.8,
    seller_confidence: float = 0.1,
    lead_type: str = "buyer",
):
    """Build a LeadIntentProfile with controllable FRS + intent confidence."""
    from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile
    return LeadIntentProfile(
        lead_id=lead_id,
        frs=_make_frs(frs_score),
        pcs=_make_pcs(),
        lead_type=lead_type,
        next_best_action="schedule_appointment",
        buyer_intent_confidence=buyer_confidence,
        seller_intent_confidence=seller_confidence,
    )


def _make_prospect_profile(lead_type: str = "buyer"):
    """Build a minimal ProspectProfile for gate evaluation."""
    from ghl_real_estate_ai.services.sdr.prospect_sourcer import ProspectProfile, ProspectSource
    return ProspectProfile(
        contact_id="test-001",
        location_id="loc-001",
        source=ProspectSource.GHL_PIPELINE,
        lead_type=lead_type,
        property_address=None,
        days_in_stage=5,
        last_activity=None,
        custom_fields={},
        mls_data=None,
    )


class TestQualificationGate:
    """Tests for QualificationGate threshold logic."""

    def _make_gate(self, profile):
        """Create a QualificationGate with a mocked decoder returning the given profile."""
        from ghl_real_estate_ai.services.sdr.qualification_gate import QualificationGate
        mock_decoder = MagicMock()
        mock_decoder.analyze_lead.return_value = profile
        return QualificationGate(intent_decoder=mock_decoder)

    def _history(self):
        return [{"role": "user", "content": "I want to buy a home in Rancho Cucamonga."}]

    # ── Pass cases ───────────────────────────────────────────────────────

    def test_passes_at_frs_threshold(self):
        """FRS exactly at threshold (60.0) should pass."""
        profile = _make_intent_profile(frs_score=60.0, buyer_confidence=0.75)
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile())
        assert decision.passed is True

    def test_passes_above_frs_threshold(self):
        """FRS above threshold with high buyer intent should pass."""
        profile = _make_intent_profile(frs_score=75.0, buyer_confidence=0.85)
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile())
        assert decision.passed is True

    def test_passes_seller_intent(self):
        """High seller confidence above threshold should pass and route to seller."""
        profile = _make_intent_profile(
            frs_score=65.0,
            buyer_confidence=0.2,
            seller_confidence=0.8,
            lead_type="seller",
        )
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile("seller"))
        assert decision.passed is True
        assert decision.handoff_target == "seller_bot"

    def test_handoff_target_buyer_when_buyer_intent_dominant(self):
        """Buyer intent > seller intent → handoff_target = buyer_bot."""
        profile = _make_intent_profile(buyer_confidence=0.9, seller_confidence=0.1)
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile())
        assert decision.handoff_target == "buyer_bot"

    def test_handoff_target_lead_bot_when_ambiguous(self):
        """Both confidences below threshold → handoff_target = lead_bot."""
        profile = _make_intent_profile(
            frs_score=65.0, buyer_confidence=0.5, seller_confidence=0.5, lead_type="unknown"
        )
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile("unknown"))
        assert decision.handoff_target == "lead_bot"

    def test_scores_propagated_to_decision(self):
        """FRS and PCS scores should be accessible on the decision object."""
        profile = _make_intent_profile(frs_score=72.5, buyer_confidence=0.8)
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile())
        assert decision.frs_score == pytest.approx(72.5)
        assert decision.pcs_score == pytest.approx(65.0)

    # ── Fail cases ───────────────────────────────────────────────────────

    def test_fails_at_frs_just_below_threshold(self):
        """FRS 59.9 (just below 60.0) should fail."""
        profile = _make_intent_profile(frs_score=59.9, buyer_confidence=0.9)
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile())
        assert decision.passed is False

    def test_fails_frs_zero(self):
        """FRS = 0 should fail."""
        profile = _make_intent_profile(frs_score=0.0, buyer_confidence=0.9)
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile())
        assert decision.passed is False

    def test_fails_confidence_below_threshold(self):
        """High FRS but both confidences below 0.70 should fail."""
        profile = _make_intent_profile(
            frs_score=80.0, buyer_confidence=0.5, seller_confidence=0.3
        )
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile())
        assert decision.passed is False

    def test_fails_returns_disqualify_reason(self):
        """Failed gate should set a disqualify_reason."""
        profile = _make_intent_profile(frs_score=40.0, buyer_confidence=0.3)
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile())
        assert decision.passed is False
        assert decision.disqualify_reason is not None
        assert len(decision.disqualify_reason) > 0

    # ── Decoder delegation ───────────────────────────────────────────────

    def test_calls_decoder_with_correct_args(self):
        """Gate must call analyze_lead with (contact_id, conversation_history)."""
        profile = _make_intent_profile(frs_score=70.0, buyer_confidence=0.8)
        from ghl_real_estate_ai.services.sdr.qualification_gate import QualificationGate
        mock_decoder = MagicMock()
        mock_decoder.analyze_lead.return_value = profile
        gate = QualificationGate(intent_decoder=mock_decoder)
        history = self._history()
        gate.evaluate("contact-xyz", history, _make_prospect_profile())
        mock_decoder.analyze_lead.assert_called_once_with("contact-xyz", history)

    def test_intent_profile_accessible_on_decision(self):
        """GateDecision.intent_profile should be the profile returned by decoder."""
        profile = _make_intent_profile(frs_score=70.0, buyer_confidence=0.8)
        gate = self._make_gate(profile)
        decision = gate.evaluate("test-001", self._history(), _make_prospect_profile())
        assert decision.intent_profile is profile
