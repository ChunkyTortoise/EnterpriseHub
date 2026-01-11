"""
Infrastructure module for EnterpriseHub deployment automation.

Provides:
- Blue-green deployment orchestration
- Health check validation
- Automated rollback capabilities
- Zero-downtime deployment coordination

Phase 4 Enterprise Scaling:
- Redis Cluster: High-availability distributed caching with consistent hashing
- Database Sharding: Horizontal partitioning by location_id for GHL multi-tenant model
- Replication Management: Cross-node replication with lag monitoring
- Connection Pool Management: Adaptive pooling for 1000+ concurrent users

Performance Targets:
- Redis cluster: 99.95% uptime, <1ms latency
- Database sharding: Linear scaling, 1000+ concurrent users
- Cross-shard queries: <100ms P95 latency
- Zero data loss during topology changes
"""

__version__ = "2.0.0"

# Phase 4 Enterprise Scaling Imports
try:
    from ghl_real_estate_ai.infrastructure.redis_cluster_config import (
        RedisClusterConfig,
        RedisClusterManager,
        ConsistentHashRing,
        ClusterNode,
        ClusterHealthStatus,
        get_redis_cluster_manager,
        cluster_cached,
    )

    from ghl_real_estate_ai.infrastructure.database_sharding_strategy import (
        ShardingStrategy,
        ShardManager,
        ShardRouter,
        ShardConfig,
        CrossShardQuery,
        get_shard_manager,
        location_sharded,
    )

    from ghl_real_estate_ai.infrastructure.enterprise_scaling_monitor import (
        EnterpriseScalingMonitor,
        Alert,
        AlertSeverity,
        ComponentType,
        ComponentHealth,
        PerformanceTarget,
        ScalingRecommendation,
        get_enterprise_monitor,
    )

    from ghl_real_estate_ai.infrastructure.deployment_config import (
        DeploymentEnvironment,
        EnterpriseDeploymentConfig,
        get_deployment_config,
        DEVELOPMENT_CONFIG,
        STAGING_CONFIG,
        PRODUCTION_CONFIG,
    )

    ENTERPRISE_SCALING_AVAILABLE = True
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f"Enterprise scaling imports failed: {e}")
    ENTERPRISE_SCALING_AVAILABLE = False

__all__ = [
    "__version__",
    "ENTERPRISE_SCALING_AVAILABLE",
]

if ENTERPRISE_SCALING_AVAILABLE:
    __all__.extend([
        # Redis Cluster
        "RedisClusterConfig",
        "RedisClusterManager",
        "ConsistentHashRing",
        "ClusterNode",
        "ClusterHealthStatus",
        "get_redis_cluster_manager",
        "cluster_cached",
        # Database Sharding
        "ShardingStrategy",
        "ShardManager",
        "ShardRouter",
        "ShardConfig",
        "CrossShardQuery",
        "get_shard_manager",
        "location_sharded",
        # Enterprise Monitoring
        "EnterpriseScalingMonitor",
        "Alert",
        "AlertSeverity",
        "ComponentType",
        "ComponentHealth",
        "PerformanceTarget",
        "ScalingRecommendation",
        "get_enterprise_monitor",
        # Deployment Configuration
        "DeploymentEnvironment",
        "EnterpriseDeploymentConfig",
        "get_deployment_config",
        "DEVELOPMENT_CONFIG",
        "STAGING_CONFIG",
        "PRODUCTION_CONFIG",
    ])
