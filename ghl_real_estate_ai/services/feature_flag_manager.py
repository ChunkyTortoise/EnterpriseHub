"""
Feature Flag Management Service for Phase 3 A/B Testing
=======================================================

Redis-backed feature flag system for progressive rollout and A/B testing.

Features:
- Per-tenant feature control
- Traffic splitting (10% → 25% → 50% → 100%)
- Automatic rollback on failure
- Performance monitoring integration
- User bucketing for consistent experience

Performance Targets:
- Flag lookup: <1ms (Redis cache)
- Rollout decision: <5ms
- Metric collection: Async, non-blocking

Business Impact:
- Safe progressive rollouts
- Data-driven feature validation
- ROI measurement per feature
- Risk mitigation through gradual deployment

Phase 3 Features Managed:
- Real-Time Intelligence Dashboard
- Multimodal Property Intelligence
- Proactive Churn Prevention
- AI-Powered Coaching

Author: EnterpriseHub Development Team
Created: January 2026
Version: 1.0.0
"""

import asyncio
import hashlib
import time
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import logging

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class RolloutStage(str, Enum):
    """Progressive rollout stages."""
    DISABLED = "disabled"
    INTERNAL = "internal"  # Internal testing only
    BETA_10 = "beta_10"    # 10% of users
    BETA_25 = "beta_25"    # 25% of users
    BETA_50 = "beta_50"    # 50% of users
    GA = "ga"              # 100% - General Availability


