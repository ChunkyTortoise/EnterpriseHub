"""
Tests for Business Intelligence Reporting Engine
Comprehensive test suite for BI reporting and intelligence capabilities
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

# Import the service under test
try:
    from ghl_real_estate_ai.services.business_intelligence_reporting_engine import (
        BusinessIntelligenceReportingEngine,
        ReportTemplate,
        BusinessReport,
        KPIDashboard
    )
except ImportError as e:
    # Skip tests if dependencies not available
    pytest.skip(f"Skipping tests due to missing dependencies: {e}", allow_module_level=True)

class TestBusinessIntelligenceReportingEngine:
    """Test suite for Business Intelligence Reporting Engine"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        """Create engine instance for testing"""
        with patch('ghl_real_estate_ai.services.business_intelligence_reporting_engine.CacheService'):
            with patch('ghl_real_estate_ai.services.business_intelligence_reporting_engine.ClaudeClient'):
                engine = BusinessIntelligenceReportingEngine()
                yield engine
    
    @pytest.fixture
    def sample_business_data(self):
        """Sample business data for testing"""
        return {
            'revenue': {
                'current_month': 1250000,
                'previous_month': 1100000,
                'current_quarter': 3500000,
                'previous_quarter': 3200000
            },
            'leads': {
                'total': 450,
                'qualified': 280,
                'converted': 65,
                'conversion_rate': 14.4
            },
            'properties': {
                'listed': 125,
                'sold': 32,
                'average_price': 675000,
                'days_on_market': 45
            },
            'agents': [
                {'name': 'John Smith', 'deals': 12, 'revenue': 1800000},
                {'name': 'Sarah Johnson', 'deals': 8, 'revenue': 1200000},
                {'name': 'Mike Wilson', 'deals': 15, 'revenue': 2200000}
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
    async def test_generate_executive_briefing(self, engine, sample_business_data):
        """Test executive briefing generation"""
        # Mock Claude client for AI narrative generation
        engine.claude_client.generate = AsyncMock(return_value=json.dumps({
            'executive_summary': 'Strong performance with 13.6% revenue growth',
            'key_highlights': [
                'Revenue exceeded targets by 8%',
                'Lead conversion improved by 2.3%',
                'Agent productivity up 15%'
            ],
            'strategic_recommendations': [
                'Expand high-performing agent teams',
                'Focus on luxury property segment',
                'Enhance digital marketing efforts'
            ],
            'risk_factors': [
                'Market cooling trends',
                'Interest rate sensitivity'
            ]
        }))
        
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        
        briefing = await engine.generate_executive_briefing(sample_business_data)
        
        assert isinstance(briefing, BusinessReport)
        assert briefing.title == "Executive Business Briefing"
        assert briefing.report_type == "executive_briefing"
        assert 'executive_summary' in briefing.content
        assert 'key_highlights' in briefing.content
        assert 'strategic_recommendations' in briefing.content
        assert isinstance(briefing.generated_at, datetime)
    
    @pytest.mark.asyncio
    async def test_generate_financial_analytics(self, engine, sample_business_data):
        """Test financial analytics report generation"""
        # Mock Claude client
        engine.claude_client.generate = AsyncMock(return_value=json.dumps({
            'revenue_analysis': 'Consistent growth trajectory',
            'profitability_metrics': {
                'gross_margin': 25.5,
                'net_margin': 12.3
            },
            'financial_insights': [
                'Q4 performance exceeding expectations',
                'Cost optimization opportunities identified'
            ]
        }))
        
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        
        financial_report = await engine.generate_financial_analytics(sample_business_data)
        
        assert isinstance(financial_report, BusinessReport)
        assert financial_report.report_type == "financial_analytics"
        assert 'revenue_analysis' in financial_report.content
        assert 'profitability_metrics' in financial_report.content
        assert 'financial_insights' in financial_report.content
    
    @pytest.mark.asyncio
    async def test_generate_competitive_intelligence(self, engine, sample_business_data):
        """Test competitive intelligence report generation"""
        # Mock Claude client
        engine.claude_client.generate = AsyncMock(return_value=json.dumps({
            'market_position': 'Leading position in luxury segment',
            'competitive_advantages': [
                'Superior customer service',
                'Advanced technology platform',
                'Strong brand recognition'
            ],
            'market_opportunities': [
                'First-time homebuyer segment',
                'Commercial real estate expansion'
            ],
            'threat_assessment': [
                'New market entrants',
                'Economic uncertainty'
            ]
        }))
        
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        
        competitive_report = await engine.generate_competitive_intelligence(sample_business_data)
        
        assert isinstance(competitive_report, BusinessReport)
        assert competitive_report.report_type == "competitive_intelligence"
        assert 'market_position' in competitive_report.content
        assert 'competitive_advantages' in competitive_report.content
        assert 'market_opportunities' in competitive_report.content
        assert 'threat_assessment' in competitive_report.content
    
    @pytest.mark.asyncio
    async def test_create_kpi_dashboard(self, engine, sample_business_data):
        """Test KPI dashboard creation"""
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        
        dashboard = await engine.create_kpi_dashboard(
            data=sample_business_data,
            dashboard_config={'refresh_interval': 300}
        )
        
        assert isinstance(dashboard, KPIDashboard)
        assert dashboard.title
        assert dashboard.created_at
        assert isinstance(dashboard.kpis, list)
        assert len(dashboard.kpis) > 0
        
        # Verify KPI structure
        for kpi in dashboard.kpis:
            assert 'name' in kpi
            assert 'value' in kpi
            assert 'trend' in kpi
            assert 'status' in kpi
    
    @pytest.mark.asyncio
    async def test_schedule_automated_reports(self, engine):
        """Test automated report scheduling"""
        report_config = {
            'report_type': 'executive_briefing',
            'frequency': 'weekly',
            'recipients': ['executive@company.com'],
            'delivery_day': 'monday',
            'delivery_time': '09:00'
        }
        
        # Mock cache service
        engine.cache_service.set = AsyncMock()
        
        schedule_id = await engine.schedule_automated_reports(report_config)
        
        assert schedule_id is not None
        assert isinstance(schedule_id, str)
        
        # Verify schedule was cached
        engine.cache_service.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_custom_report(self, engine, sample_business_data):
        """Test custom report generation"""
        # Mock Claude client
        engine.claude_client.generate = AsyncMock(return_value=json.dumps({
            'custom_analysis': 'Detailed agent performance analysis',
            'findings': [
                'Top performers drive 60% of revenue',
                'Training programs show 20% improvement'
            ],
            'recommendations': [
                'Implement peer mentoring',
                'Expand successful training modules'
            ]
        }))
        
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        
        template = ReportTemplate(
            name="Agent Performance Analysis",
            description="Detailed analysis of agent productivity",
            sections=['performance_metrics', 'comparative_analysis', 'recommendations'],
            parameters={'time_period': '90_days'}
        )
        
        custom_report = await engine.generate_custom_report(
            template=template,
            data=sample_business_data
        )
        
        assert isinstance(custom_report, BusinessReport)
        assert custom_report.report_type == "custom"
        assert 'custom_analysis' in custom_report.content
        assert 'findings' in custom_report.content
        assert 'recommendations' in custom_report.content
    
    @pytest.mark.asyncio
    async def test_export_report_data(self, engine):
        """Test report data export"""
        # Create sample report
        report = BusinessReport(
            title="Test Report",
            report_type="test",
            content={'test': 'data'},
            generated_at=datetime.now(),
            metadata={'version': '1.0'}
        )
        
        # Test different export formats
        for export_format in ['pdf', 'excel', 'json']:
            exported_data = await engine.export_report_data(
                report=report,
                format_type=export_format
            )
            
            assert isinstance(exported_data, dict)
            assert 'data' in exported_data
            assert 'format' in exported_data
            assert exported_data['format'] == export_format
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self, engine):
        """Test caching functionality"""
        cache_key = "test_bi_cache"
        test_data = {"test": "data"}
        
        # Mock cache service
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        
        # First call should miss cache
        await engine._cache_report_result(cache_key, test_data)
        
        # Verify cache set was called
        engine.cache_service.set.assert_called_once()
        
        # Mock cache hit
        engine.cache_service.get = AsyncMock(return_value=test_data)
        
        cached_data = await engine._get_cached_report(cache_key)
        assert cached_data == test_data
    
    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, engine):
        """Test performance metrics are tracked"""
        initial_reports = engine.performance_metrics.get('total_reports_generated', 0)
        
        # Mock dependencies and generate report
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock()
        engine.claude_client.generate = AsyncMock(return_value=json.dumps({
            'executive_summary': 'Test summary'
        }))
        
        await engine.generate_executive_briefing({'test': 'data'})
        
        # Performance metrics should be updated
        assert engine.performance_metrics['total_reports_generated'] == initial_reports + 1
        assert 'average_generation_time' in engine.performance_metrics
    
    @pytest.mark.asyncio
    async def test_error_handling(self, engine):
        """Test error handling in report generation"""
        # Mock Claude client to raise exception
        engine.claude_client.generate = AsyncMock(side_effect=Exception("AI service error"))
        
        # Should handle errors gracefully
        try:
            report = await engine.generate_executive_briefing({'test': 'data'})
            # If it doesn't raise, it should return a valid error report
            assert isinstance(report, BusinessReport)
            assert 'error' in report.content or report.title.lower().startswith('error')
        except Exception:
            # Or it might raise, which is also acceptable
            pass
        
        # Error should be tracked
        assert 'error_count' in engine.performance_metrics
        assert engine.performance_metrics['error_count'] > 0
    
    def test_report_template_model(self):
        """Test ReportTemplate data model"""
        template = ReportTemplate(
            name="Monthly Report",
            description="Monthly business summary",
            sections=['revenue', 'leads', 'properties'],
            parameters={'period': 'monthly'},
            formatting={'layout': 'standard'},
            filters={'exclude': ['draft_data']}
        )
        
        assert template.name == "Monthly Report"
        assert template.description == "Monthly business summary"
        assert 'revenue' in template.sections
        assert template.parameters['period'] == 'monthly'
        assert template.formatting['layout'] == 'standard'
        assert 'draft_data' in template.filters['exclude']
    
    def test_business_report_model(self):
        """Test BusinessReport data model"""
        report = BusinessReport(
            title="Test Report",
            report_type="executive_briefing",
            content={'summary': 'Test content'},
            generated_at=datetime.now(),
            metadata={'version': '1.0'},
            recipients=['test@example.com'],
            schedule_id='schedule_123'
        )
        
        assert report.title == "Test Report"
        assert report.report_type == "executive_briefing"
        assert report.content['summary'] == 'Test content'
        assert isinstance(report.generated_at, datetime)
        assert report.metadata['version'] == '1.0'
        assert 'test@example.com' in report.recipients
        assert report.schedule_id == 'schedule_123'
    
    def test_kpi_dashboard_model(self):
        """Test KPIDashboard data model"""
        dashboard = KPIDashboard(
            title="Executive Dashboard",
            created_at=datetime.now(),
            kpis=[
                {'name': 'Revenue', 'value': 1000000, 'trend': 'up', 'status': 'good'},
                {'name': 'Leads', 'value': 150, 'trend': 'stable', 'status': 'normal'}
            ],
            refresh_interval=300,
            filters={'date_range': '30d'},
            layout_config={'columns': 3}
        )
        
        assert dashboard.title == "Executive Dashboard"
        assert isinstance(dashboard.created_at, datetime)
        assert len(dashboard.kpis) == 2
        assert dashboard.refresh_interval == 300
        assert dashboard.filters['date_range'] == '30d'
        assert dashboard.layout_config['columns'] == 3

# Integration test
@pytest.mark.asyncio
async def test_full_bi_pipeline():
    """Test complete BI reporting pipeline integration"""
    try:
        with patch('ghl_real_estate_ai.services.business_intelligence_reporting_engine.CacheService'):
            with patch('ghl_real_estate_ai.services.business_intelligence_reporting_engine.ClaudeClient'):
                engine = BusinessIntelligenceReportingEngine()
                
                # Mock dependencies
                engine.cache_service.get = AsyncMock(return_value=None)
                engine.cache_service.set = AsyncMock()
                engine.claude_client.generate = AsyncMock(return_value=json.dumps({
                    'executive_summary': 'Test summary',
                    'key_highlights': ['Test highlight']
                }))
                
                sample_data = {
                    'revenue': {'current_month': 1000000},
                    'leads': {'total': 100, 'converted': 15}
                }
                
                # Generate executive briefing
                briefing = await engine.generate_executive_briefing(sample_data)
                
                assert isinstance(briefing, BusinessReport)
                assert briefing.title
                assert briefing.content
                
                # Create KPI dashboard
                dashboard = await engine.create_kpi_dashboard(sample_data)
                
                assert isinstance(dashboard, KPIDashboard)
                assert len(dashboard.kpis) > 0
                
    except ImportError:
        pytest.skip("Dependencies not available for integration test")