"""
Tests for Competitive Landscape Mapper

This module tests the LandscapeMapper including competitive positioning analysis,
strategic gap identification, and market dynamics assessment.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.analytics.landscape_mapper import (
    LandscapeMapper, CompetitorProfile, MarketSegment, CompetitivePosition,
    StrategicGap, LandscapeAnalysis, CompetitiveStrength, MarketPosition,
    StrategicGapType
)
from src.core.event_bus import EventType, EventPriority

@pytest.mark.unit


class TestLandscapeMapper:
    """Test suite for Competitive Landscape Mapper."""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus for testing."""
        mock_bus = MagicMock()
        mock_bus.publish = AsyncMock()
        return mock_bus
    
    @pytest.fixture
    def landscape_mapper(self, mock_event_bus):
        """Landscape mapper with mocked dependencies."""
        return LandscapeMapper(
            event_bus=mock_event_bus,
            analysis_cache_minutes=5,
            min_competitors_for_clustering=2,
            position_dimensions=2
        )
    
    @pytest.fixture
    def sample_competitors(self):
        """Sample competitor profiles for testing."""
        return [
            CompetitorProfile(
                competitor_id="comp_001",
                name="Tech Leader Corp",
                market_cap=50000000000.0,  # $50B
                revenue=5000000000.0,      # $5B
                customer_count=100000,
                product_features={"ai_platform": True, "automation": True, "analytics": True},
                pricing_tiers=[
                    {"name": "Enterprise", "price": 10000, "model": "subscription"},
                    {"name": "Pro", "price": 1000, "model": "subscription"}
                ],
                market_segments={"Enterprise", "Mid-Market"},
                geographic_presence={"North America", "Europe", "Asia"},
                technology_stack={"Python": "3.9", "React": "18", "AWS": "latest"},
                competitive_advantages=["First-mover advantage", "Strong AI capabilities", "Enterprise relationships"],
                weaknesses=["High pricing", "Complex onboarding"]
            ),
            CompetitorProfile(
                competitor_id="comp_002", 
                name="Fast Challenger Inc",
                market_cap=5000000000.0,   # $5B
                revenue=500000000.0,       # $500M
                customer_count=50000,
                product_features={"automation": True, "mobile_app": True},
                pricing_tiers=[
                    {"name": "Business", "price": 500, "model": "subscription"},
                    {"name": "Starter", "price": 100, "model": "subscription"}
                ],
                market_segments={"SMB", "Mid-Market"},
                geographic_presence={"North America", "Europe"},
                technology_stack={"Node.js": "18", "Vue": "3", "GCP": "latest"},
                competitive_advantages=["Competitive pricing", "Easy onboarding"],
                weaknesses=["Limited features", "Smaller customer base"]
            ),
            CompetitorProfile(
                competitor_id="comp_003",
                name="Niche Specialist Ltd",
                market_cap=1000000000.0,   # $1B
                revenue=100000000.0,       # $100M
                customer_count=5000,
                product_features={"specialized_analytics": True, "compliance": True},
                pricing_tiers=[
                    {"name": "Professional", "price": 2000, "model": "subscription"}
                ],
                market_segments={"Niche Vertical"},
                geographic_presence={"North America"},
                technology_stack={"Java": "17", "Angular": "15", "Azure": "latest"},
                competitive_advantages=["Deep domain expertise", "Compliance focus"],
                weaknesses=["Limited market reach", "Single vertical focus"]
            )
        ]
    
    @pytest.fixture
    def sample_market_segments(self):
        """Sample market segments for testing."""
        return [
            MarketSegment(
                segment_id="seg_001",
                name="Enterprise",
                size=10000000000.0,     # $10B market
                growth_rate=0.15,        # 15% annual growth
                customer_count=10000,
                avg_deal_size=100000,
                competitive_intensity=0.8,
                key_features=["ai_platform", "automation", "analytics", "enterprise_security"],
                price_sensitivity=0.3,   # Low price sensitivity
                technology_adoption="mainstream"
            ),
            MarketSegment(
                segment_id="seg_002", 
                name="Mid-Market",
                size=3000000000.0,      # $3B market
                growth_rate=0.20,       # 20% annual growth
                customer_count=30000,
                avg_deal_size=30000,
                competitive_intensity=0.9,
                key_features=["automation", "analytics", "mobile_app"],
                price_sensitivity=0.6,   # Moderate price sensitivity
                technology_adoption="mainstream"
            ),
            MarketSegment(
                segment_id="seg_003",
                name="SMB",
                size=1000000000.0,      # $1B market
                growth_rate=0.25,       # 25% annual growth
                customer_count=100000,
                avg_deal_size=5000,
                competitive_intensity=0.7,
                key_features=["automation", "mobile_app", "easy_setup"],
                price_sensitivity=0.9,   # High price sensitivity
                technology_adoption="early_adopter"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_initialize_landscape_mapper(self, landscape_mapper):
        """Test landscape mapper initialization."""
        assert landscape_mapper is not None
        assert landscape_mapper.analyses_generated == 0
        assert landscape_mapper.gaps_identified == 0
        assert landscape_mapper.min_competitors_for_clustering == 2
        assert landscape_mapper.position_dimensions == 2
    
    @pytest.mark.asyncio
    async def test_map_competitive_positions(
        self, landscape_mapper, sample_competitors, sample_market_segments
    ):
        """Test competitive positioning mapping."""
        analysis = await landscape_mapper.map_competitive_positions(
            competitors=sample_competitors,
            market_segments=sample_market_segments,
            time_horizon_months=12,
            correlation_id="test_correlation_001"
        )
        
        # Verify analysis structure
        assert isinstance(analysis, LandscapeAnalysis)
        assert analysis.correlation_id == "test_correlation_001"
        assert len(analysis.market_segments) == 3
        assert len(analysis.competitor_positions) > 0
        assert len(analysis.strategic_gaps) >= 0
        assert "positioning_matrix" in analysis.positioning_matrix
        assert len(analysis.recommendations) >= 0
        
        # Verify competitor positions
        for position in analysis.competitor_positions:
            assert isinstance(position, CompetitivePosition)
            assert position.competitor_id in [c.competitor_id for c in sample_competitors]
            assert 0.0 <= position.market_share <= 1.0
            assert 0.0 <= position.strength_score <= 1.0
            assert isinstance(position.position_type, MarketPosition)
            assert 0.0 <= position.confidence_score <= 1.0
        
        # Verify event was published
        landscape_mapper.event_bus.publish.assert_called_once()
        published_event = landscape_mapper.event_bus.publish.call_args[1]
        assert published_event['event_type'] == EventType.LANDSCAPE_MAPPED
    
    def test_calculate_market_shares(self, landscape_mapper, sample_competitors, sample_market_segments):
        """Test market share calculation."""
        enterprise_segment = sample_market_segments[0]
        
        # Test with customer count data
        market_shares = landscape_mapper._calculate_market_shares(
            sample_competitors, enterprise_segment
        )
        
        # Verify shares sum to 1.0 (approximately)
        total_share = sum(market_shares.values())
        assert abs(total_share - 1.0) < 0.01
        
        # Verify all competitors have shares
        assert len(market_shares) == len(sample_competitors)
        for comp in sample_competitors:
            assert comp.competitor_id in market_shares
            assert 0.0 <= market_shares[comp.competitor_id] <= 1.0
    
    def test_calculate_strength_score(self, landscape_mapper, sample_competitors, sample_market_segments):
        """Test competitive strength score calculation."""
        enterprise_segment = sample_market_segments[0]
        tech_leader = sample_competitors[0]  # Tech Leader Corp
        
        strength_score = landscape_mapper._calculate_strength_score(
            tech_leader, enterprise_segment
        )
        
        # Verify strength score is valid
        assert 0.0 <= strength_score <= 1.0
        
        # Tech Leader should have high strength due to features and advantages
        assert strength_score > 0.5  # Should be above average
        
        # Test with weaker competitor
        niche_specialist = sample_competitors[2]  # Smaller competitor
        niche_strength = landscape_mapper._calculate_strength_score(
            niche_specialist, enterprise_segment
        )
        
        # Tech Leader should be stronger than niche specialist in Enterprise
        assert strength_score > niche_strength
    
    def test_determine_position_type(self, landscape_mapper):
        """Test position type determination."""
        # Test leader position (high share, high strength)
        position_type = landscape_mapper._determine_position_type(
            market_share=0.4, strength_score=0.8, cluster_label=0
        )
        assert position_type == MarketPosition.LEADER
        
        # Test challenger position (lower share, high strength)
        position_type = landscape_mapper._determine_position_type(
            market_share=0.2, strength_score=0.7, cluster_label=0
        )
        assert position_type == MarketPosition.CHALLENGER
        
        # Test niche position (low share, high strength)
        position_type = landscape_mapper._determine_position_type(
            market_share=0.03, strength_score=0.7, cluster_label=0
        )
        assert position_type == MarketPosition.NICHE
        
        # Test follower position (moderate share, moderate strength)
        position_type = landscape_mapper._determine_position_type(
            market_share=0.3, strength_score=0.5, cluster_label=0
        )
        assert position_type == MarketPosition.FOLLOWER
    
    def test_extract_positioning_features(self, landscape_mapper, sample_competitors, sample_market_segments):
        """Test positioning features extraction."""
        enterprise_segment = sample_market_segments[0]
        
        feature_matrix = landscape_mapper._extract_positioning_features(
            sample_competitors, enterprise_segment
        )
        
        # Verify feature matrix shape
        assert feature_matrix.shape[0] == len(sample_competitors)
        assert feature_matrix.shape[1] > 0  # Should have multiple feature columns
        
        # Verify all values are numerical
        assert np.isfinite(feature_matrix).all()
    
    def test_identify_feature_gaps(self, landscape_mapper, sample_competitors, sample_market_segments):
        """Test feature gap identification."""
        enterprise_segment = sample_market_segments[0]
        
        feature_gaps = landscape_mapper._identify_feature_gaps(
            sample_competitors, enterprise_segment
        )
        
        # Verify gaps structure
        for gap in feature_gaps:
            assert isinstance(gap, StrategicGap)
            assert gap.gap_type == StrategicGapType.FEATURE_GAP
            assert gap.opportunity_size > 0
            assert 0.0 <= gap.difficulty_score <= 1.0
            assert gap.time_to_market > 0
            assert 0.0 <= gap.confidence_score <= 1.0
    
    def test_identify_pricing_gaps(self, landscape_mapper, sample_competitors, sample_market_segments):
        """Test pricing gap identification."""
        enterprise_segment = sample_market_segments[0]
        
        pricing_gaps = landscape_mapper._identify_pricing_gaps(
            sample_competitors, enterprise_segment
        )
        
        # Verify gaps structure
        for gap in pricing_gaps:
            assert isinstance(gap, StrategicGap)
            assert gap.gap_type == StrategicGapType.PRICING_GAP
            assert gap.opportunity_size > 0
            assert gap.time_to_market > 0
    
    def test_calculate_concentration_index(self, landscape_mapper, sample_competitors):
        """Test market concentration calculation."""
        concentration = landscape_mapper._calculate_concentration_index(sample_competitors)
        
        # HHI should be between 0 and 1
        assert 0.0 <= concentration <= 1.0
        
        # Test with empty competitors list
        empty_concentration = landscape_mapper._calculate_concentration_index([])
        assert empty_concentration == 0.0
    
    def test_analyze_technology_trends(self, landscape_mapper, sample_competitors):
        """Test technology trend analysis."""
        tech_trends = landscape_mapper._analyze_technology_trends(sample_competitors)
        
        # Verify structure
        assert "popular_technologies" in tech_trends
        assert "emerging_technologies" in tech_trends
        assert "technology_diversity" in tech_trends
        
        # Verify popular technologies are sorted by adoption
        popular_techs = tech_trends["popular_technologies"]
        if len(popular_techs) > 1:
            # Should be sorted by adoption rate (descending)
            for i in range(len(popular_techs) - 1):
                assert popular_techs[i][1] >= popular_techs[i + 1][1]
    
    def test_analyze_pricing_trends(self, landscape_mapper, sample_competitors):
        """Test pricing trend analysis."""
        pricing_trends = landscape_mapper._analyze_pricing_trends(sample_competitors)
        
        # Verify structure
        assert "price_range" in pricing_trends
        assert "popular_models" in pricing_trends
        assert "price_dispersion" in pricing_trends
        
        # Verify price range validity
        price_range = pricing_trends["price_range"]
        assert price_range["min"] >= 0
        assert price_range["max"] >= price_range["min"]
        assert price_range["avg"] >= price_range["min"]
        assert price_range["avg"] <= price_range["max"]
    
    def test_analyze_geographic_trends(self, landscape_mapper, sample_competitors):
        """Test geographic trend analysis."""
        geo_trends = landscape_mapper._analyze_geographic_trends(sample_competitors)
        
        # Verify structure
        assert "popular_regions" in geo_trends
        assert "expansion_opportunities" in geo_trends
        assert "geographic_diversity" in geo_trends
        
        # Verify geographic diversity count
        all_regions = set()
        for comp in sample_competitors:
            all_regions.update(comp.geographic_presence)
        
        assert geo_trends["geographic_diversity"] == len(all_regions)
    
    def test_create_positioning_matrix(self, landscape_mapper, sample_competitors):
        """Test positioning matrix creation."""
        # Create mock positions
        sample_positions = [
            CompetitivePosition(
                competitor_id="comp_001",
                segment_id="seg_001", 
                market_share=0.4,
                position_x=0.8,
                position_y=0.9,
                strength_score=0.9,
                position_type=MarketPosition.LEADER,
                momentum_vector=(0.1, 0.05),
                confidence_score=0.9
            ),
            CompetitivePosition(
                competitor_id="comp_002",
                segment_id="seg_001",
                market_share=0.15,
                position_x=0.3,
                position_y=0.7,
                strength_score=0.7,
                position_type=MarketPosition.CHALLENGER,
                momentum_vector=(0.05, 0.1),
                confidence_score=0.8
            )
        ]
        
        matrix = landscape_mapper._create_positioning_matrix(
            sample_competitors, sample_positions
        )
        
        # Verify matrix structure
        assert "dimensions" in matrix
        assert "quadrants" in matrix
        assert "competitors" in matrix
        
        # Verify dimensions
        assert "x_axis" in matrix["dimensions"]
        assert "y_axis" in matrix["dimensions"]
        
        # Verify quadrants
        quadrants = matrix["quadrants"]
        assert "leaders" in quadrants
        assert "challengers" in quadrants
        assert "followers" in quadrants
        assert "niches" in quadrants
        
        # Verify competitors list
        assert len(matrix["competitors"]) == len(sample_positions)
        for comp_data in matrix["competitors"]:
            assert "id" in comp_data
            assert "name" in comp_data
            assert "x" in comp_data
            assert "y" in comp_data
            assert "market_share" in comp_data
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, landscape_mapper, sample_competitors, sample_market_segments):
        """Test analysis caching."""
        # Set short cache TTL for testing
        landscape_mapper.analysis_cache_minutes = 0.01  # 0.6 seconds
        
        # First analysis call
        analysis1 = await landscape_mapper.map_competitive_positions(
            competitors=sample_competitors,
            market_segments=sample_market_segments
        )
        
        # Second call should use cache
        analysis2 = await landscape_mapper.map_competitive_positions(
            competitors=sample_competitors,
            market_segments=sample_market_segments
        )
        
        # Verify cache was used (same analysis ID would indicate cache hit)
        # Since we're generating new IDs, we check cache size instead
        assert len(landscape_mapper._analysis_cache) == 1
        
        # Wait for cache to expire
        import asyncio
        await asyncio.sleep(1)
        
        # Third call should bypass expired cache
        analysis3 = await landscape_mapper.map_competitive_positions(
            competitors=sample_competitors,
            market_segments=sample_market_segments
        )
        
        # Cache should have been refreshed
        assert analysis3.analysis_id != analysis1.analysis_id
    
    def test_performance_metrics(self, landscape_mapper):
        """Test performance metrics collection."""
        metrics = landscape_mapper.get_performance_metrics()
        
        assert "analyses_generated" in metrics
        assert "gaps_identified" in metrics
        assert "cache_hit_rate" in metrics
        assert "cached_analyses" in metrics
        assert "cached_competitors" in metrics
        
        # Initial values should be zero
        assert metrics["analyses_generated"] == 0
        assert metrics["gaps_identified"] == 0
        assert metrics["cached_analyses"] == 0
    
    def test_cache_key_generation(self, landscape_mapper, sample_competitors, sample_market_segments):
        """Test cache key generation consistency."""
        # Same inputs should generate same cache key
        key1 = landscape_mapper._generate_landscape_cache_key(
            sample_competitors, sample_market_segments
        )
        key2 = landscape_mapper._generate_landscape_cache_key(
            sample_competitors, sample_market_segments
        )
        
        assert key1 == key2
        
        # Different inputs should generate different keys
        modified_competitors = sample_competitors[:2]  # Remove one competitor
        key3 = landscape_mapper._generate_landscape_cache_key(
            modified_competitors, sample_market_segments
        )
        
        assert key1 != key3
    
    @pytest.mark.asyncio
    async def test_error_handling(self, landscape_mapper):
        """Test error handling with invalid inputs."""
        # Test with empty competitors list
        with pytest.raises(Exception):
            await landscape_mapper.map_competitive_positions(
                competitors=[],
                market_segments=[]
            )
    
    def test_momentum_vector_calculation(self, landscape_mapper, sample_competitors, sample_market_segments):
        """Test competitive momentum vector calculation."""
        competitor = sample_competitors[0]
        segment = sample_market_segments[0]
        
        momentum = landscape_mapper._calculate_momentum_vector(competitor, segment)
        
        # Verify momentum is a tuple of floats
        assert isinstance(momentum, tuple)
        assert len(momentum) == 2
        assert isinstance(momentum[0], float)
        assert isinstance(momentum[1], float)
    
    @pytest.mark.asyncio
    async def test_strategic_recommendations(self, landscape_mapper, sample_competitors, sample_market_segments):
        """Test strategic recommendation generation."""
        analysis = await landscape_mapper.map_competitive_positions(
            competitors=sample_competitors,
            market_segments=sample_market_segments
        )
        
        # Verify recommendations structure
        for recommendation in analysis.recommendations:
            assert "type" in recommendation
            assert "title" in recommendation
            assert "description" in recommendation
            assert "priority" in recommendation
            
            # Verify valid recommendation types
            valid_types = ["opportunity", "defense", "expansion", "competitive", "data_quality"]
            assert recommendation["type"] in valid_types