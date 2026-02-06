"""
Jorge's Chart Builders Utility v2.0

Advanced chart factory with ML-specific visualizations, real estate analytics,
and interactive dashboard widgets. Features standardized Jorge theme integration,
performance optimization, and comprehensive accessibility support.

Key Features:
- Plotly Chart Factory with Jorge branding
- ML Performance Charts (ROC, precision-recall, confusion matrices)
- Real Estate Analytics (market trends, lead analysis, conversion funnels)
- Interactive Dashboard Widgets with callbacks
- Responsive design for desktop/mobile
- Color-blind friendly palettes
- Export functionality for reports

Integration:
- Follows theme_manager.py patterns
- Supports light/dark themes
- Integrates with ML Analytics Engine
- Optimized for real-time updates
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import colorcet as cc
from sklearn.metrics import roc_curve, precision_recall_curve, confusion_matrix
import logging

logger = logging.getLogger(__name__)


@dataclass
class JorgeTheme:
    """Jorge's standardized theme configuration for all charts."""
    
    # Primary Brand Colors
    primary_blue = "#1E3A8A"        # Deep professional blue
    primary_gold = "#F59E0B"        # Luxury gold accent
    primary_green = "#059669"       # Success/profit green
    primary_red = "#DC2626"         # Alert/loss red
    
    # Secondary Colors
    secondary_navy = "#0F172A"      # Dark background
    secondary_slate = "#475569"     # Text/borders
    secondary_gray = "#94A3B8"      # Subtle elements
    secondary_white = "#F8FAFC"     # Light background
    
    # Semantic Colors
    success = "#10B981"             # Positive metrics
    warning = "#F59E0B"             # Attention needed
    danger = "#EF4444"              # Critical issues
    info = "#3B82F6"                # Information
    
    # Chart-Specific Palettes
    categorical_palette = [
        "#1E3A8A", "#F59E0B", "#059669", "#DC2626",
        "#7C3AED", "#EC4899", "#06B6D4", "#84CC16"
    ]
    
    sequential_palette = [
        "#F8FAFC", "#E2E8F0", "#CBD5E1", "#94A3B8",
        "#64748B", "#475569", "#334155", "#1E293B"
    ]
    
    diverging_palette = [
        "#DC2626", "#F87171", "#FCA5A5", "#FECACA",
        "#F8FAFC", "#DBEAFE", "#93C5FD", "#60A5FA", "#3B82F6"
    ]
    
    # Color-blind friendly alternatives
    colorblind_palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"
    ]
    
    # Typography
    font_family = "Inter, system-ui, -apple-system, sans-serif"
    title_font_size = 18
    subtitle_font_size = 14
    axis_font_size = 12
    legend_font_size = 11
    
    # Layout
    margin = dict(l=80, r=80, t=100, b=80)
    paper_bgcolor = "white"
    plot_bgcolor = "rgba(0,0,0,0)"
    grid_color = "#E2E8F0"
    
    @classmethod
    def get_theme_config(cls, dark_mode: bool = False) -> Dict[str, Any]:
        """Get complete theme configuration for plotly."""
        theme = {
            "layout": {
                "font": {
                    "family": cls.font_family,
                    "size": cls.axis_font_size,
                    "color": cls.secondary_slate if not dark_mode else cls.secondary_gray
                },
                "title": {
                    "font": {
                        "size": cls.title_font_size,
                        "color": cls.secondary_navy if not dark_mode else cls.secondary_white
                    },
                    "x": 0.5,
                    "xanchor": "center"
                },
                "paper_bgcolor": cls.secondary_white if not dark_mode else cls.secondary_navy,
                "plot_bgcolor": "rgba(0,0,0,0)",
                "margin": cls.margin,
                "xaxis": {
                    "gridcolor": cls.grid_color if not dark_mode else cls.secondary_slate,
                    "linecolor": cls.grid_color if not dark_mode else cls.secondary_slate,
                    "zerolinecolor": cls.grid_color if not dark_mode else cls.secondary_slate
                },
                "yaxis": {
                    "gridcolor": cls.grid_color if not dark_mode else cls.secondary_slate,
                    "linecolor": cls.grid_color if not dark_mode else cls.secondary_slate,
                    "zerolinecolor": cls.grid_color if not dark_mode else cls.secondary_slate
                },
                "colorway": cls.categorical_palette,
                "legend": {
                    "font": {"size": cls.legend_font_size},
                    "bgcolor": "rgba(255,255,255,0.8)" if not dark_mode else "rgba(0,0,0,0.8)"
                }
            }
        }
        return theme


