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
    """No-op disclosure stage.

    SB 1001 (CA) only requires disclosure when sincerely asked — not proactively.
    Bot persona is Jorge (human agent). Disclosure on every message breaks the persona.
    Bot will acknowledge being AI only when a lead explicitly asks.
    """

    @property
    def name(self) -> str:
        return "ai_disclosure"

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        """Pass through unchanged — no footer injected."""
        return response
