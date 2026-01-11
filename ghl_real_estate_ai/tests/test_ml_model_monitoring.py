"""
Comprehensive Test Suite for ML Model Monitoring System

This test suite provides thorough coverage of the ML model monitoring infrastructure,
including model performance tracking, drift detection, A/B testing, and alerting systems.

Test Categories:
- Model performance KPI tracking
- Drift detection algorithms
- A/B testing framework
- Automated alerting systems
- Dashboard integration
- Error handling and resilience

Author: EnterpriseHub AI - TDD Implementation
Date: 2026-01-10
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, List, Any, Optional

# Import system under test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports - these will be implemented following TDD
from services.ml_model_monitoring import (
    MLModelMonitoringService,
    ModelPerformanceTracker,
    ModelDriftDetector,
    ModelABTestFramework,
    ModelAlertingSystem,
    ModelPerformanceMetrics,
    DriftAnalysisResult,
    ABTestResult,
    AlertConfiguration,
    ModelMonitoringDashboard
)

from services.ai_predictive_lead_scoring import PredictiveLeadScorer
from services.churn_prediction_service import ChurnPredictionService
from services.property_matcher import PropertyMatcher


class TestMLModelMonitoringService:
    """Test suite for the main ML Model Monitoring Service"""

    @pytest.fixture
    async def monitoring_service(self):
        """Create ML monitoring service with mocked dependencies"""
        lead_scorer = Mock(spec=PredictiveLeadScorer)
        churn_predictor = Mock(spec=ChurnPredictionService)
        property_matcher = Mock(spec=PropertyMatcher)

        # Create monitoring service
        service = MLModelMonitoringService(
            lead_scorer=lead_scorer,
            churn_predictor=churn_predictor,
            property_matcher=property_matcher,
            storage_backend="memory"  # Use in-memory storage for tests
        )

        await service.initialize()
        return service

    @pytest.fixture
    def sample_performance_data(self):
        """Sample performance data for testing"""
        return {
            'lead_scoring': {
                'accuracy': 0.96,
                'precision': 0.94,
                'recall': 0.93,
                'f1_score': 0.935,
                'auc_roc': 0.97,
                'inference_time_ms': 145.2,
                'prediction_count': 1500,
                'timestamp': datetime.now()
            },
            'churn_prediction': {
                'accuracy': 0.92,
                'precision': 0.94,
                'recall': 0.89,
                'f1_score': 0.915,
                'auc_roc': 0.95,
                'inference_time_ms': 198.7,
                'prediction_count': 800,
                'timestamp': datetime.now()
            },
            'property_matching': {
                'satisfaction_score': 0.89,
                'match_quality': 0.86,
                'relevance_score': 0.91,
                'response_time_ms': 85.3,
                'match_count': 2200,
                'timestamp': datetime.now()
            }
        }

    @pytest.mark.asyncio
    async def test_service_initialization(self, monitoring_service):
        """Test service initialization and component setup"""
        assert monitoring_service.performance_tracker is not None
        assert monitoring_service.drift_detector is not None
        assert monitoring_service.ab_test_framework is not None
        assert monitoring_service.alerting_system is not None
        assert monitoring_service.dashboard is not None

        # Verify models are registered
        registered_models = await monitoring_service.get_registered_models()
        assert 'lead_scoring' in registered_models
        assert 'churn_prediction' in registered_models
        assert 'property_matching' in registered_models

    @pytest.mark.asyncio
    async def test_performance_tracking_integration(self, monitoring_service, sample_performance_data):
        """Test integration with performance tracking system"""
        # Record performance metrics
        for model_name, metrics in sample_performance_data.items():
            await monitoring_service.record_model_performance(model_name, metrics)

        # Verify metrics are tracked
        lead_scoring_metrics = await monitoring_service.get_model_performance(
            'lead_scoring',
            hours=24
        )

        assert len(lead_scoring_metrics) > 0
        latest_metric = lead_scoring_metrics[0]
        assert latest_metric.accuracy == 0.96
        assert latest_metric.inference_time_ms == 145.2

    @pytest.mark.asyncio
    async def test_real_time_monitoring_workflow(self, monitoring_service):
        """Test real-time monitoring workflow"""
        # Mock live prediction
        prediction_data = {
            'model': 'lead_scoring',
            'prediction': 0.85,
            'confidence': 0.92,
            'features': {'engagement': 0.8, 'budget_match': 0.9},
            'inference_time_ms': 150.5,
            'timestamp': datetime.now()
        }

        # Process real-time prediction
        result = await monitoring_service.process_live_prediction(prediction_data)

        assert result['status'] == 'processed'
        assert result['drift_detected'] is False  # No drift on first prediction
        assert result['performance_updated'] is True


class TestModelPerformanceTracker:
    """Test suite for model performance tracking"""

    @pytest.fixture
    def performance_tracker(self):
        """Create performance tracker instance"""
        return ModelPerformanceTracker(
            storage_backend="memory",
            retention_days=30
        )

    @pytest.fixture
    def historical_metrics(self):
        """Generate historical performance metrics"""
        base_date = datetime.now() - timedelta(days=30)
        metrics = []

        for i in range(30):  # 30 days of data
            date = base_date + timedelta(days=i)

            # Simulate performance degradation over time for lead scoring
            accuracy = 0.95 - (i * 0.002)  # Slow degradation

            metric = ModelPerformanceMetrics(
                model_name='lead_scoring',
                timestamp=date,
                accuracy=accuracy,
                precision=accuracy + 0.01,
                recall=accuracy - 0.01,
                f1_score=accuracy,
                auc_roc=accuracy + 0.02,
                inference_time_ms=150 + (i * 2),  # Gradual slowdown
                prediction_count=1000 + np.random.randint(-100, 100)
            )
            metrics.append(metric)

        return metrics

    @pytest.mark.asyncio
    async def test_performance_metric_recording(self, performance_tracker):
        """Test recording of performance metrics"""
        metric = ModelPerformanceMetrics(
            model_name='lead_scoring',
            timestamp=datetime.now(),
            accuracy=0.95,
            precision=0.93,
            recall=0.92,
            f1_score=0.925,
            auc_roc=0.96,
            inference_time_ms=145.0,
            prediction_count=1200
        )

        await performance_tracker.record_metric(metric)

        # Verify metric was recorded
        metrics = await performance_tracker.get_metrics(
            'lead_scoring',
            start_time=datetime.now() - timedelta(hours=1)
        )

        assert len(metrics) == 1
        assert metrics[0].accuracy == 0.95

    @pytest.mark.asyncio
    async def test_performance_trend_analysis(self, performance_tracker, historical_metrics):
        """Test performance trend analysis"""
        # Record historical metrics
        for metric in historical_metrics:
            await performance_tracker.record_metric(metric)

        # Analyze trends
        trend_analysis = await performance_tracker.analyze_performance_trend(
            'lead_scoring',
            metric_name='accuracy',
            days=30
        )

        assert trend_analysis['trend_direction'] == 'declining'
        assert trend_analysis['change_rate'] < 0  # Negative change rate
        assert trend_analysis['significance_level'] > 0.05  # Statistical significance

    @pytest.mark.asyncio
    async def test_performance_threshold_detection(self, performance_tracker):
        """Test performance threshold violation detection"""
        # Configure thresholds
        thresholds = {
            'accuracy': {'min': 0.90, 'target': 0.95},
            'inference_time_ms': {'max': 200, 'target': 150}
        }

        await performance_tracker.set_performance_thresholds('lead_scoring', thresholds)

        # Record metric that violates threshold
        violation_metric = ModelPerformanceMetrics(
            model_name='lead_scoring',
            timestamp=datetime.now(),
            accuracy=0.85,  # Below min threshold
            precision=0.83,
            recall=0.82,
            f1_score=0.825,
            auc_roc=0.87,
            inference_time_ms=250.0,  # Above max threshold
            prediction_count=1000
        )

        violations = await performance_tracker.check_threshold_violations(violation_metric)

        assert len(violations) == 2  # Accuracy and inference time violations
        assert 'accuracy' in [v['metric'] for v in violations]
        assert 'inference_time_ms' in [v['metric'] for v in violations]


class TestModelDriftDetector:
    """Test suite for model drift detection"""

    @pytest.fixture
    def drift_detector(self):
        """Create drift detector instance"""
        return ModelDriftDetector(
            drift_threshold=0.05,  # 5% threshold for statistical tests
            min_samples=100
        )

    @pytest.fixture
    def baseline_distribution(self):
        """Generate baseline feature distribution"""
        np.random.seed(42)  # Reproducible results
        return {
            'engagement_score': np.random.normal(0.7, 0.15, 1000),
            'budget_match': np.random.normal(0.6, 0.20, 1000),
            'response_time': np.random.exponential(2.0, 1000),
            'property_views': np.random.poisson(5, 1000)
        }

    @pytest.fixture
    def drifted_distribution(self):
        """Generate drifted feature distribution"""
        np.random.seed(24)  # Different seed for drift
        return {
            'engagement_score': np.random.normal(0.6, 0.18, 500),  # Mean shift
            'budget_match': np.random.normal(0.65, 0.25, 500),     # Variance shift
            'response_time': np.random.exponential(3.5, 500),       # Distribution change
            'property_views': np.random.poisson(7, 500)             # Parameter change
        }

    @pytest.mark.asyncio
    async def test_drift_detection_initialization(self, drift_detector, baseline_distribution):
        """Test drift detector initialization with baseline data"""
        await drift_detector.set_baseline_distribution(
            'lead_scoring',
            baseline_distribution
        )

        # Verify baseline was set
        baseline = await drift_detector.get_baseline_distribution('lead_scoring')
        assert baseline is not None
        assert 'engagement_score' in baseline
        assert len(baseline['engagement_score']) == 1000

    @pytest.mark.asyncio
    async def test_statistical_drift_detection(self, drift_detector, baseline_distribution, drifted_distribution):
        """Test statistical drift detection using KS test"""
        # Set baseline
        await drift_detector.set_baseline_distribution('lead_scoring', baseline_distribution)

        # Detect drift
        drift_result = await drift_detector.detect_feature_drift(
            'lead_scoring',
            drifted_distribution
        )

        assert isinstance(drift_result, DriftAnalysisResult)
        assert drift_result.overall_drift_detected is True
        assert len(drift_result.feature_drift_scores) == 4

        # Engagement score should show significant drift (mean shift)
        engagement_drift = next(
            score for feature, score in drift_result.feature_drift_scores.items()
            if feature == 'engagement_score'
        )
        assert engagement_drift > 0.05  # Above threshold

    @pytest.mark.asyncio
    async def test_prediction_drift_monitoring(self, drift_detector):
        """Test prediction output drift monitoring"""
        # Set baseline prediction distribution
        baseline_predictions = np.random.beta(2, 3, 1000)  # Skewed towards lower scores
        await drift_detector.set_baseline_predictions('lead_scoring', baseline_predictions)

        # Generate drifted predictions
        drifted_predictions = np.random.beta(4, 2, 500)  # Skewed towards higher scores

        # Detect prediction drift
        prediction_drift = await drift_detector.detect_prediction_drift(
            'lead_scoring',
            drifted_predictions
        )

        assert prediction_drift['drift_detected'] is True
        assert prediction_drift['drift_magnitude'] > 0.1  # Significant drift

    @pytest.mark.asyncio
    async def test_confidence_drift_detection(self, drift_detector):
        """Test model confidence drift detection"""
        # Baseline: High confidence predictions
        baseline_confidence = np.random.normal(0.85, 0.1, 1000)
        baseline_confidence = np.clip(baseline_confidence, 0, 1)

        await drift_detector.set_baseline_confidence('churn_prediction', baseline_confidence)

        # Drifted: Lower confidence predictions
        drifted_confidence = np.random.normal(0.65, 0.15, 500)
        drifted_confidence = np.clip(drifted_confidence, 0, 1)

        # Detect confidence drift
        confidence_drift = await drift_detector.detect_confidence_drift(
            'churn_prediction',
            drifted_confidence
        )

        assert confidence_drift['drift_detected'] is True
        assert confidence_drift['mean_confidence_change'] < -0.1  # Significant decrease


class TestModelABTestFramework:
    """Test suite for A/B testing framework"""

    @pytest.fixture
    def ab_test_framework(self):
        """Create A/B test framework instance"""
        return ModelABTestFramework(
            statistical_power=0.8,
            significance_level=0.05
        )

    @pytest.mark.asyncio
    async def test_ab_test_setup(self, ab_test_framework):
        """Test A/B test experiment setup"""
        test_config = {
            'name': 'lead_scoring_improvement',
            'model_a': 'lead_scoring_v1',
            'model_b': 'lead_scoring_v2',
            'traffic_split': 0.5,
            'success_metric': 'accuracy',
            'minimum_sample_size': 1000,
            'max_duration_days': 14
        }

        test_id = await ab_test_framework.create_ab_test(test_config)

        assert test_id is not None

        # Verify test was created
        test_info = await ab_test_framework.get_test_info(test_id)
        assert test_info['name'] == 'lead_scoring_improvement'
        assert test_info['status'] == 'active'

    @pytest.mark.asyncio
    async def test_traffic_routing(self, ab_test_framework):
        """Test traffic routing for A/B tests"""
        # Create test
        test_config = {
            'name': 'churn_prediction_test',
            'model_a': 'churn_v1',
            'model_b': 'churn_v2',
            'traffic_split': 0.3,  # 30% to model_b
            'success_metric': 'precision',
            'minimum_sample_size': 500,
            'max_duration_days': 10
        }

        test_id = await ab_test_framework.create_ab_test(test_config)

        # Simulate traffic routing
        model_assignments = []
        for i in range(1000):
            assigned_model = await ab_test_framework.get_model_assignment(
                test_id,
                user_id=f'user_{i}'
            )
            model_assignments.append(assigned_model)

        # Check traffic split is approximately correct
        model_b_count = sum(1 for m in model_assignments if m == 'churn_v2')
        model_b_percentage = model_b_count / 1000

        assert 0.25 <= model_b_percentage <= 0.35  # Allow for some variance

    @pytest.mark.asyncio
    async def test_statistical_significance_calculation(self, ab_test_framework):
        """Test statistical significance calculation"""
        # Create test and record results
        test_config = {
            'name': 'property_matching_test',
            'model_a': 'property_v1',
            'model_b': 'property_v2',
            'traffic_split': 0.5,
            'success_metric': 'satisfaction_score',
            'minimum_sample_size': 200,
            'max_duration_days': 7
        }

        test_id = await ab_test_framework.create_ab_test(test_config)

        # Simulate results - model B performs better
        np.random.seed(42)
        model_a_results = np.random.normal(0.75, 0.1, 150)  # Lower performance
        model_b_results = np.random.normal(0.82, 0.12, 150)  # Higher performance

        # Record results
        for result in model_a_results:
            await ab_test_framework.record_result(test_id, 'property_v1', result)

        for result in model_b_results:
            await ab_test_framework.record_result(test_id, 'property_v2', result)

        # Calculate significance
        test_result = await ab_test_framework.calculate_test_significance(test_id)

        assert isinstance(test_result, ABTestResult)
        assert test_result.is_significant is True
        assert test_result.p_value < 0.05
        assert test_result.winning_model == 'property_v2'


class TestModelAlertingSystem:
    """Test suite for automated alerting system"""

    @pytest.fixture
    def alerting_system(self):
        """Create alerting system instance"""
        return ModelAlertingSystem(
            notification_channels=['email', 'slack'],
            escalation_rules=True
        )

    @pytest.fixture
    def alert_configurations(self):
        """Sample alert configurations"""
        return {
            'lead_scoring_performance': AlertConfiguration(
                model_name='lead_scoring',
                metric='accuracy',
                threshold=0.90,
                comparison='less_than',
                severity='high',
                cooldown_minutes=30
            ),
            'churn_prediction_drift': AlertConfiguration(
                model_name='churn_prediction',
                metric='feature_drift',
                threshold=0.05,
                comparison='greater_than',
                severity='medium',
                cooldown_minutes=60
            ),
            'property_matching_latency': AlertConfiguration(
                model_name='property_matching',
                metric='response_time_ms',
                threshold=200,
                comparison='greater_than',
                severity='low',
                cooldown_minutes=15
            )
        }

    @pytest.mark.asyncio
    async def test_alert_configuration(self, alerting_system, alert_configurations):
        """Test alert configuration management"""
        for alert_name, config in alert_configurations.items():
            await alerting_system.configure_alert(alert_name, config)

        # Verify alerts were configured
        configured_alerts = await alerting_system.get_alert_configurations()
        assert len(configured_alerts) == 3
        assert 'lead_scoring_performance' in configured_alerts

    @pytest.mark.asyncio
    async def test_alert_triggering(self, alerting_system, alert_configurations):
        """Test alert triggering logic"""
        # Configure alert
        await alerting_system.configure_alert(
            'test_performance_alert',
            alert_configurations['lead_scoring_performance']
        )

        # Trigger alert with metric that violates threshold
        metric_data = {
            'model_name': 'lead_scoring',
            'metric': 'accuracy',
            'value': 0.85,  # Below 0.90 threshold
            'timestamp': datetime.now()
        }

        alert_triggered = await alerting_system.check_and_trigger_alert(
            'test_performance_alert',
            metric_data
        )

        assert alert_triggered is True

        # Check alert was logged
        recent_alerts = await alerting_system.get_recent_alerts(hours=1)
        assert len(recent_alerts) > 0
        assert recent_alerts[0]['alert_name'] == 'test_performance_alert'

    @pytest.mark.asyncio
    async def test_alert_cooldown(self, alerting_system, alert_configurations):
        """Test alert cooldown functionality"""
        # Configure alert with 30-minute cooldown
        await alerting_system.configure_alert(
            'cooldown_test',
            alert_configurations['lead_scoring_performance']
        )

        metric_data = {
            'model_name': 'lead_scoring',
            'metric': 'accuracy',
            'value': 0.80,  # Triggers alert
            'timestamp': datetime.now()
        }

        # First alert should trigger
        first_alert = await alerting_system.check_and_trigger_alert(
            'cooldown_test',
            metric_data
        )
        assert first_alert is True

        # Second alert within cooldown period should not trigger
        metric_data['timestamp'] = datetime.now() + timedelta(minutes=10)
        second_alert = await alerting_system.check_and_trigger_alert(
            'cooldown_test',
            metric_data
        )
        assert second_alert is False

    @pytest.mark.asyncio
    async def test_escalation_rules(self, alerting_system):
        """Test alert escalation rules"""
        escalation_config = AlertConfiguration(
            model_name='lead_scoring',
            metric='accuracy',
            threshold=0.80,
            comparison='less_than',
            severity='critical',
            cooldown_minutes=0,  # No cooldown for testing
            escalation_after_alerts=3,
            escalation_severity='emergency'
        )

        await alerting_system.configure_alert('escalation_test', escalation_config)

        metric_data = {
            'model_name': 'lead_scoring',
            'metric': 'accuracy',
            'value': 0.75,  # Triggers alert
            'timestamp': datetime.now()
        }

        # Trigger alerts multiple times
        for i in range(4):
            metric_data['timestamp'] = datetime.now() + timedelta(minutes=i)
            await alerting_system.check_and_trigger_alert('escalation_test', metric_data)

        # Check if escalation occurred
        recent_alerts = await alerting_system.get_recent_alerts(hours=1)
        escalated_alerts = [a for a in recent_alerts if a.get('severity') == 'emergency']

        assert len(escalated_alerts) > 0


class TestModelMonitoringDashboard:
    """Test suite for monitoring dashboard integration"""

    @pytest.fixture
    def dashboard(self):
        """Create monitoring dashboard instance"""
        return ModelMonitoringDashboard(
            refresh_interval_seconds=30,
            max_data_points=1000
        )

    @pytest.mark.asyncio
    async def test_dashboard_data_aggregation(self, dashboard):
        """Test dashboard data aggregation"""
        # Simulate performance data
        performance_data = []
        base_time = datetime.now() - timedelta(hours=24)

        for i in range(24):  # Hourly data for 24 hours
            timestamp = base_time + timedelta(hours=i)
            performance_data.append({
                'model': 'lead_scoring',
                'timestamp': timestamp,
                'accuracy': 0.95 - (i * 0.001),  # Slight degradation
                'inference_time': 150 + (i * 2)   # Slight increase
            })

        # Aggregate data for dashboard
        aggregated_data = await dashboard.aggregate_performance_data(
            performance_data,
            interval='hour'
        )

        assert len(aggregated_data) == 24
        assert 'accuracy_avg' in aggregated_data[0]
        assert 'inference_time_avg' in aggregated_data[0]

    @pytest.mark.asyncio
    async def test_real_time_metrics_feed(self, dashboard):
        """Test real-time metrics feed"""
        # Start real-time feed
        metrics_feed = dashboard.create_real_time_feed(['lead_scoring', 'churn_prediction'])

        # Simulate incoming metrics
        test_metric = {
            'model': 'lead_scoring',
            'timestamp': datetime.now(),
            'accuracy': 0.94,
            'prediction_count': 150
        }

        await dashboard.push_real_time_metric(test_metric)

        # Verify metric appears in feed
        latest_metrics = await dashboard.get_latest_metrics(limit=1)
        assert len(latest_metrics) > 0
        assert latest_metrics[0]['model'] == 'lead_scoring'


class TestEdgeCasesAndErrorHandling:
    """Test suite for edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_missing_baseline_data_handling(self):
        """Test handling of missing baseline data for drift detection"""
        drift_detector = ModelDriftDetector()

        # Try to detect drift without baseline
        current_data = {'feature1': np.random.normal(0, 1, 100)}

        drift_result = await drift_detector.detect_feature_drift(
            'nonexistent_model',
            current_data
        )

        # Should handle gracefully
        assert drift_result.overall_drift_detected is False
        assert drift_result.error_message is not None

    @pytest.mark.asyncio
    async def test_insufficient_sample_size_handling(self):
        """Test handling of insufficient sample sizes"""
        ab_test_framework = ModelABTestFramework(
            minimum_sample_size=100
        )

        test_config = {
            'name': 'small_sample_test',
            'model_a': 'model_a',
            'model_b': 'model_b',
            'traffic_split': 0.5,
            'success_metric': 'accuracy',
            'minimum_sample_size': 1000,  # High minimum
            'max_duration_days': 1
        }

        test_id = await ab_test_framework.create_ab_test(test_config)

        # Record insufficient results
        for i in range(50):  # Only 50 samples
            await ab_test_framework.record_result(test_id, 'model_a', 0.8)
            await ab_test_framework.record_result(test_id, 'model_b', 0.85)

        # Should indicate insufficient data
        test_result = await ab_test_framework.calculate_test_significance(test_id)
        assert test_result.is_significant is False
        assert 'insufficient data' in test_result.notes.lower()

    @pytest.mark.asyncio
    async def test_concurrent_monitoring_operations(self, monitoring_service):
        """Test concurrent monitoring operations"""
        # Simulate concurrent performance recordings
        async def record_metrics():
            for i in range(10):
                metric_data = {
                    'accuracy': 0.9 + (i * 0.001),
                    'inference_time_ms': 150 + i,
                    'prediction_count': 100,
                    'timestamp': datetime.now()
                }
                await monitoring_service.record_model_performance('test_model', metric_data)

        # Run multiple concurrent tasks
        tasks = [record_metrics() for _ in range(5)]
        await asyncio.gather(*tasks)

        # Verify all metrics were recorded correctly
        metrics = await monitoring_service.get_model_performance('test_model', hours=1)
        assert len(metrics) == 50  # 5 tasks * 10 metrics each


