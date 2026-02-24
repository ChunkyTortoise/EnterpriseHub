"""AI disclosure stage — discloses only when explicitly asked."""

import logging

from ghl_real_estate_ai.services.jorge.response_pipeline.base import ResponseProcessorStage
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)

logger = logging.getLogger(__name__)


class AIDisclosureProcessor(ResponseProcessorStage):
    """Appends SB 243 AI disclosure footer, respecting detected language.

    On the first message of a conversation (context.is_first_message),
    also prepends a proactive AI identity disclosure per SB 1001.
    """

    @property
    def name(self) -> str:
        return "ai_disclosure"

    # SB 243 footer (required on every outbound AI message).
    SB243_FOOTER = "\n[AI-assisted message]"

    # SB 1001 first-message prefix — identify as AI before any sales content.
    SB1001_PREFIX = "This is Jorge's AI assistant. "

    # Spanish translations for language-aware disclosure.
    SB243_FOOTER_ES = "\n[Mensaje asistido por IA]"
    SB1001_PREFIX_ES = "Este es el asistente de IA de Jorge. "

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        """Append SB 243 footer to every response; prepend SB 1001 prefix on first message."""
        lang = getattr(context, "detected_language", "en") or "en"
        footer = self.SB243_FOOTER_ES if lang.startswith("es") else self.SB243_FOOTER
        prefix = self.SB1001_PREFIX_ES if lang.startswith("es") else self.SB1001_PREFIX

        msg = response.message

        # SB 1001: prepend AI identity on first turn (if not already present).
        if context.is_first_message and "AI assistant" not in msg and "asistente de IA" not in msg:
            msg = prefix + msg

        # SB 243: append footer if not already present (guard against double-append).
        if "[AI-assisted message]" not in msg and "[Mensaje asistido por IA]" not in msg:
            msg = msg + footer

        response.message = msg
        response.action = ProcessingAction.MODIFY
        return response
