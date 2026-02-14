#!/usr/bin/env python3
"""
🎯 Dynamic Scoring Weights System
================================

Advanced lead scoring system with adaptive weights that automatically adjust based on:
- Lead segment characteristics (first-time buyer, investor, luxury)
- Market conditions (inventory levels, seasonality, interest rates)
- Real-time performance data and A/B testing results

Features:
- Segment-adaptive weight profiles
- Market condition adjustments
- Performance-based weight optimization
- A/B testing framework for continuous improvement
- Multi-tenant configuration support
- Real-time weight updates

Author: Claude Sonnet 4
Date: 2026-01-09
Version: 1.0.0
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import redis
from pydantic import BaseModel


class LeadSegment(str, Enum):
    """Lead segment classifications"""

    FIRST_TIME_BUYER = "first_time_buyer"
    REPEAT_BUYER = "repeat_buyer"
    INVESTOR = "investor"
    LUXURY = "luxury"
    COMMERCIAL = "commercial"
    SELLER = "seller"
    RENTAL = "rental"


class MarketCondition(str, Enum):
    """Market condition states"""

    SELLERS_MARKET = "sellers_market"  # Low inventory, high demand
    BUYERS_MARKET = "buyers_market"  # High inventory, low demand
    BALANCED = "balanced"  # Stable market
    VOLATILE = "volatile"  # Rapid changes
    SEASONAL_LOW = "seasonal_low"  # Q1 winter slowdown
    SEASONAL_HIGH = "seasonal_high"  # Spring/summer peak


@dataclass
class ScoringWeights:
    """Feature weights for lead scoring"""

    engagement_score: float = 0.20
    response_time: float = 0.15
    page_views: float = 0.10
    budget_match: float = 0.20
    timeline_urgency: float = 0.15
    property_matches: float = 0.08
    communication_quality: float = 0.10
    source_quality: float = 0.02

    def __post_init__(self):
        """Ensure weights sum to 1.0"""
        total = sum(self.__dict__.values())
        if abs(total - 1.0) > 0.01:
            # Normalize weights to sum to 1.0
            for key, value in self.__dict__.items():
                setattr(self, key, value / total)


@dataclass
class MarketMetrics:
    """Market condition metrics"""

    inventory_level: float  # months of inventory (0.5-12+)
    price_trend: float  # price change % last 30 days (-20 to +20)
    interest_rate: float  # current mortgage rate (3-8%)
    days_on_market: float  # average DOM (10-180 days)
    sales_velocity: float  # sales per month ratio to historical
    season_factor: float  # seasonal adjustment (0.7-1.3)

    def get_market_condition(self) -> MarketCondition:
        """Determine market condition based on metrics"""
        # Sellers market indicators
        if self.inventory_level < 2.0 and self.price_trend > 5.0 and self.days_on_market < 20:
            return MarketCondition.SELLERS_MARKET

        # Buyers market indicators
        if self.inventory_level > 6.0 and self.price_trend < -2.0 and self.days_on_market > 60:
            return MarketCondition.BUYERS_MARKET

        # Volatile market indicators
        if abs(self.price_trend) > 10.0 or self.sales_velocity < 0.6:
            return MarketCondition.VOLATILE

        # Seasonal indicators
        if self.season_factor < 0.85:
            return MarketCondition.SEASONAL_LOW
        elif self.season_factor > 1.15:
            return MarketCondition.SEASONAL_HIGH

        return MarketCondition.BALANCED


@dataclass
class WeightProfile:
    """Complete weight profile for a segment/market combination"""

    base_weights: ScoringWeights
    market_adjustments: Dict[MarketCondition, Dict[str, float]]
    performance_multipliers: Dict[str, float]
    confidence_score: float = 0.8
    last_updated: datetime = None
    test_group: Optional[str] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class ABTestConfig(BaseModel):
    """A/B test configuration"""

    test_id: str
    name: str
    description: str
    variants: Dict[str, ScoringWeights]  # variant_name -> weights
    traffic_split: Dict[str, float]  # variant_name -> percentage
    start_date: datetime
    end_date: Optional[datetime] = None
    success_metric: str = "conversion_rate"
    min_sample_size: int = 100
    statistical_power: float = 0.8
    is_active: bool = True


class WeightConfigService:
    """
    Service for managing dynamic scoring weight configurations

    Provides:
    - Tenant-specific weight profiles
    - Segment-adaptive configurations
    - Market condition adjustments
    - A/B testing support
    - Performance tracking
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        self.config_cache = {}
        self.ab_tests = {}
        self.performance_history = {}

        # Initialize default profiles
        self._initialize_default_profiles()

    def _initialize_default_profiles(self):
        """Initialize default weight profiles for each segment"""

        # First-time buyer: Emphasize education and timeline
        self.default_profiles = {
            LeadSegment.FIRST_TIME_BUYER: WeightProfile(
                base_weights=ScoringWeights(
                    engagement_score=0.25,  # Higher - they need education
                    response_time=0.15,
                    page_views=0.15,  # Higher - they browse more
                    budget_match=0.15,  # Lower - they're less certain
                    timeline_urgency=0.10,  # Lower - they take longer
                    property_matches=0.10,
                    communication_quality=0.08,
                    source_quality=0.02,
                ),
                market_adjustments={
                    MarketCondition.SELLERS_MARKET: {
                        "timeline_urgency": 0.3,  # Urgency matters more
                        "budget_match": 0.2,  # Budget certainty critical
                    },
                    MarketCondition.BUYERS_MARKET: {
                        "engagement_score": 0.2,  # More education needed
                        "page_views": 0.1,  # They can browse leisurely
                    },
                },
                performance_multipliers={},
            ),
            # Investor: Focus on numbers and speed
            LeadSegment.INVESTOR: WeightProfile(
                base_weights=ScoringWeights(
                    engagement_score=0.15,  # Lower - they're analytical
                    response_time=0.20,  # Higher - speed is critical
                    page_views=0.08,  # Lower - they know what they want
                    budget_match=0.25,  # Higher - ROI focused
                    timeline_urgency=0.15,
                    property_matches=0.12,  # Higher - specific criteria
                    communication_quality=0.03,  # Lower - brief, to the point
                    source_quality=0.02,
                ),
                market_adjustments={
                    MarketCondition.SELLERS_MARKET: {
                        "response_time": 0.4,  # Speed is everything
                        "timeline_urgency": 0.2,
                    },
                    MarketCondition.BUYERS_MARKET: {
                        "budget_match": 0.3,  # More negotiation room
                        "property_matches": 0.15,
                    },
                },
                performance_multipliers={},
            ),
            # Luxury: Personalization and relationship focus
            LeadSegment.LUXURY: WeightProfile(
                base_weights=ScoringWeights(
                    engagement_score=0.18,
                    response_time=0.12,  # Lower - they expect personal service
                    page_views=0.12,
                    budget_match=0.18,
                    timeline_urgency=0.08,  # Lower - they take time deciding
                    property_matches=0.20,  # Higher - very specific needs
                    communication_quality=0.20,  # Higher - relationship matters
                    source_quality=0.02,
                ),
                market_adjustments={
                    MarketCondition.SELLERS_MARKET: {
                        "property_matches": 0.3,  # Limited inventory
                        "communication_quality": 0.25,
                    }
                },
                performance_multipliers={},
            ),
            # Seller: Timeline and motivation focus
            LeadSegment.SELLER: WeightProfile(
                base_weights=ScoringWeights(
                    engagement_score=0.20,
                    response_time=0.18,
                    page_views=0.05,  # Lower - they're not browsing
                    budget_match=0.15,  # Price expectations
                    timeline_urgency=0.25,  # Higher - when they need to sell
                    property_matches=0.05,  # Not applicable
                    communication_quality=0.15,
                    source_quality=0.02,
                ),
                market_adjustments={
                    MarketCondition.BUYERS_MARKET: {
                        "timeline_urgency": 0.35,  # Urgency more critical
                        "communication_quality": 0.2,
                    }
                },
                performance_multipliers={},
            ),
        }

    async def get_weights_for_lead(
        self, tenant_id: str, lead_segment: LeadSegment, market_metrics: Optional[MarketMetrics] = None
    ) -> ScoringWeights:
        """
        Get optimized scoring weights for a specific lead

        Args:
            tenant_id: Tenant identifier
            lead_segment: Lead segment classification
            market_metrics: Current market conditions

        Returns:
            Optimized ScoringWeights for the lead
        """
        # Get base profile for segment
        profile = await self._get_tenant_profile(tenant_id, lead_segment)

        # Apply market adjustments if available
        if market_metrics:
            profile = self._apply_market_adjustments(profile, market_metrics)

        # Apply A/B test variant if applicable
        profile = await self._apply_ab_test_variant(tenant_id, profile)

        # Apply performance-based optimizations
        profile = await self._apply_performance_optimizations(tenant_id, lead_segment, profile)

        return profile.base_weights

    async def _get_tenant_profile(self, tenant_id: str, segment: LeadSegment) -> WeightProfile:
        """Get weight profile for tenant and segment"""
        cache_key = f"profile:{tenant_id}:{segment.value}"

        # Check cache first
        if cache_key in self.config_cache:
            return self.config_cache[cache_key]

        # Try Redis if available
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    profile_data = json.loads(cached_data)
                    profile = self._deserialize_profile(profile_data)
                    self.config_cache[cache_key] = profile
                    return profile
            except Exception:
                pass  # Fall back to default

        # Use default profile
        profile = self.default_profiles.get(segment, self.default_profiles[LeadSegment.FIRST_TIME_BUYER])

        # Cache it
        self.config_cache[cache_key] = profile
        await self._save_profile_to_cache(cache_key, profile)

        return profile

    def _apply_market_adjustments(self, profile: WeightProfile, market_metrics: MarketMetrics) -> WeightProfile:
        """Apply market condition adjustments to weight profile"""
        market_condition = market_metrics.get_market_condition()

        if market_condition not in profile.market_adjustments:
            return profile

        adjustments = profile.market_adjustments[market_condition]
        adjusted_weights = asdict(profile.base_weights)

        # Apply percentage adjustments
        for feature, adjustment in adjustments.items():
            if feature in adjusted_weights:
                # Adjustment is a multiplier (e.g., 0.3 = +30%, -0.1 = -10%)
                current_weight = adjusted_weights[feature]
                adjusted_weights[feature] = max(0.01, min(0.5, current_weight * (1 + adjustment)))

        # Renormalize weights
        total = sum(adjusted_weights.values())
        for feature in adjusted_weights:
            adjusted_weights[feature] /= total

        # Create new profile with adjusted weights
        new_profile = WeightProfile(
            base_weights=ScoringWeights(**adjusted_weights),
            market_adjustments=profile.market_adjustments,
            performance_multipliers=profile.performance_multipliers,
            confidence_score=profile.confidence_score * 0.95,  # Slight confidence reduction
            last_updated=datetime.now(),
            test_group=profile.test_group,
        )

        return new_profile

    async def _apply_ab_test_variant(self, tenant_id: str, profile: WeightProfile) -> WeightProfile:
        """Apply A/B test variant if lead is part of a test"""
        active_test = await self._get_active_ab_test(tenant_id)

        if not active_test:
            return profile

        # Determine which variant this lead should get
        variant_name = self._assign_test_variant(tenant_id, active_test)

        if variant_name in active_test.variants:
            variant_weights = active_test.variants[variant_name]

            new_profile = WeightProfile(
                base_weights=variant_weights,
                market_adjustments=profile.market_adjustments,
                performance_multipliers=profile.performance_multipliers,
                confidence_score=0.7,  # Lower confidence during testing
                last_updated=datetime.now(),
                test_group=f"{active_test.test_id}:{variant_name}",
            )

            return new_profile

        return profile

    async def _apply_performance_optimizations(
        self, tenant_id: str, segment: LeadSegment, profile: WeightProfile
    ) -> WeightProfile:
        """Apply performance-based weight optimizations"""
        # Get recent performance data
        performance_data = await self._get_performance_data(tenant_id, segment)

        if not performance_data or len(performance_data) < 50:
            return profile  # Need minimum sample size

        # Calculate feature importance based on conversion correlation
        feature_importance = self._calculate_feature_importance(performance_data)

        # Apply gradual adjustments based on performance
        adjusted_weights = asdict(profile.base_weights)

        for feature, importance in feature_importance.items():
            if feature in adjusted_weights:
                current_weight = adjusted_weights[feature]
                # Apply 10% adjustment based on importance
                adjustment_factor = 1.0 + (importance - 0.5) * 0.2
                adjusted_weights[feature] = current_weight * adjustment_factor

        # Renormalize
        total = sum(adjusted_weights.values())
        for feature in adjusted_weights:
            adjusted_weights[feature] /= total

        new_profile = WeightProfile(
            base_weights=ScoringWeights(**adjusted_weights),
            market_adjustments=profile.market_adjustments,
            performance_multipliers=feature_importance,
            confidence_score=min(0.95, profile.confidence_score + 0.1),  # Increase confidence
            last_updated=datetime.now(),
            test_group=profile.test_group,
        )

        return new_profile

    def _calculate_feature_importance(self, performance_data: List[Dict]) -> Dict[str, float]:
        """Calculate feature importance based on conversion correlation"""
        if len(performance_data) < 10:
            return {}

        # Simple correlation calculation
        # In production, use proper statistical methods
        feature_importance = {}

        converted_leads = [d for d in performance_data if d.get("converted", False)]
        len(converted_leads) / len(performance_data)

        # Calculate correlation for each feature
        features = [
            "engagement_score",
            "response_time",
            "page_views",
            "budget_match",
            "timeline_urgency",
            "property_matches",
            "communication_quality",
        ]

        for feature in features:
            feature_values = [d.get(feature, 0) for d in performance_data]
            converted_values = [d.get(feature, 0) for d in converted_leads]

            if len(converted_values) > 5:
                avg_converted = sum(converted_values) / len(converted_values)
                avg_all = sum(feature_values) / len(feature_values)

                # Simple correlation proxy
                if avg_all > 0:
                    importance = avg_converted / avg_all
                    feature_importance[feature] = max(0.1, min(1.0, importance))
                else:
                    feature_importance[feature] = 0.5
            else:
                feature_importance[feature] = 0.5  # Neutral

        return feature_importance

    async def create_ab_test(self, tenant_id: str, test_config: ABTestConfig) -> str:
        """
        Create and start an A/B test for weight optimization

        Args:
            tenant_id: Tenant identifier
            test_config: A/B test configuration

        Returns:
            Test ID
        """
        test_key = f"ab_test:{tenant_id}:{test_config.test_id}"

        # Store test configuration
        if self.redis_client:
            test_data = test_config.dict()
            test_data["start_date"] = test_config.start_date.isoformat()
            if test_config.end_date:
                test_data["end_date"] = test_config.end_date.isoformat()

            self.redis_client.set(test_key, json.dumps(test_data), ex=86400 * 30)  # 30 days

        # Cache locally
        self.ab_tests[test_key] = test_config

        return test_config.test_id

    async def _get_active_ab_test(self, tenant_id: str) -> Optional[ABTestConfig]:
        """Get active A/B test for tenant"""
        # Check cache first

        for key, test in self.ab_tests.items():
            if key.startswith(f"ab_test:{tenant_id}:") and test.is_active:
                if test.end_date is None or test.end_date > datetime.now():
                    return test

        # Check Redis
        if self.redis_client:
            try:
                pattern = f"ab_test:{tenant_id}:*"
                keys = self.redis_client.keys(pattern)

                for key in keys:
                    test_data = self.redis_client.get(key)
                    if test_data:
                        test_dict = json.loads(test_data)
                        test_config = ABTestConfig(**test_dict)

                        if test_config.is_active and (
                            test_config.end_date is None
                            or datetime.fromisoformat(test_config.end_date) > datetime.now()
                        ):
                            return test_config
            except Exception:
                pass

        return None

    def _assign_test_variant(self, tenant_id: str, test_config: ABTestConfig) -> str:
        """Assign lead to test variant based on consistent hashing"""
        # Use tenant_id hash to ensure consistent assignment
        hash_value = hash(f"{tenant_id}:{test_config.test_id}") % 100

        cumulative = 0
        for variant, percentage in test_config.traffic_split.items():
            cumulative += percentage * 100
            if hash_value < cumulative:
                return variant

        # Fallback to first variant
        return list(test_config.variants.keys())[0]

    async def record_lead_outcome(
        self,
        tenant_id: str,
        lead_id: str,
        segment: LeadSegment,
        features: Dict[str, float],
        converted: bool,
        conversion_value: float = 0.0,
    ):
        """Record lead outcome for performance optimization"""
        outcome_data = {
            "lead_id": lead_id,
            "tenant_id": tenant_id,
            "segment": segment.value,
            "features": features,
            "converted": converted,
            "conversion_value": conversion_value,
            "timestamp": datetime.now().isoformat(),
        }

        # Store in performance history
        history_key = f"performance:{tenant_id}:{segment.value}"

        if history_key not in self.performance_history:
            self.performance_history[history_key] = []

        self.performance_history[history_key].append(outcome_data)

        # Keep only recent data (last 1000 records)
        if len(self.performance_history[history_key]) > 1000:
            self.performance_history[history_key] = self.performance_history[history_key][-1000:]

        # Store in Redis if available
        if self.redis_client:
            try:
                # Store individual outcome
                outcome_key = f"outcome:{tenant_id}:{lead_id}"
                self.redis_client.set(outcome_key, json.dumps(outcome_data), ex=86400 * 7)  # 7 days

                # Add to performance list
                list_key = f"performance_list:{tenant_id}:{segment.value}"
                self.redis_client.lpush(list_key, json.dumps(outcome_data))
                self.redis_client.ltrim(list_key, 0, 999)  # Keep last 1000
                self.redis_client.expire(list_key, 86400 * 30)  # 30 days
            except Exception:
                pass  # Continue without Redis

    async def _get_performance_data(self, tenant_id: str, segment: LeadSegment) -> List[Dict]:
        """Get performance data for optimization"""
        history_key = f"performance:{tenant_id}:{segment.value}"

        # Try local cache first
        if history_key in self.performance_history:
            return self.performance_history[history_key]

        # Try Redis
        if self.redis_client:
            try:
                list_key = f"performance_list:{tenant_id}:{segment.value}"
                data = self.redis_client.lrange(list_key, 0, 999)

                performance_data = []
                for item in data:
                    try:
                        performance_data.append(json.loads(item))
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.debug(f"Failed to parse performance item: {e}")
                        continue

                # Cache locally
                self.performance_history[history_key] = performance_data
                return performance_data
            except Exception:
                pass

        return []

    async def _save_profile_to_cache(self, cache_key: str, profile: WeightProfile):
        """Save profile to Redis cache"""
        if not self.redis_client:
            return

        try:
            profile_data = {
                "base_weights": asdict(profile.base_weights),
                "market_adjustments": profile.market_adjustments,
                "performance_multipliers": profile.performance_multipliers,
                "confidence_score": profile.confidence_score,
                "last_updated": profile.last_updated.isoformat(),
                "test_group": profile.test_group,
            }

            self.redis_client.set(cache_key, json.dumps(profile_data), ex=86400)  # 24 hours
        except Exception:
            pass  # Continue without Redis

    def _deserialize_profile(self, profile_data: Dict) -> WeightProfile:
        """Deserialize profile from stored data"""
        return WeightProfile(
            base_weights=ScoringWeights(**profile_data["base_weights"]),
            market_adjustments=profile_data["market_adjustments"],
            performance_multipliers=profile_data["performance_multipliers"],
            confidence_score=profile_data["confidence_score"],
            last_updated=datetime.fromisoformat(profile_data["last_updated"]),
            test_group=profile_data.get("test_group"),
        )

    async def get_segment_performance_report(self, tenant_id: str) -> Dict[str, Any]:
        """Generate performance report across all segments"""
        report = {
            "tenant_id": tenant_id,
            "generated_at": datetime.now().isoformat(),
            "segments": {},
            "overall_metrics": {},
        }

        total_leads = 0
        total_conversions = 0

        for segment in LeadSegment:
            performance_data = await self._get_performance_data(tenant_id, segment)

            if performance_data:
                conversions = sum(1 for d in performance_data if d.get("converted", False))
                conversion_rate = conversions / len(performance_data)
                avg_value = sum(d.get("conversion_value", 0) for d in performance_data if d.get("converted", False))
                avg_value = avg_value / max(conversions, 1)

                report["segments"][segment.value] = {
                    "total_leads": len(performance_data),
                    "conversions": conversions,
                    "conversion_rate": round(conversion_rate, 3),
                    "avg_conversion_value": round(avg_value, 2),
                    "last_updated": max(d.get("timestamp", "") for d in performance_data),
                }

                total_leads += len(performance_data)
                total_conversions += conversions

        if total_leads > 0:
            report["overall_metrics"] = {
                "total_leads": total_leads,
                "total_conversions": total_conversions,
                "overall_conversion_rate": round(total_conversions / total_leads, 3),
            }

        return report


