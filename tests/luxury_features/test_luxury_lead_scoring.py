"""
Comprehensive Tests for Luxury Lead Scoring Engine
Test suite for UHNW lead qualification and luxury scoring features

Tests cover:
- Net worth estimation and analysis
- Luxury lifestyle profiling
- Investment capacity assessment
- Buying signal detection
- Competitive intelligence
- Master scoring algorithm
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.luxury_lead_scoring_engine import (
    CompetitiveIntelligence,
    InvestmentCapacityAnalysis,
    LuxuryBuyingSignal,
    LuxuryLead,
    LuxuryLeadScoringEngine,
    LuxuryLifestyleProfile,
    NetWorthIndicators,
    WealthTier,
    create_sample_luxury_lead_data,
)


@pytest.fixture
def luxury_scoring_engine():
    """Initialize luxury lead scoring engine for testing"""
    with patch.multiple(
        "ghl_real_estate_ai.services.luxury_lead_scoring_engine",
        CacheService=Mock(),
        ClaudeAssistant=Mock(),
        LLMClient=Mock(),
    ):
        engine = LuxuryLeadScoringEngine()
        # Mock the Claude response
        engine.claude.generate_claude_response = AsyncMock(return_value="Investment score: 85")
        return engine


@pytest.fixture
def sample_lead_data():
    """Sample luxury lead data for testing"""
    return create_sample_luxury_lead_data()


@pytest.fixture
def uhnw_lead_data():
    """UHNW lead data for testing high-value scenarios"""
    return {
        "lead_id": "UHNW-TEST-001",
        "contact_info": {
            "email": "founder@mega-corp.com",
            "phone": "+1-512-555-0100",
            "address": "1000 West Lake Hills Pkwy, Austin, TX 78746",
        },
        "source": "private_referral",
        "profession": "Founder & CEO",
        "company": "MegaCorp Enterprises",
        "property_search_history": [
            {
                "date": datetime.now().isoformat(),
                "min_price": 5_000_000,
                "max_price": 15_000_000,
                "location": "West Lake Hills",
                "property_type": "estate",
                "amenities": ["private_dock", "helicopter_pad", "wine_cellar", "home_theater", "spa", "guest_quarters"],
            }
        ],
        "communication_history": [
            {
                "date": datetime.now().isoformat(),
                "content": "Looking for an estate property with significant investment potential. Budget is very flexible for the right opportunity. Need comprehensive due diligence and investment analysis. Prefer off-market opportunities with privacy.",
                "type": "email",
            }
        ],
    }


class TestNetWorthAnalysis:
    """Test net worth analysis and estimation"""

    @pytest.mark.asyncio
    async def test_analyze_net_worth_indicators_basic(self, luxury_scoring_engine, sample_lead_data):
        """Test basic net worth indicator analysis"""
        indicators = await luxury_scoring_engine._analyze_net_worth_indicators(sample_lead_data)

        assert isinstance(indicators, NetWorthIndicators)
        assert indicators.estimated_net_worth > 0
        assert 0 <= indicators.net_worth_confidence <= 100
        assert indicators.investment_sophistication >= 0

    @pytest.mark.asyncio
    async def test_analyze_net_worth_uhnw_client(self, luxury_scoring_engine, uhnw_lead_data):
        """Test net worth analysis for UHNW client"""
        indicators = await luxury_scoring_engine._analyze_net_worth_indicators(uhnw_lead_data)

        # UHNW client should have high estimated net worth
        assert indicators.estimated_net_worth >= 10_000_000
        assert indicators.investment_sophistication >= 70
        assert "corporate_email" in indicators.asset_indicators

    def test_analyze_email_domain(self, luxury_scoring_engine):
        """Test email domain analysis for business indicators"""
        # Corporate email
        corporate_indicators = luxury_scoring_engine._analyze_email_domain("ceo@techcorp.com")
        assert "corporate_email" in corporate_indicators

        # Executive email
        executive_indicators = luxury_scoring_engine._analyze_email_domain("founder@startup.com")
        assert "corporate_email" in executive_indicators

        # Consumer email
        consumer_indicators = luxury_scoring_engine._analyze_email_domain("user@gmail.com")
        assert len(consumer_indicators) == 0

    def test_analyze_address_luxury_indicators(self, luxury_scoring_engine):
        """Test address analysis for luxury indicators"""
        # Luxury neighborhood
        luxury_score = luxury_scoring_engine._analyze_address_luxury_indicators(
            "123 West Lake Hills Dr, Austin, TX 78746"
        )
        assert luxury_score >= 7.0

        # Non-luxury area
        standard_score = luxury_scoring_engine._analyze_address_luxury_indicators("456 Regular St, Austin, TX 78702")
        assert standard_score < 5.0

    @pytest.mark.asyncio
    async def test_analyze_professional_indicators(self, luxury_scoring_engine):
        """Test professional indicator analysis"""
        # Executive profession
        exec_analysis = await luxury_scoring_engine._analyze_professional_indicators("CEO", "Tech Corporation")
        assert exec_analysis["net_worth_contribution"] > 1_000_000
        assert exec_analysis["investment_sophistication"] >= 80

        # Professional
        prof_analysis = await luxury_scoring_engine._analyze_professional_indicators("Doctor", "Medical Practice")
        assert exec_analysis["net_worth_contribution"] > 500_000

    def test_wealth_tier_determination(self, luxury_scoring_engine):
        """Test wealth tier classification"""
        # Test different net worth levels
        indicators_affluent = NetWorthIndicators(estimated_net_worth=3_000_000)
        tier_affluent = luxury_scoring_engine._determine_wealth_tier(indicators_affluent)
        assert tier_affluent == WealthTier.AFFLUENT

        indicators_uhnw = NetWorthIndicators(estimated_net_worth=15_000_000)
        tier_uhnw = luxury_scoring_engine._determine_wealth_tier(indicators_uhnw)
        assert tier_uhnw == WealthTier.UHNW

        indicators_ultra = NetWorthIndicators(estimated_net_worth=50_000_000)
        tier_ultra = luxury_scoring_engine._determine_wealth_tier(indicators_ultra)
        assert tier_ultra == WealthTier.ULTRA_UHNW


class TestLuxuryLifestyleAnalysis:
    """Test luxury lifestyle profiling and preferences"""

    @pytest.mark.asyncio
    async def test_analyze_luxury_lifestyle(self, luxury_scoring_engine, sample_lead_data):
        """Test luxury lifestyle analysis"""
        profile = await luxury_scoring_engine._analyze_luxury_lifestyle(sample_lead_data)

        assert isinstance(profile, LuxuryLifestyleProfile)
        assert profile.lifestyle_score >= 0
        assert isinstance(profile.preferred_neighborhoods, list)
        assert isinstance(profile.amenity_preferences, list)

    def test_extract_neighborhood_preferences(self, luxury_scoring_engine):
        """Test neighborhood preference extraction"""
        search_history = [
            {"location": "West Lake Hills"},
            {"location": "Tarrytown"},
            {"location": "West Lake Hills"},
            {"location": "Zilker"},
        ]

        neighborhoods = luxury_scoring_engine._extract_neighborhood_preferences(search_history)
        assert "West Lake Hills" in neighborhoods
        assert len(neighborhoods) <= 5

    def test_extract_amenity_preferences(self, luxury_scoring_engine):
        """Test amenity preference extraction"""
        search_history = [
            {"amenities": ["pool", "wine_cellar", "home_theater"]},
            {"amenities": ["pool", "spa", "guest_house"]},
            {"amenities": ["tennis_court", "pool"]},
        ]

        amenities = luxury_scoring_engine._extract_amenity_preferences(search_history)
        assert "pool" in amenities  # Should be most common
        assert len(amenities) <= 10


class TestInvestmentCapacityAnalysis:
    """Test investment capacity and sophistication assessment"""

    @pytest.mark.asyncio
    async def test_analyze_investment_capacity(self, luxury_scoring_engine, sample_lead_data):
        """Test investment capacity analysis"""
        capacity = await luxury_scoring_engine._analyze_investment_capacity(sample_lead_data)

        assert isinstance(capacity, InvestmentCapacityAnalysis)
        assert capacity.investment_capacity_score >= 0
        assert capacity.estimated_buying_budget >= 0

    @pytest.mark.asyncio
    async def test_investment_capacity_high_value(self, luxury_scoring_engine, uhnw_lead_data):
        """Test investment capacity for high-value client"""
        capacity = await luxury_scoring_engine._analyze_investment_capacity(uhnw_lead_data)

        # High-value client should show strong investment capacity
        assert capacity.estimated_buying_budget >= 5_000_000
        assert capacity.investment_capacity_score >= 70


class TestBuyingSignalDetection:
    """Test luxury buying signal detection"""

    @pytest.mark.asyncio
    async def test_detect_immediate_buying_signals(self, luxury_scoring_engine):
        """Test detection of immediate buying signals"""
        immediate_lead_data = {
            "communication_history": [
                {
                    "date": datetime.now().isoformat(),
                    "content": "Ready to buy immediately. Cash buyer. Need to close within 30 days.",
                    "type": "email",
                }
            ],
            "property_search_history": [],
        }

        signal = await luxury_scoring_engine._detect_luxury_buying_signals(immediate_lead_data)
        assert signal == LuxuryBuyingSignal.IMMEDIATE

    @pytest.mark.asyncio
    async def test_detect_investment_buying_signals(self, luxury_scoring_engine):
        """Test detection of investment-focused buying signals"""
        investment_lead_data = {
            "communication_history": [
                {
                    "date": datetime.now().isoformat(),
                    "content": "Looking for investment properties with strong cash flow and appreciation potential.",
                    "type": "email",
                }
            ],
            "property_search_history": [],
        }

        signal = await luxury_scoring_engine._detect_luxury_buying_signals(investment_lead_data)
        assert signal == LuxuryBuyingSignal.INVESTOR

    @pytest.mark.asyncio
    async def test_detect_active_buying_signals(self, luxury_scoring_engine, sample_lead_data):
        """Test detection of active buying signals"""
        signal = await luxury_scoring_engine._detect_luxury_buying_signals(sample_lead_data)

        # Sample lead data should show active signals
        assert signal in [LuxuryBuyingSignal.ACTIVE, LuxuryBuyingSignal.CONSIDERING]


class TestCompetitiveIntelligence:
    """Test competitive intelligence gathering"""

    @pytest.mark.asyncio
    async def test_gather_competitive_intelligence(self, luxury_scoring_engine, sample_lead_data):
        """Test competitive intelligence analysis"""
        intel = await luxury_scoring_engine._gather_competitive_intelligence(sample_lead_data)

        assert isinstance(intel, CompetitiveIntelligence)
        assert 0 <= intel.price_sensitivity <= 100
        assert 0 <= intel.referral_source_quality <= 100

    def test_score_referral_source_quality(self, luxury_scoring_engine):
        """Test referral source quality scoring"""
        # High-quality referral
        high_quality_score = luxury_scoring_engine._score_referral_source("past client")
        assert high_quality_score >= 85

        # Medium-quality referral
        medium_quality_score = luxury_scoring_engine._score_referral_source("friend")
        assert 60 <= medium_quality_score <= 80

        # Unknown referral
        unknown_score = luxury_scoring_engine._score_referral_source("unknown")
        assert unknown_score <= 60


class TestMasterScoringAlgorithm:
    """Test master luxury scoring algorithm"""

    def test_calculate_master_luxury_score(self, luxury_scoring_engine):
        """Test master luxury score calculation"""
        # Create sample luxury lead with known values
        luxury_lead = LuxuryLead(
            lead_id="TEST-001",
            contact_info={},
            source="test",
            created_date=datetime.now(),
            wealth_tier=WealthTier.UHNW,
            buying_signal=LuxuryBuyingSignal.IMMEDIATE,
        )

        # Set component scores
        luxury_lead.net_worth_indicators.net_worth_confidence = 90.0
        luxury_lead.lifestyle_profile.lifestyle_score = 85.0
        luxury_lead.investment_capacity.investment_capacity_score = 88.0
        luxury_lead.competitive_intel.referral_source_quality = 95.0
        luxury_lead.competitive_intel.price_sensitivity = 20.0  # Low sensitivity = good

        score = luxury_scoring_engine._calculate_master_luxury_score(luxury_lead)

        assert 0 <= score <= 100
        assert score >= 80  # High-quality lead should score well

    def test_determine_qualification_status(self, luxury_scoring_engine):
        """Test qualification status determination"""
        # Ultra-premium qualification
        ultra_lead = LuxuryLead(
            lead_id="ULTRA-001",
            contact_info={},
            source="test",
            created_date=datetime.now(),
            wealth_tier=WealthTier.ULTRA_UHNW,
            overall_luxury_score=90.0,
        )

        ultra_status = luxury_scoring_engine._determine_qualification_status(ultra_lead)
        assert ultra_status == "ultra_premium"

        # Premium qualification
        premium_lead = LuxuryLead(
            lead_id="PREMIUM-001",
            contact_info={},
            source="test",
            created_date=datetime.now(),
            wealth_tier=WealthTier.UHNW,
            overall_luxury_score=80.0,
        )

        premium_status = luxury_scoring_engine._determine_qualification_status(premium_lead)
        assert premium_status == "premium"

    def test_estimate_commission_potential(self, luxury_scoring_engine):
        """Test commission potential estimation"""
        # High-value lead
        high_value_lead = LuxuryLead(
            lead_id="HIGH-001",
            contact_info={},
            source="test",
            created_date=datetime.now(),
            qualification_status="ultra_premium",
            buying_signal=LuxuryBuyingSignal.IMMEDIATE,
        )

        high_value_lead.investment_capacity.estimated_buying_budget = 5_000_000

        commission = luxury_scoring_engine._estimate_commission_potential(high_value_lead)
        assert commission >= 100_000  # Should be significant for high-value properties

    def test_recommend_service_level(self, luxury_scoring_engine):
        """Test service level recommendation"""
        # White-glove candidate
        white_glove_lead = LuxuryLead(
            lead_id="WG-001",
            contact_info={},
            source="test",
            created_date=datetime.now(),
            wealth_tier=WealthTier.ULTRA_UHNW,
            overall_luxury_score=85.0,
        )

        service_level = luxury_scoring_engine._recommend_service_level(white_glove_lead)
        assert service_level in ["white_glove", "premium"]


class TestEndToEndScoring:
    """Test complete end-to-end scoring process"""

    @pytest.mark.asyncio
    async def test_score_luxury_lead_complete(self, luxury_scoring_engine, sample_lead_data):
        """Test complete luxury lead scoring process"""
        luxury_lead = await luxury_scoring_engine.score_luxury_lead(sample_lead_data)

        # Verify all components are populated
        assert isinstance(luxury_lead, LuxuryLead)
        assert luxury_lead.lead_id is not None
        assert luxury_lead.wealth_tier is not None
        assert luxury_lead.overall_luxury_score >= 0
        assert luxury_lead.qualification_status is not None
        assert luxury_lead.commission_potential >= 0
        assert luxury_lead.recommended_service_level is not None

    @pytest.mark.asyncio
    async def test_score_uhnw_lead_complete(self, luxury_scoring_engine, uhnw_lead_data):
        """Test complete UHNW lead scoring"""
        luxury_lead = await luxury_scoring_engine.score_luxury_lead(uhnw_lead_data)

        # UHNW lead should score highly
        assert luxury_lead.wealth_tier in [WealthTier.UHNW, WealthTier.ULTRA_UHNW, WealthTier.BILLIONAIRE]
        assert luxury_lead.overall_luxury_score >= 70
        assert luxury_lead.qualification_status in ["qualified", "premium", "ultra_premium"]
        assert luxury_lead.recommended_service_level in ["premium", "white_glove"]

    @pytest.mark.asyncio
    async def test_score_lead_batch(self, luxury_scoring_engine, sample_lead_data, uhnw_lead_data):
        """Test batch lead scoring"""
        lead_batch = [sample_lead_data, uhnw_lead_data]

        scored_leads = await luxury_scoring_engine.score_lead_batch(lead_batch)

        assert len(scored_leads) == 2
        assert all(isinstance(lead, LuxuryLead) for lead in scored_leads)
        assert all(lead.overall_luxury_score >= 0 for lead in scored_leads)

    def test_generate_lead_insights_summary(self, luxury_scoring_engine):
        """Test lead insights summary generation"""
        # Create sample scored leads
        sample_leads = [
            LuxuryLead(
                lead_id="LEAD-001",
                contact_info={},
                source="test",
                created_date=datetime.now(),
                wealth_tier=WealthTier.UHNW,
                overall_luxury_score=85.0,
                qualification_status="premium",
                commission_potential=150_000,
            ),
            LuxuryLead(
                lead_id="LEAD-002",
                contact_info={},
                source="test",
                created_date=datetime.now(),
                wealth_tier=WealthTier.ULTRA_UHNW,
                overall_luxury_score=92.0,
                qualification_status="ultra_premium",
                commission_potential=250_000,
            ),
        ]

        insights = luxury_scoring_engine.generate_lead_insights_summary(sample_leads)

        assert insights["total_leads_analyzed"] == 2
        assert "qualification_distribution" in insights
        assert "wealth_tier_distribution" in insights
        assert insights["total_commission_potential"] == 400_000
        assert len(insights["top_leads"]) <= 5


class TestDataValidation:
    """Test data validation and edge cases"""

    @pytest.mark.asyncio
    async def test_empty_lead_data(self, luxury_scoring_engine):
        """Test scoring with minimal lead data"""
        minimal_data = {"lead_id": "MINIMAL-001", "contact_info": {}, "source": "unknown"}

        luxury_lead = await luxury_scoring_engine.score_luxury_lead(minimal_data)

        # Should handle gracefully
        assert luxury_lead.lead_id == "MINIMAL-001"
        assert luxury_lead.overall_luxury_score >= 0
        assert luxury_lead.qualification_status is not None

    @pytest.mark.asyncio
    async def test_invalid_communication_data(self, luxury_scoring_engine):
        """Test handling of invalid communication data"""
        invalid_data = {
            "lead_id": "INVALID-001",
            "contact_info": {},
            "source": "test",
            "communication_history": [{"content": "", "date": "invalid-date"}, {"content": None}],
        }

        luxury_lead = await luxury_scoring_engine.score_luxury_lead(invalid_data)

        # Should handle gracefully without errors
        assert luxury_lead.lead_id == "INVALID-001"
        assert luxury_lead.overall_luxury_score >= 0

    def test_scoring_weights_validation(self, luxury_scoring_engine):
        """Test that scoring weights sum to 1.0"""
        weights = luxury_scoring_engine.scoring_weights
        total_weight = sum(weights.values())

        assert abs(total_weight - 1.0) < 0.001  # Allow for floating point precision


class TestIntegrationWithExistingSystems:
    """Integration tests with existing codebase systems"""

    @pytest.mark.asyncio
    async def test_integration_with_cache_service(self, luxury_scoring_engine):
        """Test integration with cache service"""
        # Mock cache hit
        with patch.object(luxury_scoring_engine.cache, "get", return_value=None):
            with patch.object(luxury_scoring_engine.cache, "set", return_value=True):
                lead_data = create_sample_luxury_lead_data()
                result = await luxury_scoring_engine.score_luxury_lead(lead_data)
                assert result is not None

    @pytest.mark.asyncio
    async def test_integration_with_claude_assistant(self, luxury_scoring_engine):
        """Test integration with Claude assistant"""
        # Verify Claude is called for AI-powered analysis
        lead_data = create_sample_luxury_lead_data()

        await luxury_scoring_engine.score_luxury_lead(lead_data)

        # Verify Claude was called (mocked)
        assert luxury_scoring_engine.claude.generate_claude_response.called


class TestPerformance:
    """Performance tests for luxury lead scoring"""

    @pytest.mark.asyncio
    async def test_scoring_performance(self, luxury_scoring_engine):
        """Test scoring performance with timer"""
        import time

        lead_data = create_sample_luxury_lead_data()

        start_time = time.time()
        await luxury_scoring_engine.score_luxury_lead(lead_data)
        end_time = time.time()

        # Should complete within reasonable time
        processing_time = end_time - start_time
        assert processing_time < 5.0  # Should be under 5 seconds

    @pytest.mark.asyncio
    async def test_batch_scoring_performance(self, luxury_scoring_engine):
        """Test batch scoring performance"""
        import time

        # Create batch of leads
        lead_batch = [create_sample_luxury_lead_data() for _ in range(10)]

        start_time = time.time()
        await luxury_scoring_engine.score_lead_batch(lead_batch)
        end_time = time.time()

        # Batch processing should be efficient
        processing_time = end_time - start_time
        assert processing_time < 30.0  # Should complete batch in under 30 seconds


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
