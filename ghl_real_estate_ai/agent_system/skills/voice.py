"""
Voice Intelligence Skills.
Enables agents to process voice transcripts, extract intent, and bridge to other swarms.
"""

import base64
from typing import Any, Dict

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.voice_ai_service import VoiceInteractionType, get_voice_ai_service
from ghl_real_estate_ai.services.voice_service import get_voice_service

from .base import skill

logger = get_logger(__name__)


@skill(name="process_voice_intent", tags=["voice", "intent", "intelligence"])
async def process_voice_intent(transcript: str, agent_id: str = "swarm_commander") -> Dict[str, Any]:
    """
    Processes a voice transcript to extract real estate intent and bridging signals.

    Args:
        transcript: The transcribed text from a voice interaction.
        agent_id: The ID of the agent processing the voice.
    """
    voice_ai_service = get_voice_ai_service()

    # 1. Start a temporary interaction session for analysis
    interaction_id = await voice_ai_service.start_voice_interaction(
        agent_id=agent_id, interaction_type=VoiceInteractionType.GENERAL_INQUIRY
    )

    # 2. Process the transcript to get Claude-powered analytics
    result = await voice_ai_service.process_voice_input(interaction_id, transcript)

    # 3. End interaction
    await voice_ai_service.end_voice_interaction(interaction_id)

    # 4. Extract UI-triggering signals
    # In a real scenario, we'd look for keywords like "dashboard", "chart", "report", "view"
    ui_trigger = False
    ui_spec = ""

    transcript_lower = transcript.lower()
    if any(keyword in transcript_lower for keyword in ["show me", "build", "generate", "dashboard", "report", "chart"]):
        ui_trigger = True
        ui_spec = transcript  # Use the transcript as the initial spec

    return {
        "intent": result["analytics"]["key_intents"],
        "sentiment": result["analytics"]["overall_sentiment"],
        "ui_trigger": ui_trigger,
        "ui_spec": ui_spec,
        "next_best_action": result["next_best_action"],
    }


@skill(name="synthesize_voice_briefing", tags=["voice", "speech"])
async def synthesize_voice_briefing(text: str) -> Dict[str, Any]:
    """
    Synthesizes a text briefing into voice via ElevenLabs.
    """
    logger.info(f"Synthesizing voice briefing: {text[:50]}...")
    voice_service = get_voice_service()

    # Generate actual audio content
    audio_content = await voice_service.synthesize_speech(text)

    # Convert to base64 for easy transport in JSON
    audio_base64 = base64.b64encode(audio_content).decode("utf-8")

    return {"status": "success", "audio_data": audio_base64, "content_type": "audio/mpeg", "text": text}
