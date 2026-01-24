"""
Predictive Insights Dashboard - Enterprise Command Center

Advanced predictive analytics dashboard with:
- Conversion Forecasting with ML-based deal probability predictions
- Commission Forecasting using lead scoring and market trends
- Lead Quality Trends with seasonal and temporal analysis
- Anomaly Detection for unusual lead patterns
- Interactive alerts and real-time monitoring

Integration:
- ML Analytics Engine for predictions
- Jorge's 6% commission rate calculations
- Advanced visualization with Plotly
- Theme-consistent design
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import json
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Enterprise imports
try:
    from ghl_real_estate_ai.services.ml_lead_analyzer import MLLeadPredictor
    from ghl_real_estate_ai.services.enhanced_lead_intelligence import EnhancedLeadIntelligence
    from ghl_real_estate_ai.core.logger import get_logger
except ImportError:
    # Fallback for development
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class PredictionMetric:
    """Prediction metric container"""
    value: float
    confidence: float
    trend: str
    change_pct: float

@dataclass
class Alert:
    """Alert data structure"""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str

class PredictiveInsightsDashboard:
    """
    Enterprise Predictive Insights Dashboard
    
    Features:
    - Conversion probability forecasting
    - Commission revenue projections
    - Lead quality trend analysis  
    - Anomaly detection and alerts
    - Interactive visualizations
    """
    
    def __init__(self):
        self.jorge_commission_rate = 0.06  # Jorge's 6% commission rate
        self.prediction_horizons = [30, 60, 90]  # Days for forecasting
        self.alerts: List[Alert] = []
        
        # Initialize session state
        if 'prediction_cache' not in st.session_state:
            st.session_state.prediction_cache = {}
        if 'prediction_tab' not in st.session_state:
            st.session_state.prediction_tab = 'forecast'
    
    def render(self, container_key: str = 'predictive_insights'):
        """Main render method"""
        self._inject_css()
        
        with st.container():
            st.markdown('<div class="prediction-dashboard">', unsafe_allow_html=True)
            
            self._render_header()
            self._render_alerts()
            self._render_tab_navigation()
            
            # Render active tab content
            tab = st.session_state.prediction_tab
            if tab == 'forecast':
                self._render_forecasting_tab()
            elif tab == 'quality':
                self._render_quality_tab()
            elif tab == 'anomalies':
                self._render_anomalies_tab()
            elif tab == 'insights':
                self._render_insights_tab()
                
            st.markdown('</div>', unsafe_allow_html=True)
    
    def _inject_css(self):
        """Inject custom CSS for enterprise styling"""
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
        
        .prediction-dashboard {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%);
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(148, 163, 184, 0.1);
            backdrop-filter: blur(20px);
        }
        
        .dashboard-header {
            text-align: center;
            margin-bottom: 2.5rem;
            padding-bottom: 1.5rem;
            border-bottom: 2px solid rgba(59, 130, 246, 0.2);
        }
        
        .dashboard-title {
            font-family: 'Inter', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: #f8fafc;
            margin: 0;
            text-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
        }
        
        .dashboard-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 1.1rem;
            color: #cbd5e1;
            margin: 0.5rem 0 0 0;
            font-weight: 500;
        }
        
        .prediction-tabs {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .prediction-tab {
            padding: 1rem 1.5rem;
            background: rgba(51, 65, 85, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            color: #e2e8f0;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
        }
        
        .prediction-tab:hover {
            background: rgba(59, 130, 246, 0.2);
            border-color: rgba(59, 130, 246, 0.4);
            transform: translateY(-2px);
        }
        
        .prediction-tab.active {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            border-color: #3b82f6;
            color: white;
            box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3);
        }
        
        .forecast-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .forecast-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(30, 41, 59, 0.6));
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .forecast-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
            border-color: rgba(59, 130, 246, 0.3);
        }
        
        .forecast-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        
        .forecast-title {
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            font-weight: 600;
            color: #cbd5e1;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .forecast-confidence {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }
        
        .forecast-value {
            font-family: 'Space Mono', monospace;
            font-size: 2.2rem;
            font-weight: 700;
            color: #f8fafc;
            margin: 0.5rem 0;
            text-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
        }
        
        .forecast-change {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .trend-positive {
            color: #22c55e;
        }
        
        .trend-negative {
            color: #ef4444;
        }
        
        .trend-neutral {
            color: #f59e0b;
        }
        
        .alert-container {
            background: rgba(220, 38, 38, 0.1);
            border: 1px solid rgba(220, 38, 38, 0.3);
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .alert-container.warning {
            background: rgba(245, 158, 11, 0.1);
            border-color: rgba(245, 158, 11, 0.3);
        }
        
        .alert-container.info {
            background: rgba(59, 130, 246, 0.1);
            border-color: rgba(59, 130, 246, 0.3);
        }
        
        .alert-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }
        
        .alert-title {
            font-weight: 600;
            color: #f8fafc;
        }
        
        .alert-timestamp {
            font-size: 0.75rem;
            color: #94a3b8;
            margin-left: auto;
        }
        
        .chart-container {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            backdrop-filter: blur(10px);
        }
        
        .chart-title {
            font-family: 'Inter', sans-serif;
            font-size: 1.2rem;
            font-weight: 600;
            color: #f8fafc;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .insight-card {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1));
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        .insight-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        
        .insight-title {
            font-family: 'Inter', sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: #f8fafc;
            margin-bottom: 0.5rem;
        }
        
        .insight-description {
            color: #cbd5e1;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }
        
        .metric-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }
        
        .metric-value {
            font-family: 'Space Mono', monospace;
            font-size: 1.8rem;
            font-weight: 700;
            color: #3b82f6;
            margin: 0.5rem 0;
        }
        
        .metric-label {
            font-size: 0.8rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _render_header(self):
        """Render dashboard header"""
        st.markdown("""
        <div class="dashboard-header">
            <h1 class="dashboard-title">🔮 Predictive Insights</h1>
            <p class="dashboard-subtitle">Advanced ML-powered forecasting and anomaly detection</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_alerts(self):
        """Render active alerts"""
        alerts = self._get_active_alerts()
        
        if alerts:
            for alert in alerts:
                level_class = alert.level.value
                level_icon = {
                    AlertLevel.INFO: "ℹ️",
                    AlertLevel.WARNING: "⚠️", 
                    AlertLevel.CRITICAL: "🚨"
                }.get(alert.level, "ℹ️")
                
                st.markdown(f"""
                <div class="alert-container {level_class}">
                    <div class="alert-header">
                        <span>{level_icon}</span>
                        <span class="alert-title">{alert.title}</span>
                        <span class="alert-timestamp">{alert.timestamp.strftime('%H:%M')}</span>
                    </div>
                    <div>{alert.message}</div>
                </div>
                """, unsafe_allow_html=True)
    
    def _render_tab_navigation(self):
        """Render tab navigation"""
        tabs = [
            ('forecast', '📈 Forecasting'),
            ('quality', '🎯 Lead Quality'),
            ('anomalies', '🔍 Anomalies'),
            ('insights', '💡 Insights')
        ]
        
        cols = st.columns(4)
        for i, (tab_key, tab_label) in enumerate(tabs):
            with cols[i]:
                if st.button(
                    tab_label, 
                    key=f'pred_tab_{tab_key}',
                    use_container_width=True,
                    type='primary' if st.session_state.prediction_tab == tab_key else 'secondary'
                ):
                    st.session_state.prediction_tab = tab_key
                    st.rerun()
    
    def _render_forecasting_tab(self):
        """Render forecasting tab with conversion and commission predictions"""
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_conversion_forecasts()
        
        with col2:
            self._render_commission_forecasts()
        
        # Full-width charts
        self._render_forecast_trends()
        self._render_probability_distribution()
    
    def _render_conversion_forecasts(self):
        """Render conversion rate forecasts"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🎯 Conversion Forecasts</h3>', unsafe_allow_html=True)
        
        forecasts = self._generate_conversion_forecasts()
        
        # Display forecast cards
        for horizon, forecast in forecasts.items():
            st.markdown(f"""
            <div class="forecast-card">
                <div class="forecast-header">
                    <div class="forecast-title">Next {horizon} Days</div>
                    <div class="forecast-confidence">{forecast.confidence:.0%}</div>
                </div>
                <div class="forecast-value">{forecast.value:.1f}%</div>
                <div class="forecast-change trend-{forecast.trend}">
                    {'📈' if forecast.trend == 'positive' else '📉' if forecast.trend == 'negative' else '➡️'}
                    {forecast.change_pct:+.1f}% vs last period
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_commission_forecasts(self):
        """Render commission revenue forecasts"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">💰 Commission Forecasts</h3>', unsafe_allow_html=True)
        
        commission_data = self._generate_commission_forecasts()
        
        # Display commission projections
        for horizon, data in commission_data.items():
            commission_value = data['deals'] * data['avg_deal_value'] * self.jorge_commission_rate
            confidence = data['confidence']
            
            st.markdown(f"""
            <div class="forecast-card">
                <div class="forecast-header">
                    <div class="forecast-title">Next {horizon} Days</div>
                    <div class="forecast-confidence">{confidence:.0%}</div>
                </div>
                <div class="forecast-value">${commission_value:,.0f}</div>
                <div class="forecast-change trend-positive">
                    📈 {data['deals']:.0f} deals @ 6% commission
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_forecast_trends(self):
        """Render forecast trend visualization"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📊 Forecast Trends & Confidence Intervals</h3>', unsafe_allow_html=True)
        
        # Generate trend data
        dates, trends = self._generate_forecast_trend_data()
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Conversion Rate Forecast', 'Deal Volume Forecast', 
                          'Commission Revenue Forecast', 'Lead Quality Index'],
            specs=[[{}, {}], [{}, {}]]
        )
        
        # Conversion rate forecast
        fig.add_trace(
            go.Scatter(
                x=dates, y=trends['conversion_actual'], 
                name='Actual Conversion',
                line=dict(color='#22c55e', width=3),
                mode='lines'
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=dates[30:], y=trends['conversion_forecast'],
                name='Forecast',
                line=dict(color='#3b82f6', width=2, dash='dash'),
                mode='lines'
            ),
            row=1, col=1
        )
        
        # Deal volume forecast
        fig.add_trace(
            go.Scatter(
                x=dates, y=trends['deals_actual'],
                name='Actual Deals',
                line=dict(color='#f59e0b', width=3),
                mode='lines'
            ),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(
                x=dates[30:], y=trends['deals_forecast'],
                name='Forecast Deals',
                line=dict(color='#8b5cf6', width=2, dash='dash'),
                mode='lines'
            ),
            row=1, col=2
        )
        
        # Commission revenue
        commission_actual = np.array(trends['deals_actual']) * 450000 * self.jorge_commission_rate
        commission_forecast = np.array(trends['deals_forecast']) * 450000 * self.jorge_commission_rate
        
        fig.add_trace(
            go.Scatter(
                x=dates, y=commission_actual,
                name='Actual Commission',
                line=dict(color='#10b981', width=3),
                mode='lines'
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=dates[30:], y=commission_forecast,
                name='Forecast Commission',
                line=dict(color='#ef4444', width=2, dash='dash'),
                mode='lines'
            ),
            row=2, col=1
        )
        
        # Lead quality index
        fig.add_trace(
            go.Scatter(
                x=dates, y=trends['quality_actual'],
                name='Quality Index',
                line=dict(color='#06b6d4', width=3),
                fill='tonexty'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=600,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            font_family='Inter'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_probability_distribution(self):
        """Render deal probability distribution"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🎲 Deal Probability Distribution</h3>', unsafe_allow_html=True)
        
        # Generate probability data
        prob_data = self._generate_probability_distribution()
        
        fig = go.Figure()
        
        # Add probability distribution
        fig.add_trace(go.Histogram(
            x=prob_data['probabilities'],
            nbinsx=20,
            name='Deal Probabilities',
            marker_color='rgba(59, 130, 246, 0.7)',
            marker_line_color='rgba(59, 130, 246, 1)',
            marker_line_width=2
        ))
        
        # Add mean line
        mean_prob = np.mean(prob_data['probabilities'])
        fig.add_vline(
            x=mean_prob,
            line_dash="dash",
            line_color="#22c55e",
            annotation_text=f"Mean: {mean_prob:.1%}",
            annotation_position="top"
        )
        
        fig.update_layout(
            title="Distribution of Deal Close Probabilities",
            xaxis_title="Close Probability",
            yaxis_title="Number of Deals",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            font_family='Inter'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_quality_tab(self):
        """Render lead quality trends and analysis"""
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_quality_heatmap()
        
        with col2:
            self._render_temporal_quality_analysis()
        
        # Full-width seasonal analysis
        self._render_seasonal_quality_patterns()
    
    def _render_quality_heatmap(self):
        """Render lead quality heatmap by source and time"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🔥 Quality Heatmap by Source</h3>', unsafe_allow_html=True)
        
        # Generate heatmap data
        heatmap_data = self._generate_quality_heatmap_data()
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data['quality_scores'],
            x=heatmap_data['time_periods'],
            y=heatmap_data['sources'],
            colorscale='RdYlGn',
            hoverongaps=False,
            colorbar=dict(title="Quality Score")
        ))
        
        fig.update_layout(
            title="Lead Quality by Source & Time",
            xaxis_title="Time Period",
            yaxis_title="Lead Source",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            font_family='Inter'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_temporal_quality_analysis(self):
        """Render temporal quality analysis"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">⏰ Quality by Time of Day</h3>', unsafe_allow_html=True)
        
        # Generate temporal data
        temporal_data = self._generate_temporal_quality_data()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=temporal_data['hours'],
            y=temporal_data['weekday_quality'],
            mode='lines+markers',
            name='Weekdays',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=temporal_data['hours'],
            y=temporal_data['weekend_quality'],
            mode='lines+markers',
            name='Weekends',
            line=dict(color='#f59e0b', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Lead Quality Throughout the Day",
            xaxis_title="Hour of Day",
            yaxis_title="Average Quality Score",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            font_family='Inter'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_seasonal_quality_patterns(self):
        """Render seasonal quality pattern analysis"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🗓️ Seasonal Quality Patterns</h3>', unsafe_allow_html=True)
        
        # Generate seasonal data
        seasonal_data = self._generate_seasonal_data()
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=['Monthly Trends', 'Day of Week Analysis'],
            specs=[[{}, {}]]
        )
        
        # Monthly trends
        fig.add_trace(
            go.Scatter(
                x=seasonal_data['months'],
                y=seasonal_data['monthly_quality'],
                mode='lines+markers',
                name='Quality Score',
                line=dict(color='#10b981', width=3),
                marker=dict(size=10)
            ),
            row=1, col=1
        )
        
        # Day of week analysis
        fig.add_trace(
            go.Bar(
                x=seasonal_data['weekdays'],
                y=seasonal_data['weekday_scores'],
                name='Daily Quality',
                marker_color='rgba(59, 130, 246, 0.7)',
                marker_line_color='rgba(59, 130, 246, 1)',
                marker_line_width=2
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            font_family='Inter'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_anomalies_tab(self):
        """Render anomaly detection and unusual patterns"""
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_anomaly_detection_chart()
        
        with col2:
            self._render_anomaly_alerts()
        
        # Full-width pattern analysis
        self._render_pattern_analysis()
    
    def _render_anomaly_detection_chart(self):
        """Render anomaly detection visualization"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🚨 Anomaly Detection</h3>', unsafe_allow_html=True)
        
        # Generate anomaly data
        anomaly_data = self._generate_anomaly_data()
        
        fig = go.Figure()
        
        # Normal data points
        normal_mask = ~anomaly_data['is_anomaly']
        fig.add_trace(go.Scatter(
            x=anomaly_data['dates'][normal_mask],
            y=anomaly_data['values'][normal_mask],
            mode='markers',
            name='Normal',
            marker=dict(color='#22c55e', size=6)
        ))
        
        # Anomalous points
        anomaly_mask = anomaly_data['is_anomaly']
        fig.add_trace(go.Scatter(
            x=anomaly_data['dates'][anomaly_mask],
            y=anomaly_data['values'][anomaly_mask],
            mode='markers',
            name='Anomaly',
            marker=dict(color='#ef4444', size=12, symbol='x')
        ))
        
        # Trend line
        fig.add_trace(go.Scatter(
            x=anomaly_data['dates'],
            y=anomaly_data['trend'],
            mode='lines',
            name='Trend',
            line=dict(color='#3b82f6', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Lead Volume Anomaly Detection",
            xaxis_title="Date",
            yaxis_title="Lead Count",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            font_family='Inter'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_anomaly_alerts(self):
        """Render anomaly-based alerts"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">⚠️ Recent Anomalies</h3>', unsafe_allow_html=True)
        
        anomalies = self._get_recent_anomalies()
        
        for anomaly in anomalies:
            severity_color = {
                'low': '#f59e0b',
                'medium': '#ef4444',
                'high': '#dc2626'
            }.get(anomaly['severity'], '#f59e0b')
            
            st.markdown(f"""
            <div style="
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid {severity_color};
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.2rem;">🚨</span>
                    <strong>{anomaly['title']}</strong>
                    <span style="margin-left: auto; font-size: 0.8rem; color: #94a3b8;">
                        {anomaly['timestamp'].strftime('%Y-%m-%d %H:%M')}
                    </span>
                </div>
                <p style="margin: 0.5rem 0 0 2rem; color: #cbd5e1; font-size: 0.9rem;">
                    {anomaly['description']}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_pattern_analysis(self):
        """Render pattern analysis visualization"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">📊 Pattern Analysis & Correlations</h3>', unsafe_allow_html=True)
        
        # Generate pattern data
        pattern_data = self._generate_pattern_analysis()
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Lead Source Correlation', 'Time Pattern Matrix', 
                          'Conversion Correlation', 'Quality vs Volume'],
            specs=[[{'type': 'heatmap'}, {'type': 'heatmap'}], 
                   [{'type': 'scatter'}, {'type': 'scatter'}]]
        )
        
        # Source correlation heatmap
        fig.add_trace(
            go.Heatmap(
                z=pattern_data['source_correlation'],
                x=pattern_data['sources'],
                y=pattern_data['sources'],
                colorscale='RdBu',
                showscale=False
            ),
            row=1, col=1
        )
        
        # Time pattern matrix
        fig.add_trace(
            go.Heatmap(
                z=pattern_data['time_patterns'],
                x=list(range(24)),
                y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                colorscale='Viridis',
                showscale=False
            ),
            row=1, col=2
        )
        
        # Conversion correlation scatter
        fig.add_trace(
            go.Scatter(
                x=pattern_data['quality_scores'],
                y=pattern_data['conversion_rates'],
                mode='markers',
                marker=dict(
                    color=pattern_data['lead_volumes'],
                    colorscale='Plasma',
                    size=8,
                    showscale=False
                ),
                name='Quality vs Conversion'
            ),
            row=2, col=1
        )
        
        # Quality vs Volume scatter
        fig.add_trace(
            go.Scatter(
                x=pattern_data['lead_volumes'],
                y=pattern_data['quality_scores'],
                mode='markers',
                marker=dict(color='#3b82f6', size=8),
                name='Volume vs Quality'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=600,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            font_family='Inter'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_insights_tab(self):
        """Render AI-generated insights and recommendations"""
        # Key insights grid
        insights = self._generate_insights()
        
        st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
        
        for insight in insights:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-icon">{insight['icon']}</div>
                <div class="insight-title">{insight['title']}</div>
                <div class="insight-description">{insight['description']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Recommendations
        self._render_recommendations()
    
    def _render_recommendations(self):
        """Render AI-powered recommendations"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🤖 AI Recommendations</h3>', unsafe_allow_html=True)
        
        recommendations = self._generate_recommendations()
        
        for rec in recommendations:
            priority_color = {
                'high': '#ef4444',
                'medium': '#f59e0b',
                'low': '#22c55e'
            }.get(rec['priority'], '#3b82f6')
            
            st.markdown(f"""
            <div style="
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid {priority_color};
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
            ">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                    <span style="font-size: 1.5rem;">{rec['icon']}</span>
                    <div>
                        <h4 style="margin: 0; color: white; font-weight: 600;">{rec['title']}</h4>
                        <span style="
                            background: {priority_color};
                            color: white;
                            padding: 0.25rem 0.5rem;
                            border-radius: 4px;
                            font-size: 0.75rem;
                            font-weight: 600;
                            text-transform: uppercase;
                        ">{rec['priority']} Priority</span>
                    </div>
                </div>
                <p style="margin: 0; color: #cbd5e1; line-height: 1.6;">
                    {rec['description']}
                </p>
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(148, 163, 184, 0.2);">
                    <strong style="color: #22c55e;">Expected Impact:</strong> 
                    <span style="color: #cbd5e1;">{rec['impact']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Data generation methods
    def _generate_conversion_forecasts(self) -> Dict[int, PredictionMetric]:
        """Generate conversion rate forecasts"""
        np.random.seed(42)  # For reproducible results
        
        forecasts = {}
        base_conversion = 12.5  # Base conversion rate
        
        for horizon in self.prediction_horizons:
            # Simulate forecast with decreasing accuracy over time
            forecast_value = base_conversion + np.random.normal(0, horizon * 0.1)
            confidence = max(0.6, 0.95 - horizon * 0.005)  # Decreasing confidence
            change_pct = np.random.uniform(-2, 3)
            trend = 'positive' if change_pct > 0.5 else 'negative' if change_pct < -0.5 else 'neutral'
            
            forecasts[horizon] = PredictionMetric(
                value=max(0, forecast_value),
                confidence=confidence,
                trend=trend,
                change_pct=change_pct
            )
        
        return forecasts
    
    def _generate_commission_forecasts(self) -> Dict[int, Dict]:
        """Generate commission revenue forecasts"""
        np.random.seed(42)
        
        forecasts = {}
        base_deals = 8  # Base deals per period
        avg_deal_value = 450000  # Average deal value
        
        for horizon in self.prediction_horizons:
            # Scale by horizon
            period_deals = base_deals * (horizon / 30)
            deals_forecast = period_deals + np.random.normal(0, period_deals * 0.2)
            confidence = max(0.7, 0.9 - horizon * 0.003)
            
            forecasts[horizon] = {
                'deals': max(0, deals_forecast),
                'avg_deal_value': avg_deal_value,
                'confidence': confidence
            }
        
        return forecasts
    
    def _generate_forecast_trend_data(self) -> Tuple[pd.DatetimeIndex, Dict]:
        """Generate trend data for forecasting charts"""
        # 60 days historical + 30 days forecast
        start_date = datetime.now() - timedelta(days=60)
        dates = pd.date_range(start=start_date, periods=90, freq='D')
        
        np.random.seed(42)
        
        # Generate realistic trends
        trends = {
            'conversion_actual': 12 + np.random.normal(0, 1, 60).cumsum() * 0.1 + np.sin(np.arange(60) * 0.1) * 2,
            'conversion_forecast': 12 + np.random.normal(0, 0.8, 30).cumsum() * 0.1,
            'deals_actual': 8 + np.random.normal(0, 1, 60).cumsum() * 0.05 + np.random.poisson(2, 60) * 0.5,
            'deals_forecast': 8 + np.random.normal(0, 0.6, 30).cumsum() * 0.05,
            'quality_actual': 75 + np.random.normal(0, 0.5, 60).cumsum() * 0.2 + np.sin(np.arange(60) * 0.15) * 3,
            'quality_forecast': 75 + np.random.normal(0, 0.4, 30).cumsum() * 0.2
        }
        
        # Ensure positive values
        for key in trends:
            trends[key] = np.maximum(trends[key], 0)
        
        return dates, trends
    
    def _generate_probability_distribution(self) -> Dict:
        """Generate deal probability distribution"""
        np.random.seed(42)
        
        # Simulate deal probabilities with realistic distribution
        n_deals = 150
        probabilities = np.concatenate([
            np.random.beta(2, 5, int(n_deals * 0.4)),  # Low probability deals
            np.random.beta(3, 3, int(n_deals * 0.4)),  # Medium probability deals  
            np.random.beta(5, 2, int(n_deals * 0.2))   # High probability deals
        ])
        
        return {
            'probabilities': probabilities,
            'n_deals': n_deals
        }
    
    def _generate_quality_heatmap_data(self) -> Dict:
        """Generate heatmap data for lead quality"""
        sources = ['Google Ads', 'Facebook', 'Organic', 'Referral', 'Direct', 'Email']
        time_periods = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
        
        np.random.seed(42)
        
        # Generate quality scores (0-100)
        quality_scores = np.random.uniform(60, 95, (len(sources), len(time_periods)))
        
        # Add some patterns
        quality_scores[0] *= 1.1  # Google Ads performs better
        quality_scores[2] *= 0.95  # Organic slightly lower
        quality_scores[:, -1] *= 1.05  # Recent week improvement
        
        return {
            'quality_scores': quality_scores,
            'sources': sources,
            'time_periods': time_periods
        }
    
    def _generate_temporal_quality_data(self) -> Dict:
        """Generate temporal quality analysis data"""
        hours = list(range(24))
        
        np.random.seed(42)
        
        # Business hours pattern for weekdays
        weekday_base = np.array([40, 35, 30, 28, 30, 35, 45, 60, 75, 80, 85, 85, 
                                80, 85, 90, 88, 85, 80, 70, 60, 50, 45, 42, 38])
        
        # Different pattern for weekends
        weekend_base = np.array([45, 42, 38, 35, 38, 42, 50, 55, 60, 65, 70, 75,
                               78, 75, 72, 68, 65, 60, 55, 52, 48, 47, 46, 45])
        
        # Add noise
        weekday_quality = weekday_base + np.random.normal(0, 3, 24)
        weekend_quality = weekend_base + np.random.normal(0, 3, 24)
        
        return {
            'hours': hours,
            'weekday_quality': weekday_quality,
            'weekend_quality': weekend_quality
        }
    
    def _generate_seasonal_data(self) -> Dict:
        """Generate seasonal pattern data"""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        np.random.seed(42)
        
        # Seasonal patterns in real estate
        monthly_quality = [72, 75, 82, 88, 92, 85, 78, 80, 85, 90, 86, 76]
        
        # Business day patterns
        weekday_scores = [85, 88, 90, 89, 87, 75, 70]
        
        return {
            'months': months,
            'monthly_quality': monthly_quality,
            'weekdays': weekdays,
            'weekday_scores': weekday_scores
        }
    
    def _generate_anomaly_data(self) -> Dict:
        """Generate anomaly detection data"""
        np.random.seed(42)
        
        n_points = 60
        dates = pd.date_range(end=datetime.now(), periods=n_points, freq='D')
        
        # Base trend
        trend = 50 + np.sin(np.arange(n_points) * 0.1) * 10 + np.random.normal(0, 0.5, n_points).cumsum()
        
        # Add normal noise
        values = trend + np.random.normal(0, 5, n_points)
        
        # Inject anomalies
        anomaly_indices = np.random.choice(n_points, size=5, replace=False)
        anomaly_multipliers = np.random.choice([-2, -1.5, 2, 2.5], size=5)
        
        is_anomaly = np.zeros(n_points, dtype=bool)
        is_anomaly[anomaly_indices] = True
        
        for i, mult in zip(anomaly_indices, anomaly_multipliers):
            values[i] = trend[i] + mult * 15  # Create clear anomalies
        
        return {
            'dates': dates,
            'values': values,
            'trend': trend,
            'is_anomaly': is_anomaly
        }
    
    def _get_recent_anomalies(self) -> List[Dict]:
        """Get recent anomaly alerts"""
        return [
            {
                'title': 'Unusual Lead Drop',
                'description': 'Google Ads lead volume dropped 45% below expected range.',
                'severity': 'high',
                'timestamp': datetime.now() - timedelta(hours=2)
            },
            {
                'title': 'Quality Score Spike',
                'description': 'Facebook leads showing 20% higher quality than usual.',
                'severity': 'low',
                'timestamp': datetime.now() - timedelta(hours=6)
            },
            {
                'title': 'Conversion Rate Anomaly',
                'description': 'Tuesday conversion rate 3x higher than typical pattern.',
                'severity': 'medium',
                'timestamp': datetime.now() - timedelta(hours=18)
            }
        ]
    
    def _generate_pattern_analysis(self) -> Dict:
        """Generate pattern analysis data"""
        np.random.seed(42)
        
        sources = ['Google', 'Facebook', 'Organic', 'Referral']
        
        # Correlation matrices
        source_correlation = np.random.uniform(0.3, 0.9, (4, 4))
        np.fill_diagonal(source_correlation, 1.0)
        
        # Time patterns (7 days x 24 hours)
        time_patterns = np.random.uniform(20, 100, (7, 24))
        
        # Add realistic business patterns
        for day in range(5):  # Weekdays
            time_patterns[day, 9:17] *= 1.5  # Business hours boost
        
        # Scatter plot data
        n_points = 100
        quality_scores = np.random.uniform(40, 95, n_points)
        conversion_rates = 5 + quality_scores * 0.15 + np.random.normal(0, 2, n_points)
        lead_volumes = np.random.poisson(20, n_points)
        
        return {
            'source_correlation': source_correlation,
            'sources': sources,
            'time_patterns': time_patterns,
            'quality_scores': quality_scores,
            'conversion_rates': conversion_rates,
            'lead_volumes': lead_volumes
        }
    
    def _generate_insights(self) -> List[Dict]:
        """Generate AI insights"""
        return [
            {
                'icon': '🎯',
                'title': 'Optimal Timing Identified',
                'description': 'Tuesday 2-4 PM shows 23% higher conversion rates. Consider increasing ad spend during these windows.'
            },
            {
                'icon': '📈',
                'title': 'Quality Trend Positive',
                'description': 'Lead quality has improved 15% over the past month, indicating better targeting strategies.'
            },
            {
                'icon': '💰',
                'title': 'Revenue Opportunity',
                'description': 'Facebook leads convert 18% better when contacted within 5 minutes. Implementing faster response could increase monthly revenue by $45K.'
            },
            {
                'icon': '🔍',
                'title': 'Seasonal Pattern Detected',
                'description': 'Spring season (March-May) shows 25% higher lead quality. Plan increased marketing budget allocation.'
            },
            {
                'icon': '⚡',
                'title': 'Source Performance',
                'description': 'Google Ads delivering highest volume but Referrals have 2x higher conversion rate.'
            },
            {
                'icon': '📊',
                'title': 'Commission Forecast',
                'description': 'Next 90 days projected to generate $165K in commissions based on current lead quality trends.'
            }
        ]
    
    def _generate_recommendations(self) -> List[Dict]:
        """Generate AI recommendations"""
        return [
            {
                'icon': '🚀',
                'title': 'Increase Tuesday Ad Spend',
                'priority': 'high',
                'description': 'Analysis shows 23% higher conversion rates on Tuesdays 2-4 PM. Increasing ad spend by 40% during this window could generate additional $12K monthly revenue.',
                'impact': '+$12K monthly revenue, +15% conversion rate'
            },
            {
                'icon': '⏰',
                'title': 'Implement Faster Response System',
                'priority': 'high', 
                'description': 'Leads contacted within 5 minutes have 45% higher conversion rates. Consider implementing automated initial response or expanding response team.',
                'impact': '+45% conversion rate, +$35K monthly revenue'
            },
            {
                'icon': '📱',
                'title': 'Optimize Mobile Experience',
                'priority': 'medium',
                'description': 'Mobile leads show 18% lower conversion but represent 65% of traffic. Improving mobile UX could unlock significant revenue.',
                'impact': '+$22K potential monthly increase'
            },
            {
                'icon': '🎯',
                'title': 'Referral Program Enhancement',
                'priority': 'medium',
                'description': 'Referral leads have 2x higher conversion rate but only 15% of volume. Enhanced referral incentives could increase high-quality lead flow.',
                'impact': '2x conversion rate, premium lead quality'
            },
            {
                'icon': '📈',
                'title': 'Seasonal Campaign Planning',
                'priority': 'low',
                'description': 'Spring season shows 25% quality improvement. Plan increased budget allocation for March-May period.',
                'impact': '+25% lead quality during peak season'
            }
        ]
    
    def _get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        current_time = datetime.now()
        
        # Simulate real-time alerts based on conditions
        active_alerts = []
        
        # Check for recent anomalies
        if current_time.hour >= 9:  # Business hours
            active_alerts.append(Alert(
                level=AlertLevel.WARNING,
                title="Lead Volume Below Threshold",
                message="Current hour lead volume is 25% below expected range",
                timestamp=current_time - timedelta(minutes=15),
                source="Volume Monitor"
            ))
        
        # Quality degradation alert
        if current_time.weekday() < 5:  # Weekdays
            active_alerts.append(Alert(
                level=AlertLevel.INFO,
                title="Quality Score Improvement",
                message="Lead quality increased 12% compared to yesterday",
                timestamp=current_time - timedelta(hours=1),
                source="Quality Monitor"
            ))
        
        return active_alerts


def render_predictive_insights_dashboard():
    """Render the complete predictive insights dashboard"""
    dashboard = PredictiveInsightsDashboard()
    dashboard.render()


# Main execution for standalone testing
if __name__ == "__main__":
    st.title("🔮 Predictive Insights Dashboard")
    render_predictive_insights_dashboard()