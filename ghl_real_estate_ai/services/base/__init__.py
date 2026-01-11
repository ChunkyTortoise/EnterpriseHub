"""
Base services module for GHL Real Estate AI.

This module provides foundational classes, protocols, and utilities that all
service implementations should use to ensure consistency, error handling,
and maintainability across the codebase.

Key Components:
- BaseService: Abstract base class with common functionality
- Service Protocols: Interface definitions for dependency injection
- Exception Hierarchy: Domain-specific exceptions
- ServiceMetrics: Performance monitoring and metrics tracking
"""

from .base_service import BaseService, ServiceMetrics
from .protocols import (
    # Data Models
    RiskLevel,
    PropertyType,
    LeadProfile,
    LeadFeatures,
    LeadScore,
    Property,
    PropertyMatch,
    ChurnPrediction,

    # Service Protocols
    PropertyMatcher,
    LeadScorer,
    ChurnPredictor,
    MemoryService,
    CacheManager,
    ConfigManager,
    HealthCheck,
    ServiceRegistry,
    DatabaseConnection,
)
from .exceptions import (
    # Base Exceptions
    GHLRealEstateError,
    ConfigurationError,
    APIKeyError,
    DatabaseConnectionError,

    # Domain-Specific Exceptions
    PropertyMatchingError,
    PropertyNotFoundError,
    FeatureExtractionError,
    MatchingModelError,

    LeadScoringError,
    LeadNotFoundError,
    BehavioralDataError,
    ScoringModelError,
    RealtimeScoringError,

    ChurnPredictionError,
    ChurnModelError,
    InterventionError,
    RiskAssessmentError,

    GHLIntegrationError,
    GHLAPIError,
    WebhookProcessingError,
    ContactSyncError,

    MemoryServiceError,
    CacheError,
    ConversationError,

    AnalyticsError,
    WorkflowError,
    AgentSystemError,

    MLModelError,
    ModelLoadingError,
    PredictionError,
    ModelTrainingError,
    FeatureEngineeringError,

    ValidationError,
    SchemaValidationError,
    BusinessRuleValidationError,

    RateLimitError,
    TimeoutError,
    PerformanceError,

    # Utility Functions
    wrap_exception,
    is_recoverable_error,
    get_fallback_strategy,
)

__all__ = [
    # Base Classes
    "BaseService",
    "ServiceMetrics",

    # Data Models
    "RiskLevel",
    "PropertyType",
    "LeadProfile",
    "LeadFeatures",
    "LeadScore",
    "Property",
    "PropertyMatch",
    "ChurnPrediction",

    # Service Protocols
    "PropertyMatcher",
    "LeadScorer",
    "ChurnPredictor",
    "MemoryService",
    "CacheManager",
    "ConfigManager",
    "HealthCheck",
    "ServiceRegistry",
    "DatabaseConnection",

    # Exception Classes
    "GHLRealEstateError",
    "ConfigurationError",
    "APIKeyError",
    "DatabaseConnectionError",
    "PropertyMatchingError",
    "PropertyNotFoundError",
    "FeatureExtractionError",
    "MatchingModelError",
    "LeadScoringError",
    "LeadNotFoundError",
    "BehavioralDataError",
    "ScoringModelError",
    "RealtimeScoringError",
    "ChurnPredictionError",
    "ChurnModelError",
    "InterventionError",
    "RiskAssessmentError",
    "GHLIntegrationError",
    "GHLAPIError",
    "WebhookProcessingError",
    "ContactSyncError",
    "MemoryServiceError",
    "CacheError",
    "ConversationError",
    "AnalyticsError",
    "WorkflowError",
    "AgentSystemError",
    "MLModelError",
    "ModelLoadingError",
    "PredictionError",
    "ModelTrainingError",
    "FeatureEngineeringError",
    "ValidationError",
    "SchemaValidationError",
    "BusinessRuleValidationError",
    "RateLimitError",
    "TimeoutError",
    "PerformanceError",

    # Utility Functions
    "wrap_exception",
    "is_recoverable_error",
    "get_fallback_strategy",
]

# Version information
__version__ = "1.0.0"
__description__ = "Base services infrastructure for GHL Real Estate AI platform"