"""
Live Metrics Component for Real-Time Dashboard Updates.

Provides real-time metric cards that automatically update without page refreshes.
Integrates with WebSocket service for instant metric updates and trend visualization.

Features:
- Auto-refreshing metric cards with trend indicators
- Real-time chart updates for time-series data
- Performance metrics with alerts and thresholds
- Commission tracking with live pipeline updates
- Lead conversion metrics with real-time scoring
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import json
import threading
import time

from ghl_real_estate_ai.core.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)

class LiveMetricsManager:
    """
    Manages real-time metrics display and updates.
    
    Provides automatic metric updates via WebSocket integration,
    trend calculation, and performance optimization for dashboard display.
    """
    
    def __init__(self):
        self.cache_service = get_cache_service()
        
        # Initialize session state for metrics
        if "live_metrics" not in st.session_state:
            st.session_state.live_metrics = {}
            
        if "metric_history" not in st.session_state:
            st.session_state.metric_history = {}
            
        if "metrics_connection_status" not in st.session_state:
            st.session_state.metrics_connection_status = "disconnected"
            
        if "metrics_last_update" not in st.session_state:
            st.session_state.metrics_last_update = None

    def render_hero_metrics(self):
        """Render the main hero metrics with live updates."""
        st.subheader("📊 Live Business Metrics")
        
        # Connection status indicator
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.session_state.metrics_last_update:
                st.caption(f"Last updated: {st.session_state.metrics_last_update}")
        with col2:
            status_icon = {"connected": "🟢", "disconnected": "🔴", "updating": "🟡"}
            st.caption(f"{status_icon.get(st.session_state.metrics_connection_status, '🔴')} Live")

        # Hero metrics grid
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._render_metric_card("total_leads", "Total Leads", "👤", "247", "↗️ 12%")
            
        with col2:
            self._render_metric_card("qualified_leads", "Qualified Leads", "✅", "89", "↗️ 18%")
            
        with col3:
            self._render_metric_card("active_deals", "Active Deals", "🤝", "23", "↗️ 5%")
            
        with col4:
            self._render_metric_card("monthly_commission", "Monthly Commission", "💰", "$24,500", "↗️ 22%")

    def _render_metric_card(self, metric_key: str, title: str, icon: str, value: str, trend: str):
        """Render individual metric card with live updates."""
        # Get live metric data if available
        live_data = st.session_state.live_metrics.get(metric_key, {})
        
        if live_data:
            value = live_data.get("formatted_value", value)
            trend = live_data.get("trend_indicator", trend)
            
        # Metric card styling
        with st.container():
            st.markdown(f"""
            <div style="
                background: white;
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid #e1e5e9;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            ">
                <h3 style="margin: 0; color: #1f2937;">{icon} {title}</h3>
                <h1 style="margin: 0.5rem 0; color: #059669; font-weight: bold;">{value}</h1>
                <p style="margin: 0; color: #6b7280; font-weight: 600;">{trend}</p>
            </div>
            """, unsafe_allow_html=True)

    def render_performance_charts(self):
        """Render real-time performance charts."""
        st.subheader("📈 Live Performance Charts")
        
        # Chart selection tabs
        tab1, tab2, tab3 = st.tabs(["Lead Trends", "Response Times", "Commission Pipeline"])
        
        with tab1:
            self._render_lead_trends_chart()
            
        with tab2:
            self._render_response_times_chart()
            
        with tab3:
            self._render_commission_pipeline_chart()

    def _render_lead_trends_chart(self):
        """Render live lead trends chart."""
        # Get historical data with live updates
        chart_data = self._get_chart_data("lead_trends", default_data={
            "dates": pd.date_range(start='2024-01-01', periods=30, freq='D'),
            "leads": [5 + i * 0.5 + (i % 7) * 2 for i in range(30)],
            "qualified": [2 + i * 0.3 + (i % 5) * 1 for i in range(30)]
        })
        
        # Create plotly chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=chart_data["dates"],
            y=chart_data["leads"],
            mode='lines+markers',
            name='Total Leads',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=chart_data["dates"],
            y=chart_data["qualified"],
            mode='lines+markers', 
            name='Qualified Leads',
            line=dict(color='#10b981', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Daily Lead Generation Trends",
            xaxis_title="Date",
            yaxis_title="Number of Leads",
            height=400,
            showlegend=True,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True, key="lead_trends_chart")

    def _render_response_times_chart(self):
        """Render live response times chart."""
        chart_data = self._get_chart_data("response_times", default_data={
            "hours": list(range(24)),
            "avg_response_mins": [3 + abs(12 - h) * 0.3 + (h % 3) * 0.5 for h in range(24)]
        })
        
        fig = go.Figure()
        
        # Color coding for response times (green < 5min, yellow < 10min, red >= 10min)
        colors = ['#10b981' if t < 5 else '#f59e0b' if t < 10 else '#ef4444' for t in chart_data["avg_response_mins"]]
        
        fig.add_trace(go.Bar(
            x=[f"{h:02d}:00" for h in chart_data["hours"]],
            y=chart_data["avg_response_mins"],
            marker_color=colors,
            name="Avg Response Time",
            text=[f"{t:.1f}m" for t in chart_data["avg_response_mins"]],
            textposition='auto'
        ))
        
        # Add 5-minute target line
        fig.add_hline(y=5, line_dash="dash", line_color="red", 
                     annotation_text="5-min Target", annotation_position="right")
        
        fig.update_layout(
            title="Average Response Time by Hour",
            xaxis_title="Hour of Day",
            yaxis_title="Response Time (minutes)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True, key="response_times_chart")

    def _render_commission_pipeline_chart(self):
        """Render live commission pipeline chart."""
        chart_data = self._get_chart_data("commission_pipeline", default_data={
            "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "potential": [45000, 52000, 48000, 61000, 58000, 67000],
            "confirmed": [32000, 38000, 35000, 42000, 41000, 48000],
            "paid": [28000, 32000, 31000, 38000, 36000, 42000]
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Potential',
            x=chart_data["months"],
            y=chart_data["potential"],
            marker_color='#fbbf24'
        ))
        
        fig.add_trace(go.Bar(
            name='Confirmed',
            x=chart_data["months"], 
            y=chart_data["confirmed"],
            marker_color='#3b82f6'
        ))
        
        fig.add_trace(go.Bar(
            name='Paid',
            x=chart_data["months"],
            y=chart_data["paid"],
            marker_color='#10b981'
        ))
        
        fig.update_layout(
            title="Monthly Commission Pipeline",
            xaxis_title="Month",
            yaxis_title="Commission Amount ($)",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True, key="commission_pipeline_chart")

    def _get_chart_data(self, chart_type: str, default_data: Dict) -> Dict:
        """Get chart data from session state or cache, with fallback to default."""
        # Check session state first
        if chart_type in st.session_state.metric_history:
            return st.session_state.metric_history[chart_type]
        
        # Try to get from cache
        try:
            cached_data = asyncio.run(self.cache_service.get(f"chart_data:{chart_type}"))
            if cached_data:
                return cached_data
        except Exception as e:
            logger.debug(f"Could not get cached chart data: {e}")
        
        # Return default data
        return default_data

    def render_alerts_panel(self):
        """Render real-time alerts and notifications panel."""
        st.subheader("🚨 Live Alerts & Notifications")
        
        # Get live alerts from session state
        alerts = st.session_state.get("live_alerts", [])
        
        if not alerts:
            st.success("✅ All systems operational - No active alerts")
            return
        
        # Display alerts by priority
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
        warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
        info_alerts = [a for a in alerts if a.get("severity") == "info"]
        
        # Critical alerts
        if critical_alerts:
            st.error("🔴 Critical Alerts")
            for alert in critical_alerts:
                st.error(f"⚠️ {alert.get('message', 'Unknown alert')}")
        
        # Warning alerts
        if warning_alerts:
            st.warning("🟡 Warning Alerts")
            for alert in warning_alerts:
                st.warning(f"⚠️ {alert.get('message', 'Unknown alert')}")
        
        # Info alerts
        if info_alerts:
            with st.expander("ℹ️ Information Alerts", expanded=False):
                for alert in info_alerts:
                    st.info(f"ℹ️ {alert.get('message', 'Unknown alert')}")

    def render_kpi_summary(self):
        """Render live KPI summary with targets and achievements."""
        st.subheader("🎯 Live KPI Dashboard")
        
        # KPI targets and current values
        kpis = [
            {
                "name": "Lead Response Time",
                "current": 3.2,
                "target": 5.0,
                "unit": "min",
                "type": "lower_better",
                "icon": "⚡"
            },
            {
                "name": "Lead Qualification Rate", 
                "current": 36.1,
                "target": 30.0,
                "unit": "%",
                "type": "higher_better",
                "icon": "✅"
            },
            {
                "name": "Commission Conversion",
                "current": 12.8,
                "target": 15.0, 
                "unit": "%",
                "type": "higher_better",
                "icon": "💰"
            },
            {
                "name": "Cache Hit Rate",
                "current": 87.3,
                "target": 80.0,
                "unit": "%",
                "type": "higher_better", 
                "icon": "🚀"
            }
        ]
        
        # Display KPIs in grid
        cols = st.columns(len(kpis))
        
        for i, kpi in enumerate(kpis):
            with cols[i]:
                self._render_kpi_card(kpi)

    def _render_kpi_card(self, kpi: Dict[str, Any]):
        """Render individual KPI card with progress indicator."""
        current = kpi["current"]
        target = kpi["target"]
        unit = kpi["unit"]
        kpi_type = kpi["type"]
        icon = kpi["icon"]
        name = kpi["name"]
        
        # Calculate progress and status
        if kpi_type == "lower_better":
            # For metrics where lower is better (like response time)
            progress = min(100, (target / current) * 100) if current > 0 else 100
            status = "success" if current <= target else "warning" if current <= target * 1.2 else "error"
        else:
            # For metrics where higher is better
            progress = min(100, (current / target) * 100) if target > 0 else 100
            status = "success" if current >= target else "warning" if current >= target * 0.8 else "error"
        
        # Status colors
        status_colors = {
            "success": "#10b981",
            "warning": "#f59e0b", 
            "error": "#ef4444"
        }
        
        # Render KPI card
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid {status_colors[status]};
            text-align: center;
            min-height: 120px;
        ">
            <h4 style="margin: 0; color: #1f2937;">{icon} {name}</h4>
            <h2 style="margin: 0.5rem 0; color: {status_colors[status]}; font-weight: bold;">
                {current}{unit}
            </h2>
            <p style="margin: 0; color: #6b7280;">Target: {target}{unit}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress bar
        st.progress(progress / 100)

    def update_metric(self, metric_key: str, value: Any, trend: Optional[str] = None):
        """Update a specific metric in session state."""
        if "live_metrics" not in st.session_state:
            st.session_state.live_metrics = {}
            
        st.session_state.live_metrics[metric_key] = {
            "value": value,
            "formatted_value": self._format_metric_value(metric_key, value),
            "trend_indicator": trend or self._calculate_trend(metric_key, value),
            "last_updated": datetime.now().isoformat()
        }
        
        st.session_state.metrics_last_update = datetime.now().strftime("%H:%M:%S")

    def _format_metric_value(self, metric_key: str, value: Any) -> str:
        """Format metric value for display."""
        if isinstance(value, (int, float)):
            if "commission" in metric_key.lower():
                return f"${value:,.0f}"
            elif "rate" in metric_key.lower() or "percent" in metric_key.lower():
                return f"{value:.1f}%"
            elif "time" in metric_key.lower():
                return f"{value:.1f}min" 
            else:
                return f"{value:,}"
        return str(value)

    def _calculate_trend(self, metric_key: str, current_value: Any) -> str:
        """Calculate trend indicator for metric."""
        # This would normally compare with historical data
        # For demo, return sample trends
        trend_map = {
            "total_leads": "↗️ 12%",
            "qualified_leads": "↗️ 18%", 
            "active_deals": "↗️ 5%",
            "monthly_commission": "↗️ 22%"
        }
        
        return trend_map.get(metric_key, "→ Stable")

def render_live_metrics_dashboard():
    """Convenience function to render complete live metrics dashboard.""" 
    metrics_manager = LiveMetricsManager()
    
    # Render all components
    metrics_manager.render_hero_metrics()
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        metrics_manager.render_performance_charts()
        
    with col2:
        metrics_manager.render_alerts_panel()
        
    st.markdown("---")
    
    metrics_manager.render_kpi_summary()

def update_live_metric(metric_key: str, value: Any, trend: Optional[str] = None):
    """Convenience function to update a live metric."""
    metrics_manager = LiveMetricsManager()
    metrics_manager.update_metric(metric_key, value, trend)