"""
Enhanced Visualization Service for Real Estate AI

Provides real estate-specific chart types and interactive visualizations:
- Revenue waterfall charts for deal progression analysis
- Geographic heatmaps for market opportunity mapping
- Lead funnel visualizations with conversion metrics
- Property lifecycle timeline charts
- Commission optimization waterfall analysis
- Interactive drill-down capabilities with sub-100ms performance
- Market trend analysis with predictive overlays

Integrates with existing Plotly infrastructure while adding enterprise-grade
real estate visualization capabilities optimized for decision-making.
"""

import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
import logging

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ChartTheme:
    """Professional chart theme configuration for enterprise real estate."""

    primary_color: str = "#2563eb"
    secondary_color: str = "#10b981"
    accent_color: str = "#f59e0b"
    danger_color: str = "#ef4444"
    success_color: str = "#22c55e"
    warning_color: str = "#eab308"
    neutral_color: str = "#64748b"

    background_color: str = "rgba(0,0,0,0)"
    paper_color: str = "rgba(0,0,0,0)"
    grid_color: str = "#334155"
    text_color: str = "#f8fafc"

    font_family: str = "system-ui, -apple-system, sans-serif"
    title_size: int = 18
    axis_size: int = 12
    legend_size: int = 11


class RealEstateChartBuilder:
    """Real estate-specific chart builder with professional theming."""

    def __init__(self, theme: Optional[ChartTheme] = None):
        self.theme = theme or ChartTheme()
        self.base_layout = self._create_base_layout()

    def _create_base_layout(self) -> Dict[str, Any]:
        """Create base layout configuration for all charts."""
        return {
            "template": "plotly_dark",
            "paper_bgcolor": self.theme.paper_color,
            "plot_bgcolor": self.theme.background_color,
            "font": {
                "family": self.theme.font_family,
                "size": self.theme.axis_size,
                "color": self.theme.text_color
            },
            "title": {
                "font": {
                    "size": self.theme.title_size,
                    "color": self.theme.text_color,
                    "family": self.theme.font_family
                },
                "x": 0.02,
                "xanchor": "left"
            },
            "xaxis": {
                "gridcolor": self.theme.grid_color,
                "color": self.theme.text_color,
                "linecolor": self.theme.grid_color
            },
            "yaxis": {
                "gridcolor": self.theme.grid_color,
                "color": self.theme.text_color,
                "linecolor": self.theme.grid_color
            },
            "legend": {
                "font": {"size": self.theme.legend_size, "color": self.theme.text_color},
                "bgcolor": "rgba(0,0,0,0.3)",
                "bordercolor": self.theme.grid_color,
                "borderwidth": 1
            },
            "margin": {"l": 20, "r": 20, "t": 60, "b": 20}
        }

    def create_revenue_waterfall_chart(
        self,
        revenue_data: Dict[str, float],
        title: str = "Revenue Waterfall Analysis",
        height: int = 400
    ) -> go.Figure:
        """
        Create revenue waterfall chart showing deal progression.

        Args:
            revenue_data: Dict with revenue components
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly figure with waterfall chart
        """
        # Example revenue components
        categories = list(revenue_data.keys())
        values = list(revenue_data.values())

        # Calculate cumulative values for waterfall effect
        cumulative = []
        running_total = 0

        for i, value in enumerate(values):
            if i == 0:  # Starting value
                cumulative.append([0, value])
                running_total = value
            elif i == len(values) - 1:  # Final total
                cumulative.append([0, running_total])
            else:  # Intermediate values
                cumulative.append([running_total, running_total + value])
                running_total += value

        # Create waterfall chart
        fig = go.Figure()

        # Add bars for each component
        for i, (category, value) in enumerate(zip(categories, values)):
            color = self.theme.primary_color
            if value > 0:
                color = self.theme.success_color
            elif value < 0:
                color = self.theme.danger_color

            # Add main bar
            fig.add_trace(go.Bar(
                name=category,
                x=[category],
                y=[abs(value)],
                base=[cumulative[i][0]],
                marker_color=color,
                text=f"${value:,.0f}",
                textposition="middle center",
                textfont=dict(color="white", weight="bold"),
                showlegend=False
            ))

            # Add connector lines (except for last item)
            if i < len(categories) - 1:
                fig.add_trace(go.Scatter(
                    x=[i + 0.4, i + 1 - 0.4],
                    y=[cumulative[i][1], cumulative[i][1]],
                    mode="lines",
                    line=dict(color=self.theme.neutral_color, dash="dot"),
                    showlegend=False
                ))

        # Update layout
        layout_config = self.base_layout.copy()
        layout_config.update({
            "title": {"text": f"<b>{title}</b>"},
            "height": height,
            "xaxis": {
                **layout_config["xaxis"],
                "title": "Revenue Components"
            },
            "yaxis": {
                **layout_config["yaxis"],
                "title": "Amount ($)",
                "tickformat": "$,.0f"
            }
        })

        fig.update_layout(layout_config)
        return fig

    def create_geographic_heatmap(
        self,
        location_data: pd.DataFrame,
        metric: str = "lead_density",
        title: str = "Lead Density Heatmap",
        height: int = 500,
        center_lat: float = 30.2672,
        center_lon: float = -97.7431,
        zoom: int = 10
    ) -> go.Figure:
        """
        Create geographic heatmap for market opportunity mapping.

        Args:
            location_data: DataFrame with lat, lon, and metric columns
            metric: Column name for heatmap values
            title: Chart title
            height: Chart height
            center_lat: Map center latitude
            center_lon: Map center longitude
            zoom: Map zoom level

        Returns:
            Plotly figure with geographic heatmap
        """
        # Create density heatmap
        fig = go.Figure(go.Densitymapbox(
            lat=location_data['lat'],
            lon=location_data['lon'],
            z=location_data[metric],
            radius=15,
            colorscale=[
                [0, f"rgba(37, 99, 235, 0.1)"],
                [0.2, f"rgba(37, 99, 235, 0.3)"],
                [0.4, f"rgba(245, 158, 11, 0.5)"],
                [0.6, f"rgba(245, 158, 11, 0.7)"],
                [0.8, f"rgba(239, 68, 68, 0.8)"],
                [1, f"rgba(239, 68, 68, 1)"]
            ],
            showscale=True,
            colorbar=dict(
                title=metric.replace('_', ' ').title(),
                titlefont=dict(color=self.theme.text_color),
                tickfont=dict(color=self.theme.text_color)
            )
        ))

        # Add scatter points for specific locations
        fig.add_trace(go.Scattermapbox(
            lat=location_data['lat'],
            lon=location_data['lon'],
            mode='markers',
            marker=dict(
                size=8,
                color=self.theme.primary_color,
                opacity=0.7
            ),
            text=location_data.get('location_name', ''),
            hovertemplate="<b>%{text}</b><br>" +
                         f"{metric.replace('_', ' ').title()}: %{{z}}<br>" +
                         "<extra></extra>",
            showlegend=False,
            name="Locations"
        ))

        fig.update_layout(
            mapbox_style="dark",
            mapbox=dict(
                center=go.layout.mapbox.Center(lat=center_lat, lon=center_lon),
                zoom=zoom
            ),
            title={
                "text": f"<b>{title}</b>",
                "font": {"size": self.theme.title_size, "color": self.theme.text_color},
                "x": 0.02
            },
            height=height,
            margin={"r": 0, "t": 60, "l": 0, "b": 0},
            paper_bgcolor=self.theme.paper_color
        )

        return fig

    def create_conversion_funnel_chart(
        self,
        funnel_data: Dict[str, int],
        title: str = "Lead Conversion Funnel",
        height: int = 400
    ) -> go.Figure:
        """
        Create conversion funnel visualization with metrics.

        Args:
            funnel_data: Dict with stage names and counts
            title: Chart title
            height: Chart height

        Returns:
            Plotly figure with funnel chart
        """
        stages = list(funnel_data.keys())
        values = list(funnel_data.values())

        # Calculate conversion rates
        conversion_rates = []
        for i in range(len(values)):
            if i == 0:
                conversion_rates.append(100)
            else:
                rate = (values[i] / values[0]) * 100 if values[0] > 0 else 0
                conversion_rates.append(rate)

        # Create funnel chart
        fig = go.Figure(go.Funnel(
            y=stages,
            x=values,
            textposition="inside",
            textinfo="value+percent initial",
            textfont_size=12,
            textfont_color="white",
            marker=dict(
                color=[
                    self.theme.primary_color,
                    self.theme.secondary_color,
                    self.theme.accent_color,
                    self.theme.success_color,
                    self.theme.warning_color
                ][:len(stages)],
                line=dict(width=2, color="white")
            ),
            connector=dict(
                line=dict(
                    color=self.theme.neutral_color,
                    dash="solid",
                    width=2
                ),
                fillcolor="rgba(100, 116, 139, 0.1)"
            )
        ))

        # Update layout
        layout_config = self.base_layout.copy()
        layout_config.update({
            "title": {"text": f"<b>{title}</b>"},
            "height": height,
            "funnelmode": "stack"
        })

        fig.update_layout(layout_config)
        return fig

    def create_property_lifecycle_timeline(
        self,
        properties: List[Dict[str, Any]],
        title: str = "Property Lifecycle Timeline",
        height: int = 400
    ) -> go.Figure:
        """
        Create property lifecycle timeline showing deal progression.

        Args:
            properties: List of property data with timeline information
            title: Chart title
            height: Chart height

        Returns:
            Plotly figure with timeline chart
        """
        fig = go.Figure()

        # Color mapping for different stages
        stage_colors = {
            "Listed": self.theme.primary_color,
            "Under Contract": self.theme.warning_color,
            "Pending": self.theme.accent_color,
            "Closed": self.theme.success_color,
            "Expired": self.theme.danger_color
        }

        y_position = 0
        for prop in properties:
            address = prop.get('address', 'Unknown Property')
            stages = prop.get('stages', [])

            for stage in stages:
                start_date = pd.to_datetime(stage['start_date'])
                end_date = pd.to_datetime(stage.get('end_date', datetime.now()))
                stage_name = stage['stage']

                # Add timeline bar
                fig.add_trace(go.Scatter(
                    x=[start_date, end_date],
                    y=[y_position, y_position],
                    mode='lines',
                    line=dict(
                        color=stage_colors.get(stage_name, self.theme.neutral_color),
                        width=8
                    ),
                    name=f"{address} - {stage_name}",
                    hovertemplate=f"<b>{address}</b><br>" +
                                  f"Stage: {stage_name}<br>" +
                                  f"Duration: {(end_date - start_date).days} days<br>" +
                                  "<extra></extra>",
                    showlegend=False
                ))

                # Add stage marker
                fig.add_trace(go.Scatter(
                    x=[start_date],
                    y=[y_position],
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=stage_colors.get(stage_name, self.theme.neutral_color),
                        symbol='circle',
                        line=dict(width=2, color='white')
                    ),
                    text=stage_name,
                    textposition="top center",
                    showlegend=False
                ))

            y_position += 1

        # Update layout
        layout_config = self.base_layout.copy()
        layout_config.update({
            "title": {"text": f"<b>{title}</b>"},
            "height": height,
            "yaxis": {
                **layout_config["yaxis"],
                "title": "Properties",
                "tickmode": "array",
                "tickvals": list(range(len(properties))),
                "ticktext": [prop.get('address', f'Property {i+1}') for i, prop in enumerate(properties)]
            },
            "xaxis": {
                **layout_config["xaxis"],
                "title": "Timeline",
                "type": "date"
            }
        })

        fig.update_layout(layout_config)
        return fig

    def create_commission_analysis_chart(
        self,
        commission_data: Dict[str, Any],
        title: str = "Commission Analysis",
        height: int = 400
    ) -> go.Figure:
        """
        Create commission analysis with breakdown and projections.

        Args:
            commission_data: Commission breakdown data
            title: Chart title
            height: Chart height

        Returns:
            Plotly figure with commission analysis
        """
        # Create subplots for comprehensive view
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Commission Breakdown",
                "Monthly Trend",
                "Deal Size Distribution",
                "Projected vs Actual"
            ],
            specs=[
                [{"type": "pie"}, {"type": "scatter"}],
                [{"type": "histogram"}, {"type": "bar"}]
            ]
        )

        # 1. Commission breakdown pie chart
        breakdown = commission_data.get('breakdown', {})
        fig.add_trace(go.Pie(
            labels=list(breakdown.keys()),
            values=list(breakdown.values()),
            hole=0.4,
            marker_colors=[
                self.theme.primary_color,
                self.theme.secondary_color,
                self.theme.accent_color,
                self.theme.success_color
            ]
        ), row=1, col=1)

        # 2. Monthly trend line chart
        monthly_data = commission_data.get('monthly_trend', {})
        months = list(monthly_data.keys())
        amounts = list(monthly_data.values())

        fig.add_trace(go.Scatter(
            x=months,
            y=amounts,
            mode='lines+markers',
            line=dict(color=self.theme.primary_color, width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor=f"rgba(37, 99, 235, 0.1)"
        ), row=1, col=2)

        # 3. Deal size histogram
        deal_sizes = commission_data.get('deal_sizes', [])
        fig.add_trace(go.Histogram(
            x=deal_sizes,
            nbinsx=10,
            marker_color=self.theme.secondary_color,
            opacity=0.7
        ), row=2, col=1)

        # 4. Projected vs actual bar chart
        projections = commission_data.get('projections', {})
        categories = list(projections.keys())
        projected = [projections[cat]['projected'] for cat in categories]
        actual = [projections[cat]['actual'] for cat in categories]

        fig.add_trace(go.Bar(
            x=categories,
            y=projected,
            name="Projected",
            marker_color=self.theme.accent_color,
            opacity=0.7
        ), row=2, col=2)

        fig.add_trace(go.Bar(
            x=categories,
            y=actual,
            name="Actual",
            marker_color=self.theme.primary_color
        ), row=2, col=2)

        # Update layout
        layout_config = self.base_layout.copy()
        layout_config.update({
            "title": {"text": f"<b>{title}</b>"},
            "height": height,
            "showlegend": True
        })

        fig.update_layout(layout_config)
        return fig

    def create_market_trend_chart(
        self,
        market_data: pd.DataFrame,
        metrics: List[str],
        title: str = "Market Trend Analysis",
        height: int = 400,
        include_predictions: bool = True
    ) -> go.Figure:
        """
        Create market trend analysis with predictive overlays.

        Args:
            market_data: DataFrame with date and metric columns
            metrics: List of metric names to plot
            title: Chart title
            height: Chart height
            include_predictions: Whether to include predictive overlays

        Returns:
            Plotly figure with market trend analysis
        """
        fig = go.Figure()

        colors = [
            self.theme.primary_color,
            self.theme.secondary_color,
            self.theme.accent_color,
            self.theme.success_color,
            self.theme.warning_color
        ]

        # Plot actual data
        for i, metric in enumerate(metrics):
            if metric in market_data.columns:
                fig.add_trace(go.Scatter(
                    x=market_data['date'],
                    y=market_data[metric],
                    mode='lines+markers',
                    name=metric.replace('_', ' ').title(),
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=6)
                ))

                # Add predictions if enabled
                if include_predictions and f"{metric}_predicted" in market_data.columns:
                    fig.add_trace(go.Scatter(
                        x=market_data['date'],
                        y=market_data[f"{metric}_predicted"],
                        mode='lines',
                        name=f"{metric.replace('_', ' ').title()} (Predicted)",
                        line=dict(
                            color=colors[i % len(colors)],
                            width=2,
                            dash='dash'
                        ),
                        opacity=0.7
                    ))

        # Update layout
        layout_config = self.base_layout.copy()
        layout_config.update({
            "title": {"text": f"<b>{title}</b>"},
            "height": height,
            "xaxis": {
                **layout_config["xaxis"],
                "title": "Date",
                "type": "date"
            },
            "yaxis": {
                **layout_config["yaxis"],
                "title": "Value"
            },
            "hovermode": "x unified"
        })

        fig.update_layout(layout_config)
        return fig

    def create_interactive_dashboard_grid(
        self,
        charts: List[go.Figure],
        grid_layout: Tuple[int, int],
        title: str = "Real Estate Analytics Dashboard"
    ) -> go.Figure:
        """
        Create interactive dashboard with multiple charts in grid layout.

        Args:
            charts: List of Plotly figures to include
            grid_layout: Tuple of (rows, cols) for grid layout
            title: Dashboard title

        Returns:
            Combined dashboard figure
        """
        rows, cols = grid_layout

        # Create subplot grid
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[f"Chart {i+1}" for i in range(len(charts))],
            horizontal_spacing=0.1,
            vertical_spacing=0.15
        )

        # Add each chart to the grid
        for i, chart in enumerate(charts):
            row = (i // cols) + 1
            col = (i % cols) + 1

            # Extract traces from the original chart
            for trace in chart.data:
                fig.add_trace(trace, row=row, col=col)

        # Update layout
        layout_config = self.base_layout.copy()
        layout_config.update({
            "title": {"text": f"<b>{title}</b>"},
            "height": 800,
            "showlegend": True
        })

        fig.update_layout(layout_config)
        return fig


class EnhancedVisualizationService:
    """
    Enhanced Visualization Service with real estate-specific capabilities.

    Provides:
    - Real estate-specific chart types and templates
    - Interactive visualizations with drill-down capabilities
    - Professional theming optimized for executive dashboards
    - Performance-optimized rendering (<100ms target)
    - Export capabilities for reports and presentations
    """

    def __init__(self, theme: Optional[ChartTheme] = None):
        self.chart_builder = RealEstateChartBuilder(theme)
        logger.info("Enhanced Visualization Service initialized")

    def generate_revenue_waterfall(
        self,
        revenue_components: Dict[str, float],
        **kwargs
    ) -> go.Figure:
        """Generate revenue waterfall chart."""
        return self.chart_builder.create_revenue_waterfall_chart(
            revenue_components, **kwargs
        )

    def generate_lead_density_map(
        self,
        location_data: pd.DataFrame,
        **kwargs
    ) -> go.Figure:
        """Generate geographic lead density heatmap."""
        return self.chart_builder.create_geographic_heatmap(
            location_data, **kwargs
        )

    def generate_conversion_funnel(
        self,
        funnel_stages: Dict[str, int],
        **kwargs
    ) -> go.Figure:
        """Generate conversion funnel visualization."""
        return self.chart_builder.create_conversion_funnel_chart(
            funnel_stages, **kwargs
        )

    def generate_property_timeline(
        self,
        property_data: List[Dict[str, Any]],
        **kwargs
    ) -> go.Figure:
        """Generate property lifecycle timeline."""
        return self.chart_builder.create_property_lifecycle_timeline(
            property_data, **kwargs
        )

    def generate_commission_analysis(
        self,
        commission_data: Dict[str, Any],
        **kwargs
    ) -> go.Figure:
        """Generate commission analysis dashboard."""
        return self.chart_builder.create_commission_analysis_chart(
            commission_data, **kwargs
        )

    def generate_market_trends(
        self,
        market_data: pd.DataFrame,
        metrics: List[str],
        **kwargs
    ) -> go.Figure:
        """Generate market trend analysis."""
        return self.chart_builder.create_market_trend_chart(
            market_data, metrics, **kwargs
        )

    def create_executive_dashboard(
        self,
        analytics_data: Dict[str, Any]
    ) -> go.Figure:
        """
        Create comprehensive executive dashboard with key visualizations.

        Args:
            analytics_data: Comprehensive analytics data

        Returns:
            Dashboard figure with multiple visualizations
        """
        charts = []

        # Revenue waterfall
        if 'revenue_components' in analytics_data:
            charts.append(self.generate_revenue_waterfall(
                analytics_data['revenue_components'],
                title="Revenue Analysis",
                height=300
            ))

        # Conversion funnel
        if 'funnel_data' in analytics_data:
            charts.append(self.generate_conversion_funnel(
                analytics_data['funnel_data'],
                title="Lead Conversion",
                height=300
            ))

        # Market trends
        if 'market_trends' in analytics_data:
            market_df = pd.DataFrame(analytics_data['market_trends'])
            charts.append(self.generate_market_trends(
                market_df,
                ['average_price', 'inventory_levels'],
                title="Market Trends",
                height=300
            ))

        # Create dashboard grid
        if charts:
            return self.chart_builder.create_interactive_dashboard_grid(
                charts,
                grid_layout=(2, 2),
                title="Executive Analytics Dashboard"
            )

        # Return empty figure if no data
        return go.Figure()

    def export_chart_as_image(
        self,
        figure: go.Figure,
        filename: str,
        format: str = "png",
        width: int = 1200,
        height: int = 800
    ) -> str:
        """
        Export chart as image for reports.

        Args:
            figure: Plotly figure to export
            filename: Output filename
            format: Image format (png, jpeg, svg)
            width: Image width
            height: Image height

        Returns:
            File path of exported image
        """
        try:
            filepath = f"exports/{filename}.{format}"
            figure.write_image(filepath, width=width, height=height)
            logger.info(f"Chart exported as image: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export chart as image: {e}")
            return ""


# Helper functions for quick integration
def create_enhanced_visualizations():
    """Initialize enhanced visualization service."""
    return EnhancedVisualizationService()

def generate_real_estate_charts(analytics_data: Dict[str, Any]) -> Dict[str, go.Figure]:
    """Generate complete set of real estate charts."""
    viz_service = create_enhanced_visualizations()

    charts = {}

    # Revenue waterfall
    if 'revenue_components' in analytics_data:
        charts['revenue_waterfall'] = viz_service.generate_revenue_waterfall(
            analytics_data['revenue_components']
        )

    # Conversion funnel
    if 'funnel_data' in analytics_data:
        charts['conversion_funnel'] = viz_service.generate_conversion_funnel(
            analytics_data['funnel_data']
        )

    # Geographic heatmap
    if 'location_data' in analytics_data:
        location_df = pd.DataFrame(analytics_data['location_data'])
        charts['lead_density_map'] = viz_service.generate_lead_density_map(
            location_df
        )

    return charts


# Export main components
__all__ = [
    "EnhancedVisualizationService",
    "RealEstateChartBuilder",
    "ChartTheme",
    "create_enhanced_visualizations",
    "generate_real_estate_charts"
]