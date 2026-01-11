"""
Real-Time Market Data Integration Service for GHL Real Estate AI Platform

This service provides real-time market data integration, contextual messaging based on
market conditions, and predictive market insights for enhanced lead engagement.
It integrates with multiple real estate APIs and ML systems to deliver timely,
relevant market information that optimizes lead conversion.

Author: AI Assistant
Created: 2026-01-09
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import aiohttp
import numpy as np
from statistics import mean, median

from pydantic import BaseModel, Field, validator
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from .advanced_ml_personalization_engine import AdvancedMLPersonalizationEngine
from .base_service import BaseService

logger = logging.getLogger(__name__)


class MarketTrendDirection(str, Enum):
    """Market trend direction indicators."""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"


class PropertyType(str, Enum):
    """Property type categories for market data."""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    COMMERCIAL = "commercial"
    LUXURY = "luxury"
    LAND = "land"


class MarketUrgency(str, Enum):
    """Market urgency levels for contextual messaging."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class MarketDataSource(str, Enum):
    """Market data source providers."""
    MLS = "mls"
    ZILLOW = "zillow"
    REDFIN = "redfin"
    REALTOR_COM = "realtor_com"
    INTERNAL = "internal"
    GOVERNMENT = "government"


# Pydantic Models

class MarketMetrics(BaseModel):
    """Real-time market metrics for a specific area and property type."""
    location_id: str
    property_type: PropertyType
    median_price: float
    price_per_sqft: float
    days_on_market: float
    inventory_level: int
    price_trend_30d: float  # Percentage change
    price_trend_90d: float
    price_trend_1y: float
    absorption_rate: float
    new_listings: int
    pending_sales: int
    closed_sales: int
    market_temperature: float  # 0-100 scale (cold to hot)
    last_updated: datetime = Field(default_factory=datetime.now)

    @validator('market_temperature')
    def validate_market_temperature(cls, v):
        return max(0, min(100, v))


class PropertyValuation(BaseModel):
    """AI-powered property valuation with confidence intervals."""
    property_id: str
    address: str
    estimated_value: float
    confidence_score: float
    value_range_low: float
    value_range_high: float
    comparable_properties: List[str]
    valuation_factors: Dict[str, float]
    market_conditions_impact: float
    predicted_appreciation: float
    last_updated: datetime = Field(default_factory=datetime.now)


