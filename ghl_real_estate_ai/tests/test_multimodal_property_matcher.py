"""
Tests for Multimodal Property Matcher Service

Comprehensive test suite validating:
- Backwards compatibility with traditional matching
- Vision intelligence integration
- Neighborhood intelligence integration
- Combined multimodal scoring algorithm
- A/B testing framework
- Performance requirements (<1.5s total, <35ms ML inference)
- Satisfaction improvement prediction (88% → 93%+)
"""

import asyncio
import pytest
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.services.multimodal_property_matcher import (
    MultimodalPropertyMatcher,
    MatchingVersion,
    ABTestConfig,
    get_multimodal_property_matcher
)
from ghl_real_estate_ai.models.matching_models import (
    MultimodalPropertyMatch,
    VisionIntelligenceScore,
    NeighborhoodIntelligenceScore,
    MultimodalScoreBreakdown,
    BehavioralProfile,
    LeadSegment
)
from ghl_real_estate_ai.services.claude_vision_analyzer import (
    PropertyAnalysis,
    LuxuryFeatures,
    ConditionScore,
    StyleClassification,
    FeatureExtraction,
    LuxuryLevel,
    PropertyCondition,
    PropertyStyle
)
from ghl_real_estate_ai.services.neighborhood_intelligence_api import (
    NeighborhoodIntelligence,
    LocationData,
    WalkabilityData,
    SchoolRatings,
    CommuteScores
)