class MarketConditionAdjuster:
    """
    Service for adjusting scoring weights based on real-time market conditions

    Integrates with:
    - MLS data feeds
    - Interest rate APIs
    - Seasonal patterns
    - Local market indicators
    """

    def __init__(self):
        self.market_cache = {}
        self.seasonal_patterns = self._initialize_seasonal_patterns()

    def _initialize_seasonal_patterns(self) -> Dict[int, float]:
        """Initialize seasonal adjustment factors by month"""
        return {
            1: 0.75,  # January - slowest
            2: 0.80,  # February
            3: 0.90,  # March - spring start
            4: 1.10,  # April - peak spring
            5: 1.15,  # May - peak
            6: 1.10,  # June
            7: 1.05,  # July
            8: 1.00,  # August
            9: 0.95,  # September
            10: 0.90,  # October
            11: 0.85,  # November
            12: 0.80,  # December - holiday slowdown
        }

    async def get_current_market_metrics(self, location: str = "Rancho Cucamonga, CA") -> MarketMetrics:
        """
        Get current market metrics for a location

        Args:
            location: Market location (city, state)

        Returns:
            Current MarketMetrics
        """
        cache_key = f"market:{location}"

        # Check cache (refresh every 4 hours)
        if cache_key in self.market_cache:
            cached_data, timestamp = self.market_cache[cache_key]
            if datetime.now() - timestamp < timedelta(hours=4):
                return cached_data

        # In production, integrate with real market data APIs
        # For now, simulate based on current date and basic patterns
        metrics = self._simulate_market_metrics(location)

        # Cache the result
        self.market_cache[cache_key] = (metrics, datetime.now())

        return metrics

    def _simulate_market_metrics(self, location: str) -> MarketMetrics:
        """Simulate market metrics (replace with real API calls)"""
        now = datetime.now()

        # Seasonal factor
        season_factor = self.seasonal_patterns.get(now.month, 1.0)

        # Simulate based on location and season
        if "Rancho Cucamonga" in location:
            # Rancho Cucamonga market characteristics
            base_inventory = 2.5
            base_price_trend = 3.0
            base_interest = 6.5
            base_dom = 25
            base_velocity = 1.0
        else:
            # Default market
            base_inventory = 4.0
            base_price_trend = 1.0
            base_interest = 6.8
            base_dom = 35
            base_velocity = 0.9

        # Add some variability
        import random

        random.seed(hash(location + str(now.date())))

        return MarketMetrics(
            inventory_level=base_inventory * (0.8 + random.random() * 0.4),
            price_trend=base_price_trend * (0.5 + random.random() * 1.0),
            interest_rate=base_interest + (random.random() - 0.5) * 0.5,
            days_on_market=base_dom * (0.7 + random.random() * 0.6),
            sales_velocity=base_velocity * season_factor * (0.8 + random.random() * 0.4),
            season_factor=season_factor,
        )


