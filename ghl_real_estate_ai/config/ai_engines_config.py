"""
AI Engines Configuration

Configuration settings for integrating Competitive Intelligence and Predictive Lead Lifecycle engines
with existing performance-optimized services and infrastructure.

Features:
- Environment-specific configuration
- Performance optimization settings
- Resource allocation and scaling
- Integration with existing services
- Monitoring and alerting configuration
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class PerformanceProfile(Enum):
    """Performance optimization profiles"""
    DEVELOPMENT = "development"  # Optimized for development speed
    BALANCED = "balanced"        # Balanced performance and resource usage
    HIGH_PERFORMANCE = "high_performance"  # Optimized for maximum performance
    COST_OPTIMIZED = "cost_optimized"     # Optimized for cost efficiency


@dataclass
class RedisConfig:
    """Redis configuration for AI engines"""
    url: str
    enable_compression: bool = True
    connection_pool_size: int = 20
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 2.0
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class DatabaseConfig:
    """Database configuration for AI engines"""
    url: str
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    enable_caching: bool = True
    cache_ttl: int = 1800  # 30 minutes


@dataclass
class MLServiceConfig:
    """ML service configuration"""
    model_cache_dir: str
    enable_model_warming: bool = True
    batch_size: int = 32
    max_batch_delay_ms: float = 100.0
    model_timeout: float = 30.0
    enable_gpu: bool = True
    gpu_memory_limit: Optional[float] = None


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    # Processing targets
    max_competitive_analysis_time_ms: float = 50.0
    max_prediction_time_ms: float = 25.0
    max_unified_analysis_time_ms: float = 75.0

    # Concurrency limits
    max_concurrent_requests: int = 10
    max_concurrent_batch: int = 5
    semaphore_timeout: float = 30.0

    # Caching
    enable_result_caching: bool = True
    cache_ttl: int = 1800  # 30 minutes
    cache_hit_rate_target: float = 0.90

    # Resource monitoring
    cpu_threshold: float = 0.8
    memory_threshold: float = 0.8
    enable_auto_scaling: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring and alerting configuration"""
    enable_performance_monitoring: bool = True
    metrics_collection_interval: int = 60  # seconds
    enable_health_checks: bool = True
    health_check_interval: int = 30  # seconds

    # Alerting thresholds
    response_time_alert_threshold_ms: float = 100.0
    error_rate_alert_threshold: float = 0.05  # 5%
    cache_hit_rate_alert_threshold: float = 0.80  # 80%

    # Logging
    log_level: str = "INFO"
    enable_structured_logging: bool = True
    log_performance_metrics: bool = True


@dataclass
class AIEnginesConfig:
    """Complete AI engines configuration"""
    environment: Environment
    performance_profile: PerformanceProfile

    # Service configurations
    redis: RedisConfig
    database: DatabaseConfig
    ml_service: MLServiceConfig

    # Performance and monitoring
    performance: PerformanceConfig
    monitoring: MonitoringConfig

    # Feature flags
    enable_competitive_engine: bool = True
    enable_predictive_engine: bool = True
    enable_cross_engine_fusion: bool = True
    enable_real_time_monitoring: bool = True

    # Integration settings
    webhook_integration: bool = True
    ghl_integration: bool = True
    streamlit_integration: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "environment": self.environment.value,
            "performance_profile": self.performance_profile.value,
            "redis_url": self.redis.url,
            "database_url": self.database.url,
            "model_cache_dir": self.ml_service.model_cache_dir,
            "enable_compression": self.redis.enable_compression,
            "enable_model_warming": self.ml_service.enable_model_warming,
            "max_concurrent_requests": self.performance.max_concurrent_requests,
            "enable_result_caching": self.performance.enable_result_caching,
            "cache_ttl": self.performance.cache_ttl,
            "enable_performance_monitoring": self.monitoring.enable_performance_monitoring,
            "log_level": self.monitoring.log_level,
        }


