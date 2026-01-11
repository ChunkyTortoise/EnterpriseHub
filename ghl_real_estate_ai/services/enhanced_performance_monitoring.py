"""
Enhanced Performance Monitoring Service - ML Model Tracking & System Health
Real-time monitoring, model drift detection, and performance optimization for EnterpriseHub.

Features:
- ML Model Performance Tracking (accuracy, latency, throughput)
- Model Drift Detection & Alerts
- System Health Monitoring
- Real-time Metrics Dashboard
- Performance Optimization Recommendations
- Automated Alerting System
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import redis
import psutil
import numpy as np
import pandas as pd

# Enterprise imports
try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """ML Model performance metrics."""
    model_id: str
    model_version: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    inference_latency_ms: float
    throughput_rps: float
    memory_usage_mb: float
    cpu_utilization: float
    timestamp: datetime
    predictions_count: int
    error_rate: float


@dataclass
class SystemMetrics:
    """System-wide performance metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    redis_memory: float
    database_connections: int
    api_response_time: float
    active_sessions: int
    timestamp: datetime


@dataclass
class PerformanceAlert:
    """Performance alert structure."""
    alert_id: str
    severity: str  # 'critical', 'warning', 'info'
    component: str  # 'ml_model', 'system', 'api', 'database'
    message: str
    metric_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class MLModelTracker:
    """ML Model performance tracking and drift detection."""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(decode_responses=True)
        self.model_metrics = defaultdict(lambda: deque(maxlen=1000))
        self.baseline_metrics = {}
        self.drift_thresholds = {
            'accuracy': 0.05,  # 5% drop
            'precision': 0.05,
            'recall': 0.05,
            'f1_score': 0.05,
            'latency': 0.50,   # 50% increase
            'error_rate': 0.10  # 10% increase
        }

    async def track_model_performance(
        self,
        model_id: str,
        model_version: str,
        metrics: Dict[str, float],
        predictions_count: int = 1
    ) -> ModelMetrics:
        """Track ML model performance metrics."""
        try:
            # Create model metrics object
            model_metrics = ModelMetrics(
                model_id=model_id,
                model_version=model_version,
                accuracy=metrics.get('accuracy', 0.0),
                precision=metrics.get('precision', 0.0),
                recall=metrics.get('recall', 0.0),
                f1_score=metrics.get('f1_score', 0.0),
                inference_latency_ms=metrics.get('latency_ms', 0.0),
                throughput_rps=metrics.get('throughput_rps', 0.0),
                memory_usage_mb=metrics.get('memory_mb', 0.0),
                cpu_utilization=metrics.get('cpu_usage', 0.0),
                timestamp=datetime.now(),
                predictions_count=predictions_count,
                error_rate=metrics.get('error_rate', 0.0)
            )

            # Store in memory for drift detection
            self.model_metrics[model_id].append(model_metrics)

            # Cache in Redis
            await self._cache_model_metrics(model_metrics)

            # Check for drift
            drift_alerts = await self.detect_model_drift(model_id)

            return model_metrics

        except Exception as e:
            logger.error(f"Error tracking model performance: {e}")
            raise

    async def detect_model_drift(self, model_id: str) -> List[PerformanceAlert]:
        """Detect model performance drift."""
        alerts = []

        try:
            if model_id not in self.model_metrics or len(self.model_metrics[model_id]) < 10:
                return alerts

            recent_metrics = list(self.model_metrics[model_id])[-10:]
            baseline = self.baseline_metrics.get(model_id)

            if not baseline:
                # Set baseline from first metrics
                baseline_data = list(self.model_metrics[model_id])[:10]
                if len(baseline_data) >= 10:
                    self.baseline_metrics[model_id] = self._calculate_baseline(baseline_data)
                return alerts

            current_avg = self._calculate_average_metrics(recent_metrics)

            # Check drift thresholds
            for metric_name, threshold in self.drift_thresholds.items():
                baseline_value = getattr(baseline, metric_name, 0)
                current_value = getattr(current_avg, metric_name, 0)

                if metric_name == 'latency':
                    # For latency, alert if increase is above threshold
                    if current_value > baseline_value * (1 + threshold):
                        alerts.append(PerformanceAlert(
                            alert_id=f"drift_{model_id}_{metric_name}_{int(time.time())}",
                            severity='warning',
                            component='ml_model',
                            message=f"Model {model_id} latency drift detected: {current_value:.2f}ms vs baseline {baseline_value:.2f}ms",
                            metric_value=current_value,
                            threshold=baseline_value * (1 + threshold),
                            timestamp=datetime.now()
                        ))
                elif metric_name == 'error_rate':
                    # For error rate, alert if increase is above threshold
                    if current_value > baseline_value + threshold:
                        alerts.append(PerformanceAlert(
                            alert_id=f"drift_{model_id}_{metric_name}_{int(time.time())}",
                            severity='critical',
                            component='ml_model',
                            message=f"Model {model_id} error rate spike: {current_value:.2%} vs baseline {baseline_value:.2%}",
                            metric_value=current_value,
                            threshold=baseline_value + threshold,
                            timestamp=datetime.now()
                        ))
                else:
                    # For accuracy metrics, alert if decrease is above threshold
                    if current_value < baseline_value * (1 - threshold):
                        alerts.append(PerformanceAlert(
                            alert_id=f"drift_{model_id}_{metric_name}_{int(time.time())}",
                            severity='critical' if threshold >= 0.1 else 'warning',
                            component='ml_model',
                            message=f"Model {model_id} {metric_name} degradation: {current_value:.2%} vs baseline {baseline_value:.2%}",
                            metric_value=current_value,
                            threshold=baseline_value * (1 - threshold),
                            timestamp=datetime.now()
                        ))

            return alerts

        except Exception as e:
            logger.error(f"Error detecting model drift: {e}")
            return []

    def _calculate_baseline(self, metrics_list: List[ModelMetrics]) -> ModelMetrics:
        """Calculate baseline metrics from historical data."""
        if not metrics_list:
            return None

        # Calculate averages
        accuracy_avg = np.mean([m.accuracy for m in metrics_list])
        precision_avg = np.mean([m.precision for m in metrics_list])
        recall_avg = np.mean([m.recall for m in metrics_list])
        f1_score_avg = np.mean([m.f1_score for m in metrics_list])
        latency_avg = np.mean([m.inference_latency_ms for m in metrics_list])
        error_rate_avg = np.mean([m.error_rate for m in metrics_list])

        return ModelMetrics(
            model_id=metrics_list[0].model_id,
            model_version="baseline",
            accuracy=accuracy_avg,
            precision=precision_avg,
            recall=recall_avg,
            f1_score=f1_score_avg,
            inference_latency_ms=latency_avg,
            throughput_rps=0,
            memory_usage_mb=0,
            cpu_utilization=0,
            timestamp=datetime.now(),
            predictions_count=0,
            error_rate=error_rate_avg
        )

    def _calculate_average_metrics(self, metrics_list: List[ModelMetrics]) -> ModelMetrics:
        """Calculate average metrics from recent data."""
        return self._calculate_baseline(metrics_list)

    async def _cache_model_metrics(self, metrics: ModelMetrics):
        """Cache model metrics in Redis."""
        try:
            key = f"model_metrics:{metrics.model_id}:{int(metrics.timestamp.timestamp())}"
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.redis_client.setex,
                key,
                3600,  # 1 hour TTL
                json.dumps(asdict(metrics), default=str)
            )
        except Exception as e:
            logger.warning(f"Failed to cache model metrics: {e}")


