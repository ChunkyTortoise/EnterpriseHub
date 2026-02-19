"""Factory functions for creating pipeline instances."""

from ghl_real_estate_ai.services.jorge.response_pipeline.pipeline import ResponsePostProcessor
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.compliance_check import (
    ComplianceCheckProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror import (
    LanguageMirrorProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.sms_truncation import (
    SMSTruncationProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.tcpa_opt_out import (
    TCPAOptOutProcessor,
)


def create_default_pipeline() -> ResponsePostProcessor:
    """Create the standard pipeline with all stages in correct order.

    Order:
        1. LanguageMirrorProcessor — detect language, set context
        2. TCPAOptOutProcessor     — can short-circuit on "stop"/"unsubscribe"
        3. ComplianceCheckProcessor — FHA/RESPA enforcement
        4. SMSTruncationProcessor   — 160 char limit for SMS (per Jorge spec)

    Note: AIDisclosureProcessor (SB 243) removed — Jorge's spec requires
    responses that sound "100% human". If SB 243 compliance is needed later,
    it should be discussed with the client first.
    """
    return ResponsePostProcessor(
        stages=[
            LanguageMirrorProcessor(),
            # Defense-in-depth: primary opt-out check is in webhook.py (lines 408-437)
            TCPAOptOutProcessor(),
            ComplianceCheckProcessor(),
            SMSTruncationProcessor(),
        ]
    )


_pipeline: ResponsePostProcessor | None = None


def get_response_pipeline() -> ResponsePostProcessor:
    """Singleton accessor for the default pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = create_default_pipeline()
    return _pipeline
