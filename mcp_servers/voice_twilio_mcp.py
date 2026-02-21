"""
Voice/Twilio MCP Server
Exposes Twilio integration tools for voice calls, SMS, call recording and transcription.

NOTE: This is a reference implementation / API design demo.
All data returned is simulated. Replace mock handlers with
real API integrations before production use.

Environment Variables Required:
- TWILIO_ACCOUNT_SID: Twilio Account SID
- TWILIO_AUTH_TOKEN: Twilio Auth Token
- TWILIO_PHONE_NUMBER: Twilio phone number for outgoing calls
- TWILIO_API_KEY: Twilio API Key (for token-based auth)
- TWILIO_API_SECRET: Twilio API Secret
- OPENAI_API_KEY: OpenAI API key for transcription
- DEEPGRAM_API_KEY: Deepgram API key for transcription (alternative)

Usage:
    python -m mcp_servers.voice_twilio_mcp
"""

import json
import os
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Create the MCP server
mcp = FastMCP("VoiceTwilio")


# =============================================================================
# Data Models
# =============================================================================


class CallStatus(str, Enum):
    QUEUED = "queued"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    BUSY = "busy"
    FAILED = "failed"
    NO_ANSWER = "no-answer"
    CANCELLED = "cancelled"


class CallDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class SmsStatus(str, Enum):
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNDELIVERED = "undelivered"


@dataclass
class CallRecord:
    """Record of a phone call"""

    call_sid: str
    from_number: str
    to_number: str
    direction: CallDirection
    status: CallStatus
    duration_seconds: int
    start_time: str
    end_time: str
    recording_url: Optional[str]
    transcription: Optional[str]
    cost: Optional[float]
    notes: Optional[str]


@dataclass
class SmsRecord:
    """Record of an SMS message"""

    message_sid: str
    from_number: str
    to_number: str
    body: str
    status: SmsStatus
    direction: CallDirection
    date_sent: str
    price: Optional[float]
    error_code: Optional[str]


@dataclass
class VoicemailInfo:
    """Voicemail message information"""

    call_sid: str
    from_number: str
    duration_seconds: int
    recording_url: str
    transcription: str
    transcript_confidence: float
    processed: bool  # Whether AI has processed this voicemail


@dataclass
class CallRecording:
    """Call recording metadata"""

    call_sid: str
    recording_sid: str
    recording_url: str
    recording_duration: int
    recording_type: str  # "archival" or "single-bridged"
    media_url: Optional[str]


@dataclass
class TranscriptionResult:
    """Transcription result with speakers"""

    recording_sid: str
    transcription_text: str
    confidence: float
    words: List[Dict[str, Any]]
    speakers: List[Dict[str, Any]]
    duration_seconds: int


# =============================================================================
# Twilio Client (Mock implementation - replace with actual Twilio SDK)
# =============================================================================


