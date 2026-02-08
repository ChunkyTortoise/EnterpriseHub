"""
Tests for Behavioral Trigger Detector.

Covers:
- Hedging pattern detection
- Commitment signal detection
- Urgency detection
- Stall / objection detection
- Response latency analysis
- Engagement drop detection
- Composite scoring
- Drift direction
- Voss technique recommendation
"""

import os

os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake_for_testing")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fake")

import pytest

from ghl_real_estate_ai.services.behavioral_trigger_detector import (
    BehavioralAnalysis,
    BehavioralTriggerDetector,
    DriftDirection,
    NegotiationTechnique,
    TriggerType,
)


@pytest.fixture
def detector():
    return BehavioralTriggerDetector()


# ---------------------------------------------------------------------------
# Hedging Detection
# ---------------------------------------------------------------------------


class TestHedgingDetection:
    """Messages with hedging language produce a positive hedging score."""

    @pytest.mark.asyncio
    async def test_clear_hedging(self, detector):
        result = await detector.analyze_message(
            message="Maybe I could consider it if the price is flexible",
            contact_id="c1",
        )
        assert result.hedging_score > 0.4
        hedging_triggers = [t for t in result.triggers if t.type == TriggerType.HEDGING]
        assert len(hedging_triggers) >= 2

    @pytest.mark.asyncio
    async def test_no_hedging(self, detector):
        result = await detector.analyze_message(
            message="I love this house",
            contact_id="c2",
        )
        assert result.hedging_score == 0.0

    @pytest.mark.asyncio
    async def test_moderate_hedging(self, detector):
        result = await detector.analyze_message(
            message="I think it depends on timing",
            contact_id="c3",
        )
        assert 0.0 < result.hedging_score < 0.8


# ---------------------------------------------------------------------------
# Commitment Detection
# ---------------------------------------------------------------------------


class TestCommitmentDetection:
    """Messages with commitment language produce a positive commitment score."""

    @pytest.mark.asyncio
    async def test_strong_commitment(self, detector):
        result = await detector.analyze_message(
            message="Absolutely, let's do it! When can we schedule?",
            contact_id="c10",
        )
        assert result.commitment_score > 0.5
        commit_triggers = [t for t in result.triggers if t.type == TriggerType.COMMITMENT_SIGNAL]
        assert len(commit_triggers) >= 2

    @pytest.mark.asyncio
    async def test_no_commitment(self, detector):
        result = await detector.analyze_message(
            message="I dunno",
            contact_id="c11",
        )
        assert result.commitment_score == 0.0

    @pytest.mark.asyncio
    async def test_mild_commitment(self, detector):
        result = await detector.analyze_message(
            message="Yes I'm ready to move forward",
            contact_id="c12",
        )
        assert result.commitment_score > 0.3


# ---------------------------------------------------------------------------
# Urgency Detection
# ---------------------------------------------------------------------------


class TestUrgencyDetection:
    """Messages expressing urgency produce a positive urgency score."""

    @pytest.mark.asyncio
    async def test_high_urgency(self, detector):
        result = await detector.analyze_message(
            message="I need to move immediately, this is urgent",
            contact_id="c20",
        )
        assert result.urgency_score > 0.5
        urgency_triggers = [t for t in result.triggers if t.type == TriggerType.URGENCY_SHIFT]
        assert len(urgency_triggers) >= 2

    @pytest.mark.asyncio
    async def test_no_urgency(self, detector):
        result = await detector.analyze_message(
            message="Just browsing some listings",
            contact_id="c21",
        )
        assert result.urgency_score == 0.0


# ---------------------------------------------------------------------------
# Stall & Objection Detection
# ---------------------------------------------------------------------------


class TestStallObjectionDetection:
    @pytest.mark.asyncio
    async def test_stall_detected(self, detector):
        result = await detector.analyze_message(
            message="Let me think about it and get back to you",
            contact_id="c30",
        )
        stall_triggers = [t for t in result.triggers if t.type == TriggerType.STALL]
        assert len(stall_triggers) >= 1

    @pytest.mark.asyncio
    async def test_objection_detected(self, detector):
        result = await detector.analyze_message(
            message="That's too expensive, I can't afford it",
            contact_id="c31",
        )
        objection_triggers = [t for t in result.triggers if t.type == TriggerType.OBJECTION]
        assert len(objection_triggers) >= 1

    @pytest.mark.asyncio
    async def test_price_sensitivity(self, detector):
        result = await detector.analyze_message(
            message="How much does this cost? Is there a discount?",
            contact_id="c32",
        )
        price_triggers = [t for t in result.triggers if t.type == TriggerType.PRICE_SENSITIVITY]
        assert len(price_triggers) >= 1


# ---------------------------------------------------------------------------
# Latency Analysis
# ---------------------------------------------------------------------------


