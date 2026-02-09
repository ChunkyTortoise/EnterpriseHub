import pytest
pytestmark = pytest.mark.integration

"""
Comprehensive tests for Inventory Alert System.

Test coverage:
- Alert system initialization and configuration
- Real-time market data processing
- Alert rule creation and management
- Alert generation and triggering
- Multi-channel delivery system
- Alert lifecycle management
- Performance monitoring and analytics
- Error handling and edge cases
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest
import pytest_asyncio

from ghl_real_estate_ai.services.inventory_alert_system import (

@pytest.mark.unit
    AlertChannel,
    AlertInstance,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    AlertType,
    InventoryAlertSystem,
    MarketDataPoint,
    TrendAnalysis,
    get_inventory_alert_system,
)


class TestInventoryAlertSystem:
    """Test suite for InventoryAlertSystem."""

    @pytest_asyncio.fixture
    async def alert_system(self):
        """Create alert system instance for testing."""
        system = InventoryAlertSystem()
        system.cache = AsyncMock()

        # Mock background monitoring task
        with patch.object(system, "_monitoring_loop", new_callable=AsyncMock):
            await system.initialize()

        return system

    @pytest.fixture
    def sample_alert_rule(self):
        """Sample alert rule for testing."""
        return AlertRule(
            rule_id="test_rule_001",
            name="Test Inventory Drop Rule",
            description="Test rule for inventory drop detection",
            alert_type=AlertType.INVENTORY_DROP,
            enabled=True,
            conditions={"metric": "active_listings", "comparison": "percentage_change"},
            threshold_values={"drop_percentage": 20.0, "minimum_baseline": 50},
            comparison_period="24h",
            severity=AlertSeverity.HIGH,
            delivery_channels=[AlertChannel.EMAIL, AlertChannel.WEBHOOK],
            throttle_minutes=120,
            created_by="test_user",
            created_at=datetime.now(),
        )

    @pytest.fixture
    def sample_market_data(self):
        """Sample market data points for testing."""
        base_time = datetime.now()
        return [
            MarketDataPoint(
                timestamp=base_time - timedelta(hours=2),
                neighborhood_id="test_neighborhood",
                metric_type="active_listings",
                value=200.0,
                metadata={"source": "mls", "confidence": 0.95},
            ),
            MarketDataPoint(
                timestamp=base_time - timedelta(hours=1),
                neighborhood_id="test_neighborhood",
                metric_type="active_listings",
                value=180.0,
                metadata={"source": "mls", "confidence": 0.95},
            ),
            MarketDataPoint(
                timestamp=base_time,
                neighborhood_id="test_neighborhood",
                metric_type="active_listings",
                value=150.0,  # 25% drop
                metadata={"source": "mls", "confidence": 0.95},
            ),
        ]

    @pytest.fixture
    def sample_alert_instance(self):
        """Sample alert instance for testing."""
        return AlertInstance(
            alert_id="alert_test_001",
            rule_id="test_rule_001",
            alert_type=AlertType.INVENTORY_DROP,
            severity=AlertSeverity.HIGH,
            status=AlertStatus.PENDING,
            title="Test Inventory Drop Alert",
            message="Inventory dropped significantly in test neighborhood",
            data_context={"drop_percentage": 25.0, "previous_value": 200, "current_value": 150},
            affected_areas=["test_neighborhood"],
            impact_score=85.0,
            confidence_score=0.95,
            urgency_score=78.0,
            target_users=["admin", "analyst"],
            delivery_channels=[AlertChannel.EMAIL],
            delivery_status={},
            triggered_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            recommended_actions=["Monitor market conditions", "Prepare buyers for competition"],
        )

    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """Test alert system initialization."""
        system = InventoryAlertSystem()
        system.cache = AsyncMock()

        # Mock dependencies
        with (
            patch.object(system, "_load_alert_rules", new_callable=AsyncMock),
            patch.object(system, "_create_default_alert_rules", new_callable=AsyncMock),
            patch.object(system, "_initialize_trend_analyzers", new_callable=AsyncMock),
            patch.object(system, "_monitoring_loop", new_callable=AsyncMock),
        ):
            await system.initialize()

            assert system.is_initialized
            assert system.cache is not None
            assert len(system.delivery_handlers) > 0

    @pytest.mark.asyncio
    async def test_process_market_data(self, alert_system, sample_market_data):
        """Test market data processing."""
        # Mock alert evaluation
        with patch.object(alert_system, "_evaluate_alert_conditions", new_callable=AsyncMock) as mock_evaluate:
            await alert_system.process_market_data(sample_market_data)

            mock_evaluate.assert_called_once_with(sample_market_data)

            # Check data buffer
            metric_key = "test_neighborhood:active_listings"
            assert len(alert_system.market_data_buffer[metric_key]) == 3

    @pytest.mark.asyncio
    async def test_create_alert_rule(self, alert_system, sample_alert_rule):
        """Test alert rule creation."""
        # Mock save operation
        with patch.object(alert_system, "_save_alert_rules", new_callable=AsyncMock):
            success = await alert_system.create_alert_rule(sample_alert_rule)

            assert success
            assert sample_alert_rule.rule_id in alert_system.alert_rules

    @pytest.mark.asyncio
    async def test_update_alert_rule(self, alert_system, sample_alert_rule):
        """Test alert rule updates."""
        # First create the rule
        alert_system.alert_rules[sample_alert_rule.rule_id] = sample_alert_rule

        # Mock save operation
        with patch.object(alert_system, "_save_alert_rules", new_callable=AsyncMock):
            updates = {"enabled": False, "throttle_minutes": 240}
            success = await alert_system.update_alert_rule(sample_alert_rule.rule_id, updates)

            assert success
            assert not alert_system.alert_rules[sample_alert_rule.rule_id].enabled
            assert alert_system.alert_rules[sample_alert_rule.rule_id].throttle_minutes == 240

    @pytest.mark.asyncio
    async def test_get_active_alerts_no_filter(self, alert_system, sample_alert_instance):
        """Test getting active alerts without filters."""
        # Add alert to active alerts
        alert_system.active_alerts[sample_alert_instance.alert_id] = sample_alert_instance

        alerts = await alert_system.get_active_alerts()

        assert len(alerts) == 1
        assert alerts[0].alert_id == sample_alert_instance.alert_id

    @pytest.mark.asyncio
    async def test_get_active_alerts_with_filters(self, alert_system, sample_alert_instance):
        """Test getting active alerts with filters."""
        alert_system.active_alerts[sample_alert_instance.alert_id] = sample_alert_instance

        # Filter by severity
        high_severity_alerts = await alert_system.get_active_alerts(severity_filter=AlertSeverity.HIGH)
        assert len(high_severity_alerts) == 1

        # Filter by different severity (should return empty)
        low_severity_alerts = await alert_system.get_active_alerts(severity_filter=AlertSeverity.LOW)
        assert len(low_severity_alerts) == 0

        # Filter by alert type
        inventory_alerts = await alert_system.get_active_alerts(type_filter=AlertType.INVENTORY_DROP)
        assert len(inventory_alerts) == 1

        # Filter by area
        area_alerts = await alert_system.get_active_alerts(area_filter="test_neighborhood")
        assert len(area_alerts) == 1

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, alert_system, sample_alert_instance):
        """Test alert acknowledgment."""
        alert_system.active_alerts[sample_alert_instance.alert_id] = sample_alert_instance

        success = await alert_system.acknowledge_alert(sample_alert_instance.alert_id, "test_user")

        assert success
        assert sample_alert_instance.status == AlertStatus.ACKNOWLEDGED
        assert sample_alert_instance.acknowledged_at is not None
        assert len(sample_alert_instance.action_history) > 0

    @pytest.mark.asyncio
    async def test_resolve_alert(self, alert_system, sample_alert_instance):
        """Test alert resolution."""
        alert_system.active_alerts[sample_alert_instance.alert_id] = sample_alert_instance

        success = await alert_system.resolve_alert(
            sample_alert_instance.alert_id, "test_user", "Issue resolved - market stabilized"
        )

        assert success
        assert sample_alert_instance.status == AlertStatus.RESOLVED
        assert sample_alert_instance.resolved_at is not None
        assert sample_alert_instance.alert_id not in alert_system.active_alerts
        assert len(alert_system.alert_history) > 0

    @pytest.mark.asyncio
    async def test_alert_generation_percentage_change(
        self, alert_system, sample_alert_rule, sample_market_data, sample_alert_instance
    ):
        """Test alert generation for percentage change conditions."""
        # Clear default rules and add only the test rule
        alert_system.alert_rules = {sample_alert_rule.rule_id: sample_alert_rule}

        # _evaluate_percentage_change requires at least 10 historical data points and 2+ data_points
        base_time = datetime.now()
        metric_key = "test_neighborhood:active_listings"
        for i in range(15):
            historical_point = MarketDataPoint(
                timestamp=base_time - timedelta(hours=20 - i),
                neighborhood_id="test_neighborhood",
                metric_type="active_listings",
                value=200.0,
                metadata={"source": "mls", "confidence": 0.95},
            )
            alert_system.market_data_buffer[metric_key].append(historical_point)

        # Mock alert generation and processing
        with (
            patch.object(alert_system, "_generate_alert") as mock_generate,
            patch.object(alert_system, "_process_new_alert", new_callable=AsyncMock) as mock_process,
        ):
            mock_alert = sample_alert_instance
            mock_generate.return_value = mock_alert

            # Evaluate conditions with triggering data points (need >= 2 for percentage_change)
            triggering_points = [
                MarketDataPoint(
                    timestamp=base_time - timedelta(hours=1),
                    neighborhood_id="test_neighborhood",
                    metric_type="active_listings",
                    value=160.0,
                    metadata={"source": "mls", "confidence": 0.95},
                ),
                MarketDataPoint(
                    timestamp=base_time,
                    neighborhood_id="test_neighborhood",
                    metric_type="active_listings",
                    value=150.0,  # 25% drop from 200 baseline
                    metadata={"source": "mls", "confidence": 0.95},
                ),
            ]
            await alert_system._evaluate_alert_conditions(triggering_points)

            # Should trigger alert generation
            mock_generate.assert_called_once()
            mock_process.assert_called_once_with(mock_alert, sample_alert_rule)

    @pytest.mark.asyncio
    async def test_alert_throttling(self, alert_system, sample_alert_rule):
        """Test alert rule throttling."""
        # Set recent trigger time
        sample_alert_rule.last_triggered = datetime.now() - timedelta(minutes=30)
        sample_alert_rule.throttle_minutes = 60

        # Should be throttled
        is_throttled = alert_system._is_rule_throttled(sample_alert_rule)
        assert is_throttled

        # Set older trigger time
        sample_alert_rule.last_triggered = datetime.now() - timedelta(minutes=90)

        # Should not be throttled
        is_throttled = alert_system._is_rule_throttled(sample_alert_rule)
        assert not is_throttled

    @pytest.mark.asyncio
    async def test_percentage_change_evaluation(self, alert_system, sample_alert_rule, sample_market_data):
        """Test percentage change condition evaluation."""
        # The service requires at least 10 historical data points in the buffer
        # and at least 2 data_points passed in. Generate enough historical data.
        base_time = datetime.now()
        metric_key = f"{sample_market_data[0].neighborhood_id}:{sample_market_data[0].metric_type}"

        # Add 15 historical data points with baseline value ~200
        for i in range(15):
            historical_point = MarketDataPoint(
                timestamp=base_time - timedelta(hours=20 - i),
                neighborhood_id="test_neighborhood",
                metric_type="active_listings",
                value=200.0,
                metadata={"source": "mls", "confidence": 0.95},
            )
            alert_system.market_data_buffer[metric_key].append(historical_point)

        # Test with triggering data (25% drop from baseline 200 to 150)
        triggering_points = [
            MarketDataPoint(
                timestamp=base_time - timedelta(hours=1),
                neighborhood_id="test_neighborhood",
                metric_type="active_listings",
                value=180.0,
                metadata={"source": "mls", "confidence": 0.95},
            ),
            MarketDataPoint(
                timestamp=base_time,
                neighborhood_id="test_neighborhood",
                metric_type="active_listings",
                value=150.0,
                metadata={"source": "mls", "confidence": 0.95},
            ),
        ]
        should_trigger = await alert_system._evaluate_percentage_change(sample_alert_rule, triggering_points)

        assert should_trigger  # 25% drop should trigger 20% threshold

    @pytest.mark.asyncio
    async def test_statistical_deviation_evaluation(self, alert_system, sample_alert_rule):
        """Test statistical deviation condition evaluation."""
        # Create rule for statistical deviation
        stats_rule = AlertRule(
            rule_id="stats_rule",
            name="Statistical Deviation Rule",
            description="Test statistical deviation",
            alert_type=AlertType.VELOCITY_CHANGE,
            enabled=True,
            conditions={"metric": "sales_velocity", "comparison": "statistical_deviation"},
            threshold_values={"deviation_threshold": 2.0},
            comparison_period="30d",
            severity=AlertSeverity.MEDIUM,
        )

        # Generate historical data with normal distribution
        base_time = datetime.now()
        normal_data = []
        for i in range(50):
            data_point = MarketDataPoint(
                timestamp=base_time - timedelta(hours=i),
                neighborhood_id="test_neighborhood",
                metric_type="sales_velocity",
                value=0.75 + np.random.normal(0, 0.05),  # Mean 0.75, std 0.05
                metadata={"source": "test"},
            )
            normal_data.append(data_point)

        # Add historical data
        metric_key = "test_neighborhood:sales_velocity"
        alert_system.market_data_buffer[metric_key].extend(normal_data)

        # Test with outlier value (3 standard deviations away)
        outlier_data = MarketDataPoint(
            timestamp=base_time,
            neighborhood_id="test_neighborhood",
            metric_type="sales_velocity",
            value=0.9,  # Significantly higher than normal
            metadata={"source": "test"},
        )

        should_trigger = await alert_system._evaluate_statistical_deviation(stats_rule, [outlier_data])

        assert should_trigger

    @pytest.mark.asyncio
    async def test_anomaly_detection_evaluation(self, alert_system):
        """Test anomaly detection condition evaluation."""
        # Create anomaly detection rule
        anomaly_rule = AlertRule(
            rule_id="anomaly_rule",
            name="Anomaly Detection Rule",
            description="Test anomaly detection",
            alert_type=AlertType.NEW_LISTING_FLOOD,
            enabled=True,
            conditions={"metric": "new_listings_daily", "comparison": "anomaly_detection"},
            threshold_values={"anomaly_threshold": 0.85},
            comparison_period="30d",
            severity=AlertSeverity.MEDIUM,
        )

        # Generate normal data
        base_time = datetime.now()
        normal_range = list(range(8, 16))  # Normal: 8-15 new listings
        normal_data = []

        for i in range(60):
            value = np.random.choice(normal_range)
            data_point = MarketDataPoint(
                timestamp=base_time - timedelta(hours=i),
                neighborhood_id="test_neighborhood",
                metric_type="new_listings_daily",
                value=float(value),
                metadata={"source": "test"},
            )
            normal_data.append(data_point)

        # Add historical data
        metric_key = "test_neighborhood:new_listings_daily"
        alert_system.market_data_buffer[metric_key].extend(normal_data)

        # Test with anomalous value
        anomaly_data = MarketDataPoint(
            timestamp=base_time,
            neighborhood_id="test_neighborhood",
            metric_type="new_listings_daily",
            value=50.0,  # Way outside normal range
            metadata={"source": "test"},
        )

        should_trigger = await alert_system._evaluate_anomaly_detection(anomaly_rule, [anomaly_data])

        assert should_trigger

    @pytest.mark.asyncio
    async def test_alert_delivery_email(self, alert_system, sample_alert_instance):
        """Test email alert delivery."""
        with patch.object(alert_system, "_send_email_alert", new_callable=AsyncMock) as mock_send:
            await alert_system._send_email_alert(sample_alert_instance)
            mock_send.assert_called_once_with(sample_alert_instance)

    @pytest.mark.asyncio
    async def test_alert_delivery_multiple_channels(self, alert_system, sample_alert_instance):
        """Test multi-channel alert delivery."""
        # Set multiple delivery channels
        sample_alert_instance.delivery_channels = [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.WEBHOOK]

        # Mock delivery handlers in the handler dict (not just methods)
        mock_email = AsyncMock()
        mock_sms = AsyncMock()
        mock_webhook = AsyncMock()
        alert_system.delivery_handlers[AlertChannel.EMAIL] = mock_email
        alert_system.delivery_handlers[AlertChannel.SMS] = mock_sms
        alert_system.delivery_handlers[AlertChannel.WEBHOOK] = mock_webhook

        await alert_system._deliver_alert(sample_alert_instance)

        # All channels should be called
        mock_email.assert_called_once()
        mock_sms.assert_called_once()
        mock_webhook.assert_called_once()

        # Check delivery status
        assert "email" in sample_alert_instance.delivery_status
        assert "sms" in sample_alert_instance.delivery_status
        assert "webhook" in sample_alert_instance.delivery_status

    @pytest.mark.asyncio
    async def test_alert_delivery_failure_handling(self, alert_system, sample_alert_instance):
        """Test alert delivery failure handling."""
        sample_alert_instance.delivery_channels = [AlertChannel.EMAIL]

        # Mock delivery failure in the handler dict
        mock_failing_handler = AsyncMock(side_effect=Exception("Delivery failed"))
        alert_system.delivery_handlers[AlertChannel.EMAIL] = mock_failing_handler

        await alert_system._deliver_alert(sample_alert_instance)

        # Should record failure in delivery status
        assert sample_alert_instance.delivery_status["email"]["status"] == "failed"
        assert "Delivery failed" in sample_alert_instance.delivery_status["email"]["error"]

    @pytest.mark.asyncio
    async def test_get_alert_analytics(self, alert_system):
        """Test alert analytics generation."""
        # Create historical alerts
        base_time = datetime.now()
        for i in range(10):
            alert = AlertInstance(
                alert_id=f"alert_{i}",
                rule_id="test_rule",
                alert_type=AlertType.INVENTORY_DROP,
                severity=AlertSeverity.HIGH if i % 2 == 0 else AlertSeverity.MEDIUM,
                status=AlertStatus.RESOLVED if i < 5 else AlertStatus.ACKNOWLEDGED,
                title=f"Test Alert {i}",
                message=f"Alert message {i}",
                data_context={},
                affected_areas=["area_1", "area_2"],
                impact_score=80.0,
                confidence_score=0.9,
                urgency_score=75.0,
                target_users=["admin"],
                delivery_channels=[AlertChannel.EMAIL],
                delivery_status={},
                triggered_at=base_time - timedelta(days=i),
                acknowledged_at=base_time - timedelta(days=i, hours=1),
                resolved_at=base_time - timedelta(days=i, hours=2) if i < 5 else None,
            )
            alert_system.alert_history.append(alert)

        analytics = await alert_system.get_alert_analytics(period_days=30)

        assert analytics["total_alerts"] == 10
        assert "alerts_by_type" in analytics
        assert "alerts_by_severity" in analytics
        assert analytics["resolution_rate"] > 0

    @pytest.mark.asyncio
    async def test_default_alert_rules_creation(self, alert_system):
        """Test creation of default alert rules."""
        # Clear existing rules
        alert_system.alert_rules = {}

        # Mock save operation
        with patch.object(alert_system, "_save_alert_rules", new_callable=AsyncMock):
            await alert_system._create_default_alert_rules()

            assert len(alert_system.alert_rules) > 0
            assert any(rule.alert_type == AlertType.INVENTORY_DROP for rule in alert_system.alert_rules.values())
            assert any(rule.alert_type == AlertType.PRICE_SPIKE for rule in alert_system.alert_rules.values())

    @pytest.mark.asyncio
    async def test_trend_analysis(self, alert_system):
        """Test trend analysis functionality."""
        # Create sample data points
        data_points = []
        base_time = datetime.now()
        values = [100, 105, 103, 108, 110, 115, 112, 118, 120]

        for i, value in enumerate(values):
            data_point = MarketDataPoint(
                timestamp=base_time - timedelta(hours=len(values) - i),
                neighborhood_id="test_neighborhood",
                metric_type="median_price",
                value=float(value * 1000),  # Convert to realistic price
                metadata={"source": "test"},
            )
            data_points.append(data_point)

        # Test trend analysis
        trend = await alert_system._analyze_inventory_trends(data_points)

        assert isinstance(trend, TrendAnalysis)
        assert trend.metric_name == "inventory"
        assert trend.trend_direction in ["up", "down", "stable"]
        assert trend.change_magnitude >= 0

    @pytest.mark.asyncio
    async def test_performance_metrics_update(self, alert_system):
        """Test performance metrics updating."""
        # Initialize metrics
        initial_alerts_generated = alert_system.alert_metrics["alerts_generated"]

        # Mock alert processing that updates metrics
        alert_system.alert_metrics["alerts_generated"] += 5
        alert_system.alert_metrics["alerts_sent"] += 4

        await alert_system._update_performance_metrics()

        assert alert_system.alert_metrics["alerts_generated"] == initial_alerts_generated + 5
        assert alert_system.alert_metrics["alerts_sent"] == 4

    @pytest.mark.asyncio
    async def test_expired_alerts_cleanup(self, alert_system, sample_alert_instance):
        """Test cleanup of expired alerts."""
        # Create expired alert
        expired_alert = sample_alert_instance
        expired_alert.expires_at = datetime.now() - timedelta(hours=1)
        alert_system.active_alerts[expired_alert.alert_id] = expired_alert

        # Run cleanup
        await alert_system._cleanup_expired_alerts()

        # Alert should be moved to history
        assert expired_alert.alert_id not in alert_system.active_alerts
        assert len(alert_system.alert_history) > 0

    @pytest.mark.asyncio
    async def test_geographic_filter_matching(self, alert_system):
        """Test geographic filter matching."""
        data_point = MarketDataPoint(
            timestamp=datetime.now(),
            neighborhood_id="included_area",
            metric_type="test_metric",
            value=100.0,
            metadata={},
        )

        # Test included areas filter
        geo_filter = {"included_areas": ["included_area", "other_area"]}
        matches = alert_system._matches_geographic_filter(data_point, geo_filter)
        assert matches

        # Test excluded areas filter
        geo_filter = {"excluded_areas": ["excluded_area"]}
        matches = alert_system._matches_geographic_filter(data_point, geo_filter)
        assert matches

        # Test excluded areas filter with excluded area
        geo_filter = {"excluded_areas": ["included_area"]}
        matches = alert_system._matches_geographic_filter(data_point, geo_filter)
        assert not matches

    def test_singleton_alert_system_instance(self):
        """Test singleton pattern for alert system instance."""
        assert callable(get_inventory_alert_system)

    @pytest.mark.asyncio
    async def test_concurrent_alert_processing(self, alert_system, sample_market_data):
        """Test concurrent alert processing."""
        # Create multiple concurrent data processing tasks
        tasks = []
        for i in range(5):
            # Create different market data for each task
            data_batch = []
            for data_point in sample_market_data:
                new_point = MarketDataPoint(
                    timestamp=data_point.timestamp,
                    neighborhood_id=f"area_{i}",
                    metric_type=data_point.metric_type,
                    value=data_point.value,
                    metadata=data_point.metadata,
                )
                data_batch.append(new_point)

            task = asyncio.create_task(alert_system.process_market_data(data_batch))
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        # Should process all data without errors
        assert len(alert_system.market_data_buffer) >= 5

    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, alert_system):
        """Test memory usage optimization with large data volumes."""
        # Generate large amount of market data
        base_time = datetime.now()
        large_data_set = []

        for i in range(2000):  # 2000 data points
            data_point = MarketDataPoint(
                timestamp=base_time - timedelta(minutes=i),
                neighborhood_id="memory_test",
                metric_type="test_metric",
                value=float(100 + i % 50),
                metadata={"source": "test"},
            )
            large_data_set.append(data_point)

        # Process data in batches
        batch_size = 100
        for i in range(0, len(large_data_set), batch_size):
            batch = large_data_set[i : i + batch_size]
            await alert_system.process_market_data(batch)

        # Check buffer size limit (should be maintained at 1000)
        metric_key = "memory_test:test_metric"
        assert len(alert_system.market_data_buffer[metric_key]) <= 1000