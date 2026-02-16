"""Twilio WebSocket media streams handler."""

from __future__ import annotations

import audioop
import base64
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Twilio sends mulaw 8kHz; Deepgram wants linear16 16kHz
TWILIO_SAMPLE_RATE = 8000
TARGET_SAMPLE_RATE = 16000


@dataclass
class TwilioHandler:
    """Manages Twilio call lifecycle and media streams."""

    account_sid: str
    auth_token: str
    base_url: str
    phone_number: str = ""

    def generate_stream_twiml(self, call_id: str) -> str:
        """Generate TwiML to connect an inbound call to our WebSocket pipeline."""
        from twilio.twiml.voice_response import VoiceResponse, Connect

        response = VoiceResponse()
        connect = Connect()
        connect.stream(
            url=f"wss://{self.base_url}/api/v1/voice/ws",
            track="both_tracks",
        )
        response.append(connect)
        return str(response)

    async def initiate_outbound_call(
        self, to_number: str, from_number: str | None = None, call_id: str = ""
    ) -> dict[str, Any]:
        """Initiate an outbound call via Twilio REST API."""
        from twilio.rest import Client

        client = Client(self.account_sid, self.auth_token)
        call = client.calls.create(
            to=to_number,
            from_=from_number or self.phone_number,
            twiml=self.generate_stream_twiml(call_id),
            status_callback=f"https://{self.base_url}/api/v1/webhooks/twilio/status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            record=False,
        )
        return {"call_sid": call.sid, "status": call.status}

    @staticmethod
    def decode_twilio_audio(payload: str) -> bytes:
        """Decode Twilio's base64 mulaw 8kHz audio to linear16 16kHz."""
        mulaw_bytes = base64.b64decode(payload)
        # Convert mulaw to linear PCM
        pcm_8k = audioop.ulaw2lin(mulaw_bytes, 2)
        # Upsample from 8kHz to 16kHz
        pcm_16k, _ = audioop.ratecv(pcm_8k, 2, 1, TWILIO_SAMPLE_RATE, TARGET_SAMPLE_RATE, None)
        return pcm_16k

    @staticmethod
    def encode_audio_for_twilio(pcm_16k: bytes) -> str:
        """Encode linear16 16kHz audio to base64 mulaw 8kHz for Twilio."""
        # Downsample from 16kHz to 8kHz
        pcm_8k, _ = audioop.ratecv(pcm_16k, 2, 1, TARGET_SAMPLE_RATE, TWILIO_SAMPLE_RATE, None)
        # Convert to mulaw
        mulaw_bytes = audioop.lin2ulaw(pcm_8k, 2)
        return base64.b64encode(mulaw_bytes).decode("ascii")

    def validate_twilio_signature(self, url: str, params: dict[str, str], signature: str) -> bool:
        """Validate that a request came from Twilio."""
        from twilio.request_validator import RequestValidator

        validator = RequestValidator(self.auth_token)
        return validator.validate(url, params, signature)
