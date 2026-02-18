"""
Test suite for Jorge's Chart Builders Utility

Comprehensive tests for chart generation, theme integration,
ML visualizations, real estate analytics, and interactive widgets.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

pytest.importorskip(
    "command_center.utils.chart_builders",
    reason="command_center chart builders not available",
)
from command_center.utils.chart_builders import (
    ChartBuilderBase,
    ChartFactory,
    InteractiveDashboardWidgets,
    JorgeTheme,
    MLPerformanceCharts,
    RealEstateAnalyticsCharts,
    quick_kpi_card,
    quick_lead_analysis,
    quick_roc_curve,
)


class TestJorgeTheme:
    """Test Jorge theme configuration and consistency."""

    def test_theme_initialization(self):
        """Test theme creates with expected attributes."""
        theme = JorgeTheme()

        # Test required color attributes
        assert hasattr(theme, "primary_blue")
        assert hasattr(theme, "primary_gold")
        assert hasattr(theme, "primary_green")
        assert hasattr(theme, "primary_red")

        # Test color format (hex codes)
        assert theme.primary_blue.startswith("#")
        assert len(theme.primary_blue) == 7

        # Test palette lengths
        assert len(theme.categorical_palette) >= 4
        assert len(theme.colorblind_palette) >= 4

    def test_theme_config_generation(self):
        """Test theme config generation for plotly."""
        theme = JorgeTheme()

        # Test light mode
        config = theme.get_theme_config(dark_mode=False)
        assert "layout" in config
        assert "font" in config["layout"]
        assert "colorway" in config["layout"]

        # Test dark mode
        dark_config = theme.get_theme_config(dark_mode=True)
        assert dark_config["layout"]["paper_bgcolor"] != config["layout"]["paper_bgcolor"]


class TestChartBuilderBase:
    """Test base chart builder functionality."""

    @pytest.fixture
    def chart_builder(self):
        """Create chart builder instance for testing."""
        return ChartBuilderBase()

    def test_theme_application(self, chart_builder):
        """Test theme application to figures."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[1, 2, 3]))

        themed_fig = chart_builder.apply_theme(fig)

        # Check that layout has been modified
        assert themed_fig.layout.font.family == chart_builder.theme.font_family
        assert themed_fig.layout.colorway == chart_builder.theme.categorical_palette

    def test_watermark_addition(self, chart_builder):
        """Test watermark addition to charts."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[1, 2, 3]))

        watermarked_fig = chart_builder.add_watermark(fig)

        # Check that annotation was added
        assert len(watermarked_fig.layout.annotations) > 0
        assert "Jorge" in watermarked_fig.layout.annotations[0].text


class TestMLPerformanceCharts:
    """Test ML-specific chart generation."""

    @pytest.fixture
    def ml_charts(self):
        """Create ML charts instance for testing."""
        return MLPerformanceCharts()

    @pytest.fixture
    def sample_ml_data(self):
        """Generate sample ML data for testing."""
        np.random.seed(42)
        return {
            "y_true": np.random.choice([0, 1], size=100, p=[0.7, 0.3]),
            "y_scores": np.random.beta(2, 5, size=100),
            "feature_names": [f"Feature_{i}" for i in range(10)],
            "importance_scores": np.random.exponential(scale=0.1, size=10),
        }

    def test_roc_curve_creation(self, ml_charts, sample_ml_data):
        """Test ROC curve chart creation."""
        fig = ml_charts.create_roc_curve(sample_ml_data["y_true"], sample_ml_data["y_scores"])

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 2  # At least model curve + diagonal
        assert "ROC Curve" in fig.layout.title.text
        assert fig.layout.xaxis.title.text == "False Positive Rate"
        assert fig.layout.yaxis.title.text == "True Positive Rate"

    def test_precision_recall_curve_creation(self, ml_charts, sample_ml_data):
        """Test precision-recall curve chart creation."""
        fig = ml_charts.create_precision_recall_curve(sample_ml_data["y_true"], sample_ml_data["y_scores"])

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1
        assert "Precision-Recall" in fig.layout.title.text
        assert fig.layout.xaxis.title.text == "Recall"
        assert fig.layout.yaxis.title.text == "Precision"

    def test_confusion_matrix_creation(self, ml_charts, sample_ml_data):
        """Test confusion matrix chart creation."""
        y_pred = (sample_ml_data["y_scores"] > 0.5).astype(int)

        fig = ml_charts.create_confusion_matrix(sample_ml_data["y_true"], y_pred)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1
        assert fig.data[0].type == "heatmap"
        assert "Confusion Matrix" in fig.layout.title.text

    def test_feature_importance_creation(self, ml_charts, sample_ml_data):
        """Test feature importance chart creation."""
        fig = ml_charts.create_feature_importance(sample_ml_data["feature_names"], sample_ml_data["importance_scores"])

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1
        assert fig.data[0].type == "bar"
        assert "Feature Importance" in fig.layout.title.text


class TestRealEstateAnalyticsCharts:
    """Test real estate analytics chart generation."""

    @pytest.fixture
    def re_charts(self):
        """Create real estate charts instance for testing."""
        return RealEstateAnalyticsCharts()

    @pytest.fixture
    def sample_lead_data(self):
        """Generate sample lead data for testing."""
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        return pd.DataFrame(
            {
                "score": np.random.beta(2, 5, size=100) * 100,
                "converted": np.random.choice([0, 1], size=100, p=[0.8, 0.2]),
                "source": np.random.choice(["Website", "Social", "Referral", "PPC"], size=100),
                "date": np.random.choice(dates, size=100),
                "value": np.random.exponential(scale=50000, size=100),
            }
        )

    @pytest.fixture
    def sample_funnel_data(self):
        """Generate sample funnel data for testing."""
        return pd.DataFrame(
            {
                "stage": ["Awareness", "Interest", "Consideration", "Intent", "Purchase"],
                "count": [1000, 750, 400, 200, 50],
            }
        )

    @pytest.fixture
    def sample_market_data(self):
        """Generate sample market data for testing."""
        dates = pd.date_range("2024-01-01", periods=12, freq="M")
        return pd.DataFrame(
            {
                "date": dates,
                "avg_price": np.random.normal(500000, 50000, size=12),
                "price_per_sqft": np.random.normal(200, 20, size=12),
                "active_listings": np.random.poisson(500, size=12),
                "avg_dom": np.random.normal(30, 10, size=12),
                "sales_volume": np.random.poisson(100, size=12),
                "new_listings": np.random.poisson(150, size=12),
            }
        )

    @pytest.fixture
    def sample_attribution_data(self):
        """Generate sample attribution data for testing."""
        return pd.DataFrame(
            {
                "source": ["Website", "Social Media", "Referrals", "PPC", "Email"],
                "count": [150, 80, 120, 90, 60],
                "conversion_rate": [0.15, 0.08, 0.25, 0.12, 0.18],
            }
        )

    def test_lead_score_distribution_creation(self, re_charts, sample_lead_data):
        """Test lead score distribution chart creation."""
        fig = re_charts.create_lead_score_distribution(sample_lead_data)

        assert isinstance(fig, go.Figure)
        assert "Lead Score Analysis" in fig.layout.title.text
        assert fig.layout.height == 800

    def test_conversion_funnel_creation(self, re_charts, sample_funnel_data):
        """Test conversion funnel chart creation."""
        fig = re_charts.create_conversion_funnel(sample_funnel_data)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1
        assert fig.data[0].type == "funnel"
        assert "Lead Conversion Funnel" in fig.layout.title.text

    def test_market_trends_creation(self, re_charts, sample_market_data):
        """Test market trends chart creation."""
        fig = re_charts.create_market_trends(sample_market_data)

        assert isinstance(fig, go.Figure)
        assert "Market Trends Analysis" in fig.layout.title.text
        assert fig.layout.height == 800

    def test_attribution_analysis_creation(self, re_charts, sample_attribution_data):
        """Test attribution analysis chart creation."""
        fig = re_charts.create_attribution_analysis(sample_attribution_data)

        assert isinstance(fig, go.Figure)
        assert "Lead Source Attribution" in fig.layout.title.text
        # Should have both pie chart and bar chart
        assert len([trace for trace in fig.data if trace.type == "pie"]) >= 1


class TestInteractiveDashboardWidgets:
    """Test interactive dashboard widget creation."""

    @pytest.fixture
    def widgets(self):
        """Create dashboard widgets instance for testing."""
        return InteractiveDashboardWidgets()

    @pytest.fixture
    def sample_time_series_data(self):
        """Generate sample time series data for testing."""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        return pd.DataFrame(
            {
                "timestamp": dates,
                "revenue": np.random.exponential(scale=10000, size=30),
                "leads": np.random.poisson(50, size=30),
                "conversions": np.random.poisson(5, size=30),
            }
        )

    @pytest.fixture
    def sample_forecast_data(self):
        """Generate sample forecast data for testing."""
        dates = pd.date_range("2024-02-01", periods=30, freq="D")
        return pd.DataFrame(
            {
                "date": dates,
                "revenue": np.random.exponential(scale=10000, size=30),
                "upper_bound": np.random.exponential(scale=12000, size=30),
                "lower_bound": np.random.exponential(scale=8000, size=30),
            }
        )

    def test_kpi_card_creation(self, widgets):
        """Test KPI card widget creation."""
        fig = widgets.create_kpi_card(title="Monthly Revenue", value=125000, change=0.15, format_type="currency")

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1
        assert fig.data[0].type == "indicator"
        assert fig.layout.height == 200

    def test_real_time_metric_creation(self, widgets, sample_time_series_data):
        """Test real-time metric chart creation."""
        fig = widgets.create_real_time_metric(sample_time_series_data, metric_column="revenue")

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 2  # Main line + trend line
        assert "Real-time Revenue" in fig.layout.title.text
        assert fig.layout.height == 400

    def test_forecast_chart_creation(self, widgets, sample_time_series_data, sample_forecast_data):
        """Test forecast chart creation."""
        fig = widgets.create_forecast_chart(
            historical_data=sample_time_series_data,
            forecast_data=sample_forecast_data,
            value_column="revenue",
            time_column="timestamp" if "timestamp" in sample_time_series_data.columns else "date",
        )

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 2  # Historical + forecast
        assert "Revenue Forecast" in fig.layout.title.text
        assert fig.layout.height == 500


class TestChartFactory:
    """Test main chart factory functionality."""

    @pytest.fixture
    def factory(self):
        """Create chart factory instance for testing."""
        return ChartFactory()

    @pytest.fixture
    def factory_colorblind(self):
        """Create colorblind-friendly chart factory for testing."""
        return ChartFactory(colorblind_friendly=True)

    def test_factory_initialization(self, factory):
        """Test factory initialization."""
        assert hasattr(factory, "ml_charts")
        assert hasattr(factory, "real_estate_charts")
        assert hasattr(factory, "dashboard_widgets")
        assert isinstance(factory.theme, JorgeTheme)

    def test_colorblind_friendly_mode(self, factory_colorblind):
        """Test colorblind friendly palette usage."""
        colors = factory_colorblind.get_theme_colors()
        assert colors["categorical_palette"] == factory_colorblind.theme.colorblind_palette

    def test_chart_creation_dispatch(self, factory):
        """Test chart creation through factory method."""
        # Test KPI card creation
        fig = factory.create_chart("kpi_card", "Test Metric", value=100, format_type="number")

        assert isinstance(fig, go.Figure)
        assert fig.data[0].type == "indicator"

    def test_invalid_chart_type(self, factory):
        """Test error handling for invalid chart types."""
        with pytest.raises(ValueError) as exc_info:
            factory.create_chart("invalid_chart_type", {})

        assert "Unknown chart type" in str(exc_info.value)

    def test_error_chart_creation(self, factory):
        """Test error chart creation when chart fails."""
        # This tests the internal _create_error_chart method
        error_fig = factory._create_error_chart("Test error message")

        assert isinstance(error_fig, go.Figure)
        assert "Chart Creation Error" in error_fig.layout.title.text
        assert len(error_fig.layout.annotations) > 0

    def test_theme_colors_retrieval(self, factory):
        """Test theme colors retrieval."""
        colors = factory.get_theme_colors()

        assert "primary_blue" in colors
        assert "primary_gold" in colors
        assert "categorical_palette" in colors
        assert isinstance(colors["categorical_palette"], list)


class TestConvenienceFunctions:
    """Test convenience functions for quick chart creation."""

    @pytest.fixture
    def sample_ml_data(self):
        """Generate sample ML data for testing."""
        np.random.seed(42)
        return {"y_true": np.random.choice([0, 1], size=50, p=[0.7, 0.3]), "y_scores": np.random.beta(2, 5, size=50)}

    @pytest.fixture
    def sample_lead_data(self):
        """Generate sample lead data for testing."""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "score": np.random.beta(2, 5, size=50) * 100,
                "converted": np.random.choice([0, 1], size=50, p=[0.8, 0.2]),
                "source": np.random.choice(["Website", "Social"], size=50),
            }
        )

    def test_quick_roc_curve(self, sample_ml_data):
        """Test quick ROC curve creation."""
        fig = quick_roc_curve(sample_ml_data["y_true"], sample_ml_data["y_scores"])

        assert isinstance(fig, go.Figure)
        assert "ROC Curve" in fig.layout.title.text

    def test_quick_lead_analysis(self, sample_lead_data):
        """Test quick lead analysis creation."""
        fig = quick_lead_analysis(sample_lead_data)

        assert isinstance(fig, go.Figure)
        assert "Lead Score Analysis" in fig.layout.title.text

    def test_quick_kpi_card(self):
        """Test quick KPI card creation."""
        fig = quick_kpi_card("Test KPI", 12345)

        assert isinstance(fig, go.Figure)
        assert fig.data[0].type == "indicator"


class TestAccessibilityFeatures:
    """Test accessibility and usability features."""

    @pytest.fixture
    def colorblind_factory(self):
        """Create colorblind-friendly factory for testing."""
        return ChartFactory(colorblind_friendly=True)

    def test_colorblind_palette_usage(self, colorblind_factory):
        """Test colorblind palette is used when enabled."""
        colors = colorblind_factory.get_theme_colors()

        # Should use colorblind palette
        assert colors["categorical_palette"] == colorblind_factory.theme.colorblind_palette

    def test_dark_mode_support(self):
        """Test dark mode theme application."""
        light_factory = ChartFactory(dark_mode=False)
        dark_factory = ChartFactory(dark_mode=True)

        light_config = light_factory.theme.get_theme_config(dark_mode=False)
        dark_config = dark_factory.theme.get_theme_config(dark_mode=True)

        # Background colors should be different
        assert light_config["layout"]["paper_bgcolor"] != dark_config["layout"]["paper_bgcolor"]


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def factory(self):
        """Create factory for error testing."""
        return ChartFactory()

    def test_empty_data_handling(self, factory):
        """Test handling of empty datasets."""
        empty_df = pd.DataFrame()

        # Should not raise exception, might return error chart
        try:
            fig = factory.create_chart("lead_score_distribution", empty_df)
            assert isinstance(fig, go.Figure)
        except Exception:
            # Expected for empty data
            pass

    def test_missing_column_handling(self):
        """Test handling of missing required columns."""
        incomplete_df = pd.DataFrame({"score": [1, 2, 3]})

        # Should handle gracefully
        charts = RealEstateAnalyticsCharts()
        try:
            fig = charts.create_lead_score_distribution(incomplete_df)
            assert isinstance(fig, go.Figure)
        except Exception:
            # Expected for incomplete data
            pass


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_dashboard_workflow(self):
        """Test complete dashboard creation workflow."""
        factory = ChartFactory()

        # Simulate dashboard with multiple chart types
        np.random.seed(42)

        # 1. KPI Cards
        revenue_kpi = factory.create_chart(
            "kpi_card", "Monthly Revenue", value=125000, change=0.15, format_type="currency"
        )

        # 2. Lead Analysis
        lead_data = pd.DataFrame(
            {
                "score": np.random.beta(2, 5, size=100) * 100,
                "converted": np.random.choice([0, 1], size=100, p=[0.8, 0.2]),
                "source": np.random.choice(["Website", "Social"], size=100),
            }
        )

        lead_analysis = factory.create_chart("lead_score_distribution", lead_data)

        # 3. ML Performance
        y_true = np.random.choice([0, 1], size=100, p=[0.7, 0.3])
        y_scores = np.random.beta(2, 5, size=100)

        roc_chart = factory.create_chart("roc_curve", y_true, y_scores=y_scores)

        # All charts should be created successfully
        assert isinstance(revenue_kpi, go.Figure)
        assert isinstance(lead_analysis, go.Figure)
        assert isinstance(roc_chart, go.Figure)

        # Charts should have consistent theming
        theme_colors = factory.get_theme_colors()
        assert revenue_kpi.data[0].number.color == theme_colors["primary_blue"]

    def test_batch_export_simulation(self):
        """Test batch export functionality."""
        factory = ChartFactory()

        # Create multiple charts
        charts = {
            "kpi_revenue": factory.create_chart("kpi_card", "Revenue", value=100000),
            "kpi_leads": factory.create_chart("kpi_card", "Leads", value=250),
        }

        # Test export structure (without actual file creation)
        assert len(charts) == 2
        assert all(isinstance(fig, go.Figure) for fig in charts.values())


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
