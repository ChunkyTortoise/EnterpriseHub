"""
Admin dashboard tests for multi-tenant memory system.

Tests cover:
- Admin interface functionality and rendering
- Tenant performance monitoring and analytics
- Claude configuration management
- System health monitoring and alerting
- Memory analytics dashboard
- Real-time metrics and visualization
- Multi-tenant administration features
"""

import asyncio
import pytest
import uuid
import json
import streamlit as st
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any

# Test imports with fallback for different execution contexts
try:
    from ghl_real_estate_ai.streamlit_components.unified_multi_tenant_admin import UnifiedMultiTenantAdmin
    from ghl_real_estate_ai.services.enhanced_memory_service import EnhancedMemoryService
    from ghl_real_estate_ai.database.connection import EnhancedDatabasePool
    from ghl_real_estate_ai.database.redis_client import EnhancedRedisClient
except ImportError:
    try:
        from streamlit_components.unified_multi_tenant_admin import UnifiedMultiTenantAdmin
        from services.enhanced_memory_service import EnhancedMemoryService
        from database.connection import EnhancedDatabasePool
        from database.redis_client import EnhancedRedisClient
    except ImportError:
        # Mock for testing environment
        UnifiedMultiTenantAdmin = Mock
        EnhancedMemoryService = Mock
        EnhancedDatabasePool = Mock
        EnhancedRedisClient = Mock

@pytest.fixture
def admin_dashboard():
    """Create admin dashboard instance for testing"""
    return UnifiedMultiTenantAdmin()

@pytest.fixture
def mock_tenant_data():
    """Mock tenant data for dashboard testing"""
    return [
        {
            "id": "tenant_1",
            "name": "Sunrise Realty",
            "location_id": "loc_12345",
            "active_conversations": 45,
            "memory_learning_rate": 0.87,
            "behavioral_data_points": 2150,
            "claude_avg_response_ms": 145,
            "conversion_rate": 0.23,
            "lead_score_avg": 78.5,
            "qualification_completion_rate": 0.91,
            "property_match_satisfaction": 0.89,
            "last_activity": datetime.now() - timedelta(minutes=5)
        },
        {
            "id": "tenant_2",
            "name": "Metro Properties",
            "location_id": "loc_67890",
            "active_conversations": 32,
            "memory_learning_rate": 0.92,
            "behavioral_data_points": 1840,
            "claude_avg_response_ms": 132,
            "conversion_rate": 0.28,
            "lead_score_avg": 82.1,
            "qualification_completion_rate": 0.94,
            "property_match_satisfaction": 0.92,
            "last_activity": datetime.now() - timedelta(minutes=2)
        },
        {
            "id": "tenant_3",
            "name": "Elite Homes",
            "location_id": "loc_54321",
            "active_conversations": 67,
            "memory_learning_rate": 0.83,
            "behavioral_data_points": 3420,
            "claude_avg_response_ms": 167,
            "conversion_rate": 0.19,
            "lead_score_avg": 75.2,
            "qualification_completion_rate": 0.88,
            "property_match_satisfaction": 0.86,
            "last_activity": datetime.now() - timedelta(minutes=8)
        }
    ]

@pytest.fixture
def mock_system_health():
    """Mock system health data for testing"""
    return {
        "database": {
            "status": "healthy",
            "connection_pool_size": 15,
            "active_connections": 8,
            "query_avg_time_ms": 12.5,
            "slow_query_count": 2,
            "error_rate_5m": 0.001
        },
        "redis": {
            "status": "healthy",
            "memory_usage_mb": 245,
            "hit_rate": 0.91,
            "operations_per_second": 1250,
            "connection_pool_size": 20,
            "active_connections": 12
        },
        "claude_apis": [
            {
                "tenant_id": "tenant_1",
                "status": "healthy",
                "avg_response_time_ms": 145,
                "requests_per_minute": 85,
                "error_rate_5m": 0.002,
                "rate_limit_usage": 0.45
            },
            {
                "tenant_id": "tenant_2",
                "status": "healthy",
                "avg_response_time_ms": 132,
                "requests_per_minute": 72,
                "error_rate_5m": 0.001,
                "rate_limit_usage": 0.38
            }
        ],
        "memory": {
            "status": "healthy",
            "cache_hit_rate": 0.88,
            "behavioral_learning_accuracy": 0.94,
            "data_consistency_score": 0.97,
            "storage_growth_rate_mb_day": 15.2
        }
    }

