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

    Per Jorge's product requirement: bot NEVER proactively identifies as AI.
    It must only disclose when explicitly asked (SB 1001 compliant — no denial).
    SB 243 footer is appended on every message for legal compliance.
    """

    @property
    def name(self) -> str:
        return "ai_disclosure"

    # SB 243 footer (required on every outbound AI message).
    SB243_FOOTER = "\n[AI-assisted message]"

    # Spanish translation.
    SB243_FOOTER_ES = "\n[Mensaje asistido por IA]"

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        """Append SB 243 footer to every response. Never proactively disclose AI identity."""
        lang = getattr(context, "detected_language", "en") or "en"
        footer = self.SB243_FOOTER_ES if lang.startswith("es") else self.SB243_FOOTER

        msg = response.message

        # SB 243: append footer if not already present (guard against double-append).
        if "[AI-assisted message]" not in msg and "[Mensaje asistido por IA]" not in msg:
            msg = msg + footer

        response.message = msg
        response.action = ProcessingAction.MODIFY
        return response
