"""
Comprehensive Tests for Executive Portfolio Manager
Test suite for UHNW client portfolio management and investment analysis

Tests cover:
- Portfolio analysis and performance calculation
- Investment scoring and ROI analysis
- Tax optimization and 1031 exchange identification
- Portfolio diversification metrics
- AI-powered recommendations
- Executive reporting
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any
import pandas as pd

from ghl_real_estate_ai.services.executive_portfolio_manager import (
    ExecutivePortfolioManager,
    PortfolioProperty,
    UHNWClient,
    PortfolioAnalysis,
    PropertyType,
    InvestmentStrategy,
    PropertyInvestmentMetrics,
    TaxOptimization,
    create_sample_uhnw_client,
    create_sample_portfolio
)


@pytest.fixture
def portfolio_manager():
    """Initialize portfolio manager for testing"""
    with patch.multiple(
        'ghl_real_estate_ai.services.executive_portfolio_manager',
        CacheService=Mock(),
        ClaudeAssistant=Mock(),
        PropertyMatcher=Mock(),
        LLMClient=Mock()
    ):
        manager = ExecutivePortfolioManager()
        # Mock Claude responses
        manager.claude.generate_claude_response = AsyncMock(return_value="Strategic recommendation: Diversify into commercial real estate for balanced growth.")
        return manager


@pytest.fixture
def sample_uhnw_client():
    """Sample UHNW client for testing"""
    return create_sample_uhnw_client()


@pytest.fixture
def sample_portfolio():
    """Sample property portfolio for testing"""
    return create_sample_portfolio()


@pytest.fixture
def luxury_property():
    """Sample luxury property for testing"""
    return PortfolioProperty(
        property_id="LUXURY-001",
        address="123 West Lake Hills Estate",
        property_type=PropertyType.ESTATE,
        purchase_date=datetime.now() - timedelta(days=730),
        purchase_price=3_500_000,
        current_value=4_200_000,
        square_footage=6500,
        lot_size=2.5,
        bedrooms=6,
        bathrooms=5.5,
        neighborhood="West Lake Hills",
        zip_code="78746",
        investment_metrics=PropertyInvestmentMetrics(
            cap_rate=0.065,
            cash_on_cash_return=0.082,
            irr=0.095,
            roi_1_year=0.088,
            roi_5_year=0.125,
            appreciation_rate=0.095,
            rental_yield=0.045,
            risk_score=25.0,
            liquidity_score=85.0
        ),
        tax_optimization=TaxOptimization(
            depreciation_benefit=152_880,  # 3.636% annual depreciation
            property_tax_deduction=50_400,  # 1.2% property tax
            mortgage_interest_deduction=126_000,  # 6% on 70% LTV
            opportunity_1031_exchange=True,
            total_tax_savings=42_500
        ),
        total_return_lifetime=0.20  # 20% total return
    )


class TestPortfolioAnalysis:
    """Test comprehensive portfolio analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_portfolio_basic(self, portfolio_manager, sample_uhnw_client, sample_portfolio):
        """Test basic portfolio analysis"""
        analysis = await portfolio_manager.analyze_portfolio(sample_uhnw_client, sample_portfolio)

        assert isinstance(analysis, PortfolioAnalysis)
        assert analysis.total_portfolio_value > 0
        assert analysis.total_equity >= 0
        assert analysis.portfolio_irr >= 0
        assert 0 <= analysis.geographic_diversification <= 100
        assert 0 <= analysis.property_type_diversification <= 100

    @pytest.mark.asyncio
    async def test_analyze_empty_portfolio(self, portfolio_manager, sample_uhnw_client):
        """Test analysis with empty portfolio"""
        empty_portfolio = []
        analysis = await portfolio_manager.analyze_portfolio(sample_uhnw_client, empty_portfolio)

        assert analysis.total_portfolio_value == 0
        assert analysis.total_equity == 0
        assert analysis.portfolio_irr == 0

    @pytest.mark.asyncio
    async def test_analyze_single_property_portfolio(self, portfolio_manager, sample_uhnw_client, luxury_property):
        """Test analysis with single property"""
        single_property_portfolio = [luxury_property]
        analysis = await portfolio_manager.analyze_portfolio(sample_uhnw_client, single_property_portfolio)

        assert analysis.total_portfolio_value == luxury_property.current_value
        assert analysis.total_equity > 0
        assert analysis.total_tax_optimization == luxury_property.tax_optimization.total_tax_savings

    def test_calculate_portfolio_irr(self, portfolio_manager, sample_portfolio):
        """Test portfolio IRR calculation"""
        irr = portfolio_manager._calculate_portfolio_irr(sample_portfolio)

        assert -1.0 <= irr <= 2.0  # Reasonable IRR bounds
        assert isinstance(irr, float)

    def test_calculate_ytd_return(self, portfolio_manager, sample_portfolio):
        """Test YTD return calculation"""
        ytd_return = portfolio_manager._calculate_ytd_return(sample_portfolio)

        assert isinstance(ytd_return, float)
        assert ytd_return >= 0  # Assuming positive returns

    def test_calculate_lifetime_return(self, portfolio_manager, sample_portfolio):
        """Test lifetime return calculation"""
        lifetime_return = portfolio_manager._calculate_lifetime_return(sample_portfolio)

        assert isinstance(lifetime_return, float)

    def test_calculate_geographic_diversification(self, portfolio_manager):
        """Test geographic diversification scoring"""
        # Diversified portfolio
        diverse_properties = [
            PortfolioProperty(
                property_id=f"PROP-{i}",
                address=f"Address {i}",
                property_type=PropertyType.LUXURY_CONDO,
                purchase_date=datetime.now(),
                purchase_price=1_000_000,
                current_value=1_100_000,
                square_footage=2000,
                lot_size=0.0,
                bedrooms=3,
                bathrooms=2.5,
                neighborhood=neighborhood,
                zip_code=zip_code
            )
            for i, (neighborhood, zip_code) in enumerate([
                ("West Lake Hills", "78746"),
                ("Tarrytown", "78733"),
                ("Zilker", "78704"),
                ("Hyde Park", "78751")
            ])
        ]

        diversification_score = portfolio_manager._calculate_geographic_diversification(diverse_properties)
        assert diversification_score > 0
        assert diversification_score <= 100

        # Non-diversified portfolio (same location)
        same_location_properties = [
            PortfolioProperty(
                property_id=f"PROP-{i}",
                address=f"Address {i}",
                property_type=PropertyType.LUXURY_CONDO,
                purchase_date=datetime.now(),
                purchase_price=1_000_000,
                current_value=1_100_000,
                square_footage=2000,
                lot_size=0.0,
                bedrooms=3,
                bathrooms=2.5,
                neighborhood="West Lake Hills",
                zip_code="78746"
            )
            for i in range(3)
        ]

        same_location_score = portfolio_manager._calculate_geographic_diversification(same_location_properties)
        assert same_location_score < diversification_score

    def test_calculate_property_type_diversification(self, portfolio_manager):
        """Test property type diversification scoring"""
        # Diversified by property type
        diverse_types = [
            PortfolioProperty(
                property_id=f"PROP-{i}",
                address=f"Address {i}",
                property_type=prop_type,
                purchase_date=datetime.now(),
                purchase_price=1_000_000,
                current_value=1_100_000,
                square_footage=2000,
                lot_size=1.0,
                bedrooms=3,
                bathrooms=2.5,
                neighborhood="West Lake Hills",
                zip_code="78746"
            )
            for i, prop_type in enumerate([
                PropertyType.ESTATE,
                PropertyType.LUXURY_CONDO,
                PropertyType.INVESTMENT_PROPERTY,
                PropertyType.VACATION_HOME
            ])
        ]

        diversification_score = portfolio_manager._calculate_property_type_diversification(diverse_types)
        assert diversification_score > 0
        assert diversification_score <= 100

    def test_calculate_tax_optimization(self, portfolio_manager, sample_portfolio):
        """Test total tax optimization calculation"""
        total_tax_savings = portfolio_manager._calculate_total_tax_optimization(sample_portfolio)

        assert total_tax_savings >= 0
        assert isinstance(total_tax_savings, float)