class TestAdminDashboardCore:
    """Test core admin dashboard functionality"""

    def test_admin_dashboard_initialization(self, admin_dashboard):
        """Test admin dashboard initialization and configuration"""

        assert admin_dashboard is not None
        assert hasattr(admin_dashboard, 'render_tenant_performance_overview')
        assert hasattr(admin_dashboard, 'render_claude_configuration_manager')
        assert hasattr(admin_dashboard, 'render_memory_analytics_dashboard')
        assert hasattr(admin_dashboard, 'render_system_health_monitoring')

    @patch('streamlit.title')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    def test_tenant_performance_overview_rendering(self, mock_metric, mock_columns, mock_title, admin_dashboard, mock_tenant_data):
        """Test tenant performance overview rendering"""

        # Mock Streamlit components
        mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]

        with patch.object(admin_dashboard, 'load_all_tenants', return_value=mock_tenant_data):
            admin_dashboard.render_tenant_performance_overview()

            # Verify page structure
            mock_title.assert_called_with("🏢 Multi-Tenant Performance Dashboard")
            mock_columns.assert_called_with(4)

            # Verify metrics rendering
            assert mock_metric.call_count >= 4  # At least 4 main metrics

            # Verify metric calculations
            expected_total_conversations = sum(t["active_conversations"] for t in mock_tenant_data)
            expected_avg_memory_rate = sum(t["memory_learning_rate"] for t in mock_tenant_data) / len(mock_tenant_data)

            metric_calls = mock_metric.call_args_list
            conversation_metric = next((call for call in metric_calls if "Active Conversations" in str(call)), None)
            assert conversation_metric is not None

    @patch('streamlit.selectbox')
    @patch('streamlit.expander')
    def test_claude_configuration_manager(self, mock_expander, mock_selectbox, admin_dashboard, mock_tenant_data):
        """Test Claude configuration management interface"""

        # Mock UI components
        mock_selectbox.return_value = "Sunrise Realty"
        mock_expander_instance = Mock()
        mock_expander.return_value.__enter__ = Mock(return_value=mock_expander_instance)
        mock_expander.return_value.__exit__ = Mock(return_value=None)

        with patch.object(admin_dashboard, 'load_all_tenants', return_value=mock_tenant_data), \
             patch.object(admin_dashboard, 'get_tenant_by_name', return_value=mock_tenant_data[0]):

            admin_dashboard.render_claude_configuration_manager()

            # Verify tenant selection
            mock_selectbox.assert_called_once()
            call_args = mock_selectbox.call_args
            assert "Select Tenant" in call_args[0][0]

            # Verify configuration sections
            expander_calls = mock_expander.call_args_list
            expected_sections = ["🔑 API Configuration", "📝 System Prompts", "🧪 A/B Testing", "📊 Claude Performance"]

            for section in expected_sections:
                section_found = any(section in str(call) for call in expander_calls)
                assert section_found, f"Section {section} not found in expanders"

    @patch('streamlit.tabs')
    def test_memory_analytics_dashboard(self, mock_tabs, admin_dashboard):
        """Test memory analytics dashboard rendering"""

        # Mock tabs component
        mock_tab_instances = [Mock(), Mock(), Mock(), Mock()]
        mock_tabs.return_value = mock_tab_instances

        admin_dashboard.render_memory_analytics_dashboard()

        # Verify tab structure
        mock_tabs.assert_called_once()
        call_args = mock_tabs.call_args[0][0]
        expected_tabs = ["Conversation Memory", "Behavioral Learning", "Storage Analytics", "Learning Insights"]

        assert call_args == expected_tabs

    @patch('streamlit.button')
    @patch('time.sleep')
    @patch('streamlit.rerun')
    def test_system_health_monitoring(self, mock_rerun, mock_sleep, mock_button, admin_dashboard, mock_system_health):
        """Test system health monitoring interface"""

        # Mock auto-refresh functionality
        mock_button.return_value = True

        with patch.object(admin_dashboard, 'get_real_time_health_metrics', return_value=mock_system_health):
            admin_dashboard.render_system_health_monitoring()

            # Verify auto-refresh functionality
            mock_button.assert_called_with("🔄 Auto-refresh")

    def test_tenant_comparison_charts_data_processing(self, admin_dashboard, mock_tenant_data):
        """Test tenant comparison charts data processing"""

        with patch.object(admin_dashboard, 'render_tenant_comparison_charts') as mock_charts:
            # Process tenant data for charts
            chart_data = admin_dashboard._prepare_tenant_comparison_data(mock_tenant_data)

            # Verify data structure
            assert "tenant_names" in chart_data
            assert "conversion_rates" in chart_data
            assert "memory_learning_rates" in chart_data
            assert "avg_response_times" in chart_data

            # Verify data accuracy
            assert len(chart_data["tenant_names"]) == len(mock_tenant_data)
            assert chart_data["conversion_rates"][0] == mock_tenant_data[0]["conversion_rate"]