class TwilioClient:
    """Client for Twilio API integration"""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self.api_key = os.getenv("TWILIO_API_KEY", "")
        self.api_secret = os.getenv("TWILIO_API_SECRET", "")

        # In production, initialize actual Twilio client:
        # from twilio.rest import Client
        # self.client = Client(self.account_sid, self.auth_token)

    def _get_client(self):
        """Get or create Twilio client"""
        # from twilio.rest import Client
        # return Client(self.account_sid, self.auth_token)
        return None  # Mock

    async def make_call(
        self,
        to_number: str,
        from_number: Optional[str] = None,
        twiml_url: Optional[str] = None,
        twiml: Optional[str] = None,
        status_callback: Optional[str] = None,
    ) -> CallRecord:
        """Initiate an outbound phone call"""
        # Mock implementation - replace with actual API call
        call_sid = f"CA{self._generate_sid()}"

        return CallRecord(
            call_sid=call_sid,
            from_number=from_number or self.phone_number,
            to_number=to_number,
            direction=CallDirection.OUTBOUND,
            status=CallStatus.QUEUED,
            duration_seconds=0,
            start_time=datetime.now().isoformat(),
            end_time="",
            recording_url=None,
            transcription=None,
            cost=None,
            notes=None,
        )

    async def send_sms(
        self, to_number: str, body: str, from_number: Optional[str] = None, media_url: Optional[str] = None
    ) -> SmsRecord:
        """Send an SMS message"""
        # Mock implementation - replace with actual API call
        message_sid = f"SM{self._generate_sid()}"

        return SmsRecord(
            message_sid=message_sid,
            from_number=from_number or self.phone_number,
            to_number=to_number,
            body=body,
            status=SmsStatus.QUEUED,
            direction=CallDirection.OUTBOUND,
            date_sent=datetime.now().isoformat(),
            price=None,
            error_code=None,
        )

    async def get_call(self, call_sid: str) -> Optional[CallRecord]:
        """Get call details"""
        # Mock - would fetch from Twilio API
        return CallRecord(
            call_sid=call_sid,
            from_number="+1234567890",
            to_number="+1987654321",
            direction=CallDirection.INBOUND,
            status=CallStatus.COMPLETED,
            duration_seconds=180,
            start_time="2026-02-14T10:00:00Z",
            end_time="2026-02-14T10:03:00Z",
            recording_url=None,
            transcription=None,
            cost=0.05,
            notes=None,
        )

    async def get_call_recordings(self, call_sid: str) -> List[CallRecording]:
        """Get recordings for a call"""
        # Mock - would fetch from Twilio API
        return []

    async def get_call_transcription(self, call_sid: str) -> Optional[TranscriptionResult]:
        """Get transcription for a call"""
        # Mock - would process recording
        return TranscriptionResult(
            recording_sid="RR123456",
            transcription_text="Hello, I'm interested in the property at 123 Main Street.",
            confidence=0.95,
            words=[],
            speakers=[],
            duration_seconds=180,
        )

    async def get_voicemails(self, phone_number: str, limit: int = 10) -> List[VoicemailInfo]:
        """Get voicemail messages for a phone number"""
        # Mock - would fetch from Twilio
        return []

    async def get_call_history(
        self, phone_number: Optional[str] = None, limit: int = 20, start_date: Optional[str] = None
    ) -> List[CallRecord]:
        """Get call history"""
        # Mock - would fetch from Twilio
        return []

    async def get_sms_history(
        self, phone_number: Optional[str] = None, limit: int = 20, start_date: Optional[str] = None
    ) -> List[SmsRecord]:
        """Get SMS history"""
        # Mock - would fetch from Twilio
        return []

    def _generate_sid(self) -> str:
        """Generate a random SID for mock calls"""
        import random
        import string

        return "".join(random.choices(string.ascii_letters + string.digits, k=32))


# =============================================================================
# Transcription Client (Mock - can use Deepgram or OpenAI Whisper)
# =============================================================================


class TranscriptionClient:
    """Client for call transcription services"""

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.deepgram_key = os.getenv("DEEPGRAM_API_KEY", "")

    async def transcribe_audio(
        self, audio_url: str, language: str = "en", punctuate: bool = True
    ) -> TranscriptionResult:
        """Transcribe audio from URL"""
        # Mock - would use Deepgram or OpenAI Whisper API
        return TranscriptionResult(
            recording_sid="RR123456",
            transcription_text="This is a sample transcription of the call.",
            confidence=0.92,
            words=[
                {"word": "This", "start": 0.0, "end": 0.5, "confidence": 0.95},
                {"word": "is", "start": 0.5, "end": 0.7, "confidence": 0.98},
            ],
            speakers=[
                {"speaker": "Agent", "start": 0.0, "end": 60.0},
                {"speaker": "Caller", "start": 60.0, "end": 180.0},
            ],
            duration_seconds=180,
        )

    async def analyze_sentiment(self, transcription_text: str) -> Dict[str, Any]:
        """Analyze sentiment of transcription"""
        # Mock - would use Claude or other NLP
        return {
            "overall_sentiment": "positive",
            "sentiment_score": 0.75,
            "emotions": {"interested": 0.8, "happy": 0.6, "uncertain": 0.2},
            "key_topics": ["property", "viewing", "financing"],
        }


# =============================================================================
# Initialize clients
# =============================================================================

twilio_client = TwilioClient()
transcription_client = TranscriptionClient()


# Phone number validation pattern (E.164 format)
_PHONE_REGEX = re.compile(r"^\+[1-9]\d{1,14}$")


def _validate_phone_number(phone: str) -> None:
    """Validate phone number is in E.164 format."""
    if not _PHONE_REGEX.match(phone):
        raise ValueError(f"Invalid phone number format: '{phone}'. Expected E.164 format (e.g., +1234567890).")