class TestInvestmentAnalysis:
    """Test investment analysis and scoring"""

    @pytest.mark.asyncio
    async def test_calculate_investment_score(self, portfolio_manager, luxury_property):
        """Test AI-powered investment score calculation"""
        investment_score = await portfolio_manager._calculate_investment_score(luxury_property)

        assert 0 <= investment_score <= 100
        assert isinstance(investment_score, float)

        # Luxury property in premium neighborhood should score well
        assert investment_score >= 50

    @pytest.mark.asyncio
    async def test_investment_score_fallback(self, portfolio_manager):
        """Test investment score fallback calculation when AI fails"""
        # Property with minimal data
        minimal_property = PortfolioProperty(
            property_id="MINIMAL-001",
            address="Unknown Address",
            property_type=PropertyType.LUXURY_CONDO,
            purchase_date=datetime.now(),
            purchase_price=1_000_000,
            current_value=1_050_000,
            square_footage=2000,
            lot_size=0.0,
            bedrooms=2,
            bathrooms=2.0,
            neighborhood="",
            zip_code=""
        )

        # Mock Claude to fail
        portfolio_manager.claude.generate_claude_response = AsyncMock(side_effect=Exception("AI unavailable"))

        investment_score = await portfolio_manager._calculate_investment_score(minimal_property)

        assert 0 <= investment_score <= 100
        assert investment_score >= 0  # Should provide fallback score