class TestAdminDashboardInteractivity:
    """Test admin dashboard interactive features"""

    @patch('streamlit.session_state')
    @patch('streamlit.selectbox')
    def test_tenant_selection_and_filtering(self, mock_selectbox, mock_session_state, admin_dashboard, mock_tenant_data):
        """Test tenant selection and filtering functionality"""

        # Mock session state
        mock_session_state.selected_tenant = "tenant_1"
        mock_selectbox.return_value = "Sunrise Realty"

        with patch.object(admin_dashboard, 'load_all_tenants', return_value=mock_tenant_data):
            selected_tenant = admin_dashboard.handle_tenant_selection()

            assert selected_tenant["name"] == "Sunrise Realty"
            assert selected_tenant["id"] == "tenant_1"

    @patch('streamlit.slider')
    @patch('streamlit.date_input')
    def test_time_range_filtering(self, mock_date_input, mock_slider, admin_dashboard):
        """Test time range filtering for analytics"""

        # Mock date range selection
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        mock_date_input.side_effect = [start_date, end_date]
        mock_slider.return_value = 24  # 24 hours

        time_filter = admin_dashboard.render_time_range_filter()

        assert time_filter["start_date"] == start_date
        assert time_filter["end_date"] == end_date
        assert time_filter["hours_back"] == 24

    @patch('streamlit.multiselect')
    def test_metric_selection(self, mock_multiselect, admin_dashboard):
        """Test metric selection for custom dashboards"""

        available_metrics = [
            "Conversion Rate", "Lead Score", "Memory Learning Rate",
            "Response Time", "Property Match Satisfaction"
        ]
        selected_metrics = ["Conversion Rate", "Lead Score", "Memory Learning Rate"]

        mock_multiselect.return_value = selected_metrics

        metrics = admin_dashboard.render_metric_selector(available_metrics)

        assert len(metrics) == 3
        assert "Conversion Rate" in metrics
        assert "Lead Score" in metrics

