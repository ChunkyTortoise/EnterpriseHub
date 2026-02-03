"""
Vapi Voice Conversation Intelligence

Processes inbound voice call events from Vapi.ai webhooks:
- Call lifecycle management (started, ended, failed)
- Real-time transcript analysis through behavioral trigger detection
- Voice-to-qualification pipeline (routes transcripts to lead scoring)
- Voice-specific analytics and latency tracking

Extends the existing ``VapiService`` (outbound calls) with inbound
intelligence and transcript qualification.

Usage::

    intelligence = VapiVoiceIntelligence(
        behavioral_detector=get_behavioral_detector(),
    )

    # Process a Vapi webhook event
    result = await intelligence.process_call_event(event_data)

    # Analyze a completed call transcript
    analysis = await intelligence.analyze_transcript(
        contact_id="c_123",
        transcript_segments=segments,
    )
"""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Data Models
# ---------------------------------------------------------------------------

class CallStatus(str, Enum):
    STARTED = "started"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    ENDED = "ended"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"


class CallDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class SpeakerRole(str, Enum):
    AGENT = "agent"
    CUSTOMER = "customer"
    SYSTEM = "system"


@dataclass
class TranscriptSegment:
    """A single segment from a Vapi transcript."""
    role: str  # SpeakerRole value
    text: str
    timestamp_ms: float = 0.0
    confidence: float = 1.0


