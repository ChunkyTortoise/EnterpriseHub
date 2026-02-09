"""Compliance check stage — wires existing ComplianceMiddleware (FHA/RESPA)."""

import logging

from ghl_real_estate_ai.services.jorge.response_pipeline.base import ResponseProcessorStage
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ComplianceFlag,
    ComplianceFlagSeverity,
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)

logger = logging.getLogger(__name__)

# Safe fallback messages by bot mode
_SAFE_FALLBACKS = {
    "seller": "Let's stick to the facts about your property. What price are you looking to get?",
    "buyer": "I'd love to help you find your next home. What's most important to you in a property?",
    "lead": "Thanks for reaching out! How can I help you today?",
    "general": "I'd love to help you with your real estate needs. What can I assist you with today?",
}


class ComplianceCheckProcessor(ResponseProcessorStage):
    """Runs ComplianceMiddleware.enforce() on the outbound message.

    If the message is BLOCKED, replaces it with a safe fallback and
    tags the contact with Compliance-Alert.
    """

    @property
    def name(self) -> str:
        return "compliance_check"

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        try:
            from ghl_real_estate_ai.services.compliance_middleware import (
                get_compliance_middleware,
            )

            middleware = get_compliance_middleware()
        except ImportError:
            logger.debug("ComplianceMiddleware not available; skipping stage")
            return response

        result = await middleware.enforce(
            message=response.message,
            contact_id=context.contact_id,
            mode=context.bot_mode,
        )

        from ghl_real_estate_ai.services.compliance_guard import ComplianceStatus

        if result.status == ComplianceStatus.BLOCKED:
            response.message = _SAFE_FALLBACKS.get(
                context.bot_mode, _SAFE_FALLBACKS["general"]
            )
            response.action = ProcessingAction.BLOCK
            response.actions.append({"type": "add_tag", "tag": "Compliance-Alert"})
            response.compliance_flags.append(
                ComplianceFlag(
                    stage=self.name,
                    category="fha_respa",
                    severity=ComplianceFlagSeverity.CRITICAL,
                    description=result.reason,
                    metadata={
                        "risk_score": result.risk_score,
                        "violations": [
                            {
                                "category": v.category.value,
                                "severity": v.severity.value,
                                "matched_text": v.matched_text,
                            }
                            for v in result.violations
                        ],
                    },
                )
            )
            logger.warning(
                "Compliance BLOCKED message for %s: %s",
                context.contact_id,
                result.reason,
            )
        elif result.status == ComplianceStatus.FLAGGED:
            response.compliance_flags.append(
                ComplianceFlag(
                    stage=self.name,
                    category="fha_respa",
                    severity=ComplianceFlagSeverity.WARNING,
                    description=result.reason,
                    metadata={"risk_score": result.risk_score},
                )
            )

        if result.respa_disclosures_needed:
            response.compliance_flags.append(
                ComplianceFlag(
                    stage=self.name,
                    category="respa_disclosure",
                    severity=ComplianceFlagSeverity.WARNING,
                    description=f"RESPA disclosures needed: {', '.join(result.respa_disclosures_needed)}",
                )
            )

        return response
