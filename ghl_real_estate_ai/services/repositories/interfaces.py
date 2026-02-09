"""
Repository Pattern Core Interfaces

Defines abstract base classes and data structures for the Repository Pattern.
All repository implementations must conform to these interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class SortOrder(Enum):
    """Sort order for query results"""

    ASC = "asc"
    DESC = "desc"


class QueryOperator(Enum):
    """Query filter operators"""

    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    BETWEEN = "between"
    NEAR = "near"  # Geographic proximity
    WITHIN = "within"  # Geographic boundary


@dataclass
class QueryFilter:
    """Individual query filter criterion"""

    field: str
    operator: QueryOperator
    value: Any
    field_type: Optional[str] = None  # For type-specific handling

    def __post_init__(self):
        """Validate filter configuration"""
        if self.operator in (QueryOperator.BETWEEN,) and not isinstance(self.value, (list, tuple)):
            raise ValueError(f"Operator {self.operator.value} requires list/tuple value")
        if self.operator in (QueryOperator.NEAR, QueryOperator.WITHIN) and self.field_type != "geo":
            self.field_type = "geo"


@dataclass
class PaginationConfig:
    """Pagination configuration"""

    page: int = 1
    limit: int = 50
    offset: Optional[int] = None
    total_count: Optional[int] = None

    def __post_init__(self):
        """Calculate offset if not provided"""
        if self.offset is None:
            self.offset = (self.page - 1) * self.limit

    @property
    def has_next_page(self) -> bool:
        """Check if there's a next page"""
        if self.total_count is None:
            return False
        return (self.offset + self.limit) < self.total_count

    @property
    def has_prev_page(self) -> bool:
        """Check if there's a previous page"""
        return self.page > 1


@dataclass
class PropertyQuery:
    """Comprehensive property query specification"""

    # Basic filters
    filters: List[QueryFilter] = field(default_factory=list)

    # Geographic filters
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_miles: Optional[float] = None
    zip_codes: Optional[List[str]] = None
    neighborhoods: Optional[List[str]] = None

    # Price range
    min_price: Optional[int] = None
    max_price: Optional[int] = None

    # Property features
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[float] = None
    max_bathrooms: Optional[float] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    property_types: Optional[List[str]] = None

    # Amenities and features
    required_amenities: List[str] = field(default_factory=list)
    preferred_amenities: List[str] = field(default_factory=list)

    # Market timing
    max_days_on_market: Optional[int] = None
    min_year_built: Optional[int] = None
    max_year_built: Optional[int] = None

    # Sorting and pagination
    sort_by: str = "price"
    sort_order: SortOrder = SortOrder.ASC
    pagination: PaginationConfig = field(default_factory=PaginationConfig)

    # Performance and quality
    include_metadata: bool = True
    include_images: bool = False
    include_virtual_tours: bool = False
    quality_score_threshold: Optional[float] = None

    # Semantic search (RAG)
    semantic_query: Optional[str] = None
    similarity_threshold: Optional[float] = None

    # Cache control
    use_cache: bool = True
    cache_ttl: Optional[timedelta] = None

    def add_filter(self, field: str, operator: QueryOperator, value: Any, field_type: Optional[str] = None):
        """Add a filter to the query"""
        self.filters.append(QueryFilter(field, operator, value, field_type))
        return self

    def add_price_range(self, min_price: Optional[int] = None, max_price: Optional[int] = None):
        """Add price range filter"""
        if min_price is not None:
            self.min_price = min_price
        if max_price is not None:
            self.max_price = max_price
        return self

    def add_location_filter(self, lat: float, lon: float, radius_miles: float):
        """Add geographic proximity filter"""
        self.latitude = lat
        self.longitude = lon
        self.radius_miles = radius_miles
        return self

    def add_amenity_filter(self, required: List[str] = None, preferred: List[str] = None):
        """Add amenity filters"""
        if required:
            self.required_amenities.extend(required)
        if preferred:
            self.preferred_amenities.extend(preferred)
        return self


@dataclass
class RepositoryMetadata:
    """Repository operation metadata"""

    source: str  # Repository identifier
    query_time_ms: Optional[float] = None
    cache_hit: bool = False
    total_scanned: Optional[int] = None
    indexes_used: Optional[List[str]] = None
    query_plan: Optional[str] = None
    api_calls_made: int = 0
    rate_limit_remaining: Optional[int] = None


