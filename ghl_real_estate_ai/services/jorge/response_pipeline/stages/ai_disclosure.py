"""SB 243 AI disclosure stage.

California SB 243 (effective Jan 2026) requires AI-generated communications
to disclose they are AI-assisted. This stage appends a language-aware footer.
"""

import logging

from ghl_real_estate_ai.services.jorge.response_pipeline.base import ResponseProcessorStage
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)

logger = logging.getLogger(__name__)

DISCLOSURE_EN = "\n[AI-assisted message]"
DISCLOSURE_ES = "\n[Mensaje asistido por IA]"


class AIDisclosureProcessor(ResponseProcessorStage):
    """Appends SB 243 AI disclosure footer, respecting detected language."""

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

        disclosure = DISCLOSURE_ES if context.detected_language == "es" else DISCLOSURE_EN

        if disclosure.strip() not in response.message:
            response.message = response.message.rstrip() + disclosure
            if response.action == ProcessingAction.PASS:
                response.action = ProcessingAction.MODIFY

        return response