class AIEnginesConfigFactory:
    """Factory for creating AI engines configurations"""

    @staticmethod
    def create_config(
        environment: Environment = Environment.PRODUCTION,
        performance_profile: PerformanceProfile = PerformanceProfile.BALANCED
    ) -> AIEnginesConfig:
        """Create configuration based on environment and performance profile"""

        # Base configurations
        redis_config = AIEnginesConfigFactory._create_redis_config(environment, performance_profile)
        database_config = AIEnginesConfigFactory._create_database_config(environment, performance_profile)
        ml_config = AIEnginesConfigFactory._create_ml_config(environment, performance_profile)
        performance_config = AIEnginesConfigFactory._create_performance_config(environment, performance_profile)
        monitoring_config = AIEnginesConfigFactory._create_monitoring_config(environment)

        return AIEnginesConfig(
            environment=environment,
            performance_profile=performance_profile,
            redis=redis_config,
            database=database_config,
            ml_service=ml_config,
            performance=performance_config,
            monitoring=monitoring_config,
            enable_competitive_engine=True,
            enable_predictive_engine=True,
            enable_cross_engine_fusion=True,
            enable_real_time_monitoring=environment == Environment.PRODUCTION,
            webhook_integration=True,
            ghl_integration=True,
            streamlit_integration=True
        )

    @staticmethod
    def _create_redis_config(environment: Environment, profile: PerformanceProfile) -> RedisConfig:
        """Create Redis configuration based on environment and profile"""
        base_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        if profile == PerformanceProfile.HIGH_PERFORMANCE:
            return RedisConfig(
                url=base_url,
                enable_compression=True,
                connection_pool_size=30,
                max_connections=100,
                socket_timeout=2.0,
                socket_connect_timeout=1.0,
                retry_on_timeout=True,
                health_check_interval=15
            )
        elif profile == PerformanceProfile.COST_OPTIMIZED:
            return RedisConfig(
                url=base_url,
                enable_compression=True,
                connection_pool_size=10,
                max_connections=25,
                socket_timeout=10.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True,
                health_check_interval=60
            )
        else:  # Balanced or Development
            return RedisConfig(
                url=base_url,
                enable_compression=True,
                connection_pool_size=20,
                max_connections=50,
                socket_timeout=5.0,
                socket_connect_timeout=2.0,
                retry_on_timeout=True,
                health_check_interval=30
            )

    @staticmethod
    def _create_database_config(environment: Environment, profile: PerformanceProfile) -> DatabaseConfig:
        """Create database configuration based on environment and profile"""
        base_url = os.getenv("DATABASE_URL", "postgresql://localhost/enterprisehub")

        if profile == PerformanceProfile.HIGH_PERFORMANCE:
            return DatabaseConfig(
                url=base_url,
                pool_size=30,
                max_overflow=50,
                pool_timeout=20,
                pool_recycle=1800,  # 30 minutes
                echo=environment == Environment.DEVELOPMENT,
                enable_caching=True,
                cache_ttl=3600  # 1 hour
            )
        elif profile == PerformanceProfile.COST_OPTIMIZED:
            return DatabaseConfig(
                url=base_url,
                pool_size=10,
                max_overflow=15,
                pool_timeout=60,
                pool_recycle=7200,  # 2 hours
                echo=False,
                enable_caching=True,
                cache_ttl=1800  # 30 minutes
            )
        else:  # Balanced or Development
            return DatabaseConfig(
                url=base_url,
                pool_size=20,
                max_overflow=30,
                pool_timeout=30,
                pool_recycle=3600,  # 1 hour
                echo=environment == Environment.DEVELOPMENT,
                enable_caching=True,
                cache_ttl=1800  # 30 minutes
            )

    @staticmethod
    def _create_ml_config(environment: Environment, profile: PerformanceProfile) -> MLServiceConfig:
        """Create ML service configuration based on environment and profile"""
        model_dir = os.getenv("MODEL_CACHE_DIR", "models")

        if profile == PerformanceProfile.HIGH_PERFORMANCE:
            return MLServiceConfig(
                model_cache_dir=model_dir,
                enable_model_warming=True,
                batch_size=64,
                max_batch_delay_ms=50.0,
                model_timeout=15.0,
                enable_gpu=True,
                gpu_memory_limit=0.8
            )
        elif profile == PerformanceProfile.COST_OPTIMIZED:
            return MLServiceConfig(
                model_cache_dir=model_dir,
                enable_model_warming=False,
                batch_size=16,
                max_batch_delay_ms=200.0,
                model_timeout=60.0,
                enable_gpu=False,
                gpu_memory_limit=None
            )
        else:  # Balanced or Development
            return MLServiceConfig(
                model_cache_dir=model_dir,
                enable_model_warming=True,
                batch_size=32,
                max_batch_delay_ms=100.0,
                model_timeout=30.0,
                enable_gpu=True,
                gpu_memory_limit=0.6
            )

    @staticmethod
    def _create_performance_config(environment: Environment, profile: PerformanceProfile) -> PerformanceConfig:
        """Create performance configuration based on environment and profile"""
        if profile == PerformanceProfile.HIGH_PERFORMANCE:
            return PerformanceConfig(
                max_competitive_analysis_time_ms=40.0,
                max_prediction_time_ms=20.0,
                max_unified_analysis_time_ms=60.0,
                max_concurrent_requests=20,
                max_concurrent_batch=10,
                semaphore_timeout=20.0,
                enable_result_caching=True,
                cache_ttl=3600,  # 1 hour
                cache_hit_rate_target=0.95,
                cpu_threshold=0.9,
                memory_threshold=0.9,
                enable_auto_scaling=True
            )
        elif profile == PerformanceProfile.COST_OPTIMIZED:
            return PerformanceConfig(
                max_competitive_analysis_time_ms=75.0,
                max_prediction_time_ms=35.0,
                max_unified_analysis_time_ms=100.0,
                max_concurrent_requests=5,
                max_concurrent_batch=2,
                semaphore_timeout=60.0,
                enable_result_caching=True,
                cache_ttl=7200,  # 2 hours
                cache_hit_rate_target=0.85,
                cpu_threshold=0.7,
                memory_threshold=0.7,
                enable_auto_scaling=False
            )
        else:  # Balanced or Development
            return PerformanceConfig(
                max_competitive_analysis_time_ms=50.0,
                max_prediction_time_ms=25.0,
                max_unified_analysis_time_ms=75.0,
                max_concurrent_requests=10,
                max_concurrent_batch=5,
                semaphore_timeout=30.0,
                enable_result_caching=True,
                cache_ttl=1800,  # 30 minutes
                cache_hit_rate_target=0.90,
                cpu_threshold=0.8,
                memory_threshold=0.8,
                enable_auto_scaling=environment == Environment.PRODUCTION
            )

    @staticmethod
    def _create_monitoring_config(environment: Environment) -> MonitoringConfig:
        """Create monitoring configuration based on environment"""
        if environment == Environment.PRODUCTION:
            return MonitoringConfig(
                enable_performance_monitoring=True,
                metrics_collection_interval=30,  # More frequent in production
                enable_health_checks=True,
                health_check_interval=15,  # More frequent health checks
                response_time_alert_threshold_ms=75.0,  # Stricter in production
                error_rate_alert_threshold=0.02,  # 2% error rate
                cache_hit_rate_alert_threshold=0.85,  # 85% cache hit rate
                log_level="INFO",
                enable_structured_logging=True,
                log_performance_metrics=True
            )
        elif environment == Environment.STAGING:
            return MonitoringConfig(
                enable_performance_monitoring=True,
                metrics_collection_interval=60,
                enable_health_checks=True,
                health_check_interval=30,
                response_time_alert_threshold_ms=100.0,
                error_rate_alert_threshold=0.05,  # 5% error rate
                cache_hit_rate_alert_threshold=0.80,  # 80% cache hit rate
                log_level="INFO",
                enable_structured_logging=True,
                log_performance_metrics=True
            )
        else:  # Development
            return MonitoringConfig(
                enable_performance_monitoring=True,
                metrics_collection_interval=120,
                enable_health_checks=True,
                health_check_interval=60,
                response_time_alert_threshold_ms=200.0,  # More relaxed in dev
                error_rate_alert_threshold=0.10,  # 10% error rate
                cache_hit_rate_alert_threshold=0.70,  # 70% cache hit rate
                log_level="DEBUG",
                enable_structured_logging=False,
                log_performance_metrics=False
            )


