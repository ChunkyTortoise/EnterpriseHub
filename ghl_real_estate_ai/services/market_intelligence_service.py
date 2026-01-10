"""
Market Intelligence Service

Advanced market analysis and intelligence gathering system for real estate agents.
Provides territory-based analytics, competitive intelligence, market opportunities,
and predictive trend analysis for informed decision-making.

Features:
- Territory-based market analysis and comparisons
- Competitive intelligence gathering and tracking
- Market opportunity identification and scoring
- Price trend analysis and predictions
- Demographic and economic insights
- Market timing recommendations

Created: January 2026
Author: GHL Real Estate AI Platform
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import random
import json

# Configure logging
logger = logging.getLogger(__name__)

class MarketTrend(Enum):
    """Market trend indicators."""
    STRONG_BUYER = "strong_buyer"
    BUYER_MARKET = "buyer_market"
    BALANCED = "balanced"
    SELLER_MARKET = "seller_market"
    STRONG_SELLER = "strong_seller"

class PropertyType(Enum):
    """Property types for market analysis."""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    LUXURY = "luxury"
    COMMERCIAL = "commercial"
    LAND = "land"
    MULTI_FAMILY = "multi_family"

class OpportunityType(Enum):
    """Types of market opportunities."""
    UNDERVALUED_PROPERTY = "undervalued_property"
    EMERGING_NEIGHBORHOOD = "emerging_neighborhood"
    PRICE_REDUCTION = "price_reduction"
    NEW_DEVELOPMENT = "new_development"
    INVESTMENT_OPPORTUNITY = "investment_opportunity"
    FIRST_TIME_BUYER_MARKET = "first_time_buyer_market"
    LUXURY_EXPANSION = "luxury_expansion"
    COMMERCIAL_OPPORTUNITY = "commercial_opportunity"

class CompetitorStatus(Enum):
    """Competitor activity status."""
    VERY_ACTIVE = "very_active"
    ACTIVE = "active"
    MODERATE = "moderate"
    LOW_ACTIVITY = "low_activity"
    INACTIVE = "inactive"

@dataclass
class MarketArea:
    """Represents a market territory or area."""
    area_id: str
    name: str
    zip_codes: List[str]
    boundaries: Dict[str, float]  # lat/lng boundaries
    population: int
    median_income: float
    primary_demographics: List[str]

    def __str__(self) -> str:
        return f"{self.name} ({', '.join(self.zip_codes[:3])}{'...' if len(self.zip_codes) > 3 else ''})"

@dataclass
class MarketMetrics:
    """Key market performance metrics."""
    area_id: str
    report_date: datetime
    avg_list_price: float
    avg_sale_price: float
    median_sale_price: float
    days_on_market: int
    inventory_months: float
    price_per_sqft: float
    total_sales: int
    new_listings: int
    price_change_30d: float
    price_change_90d: float
    price_change_1y: float
    absorption_rate: float
    list_to_sale_ratio: float

    def calculate_market_trend(self) -> MarketTrend:
        """Determine market trend based on metrics."""
        score = 0

        # Inventory analysis
        if self.inventory_months < 2:
            score += 2  # Strong seller
        elif self.inventory_months < 4:
            score += 1  # Seller market
        elif self.inventory_months > 8:
            score -= 2  # Strong buyer
        elif self.inventory_months > 6:
            score -= 1  # Buyer market

        # Price trend analysis
        if self.price_change_30d > 2:
            score += 1
        elif self.price_change_30d < -2:
            score -= 1

        # Days on market analysis
        if self.days_on_market < 15:
            score += 1
        elif self.days_on_market > 45:
            score -= 1

        # Absorption rate analysis
        if self.absorption_rate > 80:
            score += 1
        elif self.absorption_rate < 40:
            score -= 1

        # Convert score to trend
        if score >= 3:
            return MarketTrend.STRONG_SELLER
        elif score >= 1:
            return MarketTrend.SELLER_MARKET
        elif score <= -3:
            return MarketTrend.STRONG_BUYER
        elif score <= -1:
            return MarketTrend.BUYER_MARKET
        else:
            return MarketTrend.BALANCED

@dataclass
class Competitor:
    """Competitor analysis data."""
    competitor_id: str
    name: str
    agency: str
    territory_areas: List[str]
    specialties: List[PropertyType]
    recent_sales: int
    avg_sale_price: float
    market_share: float
    activity_level: CompetitorStatus
    strengths: List[str]
    weaknesses: List[str]
    recent_listings: int
    social_media_presence: float
    client_reviews_avg: float
    years_experience: int

@dataclass
class MarketOpportunity:
    """Market opportunity identification."""
    opportunity_id: str
    area_id: str
    opportunity_type: OpportunityType
    title: str
    description: str
    confidence_score: float
    potential_value: float
    effort_level: str  # low, medium, high
    time_sensitivity: str  # urgent, moderate, low
    recommended_actions: List[str]
    supporting_data: Dict[str, Any]
    created_date: datetime
    expires_date: Optional[datetime] = None

@dataclass
class MarketForecast:
    """Market forecast and predictions."""
    area_id: str
    forecast_date: datetime
    forecast_period_months: int
    predicted_price_change: float
    predicted_inventory_change: float
    predicted_sales_volume_change: float
    confidence_level: float
    key_factors: List[str]
    risk_factors: List[str]
    opportunities: List[str]

class MarketIntelligenceService:
    """
    Comprehensive market intelligence service for real estate agents.

    Provides territory-based market analysis, competitive intelligence,
    opportunity identification, and predictive market insights.
    """

    def __init__(self):
        self.market_areas: Dict[str, MarketArea] = {}
        self.market_metrics: Dict[str, MarketMetrics] = {}
        self.competitors: Dict[str, Competitor] = {}
        self.opportunities: Dict[str, MarketOpportunity] = {}
        self.forecasts: Dict[str, MarketForecast] = {}
        self.historical_data: Dict[str, List[MarketMetrics]] = {}

        # Initialize with demo data
        asyncio.create_task(self._initialize_demo_data())

    async def _initialize_demo_data(self) -> None:
        """Initialize service with demo market intelligence data."""
        try:
            # Create demo market areas
            await self._create_demo_market_areas()
            await self._create_demo_market_metrics()
            await self._create_demo_competitors()
            await self._create_demo_opportunities()
            await self._create_demo_forecasts()

            logger.info("Market intelligence service initialized with demo data")

        except Exception as e:
            logger.error(f"Error initializing demo data: {e}")

    async def _create_demo_market_areas(self) -> None:
        """Create demo market areas."""
        demo_areas = [
            {
                "area_id": "area_downtown",
                "name": "Downtown District",
                "zip_codes": ["90210", "90211", "90212"],
                "boundaries": {"north": 34.1, "south": 34.05, "east": -118.35, "west": -118.45},
                "population": 45000,
                "median_income": 95000,
                "primary_demographics": ["young professionals", "affluent families", "urban dwellers"]
            },
            {
                "area_id": "area_suburbs",
                "name": "Suburban Heights",
                "zip_codes": ["90301", "90302", "90303"],
                "boundaries": {"north": 34.2, "south": 34.1, "east": -118.25, "west": -118.35},
                "population": 78000,
                "median_income": 125000,
                "primary_demographics": ["families with children", "established professionals", "retirees"]
            },
            {
                "area_id": "area_luxury",
                "name": "Luxury Hills",
                "zip_codes": ["90401", "90402"],
                "boundaries": {"north": 34.25, "south": 34.2, "east": -118.2, "west": -118.3},
                "population": 25000,
                "median_income": 250000,
                "primary_demographics": ["high net worth individuals", "celebrities", "business executives"]
            },
            {
                "area_id": "area_emerging",
                "name": "Emerging District",
                "zip_codes": ["90501", "90502"],
                "boundaries": {"north": 34.15, "south": 34.08, "east": -118.15, "west": -118.25},
                "population": 35000,
                "median_income": 65000,
                "primary_demographics": ["young families", "artists", "small business owners"]
            }
        ]

        for area_data in demo_areas:
            area = MarketArea(**area_data)
            self.market_areas[area.area_id] = area

    async def _create_demo_market_metrics(self) -> None:
        """Create demo market metrics for each area."""
        areas = list(self.market_areas.keys())

        # Base metrics for different area types
        base_metrics = {
            "area_downtown": {
                "avg_list_price": 850000,
                "avg_sale_price": 825000,
                "median_sale_price": 780000,
                "days_on_market": 25,
                "inventory_months": 3.2,
                "price_per_sqft": 650
            },
            "area_suburbs": {
                "avg_list_price": 1200000,
                "avg_sale_price": 1175000,
                "median_sale_price": 1150000,
                "days_on_market": 35,
                "inventory_months": 4.1,
                "price_per_sqft": 475
            },
            "area_luxury": {
                "avg_list_price": 3500000,
                "avg_sale_price": 3350000,
                "median_sale_price": 3200000,
                "days_on_market": 65,
                "inventory_months": 7.5,
                "price_per_sqft": 800
            },
            "area_emerging": {
                "avg_list_price": 650000,
                "avg_sale_price": 635000,
                "median_sale_price": 620000,
                "days_on_market": 20,
                "inventory_months": 2.8,
                "price_per_sqft": 425
            }
        }

        for area_id in areas:
            base = base_metrics.get(area_id, base_metrics["area_downtown"])

            # Add some variation
            variation = random.uniform(0.95, 1.05)

            metrics = MarketMetrics(
                area_id=area_id,
                report_date=datetime.now(),
                avg_list_price=base["avg_list_price"] * variation,
                avg_sale_price=base["avg_sale_price"] * variation,
                median_sale_price=base["median_sale_price"] * variation,
                days_on_market=int(base["days_on_market"] * variation),
                inventory_months=base["inventory_months"] * variation,
                price_per_sqft=base["price_per_sqft"] * variation,
                total_sales=random.randint(45, 85),
                new_listings=random.randint(50, 100),
                price_change_30d=random.uniform(-3.5, 4.2),
                price_change_90d=random.uniform(-8.0, 12.0),
                price_change_1y=random.uniform(-15.0, 25.0),
                absorption_rate=random.uniform(35.0, 85.0),
                list_to_sale_ratio=random.uniform(0.92, 1.08)
            )

            self.market_metrics[area_id] = metrics

            # Create historical data
            historical = []
            for i in range(12):  # 12 months of historical data
                past_date = datetime.now() - timedelta(days=30 * i)
                historical_metrics = MarketMetrics(
                    area_id=area_id,
                    report_date=past_date,
                    avg_list_price=base["avg_list_price"] * random.uniform(0.9, 1.1),
                    avg_sale_price=base["avg_sale_price"] * random.uniform(0.9, 1.1),
                    median_sale_price=base["median_sale_price"] * random.uniform(0.9, 1.1),
                    days_on_market=int(base["days_on_market"] * random.uniform(0.8, 1.2)),
                    inventory_months=base["inventory_months"] * random.uniform(0.7, 1.3),
                    price_per_sqft=base["price_per_sqft"] * random.uniform(0.9, 1.1),
                    total_sales=random.randint(30, 90),
                    new_listings=random.randint(35, 110),
                    price_change_30d=random.uniform(-5.0, 6.0),
                    price_change_90d=random.uniform(-10.0, 15.0),
                    price_change_1y=random.uniform(-20.0, 30.0),
                    absorption_rate=random.uniform(25.0, 90.0),
                    list_to_sale_ratio=random.uniform(0.88, 1.12)
                )
                historical.append(historical_metrics)

            self.historical_data[area_id] = historical

    async def _create_demo_competitors(self) -> None:
        """Create demo competitor data."""
        demo_competitors = [
            {
                "competitor_id": "comp_001",
                "name": "Sarah Mitchell",
                "agency": "Premium Realty Group",
                "territory_areas": ["area_downtown", "area_luxury"],
                "specialties": [PropertyType.LUXURY, PropertyType.CONDO],
                "recent_sales": 28,
                "avg_sale_price": 1850000,
                "market_share": 12.5,
                "activity_level": CompetitorStatus.VERY_ACTIVE,
                "strengths": ["luxury market expertise", "strong social media presence", "celebrity connections"],
                "weaknesses": ["limited first-time buyer focus", "high price point"],
                "recent_listings": 15,
                "social_media_presence": 8.5,
                "client_reviews_avg": 4.8,
                "years_experience": 12
            },
            {
                "competitor_id": "comp_002",
                "name": "Michael Chen",
                "agency": "Family First Realty",
                "territory_areas": ["area_suburbs", "area_emerging"],
                "specialties": [PropertyType.SINGLE_FAMILY, PropertyType.TOWNHOUSE],
                "recent_sales": 42,
                "avg_sale_price": 975000,
                "market_share": 18.3,
                "activity_level": CompetitorStatus.VERY_ACTIVE,
                "strengths": ["family market focus", "excellent communication", "quick responses"],
                "weaknesses": ["limited luxury experience", "newer to market"],
                "recent_listings": 25,
                "social_media_presence": 6.2,
                "client_reviews_avg": 4.9,
                "years_experience": 7
            },
            {
                "competitor_id": "comp_003",
                "name": "Amanda Rodriguez",
                "agency": "Urban Living Specialists",
                "territory_areas": ["area_downtown", "area_emerging"],
                "specialties": [PropertyType.CONDO, PropertyType.MULTI_FAMILY],
                "recent_sales": 35,
                "avg_sale_price": 725000,
                "market_share": 15.7,
                "activity_level": CompetitorStatus.ACTIVE,
                "strengths": ["urban market knowledge", "investment property expertise", "bilingual"],
                "weaknesses": ["limited suburban reach", "newer agency"],
                "recent_listings": 20,
                "social_media_presence": 7.8,
                "client_reviews_avg": 4.6,
                "years_experience": 9
            }
        ]

        for comp_data in demo_competitors:
            competitor = Competitor(**comp_data)
            self.competitors[competitor.competitor_id] = competitor

    async def _create_demo_opportunities(self) -> None:
        """Create demo market opportunities."""
        demo_opportunities = [
            {
                "opportunity_id": "opp_001",
                "area_id": "area_emerging",
                "opportunity_type": OpportunityType.EMERGING_NEIGHBORHOOD,
                "title": "Emerging District Growth Opportunity",
                "description": "Rapidly gentrifying neighborhood with 15% price appreciation potential",
                "confidence_score": 0.82,
                "potential_value": 450000,
                "effort_level": "medium",
                "time_sensitivity": "moderate",
                "recommended_actions": [
                    "Build relationships with local developers",
                    "Focus on first-time buyer marketing",
                    "Create neighborhood expertise content"
                ],
                "supporting_data": {
                    "new_businesses": 12,
                    "planned_developments": 3,
                    "infrastructure_improvements": ["new metro line", "park renovation"],
                    "price_trend": "upward"
                }
            },
            {
                "opportunity_id": "opp_002",
                "area_id": "area_luxury",
                "opportunity_type": OpportunityType.UNDERVALUED_PROPERTY,
                "title": "Luxury Market Price Corrections",
                "description": "Several luxury properties listed below market value due to seller urgency",
                "confidence_score": 0.75,
                "potential_value": 850000,
                "effort_level": "high",
                "time_sensitivity": "urgent",
                "recommended_actions": [
                    "Contact high-net-worth client network",
                    "Prepare market analysis reports",
                    "Schedule exclusive previews"
                ],
                "supporting_data": {
                    "undervalued_properties": 5,
                    "avg_discount": 12.5,
                    "motivated_sellers": 3,
                    "luxury_demand": "steady"
                }
            },
            {
                "opportunity_id": "opp_003",
                "area_id": "area_downtown",
                "opportunity_type": OpportunityType.INVESTMENT_OPPORTUNITY,
                "title": "Downtown Condo Investment Wave",
                "description": "Strong rental market creating investment opportunities in downtown condos",
                "confidence_score": 0.88,
                "potential_value": 325000,
                "effort_level": "low",
                "time_sensitivity": "moderate",
                "recommended_actions": [
                    "Develop investor client base",
                    "Partner with property management companies",
                    "Create ROI analysis tools"
                ],
                "supporting_data": {
                    "rental_yield": 6.8,
                    "occupancy_rate": 94.5,
                    "rent_growth": 8.2,
                    "investor_interest": "high"
                }
            }
        ]

        for opp_data in demo_opportunities:
            opportunity = MarketOpportunity(
                **opp_data,
                created_date=datetime.now() - timedelta(days=random.randint(1, 10))
            )
            self.opportunities[opportunity.opportunity_id] = opportunity

    async def _create_demo_forecasts(self) -> None:
        """Create demo market forecasts."""
        for area_id in self.market_areas.keys():
            forecast = MarketForecast(
                area_id=area_id,
                forecast_date=datetime.now(),
                forecast_period_months=6,
                predicted_price_change=random.uniform(3.0, 12.0),
                predicted_inventory_change=random.uniform(-15.0, 25.0),
                predicted_sales_volume_change=random.uniform(-8.0, 18.0),
                confidence_level=random.uniform(0.65, 0.92),
                key_factors=[
                    "Interest rate stabilization",
                    "Economic growth indicators",
                    "Population growth trends",
                    "Infrastructure development"
                ],
                risk_factors=[
                    "Economic uncertainty",
                    "Interest rate volatility",
                    "Supply chain disruptions"
                ],
                opportunities=[
                    "First-time buyer programs",
                    "Investment property demand",
                    "Luxury market recovery"
                ]
            )
            self.forecasts[area_id] = forecast

    # Core Market Intelligence Methods

    async def get_market_overview(self, area_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get comprehensive market overview for specified areas."""
        if not area_ids:
            area_ids = list(self.market_areas.keys())

        overview = {
            "areas": [],
            "summary_metrics": {},
            "trends": {},
            "generated_at": datetime.now().isoformat()
        }

        total_sales = 0
        total_inventory = 0
        price_changes = []

        for area_id in area_ids:
            if area_id in self.market_metrics:
                area = self.market_areas[area_id]
                metrics = self.market_metrics[area_id]
                trend = metrics.calculate_market_trend()

                area_data = {
                    "area_id": area_id,
                    "name": area.name,
                    "zip_codes": area.zip_codes,
                    "metrics": {
                        "avg_sale_price": metrics.avg_sale_price,
                        "median_sale_price": metrics.median_sale_price,
                        "days_on_market": metrics.days_on_market,
                        "inventory_months": metrics.inventory_months,
                        "price_change_30d": metrics.price_change_30d,
                        "total_sales": metrics.total_sales,
                        "absorption_rate": metrics.absorption_rate
                    },
                    "trend": trend.value,
                    "trend_indicator": self._get_trend_indicator(trend)
                }

                overview["areas"].append(area_data)
                total_sales += metrics.total_sales
                total_inventory += metrics.inventory_months
                price_changes.append(metrics.price_change_30d)

        # Calculate summary metrics
        if area_ids:
            overview["summary_metrics"] = {
                "total_areas": len(area_ids),
                "total_sales": total_sales,
                "avg_inventory_months": total_inventory / len(area_ids),
                "avg_price_change_30d": sum(price_changes) / len(price_changes),
                "market_health_score": self._calculate_market_health_score(overview["areas"])
            }

        return overview

    def _get_trend_indicator(self, trend: MarketTrend) -> str:
        """Get visual trend indicator."""
        indicators = {
            MarketTrend.STRONG_BUYER: "📉 Strong Buyer Market",
            MarketTrend.BUYER_MARKET: "📊 Buyer Market",
            MarketTrend.BALANCED: "⚖️ Balanced Market",
            MarketTrend.SELLER_MARKET: "📈 Seller Market",
            MarketTrend.STRONG_SELLER: "🚀 Strong Seller Market"
        }
        return indicators.get(trend, "❓ Unknown")

    def _calculate_market_health_score(self, areas: List[Dict]) -> float:
        """Calculate overall market health score."""
        if not areas:
            return 0.0

        score = 0
        for area in areas:
            metrics = area["metrics"]

            # Positive factors
            if metrics["absorption_rate"] > 60:
                score += 1
            if metrics["price_change_30d"] > 0:
                score += 1
            if metrics["days_on_market"] < 30:
                score += 1
            if 2 <= metrics["inventory_months"] <= 6:
                score += 1

        return (score / (len(areas) * 4)) * 100

    async def get_competitive_analysis(self, area_id: str) -> Dict[str, Any]:
        """Get competitive analysis for a specific area."""
        area_competitors = [
            comp for comp in self.competitors.values()
            if area_id in comp.territory_areas
        ]

        if not area_competitors:
            return {"message": "No competitor data available for this area"}

        analysis = {
            "area_id": area_id,
            "area_name": self.market_areas[area_id].name,
            "total_competitors": len(area_competitors),
            "competitors": [],
            "market_dynamics": {},
            "competitive_gaps": [],
            "recommendations": []
        }

        total_market_share = 0
        total_recent_sales = 0
        specialties_count = {}

        for comp in area_competitors:
            competitor_data = {
                "name": comp.name,
                "agency": comp.agency,
                "market_share": comp.market_share,
                "recent_sales": comp.recent_sales,
                "avg_sale_price": comp.avg_sale_price,
                "activity_level": comp.activity_level.value,
                "specialties": [s.value for s in comp.specialties],
                "strengths": comp.strengths,
                "client_rating": comp.client_reviews_avg,
                "experience": comp.years_experience
            }
            analysis["competitors"].append(competitor_data)

            total_market_share += comp.market_share
            total_recent_sales += comp.recent_sales

            for specialty in comp.specialties:
                specialties_count[specialty.value] = specialties_count.get(specialty.value, 0) + 1

        # Market dynamics
        analysis["market_dynamics"] = {
            "concentration_level": "high" if total_market_share > 60 else "moderate" if total_market_share > 40 else "low",
            "activity_level": "high" if total_recent_sales > 100 else "moderate" if total_recent_sales > 50 else "low",
            "top_specialties": sorted(specialties_count.items(), key=lambda x: x[1], reverse=True)[:3],
            "market_share_captured": total_market_share
        }

        # Identify gaps
        all_specialties = set([s.value for s in PropertyType])
        covered_specialties = set(specialties_count.keys())
        uncovered_specialties = all_specialties - covered_specialties

        analysis["competitive_gaps"] = list(uncovered_specialties)

        # Generate recommendations
        recommendations = []
        if uncovered_specialties:
            recommendations.append(f"Consider specializing in {', '.join(list(uncovered_specialties)[:2])} as these markets have less competition")

        if total_market_share < 70:
            recommendations.append("Market has room for new entrants - opportunity for market share growth")

        if len([c for c in area_competitors if c.social_media_presence > 7]) < 2:
            recommendations.append("Strong social media presence could provide competitive advantage")

        analysis["recommendations"] = recommendations

        return analysis

    async def get_market_opportunities(
        self,
        area_id: Optional[str] = None,
        opportunity_type: Optional[OpportunityType] = None,
        min_confidence: float = 0.0
    ) -> List[MarketOpportunity]:
        """Get market opportunities with optional filters."""
        opportunities = list(self.opportunities.values())

        # Apply filters
        if area_id:
            opportunities = [o for o in opportunities if o.area_id == area_id]

        if opportunity_type:
            opportunities = [o for o in opportunities if o.opportunity_type == opportunity_type]

        if min_confidence > 0:
            opportunities = [o for o in opportunities if o.confidence_score >= min_confidence]

        # Sort by confidence score and potential value
        opportunities.sort(
            key=lambda x: (x.confidence_score * x.potential_value),
            reverse=True
        )

        return opportunities

    async def get_market_forecast(
        self,
        area_id: str,
        forecast_months: int = 6
    ) -> Optional[MarketForecast]:
        """Get market forecast for a specific area."""
        if area_id in self.forecasts:
            forecast = self.forecasts[area_id]

            # Update forecast period if different
            if forecast_months != forecast.forecast_period_months:
                # Adjust predictions based on timeframe
                adjustment_factor = forecast_months / forecast.forecast_period_months

                updated_forecast = MarketForecast(
                    area_id=forecast.area_id,
                    forecast_date=datetime.now(),
                    forecast_period_months=forecast_months,
                    predicted_price_change=forecast.predicted_price_change * adjustment_factor,
                    predicted_inventory_change=forecast.predicted_inventory_change * adjustment_factor,
                    predicted_sales_volume_change=forecast.predicted_sales_volume_change * adjustment_factor,
                    confidence_level=max(0.5, forecast.confidence_level - (adjustment_factor - 1) * 0.1),
                    key_factors=forecast.key_factors,
                    risk_factors=forecast.risk_factors,
                    opportunities=forecast.opportunities
                )
                return updated_forecast

            return forecast

        return None

    async def analyze_price_trends(self, area_id: str) -> Dict[str, Any]:
        """Analyze detailed price trends for an area."""
        if area_id not in self.market_metrics or area_id not in self.historical_data:
            return {"error": "No data available for this area"}

        current_metrics = self.market_metrics[area_id]
        historical = self.historical_data[area_id]

        # Sort historical data by date
        historical.sort(key=lambda x: x.report_date)

        trend_analysis = {
            "area_id": area_id,
            "area_name": self.market_areas[area_id].name,
            "current_metrics": {
                "avg_sale_price": current_metrics.avg_sale_price,
                "median_sale_price": current_metrics.median_sale_price,
                "price_per_sqft": current_metrics.price_per_sqft,
                "days_on_market": current_metrics.days_on_market,
                "inventory_months": current_metrics.inventory_months
            },
            "trend_data": [],
            "price_trajectory": "",
            "market_velocity": "",
            "recommendations": []
        }

        # Analyze historical trends
        for i, metrics in enumerate(historical[-6:]):  # Last 6 months
            trend_data = {
                "month": metrics.report_date.strftime("%Y-%m"),
                "avg_sale_price": metrics.avg_sale_price,
                "median_sale_price": metrics.median_sale_price,
                "price_per_sqft": metrics.price_per_sqft,
                "days_on_market": metrics.days_on_market,
                "total_sales": metrics.total_sales
            }
            trend_analysis["trend_data"].append(trend_data)

        # Calculate trajectory
        if len(historical) >= 3:
            recent_prices = [h.avg_sale_price for h in historical[-3:]]
            if all(recent_prices[i] <= recent_prices[i+1] for i in range(len(recent_prices)-1)):
                trend_analysis["price_trajectory"] = "Consistently Rising"
            elif all(recent_prices[i] >= recent_prices[i+1] for i in range(len(recent_prices)-1)):
                trend_analysis["price_trajectory"] = "Consistently Declining"
            else:
                trend_analysis["price_trajectory"] = "Fluctuating"

        # Market velocity analysis
        avg_dom = sum(h.days_on_market for h in historical[-3:]) / 3
        if avg_dom < 20:
            trend_analysis["market_velocity"] = "Fast-Moving"
        elif avg_dom < 40:
            trend_analysis["market_velocity"] = "Moderate"
        else:
            trend_analysis["market_velocity"] = "Slow-Moving"

        # Generate recommendations
        recommendations = []

        if trend_analysis["price_trajectory"] == "Consistently Rising":
            recommendations.append("Consider advising buyers to act quickly to avoid higher prices")
            recommendations.append("Good time for sellers to list properties")

        if trend_analysis["market_velocity"] == "Fast-Moving":
            recommendations.append("Prepare offers quickly and consider above-asking strategies")

        if current_metrics.inventory_months < 3:
            recommendations.append("Limited inventory - focus on off-market opportunities")

        trend_analysis["recommendations"] = recommendations

        return trend_analysis

    # Helper Methods

    async def get_market_areas(self) -> List[MarketArea]:
        """Get all available market areas."""
        return list(self.market_areas.values())

    async def get_area_demographics(self, area_id: str) -> Optional[Dict[str, Any]]:
        """Get demographic information for an area."""
        if area_id not in self.market_areas:
            return None

        area = self.market_areas[area_id]
        return {
            "area_id": area_id,
            "name": area.name,
            "population": area.population,
            "median_income": area.median_income,
            "primary_demographics": area.primary_demographics,
            "zip_codes": area.zip_codes
        }

    async def compare_market_areas(self, area_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple market areas."""
        if not all(area_id in self.market_areas for area_id in area_ids):
            return {"error": "One or more areas not found"}

        comparison = {
            "areas": [],
            "comparative_analysis": {},
            "recommendations": []
        }

        areas_data = []
        for area_id in area_ids:
            area = self.market_areas[area_id]
            metrics = self.market_metrics.get(area_id)

            if metrics:
                area_data = {
                    "area_id": area_id,
                    "name": area.name,
                    "population": area.population,
                    "median_income": area.median_income,
                    "avg_sale_price": metrics.avg_sale_price,
                    "median_sale_price": metrics.median_sale_price,
                    "days_on_market": metrics.days_on_market,
                    "price_change_30d": metrics.price_change_30d,
                    "inventory_months": metrics.inventory_months,
                    "market_trend": metrics.calculate_market_trend().value
                }
                areas_data.append(area_data)

        comparison["areas"] = areas_data

        # Comparative analysis
        if areas_data:
            price_ranges = [a["avg_sale_price"] for a in areas_data]
            dom_values = [a["days_on_market"] for a in areas_data]

            comparison["comparative_analysis"] = {
                "highest_priced_area": max(areas_data, key=lambda x: x["avg_sale_price"])["name"],
                "lowest_priced_area": min(areas_data, key=lambda x: x["avg_sale_price"])["name"],
                "fastest_moving_area": min(areas_data, key=lambda x: x["days_on_market"])["name"],
                "price_variance": max(price_ranges) - min(price_ranges),
                "dom_variance": max(dom_values) - min(dom_values)
            }

            # Generate recommendations
            recommendations = []
            fastest_area = min(areas_data, key=lambda x: x["days_on_market"])
            recommendations.append(f"{fastest_area['name']} shows fastest market activity - good for quick sales")

            highest_appreciation = max(areas_data, key=lambda x: x["price_change_30d"])
            recommendations.append(f"{highest_appreciation['name']} shows strongest price appreciation trends")

            comparison["recommendations"] = recommendations

        return comparison

# Global service instance
market_intelligence_service = MarketIntelligenceService()

# Helper functions for easy access
async def get_market_overview(area_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Helper function to get market overview."""
    return await market_intelligence_service.get_market_overview(area_ids)

async def get_competitive_analysis(area_id: str) -> Dict[str, Any]:
    """Helper function to get competitive analysis."""
    return await market_intelligence_service.get_competitive_analysis(area_id)

async def get_market_opportunities(area_id: Optional[str] = None) -> List[MarketOpportunity]:
    """Helper function to get market opportunities."""
    return await market_intelligence_service.get_market_opportunities(area_id)

async def analyze_price_trends(area_id: str) -> Dict[str, Any]:
    """Helper function to analyze price trends."""
    return await market_intelligence_service.analyze_price_trends(area_id)

if __name__ == "__main__":
    # Test the service
    async def test_service():
        service = MarketIntelligenceService()
        await asyncio.sleep(1)  # Wait for demo data

        # Test market overview
        overview = await service.get_market_overview()
        print(f"Market Overview: {len(overview['areas'])} areas analyzed")

        # Test competitive analysis
        competition = await service.get_competitive_analysis("area_downtown")
        print(f"Competition Analysis: {competition.get('total_competitors', 0)} competitors found")

        # Test opportunities
        opportunities = await service.get_market_opportunities(min_confidence=0.7)
        print(f"Market Opportunities: {len(opportunities)} high-confidence opportunities")

        # Test price trends
        trends = await service.analyze_price_trends("area_luxury")
        print(f"Price Trends: {trends.get('price_trajectory', 'Unknown')} trajectory")

    asyncio.run(test_service())