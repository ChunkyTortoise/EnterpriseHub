"""
Market Intelligence Engine for Austin Real Estate Market Analysis

Provides comprehensive geospatial analytics, market heatmap generation, and real-time
market intelligence for Jorge's Real Estate AI Platform. Optimized for Austin, Texas
market with neighborhood-level granularity and lead density analysis.

Performance Targets:
- Market heatmap generation: <50ms (database aggregation + geospatial calculation)
- Real-time metric calculation: <100ms (parallel processing)
- WebSocket event delivery: <10ms
- Cache hit rate: >70% with intelligent TTL management

Features:
- Lead density heatmaps for Deck.gl visualization
- Neighborhood-level market analysis
- Conversion rate tracking by geographic zone
- Hot zone detection with automated alerting
- Real-time market condition monitoring
"""

import asyncio
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from geopy.distance import geodesic

from ghl_real_estate_ai.api.schemas.analytics import (
    Granularity,
    MarketHeatmapDataPoint,
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)


@dataclass
class GeoBounds:
    """Geographic boundary definition for market regions."""

    north: float
    south: float
    east: float
    west: float
    center_lat: float
    center_lng: float

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "GeoBounds":
        """Create GeoBounds from dictionary with automatic center calculation."""
        return cls(
            north=data["north"],
            south=data["south"],
            east=data["east"],
            west=data["west"],
            center_lat=(data["north"] + data["south"]) / 2,
            center_lng=(data["east"] + data["west"]) / 2,
        )


@dataclass
class NeighborhoodProfile:
    """Complete neighborhood profile with market intelligence."""

    name: str
    bounds: GeoBounds
    centroid_lat: float
    centroid_lng: float
    lead_count: int
    avg_ml_score: float
    conversion_rate: float
    avg_deal_value: float
    hot_zone_score: float
    market_trend: str  # "increasing", "stable", "decreasing"
    last_updated: datetime


@dataclass
class HotZoneAlert:
    """Alert for newly detected hot zones requiring attention."""

    zone_name: str
    lat: float
    lng: float
    score: float
    contributing_factors: List[str]
    recommended_actions: List[str]
    urgency: str  # "critical", "high", "medium"
    detected_at: datetime


class MarketTrend(str, Enum):
    """Market trend classifications."""

    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"
    VOLATILE = "volatile"


