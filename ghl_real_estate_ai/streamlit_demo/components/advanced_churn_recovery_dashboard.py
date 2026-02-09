"""
Advanced Churn Recovery Dashboard - Executive KPI Center

Executive-grade dashboard for comprehensive churn recovery monitoring and management.
Provides real-time insights into churn risk, recovery campaigns, and ROI metrics
across multi-market operations.

Features:
- Executive KPI Cards (churn rate, recovery rate, CLV impact)
- Multi-Market Overview Grid (5 markets performance)
- Real-Time Recovery Pipeline (funnel visualization)
- Campaign Performance Matrix (email, SMS, phone effectiveness)
- Geographic Heat Map (churn intensity by region)
- ROI Calculator (CLV-based returns)

Author: EnterpriseHub AI
Last Updated: 2026-01-18
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure page if running standalone
if __name__ == "__main__":
    st.set_page_config(
        page_title="Advanced Churn Recovery Dashboard", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded"
    )

# Professional styling - Executive Grade
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Executive Theme */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Executive KPI Cards */
    .kpi-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid rgba(220, 224, 230, 0.5);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        backdrop-filter: blur(10px);
        margin: 8px 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
    }
    
    .kpi-title {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 8px;
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 8px 0;
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .kpi-subtitle {
        font-size: 0.85rem;
        opacity: 0.7;
        font-weight: 500;
    }
    
    /* Market Grid */
    .market-grid {
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 12px;
        margin: 16px 0;
        border: 1px solid rgba(220, 224, 230, 0.5);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    }
    
    /* Recovery Pipeline */
    .pipeline-stage {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 16px;
        border-radius: 8px;
        margin: 4px 0;
        color: white;
        font-weight: 600;
    }
    
    /* Campaign Performance */
    .campaign-channel {
        background: rgba(255, 255, 255, 0.9);
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid;
    }
    
    /* Section Headers */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.5rem;
        margin: 32px 0 16px 0;
        color: #1f2937;
    }
    
    /* Alert Styles */
    .alert-critical {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #ef4444;
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .alert-success {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border-left: 4px solid #22c55e;
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


@dataclass
class MarketMetrics:
    """Market performance metrics for dashboard"""

    name: str
    churn_rate: float
    recovery_rate: float
    active_campaigns: int
    clv_impact: float
    leads_at_risk: int
    recovered_this_month: int


@dataclass
class ChurnKPIs:
    """Executive KPI metrics"""

    overall_churn_rate: float
    recovery_rate: float
    clv_recovered: float
    active_interventions: int
    at_risk_leads: int
    success_rate: float


@st.cache_data(ttl=300)
def load_churn_metrics() -> ChurnKPIs:
    """Load executive churn metrics with 5-minute cache"""
    # Simulate realistic executive metrics
    base_churn = 0.08  # 8% base churn rate
    seasonal_factor = 1.2 if datetime.now().month in [11, 12, 1] else 1.0

    return ChurnKPIs(
        overall_churn_rate=base_churn * seasonal_factor,
        recovery_rate=0.67,  # 67% recovery rate
        clv_recovered=234750.0,
        active_interventions=42,
        at_risk_leads=127,
        success_rate=0.73,
    )


@st.cache_data(ttl=300)
def load_market_data() -> List[MarketMetrics]:
    """Load multi-market performance data"""
    markets = [
        MarketMetrics("Austin Metro", 0.065, 0.72, 18, 87500, 34, 16),
        MarketMetrics("San Antonio", 0.082, 0.68, 14, 62300, 28, 12),
        MarketMetrics("Houston West", 0.071, 0.74, 21, 94200, 41, 19),
        MarketMetrics("Dallas North", 0.089, 0.61, 16, 71800, 38, 14),
        MarketMetrics("Fort Worth", 0.076, 0.69, 12, 55400, 22, 11),
    ]
    return markets


@st.cache_data(ttl=300)
def generate_recovery_pipeline_data() -> pd.DataFrame:
    """Generate recovery pipeline funnel data"""
    return pd.DataFrame(
        {
            "Stage": ["Identified Risk", "Intervention Triggered", "Engaged", "Responded", "Recovered"],
            "Count": [127, 98, 76, 52, 34],
            "Conversion_Rate": [100, 77.2, 77.6, 68.4, 65.4],
        }
    )


@st.cache_data(ttl=300)
def generate_campaign_performance() -> pd.DataFrame:
    """Generate campaign performance by channel"""
    return pd.DataFrame(
        {
            "Channel": [
                "Email Sequence",
                "SMS Urgent",
                "Phone Callback",
                "Property Alert",
                "Market Update",
                "Consultation Offer",
            ],
            "Sent": [145, 89, 67, 112, 98, 43],
            "Opened": [98, 76, 67, 87, 72, 38],
            "Responded": [34, 28, 45, 31, 19, 24],
            "Converted": [18, 15, 32, 17, 8, 19],
            "Cost_Per_Lead": [12.50, 8.75, 45.00, 15.20, 11.80, 67.50],
            "ROI": [340, 285, 520, 275, 145, 890],
        }
    )


@st.cache_data(ttl=300)
def generate_geographic_data() -> pd.DataFrame:
    """Generate geographic churn intensity data"""
    return pd.DataFrame(
        {
            "Market": ["Austin Metro", "San Antonio", "Houston West", "Dallas North", "Fort Worth"],
            "Latitude": [30.2672, 29.4241, 29.7604, 32.7767, 32.7555],
            "Longitude": [-97.7431, -98.4936, -95.3698, -96.7970, -97.3308],
            "Churn_Rate": [6.5, 8.2, 7.1, 8.9, 7.6],
            "Recovery_Rate": [72, 68, 74, 61, 69],
            "At_Risk_Count": [34, 28, 41, 38, 22],
        }
    )


def render_executive_kpis(kpis: ChurnKPIs):
    """Render executive KPI cards"""
    st.markdown('<div class="section-header">🎯 Executive KPIs</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        color = (
            "#ef4444" if kpis.overall_churn_rate > 0.09 else "#f59e0b" if kpis.overall_churn_rate > 0.07 else "#22c55e"
        )
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: {color};">Overall Churn Rate</div>
            <div class="kpi-value" style="color: {color};">{kpis.overall_churn_rate:.1%}</div>
            <div class="kpi-subtitle">vs 8.5% target</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        color = "#22c55e" if kpis.recovery_rate > 0.65 else "#f59e0b"
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: {color};">Recovery Rate</div>
            <div class="kpi-value" style="color: {color};">{kpis.recovery_rate:.1%}</div>
            <div class="kpi-subtitle">+12% vs Q3</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: #1f77b4;">CLV Recovered</div>
            <div class="kpi-value" style="color: #1f77b4;">${kpis.clv_recovered:,.0f}</div>
            <div class="kpi-subtitle">This month</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: #8b5cf6;">Active Interventions</div>
            <div class="kpi-value" style="color: #8b5cf6;">{kpis.active_interventions}</div>
            <div class="kpi-subtitle">Running campaigns</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col5:
        color = "#ef4444" if kpis.at_risk_leads > 100 else "#f59e0b"
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: {color};">At-Risk Leads</div>
            <div class="kpi-value" style="color: {color};">{kpis.at_risk_leads}</div>
            <div class="kpi-subtitle">Require attention</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col6:
        color = "#22c55e" if kpis.success_rate > 0.70 else "#f59e0b"
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: {color};">Success Rate</div>
            <div class="kpi-value" style="color: {color};">{kpis.success_rate:.1%}</div>
            <div class="kpi-subtitle">Campaign effectiveness</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_market_overview(markets: List[MarketMetrics]):
    """Render multi-market overview grid"""
    st.markdown('<div class="section-header">🗺️ Multi-Market Overview</div>', unsafe_allow_html=True)

    # Create market comparison chart
    market_df = pd.DataFrame(
        [
            {
                "Market": market.name,
                "Churn Rate": market.churn_rate,
                "Recovery Rate": market.recovery_rate,
                "CLV Impact": market.clv_impact,
                "At Risk": market.leads_at_risk,
                "Recovered": market.recovered_this_month,
                "Campaigns": market.active_campaigns,
            }
            for market in markets
        ]
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        # Market performance matrix
        fig = px.scatter(
            market_df,
            x="Churn Rate",
            y="Recovery Rate",
            size="CLV Impact",
            color="At Risk",
            hover_data=["Market", "Campaigns"],
            title="Market Performance Matrix",
            color_continuous_scale="RdYlGn_r",
        )

        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)", plot_bgcolor="rgba(255,255,255,0.95)", font_family="Inter"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Market ranking
        st.markdown("**Market Rankings**")

        # Sort by composite score (recovery rate / churn rate)
        market_df["Score"] = market_df["Recovery Rate"] / market_df["Churn Rate"]
        market_df = market_df.sort_values("Score", ascending=False)

        for idx, row in market_df.iterrows():
            score_color = "#22c55e" if row["Score"] > 9 else "#f59e0b" if row["Score"] > 8 else "#ef4444"
            st.markdown(
                f"""
            <div style="background: rgba(255,255,255,0.9); padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid {score_color};">
                <div style="font-weight: 600;">{row["Market"]}</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">
                    Score: {row["Score"]:.1f} | At Risk: {row["At Risk"]} | Recovery: {row["Recovery Rate"]:.1%}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_recovery_pipeline(pipeline_data: pd.DataFrame):
    """Render real-time recovery pipeline"""
    st.markdown('<div class="section-header">⚡ Real-Time Recovery Pipeline</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Funnel chart
        fig = go.Figure(
            go.Funnel(
                y=pipeline_data["Stage"],
                x=pipeline_data["Count"],
                textinfo="value+percent initial",
                marker=dict(color=["#ef4444", "#f59e0b", "#1f77b4", "#8b5cf6", "#22c55e"]),
            )
        )

        fig.update_layout(
            title="Recovery Funnel - Real-time",
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Stage details
        st.markdown("**Pipeline Stages**")

        for _, row in pipeline_data.iterrows():
            stage_color = (
                "#22c55e" if row["Conversion_Rate"] > 70 else "#f59e0b" if row["Conversion_Rate"] > 60 else "#ef4444"
            )

            st.markdown(
                f"""
            <div class="pipeline-stage" style="background: linear-gradient(135deg, {stage_color}20 0%, {stage_color}40 100%); color: {stage_color}; border-left: 4px solid {stage_color};">
                <div style="font-weight: 700;">{row["Stage"]}</div>
                <div style="font-size: 1.5rem; margin: 4px 0;">{row["Count"]}</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">Conv: {row["Conversion_Rate"]:.1f}%</div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_campaign_performance(campaign_data: pd.DataFrame):
    """Render campaign performance matrix"""
    st.markdown('<div class="section-header">📊 Campaign Performance Matrix</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # ROI by channel
        fig = px.bar(
            campaign_data,
            x="Channel",
            y="ROI",
            color="ROI",
            color_continuous_scale="RdYlGn",
            title="ROI by Channel (%)",
        )

        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
            xaxis_tickangle=45,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Conversion funnel
        campaign_data["Open_Rate"] = (campaign_data["Opened"] / campaign_data["Sent"]) * 100
        campaign_data["Response_Rate"] = (campaign_data["Responded"] / campaign_data["Opened"]) * 100
        campaign_data["Conversion_Rate"] = (campaign_data["Converted"] / campaign_data["Responded"]) * 100

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=campaign_data["Channel"],
                y=campaign_data["Open_Rate"],
                mode="lines+markers",
                name="Open Rate",
                line=dict(color="#1f77b4"),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=campaign_data["Channel"],
                y=campaign_data["Response_Rate"],
                mode="lines+markers",
                name="Response Rate",
                line=dict(color="#ff7f0e"),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=campaign_data["Channel"],
                y=campaign_data["Conversion_Rate"],
                mode="lines+markers",
                name="Conversion Rate",
                line=dict(color="#2ca02c"),
            )
        )

        fig.update_layout(
            title="Conversion Rates by Channel (%)",
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
            xaxis_tickangle=45,
            yaxis_title="Rate (%)",
        )

        st.plotly_chart(fig, use_container_width=True)

    # Channel performance cards
    st.markdown("**Channel Effectiveness**")

    cols = st.columns(3)
    for idx, row in campaign_data.iterrows():
        col_idx = idx % 3

        roi_color = "#22c55e" if row["ROI"] > 400 else "#f59e0b" if row["ROI"] > 200 else "#ef4444"

        with cols[col_idx]:
            st.markdown(
                f"""
            <div class="campaign-channel" style="border-left-color: {roi_color};">
                <div style="font-weight: 600; color: {roi_color};">{row["Channel"]}</div>
                <div style="font-size: 1.2rem; margin: 4px 0;">ROI: {row["ROI"]}%</div>
                <div style="font-size: 0.8rem; opacity: 0.7;">
                    Cost/Lead: ${row["Cost_Per_Lead"]:.2f} | Converted: {row["Converted"]}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_geographic_heatmap(geo_data: pd.DataFrame):
    """Render geographic churn intensity heat map"""
    st.markdown('<div class="section-header">🌍 Geographic Churn Heat Map</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Geographic scatter plot
        fig = px.scatter_mapbox(
            geo_data,
            lat="Latitude",
            lon="Longitude",
            size="At_Risk_Count",
            color="Churn_Rate",
            hover_name="Market",
            hover_data=["Recovery_Rate", "At_Risk_Count"],
            color_continuous_scale="RdYlGn_r",
            size_max=30,
            zoom=6,
            title="Churn Intensity by Market",
        )

        fig.update_layout(mapbox_style="open-street-map", paper_bgcolor="rgba(255,255,255,0.95)", font_family="Inter")

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Geographic insights
        st.markdown("**Geographic Insights**")

        highest_churn = geo_data.loc[geo_data["Churn_Rate"].idxmax()]
        best_recovery = geo_data.loc[geo_data["Recovery_Rate"].idxmax()]
        most_at_risk = geo_data.loc[geo_data["At_Risk_Count"].idxmax()]

        st.markdown(
            f"""
        <div class="alert-critical">
            <strong>⚠️ Highest Churn</strong><br>
            {highest_churn["Market"]}: {highest_churn["Churn_Rate"]:.1f}%<br>
            <em>{highest_churn["At_Risk_Count"]} leads at risk</em>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div class="alert-success">
            <strong>✅ Best Recovery</strong><br>
            {best_recovery["Market"]}: {best_recovery["Recovery_Rate"]:.0f}%<br>
            <em>Model for other markets</em>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div class="alert-warning">
            <strong>📍 Priority Focus</strong><br>
            {most_at_risk["Market"]}: {most_at_risk["At_Risk_Count"]} at-risk leads<br>
            <em>Immediate intervention needed</em>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_roi_insights():
    """Render ROI calculator insights"""
    st.markdown('<div class="section-header">💰 ROI Impact Analysis</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**CLV Recovery Projections**")

        # Recovery scenario analysis
        scenarios = {
            "Current": {"recovery_rate": 0.67, "clv_avg": 12500},
            "Optimized": {"recovery_rate": 0.75, "clv_avg": 12500},
            "Best Case": {"recovery_rate": 0.82, "clv_avg": 12500},
        }

        at_risk = 127
        results = []

        for scenario, params in scenarios.items():
            recovered = at_risk * params["recovery_rate"]
            clv_impact = recovered * params["clv_avg"]
            results.append(
                {
                    "Scenario": scenario,
                    "Leads_Recovered": recovered,
                    "CLV_Impact": clv_impact,
                    "Monthly_ROI": clv_impact / 10000,  # Assume $10k monthly cost
                }
            )

        results_df = pd.DataFrame(results)

        fig = px.bar(
            results_df,
            x="Scenario",
            y="CLV_Impact",
            title="CLV Recovery by Scenario",
            color="CLV_Impact",
            color_continuous_scale="Blues",
        )

        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)", plot_bgcolor="rgba(255,255,255,0.95)", font_family="Inter"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Investment Recommendations**")

        # Investment priority matrix
        investments = [
            {"Area": "Email Automation", "Cost": 2500, "Impact": 8, "ROI": 320},
            {"Area": "SMS Platform", "Cost": 1200, "Impact": 6, "ROI": 285},
            {"Area": "Phone System", "Cost": 4500, "Impact": 9, "ROI": 520},
            {"Area": "AI Personalization", "Cost": 8000, "Impact": 7, "ROI": 245},
            {"Area": "Analytics Dashboard", "Cost": 3200, "Impact": 5, "ROI": 180},
        ]

        invest_df = pd.DataFrame(investments)

        # Priority score = Impact / (Cost / 1000)
        invest_df["Priority_Score"] = invest_df["Impact"] / (invest_df["Cost"] / 1000)
        invest_df = invest_df.sort_values("Priority_Score", ascending=False)

        for _, row in invest_df.iterrows():
            priority_color = (
                "#22c55e" if row["Priority_Score"] > 2 else "#f59e0b" if row["Priority_Score"] > 1.5 else "#ef4444"
            )

            st.markdown(
                f"""
            <div style="background: rgba(255,255,255,0.9); padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid {priority_color};">
                <div style="font-weight: 600;">{row["Area"]}</div>
                <div style="font-size: 0.9rem; margin: 4px 0;">
                    Cost: ${row["Cost"]:,} | ROI: {row["ROI"]}%
                </div>
                <div style="font-size: 0.8rem; opacity: 0.7; color: {priority_color};">
                    Priority Score: {row["Priority_Score"]:.1f}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_advanced_churn_recovery_dashboard():
    """Main function to render the complete dashboard"""

    # Header
    st.markdown("""
    # 🛡️ Advanced Churn Recovery Dashboard
    **Executive Command Center for Lead Recovery Operations**
    
    Real-time monitoring and management of churn recovery across all markets.
    """)

    # Sidebar controls
    with st.sidebar:
        st.markdown("### Dashboard Controls")

        auto_refresh = st.checkbox("Auto Refresh (30s)", value=False)
        time_range = st.selectbox(
            "Time Range", ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last Quarter"], index=1
        )

        market_filter = st.multiselect(
            "Market Filter",
            ["Austin Metro", "San Antonio", "Houston West", "Dallas North", "Fort Worth"],
            default=["Austin Metro", "San Antonio", "Houston West", "Dallas North", "Fort Worth"],
        )

        if auto_refresh:
            st.rerun()

    # Load data
    kpis = load_churn_metrics()
    markets = [m for m in load_market_data() if m.name in market_filter]
    pipeline_data = generate_recovery_pipeline_data()
    campaign_data = generate_campaign_performance()
    geo_data = generate_geographic_data()
    geo_data = geo_data[geo_data["Market"].isin(market_filter)]

    # Render dashboard sections
    render_executive_kpis(kpis)

    st.markdown("---")

    render_market_overview(markets)

    st.markdown("---")

    render_recovery_pipeline(pipeline_data)

    st.markdown("---")

    render_campaign_performance(campaign_data)

    st.markdown("---")

    render_geographic_heatmap(geo_data)

    st.markdown("---")

    render_roi_insights()

    # Footer
    st.markdown(
        f"""
    ---
    <div style="text-align: center; opacity: 0.6; font-size: 0.8rem; margin-top: 32px;">
        Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 
        EnterpriseHub Churn Recovery Union[Engine, Data] refresh: {time_range.lower()}
    </div>
    """,
        unsafe_allow_html=True,
    )


# Main execution
if __name__ == "__main__":
    render_advanced_churn_recovery_dashboard()