class SystemHealthMonitor:
    """System-wide health and performance monitoring."""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(decode_responses=True)
        self.health_thresholds = {
            'cpu_usage': 80.0,      # 80%
            'memory_usage': 85.0,   # 85%
            'disk_usage': 90.0,     # 90%
            'api_response_time': 500.0,  # 500ms
            'redis_memory': 80.0    # 80% of max
        }

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics."""
        try:
            # CPU and Memory
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }

            # Redis metrics
            redis_info = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.info
            )
            redis_memory = redis_info.get('used_memory', 0) / (1024 * 1024)  # MB

            # API response time (placeholder - would integrate with actual API metrics)
            api_response_time = await self._get_api_response_time()

            # Active sessions (from Redis)
            active_sessions = await self._get_active_sessions_count()

            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io=network_io,
                redis_memory=redis_memory,
                database_connections=0,  # Placeholder
                api_response_time=api_response_time,
                active_sessions=active_sessions,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            raise

    async def check_system_health(self, metrics: SystemMetrics) -> List[PerformanceAlert]:
        """Check system health against thresholds."""
        alerts = []

        try:
            # CPU Usage
            if metrics.cpu_usage > self.health_thresholds['cpu_usage']:
                alerts.append(PerformanceAlert(
                    alert_id=f"cpu_high_{int(time.time())}",
                    severity='critical' if metrics.cpu_usage > 95 else 'warning',
                    component='system',
                    message=f"High CPU usage: {metrics.cpu_usage:.1f}%",
                    metric_value=metrics.cpu_usage,
                    threshold=self.health_thresholds['cpu_usage'],
                    timestamp=datetime.now()
                ))

            # Memory Usage
            if metrics.memory_usage > self.health_thresholds['memory_usage']:
                alerts.append(PerformanceAlert(
                    alert_id=f"memory_high_{int(time.time())}",
                    severity='critical' if metrics.memory_usage > 95 else 'warning',
                    component='system',
                    message=f"High memory usage: {metrics.memory_usage:.1f}%",
                    metric_value=metrics.memory_usage,
                    threshold=self.health_thresholds['memory_usage'],
                    timestamp=datetime.now()
                ))

            # Disk Usage
            if metrics.disk_usage > self.health_thresholds['disk_usage']:
                alerts.append(PerformanceAlert(
                    alert_id=f"disk_high_{int(time.time())}",
                    severity='critical',
                    component='system',
                    message=f"High disk usage: {metrics.disk_usage:.1f}%",
                    metric_value=metrics.disk_usage,
                    threshold=self.health_thresholds['disk_usage'],
                    timestamp=datetime.now()
                ))

            # API Response Time
            if metrics.api_response_time > self.health_thresholds['api_response_time']:
                alerts.append(PerformanceAlert(
                    alert_id=f"api_slow_{int(time.time())}",
                    severity='warning',
                    component='api',
                    message=f"Slow API response time: {metrics.api_response_time:.1f}ms",
                    metric_value=metrics.api_response_time,
                    threshold=self.health_thresholds['api_response_time'],
                    timestamp=datetime.now()
                ))

            return alerts

        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return []

    async def _get_api_response_time(self) -> float:
        """Get average API response time from cache."""
        try:
            cached_time = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.get, "api_response_time_avg"
            )
            return float(cached_time) if cached_time else 0.0
        except:
            return 0.0

    async def _get_active_sessions_count(self) -> int:
        """Get count of active user sessions."""
        try:
            count = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.scard, "active_sessions"
            )
            return count or 0
        except:
            return 0


class PerformanceOptimizer:
    """Automated performance optimization recommendations."""

    def __init__(self):
        self.optimization_rules = {
            'high_cpu': {
                'threshold': 80.0,
                'recommendations': [
                    "Consider scaling horizontally",
                    "Optimize CPU-intensive operations",
                    "Implement caching for repeated computations",
                    "Review ML model inference optimization"
                ]
            },
            'high_memory': {
                'threshold': 85.0,
                'recommendations': [
                    "Implement memory pooling",
                    "Optimize data structures",
                    "Clear unused caches",
                    "Review ML model memory usage"
                ]
            },
            'slow_api': {
                'threshold': 500.0,
                'recommendations': [
                    "Implement request caching",
                    "Optimize database queries",
                    "Use async processing for heavy operations",
                    "Consider CDN for static assets"
                ]
            },
            'model_drift': {
                'threshold': 0.05,
                'recommendations': [
                    "Retrain model with recent data",
                    "Update feature engineering pipeline",
                    "Review data quality checks",
                    "Implement A/B testing for model versions"
                ]
            }
        }

    async def generate_recommendations(
        self,
        system_metrics: SystemMetrics,
        alerts: List[PerformanceAlert]
    ) -> Dict[str, List[str]]:
        """Generate performance optimization recommendations."""
        recommendations = {}

        try:
            # System performance recommendations
            if system_metrics.cpu_usage > self.optimization_rules['high_cpu']['threshold']:
                recommendations['cpu'] = self.optimization_rules['high_cpu']['recommendations']

            if system_metrics.memory_usage > self.optimization_rules['high_memory']['threshold']:
                recommendations['memory'] = self.optimization_rules['high_memory']['recommendations']

            if system_metrics.api_response_time > self.optimization_rules['slow_api']['threshold']:
                recommendations['api'] = self.optimization_rules['slow_api']['recommendations']

            # Alert-based recommendations
            for alert in alerts:
                if alert.component == 'ml_model' and 'drift' in alert.alert_id:
                    recommendations['ml_model'] = self.optimization_rules['model_drift']['recommendations']

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {}


class EnhancedPerformanceMonitoringService:
    """Main performance monitoring service with ML model tracking."""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(decode_responses=True)
        self.ml_tracker = MLModelTracker(self.redis_client)
        self.system_monitor = SystemHealthMonitor(self.redis_client)
        self.optimizer = PerformanceOptimizer()
        self.alerts_history = deque(maxlen=1000)
        self.monitoring_active = False

        # Initialize Prometheus metrics if available
        if PROMETHEUS_AVAILABLE:
            self.registry = CollectorRegistry()
            self.setup_prometheus_metrics()

    def setup_prometheus_metrics(self):
        """Setup Prometheus metrics collection."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.model_accuracy = Gauge(
            'ml_model_accuracy',
            'ML Model accuracy score',
            ['model_id', 'version'],
            registry=self.registry
        )
        self.model_latency = Histogram(
            'ml_model_inference_latency_seconds',
            'ML Model inference latency',
            ['model_id', 'version'],
            registry=self.registry
        )
        self.system_cpu = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        self.system_memory = Gauge(
            'system_memory_usage_percent',
            'System memory usage percentage',
            registry=self.registry
        )

    async def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous performance monitoring."""
        self.monitoring_active = True
        logger.info("Starting enhanced performance monitoring...")

        try:
            while self.monitoring_active:
                await self.collect_and_analyze()
                await asyncio.sleep(interval_seconds)
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            self.monitoring_active = False

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        logger.info("Stopping performance monitoring...")

    async def collect_and_analyze(self):
        """Collect metrics and analyze performance."""
        try:
            # Collect system metrics
            system_metrics = await self.system_monitor.collect_system_metrics()

            # Check system health
            system_alerts = await self.system_monitor.check_system_health(system_metrics)

            # Store alerts
            for alert in system_alerts:
                self.alerts_history.append(alert)

            # Generate optimization recommendations
            recommendations = await self.optimizer.generate_recommendations(
                system_metrics, system_alerts
            )

            # Cache current state
            await self._cache_monitoring_state(system_metrics, system_alerts, recommendations)

            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                self.system_cpu.set(system_metrics.cpu_usage)
                self.system_memory.set(system_metrics.memory_usage)

            logger.info(f"Performance monitoring cycle completed. {len(system_alerts)} alerts generated.")

        except Exception as e:
            logger.error(f"Error in collect_and_analyze: {e}")

    async def track_ml_model_performance(
        self,
        model_id: str,
        model_version: str,
        metrics: Dict[str, float],
        predictions_count: int = 1
    ) -> Tuple[ModelMetrics, List[PerformanceAlert]]:
        """Track ML model performance and detect drift."""
        try:
            # Track model metrics
            model_metrics = await self.ml_tracker.track_model_performance(
                model_id, model_version, metrics, predictions_count
            )

            # Detect drift
            drift_alerts = await self.ml_tracker.detect_model_drift(model_id)

            # Store alerts
            for alert in drift_alerts:
                self.alerts_history.append(alert)

            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                self.model_accuracy.labels(model_id=model_id, version=model_version).set(
                    model_metrics.accuracy
                )
                self.model_latency.labels(model_id=model_id, version=model_version).observe(
                    model_metrics.inference_latency_ms / 1000  # Convert to seconds
                )

            return model_metrics, drift_alerts

        except Exception as e:
            logger.error(f"Error tracking ML model performance: {e}")
            raise

    async def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive performance data for dashboard."""
        try:
            # Get cached system metrics
            system_data = await self._get_cached_system_metrics()

            # Get recent alerts
            recent_alerts = [
                alert for alert in self.alerts_history
                if alert.timestamp > datetime.now() - timedelta(hours=24)
            ]

            # Get ML model summary
            model_summary = await self._get_model_performance_summary()

            # Get recommendations
            recommendations = await self._get_cached_recommendations()

            return {
                'system_metrics': system_data,
                'alerts': {
                    'total': len(recent_alerts),
                    'critical': len([a for a in recent_alerts if a.severity == 'critical']),
                    'warning': len([a for a in recent_alerts if a.severity == 'warning']),
                    'recent': recent_alerts[:10]
                },
                'ml_models': model_summary,
                'recommendations': recommendations,
                'monitoring_status': self.monitoring_active,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}

    async def _cache_monitoring_state(
        self,
        system_metrics: SystemMetrics,
        alerts: List[PerformanceAlert],
        recommendations: Dict[str, List[str]]
    ):
        """Cache current monitoring state."""
        try:
            # Cache system metrics
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.redis_client.setex,
                "monitoring:system_metrics",
                300,  # 5 minutes TTL
                json.dumps(asdict(system_metrics), default=str)
            )

            # Cache recommendations
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.redis_client.setex,
                "monitoring:recommendations",
                300,
                json.dumps(recommendations)
            )

        except Exception as e:
            logger.warning(f"Failed to cache monitoring state: {e}")

    async def _get_cached_system_metrics(self) -> Optional[Dict]:
        """Get cached system metrics."""
        try:
            cached = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.get, "monitoring:system_metrics"
            )
            return json.loads(cached) if cached else None
        except:
            return None

    async def _get_cached_recommendations(self) -> Dict[str, List[str]]:
        """Get cached optimization recommendations."""
        try:
            cached = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.get, "monitoring:recommendations"
            )
            return json.loads(cached) if cached else {}
        except:
            return {}

    async def _get_model_performance_summary(self) -> Dict[str, Any]:
        """Get ML model performance summary."""
        try:
            summary = {
                'total_models': len(self.ml_tracker.model_metrics),
                'models': []
            }

            for model_id, metrics_list in self.ml_tracker.model_metrics.items():
                if metrics_list:
                    latest = metrics_list[-1]
                    summary['models'].append({
                        'model_id': model_id,
                        'accuracy': latest.accuracy,
                        'latency_ms': latest.inference_latency_ms,
                        'predictions_count': latest.predictions_count,
                        'last_updated': latest.timestamp.isoformat()
                    })

            return summary

        except Exception as e:
            logger.error(f"Error getting model summary: {e}")
            return {'total_models': 0, 'models': []}


