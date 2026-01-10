"""
Domain-specific exceptions for GHL Real Estate AI services.

This module defines a hierarchy of exceptions that replace the generic
Exception handling found throughout the codebase. Each domain has specific
exception types to enable proper error handling and recovery strategies.
"""

from typing import Optional, Dict, Any


class GHLRealEstateError(Exception):
    """Base exception for all GHL Real Estate AI services."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause


# === Configuration and Setup Errors ===

class ConfigurationError(GHLRealEstateError):
    """Raised when configuration is invalid or missing."""
    pass


class APIKeyError(ConfigurationError):
    """Raised when API keys are missing or invalid."""
    pass


class DatabaseConnectionError(GHLRealEstateError):
    """Raised when database connection fails."""
    pass


# === Property Matching Errors ===

class PropertyMatchingError(GHLRealEstateError):
    """Base class for property matching related errors."""
    pass


class PropertyNotFoundError(PropertyMatchingError):
    """Raised when a property cannot be found."""
    pass


class FeatureExtractionError(PropertyMatchingError):
    """Raised when property feature extraction fails."""
    pass


class MatchingModelError(PropertyMatchingError):
    """Raised when ML property matching model fails."""
    pass


# === Lead Scoring Errors ===

class LeadScoringError(GHLRealEstateError):
    """Base class for lead scoring related errors."""
    pass


class LeadNotFoundError(LeadScoringError):
    """Raised when a lead cannot be found."""
    pass


class BehavioralDataError(LeadScoringError):
    """Raised when behavioral data is insufficient or invalid."""
    pass


class ScoringModelError(LeadScoringError):
    """Raised when lead scoring model fails."""
    pass


class RealtimeScoringError(LeadScoringError):
    """Raised when real-time scoring fails."""
    pass


# === Churn Prediction Errors ===

class ChurnPredictionError(GHLRealEstateError):
    """Base class for churn prediction related errors."""
    pass


class ChurnModelError(ChurnPredictionError):
    """Raised when churn prediction model fails."""
    pass


class InterventionError(ChurnPredictionError):
    """Raised when churn intervention fails."""
    pass


class RiskAssessmentError(ChurnPredictionError):
    """Raised when risk assessment calculation fails."""
    pass


# === GHL Integration Errors ===

class GHLIntegrationError(GHLRealEstateError):
    """Base class for GoHighLevel integration errors."""
    pass


class GHLAPIError(GHLIntegrationError):
    """Raised when GHL API calls fail."""
    pass


class WebhookProcessingError(GHLIntegrationError):
    """Raised when webhook processing fails."""
    pass


class ContactSyncError(GHLIntegrationError):
    """Raised when contact synchronization fails."""
    pass


# === Memory and Cache Errors ===

class MemoryServiceError(GHLRealEstateError):
    """Base class for memory service related errors."""
    pass


class CacheError(MemoryServiceError):
    """Raised when cache operations fail."""
    pass


class ConversationError(MemoryServiceError):
    """Raised when conversation processing fails."""
    pass


# === Analytics and Workflow Errors ===

class AnalyticsError(GHLRealEstateError):
    """Base class for analytics related errors."""
    pass


class WorkflowError(GHLRealEstateError):
    """Base class for workflow automation errors."""
    pass


class AgentSystemError(GHLRealEstateError):
    """Base class for agent system errors."""
    pass


# === ML Model Errors ===

class MLModelError(GHLRealEstateError):
    """Base class for ML model related errors."""
    pass


class ModelLoadingError(MLModelError):
    """Raised when ML model loading fails."""
    pass


class PredictionError(MLModelError):
    """Raised when ML model prediction fails."""
    pass


class ModelTrainingError(MLModelError):
    """Raised when ML model training fails."""
    pass


class FeatureEngineeringError(MLModelError):
    """Raised when feature engineering fails."""
    pass


# === Validation Errors ===

class ValidationError(GHLRealEstateError):
    """Raised when input validation fails."""
    pass


class SchemaValidationError(ValidationError):
    """Raised when data doesn't match expected schema."""
    pass


class BusinessRuleValidationError(ValidationError):
    """Raised when business rule validation fails."""
    pass


# === Rate Limiting and Performance Errors ===

class RateLimitError(GHLRealEstateError):
    """Raised when API rate limits are exceeded."""
    pass


class TimeoutError(GHLRealEstateError):
    """Raised when operations timeout."""
    pass


class PerformanceError(GHLRealEstateError):
    """Raised when performance thresholds are exceeded."""
    pass


# === Helper Functions ===

def wrap_exception(exc: Exception, context: str, details: Optional[Dict[str, Any]] = None) -> GHLRealEstateError:
    """
    Wrap a generic exception in a domain-specific exception.

    Args:
        exc: The original exception
        context: Context where the exception occurred
        details: Additional details about the error

    Returns:
        Domain-specific exception wrapping the original
    """
    message = f"{context}: {str(exc)}"

    # Map common exception types to domain exceptions
    if isinstance(exc, (ConnectionError, ConnectionRefusedError)):
        return DatabaseConnectionError(message, details, exc)
    elif isinstance(exc, FileNotFoundError):
        return ConfigurationError(message, details, exc)
    elif isinstance(exc, (ValueError, TypeError)) and "model" in context.lower():
        return MLModelError(message, details, exc)
    elif isinstance(exc, (ValueError, TypeError)) and any(term in context.lower() for term in ["lead", "score"]):
        return LeadScoringError(message, details, exc)
    elif isinstance(exc, (ValueError, TypeError)) and any(term in context.lower() for term in ["property", "match"]):
        return PropertyMatchingError(message, details, exc)
    else:
        return GHLRealEstateError(message, details, exc)


def is_recoverable_error(exc: Exception) -> bool:
    """
    Determine if an error is recoverable and should trigger retry logic.

    Args:
        exc: The exception to check

    Returns:
        True if the error is recoverable, False otherwise
    """
    recoverable_types = (
        DatabaseConnectionError,
        GHLAPIError,
        CacheError,
        RateLimitError,
        TimeoutError,
    )

    return isinstance(exc, recoverable_types)


def get_fallback_strategy(exc: Exception) -> str:
    """
    Get the recommended fallback strategy for an exception.

    Args:
        exc: The exception to get strategy for

    Returns:
        String describing the fallback strategy
    """
    if isinstance(exc, (CacheError, DatabaseConnectionError)):
        return "use_in_memory_fallback"
    elif isinstance(exc, GHLAPIError):
        return "use_cached_data"
    elif isinstance(exc, (MLModelError, ScoringModelError)):
        return "use_rule_based_fallback"
    elif isinstance(exc, RateLimitError):
        return "retry_with_backoff"
    else:
        return "graceful_degradation"