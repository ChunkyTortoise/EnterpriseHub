"""
Redis Analytics Backend Connector for Customer Intelligence Platform.

Connects Streamlit UI components to the Redis-backed analytics backend,
providing real-time data streaming, caching, and data transformation
for customer intelligence dashboards.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class DataStreamType(Enum):
    """Types of real-time data streams."""
    CUSTOMER_METRICS = "customer_metrics"
    CONVERSATION_ANALYTICS = "conversation_analytics"
    SEGMENTATION_DATA = "segmentation_data"
    JOURNEY_MAPPING = "journey_mapping"
    PREDICTIVE_SCORES = "predictive_scores"
    ENGAGEMENT_METRICS = "engagement_metrics"


@dataclass
class RealTimeMetric:
    """Real-time metric data structure."""
    metric_id: str
    customer_id: str
    tenant_id: str
    metric_type: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any]
    department_id: Optional[str] = None


@dataclass
class CustomerSegment:
    """Customer segment data structure."""
    customer_id: str
    tenant_id: str
    segment_type: str
    segment_score: float
    features: Dict[str, float]
    predicted_movement: Optional[str]
    confidence: float
    updated_at: datetime


@dataclass
class JourneyStageData:
    """Customer journey stage data."""
    customer_id: str
    tenant_id: str
    current_stage: str
    predicted_next_stage: str
    stage_probability: float
    dwell_time: timedelta
    conversion_probability: float
    bottleneck_factors: List[str]
    updated_at: datetime


class RedisAnalyticsConnector:
    """
    Redis backend connector for streaming analytics data.
    
    Provides real-time data access, caching, and data transformation
    for Streamlit dashboard components.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        tenant_id: str = "default",
        cache_ttl: int = 60,  # 1 minute default cache
        max_connections: int = 20
    ):
        """
        Initialize Redis Analytics Connector.
        
        Args:
            redis_url: Redis connection URL
            tenant_id: Tenant ID for multi-tenant data isolation
            cache_ttl: Default cache TTL in seconds
            max_connections: Maximum Redis connections in pool
        """
        self.tenant_id = tenant_id
        self.cache_ttl = cache_ttl
        self.cache_service = CacheService()
        
        # Redis connection setup
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_pool = redis.ConnectionPool.from_url(
                    redis_url,
                    max_connections=max_connections,
                    decode_responses=True,
                    socket_timeout=3,
                    socket_connect_timeout=3
                )
                self.redis_client = redis.Redis(connection_pool=self.redis_pool)
                self.redis_enabled = True
                logger.info(f"Redis Analytics Connector initialized for tenant {tenant_id}")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.redis_enabled = False
                self._setup_mock_data()
        else:
            logger.warning("Redis not available, using mock data")
            self.redis_enabled = False
            self._setup_mock_data()

    def _setup_mock_data(self):
        """Setup mock data for development/testing when Redis is unavailable."""
        self.mock_data = {
            "customer_metrics": self._generate_mock_customer_metrics(),
            "conversation_analytics": self._generate_mock_conversation_analytics(),
            "segmentation_data": self._generate_mock_segmentation_data(),
            "journey_mapping": self._generate_mock_journey_data(),
            "predictive_scores": self._generate_mock_predictive_scores()
        }
        logger.info("Mock data initialized for Redis Analytics Connector")

    def _generate_mock_customer_metrics(self) -> List[RealTimeMetric]:
        """Generate mock customer metrics for testing."""
        mock_metrics = []
        current_time = datetime.utcnow()
        
        for i in range(50):
            customer_id = f"customer_{i:03d}"
            mock_metrics.extend([
                RealTimeMetric(
                    metric_id=f"engagement_{customer_id}",
                    customer_id=customer_id,
                    tenant_id=self.tenant_id,
                    metric_type="engagement_score",
                    value=np.random.uniform(0.1, 1.0),
                    timestamp=current_time - timedelta(minutes=np.random.randint(0, 60)),
                    metadata={"channel": np.random.choice(["web", "mobile", "email"]), "source": "mock"}
                ),
                RealTimeMetric(
                    metric_id=f"conversion_{customer_id}",
                    customer_id=customer_id,
                    tenant_id=self.tenant_id,
                    metric_type="conversion_probability",
                    value=np.random.uniform(0.05, 0.95),
                    timestamp=current_time - timedelta(minutes=np.random.randint(0, 60)),
                    metadata={"model_version": "v2.1", "source": "mock"}
                ),
                RealTimeMetric(
                    metric_id=f"churn_{customer_id}",
                    customer_id=customer_id,
                    tenant_id=self.tenant_id,
                    metric_type="churn_risk",
                    value=np.random.uniform(0.0, 0.8),
                    timestamp=current_time - timedelta(minutes=np.random.randint(0, 60)),
                    metadata={"risk_factors": ["low_engagement", "price_sensitivity"], "source": "mock"}
                )
            ])
        
        return mock_metrics

    def _generate_mock_conversation_analytics(self) -> Dict[str, Any]:
        """Generate mock conversation analytics data."""
        return {
            "total_conversations": np.random.randint(1000, 5000),
            "active_conversations": np.random.randint(50, 200),
            "avg_response_time": np.random.uniform(0.5, 3.0),
            "satisfaction_score": np.random.uniform(3.5, 4.8),
            "conversion_rate": np.random.uniform(0.05, 0.25),
            "hourly_stats": [
                {"hour": i, "conversations": np.random.randint(10, 100), "conversions": np.random.randint(1, 10)}
                for i in range(24)
            ]
        }

    def _generate_mock_segmentation_data(self) -> List[CustomerSegment]:
        """Generate mock customer segmentation data."""
        segment_types = ["high_value", "growth_potential", "at_risk", "champion", "loyal"]
        segments = []
        
        for i in range(100):
            customer_id = f"customer_{i:03d}"
            segment_type = np.random.choice(segment_types)
            
            segments.append(CustomerSegment(
                customer_id=customer_id,
                tenant_id=self.tenant_id,
                segment_type=segment_type,
                segment_score=np.random.uniform(0.0, 1.0),
                features={
                    "recency": np.random.uniform(0.0, 1.0),
                    "frequency": np.random.uniform(0.0, 1.0),
                    "monetary": np.random.uniform(0.0, 1.0),
                    "engagement": np.random.uniform(0.0, 1.0)
                },
                predicted_movement=np.random.choice(["upgrade", "maintain", "downgrade", None]),
                confidence=np.random.uniform(0.6, 0.95),
                updated_at=datetime.utcnow() - timedelta(minutes=np.random.randint(0, 60))
            ))
        
        return segments

    def _generate_mock_journey_data(self) -> List[JourneyStageData]:
        """Generate mock customer journey data."""
        journey_stages = ["awareness", "consideration", "evaluation", "purchase", "onboarding", "advocacy"]
        journey_data = []
        
        for i in range(75):
            customer_id = f"customer_{i:03d}"
            current_stage = np.random.choice(journey_stages)
            
            # Next stage logic
            stage_idx = journey_stages.index(current_stage)
            if stage_idx < len(journey_stages) - 1:
                predicted_next_stage = journey_stages[stage_idx + 1]
            else:
                predicted_next_stage = current_stage
            
            journey_data.append(JourneyStageData(
                customer_id=customer_id,
                tenant_id=self.tenant_id,
                current_stage=current_stage,
                predicted_next_stage=predicted_next_stage,
                stage_probability=np.random.uniform(0.3, 0.9),
                dwell_time=timedelta(days=np.random.randint(1, 30)),
                conversion_probability=np.random.uniform(0.1, 0.8),
                bottleneck_factors=np.random.choice(
                    ["pricing", "features", "support", "competition", "timing"],
                    size=np.random.randint(0, 3)
                ).tolist(),
                updated_at=datetime.utcnow() - timedelta(minutes=np.random.randint(0, 120))
            ))
        
        return journey_data

    def _generate_mock_predictive_scores(self) -> Dict[str, Any]:
        """Generate mock predictive scores."""
        return {
            "clv_predictions": {
                f"customer_{i:03d}": {
                    "predicted_clv": np.random.uniform(100, 5000),
                    "confidence": np.random.uniform(0.7, 0.95),
                    "time_horizon": "12_months"
                }
                for i in range(50)
            },
            "next_best_actions": {
                f"customer_{i:03d}": {
                    "action": np.random.choice(["upsell", "retention", "re_engagement", "cross_sell"]),
                    "confidence": np.random.uniform(0.6, 0.9),
                    "expected_impact": np.random.uniform(0.1, 0.8)
                }
                for i in range(50)
            }
        }

    # Redis Key Generators
    def _get_metrics_key(self, metric_type: Optional[str] = None) -> str:
        """Generate Redis key for metrics data."""
        base_key = f"analytics:metrics:{self.tenant_id}"
        return f"{base_key}:{metric_type}" if metric_type else base_key

    def _get_conversation_key(self) -> str:
        """Generate Redis key for conversation analytics."""
        return f"conversation_analytics:{self.tenant_id}"

    def _get_segmentation_key(self) -> str:
        """Generate Redis key for segmentation data."""
        return f"customer_segments:{self.tenant_id}"

    def _get_journey_key(self) -> str:
        """Generate Redis key for journey mapping data."""
        return f"customer_journeys:{self.tenant_id}"

    def _get_predictions_key(self) -> str:
        """Generate Redis key for predictive scores."""
        return f"predictive_scores:{self.tenant_id}"

    # Public API Methods
    async def get_real_time_metrics(
        self,
        metric_types: Optional[List[str]] = None,
        customer_ids: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[RealTimeMetric]:
        """
        Fetch real-time metrics from Redis backend.
        
        Args:
            metric_types: Filter by specific metric types
            customer_ids: Filter by specific customer IDs
            limit: Maximum number of metrics to return
        
        Returns:
            List of real-time metrics
        """
        cache_key = f"metrics:{':'.join(metric_types or [])}:{':'.join(customer_ids or [])}:{limit}"
        
        # Check cache first
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return [RealTimeMetric(**metric) for metric in cached_data]

        if self.redis_enabled:
            try:
                # Fetch from Redis
                metrics_data = await self._fetch_metrics_from_redis(metric_types, customer_ids, limit)
            except Exception as e:
                logger.error(f"Redis fetch failed, using mock data: {e}")
                metrics_data = self.mock_data["customer_metrics"][:limit]
        else:
            # Use mock data
            metrics_data = self.mock_data["customer_metrics"][:limit]

        # Apply filters
        if metric_types:
            metrics_data = [m for m in metrics_data if m.metric_type in metric_types]
        if customer_ids:
            metrics_data = [m for m in metrics_data if m.customer_id in customer_ids]

        # Cache the results
        await self.cache_service.set(
            cache_key,
            [asdict(metric) for metric in metrics_data],
            ttl=self.cache_ttl
        )

        return metrics_data[:limit]

    async def get_conversation_analytics(self) -> Dict[str, Any]:
        """Fetch conversation analytics data."""
        cache_key = "conversation_analytics"
        
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return cached_data

        if self.redis_enabled:
            try:
                analytics_data = await self._fetch_conversation_analytics_from_redis()
            except Exception as e:
                logger.error(f"Redis fetch failed, using mock data: {e}")
                analytics_data = self.mock_data["conversation_analytics"]
        else:
            analytics_data = self.mock_data["conversation_analytics"]

        await self.cache_service.set(cache_key, analytics_data, ttl=self.cache_ttl)
        return analytics_data

    async def get_customer_segments(
        self,
        segment_types: Optional[List[str]] = None,
        min_score: Optional[float] = None
    ) -> List[CustomerSegment]:
        """Fetch customer segmentation data."""
        cache_key = f"segments:{':'.join(segment_types or [])}:{min_score or 0}"
        
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return [CustomerSegment(**segment) for segment in cached_data]

        if self.redis_enabled:
            try:
                segments_data = await self._fetch_segments_from_redis()
            except Exception as e:
                logger.error(f"Redis fetch failed, using mock data: {e}")
                segments_data = self.mock_data["segmentation_data"]
        else:
            segments_data = self.mock_data["segmentation_data"]

        # Apply filters
        if segment_types:
            segments_data = [s for s in segments_data if s.segment_type in segment_types]
        if min_score:
            segments_data = [s for s in segments_data if s.segment_score >= min_score]

        await self.cache_service.set(
            cache_key,
            [asdict(segment) for segment in segments_data],
            ttl=self.cache_ttl
        )

        return segments_data

    async def get_journey_mapping_data(
        self,
        stages: Optional[List[str]] = None,
        min_probability: Optional[float] = None
    ) -> List[JourneyStageData]:
        """Fetch customer journey mapping data."""
        cache_key = f"journeys:{':'.join(stages or [])}:{min_probability or 0}"
        
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return [JourneyStageData(**journey) for journey in cached_data]

        if self.redis_enabled:
            try:
                journey_data = await self._fetch_journey_data_from_redis()
            except Exception as e:
                logger.error(f"Redis fetch failed, using mock data: {e}")
                journey_data = self.mock_data["journey_mapping"]
        else:
            journey_data = self.mock_data["journey_mapping"]

        # Apply filters
        if stages:
            journey_data = [j for j in journey_data if j.current_stage in stages]
        if min_probability:
            journey_data = [j for j in journey_data if j.conversion_probability >= min_probability]

        await self.cache_service.set(
            cache_key,
            [asdict(journey) for journey in journey_data],
            ttl=self.cache_ttl
        )

        return journey_data

    async def get_predictive_scores(self, customer_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Fetch predictive scores and recommendations."""
        cache_key = f"predictions:{':'.join(customer_ids or [])}"
        
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return cached_data

        if self.redis_enabled:
            try:
                predictions_data = await self._fetch_predictions_from_redis()
            except Exception as e:
                logger.error(f"Redis fetch failed, using mock data: {e}")
                predictions_data = self.mock_data["predictive_scores"]
        else:
            predictions_data = self.mock_data["predictive_scores"]

        # Filter by customer IDs if specified
        if customer_ids:
            filtered_predictions = {}
            for key in ["clv_predictions", "next_best_actions"]:
                if key in predictions_data:
                    filtered_predictions[key] = {
                        cid: data for cid, data in predictions_data[key].items()
                        if cid in customer_ids
                    }
            predictions_data = filtered_predictions

        await self.cache_service.set(cache_key, predictions_data, ttl=self.cache_ttl)
        return predictions_data

    # Redis-specific fetch methods
    async def _fetch_metrics_from_redis(
        self,
        metric_types: Optional[List[str]] = None,
        customer_ids: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[RealTimeMetric]:
        """Fetch metrics data from Redis."""
        metrics = []
        
        if metric_types:
            for metric_type in metric_types:
                key = self._get_metrics_key(metric_type)
                data = await self.redis_client.lrange(key, 0, limit - 1)
                for item in data:
                    metric_data = json.loads(item)
                    metrics.append(RealTimeMetric(**metric_data))
        else:
            # Fetch all metric types
            key = self._get_metrics_key()
            data = await self.redis_client.lrange(key, 0, limit - 1)
            for item in data:
                metric_data = json.loads(item)
                metrics.append(RealTimeMetric(**metric_data))
        
        return metrics[:limit]

    async def _fetch_conversation_analytics_from_redis(self) -> Dict[str, Any]:
        """Fetch conversation analytics from Redis."""
        key = self._get_conversation_key()
        data = await self.redis_client.get(key)
        return json.loads(data) if data else {}

    async def _fetch_segments_from_redis(self) -> List[CustomerSegment]:
        """Fetch customer segments from Redis."""
        key = self._get_segmentation_key()
        data = await self.redis_client.lrange(key, 0, -1)
        segments = []
        for item in data:
            segment_data = json.loads(item)
            segments.append(CustomerSegment(**segment_data))
        return segments

    async def _fetch_journey_data_from_redis(self) -> List[JourneyStageData]:
        """Fetch journey mapping data from Redis."""
        key = self._get_journey_key()
        data = await self.redis_client.lrange(key, 0, -1)
        journeys = []
        for item in data:
            journey_data = json.loads(item)
            journeys.append(JourneyStageData(**journey_data))
        return journeys

    async def _fetch_predictions_from_redis(self) -> Dict[str, Any]:
        """Fetch predictive scores from Redis."""
        key = self._get_predictions_key()
        data = await self.redis_client.get(key)
        return json.loads(data) if data else {}

    # Data transformation utilities
    def metrics_to_dataframe(self, metrics: List[RealTimeMetric]) -> pd.DataFrame:
        """Convert metrics list to pandas DataFrame for analysis."""
        if not metrics:
            return pd.DataFrame()
        
        data = []
        for metric in metrics:
            row = asdict(metric)
            row['timestamp'] = metric.timestamp.isoformat()
            data.append(row)
        
        return pd.DataFrame(data)

    def segments_to_dataframe(self, segments: List[CustomerSegment]) -> pd.DataFrame:
        """Convert segments list to pandas DataFrame for analysis."""
        if not segments:
            return pd.DataFrame()
        
        data = []
        for segment in segments:
            row = asdict(segment)
            row['updated_at'] = segment.updated_at.isoformat()
            # Flatten features dictionary
            for feature, value in segment.features.items():
                row[f"feature_{feature}"] = value
            del row['features']
            data.append(row)
        
        return pd.DataFrame(data)

    def journeys_to_dataframe(self, journeys: List[JourneyStageData]) -> pd.DataFrame:
        """Convert journey data list to pandas DataFrame for analysis."""
        if not journeys:
            return pd.DataFrame()
        
        data = []
        for journey in journeys:
            row = asdict(journey)
            row['updated_at'] = journey.updated_at.isoformat()
            row['dwell_time_days'] = journey.dwell_time.days
            row['bottleneck_factors'] = ', '.join(journey.bottleneck_factors)
            data.append(row)
        
        return pd.DataFrame(data)

    # Health check and monitoring
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the Redis connection and data freshness."""
        health_status = {
            "redis_enabled": self.redis_enabled,
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": self.tenant_id
        }
        
        if self.redis_enabled:
            try:
                # Test Redis connection
                await self.redis_client.ping()
                health_status["redis_connection"] = "healthy"
                
                # Check data freshness
                conversation_data = await self.redis_client.get(self._get_conversation_key())
                if conversation_data:
                    health_status["data_available"] = True
                    health_status["last_data_update"] = "< 1 minute"  # Placeholder
                else:
                    health_status["data_available"] = False
                    
            except Exception as e:
                health_status["redis_connection"] = f"error: {e}"
                health_status["data_available"] = False
        else:
            health_status["redis_connection"] = "disabled"
            health_status["data_available"] = True  # Mock data is always available
            health_status["using_mock_data"] = True

        return health_status

    async def close(self):
        """Clean up resources and close connections."""
        if self.redis_enabled and hasattr(self, 'redis_pool'):
            await self.redis_pool.disconnect()
            logger.info("Redis Analytics Connector closed")


# Factory function for creating connector instances
async def create_redis_analytics_connector(
    redis_url: Optional[str] = None,
    tenant_id: str = "default",
    **kwargs
) -> RedisAnalyticsConnector:
    """
    Factory function to create and initialize Redis Analytics Connector.
    
    Args:
        redis_url: Redis connection URL
        tenant_id: Tenant ID for data isolation
        **kwargs: Additional configuration options
    
    Returns:
        Configured RedisAnalyticsConnector instance
    """
    connector = RedisAnalyticsConnector(redis_url=redis_url, tenant_id=tenant_id, **kwargs)
    
    # Perform health check
    health = await connector.health_check()
    logger.info(f"Redis Analytics Connector health check: {health}")
    
    return connector