class TestMultimodalPropertyMatcher:
    """Test suite for Multimodal Property Matcher"""

    @pytest.fixture
    async def multimodal_matcher(self):
        """Create multimodal matcher instance for testing"""
        matcher = MultimodalPropertyMatcher(
            enable_multimodal=True,
            ab_test_config=ABTestConfig(enabled=False)  # Disable A/B testing for deterministic tests
        )

        # Mock the multimodal services to avoid real API calls
        matcher.vision_analyzer = AsyncMock()
        matcher.neighborhood_api = AsyncMock()

        return matcher

    @pytest.fixture
    def sample_preferences(self):
        """Sample lead preferences"""
        return {
            "lead_id": "test_lead_001",
            "budget": 600000,
            "location": "Austin",
            "bedrooms": 3,
            "bathrooms": 2,
            "property_type": "Single Family",
            "min_sqft": 1500,
            "max_hoa": 200,
            "architectural_style": "modern"
        }

    @pytest.fixture
    def sample_property(self):
        """Sample property data"""
        return {
            "id": "prop_001",
            "price": 580000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 1800,
            "property_type": "Single Family",
            "year_built": 2018,
            "address": {
                "street": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip": "78701",
                "lat": 30.2672,
                "lng": -97.7431
            },
            "images": [
                "https://example.com/img1.jpg",
                "https://example.com/img2.jpg"
            ],
            "features": ["Modern kitchen", "Pool", "Garage"],
            "days_on_market": 15
        }

    @pytest.fixture
    def mock_vision_analysis(self):
        """Mock Claude Vision analysis"""
        return PropertyAnalysis(
            property_id="prop_001",
            luxury_features=LuxuryFeatures(
                luxury_level=LuxuryLevel.HIGH_END_LUXURY,
                luxury_score=8.5,
                high_end_finishes=["Quartz countertops", "Custom cabinetry"],
                premium_materials=["Hardwood flooring", "Marble"],
                architectural_details=["Crown molding", "High ceilings"],
                designer_elements=["Modern lighting", "Designer fixtures"],
                outdoor_luxury=["Pool", "Outdoor kitchen"],
                confidence=0.92
            ),
            condition_score=ConditionScore(
                condition=PropertyCondition.EXCELLENT,
                condition_score=9.0,
                maintenance_level="excellent",
                visible_issues=[],
                positive_indicators=["Recent renovation", "Well maintained"],
                renovation_indicators=["Updated kitchen", "New appliances"],
                age_indicators="Recently built (2018)",
                confidence=0.88
            ),
            style_classification=StyleClassification(
                primary_style=PropertyStyle.MODERN,
                secondary_styles=[],
                style_confidence=0.95,
                architectural_features=["Clean lines", "Large windows"],
                period_indicators="Contemporary design",
                design_coherence=9.2
            ),
            feature_extraction=FeatureExtraction(
                has_pool=True,
                pool_type="in-ground",
                has_outdoor_kitchen=True,
                has_fireplace=True,
                fireplace_count=1,
                has_high_ceilings=True,
                has_hardwood_floors=True,
                has_modern_kitchen=True,
                kitchen_features=["Quartz countertops", "Stainless appliances"],
                has_garage=True,
                garage_spaces=2,
                outdoor_features=["Pool", "Patio", "Landscaping"],
                view_type="city",
                landscaping_quality="excellent"
            ),
            overall_appeal_score=8.8,
            target_market_segment="luxury_buyers",
            estimated_value_tier="high",
            marketing_highlights=[
                "Luxury modern estate",
                "In-ground pool",
                "Outdoor kitchen for entertaining"
            ],
            processing_time_ms=1190.0,
            images_analyzed=2,
            confidence=0.90
        )

    @pytest.fixture
    def mock_neighborhood_analysis(self):
        """Mock Neighborhood Intelligence analysis"""
        return NeighborhoodIntelligence(
            property_address="123 Main St, Austin, TX 78701",
            location=LocationData(
                address="123 Main St, Austin, TX 78701",
                lat=30.2672,
                lng=-97.7431,
                city="Austin",
                state="TX",
                zipcode="78701",
                crime_index=25  # Lower is safer
            ),
            walkability=WalkabilityData(
                address="123 Main St, Austin, TX 78701",
                lat=30.2672,
                lng=-97.7431,
                walk_score=85,
                walk_description="Very Walkable",
                transit_score=70,
                transit_description="Excellent Transit",
                bike_score=75,
                bike_description="Very Bikeable"
            ),
            schools=SchoolRatings(
                address="123 Main St, Austin, TX 78701",
                average_rating=8.5
            ),
            commute=CommuteScores(
                from_address="123 Main St, Austin, TX 78701",
                overall_commute_score=80,
                average_commute_time=20,
                employment_centers_within_30min=5,
                public_transit_accessible=True
            ),
            overall_score=82
        )

    # ========================================================================
    # Backwards Compatibility Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_traditional_matching_still_works(
        self,
        multimodal_matcher,
        sample_preferences
    ):
        """Test that traditional matching works without multimodal enhancements"""
        # Disable multimodal
        multimodal_matcher.enable_multimodal = False

        # Mock traditional matching
        with patch.object(multimodal_matcher, 'find_enhanced_matches') as mock_enhanced:
            mock_enhanced.return_value = []

            matches = await multimodal_matcher.find_multimodal_matches(
                preferences=sample_preferences,
                limit=5
            )

            # Should call traditional matching
            assert mock_enhanced.called
            assert isinstance(matches, list)

    @pytest.mark.asyncio
    async def test_multimodal_match_extends_property_match(
        self,
        multimodal_matcher,
        sample_preferences,
        sample_property
    ):
        """Test that MultimodalPropertyMatch extends PropertyMatch"""
        # Mock services
        multimodal_matcher.vision_analyzer.analyze_property_images = AsyncMock(return_value=None)
        multimodal_matcher.neighborhood_api.analyze_neighborhood = AsyncMock(return_value=None)

        # Mock base matching
        with patch.object(multimodal_matcher, 'find_enhanced_matches') as mock_enhanced:
            from ghl_real_estate_ai.models.matching_models import (
                PropertyMatch,
                MatchScoreBreakdown,
                MatchReasoning,
                TraditionalScores,
                LifestyleScores,
                ContextualScores,
                MarketTimingScore,
                AdaptiveWeights
            )

            # Create minimal traditional match
            mock_enhanced.return_value = [
                PropertyMatch(
                    property=sample_property,
                    overall_score=0.75,
                    score_breakdown=MagicMock(),
                    reasoning=MagicMock(),
                    match_rank=1,
                    generated_at=datetime.now(),
                    lead_id="test_lead_001",
                    preferences_used=sample_preferences,
                    predicted_engagement=0.60,
                    predicted_showing_request=0.25,
                    confidence_interval=(0.70, 0.80)
                )
            ]

            matches = await multimodal_matcher.find_multimodal_matches(
                preferences=sample_preferences,
                limit=5
            )

            assert len(matches) > 0
            assert isinstance(matches[0], MultimodalPropertyMatch)
            # Should have all traditional PropertyMatch fields
            assert matches[0].overall_score == 0.75
            assert matches[0].property == sample_property
            assert matches[0].lead_id == "test_lead_001"

    # ========================================================================
    # Vision Intelligence Integration Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_vision_intelligence_integration(
        self,
        multimodal_matcher,
        sample_property,
        mock_vision_analysis
    ):
        """Test Claude Vision integration"""
        # Mock vision analyzer
        multimodal_matcher.vision_analyzer.analyze_property_images = AsyncMock(
            return_value=mock_vision_analysis
        )

        # Get vision intelligence
        vision_intel = await multimodal_matcher._get_vision_intelligence(
            property_id="prop_001",
            image_urls=sample_property["images"]
        )

        assert vision_intel is not None
        assert isinstance(vision_intel, PropertyAnalysis)
        assert vision_intel.luxury_features.luxury_score == 8.5
        assert vision_intel.condition_score.condition_score == 9.0
        assert vision_intel.processing_time_ms <= 1500  # Performance target

    @pytest.mark.asyncio
    async def test_vision_score_extraction(
        self,
        multimodal_matcher,
        sample_preferences,
        mock_vision_analysis
    ):
        """Test vision score extraction and normalization"""
        vision_score = multimodal_matcher._extract_vision_score(
            mock_vision_analysis,
            sample_preferences
        )

        assert isinstance(vision_score, VisionIntelligenceScore)
        assert vision_score.luxury_score == 8.5
        assert vision_score.condition_score == 9.0
        assert 0 <= vision_score.style_match_score <= 1.0
        assert vision_score.architectural_style == "modern"
        assert vision_score.confidence > 0.8

    @pytest.mark.asyncio
    async def test_vision_contribution_calculation(
        self,
        multimodal_matcher
    ):
        """Test vision contribution to overall score"""
        vision_score = VisionIntelligenceScore(
            luxury_score=8.0,
            condition_score=9.0,
            style_match_score=0.9,
            luxury_level="high_end_luxury",
            property_condition="excellent",
            architectural_style="modern",
            premium_features=["Hardwood", "Marble"],
            visual_appeal_score=8.5,
            confidence=0.90,
            images_analyzed=3,
            processing_time_ms=1100.0
        )

        contribution = multimodal_matcher._calculate_vision_contribution(vision_score)

        # Vision should contribute 0-0.15 (15% max weight)
        assert 0 <= contribution <= 0.15
        assert contribution > 0  # Should have positive contribution

    # ========================================================================
    # Neighborhood Intelligence Integration Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_neighborhood_intelligence_integration(
        self,
        multimodal_matcher,
        sample_property,
        sample_preferences,
        mock_neighborhood_analysis
    ):
        """Test Neighborhood Intelligence integration"""
        # Mock neighborhood API
        multimodal_matcher.neighborhood_api.analyze_neighborhood = AsyncMock(
            return_value=mock_neighborhood_analysis
        )

        address_data = sample_property["address"]

        neighborhood_intel = await multimodal_matcher._get_neighborhood_intelligence(
            property_address=f"{address_data['street']}, {address_data['city']}, {address_data['state']} {address_data['zip']}",
            lat=address_data["lat"],
            lng=address_data["lng"],
            city=address_data["city"],
            state=address_data["state"],
            zipcode=address_data["zip"],
            preferences=sample_preferences
        )

        assert neighborhood_intel is not None
        assert isinstance(neighborhood_intel, NeighborhoodIntelligence)
        assert neighborhood_intel.overall_score == 82
        assert neighborhood_intel.walkability.walk_score == 85

    @pytest.mark.asyncio
    async def test_neighborhood_score_extraction(
        self,
        multimodal_matcher,
        mock_neighborhood_analysis
    ):
        """Test neighborhood score extraction and normalization"""
        neighborhood_score = multimodal_matcher._extract_neighborhood_score(
            mock_neighborhood_analysis
        )

        assert isinstance(neighborhood_score, NeighborhoodIntelligenceScore)
        assert neighborhood_score.walkability_score == 85
        assert neighborhood_score.school_average_rating == 8.5
        assert neighborhood_score.commute_score == 80
        assert neighborhood_score.overall_neighborhood_score == 82
        assert 0 <= neighborhood_score.data_completeness <= 1.0

    @pytest.mark.asyncio
    async def test_neighborhood_contribution_calculation(
        self,
        multimodal_matcher
    ):
        """Test neighborhood contribution to overall score"""
        neighborhood_score = NeighborhoodIntelligenceScore(
            walkability_score=85,
            transit_score=70,
            bike_score=75,
            school_average_rating=8.5,
            elementary_rating=None,
            middle_rating=None,
            high_rating=None,
            commute_score=80,
            average_commute_minutes=20,
            employment_centers_nearby=5,
            public_transit_accessible=True,
            overall_neighborhood_score=82,
            data_completeness=1.0,
            processing_time_ms=150.0,
            cache_hit=True
        )

        contribution = multimodal_matcher._calculate_neighborhood_contribution(neighborhood_score)

        # Neighborhood should contribute 0-0.15 (15% max weight)
        assert 0 <= contribution <= 0.15
        assert contribution > 0  # Should have positive contribution

    # ========================================================================
    # Multimodal Scoring Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multimodal_score_calculation(
        self,
        multimodal_matcher,
        sample_preferences,
        sample_property,
        mock_vision_analysis,
        mock_neighborhood_analysis
    ):
        """Test combined multimodal scoring"""
        # Create mock traditional match
        from unittest.mock import MagicMock
        traditional_match = MagicMock()
        traditional_match.overall_score = 0.75
        traditional_match.score_breakdown.lifestyle_scores.overall_score = 0.08
        traditional_match.score_breakdown.contextual_scores.overall_score = 0.10
        traditional_match.score_breakdown.market_timing_score.optimal_timing_score = 0.6
        traditional_match.score_breakdown.confidence_level = 0.85

        multimodal_breakdown = multimodal_matcher._calculate_multimodal_score(
            traditional_match=traditional_match,
            vision_intel=mock_vision_analysis,
            neighborhood_intel=mock_neighborhood_analysis,
            preferences=sample_preferences
        )

        assert isinstance(multimodal_breakdown, MultimodalScoreBreakdown)

        # Validate score components
        assert 0 <= multimodal_breakdown.traditional_score <= 1.0
        assert 0 <= multimodal_breakdown.vision_score <= 1.0
        assert 0 <= multimodal_breakdown.neighborhood_score <= 1.0
        assert 0 <= multimodal_breakdown.multimodal_overall_score <= 1.0

        # Validate weights sum to reasonable total
        total_weight = (
            multimodal_breakdown.traditional_weight +
            multimodal_breakdown.vision_weight +
            multimodal_breakdown.neighborhood_weight +
            multimodal_breakdown.lifestyle_contextual_weight +
            multimodal_breakdown.market_timing_weight
        )
        assert 0.95 <= total_weight <= 1.05  # Should be close to 1.0

        # Validate confidence
        assert 0 <= multimodal_breakdown.multimodal_confidence <= 1.0
        assert multimodal_breakdown.multimodal_confidence > 0.7  # Should be reasonably confident

    @pytest.mark.asyncio
    async def test_multimodal_score_higher_than_traditional(
        self,
        multimodal_matcher,
        sample_preferences,
        mock_vision_analysis,
        mock_neighborhood_analysis
    ):
        """Test that multimodal score is typically higher with good intelligence"""
        traditional_match = MagicMock()
        traditional_match.overall_score = 0.70
        traditional_match.score_breakdown.lifestyle_scores.overall_score = 0.08
        traditional_match.score_breakdown.contextual_scores.overall_score = 0.10
        traditional_match.score_breakdown.market_timing_score.optimal_timing_score = 0.6
        traditional_match.score_breakdown.confidence_level = 0.85

        multimodal_breakdown = multimodal_matcher._calculate_multimodal_score(
            traditional_match=traditional_match,
            vision_intel=mock_vision_analysis,
            neighborhood_intel=mock_neighborhood_analysis,
            preferences=sample_preferences
        )

        # With high-quality vision and neighborhood data, multimodal should improve score
        assert multimodal_breakdown.multimodal_overall_score >= traditional_match.overall_score

    # ========================================================================
    # A/B Testing Framework Tests
    # ========================================================================

    def test_ab_test_version_determination_consistent_bucketing(
        self,
        multimodal_matcher
    ):
        """Test A/B test version assignment is consistent for same lead"""
        multimodal_matcher.ab_test_config = ABTestConfig(
            enabled=True,
            multimodal_percentage=0.50
        )

        lead_id = "test_lead_123"

        # Same lead should always get same version
        version1 = multimodal_matcher._determine_matching_version(lead_id, False)
        version2 = multimodal_matcher._determine_matching_version(lead_id, False)

        assert version1 == version2

    def test_ab_test_version_distribution(
        self,
        multimodal_matcher
    ):
        """Test A/B test versions are distributed according to percentage"""
        multimodal_matcher.ab_test_config = ABTestConfig(
            enabled=True,
            multimodal_percentage=0.50
        )

        # Test 100 different leads
        multimodal_count = 0
        traditional_count = 0

        for i in range(100):
            lead_id = f"lead_{i}"
            version = multimodal_matcher._determine_matching_version(lead_id, False)

            if version == MatchingVersion.MULTIMODAL:
                multimodal_count += 1
            else:
                traditional_count += 1

        # Should be roughly 50/50 split (allow 20% variance)
        assert 40 <= multimodal_count <= 60
        assert 40 <= traditional_count <= 60

    def test_force_multimodal_bypasses_ab_testing(
        self,
        multimodal_matcher
    ):
        """Test force_multimodal flag bypasses A/B testing"""
        multimodal_matcher.ab_test_config = ABTestConfig(
            enabled=True,
            multimodal_percentage=0.0  # 0% multimodal
        )

        version = multimodal_matcher._determine_matching_version(
            "any_lead",
            force_multimodal=True
        )

        assert version == MatchingVersion.MULTIMODAL

    # ========================================================================
    # Satisfaction Prediction Tests
    # ========================================================================

    def test_satisfaction_prediction_baseline(
        self,
        multimodal_matcher
    ):
        """Test satisfaction prediction starts at 88% baseline"""
        # Low quality multimodal breakdown
        multimodal_breakdown = MultimodalScoreBreakdown(
            traditional_score=0.70,
            traditional_weight=0.45,
            vision_score=0.0,
            vision_weight=0.0,
            neighborhood_score=0.0,
            neighborhood_weight=0.0,
            lifestyle_contextual_score=0.15,
            lifestyle_contextual_weight=0.15,
            market_timing_score=0.60,
            market_timing_weight=0.10,
            multimodal_overall_score=0.70,
            multimodal_confidence=0.70,
            total_processing_time_ms=100.0,
            vision_processing_time_ms=0.0,
            neighborhood_processing_time_ms=0.0,
            cache_hit_rate=0.0
        )

        satisfaction = multimodal_matcher._predict_satisfaction(multimodal_breakdown)

        # Should be at or near baseline
        assert satisfaction >= 0.88

    def test_satisfaction_prediction_with_multimodal_boost(
        self,
        multimodal_matcher
    ):
        """Test satisfaction prediction improves with multimodal intelligence"""
        # High quality multimodal breakdown
        multimodal_breakdown = MultimodalScoreBreakdown(
            traditional_score=0.80,
            traditional_weight=0.45,
            vision_score=0.12,
            vision_weight=0.15,
            vision_intelligence=MagicMock(),
            neighborhood_score=0.13,
            neighborhood_weight=0.15,
            neighborhood_intelligence=MagicMock(),
            lifestyle_contextual_score=0.15,
            lifestyle_contextual_weight=0.15,
            market_timing_score=0.80,
            market_timing_weight=0.10,
            multimodal_overall_score=0.85,
            multimodal_confidence=0.90,
            total_processing_time_ms=1400.0,
            vision_processing_time_ms=1200.0,
            neighborhood_processing_time_ms=200.0,
            cache_hit_rate=0.85
        )

        satisfaction = multimodal_matcher._predict_satisfaction(multimodal_breakdown)

        # Should exceed baseline and approach 93%+ target
        assert satisfaction > 0.88
        assert satisfaction >= 0.91  # Should be close to or exceed target

    # ========================================================================
    # Performance Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_multimodal_matching_performance_target(
        self,
        multimodal_matcher,
        sample_preferences,
        sample_property,
        mock_vision_analysis,
        mock_neighborhood_analysis
    ):
        """Test multimodal matching meets <1.5s performance target"""
        # Mock services with realistic delays
        async def mock_vision_delay(*args, **kwargs):
            await asyncio.sleep(1.2)  # 1.2s vision analysis
            return mock_vision_analysis

        async def mock_neighborhood_delay(*args, **kwargs):
            await asyncio.sleep(0.15)  # 150ms neighborhood analysis
            return mock_neighborhood_analysis

        multimodal_matcher.vision_analyzer.analyze_property_images = mock_vision_delay
        multimodal_matcher.neighborhood_api.analyze_neighborhood = mock_neighborhood_delay

        # Mock traditional matching
        with patch.object(multimodal_matcher, 'find_enhanced_matches') as mock_enhanced:
            from ghl_real_estate_ai.models.matching_models import PropertyMatch

            mock_enhanced.return_value = [
                PropertyMatch(
                    property=sample_property,
                    overall_score=0.75,
                    score_breakdown=MagicMock(),
                    reasoning=MagicMock(),
                    match_rank=1,
                    generated_at=datetime.now(),
                    lead_id="test_lead_001",
                    preferences_used=sample_preferences,
                    predicted_engagement=0.60,
                    predicted_showing_request=0.25,
                    confidence_interval=(0.70, 0.80)
                )
            ]

            start_time = asyncio.get_event_loop().time()

            matches = await multimodal_matcher.find_multimodal_matches(
                preferences=sample_preferences,
                limit=1,
                force_multimodal=True
            )

            end_time = asyncio.get_event_loop().time()
            total_time_ms = (end_time - start_time) * 1000

            # Should complete within 1.5s performance target
            assert total_time_ms < 1500, f"Multimodal matching took {total_time_ms:.0f}ms, exceeds 1500ms target"
            assert len(matches) > 0

    # ========================================================================
    # Integration Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_end_to_end_multimodal_matching(
        self,
        multimodal_matcher,
        sample_preferences,
        sample_property,
        mock_vision_analysis,
        mock_neighborhood_analysis
    ):
        """Test complete end-to-end multimodal matching flow"""
        # Mock all services
        multimodal_matcher.vision_analyzer.analyze_property_images = AsyncMock(
            return_value=mock_vision_analysis
        )
        multimodal_matcher.neighborhood_api.analyze_neighborhood = AsyncMock(
            return_value=mock_neighborhood_analysis
        )

        with patch.object(multimodal_matcher, 'find_enhanced_matches') as mock_enhanced:
            from ghl_real_estate_ai.models.matching_models import PropertyMatch

            mock_enhanced.return_value = [
                PropertyMatch(
                    property=sample_property,
                    overall_score=0.75,
                    score_breakdown=MagicMock(),
                    reasoning=MagicMock(),
                    match_rank=1,
                    generated_at=datetime.now(),
                    lead_id="test_lead_001",
                    preferences_used=sample_preferences,
                    predicted_engagement=0.60,
                    predicted_showing_request=0.25,
                    confidence_interval=(0.70, 0.80)
                )
            ]

            matches = await multimodal_matcher.find_multimodal_matches(
                preferences=sample_preferences,
                limit=5,
                force_multimodal=True
            )

            # Validate results
            assert len(matches) > 0
            match = matches[0]

            assert isinstance(match, MultimodalPropertyMatch)
            assert match.multimodal_enabled is True
            assert match.multimodal_overall_score is not None
            assert match.multimodal_score_breakdown is not None
            assert len(match.vision_highlights) > 0
            assert len(match.neighborhood_highlights) > 0
            assert match.satisfaction_predicted >= 0.88

            # Validate multimodal score is better than traditional
            assert match.multimodal_overall_score >= match.overall_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