class MarketIntelligenceEngine:
    """
    Comprehensive market intelligence engine for Austin real estate market.

    Provides geospatial analytics, lead density analysis, conversion tracking,
    and automated hot zone detection with real-time alerting capabilities.
    """

    def __init__(self):
        """Initialize market intelligence engine with Austin-specific configuration."""

        self.cache_service = get_cache_service()
        self.event_publisher = get_event_publisher()

        # Austin market boundaries (expanded for metro area coverage)
        self.austin_bounds = GeoBounds(
            north=30.5168,  # North Austin/Round Rock
            south=30.0986,  # South Austin/Buda
            east=-97.5684,  # East Austin
            west=-97.9383,  # West Lake Hills
            center_lat=30.2672,
            center_lng=-97.7431,
        )

        # Austin neighborhood definitions with market intelligence
        self.neighborhoods = self._initialize_austin_neighborhoods()

        # Hot zone detection thresholds
        self.hot_zone_thresholds = {
            "lead_density_min": 50.0,  # Leads per square mile
            "conversion_rate_min": 0.15,  # 15% conversion minimum
            "ml_score_min": 75.0,  # ML score threshold
            "combined_score_min": 80.0,  # Combined hot zone score
        }

        # Performance tracking
        self._performance_metrics = {
            "heatmap_requests": 0,
            "avg_response_time_ms": 0.0,
            "cache_hits": 0,
            "hot_zones_detected": 0,
            "last_reset": datetime.utcnow(),
        }

        logger.info(
            f"MarketIntelligenceEngine initialized for Austin market with {len(self.neighborhoods)} neighborhoods"
        )

    def _initialize_austin_neighborhoods(self) -> List[NeighborhoodProfile]:
        """Initialize Austin neighborhood profiles with current market data."""

        neighborhoods_data = [
            {
                "name": "Downtown Austin",
                "centroid_lat": 30.2672,
                "centroid_lng": -97.7431,
                "bounds": {"north": 30.2750, "south": 30.2594, "east": -97.7300, "west": -97.7562},
            },
            {
                "name": "South Congress",
                "centroid_lat": 30.2515,
                "centroid_lng": -97.7481,
                "bounds": {"north": 30.2600, "south": 30.2430, "east": -97.7350, "west": -97.7612},
            },
            {
                "name": "East Austin",
                "centroid_lat": 30.2713,
                "centroid_lng": -97.7156,
                "bounds": {"north": 30.2850, "south": 30.2576, "east": -97.7000, "west": -97.7312},
            },
            {
                "name": "West Lake Hills",
                "centroid_lat": 30.2733,
                "centroid_lng": -97.8089,
                "bounds": {"north": 30.2900, "south": 30.2566, "east": -97.7800, "west": -97.8378},
            },
            {
                "name": "North Austin",
                "centroid_lat": 30.3878,
                "centroid_lng": -97.7272,
                "bounds": {"north": 30.4100, "south": 30.3656, "east": -97.7000, "west": -97.7544},
            },
            {
                "name": "Zilker/Barton Hills",
                "centroid_lat": 30.2669,
                "centroid_lng": -97.7731,
                "bounds": {"north": 30.2800, "south": 30.2538, "east": -97.7550, "west": -97.7912},
            },
            {
                "name": "Mueller",
                "centroid_lat": 30.2936,
                "centroid_lng": -97.7069,
                "bounds": {"north": 30.3050, "south": 30.2822, "east": -97.6900, "west": -97.7238},
            },
            {
                "name": "Tarrytown",
                "centroid_lat": 30.2869,
                "centroid_lng": -97.7661,
                "bounds": {"north": 30.2980, "south": 30.2758, "east": -97.7500, "west": -97.7822},
            },
            {
                "name": "Cedar Park",
                "centroid_lat": 30.5052,
                "centroid_lng": -97.8203,
                "bounds": {"north": 30.5200, "south": 30.4904, "east": -97.8000, "west": -97.8406},
            },
            {
                "name": "Round Rock",
                "centroid_lat": 30.5083,
                "centroid_lng": -97.6789,
                "bounds": {"north": 30.5250, "south": 30.4916, "east": -97.6500, "west": -97.7078},
            },
        ]

        neighborhoods = []
        for data in neighborhoods_data:
            bounds = GeoBounds.from_dict(data["bounds"])

            # Initialize with default market data (in production, load from database)
            neighborhood = NeighborhoodProfile(
                name=data["name"],
                bounds=bounds,
                centroid_lat=data["centroid_lat"],
                centroid_lng=data["centroid_lng"],
                lead_count=0,  # Will be updated with real data
                avg_ml_score=0.0,
                conversion_rate=0.0,
                avg_deal_value=0.0,
                hot_zone_score=0.0,
                market_trend=MarketTrend.STABLE.value,
                last_updated=datetime.utcnow(),
            )
            neighborhoods.append(neighborhood)

        return neighborhoods

    async def generate_lead_density_heatmap(
        self,
        time_range_days: int = 30,
        granularity: Granularity = Granularity.NEIGHBORHOOD,
        min_threshold: Optional[float] = None,
    ) -> List[MarketHeatmapDataPoint]:
        """
        Generate lead density heatmap data for Deck.gl HexagonLayer visualization.

        Performance target: <50ms (database aggregation + geospatial calculation)
        Cache strategy: 5-minute TTL with automatic invalidation on new leads

        Args:
            time_range_days: Time range for lead aggregation
            granularity: Geographic granularity level
            min_threshold: Minimum lead count threshold for inclusion

        Returns:
            List[MarketHeatmapDataPoint]: Heatmap data points for visualization

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If data processing fails
        """
        start_time = time.time()
        self._performance_metrics["heatmap_requests"] += 1

        try:
            # Validate inputs
            if time_range_days <= 0 or time_range_days > 365:
                raise ValueError("time_range_days must be between 1 and 365")

            # Generate cache key
            cache_key = f"market:heatmap:lead_density:{time_range_days}:{granularity.value}:{min_threshold or 'all'}"
            cached_result = await self.cache_service.get(cache_key)

            if cached_result:
                self._performance_metrics["cache_hits"] += 1
                logger.debug(f"Cache hit for lead density heatmap: {granularity.value}")

                processing_time_ms = (time.time() - start_time) * 1000
                self._update_performance_metrics(processing_time_ms)

                return [MarketHeatmapDataPoint(**point) for point in cached_result]

            # Query lead data with location information
            logger.debug(f"Generating lead density heatmap for {time_range_days} days at {granularity.value} level")

            leads_with_location = await self._query_leads_with_location(time_range_days)

            # Aggregate by specified granularity
            if granularity == Granularity.NEIGHBORHOOD:
                aggregated_data = await self._aggregate_by_neighborhood(leads_with_location)
            elif granularity == Granularity.ZIPCODE:
                aggregated_data = await self._aggregate_by_zipcode(leads_with_location)
            else:
                aggregated_data = await self._aggregate_by_city(leads_with_location)

            # Apply minimum threshold filter
            if min_threshold:
                aggregated_data = [data for data in aggregated_data if data["lead_count"] >= min_threshold]

            # Convert to heatmap data points
            heatmap_data = []
            for data in aggregated_data:
                heatmap_point = MarketHeatmapDataPoint(
                    lat=data["centroid_lat"],
                    lng=data["centroid_lng"],
                    value=data["lead_count"],
                    label=data["name"],
                    metadata={
                        "avg_ml_score": round(data.get("avg_ml_score", 0.0), 1),
                        "hot_leads": data.get("hot_lead_count", 0),
                        "conversion_rate": round(data.get("conversion_rate", 0.0), 3),
                        "total_leads": data["lead_count"],
                        "market_trend": data.get("market_trend", "stable"),
                        "avg_deal_value": data.get("avg_deal_value", 0),
                    },
                )
                heatmap_data.append(heatmap_point)

            # Cache result with 5-minute TTL
            cache_data = [asdict(point) for point in heatmap_data]
            await self.cache_service.set(cache_key, cache_data, ttl=300)

            # Publish real-time update event
            await self._publish_market_update_event("lead_density", heatmap_data)

            # Update performance metrics
            processing_time_ms = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time_ms)

            logger.info(f"Lead density heatmap generated with {len(heatmap_data)} points in {processing_time_ms:.1f}ms")
            return heatmap_data

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Lead density heatmap generation failed: {e} (took {processing_time_ms:.1f}ms)")
            raise RuntimeError(f"Failed to generate lead density heatmap: {str(e)}")

    async def calculate_market_metrics(self, region: str = "austin_tx", time_range_days: int = 30) -> Dict[str, Any]:
        """
        Calculate comprehensive market intelligence metrics with parallel processing.

        Performance target: <100ms (parallel calculation of all metrics)
        Returns lead density, conversion rates, deal values, and hot zones

        Args:
            region: Geographic region identifier
            time_range_days: Time range for metric calculation

        Returns:
            Dict[str, Any]: Comprehensive market metrics with hot zones

        Raises:
            ValueError: If parameters are invalid
        """
        start_time = time.time()

        try:
            # Validate inputs
            if time_range_days <= 0:
                raise ValueError("time_range_days must be positive")

            cache_key = f"market:metrics:{region}:{time_range_days}"
            cached_result = await self.cache_service.get(cache_key)

            if cached_result:
                logger.debug(f"Cache hit for market metrics: {region}")
                return cached_result

            logger.info(f"Calculating comprehensive market metrics for {region}")

            # Parallel calculation of all market metrics for performance
            tasks = [
                self.generate_lead_density_heatmap(time_range_days, Granularity.NEIGHBORHOOD),
                self._calculate_conversion_rates(time_range_days),
                self._calculate_avg_deal_values(time_range_days),
                self._analyze_market_trends(time_range_days),
            ]

            lead_density_data, conversion_rates, deal_values, trends = await asyncio.gather(*tasks)

            # Identify hot zones using combined scoring
            hot_zones = await self._identify_hot_zones(lead_density_data, conversion_rates, deal_values, trends)

            # Compile comprehensive metrics
            metrics = {
                "lead_density": {
                    "total_leads": sum(point.value for point in lead_density_data),
                    "avg_per_zone": statistics.mean([point.value for point in lead_density_data])
                    if lead_density_data
                    else 0,
                    "max_zone": max(lead_density_data, key=lambda p: p.value).label if lead_density_data else None,
                    "zones_analyzed": len(lead_density_data),
                },
                "conversion_rates": {
                    "market_avg": conversion_rates.get("market_avg", 0.0),
                    "best_zone": conversion_rates.get("best_zone", {}),
                    "worst_zone": conversion_rates.get("worst_zone", {}),
                    "trend": conversion_rates.get("trend", "stable"),
                },
                "deal_values": {
                    "market_median": deal_values.get("median", 0),
                    "premium_zones": deal_values.get("premium_zones", []),
                    "growth_rate": deal_values.get("growth_rate", 0.0),
                    "trend": deal_values.get("trend", "stable"),
                },
                "market_trends": trends,
                "hot_zones": [asdict(zone) for zone in hot_zones],
                "analysis_summary": {
                    "total_zones_analyzed": len(self.neighborhoods),
                    "hot_zones_count": len(hot_zones),
                    "market_health_score": self._calculate_market_health_score(conversion_rates, deal_values, trends),
                    "recommended_focus_areas": self._generate_focus_recommendations(hot_zones),
                },
                "calculated_at": datetime.utcnow().isoformat(),
                "time_range_days": time_range_days,
            }

            # Cache comprehensive metrics with 5-minute TTL
            await self.cache_service.set(cache_key, metrics, ttl=300)

            # Check for new hot zones and publish alerts
            await self._check_and_publish_hot_zone_alerts(hot_zones)

            processing_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Market metrics calculated in {processing_time_ms:.1f}ms with {len(hot_zones)} hot zones")

            return metrics

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Market metrics calculation failed: {e} (took {processing_time_ms:.1f}ms)")
            raise RuntimeError(f"Failed to calculate market metrics: {str(e)}")

    async def _query_leads_with_location(self, days: int) -> List[Dict[str, Any]]:
        """
        Query leads with location data from the database.

        In production, this interfaces with the actual lead database to extract
        geographic coordinates, ML scores, and lead status information.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        logger.debug(f"Querying leads with location from {start_date} to {end_date}")

        # Mock lead data for development (replace with actual database query)
        # In production: SELECT lead_id, lat, lng, ml_score, status, created_at FROM leads...
        leads = []

        for neighborhood in self.neighborhoods:
            # Generate realistic lead data for each neighborhood
            lead_count = np.random.randint(10, 50)  # Random lead count

            for i in range(lead_count):
                # Generate coordinates within neighborhood bounds
                lat = np.random.uniform(neighborhood.bounds.south, neighborhood.bounds.north)
                lng = np.random.uniform(neighborhood.bounds.west, neighborhood.bounds.east)

                # Generate realistic ML score with neighborhood bias
                base_score = {
                    "Downtown Austin": 78.5,
                    "West Lake Hills": 82.3,
                    "South Congress": 75.2,
                    "East Austin": 69.8,
                    "Mueller": 81.4,
                }.get(neighborhood.name, 72.0)

                ml_score = np.random.normal(base_score, 8.0)
                ml_score = max(0, min(100, ml_score))  # Clamp to 0-100

                leads.append(
                    {
                        "lead_id": f"lead_{neighborhood.name.replace(' ', '_')}_{i}",
                        "lat": lat,
                        "lng": lng,
                        "ml_score": ml_score,
                        "status": np.random.choice(
                            ["active", "converted", "nurture", "disqualified"], p=[0.4, 0.15, 0.35, 0.1]
                        ),
                        "created_at": start_date + timedelta(days=np.random.randint(0, days)),
                        "deal_value": np.random.randint(300000, 800000) if np.random.random() > 0.5 else None,
                        "neighborhood": neighborhood.name,
                    }
                )

        logger.debug(f"Retrieved {len(leads)} leads with location data")
        return leads

    async def _aggregate_by_neighborhood(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate lead data by Austin neighborhoods with market intelligence."""

        aggregated = []

        for neighborhood in self.neighborhoods:
            # Filter leads within this neighborhood's bounds
            neighborhood_leads = [
                lead for lead in leads if self._point_in_bounds(lead["lat"], lead["lng"], neighborhood.bounds)
            ]

            if not neighborhood_leads:
                continue

            # Calculate neighborhood metrics
            total_leads = len(neighborhood_leads)
            converted_leads = [l for l in neighborhood_leads if l["status"] == "converted"]
            conversion_rate = len(converted_leads) / total_leads if total_leads > 0 else 0.0

            # ML score analysis
            ml_scores = [l["ml_score"] for l in neighborhood_leads]
            avg_ml_score = statistics.mean(ml_scores) if ml_scores else 0.0
            hot_leads = len([l for l in neighborhood_leads if l["ml_score"] >= 75.0])

            # Deal value analysis
            deal_values = [l["deal_value"] for l in neighborhood_leads if l["deal_value"]]
            avg_deal_value = statistics.mean(deal_values) if deal_values else 0

            # Market trend analysis (simplified - in production, use historical data)
            trend = self._analyze_neighborhood_trend(neighborhood_leads)

            aggregated.append(
                {
                    "name": neighborhood.name,
                    "centroid_lat": neighborhood.centroid_lat,
                    "centroid_lng": neighborhood.centroid_lng,
                    "lead_count": total_leads,
                    "avg_ml_score": avg_ml_score,
                    "hot_lead_count": hot_leads,
                    "conversion_rate": conversion_rate,
                    "avg_deal_value": avg_deal_value,
                    "market_trend": trend,
                    "bounds": asdict(neighborhood.bounds),
                }
            )

        return aggregated

    async def _aggregate_by_zipcode(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate lead data by ZIP code (simplified for Austin market)."""

        # Austin ZIP code mappings (simplified)
        zipcode_centers = {
            "78701": {"lat": 30.2672, "lng": -97.7431, "name": "Downtown Austin"},
            "78704": {"lat": 30.2515, "lng": -97.7481, "name": "South Austin"},
            "78702": {"lat": 30.2713, "lng": -97.7156, "name": "East Austin"},
            "78746": {"lat": 30.2733, "lng": -97.8089, "name": "West Lake Hills"},
            "78759": {"lat": 30.3878, "lng": -97.7272, "name": "North Austin"},
        }

        aggregated = []

        for zipcode, center in zipcode_centers.items():
            # Assign leads to ZIP codes based on proximity (simplified)
            zip_leads = [
                lead
                for lead in leads
                if geodesic((lead["lat"], lead["lng"]), (center["lat"], center["lng"])).miles < 3.0
            ]

            if zip_leads:
                total_leads = len(zip_leads)
                converted = len([l for l in zip_leads if l["status"] == "converted"])
                conversion_rate = converted / total_leads if total_leads > 0 else 0.0
                avg_ml_score = statistics.mean([l["ml_score"] for l in zip_leads])

                aggregated.append(
                    {
                        "name": f"{center['name']} ({zipcode})",
                        "centroid_lat": center["lat"],
                        "centroid_lng": center["lng"],
                        "lead_count": total_leads,
                        "avg_ml_score": avg_ml_score,
                        "conversion_rate": conversion_rate,
                        "zipcode": zipcode,
                    }
                )

        return aggregated

    async def _aggregate_by_city(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate lead data by city level (Austin metro area)."""

        cities = {
            "Austin": {"bounds": self.austin_bounds, "leads": []},
            "Round Rock": {"bounds": GeoBounds(30.49, 30.53, -97.65, -97.72, 30.51, -97.685), "leads": []},
            "Cedar Park": {"bounds": GeoBounds(30.48, 30.52, -97.80, -97.85, 30.50, -97.825), "leads": []},
        }

        # Assign leads to cities
        for lead in leads:
            for city_name, city_data in cities.items():
                if self._point_in_bounds(lead["lat"], lead["lng"], city_data["bounds"]):
                    city_data["leads"].append(lead)
                    break

        aggregated = []
        for city_name, city_data in cities.items():
            city_leads = city_data["leads"]
            if city_leads:
                total_leads = len(city_leads)
                converted = len([l for l in city_leads if l["status"] == "converted"])
                conversion_rate = converted / total_leads if total_leads > 0 else 0.0
                avg_ml_score = statistics.mean([l["ml_score"] for l in city_leads])

                aggregated.append(
                    {
                        "name": city_name,
                        "centroid_lat": city_data["bounds"].center_lat,
                        "centroid_lng": city_data["bounds"].center_lng,
                        "lead_count": total_leads,
                        "avg_ml_score": avg_ml_score,
                        "conversion_rate": conversion_rate,
                    }
                )

        return aggregated

    def _point_in_bounds(self, lat: float, lng: float, bounds: GeoBounds) -> bool:
        """Check if a point is within geographic bounds."""
        return bounds.south <= lat <= bounds.north and bounds.west <= lng <= bounds.east

    def _analyze_neighborhood_trend(self, leads: List[Dict[str, Any]]) -> str:
        """Analyze market trend for a neighborhood based on lead patterns."""

        if len(leads) < 5:
            return MarketTrend.STABLE.value

        # Sort leads by creation date
        sorted_leads = sorted(leads, key=lambda l: l["created_at"])

        # Calculate trend based on ML score changes over time
        early_leads = sorted_leads[: len(sorted_leads) // 2]
        recent_leads = sorted_leads[len(sorted_leads) // 2 :]

        early_avg = statistics.mean([l["ml_score"] for l in early_leads])
        recent_avg = statistics.mean([l["ml_score"] for l in recent_leads])

        change = recent_avg - early_avg

        if change > 5.0:
            return MarketTrend.INCREASING.value
        elif change < -5.0:
            return MarketTrend.DECREASING.value
        else:
            return MarketTrend.STABLE.value

    async def _calculate_conversion_rates(self, time_range_days: int) -> Dict[str, Any]:
        """Calculate conversion rates across neighborhoods."""

        leads = await self._query_leads_with_location(time_range_days)
        neighborhood_data = await self._aggregate_by_neighborhood(leads)

        conversion_rates = [data["conversion_rate"] for data in neighborhood_data]
        market_avg = statistics.mean(conversion_rates) if conversion_rates else 0.0

        best_zone = max(neighborhood_data, key=lambda d: d["conversion_rate"]) if neighborhood_data else {}
        worst_zone = min(neighborhood_data, key=lambda d: d["conversion_rate"]) if neighborhood_data else {}

        return {
            "market_avg": market_avg,
            "best_zone": {"name": best_zone.get("name"), "rate": best_zone.get("conversion_rate")},
            "worst_zone": {"name": worst_zone.get("name"), "rate": worst_zone.get("conversion_rate")},
            "trend": "increasing" if market_avg > 0.12 else "stable",  # 12% baseline
        }

    async def _calculate_avg_deal_values(self, time_range_days: int) -> Dict[str, Any]:
        """Calculate average deal values across neighborhoods."""

        leads = await self._query_leads_with_location(time_range_days)
        deal_values = [l["deal_value"] for l in leads if l["deal_value"]]

        if not deal_values:
            return {"median": 0, "premium_zones": [], "growth_rate": 0.0, "trend": "stable"}

        median_value = statistics.median(deal_values)

        # Identify premium zones (top 20% by deal value)
        neighborhood_data = await self._aggregate_by_neighborhood(leads)
        sorted_by_value = sorted(neighborhood_data, key=lambda d: d["avg_deal_value"], reverse=True)
        premium_count = max(1, len(sorted_by_value) // 5)
        premium_zones = [
            {"name": zone["name"], "avg_value": zone["avg_deal_value"]}
            for zone in sorted_by_value[:premium_count]
            if zone["avg_deal_value"] > 0
        ]

        return {
            "median": median_value,
            "premium_zones": premium_zones,
            "growth_rate": 0.08,  # Simplified - in production, calculate from historical data
            "trend": "increasing",
        }

    async def _analyze_market_trends(self, time_range_days: int) -> Dict[str, Any]:
        """Analyze overall market trends across all metrics."""

        return {
            "overall_market_direction": "increasing",
            "lead_volume_trend": "stable",
            "quality_trend": "increasing",
            "geographic_shifts": ["East Austin growth", "West Lake Hills premium demand"],
            "seasonal_factors": ["Spring buying season", "Low inventory pressure"],
        }

    async def _identify_hot_zones(
        self,
        lead_density_data: List[MarketHeatmapDataPoint],
        conversion_rates: Dict[str, Any],
        deal_values: Dict[str, Any],
        trends: Dict[str, Any],
    ) -> List[HotZoneAlert]:
        """Identify hot zones requiring immediate attention using composite scoring."""

        hot_zones = []

        for point in lead_density_data:
            # Calculate composite hot zone score
            lead_density_score = min(100, (point.value / 50.0) * 100)  # Normalize to 100
            conversion_score = min(100, (point.metadata.get("conversion_rate", 0) / 0.20) * 100)
            ml_score = point.metadata.get("avg_ml_score", 0)

            composite_score = lead_density_score * 0.4 + conversion_score * 0.4 + ml_score * 0.2

            # Check if zone qualifies as hot zone
            if (
                composite_score >= self.hot_zone_thresholds["combined_score_min"]
                and point.value >= self.hot_zone_thresholds["lead_density_min"]
            ):
                # Determine contributing factors
                factors = []
                if point.value >= self.hot_zone_thresholds["lead_density_min"]:
                    factors.append("high_lead_density")
                if point.metadata.get("conversion_rate", 0) >= self.hot_zone_thresholds["conversion_rate_min"]:
                    factors.append("above_avg_conversion")
                if ml_score >= self.hot_zone_thresholds["ml_score_min"]:
                    factors.append("high_quality_leads")

                # Generate recommended actions
                actions = self._generate_hot_zone_actions(composite_score, factors)

                # Determine urgency level
                urgency = "critical" if composite_score >= 90 else "high"

                hot_zone = HotZoneAlert(
                    zone_name=point.label,
                    lat=point.lat,
                    lng=point.lng,
                    score=composite_score,
                    contributing_factors=factors,
                    recommended_actions=actions,
                    urgency=urgency,
                    detected_at=datetime.utcnow(),
                )

                hot_zones.append(hot_zone)

        # Sort by score (highest first)
        hot_zones.sort(key=lambda z: z.score, reverse=True)

        logger.info(f"Identified {len(hot_zones)} hot zones for immediate attention")
        return hot_zones

    def _generate_hot_zone_actions(self, score: float, factors: List[str]) -> List[str]:
        """Generate recommended actions for hot zones based on factors."""

        actions = []

        if "high_lead_density" in factors:
            actions.append("increase_agent_allocation")
            actions.append("schedule_market_visit")

        if "above_avg_conversion" in factors:
            actions.append("replicate_success_factors")
            actions.append("increase_marketing_budget")

        if "high_quality_leads" in factors:
            actions.append("deploy_premium_agents")
            actions.append("prioritize_follow_ups")

        if score >= 90:
            actions.append("establish_temporary_office")
            actions.append("urgent_market_analysis")

        return actions

    async def _check_and_publish_hot_zone_alerts(self, hot_zones: List[HotZoneAlert]):
        """Check for new hot zones and publish WebSocket alerts."""

        for zone in hot_zones:
            if zone.urgency in ["critical", "high"]:
                try:
                    await self.event_publisher.publish_hot_zone_detection(
                        zone_name=zone.zone_name,
                        lat=zone.lat,
                        lng=zone.lng,
                        score=zone.score,
                        factors=zone.contributing_factors,
                        actions=zone.recommended_actions,
                        urgency=zone.urgency,
                    )

                    self._performance_metrics["hot_zones_detected"] += 1
                    logger.info(f"Published hot zone alert for {zone.zone_name} (score: {zone.score:.1f})")

                except Exception as e:
                    logger.error(f"Failed to publish hot zone alert: {e}")

    def _calculate_market_health_score(
        self, conversion_rates: Dict[str, Any], deal_values: Dict[str, Any], trends: Dict[str, Any]
    ) -> float:
        """Calculate overall market health score (0-100)."""

        # Weighted scoring based on key market indicators
        conversion_score = min(100, (conversion_rates.get("market_avg", 0) / 0.15) * 100)
        value_score = min(100, (deal_values.get("median", 0) / 500000) * 100)
        trend_score = 80 if trends.get("overall_market_direction") == "increasing" else 60

        health_score = conversion_score * 0.4 + value_score * 0.3 + trend_score * 0.3
        return round(health_score, 1)

    def _generate_focus_recommendations(self, hot_zones: List[HotZoneAlert]) -> List[str]:
        """Generate strategic focus recommendations based on hot zone analysis."""

        if not hot_zones:
            return ["monitor_market_conditions", "maintain_current_coverage"]

        recommendations = []

        # Analyze hot zone patterns
        critical_zones = [z for z in hot_zones if z.urgency == "critical"]
        high_zones = [z for z in hot_zones if z.urgency == "high"]

        if critical_zones:
            recommendations.append(f"immediate_deployment_{len(critical_zones)}_critical_zones")

        if high_zones:
            recommendations.append(f"prioritize_coverage_{len(high_zones)}_high_opportunity_zones")

        # Geographic clustering recommendations
        if len(hot_zones) >= 3:
            recommendations.append("consider_geographic_clustering_strategy")

        recommendations.append("increase_market_intelligence_monitoring")

        return recommendations

    async def _publish_market_update_event(self, metric_type: str, heatmap_data: List[MarketHeatmapDataPoint]):
        """Publish real-time market update event via WebSocket."""

        try:
            # Create summary for event
            total_leads = sum(point.value for point in heatmap_data)
            top_zone = max(heatmap_data, key=lambda p: p.value) if heatmap_data else None

            event_data = {
                "metric_type": metric_type,
                "total_data_points": len(heatmap_data),
                "total_value": total_leads,
                "top_performing_zone": {
                    "name": top_zone.label,
                    "value": top_zone.value,
                    "lat": top_zone.lat,
                    "lng": top_zone.lng,
                }
                if top_zone
                else None,
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Publish through existing event system
            await self.event_publisher.publish_dashboard_refresh(component="market_heatmap", data=event_data)

            logger.debug(f"Published market update event: {metric_type}")

        except Exception as e:
            logger.error(f"Failed to publish market update event: {e}")

    def _update_performance_metrics(self, processing_time_ms: float):
        """Update performance metrics for monitoring."""

        total_requests = self._performance_metrics["heatmap_requests"]
        current_avg = self._performance_metrics["avg_response_time_ms"]

        # Running average calculation
        new_avg = ((current_avg * (total_requests - 1)) + processing_time_ms) / total_requests
        self._performance_metrics["avg_response_time_ms"] = new_avg

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for monitoring."""

        cache_hit_rate = 0.0
        if self._performance_metrics["heatmap_requests"] > 0:
            cache_hit_rate = self._performance_metrics["cache_hits"] / self._performance_metrics["heatmap_requests"]

        return {
            "total_heatmap_requests": self._performance_metrics["heatmap_requests"],
            "avg_response_time_ms": self._performance_metrics["avg_response_time_ms"],
            "cache_hit_rate": cache_hit_rate,
            "hot_zones_detected": self._performance_metrics["hot_zones_detected"],
            "neighborhoods_monitored": len(self.neighborhoods),
            "target_response_time_ms": 50.0,
            "performance_status": "good"
            if self._performance_metrics["avg_response_time_ms"] < 50.0
            else "needs_optimization",
            "last_reset": self._performance_metrics["last_reset"].isoformat(),
        }


# ============================================================================
# Service Factory Functions
# ============================================================================

_market_intelligence_instance = None


def get_market_intelligence_engine() -> MarketIntelligenceEngine:
    """Get singleton instance of MarketIntelligenceEngine."""
    global _market_intelligence_instance

    if _market_intelligence_instance is None:
        _market_intelligence_instance = MarketIntelligenceEngine()

    return _market_intelligence_instance


if __name__ == "__main__":
    # Development/testing entry point
    import asyncio

    async def test_market_intelligence():
        """Test market intelligence functionality."""

        engine = get_market_intelligence_engine()

        # Test lead density heatmap
        try:
            heatmap = await engine.generate_lead_density_heatmap()
            print(f"Heatmap generated with {len(heatmap)} data points")
        except Exception as e:
            print(f"Heatmap test failed: {e}")

        # Test comprehensive metrics
        try:
            metrics = await engine.calculate_market_metrics()
            print(f"Market metrics calculated with {len(metrics['hot_zones'])} hot zones")
        except Exception as e:
            print(f"Metrics test failed: {e}")

        # Check performance
        performance = await engine.get_performance_metrics()
        print(f"Performance metrics: {performance}")

    # Run test
    asyncio.run(test_market_intelligence())
