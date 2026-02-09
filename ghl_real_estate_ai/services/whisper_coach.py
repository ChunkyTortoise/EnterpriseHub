"""
Whisper Mode Real-Time Coaching Engine - Section 3 of 2026 Strategic Roadmap
Provides live sentiment analysis and coaching cues for Jorge during calls.
"""

import json
from typing import Any, Dict, Optional

from pydantic import BaseModel

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

logger = get_logger(__name__)


class CoachingCue(BaseModel):
    sentiment: str
    objection_type: Optional[str] = None
    suggested_phrase: str
    inject_cma: bool = False
    priority: str = "MEDIUM"


class WhisperCoachEngine:
    """
    Analyzes live call transcripts to provide coaching cues to Jorge.
    """

    def __init__(self):
        self.claude = get_claude_orchestrator()
        import os

        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "coaching_library.json")
        try:
            with open(data_path, "r") as f:
                self.coaching_library = json.load(f)
        except FileNotFoundError:
            with open("ghl_real_estate_ai/data/coaching_library.json", "r") as f:
                self.coaching_library = json.load(f)

    async def analyze_transcript_chunk(self, transcript: str, lead_context: Dict[str, Any]) -> CoachingCue:
        """
        Analyzes a chunk of conversation to detect sentiment and objections.
        """
        logger.info(f"Whisper Mode: Analyzing chunk: '{transcript[:50]}...'")

        # In a real run, we'd use Claude to classify sentiment and detect objections
        # Here we'll use a rule-based engine for sub-second latency in the prototype

        lower_transcript = transcript.lower()
        sentiment = "NEUTRAL"
        if any(w in lower_transcript for k, w in [("pos", "great"), ("pos", "yes"), ("pos", "interested")]):
            sentiment = "POSITIVE"
        if any(w in lower_transcript for k, w in [("neg", "expensive"), ("neg", "but"), ("neg", "wait")]):
            sentiment = "RESISTANT"

        objection = None
        if "price" in lower_transcript or "expensive" in lower_transcript or "zillow" in lower_transcript:
            objection = "price_too_high"
        elif "wait" in lower_transcript or "next year" in lower_transcript:
            objection = "timeline_delay"
        elif "agent" in lower_transcript or "realtor" in lower_transcript:
            objection = "has_another_agent"

        # Get suggested phrase from library
        if objection:
            suggested = self.coaching_library[objection]["cue"]
            inject = objection == "price_too_high"
        else:
            suggested = "Keep building rapport. Ask about their 'why'."
            inject = False

        if sentiment == "RESISTANT" and not objection:
            suggested = self.coaching_library["hesitation"]["cue"]

        return CoachingCue(
            sentiment=sentiment,
            objection_type=objection,
            suggested_phrase=suggested,
            inject_cma=inject,
            priority="HIGH" if objection else "MEDIUM",
        )


_whisper_coach = None


def get_whisper_coach() -> WhisperCoachEngine:
    global _whisper_coach
    if _whisper_coach is None:
        _whisper_coach = WhisperCoachEngine()
    return _whisper_coach