# =============================================================================
# MCP Tools - Call Management
# =============================================================================


@mcp.tool()
async def make_call(
    to_number: str,
    twiml: Optional[str] = None,
    twiml_url: Optional[str] = None,
    record: bool = True,
    status_callback: Optional[str] = None,
) -> str:
    """
    Initiate an outbound phone call.

    Args:
        to_number: Recipient phone number (E.164 format, e.g., +1234567890)
        twiml: TwiML instructions for the call
        twiml_url: URL to fetch TwiML instructions from
        record: Whether to record the call
        status_callback: URL for call status callbacks

    Returns:
        JSON string containing call details
    """
    try:
        _validate_phone_number(to_number)
        call = await twilio_client.make_call(
            to_number=to_number, twiml=twiml, twiml_url=twiml_url, status_callback=status_callback
        )
        return json.dumps(asdict(call), indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "to_number": to_number})


@mcp.tool()
async def get_call_details(call_sid: str) -> str:
    """
    Get details of a specific call.

    Args:
        call_sid: The Twilio Call SID

    Returns:
        JSON string containing call details
    """
    try:
        call = await twilio_client.get_call(call_sid)
        if call:
            return json.dumps(asdict(call), indent=2, default=str)
        return json.dumps({"error": "Call not found", "call_sid": call_sid})
    except Exception as e:
        return json.dumps({"error": str(e), "call_sid": call_sid})


@mcp.tool()
async def end_call(call_sid: str) -> str:
    """
    End an active call.

    Args:
        call_sid: The Twilio Call SID to end

    Returns:
        JSON string confirming the action
    """
    try:
        # In production: client.calls(call_sid).update(status="completed")
        return json.dumps({"success": True, "call_sid": call_sid, "message": "Call ended successfully"})
    except Exception as e:
        return json.dumps({"error": str(e), "call_sid": call_sid})


@mcp.tool()
async def get_call_recordings(call_sid: str) -> str:
    """
    Get all recordings for a call.

    Args:
        call_sid: The Twilio Call SID

    Returns:
        JSON string containing recording details
    """
    try:
        recordings = await twilio_client.get_call_recordings(call_sid)
        result = [asdict(rec) for rec in recordings]
        return json.dumps({"call_sid": call_sid, "recordings": result, "count": len(result)}, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "call_sid": call_sid})


@mcp.tool()
async def get_call_history(
    phone_number: Optional[str] = None, limit: int = 20, start_date: Optional[str] = None
) -> str:
    """
    Get call history with optional filtering.

    Args:
        phone_number: Filter by phone number
        limit: Maximum number of records to return
        start_date: Filter calls after this date (ISO format)

    Returns:
        JSON string containing call history
    """
    try:
        calls = await twilio_client.get_call_history(phone_number=phone_number, limit=limit, start_date=start_date)
        result = [asdict(call) for call in calls]
        return json.dumps({"calls": result, "count": len(result)}, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# MCP Tools - SMS Management
# =============================================================================


@mcp.tool()
async def send_sms(to_number: str, body: str, media_url: Optional[str] = None) -> str:
    """
    Send an SMS message.

    Args:
        to_number: Recipient phone number (E.164 format)
        body: Message body
        media_url: Optional media URL (MMS)

    Returns:
        JSON string containing message details
    """
    try:
        _validate_phone_number(to_number)
        message = await twilio_client.send_sms(to_number=to_number, body=body, media_url=media_url)
        return json.dumps(asdict(message), indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "to_number": to_number})