class ChartBuilderBase:
    """Base class for all chart builders with common functionality."""
    
    def __init__(self, theme: JorgeTheme = None, dark_mode: bool = False):
        self.theme = theme or JorgeTheme()
        self.dark_mode = dark_mode
        self.theme_config = self.theme.get_theme_config(dark_mode)
    
    def apply_theme(self, fig: go.Figure) -> go.Figure:
        """Apply Jorge theme to any plotly figure."""
        fig.update_layout(**self.theme_config["layout"])
        return fig
    
    def add_watermark(self, fig: go.Figure, text: str = "Jorge Real Estate AI") -> go.Figure:
        """Add Jorge branding watermark to chart."""
        fig.add_annotation(
            text=text,
            xref="paper", yref="paper",
            x=1.0, y=0.02,
            xanchor="right", yanchor="bottom",
            showarrow=False,
            font=dict(size=10, color=self.theme.secondary_gray),
            opacity=0.6
        )
        return fig
    
    def export_chart(self, fig: go.Figure, filename: str, format: str = "png") -> str:
        """Export chart for reports and presentations."""
        try:
            if format.lower() == "html":
                fig.write_html(f"{filename}.html")
            elif format.lower() == "png":
                fig.write_image(f"{filename}.png", width=1200, height=800, scale=2)
            elif format.lower() == "pdf":
                fig.write_image(f"{filename}.pdf", width=1200, height=800)
            elif format.lower() == "svg":
                fig.write_image(f"{filename}.svg", width=1200, height=800)
            
            logger.info(f"Chart exported successfully: {filename}.{format}")
            return f"{filename}.{format}"
        except Exception as e:
            logger.error(f"Error exporting chart: {e}")
            raise


