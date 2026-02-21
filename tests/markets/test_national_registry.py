"""
Tests for National Market Registry

Comprehensive test suite for national market expansion, corporate headquarters
mapping, and Fortune 500 relocation program management.

Author: EnterpriseHub AI
Created: 2026-01-18
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from ghl_real_estate_ai.markets.national_registry import (
    CorporateHeadquarters,
    CorporatePartnerTier,
    CrossMarketInsights,
    MarketExpansionTarget,
    NationalMarketRegistry,
    get_corporate_program,
    get_market_migration_insights,
    get_national_market_registry,
)


@pytest.fixture
def mock_cache_service():
    """Mock cache service"""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_base_registry():
    """Mock base market registry"""
    registry = Mock()
    registry.list_markets.return_value = ["rancho_cucamonga", "denver", "phoenix", "seattle"]
    registry.get_market_config.return_value = {
        "market_id": "denver",
        "market_name": "Denver Metropolitan Area",
        "market_type": "tech_hub",
        "median_home_price": 565000,
        "price_appreciation_1y": 8.5,
        "demographics": {"population": 2963821, "median_household_income": 78285, "population_growth_rate": 0.028},
    }
    registry.get_market_service = Mock(return_value=Mock())
    registry.service_classes = {}
    return registry


@pytest.fixture
def mock_claude_assistant():
    """Mock Claude assistant"""
    assistant = Mock()
    assistant.generate_strategic_insights = AsyncMock(return_value="Strategic insights generated")
    return assistant


@pytest.fixture
def national_registry(mock_cache_service, mock_base_registry, mock_claude_assistant):
    """Create national registry with mocked dependencies"""
    with (
        patch("ghl_real_estate_ai.markets.national_registry.get_cache_service", return_value=mock_cache_service),
        patch("ghl_real_estate_ai.markets.national_registry.ClaudeAssistant", return_value=mock_claude_assistant),
        patch("ghl_real_estate_ai.markets.national_registry.get_market_registry", return_value=mock_base_registry),
        patch("pathlib.Path.mkdir"),
        patch("pathlib.Path.exists", return_value=False),
        patch("builtins.open", mock_open()),
    ):
        registry = NationalMarketRegistry(mock_base_registry)
        return registry


@pytest.fixture
def sample_corporate_headquarters():
    """Sample corporate headquarters for testing"""
    return CorporateHeadquarters(
        company_name="Test Corporation",
        ticker_symbol="TEST",
        industry="Technology",
        headquarters_location=(37.7749, -122.4194),
        headquarters_city="San Francisco",
        headquarters_state="CA",
        employee_count=50000,
        fortune_ranking=100,
        partnership_tier=CorporatePartnerTier.GOLD,
        preferred_markets=["denver", "rancho_cucamonga", "seattle"],
        relocation_volume_annual=200,
        average_relocation_budget=85000.0,
        contact_info={"hr_director": "test@test.com", "phone": "+1-555-0123", "program_manager": "Jane Smith"},
        program_start_date=datetime(2024, 1, 1),
        last_updated=datetime.now(),
    )


class TestNationalMarketRegistry:
    """Test suite for NationalMarketRegistry class"""

    def test_initialization(self, national_registry):
        """Test registry initialization"""
        assert national_registry.base_registry is not None
        assert national_registry.cache is not None
        assert isinstance(national_registry.corporate_headquarters, dict)
        assert isinstance(national_registry.expansion_targets, dict)
        assert isinstance(national_registry.corporate_partnerships, dict)

    def test_load_corporate_headquarters_creates_initial_data(self, national_registry):
        """Test that initial corporate headquarters data is created"""
        # Should have created initial Fortune 500 data
        assert len(national_registry.corporate_headquarters) >= 5

        # Verify key companies are included
        company_ids = list(national_registry.corporate_headquarters.keys())
        expected_companies = ["amazon", "microsoft", "google", "boeing", "intel"]

        for expected in expected_companies:
            assert any(expected in comp_id for comp_id in company_ids)

    def test_initial_expansion_targets(self, national_registry):
        """Test initial expansion targets creation"""
        # Should have created targets for new markets
        assert len(national_registry.expansion_targets) >= 3

        # Verify target markets
        target_markets = list(national_registry.expansion_targets.keys())
        expected_targets = ["denver", "phoenix", "seattle"]

        for expected in expected_targets:
            assert expected in target_markets

        # Verify target structure
        for target in national_registry.expansion_targets.values():
            assert isinstance(target, MarketExpansionTarget)
            assert target.expansion_priority >= 1
            assert target.estimated_annual_revenue_potential > 0
            assert target.investment_required > 0

    @pytest.mark.asyncio
    async def test_get_corporate_relocation_program(self, national_registry):
        """Test getting corporate relocation program details"""
        # Test with existing company (Amazon)
        program = await national_registry.get_corporate_relocation_program("amazon")

        assert program is not None
        assert "company_info" in program
        assert "headquarters" in program
        assert "relocation_program" in program
        assert "preferred_market_details" in program
        assert "contact_information" in program
        assert "service_tiers" in program

        # Verify company info
        company_info = program["company_info"]
        assert company_info["name"] == "Amazon"
        assert company_info["ticker"] == "AMZN"
        assert company_info["partnership_tier"] == CorporatePartnerTier.PLATINUM.value

        # Verify relocation program details
        relocation_program = program["relocation_program"]
        assert relocation_program["annual_volume"] > 0
        assert relocation_program["average_budget"] > 0
        assert isinstance(relocation_program["preferred_markets"], list)

    @pytest.mark.asyncio
    async def test_get_corporate_relocation_program_not_found(self, national_registry):
        """Test getting program for non-existent company"""
        program = await national_registry.get_corporate_relocation_program("nonexistent")
        assert program is None

    def test_find_corporate_headquarters(self, national_registry):
        """Test finding corporate headquarters by various identifiers"""
        # Test by company name
        found = national_registry._find_corporate_headquarters("Amazon")
        assert found is not None
        assert found.company_name == "Amazon"

        # Test by ticker symbol
        found = national_registry._find_corporate_headquarters("AMZN")
        assert found is not None
        assert found.ticker_symbol == "AMZN"

        # Test case insensitive
        found = national_registry._find_corporate_headquarters("amazon")
        assert found is not None

        # Test partial match
        found = national_registry._find_corporate_headquarters("Microsoft")
        assert found is not None

        # Test not found
        found = national_registry._find_corporate_headquarters("Nonexistent Corp")
        assert found is None

    def test_get_service_tiers_for_partnership(self, national_registry):
        """Test service tier definitions for different partnership levels"""
        # Test Platinum tier
        platinum_tiers = national_registry._get_service_tiers_for_partnership(CorporatePartnerTier.PLATINUM)
        assert platinum_tiers["dedicated_relocation_specialist"] is True
        assert platinum_tiers["24_7_support"] is True
        assert platinum_tiers["volume_discounts"] == 15
        assert platinum_tiers["quarterly_business_reviews"] is True

        # Test Gold tier
        gold_tiers = national_registry._get_service_tiers_for_partnership(CorporatePartnerTier.GOLD)
        assert gold_tiers["dedicated_relocation_specialist"] is True
        assert gold_tiers["24_7_support"] is False
        assert gold_tiers["volume_discounts"] == 10

        # Test Silver tier
        silver_tiers = national_registry._get_service_tiers_for_partnership(CorporatePartnerTier.SILVER)
        assert silver_tiers["dedicated_relocation_specialist"] is False
        assert silver_tiers["volume_discounts"] == 5

        # Test Bronze tier
        bronze_tiers = national_registry._get_service_tiers_for_partnership(CorporatePartnerTier.BRONZE)
        assert bronze_tiers["volume_discounts"] == 0
        assert bronze_tiers["quarterly_business_reviews"] is False

    @pytest.mark.asyncio
    async def test_get_cross_market_insights(self, national_registry):
        """Test cross-market migration insights"""
        insights = await national_registry.get_cross_market_insights("rancho_cucamonga", "denver")

        assert insights is not None
        assert isinstance(insights, CrossMarketInsights)
        assert insights.source_market == "rancho_cucamonga"
        assert insights.target_market == "denver"
        assert insights.migration_volume > 0
        assert isinstance(insights.average_salary_delta, float)
        assert isinstance(insights.cost_of_living_comparison, float)
        assert isinstance(insights.housing_affordability_ratio, float)
        assert isinstance(insights.corporate_driving_factors, list)
        assert isinstance(insights.seasonal_patterns, dict)
        assert isinstance(insights.top_employment_sectors, list)
        assert 0.0 <= insights.success_probability <= 1.0

    @pytest.mark.asyncio
    async def test_get_cross_market_insights_invalid_markets(self, national_registry):
        """Test cross-market insights with invalid market"""
        insights = await national_registry.get_cross_market_insights("invalid", "denver")
        assert insights is None

    def test_estimate_migration_volume(self, national_registry):
        """Test migration volume estimation"""
        volume = national_registry._estimate_migration_volume("rancho_cucamonga", "denver")
        assert isinstance(volume, int)
        assert volume > 0

        # Volume should be based on market characteristics
        # Larger or more attractive markets should have higher migration
        volume_large = national_registry._estimate_migration_volume("houston", "seattle")
        volume_small = national_registry._estimate_migration_volume("san_antonio", "phoenix")

        # Both should be positive integers
        assert isinstance(volume_large, int) and volume_large > 0
        assert isinstance(volume_small, int) and volume_small > 0

    def test_find_shared_employers(self, national_registry):
        """Test finding employers operating in multiple markets"""
        shared = national_registry._find_shared_employers("denver", "seattle")
        assert isinstance(shared, list)

        # Should find companies like Amazon, Microsoft, Google that operate in both markets
        shared_names = [name.lower() for name in shared]
        tech_companies = ["amazon", "microsoft", "google"]

        # At least one tech company should be in both markets
        assert any(tech in " ".join(shared_names) for tech in tech_companies)

    def test_calculate_salary_delta(self, national_registry):
        """Test salary delta calculation"""
        source_config = {"demographics": {"median_household_income": 70000}}
        target_config = {"demographics": {"median_household_income": 85000}}

        delta = national_registry._calculate_salary_delta(source_config, target_config)
        expected_delta = ((85000 - 70000) / 70000) * 100  # ~21.43%
        assert abs(delta - expected_delta) < 0.01

    def test_calculate_col_comparison(self, national_registry):
        """Test cost of living comparison"""
        source_config = {"median_home_price": 400000}
        target_config = {"median_home_price": 500000}

        col_comparison = national_registry._calculate_col_comparison(source_config, target_config)
        expected = ((500000 - 400000) / 400000) * 100  # 25%
        assert abs(col_comparison - expected) < 0.01

    def test_calculate_housing_affordability(self, national_registry):
        """Test housing affordability calculation"""
        target_config = {"median_home_price": 600000, "demographics": {"median_household_income": 100000}}

        ratio = national_registry._calculate_housing_affordability(target_config, target_config)
        expected_ratio = 600000 / 100000  # 6.0
        assert ratio == expected_ratio

    def test_identify_corporate_factors(self, national_registry):
        """Test corporate driving factors identification"""
        factors = national_registry._identify_corporate_factors("rancho_cucamonga", "denver")
        assert isinstance(factors, list)
        assert len(factors) > 0
        assert all(isinstance(factor, str) for factor in factors)

    def test_analyze_seasonal_patterns(self, national_registry):
        """Test seasonal pattern analysis"""
        patterns = national_registry._analyze_seasonal_patterns("rancho_cucamonga", "denver")
        assert isinstance(patterns, dict)
        assert "Q1" in patterns
        assert "Q2" in patterns
        assert "Q3" in patterns
        assert "Q4" in patterns

        # All quarters should sum to 100 (percentages)
        total = sum(patterns.values())
        assert 95 <= total <= 105  # Allow small rounding variance

    def test_get_top_sectors(self, national_registry):
        """Test top employment sectors identification"""
        # Test tech hub
        tech_config = {"market_type": "tech_hub"}
        sectors = national_registry._get_top_sectors(tech_config)
        assert "Technology" in sectors

        # Test finance hub
        finance_config = {"market_type": "finance_hub"}
        sectors = national_registry._get_top_sectors(finance_config)
        assert "Financial Services" in sectors

        # Test unknown type defaults
        unknown_config = {"market_type": "unknown"}
        sectors = national_registry._get_top_sectors(unknown_config)
        assert "Professional Services" in sectors

    def test_calculate_success_probability(self, national_registry):
        """Test success probability calculation"""
        prob = national_registry._calculate_success_probability("rancho_cucamonga", "denver")
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0

    @pytest.mark.asyncio
    async def test_get_expansion_opportunities(self, national_registry):
        """Test getting expansion opportunities"""
        opportunities = await national_registry.get_expansion_opportunities()
        assert isinstance(opportunities, list)
        assert len(opportunities) > 0

        # Should be sorted by priority and ROI
        for i in range(len(opportunities) - 1):
            current = opportunities[i]
            next_opp = opportunities[i + 1]

            # Either higher priority or equal priority with higher ROI
            assert current.expansion_priority >= next_opp.expansion_priority or (
                current.expansion_priority == next_opp.expansion_priority
                and current.roi_projection >= next_opp.roi_projection
            )

    @pytest.mark.asyncio
    async def test_get_national_market_summary(self, national_registry):
        """Test national market summary generation"""
        summary = await national_registry.get_national_market_summary()

        assert "total_markets" in summary
        assert "expansion_markets" in summary
        assert "corporate_partnerships" in summary
        assert "revenue_enhancement_target" in summary
        assert "investment_required" in summary
        assert "average_roi_projection" in summary
        assert "partnership_tiers" in summary
        assert "markets_by_type" in summary
        assert "last_updated" in summary

        # Verify data types and basic validity
        assert isinstance(summary["total_markets"], int)
        assert isinstance(summary["revenue_enhancement_target"], float)
        assert isinstance(summary["partnership_tiers"], dict)
        assert summary["total_markets"] > 0

    def test_register_corporate_partnership(self, national_registry, sample_corporate_headquarters):
        """Test registering new corporate partnership"""
        success = national_registry.register_corporate_partnership(sample_corporate_headquarters)
        assert success is True

        # Verify partnership was registered
        corp_id = "test_corporation"
        assert corp_id in national_registry.corporate_headquarters

        registered = national_registry.corporate_headquarters[corp_id]
        assert registered.company_name == sample_corporate_headquarters.company_name
        assert registered.ticker_symbol == sample_corporate_headquarters.ticker_symbol
        assert registered.partnership_tier == sample_corporate_headquarters.partnership_tier

    def test_health_check(self, national_registry):
        """Test registry health check"""
        health = national_registry.health_check()

        assert "status" in health
        assert "national_registry" in health
        assert "base_registry" in health
        assert "cache_available" in health
        assert "last_check" in health

        assert health["status"] == "healthy"
        assert isinstance(health["national_registry"], dict)
        assert "corporate_headquarters" in health["national_registry"]
        assert "expansion_targets" in health["national_registry"]

    def test_singleton_pattern(self):
        """Test singleton pattern for global registry instance"""
        with (
            patch("ghl_real_estate_ai.markets.national_registry.get_cache_service"),
            patch("ghl_real_estate_ai.markets.national_registry.get_market_registry"),
            patch("ghl_real_estate_ai.markets.national_registry.ClaudeAssistant"),
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", mock_open()),
        ):
            registry1 = get_national_market_registry()
            registry2 = get_national_market_registry()

            assert registry1 is registry2

    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience functions"""
        with patch("ghl_real_estate_ai.markets.national_registry.get_national_market_registry") as mock_registry:
            mock_instance = Mock()
            mock_instance.get_corporate_relocation_program = AsyncMock(return_value={"test": "data"})
            mock_instance.get_cross_market_insights = AsyncMock(return_value=Mock())
            mock_registry.return_value = mock_instance

            # Test get_corporate_program
            result = await get_corporate_program("test_company")
            mock_instance.get_corporate_relocation_program.assert_called_once_with("test_company")
            assert result == {"test": "data"}

            # Test get_market_migration_insights
            insights = await get_market_migration_insights("rancho_cucamonga", "denver")
            mock_instance.get_cross_market_insights.assert_called_once_with("rancho_cucamonga", "denver")
            assert insights is not None


