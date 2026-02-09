#!/usr/bin/env python3
"""
🎯 Scoring Configuration Management
==================================

Centralized configuration for the dynamic scoring system.
Provides environment-specific settings, feature flags, and
runtime configuration management.

Features:
- Environment-specific configurations
- Feature flag management
- A/B testing configurations
- Performance tuning settings
- Market condition thresholds

Author: Claude Sonnet 4
Date: 2026-01-09
Version: 1.0.0
"""

import os
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .dynamic_scoring_weights import LeadSegment, MarketCondition, ScoringWeights


class ScoringEnvironment(str, Enum):
    """Scoring system environments"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DEMO = "demo"


@dataclass
class PerformanceConfig:
    """Performance and timeout configurations"""

    max_scoring_time_ms: int = 500
    redis_timeout_ms: int = 100
    cache_ttl_seconds: int = 300
    batch_size_limit: int = 100
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout_minutes: int = 5


@dataclass
class MarketThresholds:
    """Market condition detection thresholds"""

    sellers_market_inventory: float = 2.0
    buyers_market_inventory: float = 6.0
    high_price_trend: float = 5.0
    low_price_trend: float = -2.0
    fast_dom: int = 20
    slow_dom: int = 60
    seasonal_low_factor: float = 0.85
    seasonal_high_factor: float = 1.15


@dataclass
class FeatureFlags:
    """Feature flags for gradual rollout"""

    enable_dynamic_weights: bool = True
    enable_ml_scoring: bool = True
    enable_market_adjustments: bool = True
    enable_ab_testing: bool = True
    enable_performance_optimization: bool = True
    enable_real_time_updates: bool = False
    enable_advanced_segmentation: bool = False
    enable_multi_tenant: bool = True


@dataclass
class ABTestingConfig:
    """A/B testing configuration"""

    default_traffic_split: float = 0.1  # 10% in tests by default
    min_sample_size: int = 100
    max_test_duration_days: int = 30
    statistical_significance: float = 0.95
    auto_promote_winner: bool = False
    test_cooldown_days: int = 7


@dataclass
class ScoringModeConfig:
    """Configuration for different scoring modes"""

    jorge_weight: float = 0.4
    ml_weight: float = 0.3
    dynamic_weight: float = 0.3
    confidence_threshold: float = 0.7
    fallback_enabled: bool = True
    hybrid_enabled: bool = True


class ScoringConfigManager:
    """
    Central configuration manager for the scoring system

    Handles:
    - Environment-specific configurations
    - Feature flag management
    - Runtime configuration updates
    - Validation and defaults
    """

    def __init__(self, environment: Optional[ScoringEnvironment] = None):
        self.environment = environment or self._detect_environment()
        self._load_configurations()

    def _detect_environment(self) -> ScoringEnvironment:
        """Auto-detect environment from environment variables"""
        env_var = os.getenv("SCORING_ENVIRONMENT", os.getenv("ENVIRONMENT", "development")).lower()

        if env_var in ["prod", "production"]:
            return ScoringEnvironment.PRODUCTION
        elif env_var in ["stage", "staging"]:
            return ScoringEnvironment.STAGING
        elif env_var in ["demo"]:
            return ScoringEnvironment.DEMO
        else:
            return ScoringEnvironment.DEVELOPMENT

    def _load_configurations(self):
        """Load environment-specific configurations"""

        # Base configurations
        self.performance = PerformanceConfig()
        self.market_thresholds = MarketThresholds()
        self.ab_testing = ABTestingConfig()
        self.scoring_modes = ScoringModeConfig()

        # Environment-specific feature flags
        if self.environment == ScoringEnvironment.PRODUCTION:
            self.features = FeatureFlags(
                enable_dynamic_weights=True,
                enable_ml_scoring=True,
                enable_market_adjustments=True,
                enable_ab_testing=True,
                enable_performance_optimization=True,
                enable_real_time_updates=False,  # Disabled in prod initially
                enable_advanced_segmentation=False,  # Disabled in prod initially
                enable_multi_tenant=True,
            )
            # Stricter performance requirements
            self.performance.max_scoring_time_ms = 300
            self.performance.redis_timeout_ms = 50

        elif self.environment == ScoringEnvironment.STAGING:
            self.features = FeatureFlags(
                enable_dynamic_weights=True,
                enable_ml_scoring=True,
                enable_market_adjustments=True,
                enable_ab_testing=True,
                enable_performance_optimization=True,
                enable_real_time_updates=True,  # Test new features
                enable_advanced_segmentation=True,
                enable_multi_tenant=True,
            )

        elif self.environment == ScoringEnvironment.DEMO:
            self.features = FeatureFlags(
                enable_dynamic_weights=True,
                enable_ml_scoring=False,  # Simplified for demo
                enable_market_adjustments=True,
                enable_ab_testing=False,  # No A/B testing in demo
                enable_performance_optimization=False,
                enable_real_time_updates=False,
                enable_advanced_segmentation=False,
                enable_multi_tenant=False,
            )

        else:  # DEVELOPMENT
            self.features = FeatureFlags(
                enable_dynamic_weights=True,
                enable_ml_scoring=True,
                enable_market_adjustments=True,
                enable_ab_testing=True,
                enable_performance_optimization=True,
                enable_real_time_updates=True,
                enable_advanced_segmentation=True,
                enable_multi_tenant=True,
            )
            # Relaxed performance for debugging
            self.performance.max_scoring_time_ms = 1000

        # Load from environment variables if available
        self._load_from_environment()

    def _load_from_environment(self):
        """Load configuration overrides from environment variables"""

        # Performance overrides
        if os.getenv("SCORING_MAX_TIME_MS"):
            self.performance.max_scoring_time_ms = int(os.getenv("SCORING_MAX_TIME_MS"))

        if os.getenv("SCORING_REDIS_TIMEOUT_MS"):
            self.performance.redis_timeout_ms = int(os.getenv("SCORING_REDIS_TIMEOUT_MS"))

        if os.getenv("SCORING_CACHE_TTL"):
            self.performance.cache_ttl_seconds = int(os.getenv("SCORING_CACHE_TTL"))

        # Feature flag overrides
        if os.getenv("ENABLE_DYNAMIC_WEIGHTS"):
            self.features.enable_dynamic_weights = os.getenv("ENABLE_DYNAMIC_WEIGHTS").lower() == "true"

        if os.getenv("ENABLE_ML_SCORING"):
            self.features.enable_ml_scoring = os.getenv("ENABLE_ML_SCORING").lower() == "true"

        if os.getenv("ENABLE_AB_TESTING"):
            self.features.enable_ab_testing = os.getenv("ENABLE_AB_TESTING").lower() == "true"

        # Scoring mode overrides
        if os.getenv("JORGE_WEIGHT"):
            self.scoring_modes.jorge_weight = float(os.getenv("JORGE_WEIGHT"))

        if os.getenv("ML_WEIGHT"):
            self.scoring_modes.ml_weight = float(os.getenv("ML_WEIGHT"))

        if os.getenv("DYNAMIC_WEIGHT"):
            self.scoring_modes.dynamic_weight = float(os.getenv("DYNAMIC_WEIGHT"))

    def get_segment_weights(self, segment: LeadSegment) -> ScoringWeights:
        """Get default weights for a lead segment"""

        # Segment-specific weight profiles
        weights_map = {
            LeadSegment.FIRST_TIME_BUYER: ScoringWeights(
                engagement_score=0.25,
                response_time=0.15,
                page_views=0.15,
                budget_match=0.15,
                timeline_urgency=0.10,
                property_matches=0.10,
                communication_quality=0.08,
                source_quality=0.02,
            ),
            LeadSegment.INVESTOR: ScoringWeights(
                engagement_score=0.15,
                response_time=0.20,
                page_views=0.08,
                budget_match=0.25,
                timeline_urgency=0.15,
                property_matches=0.12,
                communication_quality=0.03,
                source_quality=0.02,
            ),
            LeadSegment.LUXURY: ScoringWeights(
                engagement_score=0.18,
                response_time=0.12,
                page_views=0.12,
                budget_match=0.18,
                timeline_urgency=0.08,
                property_matches=0.20,
                communication_quality=0.20,
                source_quality=0.02,
            ),
            LeadSegment.SELLER: ScoringWeights(
                engagement_score=0.20,
                response_time=0.18,
                page_views=0.05,
                budget_match=0.15,
                timeline_urgency=0.25,
                property_matches=0.05,
                communication_quality=0.15,
                source_quality=0.02,
            ),
        }

        return weights_map.get(segment, weights_map[LeadSegment.FIRST_TIME_BUYER])

    def get_market_adjustments(self, segment: LeadSegment) -> Dict[MarketCondition, Dict[str, float]]:
        """Get market adjustment factors for a segment"""

        # Base market adjustments by segment
        adjustments = {
            LeadSegment.FIRST_TIME_BUYER: {
                MarketCondition.SELLERS_MARKET: {"timeline_urgency": 0.3, "budget_match": 0.2},
                MarketCondition.BUYERS_MARKET: {"engagement_score": 0.2, "page_views": 0.1},
                MarketCondition.SEASONAL_LOW: {"engagement_score": 0.15, "timeline_urgency": -0.1},
            },
            LeadSegment.INVESTOR: {
                MarketCondition.SELLERS_MARKET: {"response_time": 0.4, "timeline_urgency": 0.2},
                MarketCondition.BUYERS_MARKET: {"budget_match": 0.3, "property_matches": 0.15},
            },
            LeadSegment.LUXURY: {
                MarketCondition.SELLERS_MARKET: {"property_matches": 0.3, "communication_quality": 0.25},
                MarketCondition.BUYERS_MARKET: {"timeline_urgency": -0.2, "budget_match": 0.1},
            },
            LeadSegment.SELLER: {
                MarketCondition.BUYERS_MARKET: {"timeline_urgency": 0.35, "communication_quality": 0.2},
                MarketCondition.SELLERS_MARKET: {"timeline_urgency": -0.1, "budget_match": 0.2},
            },
        }

        return adjustments.get(segment, {})

    def get_tier_thresholds(self, confidence: float) -> Dict[str, float]:
        """Get tier classification thresholds based on confidence"""

        if confidence >= 0.8:
            return {"hot": 70.0, "warm": 50.0}
        elif confidence >= 0.6:
            return {"hot": 75.0, "warm": 55.0}
        else:
            return {"hot": 80.0, "warm": 60.0}

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return getattr(self.features, f"enable_{feature}", False)

    def should_use_fallback(self, component: str, failure_count: int) -> bool:
        """Determine if component should use fallback"""
        return failure_count >= self.performance.circuit_breaker_threshold

    def get_ab_test_config(self, test_type: str = "default") -> ABTestingConfig:
        """Get A/B testing configuration"""
        if not self.features.enable_ab_testing:
            # Return disabled config
            disabled_config = ABTestingConfig()
            disabled_config.default_traffic_split = 0.0
            return disabled_config

        return self.ab_testing

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        return {
            "socket_timeout": self.performance.redis_timeout_ms / 1000.0,
            "socket_connect_timeout": self.performance.redis_timeout_ms / 1000.0,
            "retry_on_timeout": True,
            "health_check_interval": 30,
        }

    def validate_configuration(self) -> List[str]:
        """Validate current configuration and return any issues"""
        issues = []

        # Validate scoring mode weights sum to 1
        total_weight = (
            self.scoring_modes.jorge_weight + self.scoring_modes.ml_weight + self.scoring_modes.dynamic_weight
        )

        if abs(total_weight - 1.0) > 0.01:
            issues.append(f"Scoring mode weights sum to {total_weight:.3f}, should be 1.0")

        # Validate performance settings
        if self.performance.max_scoring_time_ms < 50:
            issues.append("Max scoring time too low, may cause timeouts")

        if self.performance.cache_ttl_seconds < 60:
            issues.append("Cache TTL very low, may impact performance")

        # Validate feature flag consistency
        if not self.features.enable_dynamic_weights and self.features.enable_market_adjustments:
            issues.append("Market adjustments enabled but dynamic weights disabled")

        if not self.features.enable_dynamic_weights and self.features.enable_ab_testing:
            issues.append("A/B testing enabled but dynamic weights disabled")

        # Validate environment-specific requirements
        if self.environment == ScoringEnvironment.PRODUCTION:
            if self.performance.max_scoring_time_ms > 500:
                issues.append("Production scoring time limit too high")

            if self.features.enable_real_time_updates:
                issues.append("Real-time updates should be disabled in production initially")

        return issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "environment": self.environment.value,
            "features": asdict(self.features),
            "performance": asdict(self.performance),
            "market_thresholds": asdict(self.market_thresholds),
            "ab_testing": asdict(self.ab_testing),
            "scoring_modes": asdict(self.scoring_modes),
            "validation_issues": self.validate_configuration(),
        }

    def update_feature_flag(self, feature: str, enabled: bool):
        """Runtime update of feature flags"""
        if hasattr(self.features, f"enable_{feature}"):
            setattr(self.features, f"enable_{feature}", enabled)
            print(f"Updated feature '{feature}' to {enabled}")
        else:
            raise ValueError(f"Unknown feature: {feature}")

    def update_performance_setting(self, setting: str, value: Any):
        """Runtime update of performance settings"""
        if hasattr(self.performance, setting):
            setattr(self.performance, setting, value)
            print(f"Updated performance setting '{setting}' to {value}")
        else:
            raise ValueError(f"Unknown performance setting: {setting}")

    def create_tenant_config(self, tenant_id: str, overrides: Dict[str, Any]) -> "TenantScoringConfig":
        """Create tenant-specific configuration"""
        return TenantScoringConfig(tenant_id=tenant_id, base_config=self, overrides=overrides)


class TenantScoringConfig:
    """
    Tenant-specific scoring configuration

    Inherits from base configuration but allows per-tenant overrides
    """

    def __init__(self, tenant_id: str, base_config: ScoringConfigManager, overrides: Dict[str, Any]):
        self.tenant_id = tenant_id
        self.base_config = base_config
        self.overrides = overrides
        self.created_at = datetime.now()

    def get_feature_flag(self, feature: str) -> bool:
        """Get feature flag with tenant override"""
        override_key = f"features.enable_{feature}"
        if override_key in self.overrides:
            return self.overrides[override_key]

        return self.base_config.is_feature_enabled(feature)

    def get_segment_weights(self, segment: LeadSegment) -> ScoringWeights:
        """Get segment weights with tenant overrides"""
        override_key = f"segment_weights.{segment.value}"
        if override_key in self.overrides:
            weights_dict = self.overrides[override_key]
            return ScoringWeights(**weights_dict)

        return self.base_config.get_segment_weights(segment)

    def get_tier_thresholds(self, confidence: float) -> Dict[str, float]:
        """Get tier thresholds with tenant overrides"""
        if "tier_thresholds" in self.overrides:
            thresholds = self.overrides["tier_thresholds"]
            # Adjust for confidence if not explicitly overridden
            if confidence < 0.8 and "confidence_adjustment" not in self.overrides:
                return {"hot": thresholds.get("hot", 70) + 5, "warm": thresholds.get("warm", 50) + 5}
            return thresholds

        return self.base_config.get_tier_thresholds(confidence)

    def to_dict(self) -> Dict[str, Any]:
        """Convert tenant config to dictionary"""
        return {
            "tenant_id": self.tenant_id,
            "base_environment": self.base_config.environment.value,
            "overrides": self.overrides,
            "created_at": self.created_at.isoformat(),
        }


# Global configuration instance
_config_manager = None


def get_scoring_config(environment: Optional[ScoringEnvironment] = None) -> ScoringConfigManager:
    """Get global scoring configuration manager (singleton)"""
    global _config_manager

    if _config_manager is None or (environment and _config_manager.environment != environment):
        _config_manager = ScoringConfigManager(environment)

    return _config_manager


def reload_scoring_config(environment: Optional[ScoringEnvironment] = None) -> ScoringConfigManager:
    """Force reload of scoring configuration"""
    global _config_manager
    _config_manager = None
    return get_scoring_config(environment)


# Example configurations for different environments
EXAMPLE_CONFIGS = {
    "production": {
        "features.enable_real_time_updates": False,
        "features.enable_advanced_segmentation": False,
        "performance.max_scoring_time_ms": 250,
        "tier_thresholds": {"hot": 75, "warm": 55},
    },
    "high_volume_tenant": {
        "performance.max_scoring_time_ms": 100,
        "performance.cache_ttl_seconds": 600,
        "features.enable_performance_optimization": True,
        "scoring_modes.jorge_weight": 0.3,
        "scoring_modes.dynamic_weight": 0.4,
    },
    "luxury_focused_tenant": {
        "segment_weights.luxury": {
            "engagement_score": 0.15,
            "response_time": 0.10,
            "page_views": 0.10,
            "budget_match": 0.20,
            "timeline_urgency": 0.05,
            "property_matches": 0.25,
            "communication_quality": 0.25,
            "source_quality": 0.05,
        },
        "tier_thresholds": {"hot": 80, "warm": 65},
    },
}


if __name__ == "__main__":
    # Example usage
    print("🎯 Scoring Configuration Examples:\n")

    # Test different environments
    for env in ScoringEnvironment:
        config = ScoringConfigManager(env)
        print(f"📊 {env.value.upper()} Environment:")
        print(f"   Dynamic Weights: {config.features.enable_dynamic_weights}")
        print(f"   ML Scoring: {config.features.enable_ml_scoring}")
        print(f"   A/B Testing: {config.features.enable_ab_testing}")
        print(f"   Max Scoring Time: {config.performance.max_scoring_time_ms}ms")
        print(f"   Redis Timeout: {config.performance.redis_timeout_ms}ms")

        issues = config.validate_configuration()
        if issues:
            print(f"   ⚠️  Issues: {issues}")
        else:
            print(f"   ✅ Configuration valid")
        print()

    # Test tenant-specific configuration
    print("🏢 Tenant-Specific Configuration:")
    base_config = get_scoring_config(ScoringEnvironment.PRODUCTION)
    tenant_config = base_config.create_tenant_config(
        tenant_id="luxury_realty_co", overrides=EXAMPLE_CONFIGS["luxury_focused_tenant"]
    )

    luxury_weights = tenant_config.get_segment_weights(LeadSegment.LUXURY)
    print(f"   Luxury Weights - Communication Quality: {luxury_weights.communication_quality}")
    print(f"   Luxury Weights - Property Matches: {luxury_weights.property_matches}")

    thresholds = tenant_config.get_tier_thresholds(0.8)
    print(f"   Tier Thresholds - Hot: {thresholds['hot']}, Warm: {thresholds['warm']}")
    print()

    # Test configuration validation
    print("🔍 Configuration Validation:")
    config = get_scoring_config()
    issues = config.validate_configuration()

    if issues:
        print(f"   Found {len(issues)} issues:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("   ✅ All configurations valid")
    print()

    # Test runtime updates
    print("🔄 Runtime Configuration Updates:")
    print(f"   ML Scoring before: {config.features.enable_ml_scoring}")
    config.update_feature_flag("ml_scoring", False)
    print(f"   ML Scoring after: {config.features.enable_ml_scoring}")

    print(f"   Max scoring time before: {config.performance.max_scoring_time_ms}ms")
    config.update_performance_setting("max_scoring_time_ms", 200)
    print(f"   Max scoring time after: {config.performance.max_scoring_time_ms}ms")