@mcp.tool()
async def send_sms_template(to_number: str, template_name: str, variables: Optional[Dict[str, str]] = None) -> str:
    """
    Send an SMS using a predefined template.

    Args:
        to_number: Recipient phone number
        template_name: Name of the template to use
        variables: Variables to fill in the template

    Returns:
        JSON string containing message details
    """
    try:
        _validate_phone_number(to_number)
        # Template definitions
        templates = {
            "property_inquiry": "Hi {name}! Thanks for your interest in {property_address}. We're excited to tell you more. Reply STOP to unsubscribe.",
            "appointment_reminder": "Reminder: You have an appointment on {date} at {time}. Reply C to confirm or R to reschedule.",
            "voicemail_followup": "Hi {name}! I saw you left a voicemail about {topic}. I'd love to discuss this further. Call me back at {phone_number}.",
            "market_update": "Your monthly market update for {zip_code} is ready! Median price: ${median_price}. View details at {link}. Reply STOP to unsubscribe.",
            "new_listing": "New listing alert! {property_address} just hit the market at ${price}. {beds} bed, {baths} bath. Learn more: {link}",
        }

        if template_name not in templates:
            return json.dumps(
                {"error": f"Template '{template_name}' not found", "available_templates": list(templates.keys())}
            )

        # Fill template with safe formatting (missing keys become empty string)
        body = templates[template_name]
        if variables:
            body = body.format_map(defaultdict(str, variables))

        message = await twilio_client.send_sms(to_number=to_number, body=body)
        return json.dumps(asdict(message), indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_sms_history(phone_number: Optional[str] = None, limit: int = 20, start_date: Optional[str] = None) -> str:
    """
    Get SMS message history.

    Args:
        phone_number: Filter by phone number
        limit: Maximum number of records
        start_date: Filter messages after this date

    Returns:
        JSON string containing SMS history
    """
    try:
        messages = await twilio_client.get_sms_history(phone_number=phone_number, limit=limit, start_date=start_date)
        result = [asdict(msg) for msg in messages]
        return json.dumps({"messages": result, "count": len(result)}, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# MCP Tools - Transcription & Analysis
# =============================================================================


@mcp.tool()
async def transcribe_call_recording(recording_url: str, language: str = "en") -> str:
    """
    Transcribe a call recording.

    Args:
        recording_url: URL of the recording audio file
        language: Language code (default: en)

    Returns:
        JSON string containing transcription
    """
    try:
        result = await transcription_client.transcribe_audio(audio_url=recording_url, language=language)
        return json.dumps(asdict(result), indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_call_transcription(call_sid: str) -> str:
    """
    Get or generate transcription for a call.

    Args:
        call_sid: The Twilio Call SID

    Returns:
        JSON string containing transcription
    """
    try:
        result = await twilio_client.get_call_transcription(call_sid)
        if result:
            return json.dumps(asdict(result), indent=2, default=str)
        return json.dumps({"error": "No transcription available", "call_sid": call_sid})
    except Exception as e:
        return json.dumps({"error": str(e), "call_sid": call_sid})


@mcp.tool()
async def analyze_voicemail(call_sid: str) -> str:
    """
    Analyze a voicemail with AI to extract key information.

    Args:
        call_sid: The call SID of the voicemail

    Returns:
        JSON string containing voicemail analysis
    """
    try:
        # Get recording and transcription
        call = await twilio_client.get_call(call_sid)

        if not call or not call.recording_url:
            return json.dumps({"error": "No recording found", "call_sid": call_sid})

        transcription = await transcription_client.transcribe_audio(call.recording_url)
        sentiment = await transcription_client.analyze_sentiment(transcription.transcription_text)

        # Extract key information
        analysis = {
            "call_sid": call_sid,
            "from_number": call.from_number,
            "duration_seconds": call.duration_seconds,
            "transcription": transcription.transcription_text,
            "confidence": transcription.confidence,
            "sentiment_analysis": sentiment,
            "summary": f"Caller from {call.from_number} left a {call.duration_seconds}s voicemail. Sentiment: {sentiment['overall_sentiment']}",
            "action_items": _extract_action_items(transcription.transcription_text),
            "processed_at": datetime.now().isoformat(),
        }

        return json.dumps(analysis, indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": str(e), "call_sid": call_sid})


def _extract_action_items(transcription_text: str) -> List[str]:
    """Extract action items from transcription"""
    # Simple mock - in production use NLP
    action_items = []

    text_lower = transcription_text.lower()

    if "call back" in text_lower:
        action_items.append("Return phone call")
    if "schedule" in text_lower or "appointment" in text_lower:
        action_items.append("Schedule appointment")
    if "price" in text_lower or "cost" in text_lower:
        action_items.append("Provide pricing information")
    if "interested" in text_lower:
        action_items.append("Follow up on interest")

    return action_items


# =============================================================================
# MCP Tools - Voicemail Management
# =============================================================================


@mcp.tool()
async def get_voicemails(phone_number: str, limit: int = 10) -> str:
    """
    Get voicemail messages for a phone number.

    Args:
        phone_number: The phone number to check voicemails for
        limit: Maximum number of voicemails to return

    Returns:
        JSON string containing voicemail list
    """
    try:
        voicemails = await twilio_client.get_voicemails(phone_number, limit=limit)
        result = [asdict(vm) for vm in voicemails]
        return json.dumps({"voicemails": result, "count": len(result)}, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# MCP Tools - Call Routing
# =============================================================================


@mcp.tool()
async def route_call(
    from_number: str,
    lead_score: Optional[float] = None,
    property_interest: Optional[str] = None,
    last_interaction: Optional[str] = None,
) -> str:
    """
    Route an incoming call based on lead intelligence.

    Args:
        from_number: Caller's phone number
        lead_score: Lead score (0-100) if available
        property_interest: Property or area of interest
        last_interaction: Description of last interaction

    Returns:
        JSON string containing routing decision
    """
    try:
        # Determine routing based on lead score
        if lead_score and lead_score >= 80:
            route_to = "live_agent"
            priority = "high"
            greeting = "Thank you for calling! Let me connect you with a senior agent right away."
        elif lead_score and lead_score >= 50:
            route_to = "junior_agent"
            priority = "medium"
            greeting = "Thanks for calling! An agent will be with you shortly."
        else:
            route_to = "self_service"
            priority = "low"
            greeting = (
                "Welcome! Press 1 for property listings, 2 for market information, or stay on the line for an agent."
            )

        routing_decision = {
            "from_number": from_number,
            "route_to": route_to,
            "priority": priority,
            "greeting": greeting,
            "lead_score": lead_score,
            "property_interest": property_interest,
            "last_interaction": last_interaction,
            "estimated_wait_time_seconds": 30 if route_to != "self_service" else 0,
            "routing_rules_applied": ["lead_score_threshold", "property_interest_match"],
        }

        return json.dumps(routing_decision, indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# MCP Resources
# =============================================================================


@mcp.resource("voice://status-callback")
async def get_call_status_codes() -> str:
    """Get list of call status callback codes"""
    return json.dumps(
        {
            "call_statuses": [
                {"value": status.value, "description": desc}
                for status, desc in [
                    (CallStatus.QUEUED, "Call is queued"),
                    (CallStatus.RINGING, "Call is ringing"),
                    (CallStatus.IN_PROGRESS, "Call is in progress"),
                    (CallStatus.COMPLETED, "Call has completed"),
                    (CallStatus.BUSY, "Line is busy"),
                    (CallStatus.FAILED, "Call failed"),
                    (CallStatus.NO_ANSWER, "No answer"),
                    (CallStatus.CANCELLED, "Call was cancelled"),
                ]
            ]
        }
    )


@mcp.resource("voice://templates")
async def get_sms_templates() -> str:
    """Get available SMS templates"""
    return json.dumps(
        {
            "templates": [
                {
                    "name": "property_inquiry",
                    "description": "Response to property inquiry",
                    "variables": ["name", "property_address"],
                },
                {"name": "appointment_reminder", "description": "Appointment reminder", "variables": ["date", "time"]},
                {
                    "name": "voicemail_followup",
                    "description": "Follow up to voicemail",
                    "variables": ["name", "topic", "phone_number"],
                },
                {
                    "name": "market_update",
                    "description": "Monthly market update",
                    "variables": ["zip_code", "median_price", "link"],
                },
                {
                    "name": "new_listing",
                    "description": "New listing alert",
                    "variables": ["property_address", "price", "beds", "baths", "link"],
                },
            ]
        }
    )


# =============================================================================
# MCP Prompts
# =============================================================================


@mcp.prompt()
def generate_call_summary() -> str:
    """Prompt for generating a call summary from transcription"""
    return """
    Generate a concise summary of the following call transcription:
    
    {transcription}
    
    Include:
    1. Caller intent
    2. Key information exchanged
    3. Next steps/action items
    4. Sentiment assessment
    """


@mcp.prompt()
def generate_voicemail_response() -> str:
    """Prompt for generating a response to a voicemail"""
    return """
    The caller left this voicemail:
    
    {voicemail_transcription}
    
    Generate an appropriate SMS response that:
    1. Acknowledges their interest
    2. Provides relevant information
    3. Includes a clear call to action
    4. Is concise (under 160 characters if possible)
    """


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        import asyncio

        async def test():
            result = await send_sms("+1234567890", "Test message from MCP")
            print(result)

        asyncio.run(test())
    else:
        mcp.run()