class TestDataStructures:
    """Test data structure classes"""

    def test_corporate_headquarters_creation(self):
        """Test CorporateHeadquarters data structure"""
        headquarters = CorporateHeadquarters(
            company_name="Test Corp",
            ticker_symbol="TEST",
            industry="Technology",
            headquarters_location=(40.7128, -74.0060),
            headquarters_city="New York",
            headquarters_state="NY",
            employee_count=10000,
            fortune_ranking=250,
            partnership_tier=CorporatePartnerTier.SILVER,
            preferred_markets=["denver", "rancho_cucamonga"],
            relocation_volume_annual=50,
            average_relocation_budget=70000.0,
            contact_info={"email": "test@test.com"},
            program_start_date=datetime(2024, 6, 1),
            last_updated=datetime.now(),
        )

        assert headquarters.company_name == "Test Corp"
        assert headquarters.ticker_symbol == "TEST"
        assert headquarters.partnership_tier == CorporatePartnerTier.SILVER
        assert len(headquarters.preferred_markets) == 2
        assert headquarters.relocation_volume_annual == 50

    def test_market_expansion_target_creation(self):
        """Test MarketExpansionTarget data structure"""
        target = MarketExpansionTarget(
            market_id="test_market",
            market_name="Test Market",
            state="TX",
            region="Test Region",
            expansion_priority=8,
            corporate_headquarters_count=5,
            fortune_500_presence=3,
            estimated_annual_revenue_potential=500000.0,
            market_entry_complexity="medium",
            competitive_landscape={"competitors": ["A", "B"]},
            expansion_timeline="Q2 2026",
            investment_required=150000.0,
            roi_projection=3.5,
        )

        assert target.market_id == "test_market"
        assert target.expansion_priority == 8
        assert target.estimated_annual_revenue_potential == 500000.0
        assert target.roi_projection == 3.5

    def test_cross_market_insights_creation(self):
        """Test CrossMarketInsights data structure"""
        insights = CrossMarketInsights(
            source_market="rancho_cucamonga",
            target_market="denver",
            migration_volume=120,
            average_salary_delta=15.5,
            cost_of_living_comparison=8.2,
            housing_affordability_ratio=6.5,
            corporate_driving_factors=["Tech growth", "Quality of life"],
            seasonal_patterns={"Q1": 30, "Q2": 25, "Q3": 20, "Q4": 25},
            top_employment_sectors=["Technology", "Healthcare"],
            success_probability=0.82,
        )

        assert insights.source_market == "rancho_cucamonga"
        assert insights.target_market == "denver"
        assert insights.migration_volume == 120
        assert 0.0 <= insights.success_probability <= 1.0
        assert len(insights.corporate_driving_factors) == 2


if __name__ == "__main__":
    pytest.main([__file__])
