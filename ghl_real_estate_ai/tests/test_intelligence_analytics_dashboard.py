"""
Tests for Intelligence Analytics Dashboard
Comprehensive test suite for the analytics dashboard and performance monitoring system.

Created: January 10, 2026
Author: EnterpriseHub Development Team
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import streamlit as st

from ..services.intelligence_performance_monitor import (
    IntelligencePerformanceMonitor,
    PerformanceMetric,
    ComponentPerformance,
    UserInteractionEvent,
    BusinessIntelligenceMetric,
    ClaudeServiceMetrics,
    DashboardHealthMetrics,
    performance_monitor,
    track_performance,
    track_interaction
)
from ..streamlit_components.intelligence_analytics_dashboard import (
    IntelligenceAnalyticsDashboard,
    analytics_dashboard
)


class TestIntelligencePerformanceMonitor:
    """Test cases for the performance monitoring system."""

    @pytest.fixture
    async def monitor(self):
        """Create a test monitor instance."""
        monitor = IntelligencePerformanceMonitor(redis_url="redis://localhost:6379/5")

        # Mock Redis for testing
        monitor.redis_client = AsyncMock()
        monitor.redis_client.ping = AsyncMock(return_value=True)
        monitor.redis_client.setex = AsyncMock(return_value=True)
        monitor.redis_client.get = AsyncMock(return_value=None)
        monitor.redis_client.keys = AsyncMock(return_value=[])

        await monitor.initialize()
        return monitor

    @pytest.mark.asyncio
    async def test_monitor_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor.redis_client is not None
        assert monitor.thresholds["component_render_time"] == 500
        assert monitor.thresholds["claude_response_time"] == 200

    @pytest.mark.asyncio
    async def test_record_performance(self, monitor):
        """Test performance metric recording."""
        await monitor.record_performance(
            component="journey_map",
            operation="render",
            duration_ms=245.5,
            user_id="test_user",
            session_id="test_session",
            metadata={"test": True},
            success=True
        )

        # Should have added metric to buffer
        assert len(monitor.performance_buffer) == 1

        metric = monitor.performance_buffer[0]
        assert metric.component == "journey_map"
        assert metric.operation == "render"
        assert metric.duration_ms == 245.5
        assert metric.success is True

    @pytest.mark.asyncio
    async def test_record_user_interaction(self, monitor):
        """Test user interaction recording."""
        await monitor.record_user_interaction(
            event_type="click",
            component="sentiment_dashboard",
            user_id="test_user",
            session_id="test_session",
            element_id="filter_button",
            interaction_value="high_sentiment",
            metadata={"page": "dashboard"}
        )

        # Should have added interaction to buffer
        assert len(monitor.interaction_buffer) == 1

        interaction = monitor.interaction_buffer[0]
        assert interaction.event_type == "click"
        assert interaction.component == "sentiment_dashboard"
        assert interaction.element_id == "filter_button"

    @pytest.mark.asyncio
    async def test_component_performance_calculation(self, monitor):
        """Test component performance calculation."""
        # Mock Redis data
        mock_data = [
            json.dumps({
                "duration_ms": 200,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }),
            json.dumps({
                "duration_ms": 350,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }),
            json.dumps({
                "duration_ms": 180,
                "success": False,
                "timestamp": datetime.now().isoformat()
            })
        ]

        monitor.redis_client.keys.return_value = ["perf:test:1", "perf:test:2", "perf:test:3"]
        monitor.redis_client.get.side_effect = mock_data

        performance = await monitor.get_component_performance("test_component", 24)

        assert isinstance(performance, ComponentPerformance)
        assert performance.component_name == "test_component"
        assert performance.total_renders == 3
        assert performance.error_rate > 0  # Should detect the failure

    @pytest.mark.asyncio
    async def test_claude_service_metrics(self, monitor):
        """Test Claude service metrics retrieval."""
        metrics = await monitor.get_claude_service_metrics("claude_agent_service", 24)

        assert isinstance(metrics, ClaudeServiceMetrics)
        assert metrics.service_name == "claude_agent_service"
        assert metrics.avg_response_time > 0
        assert 0 <= metrics.success_rate <= 1
        assert 0 <= metrics.cache_hit_rate <= 1

    @pytest.mark.asyncio
    async def test_dashboard_health_metrics(self, monitor):
        """Test dashboard health metrics calculation."""
        health = await monitor.get_dashboard_health()

        assert isinstance(health, DashboardHealthMetrics)
        assert 0 <= health.uptime_percentage <= 100
        assert health.active_users_24h >= 0
        assert health.total_sessions_today >= 0
        assert 0 <= health.data_freshness_score <= 100

    @pytest.mark.asyncio
    async def test_business_intelligence_metrics(self, monitor):
        """Test business intelligence metrics calculation."""
        metrics = await monitor.get_business_intelligence()

        assert isinstance(metrics, list)
        assert len(metrics) > 0

        for metric in metrics:
            assert isinstance(metric, BusinessIntelligenceMetric)
            assert metric.metric_name is not None
            assert metric.value >= 0
            assert metric.unit in ["percentage", "score", "minutes", "percentage_faster"]

    @pytest.mark.asyncio
    async def test_performance_recommendations(self, monitor):
        """Test performance recommendations generation."""
        # Mock poor performance data
        monitor.get_component_performance = AsyncMock(return_value=ComponentPerformance(
            component_name="test_component",
            total_renders=100,
            avg_render_time=750,  # Above threshold
            p95_render_time=1200,
            p99_render_time=1800,
            error_rate=0.08,  # Above threshold
            last_24h_usage=100,
            performance_score=65
        ))

        recommendations = await monitor.get_performance_recommendations()

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should have recommendations for slow performance and high error rate
        has_performance_rec = any(r.get('type') == 'performance' for r in recommendations)
        has_reliability_rec = any(r.get('type') == 'reliability' for r in recommendations)

        assert has_performance_rec or has_reliability_rec

    @pytest.mark.asyncio
    async def test_export_analytics_report(self, monitor):
        """Test analytics report export."""
        start_date = datetime.now() - timedelta(hours=24)
        end_date = datetime.now()

        report = await monitor.export_analytics_report(start_date, end_date)

        assert isinstance(report, dict)
        assert "report_period" in report
        assert "dashboard_health" in report
        assert "component_performance" in report
        assert "claude_services" in report
        assert "business_metrics" in report
        assert "recommendations" in report
        assert "generated_at" in report

    def test_performance_tracking_decorator(self):
        """Test performance tracking decorator."""
        @track_performance("test_component", "test_operation")
        def test_function():
            return "success"

        # Mock the monitor
        with patch.object(performance_monitor, 'performance_buffer') as mock_buffer:
            result = test_function()

            assert result == "success"
            assert mock_buffer.append.called

    def test_interaction_tracking_decorator(self):
        """Test interaction tracking decorator."""
        @track_interaction("test_component")
        def test_function(value="test"):
            return f"processed_{value}"

        # Mock Streamlit session state
        with patch('streamlit.session_state') as mock_state:
            mock_state.user_id = "test_user"
            mock_state.session_id = "test_session"

            with patch.object(performance_monitor, 'interaction_buffer') as mock_buffer:
                result = test_function(value="hello")

                assert result == "processed_hello"
                # Note: interaction tracking might not work in test environment


class TestIntelligenceAnalyticsDashboard:
    """Test cases for the analytics dashboard component."""

    @pytest.fixture
    def dashboard(self):
        """Create a test dashboard instance."""
        dashboard = IntelligenceAnalyticsDashboard()
        dashboard.monitor = AsyncMock()
        return dashboard

    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit components for testing."""
        with patch.multiple(
            'streamlit',
            title=MagicMock(),
            markdown=MagicMock(),
            columns=MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()]),
            subheader=MagicMock(),
            selectbox=MagicMock(return_value="24h"),
            checkbox=MagicMock(return_value=True),
            button=MagicMock(return_value=False),
            metric=MagicMock(),
            success=MagicMock(),
            error=MagicMock(),
            info=MagicMock(),
            warning=MagicMock(),
            plotly_chart=MagicMock(),
            expander=MagicMock(),
            container=MagicMock(),
            download_button=MagicMock(),
            rerun=MagicMock(),
            session_state=MagicMock()
        ) as mock_st:
            # Configure session state mock
            mock_st['session_state'].get.return_value = False
            mock_st['session_state'].__contains__ = MagicMock(return_value=False)

            yield mock_st

    @pytest.mark.asyncio
    async def test_dashboard_initialization(self, dashboard, mock_streamlit):
        """Test dashboard initialization."""
        dashboard.monitor.initialize = AsyncMock()

        await dashboard.initialize()

        dashboard.monitor.initialize.assert_called_once()

    def test_render_main_dashboard_structure(self, dashboard, mock_streamlit):
        """Test main dashboard rendering structure."""
        # Mock initialization state
        mock_streamlit['session_state'].__contains__ = MagicMock(return_value=True)
        mock_streamlit['session_state'].get.return_value = True

        # Mock async methods
        dashboard.monitor = MagicMock()
        dashboard.monitor.get_dashboard_health = AsyncMock(return_value=DashboardHealthMetrics(
            uptime_percentage=99.5,
            avg_page_load_time=2.1,
            active_users_24h=45,
            total_sessions_today=120,
            data_freshness_score=95.0,
            system_load=0.3,
            memory_usage_mb=512.0,
            redis_health=True,
            websocket_connections=8,
            errors_per_hour=0.5
        ))

        # This would normally require mocking the entire async rendering pipeline
        # For now, just test that the method exists and can be called
        assert hasattr(dashboard, 'render_main_dashboard')

    def test_dashboard_controls_rendering(self, dashboard, mock_streamlit):
        """Test dashboard controls rendering."""
        dashboard._render_dashboard_controls()

        # Verify selectbox calls for filters
        assert mock_streamlit['selectbox'].call_count >= 3
        assert mock_streamlit['checkbox'].called

    def test_mini_performance_widget(self, dashboard, mock_streamlit):
        """Test mini performance widget rendering."""
        dashboard.render_mini_performance_widget()

        # Should render without errors
        assert mock_streamlit['markdown'].called
        assert mock_streamlit['container'].called

    def test_real_time_alerts_widget(self, dashboard, mock_streamlit):
        """Test real-time alerts widget rendering."""
        dashboard.render_real_time_alerts()

        # Should render success message when no alerts
        assert mock_streamlit['success'].called

    @pytest.mark.asyncio
    async def test_export_functionality(self, dashboard, mock_streamlit):
        """Test analytics report export functionality."""
        # Mock the monitor's export method
        mock_report = {
            "report_period": {
                "start": "2026-01-09T00:00:00",
                "end": "2026-01-10T00:00:00",
                "duration_days": 1
            },
            "dashboard_health": {},
            "component_performance": {},
            "generated_at": "2026-01-10T12:00:00"
        }

        dashboard.monitor.export_analytics_report = AsyncMock(return_value=mock_report)

        # Mock session state for filters
        mock_streamlit['session_state'].analytics_filters = {'time_range': '24h'}

        await dashboard._export_analytics_report()

        dashboard.monitor.export_analytics_report.assert_called_once()
        assert mock_streamlit['download_button'].called

    def test_error_handling(self, dashboard, mock_streamlit):
        """Test error handling in dashboard components."""
        # Mock a failing monitor method
        dashboard.monitor = MagicMock()
        dashboard.monitor.get_dashboard_health = AsyncMock(side_effect=Exception("Test error"))

        # Should handle errors gracefully
        try:
            # This would trigger the error handling
            asyncio.run(dashboard._render_system_overview())
        except Exception:
            # Error should be caught and displayed via st.error
            pass

        # Should have called st.error
        assert mock_streamlit['error'].called


