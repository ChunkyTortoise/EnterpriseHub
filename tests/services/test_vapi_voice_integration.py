import pytest
pytestmark = pytest.mark.integration

"""
Tests for Vapi Voice Conversation Intelligence.

Covers:
- Call event processing (started, ended, failed, transcript)
- Event normalization from Vapi webhook payloads
- Transcript analysis with behavioral detector integration
- Qualification signal extraction
- Temperature classification
- Call lifecycle management
- Graceful handling of missing data
"""

import os

os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake_for_testing")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fake")

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.services.vapi_voice_integration import (

    CallEventResult,
    SpeakerRole,
    TranscriptAnalysis,
    TranscriptSegment,
    VapiVoiceIntelligence,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class FakeBehavioralAnalysis:
    composite_score: float = 0.5
    hedging_score: float = 0.1
    commitment_score: float = 0.6
    urgency_score: float = 0.5
    drift_direction: str = "warming"
    recommended_technique: str = "anchoring"
    latency_factor: float = 0.2
    triggers: list = None

    def __post_init__(self):
        if self.triggers is None:
            self.triggers = []


def _mock_detector(composite=0.5, commitment=0.6, urgency=0.5):
    detector = MagicMock()
    detector.analyze_message = AsyncMock(
        return_value=FakeBehavioralAnalysis(
            composite_score=composite,
            commitment_score=commitment,
            urgency_score=urgency,
        )
    )
    return detector


def _sample_transcript():
    return [
        TranscriptSegment(role="agent", text="Hi Maria, thanks for calling. What are you looking for?"),
        TranscriptSegment(role="customer", text="I'm looking for a 3 bedroom home in Victoria under $800k"),
        TranscriptSegment(role="agent", text="Great, are you pre-approved for a mortgage?"),
        TranscriptSegment(role="customer", text="Yes I'm pre-approved and ready to move within 2 months"),
        TranscriptSegment(role="agent", text="Perfect, let me find some properties for you"),
        TranscriptSegment(role="customer", text="Absolutely, I'm very interested"),
    ]


def _vapi_call_ended_payload(call_id="call_123", contact_id="c_123"):
    return {
        "message": {
            "type": "end-of-call-report",
            "call": {
                "id": call_id,
                "direction": "inbound",
                "status": "ended",
                "duration": 180,
                "customer": {"number": "+19095551234"},
                "metadata": {"contact_id": contact_id},
            },
            "artifact": {
                "duration": 180,
                "messages": [
                    {"role": "agent", "message": "Hi, thanks for calling"},
                    {"role": "customer", "message": "I want to buy a 3BR home in Rancho Cucamonga for $750k"},
                    {"role": "agent", "message": "Are you pre-approved?"},
                    {"role": "customer", "message": "Yes, pre-approved and ready to move ASAP"},
                ],
            },
        },
    }


# ---------------------------------------------------------------------------
# Call Event Processing
# ---------------------------------------------------------------------------


class TestCallEventProcessing:
    @pytest.mark.asyncio
    async def test_call_started(self):
        vi = VapiVoiceIntelligence()
        result = await vi.process_call_event(
            {
                "message": {
                    "type": "call-started",
                    "call": {"id": "call_1", "direction": "inbound", "customer": {"number": "+1234"}},
                },
            }
        )
        assert result.success is True
        assert result.event_type == "call-started"
        assert "call_1" in vi._active_calls

    @pytest.mark.asyncio
    async def test_call_ended_with_transcript(self):
        detector = _mock_detector(composite=0.7, commitment=0.8, urgency=0.6)
        vi = VapiVoiceIntelligence(behavioral_detector=detector)

        result = await vi.process_call_event(_vapi_call_ended_payload())

        assert result.success is True
        assert result.analysis is not None
        assert result.analysis.lead_temperature == "hot"
        assert len(result.actions) >= 1
        assert any(a["tag"] == "Hot-Voice-Lead" for a in result.actions)

    @pytest.mark.asyncio
    async def test_call_failed(self):
        vi = VapiVoiceIntelligence()
        result = await vi.process_call_event(
            {
                "message": {
                    "type": "call-failed",
                    "call": {"id": "call_fail", "status": "no_answer"},
                },
            }
        )
        assert result.success is True
        assert "failed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_transcript_update(self):
        vi = VapiVoiceIntelligence()
        # First register the call
        await vi.process_call_event(
            {
                "message": {"type": "call-started", "call": {"id": "call_t"}},
            }
        )
        # Then send transcript update
        result = await vi.process_call_event(
            {
                "message": {"type": "conversation-update", "call": {"id": "call_t"}},
                "transcript": [
                    {"role": "customer", "text": "I want to buy"},
                ],
            }
        )
        assert result.success is True
        assert vi._active_calls["call_t"].transcript_segments

    @pytest.mark.asyncio
    async def test_unknown_event_acknowledged(self):
        vi = VapiVoiceIntelligence()
        result = await vi.process_call_event(
            {
                "message": {"type": "some-unknown-event", "call": {"id": "call_u"}},
            }
        )
        assert result.success is True
        assert "acknowledged" in result.message


# ---------------------------------------------------------------------------
# Transcript Analysis
# ---------------------------------------------------------------------------


class TestTranscriptAnalysis:
    @pytest.mark.asyncio
    async def test_hot_transcript(self):
        detector = _mock_detector(composite=0.75)
        vi = VapiVoiceIntelligence(behavioral_detector=detector)

        segments = _sample_transcript()
        analysis = await vi.analyze_transcript(
            contact_id="c_hot",
            call_id="call_hot",
            transcript_segments=segments,
            call_duration_seconds=180,
        )
        assert analysis.lead_temperature == "hot"
        assert analysis.composite_score == 0.75
        assert analysis.customer_segments == 3
        assert analysis.processing_latency_ms >= 0

    @pytest.mark.asyncio
    async def test_cold_transcript(self):
        detector = _mock_detector(composite=0.2)
        vi = VapiVoiceIntelligence(behavioral_detector=detector)

        segments = [
            TranscriptSegment(role="agent", text="How can I help?"),
            TranscriptSegment(role="customer", text="Just looking"),
        ]
        analysis = await vi.analyze_transcript(
            contact_id="c_cold",
            call_id="call_cold",
            transcript_segments=segments,
        )
        assert analysis.lead_temperature == "cold"
        assert analysis.is_qualified is False

    @pytest.mark.asyncio
    async def test_no_detector_still_works(self):
        """Without behavioral detector, analysis should still return with zero scores."""
        vi = VapiVoiceIntelligence(behavioral_detector=None)
        analysis = await vi.analyze_transcript(
            contact_id="c_none",
            call_id="call_none",
            transcript_segments=_sample_transcript(),
        )
        assert analysis.composite_score == 0.0
        assert analysis.lead_temperature == "cold"

    @pytest.mark.asyncio
    async def test_empty_transcript(self):
        vi = VapiVoiceIntelligence()
        analysis = await vi.analyze_transcript(
            contact_id="c_empty",
            call_id="call_empty",
            transcript_segments=[],
        )
        assert analysis.total_segments == 0
        assert analysis.customer_segments == 0
        assert analysis.lead_temperature == "cold"

    @pytest.mark.asyncio
    async def test_detector_failure_graceful(self):
        detector = MagicMock()
        detector.analyze_message = AsyncMock(side_effect=RuntimeError("boom"))
        vi = VapiVoiceIntelligence(behavioral_detector=detector)

        analysis = await vi.analyze_transcript(
            contact_id="c_fail",
            call_id="call_fail",
            transcript_segments=_sample_transcript(),
        )
        # Should not crash, scores default to 0
        assert analysis.composite_score == 0.0


# ---------------------------------------------------------------------------
# Qualification Signal Extraction
# ---------------------------------------------------------------------------


class TestQualificationSignals:
    @pytest.mark.asyncio
    async def test_budget_detected(self):
        vi = VapiVoiceIntelligence()
        analysis = await vi.analyze_transcript(
            contact_id="c_budget",
            call_id="call_b",
            transcript_segments=[
                TranscriptSegment(role="customer", text="My budget is around $750k"),
            ],
        )
        assert analysis.qualification_signals.get("has_budget") is True

    @pytest.mark.asyncio
    async def test_timeline_detected(self):
        vi = VapiVoiceIntelligence()
        analysis = await vi.analyze_transcript(
            contact_id="c_timeline",
            call_id="call_t",
            transcript_segments=[
                TranscriptSegment(role="customer", text="I need to move within 3 months"),
            ],
        )
        assert analysis.qualification_signals.get("has_timeline") is True

    @pytest.mark.asyncio
    async def test_location_detected(self):
        vi = VapiVoiceIntelligence()
        analysis = await vi.analyze_transcript(
            contact_id="c_loc",
            call_id="call_l",
            transcript_segments=[
                TranscriptSegment(role="customer", text="I'm interested in the Victoria area"),
            ],
        )
        assert analysis.qualification_signals.get("has_location") is True

    @pytest.mark.asyncio
    async def test_pre_approval_detected(self):
        vi = VapiVoiceIntelligence()
        analysis = await vi.analyze_transcript(
            contact_id="c_pre",
            call_id="call_p",
            transcript_segments=[
                TranscriptSegment(role="customer", text="I'm pre-approved for 800k"),
            ],
        )
        assert analysis.qualification_signals.get("pre_approved") is True

    @pytest.mark.asyncio
    async def test_property_prefs_detected(self):
        vi = VapiVoiceIntelligence()
        analysis = await vi.analyze_transcript(
            contact_id="c_prefs",
            call_id="call_pr",
            transcript_segments=[
                TranscriptSegment(role="customer", text="Looking for 3 bedroom with a pool"),
            ],
        )
        assert analysis.qualification_signals.get("has_property_prefs") is True


# ---------------------------------------------------------------------------
# Full Qualification Pipeline
# ---------------------------------------------------------------------------


class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_qualified_hot_lead(self):
        """Customer with budget + timeline + high composite = qualified hot lead."""
        detector = _mock_detector(composite=0.8)
        vi = VapiVoiceIntelligence(behavioral_detector=detector)

        analysis = await vi.analyze_transcript(
            contact_id="c_full",
            call_id="call_full",
            transcript_segments=[
                TranscriptSegment(role="agent", text="What's your budget?"),
                TranscriptSegment(role="customer", text="I'm pre-approved for $800k and ready to move ASAP"),
            ],
            call_duration_seconds=120,
        )
        assert analysis.lead_temperature == "hot"
        assert analysis.is_qualified is True
        assert analysis.qualification_signals["has_budget"] is True
        assert analysis.qualification_signals["has_timeline"] is True
        assert analysis.call_duration_seconds == 120

    @pytest.mark.asyncio
    async def test_unqualified_warm_lead(self):
        """Customer with some interest but no budget/timeline = warm but not qualified."""
        detector = _mock_detector(composite=0.5)
        vi = VapiVoiceIntelligence(behavioral_detector=detector)

        analysis = await vi.analyze_transcript(
            contact_id="c_warm",
            call_id="call_warm",
            transcript_segments=[
                TranscriptSegment(role="customer", text="I'm just looking at houses"),
            ],
        )
        assert analysis.lead_temperature == "warm"
        assert analysis.is_qualified is False