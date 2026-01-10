"""
Service protocols (interfaces) for GHL Real Estate AI services.

These protocols define the contracts that service implementations must follow,
enabling dependency injection, testing, and service consolidation.
"""

from typing import Protocol, List, Dict, Any, Optional, AsyncContextManager
from abc import abstractmethod
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


# === Data Models ===

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PropertyType(Enum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    COMMERCIAL = "commercial"


@dataclass
class LeadProfile:
    id: str
    name: str
    email: str
    phone: Optional[str]
    budget_min: Optional[float]
    budget_max: Optional[float]
    preferred_locations: List[str]
    property_type_preferences: List[PropertyType]
    timeline: Optional[str]
    created_at: datetime
    last_activity: Optional[datetime]
    ghl_contact_id: Optional[str] = None


@dataclass
class LeadFeatures:
    lead_id: str
    engagement_score: float
    budget_alignment: float
    location_preference_match: float
    timeline_urgency: float
    behavioral_signals: Dict[str, float]
    interaction_history: List[Dict[str, Any]]
    extracted_at: datetime


@dataclass
class LeadScore:
    lead_id: str
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    risk_level: RiskLevel
    factors: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime
    model_version: str


@dataclass
class Property:
    id: str
    address: str
    city: str
    state: str
    zip_code: str
    property_type: PropertyType
    price: float
    bedrooms: int
    bathrooms: float
    square_footage: Optional[int]
    lot_size: Optional[float]
    year_built: Optional[int]
    amenities: List[str]
    school_district: Optional[str]
    listing_agent: Optional[str]
    listing_date: datetime


@dataclass
class PropertyMatch:
    lead_id: str
    property_id: str
    match_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    match_factors: Dict[str, float]
    explanation: str
    generated_at: datetime


@dataclass
class ChurnPrediction:
    lead_id: str
    churn_probability: float  # 0.0 to 1.0
    risk_level: RiskLevel
    time_to_churn_days: Optional[int]
    risk_factors: List[Dict[str, Any]]
    protective_factors: List[Dict[str, Any]]
    intervention_recommendations: List[str]
    confidence: float
    generated_at: datetime
    model_version: str


# === Service Protocols ===

class PropertyMatcher(Protocol):
    """Protocol for property matching services."""

    @abstractmethod
    async def find_matches(self, lead_profile: LeadProfile, limit: int = 10) -> List[PropertyMatch]:
        """
        Find property matches for a lead.

        Args:
            lead_profile: Lead information and preferences
            limit: Maximum number of matches to return

        Returns:
            List of property matches sorted by match score

        Raises:
            PropertyMatchingError: When matching fails
        """
        ...

    @abstractmethod
    async def calculate_match_score(self, lead_profile: LeadProfile, property: Property) -> float:
        """
        Calculate match score between a lead and property.

        Args:
            lead_profile: Lead information and preferences
            property: Property information

        Returns:
            Match score between 0.0 and 1.0

        Raises:
            PropertyMatchingError: When score calculation fails
        """
        ...

    @abstractmethod
    async def explain_match(self, match: PropertyMatch) -> Dict[str, Any]:
        """
        Explain why a property was matched to a lead.

        Args:
            match: The property match to explain

        Returns:
            Explanation details including factor contributions

        Raises:
            PropertyMatchingError: When explanation generation fails
        """
        ...


class LeadScorer(Protocol):
    """Protocol for lead scoring services."""

    @abstractmethod
    async def score_lead(self, features: LeadFeatures) -> LeadScore:
        """
        Score a lead based on extracted features.

        Args:
            features: Extracted lead features

        Returns:
            Lead score with confidence and explanations

        Raises:
            LeadScoringError: When scoring fails
        """
        ...

    @abstractmethod
    async def extract_features(self, lead_profile: LeadProfile) -> LeadFeatures:
        """
        Extract features from lead profile for scoring.

        Args:
            lead_profile: Lead information

        Returns:
            Extracted features ready for scoring

        Raises:
            LeadScoringError: When feature extraction fails
        """
        ...

    @abstractmethod
    async def batch_score_leads(self, lead_profiles: List[LeadProfile]) -> List[LeadScore]:
        """
        Score multiple leads efficiently.

        Args:
            lead_profiles: List of lead profiles to score

        Returns:
            List of lead scores

        Raises:
            LeadScoringError: When batch scoring fails
        """
        ...


class ChurnPredictor(Protocol):
    """Protocol for churn prediction services."""

    @abstractmethod
    async def predict_churn(self, lead_id: str, features: Optional[LeadFeatures] = None) -> ChurnPrediction:
        """
        Predict churn risk for a lead.

        Args:
            lead_id: Lead identifier
            features: Pre-extracted features (optional)

        Returns:
            Churn prediction with risk assessment and recommendations

        Raises:
            ChurnPredictionError: When prediction fails
        """
        ...

    @abstractmethod
    async def explain_churn_factors(self, prediction: ChurnPrediction) -> Dict[str, Any]:
        """
        Explain the factors contributing to churn risk.

        Args:
            prediction: Churn prediction to explain

        Returns:
            Detailed explanation of risk and protective factors

        Raises:
            ChurnPredictionError: When explanation generation fails
        """
        ...

    @abstractmethod
    async def recommend_interventions(self, prediction: ChurnPrediction) -> List[str]:
        """
        Recommend interventions to reduce churn risk.

        Args:
            prediction: Churn prediction

        Returns:
            List of recommended interventions

        Raises:
            InterventionError: When intervention recommendations fail
        """
        ...


class MemoryService(Protocol):
    """Protocol for memory and conversation management services."""

    @abstractmethod
    async def store_conversation(self, tenant_id: str, contact_id: str, messages: List[Dict[str, Any]]) -> str:
        """
        Store a conversation in memory.

        Args:
            tenant_id: Tenant identifier
            contact_id: Contact identifier
            messages: List of conversation messages

        Returns:
            Conversation ID

        Raises:
            MemoryServiceError: When storage fails
        """
        ...

    @abstractmethod
    async def retrieve_context(self, tenant_id: str, contact_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Retrieve conversation context for a contact.

        Args:
            tenant_id: Tenant identifier
            contact_id: Contact identifier
            limit: Maximum number of messages to retrieve

        Returns:
            Conversation context

        Raises:
            MemoryServiceError: When retrieval fails
        """
        ...

    @abstractmethod
    async def update_memory_summary(self, conversation_id: str, summary: str) -> None:
        """
        Update the memory summary for a conversation.

        Args:
            conversation_id: Conversation identifier
            summary: New summary

        Raises:
            MemoryServiceError: When update fails
        """
        ...


class CacheManager(Protocol):
    """Protocol for cache management services."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found

        Raises:
            CacheError: When cache operation fails
        """
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Raises:
            CacheError: When cache operation fails
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if key didn't exist

        Raises:
            CacheError: When cache operation fails
        """
        ...

    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Pattern to match (supports wildcards)

        Returns:
            Number of keys deleted

        Raises:
            CacheError: When cache operation fails
        """
        ...


class ConfigManager(Protocol):
    """Protocol for configuration management services."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value

        Raises:
            ConfigurationError: When configuration access fails
        """
        ...

    @abstractmethod
    def get_weights(self) -> Dict[str, float]:
        """
        Get lead scoring weights configuration.

        Returns:
            Dictionary of scoring weights

        Raises:
            ConfigurationError: When weights access fails
        """
        ...

    @abstractmethod
    def get_thresholds(self) -> Dict[str, float]:
        """
        Get performance thresholds configuration.

        Returns:
            Dictionary of performance thresholds

        Raises:
            ConfigurationError: When thresholds access fails
        """
        ...


class HealthCheck(Protocol):
    """Protocol for service health checking."""

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """
        Check service health status.

        Returns:
            Health status information

        Raises:
            GHLRealEstateError: When health check fails
        """
        ...

    @abstractmethod
    async def check_dependencies(self) -> Dict[str, bool]:
        """
        Check health of service dependencies.

        Returns:
            Status of each dependency

        Raises:
            GHLRealEstateError: When dependency check fails
        """
        ...


# === Service Registry Protocol ===

class ServiceRegistry(Protocol):
    """Protocol for service registry/container."""

    @abstractmethod
    async def register(self, service_name: str, service_instance: Any) -> None:
        """
        Register a service instance.

        Args:
            service_name: Name of the service
            service_instance: Service instance

        Raises:
            ConfigurationError: When registration fails
        """
        ...

    @abstractmethod
    async def get(self, service_name: str) -> Any:
        """
        Get a registered service instance.

        Args:
            service_name: Name of the service

        Returns:
            Service instance

        Raises:
            ConfigurationError: When service not found
        """
        ...

    @abstractmethod
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on all registered services.

        Returns:
            Health status of all services

        Raises:
            GHLRealEstateError: When health checks fail
        """
        ...


# === Async Context Manager Protocols ===

class DatabaseConnection(Protocol):
    """Protocol for database connection management."""

    @abstractmethod
    async def __aenter__(self) -> 'DatabaseConnection':
        """Enter async context."""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        ...

    @abstractmethod
    async def execute(self, query: str, *args) -> Any:
        """Execute a database query."""
        ...

    @abstractmethod
    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch query results."""
        ...

    @abstractmethod
    async def fetchone(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch single query result."""
        ...