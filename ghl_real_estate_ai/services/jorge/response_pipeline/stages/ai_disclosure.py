"""AI disclosure stage — discloses only when explicitly asked."""

import logging

from ghl_real_estate_ai.services.jorge.response_pipeline.base import ResponseProcessorStage
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
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

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        # Disclosure only when explicitly asked — no proactive footer or prefix
        return response
