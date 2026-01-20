"""
Enhanced Competitive Intelligence Engine - Analytics Package

This package provides executive-grade analytics capabilities including:
- Executive Analytics Engine with Claude 3.5 Sonnet integration
- Competitive Landscape Mapper for positioning analysis
- Market Share Analytics for time series forecasting

Author: Claude
Date: January 2026
"""

from .executive_analytics_engine import (
    ExecutiveAnalyticsEngine,
    StakeholderType,
    ThreatLevel,
    OpportunityType,
    ExecutiveSummary,
    StrategicPattern,
    ROIAnalysis,
    CompetitiveIntelligence,
    PredictionData
)

from .landscape_mapper import (
    LandscapeMapper,
    CompetitorProfile,
    MarketSegment,
    CompetitivePosition,
    StrategicGap,
    LandscapeAnalysis,
    CompetitiveStrength,
    MarketPosition,
    StrategicGapType
)

from .market_share_analytics import (
    MarketShareAnalytics,
    MarketShareDataPoint,
    TimeSeriesForecast,
    CompetitiveDynamics,
    MarketExpansionOpportunity,
    MarketShareAnalysis,
    TrendType,
    ForecastHorizon,
    ModelType
)

# Version and metadata
__version__ = "1.0.0"
__author__ = "Claude"

# Package-level exports
__all__ = [
    # Executive Analytics
    "ExecutiveAnalyticsEngine",
    "StakeholderType",
    "ThreatLevel", 
    "OpportunityType",
    "ExecutiveSummary",
    "StrategicPattern",
    "ROIAnalysis",
    "CompetitiveIntelligence",
    "PredictionData",
    
    # Landscape Mapping
    "LandscapeMapper",
    "CompetitorProfile",
    "MarketSegment", 
    "CompetitivePosition",
    "StrategicGap",
    "LandscapeAnalysis",
    "CompetitiveStrength",
    "MarketPosition",
    "StrategicGapType",
    
    # Market Share Analytics
    "MarketShareAnalytics",
    "MarketShareDataPoint",
    "TimeSeriesForecast",
    "CompetitiveDynamics", 
    "MarketExpansionOpportunity",
    "MarketShareAnalysis",
    "TrendType",
    "ForecastHorizon",
    "ModelType"
]