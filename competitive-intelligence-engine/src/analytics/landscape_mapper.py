"""
Enhanced Competitive Intelligence Engine - Competitive Landscape Mapper

This module implements dynamic competitive positioning analysis, market share visualization,
competitive strength assessment, and strategic gap identification.

Features:
- Real-time competitive positioning analysis
- Market share visualization data generation
- Competitive strength assessment across multiple dimensions
- Strategic gap identification and opportunity mapping
- Dynamic market boundary mapping and segmentation

Author: Claude
Date: January 2026
"""

import asyncio
import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from uuid import uuid4

import numpy as np
from scipy.spatial.distance import euclidean
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from ..core.event_bus import (
    EventBus, EventType, EventPriority, get_event_bus
)

# Configure logging
logger = logging.getLogger(__name__)


class CompetitiveStrength(Enum):
    """Competitive strength levels."""
    DOMINANT = "dominant"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NEGLIGIBLE = "negligible"


class MarketPosition(Enum):
    """Market positioning categories."""
    LEADER = "leader"
    CHALLENGER = "challenger"
    FOLLOWER = "follower"
    NICHE = "niche"
    EMERGING = "emerging"


class StrategicGapType(Enum):
    """Types of strategic gaps."""
    FEATURE_GAP = "feature_gap"
    PRICING_GAP = "pricing_gap"
    MARKET_GAP = "market_gap"
    TECHNOLOGY_GAP = "technology_gap"
    CUSTOMER_GAP = "customer_gap"
    DISTRIBUTION_GAP = "distribution_gap"


@dataclass
class CompetitorProfile:
    """Comprehensive competitor profile."""
    competitor_id: str
    name: str
    market_cap: Optional[float] = None
    revenue: Optional[float] = None
    customer_count: Optional[int] = None
    product_features: Dict[str, Any] = field(default_factory=dict)
    pricing_tiers: List[Dict[str, Any]] = field(default_factory=list)
    market_segments: Set[str] = field(default_factory=set)
    geographic_presence: Set[str] = field(default_factory=set)
    technology_stack: Dict[str, Any] = field(default_factory=dict)
    competitive_advantages: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MarketSegment:
    """Market segment definition."""
    segment_id: str
    name: str
    size: float  # Market size in dollars
    growth_rate: float  # Annual growth rate
    customer_count: int
    avg_deal_size: float
    competitive_intensity: float  # 0.0 to 1.0
    key_features: List[str]
    price_sensitivity: float  # 0.0 to 1.0
    technology_adoption: str  # early_adopter, mainstream, laggard


@dataclass
class CompetitivePosition:
    """Competitive position in market space."""
    competitor_id: str
    segment_id: str
    market_share: float  # 0.0 to 1.0
    position_x: float  # 2D positioning coordinate
    position_y: float  # 2D positioning coordinate
    strength_score: float  # 0.0 to 1.0
    position_type: MarketPosition
    momentum_vector: Tuple[float, float]  # Direction of movement
    confidence_score: float  # 0.0 to 1.0


@dataclass
class StrategicGap:
    """Identified strategic gap or opportunity."""
    gap_id: str
    gap_type: StrategicGapType
    description: str
    market_segments: List[str]
    opportunity_size: float  # Dollar value
    difficulty_score: float  # 0.0 to 1.0 (ease of addressing)
    time_to_market: int  # Months
    competitive_threats: List[str]
    required_capabilities: List[str]
    confidence_score: float


@dataclass
class LandscapeAnalysis:
    """Complete competitive landscape analysis."""
    analysis_id: str
    created_at: datetime
    market_segments: List[MarketSegment]
    competitor_positions: List[CompetitivePosition]
    strategic_gaps: List[StrategicGap]
    market_dynamics: Dict[str, Any]
    positioning_matrix: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    correlation_id: Optional[str] = None


