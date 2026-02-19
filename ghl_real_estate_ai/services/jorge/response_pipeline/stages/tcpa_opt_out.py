"""TCPA opt-out detection stage.

Detects opt-out phrases in the user message and short-circuits the pipeline
with a compliant unsubscribe acknowledgement.
"""

import logging
from typing import FrozenSet

from ghl_real_estate_ai.services.jorge.response_pipeline.base import ResponseProcessorStage
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ComplianceFlag,
    ComplianceFlagSeverity,
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)

logger = logging.getLogger(__name__)

OPT_OUT_PHRASES: FrozenSet[str] = frozenset(
    {
        "stop",
        "unsubscribe",
        "not interested",
        "opt out",
        "remove me",
        "don't contact me",
        "dont contact me",
        "no more messages",
        "cancel",
        "parar",  # Spanish
        "cancelar",  # Spanish
        "no más",  # Spanish
    }
)

# Per Jorge spec section 2.6 — exact wording required
OPT_OUT_RESPONSE_EN = "No problem at all, reach out whenever you're ready"

OPT_OUT_RESPONSE_ES = "Sin problema, escríbenos cuando estés listo"


class TCPAOptOutProcessor(ResponseProcessorStage):
    """Detects TCPA opt-out keywords in the user message and short-circuits."""

    @property
    def name(self) -> str:
        return "tcpa_opt_out"

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        user_lower = context.user_message.lower().strip()

        if any(phrase in user_lower for phrase in OPT_OUT_PHRASES):
            context.is_opt_out = True
            lang = context.detected_language

            response.message = OPT_OUT_RESPONSE_ES if lang == "es" else OPT_OUT_RESPONSE_EN
            response.action = ProcessingAction.SHORT_CIRCUIT
            response.actions.append({"type": "add_tag", "tag": "TCPA-Opt-Out"})
            response.actions.append({"type": "add_tag", "tag": "AI-Off"})
            response.compliance_flags.append(
                ComplianceFlag(
                    stage=self.name,
                    category="tcpa",
                    severity=ComplianceFlagSeverity.INFO,
                    description=f"Opt-out detected for contact {context.contact_id}",
                )
            )
            logger.info("TCPA opt-out detected for contact %s", context.contact_id)

        return response