class FeatureStatus(str, Enum):
    """Feature flag status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ROLLED_BACK = "rolled_back"
    ARCHIVED = "archived"


class RollbackReason(str, Enum):
    """Automatic rollback triggers."""
    ERROR_RATE_SPIKE = "error_rate_spike"
    LATENCY_DEGRADATION = "latency_degradation"
    BUSINESS_METRIC_DROP = "business_metric_drop"
    MANUAL = "manual"


@dataclass
class FeatureFlag:
    """Feature flag configuration."""
    feature_id: str
    name: str
    description: str

    # Rollout configuration
    rollout_stage: RolloutStage = RolloutStage.DISABLED
    status: FeatureStatus = FeatureStatus.ACTIVE

    # Traffic control
    percentage: float = 0.0  # 0-100
    tenant_whitelist: List[str] = field(default_factory=list)
    tenant_blacklist: List[str] = field(default_factory=list)

    # A/B testing
    variant_name: str = "treatment"  # "control" vs "treatment"
    experiment_id: Optional[str] = None

    # Automatic rollback thresholds
    error_rate_threshold: float = 5.0  # % error rate
    latency_threshold_ms: float = 1000.0  # P95 latency
    metric_drop_threshold: float = 10.0  # % drop in key metric

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"

    # Business tracking
    roi_target: float = 0.0  # Annual ROI target
    current_roi: float = 0.0  # Measured ROI

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['rollout_stage'] = self.rollout_stage.value
        result['status'] = self.status.value
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureFlag':
        """Create from dictionary."""
        data = data.copy()
        data['rollout_stage'] = RolloutStage(data.get('rollout_stage', 'disabled'))
        data['status'] = FeatureStatus(data.get('status', 'active'))
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class UserBucket:
    """User bucketing for consistent A/B test experience."""
    user_id: str
    tenant_id: str
    bucket_hash: int
    variant: str  # "control" or "treatment"
    assigned_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'bucket_hash': self.bucket_hash,
            'variant': self.variant,
            'assigned_at': self.assigned_at.isoformat()
        }


class FeatureFlagManager:
    """
    Feature flag management service with A/B testing support.

    Provides:
    - Feature flag evaluation with <1ms latency
    - User bucketing for consistent experience
    - Progressive rollout management
    - Automatic rollback on performance degradation
    - Business metrics tracking integration
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        cache_ttl: int = 60
    ):
        """
        Initialize feature flag manager.

        Args:
            redis_url: Redis connection URL
            cache_ttl: Cache TTL in seconds
        """
        self.redis_url = redis_url
        self.cache_ttl = cache_ttl

        # Redis client
        self.redis: Optional[Any] = None

        # Local cache for flag lookups
        self.flag_cache: Dict[str, FeatureFlag] = {}
        self.cache_timestamps: Dict[str, float] = {}

        # User bucket cache
        self.bucket_cache: Dict[str, UserBucket] = {}

        # Performance metrics
        self.lookup_times: List[float] = []

        # Redis key prefixes
        self.FLAG_PREFIX = "feature_flag:"
        self.BUCKET_PREFIX = "user_bucket:"
        self.METRICS_PREFIX = "flag_metrics:"

        logger.info("FeatureFlagManager initialized")

    async def initialize(self) -> bool:
        """Initialize Redis connection."""
        try:
            if aioredis is None:
                logger.warning("Redis not available, using in-memory cache only")
                return True

            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=1.0
            )

            await self.redis.ping()
            logger.info("Redis connection established for feature flags")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            return False

    async def create_flag(self, flag: FeatureFlag) -> bool:
        """
        Create or update feature flag.

        Args:
            flag: FeatureFlag configuration

        Returns:
            True if successful
        """
        try:
            flag.updated_at = datetime.utcnow()

            # Save to Redis
            if self.redis:
                key = f"{self.FLAG_PREFIX}{flag.feature_id}"
                await self.redis.setex(
                    key,
                    86400,  # 24 hour TTL
                    json.dumps(flag.to_dict())
                )

            # Update cache
            self.flag_cache[flag.feature_id] = flag
            self.cache_timestamps[flag.feature_id] = time.time()

            logger.info(f"Feature flag created/updated: {flag.feature_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create flag {flag.feature_id}: {e}")
            return False

    async def get_flag(self, feature_id: str) -> Optional[FeatureFlag]:
        """
        Get feature flag configuration.

        Args:
            feature_id: Feature identifier

        Returns:
            FeatureFlag if found, None otherwise
        """
        start_time = time.time()

        try:
            # Check local cache first
            if feature_id in self.flag_cache:
                cache_age = time.time() - self.cache_timestamps.get(feature_id, 0)
                if cache_age < self.cache_ttl:
                    return self.flag_cache[feature_id]

            # Fetch from Redis
            if self.redis:
                key = f"{self.FLAG_PREFIX}{feature_id}"
                data = await self.redis.get(key)

                if data:
                    flag = FeatureFlag.from_dict(json.loads(data))
                    self.flag_cache[feature_id] = flag
                    self.cache_timestamps[feature_id] = time.time()
                    return flag

            return None

        except Exception as e:
            logger.error(f"Error fetching flag {feature_id}: {e}")
            return self.flag_cache.get(feature_id)

        finally:
            # Track lookup time
            lookup_time = (time.time() - start_time) * 1000
            self.lookup_times.append(lookup_time)
            if len(self.lookup_times) > 1000:
                self.lookup_times.pop(0)

    async def is_enabled(
        self,
        feature_id: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if feature is enabled for given tenant/user.

        Args:
            feature_id: Feature identifier
            tenant_id: Tenant identifier
            user_id: Optional user identifier for bucketing
            context: Additional context for evaluation

        Returns:
            True if feature enabled
        """
        try:
            flag = await self.get_flag(feature_id)

            if not flag:
                return False

            # Check status
            if flag.status != FeatureStatus.ACTIVE:
                return False

            # Check rollout stage
            if flag.rollout_stage == RolloutStage.DISABLED:
                return False

            # Check blacklist
            if tenant_id in flag.tenant_blacklist:
                return False

            # Check whitelist
            if flag.tenant_whitelist and tenant_id in flag.tenant_whitelist:
                return True

            # Internal testing only
            if flag.rollout_stage == RolloutStage.INTERNAL:
                return tenant_id in flag.tenant_whitelist

            # General availability
            if flag.rollout_stage == RolloutStage.GA:
                return True

            # Percentage-based rollout
            if user_id:
                bucket = await self._get_user_bucket(
                    feature_id,
                    tenant_id,
                    user_id
                )
                return bucket.bucket_hash % 100 < flag.percentage

            # Default to percentage for tenant-level check
            tenant_hash = self._hash_string(f"{feature_id}:{tenant_id}")
            return tenant_hash % 100 < flag.percentage

        except Exception as e:
            logger.error(f"Error evaluating flag {feature_id}: {e}")
            return False

    async def get_variant(
        self,
        feature_id: str,
        tenant_id: str,
        user_id: str
    ) -> str:
        """
        Get A/B test variant for user.

        Args:
            feature_id: Feature identifier
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            Variant name ("control" or "treatment")
        """
        try:
            # Get or create user bucket
            bucket = await self._get_user_bucket(
                feature_id,
                tenant_id,
                user_id
            )

            return bucket.variant

        except Exception as e:
            logger.error(f"Error getting variant: {e}")
            return "control"  # Safe default

    async def _get_user_bucket(
        self,
        feature_id: str,
        tenant_id: str,
        user_id: str
    ) -> UserBucket:
        """Get or create user bucket for consistent assignment."""
        cache_key = f"{feature_id}:{tenant_id}:{user_id}"

        # Check cache
        if cache_key in self.bucket_cache:
            return self.bucket_cache[cache_key]

        # Check Redis
        if self.redis:
            redis_key = f"{self.BUCKET_PREFIX}{cache_key}"
            data = await self.redis.get(redis_key)

            if data:
                bucket_data = json.loads(data)
                bucket_data['assigned_at'] = datetime.fromisoformat(
                    bucket_data['assigned_at']
                )
                bucket = UserBucket(**bucket_data)
                self.bucket_cache[cache_key] = bucket
                return bucket

        # Create new bucket
        bucket_hash = self._hash_string(f"{feature_id}:{tenant_id}:{user_id}")

        # 50/50 split for A/B testing
        variant = "treatment" if bucket_hash % 2 == 0 else "control"

        bucket = UserBucket(
            user_id=user_id,
            tenant_id=tenant_id,
            bucket_hash=bucket_hash,
            variant=variant
        )

        # Save to Redis
        if self.redis:
            redis_key = f"{self.BUCKET_PREFIX}{cache_key}"
            await self.redis.setex(
                redis_key,
                86400 * 30,  # 30 days
                json.dumps(bucket.to_dict())
            )

        # Cache locally
        self.bucket_cache[cache_key] = bucket

        return bucket

    def _hash_string(self, s: str) -> int:
        """Generate consistent hash for string."""
        return int(hashlib.md5(s.encode()).hexdigest(), 16)

    async def update_rollout_stage(
        self,
        feature_id: str,
        stage: RolloutStage
    ) -> bool:
        """
        Update feature rollout stage.

        Args:
            feature_id: Feature identifier
            stage: New rollout stage

        Returns:
            True if successful
        """
        try:
            flag = await self.get_flag(feature_id)

            if not flag:
                logger.error(f"Flag {feature_id} not found")
                return False

            # Map stage to percentage
            stage_percentages = {
                RolloutStage.DISABLED: 0.0,
                RolloutStage.INTERNAL: 0.0,
                RolloutStage.BETA_10: 10.0,
                RolloutStage.BETA_25: 25.0,
                RolloutStage.BETA_50: 50.0,
                RolloutStage.GA: 100.0
            }

            flag.rollout_stage = stage
            flag.percentage = stage_percentages.get(stage, 0.0)

            await self.create_flag(flag)

            logger.info(f"Rollout stage updated: {feature_id} -> {stage.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update rollout stage: {e}")
            return False

    async def rollback_feature(
        self,
        feature_id: str,
        reason: RollbackReason,
        details: Optional[str] = None
    ) -> bool:
        """
        Rollback feature to disabled state.

        Args:
            feature_id: Feature identifier
            reason: Rollback reason
            details: Optional details

        Returns:
            True if successful
        """
        try:
            flag = await self.get_flag(feature_id)

            if not flag:
                return False

            flag.status = FeatureStatus.ROLLED_BACK
            flag.rollout_stage = RolloutStage.DISABLED
            flag.percentage = 0.0

            await self.create_flag(flag)

            # Log rollback event
            logger.warning(
                f"Feature rolled back: {feature_id}, "
                f"Reason: {reason.value}, Details: {details}"
            )

            # Record rollback metrics
            if self.redis:
                metrics_key = f"{self.METRICS_PREFIX}rollback:{feature_id}"
                await self.redis.rpush(
                    metrics_key,
                    json.dumps({
                        'timestamp': datetime.utcnow().isoformat(),
                        'reason': reason.value,
                        'details': details
                    })
                )

            return True

        except Exception as e:
            logger.error(f"Failed to rollback feature: {e}")
            return False

    async def get_all_flags(self) -> List[FeatureFlag]:
        """Get all feature flags."""
        flags = []

        try:
            if self.redis:
                # Scan for all flag keys
                async for key in self.redis.scan_iter(
                    match=f"{self.FLAG_PREFIX}*"
                ):
                    data = await self.redis.get(key)
                    if data:
                        flag = FeatureFlag.from_dict(json.loads(data))
                        flags.append(flag)
            else:
                # Return cached flags
                flags = list(self.flag_cache.values())

        except Exception as e:
            logger.error(f"Error fetching all flags: {e}")

        return flags

    async def record_flag_usage(
        self,
        feature_id: str,
        tenant_id: str,
        user_id: Optional[str],
        enabled: bool,
        variant: str
    ) -> None:
        """Record feature flag usage for analytics."""
        try:
            if not self.redis:
                return

            usage_key = f"{self.METRICS_PREFIX}usage:{feature_id}:{datetime.utcnow().strftime('%Y%m%d')}"

            await self.redis.hincrby(
                usage_key,
                f"{variant}:{'enabled' if enabled else 'disabled'}",
                1
            )

            # Set expiry
            await self.redis.expire(usage_key, 86400 * 90)  # 90 days

        except Exception as e:
            logger.error(f"Error recording flag usage: {e}")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get feature flag performance metrics."""
        if not self.lookup_times:
            return {"message": "No metrics available"}

        sorted_times = sorted(self.lookup_times)

        return {
            "total_lookups": len(self.lookup_times),
            "avg_latency_ms": sum(self.lookup_times) / len(self.lookup_times),
            "p50_latency_ms": sorted_times[len(sorted_times) // 2],
            "p95_latency_ms": sorted_times[int(len(sorted_times) * 0.95)],
            "p99_latency_ms": sorted_times[int(len(sorted_times) * 0.99)],
            "max_latency_ms": max(self.lookup_times),
            "cache_size": len(self.flag_cache),
            "bucket_cache_size": len(self.bucket_cache)
        }

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Feature flag manager closed")


# Global instance
_feature_flag_manager: Optional[FeatureFlagManager] = None


async def get_feature_flag_manager(
    redis_url: str = "redis://localhost:6379/0"
) -> FeatureFlagManager:
    """Get or create global feature flag manager."""
    global _feature_flag_manager

    if _feature_flag_manager is None:
        _feature_flag_manager = FeatureFlagManager(redis_url=redis_url)
        await _feature_flag_manager.initialize()

    return _feature_flag_manager


# ========================================================================
# Phase 3 Feature Flags - Pre-configured
# ========================================================================

PHASE_3_FEATURE_FLAGS = {
    "realtime_intelligence": FeatureFlag(
        feature_id="realtime_intelligence",
        name="Real-Time Lead Intelligence Dashboard",
        description="WebSocket-based real-time ML intelligence streaming",
        rollout_stage=RolloutStage.DISABLED,
        roi_target=75000.0,  # $75K-120K/year
        error_rate_threshold=3.0,
        latency_threshold_ms=100.0
    ),
    "property_intelligence": FeatureFlag(
        feature_id="property_intelligence",
        name="Multimodal Property Intelligence",
        description="Claude Vision + neighborhood intelligence integration",
        rollout_stage=RolloutStage.DISABLED,
        roi_target=45000.0,  # $45K-60K/year
        error_rate_threshold=5.0,
        latency_threshold_ms=1500.0
    ),
    "churn_prevention": FeatureFlag(
        feature_id="churn_prevention",
        name="Proactive Churn Prevention",
        description="3-stage intervention framework with multi-channel notifications",
        rollout_stage=RolloutStage.DISABLED,
        roi_target=55000.0,  # $55K-80K/year
        error_rate_threshold=2.0,
        latency_threshold_ms=30000.0  # 30s intervention latency
    ),
    "ai_coaching": FeatureFlag(
        feature_id="ai_coaching",
        name="AI-Powered Coaching Foundation",
        description="Claude conversation analysis with real-time coaching",
        rollout_stage=RolloutStage.DISABLED,
        roi_target=60000.0,  # $60K-90K/year
        error_rate_threshold=5.0,
        latency_threshold_ms=2000.0
    )
}


async def initialize_phase3_flags() -> bool:
    """Initialize Phase 3 feature flags."""
    try:
        manager = await get_feature_flag_manager()

        for flag in PHASE_3_FEATURE_FLAGS.values():
            await manager.create_flag(flag)

        logger.info("Phase 3 feature flags initialized")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Phase 3 flags: {e}")
        return False


__all__ = [
    "FeatureFlagManager",
    "FeatureFlag",
    "RolloutStage",
    "FeatureStatus",
    "RollbackReason",
    "get_feature_flag_manager",
    "initialize_phase3_flags",
    "PHASE_3_FEATURE_FLAGS"
]