@dataclass
class CallEvent:
    """Normalized Vapi call event."""
    event_type: str  # "call.started", "call.ended", "transcript", etc.
    call_id: str
    contact_id: Optional[str] = None
    contact_phone: Optional[str] = None
    direction: str = "inbound"
    status: str = "started"
    duration_seconds: float = 0.0
    transcript_segments: List[TranscriptSegment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptAnalysis:
    """Result of analyzing a voice call transcript."""
    contact_id: str
    call_id: str
    # Behavioral analysis
    composite_score: float  # 0-1 lead temperature
    hedging_score: float
    commitment_score: float
    urgency_score: float
    drift_direction: str
    recommended_technique: Optional[str]
    # Qualification
    lead_temperature: str  # "hot", "warm", "cold"
    is_qualified: bool
    qualification_signals: Dict[str, Any]
    # Metrics
    total_segments: int
    customer_segments: int
    avg_customer_response_length: float
    call_duration_seconds: float
    processing_latency_ms: float


@dataclass
class CallEventResult:
    """Result returned after processing a Vapi webhook event."""
    success: bool
    event_type: str
    call_id: str
    message: str
    analysis: Optional[TranscriptAnalysis] = None
    actions: List[Dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Voice Intelligence Service
# ---------------------------------------------------------------------------

class VapiVoiceIntelligence:
    """
    Processes Vapi.ai voice call events and extracts qualification
    intelligence from call transcripts.
    """

    # Temperature thresholds for voice qualification
    HOT_THRESHOLD = 0.65
    WARM_THRESHOLD = 0.40

    def __init__(self, behavioral_detector=None):
        self.behavioral_detector = behavioral_detector
        # Active call tracking: call_id → CallEvent
        self._active_calls: Dict[str, CallEvent] = {}

    # ------------------------------------------------------------------
    # Public API: process webhook events
    # ------------------------------------------------------------------

    async def process_call_event(
        self,
        event_data: Dict[str, Any],
    ) -> CallEventResult:
        """
        Process a raw Vapi webhook event payload.

        Handles event types:
        - call.started → register active call
        - call.ended → analyze transcript, return qualification
        - call.failed / no-answer → log and clean up
        - transcript → incremental transcript update
        """
        event = self._normalize_event(event_data)

        if event.event_type in ("call.started", "call-started"):
            return await self._handle_call_started(event)
        elif event.event_type in ("call.ended", "call-ended", "end-of-call-report"):
            return await self._handle_call_ended(event)
        elif event.event_type in ("call.failed", "call-failed"):
            return self._handle_call_failed(event)
        elif event.event_type in ("transcript", "conversation-update"):
            return self._handle_transcript_update(event)
        else:
            logger.info("Unhandled Vapi event type: %s", event.event_type)
            return CallEventResult(
                success=True,
                event_type=event.event_type,
                call_id=event.call_id,
                message=f"Event type '{event.event_type}' acknowledged",
            )

    # ------------------------------------------------------------------
    # Public API: analyze a transcript
    # ------------------------------------------------------------------

    async def analyze_transcript(
        self,
        contact_id: str,
        call_id: str,
        transcript_segments: List[TranscriptSegment],
        call_duration_seconds: float = 0.0,
    ) -> TranscriptAnalysis:
        """
        Run behavioral + qualification analysis on a completed transcript.
        """
        start_ts = time.monotonic()

        # Extract customer-only text
        customer_segments = [s for s in transcript_segments if s.role == SpeakerRole.CUSTOMER.value]
        customer_text = " ".join(s.text for s in customer_segments)

        # Calculate response metrics
        customer_lengths = [len(s.text.split()) for s in customer_segments]
        avg_length = sum(customer_lengths) / len(customer_lengths) if customer_lengths else 0

        # Run behavioral analysis on combined customer text
        behavioral = None
        if self.behavioral_detector and customer_text.strip():
            try:
                # Build conversation history from segments for context
                history = [{"message": s.text, "role": s.role} for s in transcript_segments]
                behavioral = await self.behavioral_detector.analyze_message(
                    message=customer_text,
                    contact_id=contact_id,
                    conversation_history=history,
                )
            except Exception as exc:
                logger.warning("Behavioral analysis failed for call %s: %s", call_id, exc)

        # Derive scores
        composite = behavioral.composite_score if behavioral else 0.0
        hedging = behavioral.hedging_score if behavioral else 0.0
        commitment = behavioral.commitment_score if behavioral else 0.0
        urgency = behavioral.urgency_score if behavioral else 0.0
        drift = behavioral.drift_direction if behavioral else "stable"
        technique = behavioral.recommended_technique if behavioral else None

        # Qualification signals from transcript content
        signals = self._extract_qualification_signals(customer_text)

        # Temperature classification
        if composite >= self.HOT_THRESHOLD:
            temperature = "hot"
        elif composite >= self.WARM_THRESHOLD:
            temperature = "warm"
        else:
            temperature = "cold"

        is_qualified = temperature == "hot" and signals.get("has_budget") and signals.get("has_timeline")

        processing_ms = (time.monotonic() - start_ts) * 1000

        return TranscriptAnalysis(
            contact_id=contact_id,
            call_id=call_id,
            composite_score=round(composite, 3),
            hedging_score=round(hedging, 3),
            commitment_score=round(commitment, 3),
            urgency_score=round(urgency, 3),
            drift_direction=drift,
            recommended_technique=technique,
            lead_temperature=temperature,
            is_qualified=is_qualified,
            qualification_signals=signals,
            total_segments=len(transcript_segments),
            customer_segments=len(customer_segments),
            avg_customer_response_length=round(avg_length, 1),
            call_duration_seconds=call_duration_seconds,
            processing_latency_ms=round(processing_ms, 2),
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _handle_call_started(self, event: CallEvent) -> CallEventResult:
        self._active_calls[event.call_id] = event
        logger.info(
            "Voice call started: %s (contact=%s, direction=%s)",
            event.call_id, event.contact_id, event.direction,
        )
        return CallEventResult(
            success=True,
            event_type=event.event_type,
            call_id=event.call_id,
            message="Call registered",
        )

    async def _handle_call_ended(self, event: CallEvent) -> CallEventResult:
        # Merge transcript from active call if available
        active = self._active_calls.pop(event.call_id, None)
        segments = event.transcript_segments
        if not segments and active:
            segments = active.transcript_segments

        contact_id = event.contact_id or (active.contact_id if active else "unknown")

        analysis = None
        actions: List[Dict[str, Any]] = []

        if segments:
            analysis = await self.analyze_transcript(
                contact_id=contact_id,
                call_id=event.call_id,
                transcript_segments=segments,
                call_duration_seconds=event.duration_seconds,
            )

            # Build GHL tag actions from analysis
            temp_tag_map = {"hot": "Hot-Voice-Lead", "warm": "Warm-Voice-Lead", "cold": "Cold-Voice-Lead"}
            actions.append({"type": "add_tag", "tag": temp_tag_map.get(analysis.lead_temperature, "Cold-Voice-Lead")})
            actions.append({"type": "add_tag", "tag": "Voice-Qualified"})

            if analysis.is_qualified:
                actions.append({"type": "add_tag", "tag": "Voice-Hot-Qualified"})

            logger.info(
                "Voice call analysis complete: %s → %s (composite=%.2f, qualified=%s, latency=%.0fms)",
                event.call_id, analysis.lead_temperature,
                analysis.composite_score, analysis.is_qualified,
                analysis.processing_latency_ms,
            )

        return CallEventResult(
            success=True,
            event_type=event.event_type,
            call_id=event.call_id,
            message="Call ended — analysis complete" if analysis else "Call ended — no transcript",
            analysis=analysis,
            actions=actions,
        )

    def _handle_call_failed(self, event: CallEvent) -> CallEventResult:
        self._active_calls.pop(event.call_id, None)
        logger.warning("Voice call failed: %s (status=%s)", event.call_id, event.status)
        return CallEventResult(
            success=True,
            event_type=event.event_type,
            call_id=event.call_id,
            message=f"Call failed: {event.status}",
        )

    def _handle_transcript_update(self, event: CallEvent) -> CallEventResult:
        """Append new segments to active call tracking."""
        active = self._active_calls.get(event.call_id)
        if active and event.transcript_segments:
            active.transcript_segments.extend(event.transcript_segments)

        return CallEventResult(
            success=True,
            event_type=event.event_type,
            call_id=event.call_id,
            message=f"Transcript updated ({len(event.transcript_segments)} segments)",
        )

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_event(data: Dict[str, Any]) -> CallEvent:
        """Normalize a raw Vapi webhook payload into a CallEvent."""
        # Vapi sends different structures depending on event type
        message = data.get("message", {})
        event_type = message.get("type", data.get("type", data.get("event", "unknown")))

        call_data = message.get("call", data.get("call", {}))
        call_id = call_data.get("id", data.get("call_id", "unknown"))

        customer = call_data.get("customer", {})
        contact_phone = customer.get("number", "")
        contact_id = (
            call_data.get("metadata", {}).get("contact_id")
            or data.get("contact_id", "")
        )

        # Parse transcript if present
        transcript_segments: List[TranscriptSegment] = []
        raw_transcript = data.get("transcript", message.get("transcript", []))
        if isinstance(raw_transcript, list):
            for seg in raw_transcript:
                if isinstance(seg, dict):
                    transcript_segments.append(TranscriptSegment(
                        role=seg.get("role", "customer"),
                        text=seg.get("text", seg.get("content", "")),
                        timestamp_ms=seg.get("timestamp", 0),
                        confidence=seg.get("confidence", 1.0),
                    ))

        # End-of-call report includes full artifact
        artifact = message.get("artifact", data.get("artifact", {}))
        if artifact and not transcript_segments:
            for seg in artifact.get("messages", []):
                transcript_segments.append(TranscriptSegment(
                    role=seg.get("role", "customer"),
                    text=seg.get("message", seg.get("content", "")),
                    timestamp_ms=seg.get("secondsFromStart", 0) * 1000,
                ))

        duration = (
            call_data.get("duration", 0)
            or artifact.get("duration", 0)
            or data.get("duration_seconds", 0)
        )

        return CallEvent(
            event_type=event_type,
            call_id=call_id,
            contact_id=contact_id,
            contact_phone=contact_phone,
            direction=call_data.get("direction", "inbound"),
            status=call_data.get("status", event_type.split(".")[-1] if "." in event_type else "unknown"),
            duration_seconds=float(duration),
            transcript_segments=transcript_segments,
            metadata=call_data.get("metadata", {}),
        )

    # ------------------------------------------------------------------
    # Qualification signal extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_qualification_signals(customer_text: str) -> Dict[str, Any]:
        """Extract qualification signals from combined customer text."""
        text_lower = customer_text.lower()
        signals: Dict[str, Any] = {}

        # Budget detection
        budget_patterns = [
            r"\$[\d,]+k?", r"\b\d{3,}k\b", r"\bbudget\b",
            r"\bafford\b", r"\bpre[\s-]?approved\b", r"\bmortgage\b",
        ]
        signals["has_budget"] = any(re.search(p, text_lower) for p in budget_patterns)

        # Timeline detection
        timeline_patterns = [
            r"\b(asap|immediately|this\s+month|next\s+month|soon)\b",
            r"\b\d+\s+(days?|weeks?|months?)\b",
            r"\b(ready\s+to|looking\s+to)\s+(move|buy|sell)\b",
        ]
        signals["has_timeline"] = any(re.search(p, text_lower) for p in timeline_patterns)

        # Location preferences
        location_patterns = [
            r"\b(victoria|haven|etiwanda|terra\s+vista|central\s+park)\b",
            r"\b(rancho|cucamonga|fontana|upland|ontario)\b",
        ]
        signals["has_location"] = any(re.search(p, text_lower) for p in location_patterns)

        # Property type preferences
        property_patterns = [
            r"\b\d+\s*(br|bed|bedroom)\b",
            r"\b(condo|townhouse|single\s+family|detached)\b",
            r"\b(pool|garage|yard|garden)\b",
        ]
        signals["has_property_prefs"] = any(re.search(p, text_lower) for p in property_patterns)

        # Pre-approval status
        signals["pre_approved"] = bool(re.search(r"\bpre[\s-]?approved\b", text_lower))

        return signals


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_intelligence: Optional[VapiVoiceIntelligence] = None


def get_voice_intelligence(**kwargs) -> VapiVoiceIntelligence:
    global _intelligence
    if _intelligence is None:
        _intelligence = VapiVoiceIntelligence(**kwargs)
    return _intelligence
