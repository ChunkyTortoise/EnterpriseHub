"""
Tests for Advanced Analytics Visualization Engine
Comprehensive test suite for analytics and visualization capabilities
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

# Import the service under test
try:
    from ghl_real_estate_ai.services.advanced_analytics_visualization_engine import (
        AdvancedAnalyticsVisualizationEngine,
        AnalyticsKPI,
        AnalyticsDashboard,
        AnalyticsInsight
    )
except ImportError as e:
    # Skip tests if dependencies not available
    pytest.skip(f"Skipping tests due to missing dependencies: {e}", allow_module_level=True)

class TestAdvancedAnalyticsVisualizationEngine:
    """Test suite for Advanced Analytics Visualization Engine"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        """Create engine instance for testing"""
        with patch('ghl_real_estate_ai.services.advanced_analytics_visualization_engine.CacheService'):
            with patch('ghl_real_estate_ai.services.advanced_analytics_visualization_engine.ClaudeClient'):
                engine = AdvancedAnalyticsVisualizationEngine()
                yield engine
    
    @pytest.fixture
    def sample_data(self):
        """Sample analytics data for testing"""
        return {
            'leads': [
                {'id': 'lead1', 'score': 85, 'created_date': '2024-01-15', 'status': 'qualified'},
                {'id': 'lead2', 'score': 92, 'created_date': '2024-01-16', 'status': 'converted'},
                {'id': 'lead3', 'score': 78, 'created_date': '2024-01-17', 'status': 'nurturing'}
            ],
            'properties': [
                {'id': 'prop1', 'price': 500000, 'views': 120, 'inquiries': 8},
                {'id': 'prop2', 'price': 750000, 'views': 95, 'inquiries': 12},
                {'id': 'prop3', 'price': 320000, 'views': 200, 'inquiries': 15}
            ],
            'agents': [
                {'id': 'agent1', 'deals_closed': 12, 'revenue': 1200000},
                {'id': 'agent2', 'deals_closed': 8, 'revenue': 950000},
                {'id': 'agent3', 'deals_closed': 15, 'revenue': 1800000}
            ]
        }
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initializes correctly"""
        assert engine is not None
        assert hasattr(engine, 'cache_service')
        assert hasattr(engine, 'claude_client')
        assert hasattr(engine, 'performance_metrics')
    
    @pytest.mark.asyncio
    async def test_calculate_kpis(self, engine, sample_data):
        """Test KPI calculation functionality"""
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        
        kpis = await engine.calculate_kpis(sample_data)
        
        assert isinstance(kpis, list)
        assert len(kpis) > 0
        
        for kpi in kpis:
            assert isinstance(kpi, AnalyticsKPI)
            assert kpi.name
            assert kpi.value is not None
            assert kpi.trend_direction in ['up', 'down', 'stable']
    
    @pytest.mark.asyncio
    async def test_generate_interactive_charts(self, engine, sample_data):
        """Test interactive chart generation"""
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        
        charts = await engine.generate_interactive_charts(sample_data, 'leads')
        
        assert isinstance(charts, dict)
        assert 'charts' in charts
        assert 'metadata' in charts
        assert len(charts['charts']) > 0
        
        # Verify chart structure
        for chart in charts['charts']:
            assert 'type' in chart
            assert 'data' in chart
            assert 'config' in chart
    
    @pytest.mark.asyncio
    async def test_detect_anomalies(self, engine, sample_data):
        """Test anomaly detection functionality"""
        # Mock Claude client for AI analysis
        engine.claude_client.generate = AsyncMock(return_value=json.dumps({
            'anomalies': [
                {
                    'type': 'spike',
                    'metric': 'lead_volume',
                    'severity': 'medium',
                    'description': 'Unusual increase in lead volume'
                }
            ],
            'recommendations': ['Monitor lead quality', 'Review marketing campaigns']
        }))
        
        anomalies = await engine.detect_anomalies(sample_data)
        
        assert isinstance(anomalies, list)
        if len(anomalies) > 0:
            for anomaly in anomalies:
                assert 'type' in anomaly
                assert 'severity' in anomaly
                assert 'description' in anomaly
    
    @pytest.mark.asyncio
    async def test_generate_predictive_insights(self, engine, sample_data):
        """Test predictive insights generation"""
        # Mock Claude client
        engine.claude_client.generate = AsyncMock(return_value=json.dumps({
            'predictions': [
                {
                    'metric': 'revenue',
                    'predicted_value': 2500000,
                    'confidence': 0.85,
                    'timeframe': '30_days'
                }
            ],
            'insights': [
                {
                    'type': 'trend',
                    'description': 'Revenue growth trending upward',
                    'confidence': 0.92
                }
            ]
        }))
        
        insights = await engine.generate_predictive_insights(sample_data, 30)
        
        assert isinstance(insights, list)
        if len(insights) > 0:
            for insight in insights:
                assert isinstance(insight, AnalyticsInsight)
                assert insight.type
                assert insight.description
                assert insight.confidence >= 0 and insight.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_create_dashboard(self, engine, sample_data):
        """Test dashboard creation"""
        # Mock dependencies
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        engine.claude_client.generate = AsyncMock(return_value=json.dumps({
            'insights': ['Strong performance this quarter'],
            'recommendations': ['Focus on high-value leads']
        }))
        
        dashboard = await engine.create_dashboard(
            data=sample_data,
            dashboard_type='executive',
            filters={'date_range': '30d'}
        )
        
        assert isinstance(dashboard, AnalyticsDashboard)
        assert dashboard.title
        assert dashboard.created_at
        assert isinstance(dashboard.kpis, list)
        assert isinstance(dashboard.charts, dict)
        assert isinstance(dashboard.insights, list)
    
    @pytest.mark.asyncio
    async def test_export_analytics_data(self, engine, sample_data):
        """Test analytics data export"""
        # Mock dependencies
        engine.cache_service.get = AsyncMock(return_value=None)
        
        export_data = await engine.export_analytics_data(
            data=sample_data,
            format_type='json',
            include_charts=True
        )
        
        assert isinstance(export_data, dict)
        assert 'data' in export_data
        assert 'metadata' in export_data
        assert 'format' in export_data
        assert export_data['format'] == 'json'
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self, engine):
        """Test caching functionality"""
        cache_key = "test_analytics_cache"
        test_data = {"test": "data"}
        
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        
        # First call should miss cache
        await engine._cache_analytics_result(cache_key, test_data)
        
        # Verify cache set was called
        engine.cache_service.set.assert_called_once()
        
        # Mock cache hit
        engine.cache_service.get = AsyncMock(return_value=test_data)
        
        cached_data = await engine._get_cached_analytics(cache_key)
        assert cached_data == test_data
    
    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, engine):
        """Test performance metrics are tracked"""
        initial_requests = engine.performance_metrics.get('total_requests', 0)
        
        # Mock cache and trigger analytics operation
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        
        await engine.calculate_kpis({'test': 'data'})
        
        # Performance metrics should be updated
        assert engine.performance_metrics['total_requests'] == initial_requests + 1
        assert 'average_response_time' in engine.performance_metrics
    
    @pytest.mark.asyncio
    async def test_error_handling(self, engine):
        """Test error handling in analytics operations"""
        # Mock cache service to raise exception
        engine.cache_service.get = AsyncMock(side_effect=Exception("Cache error"))
        
        # Should handle errors gracefully
        kpis = await engine.calculate_kpis({'test': 'data'})
        
        # Should return empty list on error but not crash
        assert isinstance(kpis, list)
        assert 'error_count' in engine.performance_metrics
        assert engine.performance_metrics['error_count'] > 0
    
    def test_analytics_kpi_model(self):
        """Test AnalyticsKPI data model"""
        kpi = AnalyticsKPI(
            name="conversion_rate",
            value=15.5,
            unit="percentage",
            trend_direction="up",
            trend_percentage=2.3,
            target_value=18.0,
            description="Lead conversion rate"
        )
        
        assert kpi.name == "conversion_rate"
        assert kpi.value == 15.5
        assert kpi.unit == "percentage"
        assert kpi.trend_direction == "up"
        assert kpi.trend_percentage == 2.3
        assert kpi.target_value == 18.0
        assert kpi.description == "Lead conversion rate"
    
    def test_analytics_insight_model(self):
        """Test AnalyticsInsight data model"""
        insight = AnalyticsInsight(
            type="trend",
            description="Revenue growth trending upward",
            confidence=0.92,
            impact_level="high",
            recommendations=["Continue current strategy"],
            data_points=["Q4 revenue", "Lead quality"]
        )
        
        assert insight.type == "trend"
        assert insight.description == "Revenue growth trending upward"
        assert insight.confidence == 0.92
        assert insight.impact_level == "high"
        assert "Continue current strategy" in insight.recommendations
        assert "Q4 revenue" in insight.data_points
    
    def test_analytics_dashboard_model(self):
        """Test AnalyticsDashboard data model"""
        dashboard = AnalyticsDashboard(
            title="Executive Dashboard",
            description="High-level business metrics",
            created_at=datetime.now(),
            dashboard_type="executive",
            kpis=[],
            charts={},
            insights=[],
            filters={"date_range": "30d"}
        )
        
        assert dashboard.title == "Executive Dashboard"
        assert dashboard.description == "High-level business metrics"
        assert dashboard.dashboard_type == "executive"
        assert isinstance(dashboard.created_at, datetime)
        assert isinstance(dashboard.kpis, list)
        assert isinstance(dashboard.charts, dict)
        assert isinstance(dashboard.insights, list)
        assert dashboard.filters["date_range"] == "30d"

# Integration test
@pytest.mark.asyncio
async def test_full_analytics_pipeline():
    """Test complete analytics pipeline integration"""
    try:
        with patch('ghl_real_estate_ai.services.advanced_analytics_visualization_engine.CacheService'):
            with patch('ghl_real_estate_ai.services.advanced_analytics_visualization_engine.ClaudeClient'):
                engine = AdvancedAnalyticsVisualizationEngine()
                
                # Mock dependencies
                engine.cache_service.get = AsyncMock(return_value=None)
                engine.cache_service.set = AsyncMock()
                engine.claude_client.generate = AsyncMock(return_value=json.dumps({
                    'insights': ['Test insight'],
                    'predictions': [{'metric': 'test', 'value': 100}]
                }))
                
                sample_data = {
                    'leads': [{'id': '1', 'score': 85}],
                    'properties': [{'id': '1', 'price': 500000}]
                }
                
                # Run full pipeline
                dashboard = await engine.create_dashboard(
                    data=sample_data,
                    dashboard_type='operational'
                )
                
                assert isinstance(dashboard, AnalyticsDashboard)
                assert dashboard.title
                
    except ImportError:
        pytest.skip("Dependencies not available for integration test")