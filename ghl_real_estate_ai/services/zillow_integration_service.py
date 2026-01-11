"""
Zillow Integration Service

Handles property data retrieval from Zillow through multiple API sources:
- Official Zillow APIs (when available)
- Third-party providers (HasData, Apify, ZenRows)
- Fallback to cached/demo data

Provides real estate property information for lead matching and market analysis.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import aiohttp
from enum import Enum

from ..ghl_utils.config import settings

logger = logging.getLogger(__name__)


class ZillowDataSource(Enum):
    """Available Zillow data sources"""
    OFFICIAL = "official"
    HASDATA = "hasdata"
    APIFY = "apify"
    ZENROWS = "zenrows"
    DEMO = "demo"


@dataclass
class PropertyData:
    """Structure for property information from Zillow"""
    zpid: str  # Zillow Property ID
    address: str
    city: str
    state: str
    zipcode: str
    price: Optional[int] = None
    zestimate: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    listing_status: Optional[str] = None
    days_on_market: Optional[int] = None
    price_per_sqft: Optional[float] = None
    neighborhood: Optional[str] = None
    school_rating: Optional[int] = None
    walkability_score: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    photos: List[str] = None
    listing_agent: Optional[str] = None
    description: Optional[str] = None
    last_updated: datetime = datetime.now()

    def __post_init__(self):
        if self.photos is None:
            self.photos = []

        # Calculate price per sqft if missing
        if self.price and self.sqft and not self.price_per_sqft:
            self.price_per_sqft = round(self.price / self.sqft, 2)


@dataclass
class MarketAnalysis:
    """Market analysis data from Zillow"""
    area: str
    median_price: Optional[int] = None
    price_change_30d: Optional[float] = None
    price_change_1y: Optional[float] = None
    inventory_level: Optional[str] = None
    median_days_on_market: Optional[int] = None
    price_per_sqft_median: Optional[float] = None
    home_value_index: Optional[int] = None
    forecast_change_1y: Optional[float] = None
    last_updated: datetime = datetime.now()


class ZillowIntegrationService:
    """
    Comprehensive Zillow integration service with multiple data sources.

    Provides property data, market analysis, and neighborhood information
    for real estate agents and lead matching systems.
    """

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_keys = {
            'hasdata': getattr(settings, 'hasdata_api_key', None),
            'apify': getattr(settings, 'apify_api_key', None),
            'zenrows': getattr(settings, 'zenrows_api_key', None),
            'zillow_official': getattr(settings, 'zillow_api_key', None)
        }
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 3600  # 1 hour cache
        self.preferred_source = ZillowDataSource.HASDATA
        self.fallback_sources = [
            ZillowDataSource.APIFY,
            ZillowDataSource.ZENROWS,
            ZillowDataSource.DEMO
        ]

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def search_properties(
        self,
        location: str,
        filters: Optional[Dict[str, Any]] = None,
        max_results: int = 20
    ) -> List[PropertyData]:
        """
        Search for properties in a given location with optional filters.

        Args:
            location: City, ZIP, or address to search
            filters: Price range, beds, baths, property type, etc.
            max_results: Maximum number of properties to return

        Returns:
            List of PropertyData objects
        """
        cache_key = f"search_{location}_{json.dumps(filters or {}, sort_keys=True)}_{max_results}"

        # Check cache first
        if self._is_cached(cache_key):
            logger.info(f"Returning cached property search for {location}")
            return self.cache[cache_key]['data']

        try:
            # Try preferred source first
            properties = await self._search_with_source(
                self.preferred_source, location, filters, max_results
            )

            if properties:
                self._cache_data(cache_key, properties)
                logger.info(f"Found {len(properties)} properties in {location} via {self.preferred_source.value}")
                return properties

        except Exception as e:
            logger.warning(f"Primary source {self.preferred_source.value} failed: {str(e)}")

        # Try fallback sources
        for source in self.fallback_sources:
            try:
                properties = await self._search_with_source(
                    source, location, filters, max_results
                )
                if properties:
                    self._cache_data(cache_key, properties)
                    logger.info(f"Found {len(properties)} properties in {location} via fallback {source.value}")
                    return properties
            except Exception as e:
                logger.warning(f"Fallback source {source.value} failed: {str(e)}")
                continue

        # Return demo data if all sources fail
        return self._get_demo_properties(location, filters, max_results)

    async def get_property_details(self, zpid: str) -> Optional[PropertyData]:
        """
        Get detailed information for a specific property.

        Args:
            zpid: Zillow Property ID

        Returns:
            PropertyData object with detailed information
        """
        cache_key = f"property_{zpid}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            property_data = await self._get_property_details_with_source(
                self.preferred_source, zpid
            )

            if property_data:
                self._cache_data(cache_key, property_data)
                return property_data

        except Exception as e:
            logger.warning(f"Primary source failed for property {zpid}: {str(e)}")

        # Try fallback sources
        for source in self.fallback_sources:
            try:
                property_data = await self._get_property_details_with_source(source, zpid)
                if property_data:
                    self._cache_data(cache_key, property_data)
                    return property_data
            except Exception as e:
                logger.warning(f"Fallback source {source.value} failed for property {zpid}: {str(e)}")
                continue

        return None

    async def get_market_analysis(self, area: str) -> Optional[MarketAnalysis]:
        """
        Get market analysis for a specific area.

        Args:
            area: City, ZIP, or neighborhood name

        Returns:
            MarketAnalysis object
        """
        cache_key = f"market_{area}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            analysis = await self._get_market_analysis_with_source(
                self.preferred_source, area
            )

            if analysis:
                self._cache_data(cache_key, analysis)
                return analysis

        except Exception as e:
            logger.warning(f"Market analysis failed for {area}: {str(e)}")

        # Return demo market data
        return self._get_demo_market_analysis(area)

    async def find_properties_near_coordinates(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 5.0,
        max_results: int = 20
    ) -> List[PropertyData]:
        """
        Find properties near specific coordinates.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius in miles
            max_results: Maximum number of properties

        Returns:
            List of PropertyData objects
        """
        # Convert to location string and use regular search
        location = f"{lat},{lon}"
        return await self.search_properties(
            location,
            {"radius": radius_miles},
            max_results
        )

    async def _search_with_source(
        self,
        source: ZillowDataSource,
        location: str,
        filters: Optional[Dict[str, Any]],
        max_results: int
    ) -> List[PropertyData]:
        """Search with specific data source"""

        if source == ZillowDataSource.HASDATA:
            return await self._search_hasdata(location, filters, max_results)
        elif source == ZillowDataSource.APIFY:
            return await self._search_apify(location, filters, max_results)
        elif source == ZillowDataSource.ZENROWS:
            return await self._search_zenrows(location, filters, max_results)
        elif source == ZillowDataSource.DEMO:
            return self._get_demo_properties(location, filters, max_results)
        else:
            raise ValueError(f"Unsupported data source: {source}")

    async def _search_hasdata(
        self,
        location: str,
        filters: Optional[Dict[str, Any]],
        max_results: int
    ) -> List[PropertyData]:
        """Search using HasData Zillow API"""

        if not self.api_keys.get('hasdata'):
            raise ValueError("HasData API key not configured")

        url = "https://api.hasdata.com/zillow/search"
        headers = {
            "Authorization": f"Bearer {self.api_keys['hasdata']}",
            "Content-Type": "application/json"
        }

        payload = {
            "location": location,
            "max_results": max_results
        }

        if filters:
            payload.update(filters)

        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return [self._parse_hasdata_property(prop) for prop in data.get('properties', [])]
            else:
                raise Exception(f"HasData API error: {response.status}")

    async def _search_apify(
        self,
        location: str,
        filters: Optional[Dict[str, Any]],
        max_results: int
    ) -> List[PropertyData]:
        """Search using Apify Zillow scraper"""

        if not self.api_keys.get('apify'):
            raise ValueError("Apify API key not configured")

        # Apify implementation would go here
        # For now, return empty list
        logger.warning("Apify integration not yet implemented")
        return []

    async def _search_zenrows(
        self,
        location: str,
        filters: Optional[Dict[str, Any]],
        max_results: int
    ) -> List[PropertyData]:
        """Search using ZenRows Zillow scraper"""

        if not self.api_keys.get('zenrows'):
            raise ValueError("ZenRows API key not configured")

        # ZenRows implementation would go here
        logger.warning("ZenRows integration not yet implemented")
        return []

    def _get_demo_properties(
        self,
        location: str,
        filters: Optional[Dict[str, Any]],
        max_results: int
    ) -> List[PropertyData]:
        """Return demo property data"""

        base_properties = [
            PropertyData(
                zpid="123456789",
                address="123 Main St",
                city="Austin",
                state="TX",
                zipcode="78701",
                price=750000,
                zestimate=765000,
                bedrooms=3,
                bathrooms=2.5,
                sqft=2100,
                lot_size=7200,
                year_built=2018,
                property_type="Single Family",
                listing_status="For Sale",
                days_on_market=15,
                neighborhood="Downtown",
                school_rating=8,
                walkability_score=85,
                lat=30.2672,
                lon=-97.7431,
                photos=["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"],
                listing_agent="Sarah Mitchell",
                description="Beautiful modern home in prime downtown location"
            ),
            PropertyData(
                zpid="987654321",
                address="456 Oak Ave",
                city="Austin",
                state="TX",
                zipcode="78702",
                price=525000,
                zestimate=510000,
                bedrooms=2,
                bathrooms=2.0,
                sqft=1650,
                lot_size=5400,
                year_built=2015,
                property_type="Townhouse",
                listing_status="For Sale",
                days_on_market=8,
                neighborhood="East Austin",
                school_rating=7,
                walkability_score=78,
                lat=30.2700,
                lon=-97.7300,
                photos=["https://example.com/photo3.jpg"],
                listing_agent="Mike Rodriguez",
                description="Stylish townhome in trendy East Austin neighborhood"
            ),
            PropertyData(
                zpid="456789123",
                address="789 Hill Dr",
                city="Austin",
                state="TX",
                zipcode="78703",
                price=1250000,
                zestimate=1275000,
                bedrooms=4,
                bathrooms=3.5,
                sqft=3200,
                lot_size=12000,
                year_built=2020,
                property_type="Single Family",
                listing_status="For Sale",
                days_on_market=22,
                neighborhood="Westlake",
                school_rating=9,
                walkability_score=65,
                lat=30.2500,
                lon=-97.7800,
                photos=["https://example.com/photo4.jpg", "https://example.com/photo5.jpg"],
                listing_agent="Jennifer Lee",
                description="Luxury estate with hill country views"
            )
        ]

        # Filter based on location and criteria
        filtered_properties = []
        for prop in base_properties:
            # Simple location matching
            if location.lower() in prop.city.lower() or location.lower() in prop.zipcode:
                # Apply filters if provided
                if filters:
                    if filters.get('min_price') and prop.price < filters['min_price']:
                        continue
                    if filters.get('max_price') and prop.price > filters['max_price']:
                        continue
                    if filters.get('min_beds') and prop.bedrooms < filters['min_beds']:
                        continue
                    if filters.get('max_beds') and prop.bedrooms > filters['max_beds']:
                        continue

                filtered_properties.append(prop)

        return filtered_properties[:max_results]

    async def _get_property_details_with_source(
        self,
        source: ZillowDataSource,
        zpid: str
    ) -> Optional[PropertyData]:
        """Get property details from specific source"""

        if source == ZillowDataSource.DEMO:
            # Return demo property if zpid matches
            demo_props = self._get_demo_properties("", None, 10)
            for prop in demo_props:
                if prop.zpid == zpid:
                    return prop
            return None

        # Other sources would be implemented here
        return None

    async def _get_market_analysis_with_source(
        self,
        source: ZillowDataSource,
        area: str
    ) -> Optional[MarketAnalysis]:
        """Get market analysis from specific source"""

        if source == ZillowDataSource.DEMO:
            return self._get_demo_market_analysis(area)

        # Other sources would be implemented here
        return None

    def _get_demo_market_analysis(self, area: str) -> MarketAnalysis:
        """Return demo market analysis"""

        return MarketAnalysis(
            area=area,
            median_price=650000,
            price_change_30d=2.3,
            price_change_1y=8.7,
            inventory_level="Low",
            median_days_on_market=25,
            price_per_sqft_median=295,
            home_value_index=325,
            forecast_change_1y=5.2
        )

    def _parse_hasdata_property(self, data: Dict[str, Any]) -> PropertyData:
        """Parse property data from HasData API response"""

        return PropertyData(
            zpid=str(data.get('zpid', '')),
            address=data.get('address', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            zipcode=data.get('zipcode', ''),
            price=data.get('price'),
            zestimate=data.get('zestimate'),
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'),
            sqft=data.get('livingArea'),
            lot_size=data.get('lotAreaValue'),
            year_built=data.get('yearBuilt'),
            property_type=data.get('homeType'),
            listing_status=data.get('homeStatus'),
            days_on_market=data.get('daysOnZillow'),
            neighborhood=data.get('neighborhood'),
            lat=data.get('latitude'),
            lon=data.get('longitude'),
            photos=data.get('photos', []),
            description=data.get('description')
        )

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and not expired"""
        if key not in self.cache:
            return False

        cached_time = self.cache[key]['timestamp']
        return datetime.now() - cached_time < timedelta(seconds=self.cache_ttl)

    def _cache_data(self, key: str, data: Any):
        """Cache data with timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "total_cached_items": len(self.cache),
            "cache_ttl_seconds": self.cache_ttl,
            "preferred_source": self.preferred_source.value,
            "available_sources": [source.value for source in [self.preferred_source] + self.fallback_sources],
            "api_keys_configured": {
                key: bool(value) for key, value in self.api_keys.items()
            }
        }


# Global instance for easy access
zillow_service = ZillowIntegrationService()


# Convenience functions
async def search_zillow_properties(
    location: str,
    filters: Optional[Dict[str, Any]] = None,
    max_results: int = 20
) -> List[PropertyData]:
    """Convenience function to search Zillow properties"""
    async with zillow_service:
        return await zillow_service.search_properties(location, filters, max_results)


async def get_zillow_property(zpid: str) -> Optional[PropertyData]:
    """Convenience function to get property details"""
    async with zillow_service:
        return await zillow_service.get_property_details(zpid)


async def get_zillow_market_data(area: str) -> Optional[MarketAnalysis]:
    """Convenience function to get market analysis"""
    async with zillow_service:
        return await zillow_service.get_market_analysis(area)