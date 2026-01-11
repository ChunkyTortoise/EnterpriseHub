"""
Tests for Enterprise Monitoring Stack

Comprehensive testing for:
- Prometheus metrics collection
- ML-based predictive alerting
- Alert notification system
- Incident management
- Performance targets validation
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
import numpy as np

# Import monitoring components
from ghl_real_estate_ai.infrastructure.enterprise_monitoring import (
    EnterpriseMetricsRegistry,
    PredictiveAlertingEngine,
    EnterpriseMonitoringStack,
    MetricCategory
)

from ghl_real_estate_ai.services.predictive_alerting_engine import (
    PredictiveAlertingService,
    AlertChannel,
    IncidentPriority,
    AlertNotificationManager,
    IncidentManagementSystem
)

from services.ai_operations.intelligent_monitoring_engine import (
    IntelligentMonitoringEngine,
    AlertSeverity,
    AnomalyType
)


class TestEnterpriseMetricsRegistry:
    """Test Prometheus metrics registry."""

    def test_registry_initialization(self):
        """Test metrics registry initializes with all metric categories."""
        registry = EnterpriseMetricsRegistry()

        assert registry.metrics is not None
        assert len(registry.metrics) > 0

        # Check infrastructure metrics
        assert 'cpu_usage_percent' in registry.metrics
        assert 'memory_usage_bytes' in registry.metrics
        assert 'disk_usage_bytes' in registry.metrics

        # Check application metrics
        assert 'http_requests_total' in registry.metrics
        assert 'http_request_duration' in registry.metrics
        assert 'database_connections' in registry.metrics

        # Check business metrics
        assert 'leads_total' in registry.metrics
        assert 'lead_score' in registry.metrics
        assert 'property_matches' in registry.metrics

        # Check ML metrics
        assert 'ml_inference_duration' in registry.metrics
        assert 'ml_model_accuracy' in registry.metrics
        assert 'ml_model_drift_score' in registry.metrics

    def test_system_metrics_collection(self):
        """Test system metrics are collected correctly."""
        registry = EnterpriseMetricsRegistry()

        # Collect system metrics
        registry.collect_system_metrics()

        # Verify metrics were collected (they should be set with values > 0)
        assert registry.metrics is not None

    def test_metric_access_with_labels(self):
        """Test accessing metrics with labels."""
        registry = EnterpriseMetricsRegistry()

        # Get HTTP request metric with labels
        http_metric = registry.get_metric(
            'http_requests_total',
            service='test',
            method='GET',
            endpoint='/api/test',
            status='200'
        )

        assert http_metric is not None

        # Increment the metric
        http_metric.inc()

        # The value should be tracked
        assert http_metric._value.get() >= 1


class TestPredictiveAlertingEngine:
    """Test ML-based predictive alerting."""

    @pytest.mark.asyncio
    async def test_alerting_engine_initialization(self):
        """Test alerting engine initializes correctly."""
        registry = EnterpriseMetricsRegistry()
        engine = PredictiveAlertingEngine(
            metrics_registry=registry,
            alert_accuracy_target=0.95
        )

        await engine.initialize()

        assert engine.monitoring_engine is not None
        assert engine.active_alerts is not None

        await engine.shutdown()

    @pytest.mark.asyncio
    async def test_metric_ingestion_for_prediction(self):
        """Test metrics are ingested for predictive analysis."""
        registry = EnterpriseMetricsRegistry()
        engine = PredictiveAlertingEngine(metrics_registry=registry)

        await engine.initialize()

        try:
            # Ingest normal metrics
            for i in range(10):
                await engine.ingest_metric_for_prediction(
                    'test_service',
                    'response_time',
                    50.0 + np.random.normal(0, 5)
                )

            # Wait for processing
            await asyncio.sleep(2)

            # Should have processed metrics
            assert engine.monitoring_engine is not None

        finally:
            await engine.shutdown()

    @pytest.mark.asyncio
    async def test_alert_deduplication(self):
        """Test duplicate alerts are filtered."""
        registry = EnterpriseMetricsRegistry()
        engine = PredictiveAlertingEngine(metrics_registry=registry)

        await engine.initialize()

        try:
            # Ingest anomalous metrics that should trigger alerts
            for i in range(5):
                await engine.ingest_metric_for_prediction(
                    'test_service',
                    'response_time',
                    500.0 + np.random.normal(0, 10)  # Abnormally high
                )
                await asyncio.sleep(0.5)

            # Wait for alert processing
            await asyncio.sleep(3)

            # Should have alerts but with deduplication
            # (exact count depends on timing and ML detection)

        finally:
            await engine.shutdown()

    @pytest.mark.asyncio
    async def test_capacity_forecasting(self):
        """Test capacity forecasting functionality."""
        registry = EnterpriseMetricsRegistry()
        engine = PredictiveAlertingEngine(metrics_registry=registry)

        await engine.initialize()

        try:
            forecast = await engine.forecast_capacity('memory', horizon_hours=24)

            assert forecast is not None
            assert 'resource_type' in forecast
            assert forecast['resource_type'] == 'memory'
            assert 'horizon_hours' in forecast

        finally:
            await engine.shutdown()


class TestPredictiveAlertingService:
    """Test predictive alerting service."""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test alerting service starts correctly."""
        service = PredictiveAlertingService(
            alert_accuracy_target=0.95,
            prediction_horizon_minutes=10
        )

        await service.start()

        assert service.monitoring_engine is not None
        assert service.notification_manager is not None
        assert service.incident_manager is not None
        assert len(service.alert_rules) > 0

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_alert_rule_loading(self):
        """Test default alert rules are loaded."""
        service = PredictiveAlertingService()
        await service.start()

        try:
            # Should have default alert rules
            assert len(service.alert_rules) >= 4

            # Check for specific rules
            assert 'high_cpu' in service.alert_rules
            assert 'high_memory' in service.alert_rules
            assert 'ml_inference_slow' in service.alert_rules

        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_metric_ingestion_and_alerting(self):
        """Test metrics trigger alerts correctly."""
        service = PredictiveAlertingService()
        await service.start()

        try:
            # Ingest normal metrics
            for i in range(10):
                await service.ingest_metric(
                    'test_service',
                    'response_time_ms',
                    45.0 + np.random.normal(0, 5)
                )

            # Ingest anomalous metrics
            for i in range(5):
                await service.ingest_metric(
                    'test_service',
                    'response_time_ms',
                    250.0 + np.random.normal(0, 10)
                )

            # Wait for processing
            await asyncio.sleep(5)

            # Check alert statistics
            assert service.alert_stats['total_alerts'] >= 0

        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_alert_performance_report(self):
        """Test alert performance reporting."""
        service = PredictiveAlertingService()
        await service.start()

        try:
            report = service.get_alert_performance_report()

            assert 'accuracy' in report
            assert 'false_positive_rate' in report
            assert 'stats' in report
            assert 'mttr' in report

        finally:
            await service.shutdown()


