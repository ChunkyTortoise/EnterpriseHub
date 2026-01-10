"""
Redfin Integration Service

Handles property data retrieval from Redfin through third-party providers:
- HasData Redfin API
- ScrapingBee Redfin Scraper
- Oxylabs Redfin Data
- Fallback to demo data

Provides real estate property information with focus on market trends and pricing data.
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


class RedfinDataSource(Enum):
    """Available Redfin data sources"""
    HASDATA = "hasdata"
    SCRAPINGBEE = "scrapingbee"
    OXYLABS = "oxylabs"
    DECODO = "decodo"
    DEMO = "demo"


@dataclass
class RedfinPropertyData:
    """Structure for property information from Redfin"""
    property_id: str
    address: str
    city: str
    state: str
    zipcode: str
    price: Optional[int] = None
    price_per_sqft: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    listing_status: Optional[str] = None
    days_on_market: Optional[int] = None
    listing_date: Optional[datetime] = None
    price_history: List[Dict[str, Any]] = None
    neighborhood: Optional[str] = None
    walk_score: Optional[int] = None
    transit_score: Optional[int] = None
    bike_score: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    photos: List[str] = None
    virtual_tour_url: Optional[str] = None
    listing_agent: Optional[str] = None
    brokerage: Optional[str] = None
    description: Optional[str] = None
    hoa_fees: Optional[int] = None
    property_taxes: Optional[int] = None
    parking_spots: Optional[int] = None
    has_garage: Optional[bool] = None
    has_pool: Optional[bool] = None
    last_updated: datetime = datetime.now()

    def __post_init__(self):
        if self.price_history is None:
            self.price_history = []
        if self.photos is None:
            self.photos = []

        # Calculate price per sqft if missing
        if self.price and self.sqft and not self.price_per_sqft:
            self.price_per_sqft = round(self.price / self.sqft, 2)


@dataclass
class RedfinMarketData:
    """Market trends and analytics from Redfin"""
    area: str
    median_sale_price: Optional[int] = None
    median_list_price: Optional[int] = None
    price_change_mom: Optional[float] = None  # Month over month
    price_change_yoy: Optional[float] = None  # Year over year
    homes_sold: Optional[int] = None
    new_listings: Optional[int] = None
    inventory_level: Optional[int] = None
    months_of_supply: Optional[float] = None
    median_dom: Optional[int] = None  # Days on market
    list_to_sale_ratio: Optional[float] = None
    pending_sales: Optional[int] = None
    price_drops: Optional[int] = None
    tour_insights: Dict[str, Any] = None
    buyer_demand_score: Optional[int] = None
    competitiveness_score: Optional[int] = None
    last_updated: datetime = datetime.now()

    def __post_init__(self):
        if self.tour_insights is None:
            self.tour_insights = {}


@dataclass
class RedfinNeighborhoodInsights:
    """Neighborhood insights from Redfin"""
    neighborhood: str
    city: str
    state: str
    median_home_price: Optional[int] = None
    price_trend_1m: Optional[float] = None
    price_trend_3m: Optional[float] = None
    price_trend_1y: Optional[float] = None
    homes_for_sale: Optional[int] = None
    homes_recently_sold: Optional[int] = None
    median_days_on_market: Optional[int] = None
    walkability: Optional[int] = None
    transit_access: Optional[int] = None
    bike_friendly: Optional[int] = None
    crime_score: Optional[str] = None
    school_quality: Optional[int] = None
    restaurants_nearby: Optional[int] = None
    shopping_score: Optional[int] = None
    demographics: Dict[str, Any] = None
    last_updated: datetime = datetime.now()

    def __post_init__(self):
        if self.demographics is None:
            self.demographics = {}


class RedfinIntegrationService:
    """
    Comprehensive Redfin integration service with multiple data sources.

    Provides property data, market insights, and neighborhood analytics
    specifically focused on Redfin's proprietary market data and trends.
    """

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_keys = {
            'hasdata': getattr(settings, 'hasdata_api_key', None),
            'scrapingbee': getattr(settings, 'scrapingbee_api_key', None),
            'oxylabs': getattr(settings, 'oxylabs_api_key', None),
            'decodo': getattr(settings, 'decodo_api_key', None)
        }
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 3600  # 1 hour cache
        self.preferred_source = RedfinDataSource.HASDATA
        self.fallback_sources = [
            RedfinDataSource.SCRAPINGBEE,
            RedfinDataSource.OXYLABS,
            RedfinDataSource.DEMO
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
    ) -> List[RedfinPropertyData]:
        """
        Search for properties on Redfin in a given location.

        Args:
            location: City, ZIP, or address to search
            filters: Price range, property type, etc.
            max_results: Maximum number of properties to return

        Returns:
            List of RedfinPropertyData objects
        """
        cache_key = f"redfin_search_{location}_{json.dumps(filters or {}, sort_keys=True)}_{max_results}"

        # Check cache first
        if self._is_cached(cache_key):
            logger.info(f"Returning cached Redfin search for {location}")
            return self.cache[cache_key]['data']

        try:
            # Try preferred source first
            properties = await self._search_with_source(
                self.preferred_source, location, filters, max_results
            )

            if properties:
                self._cache_data(cache_key, properties)
                logger.info(f"Found {len(properties)} Redfin properties in {location} via {self.preferred_source.value}")
                return properties

        except Exception as e:
            logger.warning(f"Primary Redfin source {self.preferred_source.value} failed: {str(e)}")

        # Try fallback sources
        for source in self.fallback_sources:
            try:
                properties = await self._search_with_source(
                    source, location, filters, max_results
                )
                if properties:
                    self._cache_data(cache_key, properties)
                    logger.info(f"Found {len(properties)} Redfin properties in {location} via fallback {source.value}")
                    return properties
            except Exception as e:
                logger.warning(f"Redfin fallback source {source.value} failed: {str(e)}")
                continue

        # Return demo data if all sources fail
        return self._get_demo_redfin_properties(location, filters, max_results)

    async def get_property_details(self, property_id: str) -> Optional[RedfinPropertyData]:
        """
        Get detailed information for a specific Redfin property.

        Args:
            property_id: Redfin property identifier

        Returns:
            RedfinPropertyData object with detailed information
        """
        cache_key = f"redfin_property_{property_id}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            property_data = await self._get_property_details_with_source(
                self.preferred_source, property_id
            )

            if property_data:
                self._cache_data(cache_key, property_data)
                return property_data

        except Exception as e:
            logger.warning(f"Primary source failed for Redfin property {property_id}: {str(e)}")

        # Try fallback sources
        for source in self.fallback_sources:
            try:
                property_data = await self._get_property_details_with_source(source, property_id)
                if property_data:
                    self._cache_data(cache_key, property_data)
                    return property_data
            except Exception as e:
                logger.warning(f"Redfin fallback source {source.value} failed for property {property_id}: {str(e)}")
                continue

        return None

    async def get_market_data(self, area: str) -> Optional[RedfinMarketData]:
        """
        Get Redfin market data for a specific area.

        Args:
            area: City, ZIP, or region name

        Returns:
            RedfinMarketData object
        """
        cache_key = f"redfin_market_{area}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            market_data = await self._get_market_data_with_source(
                self.preferred_source, area
            )

            if market_data:
                self._cache_data(cache_key, market_data)
                return market_data

        except Exception as e:
            logger.warning(f"Redfin market data failed for {area}: {str(e)}")

        # Return demo market data
        return self._get_demo_market_data(area)

    async def get_neighborhood_insights(self, neighborhood: str, city: str, state: str) -> Optional[RedfinNeighborhoodInsights]:
        """
        Get neighborhood insights from Redfin.

        Args:
            neighborhood: Neighborhood name
            city: City name
            state: State abbreviation

        Returns:
            RedfinNeighborhoodInsights object
        """
        cache_key = f"redfin_neighborhood_{neighborhood}_{city}_{state}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            insights = await self._get_neighborhood_insights_with_source(
                self.preferred_source, neighborhood, city, state
            )

            if insights:
                self._cache_data(cache_key, insights)
                return insights

        except Exception as e:
            logger.warning(f"Redfin neighborhood insights failed for {neighborhood}: {str(e)}")

        # Return demo insights
        return self._get_demo_neighborhood_insights(neighborhood, city, state)

    async def _search_with_source(
        self,
        source: RedfinDataSource,
        location: str,
        filters: Optional[Dict[str, Any]],
        max_results: int
    ) -> List[RedfinPropertyData]:
        """Search with specific data source"""

        if source == RedfinDataSource.HASDATA:
            return await self._search_hasdata_redfin(location, filters, max_results)
        elif source == RedfinDataSource.SCRAPINGBEE:
            return await self._search_scrapingbee_redfin(location, filters, max_results)
        elif source == RedfinDataSource.OXYLABS:
            return await self._search_oxylabs_redfin(location, filters, max_results)
        elif source == RedfinDataSource.DEMO:
            return self._get_demo_redfin_properties(location, filters, max_results)
        else:
            raise ValueError(f"Unsupported Redfin data source: {source}")

    async def _search_hasdata_redfin(
        self,
        location: str,
        filters: Optional[Dict[str, Any]],
        max_results: int
    ) -> List[RedfinPropertyData]:
        """Search using HasData Redfin API"""

        if not self.api_keys.get('hasdata'):
            raise ValueError("HasData API key not configured")

        url = "https://api.hasdata.com/redfin/search"
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
                return [self._parse_hasdata_redfin_property(prop) for prop in data.get('properties', [])]
            else:
                raise Exception(f"HasData Redfin API error: {response.status}")

    async def _search_scrapingbee_redfin(
        self,
        location: str,
        filters: Optional[Dict[str, Any]],
        max_results: int
    ) -> List[RedfinPropertyData]:
        """Search using ScrapingBee Redfin scraper"""

        if not self.api_keys.get('scrapingbee'):
            raise ValueError("ScrapingBee API key not configured")

        # ScrapingBee implementation would go here
        logger.warning("ScrapingBee Redfin integration not yet implemented")
        return []

    async def _search_oxylabs_redfin(
        self,
        location: str,
        filters: Optional[Dict[str, Any]],
        max_results: int
    ) -> List[RedfinPropertyData]:
        """Search using Oxylabs Redfin data"""

        if not self.api_keys.get('oxylabs'):
            raise ValueError("Oxylabs API key not configured")

        # Oxylabs implementation would go here
        logger.warning("Oxylabs Redfin integration not yet implemented")
        return []

    def _get_demo_redfin_properties(
        self,
        location: str,
        filters: Optional[Dict[str, Any]],
        max_results: int
    ) -> List[RedfinPropertyData]:
        """Return demo Redfin property data"""

        base_properties = [
            RedfinPropertyData(
                property_id="rf_001",
                address="789 Maple Street",
                city="Austin",
                state="TX",
                zipcode="78701",
                price=695000,
                price_per_sqft=331,
                bedrooms=3,
                bathrooms=2.0,
                sqft=2100,
                lot_size=6500,
                year_built=2017,
                property_type="Single Family Home",
                listing_status="Active",
                days_on_market=12,
                listing_date=datetime.now() - timedelta(days=12),
                price_history=[
                    {"date": "2024-01-15", "price": 710000, "event": "Listed"},
                    {"date": "2024-01-30", "price": 695000, "event": "Price Drop"}
                ],
                neighborhood="Zilker",
                walk_score=92,
                transit_score=78,
                bike_score=85,
                lat=30.2642,
                lon=-97.7611,
                photos=["https://example.com/rf1.jpg"],
                listing_agent="Amanda Chen",
                brokerage="Redfin Corporation",
                description="Modern home with energy-efficient features",
                property_taxes=8500,
                parking_spots=2,
                has_garage=True,
                has_pool=False
            ),
            RedfinPropertyData(
                property_id="rf_002",
                address="456 Cedar Lane",
                city="Austin",
                state="TX",
                zipcode="78704",
                price=485000,
                price_per_sqft=290,
                bedrooms=2,
                bathrooms=2.5,
                sqft=1672,
                lot_size=4200,
                year_built=2019,
                property_type="Townhome",
                listing_status="Active",
                days_on_market=6,
                listing_date=datetime.now() - timedelta(days=6),
                price_history=[
                    {"date": "2024-01-03", "price": 485000, "event": "Listed"}
                ],
                neighborhood="South Austin",
                walk_score=78,
                transit_score=65,
                bike_score=82,
                lat=30.2500,
                lon=-97.7600,
                photos=["https://example.com/rf2.jpg", "https://example.com/rf2b.jpg"],
                listing_agent="David Park",
                brokerage="Redfin Corporation",
                description="Contemporary townhome with rooftop deck",
                hoa_fees=150,
                property_taxes=5800,
                parking_spots=1,
                has_garage=False,
                has_pool=False
            ),
            RedfinPropertyData(
                property_id="rf_003",
                address="321 Pine Ridge",
                city="Austin",
                state="TX",
                zipcode="78746",
                price=1150000,
                price_per_sqft=359,
                bedrooms=4,
                bathrooms=3.5,
                sqft=3200,
                lot_size=15000,
                year_built=2021,
                property_type="Single Family Home",
                listing_status="Active",
                days_on_market=28,
                listing_date=datetime.now() - timedelta(days=28),
                price_history=[
                    {"date": "2023-12-12", "price": 1225000, "event": "Listed"},
                    {"date": "2023-12-28", "price": 1175000, "event": "Price Drop"},
                    {"date": "2024-01-08", "price": 1150000, "event": "Price Drop"}
                ],
                neighborhood="Westlake Hills",
                walk_score=45,
                transit_score=25,
                bike_score=35,
                lat=30.2800,
                lon=-97.8200,
                photos=["https://example.com/rf3.jpg"],
                virtual_tour_url="https://example.com/tour3",
                listing_agent="Jessica Martinez",
                brokerage="Redfin Corporation",
                description="Luxury home with Hill Country views and pool",
                property_taxes=14500,
                parking_spots=3,
                has_garage=True,
                has_pool=True
            )
        ]

        # Filter and return properties
        filtered_properties = []
        for prop in base_properties:
            if location.lower() in prop.city.lower() or location.lower() in prop.zipcode:
                # Apply filters if provided
                if filters:
                    if filters.get('min_price') and prop.price < filters['min_price']:
                        continue
                    if filters.get('max_price') and prop.price > filters['max_price']:
                        continue
                    if filters.get('min_beds') and prop.bedrooms < filters['min_beds']:
                        continue

                filtered_properties.append(prop)

        return filtered_properties[:max_results]

    def _get_demo_market_data(self, area: str) -> RedfinMarketData:
        """Return demo Redfin market data"""

        return RedfinMarketData(
            area=area,
            median_sale_price=620000,
            median_list_price=635000,
            price_change_mom=1.8,
            price_change_yoy=6.2,
            homes_sold=245,
            new_listings=198,
            inventory_level=1250,
            months_of_supply=2.1,
            median_dom=18,
            list_to_sale_ratio=0.97,
            pending_sales=89,
            price_drops=42,
            tour_insights={
                "most_toured_day": "Saturday",
                "avg_tours_per_property": 8.5,
                "virtual_tour_engagement": "High"
            },
            buyer_demand_score=78,
            competitiveness_score=85
        )

    def _get_demo_neighborhood_insights(
        self,
        neighborhood: str,
        city: str,
        state: str
    ) -> RedfinNeighborhoodInsights:
        """Return demo neighborhood insights"""

        return RedfinNeighborhoodInsights(
            neighborhood=neighborhood,
            city=city,
            state=state,
            median_home_price=575000,
            price_trend_1m=2.1,
            price_trend_3m=4.8,
            price_trend_1y=7.3,
            homes_for_sale=45,
            homes_recently_sold=38,
            median_days_on_market=22,
            walkability=82,
            transit_access=68,
            bike_friendly=75,
            crime_score="B+",
            school_quality=8,
            restaurants_nearby=125,
            shopping_score=87,
            demographics={
                "median_age": 34,
                "avg_household_income": 95000,
                "college_educated_pct": 78,
                "families_with_children_pct": 42
            }
        )

    async def _get_property_details_with_source(
        self,
        source: RedfinDataSource,
        property_id: str
    ) -> Optional[RedfinPropertyData]:
        """Get property details from specific source"""

        if source == RedfinDataSource.DEMO:
            # Return demo property if ID matches
            demo_props = self._get_demo_redfin_properties("", None, 10)
            for prop in demo_props:
                if prop.property_id == property_id:
                    return prop
            return None

        # Other sources would be implemented here
        return None

    async def _get_market_data_with_source(
        self,
        source: RedfinDataSource,
        area: str
    ) -> Optional[RedfinMarketData]:
        """Get market data from specific source"""

        if source == RedfinDataSource.DEMO:
            return self._get_demo_market_data(area)

        # Other sources would be implemented here
        return None

    async def _get_neighborhood_insights_with_source(
        self,
        source: RedfinDataSource,
        neighborhood: str,
        city: str,
        state: str
    ) -> Optional[RedfinNeighborhoodInsights]:
        """Get neighborhood insights from specific source"""

        if source == RedfinDataSource.DEMO:
            return self._get_demo_neighborhood_insights(neighborhood, city, state)

        # Other sources would be implemented here
        return None

    def _parse_hasdata_redfin_property(self, data: Dict[str, Any]) -> RedfinPropertyData:
        """Parse property data from HasData Redfin API response"""

        return RedfinPropertyData(
            property_id=str(data.get('property_id', '')),
            address=data.get('address', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            zipcode=data.get('zipcode', ''),
            price=data.get('price'),
            price_per_sqft=data.get('price_per_sqft'),
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'),
            sqft=data.get('sqft'),
            lot_size=data.get('lot_size'),
            year_built=data.get('year_built'),
            property_type=data.get('property_type'),
            listing_status=data.get('listing_status'),
            days_on_market=data.get('days_on_market'),
            neighborhood=data.get('neighborhood'),
            walk_score=data.get('walk_score'),
            lat=data.get('latitude'),
            lon=data.get('longitude'),
            photos=data.get('photos', []),
            listing_agent=data.get('agent_name'),
            brokerage=data.get('brokerage'),
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
redfin_service = RedfinIntegrationService()


# Convenience functions
async def search_redfin_properties(
    location: str,
    filters: Optional[Dict[str, Any]] = None,
    max_results: int = 20
) -> List[RedfinPropertyData]:
    """Convenience function to search Redfin properties"""
    async with redfin_service:
        return await redfin_service.search_properties(location, filters, max_results)


async def get_redfin_property(property_id: str) -> Optional[RedfinPropertyData]:
    """Convenience function to get Redfin property details"""
    async with redfin_service:
        return await redfin_service.get_property_details(property_id)


async def get_redfin_market_data(area: str) -> Optional[RedfinMarketData]:
    """Convenience function to get Redfin market analysis"""
    async with redfin_service:
        return await redfin_service.get_market_data(area)


async def get_redfin_neighborhood_insights(
    neighborhood: str,
    city: str,
    state: str
) -> Optional[RedfinNeighborhoodInsights]:
    """Convenience function to get neighborhood insights"""
    async with redfin_service:
        return await redfin_service.get_neighborhood_insights(neighborhood, city, state)