class LandscapeMapper:
    """
    Competitive Landscape Mapper - Dynamic Market Positioning
    
    This mapper analyzes competitive landscapes using multi-dimensional analysis,
    clustering algorithms, and strategic positioning frameworks to provide
    real-time competitive intelligence and opportunity identification.
    
    Features:
    - Real-time competitive positioning analysis
    - Market share visualization data generation
    - Competitive strength assessment across dimensions
    - Strategic gap identification with ML clustering
    - Dynamic market boundary mapping
    """
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        analysis_cache_minutes: int = 30,
        min_competitors_for_clustering: int = 3,
        position_dimensions: int = 2
    ):
        """
        Initialize the Landscape Mapper.
        
        Args:
            event_bus: Event bus for coordination
            analysis_cache_minutes: Cache duration for analyses
            min_competitors_for_clustering: Minimum competitors for clustering
            position_dimensions: Dimensions for positioning analysis
        """
        self.event_bus = event_bus or get_event_bus()
        self.analysis_cache_minutes = analysis_cache_minutes
        self.min_competitors_for_clustering = min_competitors_for_clustering
        self.position_dimensions = position_dimensions
        
        # Analysis cache
        self._analysis_cache: Dict[str, Tuple[LandscapeAnalysis, datetime]] = {}
        self._competitor_cache: Dict[str, Tuple[CompetitorProfile, datetime]] = {}
        
        # ML components
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=position_dimensions)
        
        # Performance metrics
        self.analyses_generated = 0
        self.gaps_identified = 0
        self.cache_hit_rate = 0.0
        
        logger.info("Landscape Mapper initialized")
    
    async def map_competitive_positions(
        self,
        competitors: List[CompetitorProfile],
        market_segments: List[MarketSegment],
        time_horizon_months: int = 12,
        correlation_id: Optional[str] = None
    ) -> LandscapeAnalysis:
        """
        Generate comprehensive competitive landscape mapping.
        
        Args:
            competitors: Competitor profiles to analyze
            market_segments: Market segments to consider
            time_horizon_months: Analysis time horizon
            correlation_id: Event correlation tracking
            
        Returns:
            Complete landscape analysis with positioning
        """
        start_time = datetime.now()
        
        try:
            # Generate cache key
            cache_key = self._generate_landscape_cache_key(competitors, market_segments)
            
            # Check cache
            cached_analysis = self._get_cached_analysis(cache_key)
            if cached_analysis:
                logger.debug(f"Cache hit for landscape analysis: {cache_key}")
                return cached_analysis
            
            # Perform competitive positioning analysis
            positioning_analysis = await self._analyze_competitive_positioning(
                competitors, market_segments
            )
            
            # Identify strategic gaps
            strategic_gaps = await self._identify_strategic_gaps(
                competitors, market_segments, positioning_analysis
            )
            
            # Generate market dynamics analysis
            market_dynamics = self._analyze_market_dynamics(
                competitors, market_segments, time_horizon_months
            )
            
            # Create positioning matrix for visualization
            positioning_matrix = self._create_positioning_matrix(
                competitors, positioning_analysis
            )
            
            # Generate strategic recommendations
            recommendations = await self._generate_strategic_recommendations(
                positioning_analysis, strategic_gaps, market_dynamics
            )
            
            # Create comprehensive analysis
            analysis = LandscapeAnalysis(
                analysis_id=str(uuid4()),
                created_at=datetime.now(timezone.utc),
                market_segments=market_segments,
                competitor_positions=positioning_analysis,
                strategic_gaps=strategic_gaps,
                market_dynamics=market_dynamics,
                positioning_matrix=positioning_matrix,
                recommendations=recommendations,
                correlation_id=correlation_id
            )
            
            # Cache the result
            self._cache_analysis(cache_key, analysis)
            
            # Update metrics
            self.analyses_generated += 1
            self.gaps_identified += len(strategic_gaps)
            
            # Publish event
            await self._publish_landscape_event(analysis)
            
            analysis_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Generated landscape analysis with {len(positioning_analysis)} "
                f"positions and {len(strategic_gaps)} gaps in {analysis_time:.2f} seconds"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to map competitive positions: {e}")
            raise
    
    async def _analyze_competitive_positioning(
        self,
        competitors: List[CompetitorProfile],
        market_segments: List[MarketSegment]
    ) -> List[CompetitivePosition]:
        """Analyze competitive positions using multi-dimensional analysis."""
        try:
            positions = []
            
            for segment in market_segments:
                # Get competitors active in this segment
                segment_competitors = [
                    comp for comp in competitors
                    if segment.name in comp.market_segments or not comp.market_segments
                ]
                
                if len(segment_competitors) < 2:
                    continue  # Skip segments with insufficient competitors
                
                # Calculate market shares
                market_shares = self._calculate_market_shares(
                    segment_competitors, segment
                )
                
                # Perform positioning analysis
                if len(segment_competitors) >= self.min_competitors_for_clustering:
                    segment_positions = await self._cluster_competitive_positions(
                        segment_competitors, segment, market_shares
                    )
                else:
                    segment_positions = self._simple_positioning_analysis(
                        segment_competitors, segment, market_shares
                    )
                
                positions.extend(segment_positions)
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to analyze competitive positioning: {e}")
            raise
    
    async def _cluster_competitive_positions(
        self,
        competitors: List[CompetitorProfile],
        segment: MarketSegment,
        market_shares: Dict[str, float]
    ) -> List[CompetitivePosition]:
        """Use ML clustering for competitive positioning."""
        try:
            # Extract features for positioning
            feature_matrix = self._extract_positioning_features(competitors, segment)
            
            if feature_matrix.size == 0:
                return self._simple_positioning_analysis(competitors, segment, market_shares)
            
            # Standardize features
            scaled_features = self.scaler.fit_transform(feature_matrix)
            
            # Reduce dimensions for 2D positioning
            if scaled_features.shape[1] > self.position_dimensions:
                positioned_features = self.pca.fit_transform(scaled_features)
            else:
                positioned_features = scaled_features
                # Pad with zeros if needed
                if positioned_features.shape[1] < self.position_dimensions:
                    padding = np.zeros((positioned_features.shape[0], 
                                      self.position_dimensions - positioned_features.shape[1]))
                    positioned_features = np.hstack([positioned_features, padding])
            
            # Perform clustering to identify strategic groups
            if len(competitors) >= 4:
                clustering = DBSCAN(eps=0.5, min_samples=2).fit(positioned_features)
            else:
                # Use simple k-means for smaller competitor sets
                n_clusters = min(3, len(competitors))
                clustering = KMeans(n_clusters=n_clusters, random_state=42).fit(positioned_features)
            
            # Create competitive positions
            positions = []
            for i, competitor in enumerate(competitors):
                cluster_label = clustering.labels_[i] if hasattr(clustering, 'labels_') else 0
                
                # Calculate strength score
                strength_score = self._calculate_strength_score(competitor, segment)
                
                # Determine market position type
                position_type = self._determine_position_type(
                    market_shares.get(competitor.competitor_id, 0.0),
                    strength_score,
                    cluster_label
                )
                
                # Calculate momentum vector (simplified)
                momentum = self._calculate_momentum_vector(competitor, segment)
                
                position = CompetitivePosition(
                    competitor_id=competitor.competitor_id,
                    segment_id=segment.segment_id,
                    market_share=market_shares.get(competitor.competitor_id, 0.0),
                    position_x=positioned_features[i, 0],
                    position_y=positioned_features[i, 1],
                    strength_score=strength_score,
                    position_type=position_type,
                    momentum_vector=momentum,
                    confidence_score=0.8  # High confidence for clustered analysis
                )
                
                positions.append(position)
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to cluster competitive positions: {e}")
            # Fallback to simple analysis
            return self._simple_positioning_analysis(competitors, segment, market_shares)
    
    def _extract_positioning_features(
        self,
        competitors: List[CompetitorProfile],
        segment: MarketSegment
    ) -> np.ndarray:
        """Extract numerical features for competitive positioning."""
        try:
            features = []
            
            for competitor in competitors:
                feature_vector = []
                
                # Financial features
                feature_vector.append(competitor.revenue or 0.0)
                feature_vector.append(competitor.customer_count or 0)
                
                # Product features (count of features in segment)
                relevant_features = len([
                    f for f in competitor.product_features.keys()
                    if f in segment.key_features
                ])
                feature_vector.append(relevant_features)
                
                # Pricing position (average of pricing tiers)
                avg_price = 0.0
                if competitor.pricing_tiers:
                    prices = [tier.get('price', 0) for tier in competitor.pricing_tiers]
                    avg_price = sum(prices) / len(prices)
                feature_vector.append(avg_price)
                
                # Geographic presence
                feature_vector.append(len(competitor.geographic_presence))
                
                # Competitive advantages count
                feature_vector.append(len(competitor.competitive_advantages))
                
                # Technology score (simplified)
                tech_score = len(competitor.technology_stack)
                feature_vector.append(tech_score)
                
                features.append(feature_vector)
            
            return np.array(features) if features else np.array([])
            
        except Exception as e:
            logger.error(f"Failed to extract positioning features: {e}")
            return np.array([])
    
    def _simple_positioning_analysis(
        self,
        competitors: List[CompetitorProfile],
        segment: MarketSegment,
        market_shares: Dict[str, float]
    ) -> List[CompetitivePosition]:
        """Simple positioning analysis for small competitor sets."""
        positions = []
        
        for i, competitor in enumerate(competitors):
            # Simple 2D positioning based on market share and strength
            market_share = market_shares.get(competitor.competitor_id, 0.0)
            strength_score = self._calculate_strength_score(competitor, segment)
            
            # Position based on market share (x) and strength (y)
            position_x = market_share
            position_y = strength_score
            
            # Add some spacing for visualization
            position_x += (i * 0.1) - 0.05
            
            position_type = self._determine_position_type(
                market_share, strength_score, 0
            )
            
            momentum = self._calculate_momentum_vector(competitor, segment)
            
            position = CompetitivePosition(
                competitor_id=competitor.competitor_id,
                segment_id=segment.segment_id,
                market_share=market_share,
                position_x=position_x,
                position_y=position_y,
                strength_score=strength_score,
                position_type=position_type,
                momentum_vector=momentum,
                confidence_score=0.6  # Lower confidence for simple analysis
            )
            
            positions.append(position)
        
        return positions
    
    def _calculate_market_shares(
        self,
        competitors: List[CompetitorProfile],
        segment: MarketSegment
    ) -> Dict[str, float]:
        """Calculate market shares for competitors in segment."""
        try:
            # Use customer count as proxy if available, otherwise revenue
            shares = {}
            total_value = 0.0
            competitor_values = {}
            
            for competitor in competitors:
                # Prefer customer count for market share calculation
                value = competitor.customer_count or 0
                if value == 0:
                    # Fallback to revenue
                    value = competitor.revenue or 0
                
                competitor_values[competitor.competitor_id] = value
                total_value += value
            
            # Calculate shares
            if total_value > 0:
                for comp_id, value in competitor_values.items():
                    shares[comp_id] = value / total_value
            else:
                # Equal shares if no data available
                equal_share = 1.0 / len(competitors) if competitors else 0.0
                for competitor in competitors:
                    shares[competitor.competitor_id] = equal_share
            
            return shares
            
        except Exception as e:
            logger.error(f"Failed to calculate market shares: {e}")
            return {}
    
    def _calculate_strength_score(
        self,
        competitor: CompetitorProfile,
        segment: MarketSegment
    ) -> float:
        """Calculate competitive strength score for competitor in segment."""
        try:
            score_components = []
            
            # Feature coverage in segment
            if segment.key_features:
                feature_coverage = len([
                    f for f in competitor.product_features.keys()
                    if f in segment.key_features
                ]) / len(segment.key_features)
                score_components.append(feature_coverage * 0.3)
            
            # Financial strength (normalized)
            if competitor.revenue:
                # Normalize revenue (simple logarithmic scaling)
                revenue_score = min(1.0, math.log10(competitor.revenue) / 10.0)
                score_components.append(revenue_score * 0.2)
            
            # Customer base strength
            if competitor.customer_count:
                customer_score = min(1.0, math.log10(competitor.customer_count) / 6.0)
                score_components.append(customer_score * 0.2)
            
            # Competitive advantages
            advantage_score = min(1.0, len(competitor.competitive_advantages) / 5.0)
            score_components.append(advantage_score * 0.15)
            
            # Geographic presence
            geo_score = min(1.0, len(competitor.geographic_presence) / 10.0)
            score_components.append(geo_score * 0.1)
            
            # Technology stack
            tech_score = min(1.0, len(competitor.technology_stack) / 8.0)
            score_components.append(tech_score * 0.05)
            
            # Calculate weighted average
            total_score = sum(score_components) if score_components else 0.5
            return min(1.0, max(0.0, total_score))
            
        except Exception as e:
            logger.error(f"Failed to calculate strength score: {e}")
            return 0.5  # Default moderate strength
    
    def _determine_position_type(
        self,
        market_share: float,
        strength_score: float,
        cluster_label: int
    ) -> MarketPosition:
        """Determine market position type based on share and strength."""
        if market_share > 0.3 and strength_score > 0.7:
            return MarketPosition.LEADER
        elif market_share > 0.15 and strength_score > 0.6:
            return MarketPosition.CHALLENGER
        elif market_share < 0.05 and strength_score > 0.6:
            return MarketPosition.NICHE
        elif strength_score < 0.4:
            return MarketPosition.EMERGING
        else:
            return MarketPosition.FOLLOWER
    
    def _calculate_momentum_vector(
        self,
        competitor: CompetitorProfile,
        segment: MarketSegment
    ) -> Tuple[float, float]:
        """Calculate momentum vector for competitive movement."""
        # Simplified momentum calculation
        # In practice, this would use historical data
        
        # Base momentum on competitive advantages vs weaknesses
        advantages = len(competitor.competitive_advantages)
        weaknesses = len(competitor.weaknesses)
        
        momentum_strength = (advantages - weaknesses) * 0.1
        
        # Direction based on segment growth and tech alignment
        x_momentum = segment.growth_rate * 0.01  # Market growth
        y_momentum = momentum_strength  # Competitive strength change
        
        return (x_momentum, y_momentum)
    
    async def _identify_strategic_gaps(
        self,
        competitors: List[CompetitorProfile],
        market_segments: List[MarketSegment],
        positioning_analysis: List[CompetitivePosition]
    ) -> List[StrategicGap]:
        """Identify strategic gaps and opportunities in the market."""
        try:
            gaps = []
            
            for segment in market_segments:
                segment_gaps = await self._analyze_segment_gaps(
                    competitors, segment, positioning_analysis
                )
                gaps.extend(segment_gaps)
            
            # Sort gaps by opportunity size and confidence
            gaps.sort(key=lambda g: g.opportunity_size * g.confidence_score, reverse=True)
            
            return gaps
            
        except Exception as e:
            logger.error(f"Failed to identify strategic gaps: {e}")
            return []
    
    async def _analyze_segment_gaps(
        self,
        competitors: List[CompetitorProfile],
        segment: MarketSegment,
        positioning_analysis: List[CompetitivePosition]
    ) -> List[StrategicGap]:
        """Analyze strategic gaps within a specific market segment."""
        gaps = []
        
        # Get positions in this segment
        segment_positions = [
            pos for pos in positioning_analysis
            if pos.segment_id == segment.segment_id
        ]
        
        # Feature gaps
        feature_gaps = self._identify_feature_gaps(competitors, segment)
        gaps.extend(feature_gaps)
        
        # Pricing gaps
        pricing_gaps = self._identify_pricing_gaps(competitors, segment)
        gaps.extend(pricing_gaps)
        
        # Market coverage gaps
        coverage_gaps = self._identify_coverage_gaps(segment_positions, segment)
        gaps.extend(coverage_gaps)
        
        return gaps
    
    def _identify_feature_gaps(
        self,
        competitors: List[CompetitorProfile],
        segment: MarketSegment
    ) -> List[StrategicGap]:
        """Identify feature gaps in the market segment."""
        gaps = []
        
        # Find features that are requested but not well-served
        all_competitor_features = set()
        for competitor in competitors:
            all_competitor_features.update(competitor.product_features.keys())
        
        # Features in segment but missing from most competitors
        for feature in segment.key_features:
            competitors_with_feature = sum(
                1 for comp in competitors
                if feature in comp.product_features
            )
            
            coverage_ratio = competitors_with_feature / len(competitors) if competitors else 0
            
            # If less than 50% have the feature, it's a gap
            if coverage_ratio < 0.5:
                gap = StrategicGap(
                    gap_id=str(uuid4()),
                    gap_type=StrategicGapType.FEATURE_GAP,
                    description=f"Underserved feature: {feature}",
                    market_segments=[segment.segment_id],
                    opportunity_size=segment.size * (1 - coverage_ratio) * 0.1,
                    difficulty_score=0.5,  # Default moderate difficulty
                    time_to_market=6,  # 6 months for feature development
                    competitive_threats=[
                        comp.competitor_id for comp in competitors
                        if feature in comp.product_features
                    ],
                    required_capabilities=[f"Development of {feature}"],
                    confidence_score=0.7
                )
                gaps.append(gap)
        
        return gaps
    
    def _identify_pricing_gaps(
        self,
        competitors: List[CompetitorProfile],
        segment: MarketSegment
    ) -> List[StrategicGap]:
        """Identify pricing gaps in the market segment."""
        gaps = []
        
        # Collect all pricing points
        all_prices = []
        for competitor in competitors:
            for tier in competitor.pricing_tiers:
                price = tier.get('price', 0)
                if price > 0:
                    all_prices.append(price)
        
        if len(all_prices) < 2:
            return gaps  # Need at least 2 pricing points
        
        # Sort prices
        all_prices.sort()
        
        # Find large gaps between pricing tiers
        for i in range(len(all_prices) - 1):
            gap_size = all_prices[i + 1] - all_prices[i]
            
            # If gap is larger than 50% of the lower price, it's significant
            if gap_size > all_prices[i] * 0.5 and gap_size > 1000:  # Minimum $1000 gap
                gap = StrategicGap(
                    gap_id=str(uuid4()),
                    gap_type=StrategicGapType.PRICING_GAP,
                    description=f"Pricing gap between ${all_prices[i]:,.0f} and ${all_prices[i+1]:,.0f}",
                    market_segments=[segment.segment_id],
                    opportunity_size=segment.size * 0.1,  # 10% of segment
                    difficulty_score=0.3,  # Pricing easier than features
                    time_to_market=3,  # 3 months for pricing strategy
                    competitive_threats=[],
                    required_capabilities=["Pricing strategy", "Value positioning"],
                    confidence_score=0.8
                )
                gaps.append(gap)
        
        return gaps
    
    def _identify_coverage_gaps(
        self,
        segment_positions: List[CompetitivePosition],
        segment: MarketSegment
    ) -> List[StrategicGap]:
        """Identify market coverage gaps using position analysis."""
        gaps = []
        
        if len(segment_positions) < 2:
            return gaps
        
        # Find areas of positioning space with low competitor density
        positions = [(pos.position_x, pos.position_y) for pos in segment_positions]
        
        # Simple gap detection - find areas far from existing competitors
        for i, pos1 in enumerate(positions):
            min_distance = float('inf')
            for j, pos2 in enumerate(positions):
                if i != j:
                    distance = euclidean(pos1, pos2)
                    min_distance = min(min_distance, distance)
            
            # If this position is isolated (far from others), there might be a gap
            if min_distance > 0.5:  # Threshold for isolation
                gap = StrategicGap(
                    gap_id=str(uuid4()),
                    gap_type=StrategicGapType.MARKET_GAP,
                    description=f"Underserved market position at ({pos1[0]:.2f}, {pos1[1]:.2f})",
                    market_segments=[segment.segment_id],
                    opportunity_size=segment.size * 0.05,  # 5% of segment
                    difficulty_score=0.6,
                    time_to_market=12,  # Longer for new market positioning
                    competitive_threats=[pos.competitor_id for pos in segment_positions],
                    required_capabilities=["Market positioning", "Product differentiation"],
                    confidence_score=0.6
                )
                gaps.append(gap)
        
        return gaps
    
    def _analyze_market_dynamics(
        self,
        competitors: List[CompetitorProfile],
        market_segments: List[MarketSegment],
        time_horizon_months: int
    ) -> Dict[str, Any]:
        """Analyze overall market dynamics and trends."""
        dynamics = {
            "market_growth": {
                "overall_growth": sum(seg.growth_rate for seg in market_segments) / len(market_segments) if market_segments else 0,
                "fastest_growing_segment": max(market_segments, key=lambda s: s.growth_rate).name if market_segments else None,
                "growth_forecast": {}
            },
            "competitive_intensity": {
                "average_intensity": sum(seg.competitive_intensity for seg in market_segments) / len(market_segments) if market_segments else 0,
                "most_competitive_segment": max(market_segments, key=lambda s: s.competitive_intensity).name if market_segments else None,
                "concentration_index": self._calculate_concentration_index(competitors)
            },
            "technology_trends": self._analyze_technology_trends(competitors),
            "pricing_trends": self._analyze_pricing_trends(competitors),
            "geographic_expansion": self._analyze_geographic_trends(competitors)
        }
        
        return dynamics
    
    def _calculate_concentration_index(self, competitors: List[CompetitorProfile]) -> float:
        """Calculate market concentration index (simplified HHI)."""
        if not competitors:
            return 0.0
        
        # Use revenue as proxy for market concentration
        revenues = [comp.revenue or 0 for comp in competitors]
        total_revenue = sum(revenues)
        
        if total_revenue == 0:
            return 0.0
        
        # Calculate Herfindahl-Hirschman Index
        hhi = sum((revenue / total_revenue) ** 2 for revenue in revenues)
        return hhi
    
    def _analyze_technology_trends(self, competitors: List[CompetitorProfile]) -> Dict[str, Any]:
        """Analyze technology adoption trends."""
        all_technologies = {}
        for competitor in competitors:
            for tech, version in competitor.technology_stack.items():
                if tech not in all_technologies:
                    all_technologies[tech] = 0
                all_technologies[tech] += 1
        
        # Sort by adoption rate
        adoption_rates = {
            tech: count / len(competitors) for tech, count in all_technologies.items()
        } if competitors else {}
        
        return {
            "popular_technologies": sorted(adoption_rates.items(), key=lambda x: x[1], reverse=True)[:5],
            "emerging_technologies": [tech for tech, rate in adoption_rates.items() if 0.1 <= rate <= 0.3],
            "technology_diversity": len(all_technologies)
        }
    
    def _analyze_pricing_trends(self, competitors: List[CompetitorProfile]) -> Dict[str, Any]:
        """Analyze pricing strategy trends."""
        all_prices = []
        pricing_models = {}
        
        for competitor in competitors:
            for tier in competitor.pricing_tiers:
                price = tier.get('price', 0)
                if price > 0:
                    all_prices.append(price)
                
                model = tier.get('model', 'unknown')
                pricing_models[model] = pricing_models.get(model, 0) + 1
        
        return {
            "price_range": {
                "min": min(all_prices) if all_prices else 0,
                "max": max(all_prices) if all_prices else 0,
                "avg": sum(all_prices) / len(all_prices) if all_prices else 0
            },
            "popular_models": sorted(pricing_models.items(), key=lambda x: x[1], reverse=True),
            "price_dispersion": np.std(all_prices) if all_prices else 0
        }
    
    def _analyze_geographic_trends(self, competitors: List[CompetitorProfile]) -> Dict[str, Any]:
        """Analyze geographic expansion trends."""
        geographic_coverage = {}
        for competitor in competitors:
            for region in competitor.geographic_presence:
                geographic_coverage[region] = geographic_coverage.get(region, 0) + 1
        
        return {
            "popular_regions": sorted(geographic_coverage.items(), key=lambda x: x[1], reverse=True),
            "expansion_opportunities": [region for region, count in geographic_coverage.items() if count <= 2],
            "geographic_diversity": len(geographic_coverage)
        }
    
    def _create_positioning_matrix(
        self,
        competitors: List[CompetitorProfile],
        positions: List[CompetitivePosition]
    ) -> Dict[str, Any]:
        """Create positioning matrix for visualization."""
        matrix = {
            "dimensions": {
                "x_axis": "Market Share / Reach",
                "y_axis": "Competitive Strength"
            },
            "quadrants": {
                "leaders": [],      # High share, high strength
                "challengers": [],  # Lower share, high strength  
                "followers": [],    # High share, lower strength
                "niches": []       # Lower share, lower strength
            },
            "competitors": []
        }
        
        for position in positions:
            competitor = next((c for c in competitors if c.competitor_id == position.competitor_id), None)
            if not competitor:
                continue
            
            comp_data = {
                "id": position.competitor_id,
                "name": competitor.name,
                "x": position.position_x,
                "y": position.position_y,
                "market_share": position.market_share,
                "strength_score": position.strength_score,
                "position_type": position.position_type.value,
                "momentum": position.momentum_vector
            }
            
            # Categorize into quadrants
            if position.market_share > 0.2 and position.strength_score > 0.7:
                matrix["quadrants"]["leaders"].append(comp_data)
            elif position.market_share <= 0.2 and position.strength_score > 0.7:
                matrix["quadrants"]["challengers"].append(comp_data)
            elif position.market_share > 0.2 and position.strength_score <= 0.7:
                matrix["quadrants"]["followers"].append(comp_data)
            else:
                matrix["quadrants"]["niches"].append(comp_data)
            
            matrix["competitors"].append(comp_data)
        
        return matrix
    
    async def _generate_strategic_recommendations(
        self,
        positions: List[CompetitivePosition],
        gaps: List[StrategicGap],
        dynamics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on landscape analysis."""
        recommendations = []
        
        # Recommendation 1: Top opportunity gaps
        top_gaps = sorted(gaps, key=lambda g: g.opportunity_size, reverse=True)[:3]
        if top_gaps:
            recommendations.append({
                "type": "opportunity",
                "title": "Top Strategic Opportunities",
                "description": f"Focus on {len(top_gaps)} highest-value strategic gaps",
                "gaps": [g.gap_id for g in top_gaps],
                "total_value": sum(g.opportunity_size for g in top_gaps),
                "priority": "high"
            })
        
        # Recommendation 2: Competitive threats
        weak_positions = [pos for pos in positions if pos.strength_score < 0.4]
        if weak_positions:
            recommendations.append({
                "type": "defense",
                "title": "Strengthen Weak Positions",
                "description": f"Address {len(weak_positions)} vulnerable market positions",
                "positions": [pos.competitor_id for pos in weak_positions],
                "priority": "medium"
            })
        
        # Recommendation 3: Market dynamics
        if dynamics["market_growth"]["overall_growth"] > 0.1:
            recommendations.append({
                "type": "expansion",
                "title": "Capitalize on Market Growth",
                "description": f"Market growing at {dynamics['market_growth']['overall_growth']:.1%} annually",
                "fastest_segment": dynamics["market_growth"]["fastest_growing_segment"],
                "priority": "high"
            })
        
        return recommendations
    
    def _generate_landscape_cache_key(
        self,
        competitors: List[CompetitorProfile],
        segments: List[MarketSegment]
    ) -> str:
        """Generate cache key for landscape analysis."""
        import hashlib
        
        comp_hash = str(sum(hash(c.competitor_id) for c in competitors))
        seg_hash = str(sum(hash(s.segment_id) for s in segments))
        
        key_string = f"{comp_hash}|{seg_hash}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_analysis(self, cache_key: str) -> Optional[LandscapeAnalysis]:
        """Get cached landscape analysis if still valid."""
        if cache_key in self._analysis_cache:
            analysis, timestamp = self._analysis_cache[cache_key]
            
            cache_age = datetime.now() - timestamp
            if cache_age < timedelta(minutes=self.analysis_cache_minutes):
                return analysis
            else:
                del self._analysis_cache[cache_key]
        
        return None
    
    def _cache_analysis(self, cache_key: str, analysis: LandscapeAnalysis):
        """Cache landscape analysis."""
        self._analysis_cache[cache_key] = (analysis, datetime.now())
        
        # Clean old entries
        if len(self._analysis_cache) > 50:
            oldest_keys = sorted(
                self._analysis_cache.keys(),
                key=lambda k: self._analysis_cache[k][1]
            )[:-50]
            
            for key in oldest_keys:
                del self._analysis_cache[key]
    
    async def _publish_landscape_event(self, analysis: LandscapeAnalysis):
        """Publish landscape analysis event."""
        try:
            await self.event_bus.publish(
                event_type=EventType.LANDSCAPE_MAPPED,
                data={
                    "analysis_id": analysis.analysis_id,
                    "segments_analyzed": len(analysis.market_segments),
                    "positions_mapped": len(analysis.competitor_positions),
                    "gaps_identified": len(analysis.strategic_gaps),
                    "total_opportunity_value": sum(g.opportunity_size for g in analysis.strategic_gaps),
                    "created_at": analysis.created_at.isoformat()
                },
                source_system="landscape_mapper",
                priority=EventPriority.MEDIUM,
                correlation_id=analysis.correlation_id
            )
            
        except Exception as e:
            logger.error(f"Failed to publish landscape event: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get mapper performance metrics."""
        return {
            "analyses_generated": self.analyses_generated,
            "gaps_identified": self.gaps_identified,
            "cache_hit_rate": self.cache_hit_rate,
            "cached_analyses": len(self._analysis_cache),
            "cached_competitors": len(self._competitor_cache)
        }


# Export public API
__all__ = [
    "LandscapeMapper",
    "CompetitorProfile", 
    "MarketSegment",
    "CompetitivePosition",
    "StrategicGap",
    "LandscapeAnalysis",
    "CompetitiveStrength",
    "MarketPosition",
    "StrategicGapType"
]