# Default configurations for each environment
DEVELOPMENT_CONFIG = AIEnginesConfigFactory.create_config(
    Environment.DEVELOPMENT,
    PerformanceProfile.DEVELOPMENT
)

STAGING_CONFIG = AIEnginesConfigFactory.create_config(
    Environment.STAGING,
    PerformanceProfile.BALANCED
)

PRODUCTION_CONFIG = AIEnginesConfigFactory.create_config(
    Environment.PRODUCTION,
    PerformanceProfile.HIGH_PERFORMANCE
)

PRODUCTION_COST_OPTIMIZED_CONFIG = AIEnginesConfigFactory.create_config(
    Environment.PRODUCTION,
    PerformanceProfile.COST_OPTIMIZED
)


def get_config(environment: Optional[str] = None) -> AIEnginesConfig:
    """Get configuration for specified environment or from environment variable"""
    env = environment or os.getenv("ENVIRONMENT", "production").lower()

    if env == "development":
        return DEVELOPMENT_CONFIG
    elif env == "staging":
        return STAGING_CONFIG
    elif env == "production":
        # Check for cost optimization flag
        if os.getenv("COST_OPTIMIZED", "false").lower() == "true":
            return PRODUCTION_COST_OPTIMIZED_CONFIG
        return PRODUCTION_CONFIG
    else:
        # Default to production for unknown environments
        return PRODUCTION_CONFIG


def get_environment_variables() -> Dict[str, str]:
    """Get required environment variables for AI engines"""
    return {
        "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql://localhost/enterprisehub"),
        "MODEL_CACHE_DIR": os.getenv("MODEL_CACHE_DIR", "models"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "production"),
        "COST_OPTIMIZED": os.getenv("COST_OPTIMIZED", "false"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "ENABLE_GPU": os.getenv("ENABLE_GPU", "true"),
        "MAX_CONCURRENT_REQUESTS": os.getenv("MAX_CONCURRENT_REQUESTS", "10"),
        "CACHE_TTL": os.getenv("CACHE_TTL", "1800"),
    }


def validate_environment() -> bool:
    """Validate that all required environment variables are set"""
    required_vars = [
        "REDIS_URL",
        "DATABASE_URL"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False

    print("✅ All required environment variables are set")
    return True


# Export main configuration getter
__all__ = [
    "get_config",
    "get_environment_variables",
    "validate_environment",
    "AIEnginesConfig",
    "Environment",
    "PerformanceProfile"
]