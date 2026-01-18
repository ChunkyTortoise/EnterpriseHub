"""
Austin Market Data Service - Real-time MLS integration and market intelligence.

Provides comprehensive Austin real estate market data including:
- MLS property listings and market trends
- School district ratings and boundary mapping
- Neighborhood analytics and demographics
- Corporate relocation data for tech workers
- Market timing and inventory analysis
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger

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
class AustinNeighborhood:
    """Austin neighborhood with comprehensive market data."""
    name: str
    zone: str  # Central, North, South, East, West
    median_price: float
    price_trend_3m: float  # Percentage change
    inventory_days: int
    school_rating: float
    walkability_score: int
    tech_worker_appeal: float  # 0-100 score
    corporate_proximity: Dict[str, float]  # Company name -> commute minutes
    amenities: List[str]
    demographics: Dict[str, Any]
    market_condition: MarketCondition


@dataclass
class PropertyListing:
    """Austin MLS property listing."""
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
    """Austin market performance metrics."""
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
    Comprehensive Austin real estate market intelligence service.

    Integrates with MLS data, school ratings, corporate data,
    and provides real-time market analysis.
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.neighborhoods = self._load_neighborhood_data()
        self.corporate_hqs = self._load_corporate_headquarters()

    async def get_market_metrics(
        self,
        neighborhood: Optional[str] = None,
        property_type: Optional[PropertyType] = None,
        price_range: Optional[Tuple[float, float]] = None
    ) -> MarketMetrics:
        """Get real-time Austin market metrics with optional filtering."""
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
        logger.info(f"Fetched fresh market metrics for {neighborhood or 'Austin'}")

        return metrics

    async def search_properties(
        self,
        criteria: Dict[str, Any],
        limit: int = 50
    ) -> List[PropertyListing]:
        """
        Search Austin MLS properties with comprehensive criteria.

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

    async def get_neighborhood_analysis(self, neighborhood: str) -> Optional[AustinNeighborhood]:
        """Get comprehensive neighborhood analysis."""
        cache_key = f"neighborhood_analysis:{neighborhood.lower()}"

        # Try cache first (1-hour TTL for neighborhood data)
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for neighborhood: {neighborhood}")
            return AustinNeighborhood(**cached)

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
        self,
        employer: Optional[str] = None,
        position_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get insights for corporate relocations to Austin.

        Focuses on Apple, Google, Meta, Tesla, and other major employers.
        """
        cache_key = f"corporate_insights:{employer}:{position_level}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        insights = await self._generate_corporate_insights(employer, position_level)

        # Cache for 6 hours
        await self.cache.set(cache_key, insights, ttl=21600)

        return insights

    async def get_commute_analysis(
        self,
        property_coords: Tuple[float, float],
        work_location: str
    ) -> Dict[str, Any]:
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
        neighborhood: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get market timing recommendations for Austin market."""
        current_metrics = await self.get_market_metrics(neighborhood, property_type)

        advice = {
            "timing_score": 0,  # 0-100, higher = better time
            "market_condition": current_metrics.market_condition.value,
            "recommendations": [],
            "seasonal_factors": self._get_seasonal_factors(),
            "urgency_level": "low"  # low, medium, high
        }

        # Analyze market conditions for timing
        if transaction_type == "buy":
            advice.update(self._analyze_buy_timing(current_metrics))
        else:
            advice.update(self._analyze_sell_timing(current_metrics))

        return advice

    def _load_neighborhood_data(self) -> Dict[str, Dict[str, Any]]:
        """Load Austin neighborhood base data."""
        return {
            "downtown": {
                "name": "Downtown Austin",
                "zone": "Central",
                "median_price": 850000,
                "school_rating": 7.2,
                "walkability_score": 95,
                "tech_worker_appeal": 90,
                "amenities": ["Rainey Street", "Lady Bird Lake", "Convention Center", "Nightlife"],
                "demographics": {"age_median": 32, "income_median": 95000, "tech_workers": 0.35}
            },
            "south_lamar": {
                "name": "South Lamar",
                "zone": "Central",
                "median_price": 725000,
                "school_rating": 8.1,
                "walkability_score": 88,
                "tech_worker_appeal": 85,
                "amenities": ["Food Trucks", "Zilker Park", "South Lamar District", "Restaurants"],
                "demographics": {"age_median": 31, "income_median": 88000, "tech_workers": 0.32}
            },
            "mueller": {
                "name": "Mueller",
                "zone": "East",
                "median_price": 650000,
                "school_rating": 8.7,
                "walkability_score": 78,
                "tech_worker_appeal": 88,
                "amenities": ["Mueller Lake Park", "Dell Children's Hospital", "Town Center", "Farmers Market"],
                "demographics": {"age_median": 35, "income_median": 92000, "tech_workers": 0.28}
            },
            "round_rock": {
                "name": "Round Rock",
                "zone": "North",
                "median_price": 485000,
                "school_rating": 9.1,
                "walkability_score": 45,
                "tech_worker_appeal": 95,  # High due to Apple campus
                "amenities": ["Dell Diamond", "Round Rock Premium Outlets", "Apple Campus", "Family Friendly"],
                "demographics": {"age_median": 38, "income_median": 105000, "tech_workers": 0.42}
            },
            "cedar_park": {
                "name": "Cedar Park",
                "zone": "Northwest",
                "median_price": 465000,
                "school_rating": 9.3,
                "walkability_score": 35,
                "tech_worker_appeal": 80,
                "amenities": ["H-E-B Center", "Sculpture Falls", "Good Schools", "Family Community"],
                "demographics": {"age_median": 41, "income_median": 98000, "tech_workers": 0.25}
            },
            "east_austin": {
                "name": "East Austin",
                "zone": "East",
                "median_price": 580000,
                "school_rating": 6.8,
                "walkability_score": 72,
                "tech_worker_appeal": 75,
                "amenities": ["Food Scene", "Art District", "Music Venues", "Hip Culture"],
                "demographics": {"age_median": 29, "income_median": 72000, "tech_workers": 0.22}
            },
            "westlake": {
                "name": "Westlake",
                "zone": "West",
                "median_price": 1200000,
                "school_rating": 9.8,
                "walkability_score": 25,
                "tech_worker_appeal": 70,
                "amenities": ["Lake Austin", "Luxury Shopping", "Top Schools", "Hill Country"],
                "demographics": {"age_median": 45, "income_median": 185000, "tech_workers": 0.18}
            },
            "domain": {
                "name": "Domain/Arboretum",
                "zone": "Northwest",
                "median_price": 575000,
                "school_rating": 8.5,
                "walkability_score": 65,
                "tech_worker_appeal": 92,
                "amenities": ["The Domain", "Shopping", "Tech Offices", "Urban Living"],
                "demographics": {"age_median": 33, "income_median": 102000, "tech_workers": 0.38}
            }
        }

    def _load_corporate_headquarters(self) -> Dict[str, Dict[str, Any]]:
        """Load major corporate headquarters and campuses in Austin."""
        return {
            "apple": {
                "name": "Apple",
                "location": "Round Rock",
                "coordinates": (30.389444, -97.708333),
                "employees": 15000,
                "expansion_plans": "Up to 20,000 by 2026",
                "avg_salary": 145000,
                "preferred_neighborhoods": ["Round Rock", "Cedar Park", "Domain", "Mueller"]
            },
            "google": {
                "name": "Google",
                "location": "Downtown Austin",
                "coordinates": (30.268889, -97.745556),
                "employees": 2500,
                "expansion_plans": "Steady growth",
                "avg_salary": 155000,
                "preferred_neighborhoods": ["Downtown", "South Lamar", "East Austin", "Mueller"]
            },
            "meta": {
                "name": "Meta",
                "location": "Domain",
                "coordinates": (30.384444, -97.727778),
                "employees": 3000,
                "expansion_plans": "Significant expansion planned",
                "avg_salary": 165000,
                "preferred_neighborhoods": ["Domain", "Round Rock", "Cedar Park", "Downtown"]
            },
            "tesla": {
                "name": "Tesla",
                "location": "East Austin (Gigafactory)",
                "coordinates": (30.230556, -97.610556),
                "employees": 20000,
                "expansion_plans": "Major manufacturing hub",
                "avg_salary": 95000,
                "preferred_neighborhoods": ["East Austin", "Mueller", "Manor", "Pflugerville"]
            },
            "dell": {
                "name": "Dell Technologies",
                "location": "Round Rock",
                "coordinates": (30.388889, -97.678889),
                "employees": 12000,
                "expansion_plans": "Stable workforce",
                "avg_salary": 125000,
                "preferred_neighborhoods": ["Round Rock", "Cedar Park", "Leander", "Georgetown"]
            },
            "ibm": {
                "name": "IBM",
                "location": "North Austin",
                "coordinates": (30.395556, -97.727222),
                "employees": 6000,
                "expansion_plans": "Moderate growth",
                "avg_salary": 135000,
                "preferred_neighborhoods": ["Domain", "Round Rock", "Cedar Park", "North Austin"]
            }
        }

    async def _fetch_market_metrics(
        self,
        neighborhood: Optional[str],
        property_type: Optional[PropertyType],
        price_range: Optional[Tuple[float, float]]
    ) -> MarketMetrics:
        """Fetch real-time market metrics from MLS and market data sources."""
        # Simulate MLS API call - in production, integrate with actual MLS
        # This would connect to Austin Board of Realtors MLS or similar

        base_metrics = {
            "median_price": 625000,
            "average_days_on_market": 28,
            "inventory_count": 2150,
            "months_supply": 1.8,
            "price_trend_1m": 0.8,
            "price_trend_3m": 3.2,
            "price_trend_1y": 12.5,
            "new_listings_7d": 285,
            "closed_sales_30d": 1156,
            "pending_sales": 892,
            "absorption_rate": 85.2,
            "market_condition": MarketCondition.STRONG_SELLERS
        }

        # Adjust based on neighborhood
        if neighborhood:
            neighborhood_data = self.neighborhoods.get(neighborhood.lower(), {})
            if neighborhood_data:
                price_multiplier = neighborhood_data.get("median_price", 625000) / 625000
                base_metrics["median_price"] = int(base_metrics["median_price"] * price_multiplier)

        # Adjust based on property type
        if property_type:
            type_adjustments = {
                PropertyType.CONDO: {"median_price": 0.75, "average_days_on_market": 1.2},
                PropertyType.TOWNHOME: {"median_price": 0.85, "average_days_on_market": 0.9},
                PropertyType.LAND: {"median_price": 0.4, "average_days_on_market": 2.5},
                PropertyType.MULTI_FAMILY: {"median_price": 1.8, "average_days_on_market": 1.8}
            }

            adjustments = type_adjustments.get(property_type, {})
            for key, multiplier in adjustments.items():
                if key in base_metrics:
                    base_metrics[key] = int(base_metrics[key] * multiplier)

        return MarketMetrics(**base_metrics)

    async def _search_mls_properties(
        self,
        criteria: Dict[str, Any],
        limit: int
    ) -> List[PropertyListing]:
        """Search MLS properties - integrate with actual MLS API in production."""
        # Simulate MLS search results
        # In production, this would connect to Austin MLS API

        sample_properties = [
            {
                "mls_id": "ATX2024001",
                "address": "123 South Lamar Blvd, Austin, TX 78704",
                "price": 725000,
                "beds": 3,
                "baths": 2.5,
                "sqft": 2100,
                "lot_size": 0.18,
                "year_built": 2019,
                "property_type": PropertyType.SINGLE_FAMILY,
                "neighborhood": "South Lamar",
                "school_district": "Austin ISD",
                "days_on_market": 12,
                "price_per_sqft": 345,
                "price_changes": [],
                "features": ["Open Floor Plan", "Modern Kitchen", "Walkable", "Food Trucks"],
                "coordinates": (30.252222, -97.763889),
                "photos": ["photo1.jpg", "photo2.jpg"],
                "description": "Modern home in vibrant South Lamar district",
                "listing_agent": {"name": "Jorge Martinez", "phone": "(512) 555-0123"},
                "last_updated": datetime.now()
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

    async def _enhance_neighborhood_data(self, base_data: Dict[str, Any]) -> AustinNeighborhood:
        """Enhance neighborhood data with real-time market information."""
        # Get current market metrics for the neighborhood
        metrics = await self.get_market_metrics(base_data["name"])

        # Calculate corporate proximity
        corporate_proximity = {}
        for corp_name, corp_data in self.corporate_hqs.items():
            # Simplified distance calculation - in production use actual routing API
            distance_minutes = 25  # Placeholder
            corporate_proximity[corp_data["name"]] = distance_minutes

        return AustinNeighborhood(
            name=base_data["name"],
            zone=base_data["zone"],
            median_price=metrics.median_price,
            price_trend_3m=metrics.price_trend_3m,
            inventory_days=metrics.average_days_on_market,
            school_rating=base_data["school_rating"],
            walkability_score=base_data["walkability_score"],
            tech_worker_appeal=base_data["tech_worker_appeal"],
            corporate_proximity=corporate_proximity,
            amenities=base_data["amenities"],
            demographics=base_data["demographics"],
            market_condition=metrics.market_condition
        )

    async def _fetch_school_district_data(self, district_name: str) -> Dict[str, Any]:
        """Fetch comprehensive school district information."""
        # In production, integrate with Texas Education Agency API
        districts = {
            "austin isd": {
                "name": "Austin Independent School District",
                "rating": 7.8,
                "enrollment": 75000,
                "student_teacher_ratio": 14.2,
                "graduation_rate": 89.5,
                "college_readiness": 78.2,
                "top_schools": [
                    {"name": "Liberal Arts and Science Academy", "rating": 10.0, "type": "High School"},
                    {"name": "Anderson High School", "rating": 9.2, "type": "High School"},
                    {"name": "Bowie High School", "rating": 8.8, "type": "High School"}
                ],
                "special_programs": ["Dual Language", "STEM", "Fine Arts", "International Baccalaureate"],
                "boundaries": "Central Austin, South Austin, East Austin"
            },
            "round rock isd": {
                "name": "Round Rock Independent School District",
                "rating": 9.1,
                "enrollment": 48000,
                "student_teacher_ratio": 15.1,
                "graduation_rate": 94.2,
                "college_readiness": 85.7,
                "top_schools": [
                    {"name": "Westwood High School", "rating": 9.8, "type": "High School"},
                    {"name": "Round Rock High School", "rating": 9.5, "type": "High School"},
                    {"name": "Cedar Ridge High School", "rating": 9.3, "type": "High School"}
                ],
                "special_programs": ["STEM Academy", "Early College", "Career and Technical Education"],
                "boundaries": "Round Rock, Pflugerville, Cedar Park (partial)"
            }
        }

        return districts.get(district_name.lower(), {})

    async def _generate_corporate_insights(
        self,
        employer: Optional[str],
        position_level: Optional[str]
    ) -> Dict[str, Any]:
        """Generate insights for corporate relocations."""
        insights = {
            "market_overview": {
                "total_tech_workers": 85000,
                "growth_rate_annual": 15.2,
                "median_salary": 125000,
                "housing_demand": "Very High"
            },
            "top_employers": list(self.corporate_hqs.values()),
            "recommended_neighborhoods": [],
            "budget_guidance": {},
            "timing_advice": {}
        }

        if employer and employer.lower() in self.corporate_hqs:
            corp_data = self.corporate_hqs[employer.lower()]

            # Recommend neighborhoods based on employer location
            if employer.lower() == "apple":
                insights["recommended_neighborhoods"] = [
                    {"name": "Round Rock", "commute": "5 mins", "appeal": "Direct access to campus"},
                    {"name": "Cedar Park", "commute": "15 mins", "appeal": "Excellent schools, family-friendly"},
                    {"name": "Domain", "commute": "20 mins", "appeal": "Urban amenities, tech community"}
                ]
            elif employer.lower() == "google":
                insights["recommended_neighborhoods"] = [
                    {"name": "Downtown", "commute": "Walking", "appeal": "Urban lifestyle, entertainment"},
                    {"name": "South Lamar", "commute": "10 mins", "appeal": "Food scene, cultural activities"},
                    {"name": "East Austin", "commute": "15 mins", "appeal": "Trendy, artistic community"}
                ]

            # Budget guidance based on salary
            avg_salary = corp_data["avg_salary"]
            recommended_budget = avg_salary * 3  # 3x salary rule

            insights["budget_guidance"] = {
                "recommended_max": recommended_budget,
                "comfortable_range": f"${recommended_budget * 0.7:.0f} - ${recommended_budget:.0f}",
                "monthly_payment_target": f"${recommended_budget * 0.28 / 12:.0f}",
                "down_payment_suggestion": f"${recommended_budget * 0.2:.0f} (20%)"
            }

        return insights

    async def _calculate_commute_analysis(
        self,
        property_coords: Tuple[float, float],
        work_location: str
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
                "cost_monthly": "$180 (gas + parking)"
            },
            "public_transit": {
                "time_typical": "45 minutes",
                "cost_monthly": "$41.25 (CapMetro)",
                "routes": ["Bus + Light Rail"],
                "walkability_to_transit": "8/10"
            },
            "bike": {
                "time_typical": "45 minutes",
                "distance": "12.8 miles",
                "safety_rating": "7/10",
                "bike_lanes": "Partially protected"
            },
            "overall_score": 8.5,
            "recommendation": "Excellent commute with multiple transportation options"
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
            "urgency_level": urgency
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
            "urgency_level": urgency
        }

    def _get_seasonal_factors(self) -> Dict[str, Any]:
        """Get Austin seasonal market factors."""
        month = datetime.now().month

        seasonal_data = {
            "spring": {
                "months": [3, 4, 5],
                "activity_level": "Peak",
                "buyer_behavior": "High activity, competitive",
                "seller_behavior": "Highest listing volume",
                "recommendation": "Best time for sellers, competitive for buyers"
            },
            "summer": {
                "months": [6, 7, 8],
                "activity_level": "High",
                "buyer_behavior": "Sustained activity, family moves",
                "seller_behavior": "Continued strong inventory",
                "recommendation": "Good for both buyers and sellers"
            },
            "fall": {
                "months": [9, 10, 11],
                "activity_level": "Moderate",
                "buyer_behavior": "More selective, school considerations",
                "seller_behavior": "Inventory begins to decline",
                "recommendation": "Balanced market conditions"
            },
            "winter": {
                "months": [12, 1, 2],
                "activity_level": "Slower",
                "buyer_behavior": "Serious buyers, less competition",
                "seller_behavior": "Limited inventory",
                "recommendation": "Opportunities for motivated buyers"
            }
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
            "austin_specific_factors": [
                "SXSW (March) increases spring activity",
                "UT academic calendar affects rental market",
                "Corporate relocations peak in summer",
                "Holiday season slowdown is brief due to mild weather"
            ]
        }


# Global service instance
_austin_market_service = None

def get_austin_market_service() -> AustinMarketService:
    """Get singleton instance of Austin Market Service."""
    global _austin_market_service
    if _austin_market_service is None:
        _austin_market_service = AustinMarketService()
    return _austin_market_service