"""Factory functions for creating pipeline instances."""

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
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.response_translation import (
    ResponseTranslationProcessor,
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
        1. LanguageMirrorProcessor       — detect language, set context
        2. TCPAOptOutProcessor           — can short-circuit on "stop"/"unsubscribe"
        3. ConversationRepairProcessor   — breakdown detection, graduated repair ladder
        4. ComplianceCheckProcessor      — FHA/RESPA enforcement
        5. AIDisclosureProcessor         — no-op; disclosure only when sincerely asked
        6. ResponseTranslationProcessor  — mirror user language (es, …)
        7. SMSTruncationProcessor        — 320 char limit for SMS

    AI disclosure policy: Jorge does NOT proactively identify as AI.
    Disclosure happens only when a lead explicitly asks "are you a bot?" / "are you AI?"
    Per SB 1001 (CA) — no proactive footer required or added.
    """
    return ResponsePostProcessor(stages=[
        LanguageMirrorProcessor(),
        # Defense-in-depth: primary opt-out check is in webhook.py (lines 408-437)
        TCPAOptOutProcessor(),
        ConversationRepairProcessor(),
        ComplianceCheckProcessor(),
        # AIDisclosureProcessor is a no-op stub — kept for future optional use
        AIDisclosureProcessor(),
        # F-13 FIX: Translate fixed qualification / scheduling / handoff messages
        # to match the user's detected language.
        ResponseTranslationProcessor(),
        SMSTruncationProcessor(),
    ])


_pipeline: ResponsePostProcessor | None = None


def get_response_pipeline() -> ResponsePostProcessor:
    """Singleton accessor for the default pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = create_default_pipeline()
    return _pipeline
