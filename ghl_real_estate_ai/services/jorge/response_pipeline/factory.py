"""Factory functions for creating pipeline instances."""

import os

from ghl_real_estate_ai.services.jorge.response_pipeline.pipeline import ResponsePostProcessor
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.ai_disclosure import (
    AIDisclosureProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.compliance_check import (
    ComplianceCheckProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.conversation_repair import (
    ConversationRepairProcessor,
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
        1. LanguageMirrorProcessor  — detect language, set context
        2. TCPAOptOutProcessor      — can short-circuit on "stop"/"unsubscribe"
        3. ConversationRepairProcessor (optional; env-gated)
        4. ComplianceCheckProcessor  — FHA/RESPA enforcement
        5. AIDisclosureProcessor     — SB 243 AI disclosure footer
        6. SMSTruncationProcessor    — 320 char limit for SMS
    """
    repair_enabled = os.getenv("CONVERSATION_REPAIR_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    disclosure_enabled = os.getenv("AI_DISCLOSURE_ENABLED", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    stages = [
        LanguageMirrorProcessor(),
        # Defense-in-depth: primary opt-out check is in webhook.py (lines 408-437)
        TCPAOptOutProcessor(),
    ]
    if repair_enabled:
        stages.append(ConversationRepairProcessor())
    stages.append(ComplianceCheckProcessor())
    if disclosure_enabled:
        stages.append(AIDisclosureProcessor())
    stages.append(SMSTruncationProcessor())

    return ResponsePostProcessor(stages=stages)


_pipeline: ResponsePostProcessor | None = None


def get_response_pipeline() -> ResponsePostProcessor:
    """Singleton accessor for the default pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = create_default_pipeline()
    return _pipeline
