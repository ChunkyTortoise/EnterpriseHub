"""
Custom exceptions for buyer qualification and error handling.
"""


class BuyerQualificationError(Exception):
    """Base exception for buyer qualification failures"""

    def __init__(self, message: str, recoverable: bool = False, escalate: bool = False):
        super().__init__(message)
        self.recoverable = recoverable
        self.escalate = escalate


class BuyerIntentAnalysisError(BuyerQualificationError):
    """Raised when buyer intent analysis fails"""

    pass


class FinancialAssessmentError(BuyerQualificationError):
    """Raised when financial readiness assessment fails"""

    pass


class ClaudeAPIError(BuyerQualificationError):
    """Raised when Claude AI service fails"""

    pass


class NetworkError(BuyerQualificationError):
    """Raised when network connectivity issues occur"""

    pass


class ComplianceValidationError(BuyerQualificationError):
    """Raised when compliance validation fails (Fair Housing, DRE)"""

    pass


# Error IDs for monitoring and alerting
ERROR_ID_BUYER_QUALIFICATION_FAILED = "BUYER_QUALIFICATION_FAILED"
ERROR_ID_FINANCIAL_ASSESSMENT_FAILED = "FINANCIAL_ASSESSMENT_FAILED"
ERROR_ID_COMPLIANCE_VIOLATION = "COMPLIANCE_VIOLATION"
ERROR_ID_SYSTEM_FAILURE = "SYSTEM_FAILURE"
