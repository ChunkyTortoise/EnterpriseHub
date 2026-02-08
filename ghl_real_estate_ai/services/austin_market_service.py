"""
Rancho Cucamonga Market Data Service - Real-time MLS integration and market intelligence.

Provides comprehensive Austin Metropolitan Area real estate market data including:
- MLS property listings and market trends
- School district ratings and boundary mapping (Etiwanda, Central Elementary)
- Neighborhood analytics and demographics
- Corporate relocation data for logistics/healthcare workers
- Market timing and inventory analysis
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class PropertyType(Enum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOME = "townhome"
    LAND = "land"
    MULTI_FAMILY = "multi_family"


class MarketCondition(Enum):
    STRONG_SELLERS = "strong_sellers"
    BALANCED = "balanced"
    STRONG_BUYERS = "strong_buyers"
    TRANSITIONING = "transitioning"


@dataclass
class RanchoCucamongaNeighborhood:
    """Rancho Cucamonga neighborhood with comprehensive market data."""

    name: str
    zone: str  # Central RC, Alta Loma, Etiwanda, North RC, South RC
    median_price: float
    price_trend_3m: float  # Percentage change
    inventory_days: int
    school_rating: float
    walkability_score: int
    logistics_healthcare_appeal: float  # 0-100 score for logistics/healthcare workers
    corporate_proximity: Dict[str, float]  # Company name -> commute minutes
    amenities: List[str]
    demographics: Dict[str, Any]
    market_condition: MarketCondition


@dataclass
class PropertyListing:
    """Austin Metropolitan Area MLS property listing."""

    mls_id: str
    address: str
    price: float
    beds: int
    baths: float
    sqft: int
    lot_size: Optional[float]
    year_built: int
    property_type: PropertyType
    neighborhood: str
    school_district: str
    days_on_market: int
    price_per_sqft: float
    price_changes: List[Dict[str, Any]]
    features: List[str]
    coordinates: Tuple[float, float]
    photos: List[str]
    description: str
    listing_agent: Dict[str, Any]
    last_updated: datetime


@dataclass
class MarketMetrics:
    """Austin Metropolitan Area market performance metrics."""

    median_price: float
    average_days_on_market: int
    inventory_count: int
    months_supply: float
    price_trend_1m: float
    price_trend_3m: float
    price_trend_1y: float
    new_listings_7d: int
    closed_sales_30d: int
    pending_sales: int
    absorption_rate: float
    market_condition: MarketCondition


class AustinMarketService:
    """
    Comprehensive Austin Metropolitan Area real estate market intelligence service.

    Integrates with MLS data, school ratings, corporate data,
    and provides real-time market analysis for the Austin Tech Hub.
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.neighborhoods = self._load_neighborhood_data()
        self.corporate_hqs = self._load_corporate_headquarters()

    async def get_market_metrics(
        self,
        neighborhood: Optional[str] = None,
        property_type: Optional[PropertyType] = None,
        price_range: Optional[Tuple[float, float]] = None,
    ) -> MarketMetrics:
        """Get real-time Austin Metropolitan Area market metrics with optional filtering."""
        cache_key = f"market_metrics:{neighborhood}:{property_type}:{price_range}"

        # Try cache first (5-minute TTL for market data)
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for market metrics: {cache_key}")
            return MarketMetrics(**cached)

        # Fetch fresh market data
        metrics = await self._fetch_market_metrics(neighborhood, property_type, price_range)

        # Cache for 5 minutes
        await self.cache.set(cache_key, metrics.__dict__, ttl=300)
        logger.info(f"Fetched fresh market metrics for {neighborhood or 'Rancho Cucamonga'}")

        return metrics

    async def search_properties(self, criteria: Dict[str, Any], limit: int = 50) -> List[PropertyListing]:
        """
        Search Austin Metropolitan Area MLS properties with comprehensive criteria.

        Args:
            criteria: Search criteria including price, beds, baths, neighborhood, etc.
            limit: Maximum number of properties to return
        """
        cache_key = f"property_search:{hash(str(sorted(criteria.items())))}"

        # Try cache first (10-minute TTL for property searches)
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for property search: {len(cached)} properties")
            return [PropertyListing(**p) for p in cached]

        # Fetch properties from MLS
        properties = await self._search_mls_properties(criteria, limit)

        # Cache for 10 minutes
        await self.cache.set(cache_key, [p.__dict__ for p in properties], ttl=600)
        logger.info(f"Fetched {len(properties)} properties from MLS")

        return properties

    async def get_neighborhood_analysis(self, neighborhood: str) -> Optional[RanchoCucamongaNeighborhood]:
        """Get comprehensive neighborhood analysis."""
        cache_key = f"neighborhood_analysis:{neighborhood.lower()}"

        # Try cache first (1-hour TTL for neighborhood data)
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for neighborhood: {neighborhood}")
            return RanchoCucamongaNeighborhood(**cached)

        # Get neighborhood data
        neighborhood_data = self.neighborhoods.get(neighborhood.lower())
        if not neighborhood_data:
            logger.warning(f"Neighborhood not found: {neighborhood}")
            return None

        # Enhance with real-time market data
        enhanced = await self._enhance_neighborhood_data(neighborhood_data)

        # Cache for 1 hour
        await self.cache.set(cache_key, enhanced.__dict__, ttl=3600)
        logger.info(f"Enhanced neighborhood analysis for {neighborhood}")

        return enhanced

    async def get_school_district_info(self, district_name: str) -> Dict[str, Any]:
        """Get detailed school district information and ratings."""
        cache_key = f"school_district:{district_name.lower()}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Fetch school district data
        district_info = await self._fetch_school_district_data(district_name)

        # Cache for 24 hours (school data changes slowly)
        await self.cache.set(cache_key, district_info, ttl=86400)

        return district_info

    async def get_corporate_relocation_insights(
        self, employer: Optional[str] = None, position_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get insights for corporate relocations to Austin Metropolitan Area.

        Focuses on Amazon, Kaiser Permanente, FedEx, UPS, and other major employers.
        """
        cache_key = f"corporate_insights:{employer}:{position_level}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        insights = await self._generate_corporate_insights(employer, position_level)

        # Cache for 6 hours
        await self.cache.set(cache_key, insights, ttl=21600)

        return insights

    async def get_commute_analysis(self, property_coords: Tuple[float, float], work_location: str) -> Dict[str, Any]:
        """Analyze commute times and routes from property to work location."""
        cache_key = f"commute:{property_coords}:{work_location}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        commute_data = await self._calculate_commute_analysis(property_coords, work_location)

        # Cache for 12 hours (traffic patterns are relatively stable)
        await self.cache.set(cache_key, commute_data, ttl=43200)

        return commute_data

    async def get_market_timing_advice(
        self,
        transaction_type: str,  # "buy" or "sell"
        property_type: PropertyType,
        neighborhood: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get market timing recommendations for Austin Metropolitan Area market."""
        current_metrics = await self.get_market_metrics(neighborhood, property_type)

        advice = {
            "timing_score": 0,  # 0-100, higher = better time
            "market_condition": current_metrics.market_condition.value,
            "recommendations": [],
            "seasonal_factors": self._get_seasonal_factors(),
            "urgency_level": "low",  # low, medium, high
        }

        # Analyze market conditions for timing
        if transaction_type == "buy":
            advice.update(self._analyze_buy_timing(current_metrics))
        else:
            advice.update(self._analyze_sell_timing(current_metrics))

        return advice

    def _load_neighborhood_data(self) -> Dict[str, Dict[str, Any]]:
        """Load Rancho Cucamonga neighborhood base data."""
        return {
            "alta_loma": {
                "name": "Alta Loma",
                "zone": "Central",
                "median_price": 1100000,
                "school_rating": 8.9,
                "walkability_score": 45,
                "logistics_healthcare_appeal": 75,
                "amenities": [
                    "Victoria Gardens",
                    "Alta Loma Community Center",
                    "Red Hill Country Club",
                    "Luxury Homes",
                ],
                "demographics": {"age_median": 42, "income_median": 125000, "logistics_healthcare": 0.25},
            },
            "etiwanda": {
                "name": "Etiwanda",
                "zone": "North",
                "median_price": 950000,
                "school_rating": 9.3,
                "walkability_score": 55,
                "logistics_healthcare_appeal": 90,
                "amenities": ["Etiwanda Creek Park", "Top Schools", "Family Communities", "Day Creek Golf Course"],
                "demographics": {"age_median": 38, "income_median": 115000, "logistics_healthcare": 0.35},
            },
            "central_rc": {
                "name": "Central Rancho Cucamonga",
                "zone": "Central",
                "median_price": 750000,
                "school_rating": 8.1,
                "walkability_score": 65,
                "logistics_healthcare_appeal": 85,
                "amenities": ["Victoria Gardens Mall", "Central Park", "Restaurants", "Shopping Centers"],
                "demographics": {"age_median": 35, "income_median": 95000, "logistics_healthcare": 0.30},
            },
            "north_rc": {
                "name": "North Rancho Cucamonga",
                "zone": "North",
                "median_price": 850000,
                "school_rating": 8.7,
                "walkability_score": 50,
                "logistics_healthcare_appeal": 80,
                "amenities": ["Lewis Family Playfields", "New Construction", "Commuter Friendly", "Family Oriented"],
                "demographics": {"age_median": 36, "income_median": 105000, "logistics_healthcare": 0.28},
            },
            "south_rc": {
                "name": "South Rancho Cucamonga",
                "zone": "South",
                "median_price": 680000,
                "school_rating": 7.8,
                "walkability_score": 60,
                "logistics_healthcare_appeal": 88,
                "amenities": ["Cucamonga Peak Trail", "Historic Route 66", "Starter Homes", "Commuter Access"],
                "demographics": {"age_median": 32, "income_median": 85000, "logistics_healthcare": 0.40},
            },
            "victoria_gardens": {
                "name": "Victoria Gardens Area",
                "zone": "Central",
                "median_price": 820000,
                "school_rating": 8.5,
                "walkability_score": 75,
                "logistics_healthcare_appeal": 82,
                "amenities": ["Victoria Gardens Mall", "Dining", "Entertainment", "Shopping"],
                "demographics": {"age_median": 34, "income_median": 98000, "logistics_healthcare": 0.32},
            },
            "terra_vista": {
                "name": "Terra Vista",
                "zone": "West",
                "median_price": 1050000,
                "school_rating": 9.1,
                "walkability_score": 40,
                "logistics_healthcare_appeal": 70,
                "amenities": ["Luxury Homes", "Golf Course Views", "Gated Communities", "Mountain Views"],
                "demographics": {"age_median": 45, "income_median": 165000, "logistics_healthcare": 0.20},
            },
            "day_creek": {
                "name": "Day Creek",
                "zone": "East",
                "median_price": 780000,
                "school_rating": 8.3,
                "walkability_score": 55,
                "logistics_healthcare_appeal": 85,
                "amenities": ["Day Creek Golf Course", "Family Neighborhoods", "Parks", "Schools"],
                "demographics": {"age_median": 37, "income_median": 108000, "logistics_healthcare": 0.30},
            },
        }

    def _load_corporate_headquarters(self) -> Dict[str, Dict[str, Any]]:
        """Load major corporate headquarters and employers in Austin Metropolitan Area."""
        return {
            "amazon_logistics": {
                "name": "Amazon Fulfillment Centers",
                "location": "Rancho Cucamonga/Ontario",
                "coordinates": (34.106389, -117.593056),
                "employees": 12000,
                "expansion_plans": "Continued logistics expansion",
                "avg_salary": 85000,
                "preferred_neighborhoods": ["South RC", "Central RC", "Etiwanda", "North RC"],
            },
            "kaiser_permanente": {
                "name": "Kaiser Permanente",
                "location": "Ontario/Fontana",
                "coordinates": (34.063611, -117.650833),
                "employees": 8500,
                "expansion_plans": "Healthcare expansion across IE",
                "avg_salary": 95000,
                "preferred_neighborhoods": ["Central RC", "Etiwanda", "Alta Loma", "Victoria Gardens"],
            },
            "fedex": {
                "name": "FedEx Ground",
                "location": "Rancho Cucamonga",
                "coordinates": (34.101389, -117.583056),
                "employees": 5000,
                "expansion_plans": "Logistics hub expansion",
                "avg_salary": 75000,
                "preferred_neighborhoods": ["South RC", "Central RC", "North RC", "Day Creek"],
            },
            "ups": {
                "name": "UPS Logistics",
                "location": "Ontario",
                "coordinates": (34.058889, -117.640556),
                "employees": 4500,
                "expansion_plans": "Distribution center growth",
                "avg_salary": 78000,
                "preferred_neighborhoods": ["Central RC", "South RC", "Victoria Gardens", "Day Creek"],
            },
            "san_antonio_regional": {
                "name": "San Antonio Regional Hospital",
                "location": "Upland",
                "coordinates": (34.113333, -117.648889),
                "employees": 3500,
                "expansion_plans": "Healthcare services expansion",
                "avg_salary": 85000,
                "preferred_neighborhoods": ["Etiwanda", "Alta Loma", "Central RC", "Terra Vista"],
            },
            "chino_valley_medical": {
                "name": "Chino Valley Medical Center",
                "location": "Chino",
                "coordinates": (34.025556, -117.688889),
                "employees": 2800,
                "expansion_plans": "Regional healthcare expansion",
                "avg_salary": 90000,
                "preferred_neighborhoods": ["Chino Hills", "South RC", "Central RC", "Day Creek"],
            },
        }

    async def _fetch_market_metrics(
        self,
        neighborhood: Optional[str],
        property_type: Optional[PropertyType],
        price_range: Optional[Tuple[float, float]],
    ) -> MarketMetrics:
        """Fetch real-time market metrics from MLS and market data sources."""
        # Simulate MLS API call - in production, integrate with actual MLS
        # This would connect to Austin Tech Hub MLS or San Bernardino County MLS

        base_metrics = {
            "median_price": 825000,
            "average_days_on_market": 35,
            "inventory_count": 1850,
            "months_supply": 2.1,
            "price_trend_1m": 0.5,
            "price_trend_3m": 2.8,
            "price_trend_1y": 8.5,
            "new_listings_7d": 220,
            "closed_sales_30d": 975,
            "pending_sales": 750,
            "absorption_rate": 82.3,
            "market_condition": MarketCondition.BALANCED,
        }

        # Adjust based on neighborhood
        if neighborhood:
            neighborhood_data = self.neighborhoods.get(neighborhood.lower(), {})
            if neighborhood_data:
                price_multiplier = neighborhood_data.get("median_price", 825000) / 825000
                base_metrics["median_price"] = int(base_metrics["median_price"] * price_multiplier)

        # Adjust based on property type
        if property_type:
            type_adjustments = {
                PropertyType.CONDO: {"median_price": 0.75, "average_days_on_market": 1.2},
                PropertyType.TOWNHOME: {"median_price": 0.85, "average_days_on_market": 0.9},
                PropertyType.LAND: {"median_price": 0.4, "average_days_on_market": 2.5},
                PropertyType.MULTI_FAMILY: {"median_price": 1.8, "average_days_on_market": 1.8},
            }

            adjustments = type_adjustments.get(property_type, {})
            for key, multiplier in adjustments.items():
                if key in base_metrics:
                    base_metrics[key] = int(base_metrics[key] * multiplier)

        return MarketMetrics(**base_metrics)

    async def _search_mls_properties(self, criteria: Dict[str, Any], limit: int) -> List[PropertyListing]:
        """Search MLS properties - integrate with actual MLS API in production."""
        # Simulate MLS search results
        # In production, this would connect to Austin Tech Hub MLS API

        sample_properties = [
            {
                "mls_id": "IE2024001",
                "address": "12345 Haven Avenue, Rancho Cucamonga, CA 91739",
                "price": 950000,
                "beds": 4,
                "baths": 3.0,
                "sqft": 2800,
                "lot_size": 0.25,
                "year_built": 2018,
                "property_type": PropertyType.SINGLE_FAMILY,
                "neighborhood": "Etiwanda",
                "school_district": "Etiwanda School District",
                "days_on_market": 22,
                "price_per_sqft": 339,
                "price_changes": [],
                "features": ["Open Floor Plan", "Modern Kitchen", "Family Friendly", "Top Schools"],
                "coordinates": (34.140833, -117.565278),
                "photos": ["photo1.jpg", "photo2.jpg"],
                "description": "Beautiful family home in prestigious Etiwanda area",
                "listing_agent": {"name": "Jorge Martinez", "phone": "(909) 555-0123"},
                "last_updated": datetime.now(),
            }
        ]

        # Filter based on criteria
        filtered_properties = []
        for prop_data in sample_properties[:limit]:
            # Apply filters
            if criteria.get("min_price") and prop_data["price"] < criteria["min_price"]:
                continue
            if criteria.get("max_price") and prop_data["price"] > criteria["max_price"]:
                continue
            if criteria.get("min_beds") and prop_data["beds"] < criteria["min_beds"]:
                continue
            if criteria.get("neighborhood") and prop_data["neighborhood"].lower() != criteria["neighborhood"].lower():
                continue

            filtered_properties.append(PropertyListing(**prop_data))

        return filtered_properties

    async def _enhance_neighborhood_data(self, base_data: Dict[str, Any]) -> RanchoCucamongaNeighborhood:
        """Enhance neighborhood data with real-time market information."""
        # Get current market metrics for the neighborhood
        metrics = await self.get_market_metrics(base_data["name"])

        # Calculate corporate proximity
        corporate_proximity = {}
        for corp_name, corp_data in self.corporate_hqs.items():
            # Simplified distance calculation - in production use actual routing API
            distance_minutes = 25  # Placeholder
            corporate_proximity[corp_data["name"]] = distance_minutes

        return RanchoCucamongaNeighborhood(
            name=base_data["name"],
            zone=base_data["zone"],
            median_price=metrics.median_price,
            price_trend_3m=metrics.price_trend_3m,
            inventory_days=metrics.average_days_on_market,
            school_rating=base_data["school_rating"],
            walkability_score=base_data["walkability_score"],
            logistics_healthcare_appeal=base_data["logistics_healthcare_appeal"],
            corporate_proximity=corporate_proximity,
            amenities=base_data["amenities"],
            demographics=base_data["demographics"],
            market_condition=metrics.market_condition,
        )

    async def _fetch_school_district_data(self, district_name: str) -> Dict[str, Any]:
        """Fetch comprehensive school district information."""
        # In production, integrate with California Department of Education API
        districts = {
            "etiwanda school district": {
                "name": "Etiwanda School District",
                "rating": 9.3,
                "enrollment": 22000,
                "student_teacher_ratio": 21.5,
                "graduation_rate": 96.8,
                "college_readiness": 88.4,
                "top_schools": [
                    {"name": "Etiwanda High School", "rating": 9.5, "type": "High School"},
                    {"name": "George Washington High School", "rating": 9.2, "type": "High School"},
                    {"name": "Eleanor Roosevelt High School", "rating": 9.0, "type": "High School"},
                ],
                "special_programs": ["AVID", "AP", "STEM", "Dual Enrollment"],
                "boundaries": "North Rancho Cucamonga, Etiwanda area",
            },
            "central elementary school district": {
                "name": "Central Elementary School District",
                "rating": 8.1,
                "enrollment": 8500,
                "student_teacher_ratio": 22.8,
                "graduation_rate": 92.3,
                "college_readiness": 79.2,
                "top_schools": [
                    {"name": "Rancho Cucamonga High School", "rating": 8.8, "type": "High School"},
                    {"name": "Los Osos High School", "rating": 8.5, "type": "High School"},
                    {"name": "Alta Loma High School", "rating": 8.9, "type": "High School"},
                ],
                "special_programs": ["IB Programme", "Career Technical Education", "GATE"],
                "boundaries": "Central Rancho Cucamonga, Alta Loma",
            },
        }

        return districts.get(district_name.lower(), {})

    async def _generate_corporate_insights(
        self, employer: Optional[str], position_level: Optional[str]
    ) -> Dict[str, Any]:
        """Generate insights for corporate relocations."""
        insights = {
            "market_overview": {
                "total_logistics_healthcare_workers": 45000,
                "growth_rate_annual": 8.5,
                "median_salary": 85000,
                "housing_demand": "High",
            },
            "top_employers": list(self.corporate_hqs.values()),
            "recommended_neighborhoods": [],
            "budget_guidance": {},
            "timing_advice": {},
        }

        if employer and employer.lower().replace(" ", "_") in self.corporate_hqs:
            corp_data = self.corporate_hqs[employer.lower().replace(" ", "_")]

            # Recommend neighborhoods based on employer location
            if employer.lower() == "amazon_logistics" or "amazon" in employer.lower():
                insights["recommended_neighborhoods"] = [
                    {"name": "South RC", "commute": "10 mins", "appeal": "Direct access to fulfillment centers"},
                    {"name": "Central RC", "commute": "15 mins", "appeal": "Family-friendly, good schools"},
                    {"name": "Etiwanda", "commute": "20 mins", "appeal": "Top schools, family community"},
                ]
            elif employer.lower() == "kaiser_permanente" or "kaiser" in employer.lower():
                insights["recommended_neighborhoods"] = [
                    {"name": "Central RC", "commute": "15 mins", "appeal": "Healthcare community, amenities"},
                    {"name": "Etiwanda", "commute": "20 mins", "appeal": "Excellent schools for healthcare families"},
                    {"name": "Alta Loma", "commute": "25 mins", "appeal": "Luxury community, professional appeal"},
                ]

            # Budget guidance based on salary
            avg_salary = corp_data["avg_salary"]
            recommended_budget = avg_salary * 3  # 3x salary rule

            insights["budget_guidance"] = {
                "recommended_max": recommended_budget,
                "comfortable_range": f"${recommended_budget * 0.7:.0f} - ${recommended_budget:.0f}",
                "monthly_payment_target": f"${recommended_budget * 0.28 / 12:.0f}",
                "down_payment_suggestion": f"${recommended_budget * 0.2:.0f} (20%)",
            }

        return insights

    async def _calculate_commute_analysis(
        self, property_coords: Tuple[float, float], work_location: str
    ) -> Dict[str, Any]:
        """Calculate comprehensive commute analysis."""
        # In production, integrate with Google Maps API or similar
        work_coords = self.corporate_hqs.get(work_location.lower(), {}).get("coordinates")

        if not work_coords:
            return {"error": "Work location not found"}

        # Simplified commute calculation - use real routing API in production
        return {
            "driving": {
                "time_typical": "25 minutes",
                "time_rush_hour": "35 minutes",
                "distance": "15.2 miles",
                "cost_monthly": "$180 (gas + parking)",
            },
            "public_transit": {
                "time_typical": "45 minutes",
                "cost_monthly": "$41.25 (CapMetro)",
                "routes": ["Bus + Light Rail"],
                "walkability_to_transit": "8/10",
            },
            "bike": {
                "time_typical": "45 minutes",
                "distance": "12.8 miles",
                "safety_rating": "7/10",
                "bike_lanes": "Partially protected",
            },
            "overall_score": 8.5,
            "recommendation": "Excellent commute with multiple transportation options",
        }

    def _analyze_buy_timing(self, metrics: MarketMetrics) -> Dict[str, Any]:
        """Analyze optimal buying timing based on market conditions."""
        timing_score = 50  # Base score
        recommendations = []
        urgency = "medium"

        # Analyze market conditions
        if metrics.market_condition == MarketCondition.STRONG_SELLERS:
            timing_score -= 20
            recommendations.append("Prepare for competitive offers and quick decisions")
            urgency = "high"
        elif metrics.market_condition == MarketCondition.BALANCED:
            timing_score += 10
            recommendations.append("Good time to buy with reasonable negotiating power")
        elif metrics.market_condition == MarketCondition.STRONG_BUYERS:
            timing_score += 30
            recommendations.append("Excellent buyer's market - take time to negotiate")
            urgency = "low"

        # Analyze inventory levels
        if metrics.months_supply < 2:
            timing_score -= 15
            recommendations.append("Low inventory - be prepared to act fast on good properties")
        elif metrics.months_supply > 4:
            timing_score += 15
            recommendations.append("Good inventory levels - more selection available")

        # Price trend analysis
        if metrics.price_trend_3m > 5:
            timing_score -= 10
            recommendations.append("Prices rising quickly - consider buying sooner")
        elif metrics.price_trend_3m < 0:
            timing_score += 15
            recommendations.append("Price cooling provides better opportunities")

        return {
            "timing_score": max(0, min(100, timing_score)),
            "recommendations": recommendations,
            "urgency_level": urgency,
        }

    def _analyze_sell_timing(self, metrics: MarketMetrics) -> Dict[str, Any]:
        """Analyze optimal selling timing based on market conditions."""
        timing_score = 50  # Base score
        recommendations = []
        urgency = "medium"

        # Market conditions for sellers
        if metrics.market_condition == MarketCondition.STRONG_SELLERS:
            timing_score += 30
            recommendations.append("Excellent time to sell - strong seller's market")
            urgency = "high"
        elif metrics.market_condition == MarketCondition.BALANCED:
            timing_score += 10
            recommendations.append("Good market conditions for selling")
        elif metrics.market_condition == MarketCondition.STRONG_BUYERS:
            timing_score -= 20
            recommendations.append("Challenging market - price competitively")
            urgency = "low"

        # Days on market analysis
        if metrics.average_days_on_market < 20:
            timing_score += 15
            recommendations.append("Properties selling quickly - good market velocity")
        elif metrics.average_days_on_market > 45:
            timing_score -= 10
            recommendations.append("Properties taking longer to sell - ensure competitive pricing")

        # Price trends
        if metrics.price_trend_3m > 5:
            timing_score += 15
            recommendations.append("Strong price appreciation continues")
        elif metrics.price_trend_3m < 0:
            timing_score -= 15
            recommendations.append("Price pressure - consider waiting if possible")

        return {
            "timing_score": max(0, min(100, timing_score)),
            "recommendations": recommendations,
            "urgency_level": urgency,
        }

    def _get_seasonal_factors(self) -> Dict[str, Any]:
        """Get Austin Metropolitan Area seasonal market factors."""
        month = datetime.now().month

        seasonal_data = {
            "spring": {
                "months": [3, 4, 5],
                "activity_level": "Peak",
                "buyer_behavior": "High activity, competitive",
                "seller_behavior": "Highest listing volume",
                "recommendation": "Best time for sellers, competitive for buyers",
            },
            "summer": {
                "months": [6, 7, 8],
                "activity_level": "High",
                "buyer_behavior": "Sustained activity, family moves",
                "seller_behavior": "Continued strong inventory",
                "recommendation": "Good for both buyers and sellers",
            },
            "fall": {
                "months": [9, 10, 11],
                "activity_level": "Moderate",
                "buyer_behavior": "More selective, school considerations",
                "seller_behavior": "Inventory begins to decline",
                "recommendation": "Balanced market conditions",
            },
            "winter": {
                "months": [12, 1, 2],
                "activity_level": "Slower",
                "buyer_behavior": "Serious buyers, less competition",
                "seller_behavior": "Limited inventory",
                "recommendation": "Opportunities for motivated buyers",
            },
        }

        # Determine current season
        current_season = "winter"
        for season, data in seasonal_data.items():
            if month in data["months"]:
                current_season = season
                break

        return {
            "current_season": current_season,
            "seasonal_data": seasonal_data[current_season],
            "inland_empire_specific_factors": [
                "Logistics hiring peaks in Q4 for holiday season",
                "Healthcare hiring increases in summer months",
                "Family moves align with school calendar",
                "Weather allows year-round showing activity",
            ],
        }

    async def get_pricing_analytics(
        self,
        neighborhood: Optional[str] = None,
        property_type: Optional[PropertyType] = None,
        price_range: Optional[Tuple[float, float]] = None,
        days_back: int = 90,
    ) -> Dict[str, Any]:
        """
        Get comprehensive pricing analytics for Dynamic Pricing Intelligence integration.

        Returns detailed market pricing data for valuation and investment analysis.
        """
        cache_key = f"pricing_analytics:{neighborhood}:{property_type}:{price_range}:{days_back}"

        # Try cache first (15-minute TTL for pricing data)
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for pricing analytics: {neighborhood}")
            return cached

        # Get base market metrics
        market_metrics = await self.get_market_metrics(neighborhood, property_type, price_range)

        # Calculate price distribution data
        price_distribution = self._calculate_price_distribution(neighborhood, property_type)

        # Get appreciation trends
        appreciation_trends = self._calculate_appreciation_trends(neighborhood, days_back)

        # Calculate investment metrics
        investment_metrics = self._calculate_investment_metrics(neighborhood)

        # Get competitive pricing data
        competitive_data = await self._get_competitive_pricing_data(neighborhood)

        pricing_analytics = {
            "market_metrics": {
                "median_price": market_metrics.median_price,
                "average_days_on_market": market_metrics.average_days_on_market,
                "price_trend_1m": market_metrics.price_trend_1m,
                "price_trend_3m": market_metrics.price_trend_3m,
                "price_trend_1y": market_metrics.price_trend_1y,
                "market_condition": market_metrics.market_condition.value,
                "absorption_rate": market_metrics.absorption_rate,
            },
            "price_distribution": price_distribution,
            "appreciation_trends": appreciation_trends,
            "investment_metrics": investment_metrics,
            "competitive_analysis": competitive_data,
            "pricing_recommendations": self._generate_pricing_recommendations(
                market_metrics, price_distribution, appreciation_trends
            ),
            "last_updated": datetime.now().isoformat(),
        }

        # Cache for 15 minutes
        await self.cache.set(cache_key, pricing_analytics, ttl=900)
        logger.info(f"Generated pricing analytics for {neighborhood or 'Rancho Cucamonga'}")

        return pricing_analytics

    def _calculate_price_distribution(
        self, neighborhood: Optional[str], property_type: Optional[PropertyType]
    ) -> Dict[str, Any]:
        """Calculate price distribution statistics for the market."""
        # Simulated price distribution data
        # In production, would analyze actual MLS data

        base_median = self.neighborhoods.get(neighborhood.lower() if neighborhood else "central_rc", {}).get(
            "median_price", 825000
        )

        return {
            "percentiles": {
                "p10": int(base_median * 0.6),
                "p25": int(base_median * 0.8),
                "p50": int(base_median),
                "p75": int(base_median * 1.3),
                "p90": int(base_median * 1.7),
            },
            "price_per_sqft": {"min": 220, "median": 295, "max": 450, "average": 310},
            "active_listings_by_price": {
                "under_500k": 45,
                "500k_750k": 125,
                "750k_1m": 85,
                "1m_1_5m": 35,
                "over_1_5m": 15,
            },
        }

    def _calculate_appreciation_trends(self, neighborhood: Optional[str], days_back: int) -> Dict[str, Any]:
        """Calculate historical appreciation trends."""
        # Simulated appreciation data
        # In production, would analyze historical sales data

        # Base appreciation for Rancho Cucamonga market
        base_appreciation = 8.5  # Annual percentage

        # Neighborhood adjustments
        neighborhood_multiplier = 1.0
        if neighborhood:
            neighborhood_data = self.neighborhoods.get(neighborhood.lower(), {})
            # Higher-end neighborhoods typically appreciate faster
            if neighborhood_data.get("median_price", 825000) > 1000000:
                neighborhood_multiplier = 1.2
            elif neighborhood_data.get("median_price", 825000) < 600000:
                neighborhood_multiplier = 0.9

        actual_appreciation = base_appreciation * neighborhood_multiplier

        return {
            "annual_appreciation": round(actual_appreciation, 2),
            "quarterly_trends": [
                {"quarter": "Q1_2024", "appreciation": round(actual_appreciation * 0.25, 2)},
                {"quarter": "Q2_2024", "appreciation": round(actual_appreciation * 0.28, 2)},
                {"quarter": "Q3_2024", "appreciation": round(actual_appreciation * 0.23, 2)},
                {"quarter": "Q4_2024", "appreciation": round(actual_appreciation * 0.24, 2)},
            ],
            "5_year_projection": round(actual_appreciation * 5, 1),
            "appreciation_vs_county": "+2.3%",  # Outperforming San Bernardino County
            "appreciation_vs_state": "+0.8%",  # Slightly outperforming California
        }

    def _calculate_investment_metrics(self, neighborhood: Optional[str]) -> Dict[str, Any]:
        """Calculate investment-specific metrics for the market."""
        neighborhood_data = self.neighborhoods.get(neighborhood.lower() if neighborhood else "central_rc", {})

        median_price = neighborhood_data.get("median_price", 825000)

        # Estimate rental yields (would use actual rental data in production)
        monthly_rent = median_price * 0.007  # 0.7% rule for IE market
        annual_rent = monthly_rent * 12
        gross_yield = (annual_rent / median_price) * 100

        return {
            "rental_yield": {
                "gross_yield": round(gross_yield, 2),
                "estimated_net_yield": round(gross_yield * 0.65, 2),  # After expenses
                "monthly_rent_estimate": int(monthly_rent),
                "rent_to_price_ratio": round((monthly_rent / median_price) * 100, 3),
            },
            "investment_scores": {
                "cash_flow_potential": 75,  # 0-100 scale
                "appreciation_potential": 85,
                "liquidity_score": neighborhood_data.get("logistics_healthcare_appeal", 80),
                "overall_investment_grade": "B+",
            },
            "market_fundamentals": {
                "job_growth_rate": 3.2,  # Annual percentage
                "population_growth_rate": 2.8,
                "new_construction_permits": 145,  # Monthly average
                "corporate_expansion_activity": "High",  # Amazon, healthcare growth
            },
        }

    async def _get_competitive_pricing_data(self, neighborhood: Optional[str]) -> Dict[str, Any]:
        """Get competitive pricing analysis data."""
        # Simulated competitive analysis
        # In production, would analyze actual listing and sales data

        return {
            "price_positioning": {
                "below_market_listings": 25,  # Count
                "at_market_listings": 45,
                "above_market_listings": 30,
                "overpriced_listings": 15,
            },
            "days_on_market_by_pricing": {
                "aggressively_priced": 18,  # Days
                "competitively_priced": 28,
                "strategically_priced": 35,
                "overpriced": 65,
            },
            "price_reduction_analysis": {
                "listings_with_reductions": 35,  # Percentage
                "average_reduction_amount": 25000,
                "average_days_before_reduction": 45,
                "success_rate_after_reduction": 78,
            },
            "seasonal_pricing_patterns": {
                "spring_premium": 3.5,  # Percentage above annual average
                "summer_premium": 1.8,
                "fall_discount": -1.2,
                "winter_discount": -2.8,
            },
        }

    def _generate_pricing_recommendations(
        self, market_metrics: MarketMetrics, price_distribution: Dict[str, Any], appreciation_trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate intelligent pricing recommendations."""
        recommendations = {
            "current_market_strategy": "",
            "pricing_guidance": [],
            "timing_recommendations": [],
            "risk_factors": [],
        }

        # Determine market strategy based on conditions
        if market_metrics.market_condition == MarketCondition.STRONG_SELLERS:
            recommendations["current_market_strategy"] = "aggressive_pricing"
            recommendations["pricing_guidance"].append(
                "Market supports premium pricing - consider 2-5% above comparable sales"
            )
        elif market_metrics.market_condition == MarketCondition.STRONG_BUYERS:
            recommendations["current_market_strategy"] = "competitive_pricing"
            recommendations["pricing_guidance"].append(
                "Buyer's market requires competitive pricing - stay within 2% of market value"
            )
        else:
            recommendations["current_market_strategy"] = "balanced_approach"
            recommendations["pricing_guidance"].append(
                "Balanced market allows strategic pricing based on property positioning"
            )

        # Appreciation-based recommendations
        annual_appreciation = appreciation_trends.get("annual_appreciation", 0)
        if annual_appreciation > 7:
            recommendations["timing_recommendations"].append(
                "Strong appreciation trend supports holding strategy for sellers"
            )
        elif annual_appreciation < 3:
            recommendations["risk_factors"].append("Slower appreciation may limit investment upside")

        # Market velocity recommendations
        if market_metrics.average_days_on_market < 25:
            recommendations["timing_recommendations"].append("Fast-moving market - price competitively for quick sale")
        elif market_metrics.average_days_on_market > 45:
            recommendations["pricing_guidance"].append(
                "Slower market - consider strategic pricing 3-5% below market for attraction"
            )

        return recommendations


# Global service instance
_rancho_cucamonga_market_service = None


def get_rancho_cucamonga_market_service() -> AustinMarketService:
    """Get singleton instance of Rancho Cucamonga Market Service."""
    global _rancho_cucamonga_market_service
    if _rancho_cucamonga_market_service is None:
        _rancho_cucamonga_market_service = AustinMarketService()
    return _rancho_cucamonga_market_service


# Alias for backward compatibility with Austin naming - keep existing class name
RanchoCucamongaMarketService = AustinMarketService