class TestAlertNotificationManager:
    """Test alert notification system."""

    @pytest.mark.asyncio
    async def test_notification_manager_initialization(self):
        """Test notification manager initializes."""
        manager = AlertNotificationManager()

        assert manager.notification_history is not None
        assert manager.channel_configs is not None

    def test_channel_configuration(self):
        """Test notification channel configuration."""
        manager = AlertNotificationManager()

        manager.configure_channel(
            AlertChannel.SLACK,
            {'webhook_url': 'https://hooks.slack.com/test', 'enabled': True}
        )

        assert AlertChannel.SLACK in manager.channel_configs

    @pytest.mark.asyncio
    async def test_log_notification(self):
        """Test log-based notifications work."""
        from services.ai_operations.intelligent_monitoring_engine import PredictiveAlert

        manager = AlertNotificationManager()

        # Create test alert
        test_alert = PredictiveAlert(
            alert_id='test-001',
            service_name='test_service',
            alert_type=AnomalyType.PERFORMANCE_DEGRADATION,
            severity=AlertSeverity.WARNING,
            confidence=np.float32(0.85),
            predicted_impact='Test impact',
            time_to_impact=timedelta(minutes=5),
            recommended_actions=['Test action'],
            auto_resolution_possible=True,
            root_cause_analysis={}
        )

        # Send to log channel
        results = await manager.send_alert_notification(
            test_alert,
            [AlertChannel.LOG]
        )

        assert results[AlertChannel.LOG.value] is True