class MLPerformanceCharts(ChartBuilderBase):
    """Specialized charts for ML model performance analysis."""
    
    def create_roc_curve(self, y_true: np.ndarray, y_scores: np.ndarray, 
                        model_names: List[str] = None) -> go.Figure:
        """Create ROC curve chart with AUC scores."""
        fig = go.Figure()
        
        if model_names is None:
            model_names = ["Model"]
        
        # Handle multiple models
        if len(y_scores.shape) == 1:
            y_scores = y_scores.reshape(-1, 1)
            
        for i, model_name in enumerate(model_names):
            if i < y_scores.shape[1]:
                fpr, tpr, _ = roc_curve(y_true, y_scores[:, i])
                auc_score = np.trapz(tpr, fpr)
                
                fig.add_trace(go.Scatter(
                    x=fpr, y=tpr,
                    mode='lines',
                    name=f'{model_name} (AUC = {auc_score:.3f})',
                    line=dict(color=self.theme.categorical_palette[i % len(self.theme.categorical_palette)], width=3)
                ))
        
        # Add diagonal line
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1],
            mode='lines',
            name='Random Classifier',
            line=dict(dash='dash', color=self.theme.secondary_gray, width=2)
        ))
        
        fig.update_layout(
            title="ROC Curve Analysis",
            xaxis_title="False Positive Rate",
            yaxis_title="True Positive Rate",
            showlegend=True
        )
        
        return self.apply_theme(self.add_watermark(fig))
    
    def create_precision_recall_curve(self, y_true: np.ndarray, y_scores: np.ndarray,
                                    model_names: List[str] = None) -> go.Figure:
        """Create precision-recall curve chart."""
        fig = go.Figure()
        
        if model_names is None:
            model_names = ["Model"]
        
        if len(y_scores.shape) == 1:
            y_scores = y_scores.reshape(-1, 1)
        
        for i, model_name in enumerate(model_names):
            if i < y_scores.shape[1]:
                precision, recall, _ = precision_recall_curve(y_true, y_scores[:, i])
                avg_precision = np.mean(precision)
                
                fig.add_trace(go.Scatter(
                    x=recall, y=precision,
                    mode='lines',
                    name=f'{model_name} (AP = {avg_precision:.3f})',
                    line=dict(color=self.theme.categorical_palette[i % len(self.theme.categorical_palette)], width=3),
                    fill='tonexty' if i == 0 else None,
                    fillcolor=f"rgba{tuple(list(int(self.theme.categorical_palette[i % len(self.theme.categorical_palette)][1:][i:i+2], 16) for i in (0, 2, 4)) + [0.1])}"
                ))
        
        fig.update_layout(
            title="Precision-Recall Curve Analysis",
            xaxis_title="Recall",
            yaxis_title="Precision",
            showlegend=True
        )
        
        return self.apply_theme(self.add_watermark(fig))
    
    def create_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray,
                               labels: List[str] = None) -> go.Figure:
        """Create interactive confusion matrix heatmap."""
        cm = confusion_matrix(y_true, y_pred)
        
        if labels is None:
            labels = [f"Class {i}" for i in range(len(cm))]
        
        # Calculate percentages
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        
        # Create hover text
        hover_text = []
        for i in range(len(cm)):
            hover_row = []
            for j in range(len(cm[0])):
                hover_row.append(
                    f"True: {labels[i]}<br>"
                    f"Predicted: {labels[j]}<br>"
                    f"Count: {cm[i][j]}<br>"
                    f"Percentage: {cm_normalized[i][j]:.1%}"
                )
            hover_text.append(hover_row)
        
        fig = go.Figure(data=go.Heatmap(
            z=cm,
            x=labels,
            y=labels,
            text=cm,
            texttemplate="%{text}",
            textfont={"size": 12},
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_text,
            colorscale="Blues",
            showscale=True
        ))
        
        fig.update_layout(
            title="Confusion Matrix",
            xaxis_title="Predicted Label",
            yaxis_title="True Label",
            xaxis=dict(side="bottom"),
            yaxis=dict(autorange="reversed")
        )
        
        return self.apply_theme(self.add_watermark(fig))
    
    def create_feature_importance(self, feature_names: List[str], importance_scores: np.ndarray,
                                 model_name: str = "Model") -> go.Figure:
        """Create feature importance chart."""
        # Sort by importance
        sorted_indices = np.argsort(importance_scores)[::-1]
        sorted_features = [feature_names[i] for i in sorted_indices]
        sorted_scores = importance_scores[sorted_indices]
        
        # Take top 20 features for readability
        if len(sorted_features) > 20:
            sorted_features = sorted_features[:20]
            sorted_scores = sorted_scores[:20]
        
        fig = go.Figure(data=go.Bar(
            y=sorted_features,
            x=sorted_scores,
            orientation='h',
            marker_color=self.theme.primary_blue,
            text=[f"{score:.3f}" for score in sorted_scores],
            textposition='outside'
        ))
        
        fig.update_layout(
            title=f"Feature Importance - {model_name}",
            xaxis_title="Importance Score",
            yaxis_title="Features",
            yaxis=dict(autorange="reversed"),
            height=max(400, len(sorted_features) * 25)
        )
        
        return self.apply_theme(self.add_watermark(fig))


