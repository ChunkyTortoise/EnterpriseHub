"""Factory functions for creating pipeline instances."""

from ghl_real_estate_ai.services.jorge.response_pipeline.pipeline import ResponsePostProcessor
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.ai_disclosure import (
    AIDisclosureProcessor,
)
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
        4. AIDisclosureProcessor    — SB 243 footer
        5. SMSTruncationProcessor   — 320 char limit for SMS
    """
    return ResponsePostProcessor(
        stages=[
            LanguageMirrorProcessor(),
            TCPAOptOutProcessor(),
            ComplianceCheckProcessor(),
            AIDisclosureProcessor(),
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
