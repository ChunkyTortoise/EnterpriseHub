"""
Property Query Builder Implementation

Provides a fluent interface for building complex property queries.
Supports method chaining and validation for building PropertyQuery objects.
"""

from typing import List, Optional, Dict, Any
try:
    from .interfaces import IPropertyQueryBuilder, PropertyQuery, QueryFilter, QueryOperator, SortOrder, PaginationConfig
except ImportError:
    from interfaces import IPropertyQueryBuilder, PropertyQuery, QueryFilter, QueryOperator, SortOrder, PaginationConfig


class PropertyQueryBuilder(IPropertyQueryBuilder):
    """
    Fluent interface for building property queries.

    Supports method chaining and provides validation for query parameters.
    """

    def __init__(self):
        """Initialize empty query builder"""
        self._query = PropertyQuery()

    def reset(self) -> 'PropertyQueryBuilder':
        """Reset query builder to empty state"""
        self._query = PropertyQuery()
        return self

    def filter_by_price(self, min_price: int = None, max_price: int = None) -> 'PropertyQueryBuilder':
        """Add price range filter"""
        if min_price is not None:
            self._query.min_price = min_price
        if max_price is not None:
            self._query.max_price = max_price
        return self

    def filter_by_location(self, location: str = None, lat: float = None, lon: float = None,
                          radius_miles: float = None) -> 'PropertyQueryBuilder':
        """Add location-based filter"""
        if location:
            self._query.location = location

        if lat is not None and lon is not None:
            self._query.latitude = lat
            self._query.longitude = lon

        if radius_miles is not None:
            self._query.radius_miles = radius_miles

        return self

    def filter_by_bedrooms(self, min_beds: int = None, max_beds: int = None) -> 'PropertyQueryBuilder':
        """Add bedroom count filter"""
        if min_beds is not None:
            self._query.min_bedrooms = min_beds
        if max_beds is not None:
            self._query.max_bedrooms = max_beds
        return self

    def filter_by_bathrooms(self, min_baths: float = None, max_baths: float = None) -> 'PropertyQueryBuilder':
        """Add bathroom count filter"""
        if min_baths is not None:
            self._query.min_bathrooms = min_baths
        if max_baths is not None:
            self._query.max_bathrooms = max_baths
        return self

    def filter_by_sqft(self, min_sqft: int = None, max_sqft: int = None) -> 'PropertyQueryBuilder':
        """Add square footage filter"""
        if min_sqft is not None:
            self._query.min_sqft = min_sqft
        if max_sqft is not None:
            self._query.max_sqft = max_sqft
        return self

    def filter_by_property_types(self, property_types: List[str]) -> 'PropertyQueryBuilder':
        """Add property type filter"""
        self._query.property_types = property_types
        return self

    def filter_by_neighborhoods(self, neighborhoods: List[str]) -> 'PropertyQueryBuilder':
        """Add neighborhood filter"""
        self._query.neighborhoods = neighborhoods
        return self

    def filter_by_zip_codes(self, zip_codes: List[str]) -> 'PropertyQueryBuilder':
        """Add zip code filter"""
        self._query.zip_codes = zip_codes
        return self

    def filter_by_amenities(self, required: List[str] = None, preferred: List[str] = None) -> 'PropertyQueryBuilder':
        """Add amenity filters"""
        if required:
            self._query.required_amenities = required
        if preferred:
            self._query.preferred_amenities = preferred
        return self

    def filter_by_days_on_market(self, max_days: int) -> 'PropertyQueryBuilder':
        """Add days on market filter"""
        self._query.max_days_on_market = max_days
        return self

    def filter_by_year_built(self, min_year: int = None, max_year: int = None) -> 'PropertyQueryBuilder':
        """Add year built filter"""
        if min_year is not None:
            self._query.min_year_built = min_year
        if max_year is not None:
            self._query.max_year_built = max_year
        return self

    def semantic_search(self, query_text: str, similarity_threshold: float = None) -> 'PropertyQueryBuilder':
        """Add semantic search query"""
        self._query.semantic_query = query_text
        if similarity_threshold is not None:
            self._query.similarity_threshold = similarity_threshold
        return self

    def add_custom_filter(self, field: str, operator: QueryOperator, value: Any,
                         field_type: str = None) -> 'PropertyQueryBuilder':
        """Add custom filter"""
        self._query.add_filter(field, operator, value, field_type)
        return self

    def sort_by(self, field: str, order: SortOrder = SortOrder.ASC) -> 'PropertyQueryBuilder':
        """Add sorting specification"""
        self._query.sort_by = field
        self._query.sort_order = order
        return self

    def paginate(self, page: int = 1, limit: int = 50) -> 'PropertyQueryBuilder':
        """Add pagination"""
        self._query.pagination = PaginationConfig(page=page, limit=limit)
        return self

    def include_metadata(self, include: bool = True) -> 'PropertyQueryBuilder':
        """Include metadata in results"""
        self._query.include_metadata = include
        return self

    def include_images(self, include: bool = True) -> 'PropertyQueryBuilder':
        """Include image URLs in results"""
        self._query.include_images = include
        return self

    def include_virtual_tours(self, include: bool = True) -> 'PropertyQueryBuilder':
        """Include virtual tour links in results"""
        self._query.include_virtual_tours = include
        return self

    def cache_control(self, use_cache: bool = True, cache_ttl_seconds: int = None) -> 'PropertyQueryBuilder':
        """Configure caching behavior"""
        self._query.use_cache = use_cache
        if cache_ttl_seconds is not None:
            from datetime import timedelta
            self._query.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        return self

    def quality_threshold(self, min_score: float) -> 'PropertyQueryBuilder':
        """Set minimum quality score threshold"""
        self._query.quality_score_threshold = min_score
        return self

    def build(self) -> PropertyQuery:
        """Build the final query object"""
        # Validate query before returning
        self._validate_query()
        return self._query

    def _validate_query(self):
        """Validate query parameters"""
        # Price validation
        if (self._query.min_price is not None and self._query.max_price is not None and
            self._query.min_price > self._query.max_price):
            raise ValueError("min_price cannot be greater than max_price")

        # Bedroom validation
        if (self._query.min_bedrooms is not None and self._query.max_bedrooms is not None and
            self._query.min_bedrooms > self._query.max_bedrooms):
            raise ValueError("min_bedrooms cannot be greater than max_bedrooms")

        # Bathroom validation
        if (self._query.min_bathrooms is not None and self._query.max_bathrooms is not None and
            self._query.min_bathrooms > self._query.max_bathrooms):
            raise ValueError("min_bathrooms cannot be greater than max_bathrooms")

        # Square footage validation
        if (self._query.min_sqft is not None and self._query.max_sqft is not None and
            self._query.min_sqft > self._query.max_sqft):
            raise ValueError("min_sqft cannot be greater than max_sqft")

        # Year built validation
        if (self._query.min_year_built is not None and self._query.max_year_built is not None and
            self._query.min_year_built > self._query.max_year_built):
            raise ValueError("min_year_built cannot be greater than max_year_built")

        # Geographic validation
        if ((self._query.latitude is not None or self._query.longitude is not None) and
            (self._query.latitude is None or self._query.longitude is None)):
            raise ValueError("Both latitude and longitude must be provided for geographic search")

        if self._query.radius_miles is not None and self._query.radius_miles <= 0:
            raise ValueError("radius_miles must be positive")

        # Pagination validation
        if self._query.pagination.page < 1:
            raise ValueError("Page number must be >= 1")

        if self._query.pagination.limit < 1 or self._query.pagination.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")


