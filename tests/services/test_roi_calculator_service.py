"""
Unit tests for ROI Calculator Service.

Tests ROI calculation logic, client value analysis, and competitive positioning for Jorge's platform.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from decimal import Decimal

from ghl_real_estate_ai.services.roi_calculator_service import (
    ROICalculatorService,
    ClientROIReport,
    HumanVsAIComparison,
    CompetitiveAnalysis,
    ROIProjection
)


class TestROICalculatorService:
    """Unit tests for ROI Calculator Service."""
    
    @pytest.fixture
    def roi_calculator(self):
        """Create ROI calculator with mocked dependencies."""
        calculator = ROICalculatorService()
        
        # Mock external services
        calculator.revenue_engine = AsyncMock()
        calculator.cache_service = AsyncMock()
        calculator.pricing_optimizer = AsyncMock()
        
        return calculator
    
    @pytest.fixture
    def sample_location_metrics(self):
        """Sample location performance metrics."""
        return {
            "total_leads": 425,
            "qualified_leads": 312,
            "converted_leads": 89,
            "total_revenue": 178500.0,
            "average_deal_size": 2005.62,
            "conversion_rate": 0.209,
            "lead_sources": {
                "website": 180,
                "referral": 95,
                "social_media": 85,
                "paid_ads": 65
            },
            "monthly_trends": [
                {"month": "2024-01", "leads": 95, "revenue": 38750},
                {"month": "2024-02", "leads": 108, "revenue": 42300},
                {"month": "2024-03", "leads": 132, "revenue": 54200},
                {"month": "2024-04", "leads": 90, "revenue": 43250}
            ]
        }

    async def test_generate_client_roi_report(self, roi_calculator, sample_location_metrics):
        """Test complete ROI report generation."""
        
        # Setup revenue engine mock
        roi_calculator.revenue_engine.get_location_metrics.return_value = sample_location_metrics
        
        # Setup pricing optimizer mock
        roi_calculator.pricing_optimizer.get_pricing_analytics.return_value = {
            "average_price_by_tier": {"hot": 425.0, "warm": 275.0, "cold": 150.0},
            "total_revenue_attributed": 156780.0,
            "cost_optimization_savings": 23400.0
        }
        
        # Generate ROI report
        report = await roi_calculator.generate_client_roi_report(
            location_id="test_location_456",
            days=30,
            include_projections=True
        )
        
        # Verify report structure
        assert isinstance(report, ClientROIReport)
        assert report.location_id == "test_location_456"
        assert report.report_period_days == 30
        
        # Verify calculated metrics
        assert report.total_leads == 425
        assert report.qualified_leads == 312
        assert report.converted_leads == 89
        assert report.conversion_rate == pytest.approx(0.209, rel=1e-2)
        assert report.total_revenue == 178500.0
        
        # Verify ROI calculation
        assert report.roi_percentage > 100  # Should show positive ROI
        assert report.projected_annual_revenue > report.total_revenue * 10  # Annual projection
        
        # Verify competitive metrics
        assert report.competitive_advantage_score >= 0
        assert report.competitive_advantage_score <= 10

    async def test_human_vs_ai_comparison(self, roi_calculator, sample_location_metrics):
        """Test human vs AI performance comparison."""
        
        roi_calculator.revenue_engine.get_location_metrics.return_value = sample_location_metrics
        
        comparison = await roi_calculator.calculate_human_vs_ai_comparison(
            location_id="test_location",
            days=30
        )
        
        # Verify comparison structure
        assert isinstance(comparison, HumanVsAIComparison)
        
        # AI should show efficiency advantages
        assert comparison.ai_response_time < comparison.human_response_time
        assert comparison.ai_accuracy >= comparison.human_accuracy
        assert comparison.ai_cost_per_lead <= comparison.human_cost_per_lead
        
        # Verify savings calculation
        assert comparison.time_savings_hours > 0
        assert comparison.cost_savings_monthly > 0
        assert comparison.efficiency_improvement_percentage > 0

    async def test_competitive_analysis(self, roi_calculator):
        """Test competitive positioning analysis."""
        
        # Mock competitive data
        roi_calculator._get_industry_benchmarks = AsyncMock(return_value={
            "average_conversion_rate": 0.15,
            "average_cost_per_lead": 185.0,
            "average_response_time": 4.2,
            "average_lead_quality_score": 6.8,
            "typical_roi": 180.0
        })
        
        # Mock client performance
        client_metrics = {
            "conversion_rate": 0.209,
            "cost_per_lead": 125.0,
            "response_time": 0.3,
            "lead_quality_score": 8.4,
            "roi_percentage": 285.0
        }
        
        analysis = await roi_calculator.perform_competitive_analysis(
            location_id="test_location",
            client_metrics=client_metrics
        )
        
        # Verify competitive advantages
        assert isinstance(analysis, CompetitiveAnalysis)
        assert analysis.conversion_rate_advantage > 0  # Better than industry average
        assert analysis.cost_efficiency_advantage > 0  # Lower cost per lead
        assert analysis.speed_advantage > 0  # Faster response time
        assert analysis.overall_competitive_score > 7.0  # Strong competitive position

    async def test_roi_projections(self, roi_calculator, sample_location_metrics):
        """Test ROI projection calculations."""
        
        roi_calculator.revenue_engine.get_location_metrics.return_value = sample_location_metrics
        
        # Test various projection scenarios
        projection_scenarios = [
            {"growth_rate": 0.15, "period_months": 12},  # Conservative growth
            {"growth_rate": 0.25, "period_months": 12},  # Moderate growth
            {"growth_rate": 0.40, "period_months": 12}   # Aggressive growth
        ]
        
        for scenario in projection_scenarios:
            projection = await roi_calculator.calculate_roi_projection(
                location_id="test_location",
                growth_rate=scenario["growth_rate"],
                period_months=scenario["period_months"]
            )
            
            assert isinstance(projection, ROIProjection)
            
            # Projected revenue should be higher than current
            current_monthly = sample_location_metrics["total_revenue"] / 4  # 4 months of data
            projected_monthly = projection.projected_monthly_revenue
            
            expected_growth = 1 + scenario["growth_rate"]
            assert projected_monthly >= current_monthly * expected_growth * 0.9  # Allow some variance
            
            # Verify projection components
            assert projection.projected_annual_revenue > 0
            assert projection.investment_required > 0
            assert projection.net_profit_increase > 0
            assert projection.payback_period_months > 0

    async def test_cost_breakdown_analysis(self, roi_calculator):
        """Test detailed cost breakdown and savings analysis."""
        
        # Mock current costs
        current_costs = {
            "staff_time": 4800.0,  # Monthly staff costs
            "lead_acquisition": 3200.0,
            "technology": 450.0,
            "overhead": 800.0
        }
        
        # Mock AI-optimized costs
        ai_optimized_costs = {
            "staff_time": 2400.0,  # 50% reduction through automation
            "lead_acquisition": 2560.0,  # 20% reduction through better targeting
            "technology": 750.0,  # Increased for AI tools
            "overhead": 650.0  # Reduced operational overhead
        }
        
        savings_analysis = await roi_calculator.calculate_cost_savings(
            location_id="test_location",
            current_costs=current_costs,
            optimized_costs=ai_optimized_costs
        )
        
        # Verify savings calculations
        total_current = sum(current_costs.values())
        total_optimized = sum(ai_optimized_costs.values())
        expected_savings = total_current - total_optimized
        
        assert savings_analysis["monthly_savings"] == expected_savings
        assert savings_analysis["annual_savings"] == expected_savings * 12
        assert savings_analysis["savings_percentage"] == (expected_savings / total_current) * 100
        
        # Verify category-specific savings
        assert savings_analysis["savings_by_category"]["staff_time"] == 2400.0
        assert savings_analysis["savings_by_category"]["lead_acquisition"] == 640.0

    async def test_client_value_calculation(self, roi_calculator, sample_location_metrics):
        """Test comprehensive client value calculation."""
        
        roi_calculator.revenue_engine.get_location_metrics.return_value = sample_location_metrics
        
        # Mock pricing data
        roi_calculator.pricing_optimizer.get_pricing_analytics.return_value = {
            "total_revenue_attributed": 156780.0,
            "average_price_by_tier": {"hot": 425.0, "warm": 275.0, "cold": 150.0},
            "leads_by_tier": {"hot": 89, "warm": 156, "cold": 180}
        }
        
        client_value = await roi_calculator.calculate_total_client_value(
            location_id="test_location",
            period_days=30
        )
        
        # Verify value components
        assert client_value["direct_revenue"] == 178500.0
        assert client_value["cost_savings"] > 0
        assert client_value["efficiency_gains"] > 0
        assert client_value["competitive_advantage_value"] > 0
        
        # Total value should exceed direct revenue
        assert client_value["total_client_value"] > client_value["direct_revenue"]

    async def test_interactive_savings_calculator(self, roi_calculator):
        """Test interactive savings calculator for client demos."""
        
        # Simulate client input parameters
        client_params = {
            "current_monthly_leads": 350,
            "current_conversion_rate": 0.12,
            "current_cost_per_lead": 195.0,
            "average_deal_size": 1650.0,
            "current_staff_hours": 160,  # Hours per month on lead management
            "staff_hourly_rate": 35.0
        }
        
        # Calculate interactive savings
        savings_scenario = await roi_calculator.calculate_interactive_savings(
            client_params=client_params,
            ai_improvements={
                "conversion_rate_increase": 0.08,  # Increase conversion by 8 percentage points
                "cost_per_lead_reduction": 0.25,   # Reduce cost per lead by 25%
                "staff_time_reduction": 0.60      # Reduce staff time by 60%
            }
        )
        
        # Verify improvement calculations
        improved_conversion = client_params["current_conversion_rate"] + 0.08
        improved_cost_per_lead = client_params["current_cost_per_lead"] * 0.75
        improved_staff_hours = client_params["current_staff_hours"] * 0.40
        
        assert savings_scenario["improved_conversion_rate"] == improved_conversion
        assert savings_scenario["improved_cost_per_lead"] == improved_cost_per_lead
        assert savings_scenario["improved_staff_hours"] == improved_staff_hours
        
        # Verify financial impact
        additional_conversions = client_params["current_monthly_leads"] * 0.08
        additional_revenue = additional_conversions * client_params["average_deal_size"]
        
        assert savings_scenario["additional_monthly_revenue"] >= additional_revenue * 0.9  # Allow variance

    async def test_report_caching(self, roi_calculator, sample_location_metrics):
        """Test ROI report caching mechanism."""
        
        location_id = "test_location"
        cache_key = f"roi_report_{location_id}_30"
        
        # First call - should calculate and cache
        roi_calculator.cache_service.get.return_value = None
        roi_calculator.revenue_engine.get_location_metrics.return_value = sample_location_metrics
        
        report1 = await roi_calculator.generate_client_roi_report(location_id, days=30)
        
        # Verify cache was called for storage
        roi_calculator.cache_service.set.assert_called()
        
        # Second call - should return cached result
        roi_calculator.cache_service.get.return_value = report1
        
        report2 = await roi_calculator.generate_client_roi_report(location_id, days=30)
        
        # Should be identical (cached)
        assert report1.total_revenue == report2.total_revenue
        assert report1.roi_percentage == report2.roi_percentage

    async def test_error_handling_insufficient_data(self, roi_calculator):
        """Test error handling when insufficient data is available."""
        
        # Mock scenario with minimal data
        roi_calculator.revenue_engine.get_location_metrics.return_value = {
            "total_leads": 5,  # Very low volume
            "qualified_leads": 2,
            "converted_leads": 0,
            "total_revenue": 0.0
        }
        
        report = await roi_calculator.generate_client_roi_report(
            location_id="new_location",
            days=30,
            include_projections=False
        )
        
        # Should handle gracefully with default values
        assert report.total_leads == 5
        assert report.converted_leads == 0
        assert report.total_revenue == 0.0
        assert report.roi_percentage == 0.0
        
        # Should indicate insufficient data
        assert report.data_quality_score < 0.5

    async def test_export_roi_report(self, roi_calculator, sample_location_metrics):
        """Test ROI report export functionality."""
        
        roi_calculator.revenue_engine.get_location_metrics.return_value = sample_location_metrics
        
        # Generate report
        report = await roi_calculator.generate_client_roi_report("test_location", days=30)
        
        # Test export formats
        export_formats = ["pdf", "xlsx", "csv"]
        
        for format_type in export_formats:
            export_result = await roi_calculator.export_roi_report(
                report=report,
                format=format_type,
                include_charts=True
            )
            
            assert export_result["export_format"] == format_type
            assert export_result["file_size"] > 0
            assert "download_url" in export_result
            assert "expires_at" in export_result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])