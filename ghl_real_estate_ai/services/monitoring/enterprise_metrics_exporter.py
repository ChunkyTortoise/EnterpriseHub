"""
Enterprise Metrics Exporter for EnterpriseHub AI Coaching Platform
Exposes comprehensive metrics for Prometheus monitoring and alerting
Supports 99.95% uptime SLA and enterprise performance targets
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, Info, start_http_server
from prometheus_client.core import REGISTRY
import psycopg2
import redis.asyncio as redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..base import BaseService
from ..database_shard_router import DatabaseShardingService
from ..advanced_coaching_analytics import AdvancedCoachingAnalytics
from ..performance_prediction_engine import PerformancePredictionEngine
from ...config.settings import get_settings

logger = logging.getLogger(__name__)

@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""
    collection_interval: int = 15  # seconds
    http_server_port: int = 8000
    redis_metrics_enabled: bool = True
    database_metrics_enabled: bool = True
    coaching_metrics_enabled: bool = True
    business_metrics_enabled: bool = True

class EnterpriseMetricsExporter(BaseService):
    """
    Enterprise-grade metrics exporter for comprehensive monitoring.

    Exposes metrics for:
    - SLA monitoring (99.95% uptime)
    - AI coaching performance
    - Business KPIs and ROI
    - Infrastructure health
    - Security and compliance
    """

    def __init__(self, config: Optional[MetricsConfig] = None):
        super().__init__()
        self.config = config or MetricsConfig()
        self.settings = get_settings()

        # Create custom registry for enterprise metrics
        self.registry = CollectorRegistry()

        # Initialize service dependencies
        self.db_sharding = DatabaseShardingService()
        self.coaching_analytics = AdvancedCoachingAnalytics()
        self.performance_engine = PerformancePredictionEngine()

        # Initialize metric collectors
        self._init_sla_metrics()
        self._init_coaching_metrics()
        self._init_business_metrics()
        self._init_infrastructure_metrics()
        self._init_security_metrics()

        # Collection state
        self.collection_task: Optional[asyncio.Task] = None
        self.is_running = False

    def _init_sla_metrics(self) -> None:
        """Initialize SLA monitoring metrics."""
        # Service availability (99.95% target)
        self.service_availability = Gauge(
            'service_availability_ratio',
            'Current service availability ratio',
            registry=self.registry
        )

        # API response time (95th percentile <200ms)
        self.api_response_time = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'status'],
            buckets=(0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0, 2.0, 5.0),
            registry=self.registry
        )

        # ML inference time (<500ms target)
        self.ml_inference_time = Histogram(
            'ml_inference_duration_seconds',
            'ML model inference duration in seconds',
            ['model_name', 'prediction_type'],
            buckets=(0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 5.0),
            registry=self.registry
        )

        # Concurrent user capacity (1000+ target)
        self.active_connections = Gauge(
            'active_websocket_connections',
            'Number of active WebSocket connections',
            registry=self.registry
        )

    def _init_coaching_metrics(self) -> None:
        """Initialize AI coaching performance metrics."""
        # Training time reduction (50% target)
        self.training_duration = Gauge(
            'coaching_training_duration_minutes',
            'Average coaching session duration in minutes',
            registry=self.registry
        )

        self.baseline_training_duration = Gauge(
            'coaching_baseline_training_duration_minutes',
            'Baseline training duration before AI coaching',
            registry=self.registry
        )

        # Agent productivity (25% increase target)
        self.agent_deals_per_day = Gauge(
            'agent_deals_closed_per_day',
            'Average deals closed per agent per day',
            ['agent_id'],
            registry=self.registry
        )

        self.agent_baseline_deals = Gauge(
            'agent_baseline_deals_per_day',
            'Baseline deals per day before AI coaching',
            registry=self.registry
        )

        # Coaching effectiveness
        self.coaching_sessions_total = Counter(
            'coaching_sessions_total',
            'Total coaching sessions initiated',
            ['session_type'],
            registry=self.registry
        )

        self.coaching_sessions_improved = Counter(
            'coaching_sessions_improved_total',
            'Coaching sessions showing improvement',
            ['improvement_type'],
            registry=self.registry
        )

        # Model performance
        self.coaching_model_accuracy = Gauge(
            'coaching_model_accuracy_score',
            'Current coaching model accuracy score',
            ['model_version'],
            registry=self.registry
        )

        self.coaching_model_drift = Gauge(
            'coaching_model_drift_score',
            'Model drift detection score',
            ['model_name'],
            registry=self.registry
        )

    def _init_business_metrics(self) -> None:
        """Initialize business KPI metrics."""
        # Revenue impact ($60K-90K annual target)
        self.revenue_impact_monthly = Gauge(
            'coaching_revenue_impact_monthly',
            'Monthly revenue impact from AI coaching in USD',
            registry=self.registry
        )

        # Lead conversion improvement
        self.lead_conversion_rate = Gauge(
            'lead_conversion_rate',
            'Current lead conversion rate',
            ['time_period'],
            registry=self.registry
        )

        self.baseline_conversion_rate = Gauge(
            'baseline_lead_conversion_rate',
            'Baseline lead conversion rate',
            registry=self.registry
        )

        # Customer satisfaction
        self.coaching_satisfaction = Gauge(
            'coaching_satisfaction_score',
            'Customer satisfaction score for AI coaching (1-5)',
            registry=self.registry
        )

        # Cost efficiency
        self.ai_cost_per_session = Gauge(
            'coaching_ai_cost_per_session',
            'AI API cost per coaching session in USD',
            registry=self.registry
        )

        self.revenue_per_session = Gauge(
            'coaching_revenue_per_session',
            'Revenue generated per coaching session in USD',
            registry=self.registry
        )

    def _init_infrastructure_metrics(self) -> None:
        """Initialize infrastructure health metrics."""
        # Deployment metrics
        self.deployment_active_env = Gauge(
            'deployment_active_environment',
            'Currently active deployment environment (0=blue, 1=green)',
            registry=self.registry
        )

        self.deployment_switch_duration = Gauge(
            'deployment_switch_duration_seconds',
            'Duration of last deployment switch in seconds',
            registry=self.registry
        )

        self.deployment_health_check = Gauge(
            'deployment_health_check_success',
            'Deployment health check status (0=failed, 1=success)',
            registry=self.registry
        )

        self.deployment_rollback_ready = Gauge(
            'deployment_rollback_ready',
            'Rollback readiness status (0=not ready, 1=ready)',
            registry=self.registry
        )

        # AI context utilization
        self.ai_context_tokens_used = Gauge(
            'ai_context_tokens_used',
            'Number of AI context tokens currently used',
            registry=self.registry
        )

        self.ai_context_tokens_available = Gauge(
            'ai_context_tokens_available',
            'Total AI context tokens available',
            registry=self.registry
        )

    def _init_security_metrics(self) -> None:
        """Initialize security and compliance metrics."""
        # PII detection and sanitization
        self.pii_detection_failures = Counter(
            'pii_detection_failures_total',
            'Total PII detection failures',
            ['failure_type'],
            registry=self.registry
        )

        # Authentication metrics
        self.authentication_failures = Counter(
            'authentication_failures_total',
            'Total authentication failures',
            ['failure_reason'],
            registry=self.registry
        )

        # Rate limiting
        self.rate_limited_requests = Counter(
            'http_requests_total',
            'Total HTTP requests with rate limiting',
            ['method', 'endpoint', 'code'],
            registry=self.registry
        )

    async def start_metrics_collection(self) -> None:
        """Start the metrics collection process."""
        if self.is_running:
            logger.warning("Metrics collection is already running")
            return

        self.is_running = True

        # Start HTTP server for Prometheus scraping
        start_http_server(self.config.http_server_port, registry=self.registry)
        logger.info(f"Metrics HTTP server started on port {self.config.http_server_port}")

        # Start collection loop
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collection started")

    async def stop_metrics_collection(self) -> None:
        """Stop the metrics collection process."""
        self.is_running = False

        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

        logger.info("Metrics collection stopped")

    async def _collection_loop(self) -> None:
        """Main metrics collection loop."""
        while self.is_running:
            try:
                start_time = time.time()

                # Collect metrics in parallel
                await asyncio.gather(
                    self._collect_sla_metrics(),
                    self._collect_coaching_metrics(),
                    self._collect_business_metrics(),
                    self._collect_infrastructure_metrics(),
                    self._collect_security_metrics(),
                    return_exceptions=True
                )

                collection_duration = time.time() - start_time
                logger.debug(f"Metrics collection completed in {collection_duration:.2f}s")

                # Wait for next collection interval
                await asyncio.sleep(self.config.collection_interval)

            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _collect_sla_metrics(self) -> None:
        """Collect SLA-related metrics."""
        try:
            # Service availability (from error rate)
            # This would typically come from application metrics
            # For now, simulate based on system health
            availability = await self._calculate_service_availability()
            self.service_availability.set(availability)

            # Active connections (from WebSocket manager)
            active_connections = await self._get_active_connections()
            self.active_connections.set(active_connections)

        except Exception as e:
            logger.error(f"Error collecting SLA metrics: {e}")

    async def _collect_coaching_metrics(self) -> None:
        """Collect AI coaching performance metrics."""
        try:
            # Get coaching analytics data
            analytics_data = await self.coaching_analytics.get_comprehensive_analytics(
                tenant_id="system",
                time_range_hours=24
            )

            # Training time metrics
            if analytics_data.average_session_duration:
                self.training_duration.set(analytics_data.average_session_duration / 60)  # Convert to minutes

            # Coaching effectiveness
            if analytics_data.success_rate:
                # Update counters based on session data
                pass  # Implementation would increment counters

            # Model performance from prediction engine
            model_metrics = await self.performance_engine.get_model_performance_metrics()
            if model_metrics:
                self.coaching_model_accuracy.labels(model_version="v1").set(model_metrics.get('accuracy', 0))
                self.coaching_model_drift.labels(model_name="coaching_predictor").set(model_metrics.get('drift_score', 0))

        except Exception as e:
            logger.error(f"Error collecting coaching metrics: {e}")

    async def _collect_business_metrics(self) -> None:
        """Collect business KPI metrics."""
        try:
            # Revenue impact calculation
            revenue_data = await self.coaching_analytics.calculate_coaching_roi(
                agent_id="system",
                tenant_id="system",
                coaching_program_id="default"
            )

            if revenue_data:
                monthly_impact = revenue_data.annual_value / 12
                self.revenue_impact_monthly.set(monthly_impact)

            # Lead conversion rates
            conversion_metrics = await self._get_conversion_metrics()
            if conversion_metrics:
                self.lead_conversion_rate.labels(time_period="current_week").set(
                    conversion_metrics.get('current_rate', 0)
                )
                self.baseline_conversion_rate.set(
                    conversion_metrics.get('baseline_rate', 0)
                )

            # Customer satisfaction (from survey data)
            satisfaction_score = await self._get_satisfaction_score()
            if satisfaction_score:
                self.coaching_satisfaction.set(satisfaction_score)

        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")

    async def _collect_infrastructure_metrics(self) -> None:
        """Collect infrastructure health metrics."""
        try:
            # Deployment status (from deployment service)
            deployment_status = await self._get_deployment_status()
            if deployment_status:
                self.deployment_active_env.set(deployment_status.get('active_env', 0))
                self.deployment_health_check.set(deployment_status.get('health_check', 1))
                self.deployment_rollback_ready.set(deployment_status.get('rollback_ready', 1))

            # AI context utilization
            context_metrics = await self._get_ai_context_metrics()
            if context_metrics:
                self.ai_context_tokens_used.set(context_metrics.get('used', 0))
                self.ai_context_tokens_available.set(context_metrics.get('available', 0))

        except Exception as e:
            logger.error(f"Error collecting infrastructure metrics: {e}")

    async def _collect_security_metrics(self) -> None:
        """Collect security and compliance metrics."""
        try:
            # PII detection metrics (from secure logging service)
            # Authentication metrics (from auth service)
            # Rate limiting metrics (from API gateway)

            # These would be collected from respective services
            # For now, placeholder implementation
            pass

        except Exception as e:
            logger.error(f"Error collecting security metrics: {e}")

    async def _calculate_service_availability(self) -> float:
        """Calculate current service availability ratio."""
        try:
            # This would typically query application logs or health checks
            # For demonstration, return high availability
            return 0.9998  # 99.98% availability
        except Exception:
            return 0.99  # Conservative estimate during errors

    async def _get_active_connections(self) -> int:
        """Get current number of active WebSocket connections."""
        try:
            # Query Redis or connection manager for active connections
            # Placeholder implementation
            return 150  # Example active connections
        except Exception:
            return 0

    async def _get_conversion_metrics(self) -> Optional[Dict[str, float]]:
        """Get lead conversion rate metrics."""
        try:
            # Query database for conversion rates
            return {
                'current_rate': 0.15,    # 15% current conversion rate
                'baseline_rate': 0.12    # 12% baseline conversion rate
            }
        except Exception:
            return None

    async def _get_satisfaction_score(self) -> Optional[float]:
        """Get customer satisfaction score."""
        try:
            # Query satisfaction survey data
            return 4.3  # Example satisfaction score out of 5
        except Exception:
            return None

    async def _get_deployment_status(self) -> Optional[Dict[str, int]]:
        """Get deployment infrastructure status."""
        try:
            # Query deployment service for status
            return {
                'active_env': 1,        # Green environment active
                'health_check': 1,      # Health check passed
                'rollback_ready': 1     # Rollback ready
            }
        except Exception:
            return None

    async def _get_ai_context_metrics(self) -> Optional[Dict[str, int]]:
        """Get AI context utilization metrics."""
        try:
            # Query AI service for context utilization
            return {
                'used': 85000,      # Tokens used
                'available': 100000  # Total tokens available
            }
        except Exception:
            return None

    # Public methods for external metric updates
    def record_api_request(self, method: str, endpoint: str, status: str, duration: float) -> None:
        """Record API request metrics."""
        self.api_response_time.labels(method=method, endpoint=endpoint, status=status).observe(duration)

    def record_ml_inference(self, model_name: str, prediction_type: str, duration: float) -> None:
        """Record ML inference metrics."""
        self.ml_inference_time.labels(model_name=model_name, prediction_type=prediction_type).observe(duration)

    def record_coaching_session(self, session_type: str, improved: bool = False) -> None:
        """Record coaching session metrics."""
        self.coaching_sessions_total.labels(session_type=session_type).inc()
        if improved:
            self.coaching_sessions_improved.labels(improvement_type=session_type).inc()

    def record_authentication_failure(self, reason: str) -> None:
        """Record authentication failure."""
        self.authentication_failures.labels(failure_reason=reason).inc()

    def record_pii_detection_failure(self, failure_type: str) -> None:
        """Record PII detection failure."""
        self.pii_detection_failures.labels(failure_type=failure_type).inc()

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary for health checks."""
        return {
            "service_availability": self.service_availability._value.get() if hasattr(self.service_availability, '_value') else 0,
            "active_connections": self.active_connections._value.get() if hasattr(self.active_connections, '_value') else 0,
            "is_collecting": self.is_running,
            "collection_interval": self.config.collection_interval
        }

# Global instance for application use
metrics_exporter = None

def get_metrics_exporter() -> EnterpriseMetricsExporter:
    """Get global metrics exporter instance."""
    global metrics_exporter
    if metrics_exporter is None:
        metrics_exporter = EnterpriseMetricsExporter()
    return metrics_exporter

def start_metrics_server(port: int = 8000) -> None:
    """Start metrics collection server."""
    exporter = get_metrics_exporter()
    asyncio.create_task(exporter.start_metrics_collection())
    logger.info(f"Enterprise metrics server starting on port {port}")