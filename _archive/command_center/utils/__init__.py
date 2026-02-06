"""
Jorge's Command Center Utilities

Advanced utilities for dashboard analytics, chart generation,
and data visualization with Jorge theme integration.

Modules:
- chart_builders: Comprehensive chart factory with ML and real estate analytics
- theme_manager: Centralized theme and styling management
- data_processors: Optimized data processing utilities
- export_manager: Report and presentation export functionality
"""

from .chart_builders import (
    ChartFactory,
    JorgeTheme,
    MLPerformanceCharts,
    RealEstateAnalyticsCharts,
    InteractiveDashboardWidgets,
    quick_roc_curve,
    quick_lead_analysis,
    quick_kpi_card
)

__all__ = [
    'ChartFactory',
    'JorgeTheme',
    'MLPerformanceCharts',
    'RealEstateAnalyticsCharts', 
    'InteractiveDashboardWidgets',
    'quick_roc_curve',
    'quick_lead_analysis',
    'quick_kpi_card'
]

__version__ = "2.0.0"
__author__ = "Jorge Real Estate AI Team"