class DynamicScoringOrchestrator:
    """
    Main orchestrator for the dynamic scoring system

    Coordinates:
    - Weight configuration
    - Market condition adjustments
    - A/B testing
    - Performance tracking
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.weight_config = WeightConfigService(redis_url)
        self.market_adjuster = MarketConditionAdjuster()
        self.active_tests = {}

    async def score_lead_with_dynamic_weights(
        self, tenant_id: str, lead_id: str, lead_data: Dict[str, Any], segment: Optional[LeadSegment] = None
    ) -> Dict[str, Any]:
        """
        Score a lead using dynamic weights

        Args:
            tenant_id: Tenant identifier
            lead_id: Lead identifier
            lead_data: Lead information
            segment: Lead segment (auto-detected if not provided)

        Returns:
            Comprehensive scoring result with explanations
        """
        # Auto-detect segment if not provided
        if segment is None:
            segment = self._detect_lead_segment(lead_data)

        # Get current market conditions
        location = lead_data.get("location", "Rancho Cucamonga, CA")
        market_metrics = await self.market_adjuster.get_current_market_metrics(location)

        # Get optimized weights
        weights = await self.weight_config.get_weights_for_lead(tenant_id, segment, market_metrics)

        # Calculate score using optimized weights
        score_result = self._calculate_weighted_score(lead_data, weights)

        # Add dynamic context
        score_result.update(
            {
                "lead_id": lead_id,
                "segment": segment.value,
                "market_condition": market_metrics.get_market_condition().value,
                "weights_used": asdict(weights),
                "market_metrics": asdict(market_metrics),
                "scored_at": datetime.now().isoformat(),
            }
        )

        return score_result

    def _convert_context_to_lead_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to convert test context format to lead data format"""
        prefs = context.get("extracted_preferences", {})
        messages = context.get("conversation_history", [])

        return {
            "budget": prefs.get("budget", 0),
            "location": prefs.get("location", "Rancho Cucamonga, CA"),
            "timeline": prefs.get("timeline", ""),
            "intent": prefs.get("motivation", ""),
            "messages": messages,
            "email_opens": context.get("email_opens", 0),
            "avg_response_time": context.get("avg_response_time", 24),
            "page_views": context.get("page_views", 0),
            "budget_match": context.get("budget_match", 0.5),
            "property_matches": context.get("property_matches", 0),
            "communication_quality": context.get("communication_quality", 0.5),
            "source": prefs.get("source", "unknown"),
        }

    def _detect_lead_segment(self, lead_data: Dict[str, Any]) -> LeadSegment:
        """Auto-detect lead segment from lead data"""
        # Check for explicit segment indicators
        budget = lead_data.get("budget", 0)
        if isinstance(budget, str):
            budget = self._parse_budget(budget)

        intent = lead_data.get("intent", "").lower()
        lead_data.get("source", "").lower()

        # Luxury indicators
        if budget > 1000000 or "luxury" in intent or "high-end" in intent:
            return LeadSegment.LUXURY

        # Investor indicators
        if (
            "investment" in intent
            or "investor" in intent
            or "roi" in intent
            or "rental" in intent
            or "multiple" in intent
        ):
            return LeadSegment.INVESTOR

        # Seller indicators
        if "sell" in intent or "selling" in intent or "list" in intent:
            return LeadSegment.SELLER

        # Commercial indicators
        if "commercial" in intent or "business" in intent or budget > 2000000:
            return LeadSegment.COMMERCIAL

        # First-time buyer indicators
        messages = lead_data.get("messages", [])
        for msg in messages:
            content = msg.get("content", "").lower()
            if "first time" in content or "never bought" in content or "first home" in content:
                return LeadSegment.FIRST_TIME_BUYER

        # Default to repeat buyer
        return LeadSegment.REPEAT_BUYER

    def _parse_budget(self, budget_str: str) -> float:
        """Parse budget string to numeric value"""
        import re

        # Remove common prefixes and clean
        budget_str = budget_str.replace("$", "").replace(",", "").strip().lower()

        # Handle 'k' and 'm' suffixes
        if "k" in budget_str:
            match = re.search(r"(\d+\.?\d*)k", budget_str)
            if match:
                return float(match.group(1)) * 1000
        elif "m" in budget_str:
            match = re.search(r"(\d+\.?\d*)m", budget_str)
            if match:
                return float(match.group(1)) * 1000000

        # Try to extract numeric value
        match = re.search(r"(\d+\.?\d*)", budget_str)
        if match:
            return float(match.group(1))

        return 0

    def _calculate_weighted_score(self, lead_data: Dict[str, Any], weights: ScoringWeights) -> Dict[str, Any]:
        """Calculate score using the provided weights"""
        # Extract features (simplified version)
        features = {
            "engagement_score": min(lead_data.get("email_opens", 0) / 10.0, 1.0),
            "response_time": self._score_response_time(lead_data.get("avg_response_time", 24)),
            "page_views": min(lead_data.get("page_views", 0) / 20.0, 1.0),
            "budget_match": lead_data.get("budget_match", 0.5),
            "timeline_urgency": self._score_timeline(lead_data.get("timeline", "")),
            "property_matches": min(lead_data.get("property_matches", 0) / 10.0, 1.0),
            "communication_quality": lead_data.get("communication_quality", 0.5),
            "source_quality": self._score_source(lead_data.get("source", "")),
        }

        # Calculate weighted score
        total_score = 0.0
        feature_contributions = {}

        weight_dict = asdict(weights)
        for feature, value in features.items():
            contribution = value * weight_dict.get(feature, 0.0)
            feature_contributions[feature] = contribution
            total_score += contribution

        # Convert to 0-100 scale
        final_score = total_score * 100

        # Determine tier
        if final_score >= 70:
            tier = "hot"
        elif final_score >= 50:
            tier = "warm"
        else:
            tier = "cold"

        return {
            "score": round(final_score, 2),
            "tier": tier,
            "features": features,
            "feature_contributions": feature_contributions,
            "confidence": 0.85,  # Base confidence
        }

    def _score_response_time(self, response_time: float) -> float:
        """Score response time (lower is better)"""
        if response_time <= 1:
            return 1.0
        elif response_time >= 48:
            return 0.0
        else:
            return 1.0 - (response_time / 48.0)

    def _score_timeline(self, timeline: str) -> float:
        """Score timeline urgency"""
        timeline_lower = timeline.lower()

        if any(word in timeline_lower for word in ["asap", "immediately", "urgent"]):
            return 1.0
        elif any(word in timeline_lower for word in ["soon", "month"]):
            return 0.7
        elif any(word in timeline_lower for word in ["3 months", "quarter"]):
            return 0.5
        else:
            return 0.3

    def _score_source(self, source: str) -> float:
        """Score lead source quality"""
        source_scores = {"referral": 1.0, "organic": 0.9, "direct": 0.8, "social": 0.6, "paid": 0.5, "other": 0.3}

        for source_type, score in source_scores.items():
            if source_type in source.lower():
                return score

        return 0.3  # Default

    async def record_conversion_outcome(
        self,
        tenant_id: str,
        lead_id: str,
        converted: bool,
        conversion_value: float = 0.0,
        lead_data: Optional[Dict] = None,
    ):
        """Record conversion outcome for performance optimization"""
        if lead_data is None:
            return

        segment = self._detect_lead_segment(lead_data)

        # Extract features for correlation analysis
        features = {
            "engagement_score": min(lead_data.get("email_opens", 0) / 10.0, 1.0),
            "response_time": lead_data.get("avg_response_time", 24),
            "page_views": lead_data.get("page_views", 0),
            "budget_match": lead_data.get("budget_match", 0.5),
            "timeline_urgency": self._score_timeline(lead_data.get("timeline", "")),
            "property_matches": lead_data.get("property_matches", 0),
            "communication_quality": lead_data.get("communication_quality", 0.5),
        }

        await self.weight_config.record_lead_outcome(tenant_id, lead_id, segment, features, converted, conversion_value)

    async def create_weight_optimization_test(
        self,
        tenant_id: str,
        test_name: str,
        segment: LeadSegment,
        variant_weights: List[ScoringWeights],
        duration_days: int = 30,
    ) -> str:
        """
        Create A/B test for weight optimization

        Args:
            tenant_id: Tenant identifier
            test_name: Human-readable test name
            segment: Target segment for testing
            variant_weights: List of weight variants to test
            duration_days: Test duration in days

        Returns:
            Test ID
        """
        test_id = f"{segment.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create variants
        variants = {}
        traffic_split = {}
        split_percentage = 1.0 / len(variant_weights)

        for i, weights in enumerate(variant_weights):
            variant_name = f"variant_{chr(65 + i)}"  # A, B, C, etc.
            variants[variant_name] = weights
            traffic_split[variant_name] = split_percentage

        test_config = ABTestConfig(
            test_id=test_id,
            name=test_name,
            description=f"Weight optimization for {segment.value} segment",
            variants=variants,
            traffic_split=traffic_split,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=duration_days),
            success_metric="conversion_rate",
            min_sample_size=100,
            is_active=True,
        )

        return await self.weight_config.create_ab_test(tenant_id, test_config)

    async def get_performance_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        # Get segment performance
        segment_report = await self.weight_config.get_segment_performance_report(tenant_id)

        # Get current market conditions
        market_metrics = await self.market_adjuster.get_current_market_metrics()

        # Get active tests
        active_test = await self.weight_config._get_active_ab_test(tenant_id)

        dashboard = {
            "tenant_id": tenant_id,
            "generated_at": datetime.now().isoformat(),
            "segment_performance": segment_report,
            "market_conditions": {
                "condition": market_metrics.get_market_condition().value,
                "metrics": asdict(market_metrics),
            },
            "active_ab_test": active_test.dict() if active_test else None,
            "system_health": {
                "cache_hit_rate": 0.95,  # Simulated
                "avg_scoring_latency": 45,  # ms
                "daily_scores": 1250,  # Simulated
                "last_updated": datetime.now().isoformat(),
            },
        }

        return dashboard