class TestTaxOptimization:
    """Test tax optimization analysis"""

    def test_calculate_1031_exchange_opportunities(self, portfolio_manager):
        """Test 1031 exchange opportunity identification"""
        # Properties with significant gains
        profitable_properties = [
            PortfolioProperty(
                property_id=f"PROFIT-{i}",
                address=f"Profitable Address {i}",
                property_type=PropertyType.INVESTMENT_PROPERTY,
                purchase_date=datetime.now() - timedelta(days=365 * 3),
                purchase_price=1_000_000,
                current_value=1_500_000 + (i * 100_000),
                square_footage=2500,
                lot_size=1.0,
                bedrooms=4,
                bathrooms=3.0,
                neighborhood="Austin",
                zip_code="78704"
            )
            for i in range(3)
        ]

        opportunities = portfolio_manager.calculate_1031_exchange_opportunities(profitable_properties)

        assert len(opportunities) > 0
        assert all("capital_gain" in opp for opp in opportunities)
        assert all("potential_tax_savings" in opp for opp in opportunities)
        assert all(opp["capital_gain"] >= 100_000 for opp in opportunities)

    def test_calculate_1031_no_opportunities(self, portfolio_manager):
        """Test 1031 exchange with no opportunities"""
        # Properties without significant gains
        break_even_properties = [
            PortfolioProperty(
                property_id="BREAK_EVEN-001",
                address="Break Even Address",
                property_type=PropertyType.PRIMARY_RESIDENCE,
                purchase_date=datetime.now() - timedelta(days=365),
                purchase_price=1_000_000,
                current_value=1_020_000,  # Minimal gain
                square_footage=2500,
                lot_size=1.0,
                bedrooms=4,
                bathrooms=3.0,
                neighborhood="Austin",
                zip_code="78704"
            )
        ]

        opportunities = portfolio_manager.calculate_1031_exchange_opportunities(break_even_properties)
        assert len(opportunities) == 0


class TestRecommendations:
    """Test AI-powered strategic recommendations"""

    @pytest.mark.asyncio
    async def test_generate_strategic_recommendations(self, portfolio_manager, sample_uhnw_client, sample_portfolio):
        """Test strategic recommendation generation"""
        recommendations = await portfolio_manager._generate_strategic_recommendations(sample_uhnw_client, sample_portfolio)

        assert isinstance(recommendations, dict)
        assert "rebalancing" in recommendations
        assert "acquisitions" in recommendations
        assert "dispositions" in recommendations
        assert all(isinstance(rec_list, list) for rec_list in recommendations.values())

    @pytest.mark.asyncio
    async def test_generate_strategic_recommendations_fallback(self, portfolio_manager, sample_uhnw_client, sample_portfolio):
        """Test recommendation fallback when AI fails"""
        # Mock Claude to fail
        portfolio_manager.claude.generate_claude_response = AsyncMock(side_effect=Exception("AI unavailable"))

        recommendations = await portfolio_manager._generate_strategic_recommendations(sample_uhnw_client, sample_portfolio)

        # Should provide fallback recommendations
        assert isinstance(recommendations, dict)
        assert len(recommendations.get("rebalancing", [])) > 0


