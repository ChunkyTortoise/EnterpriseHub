"""SB 243 AI disclosure stage.

California SB 243 (effective Jan 2026) requires AI-generated communications
to disclose they are AI-assisted. This stage appends a language-aware footer.
"""

import logging
import re

from ghl_real_estate_ai.services.jorge.response_pipeline.base import ResponseProcessorStage
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)

logger = logging.getLogger(__name__)

DISCLOSURE_EN = "\n[AI-assisted message]"
DISCLOSURE_ES = "\n[Mensaje asistido por IA]"

# SB 1001 proactive disclosure — must appear in first message of each conversation
PROACTIVE_DISCLOSURE_EN = "Hey! I'm Jorge's AI assistant. "
PROACTIVE_DISCLOSURE_ES = "¡Hola! Soy el asistente de IA de Jorge. "


class AIDisclosureProcessor(ResponseProcessorStage):
    """Appends SB 243 AI disclosure footer, respecting detected language.

    On the first message of a conversation (context.is_first_message),
    also prepends a proactive AI identity disclosure per SB 1001.
    """

    @property
    def name(self) -> str:
        return "ai_disclosure"

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        # Don't add disclosure to opt-out acks or blocked messages
        if response.action in (ProcessingAction.SHORT_CIRCUIT, ProcessingAction.BLOCK):
            return response

        is_spanish = context.detected_language == "es"
        disclosure = DISCLOSURE_ES if is_spanish else DISCLOSURE_EN

        # SB 1001: Proactive disclosure on first message
        if context.is_first_message:
            proactive = PROACTIVE_DISCLOSURE_ES if is_spanish else PROACTIVE_DISCLOSURE_EN
            if not response.message.startswith(proactive):
                # Strip leading "Hey[!,]? " so we don't get "Hey! I'm Jorge's AI. Hey! ..."
                cleaned = re.sub(r'^(hey[!,]?\s+)', '', response.message, flags=re.IGNORECASE)
                response.message = proactive + cleaned
                if response.action == ProcessingAction.PASS:
                    response.action = ProcessingAction.MODIFY

        # SB 243: Footer on every message
        if disclosure.strip() not in response.message:
            response.message = response.message.rstrip() + disclosure
            if response.action == ProcessingAction.PASS:
                response.action = ProcessingAction.MODIFY

        return response