class TestAdminDashboardDataIntegration:
    """Test admin dashboard data integration and processing"""

    @pytest.mark.asyncio
    async def test_real_time_data_loading(self, admin_dashboard, mock_tenant_data, mock_system_health):
        """Test real-time data loading and refresh"""

        with patch.object(admin_dashboard, 'database_service') as mock_db, \
             patch.object(admin_dashboard, 'redis_service') as mock_redis:

            # Mock real-time data sources
            mock_db.get_tenant_metrics.return_value = mock_tenant_data
            mock_redis.get_system_health.return_value = mock_system_health

            # Load real-time data
            dashboard_data = await admin_dashboard.load_real_time_dashboard_data()

            # Verify data structure
            assert "tenants" in dashboard_data
            assert "system_health" in dashboard_data
            assert "last_updated" in dashboard_data

            # Verify data freshness
            last_updated = dashboard_data["last_updated"]
            assert (datetime.now() - last_updated).seconds < 60  # Updated within last minute

    def test_memory_analytics_data_processing(self, admin_dashboard):
        """Test memory analytics data processing and aggregation"""

        # Mock conversation memory data
        mock_conversation_data = [
            {
                "tenant_id": "tenant_1",
                "conversation_count": 45,
                "avg_conversation_length": 12.5,
                "memory_retention_rate": 0.94,
                "behavioral_learning_accuracy": 0.89
            },
            {
                "tenant_id": "tenant_2",
                "conversation_count": 32,
                "avg_conversation_length": 8.3,
                "memory_retention_rate": 0.91,
                "behavioral_learning_accuracy": 0.92
            }
        ]

        with patch.object(admin_dashboard, 'get_conversation_memory_data', return_value=mock_conversation_data):
            analytics = admin_dashboard.process_memory_analytics()

            # Verify aggregated metrics
            assert "total_conversations" in analytics
            assert "avg_retention_rate" in analytics
            assert "avg_learning_accuracy" in analytics

            # Verify calculations
            expected_total = sum(d["conversation_count"] for d in mock_conversation_data)
            assert analytics["total_conversations"] == expected_total

    def test_performance_trend_analysis(self, admin_dashboard, mock_tenant_data):
        """Test performance trend analysis and forecasting"""

        # Mock historical performance data
        historical_data = []
        for days_back in range(30, 0, -1):
            data_point = {
                "date": datetime.now() - timedelta(days=days_back),
                "conversion_rate": 0.20 + (days_back * 0.001),  # Improving trend
                "memory_learning_rate": 0.80 + (days_back * 0.002),
                "avg_response_time": 180 - (days_back * 1.5)
            }
            historical_data.append(data_point)

        with patch.object(admin_dashboard, 'get_historical_performance_data', return_value=historical_data):
            trends = admin_dashboard.analyze_performance_trends()

            # Verify trend analysis
            assert "conversion_rate_trend" in trends
            assert "memory_learning_trend" in trends
            assert "response_time_trend" in trends

            # Verify trend direction detection
            assert trends["conversion_rate_trend"]["direction"] in ["improving", "stable", "declining"]
            assert trends["memory_learning_trend"]["direction"] in ["improving", "stable", "declining"]

class TestAdminDashboardAlerts:
    """Test admin dashboard alerting and notification system"""

    def test_performance_threshold_monitoring(self, admin_dashboard, mock_tenant_data):
        """Test performance threshold monitoring and alert generation"""

        # Define performance thresholds
        thresholds = {
            "conversion_rate_min": 0.15,
            "memory_learning_rate_min": 0.80,
            "claude_response_time_max": 200,
            "property_match_satisfaction_min": 0.85
        }

        with patch.object(admin_dashboard, 'get_performance_thresholds', return_value=thresholds):
            alerts = admin_dashboard.check_performance_alerts(mock_tenant_data)

            # Verify alert generation
            assert isinstance(alerts, list)

            # Check for specific alerts
            low_conversion_alerts = [a for a in alerts if "conversion rate" in a["message"].lower()]
            slow_response_alerts = [a for a in alerts if "response time" in a["message"].lower()]

            # Verify alert details
            for alert in alerts:
                assert "tenant_id" in alert
                assert "severity" in alert
                assert "message" in alert
                assert "timestamp" in alert
                assert alert["severity"] in ["low", "medium", "high", "critical"]

    def test_system_health_alerts(self, admin_dashboard, mock_system_health):
        """Test system health monitoring and critical alerts"""

        # Simulate unhealthy system state
        unhealthy_system_health = {
            **mock_system_health,
            "database": {
                **mock_system_health["database"],
                "status": "degraded",
                "error_rate_5m": 0.05,  # 5% error rate (critical)
                "query_avg_time_ms": 250   # Slow queries
            },
            "redis": {
                **mock_system_health["redis"],
                "status": "unhealthy",
                "hit_rate": 0.65,  # Low hit rate
                "memory_usage_mb": 890  # High memory usage
            }
        }

        alerts = admin_dashboard.check_system_health_alerts(unhealthy_system_health)

        # Verify critical alerts generated
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        assert len(critical_alerts) > 0

        # Verify database alerts
        db_alerts = [a for a in alerts if "database" in a["message"].lower()]
        assert len(db_alerts) > 0

        # Verify Redis alerts
        redis_alerts = [a for a in alerts if "redis" in a["message"].lower()]
        assert len(redis_alerts) > 0

    @patch('streamlit.error')
    @patch('streamlit.warning')
    @patch('streamlit.info')
    def test_alert_display_system(self, mock_info, mock_warning, mock_error, admin_dashboard):
        """Test alert display system with different severity levels"""

        # Mock alerts with different severities
        test_alerts = [
            {"severity": "critical", "message": "Database connection pool exhausted"},
            {"severity": "high", "message": "Claude API response time exceeding 300ms"},
            {"severity": "medium", "message": "Memory learning accuracy below 85%"},
            {"severity": "low", "message": "Cache hit rate slightly below target"}
        ]

        admin_dashboard.display_alerts(test_alerts)

        # Verify appropriate Streamlit alert components were called
        mock_error.assert_called()  # Critical alerts
        mock_warning.assert_called()  # High alerts

    def test_intelligent_alert_filtering(self, admin_dashboard):
        """Test intelligent alert filtering to prevent spam"""

        # Simulate repetitive alerts
        repetitive_alerts = [
            {"tenant_id": "tenant_1", "message": "High response time detected", "timestamp": datetime.now() - timedelta(minutes=1)},
            {"tenant_id": "tenant_1", "message": "High response time detected", "timestamp": datetime.now() - timedelta(minutes=2)},
            {"tenant_id": "tenant_1", "message": "High response time detected", "timestamp": datetime.now() - timedelta(minutes=3)},
            {"tenant_id": "tenant_2", "message": "Low conversion rate", "timestamp": datetime.now() - timedelta(minutes=1)}
        ]

        filtered_alerts = admin_dashboard.filter_duplicate_alerts(repetitive_alerts, time_window_minutes=5)

        # Verify duplicate filtering
        tenant_1_alerts = [a for a in filtered_alerts if a["tenant_id"] == "tenant_1"]
        assert len(tenant_1_alerts) == 1  # Duplicates filtered

        tenant_2_alerts = [a for a in filtered_alerts if a["tenant_id"] == "tenant_2"]
        assert len(tenant_2_alerts) == 1  # Unique alert preserved

