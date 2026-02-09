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
        "cancel",
        "parar",  # Spanish
        "cancelar",  # Spanish
        "no más",  # Spanish
    }
)

OPT_OUT_RESPONSE_EN = (
    "You've been unsubscribed from automated messages. "
    "If you'd like to reconnect, just text us anytime."
)

OPT_OUT_RESPONSE_ES = (
    "Ha sido dado de baja de los mensajes automáticos. "
    "Si desea reconectarse, envíenos un mensaje en cualquier momento."
)


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
            response.actions.append({"type": "add_tag", "tag": "AI-Off"})
            response.actions.append({"type": "add_tag", "tag": "TCPA-Opt-Out"})
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