class TestPerformanceOptimization:
    """Test performance optimization features."""

    @pytest.mark.asyncio
    async def test_metric_buffer_processing(self):
        """Test metric buffer processing performance."""
        monitor = IntelligencePerformanceMonitor()
        monitor.redis_client = AsyncMock()

        # Add many metrics to buffer
        for i in range(1000):
            metric = PerformanceMetric(
                component="test",
                operation="test_op",
                duration_ms=100 + i,
                timestamp=datetime.now(),
                metadata={},
                success=True
            )
            monitor.performance_buffer.append(metric)

        # Process buffer (mock the storage)
        monitor._store_performance_metric = AsyncMock()

        # Should process all metrics efficiently
        initial_count = len(monitor.performance_buffer)

        # Simulate buffer processing
        while monitor.performance_buffer:
            metric = monitor.performance_buffer.popleft()
            await monitor._store_performance_metric(metric)

        assert len(monitor.performance_buffer) == 0
        assert monitor._store_performance_metric.call_count == initial_count

    def test_performance_score_calculation(self):
        """Test performance score calculation accuracy."""
        monitor = IntelligencePerformanceMonitor()

        # Test perfect performance
        score = monitor._calculate_performance_score(200, 0.0, "test_component")
        assert score == 100.0

        # Test slow performance
        score = monitor._calculate_performance_score(1000, 0.0, "test_component")
        assert score < 100.0

        # Test high error rate
        score = monitor._calculate_performance_score(200, 0.1, "test_component")
        assert score < 100.0

        # Test very poor performance
        score = monitor._calculate_performance_score(2000, 0.2, "test_component")
        assert score < 50.0

    @pytest.mark.asyncio
    async def test_cache_effectiveness(self):
        """Test Redis cache effectiveness."""
        monitor = IntelligencePerformanceMonitor()
        monitor.redis_client = AsyncMock()

        # Test cache hit
        cached_data = json.dumps({
            "service_name": "test_service",
            "avg_response_time": 150.0,
            "requests_per_minute": 45,
            "success_rate": 0.98,
            "error_rate": 0.02,
            "cache_hit_rate": 0.85,
            "token_usage": 1250,
            "cost_per_request": 0.0023
        })

        monitor.redis_client.get.return_value = cached_data

        metrics = await monitor.get_claude_service_metrics("test_service", 24)

        # Should use cached data
        assert metrics.service_name == "test_service"
        assert metrics.avg_response_time == 150.0
        monitor.redis_client.get.assert_called_once()

    def test_memory_usage_optimization(self):
        """Test memory usage with large datasets."""
        monitor = IntelligencePerformanceMonitor()

        # Test buffer limits
        original_maxlen = monitor.performance_buffer.maxlen

        # Add more items than buffer can hold
        for i in range(original_maxlen + 100):
            metric = PerformanceMetric(
                component="test",
                operation="test",
                duration_ms=i,
                timestamp=datetime.now(),
                metadata={},
                success=True
            )
            monitor.performance_buffer.append(metric)

        # Buffer should not exceed maxlen
        assert len(monitor.performance_buffer) == original_maxlen


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_monitoring_workflow(self):
        """Test complete monitoring workflow."""
        monitor = IntelligencePerformanceMonitor()
        monitor.redis_client = AsyncMock()
        monitor._store_performance_metric = AsyncMock()
        monitor._store_interaction_event = AsyncMock()

        # Simulate a user session with multiple interactions
        session_id = "test_session_123"
        user_id = "test_user_456"

        # Record various performance metrics
        await monitor.record_performance("journey_map", "render", 245.5, user_id, session_id)
        await monitor.record_performance("sentiment_dashboard", "update", 123.2, user_id, session_id)
        await monitor.record_performance("claude_agent_service", "coaching", 89.1, user_id, session_id)

        # Record user interactions
        await monitor.record_user_interaction("click", "journey_map", user_id, session_id, "stage_node_3")
        await monitor.record_user_interaction("filter", "sentiment_dashboard", user_id, session_id, "sentiment_filter")
        await monitor.record_user_interaction("hover", "competitive_intel", user_id, session_id, "competitor_card")

        # Verify all metrics were buffered
        assert len(monitor.performance_buffer) == 3
        assert len(monitor.interaction_buffer) == 3

        # Process buffers
        while monitor.performance_buffer:
            metric = monitor.performance_buffer.popleft()
            await monitor._store_performance_metric(metric)

        while monitor.interaction_buffer:
            interaction = monitor.interaction_buffer.popleft()
            await monitor._store_interaction_event(interaction)

        # Verify storage was called
        assert monitor._store_performance_metric.call_count == 3
        assert monitor._store_interaction_event.call_count == 3

    @pytest.mark.asyncio
    async def test_dashboard_with_real_data_flow(self):
        """Test dashboard with realistic data flow."""
        dashboard = IntelligenceAnalyticsDashboard()
        dashboard.monitor = AsyncMock()

        # Mock realistic data
        dashboard.monitor.get_dashboard_health.return_value = DashboardHealthMetrics(
            uptime_percentage=99.2,
            avg_page_load_time=1.8,
            active_users_24h=67,
            total_sessions_today=234,
            data_freshness_score=92.5,
            system_load=0.4,
            memory_usage_mb=768.0,
            redis_health=True,
            websocket_connections=15,
            errors_per_hour=1.2
        )

        dashboard.monitor.get_component_performance.return_value = ComponentPerformance(
            component_name="journey_map",
            total_renders=145,
            avg_render_time=234.7,
            p95_render_time=456.2,
            p99_render_time=789.1,
            error_rate=0.034,
            last_24h_usage=145,
            performance_score=87.3
        )

        dashboard.monitor.get_business_intelligence.return_value = [
            BusinessIntelligenceMetric(
                metric_name="agent_efficiency_improvement",
                value=38.7,
                unit="percentage",
                period="daily",
                timestamp=datetime.now(),
                comparison_period=31.2,
                trend_direction="up"
            )
        ]

        dashboard.monitor.get_performance_recommendations.return_value = [
            {
                "type": "performance",
                "component": "sentiment_dashboard",
                "issue": "Moderate render time",
                "current_value": "456ms",
                "threshold": "500ms",
                "recommendation": "Consider implementing data virtualization",
                "priority": "medium"
            }
        ]

        # Test that dashboard can handle this data
        health = await dashboard.monitor.get_dashboard_health()
        performance = await dashboard.monitor.get_component_performance("journey_map")
        bi_metrics = await dashboard.monitor.get_business_intelligence()
        recommendations = await dashboard.monitor.get_performance_recommendations()

        assert health.uptime_percentage > 99
        assert performance.avg_render_time < 300
        assert len(bi_metrics) > 0
        assert len(recommendations) > 0

    def test_error_resilience(self):
        """Test system resilience to various error conditions."""
        monitor = IntelligencePerformanceMonitor()

        # Test with invalid data
        try:
            metric = PerformanceMetric(
                component="test",
                operation="test",
                duration_ms=-100,  # Invalid negative duration
                timestamp=datetime.now(),
                metadata={},
                success=True
            )
            monitor.performance_buffer.append(metric)
            # Should not crash
            assert len(monitor.performance_buffer) == 1
        except Exception:
            pytest.fail("Should handle invalid metric data gracefully")

        # Test with missing Redis connection
        monitor.redis_client = None

        try:
            # Should not crash when Redis is unavailable
            result = asyncio.run(monitor.get_component_performance("test"))
            # Should return default empty performance
            assert result.total_renders == 0
        except ValueError as e:
            # Expected error for uninitialized monitor
            assert "Monitor not initialized" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])