class TestAdminDashboardSecurity:
    """Test admin dashboard security and access control"""

    def test_admin_access_control(self, admin_dashboard):
        """Test admin access control and authentication"""

        # Test unauthorized access
        with patch('streamlit.session_state') as mock_session_state:
            mock_session_state.authenticated = False
            mock_session_state.user_role = "viewer"

            access_granted = admin_dashboard.check_admin_access()
            assert access_granted == False

            # Test authorized access
            mock_session_state.authenticated = True
            mock_session_state.user_role = "admin"

            access_granted = admin_dashboard.check_admin_access()
            assert access_granted == True

    def test_tenant_data_access_control(self, admin_dashboard, mock_tenant_data):
        """Test tenant-specific data access control"""

        # Test admin can see all tenants
        with patch('streamlit.session_state') as mock_session_state:
            mock_session_state.user_role = "admin"
            mock_session_state.accessible_tenants = []  # Empty means all tenants

            accessible_tenants = admin_dashboard.filter_accessible_tenants(mock_tenant_data)
            assert len(accessible_tenants) == len(mock_tenant_data)

            # Test limited user can only see specific tenants
            mock_session_state.user_role = "manager"
            mock_session_state.accessible_tenants = ["tenant_1", "tenant_2"]

            accessible_tenants = admin_dashboard.filter_accessible_tenants(mock_tenant_data)
            assert len(accessible_tenants) == 2

    def test_sensitive_data_masking(self, admin_dashboard):
        """Test sensitive data masking in dashboard displays"""

        # Mock tenant config with sensitive data
        sensitive_config = {
            "claude_api_key": "sk-ant-api03-1234567890abcdef",
            "ghl_api_key": "ghl_live_1234567890abcdef",
            "database_password": "super_secret_password"
        }

        masked_config = admin_dashboard.mask_sensitive_data(sensitive_config)

        # Verify sensitive data is masked
        assert "sk-ant-api03-****" in masked_config["claude_api_key"]
        assert "ghl_live_****" in masked_config["ghl_api_key"]
        assert "****" in masked_config["database_password"]

        # Verify masking preserves some characters for identification
        assert masked_config["claude_api_key"].startswith("sk-ant-api03-")
        assert masked_config["ghl_api_key"].startswith("ghl_live_")

if __name__ == "__main__":
    # Run admin dashboard tests
    pytest.main([__file__, "-v"])