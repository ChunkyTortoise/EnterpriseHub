"""
Claude Caching Configuration
Production configuration for 70% cost reduction implementation
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from ghl_real_estate_ai.services.claude_prompt_caching_service import CacheStrategy

@dataclass
class CachingConfig:
    """Production caching configuration."""

    # Redis configuration
    redis_url: str = os.getenv("CLAUDE_CACHE_REDIS_URL", "redis://localhost:6379/2")
    redis_max_connections: int = int(os.getenv("CLAUDE_CACHE_REDIS_CONNECTIONS", "20"))

    # Cost configuration
    cost_per_1k_tokens: float = float(os.getenv("CLAUDE_COST_PER_1K_TOKENS", "0.015"))
    target_cost_reduction: float = 0.70  # 70% target

    # Cache size limits
    max_cache_size_mb: float = float(os.getenv("CLAUDE_CACHE_MAX_SIZE_MB", "500"))
    cache_cleanup_threshold_mb: float = float(os.getenv("CLAUDE_CACHE_CLEANUP_THRESHOLD", "400"))

    # Performance settings
    enable_compression: bool = os.getenv("CLAUDE_CACHE_COMPRESSION", "true").lower() == "true"
    compression_level: int = int(os.getenv("CLAUDE_CACHE_COMPRESSION_LEVEL", "6"))

    # Strategy TTL overrides (in seconds)
    strategy_ttl_overrides: Dict[str, int] = None

    def __post_init__(self):
        if self.strategy_ttl_overrides is None:
            self.strategy_ttl_overrides = {
                "aggressive": int(os.getenv("CACHE_TTL_AGGRESSIVE", "86400")),    # 24h
                "standard": int(os.getenv("CACHE_TTL_STANDARD", "14400")),        # 4h
                "conservative": int(os.getenv("CACHE_TTL_CONSERVATIVE", "7200")),  # 2h
                "real_time": int(os.getenv("CACHE_TTL_REAL_TIME", "1800")),       # 30min
            }

class CacheWarmingProfiles:
    """Pre-defined cache warming profiles for different scenarios."""

    @staticmethod
    def get_daily_warming_requests() -> List[Dict[str, Any]]:
        """Get requests to warm cache daily for common operations."""
        return [
            # Property analysis templates
            {
                "prompt": "Analyze the investment potential of a downtown condo",
                "system_prompt": "You are a real estate investment expert. Provide detailed ROI analysis.",
                "context_data": {"type": "property_analysis", "category": "investment"}
            },
            {
                "prompt": "Evaluate the market conditions for single-family homes",
                "system_prompt": "You are a market analyst. Provide current market insights.",
                "context_data": {"type": "market_analysis", "category": "residential"}
            },

            # Lead qualification templates
            {
                "prompt": "What questions should I ask to qualify a first-time home buyer?",
                "system_prompt": "You are a lead qualification expert. Provide comprehensive question sets.",
                "context_data": {"type": "qualification_guidance", "category": "first_time_buyer"}
            },
            {
                "prompt": "How do I qualify an investor lead for commercial properties?",
                "system_prompt": "You are a commercial real estate expert. Provide investor qualification strategies.",
                "context_data": {"type": "qualification_guidance", "category": "commercial_investor"}
            },

            # Agent coaching templates
            {
                "prompt": "How should I handle price objections during property showings?",
                "system_prompt": "You are a real estate sales coach. Provide objection handling strategies.",
                "context_data": {"type": "coaching_guidance", "category": "objection_handling"}
            },
            {
                "prompt": "What's the best way to follow up with warm leads?",
                "system_prompt": "You are a follow-up strategy expert. Provide proven follow-up sequences.",
                "context_data": {"type": "coaching_guidance", "category": "follow_up"}
            },

            # Documentation templates
            {
                "prompt": "Explain the home buying process step by step",
                "system_prompt": "You are a real estate process expert. Provide clear, actionable steps.",
                "context_data": {"type": "documentation", "category": "buying_process"}
            },
            {
                "prompt": "What are the key factors in property valuation?",
                "system_prompt": "You are a property valuation expert. Provide comprehensive valuation factors.",
                "context_data": {"type": "documentation", "category": "valuation"}
            }
        ]

    @staticmethod
    def get_weekly_warming_requests() -> List[Dict[str, Any]]:
        """Get requests to warm cache weekly for periodic content."""
        return [
            # Market analysis (updated weekly)
            {
                "prompt": "Analyze current interest rate trends and their impact on real estate",
                "system_prompt": "You are a financial market analyst specializing in real estate.",
                "context_data": {"type": "market_analysis", "frequency": "weekly"}
            },
            {
                "prompt": "What are the latest trends in luxury home sales?",
                "system_prompt": "You are a luxury real estate market expert.",
                "context_data": {"type": "market_trends", "category": "luxury", "frequency": "weekly"}
            },

            # Regional insights
            {
                "prompt": "Provide insights on suburban vs urban property demand shifts",
                "system_prompt": "You are a demographic and real estate trend analyst.",
                "context_data": {"type": "regional_analysis", "frequency": "weekly"}
            }
        ]

class ClaudeCacheIntegration:
    """Integration patterns for existing Claude services."""

    @staticmethod
    def get_integration_patterns() -> Dict[str, Dict[str, Any]]:
        """Get integration patterns for different Claude services."""
        return {
            "claude_agent_service": {
                "methods_to_cache": [
                    "get_property_analysis",
                    "get_market_insights",
                    "get_investment_advice",
                    "get_qualification_questions"
                ],
                "default_strategy": CacheStrategy.STANDARD,
                "context_extraction": "property_id, analysis_type",
                "estimated_cost_reduction": "65-75%"
            },

            "claude_semantic_analyzer": {
                "methods_to_cache": [
                    "analyze_lead_intent",
                    "extract_semantic_preferences",
                    "generate_intelligent_questions"
                ],
                "default_strategy": CacheStrategy.CONSERVATIVE,
                "context_extraction": "lead_id, intent_type",
                "estimated_cost_reduction": "55-70%"
            },

            "qualification_orchestrator": {
                "methods_to_cache": [
                    "get_qualification_strategy",
                    "generate_follow_up_questions",
                    "analyze_qualification_completeness"
                ],
                "default_strategy": CacheStrategy.STANDARD,
                "context_extraction": "qualification_stage, lead_type",
                "estimated_cost_reduction": "60-75%"
            },

            "claude_action_planner": {
                "methods_to_cache": [
                    "get_action_recommendations",
                    "generate_follow_up_strategy",
                    "analyze_priority_scoring"
                ],
                "default_strategy": CacheStrategy.CONSERVATIVE,
                "context_extraction": "action_context, urgency_level",
                "estimated_cost_reduction": "50-65%"
            }
        }

class CostOptimizationTargets:
    """Cost optimization targets and monitoring thresholds."""

    # Monthly cost targets (based on usage patterns)
    MONTHLY_COST_TARGETS = {
        "property_analysis": {
            "baseline_monthly_cost": 450.00,  # Without caching
            "target_monthly_cost": 135.00,    # 70% reduction
            "api_calls_per_month": 3000,
            "avg_tokens_per_call": 1000
        },

        "lead_qualification": {
            "baseline_monthly_cost": 320.00,
            "target_monthly_cost": 96.00,
            "api_calls_per_month": 2100,
            "avg_tokens_per_call": 1024
        },

        "real_time_coaching": {
            "baseline_monthly_cost": 180.00,
            "target_monthly_cost": 90.00,     # 50% reduction (real-time has less caching)
            "api_calls_per_month": 1200,
            "avg_tokens_per_call": 1000
        },

        "market_analysis": {
            "baseline_monthly_cost": 280.00,
            "target_monthly_cost": 70.00,     # 75% reduction (high cache hit rate)
            "api_calls_per_month": 1800,
            "avg_tokens_per_call": 1040
        }
    }

    # Alert thresholds
    COST_ALERT_THRESHOLDS = {
        "monthly_cost_exceeded": 1.2,        # Alert if 20% over target
        "cache_hit_ratio_below": 0.6,        # Alert if hit ratio below 60%
        "daily_cost_spike": 2.0,             # Alert if daily cost 2x normal
        "cache_size_threshold": 0.9          # Alert if cache 90% full
    }

    @classmethod
    def calculate_total_monthly_savings(cls) -> Dict[str, float]:
        """Calculate total expected monthly savings."""
        total_baseline = sum(target["baseline_monthly_cost"] for target in cls.MONTHLY_COST_TARGETS.values())
        total_target = sum(target["target_monthly_cost"] for target in cls.MONTHLY_COST_TARGETS.values())

        return {
            "total_baseline_cost": total_baseline,
            "total_target_cost": total_target,
            "total_monthly_savings": total_baseline - total_target,
            "cost_reduction_percentage": ((total_baseline - total_target) / total_baseline) * 100,
            "annual_savings_projection": (total_baseline - total_target) * 12
        }

class ProductionCacheConfig:
    """Production-ready cache configuration."""

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.config = CachingConfig()

        # Environment-specific overrides
        if environment == "production":
            self._apply_production_settings()
        elif environment == "staging":
            self._apply_staging_settings()
        elif environment == "development":
            self._apply_development_settings()

    def _apply_production_settings(self):
        """Apply production-optimized settings."""
        # Larger cache for production
        self.config.max_cache_size_mb = 1000.0  # 1GB cache
        self.config.cache_cleanup_threshold_mb = 800.0

        # Longer TTLs for stable production content
        self.config.strategy_ttl_overrides.update({
            "aggressive": 172800,  # 48h for stable content
            "standard": 28800,     # 8h for standard content
        })

        # Production Redis with clustering
        self.config.redis_url = os.getenv(
            "CLAUDE_CACHE_REDIS_URL",
            "redis://prod-redis-cluster:6379/2"
        )

    def _apply_staging_settings(self):
        """Apply staging environment settings."""
        # Moderate cache size for staging
        self.config.max_cache_size_mb = 250.0
        self.config.cache_cleanup_threshold_mb = 200.0

        # Shorter TTLs for testing
        self.config.strategy_ttl_overrides.update({
            "aggressive": 43200,   # 12h
            "standard": 7200,      # 2h
        })

    def _apply_development_settings(self):
        """Apply development environment settings."""
        # Small cache for development
        self.config.max_cache_size_mb = 50.0
        self.config.cache_cleanup_threshold_mb = 40.0

        # Very short TTLs for development
        self.config.strategy_ttl_overrides.update({
            "aggressive": 3600,    # 1h
            "standard": 1800,      # 30min
            "conservative": 900,   # 15min
            "real_time": 300,      # 5min
        })

        # Local Redis for development
        self.config.redis_url = "redis://localhost:6379/2"

# Cache monitoring configuration
class CacheMonitoringConfig:
    """Monitoring and alerting configuration for cache performance."""

    # Metrics collection intervals
    METRICS_COLLECTION_INTERVALS = {
        "real_time": 60,        # 1 minute
        "short_term": 300,      # 5 minutes
        "medium_term": 1800,    # 30 minutes
        "long_term": 3600       # 1 hour
    }

    # Performance benchmarks
    PERFORMANCE_BENCHMARKS = {
        "cache_retrieval_time_ms": 10,      # < 10ms cache retrieval
        "cache_storage_time_ms": 50,        # < 50ms cache storage
        "compression_ratio_min": 2.0,       # > 2x compression
        "hit_ratio_target": 0.70,           # 70% hit ratio target
        "memory_efficiency_mb_per_k_requests": 5.0  # < 5MB per 1K requests
    }

    # Alert conditions
    ALERT_CONDITIONS = {
        "cache_retrieval_slow": {
            "condition": "cache_retrieval_time_ms > 25",
            "severity": "warning",
            "action": "investigate_redis_performance"
        },
        "hit_ratio_low": {
            "condition": "hit_ratio < 0.5",
            "severity": "critical",
            "action": "review_caching_strategy"
        },
        "cost_target_missed": {
            "condition": "monthly_cost_reduction < 0.6",
            "severity": "warning",
            "action": "optimize_cache_patterns"
        },
        "cache_size_critical": {
            "condition": "cache_utilization > 0.95",
            "severity": "critical",
            "action": "immediate_cleanup_required"
        }
    }

# Usage examples for integration
class CacheUsageExamples:
    """Examples of how to integrate caching with existing services."""

    @staticmethod
    def property_analysis_integration():
        """Example: Integrating caching with property analysis."""
        return """
        # Before caching integration:
        async def analyze_property(self, property_data):
            response = await self.claude_client.call(
                prompt=f"Analyze property: {property_data}",
                system_prompt="You are a property expert"
            )
            return response

        # After caching integration:
        async def analyze_property_cached(self, property_data):
            from ghl_real_estate_ai.services.claude_prompt_caching_service import cached_claude_call

            content, was_cached, cost = await cached_claude_call(
                prompt=f"Analyze property: {property_data}",
                system_prompt="You are a property expert",
                claude_api_function=self.claude_client.call,
                context_data={"type": "property_analysis", "property_id": property_data.get("id")}
            )

            # Log cache performance
            self.metrics.record_cache_hit(was_cached, cost)
            return content
        """

    @staticmethod
    def batch_caching_integration():
        """Example: Batch caching for high-volume operations."""
        return """
        # Batch property analysis with caching
        async def analyze_properties_batch_cached(self, properties_list):
            from ghl_real_estate_ai.services.claude_prompt_caching_service import ClaudePromptCachingService, RealEstateCachePatterns

            async with ClaudePromptCachingService() as cache_service:
                # Prepare batch requests
                requests = [
                    RealEstateCachePatterns.property_analysis_request(prop_data)
                    for prop_data in properties_list
                ]

                # Warm cache for batch processing
                await cache_service.warm_cache(requests, self.claude_client.call, concurrency_limit=3)

                # Process with high cache hit ratio
                results = []
                for request in requests:
                    response, was_cached = await cache_service.get_or_call_claude(
                        request, self.claude_client.call
                    )
                    results.append({
                        "content": response.content,
                        "cached": was_cached,
                        "cost": response.cost
                    })

                return results
        """

# Default configuration instance
default_config = ProductionCacheConfig(
    environment=os.getenv("ENVIRONMENT", "production")
)

# Cost optimization targets
cost_targets = CostOptimizationTargets.calculate_total_monthly_savings()

# Export key configuration
__all__ = [
    "CachingConfig",
    "CacheWarmingProfiles",
    "ClaudeCacheIntegration",
    "CostOptimizationTargets",
    "ProductionCacheConfig",
    "CacheMonitoringConfig",
    "CacheUsageExamples",
    "default_config",
    "cost_targets"
]