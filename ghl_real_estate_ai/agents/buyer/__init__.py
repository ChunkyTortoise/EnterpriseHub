"""
Jorge Buyer Bot - Modular Implementation

This package contains the decomposed buyer bot modules.
Import JorgeBuyerBot from the parent module: `from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot`
"""

# Export key components for advanced usage
# NOTE: JorgeBuyerBot should be imported from ghl_real_estate_ai.agents.jorge_buyer_bot
# to avoid circular imports
from ghl_real_estate_ai.agents.buyer.constants import COMPLIANCE_SEVERITY_MAP, OPT_OUT_PHRASES
from ghl_real_estate_ai.agents.buyer.exceptions import (
    ERROR_ID_BUYER_QUALIFICATION_FAILED,
    ERROR_ID_COMPLIANCE_VIOLATION,
    ERROR_ID_FINANCIAL_ASSESSMENT_FAILED,
    ERROR_ID_SYSTEM_FAILURE,
    BuyerIntentAnalysisError,
    BuyerQualificationError,
    ClaudeAPIError,
    ComplianceValidationError,
    FinancialAssessmentError,
    NetworkError,
)
from ghl_real_estate_ai.agents.buyer.retry_utils import RetryConfig, async_retry_with_backoff

__all__ = [
    # NOTE: Import JorgeBuyerBot from ghl_real_estate_ai.agents.jorge_buyer_bot
    "BuyerQualificationError",
    "BuyerIntentAnalysisError",
    "FinancialAssessmentError",
    "ClaudeAPIError",
    "NetworkError",
    "ComplianceValidationError",
    "ERROR_ID_BUYER_QUALIFICATION_FAILED",
    "ERROR_ID_FINANCIAL_ASSESSMENT_FAILED",
    "ERROR_ID_COMPLIANCE_VIOLATION",
    "ERROR_ID_SYSTEM_FAILURE",
    "RetryConfig",
    "async_retry_with_backoff",
    "COMPLIANCE_SEVERITY_MAP",
    "OPT_OUT_PHRASES",
]
