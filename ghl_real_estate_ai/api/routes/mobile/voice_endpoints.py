"""
Mobile Voice API Endpoints (Phase 4: Mobile Optimization)

REST API endpoints for mobile voice integration with Claude AI.
Optimized for mobile devices with voice-to-text and text-to-speech capabilities.

Features:
- Voice session management
- Real-time voice processing
- Audio upload and transcription
- Voice coaching responses
- Voice command handling
- Audio streaming support
- Mobile-optimized error handling

Performance Targets:
- Voice processing: <100ms
- Audio upload: Streaming support
- Response generation: <150ms
- Concurrent voice sessions: 50+ per server
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
import asyncio
import logging
import time
from datetime import datetime
import json
import io

# Local imports
from ghl_real_estate_ai.services.claude.mobile.voice_integration_service import (
    VoiceIntegrationService,
    VoiceState,
    VoiceCommand,
    VoiceProcessingResult,
    VoiceResponse,
    VoiceSession
)
from ghl_real_estate_ai.services.claude.mobile.mobile_coaching_service import (
    MobileCoachingService,
    MobileCoachingMode,
    MobileCoachingContext
)

logger = logging.getLogger(__name__)

# Initialize services
voice_service = VoiceIntegrationService()
mobile_coaching_service = MobileCoachingService()

# Create router
voice_router = APIRouter(prefix="/api/v1/mobile/voice", tags=["Mobile Voice"])


# Request/Response Models
class StartVoiceSessionRequest(BaseModel):
    agent_id: str = Field(..., description="Agent identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Session context")
    device_info: Optional[Dict[str, Any]] = Field(default=None, description="Device capabilities")
    network_status: str = Field(default="wifi", description="Network connection type")
    battery_level: Optional[float] = Field(default=None, description="Battery level (0.0-1.0)")


class VoiceProcessingRequest(BaseModel):
    session_id: str = Field(..., description="Voice session ID")
    context: Optional[str] = Field(default=None, description="Conversation context")
    urgency_level: str = Field(default="normal", description="Response urgency")


class VoiceCoachingRequest(BaseModel):
    session_id: str = Field(..., description="Voice session ID")
    conversation_context: str = Field(..., description="Current conversation context")
    client_message: str = Field(..., description="Latest client message")
    priority: str = Field(default="normal", description="Coaching priority")


class VoiceCommandRequest(BaseModel):
    session_id: str = Field(..., description="Voice session ID")
    command_text: str = Field(..., description="Voice command text")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Command context")


class VoiceSessionResponse(BaseModel):
    session_id: str
    agent_id: str
    state: str
    start_time: str
    context: Dict[str, Any]
    success: bool
    message: Optional[str] = None


class VoiceProcessingResponse(BaseModel):
    text: str
    confidence: float
    processing_time_ms: int
    detected_command: Optional[str] = None
    audio_quality: float
    background_noise_level: float
    success: bool
    message: Optional[str] = None


class VoiceCoachingResponse(BaseModel):
    coaching_text: str
    audio_available: bool
    emotion_tone: str
    priority: str
    processing_time_ms: int
    quick_actions: List[str]
    success: bool
    message: Optional[str] = None


class VoicePerformanceResponse(BaseModel):
    active_sessions: int
    average_processing_time_ms: float
    voice_latency_target_ms: int
    performance_target_met: bool
    voice_dependencies_available: bool


# Voice Session Management Endpoints

@voice_router.post("/sessions/start", response_model=VoiceSessionResponse)
async def start_voice_session(request: StartVoiceSessionRequest):
    """
    Start a new voice interaction session for mobile agent

    Creates a voice session optimized for mobile device capabilities,
    network conditions, and battery life.
    """
    try:
        start_time = time.time()

        # Create mobile coaching context
        coaching_context = MobileCoachingContext(
            agent_id=request.agent_id,
            session_id="",  # Will be set by voice service
            mode=MobileCoachingMode.QUICK_INSIGHTS,  # Default for voice
            client_info=request.context or {},
            device_info=request.device_info,
            network_status=request.network_status,
            battery_level=request.battery_level
        )

        # Start voice session
        voice_session = await voice_service.start_voice_session(
            agent_id=request.agent_id,
            context=request.context
        )

        # Update coaching context with session ID
        coaching_context.session_id = voice_session.session_id

        # Start mobile coaching session
        mobile_session = await mobile_coaching_service.start_mobile_coaching_session(
            agent_id=request.agent_id,
            context=coaching_context
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Voice session started: {voice_session.session_id} in {processing_time_ms}ms")

        return VoiceSessionResponse(
            session_id=voice_session.session_id,
            agent_id=voice_session.agent_id,
            state=voice_session.state.value,
            start_time=voice_session.start_time.isoformat(),
            context=voice_session.context,
            success=True
        )

    except Exception as e:
        logger.error(f"Error starting voice session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.get("/sessions/{session_id}/status", response_model=Dict[str, Any])
async def get_voice_session_status(session_id: str):
    """Get current status of voice session"""
    try:
        status = voice_service.get_session_status(session_id)

        if not status:
            raise HTTPException(status_code=404, detail="Voice session not found")

        return {
            "session_status": status,
            "mobile_coaching_active": session_id in mobile_coaching_service.active_sessions,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.post("/sessions/{session_id}/end")
async def end_voice_session(session_id: str):
    """End voice session and provide summary"""
    try:
        # End voice session
        voice_summary = await voice_service.end_voice_session(session_id)

        # End mobile coaching session
        mobile_summary = await mobile_coaching_service.end_mobile_coaching_session(session_id)

        return {
            "voice_summary": voice_summary,
            "mobile_coaching_summary": mobile_summary,
            "session_ended": True,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

    except Exception as e:
        logger.error(f"Error ending voice session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Voice Processing Endpoints

@voice_router.post("/process-audio", response_model=VoiceProcessingResponse)
async def process_voice_audio(
    session_id: str = Form(...),
    audio_file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    urgency_level: str = Form("normal")
):
    """
    Process uploaded audio file and convert to text with analysis

    Supports various audio formats and provides real-time transcription
    with voice command detection and coaching suggestions.
    """
    try:
        start_time = time.time()

        # Validate session
        session_status = voice_service.get_session_status(session_id)
        if not session_status:
            raise HTTPException(status_code=404, detail="Voice session not found")

        # Read audio data
        audio_data = await audio_file.read()

        # Validate audio file
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        if len(audio_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Audio file too large (max 10MB)")

        # Process voice input
        result = await voice_service.process_voice_input(
            session_id=session_id,
            audio_data=audio_data,
            format=audio_file.filename.split('.')[-1] if '.' in audio_file.filename else "wav"
        )

        total_processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Audio processed in {total_processing_time_ms}ms: {result.confidence:.2f} confidence")

        return VoiceProcessingResponse(
            text=result.text,
            confidence=result.confidence,
            processing_time_ms=total_processing_time_ms,
            detected_command=result.detected_command.value if result.detected_command else None,
            audio_quality=result.audio_quality,
            background_noise_level=result.background_noise_level,
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing voice audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.post("/coaching", response_model=VoiceCoachingResponse)
async def generate_voice_coaching(request: VoiceCoachingRequest):
    """
    Generate voice coaching response with text-to-speech

    Provides real-time coaching insights optimized for mobile voice interaction
    with optional audio synthesis for hands-free operation.
    """
    try:
        start_time = time.time()

        # Validate session
        session_status = voice_service.get_session_status(request.session_id)
        if not session_status:
            raise HTTPException(status_code=404, detail="Voice session not found")

        # Get mobile coaching suggestion first
        mobile_suggestion = await mobile_coaching_service.get_mobile_coaching_suggestion(
            session_id=request.session_id,
            conversation_context=request.conversation_context,
            client_message=request.client_message,
            urgency_level=request.priority
        )

        if mobile_suggestion:
            # Use mobile coaching suggestion for voice
            coaching_response = VoiceResponse(
                text=mobile_suggestion.message,
                emotion_tone="supportive",
                priority=mobile_suggestion.priority.value
            )
            quick_actions = [action.value for action in mobile_suggestion.quick_actions]
        else:
            # Generate voice coaching directly
            coaching_response = await voice_service.generate_voice_coaching(
                session_id=request.session_id,
                conversation_context=request.conversation_context,
                client_message=request.client_message
            )
            quick_actions = ["respond", "ask_question", "take_notes"]

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Voice coaching generated in {processing_time_ms}ms")

        return VoiceCoachingResponse(
            coaching_text=coaching_response.text,
            audio_available=coaching_response.audio_data is not None,
            emotion_tone=coaching_response.emotion_tone,
            priority=coaching_response.priority,
            processing_time_ms=processing_time_ms,
            quick_actions=quick_actions,
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating voice coaching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.get("/coaching/{session_id}/audio")
async def get_coaching_audio(session_id: str, text: str):
    """
    Get text-to-speech audio for coaching text

    Generates audio response for hands-free coaching during client interactions.
    """
    try:
        # Validate session
        session_status = voice_service.get_session_status(session_id)
        if not session_status:
            raise HTTPException(status_code=404, detail="Voice session not found")

        # Generate audio (this would be implemented in voice service)
        audio_data = await voice_service._text_to_speech(text)

        if not audio_data:
            raise HTTPException(status_code=500, detail="Audio generation failed")

        # Return audio as streaming response
        audio_stream = io.BytesIO(audio_data)

        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=coaching_audio.wav"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating coaching audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Voice Command Endpoints

@voice_router.post("/commands/execute")
async def execute_voice_command(request: VoiceCommandRequest):
    """
    Execute voice command with optional context

    Processes voice commands like "start coaching", "take notes", "end session"
    and executes appropriate actions.
    """
    try:
        # Validate session
        session_status = voice_service.get_session_status(request.session_id)
        if not session_status:
            raise HTTPException(status_code=404, detail="Voice session not found")

        # Detect command from text
        detected_command = voice_service._detect_voice_command(request.command_text)

        if not detected_command:
            return {
                "success": False,
                "message": "Voice command not recognized",
                "available_commands": [cmd.value for cmd in VoiceCommand]
            }

        # Handle the voice command
        await voice_service._handle_voice_command(detected_command, request.session_id)

        return {
            "command_executed": detected_command.value,
            "success": True,
            "message": f"Successfully executed: {detected_command.value}",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing voice command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.get("/commands/available")
async def get_available_voice_commands():
    """Get list of available voice commands"""
    try:
        commands = []
        for command in VoiceCommand:
            patterns = voice_service.command_patterns.get(command, [])
            commands.append({
                "command": command.value,
                "patterns": patterns,
                "description": f"Voice command for {command.value.replace('_', ' ')}"
            })

        return {
            "available_commands": commands,
            "total_commands": len(commands),
            "success": True
        }

    except Exception as e:
        logger.error(f"Error getting available commands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Performance and Monitoring Endpoints

@voice_router.get("/performance", response_model=VoicePerformanceResponse)
async def get_voice_performance_metrics():
    """Get voice integration performance metrics"""
    try:
        metrics = await voice_service.get_performance_metrics()

        return VoicePerformanceResponse(
            active_sessions=metrics["active_sessions"],
            average_processing_time_ms=metrics["average_processing_time_ms"],
            voice_latency_target_ms=metrics["voice_latency_target_ms"],
            performance_target_met=metrics["performance_target_met"] > 80,  # 80% threshold
            voice_dependencies_available=metrics["voice_dependencies_available"]
        )

    except Exception as e:
        logger.error(f"Error getting voice performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.get("/health")
async def voice_health_check():
    """Health check for voice services"""
    try:
        # Check voice service health
        voice_healthy = voice_service.speech_recognizer is not None and voice_service.tts_engine is not None

        # Check mobile coaching service health
        mobile_healthy = len(mobile_coaching_service.offline_coaching_cache) > 0

        return {
            "voice_service": {
                "healthy": voice_healthy,
                "speech_recognition": voice_service.speech_recognizer is not None,
                "text_to_speech": voice_service.tts_engine is not None
            },
            "mobile_coaching": {
                "healthy": mobile_healthy,
                "offline_cache_ready": mobile_healthy,
                "active_sessions": len(mobile_coaching_service.active_sessions)
            },
            "overall_health": voice_healthy and mobile_healthy,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in voice health check: {e}")
        return {
            "voice_service": {"healthy": False, "error": str(e)},
            "mobile_coaching": {"healthy": False},
            "overall_health": False,
            "timestamp": datetime.now().isoformat()
        }


# Utility Endpoints

@voice_router.get("/audio-formats")
async def get_supported_audio_formats():
    """Get list of supported audio formats for voice processing"""
    return {
        "supported_formats": ["wav", "mp3", "m4a", "ogg", "webm"],
        "recommended_format": "wav",
        "max_file_size_mb": 10,
        "recommended_sample_rate": 16000,
        "recommended_bit_depth": 16
    }


@voice_router.post("/test-audio")
async def test_audio_upload(audio_file: UploadFile = File(...)):
    """Test audio file upload and basic validation"""
    try:
        audio_data = await audio_file.read()

        return {
            "filename": audio_file.filename,
            "content_type": audio_file.content_type,
            "file_size_bytes": len(audio_data),
            "file_size_mb": len(audio_data) / (1024 * 1024),
            "valid_size": len(audio_data) <= 10 * 1024 * 1024,  # 10MB limit
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

    except Exception as e:
        logger.error(f"Error testing audio upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))