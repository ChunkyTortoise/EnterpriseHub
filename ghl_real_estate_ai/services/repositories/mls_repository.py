"""
MLS API Property Repository Implementation

Handles property data from Multiple Listing Service (MLS) APIs.
Supports various MLS providers with standardized query interface.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from .interfaces import (
    IPropertyRepository,
    PropertyQuery,
    RepositoryError,
    RepositoryMetadata,
    RepositoryResult,
)


class MLSAPIRepository(IPropertyRepository):
    """
    Repository implementation for MLS API property data.

    Features:
    - Multiple MLS provider support
    - Rate limiting and retry logic
    - Response caching
    - Real-time data access
    - Authentication handling
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize MLS API repository.

        Config options:
        - api_base_url: MLS API base URL
        - api_key: Authentication API key
        - api_secret: Authentication secret (if required)
        - rate_limit: Requests per second limit
        - timeout: Request timeout in seconds
        - retry_attempts: Number of retry attempts
        - cache_ttl: Response cache TTL in seconds
        """
        super().__init__("mls_api_repository", config)

        # API configuration
        self.api_base_url = config.get("api_base_url", "")
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")

        # Performance settings
        self.rate_limit = config.get("rate_limit", 10)  # requests/second
        self.timeout = config.get("timeout", 30)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.cache_ttl = config.get("cache_ttl", 300)  # 5 minutes

        # Provider-specific settings
        self.provider = config.get("provider", "generic")  # e.g., "trestle", "bridge", "sparkapi"
        self.market_area = config.get("market_area", "")

        # Internal state
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._response_cache: Dict[str, tuple] = {}  # (data, timestamp)
        self._rate_limiter = asyncio.Semaphore(self.rate_limit)

    async def connect(self) -> bool:
        """Establish connection to MLS API"""
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)

            # Authenticate with API
            await self._authenticate()

            self._is_connected = True
            return True

        except Exception as e:
            raise RepositoryError(f"Failed to connect to MLS API: {e}", repository_type="mls_api", original_error=e)

    async def disconnect(self):
        """Close HTTP session and clear cache"""
        if self._session:
            await self._session.close()
        self._response_cache.clear()
        self._auth_token = None
        self._token_expires_at = None
        self._is_connected = False

    async def health_check(self) -> Dict[str, Any]:
        """Check MLS API health and connectivity"""
        health = {
            "status": "healthy",
            "api_url": self.api_base_url,
            "provider": self.provider,
            "authenticated": self._auth_token is not None,
            "cache_entries": len(self._response_cache),
            "issues": [],
        }

        try:
            # Test API connectivity
            test_query = PropertyQuery()
            test_query.pagination.limit = 1
            result = await self._make_api_request("/search", {"limit": 1})

            if not result:
                health["issues"].append("API test query failed")
                health["status"] = "degraded"

        except Exception as e:
            health["issues"].append(f"API connectivity issue: {str(e)}")
            health["status"] = "unhealthy"

        # Check token expiration
        if self._token_expires_at and datetime.now() >= self._token_expires_at:
            health["issues"].append("Authentication token expired")
            if health["status"] == "healthy":
                health["status"] = "warning"

        return health

    async def find_properties(self, query: PropertyQuery) -> RepositoryResult:
        """Find properties via MLS API"""
        start_time = datetime.now()

        try:
            # Ensure authentication
            await self._ensure_authenticated()

            # Build API query parameters
            api_params = await self._build_api_params(query)

            # Check cache first
            cache_key = self._generate_cache_key(api_params)
            cached_result = self._get_cached_response(cache_key)

            if cached_result and query.use_cache:
                return self._create_repository_result(cached_result, start_time, cache_hit=True)

            # Make API request
            endpoint = self._get_search_endpoint()
            raw_data = await self._make_api_request(endpoint, api_params)

            if not raw_data:
                return RepositoryResult(success=False, errors=["No data returned from MLS API"])

            # Process and normalize response
            processed_data = await self._process_api_response(raw_data)

            # Cache the response
            if query.use_cache:
                self._cache_response(cache_key, processed_data)

            return self._create_repository_result(processed_data, start_time, cache_hit=False)

        except Exception as e:
            return RepositoryResult(success=False, errors=[f"MLS API query failed: {str(e)}"])

    async def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get specific property by MLS ID"""
        await self._ensure_authenticated()

        endpoint = self._get_property_endpoint(property_id)
        raw_data = await self._make_api_request(endpoint, {})

        if raw_data:
            processed = await self._process_api_response(raw_data)
            return processed.get("properties", [{}])[0] if processed.get("properties") else None

        return None

    async def count_properties(self, query: PropertyQuery) -> int:
        """Count properties matching query via API"""
        await self._ensure_authenticated()

        # Modify query for count-only request
        count_params = await self._build_api_params(query)
        count_params["count_only"] = True

        endpoint = self._get_search_endpoint()
        raw_data = await self._make_api_request(endpoint, count_params)

        if raw_data and "total_count" in raw_data:
            return raw_data["total_count"]

        # Fallback: estimate from paginated query
        count_params["limit"] = 1
        raw_data = await self._make_api_request(endpoint, count_params)
        return raw_data.get("total_count", 0) if raw_data else 0

    def get_supported_filters(self) -> List[str]:
        """Get supported filter fields for this MLS provider"""
        base_filters = [
            "ListPrice",
            "BedroomsTotal",
            "BathroomsTotalDecimal",
            "LivingArea",
            "PropertyType",
            "City",
            "PostalCode",
            "StateOrProvince",
            "ListingKey",
            "MLSAreaMajor",
            "YearBuilt",
            "DaysOnMarket",
        ]

        # Provider-specific additional filters
        provider_filters = {
            "trestle": ["WaterViewYN", "PoolPrivateYN", "GarageYN"],
            "bridge": ["HasPool", "HasGarage", "HasFireplace"],
            "sparkapi": ["Pool", "Garage", "Fireplace"],
        }

        return base_filters + provider_filters.get(self.provider, [])

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get MLS API performance metrics"""
        return {
            "repository_type": "mls_api",
            "provider": self.provider,
            "api_base_url": self.api_base_url,
            "rate_limit": self.rate_limit,
            "cache_entries": len(self._response_cache),
            "authenticated": self._auth_token is not None,
            "token_expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
        }

    # Private methods
    async def _authenticate(self):
        """Authenticate with MLS API"""
        if not self.api_key:
            raise RepositoryError("API key required for MLS authentication")

        auth_data = await self._get_auth_data()

        if self.provider == "trestle":
            await self._authenticate_trestle(auth_data)
        elif self.provider == "bridge":
            await self._authenticate_bridge(auth_data)
        elif self.provider == "sparkapi":
            await self._authenticate_sparkapi(auth_data)
        else:
            await self._authenticate_generic(auth_data)

    async def _get_auth_data(self) -> Dict[str, Any]:
        """Get authentication data for API"""
        auth_data = {"api_key": self.api_key, "grant_type": "client_credentials"}

        if self.api_secret:
            auth_data["api_secret"] = self.api_secret

        return auth_data

    async def _authenticate_generic(self, auth_data: Dict[str, Any]):
        """Generic authentication flow"""
        auth_endpoint = f"{self.api_base_url}/oauth2/token"

        async with self._rate_limiter:
            async with self._session.post(auth_endpoint, data=auth_data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self._auth_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                else:
                    error_text = await response.text()
                    raise RepositoryError(f"Authentication failed: {error_text}")

    async def _authenticate_trestle(self, auth_data: Dict[str, Any]):
        """Trestle MLS authentication"""
        auth_endpoint = f"{self.api_base_url}/login"

        # Trestle-specific authentication
        headers = {"Authorization": f"Basic {self.api_key}", "Content-Type": "application/json"}

        async with self._rate_limiter:
            async with self._session.post(auth_endpoint, headers=headers, json=auth_data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self._auth_token = token_data.get("access_token")
                    self._token_expires_at = datetime.now() + timedelta(hours=24)
                else:
                    raise RepositoryError(f"Trestle authentication failed: {response.status}")

    async def _authenticate_bridge(self, auth_data: Dict[str, Any]):
        """Bridge Interactive authentication"""
        # Implement Bridge-specific auth logic
        await self._authenticate_generic(auth_data)

    async def _authenticate_sparkapi(self, auth_data: Dict[str, Any]):
        """Spark API authentication"""
        # Implement Spark API-specific auth logic
        await self._authenticate_generic(auth_data)

    async def _ensure_authenticated(self):
        """Ensure we have a valid authentication token"""
        if not self._auth_token or (self._token_expires_at and datetime.now() >= self._token_expires_at):
            await self._authenticate()

    async def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make authenticated API request with retry logic"""
        url = f"{self.api_base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self._auth_token}", "Accept": "application/json"}

        for attempt in range(self.retry_attempts):
            try:
                async with self._rate_limiter:
                    async with self._session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 401:
                            # Re-authenticate and retry
                            await self._authenticate()
                            headers["Authorization"] = f"Bearer {self._auth_token}"
                            continue
                        elif response.status == 429:
                            # Rate limited, wait and retry
                            retry_after = int(response.headers.get("Retry-After", 5))
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            error_text = await response.text()
                            raise RepositoryError(f"API error {response.status}: {error_text}")

            except asyncio.TimeoutError:
                if attempt == self.retry_attempts - 1:
                    raise RepositoryError("API request timeout")
                await asyncio.sleep(2**attempt)  # Exponential backoff

        return None

    async def _build_api_params(self, query: PropertyQuery) -> Dict[str, Any]:
        """Convert PropertyQuery to MLS API parameters"""
        params = {}

        # Price range
        if query.min_price is not None:
            params["ListPriceMin"] = query.min_price
        if query.max_price is not None:
            params["ListPriceMax"] = query.max_price

        # Bedrooms and bathrooms
        if query.min_bedrooms is not None:
            params["BedroomsTotalMin"] = query.min_bedrooms
        if query.max_bedrooms is not None:
            params["BedroomsTotalMax"] = query.max_bedrooms
        if query.min_bathrooms is not None:
            params["BathroomsTotalMin"] = query.min_bathrooms
        if query.max_bathrooms is not None:
            params["BathroomsTotalMax"] = query.max_bathrooms

        # Square footage
        if query.min_sqft is not None:
            params["LivingAreaMin"] = query.min_sqft
        if query.max_sqft is not None:
            params["LivingAreaMax"] = query.max_sqft

        # Property types
        if query.property_types:
            params["PropertyType"] = ",".join(query.property_types)

        # Location
        if query.location:
            params["City"] = query.location
        if query.zip_codes:
            params["PostalCode"] = ",".join(query.zip_codes)

        # Days on market
        if query.max_days_on_market is not None:
            params["DaysOnMarketMax"] = query.max_days_on_market

        # Sorting
        sort_mapping = {
            "price": "ListPrice",
            "bedrooms": "BedroomsTotal",
            "bathrooms": "BathroomsTotalDecimal",
            "sqft": "LivingArea",
            "days_on_market": "DaysOnMarket",
        }

        if query.sort_by in sort_mapping:
            params["$orderby"] = f"{sort_mapping[query.sort_by]} {query.sort_order.value}"

        # Pagination
        params["$top"] = query.pagination.limit
        params["$skip"] = query.pagination.offset

        # Provider-specific parameters
        if self.market_area:
            params["MLSAreaMajor"] = self.market_area

        return params

    async def _process_api_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize MLS API response"""
        processed = {"properties": [], "total_count": 0, "metadata": {}}

        # Extract properties from response
        if "value" in raw_data:  # OData format
            properties = raw_data["value"]
            processed["total_count"] = raw_data.get("@odata.count", len(properties))
        elif "results" in raw_data:
            properties = raw_data["results"]
            processed["total_count"] = raw_data.get("total_results", len(properties))
        else:
            properties = raw_data if isinstance(raw_data, list) else [raw_data]
            processed["total_count"] = len(properties)

        # Normalize property data
        processed["properties"] = [await self._normalize_mls_property(prop) for prop in properties]

        return processed

    async def _normalize_mls_property(self, mls_prop: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MLS property data to standard format"""
        normalized = {
            "id": mls_prop.get("ListingKey") or mls_prop.get("ListingId"),
            "mls_id": mls_prop.get("ListingKey") or mls_prop.get("ListingId"),
            "address": self._build_address(mls_prop),
            "price": mls_prop.get("ListPrice", 0),
            "bedrooms": mls_prop.get("BedroomsTotal", 0),
            "bathrooms": mls_prop.get("BathroomsTotalDecimal") or mls_prop.get("BathroomsTotal", 0),
            "sqft": mls_prop.get("LivingArea", 0),
            "property_type": mls_prop.get("PropertyType", ""),
            "year_built": mls_prop.get("YearBuilt"),
            "days_on_market": mls_prop.get("DaysOnMarket", 0),
            "neighborhood": mls_prop.get("MLSAreaMajor") or mls_prop.get("Neighborhood"),
            "city": mls_prop.get("City"),
            "state": mls_prop.get("StateOrProvince"),
            "zip_code": mls_prop.get("PostalCode"),
            "latitude": mls_prop.get("Latitude"),
            "longitude": mls_prop.get("Longitude"),
            "listing_date": mls_prop.get("ListingContractDate"),
            "status": mls_prop.get("StandardStatus"),
            "amenities": self._extract_amenities(mls_prop),
            "_source": "mls_api",
            "_raw_data": mls_prop,
        }

        return normalized

    def _build_address(self, mls_prop: Dict[str, Any]) -> str:
        """Build formatted address from MLS data"""
        parts = []

        if mls_prop.get("StreetNumber"):
            parts.append(str(mls_prop["StreetNumber"]))
        if mls_prop.get("StreetName"):
            parts.append(mls_prop["StreetName"])
        if mls_prop.get("StreetSuffix"):
            parts.append(mls_prop["StreetSuffix"])

        return " ".join(parts) or mls_prop.get("UnparsedAddress", "Address not available")

    def _extract_amenities(self, mls_prop: Dict[str, Any]) -> List[str]:
        """Extract amenities from MLS property data"""
        amenities = []

        # Common amenity mappings
        amenity_mappings = {
            "PoolPrivateYN": "pool",
            "GarageYN": "garage",
            "FireplaceYN": "fireplace",
            "WaterViewYN": "water_view",
            "HasPool": "pool",
            "HasGarage": "garage",
            "HasFireplace": "fireplace",
        }

        for field, amenity in amenity_mappings.items():
            if mls_prop.get(field) in [True, "Y", "Yes", 1]:
                amenities.append(amenity)

        return amenities

    def _get_search_endpoint(self) -> str:
        """Get the search endpoint for this provider"""
        endpoints = {"trestle": "/properties", "bridge": "/listings", "sparkapi": "/listings", "generic": "/properties"}
        return endpoints.get(self.provider, "/properties")

    def _get_property_endpoint(self, property_id: str) -> str:
        """Get the single property endpoint"""
        endpoints = {
            "trestle": f"/properties/{property_id}",
            "bridge": f"/listings/{property_id}",
            "sparkapi": f"/listings/{property_id}",
            "generic": f"/properties/{property_id}",
        }
        return endpoints.get(self.provider, f"/properties/{property_id}")

    def _generate_cache_key(self, params: Dict[str, Any]) -> str:
        """Generate cache key from API parameters"""
        sorted_params = sorted(params.items())
        return f"mls_{hash(str(sorted_params))}"

    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if still valid"""
        if cache_key in self._response_cache:
            data, timestamp = self._response_cache[cache_key]
            if datetime.now() - timestamp <= timedelta(seconds=self.cache_ttl):
                return data
        return None

    def _cache_response(self, cache_key: str, data: Dict[str, Any]):
        """Cache API response"""
        self._response_cache[cache_key] = (data, datetime.now())

        # Clean old cache entries
        cutoff = datetime.now() - timedelta(seconds=self.cache_ttl * 2)
        self._response_cache = {k: v for k, v in self._response_cache.items() if v[1] > cutoff}

    def _create_repository_result(
        self, processed_data: Dict[str, Any], start_time: datetime, cache_hit: bool
    ) -> RepositoryResult:
        """Create RepositoryResult from processed data"""
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        metadata = RepositoryMetadata(
            source=self.name,
            query_time_ms=execution_time,
            cache_hit=cache_hit,
            total_scanned=processed_data.get("total_count"),
            api_calls_made=0 if cache_hit else 1,
        )

        return RepositoryResult(
            data=processed_data.get("properties", []),
            total_count=processed_data.get("total_count", 0),
            metadata=metadata,
            execution_time_ms=execution_time,
        )
