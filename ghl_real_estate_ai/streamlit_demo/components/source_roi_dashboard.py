"""
Lead Source ROI Dashboard

Streamlit dashboard for visualizing lead source performance, ROI metrics,
and optimization recommendations. Enables data-driven budget allocation decisions.

Features:
- Top 10 sources by conversion rate
- Top 10 sources by revenue
- Cost efficiency comparison
- Trend analysis over time
- Budget optimization recommendations
"""

import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Mock data for development/demo mode
DEMO_MODE = True


class SourceROIDashboard:
    """Dashboard for lead source ROI analytics and optimization."""

    def __init__(self):
        """Initialize dashboard."""
        self.demo_mode = DEMO_MODE

    def render(self) -> None:
        """Render the complete dashboard."""
        st.header("📊 Lead Source ROI Analytics")
        st.markdown("Track and optimize marketing spend across lead sources")

        # Time range selector
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            time_range = st.selectbox(
                "Time Range",
                options=[7, 14, 30, 60, 90],
                index=2,
                format_func=lambda x: f"Last {x} days",
            )

        with col2:
            st.metric(
                "Total Budget",
                "$45,000",
                delta="$5,000",
            )

        with col3:
            st.metric(
                "Total ROI",
                "245%",
                delta="18%",
            )

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "🏆 Top Performers",
                "💰 ROI Analysis",
                "📈 Trends",
                "🎯 Recommendations",
            ]
        )

        with tab1:
            self._render_top_performers(time_range)

        with tab2:
            self._render_roi_analysis(time_range)

        with tab3:
            self._render_trends(time_range)

        with tab4:
            self._render_recommendations(time_range)

    def _render_top_performers(self, days: int) -> None:
        """Render top performing sources view."""
        st.subheader("Top Performing Lead Sources")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🥇 By Conversion Rate")
            top_by_conversion = self._get_top_sources_by_conversion(days)
            self._render_source_table(top_by_conversion, "conversion_rate")

        with col2:
            st.markdown("### 💎 By Revenue")
            top_by_revenue = self._get_top_sources_by_revenue(days)
            self._render_source_table(top_by_revenue, "revenue")

        # Conversion rate chart
        st.markdown("### Conversion Rate Comparison")
        fig_conversion = self._create_conversion_chart(top_by_conversion)
        st.plotly_chart(fig_conversion, use_container_width=True)

    def _render_roi_analysis(self, days: int) -> None:
        """Render ROI analysis view."""
        st.subheader("Return on Investment Analysis")

        # ROI overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Avg ROI", "245%", delta="18%")
        with col2:
            st.metric("Avg Cost/Lead", "$42", delta="-$5")
        with col3:
            st.metric("Avg Cost/Close", "$1,850", delta="-$200")
        with col4:
            st.metric("Total Profit", "$65,250", delta="$8,400")

        # ROI bubble chart
        st.markdown("### ROI vs Volume Analysis")
        roi_data = self._get_roi_data(days)
        fig_bubble = self._create_roi_bubble_chart(roi_data)
        st.plotly_chart(fig_bubble, use_container_width=True)

        # Cost efficiency comparison
        st.markdown("### Cost Efficiency Metrics")
        col1, col2 = st.columns(2)

        with col1:
            fig_cost_per_lead = self._create_cost_per_lead_chart(roi_data)
            st.plotly_chart(fig_cost_per_lead, use_container_width=True)

        with col2:
            fig_cost_per_close = self._create_cost_per_close_chart(roi_data)
            st.plotly_chart(fig_cost_per_close, use_container_width=True)

    def _render_trends(self, days: int) -> None:
        """Render trend analysis view."""
        st.subheader("Performance Trends")

        # Source selector
        sources = self._get_all_sources()
        selected_sources = st.multiselect(
            "Select sources to compare",
            options=sources,
            default=sources[:3] if len(sources) >= 3 else sources,
        )

        if not selected_sources:
            st.warning("Please select at least one source to view trends")
            return

        # Trend charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Revenue Trend")
            fig_revenue = self._create_revenue_trend_chart(selected_sources, days)
            st.plotly_chart(fig_revenue, use_container_width=True)

        with col2:
            st.markdown("### Conversion Rate Trend")
            fig_conversion = self._create_conversion_trend_chart(selected_sources, days)
            st.plotly_chart(fig_conversion, use_container_width=True)

        # ROI trend
        st.markdown("### ROI Trend")
        fig_roi = self._create_roi_trend_chart(selected_sources, days)
        st.plotly_chart(fig_roi, use_container_width=True)

    def _render_recommendations(self, days: int) -> None:
        """Render optimization recommendations."""
        st.subheader("🎯 Budget Optimization Recommendations")

        recommendations = self._get_recommendations(days)

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Recommended Budget Shift",
                f"${recommendations['recommended_shift']:,.0f}",
                delta=f"{recommendations['shift_percent']}%",
            )

        with col2:
            st.metric(
                "Projected Revenue Impact",
                f"+${recommendations['projected_impact']:,.0f}",
            )

        with col3:
            st.metric(
                "Potential ROI Improvement",
                f"+{recommendations['roi_improvement']:.1f}%",
            )

        # Top performers to invest in
        st.markdown("### ✅ Increase Budget")
        st.success("Sources with high ROI - Recommended for increased investment")

        top_df = pd.DataFrame(recommendations["top_performers"])
        st.dataframe(
            top_df,
            use_container_width=True,
            hide_index=True,
        )

        # Underperformers to reduce
        st.markdown("### ⚠️ Reduce or Pause")
        st.warning("Sources with low ROI - Consider reducing investment")

        under_df = pd.DataFrame(recommendations["underperformers"])
        st.dataframe(
            under_df,
            use_container_width=True,
            hide_index=True,
        )

        # Specific recommendations
        st.markdown("### 💡 Action Items")

        for i, rec in enumerate(recommendations["action_items"], 1):
            st.markdown(f"{i}. **{rec['title']}**")
            st.markdown(f"   {rec['description']}")
            if rec.get("impact"):
                st.markdown(f"   *Expected Impact: {rec['impact']}*")
            st.markdown("")

    # ── Data Methods ──────────────────────────────────────────────────────

    def _get_top_sources_by_conversion(self, days: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top sources by conversion rate."""
        # Mock data for demo
        sources = [
            {"name": "Facebook Ads", "conversion_rate": 12.5, "contacts": 450, "closed": 56, "revenue": 4200000},
            {"name": "Google Ads", "conversion_rate": 10.8, "contacts": 380, "closed": 41, "revenue": 3280000},
            {"name": "Referral", "conversion_rate": 18.2, "contacts": 220, "closed": 40, "revenue": 3600000},
            {"name": "Zillow", "conversion_rate": 8.5, "contacts": 520, "closed": 44, "revenue": 3520000},
            {"name": "Realtor.com", "conversion_rate": 7.2, "contacts": 340, "closed": 24, "revenue": 1920000},
            {"name": "Instagram", "conversion_rate": 9.5, "contacts": 280, "closed": 27, "revenue": 2160000},
            {"name": "LinkedIn", "conversion_rate": 15.3, "contacts": 150, "closed": 23, "revenue": 2070000},
            {"name": "Open House", "conversion_rate": 14.0, "contacts": 180, "closed": 25, "revenue": 2250000},
            {"name": "Email Campaign", "conversion_rate": 6.8, "contacts": 420, "closed": 29, "revenue": 2320000},
            {"name": "Direct Mail", "conversion_rate": 5.2, "contacts": 300, "closed": 16, "revenue": 1280000},
        ]
        return sorted(sources, key=lambda x: x["conversion_rate"], reverse=True)[:limit]

    def _get_top_sources_by_revenue(self, days: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top sources by total revenue."""
        sources = self._get_top_sources_by_conversion(days, limit=20)
        return sorted(sources, key=lambda x: x["revenue"], reverse=True)[:limit]

    def _get_roi_data(self, days: int) -> List[Dict[str, Any]]:
        """Get ROI data for all sources."""
        # Mock data
        return [
            {"name": "Facebook Ads", "roi": 280, "cost": 12000, "revenue": 45600, "contacts": 450, "closed": 56},
            {"name": "Google Ads", "roi": 220, "cost": 15000, "revenue": 48000, "contacts": 380, "closed": 41},
            {"name": "Referral", "roi": 450, "cost": 5000, "revenue": 27500, "contacts": 220, "closed": 40},
            {"name": "Zillow", "roi": 180, "cost": 8000, "revenue": 22400, "contacts": 520, "closed": 44},
            {"name": "Realtor.com", "roi": 95, "cost": 6000, "revenue": 11700, "contacts": 340, "closed": 24},
            {"name": "Instagram", "roi": 240, "cost": 4500, "revenue": 15300, "contacts": 280, "closed": 27},
            {"name": "LinkedIn", "roi": 310, "cost": 3000, "revenue": 12300, "contacts": 150, "closed": 23},
            {"name": "Open House", "roi": 380, "cost": 2500, "revenue": 12000, "contacts": 180, "closed": 25},
        ]

    def _get_all_sources(self) -> List[str]:
        """Get list of all source names."""
        return [
            "Facebook Ads",
            "Google Ads",
            "Referral",
            "Zillow",
            "Realtor.com",
            "Instagram",
            "LinkedIn",
            "Open House",
        ]

    def _get_recommendations(self, days: int) -> Dict[str, Any]:
        """Get optimization recommendations."""
        return {
            "recommended_shift": 9000,
            "shift_percent": 20,
            "projected_impact": 12500,
            "roi_improvement": 15.8,
            "top_performers": [
                {
                    "Source": "Referral",
                    "Current Budget": "$5,000",
                    "ROI": "450%",
                    "Recommendation": "Increase to $8,000",
                },
                {
                    "Source": "Open House",
                    "Current Budget": "$2,500",
                    "ROI": "380%",
                    "Recommendation": "Increase to $4,000",
                },
                {
                    "Source": "LinkedIn",
                    "Current Budget": "$3,000",
                    "ROI": "310%",
                    "Recommendation": "Increase to $4,500",
                },
            ],
            "underperformers": [
                {
                    "Source": "Realtor.com",
                    "Current Budget": "$6,000",
                    "ROI": "95%",
                    "Recommendation": "Reduce to $3,000",
                },
                {"Source": "Direct Mail", "Current Budget": "$4,000", "ROI": "65%", "Recommendation": "Pause campaign"},
            ],
            "action_items": [
                {
                    "title": "Shift $3,000 from Realtor.com to Referral program",
                    "description": "Realtor.com ROI is 95% vs Referral at 450%. This shift could generate $13,500 additional revenue.",
                    "impact": "+$10,500 projected revenue",
                },
                {
                    "title": "Scale LinkedIn campaigns by 50%",
                    "description": "LinkedIn has 310% ROI with lowest cost per qualified lead ($35 vs $58 average).",
                    "impact": "+$4,650 projected revenue",
                },
                {
                    "title": "Pause Direct Mail and reallocate to Open House events",
                    "description": "Direct Mail ROI is 65% (below breakeven). Open House ROI is 380%.",
                    "impact": "+$11,200 projected revenue",
                },
                {
                    "title": "Invest in referral incentive program",
                    "description": "Referrals show highest ROI (450%) and conversion rate (18.2%). Consider increasing referral bonuses.",
                    "impact": "+$8,000 projected revenue",
                },
            ],
        }

    # ── Chart Methods ─────────────────────────────────────────────────────

    def _render_source_table(self, data: List[Dict[str, Any]], highlight_col: str) -> None:
        """Render source performance table."""
        df = pd.DataFrame(data)

        # Format columns
        df_display = df.copy()
        df_display["conversion_rate"] = df_display["conversion_rate"].apply(lambda x: f"{x:.1f}%")
        df_display["revenue"] = df_display["revenue"].apply(lambda x: f"${x:,.0f}")

        df_display = df_display.rename(
            columns={
                "name": "Source",
                "conversion_rate": "Conv. Rate",
                "contacts": "Leads",
                "closed": "Closed",
                "revenue": "Revenue",
            }
        )

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
        )

    def _create_conversion_chart(self, data: List[Dict[str, Any]]) -> go.Figure:
        """Create conversion rate bar chart."""
        df = pd.DataFrame(data)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df["name"],
                y=df["conversion_rate"],
                text=df["conversion_rate"].apply(lambda x: f"{x:.1f}%"),
                textposition="outside",
                marker=dict(
                    color=df["conversion_rate"],
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title="Rate %"),
                ),
            )
        )

        fig.update_layout(
            title="Conversion Rate by Source",
            xaxis_title="Lead Source",
            yaxis_title="Conversion Rate (%)",
            height=400,
            showlegend=False,
        )

        return fig

    def _create_roi_bubble_chart(self, data: List[Dict[str, Any]]) -> go.Figure:
        """Create ROI bubble chart."""
        df = pd.DataFrame(data)

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["cost"],
                y=df["roi"],
                mode="markers+text",
                marker=dict(
                    size=df["closed"] * 5,  # Bubble size = closed deals
                    color=df["roi"],
                    colorscale="RdYlGn",
                    showscale=True,
                    colorbar=dict(title="ROI %"),
                    line=dict(width=2, color="white"),
                ),
                text=df["name"],
                textposition="top center",
                hovertemplate="<b>%{text}</b><br>"
                + "Cost: $%{x:,.0f}<br>"
                + "ROI: %{y:.0f}%<br>"
                + "Closed Deals: %{marker.size}<extra></extra>",
            )
        )

        fig.update_layout(
            title="ROI vs Marketing Cost (bubble size = closed deals)",
            xaxis_title="Marketing Cost ($)",
            yaxis_title="ROI (%)",
            height=500,
            hovermode="closest",
        )

        return fig

    def _create_cost_per_lead_chart(self, data: List[Dict[str, Any]]) -> go.Figure:
        """Create cost per lead comparison chart."""
        df = pd.DataFrame(data)
        df["cost_per_lead"] = df["cost"] / df["contacts"]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df["name"],
                y=df["cost_per_lead"],
                text=df["cost_per_lead"].apply(lambda x: f"${x:.0f}"),
                textposition="outside",
                marker=dict(color="lightblue"),
            )
        )

        fig.update_layout(
            title="Cost per Lead",
            xaxis_title="Source",
            yaxis_title="Cost ($)",
            height=350,
            showlegend=False,
        )

        return fig

    def _create_cost_per_close_chart(self, data: List[Dict[str, Any]]) -> go.Figure:
        """Create cost per close comparison chart."""
        df = pd.DataFrame(data)
        df["cost_per_close"] = df["cost"] / df["closed"]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df["name"],
                y=df["cost_per_close"],
                text=df["cost_per_close"].apply(lambda x: f"${x:.0f}"),
                textposition="outside",
                marker=dict(color="lightcoral"),
            )
        )

        fig.update_layout(
            title="Cost per Close",
            xaxis_title="Source",
            yaxis_title="Cost ($)",
            height=350,
            showlegend=False,
        )

        return fig

    def _create_revenue_trend_chart(self, sources: List[str], days: int) -> go.Figure:
        """Create revenue trend line chart."""
        # Generate mock trend data
        dates = pd.date_range(end=datetime.now(), periods=days, freq="D")

        fig = go.Figure()

        for source in sources:
            # Mock revenue data with trend
            base = np.random.randint(1000, 5000)
            trend = np.cumsum(np.random.randn(days) * 200 + base / days)
            trend = np.maximum(trend, 0)  # Ensure positive

            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=trend,
                    mode="lines",
                    name=source,
                    line=dict(width=2),
                )
            )

        fig.update_layout(
            title="Revenue Trend",
            xaxis_title="Date",
            yaxis_title="Revenue ($)",
            height=400,
            hovermode="x unified",
        )

        return fig

    def _create_conversion_trend_chart(self, sources: List[str], days: int) -> go.Figure:
        """Create conversion rate trend chart."""
        dates = pd.date_range(end=datetime.now(), periods=days, freq="D")

        fig = go.Figure()

        for source in sources:
            # Mock conversion rate data
            base_rate = np.random.uniform(5, 15)
            rates = base_rate + np.cumsum(np.random.randn(days) * 0.3)
            rates = np.clip(rates, 0, 100)  # Keep in valid range

            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=rates,
                    mode="lines",
                    name=source,
                    line=dict(width=2),
                )
            )

        fig.update_layout(
            title="Conversion Rate Trend",
            xaxis_title="Date",
            yaxis_title="Conversion Rate (%)",
            height=400,
            hovermode="x unified",
        )

        return fig

    def _create_roi_trend_chart(self, sources: List[str], days: int) -> go.Figure:
        """Create ROI trend chart."""
        dates = pd.date_range(end=datetime.now(), periods=days, freq="D")

        fig = go.Figure()

        for source in sources:
            # Mock ROI data
            base_roi = np.random.uniform(100, 300)
            roi = base_roi + np.cumsum(np.random.randn(days) * 5)
            roi = np.maximum(roi, 0)  # Ensure positive

            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=roi,
                    mode="lines",
                    name=source,
                    line=dict(width=2),
                    fill="tonexty" if source != sources[0] else None,
                )
            )

        fig.update_layout(
            title="ROI Trend",
            xaxis_title="Date",
            yaxis_title="ROI (%)",
            height=400,
            hovermode="x unified",
        )

        return fig


def render_source_roi_dashboard() -> None:
    """Main entry point for the dashboard."""
    dashboard = SourceROIDashboard()
    dashboard.render()


if __name__ == "__main__":
    render_source_roi_dashboard()