# Integration Test
@pytest.mark.integration
class TestMLMonitoringSystemIntegration:
    """Integration tests for the complete ML monitoring system"""

    @pytest.fixture
    async def full_monitoring_system(self):
        """Set up complete monitoring system with real ML models"""
        # Create real instances (with mocked external dependencies)
        lead_scorer = PredictiveLeadScorer()
        churn_predictor = Mock(spec=ChurnPredictionService)  # Mock for simplicity
        property_matcher = PropertyMatcher()

        # Create monitoring service
        monitoring_service = MLModelMonitoringService(
            lead_scorer=lead_scorer,
            churn_predictor=churn_predictor,
            property_matcher=property_matcher,
            storage_backend="memory"
        )

        await monitoring_service.initialize()
        return monitoring_service

    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_workflow(self, full_monitoring_system):
        """Test complete end-to-end monitoring workflow"""
        # 1. Record baseline performance
        baseline_metrics = {
            'accuracy': 0.95,
            'precision': 0.93,
            'recall': 0.92,
            'f1_score': 0.925,
            'auc_roc': 0.96,
            'inference_time_ms': 145.0,
            'prediction_count': 1000,
            'timestamp': datetime.now() - timedelta(days=1)
        }

        await full_monitoring_system.record_model_performance(
            'lead_scoring',
            baseline_metrics
        )

        # 2. Set up alerts
        alert_config = AlertConfiguration(
            model_name='lead_scoring',
            metric='accuracy',
            threshold=0.90,
            comparison='less_than',
            severity='high',
            cooldown_minutes=5
        )

        await full_monitoring_system.alerting_system.configure_alert(
            'accuracy_degradation',
            alert_config
        )

        # 3. Simulate performance degradation
        degraded_metrics = {
            'accuracy': 0.85,  # Below threshold
            'precision': 0.83,
            'recall': 0.82,
            'f1_score': 0.825,
            'auc_roc': 0.87,
            'inference_time_ms': 200.0,  # Increased latency
            'prediction_count': 800,
            'timestamp': datetime.now()
        }

        await full_monitoring_system.record_model_performance(
            'lead_scoring',
            degraded_metrics
        )

        # 4. Verify alert was triggered
        recent_alerts = await full_monitoring_system.alerting_system.get_recent_alerts(hours=1)
        assert len(recent_alerts) > 0

        accuracy_alerts = [
            alert for alert in recent_alerts
            if alert['metric'] == 'accuracy'
        ]
        assert len(accuracy_alerts) > 0

        # 5. Check drift detection
        # Simulate feature distribution data
        current_features = {
            'engagement_score': np.random.normal(0.6, 0.15, 500),  # Drift from baseline
            'budget_match': np.random.normal(0.8, 0.10, 500)
        }

        drift_result = await full_monitoring_system.drift_detector.detect_feature_drift(
            'lead_scoring',
            current_features
        )

        # Verify monitoring system detected changes
        assert drift_result is not None


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([__file__, "-v", "--tb=short", "--cov=services.ml_model_monitoring"])