class RealEstateAnalyticsCharts(ChartBuilderBase):
    """Specialized charts for real estate analytics and lead management."""
    
    def create_lead_score_distribution(self, lead_scores: pd.DataFrame) -> go.Figure:
        """Create lead score distribution analysis."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Score Distribution", "Score vs Conversion", "Box Plot by Source", "Trend Over Time"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 1. Score distribution histogram
        fig.add_trace(
            go.Histogram(
                x=lead_scores['score'],
                nbinsx=30,
                marker_color=self.theme.primary_blue,
                opacity=0.7,
                name="Lead Scores"
            ),
            row=1, col=1
        )
        
        # 2. Score vs conversion scatter
        if 'converted' in lead_scores.columns:
            colors = [self.theme.primary_green if conv else self.theme.secondary_gray 
                     for conv in lead_scores['converted']]
            fig.add_trace(
                go.Scatter(
                    x=lead_scores['score'],
                    y=lead_scores.get('value', lead_scores.index),
                    mode='markers',
                    marker=dict(color=colors, size=8, opacity=0.6),
                    name="Conversion Status"
                ),
                row=1, col=2
            )
        
        # 3. Box plot by source
        if 'source' in lead_scores.columns:
            sources = lead_scores['source'].unique()
            for i, source in enumerate(sources):
                source_data = lead_scores[lead_scores['source'] == source]['score']
                fig.add_trace(
                    go.Box(
                        y=source_data,
                        name=source,
                        marker_color=self.theme.categorical_palette[i % len(self.theme.categorical_palette)]
                    ),
                    row=2, col=1
                )
        
        # 4. Trend over time
        if 'date' in lead_scores.columns:
            daily_avg = lead_scores.groupby('date')['score'].mean().reset_index()
            fig.add_trace(
                go.Scatter(
                    x=daily_avg['date'],
                    y=daily_avg['score'],
                    mode='lines+markers',
                    line=dict(color=self.theme.primary_gold, width=3),
                    name="Daily Average"
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title="Lead Score Analysis Dashboard",
            showlegend=True,
            height=800
        )
        
        return self.apply_theme(self.add_watermark(fig))
    
    def create_conversion_funnel(self, funnel_data: pd.DataFrame) -> go.Figure:
        """Create conversion funnel chart."""
        fig = go.Figure(go.Funnel(
            y=funnel_data['stage'],
            x=funnel_data['count'],
            textposition="inside",
            textinfo="value+percent initial",
            marker_color=self.theme.categorical_palette[:len(funnel_data)],
            connector=dict(line=dict(color=self.theme.secondary_gray, dash="solid", width=2))
        ))
        
        fig.update_layout(
            title="Lead Conversion Funnel",
            font_size=12,
            height=600
        )
        
        return self.apply_theme(self.add_watermark(fig))
    
    def create_market_trends(self, market_data: pd.DataFrame) -> go.Figure:
        """Create market trends analysis with multiple metrics."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Price Trends", "Inventory Levels", "Days on Market", "Market Activity"),
            specs=[[{"secondary_y": True}, {"secondary_y": True}],
                   [{"secondary_y": False}, {"secondary_y": True}]]
        )
        
        # 1. Price trends
        if 'avg_price' in market_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=market_data['date'],
                    y=market_data['avg_price'],
                    mode='lines+markers',
                    name='Avg Price',
                    line=dict(color=self.theme.primary_blue, width=3)
                ),
                row=1, col=1
            )
        
        if 'price_per_sqft' in market_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=market_data['date'],
                    y=market_data['price_per_sqft'],
                    mode='lines',
                    name='Price/SqFt',
                    line=dict(color=self.theme.primary_gold, width=2, dash='dash')
                ),
                row=1, col=1, secondary_y=True
            )
        
        # 2. Inventory levels
        if 'active_listings' in market_data.columns:
            fig.add_trace(
                go.Bar(
                    x=market_data['date'],
                    y=market_data['active_listings'],
                    name='Active Listings',
                    marker_color=self.theme.primary_green,
                    opacity=0.7
                ),
                row=1, col=2
            )
        
        # 3. Days on market
        if 'avg_dom' in market_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=market_data['date'],
                    y=market_data['avg_dom'],
                    mode='lines+markers',
                    name='Avg Days on Market',
                    line=dict(color=self.theme.primary_red, width=3),
                    fill='tonexty'
                ),
                row=2, col=1
            )
        
        # 4. Market activity
        if 'sales_volume' in market_data.columns and 'new_listings' in market_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=market_data['date'],
                    y=market_data['sales_volume'],
                    mode='lines',
                    name='Sales Volume',
                    line=dict(color=self.theme.info, width=2)
                ),
                row=2, col=2
            )
            
            fig.add_trace(
                go.Scatter(
                    x=market_data['date'],
                    y=market_data['new_listings'],
                    mode='lines',
                    name='New Listings',
                    line=dict(color=self.theme.warning, width=2, dash='dot')
                ),
                row=2, col=2, secondary_y=True
            )
        
        fig.update_layout(
            title="Market Trends Analysis",
            showlegend=True,
            height=800
        )
        
        return self.apply_theme(self.add_watermark(fig))
    
    def create_attribution_analysis(self, attribution_data: pd.DataFrame) -> go.Figure:
        """Create lead source attribution analysis."""
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "domain"}, {"type": "xy"}]],
            subplot_titles=("Source Distribution", "Source Performance")
        )
        
        # 1. Source distribution pie chart
        fig.add_trace(
            go.Pie(
                labels=attribution_data['source'],
                values=attribution_data['count'],
                hole=0.4,
                marker_colors=self.theme.categorical_palette[:len(attribution_data)],
                textinfo='label+percent',
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # 2. Source performance bar chart
        if 'conversion_rate' in attribution_data.columns:
            fig.add_trace(
                go.Bar(
                    x=attribution_data['source'],
                    y=attribution_data['conversion_rate'],
                    marker_color=self.theme.primary_blue,
                    text=[f"{rate:.1%}" for rate in attribution_data['conversion_rate']],
                    textposition='outside',
                    name='Conversion Rate'
                ),
                row=1, col=2
            )
        
        fig.update_layout(
            title="Lead Source Attribution Analysis",
            showlegend=False,
            height=500
        )
        
        return self.apply_theme(self.add_watermark(fig))


class InteractiveDashboardWidgets(ChartBuilderBase):
    """Interactive dashboard widgets with callbacks and dynamic updates."""
    
    def create_kpi_card(self, title: str, value: Union[str, float], 
                       change: float = None, format_type: str = "number") -> go.Figure:
        """Create KPI card widget."""
        fig = go.Figure()
        
        # Format value
        if format_type == "currency":
            formatted_value = f"${value:,.0f}" if isinstance(value, (int, float)) else value
        elif format_type == "percentage":
            formatted_value = f"{value:.1%}" if isinstance(value, (int, float)) else value
        else:
            formatted_value = f"{value:,.0f}" if isinstance(value, (int, float)) else value
        
        # Add main metric
        fig.add_trace(go.Indicator(
            mode="number+delta" if change is not None else "number",
            value=value if isinstance(value, (int, float)) else 0,
            title={"text": title, "font": {"size": 16}},
            number={"font": {"size": 36, "color": self.theme.primary_blue}},
            delta={"reference": value - change if change is not None else 0,
                   "valueformat": ".1%",
                   "increasing": {"color": self.theme.success},
                   "decreasing": {"color": self.theme.danger}} if change is not None else None,
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        
        fig.update_layout(
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        return fig
    
    def create_real_time_metric(self, data: pd.DataFrame, metric_column: str,
                               time_column: str = 'timestamp') -> go.Figure:
        """Create real-time updating metric chart."""
        fig = go.Figure()
        
        # Add main line
        fig.add_trace(go.Scatter(
            x=data[time_column],
            y=data[metric_column],
            mode='lines+markers',
            line=dict(color=self.theme.primary_blue, width=3),
            marker=dict(size=6),
            name=metric_column.title(),
            hovertemplate=f"<b>{metric_column.title()}</b><br>" +
                         "Time: %{x}<br>" +
                         "Value: %{y:,.0f}<br>" +
                         "<extra></extra>"
        ))
        
        # Add trend line
        if len(data) > 1:
            z = np.polyfit(range(len(data)), data[metric_column], 1)
            trend_line = np.poly1d(z)(range(len(data)))
            
            fig.add_trace(go.Scatter(
                x=data[time_column],
                y=trend_line,
                mode='lines',
                line=dict(color=self.theme.primary_gold, width=2, dash='dash'),
                name='Trend',
                opacity=0.7
            ))
        
        # Add confidence band if variance data available
        if f'{metric_column}_std' in data.columns:
            upper_bound = data[metric_column] + data[f'{metric_column}_std']
            lower_bound = data[metric_column] - data[f'{metric_column}_std']
            
            fig.add_trace(go.Scatter(
                x=data[time_column],
                y=upper_bound,
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=data[time_column],
                y=lower_bound,
                mode='lines',
                line=dict(width=0),
                fillcolor=f"rgba{tuple(list(int(self.theme.primary_blue[1:][i:i+2], 16) for i in (0, 2, 4)) + [0.2])}",
                fill='tonexty',
                showlegend=False,
                hoverinfo='skip'
            ))
        
        fig.update_layout(
            title=f"Real-time {metric_column.title()}",
            xaxis_title="Time",
            yaxis_title=metric_column.title(),
            height=400,
            hovermode='x unified'
        )
        
        return self.apply_theme(fig)
    
    def create_forecast_chart(self, historical_data: pd.DataFrame, 
                             forecast_data: pd.DataFrame,
                             value_column: str, time_column: str = 'date') -> go.Figure:
        """Create forecast chart with confidence intervals."""
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=historical_data[time_column],
            y=historical_data[value_column],
            mode='lines+markers',
            name='Historical',
            line=dict(color=self.theme.primary_blue, width=3),
            marker=dict(size=6)
        ))
        
        # Forecast data
        fig.add_trace(go.Scatter(
            x=forecast_data[time_column],
            y=forecast_data[value_column],
            mode='lines+markers',
            name='Forecast',
            line=dict(color=self.theme.primary_gold, width=3, dash='dash'),
            marker=dict(size=6, symbol='diamond')
        ))
        
        # Confidence intervals
        if 'upper_bound' in forecast_data.columns and 'lower_bound' in forecast_data.columns:
            fig.add_trace(go.Scatter(
                x=forecast_data[time_column],
                y=forecast_data['upper_bound'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast_data[time_column],
                y=forecast_data['lower_bound'],
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor=f"rgba{tuple(list(int(self.theme.primary_gold[1:][i:i+2], 16) for i in (0, 2, 4)) + [0.2])}",
                name='Confidence Interval',
                hoverinfo='skip'
            ))
        
        # Add vertical line at forecast start
        forecast_start = forecast_data[time_column].iloc[0]
        fig.add_vline(
            x=forecast_start,
            line_dash="dot",
            line_color=self.theme.secondary_gray,
            annotation_text="Forecast Start"
        )
        
        fig.update_layout(
            title=f"{value_column.title()} Forecast",
            xaxis_title="Date",
            yaxis_title=value_column.title(),
            height=500,
            hovermode='x unified'
        )
        
        return self.apply_theme(self.add_watermark(fig))


class ChartFactory:
    """Main chart factory for creating all chart types with Jorge theme integration."""
    
    def __init__(self, dark_mode: bool = False, colorblind_friendly: bool = False):
        self.dark_mode = dark_mode
        self.colorblind_friendly = colorblind_friendly
        self.theme = JorgeTheme()
        
        # Override palette if colorblind friendly
        if colorblind_friendly:
            self.theme.categorical_palette = self.theme.colorblind_palette
        
        # Initialize chart builders
        self.ml_charts = MLPerformanceCharts(self.theme, dark_mode)
        self.real_estate_charts = RealEstateAnalyticsCharts(self.theme, dark_mode)
        self.dashboard_widgets = InteractiveDashboardWidgets(self.theme, dark_mode)
    
    def create_chart(self, chart_type: str, data: Any, **kwargs) -> go.Figure:
        """Factory method to create any chart type."""
        chart_mapping = {
            # ML Performance Charts
            'roc_curve': self.ml_charts.create_roc_curve,
            'precision_recall': self.ml_charts.create_precision_recall_curve,
            'confusion_matrix': self.ml_charts.create_confusion_matrix,
            'feature_importance': self.ml_charts.create_feature_importance,
            
            # Real Estate Analytics
            'lead_score_distribution': self.real_estate_charts.create_lead_score_distribution,
            'conversion_funnel': self.real_estate_charts.create_conversion_funnel,
            'market_trends': self.real_estate_charts.create_market_trends,
            'attribution_analysis': self.real_estate_charts.create_attribution_analysis,
            
            # Dashboard Widgets
            'kpi_card': self.dashboard_widgets.create_kpi_card,
            'real_time_metric': self.dashboard_widgets.create_real_time_metric,
            'forecast_chart': self.dashboard_widgets.create_forecast_chart
        }
        
        if chart_type not in chart_mapping:
            raise ValueError(f"Unknown chart type: {chart_type}. Available types: {list(chart_mapping.keys())}")
        
        try:
            return chart_mapping[chart_type](data, **kwargs)
        except Exception as e:
            logger.error(f"Error creating {chart_type} chart: {e}")
            # Return error chart
            return self._create_error_chart(str(e))
    
    def _create_error_chart(self, error_message: str) -> go.Figure:
        """Create error chart when chart creation fails."""
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart Error: {error_message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor="center", yanchor="middle",
            showarrow=False,
            font=dict(size=16, color=self.theme.danger),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=self.theme.danger,
            borderwidth=2
        )
        
        fig.update_layout(
            title="Chart Creation Error",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            height=400
        )
        
        return self.ml_charts.apply_theme(fig)
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Get current theme colors for external use."""
        return {
            'primary_blue': self.theme.primary_blue,
            'primary_gold': self.theme.primary_gold,
            'primary_green': self.theme.primary_green,
            'primary_red': self.theme.primary_red,
            'categorical_palette': self.theme.categorical_palette,
            'success': self.theme.success,
            'warning': self.theme.warning,
            'danger': self.theme.danger,
            'info': self.theme.info
        }
    
    def batch_export(self, charts: Dict[str, go.Figure], base_path: str = "./exports",
                    formats: List[str] = ["png", "html"]) -> Dict[str, List[str]]:
        """Batch export multiple charts for reports."""
        exported_files = {}
        
        for chart_name, fig in charts.items():
            chart_files = []
            for format_type in formats:
                try:
                    filename = f"{base_path}/{chart_name}"
                    exported_file = self.ml_charts.export_chart(fig, filename, format_type)
                    chart_files.append(exported_file)
                except Exception as e:
                    logger.error(f"Error exporting {chart_name} as {format_type}: {e}")
            
            exported_files[chart_name] = chart_files
        
        return exported_files


# Convenience functions for quick chart creation
def quick_roc_curve(y_true: np.ndarray, y_scores: np.ndarray, **kwargs) -> go.Figure:
    """Quick ROC curve creation."""
    factory = ChartFactory()
    return factory.create_chart('roc_curve', y_true, y_scores=y_scores, **kwargs)

def quick_lead_analysis(lead_data: pd.DataFrame, **kwargs) -> go.Figure:
    """Quick lead score distribution analysis."""
    factory = ChartFactory()
    return factory.create_chart('lead_score_distribution', lead_data, **kwargs)

def quick_kpi_card(title: str, value: Union[str, float], **kwargs) -> go.Figure:
    """Quick KPI card creation."""
    factory = ChartFactory()
    return factory.create_chart('kpi_card', title, value=value, **kwargs)


# Example usage and demonstration
if __name__ == "__main__":
    # Example data generation for testing
    np.random.seed(42)
    
    # Sample ML data
    y_true = np.random.choice([0, 1], size=1000, p=[0.7, 0.3])
    y_scores = np.random.beta(2, 5, size=1000)
    
    # Sample lead data
    lead_data = pd.DataFrame({
        'score': np.random.beta(2, 5, size=500) * 100,
        'converted': np.random.choice([0, 1], size=500, p=[0.8, 0.2]),
        'source': np.random.choice(['Website', 'Social', 'Referral', 'PPC'], size=500),
        'date': pd.date_range('2024-01-01', periods=500, freq='D')[:500],
        'value': np.random.exponential(scale=50000, size=500)
    })
    
    # Create chart factory
    factory = ChartFactory(dark_mode=False, colorblind_friendly=True)
    
    # Demonstrate chart creation
    print("Jorge's Chart Builder Demo")
    print("=========================")
    
    # ROC Curve
    roc_fig = factory.create_chart('roc_curve', y_true, y_scores=y_scores)
    print("✓ ROC Curve created")
    
    # Lead Analysis
    lead_fig = factory.create_chart('lead_score_distribution', lead_data)
    print("✓ Lead Score Distribution created")
    
    # KPI Card
    kpi_fig = factory.create_chart('kpi_card', "Monthly Revenue", value=125000, change=0.15, format_type="currency")
    print("✓ KPI Card created")
    
    # Export examples
    charts = {
        'roc_analysis': roc_fig,
        'lead_analysis': lead_fig,
        'revenue_kpi': kpi_fig
    }
    
    # Batch export (commented out to avoid actual file creation in demo)
    # exported = factory.batch_export(charts)
    # print(f"✓ Charts exported: {exported}")
    
    print("\nChart Builder successfully initialized!")
    print(f"Available chart types: {list(factory.chart_mapping.keys()) if hasattr(factory, 'chart_mapping') else 'See create_chart method'}")
    print("Theme colors loaded:", factory.get_theme_colors().keys())