"""Abstract base class for pipeline processing stages."""

from abc import ABC, abstractmethod

from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingContext,
)


class ResponseProcessorStage(ABC):
    """Base class for all pipeline processing stages.

    Each stage receives a ProcessedResponse, may modify it, and returns it.
    Stages can short-circuit the pipeline by setting action to SHORT_CIRCUIT.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable stage name for logging."""

    @abstractmethod
    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        """Process the response and return (possibly modified) result.

        Args:
            response: Current pipeline response state.
            context: Shared processing context.

        Returns:
            Updated ProcessedResponse.
        """
