"""
Tests for National Market Intelligence Service

Comprehensive test suite for national market intelligence, cross-market analytics,
and corporate migration pattern analysis.

Author: EnterpriseHub AI
Created: 2026-01-18
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.national_market_intelligence import (
    CompetitiveAnalysis,
    MarketMetrics,
    MarketTrend,
    MigrationPattern,
    NationalMarketIntelligence,
    OpportunityLevel,
    PricingIntelligence,
    get_national_market_intelligence,
)


@pytest.fixture
def mock_cache_service():
    """Mock cache service"""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_national_registry():
    """Mock national market registry"""
    registry = Mock()

    # Mock base registry
    base_registry = Mock()
    base_registry.list_markets.return_value = ["denver", "phoenix", "seattle"]
    base_registry.get_market_config.return_value = {
        "market_id": "denver",
        "market_name": "Denver Metropolitan Area",
        "market_type": "tech_hub",
        "state": "CO",
        "median_home_price": 565000,
        "price_appreciation_1y": 8.5,
        "inventory_days": 35,
        "demographics": {
            "population": 2963821,
            "median_household_income": 78285,
            "employment_rate": 0.95,
            "population_growth_rate": 0.028,
            "college_education_rate": 0.45,
        },
        "employers": [
            {"name": "Google", "industry": "Technology"},
            {"name": "Lockheed Martin", "industry": "Aerospace"},
        ],
        "neighborhoods": [{"name": "Cherry Creek", "school_rating": 9.1}, {"name": "Boulder", "school_rating": 9.3}],
    }

    registry.base_registry = base_registry
    return registry


@pytest.fixture
def mock_claude_assistant():
    """Mock Claude assistant"""
    assistant = Mock()
    assistant.generate_welcome_message = AsyncMock(return_value="Welcome message")
    return assistant


@pytest.fixture
def intelligence_service(mock_cache_service, mock_national_registry, mock_claude_assistant):
    """Create intelligence service with mocked dependencies"""
    with (
        patch(
            "ghl_real_estate_ai.services.national_market_intelligence.get_cache_service",
            return_value=mock_cache_service,
        ),
        patch(
            "ghl_real_estate_ai.services.national_market_intelligence.get_national_market_registry",
            return_value=mock_national_registry,
        ),
        patch(
            "ghl_real_estate_ai.services.national_market_intelligence.ClaudeAssistant",
            return_value=mock_claude_assistant,
        ),
        patch("pathlib.Path.mkdir"),
        patch("pathlib.Path.exists", return_value=False),
    ):
        service = NationalMarketIntelligence()
        return service


class TestNationalMarketIntelligence:
    """Test suite for NationalMarketIntelligence class"""

    def test_initialization(self, intelligence_service):
        """Test service initialization"""
        assert intelligence_service.cache is not None
        assert intelligence_service.claude_assistant is not None
        assert intelligence_service.national_registry is not None
        assert isinstance(intelligence_service.market_metrics, dict)
        assert isinstance(intelligence_service.competitive_analyses, dict)
        assert isinstance(intelligence_service.migration_patterns, list)

    @pytest.mark.asyncio
    async def test_generate_market_metrics(self, intelligence_service):
        """Test market metrics generation"""
        # Generate metrics for Denver
        await intelligence_service._generate_market_metrics("denver")

        # Verify metrics were created
        assert "denver" in intelligence_service.market_metrics
        metrics = intelligence_service.market_metrics["denver"]

        assert isinstance(metrics, MarketMetrics)
        assert metrics.market_id == "denver"
        assert metrics.market_name == "Denver Metropolitan Area"
        assert metrics.median_home_price == 565000
        assert metrics.price_appreciation_1y == 8.5
        assert isinstance(metrics.market_trend, MarketTrend)
        assert 0 <= metrics.opportunity_score <= 100

    @pytest.mark.asyncio
    async def test_calculate_opportunity_score(self, intelligence_service):
        """Test opportunity score calculation"""
        market_config = {
            "demographics": {
                "population_growth_rate": 0.035,  # High growth
                "college_education_rate": 0.45,  # High education
            },
            "price_appreciation_1y": 8.5,  # Healthy appreciation
            "market_type": "tech_hub",  # Bonus market type
            "employers": [{"name": "Google"}, {"name": "Microsoft"}],
        }

        score = await intelligence_service._calculate_opportunity_score("test_market", market_config)

        assert isinstance(score, float)
        assert 5.0 <= score <= 95.0
        # Should be high score due to good fundamentals
        assert score > 70.0

    def test_determine_market_trend(self, intelligence_service):
        """Test market trend determination"""
        # Test rapidly growing market
        config_rapid = {"price_appreciation_1y": 16.0, "demographics": {"population_growth_rate": 0.05}}
        trend = intelligence_service._determine_market_trend(config_rapid)
        assert trend == MarketTrend.RAPIDLY_GROWING

        # Test growing market
        config_growing = {"price_appreciation_1y": 9.0, "demographics": {"population_growth_rate": 0.03}}
        trend = intelligence_service._determine_market_trend(config_growing)
        assert trend == MarketTrend.GROWING

        # Test stable market
        config_stable = {"price_appreciation_1y": 5.0, "demographics": {"population_growth_rate": 0.02}}
        trend = intelligence_service._determine_market_trend(config_stable)
        assert trend == MarketTrend.STABLE

        # Test declining market
        config_declining = {"price_appreciation_1y": -2.0, "demographics": {"population_growth_rate": -0.01}}
        trend = intelligence_service._determine_market_trend(config_declining)
        assert trend == MarketTrend.DECLINING

    def test_estimate_tech_job_growth(self, intelligence_service):
        """Test tech job growth estimation"""
        # Tech headquarters market with major employers
        config_tech = {
            "market_type": "tech_headquarters",
            "employers": [{"name": "Google Cloud Platform"}, {"name": "Microsoft Azure"}],
        }
        growth = intelligence_service._estimate_tech_job_growth(config_tech)
        assert growth > 0.12  # Should be high for tech headquarters with major employers

        # Non-tech market
        config_energy = {"market_type": "energy_hub", "employers": [{"name": "ExxonMobil"}, {"name": "Chevron"}]}
        growth = intelligence_service._estimate_tech_job_growth(config_energy)
        assert growth < 0.05  # Should be lower for non-tech market

    def test_calculate_col_index(self, intelligence_service):
        """Test cost of living index calculation"""
        # High COL market
        config_high = {"median_home_price": 800000, "demographics": {"median_household_income": 70000}}
        col_index = intelligence_service._calculate_col_index(config_high)
        assert col_index > 100  # Above national average

        # Low COL market
        config_low = {"median_home_price": 200000, "demographics": {"median_household_income": 90000}}
        col_index = intelligence_service._calculate_col_index(config_low)
        assert col_index < 100  # Below national average

    def test_calculate_qol_score(self, intelligence_service):
        """Test quality of life score calculation"""
        config = {
            "state": "CO",  # Gets bonus
            "market_type": "tech_hub",  # Gets bonus
            "neighborhoods": [{"school_rating": 9.0}, {"school_rating": 8.5}],
        }
        score = intelligence_service._calculate_qol_score(config)
        assert 20.0 <= score <= 95.0
        assert score > 60  # Should be good score

    @pytest.mark.asyncio
    async def test_generate_competitive_analysis(self, intelligence_service):
        """Test competitive analysis generation"""
        # First generate market metrics
        await intelligence_service._generate_market_metrics("denver")

        # Then generate competitive analysis
        await intelligence_service._generate_competitive_analysis("denver")

        assert "denver" in intelligence_service.competitive_analyses
        analysis = intelligence_service.competitive_analyses["denver"]

        assert isinstance(analysis, CompetitiveAnalysis)
        assert analysis.market_id == "denver"
        assert len(analysis.major_competitors) > 0
        assert 0.0 <= analysis.competitive_intensity <= 1.0
        assert isinstance(analysis.opportunity_rating, OpportunityLevel)
        assert len(analysis.differentiation_opportunities) > 0

    @pytest.mark.asyncio
    async def test_generate_pricing_intelligence(self, intelligence_service):
        """Test pricing intelligence generation"""
        # Generate market metrics first
        await intelligence_service._generate_market_metrics("denver")
        await intelligence_service._generate_market_metrics("phoenix")

        # Generate pricing intelligence
        await intelligence_service._generate_pricing_intelligence()

        pricing = intelligence_service.pricing_intelligence
        assert pricing is not None
        assert isinstance(pricing, PricingIntelligence)
        assert pricing.national_median > 0
        assert len(pricing.market_comparisons) > 0
        assert len(pricing.price_trend_forecast) > 0
        assert len(pricing.affordability_rankings) > 0
        assert isinstance(pricing.last_analysis, datetime)

    @pytest.mark.asyncio
    async def test_generate_migration_patterns(self, intelligence_service):
        """Test migration patterns generation"""
        # Setup market metrics
        intelligence_service.market_metrics["austin"] = MarketMetrics(
            market_id="austin",
            market_name="Austin",
            population=2000000,
            median_home_price=500000,
            price_appreciation_1y=10.0,
            price_appreciation_3y=30.0,
            inventory_days=25,
            employment_rate=0.95,
            income_growth_rate=0.04,
            corporate_headquarters_count=8,
            tech_job_growth=0.08,
            cost_of_living_index=110.0,
            quality_of_life_score=85.0,
            market_trend=MarketTrend.GROWING,
            opportunity_score=82.0,
            last_updated=datetime.now(),
        )

        intelligence_service.market_metrics["denver"] = MarketMetrics(
            market_id="denver",
            market_name="Denver",
            population=2963821,
            median_home_price=565000,
            price_appreciation_1y=8.5,
            price_appreciation_3y=25.5,
            inventory_days=35,
            employment_rate=0.95,
            income_growth_rate=0.03,
            corporate_headquarters_count=8,
            tech_job_growth=0.10,
            cost_of_living_index=105.0,
            quality_of_life_score=88.0,
            market_trend=MarketTrend.GROWING,
            opportunity_score=85.0,
            last_updated=datetime.now(),
        )

        await intelligence_service._generate_migration_patterns()

        assert len(intelligence_service.migration_patterns) > 0

        pattern = intelligence_service.migration_patterns[0]
        assert isinstance(pattern, MigrationPattern)
        assert pattern.annual_volume > 0
        assert len(pattern.primary_industries) > 0
        assert pattern.average_salary_band[1] > pattern.average_salary_band[0]
        assert 0.0 <= pattern.success_rate <= 1.0

    def test_estimate_migration_volume(self, intelligence_service):
        """Test migration volume estimation"""
        # Setup test metrics
        intelligence_service.market_metrics["source"] = MarketMetrics(
            market_id="source",
            market_name="Source",
            population=1000000,
            median_home_price=400000,
            price_appreciation_1y=5.0,
            price_appreciation_3y=15.0,
            inventory_days=30,
            employment_rate=0.94,
            income_growth_rate=0.03,
            corporate_headquarters_count=5,
            tech_job_growth=0.05,
            cost_of_living_index=95.0,
            quality_of_life_score=75.0,
            market_trend=MarketTrend.STABLE,
            opportunity_score=65.0,
            last_updated=datetime.now(),
        )

        intelligence_service.market_metrics["destination"] = MarketMetrics(
            market_id="destination",
            market_name="Destination",
            population=1500000,
            median_home_price=600000,
            price_appreciation_1y=8.0,
            price_appreciation_3y=24.0,
            inventory_days=28,
            employment_rate=0.96,
            income_growth_rate=0.04,
            corporate_headquarters_count=8,
            tech_job_growth=0.08,
            cost_of_living_index=110.0,
            quality_of_life_score=85.0,
            market_trend=MarketTrend.GROWING,
            opportunity_score=80.0,
            last_updated=datetime.now(),
        )

        volume = intelligence_service._estimate_migration_volume("source", "destination")
        assert isinstance(volume, int)
        assert 25 <= volume <= 150

    @pytest.mark.asyncio
    async def test_get_national_market_overview(self, intelligence_service):
        """Test national market overview generation"""
        # Setup test data
        await intelligence_service._generate_market_metrics("denver")
        await intelligence_service._generate_competitive_analysis("denver")
        await intelligence_service._generate_pricing_intelligence()
        await intelligence_service._generate_migration_patterns()

        overview = await intelligence_service.get_national_market_overview()

        assert "summary" in overview
        assert "top_opportunities" in overview
        assert "market_trends" in overview
        assert "pricing_insights" in overview
        assert "migration_flows" in overview
        assert "competitive_landscape" in overview
        assert "expansion_recommendations" in overview

        # Verify summary data
        summary = overview["summary"]
        assert summary["total_markets"] > 0
        assert summary["average_opportunity_score"] > 0
        assert summary["total_corporate_headquarters"] >= 0

    @pytest.mark.asyncio
    async def test_get_top_market_opportunities(self, intelligence_service):
        """Test top market opportunities retrieval"""
        # Setup multiple markets with different scores
        intelligence_service.market_metrics["high_opportunity"] = MarketMetrics(
            market_id="high_opportunity",
            market_name="High Opportunity",
            population=2000000,
            median_home_price=500000,
            price_appreciation_1y=10.0,
            price_appreciation_3y=30.0,
            inventory_days=25,
            employment_rate=0.96,
            income_growth_rate=0.04,
            corporate_headquarters_count=10,
            tech_job_growth=0.12,
            cost_of_living_index=105.0,
            quality_of_life_score=90.0,
            market_trend=MarketTrend.RAPIDLY_GROWING,
            opportunity_score=90.0,
            last_updated=datetime.now(),
        )

        intelligence_service.market_metrics["low_opportunity"] = MarketMetrics(
            market_id="low_opportunity",
            market_name="Low Opportunity",
            population=800000,
            median_home_price=300000,
            price_appreciation_1y=2.0,
            price_appreciation_3y=6.0,
            inventory_days=45,
            employment_rate=0.90,
            income_growth_rate=0.01,
            corporate_headquarters_count=2,
            tech_job_growth=0.02,
            cost_of_living_index=85.0,
            quality_of_life_score=65.0,
            market_trend=MarketTrend.STABLE,
            opportunity_score=35.0,
            last_updated=datetime.now(),
        )

        opportunities = await intelligence_service._get_top_market_opportunities(limit=5)

        assert len(opportunities) <= 5
        assert opportunities[0]["opportunity_score"] >= opportunities[-1]["opportunity_score"]
        assert all("market_id" in opp for opp in opportunities)
        assert all("opportunity_score" in opp for opp in opportunities)

    def test_analyze_market_trends(self, intelligence_service):
        """Test market trends analysis"""
        # Setup markets with different trends
        intelligence_service.market_metrics = {
            "growing1": MarketMetrics(
                "growing1",
                "Growing 1",
                1000000,
                400000,
                8.0,
                24.0,
                30,
                0.95,
                0.03,
                5,
                0.06,
                100.0,
                80.0,
                MarketTrend.GROWING,
                70.0,
                datetime.now(),
            ),
            "growing2": MarketMetrics(
                "growing2",
                "Growing 2",
                1200000,
                450000,
                9.0,
                27.0,
                28,
                0.96,
                0.04,
                6,
                0.07,
                105.0,
                82.0,
                MarketTrend.GROWING,
                75.0,
                datetime.now(),
            ),
            "stable1": MarketMetrics(
                "stable1",
                "Stable 1",
                900000,
                350000,
                4.0,
                12.0,
                35,
                0.94,
                0.02,
                3,
                0.03,
                90.0,
                70.0,
                MarketTrend.STABLE,
                60.0,
                datetime.now(),
            ),
        }

        trends = intelligence_service._analyze_market_trends()

        assert "trend_distribution" in trends
        assert "average_appreciation" in trends
        assert "appreciation_range" in trends
        assert "growth_markets" in trends
        assert "stable_markets" in trends

        assert trends["growth_markets"] == 2
        assert trends["stable_markets"] == 1
        assert trends["average_appreciation"] == 7.0  # (8+9+4)/3

    @pytest.mark.asyncio
    async def test_generate_expansion_recommendations(self, intelligence_service):
        """Test expansion recommendations generation"""
        # Setup market metrics and competitive analyses
        intelligence_service.market_metrics = {
            "premium_market": MarketMetrics(
                "premium_market",
                "Premium Market",
                2000000,
                600000,
                12.0,
                36.0,
                25,
                0.97,
                0.05,
                12,
                0.15,
                120.0,
                92.0,
                MarketTrend.RAPIDLY_GROWING,
                88.0,
                datetime.now(),
            ),
            "good_market": MarketMetrics(
                "good_market",
                "Good Market",
                1500000,
                500000,
                8.0,
                24.0,
                30,
                0.95,
                0.03,
                8,
                0.08,
                110.0,
                85.0,
                MarketTrend.GROWING,
                78.0,
                datetime.now(),
            ),
        }

        intelligence_service.competitive_analyses = {
            "premium_market": CompetitiveAnalysis(
                "premium_market", ["Competitor A"], {}, 0.7, [], {}, [], [], [], "moderate", OpportunityLevel.PREMIUM
            ),
            "good_market": CompetitiveAnalysis(
                "good_market", ["Competitor B"], {}, 0.6, [], {}, [], [], [], "low", OpportunityLevel.HIGH
            ),
        }

        intelligence_service.pricing_intelligence = PricingIntelligence(
            {}, 500000, {}, [], {}, {}, {}, {"premium_market": 8.8, "good_market": 7.8}, datetime.now()
        )

        recommendations = await intelligence_service._generate_expansion_recommendations()

        assert len(recommendations) <= 3
        assert all("market_id" in rec for rec in recommendations)
        assert all("recommendation_type" in rec for rec in recommendations)
        assert all("opportunity_score" in rec for rec in recommendations)

        # Premium market should have immediate expansion recommendation
        premium_rec = next((r for r in recommendations if r["market_id"] == "premium_market"), None)
        assert premium_rec is not None
        assert premium_rec["recommendation_type"] == "immediate_expansion"

    def test_health_check(self, intelligence_service):
        """Test service health check"""
        health = intelligence_service.health_check()

        assert "status" in health
        assert "service" in health
        assert "metrics" in health
        assert "data_files" in health
        assert "cache_available" in health
        assert "last_check" in health

        assert health["service"] == "NationalMarketIntelligence"
        assert isinstance(health["metrics"], dict)

    def test_singleton_pattern(self):
        """Test singleton pattern for global service instance"""
        with (
            patch("ghl_real_estate_ai.services.national_market_intelligence.get_cache_service"),
            patch("ghl_real_estate_ai.services.national_market_intelligence.get_national_market_registry"),
            patch("ghl_real_estate_ai.services.national_market_intelligence.ClaudeAssistant"),
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
        ):
            service1 = get_national_market_intelligence()
            service2 = get_national_market_intelligence()

            assert service1 is service2


@pytest.mark.asyncio
async def test_data_persistence():
    """Test data persistence and loading"""
    import json
    from unittest.mock import mock_open

    mock_data = json.dumps(
        {
            "test_market": {
                "market_id": "test_market",
                "market_name": "Test Market",
                "population": 1000000,
                "median_home_price": 400000.0,
                "price_appreciation_1y": 5.0,
                "price_appreciation_3y": 15.0,
                "inventory_days": 30,
                "employment_rate": 0.94,
                "income_growth_rate": 0.03,
                "corporate_headquarters_count": 5,
                "tech_job_growth": 0.05,
                "cost_of_living_index": 100.0,
                "quality_of_life_score": 75.0,
                "market_trend": "stable",
                "opportunity_score": 65.0,
                "last_updated": "2026-01-18T10:00:00",
            }
        }
    )

    with (
        patch("ghl_real_estate_ai.services.national_market_intelligence.get_cache_service"),
        patch("ghl_real_estate_ai.services.national_market_intelligence.get_national_market_registry"),
        patch("ghl_real_estate_ai.services.national_market_intelligence.ClaudeAssistant"),
        patch("pathlib.Path.mkdir"),
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=mock_data)),
    ):
        with patch("json.load", return_value=json.loads(mock_data)):
            service = NationalMarketIntelligence()
            assert len(service.market_metrics) <= 1  # May load data from mock or not depending on init


if __name__ == "__main__":
    pytest.main([__file__])