class TestExecutiveReporting:
    """Test executive report generation"""

    @pytest.mark.asyncio
    async def test_generate_executive_report(self, portfolio_manager, sample_uhnw_client):
        """Test executive report generation"""
        # Sample analysis
        analysis = PortfolioAnalysis(
            total_portfolio_value=10_000_000,
            portfolio_irr=0.095,
            portfolio_roi_ytd=0.082,
            total_tax_optimization=125_000
        )

        report = await portfolio_manager.generate_executive_report(sample_uhnw_client, analysis)

        assert isinstance(report, str)
        assert len(report) > 100  # Should be substantial report
        assert sample_uhnw_client.client_name in report

    @pytest.mark.asyncio
    async def test_generate_executive_report_fallback(self, portfolio_manager, sample_uhnw_client):
        """Test executive report fallback when AI fails"""
        # Mock Claude to fail
        portfolio_manager.claude.generate_claude_response = AsyncMock(side_effect=Exception("AI unavailable"))

        analysis = PortfolioAnalysis(
            total_portfolio_value=5_000_000,
            portfolio_irr=0.075,
            portfolio_roi_ytd=0.065
        )

        report = await portfolio_manager.generate_executive_report(sample_uhnw_client, analysis)

        # Should provide fallback report
        assert isinstance(report, str)
        assert len(report) > 50
        assert sample_uhnw_client.client_name in report


class TestAcquisitionOpportunities:
    """Test acquisition opportunity identification"""

    @pytest.mark.asyncio
    async def test_identify_acquisition_opportunities(self, portfolio_manager, sample_uhnw_client):
        """Test acquisition opportunity identification"""
        opportunities = await portfolio_manager.identify_acquisition_opportunities(
            sample_uhnw_client,
            target_budget=5_000_000,
            strategy=InvestmentStrategy.BALANCED
        )

        assert isinstance(opportunities, list)
        assert len(opportunities) > 0
        assert all("property_id" in opp for opp in opportunities)
        assert all("projected_roi" in opp for opp in opportunities)
        assert all("investment_score" in opp for opp in opportunities)

    @pytest.mark.asyncio
    async def test_identify_acquisition_opportunities_growth_strategy(self, portfolio_manager, sample_uhnw_client):
        """Test acquisition opportunities with growth strategy"""
        opportunities = await portfolio_manager.identify_acquisition_opportunities(
            sample_uhnw_client,
            target_budget=3_000_000,
            strategy=InvestmentStrategy.GROWTH
        )

        assert isinstance(opportunities, list)
        assert len(opportunities) > 0


class TestPortfolioValuation:
    """Test portfolio valuation updates"""

    @pytest.mark.asyncio
    async def test_update_portfolio_valuations(self, portfolio_manager, sample_portfolio):
        """Test portfolio valuation updates"""
        original_values = {prop.property_id: prop.current_value for prop in sample_portfolio}

        updated_properties = await portfolio_manager.update_portfolio_valuations(sample_portfolio)

        assert len(updated_properties) == len(sample_portfolio)
        assert all(prop.current_value > 0 for prop in updated_properties)
        assert all(prop.last_valuation_date <= datetime.now() for prop in updated_properties)

        # At least some valuations should have changed (due to appreciation)
        updated_values = {prop.property_id: prop.current_value for prop in updated_properties}
        assert any(updated_values[pid] != original_values[pid] for pid in original_values)


class TestPerformanceAttribution:
    """Test performance attribution analysis"""

    def test_generate_performance_attribution(self, portfolio_manager, sample_portfolio):
        """Test performance attribution calculation"""
        attribution = portfolio_manager.generate_performance_attribution(sample_portfolio)

        assert isinstance(attribution, dict)
        assert "total_portfolio_return" in attribution
        assert "property_type_attribution" in attribution
        assert "location_attribution" in attribution

        # Verify attribution components
        type_attribution = attribution["property_type_attribution"]
        location_attribution = attribution["location_attribution"]

        assert isinstance(type_attribution, dict)
        assert isinstance(location_attribution, dict)

    def test_generate_performance_attribution_empty_portfolio(self, portfolio_manager):
        """Test performance attribution with empty portfolio"""
        empty_portfolio = []
        attribution = portfolio_manager.generate_performance_attribution(empty_portfolio)

        assert attribution["total_portfolio_return"] == 0
        assert len(attribution["property_type_attribution"]) == 0
        assert len(attribution["location_attribution"]) == 0


