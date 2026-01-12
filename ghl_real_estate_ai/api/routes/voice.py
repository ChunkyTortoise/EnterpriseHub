"""
Voice API Routes for GHL Real Estate AI.
"""

from fastapi import APIRouter, BackgroundTasks, Request, Response

from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.voice_service import VoiceService

logger = get_logger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])

voice_service = VoiceService()
conversation_manager = ConversationManager()
ghl_client = GHLClient()


@router.post("/incoming")
async def handle_incoming_call(request: Request):
    """
    Handle an incoming voice call (e.g., from Twilio).
    Returns TwiML or similar XML response.
    """
    # For now, return a basic XML response to greet the caller
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Hey! Thanks for calling Jorge Sales's real estate team. How can I help you today?</Say>
    <Record action="/api/voice/process" maxLength="30" />
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/process")
async def process_voice_input(request: Request, background_tasks: BackgroundTasks):
    """
    Process recorded voice input.
    """
    # 1. Get audio from request (simulated)
    audio_content = b"mock_audio"  # Would extract from Twilio request

    # 2. Transcribe
    transcription = await voice_service.transcribe_audio(audio_content)
    logger.info(f"Voice Transcription: {transcription}")

    # 3. Generate AI response
    # For demo, use a dummy contact_id
    contact_id = "voice_contact_123"
    context = await conversation_manager.get_context(contact_id)

    ai_response = await conversation_manager.generate_response(
        user_message=transcription,
        contact_info={"first_name": "Caller"},
        context=context,
    )

    # 4. Synthesize AI response back to speech
    voice_response = await voice_service.synthesize_speech(ai_response.message)

    # 5. Return TwiML to play the response
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>{ai_response.message}</Say>
    <Record action="/api/voice/process" maxLength="30" />
</Response>"""

    # Update context in background
    background_tasks.add_task(
        conversation_manager.update_context,
        contact_id=contact_id,
        user_message=transcription,
        ai_response=ai_response.message,
        extracted_data=ai_response.extracted_data,
    )

    return Response(content=twiml, media_type="application/xml")