@dataclass
class RepositoryResult:
    """Generic repository operation result container"""

    # Core result data
    data: List[Dict[str, Any]] = field(default_factory=list)
    total_count: Optional[int] = None

    # Pagination
    pagination: Optional[PaginationConfig] = None

    # Operation metadata
    metadata: Optional[RepositoryMetadata] = None

    # Status and errors
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Performance metrics
    execution_time_ms: Optional[float] = None

    @property
    def count(self) -> int:
        """Number of results returned"""
        return len(self.data)

    @property
    def has_data(self) -> bool:
        """Check if result contains data"""
        return len(self.data) > 0

    @property
    def has_errors(self) -> bool:
        """Check if result contains errors"""
        return len(self.errors) > 0

    def add_error(self, error: str):
        """Add an error to the result"""
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str):
        """Add a warning to the result"""
        self.warnings.append(warning)


class RepositoryError(Exception):
    """Base exception for repository operations"""

    def __init__(self, message: str, repository_type: str = None, original_error: Exception = None):
        super().__init__(message)
        self.repository_type = repository_type
        self.original_error = original_error


class IPropertyQueryBuilder(ABC):
    """Interface for building property queries"""

    @abstractmethod
    def reset(self) -> "IPropertyQueryBuilder":
        """Reset query builder to empty state"""
        pass

    @abstractmethod
    def filter_by_price(self, min_price: int = None, max_price: int = None) -> "IPropertyQueryBuilder":
        """Add price range filter"""
        pass

    @abstractmethod
    def filter_by_location(
        self, location: str = None, lat: float = None, lon: float = None, radius_miles: float = None
    ) -> "IPropertyQueryBuilder":
        """Add location-based filter"""
        pass

    @abstractmethod
    def filter_by_bedrooms(self, min_beds: int = None, max_beds: int = None) -> "IPropertyQueryBuilder":
        """Add bedroom count filter"""
        pass

    @abstractmethod
    def filter_by_amenities(self, required: List[str] = None, preferred: List[str] = None) -> "IPropertyQueryBuilder":
        """Add amenity filters"""
        pass

    @abstractmethod
    def sort_by(self, field: str, order: SortOrder = SortOrder.ASC) -> "IPropertyQueryBuilder":
        """Add sorting specification"""
        pass

    @abstractmethod
    def paginate(self, page: int = 1, limit: int = 50) -> "IPropertyQueryBuilder":
        """Add pagination"""
        pass

    @abstractmethod
    def build(self) -> PropertyQuery:
        """Build the final query object"""
        pass


class IPropertyRepository(ABC):
    """
    Abstract base class for property repositories.

    Defines the contract that all property data sources must implement.
    Supports both synchronous and asynchronous operations.
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if repository is connected and ready"""
        return self._is_connected

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to data source.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self):
        """Cleanup and disconnect from data source"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check repository health status.

        Returns:
            Dictionary with health status information
        """
        pass

    # Core query operations
    @abstractmethod
    async def find_properties(self, query: PropertyQuery) -> RepositoryResult:
        """
        Find properties matching query criteria.

        Args:
            query: Property query specification

        Returns:
            Repository result with matching properties
        """
        pass

    @abstractmethod
    async def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific property by ID.

        Args:
            property_id: Unique property identifier

        Returns:
            Property data or None if not found
        """
        pass

    @abstractmethod
    async def count_properties(self, query: PropertyQuery) -> int:
        """
        Count properties matching query without returning data.

        Args:
            query: Property query specification

        Returns:
            Number of matching properties
        """
        pass

    # Convenience methods (default implementations)
    async def find_properties_sync(self, query: PropertyQuery) -> RepositoryResult:
        """Synchronous wrapper for find_properties"""
        return await self.find_properties(query)

    async def get_property_by_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Find property by address (if supported)"""
        query = PropertyQuery()
        query.add_filter("address", QueryOperator.EQUALS, address)
        result = await self.find_properties(query)
        return result.data[0] if result.has_data else None

    # Batch operations
    async def get_properties_by_ids(self, property_ids: List[str]) -> RepositoryResult:
        """Get multiple properties by IDs"""
        query = PropertyQuery()
        query.add_filter("id", QueryOperator.IN, property_ids)
        return await self.find_properties(query)

    # Utility methods
    def create_query_builder(self) -> IPropertyQueryBuilder:
        """Create a query builder for this repository"""
        from .query_builder import PropertyQueryBuilder

        return PropertyQueryBuilder()

    @abstractmethod
    def get_supported_filters(self) -> List[str]:
        """Get list of supported filter fields for this repository"""
        pass

    @abstractmethod
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get repository performance metrics"""
        pass


# Type aliases for convenience
PropertyList = List[Dict[str, Any]]
PropertyDict = Dict[str, Any]
RepositoryConfig = Dict[str, Any]

# Repository registry type
RepositoryRegistry = Dict[str, Callable[..., IPropertyRepository]]