class TestDataValidation:
    """Test data validation and edge cases"""

    @pytest.mark.asyncio
    async def test_analyze_portfolio_with_invalid_data(self, portfolio_manager, sample_uhnw_client):
        """Test portfolio analysis with invalid property data"""
        invalid_property = PortfolioProperty(
            property_id="INVALID-001",
            address="",
            property_type=PropertyType.LUXURY_CONDO,
            purchase_date=datetime.now(),
            purchase_price=0,  # Invalid price
            current_value=-1000,  # Invalid value
            square_footage=0,
            lot_size=0.0,
            bedrooms=0,
            bathrooms=0.0,
            neighborhood="",
            zip_code=""
        )

        invalid_portfolio = [invalid_property]
        analysis = await portfolio_manager.analyze_portfolio(sample_uhnw_client, invalid_portfolio)

        # Should handle gracefully
        assert isinstance(analysis, PortfolioAnalysis)
        assert analysis.total_portfolio_value >= 0

    def test_calculate_irr_with_zero_investment(self, portfolio_manager):
        """Test IRR calculation with zero investment"""
        zero_investment_properties = [
            PortfolioProperty(
                property_id="ZERO-001",
                address="Zero Investment Property",
                property_type=PropertyType.LUXURY_CONDO,
                purchase_date=datetime.now(),
                purchase_price=0,  # Zero investment
                current_value=1_000_000,
                square_footage=2000,
                lot_size=0.0,
                bedrooms=3,
                bathrooms=2.0,
                neighborhood="Austin",
                zip_code="78704"
            )
        ]

        irr = portfolio_manager._calculate_portfolio_irr(zero_investment_properties)
        assert irr == 0.0  # Should handle gracefully


@pytest.mark.integration
class TestIntegrationWithExistingSystems:
    """Integration tests with existing systems"""

    @pytest.mark.asyncio
    async def test_integration_with_cache_service(self, portfolio_manager, sample_portfolio):
        """Test integration with cache service"""
        with patch.object(portfolio_manager.cache, 'get', return_value=None):
            with patch.object(portfolio_manager.cache, 'set', return_value=True):
                updated_portfolio = await portfolio_manager.update_portfolio_valuations(sample_portfolio)
                assert updated_portfolio is not None

    @pytest.mark.asyncio
    async def test_integration_with_property_matcher(self, portfolio_manager, sample_uhnw_client):
        """Test integration with property matcher service"""
        opportunities = await portfolio_manager.identify_acquisition_opportunities(
            sample_uhnw_client,
            target_budget=2_000_000
        )

        # Should return opportunities even with mocked property matcher
        assert isinstance(opportunities, list)


@pytest.mark.performance
class TestPerformance:
    """Performance tests for portfolio management"""

    @pytest.mark.asyncio
    async def test_portfolio_analysis_performance(self, portfolio_manager, sample_uhnw_client, sample_portfolio):
        """Test portfolio analysis performance"""
        import time

        start_time = time.time()
        await portfolio_manager.analyze_portfolio(sample_uhnw_client, sample_portfolio)
        end_time = time.time()

        # Should complete within reasonable time
        processing_time = end_time - start_time
        assert processing_time < 10.0  # Should be under 10 seconds

    @pytest.mark.asyncio
    async def test_large_portfolio_performance(self, portfolio_manager, sample_uhnw_client):
        """Test performance with large portfolio"""
        import time

        # Create large portfolio
        large_portfolio = []
        for i in range(50):  # 50 properties
            property_data = PortfolioProperty(
                property_id=f"LARGE-{i:03d}",
                address=f"Property Address {i}",
                property_type=PropertyType.INVESTMENT_PROPERTY,
                purchase_date=datetime.now() - timedelta(days=365 * 2),
                purchase_price=1_000_000 + (i * 50_000),
                current_value=1_100_000 + (i * 55_000),
                square_footage=2000 + (i * 100),
                lot_size=1.0,
                bedrooms=3 + (i % 3),
                bathrooms=2.0 + (i % 2),
                neighborhood="Test Neighborhood",
                zip_code="78704"
            )
            large_portfolio.append(property_data)

        start_time = time.time()
        analysis = await portfolio_manager.analyze_portfolio(sample_uhnw_client, large_portfolio)
        end_time = time.time()

        # Should handle large portfolio efficiently
        processing_time = end_time - start_time
        assert processing_time < 30.0  # Should complete in under 30 seconds
        assert analysis.total_portfolio_value > 50_000_000  # Sanity check


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])