class TestLatencyAnalysis:
    @pytest.mark.asyncio
    async def test_fast_response_low_factor(self, detector):
        result = await detector.analyze_message(
            message="Yes",
            contact_id="c40",
            response_latency_ms=5000,  # 5 seconds — fast
        )
        assert result.latency_factor < 0.3

    @pytest.mark.asyncio
    async def test_slow_response_high_factor(self, detector):
        result = await detector.analyze_message(
            message="I think so",
            contact_id="c41",
            response_latency_ms=300_000,  # 5 minutes
        )
        assert result.latency_factor > 0.5

    @pytest.mark.asyncio
    async def test_very_slow_triggers_anomaly(self, detector):
        result = await detector.analyze_message(
            message="Okay",
            contact_id="c42",
            response_latency_ms=600_000,  # 10 minutes
        )
        anomaly_triggers = [t for t in result.triggers if t.type == TriggerType.LATENCY_ANOMALY]
        assert len(anomaly_triggers) >= 1

    @pytest.mark.asyncio
    async def test_no_latency_data(self, detector):
        result = await detector.analyze_message(
            message="Hello",
            contact_id="c43",
            response_latency_ms=None,
        )
        assert result.latency_factor == 0.0


# ---------------------------------------------------------------------------
# Engagement Drop
# ---------------------------------------------------------------------------


class TestEngagementDrop:
    @pytest.mark.asyncio
    async def test_engagement_drop_detected(self, detector):
        """Short message after long history → engagement drop trigger."""
        history = [
            {"message": "I've been thinking about selling my house in the Victoria area, it's a 4 bedroom with a pool"},
            {
                "message": "The market has been great lately and I think it could fetch around 800k based on recent sales"
            },
            {"message": "We're relocating because of a job change, need to move within 60 days ideally"},
        ]
        result = await detector.analyze_message(
            message="Ok",
            contact_id="c50",
            conversation_history=history,
        )
        drop_triggers = [t for t in result.triggers if t.type == TriggerType.ENGAGEMENT_DROP]
        assert len(drop_triggers) >= 1

    @pytest.mark.asyncio
    async def test_no_drop_with_matching_length(self, detector):
        history = [
            {"message": "Hi there"},
            {"message": "How are you"},
        ]
        result = await detector.analyze_message(
            message="I'm good thanks",
            contact_id="c51",
            conversation_history=history,
        )
        drop_triggers = [t for t in result.triggers if t.type == TriggerType.ENGAGEMENT_DROP]
        assert len(drop_triggers) == 0


# ---------------------------------------------------------------------------
# Composite Scoring
# ---------------------------------------------------------------------------


class TestCompositeScoring:
    @pytest.mark.asyncio
    async def test_committed_urgent_message_high_score(self, detector):
        result = await detector.analyze_message(
            message="Absolutely, I'm ready to move immediately, let's do it today",
            contact_id="c60",
        )
        assert result.composite_score > 0.5

    @pytest.mark.asyncio
    async def test_hedging_message_lower_score(self, detector):
        result = await detector.analyze_message(
            message="Maybe, it depends, not sure, possibly could consider",
            contact_id="c61",
        )
        # Hedging inverts, so composite should be lower
        assert result.composite_score < 0.5

    @pytest.mark.asyncio
    async def test_composite_bounded(self, detector):
        result = await detector.analyze_message(
            message="Absolutely definitely for sure let's do it ASAP immediately",
            contact_id="c62",
        )
        assert 0.0 <= result.composite_score <= 1.0


# ---------------------------------------------------------------------------
# Drift Direction
# ---------------------------------------------------------------------------


class TestDriftDirection:
    @pytest.mark.asyncio
    async def test_warming_drift(self, detector):
        result = await detector.analyze_message(
            message="Absolutely, let's schedule immediately",
            contact_id="c70",
        )
        assert result.drift_direction == DriftDirection.WARMING.value

    @pytest.mark.asyncio
    async def test_cooling_drift(self, detector):
        result = await detector.analyze_message(
            message="Maybe I'm not sure, it depends, I'll think about it",
            contact_id="c71",
        )
        assert result.drift_direction == DriftDirection.COOLING.value

    @pytest.mark.asyncio
    async def test_stable_drift(self, detector):
        result = await detector.analyze_message(
            message="Hello how are you",
            contact_id="c72",
        )
        assert result.drift_direction == DriftDirection.STABLE.value


# ---------------------------------------------------------------------------
# Technique Recommendation
# ---------------------------------------------------------------------------


class TestTechniqueRecommendation:
    @pytest.mark.asyncio
    async def test_stall_recommends_direct_challenge(self, detector):
        result = await detector.analyze_message(
            message="Let me think about it and get back to you, no rush",
            contact_id="c80",
        )
        assert result.recommended_technique == NegotiationTechnique.DIRECT_CHALLENGE.value

    @pytest.mark.asyncio
    async def test_objection_recommends_tactical_empathy(self, detector):
        result = await detector.analyze_message(
            message="That's too expensive for my budget, I can't afford it",
            contact_id="c81",
        )
        assert result.recommended_technique == NegotiationTechnique.TACTICAL_EMPATHY.value

    @pytest.mark.asyncio
    async def test_hedging_recommends_labeling(self, detector):
        result = await detector.analyze_message(
            message="Maybe I could consider it if the price is flexible and negotiable",
            contact_id="c82",
        )
        assert result.recommended_technique == NegotiationTechnique.LABELING.value

    @pytest.mark.asyncio
    async def test_commitment_recommends_anchoring(self, detector):
        result = await detector.analyze_message(
            message="Absolutely, I'm definitely ready to sign me up for sure",
            contact_id="c83",
        )
        assert result.recommended_technique == NegotiationTechnique.ANCHORING.value

    @pytest.mark.asyncio
    async def test_neutral_message_no_technique(self, detector):
        result = await detector.analyze_message(
            message="Hello",
            contact_id="c84",
        )
        assert result.recommended_technique is None
