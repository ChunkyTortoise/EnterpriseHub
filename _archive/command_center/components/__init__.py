"""
Command Center Components Package

Enterprise-grade dashboard components for Jorge's Real Estate AI system:

Components:
- predictive_insights.py: ML-powered forecasting and anomaly detection
- global_filters.py: Consistent filtering across all dashboards  
- theme_manager.py: Enterprise theming and styling

Integration Features:
- Consistent styling and theming
- Shared filtering capabilities
- ML analytics integration
- Jorge's commission calculations (6% rate)
- Real-time monitoring and alerts
"""

from .predictive_insights import PredictiveInsightsDashboard, render_predictive_insights_dashboard
from .global_filters import GlobalFilters, create_global_filters
from .theme_manager import ThemeManager, ThemePresets, apply_enterprise_theme, style_enterprise_chart

__all__ = [
    'PredictiveInsightsDashboard',
    'render_predictive_insights_dashboard', 
    'GlobalFilters',
    'create_global_filters',
    'ThemeManager',
    'ThemePresets', 
    'apply_enterprise_theme',
    'style_enterprise_chart'
]

# Version info
__version__ = "1.0.0"
__author__ = "Jorge Real Estate AI System"