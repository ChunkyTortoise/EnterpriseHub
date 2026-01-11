"""
Deployment Configuration for Phase 4 Enterprise Scaling

Provides configuration management for:
- Redis cluster deployment
- Database shard deployment
- Environment-specific settings
- Railway/Vercel deployment integration

Deployment Targets:
- Development: Single-node Redis, single PostgreSQL
- Staging: 3-node Redis cluster, 2 database shards
- Production: 6-node Redis cluster (3 masters + 3 replicas), 3+ database shards
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from ghl_real_estate_ai.infrastructure.redis_cluster_config import RedisClusterConfig, ClusterNode, NodeRole
from ghl_real_estate_ai.infrastructure.database_sharding_strategy import ShardConfig, ShardingStrategy


class DeploymentEnvironment(str, Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnterpriseDeploymentConfig:
    """Complete deployment configuration for enterprise scaling."""

    environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT

    # Redis cluster configuration
    redis_cluster: Optional[RedisClusterConfig] = None

    # Database sharding configuration
    database_shards: List[ShardConfig] = field(default_factory=list)
    sharding_strategy: ShardingStrategy = ShardingStrategy.LOCATION

    # Performance targets (Phase 4)
    target_redis_latency_ms: float = 1.0
    target_redis_uptime: float = 99.95
    target_db_p90_ms: float = 50.0
    target_cross_shard_p95_ms: float = 100.0
    target_concurrent_users: int = 1000

    # Scaling thresholds
    connection_pool_scale_threshold: float = 85.0  # Percent utilization
    shard_rebalance_threshold: float = 70.0  # Balance score
    auto_scaling_enabled: bool = True

    # Monitoring configuration
    health_check_interval: int = 5  # seconds
    metrics_retention_hours: int = 24
    alert_webhook_url: Optional[str] = None

    # Railway/Vercel integration
    railway_project_id: Optional[str] = None
    vercel_project_id: Optional[str] = None

    def __post_init__(self):
        """Initialize environment-specific defaults."""
        if self.redis_cluster is None:
            self.redis_cluster = self._get_default_redis_config()

        if not self.database_shards:
            self.database_shards = self._get_default_shard_config()

    def _get_default_redis_config(self) -> RedisClusterConfig:
        """Get default Redis configuration for environment."""
        if self.environment == DeploymentEnvironment.DEVELOPMENT:
            return RedisClusterConfig(
                cluster_id="enterprisehub-dev",
                nodes=[
                    {"host": "localhost", "port": 6379, "id": "node-0", "role": "master"}
                ],
                min_master_nodes=1,
                replica_count=0,
                virtual_nodes=50,
                health_check_interval=10
            )

        elif self.environment == DeploymentEnvironment.STAGING:
            return RedisClusterConfig(
                cluster_id="enterprisehub-staging",
                nodes=[
                    {"host": "redis-staging-1", "port": 6379, "id": "node-0", "role": "master"},
                    {"host": "redis-staging-2", "port": 6379, "id": "node-1", "role": "master"},
                    {"host": "redis-staging-3", "port": 6379, "id": "node-2", "role": "master"},
                ],
                min_master_nodes=2,
                replica_count=0,
                virtual_nodes=100,
                health_check_interval=5
            )

        else:  # Production
            return RedisClusterConfig(
                cluster_id="enterprisehub-prod",
                nodes=[
                    {"host": "redis-prod-1", "port": 6379, "id": "node-0", "role": "master"},
                    {"host": "redis-prod-2", "port": 6379, "id": "node-1", "role": "master"},
                    {"host": "redis-prod-3", "port": 6379, "id": "node-2", "role": "master"},
                    {"host": "redis-prod-4", "port": 6379, "id": "node-3", "role": "replica", "master_id": "node-0"},
                    {"host": "redis-prod-5", "port": 6379, "id": "node-4", "role": "replica", "master_id": "node-1"},
                    {"host": "redis-prod-6", "port": 6379, "id": "node-5", "role": "replica", "master_id": "node-2"},
                ],
                min_master_nodes=3,
                replica_count=1,
                virtual_nodes=150,
                health_check_interval=5,
                max_replication_lag_ms=1000.0
            )

    def _get_default_shard_config(self) -> List[ShardConfig]:
        """Get default shard configuration for environment."""
        if self.environment == DeploymentEnvironment.DEVELOPMENT:
            return [
                ShardConfig(
                    shard_id="shard-primary",
                    host="localhost",
                    port=5432,
                    database="enterprisehub",
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", ""),
                    hash_range_start=0,
                    hash_range_end=1000000,
                    location_ids=["loc_default"],
                    min_connections=2,
                    max_connections=10
                )
            ]

        elif self.environment == DeploymentEnvironment.STAGING:
            return [
                ShardConfig(
                    shard_id="shard-1",
                    host="db-staging-1",
                    port=5432,
                    database="enterprisehub_shard1",
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", ""),
                    hash_range_start=0,
                    hash_range_end=500000,
                    min_connections=5,
                    max_connections=25
                ),
                ShardConfig(
                    shard_id="shard-2",
                    host="db-staging-2",
                    port=5432,
                    database="enterprisehub_shard2",
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", ""),
                    hash_range_start=500001,
                    hash_range_end=1000000,
                    min_connections=5,
                    max_connections=25
                )
            ]

        else:  # Production
            return [
                ShardConfig(
                    shard_id="shard-1",
                    host=os.getenv("DB_SHARD1_HOST", "db-prod-1"),
                    port=5432,
                    database="enterprisehub_shard1",
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", ""),
                    hash_range_start=0,
                    hash_range_end=333333,
                    min_connections=10,
                    max_connections=50
                ),
                ShardConfig(
                    shard_id="shard-2",
                    host=os.getenv("DB_SHARD2_HOST", "db-prod-2"),
                    port=5432,
                    database="enterprisehub_shard2",
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", ""),
                    hash_range_start=333334,
                    hash_range_end=666666,
                    min_connections=10,
                    max_connections=50
                ),
                ShardConfig(
                    shard_id="shard-3",
                    host=os.getenv("DB_SHARD3_HOST", "db-prod-3"),
                    port=5432,
                    database="enterprisehub_shard3",
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", ""),
                    hash_range_start=666667,
                    hash_range_end=1000000,
                    min_connections=10,
                    max_connections=50
                )
            ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment.value,
            "redis_cluster": {
                "cluster_id": self.redis_cluster.cluster_id,
                "nodes": len(self.redis_cluster.nodes),
                "min_master_nodes": self.redis_cluster.min_master_nodes,
                "replica_count": self.redis_cluster.replica_count
            },
            "database_shards": [
                {
                    "shard_id": s.shard_id,
                    "host": s.host,
                    "database": s.database
                }
                for s in self.database_shards
            ],
            "targets": {
                "redis_latency_ms": self.target_redis_latency_ms,
                "redis_uptime": self.target_redis_uptime,
                "db_p90_ms": self.target_db_p90_ms,
                "cross_shard_p95_ms": self.target_cross_shard_p95_ms,
                "concurrent_users": self.target_concurrent_users
            },
            "scaling": {
                "pool_threshold": self.connection_pool_scale_threshold,
                "rebalance_threshold": self.shard_rebalance_threshold,
                "auto_scaling": self.auto_scaling_enabled
            }
        }


def get_deployment_config(
    environment: Optional[str] = None
) -> EnterpriseDeploymentConfig:
    """
    Get deployment configuration for environment.

    Args:
        environment: Override environment (defaults to ENV var or development)

    Returns:
        EnterpriseDeploymentConfig instance
    """
    if environment is None:
        environment = os.getenv("DEPLOYMENT_ENVIRONMENT", "development")

    try:
        env = DeploymentEnvironment(environment.lower())
    except ValueError:
        env = DeploymentEnvironment.DEVELOPMENT

    config = EnterpriseDeploymentConfig(environment=env)

    # Override from environment variables
    if os.getenv("REDIS_CLUSTER_NODES"):
        # Parse comma-separated node list
        nodes = []
        for i, node_spec in enumerate(os.getenv("REDIS_CLUSTER_NODES", "").split(",")):
            if ":" in node_spec:
                host, port = node_spec.split(":")
                nodes.append({
                    "host": host,
                    "port": int(port),
                    "id": f"node-{i}",
                    "role": "master"
                })

        if nodes:
            config.redis_cluster.nodes = nodes

    # Railway-specific configuration
    if os.getenv("RAILWAY_ENVIRONMENT"):
        config.railway_project_id = os.getenv("RAILWAY_PROJECT_ID")

        # Railway provides Redis URL
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            # Parse Redis URL and configure cluster
            from urllib.parse import urlparse
            parsed = urlparse(redis_url)
            config.redis_cluster.nodes = [{
                "host": parsed.hostname,
                "port": parsed.port or 6379,
                "id": "railway-redis",
                "role": "master"
            }]

        # Railway PostgreSQL configuration
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            config.database_shards = [
                ShardConfig(
                    shard_id="railway-db",
                    host=parsed.hostname,
                    port=parsed.port or 5432,
                    database=parsed.path.lstrip("/"),
                    user=parsed.username,
                    password=parsed.password,
                    hash_range_start=0,
                    hash_range_end=1000000
                )
            ]

    return config


# Pre-configured deployments for common scenarios
DEVELOPMENT_CONFIG = EnterpriseDeploymentConfig(
    environment=DeploymentEnvironment.DEVELOPMENT,
    target_concurrent_users=100,
    auto_scaling_enabled=False,
    health_check_interval=30
)

STAGING_CONFIG = EnterpriseDeploymentConfig(
    environment=DeploymentEnvironment.STAGING,
    target_concurrent_users=500,
    auto_scaling_enabled=True,
    health_check_interval=10
)

PRODUCTION_CONFIG = EnterpriseDeploymentConfig(
    environment=DeploymentEnvironment.PRODUCTION,
    target_concurrent_users=1000,
    auto_scaling_enabled=True,
    health_check_interval=5,
    alert_webhook_url=os.getenv("ALERT_WEBHOOK_URL")
)


__all__ = [
    "DeploymentEnvironment",
    "EnterpriseDeploymentConfig",
    "get_deployment_config",
    "DEVELOPMENT_CONFIG",
    "STAGING_CONFIG",
    "PRODUCTION_CONFIG",
]