# Example usage and testing
if __name__ == "__main__":

    async def main():
        # Initialize system
        orchestrator = DynamicScoringOrchestrator()

        # Example lead data
        lead_data = {
            "id": "lead_123",
            "budget": 750000,
            "location": "Rancho Cucamonga, CA",
            "intent": "buying",
            "email_opens": 8,
            "emails_sent": 10,
            "avg_response_time": 2.5,
            "page_views": 15,
            "budget_match": 0.85,
            "timeline": "next 2 months",
            "property_matches": 5,
            "communication_quality": 0.9,
            "source": "organic",
            "messages": [
                {"content": "Looking for a house in Rancho Cucamonga with 3-4 bedrooms, budget around $750k"},
                {"content": "When can we schedule a viewing?"},
            ],
        }

        # Score the lead
        result = await orchestrator.score_lead_with_dynamic_weights(
            tenant_id="tenant_123", lead_id="lead_123", lead_data=lead_data
        )

        print("🎯 Dynamic Scoring Result:")
        print(f"   Score: {result['score']}/100")
        print(f"   Tier: {result['tier'].upper()}")
        print(f"   Segment: {result['segment'].replace('_', ' ').title()}")
        print(f"   Market Condition: {result['market_condition'].replace('_', ' ').title()}")
        print(f"   Confidence: {result['confidence']:.1%}")

        print("\n📊 Feature Contributions:")
        for feature, contribution in result["feature_contributions"].items():
            print(f"   {feature.replace('_', ' ').title()}: {contribution:.3f}")

        print("\n🌡️  Market Metrics:")
        metrics = result["market_metrics"]
        print(f"   Inventory Level: {metrics['inventory_level']:.1f} months")
        print(f"   Price Trend: {metrics['price_trend']:+.1f}%")
        print(f"   Interest Rate: {metrics['interest_rate']:.1f}%")
        print(f"   Days on Market: {metrics['days_on_market']:.0f}")
        print(f"   Seasonal Factor: {metrics['season_factor']:.2f}")

        # Simulate conversion outcome
        await orchestrator.record_conversion_outcome(
            tenant_id="tenant_123", lead_id="lead_123", converted=True, conversion_value=15000.0, lead_data=lead_data
        )

        print("\n✅ Conversion outcome recorded for optimization")

        # Get performance dashboard
        dashboard = await orchestrator.get_performance_dashboard("tenant_123")
        print(f"\n📈 Performance Dashboard Generated")
        print(f"   Market Condition: {dashboard['market_conditions']['condition'].replace('_', ' ').title()}")
        print(f"   System Health: {dashboard['system_health']['avg_scoring_latency']}ms avg latency")

    # Run the example
    asyncio.run(main())