# Performance monitoring instance (singleton)
performance_monitor = EnhancedPerformanceMonitoringService()


# Utility functions for easy integration
async def track_model_performance(
    model_id: str,
    model_version: str,
    accuracy: float,
    latency_ms: float,
    predictions_count: int = 1,
    **additional_metrics
) -> Tuple[ModelMetrics, List[PerformanceAlert]]:
    """Utility function to track ML model performance."""
    metrics = {
        'accuracy': accuracy,
        'latency_ms': latency_ms,
        **additional_metrics
    }
    return await performance_monitor.track_ml_model_performance(
        model_id, model_version, metrics, predictions_count
    )


async def get_performance_summary() -> Dict[str, Any]:
    """Get current performance monitoring summary."""
    return await performance_monitor.get_performance_dashboard_data()


def start_background_monitoring(interval_seconds: int = 30):
    """Start background performance monitoring."""
    asyncio.create_task(performance_monitor.start_monitoring(interval_seconds))


def stop_background_monitoring():
    """Stop background performance monitoring."""
    performance_monitor.stop_monitoring()


if __name__ == "__main__":
    # Example usage
    async def demo():
        """Demo performance monitoring."""
        # Track a model
        metrics, alerts = await track_model_performance(
            model_id="lead_scorer_v2",
            model_version="2.1.0",
            accuracy=0.96,
            latency_ms=45.2,
            predictions_count=100,
            precision=0.94,
            recall=0.92,
            f1_score=0.93
        )

        print(f"Tracked model metrics: {metrics.accuracy:.2%} accuracy, {metrics.inference_latency_ms:.1f}ms latency")
        if alerts:
            print(f"Generated {len(alerts)} alerts")

        # Get performance summary
        summary = await get_performance_summary()
        print(f"Performance summary: {summary}")

    # Run demo
    asyncio.run(demo())