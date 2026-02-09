"""Response post-processing pipeline orchestrator."""

import logging
from typing import List

from ghl_real_estate_ai.services.jorge.response_pipeline.base import ResponseProcessorStage
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)

logger = logging.getLogger(__name__)


class ResponsePostProcessor:
    """Chains multiple ResponseProcessorStage instances in order.

    Stages run sequentially. If any stage sets action to SHORT_CIRCUIT,
    remaining stages are skipped.
    """

    def __init__(self, stages: List[ResponseProcessorStage] | None = None):
        self._stages: List[ResponseProcessorStage] = stages or []

    def add_stage(self, stage: ResponseProcessorStage) -> "ResponsePostProcessor":
        """Append a stage to the pipeline. Returns self for chaining."""
        self._stages.append(stage)
        return self

    @property
    def stages(self) -> List[ResponseProcessorStage]:
        return list(self._stages)

    async def process(
        self,
        message: str,
        context: ProcessingContext | None = None,
    ) -> ProcessedResponse:
        """Run the message through all pipeline stages.

        Args:
            message: Raw bot response text.
            context: Processing context (created with defaults if None).

        Returns:
            ProcessedResponse with final message and metadata.
        """
        if context is None:
            context = ProcessingContext()

        response = ProcessedResponse(
            message=message,
            original_message=message,
            context=context,
        )

        for stage in self._stages:
            try:
                response = await stage.process(response, context)
                response.stage_log.append(f"{stage.name}:{response.action.value}")

                if response.action == ProcessingAction.SHORT_CIRCUIT:
                    logger.info(
                        "Pipeline short-circuited at stage '%s' for contact %s",
                        stage.name,
                        context.contact_id,
                    )
                    break
            except Exception:
                logger.exception(
                    "Stage '%s' raised an exception for contact %s; skipping",
                    stage.name,
                    context.contact_id,
                )
                response.stage_log.append(f"{stage.name}:error")

        return response
