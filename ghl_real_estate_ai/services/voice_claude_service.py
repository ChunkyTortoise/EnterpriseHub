"""
Voice Claude Service - Speech-enabled AI Assistant
Extends the Claude assistant with voice interaction capabilities for mobile apps.
"""

import asyncio
import base64
import io
import json
import logging
import tempfile
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import aiofiles
import aiohttp
import speech_recognition as sr
from pydantic import BaseModel, ConfigDict, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant

logger = get_logger(__name__)


class VoiceInteractionType(str, Enum):
    """Types of voice interactions supported."""

    PROPERTY_INQUIRY = "property_inquiry"
    LEAD_UPDATE = "lead_update"
    SCHEDULE_SHOWING = "schedule_showing"
    MARKET_QUESTION = "market_question"
    GENERAL_ASSISTANCE = "general_assistance"


class AudioFormat(str, Enum):
    """Supported audio formats for voice processing."""

    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"
    WEBM = "webm"
    OGG = "ogg"


class VoiceRequest(BaseModel):
    """Voice interaction request model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    audio_data: str = Field(..., description="Base64 encoded audio data")
    audio_format: AudioFormat = Field(default=AudioFormat.WAV, description="Audio format")
    sample_rate: Optional[int] = Field(default=16000, description="Audio sample rate")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")
    language: str = Field(default="en-US", description="Expected language")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Conversation context")
    user_location: Optional[Dict[str, float]] = Field(None, description="User GPS location")
    interaction_type: Optional[VoiceInteractionType] = Field(None, description="Expected interaction type")


class VoiceResponse(BaseModel):
    """Voice interaction response model."""

    transcription: str = Field(..., description="Speech-to-text result")
    ai_response: str = Field(..., description="AI assistant response")
    audio_response: Optional[str] = Field(None, description="Base64 encoded audio response")
    confidence_score: float = Field(..., description="Transcription confidence")
    interaction_type: VoiceInteractionType = Field(..., description="Detected interaction type")
    extracted_entities: Dict[str, Any] = Field(default={}, description="Extracted entities from speech")
    suggested_actions: List[Dict[str, Any]] = Field(default=[], description="Suggested follow-up actions")
    session_id: str = Field(..., description="Voice session identifier")
    processing_time_ms: int = Field(..., description="Total processing time")


class VoiceCommand(BaseModel):
    """Structured voice command representation."""

    command_type: str = Field(..., description="Type of command")
    intent: str = Field(..., description="User intent")
    entities: Dict[str, Any] = Field(default={}, description="Extracted entities")
    confidence: float = Field(..., description="Intent confidence score")
    parameters: Dict[str, Any] = Field(default={}, description="Command parameters")


class VoiceSessionContext(BaseModel):
    """Voice conversation session context."""

    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    started_at: datetime = Field(default_factory=datetime.now)
    last_interaction: datetime = Field(default_factory=datetime.now)
    conversation_history: List[Dict[str, Any]] = Field(default=[], description="Conversation turns")
    current_context: Dict[str, Any] = Field(default={}, description="Current conversation context")
    properties_discussed: List[str] = Field(default=[], description="Properties mentioned in session")
    leads_mentioned: List[str] = Field(default=[], description="Leads mentioned in session")


class VoiceClaudeService:
    """Enhanced Claude assistant with voice capabilities."""

    def __init__(self, market_id: str = "austin"):
        self.claude_assistant = ClaudeAssistant(context_type="voice", market_id=market_id)
        self.market_id = market_id
        self.cache = None

        # Initialize speech recognition
        self.recognizer = sr.Recognizer()

        # Voice processing configuration
        self.supported_languages = ["en-US", "en-GB", "es-ES", "es-MX", "fr-FR", "de-DE", "it-IT", "pt-BR"]

        # Intent classification patterns
        self.intent_patterns = {
            VoiceInteractionType.PROPERTY_INQUIRY: [
                "tell me about",
                "what's the price",
                "show me properties",
                "house details",
                "square footage",
                "bedrooms",
                "bathrooms",
                "neighborhood",
                "schools",
            ],
            VoiceInteractionType.LEAD_UPDATE: [
                "update lead",
                "change status",
                "add note",
                "mark as",
                "follow up",
                "interested",
                "not interested",
                "qualified",
                "ready to buy",
            ],
            VoiceInteractionType.SCHEDULE_SHOWING: [
                "schedule",
                "book showing",
                "set appointment",
                "tour",
                "visit",
                "available times",
                "calendar",
                "meet",
                "viewing",
            ],
            VoiceInteractionType.MARKET_QUESTION: [
                "market conditions",
                "home values",
                "trends",
                "appreciation",
                "neighborhood stats",
                "comparable sales",
                "market analysis",
            ],
            VoiceInteractionType.GENERAL_ASSISTANCE: ["help", "what can you do", "how do I", "explain", "assist"],
        }

    async def _get_cache(self):
        """Get cache service instance."""
        if not self.cache:
            self.cache = get_cache_service()
        return self.cache

    async def process_voice_interaction(
        self, voice_request: VoiceRequest, user_id: str, session_id: Optional[str] = None
    ) -> VoiceResponse:
        """
        Process complete voice interaction: speech-to-text, AI processing, text-to-speech.
        """
        start_time = datetime.now()

        try:
            # Create or retrieve session
            if not session_id:
                session_id = str(uuid.uuid4())

            session_context = await self._get_or_create_session(session_id, user_id)

            # Step 1: Speech-to-Text
            transcription_result = await self._transcribe_audio(
                voice_request.audio_data, voice_request.audio_format, voice_request.language, voice_request.sample_rate
            )

            if not transcription_result["success"]:
                raise Exception(f"Transcription failed: {transcription_result['error']}")

            transcription = transcription_result["text"]
            confidence = transcription_result["confidence"]

            # Step 2: Intent Classification and Entity Extraction
            voice_command = await self._classify_intent_and_extract_entities(
                transcription, voice_request.context or {}, session_context
            )

            # Step 3: Update session context
            await self._update_session_context(
                session_context, transcription, voice_command, voice_request.user_location
            )

            # Step 4: Generate AI response using Claude
            ai_response = await self._generate_claude_voice_response(
                voice_command, session_context, voice_request.user_location
            )

            # Step 5: Text-to-Speech (optional)
            audio_response = None
            if voice_request.context and voice_request.context.get("include_audio_response", True):
                audio_response = await self._synthesize_speech(ai_response, voice_request.language)

            # Step 6: Generate suggested actions
            suggested_actions = await self._generate_suggested_actions(voice_command, ai_response, session_context)

            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Store session updates
            await self._save_session_context(session_context)

            return VoiceResponse(
                transcription=transcription,
                ai_response=ai_response,
                audio_response=audio_response,
                confidence_score=confidence,
                interaction_type=voice_command.command_type,
                extracted_entities=voice_command.entities,
                suggested_actions=suggested_actions,
                session_id=session_id,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Voice interaction processing error: {e}")

            # Return error response
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return VoiceResponse(
                transcription="",
                ai_response=f"I'm sorry, I couldn't process your request. Please try again. Error: {str(e)}",
                confidence_score=0.0,
                interaction_type=VoiceInteractionType.GENERAL_ASSISTANCE,
                session_id=session_id or str(uuid.uuid4()),
                processing_time_ms=processing_time,
            )

    async def _transcribe_audio(
        self, audio_data: str, audio_format: AudioFormat, language: str, sample_rate: Optional[int]
    ) -> Dict[str, Any]:
        """Convert speech to text using speech recognition."""
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)

            # Create temporary file for audio processing
            with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name

            try:
                # Load audio file
                with sr.AudioFile(temp_file_path) as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.record(source)

                # Transcribe using Google Speech Recognition (free tier)
                # In production, you'd use a more robust service like Azure Speech or Google Cloud Speech-to-Text
                try:
                    text = self.recognizer.recognize_google(audio, language=language)
                    confidence = 0.9  # Google API doesn't return confidence, so we estimate
                except sr.UnknownValueError:
                    return {"success": False, "error": "Speech not recognized", "text": "", "confidence": 0.0}
                except sr.RequestError as e:
                    return {
                        "success": False,
                        "error": f"Speech recognition service error: {e}",
                        "text": "",
                        "confidence": 0.0,
                    }

                return {"success": True, "text": text, "confidence": confidence, "language": language}

            finally:
                # Clean up temporary file
                import os

                try:
                    os.unlink(temp_file_path)
                except:
                    pass

        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            return {"success": False, "error": str(e), "text": "", "confidence": 0.0}

    async def _classify_intent_and_extract_entities(
        self, text: str, context: Dict[str, Any], session_context: VoiceSessionContext
    ) -> VoiceCommand:
        """Classify user intent and extract entities from transcribed text."""
        try:
            text_lower = text.lower()

            # Intent classification based on keywords
            intent_scores = {}
            for intent_type, keywords in self.intent_patterns.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                if score > 0:
                    intent_scores[intent_type] = score / len(keywords)

            # Get the highest scoring intent
            if intent_scores:
                detected_intent = max(intent_scores, key=intent_scores.get)
                confidence = intent_scores[detected_intent]
            else:
                detected_intent = VoiceInteractionType.GENERAL_ASSISTANCE
                confidence = 0.5

            # Extract entities based on intent
            entities = await self._extract_entities_by_intent(text, detected_intent, session_context)

            # Extract general parameters
            parameters = {"original_text": text, "word_count": len(text.split()), "context": context}

            return VoiceCommand(
                command_type=detected_intent,
                intent=detected_intent,
                entities=entities,
                confidence=confidence,
                parameters=parameters,
            )

        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return VoiceCommand(
                command_type=VoiceInteractionType.GENERAL_ASSISTANCE,
                intent="error_fallback",
                entities={},
                confidence=0.0,
                parameters={"error": str(e)},
            )

    async def _extract_entities_by_intent(
        self, text: str, intent: VoiceInteractionType, session_context: VoiceSessionContext
    ) -> Dict[str, Any]:
        """Extract entities based on the detected intent."""
        entities = {}
        text_lower = text.lower()

        try:
            if intent == VoiceInteractionType.PROPERTY_INQUIRY:
                # Extract property-related entities

                # Price mentions
                import re

                price_patterns = [
                    r"\$[\d,]+",
                    r"(\d+)\s*(?:Union[thousand, k])",
                    r"(\d+)\s*(?:Union[million, m])",
                    r"under (\d+)",
                    r"below (\d+)",
                    r"around (\d+)",
                ]

                for pattern in price_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        entities["price_mention"] = matches[0] if isinstance(matches[0], str) else str(matches[0])
                        break

                # Room counts
                bedroom_match = re.search(r"(\d+)\s*(?:Union[bed, bedroom])", text_lower)
                if bedroom_match:
                    entities["bedrooms"] = int(bedroom_match.group(1))

                bathroom_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:Union[bath, bathroom])", text_lower)
                if bathroom_match:
                    entities["bathrooms"] = float(bathroom_match.group(1))

                # Location mentions
                location_keywords = [
                    "downtown",
                    "south austin",
                    "north austin",
                    "west lake",
                    "cedar park",
                    "lakeway",
                    "bee cave",
                    "dripping springs",
                    "pflugerville",
                    "round rock",
                ]
                for location in location_keywords:
                    if location in text_lower:
                        entities["location"] = location
                        break

            elif intent == VoiceInteractionType.LEAD_UPDATE:
                # Extract lead status updates
                status_keywords = {
                    "hot": ["hot", "very interested", "ready to buy", "motivated"],
                    "warm": ["warm", "interested", "considering", "thinking about"],
                    "cold": ["cold", "not interested", "not ready", "maybe later"],
                    "qualified": ["qualified", "pre-approved", "approved", "financing ready"],
                    "unqualified": ["unqualified", "no financing", "not approved"],
                }

                for status, keywords in status_keywords.items():
                    if any(keyword in text_lower for keyword in keywords):
                        entities["lead_status"] = status
                        break

                # Extract lead names (simple approach - would be more sophisticated in production)
                if "lead" in text_lower:
                    # Look for common names mentioned
                    name_patterns = [
                        r"lead\s+(\w+)",
                        r"client\s+(\w+)",
                        r"buyer\s+(\w+)",
                        r"(\w+)\s+is\s+(?:Union[interested, not] Union[interested, qualified])",
                    ]

                    for pattern in name_patterns:
                        match = re.search(pattern, text_lower)
                        if match:
                            entities["lead_name"] = match.group(1).title()
                            break

            elif intent == VoiceInteractionType.SCHEDULE_SHOWING:
                # Extract scheduling information

                # Time mentions
                time_patterns = [
                    r"(\d{1,2})\s*(?:Union[am, pm])",
                    r"(\d{1,2}):(\d{2})\s*(?:Union[am, pm])",
                    r"(Union[morning, afternoon]|evening)",
                    r"(Union[today, tomorrow]|next Union[week, this] week)",
                ]

                for pattern in time_patterns:
                    match = re.search(pattern, text_lower)
                    if match:
                        entities["time_preference"] = match.group(0)
                        break

                # Date mentions
                date_patterns = [
                    r"(Union[monday, tuesday]|Union[wednesday, thursday]|Union[friday, saturday]|sunday)",
                    r"(\d{1,2})/(\d{1,2})",
                    r"(Union[january, february]|Union[march, april]|Union[may, june]|Union[july, august]|Union[september, october]|Union[november, december])\s+(\d{1,2})",
                ]

                for pattern in date_patterns:
                    match = re.search(pattern, text_lower)
                    if match:
                        entities["date_preference"] = match.group(0)
                        break

            elif intent == VoiceInteractionType.MARKET_QUESTION:
                # Extract market-related entities

                # Market areas
                if any(area in text_lower for area in ["austin", "travis county", "williamson county"]):
                    entities["market_area"] = "austin_metro"

                # Market metrics
                metric_keywords = {
                    "prices": ["price", "cost", "expensive", "affordable"],
                    "inventory": ["inventory", "homes available", "listings"],
                    "trends": ["trend", "direction", "going up", "going down"],
                    "appreciation": ["appreciation", "value increase", "growth"],
                }

                for metric, keywords in metric_keywords.items():
                    if any(keyword in text_lower for keyword in keywords):
                        entities["market_metric"] = metric
                        break

            # Always extract any property IDs mentioned
            property_id_match = re.search(r"property\s+(\w+\d+|\d+)", text_lower)
            if property_id_match:
                entities["property_id"] = property_id_match.group(1)

            # Extract any lead IDs mentioned
            lead_id_match = re.search(r"lead\s+(?:id\s+)?(\w+\d+|\d+)", text_lower)
            if lead_id_match:
                entities["lead_id"] = lead_id_match.group(1)

        except Exception as e:
            logger.warning(f"Entity extraction error: {e}")

        return entities

    async def _generate_claude_voice_response(
        self,
        voice_command: VoiceCommand,
        session_context: VoiceSessionContext,
        user_location: Optional[Dict[str, float]],
    ) -> str:
        """Generate AI response using Claude with voice-optimized prompting."""
        try:
            # Build context for Claude
            claude_context = {
                "interaction_type": voice_command.command_type,
                "user_intent": voice_command.intent,
                "extracted_entities": voice_command.entities,
                "conversation_history": session_context.conversation_history[-5:],  # Last 5 turns
                "user_location": user_location,
                "market_id": self.market_id,
                "voice_optimized": True,  # Signal for conversational response style
                "session_properties": session_context.properties_discussed,
                "session_leads": session_context.leads_mentioned,
            }

            # Use the enhanced Claude assistant
            if hasattr(self.claude_assistant, "orchestrator") and self.claude_assistant.orchestrator:
                # Use Claude orchestrator for sophisticated response
                query = self._build_voice_query(voice_command, session_context)
                response_obj = await self.claude_assistant.orchestrator.chat_query(query, claude_context)
                return response_obj.content
            else:
                # Fallback to rule-based responses
                return await self._generate_fallback_response(voice_command, session_context)

        except Exception as e:
            logger.error(f"Claude voice response generation error: {e}")
            return await self._generate_fallback_response(voice_command, session_context)

    def _build_voice_query(self, voice_command: VoiceCommand, session_context: VoiceSessionContext) -> str:
        """Build optimized query for Claude voice interaction."""
        base_query = voice_command.parameters.get("original_text", "")

        # Add voice-specific instructions
        voice_instructions = """
        Please provide a natural, conversational response optimized for voice interaction:
        - Keep responses under 30 seconds when spoken (roughly 200 words)
        - Use casual, friendly tone appropriate for Jorge's real estate business
        - Avoid complex formatting or lists that don't translate well to speech
        - If providing data, summarize key points rather than detailed figures
        - End with a clear next step or question to continue the conversation
        """

        # Add context-specific instructions
        if voice_command.command_type == VoiceInteractionType.PROPERTY_INQUIRY:
            context_instructions = (
                "Focus on the most compelling property features and provide actionable insights for the buyer."
            )
        elif voice_command.command_type == VoiceInteractionType.LEAD_UPDATE:
            context_instructions = "Confirm the update and suggest logical next steps for nurturing this lead."
        elif voice_command.command_type == VoiceInteractionType.SCHEDULE_SHOWING:
            context_instructions = "Help coordinate scheduling and provide relevant property preparation tips."
        else:
            context_instructions = "Provide helpful, actionable guidance."

        return f"{voice_instructions}\n\n{context_instructions}\n\nUser query: {base_query}"

    async def _generate_fallback_response(
        self, voice_command: VoiceCommand, session_context: VoiceSessionContext
    ) -> str:
        """Generate fallback response when Claude is unavailable."""

        intent = voice_command.command_type
        entities = voice_command.entities

        if intent == VoiceInteractionType.PROPERTY_INQUIRY:
            if "price_mention" in entities:
                return f"I can help you find properties around {entities['price_mention']}. Let me search our current listings in the Austin area. What specific neighborhoods are you most interested in?"
            elif "bedrooms" in entities or "bathrooms" in entities:
                beds = entities.get("bedrooms", "your preferred")
                baths = entities.get("bathrooms", "")
                bath_text = f" and {baths} bathrooms" if baths else ""
                return f"I'll look for properties with {beds} bedrooms{bath_text}. Are you looking at any particular area of Austin?"
            else:
                return "I'd be happy to help you find the perfect property. What are your main criteria - price range, number of bedrooms, or preferred neighborhoods?"

        elif intent == VoiceInteractionType.LEAD_UPDATE:
            if "lead_status" in entities:
                status = entities["lead_status"]
                lead_name = entities.get("lead_name", "that lead")
                return f"I've updated {lead_name}'s status to {status}. Based on this status, would you like me to suggest the next best action for follow-up?"
            else:
                return "I can help update lead information. Which lead would you like to update, and what changes should I make?"

        elif intent == VoiceInteractionType.SCHEDULE_SHOWING:
            if "time_preference" in entities or "date_preference" in entities:
                time_pref = entities.get("time_preference", "")
                date_pref = entities.get("date_preference", "")
                return f"I'll help you schedule a showing for {date_pref} {time_pref}. Which property should I book, and who is the client?"
            else:
                return "I can help schedule property showings. What property would you like to show, and when works best for your client?"

        elif intent == VoiceInteractionType.MARKET_QUESTION:
            return "I can provide Austin market insights. The market is currently showing steady appreciation with good buyer activity. What specific aspect would you like to know about - prices, inventory, or trends in a particular area?"

        else:
            return "I'm here to help with your real estate business. You can ask me about properties, update leads, schedule showings, or get market insights. What would you like to do?"

    async def _synthesize_speech(self, text: str, language: str = "en-US") -> Optional[str]:
        """Convert text to speech (placeholder implementation)."""
        try:
            # This would integrate with a TTS service like Azure Speech, Google Text-to-Speech, or AWS Polly
            # For now, we'll return None to indicate audio synthesis is not available

            # Example implementation would be:
            # 1. Call TTS API with text and voice settings
            # 2. Receive audio data
            # 3. Encode as base64
            # 4. Return base64 string

            logger.info(f"TTS would synthesize: {text[:50]}...")
            return None  # Audio synthesis not implemented in demo

        except Exception as e:
            logger.warning(f"Text-to-speech synthesis error: {e}")
            return None

    async def _generate_suggested_actions(
        self, voice_command: VoiceCommand, ai_response: str, session_context: VoiceSessionContext
    ) -> List[Dict[str, Any]]:
        """Generate suggested follow-up actions based on the interaction."""
        actions = []

        try:
            intent = voice_command.command_type
            entities = voice_command.entities

            if intent == VoiceInteractionType.PROPERTY_INQUIRY:
                actions.extend(
                    [
                        {
                            "action": "search_properties",
                            "title": "Search Properties",
                            "description": "Find matching properties based on criteria",
                            "icon": "search",
                            "priority": "high",
                        },
                        {
                            "action": "schedule_showing",
                            "title": "Schedule Showing",
                            "description": "Book a property viewing",
                            "icon": "calendar",
                            "priority": "medium",
                        },
                        {
                            "action": "get_market_analysis",
                            "title": "Market Analysis",
                            "description": "Get detailed neighborhood analysis",
                            "icon": "chart",
                            "priority": "medium",
                        },
                    ]
                )

            elif intent == VoiceInteractionType.LEAD_UPDATE:
                actions.extend(
                    [
                        {
                            "action": "view_lead_profile",
                            "title": "View Lead Profile",
                            "description": "See complete lead information",
                            "icon": "user",
                            "priority": "high",
                        },
                        {
                            "action": "send_follow_up",
                            "title": "Send Follow-up",
                            "description": "Send personalized message",
                            "icon": "message",
                            "priority": "high",
                        },
                        {
                            "action": "update_crm",
                            "title": "Update CRM",
                            "description": "Sync changes to GoHighLevel",
                            "icon": "sync",
                            "priority": "medium",
                        },
                    ]
                )

            elif intent == VoiceInteractionType.SCHEDULE_SHOWING:
                actions.extend(
                    [
                        {
                            "action": "confirm_appointment",
                            "title": "Confirm Appointment",
                            "description": "Send calendar invite",
                            "icon": "calendar-check",
                            "priority": "high",
                        },
                        {
                            "action": "prepare_showing_materials",
                            "title": "Prepare Materials",
                            "description": "Get listing sheets and comparables",
                            "icon": "file-text",
                            "priority": "medium",
                        },
                        {
                            "action": "set_reminders",
                            "title": "Set Reminders",
                            "description": "Add showing reminders",
                            "icon": "bell",
                            "priority": "medium",
                        },
                    ]
                )

            elif intent == VoiceInteractionType.MARKET_QUESTION:
                actions.extend(
                    [
                        {
                            "action": "generate_market_report",
                            "title": "Generate Report",
                            "description": "Create detailed market analysis",
                            "icon": "document",
                            "priority": "high",
                        },
                        {
                            "action": "find_comparables",
                            "title": "Find Comparables",
                            "description": "Get recent comparable sales",
                            "icon": "compare",
                            "priority": "medium",
                        },
                    ]
                )

            # Always add general actions
            actions.extend(
                [
                    {
                        "action": "voice_continue",
                        "title": "Continue Talking",
                        "description": "Ask another question",
                        "icon": "mic",
                        "priority": "low",
                    },
                    {
                        "action": "view_dashboard",
                        "title": "Open Dashboard",
                        "description": "Go to main dashboard",
                        "icon": "home",
                        "priority": "low",
                    },
                ]
            )

        except Exception as e:
            logger.warning(f"Error generating suggested actions: {e}")

        return actions

    async def _get_or_create_session(self, session_id: str, user_id: str) -> VoiceSessionContext:
        """Get existing session or create new one."""
        cache = await self._get_cache()

        # Try to get existing session
        session_data = await cache.get(f"voice_session:{session_id}")

        if session_data:
            return VoiceSessionContext(**session_data)
        else:
            # Create new session
            return VoiceSessionContext(session_id=session_id, user_id=user_id)

    async def _update_session_context(
        self,
        session_context: VoiceSessionContext,
        transcription: str,
        voice_command: VoiceCommand,
        user_location: Optional[Dict[str, float]],
    ):
        """Update session context with new interaction."""
        # Update timestamps
        session_context.last_interaction = datetime.now()

        # Add conversation turn
        conversation_turn = {
            "timestamp": session_context.last_interaction.isoformat(),
            "user_input": transcription,
            "intent": voice_command.command_type,
            "entities": voice_command.entities,
            "confidence": voice_command.confidence,
            "user_location": user_location,
        }
        session_context.conversation_history.append(conversation_turn)

        # Track mentioned properties and leads
        if "property_id" in voice_command.entities:
            property_id = voice_command.entities["property_id"]
            if property_id not in session_context.properties_discussed:
                session_context.properties_discussed.append(property_id)

        if "lead_id" in voice_command.entities or "lead_name" in voice_command.entities:
            lead_identifier = voice_command.entities.get("lead_id") or voice_command.entities.get("lead_name")
            if lead_identifier not in session_context.leads_mentioned:
                session_context.leads_mentioned.append(lead_identifier)

        # Update current context
        session_context.current_context.update(
            {
                "last_intent": voice_command.command_type,
                "last_entities": voice_command.entities,
                "interaction_count": len(session_context.conversation_history),
            }
        )

    async def _save_session_context(self, session_context: VoiceSessionContext):
        """Save session context to cache."""
        cache = await self._get_cache()

        # Convert to dict for storage
        session_data = session_context.dict()

        # Store with 2-hour expiry
        await cache.set(f"voice_session:{session_context.session_id}", session_data, ttl=7200)

    async def get_session_summary(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get summary of voice session activity."""
        try:
            session_context = await self._get_or_create_session(session_id, user_id)

            # Calculate summary statistics
            total_interactions = len(session_context.conversation_history)
            intent_counts = {}

            for turn in session_context.conversation_history:
                intent = turn.get("intent", "unknown")
                intent_counts[intent] = intent_counts.get(intent, 0) + 1

            # Calculate session duration
            session_duration = None
            if session_context.conversation_history:
                start_time = datetime.fromisoformat(session_context.conversation_history[0]["timestamp"])
                duration_seconds = (session_context.last_interaction - start_time).total_seconds()
                session_duration = f"{int(duration_seconds // 60)}m {int(duration_seconds % 60)}s"

            return {
                "session_id": session_id,
                "user_id": user_id,
                "started_at": session_context.started_at.isoformat(),
                "last_interaction": session_context.last_interaction.isoformat(),
                "duration": session_duration,
                "total_interactions": total_interactions,
                "intent_breakdown": intent_counts,
                "properties_discussed": session_context.properties_discussed,
                "leads_mentioned": session_context.leads_mentioned,
                "current_context": session_context.current_context,
            }

        except Exception as e:
            logger.error(f"Session summary error: {e}")
            return {"error": str(e), "session_id": session_id, "user_id": user_id}

    async def clear_session(self, session_id: str) -> bool:
        """Clear voice session data."""
        try:
            cache = await self._get_cache()
            await cache.delete(f"voice_session:{session_id}")
            return True
        except Exception as e:
            logger.error(f"Session clear error: {e}")
            return False
