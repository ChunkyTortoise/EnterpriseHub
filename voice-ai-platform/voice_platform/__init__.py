"""
Voice AI Platform for Real Estate.

A Pipecat-based voice agent platform integrating Twilio, Deepgram, ElevenLabs,
and Claude for real estate lead qualification and CRM integration.

Architecture:
    Twilio Voice API (WebSocket Media Stream)
        Pipecat Pipeline Orchestrator (<500ms e2e)
            Deepgram STT Nova-3 ($0.0077/min)
            Claude/GPT (Intent + Response)
            ElevenLabs TTS Flash (~75ms)
            EnterpriseHub APIs (LeadBot, GHL CRM, Calendar, Handoff)

Usage:
    from voice_platform import VoiceAgent, CallRecord
    from voice_platform.services.pipeline import create_pipeline
"""

from voice_platform.models.agent import VoiceAgent
from voice_platform.models.call import CallAnalytics, CallRecord, CallTranscript

__version__ = "0.1.0"
__all__ = [
    "VoiceAgent",
    "CallRecord",
    "CallTranscript",
    "CallAnalytics",
]
