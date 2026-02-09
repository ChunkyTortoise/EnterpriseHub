"""Language detection pipeline stage.

Detects the language of the user's message and sets context for downstream
stages (AI disclosure footer language, TCPA opt-out response language).
This stage does **not** modify the response message itself.
"""

import logging
from dataclasses import asdict

from ghl_real_estate_ai.services.jorge.response_pipeline.base import (
    ResponseProcessorStage,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingContext,
)
from ghl_real_estate_ai.services.language_detection import (
    get_language_detection_service,
)

logger = logging.getLogger(__name__)


class LanguageMirrorProcessor(ResponseProcessorStage):
    """Detects user message language and sets context for downstream stages.

    This stage enriches the :class:`ProcessingContext` with:
    - ``detected_language`` — ISO 639-1 code (e.g. ``"en"``, ``"es"``)
    - ``metadata["language_detection"]`` — full detection result dict

    It never modifies the response message.
    """

    @property
    def name(self) -> str:
        return "language_mirror"

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        service = get_language_detection_service()
        detection = service.detect(
            context.user_message,
            contact_id=context.contact_id or None,
        )

        context.detected_language = detection.language
        context.metadata["language_detection"] = asdict(detection)

        logger.debug(
            "Language detected for contact %s: %s (%.2f)",
            context.contact_id,
            detection.language,
            detection.confidence,
        )

        return response