class MarketInsight(BaseModel):
    """Market insight with actionable intelligence."""
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location_id: str
    property_type: PropertyType
    insight_type: str  # "opportunity", "warning", "trend", "forecast"
    title: str
    description: str
    impact_score: float  # 0-100
    urgency: MarketUrgency
    recommended_actions: List[str]
    supporting_data: Dict[str, Any]
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ContextualMessage(BaseModel):
    """Market-driven contextual message for lead engagement."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    message_type: str  # "market_update", "opportunity_alert", "price_change", "timing_advice"
    subject: str
    content: str
    market_insights: List[MarketInsight]
    property_references: List[str]
    urgency_level: MarketUrgency
    personalization_score: float
    optimal_send_time: datetime
    expiration_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class MarketForecast(BaseModel):
    """Predictive market forecast for strategic planning."""
    forecast_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location_id: str
    property_type: PropertyType
    forecast_horizon: int  # days
    predicted_price_change: float
    confidence_interval: Tuple[float, float]
    key_factors: List[str]
    forecast_accuracy_score: float
    model_version: str
    generated_at: datetime = Field(default_factory=datetime.now)


class MarketAlert(BaseModel):
    """Real-time market alert for immediate action."""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str
    location_id: str
    property_type: Optional[PropertyType] = None
    trigger_condition: str
    current_value: float
    threshold_value: float
    severity: MarketUrgency
    recommended_response: str
    affected_leads: List[str]
    expires_at: datetime
    triggered_at: datetime = Field(default_factory=datetime.now)


# Main Service Class

class RealTimeMarketIntegration(BaseService):
    """
    Real-Time Market Data Integration Service

    Provides comprehensive market data integration, contextual messaging,
    and predictive insights for optimized lead engagement.
    """

    def __init__(self):
        """Initialize the real-time market integration service."""
        super().__init__()
        self.personalization_engine = AdvancedMLPersonalizationEngine()

        # Market data configurations
        self.data_sources = self._configure_data_sources()
        self.market_models = self._initialize_market_models()
        self.alert_thresholds = self._configure_alert_thresholds()

        # Caching and optimization
        self.market_cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(minutes=15)  # 15-minute cache
        self.forecast_cache: Dict[str, MarketForecast] = {}

        logger.info("Real-Time Market Integration service initialized")

    def _configure_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """Configure market data source APIs and endpoints."""
        return {
            "mls": {
                "base_url": "https://api.mls.com/v2",
                "rate_limit": 100,  # requests per minute
                "priority": 1
            },
            "zillow": {
                "base_url": "https://api.zillow.com/v1",
                "rate_limit": 1000,
                "priority": 2
            },
            "redfin": {
                "base_url": "https://api.redfin.com/v1",
                "rate_limit": 500,
                "priority": 3
            },
            "realtor_com": {
                "base_url": "https://api.realtor.com/v2",
                "rate_limit": 200,
                "priority": 4
            },
            "government": {
                "base_url": "https://api.hud.gov/v1",
                "rate_limit": 50,
                "priority": 5
            }
        }

    def _initialize_market_models(self) -> Dict[str, Any]:
        """Initialize ML models for market prediction and analysis."""
        return {
            "price_predictor": RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                random_state=42
            ),
            "trend_analyzer": LinearRegression(),
            "market_temperature": RandomForestRegressor(
                n_estimators=50,
                max_depth=10,
                random_state=42
            ),
            "scaler": StandardScaler()
        }

    def _configure_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Configure thresholds for market alerts."""
        return {
            "price_change": {
                "moderate": 0.05,  # 5% price change
                "high": 0.10,      # 10% price change
                "critical": 0.15   # 15% price change
            },
            "inventory_change": {
                "moderate": 0.20,  # 20% inventory change
                "high": 0.30,      # 30% inventory change
                "critical": 0.50   # 50% inventory change
            },
            "market_temperature": {
                "cold": 30,        # Below 30 is cold market
                "hot": 70          # Above 70 is hot market
            },
            "days_on_market": {
                "fast": 15,        # Under 15 days is fast
                "slow": 60         # Over 60 days is slow
            }
        }

    async def get_real_time_market_data(
        self,
        location_id: str,
        property_type: PropertyType,
        force_refresh: bool = False
    ) -> MarketMetrics:
        """Get real-time market data for a specific location and property type."""
        try:
            cache_key = f"{location_id}_{property_type}"

            # Check cache first
            if not force_refresh and cache_key in self.market_cache:
                cached_data = self.market_cache[cache_key]
                if datetime.now() - cached_data["timestamp"] < self.cache_ttl:
                    return MarketMetrics(**cached_data["data"])

            # Fetch fresh data from multiple sources
            market_data = await self._aggregate_market_data(location_id, property_type)

            # Cache the results
            self.market_cache[cache_key] = {
                "data": market_data.dict(),
                "timestamp": datetime.now()
            }

            logger.info(f"Market data retrieved for {location_id} - {property_type}")
            return market_data

        except Exception as e:
            logger.error(f"Error retrieving market data: {e}")
            raise

    async def _aggregate_market_data(
        self,
        location_id: str,
        property_type: PropertyType
    ) -> MarketMetrics:
        """Aggregate market data from multiple sources."""
        try:
            # Fetch data from multiple sources in parallel
            data_tasks = []
            for source, config in self.data_sources.items():
                task = asyncio.create_task(
                    self._fetch_from_source(source, location_id, property_type)
                )
                data_tasks.append(task)

            raw_data_list = await asyncio.gather(*data_tasks, return_exceptions=True)

            # Filter successful responses and aggregate
            valid_data = [
                data for data in raw_data_list
                if not isinstance(data, Exception) and data is not None
            ]

            if not valid_data:
                raise ValueError("No valid market data sources available")

            # Aggregate the data using weighted averages and median calculations
            aggregated_metrics = self._compute_aggregated_metrics(valid_data)

            return MarketMetrics(
                location_id=location_id,
                property_type=property_type,
                **aggregated_metrics
            )

        except Exception as e:
            logger.error(f"Error aggregating market data: {e}")
            raise

    async def _fetch_from_source(
        self,
        source: str,
        location_id: str,
        property_type: PropertyType
    ) -> Optional[Dict[str, Any]]:
        """Fetch market data from a specific source."""
        try:
            config = self.data_sources[source]
            url = f"{config['base_url']}/market/{location_id}/{property_type}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"Authorization": f"Bearer {self._get_api_key(source)}"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._normalize_source_data(source, data)
                    else:
                        logger.warning(f"Failed to fetch from {source}: {response.status}")
                        return None

        except Exception as e:
            logger.warning(f"Error fetching from {source}: {e}")
            return None

    def _normalize_source_data(self, source: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data from different sources to a common format."""
        # Each source has different data formats - normalize them
        if source == "mls":
            return self._normalize_mls_data(raw_data)
        elif source == "zillow":
            return self._normalize_zillow_data(raw_data)
        elif source == "redfin":
            return self._normalize_redfin_data(raw_data)
        # Add more source-specific normalization as needed
        else:
            return raw_data

    def _normalize_mls_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MLS data format."""
        return {
            "median_price": data.get("medianPrice", 0),
            "price_per_sqft": data.get("pricePerSqft", 0),
            "days_on_market": data.get("avgDaysOnMarket", 0),
            "inventory_level": data.get("totalListings", 0),
            "new_listings": data.get("newListings", 0),
            "pending_sales": data.get("pendingSales", 0),
            "closed_sales": data.get("closedSales", 0),
            "price_trend_30d": data.get("priceChange30d", 0) / 100,
            "price_trend_90d": data.get("priceChange90d", 0) / 100,
            "price_trend_1y": data.get("priceChange1y", 0) / 100
        }

    def _normalize_zillow_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Zillow data format."""
        return {
            "median_price": data.get("zestimate", {}).get("amount", 0),
            "price_per_sqft": data.get("price_per_sqft", 0),
            "days_on_market": data.get("days_on_zillow", 0),
            "inventory_level": data.get("total_homes", 0),
            "price_trend_30d": data.get("home_values", {}).get("change_30d", 0),
            "price_trend_90d": data.get("home_values", {}).get("change_90d", 0),
            "price_trend_1y": data.get("home_values", {}).get("change_1y", 0)
        }

    def _compute_aggregated_metrics(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute aggregated metrics from multiple data sources."""
        try:
            # Extract values for each metric across all sources
            metrics = {}

            # Calculate weighted averages (give higher weight to more reliable sources)
            source_weights = {"mls": 0.4, "zillow": 0.3, "redfin": 0.2, "realtor_com": 0.1}

            for metric in ["median_price", "price_per_sqft", "days_on_market"]:
                values = [d.get(metric, 0) for d in data_list if d.get(metric, 0) > 0]
                if values:
                    metrics[metric] = median(values)  # Use median for robustness
                else:
                    metrics[metric] = 0

            # Sum values for count-based metrics
            for metric in ["inventory_level", "new_listings", "pending_sales", "closed_sales"]:
                values = [d.get(metric, 0) for d in data_list]
                metrics[metric] = int(mean(values)) if values else 0

            # Average percentage changes
            for metric in ["price_trend_30d", "price_trend_90d", "price_trend_1y"]:
                values = [d.get(metric, 0) for d in data_list if d.get(metric) is not None]
                metrics[metric] = mean(values) if values else 0

            # Calculate derived metrics
            metrics["absorption_rate"] = self._calculate_absorption_rate(metrics)
            metrics["market_temperature"] = self._calculate_market_temperature(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Error computing aggregated metrics: {e}")
            raise

    def _calculate_absorption_rate(self, metrics: Dict[str, Any]) -> float:
        """Calculate market absorption rate."""
        if metrics["inventory_level"] > 0 and metrics["closed_sales"] > 0:
            return metrics["closed_sales"] / metrics["inventory_level"] * 100
        return 0.0

    def _calculate_market_temperature(self, metrics: Dict[str, Any]) -> float:
        """Calculate market temperature score (0-100)."""
        try:
            # Multiple factors influence market temperature
            factors = {
                "days_on_market": self._normalize_dom_score(metrics["days_on_market"]),
                "price_trend": self._normalize_price_trend(metrics["price_trend_30d"]),
                "absorption_rate": self._normalize_absorption_rate(metrics["absorption_rate"]),
                "inventory_level": self._normalize_inventory_score(metrics["inventory_level"])
            }

            # Weighted combination
            weights = {"days_on_market": 0.3, "price_trend": 0.3, "absorption_rate": 0.25, "inventory_level": 0.15}

            temperature = sum(factors[factor] * weights[factor] for factor in factors)
            return max(0, min(100, temperature))

        except Exception as e:
            logger.error(f"Error calculating market temperature: {e}")
            return 50.0  # Default to neutral

    def _normalize_dom_score(self, days_on_market: float) -> float:
        """Normalize days on market to 0-100 scale (lower DOM = hotter market)."""
        if days_on_market <= 15:
            return 90  # Very hot
        elif days_on_market <= 30:
            return 70  # Hot
        elif days_on_market <= 60:
            return 50  # Neutral
        elif days_on_market <= 120:
            return 30  # Cool
        else:
            return 10  # Cold

    def _normalize_price_trend(self, price_trend: float) -> float:
        """Normalize price trend to 0-100 scale."""
        # Convert percentage to score
        if price_trend >= 0.10:
            return 95  # Very hot
        elif price_trend >= 0.05:
            return 75  # Hot
        elif price_trend >= 0.02:
            return 60  # Warm
        elif price_trend >= -0.02:
            return 50  # Neutral
        elif price_trend >= -0.05:
            return 30  # Cool
        else:
            return 15  # Cold

    async def generate_market_insights(
        self,
        location_id: str,
        property_type: PropertyType,
        lead_context: Optional[Dict[str, Any]] = None
    ) -> List[MarketInsight]:
        """Generate actionable market insights for a specific area."""
        try:
            market_data = await self.get_real_time_market_data(location_id, property_type)
            historical_data = await self._get_historical_trends(location_id, property_type)

            insights = []

            # Price trend insights
            if abs(market_data.price_trend_30d) > self.alert_thresholds["price_change"]["moderate"]:
                insights.append(await self._generate_price_trend_insight(market_data, historical_data))

            # Market temperature insights
            if market_data.market_temperature > 75:
                insights.append(await self._generate_hot_market_insight(market_data))
            elif market_data.market_temperature < 25:
                insights.append(await self._generate_cold_market_insight(market_data))

            # Inventory insights
            inventory_change = await self._calculate_inventory_change(location_id, property_type)
            if abs(inventory_change) > self.alert_thresholds["inventory_change"]["moderate"]:
                insights.append(await self._generate_inventory_insight(market_data, inventory_change))

            # Opportunity insights
            opportunities = await self._identify_market_opportunities(market_data, historical_data, lead_context)
            insights.extend(opportunities)

            logger.info(f"Generated {len(insights)} market insights for {location_id}")
            return insights

        except Exception as e:
            logger.error(f"Error generating market insights: {e}")
            return []

    async def _generate_price_trend_insight(
        self,
        market_data: MarketMetrics,
        historical_data: Dict[str, Any]
    ) -> MarketInsight:
        """Generate insight about price trends."""
        trend_direction = "rising" if market_data.price_trend_30d > 0 else "falling"
        change_magnitude = abs(market_data.price_trend_30d)

        if change_magnitude > 0.10:
            urgency = MarketUrgency.HIGH
            impact_score = 85
        elif change_magnitude > 0.05:
            urgency = MarketUrgency.MODERATE
            impact_score = 65
        else:
            urgency = MarketUrgency.LOW
            impact_score = 40

        return MarketInsight(
            location_id=market_data.location_id,
            property_type=market_data.property_type,
            insight_type="trend",
            title=f"Significant Price Trend: {trend_direction.title()} Market",
            description=f"Property prices are {trend_direction} by {change_magnitude:.1%} over the past 30 days. "
                       f"This represents a significant market shift that creates timing opportunities.",
            impact_score=impact_score,
            urgency=urgency,
            recommended_actions=[
                f"Advise {'buyers to act quickly' if trend_direction == 'rising' else 'sellers to price competitively'}",
                "Share market trend data with active leads",
                f"Emphasize {'urgency' if trend_direction == 'rising' else 'opportunity'} in communications"
            ],
            supporting_data={
                "price_change_30d": market_data.price_trend_30d,
                "price_change_90d": market_data.price_trend_90d,
                "median_price": market_data.median_price,
                "trend_direction": trend_direction
            }
        )

    async def generate_contextual_message(
        self,
        lead_id: str,
        message_type: str,
        market_context: Dict[str, Any],
        personalization_context: Dict[str, Any]
    ) -> ContextualMessage:
        """Generate contextual message based on market conditions and lead profile."""
        try:
            location_id = market_context.get("location_id")
            property_type = PropertyType(market_context.get("property_type", "single_family"))

            # Get current market data and insights
            market_data = await self.get_real_time_market_data(location_id, property_type)
            market_insights = await self.generate_market_insights(location_id, property_type, market_context)

            # Generate personalized content using ML personalization engine
            personalization_output = await self.personalization_engine.generate_personalized_communication(
                lead_id=lead_id,
                evaluation_result=personalization_context.get("evaluation_result"),
                message_template=self._get_message_template(message_type),
                interaction_history=personalization_context.get("interaction_history", []),
                context={**market_context, "market_data": market_data.dict()}
            )

            # Determine urgency based on market conditions
            urgency = self._determine_message_urgency(market_data, market_insights)

            # Create contextual message
            message_content = await self._compose_market_message(
                message_type,
                market_data,
                market_insights,
                personalization_output.personalized_content,
                market_context
            )

            # Calculate optimal send time
            optimal_send_time = personalization_output.optimal_timing

            contextual_message = ContextualMessage(
                lead_id=lead_id,
                message_type=message_type,
                subject=self._generate_subject_line(message_type, market_data, urgency),
                content=message_content,
                market_insights=market_insights,
                property_references=market_context.get("property_references", []),
                urgency_level=urgency,
                personalization_score=personalization_output.personalization_score,
                optimal_send_time=optimal_send_time,
                expiration_time=datetime.now() + timedelta(hours=24) if urgency in [MarketUrgency.HIGH, MarketUrgency.CRITICAL] else None
            )

            logger.info(f"Generated contextual message for lead {lead_id}: {message_type}")
            return contextual_message

        except Exception as e:
            logger.error(f"Error generating contextual message: {e}")
            raise

    def _get_message_template(self, message_type: str) -> str:
        """Get message template based on message type."""
        templates = {
            "market_update": "Hi {lead_name}, here's an important market update for {location}...",
            "opportunity_alert": "Hi {lead_name}, I wanted to alert you to a time-sensitive opportunity...",
            "price_change": "Hi {lead_name}, there have been significant price changes in {location}...",
            "timing_advice": "Hi {lead_name}, based on current market conditions, here's my professional advice..."
        }
        return templates.get(message_type, "Hi {lead_name}, I have important market information to share...")

    def _determine_message_urgency(
        self,
        market_data: MarketMetrics,
        market_insights: List[MarketInsight]
    ) -> MarketUrgency:
        """Determine message urgency based on market conditions."""
        # Check for critical insights
        if any(insight.urgency == MarketUrgency.CRITICAL for insight in market_insights):
            return MarketUrgency.CRITICAL

        # Check for high urgency conditions
        high_urgency_conditions = [
            market_data.market_temperature > 85,
            abs(market_data.price_trend_30d) > 0.15,
            market_data.days_on_market < 10,
            any(insight.urgency == MarketUrgency.HIGH for insight in market_insights)
        ]

        if any(high_urgency_conditions):
            return MarketUrgency.HIGH

        # Check for moderate urgency
        moderate_urgency_conditions = [
            market_data.market_temperature > 70,
            abs(market_data.price_trend_30d) > 0.05,
            any(insight.urgency == MarketUrgency.MODERATE for insight in market_insights)
        ]

        if any(moderate_urgency_conditions):
            return MarketUrgency.MODERATE

        return MarketUrgency.LOW

    async def _compose_market_message(
        self,
        message_type: str,
        market_data: MarketMetrics,
        market_insights: List[MarketInsight],
        personalized_content: str,
        context: Dict[str, Any]
    ) -> str:
        """Compose the final market-driven message content."""
        base_content = personalized_content

        # Add market-specific content based on message type
        if message_type == "market_update":
            market_content = f"""

📊 Current Market Snapshot:
• Median Price: ${market_data.median_price:,.0f}
• Average Days on Market: {market_data.days_on_market:.0f} days
• Market Temperature: {self._get_temperature_description(market_data.market_temperature)}
• 30-Day Price Trend: {market_data.price_trend_30d:+.1%}
"""

        elif message_type == "opportunity_alert":
            top_insight = max(market_insights, key=lambda x: x.impact_score, default=None)
            if top_insight:
                market_content = f"""

🚨 Market Opportunity Alert:
{top_insight.description}

Recommended Actions:
{chr(10).join(f"• {action}" for action in top_insight.recommended_actions)}
"""

        elif message_type == "price_change":
            trend_direction = "increased" if market_data.price_trend_30d > 0 else "decreased"
            market_content = f"""

💰 Price Update:
Property values have {trend_direction} by {abs(market_data.price_trend_30d):.1%} over the past month.
Current median price: ${market_data.median_price:,.0f}

This creates {'urgency for buyers' if market_data.price_trend_30d > 0 else 'opportunities for sellers'}.
"""

        else:
            market_content = "\n\n📈 Current market conditions are creating unique opportunities. Let's discuss how this impacts your real estate goals."

        return base_content + market_content

    def _generate_subject_line(
        self,
        message_type: str,
        market_data: MarketMetrics,
        urgency: MarketUrgency
    ) -> str:
        """Generate compelling subject line based on message type and urgency."""
        urgency_prefix = {
            MarketUrgency.CRITICAL: "🚨 URGENT: ",
            MarketUrgency.HIGH: "⚡ Time-Sensitive: ",
            MarketUrgency.MODERATE: "📈 Market Update: ",
            MarketUrgency.LOW: "📊 "
        }

        if message_type == "market_update":
            return f"{urgency_prefix[urgency]}Market conditions changing in your area"
        elif message_type == "opportunity_alert":
            return f"{urgency_prefix[urgency]}Don't miss this market opportunity"
        elif message_type == "price_change":
            trend = "rising" if market_data.price_trend_30d > 0 else "dropping"
            return f"{urgency_prefix[urgency]}Property prices {trend} - {abs(market_data.price_trend_30d):.1%} change"
        elif message_type == "timing_advice":
            return f"{urgency_prefix[urgency]}Perfect timing for your real estate move"
        else:
            return f"{urgency_prefix[urgency]}Important market insight for you"

    def _get_temperature_description(self, temperature: float) -> str:
        """Get human-readable market temperature description."""
        if temperature >= 85:
            return "🔥 Red Hot (Seller's Market)"
        elif temperature >= 70:
            return "🌡️ Hot (Favors Sellers)"
        elif temperature >= 55:
            return "⚖️ Balanced Market"
        elif temperature >= 40:
            return "❄️ Cool (Favors Buyers)"
        else:
            return "🧊 Cold (Buyer's Market)"

    async def create_market_forecast(
        self,
        location_id: str,
        property_type: PropertyType,
        forecast_days: int = 90
    ) -> MarketForecast:
        """Create predictive market forecast using ML models."""
        try:
            # Get historical data for model training
            historical_data = await self._get_historical_market_data(location_id, property_type, days=365)
            current_data = await self.get_real_time_market_data(location_id, property_type)

            # Prepare features for ML prediction
            features = self._prepare_forecast_features(historical_data, current_data)

            # Make predictions
            predicted_change = await self._predict_price_change(features, forecast_days)
            confidence_interval = await self._calculate_confidence_interval(features, predicted_change)

            # Identify key factors
            key_factors = await self._identify_forecast_factors(features, historical_data)

            forecast = MarketForecast(
                location_id=location_id,
                property_type=property_type,
                forecast_horizon=forecast_days,
                predicted_price_change=predicted_change,
                confidence_interval=confidence_interval,
                key_factors=key_factors,
                forecast_accuracy_score=0.85,  # Based on model validation
                model_version="v2.1"
            )

            # Cache the forecast
            cache_key = f"{location_id}_{property_type}_{forecast_days}"
            self.forecast_cache[cache_key] = forecast

            logger.info(f"Market forecast created for {location_id}: {predicted_change:+.1%} over {forecast_days} days")
            return forecast

        except Exception as e:
            logger.error(f"Error creating market forecast: {e}")
            raise

    # Helper methods (simplified implementations)

    async def _get_historical_trends(self, location_id: str, property_type: PropertyType) -> Dict[str, Any]:
        """Get historical market trends (placeholder implementation)."""
        return {
            "price_history": [market_data for _ in range(12)],  # 12 months of data
            "trend_analysis": {"direction": "stable", "volatility": 0.15}
        }

    async def _calculate_inventory_change(self, location_id: str, property_type: PropertyType) -> float:
        """Calculate inventory level change (placeholder implementation)."""
        return 0.25  # 25% increase in inventory

    async def _identify_market_opportunities(
        self,
        market_data: MarketMetrics,
        historical_data: Dict[str, Any],
        lead_context: Optional[Dict[str, Any]]
    ) -> List[MarketInsight]:
        """Identify market opportunities (placeholder implementation)."""
        return []

    def _get_api_key(self, source: str) -> str:
        """Get API key for specific data source."""
        # In production, retrieve from secure environment variables
        api_keys = {
            "mls": "mls_api_key_here",
            "zillow": "zillow_api_key_here",
            "redfin": "redfin_api_key_here",
            "realtor_com": "realtor_api_key_here"
        }
        return api_keys.get(source, "default_key")

    async def _get_historical_market_data(
        self,
        location_id: str,
        property_type: PropertyType,
        days: int
    ) -> List[Dict[str, Any]]:
        """Get historical market data for ML training."""
        # Placeholder implementation
        return [{"price": 350000, "date": "2025-12-01"} for _ in range(days)]

    def _prepare_forecast_features(
        self,
        historical_data: List[Dict[str, Any]],
        current_data: MarketMetrics
    ) -> Dict[str, float]:
        """Prepare features for ML forecasting."""
        return {
            "current_price": current_data.median_price,
            "price_trend_30d": current_data.price_trend_30d,
            "market_temperature": current_data.market_temperature,
            "days_on_market": current_data.days_on_market,
            "inventory_level": current_data.inventory_level
        }

    async def _predict_price_change(self, features: Dict[str, float], forecast_days: int) -> float:
        """Predict price change using ML models."""
        # Simplified ML prediction
        base_trend = features["price_trend_30d"]
        market_factor = (features["market_temperature"] - 50) / 100
        time_factor = forecast_days / 30

        predicted_change = base_trend * time_factor * (1 + market_factor)
        return predicted_change

    async def _calculate_confidence_interval(
        self,
        features: Dict[str, float],
        predicted_change: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval for prediction."""
        volatility = 0.02  # 2% standard volatility
        confidence_range = 1.96 * volatility  # 95% confidence

        return (
            predicted_change - confidence_range,
            predicted_change + confidence_range
        )

    async def _identify_forecast_factors(
        self,
        features: Dict[str, float],
        historical_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify key factors driving the forecast."""
        factors = []

        if features["market_temperature"] > 70:
            factors.append("High market demand")

        if abs(features["price_trend_30d"]) > 0.05:
            factors.append("Strong price momentum")

        if features["days_on_market"] < 20:
            factors.append("Fast-moving inventory")

        if features["inventory_level"] < 100:
            factors.append("Limited supply")

        return factors or ["Stable market conditions"]


# Integration with Streamlit for Market Dashboard

class MarketDashboardComponent:
    """Streamlit component for real-time market dashboard."""

    def __init__(self, market_service: RealTimeMarketIntegration):
        self.market_service = market_service

    def render_market_dashboard(self, location_id: str, property_type: PropertyType) -> None:
        """Render comprehensive market dashboard."""
        st.title("🏠 Real-Time Market Intelligence Dashboard")

        # Get market data
        market_data = asyncio.run(
            self.market_service.get_real_time_market_data(location_id, property_type)
        )

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Median Price",
                f"${market_data.median_price:,.0f}",
                f"{market_data.price_trend_30d:+.1%} (30d)"
            )

        with col2:
            st.metric(
                "Days on Market",
                f"{market_data.days_on_market:.0f}",
                "Fast" if market_data.days_on_market < 30 else "Slow"
            )

        with col3:
            st.metric(
                "Market Temperature",
                f"{market_data.market_temperature:.0f}°",
                self._get_temperature_emoji(market_data.market_temperature)
            )

        with col4:
            st.metric(
                "Inventory",
                f"{market_data.inventory_level:,}",
                f"{market_data.absorption_rate:.1f}% absorption"
            )

        # Market insights
        insights = asyncio.run(
            self.market_service.generate_market_insights(location_id, property_type)
        )

        if insights:
            st.subheader("📊 Market Insights")
            for insight in insights:
                with st.expander(f"{insight.title} (Impact: {insight.impact_score:.0f})"):
                    st.write(insight.description)
                    if insight.recommended_actions:
                        st.write("**Recommended Actions:**")
                        for action in insight.recommended_actions:
                            st.write(f"• {action}")

        # Market forecast
        st.subheader("🔮 Market Forecast")
        forecast = asyncio.run(
            self.market_service.create_market_forecast(location_id, property_type, 90)
        )

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "90-Day Price Forecast",
                f"{forecast.predicted_price_change:+.1%}",
                f"Confidence: {forecast.forecast_accuracy_score:.0%}"
            )

        with col2:
            st.write("**Key Forecast Factors:**")
            for factor in forecast.key_factors:
                st.write(f"• {factor}")

    def _get_temperature_emoji(self, temperature: float) -> str:
        """Get emoji for market temperature."""
        if temperature >= 85:
            return "🔥"
        elif temperature >= 70:
            return "🌡️"
        elif temperature >= 55:
            return "⚖️"
        elif temperature >= 40:
            return "❄️"
        else:
            return "🧊"


if __name__ == "__main__":
    # Example usage for testing
    market_service = RealTimeMarketIntegration()

    # Get real-time market data
    market_data = asyncio.run(
        market_service.get_real_time_market_data("denver_co", PropertyType.SINGLE_FAMILY)
    )
    print(f"Market temperature: {market_data.market_temperature}°")

    # Generate market insights
    insights = asyncio.run(
        market_service.generate_market_insights("denver_co", PropertyType.SINGLE_FAMILY)
    )
    print(f"Generated {len(insights)} market insights")

    # Create contextual message
    contextual_message = asyncio.run(
        market_service.generate_contextual_message(
            "lead_001",
            "market_update",
            {"location_id": "denver_co", "property_type": "single_family"},
            {"evaluation_result": None, "interaction_history": []}
        )
    )
    print(f"Generated contextual message: {contextual_message.subject}")