class FluentPropertyQuery:
    """
    Static factory methods for common query patterns.
    Provides convenient shortcuts for common use cases.
    """

    @staticmethod
    def by_price_range(min_price: int = None, max_price: int = None) -> PropertyQueryBuilder:
        """Start query with price range filter"""
        return PropertyQueryBuilder().filter_by_price(min_price, max_price)

    @staticmethod
    def by_location(location: str) -> PropertyQueryBuilder:
        """Start query with location filter"""
        return PropertyQueryBuilder().filter_by_location(location=location)

    @staticmethod
    def near_coordinates(lat: float, lon: float, radius_miles: float = 10) -> PropertyQueryBuilder:
        """Start query with coordinate proximity filter"""
        return PropertyQueryBuilder().filter_by_location(lat=lat, lon=lon, radius_miles=radius_miles)

    @staticmethod
    def by_bedrooms(min_beds: int = None, max_beds: int = None) -> PropertyQueryBuilder:
        """Start query with bedroom filter"""
        return PropertyQueryBuilder().filter_by_bedrooms(min_beds, max_beds)

    @staticmethod
    def semantic(query_text: str) -> PropertyQueryBuilder:
        """Start query with semantic search"""
        return PropertyQueryBuilder().semantic_search(query_text)

    @staticmethod
    def luxury_homes(min_price: int = 1000000, min_sqft: int = 3000) -> PropertyQueryBuilder:
        """Pre-configured luxury homes query"""
        return (PropertyQueryBuilder()
                .filter_by_price(min_price=min_price)
                .filter_by_sqft(min_sqft=min_sqft)
                .filter_by_amenities(required=["garage"], preferred=["pool", "fireplace"])
                .sort_by("price", SortOrder.DESC))

    @staticmethod
    def starter_homes(max_price: int = 400000, max_bedrooms: int = 3) -> PropertyQueryBuilder:
        """Pre-configured starter homes query"""
        return (PropertyQueryBuilder()
                .filter_by_price(max_price=max_price)
                .filter_by_bedrooms(max_beds=max_bedrooms)
                .sort_by("price", SortOrder.ASC))

    @staticmethod
    def family_homes(min_bedrooms: int = 3, required_amenities: List[str] = None) -> PropertyQueryBuilder:
        """Pre-configured family homes query"""
        amenities = required_amenities or ["garage", "yard"]
        return (PropertyQueryBuilder()
                .filter_by_bedrooms(min_beds=min_bedrooms)
                .filter_by_amenities(required=amenities)
                .sort_by("sqft", SortOrder.DESC))

    @staticmethod
    def investment_properties(max_days_on_market: int = 30) -> PropertyQueryBuilder:
        """Pre-configured investment property query"""
        return (PropertyQueryBuilder()
                .filter_by_days_on_market(max_days_on_market)
                .filter_by_property_types(["Single Family", "Townhome", "Condo"])
                .sort_by("price", SortOrder.ASC))


# Convenience aliases
Q = FluentPropertyQuery  # Short alias for quick access
QueryBuilder = PropertyQueryBuilder