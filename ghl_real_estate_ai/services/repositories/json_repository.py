"""
JSON Property Repository Implementation

Handles property data stored in JSON files. Supports multiple JSON sources
and provides efficient filtering and querying capabilities.
"""

import asyncio
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from .interfaces import (
        IPropertyRepository,
        PropertyQuery,
        QueryOperator,
        RepositoryError,
        RepositoryMetadata,
        RepositoryResult,
        SortOrder,
    )
except ImportError:
    from interfaces import (
        IPropertyRepository,
        PropertyQuery,
        QueryOperator,
        RepositoryError,
        RepositoryMetadata,
        RepositoryResult,
        SortOrder,
    )


class JsonPropertyRepository(IPropertyRepository):
    """
    Repository implementation for JSON-based property data.

    Features:
    - Multiple JSON file support
    - In-memory caching for performance
    - Complex query filtering
    - Geographic proximity calculations
    - Amenity matching with fuzzy logic
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize JSON repository.

        Config options:
        - data_paths: List of JSON file paths
        - cache_ttl: Cache time-to-live in seconds
        - auto_refresh: Automatically refresh data
        - normalize_data: Normalize property data format
        """
        super().__init__("json_repository", config)

        self.data_paths = config.get("data_paths", [])
        self.cache_ttl = config.get("cache_ttl", 300)  # 5 minutes
        self.auto_refresh = config.get("auto_refresh", True)
        self.normalize_data = config.get("normalize_data", True)

        # Internal state
        self._properties_cache: List[Dict[str, Any]] = []
        self._last_loaded: Optional[datetime] = None
        self._file_mtimes: Dict[str, float] = {}

    async def connect(self) -> bool:
        """Load JSON data and establish 'connection'"""
        try:
            await self._load_json_data()
            self._is_connected = True
            return True
        except Exception as e:
            raise RepositoryError(
                f"Failed to connect to JSON data sources: {e}", repository_type="json", original_error=e
            )

    async def disconnect(self):
        """Clear cached data"""
        self._properties_cache.clear()
        self._last_loaded = None
        self._file_mtimes.clear()
        self._is_connected = False

    async def health_check(self) -> Dict[str, Any]:
        """Check JSON files and data health"""
        health = {
            "status": "healthy",
            "properties_count": len(self._properties_cache),
            "last_loaded": self._last_loaded.isoformat() if self._last_loaded else None,
            "data_sources": len(self.data_paths),
            "issues": [],
        }

        # Check file accessibility
        for path in self.data_paths:
            file_path = Path(path)
            if not file_path.exists():
                health["issues"].append(f"File not found: {path}")
                health["status"] = "degraded"
            elif not file_path.is_file():
                health["issues"].append(f"Not a file: {path}")
                health["status"] = "degraded"

        # Check data freshness
        if self.auto_refresh and self._should_refresh():
            health["issues"].append("Data may be stale, refresh recommended")
            if health["status"] == "healthy":
                health["status"] = "warning"

        return health

    async def find_properties(self, query: PropertyQuery) -> RepositoryResult:
        """Find properties matching query criteria"""
        start_time = datetime.now()

        try:
            # Ensure data is fresh
            if not self._is_connected or self._should_refresh():
                await self._load_json_data()

            # Apply filters
            filtered_properties = await self._apply_filters(self._properties_cache, query)

            # Apply sorting
            sorted_properties = await self._apply_sorting(filtered_properties, query)

            # Apply pagination
            paginated_properties, total_count = await self._apply_pagination(sorted_properties, query)

            # Create metadata
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            metadata = RepositoryMetadata(
                source=self.name,
                query_time_ms=execution_time,
                cache_hit=True,  # JSON is always cached
                total_scanned=len(self._properties_cache),
            )

            return RepositoryResult(
                data=paginated_properties,
                total_count=total_count,
                pagination=query.pagination,
                metadata=metadata,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            return RepositoryResult(success=False, errors=[f"Query failed: {str(e)}"])

    async def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get specific property by ID"""
        if not self._is_connected or self._should_refresh():
            await self._load_json_data()

        for prop in self._properties_cache:
            if str(prop.get("id")) == str(property_id):
                return prop
        return None

    async def count_properties(self, query: PropertyQuery) -> int:
        """Count properties matching query"""
        if not self._is_connected or self._should_refresh():
            await self._load_json_data()

        filtered_properties = await self._apply_filters(self._properties_cache, query)
        return len(filtered_properties)

    def get_supported_filters(self) -> List[str]:
        """Get supported filter fields"""
        return [
            "id",
            "address",
            "price",
            "bedrooms",
            "bathrooms",
            "sqft",
            "square_feet",
            "neighborhood",
            "property_type",
            "year_built",
            "recently_renovated",
            "amenities",
            "days_on_market",
            "latitude",
            "longitude",
        ]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get repository performance metrics"""
        return {
            "repository_type": "json",
            "cached_properties": len(self._properties_cache),
            "last_loaded": self._last_loaded.isoformat() if self._last_loaded else None,
            "data_sources": len(self.data_paths),
            "cache_ttl_seconds": self.cache_ttl,
            "auto_refresh": self.auto_refresh,
        }

    # Private methods
    async def _load_json_data(self):
        """Load and merge data from all JSON sources"""
        all_properties = []
        current_mtimes = {}

        for data_path in self.data_paths:
            path_obj = Path(data_path)

            if not path_obj.exists():
                continue

            # Check if file was modified
            current_mtime = path_obj.stat().st_mtime
            current_mtimes[data_path] = current_mtime

            # Skip if file hasn't changed
            if (
                data_path in self._file_mtimes
                and self._file_mtimes[data_path] == current_mtime
                and not self._should_refresh()
            ):
                continue

            try:
                with open(path_obj, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Handle different JSON structures
                properties = self._extract_properties_from_json(data, data_path)
                all_properties.extend(properties)

            except json.JSONDecodeError as e:
                raise RepositoryError(f"Invalid JSON in {data_path}: {e}", repository_type="json", original_error=e)

        # Update cache and timestamps
        if all_properties or not self._properties_cache:
            self._properties_cache = all_properties
            self._last_loaded = datetime.now()
            self._file_mtimes = current_mtimes

        # Normalize data if required
        if self.normalize_data:
            self._properties_cache = [self._normalize_property(p) for p in self._properties_cache]

    def _extract_properties_from_json(self, data: Any, source_path: str) -> List[Dict[str, Any]]:
        """Extract property list from various JSON structures"""
        properties = []

        if isinstance(data, list):
            # Direct array of properties
            properties = data
        elif isinstance(data, dict):
            # Check common property array keys
            for key in ["properties", "listings", "data", "results", "items"]:
                if key in data and isinstance(data[key], list):
                    properties = data[key]
                    break

            # If still not found, check if it's a single property
            if not properties and any(k in data for k in ["id", "address", "price"]):
                properties = [data]

        # Add source metadata
        for prop in properties:
            if isinstance(prop, dict):
                prop["_source"] = source_path
                prop["_loaded_at"] = datetime.now().isoformat()

        return properties

    def _normalize_property(self, prop: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize property data format"""
        normalized = prop.copy()

        # Standardize common field names
        field_mappings = {
            "beds": "bedrooms",
            "baths": "bathrooms",
            "square_feet": "sqft",
            "property_type": "type",
            "listing_price": "price",
            "list_price": "price",
        }

        for old_key, new_key in field_mappings.items():
            if old_key in normalized and new_key not in normalized:
                normalized[new_key] = normalized[old_key]

        # Ensure required fields exist
        defaults = {
            "id": f"prop_{hash(str(prop))}",
            "bedrooms": 0,
            "bathrooms": 0,
            "sqft": 0,
            "price": 0,
            "amenities": [],
        }

        for key, default_value in defaults.items():
            if key not in normalized:
                normalized[key] = default_value

        # Normalize amenities to list
        if isinstance(normalized.get("amenities"), str):
            normalized["amenities"] = [a.strip() for a in normalized["amenities"].split(",")]

        return normalized

    def _should_refresh(self) -> bool:
        """Check if data should be refreshed"""
        if not self.auto_refresh or not self._last_loaded:
            return True

        age = datetime.now() - self._last_loaded
        return age.total_seconds() > self.cache_ttl

    async def _apply_filters(self, properties: List[Dict[str, Any]], query: PropertyQuery) -> List[Dict[str, Any]]:
        """Apply all query filters to property list"""
        filtered = properties.copy()

        # Price range filters
        if query.min_price is not None:
            filtered = [p for p in filtered if p.get("price", 0) >= query.min_price]
        if query.max_price is not None:
            filtered = [p for p in filtered if p.get("price", 0) <= query.max_price]

        # Bedroom filters
        if query.min_bedrooms is not None:
            filtered = [p for p in filtered if p.get("bedrooms", 0) >= query.min_bedrooms]
        if query.max_bedrooms is not None:
            filtered = [p for p in filtered if p.get("bedrooms", 0) <= query.max_bedrooms]

        # Bathroom filters
        if query.min_bathrooms is not None:
            filtered = [p for p in filtered if p.get("bathrooms", 0) >= query.min_bathrooms]
        if query.max_bathrooms is not None:
            filtered = [p for p in filtered if p.get("bathrooms", 0) <= query.max_bathrooms]

        # Square footage filters
        if query.min_sqft is not None:
            filtered = [p for p in filtered if p.get("sqft", 0) >= query.min_sqft]
        if query.max_sqft is not None:
            filtered = [p for p in filtered if p.get("sqft", 0) <= query.max_sqft]

        # Property type filter
        if query.property_types:
            filtered = [
                p for p in filtered if p.get("property_type", "").lower() in [pt.lower() for pt in query.property_types]
            ]

        # Location filters
        if query.neighborhoods:
            filtered = [
                p for p in filtered if p.get("neighborhood", "").lower() in [n.lower() for n in query.neighborhoods]
            ]

        # Geographic proximity filter
        if query.latitude and query.longitude and query.radius_miles:
            filtered = [
                p for p in filtered if self._is_within_radius(p, query.latitude, query.longitude, query.radius_miles)
            ]

        # Amenity filters
        if query.required_amenities:
            filtered = [p for p in filtered if self._has_required_amenities(p, query.required_amenities)]

        # Days on market filter
        if query.max_days_on_market is not None:
            filtered = [p for p in filtered if p.get("days_on_market", 0) <= query.max_days_on_market]

        # Custom filters
        for filter_obj in query.filters:
            filtered = self._apply_custom_filter(filtered, filter_obj)

        return filtered

    def _is_within_radius(self, prop: Dict[str, Any], lat: float, lon: float, radius_miles: float) -> bool:
        """Check if property is within specified radius"""
        prop_lat = prop.get("latitude")
        prop_lon = prop.get("longitude")

        if not prop_lat or not prop_lon:
            return False  # No coordinates available

        # Calculate distance using Haversine formula
        distance = self._calculate_distance(lat, lon, float(prop_lat), float(prop_lon))
        return distance <= radius_miles

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in miles using Haversine formula"""
        R = 3959  # Earth's radius in miles

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def _has_required_amenities(self, prop: Dict[str, Any], required: List[str]) -> bool:
        """Check if property has all required amenities"""
        prop_amenities = prop.get("amenities", [])
        if isinstance(prop_amenities, str):
            prop_amenities = [a.strip().lower() for a in prop_amenities.split(",")]
        else:
            prop_amenities = [str(a).lower() for a in prop_amenities]

        required_lower = [r.lower() for r in required]

        return all(any(req in amenity for amenity in prop_amenities) for req in required_lower)

    def _apply_custom_filter(self, properties: List[Dict[str, Any]], filter_obj) -> List[Dict[str, Any]]:
        """Apply custom filter to property list"""
        field = filter_obj.field
        operator = filter_obj.operator
        value = filter_obj.value

        filtered = []
        for prop in properties:
            prop_value = prop.get(field)
            if prop_value is None:
                continue

            if self._evaluate_filter_condition(prop_value, operator, value):
                filtered.append(prop)

        return filtered

    def _evaluate_filter_condition(self, prop_value: Any, operator: QueryOperator, filter_value: Any) -> bool:
        """Evaluate individual filter condition"""
        try:
            if operator == QueryOperator.EQUALS:
                return str(prop_value).lower() == str(filter_value).lower()
            elif operator == QueryOperator.NOT_EQUALS:
                return str(prop_value).lower() != str(filter_value).lower()
            elif operator == QueryOperator.GREATER_THAN:
                return float(prop_value) > float(filter_value)
            elif operator == QueryOperator.GREATER_THAN_OR_EQUAL:
                return float(prop_value) >= float(filter_value)
            elif operator == QueryOperator.LESS_THAN:
                return float(prop_value) < float(filter_value)
            elif operator == QueryOperator.LESS_THAN_OR_EQUAL:
                return float(prop_value) <= float(filter_value)
            elif operator == QueryOperator.IN:
                return prop_value in filter_value
            elif operator == QueryOperator.NOT_IN:
                return prop_value not in filter_value
            elif operator == QueryOperator.CONTAINS:
                return str(filter_value).lower() in str(prop_value).lower()
            elif operator == QueryOperator.STARTS_WITH:
                return str(prop_value).lower().startswith(str(filter_value).lower())
            elif operator == QueryOperator.ENDS_WITH:
                return str(prop_value).lower().endswith(str(filter_value).lower())
            elif operator == QueryOperator.BETWEEN:
                return filter_value[0] <= prop_value <= filter_value[1]
            else:
                return False
        except (ValueError, TypeError, IndexError):
            return False

    async def _apply_sorting(self, properties: List[Dict[str, Any]], query: PropertyQuery) -> List[Dict[str, Any]]:
        """Apply sorting to property list"""
        if not query.sort_by:
            return properties

        reverse = query.sort_order == SortOrder.DESC

        def sort_key(prop: Dict[str, Any]):
            value = prop.get(query.sort_by, 0)
            # Handle numeric sorting
            if isinstance(value, (int, float)):
                return value
            # Handle string sorting
            return str(value).lower()

        return sorted(properties, key=sort_key, reverse=reverse)

    async def _apply_pagination(self, properties: List[Dict[str, Any]], query: PropertyQuery) -> tuple:
        """Apply pagination to property list"""
        total_count = len(properties)

        # Update pagination with total count
        query.pagination.total_count = total_count

        start = query.pagination.offset
        end = start + query.pagination.limit

        paginated = properties[start:end]

        return paginated, total_count