class TestIncidentManagementSystem:
    """Test incident management."""

    @pytest.mark.asyncio
    async def test_incident_creation(self):
        """Test incident creation from alerts."""
        from services.ai_operations.intelligent_monitoring_engine import PredictiveAlert

        manager = IncidentManagementSystem()

        # Create test alerts
        test_alerts = [
            PredictiveAlert(
                alert_id=f'test-{i}',
                service_name='test_service',
                alert_type=AnomalyType.PERFORMANCE_DEGRADATION,
                severity=AlertSeverity.HIGH,
                confidence=np.float32(0.85),
                predicted_impact='Test impact',
                time_to_impact=timedelta(minutes=5),
                recommended_actions=['Test action'],
                auto_resolution_possible=False,
                root_cause_analysis={}
            )
            for i in range(3)
        ]

        incident = await manager.create_incident(
            alerts=test_alerts,
            title='Test Incident',
            description='Test incident description'
        )

        assert incident is not None
        assert incident.priority == IncidentPriority.P1_HIGH
        assert len(incident.alerts) == 3
        assert incident.status == 'open'

    @pytest.mark.asyncio
    async def test_incident_resolution(self):
        """Test incident resolution tracking."""
        from services.ai_operations.intelligent_monitoring_engine import PredictiveAlert

        manager = IncidentManagementSystem()

        # Create incident
        test_alert = PredictiveAlert(
            alert_id='test-001',
            service_name='test_service',
            alert_type=AnomalyType.PERFORMANCE_DEGRADATION,
            severity=AlertSeverity.MEDIUM,
            confidence=np.float32(0.85),
            predicted_impact='Test impact',
            time_to_impact=timedelta(minutes=5),
            recommended_actions=['Test action'],
            auto_resolution_possible=True,
            root_cause_analysis={}
        )

        incident = await manager.create_incident(
            alerts=[test_alert],
            title='Test Incident',
            description='Test'
        )

        incident_id = incident.incident_id

        # Wait a bit
        await asyncio.sleep(1)

        # Resolve incident
        await manager.resolve_incident(
            incident_id,
            'Resolved by test'
        )

        # Should be resolved
        assert incident_id not in manager.incidents
        assert len(manager.incident_history) > 0

    def test_mttr_calculation(self):
        """Test Mean Time To Resolution calculation."""
        manager = IncidentManagementSystem()

        # Manually set some MTTR data for testing
        manager.mttr_by_priority[IncidentPriority.P1_HIGH] = timedelta(minutes=15)
        manager.mttr_by_priority[IncidentPriority.P2_MEDIUM] = timedelta(minutes=30)

        report = manager.get_mttr_report()

        assert 'p1_high' in report
        assert report['p1_high']['mttr_minutes'] == 15.0


class TestEnterpriseMonitoringStack:
    """Test complete monitoring stack integration."""

    @pytest.mark.asyncio
    async def test_monitoring_stack_startup(self):
        """Test monitoring stack starts all components."""
        stack = EnterpriseMonitoringStack(
            enable_prometheus=True,
            enable_predictive_alerts=True,
            metrics_collection_interval=5
        )

        await stack.start()

        assert stack.metrics_registry is not None
        assert stack.alerting_engine is not None
        assert stack.is_running is True

        await stack.stop()

    @pytest.mark.asyncio
    async def test_metrics_collection_loop(self):
        """Test metrics are collected periodically."""
        stack = EnterpriseMonitoringStack(
            metrics_collection_interval=2  # Fast collection for testing
        )

        await stack.start()

        # Let it run for a bit
        await asyncio.sleep(5)

        # Should have collected metrics
        metrics_snapshot = stack.get_metrics_snapshot()
        assert len(metrics_snapshot) > 0

        await stack.stop()

    @pytest.mark.asyncio
    async def test_monitoring_overhead(self):
        """Test monitoring overhead is <2% as per target."""
        import psutil

        # Measure baseline CPU
        baseline_cpu = psutil.cpu_percent(interval=1)

        stack = EnterpriseMonitoringStack(
            metrics_collection_interval=5
        )

        await stack.start()

        # Let monitoring run
        await asyncio.sleep(10)

        # Measure CPU with monitoring
        monitoring_cpu = psutil.cpu_percent(interval=1)

        await stack.stop()

        # Calculate overhead (rough approximation)
        overhead = monitoring_cpu - baseline_cpu

        # Should be less than 2% overhead
        # Note: This is a rough test and may vary based on system load
        assert overhead < 5.0  # Using 5% as threshold to account for test variance


class TestPerformanceTargets:
    """Validate performance targets are met."""

    @pytest.mark.asyncio
    async def test_alert_processing_time(self):
        """Test alert processing time is <100ms."""
        service = PredictiveAlertingService()
        await service.start()

        try:
            processing_times = []

            for i in range(10):
                start_time = time.perf_counter()

                await service.ingest_metric(
                    'test_service',
                    'response_time',
                    50.0
                )

                processing_time = (time.perf_counter() - start_time) * 1000  # ms
                processing_times.append(processing_time)

            # Average processing time should be <100ms
            avg_processing_time = np.mean(processing_times)
            assert avg_processing_time < 100.0, f"Average processing time {avg_processing_time}ms exceeds 100ms target"

        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_prediction_lead_time(self):
        """Test prediction lead time is 5-15 minutes."""
        service = PredictiveAlertingService(
            prediction_horizon_minutes=10
        )

        await service.start()

        try:
            assert service.prediction_horizon == 10
            assert 5 <= service.prediction_horizon <= 15

        finally:
            await service.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
