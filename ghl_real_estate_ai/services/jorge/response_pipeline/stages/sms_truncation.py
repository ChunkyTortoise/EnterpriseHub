"""SMS-safe truncation stage.

Truncates messages at sentence boundaries to stay within SMS character limits.
"""

import logging

from ghl_real_estate_ai.services.jorge.response_pipeline.base import ResponseProcessorStage
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)

logger = logging.getLogger(__name__)

SMS_MAX_CHARS = 320
SENTENCE_SEPARATORS = (". ", "! ", "? ")


class SMSTruncationProcessor(ResponseProcessorStage):
    """Truncates messages exceeding SMS_MAX_CHARS at sentence boundaries."""

    def __init__(self, max_chars: int = SMS_MAX_CHARS):
        self._max_chars = max_chars

    @property
    def name(self) -> str:
        return "sms_truncation"

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        # Only truncate for SMS channel
        if context.channel != "sms":
            return response

        if len(response.message) <= self._max_chars:
            return response

        truncated = response.message[: self._max_chars]
        for sep in SENTENCE_SEPARATORS:
            idx = truncated.rfind(sep)
            if idx > self._max_chars // 2:
                truncated = truncated[: idx + 1]
                break
        response.message = truncated.rstrip()

        if response.action == ProcessingAction.PASS:
            response.action = ProcessingAction.MODIFY

        logger.debug(
            "Truncated message for %s from %d to %d chars",
            context.contact_id,
            len(response.original_message),
            len(response.message),
        )
        return response
