"""
Multi-Market Analytics View - Geographic Performance Intelligence

Comprehensive analytics dashboard for multi-market operations providing deep insights
into geographic performance, cross-market attribution, and competitive positioning
across all active markets.

Features:
- Market comparison matrix with performance metrics
- Geographic performance trends over time
- Cross-market lead attribution analysis
- Market health scores with alerting
- Competitive positioning by market

Author: EnterpriseHub AI
Last Updated: 2026-01-18
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure page if running standalone
if __name__ == "__main__":
    st.set_page_config(
        page_title="Multi-Market Analytics", page_icon="🌍", layout="wide", initial_sidebar_state="expanded"
    )

# Professional executive styling
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Executive Theme - Multi-Market */
    .stApp {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Market Cards */
    .market-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(203, 213, 225, 0.6);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
        margin: 12px 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .market-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
    }
    
    .market-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
    }
    
    /* Market Health Indicators */
    .health-excellent::before { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .health-good::before { background: linear-gradient(90deg, #84cc16, #65a30d); }
    .health-warning::before { background: linear-gradient(90deg, #f59e0b, #d97706); }
    .health-critical::before { background: linear-gradient(90deg, #ef4444, #dc2626); }
    
    /* Performance Matrix */
    .performance-matrix {
        background: rgba(255, 255, 255, 0.95);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid rgba(203, 213, 225, 0.6);
        margin: 16px 0;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
    }
    
    /* Trend Indicators */
    .trend-up { color: #22c55e; font-weight: 600; }
    .trend-down { color: #ef4444; font-weight: 600; }
    .trend-stable { color: #64748b; font-weight: 600; }
    
    /* Section Headers */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.6rem;
        margin: 24px 0 16px 0;
        color: #1e293b;
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 16px;
        border-radius: 10px;
        margin: 8px 0;
        border-left: 3px solid;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: scale(1.02);
    }
    
    /* Attribution Flow */
    .attribution-node {
        background: rgba(59, 130, 246, 0.1);
        padding: 12px;
        border-radius: 8px;
        margin: 6px 0;
        border: 2px solid rgba(59, 130, 246, 0.3);
        text-align: center;
        font-weight: 600;
    }
    
    /* Competitive Positioning */
    .competitive-leader {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border-left: 4px solid #22c55e;
    }
    
    .competitive-challenger {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
    }
    
    .competitive-follower {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #ef4444;
    }
    
    /* Alert Styles */
    .market-alert {
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
        font-weight: 500;
        border-left: 4px solid;
    }
    
    .alert-opportunity {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left-color: #3b82f6;
        color: #1d4ed8;
    }
    
    .alert-risk {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left-color: #ef4444;
        color: #dc2626;
    }
</style>
""",
    unsafe_allow_html=True,
)


@dataclass
class MarketPerformance:
    """Market performance data structure"""

    name: str
    region: str
    active_leads: int
    conversion_rate: float
    avg_deal_size: float
    market_share: float
    growth_rate: float
    health_score: int
    competitive_position: str
    month_over_month: float
    attribution_sources: Dict[str, int]


@dataclass
class CrossMarketFlow:
    """Cross-market attribution flow"""

    source_market: str
    target_market: str
    lead_count: int
    conversion_rate: float
    avg_value: float


@st.cache_data(ttl=300)
def load_market_performance_data() -> List[MarketPerformance]:
    """Load comprehensive market performance data"""
    return [
        MarketPerformance(
            name="Austin Metro",
            region="Central Texas",
            active_leads=342,
            conversion_rate=0.18,
            avg_deal_size=485000,
            market_share=0.23,
            growth_rate=0.15,
            health_score=87,
            competitive_position="Leader",
            month_over_month=0.12,
            attribution_sources={"Organic": 145, "Paid": 98, "Referral": 67, "Social": 32},
        ),
        MarketPerformance(
            name="San Antonio",
            region="South Texas",
            active_leads=278,
            conversion_rate=0.14,
            avg_deal_size=365000,
            market_share=0.19,
            growth_rate=0.08,
            health_score=74,
            competitive_position="Challenger",
            month_over_month=0.06,
            attribution_sources={"Organic": 118, "Paid": 87, "Referral": 45, "Social": 28},
        ),
        MarketPerformance(
            name="Houston West",
            region="Greater Houston",
            active_leads=456,
            conversion_rate=0.21,
            avg_deal_size=525000,
            market_share=0.31,
            growth_rate=0.22,
            health_score=93,
            competitive_position="Leader",
            month_over_month=0.18,
            attribution_sources={"Organic": 203, "Paid": 142, "Referral": 78, "Social": 33},
        ),
        MarketPerformance(
            name="Dallas North",
            region="North Texas",
            active_leads=389,
            conversion_rate=0.16,
            avg_deal_size=412000,
            market_share=0.21,
            growth_rate=0.11,
            health_score=78,
            competitive_position="Challenger",
            month_over_month=0.09,
            attribution_sources={"Organic": 165, "Paid": 124, "Referral": 67, "Social": 33},
        ),
        MarketPerformance(
            name="Fort Worth",
            region="Tarrant County",
            active_leads=234,
            conversion_rate=0.13,
            avg_deal_size=348000,
            market_share=0.16,
            growth_rate=0.05,
            health_score=68,
            competitive_position="Follower",
            month_over_month=0.02,
            attribution_sources={"Organic": 98, "Paid": 76, "Referral": 38, "Social": 22},
        ),
    ]


@st.cache_data(ttl=300)
def generate_time_series_data() -> pd.DataFrame:
    """Generate market performance trends over time"""
    dates = pd.date_range(start="2023-09-01", end="2024-01-18", freq="W")
    markets = ["Austin Metro", "San Antonio", "Houston West", "Dallas North", "Fort Worth"]

    data = []
    for market in markets:
        base_performance = np.random.uniform(0.12, 0.22)
        for date in dates:
            # Add seasonality and growth trends
            seasonal = 0.02 * np.sin(2 * np.pi * date.dayofyear / 365)
            growth = 0.001 * (date - dates[0]).days
            noise = np.random.normal(0, 0.01)

            performance = base_performance + seasonal + growth + noise
            performance = max(0.08, min(0.25, performance))  # Clamp values

            data.append(
                {
                    "Date": date,
                    "Market": market,
                    "Conversion_Rate": performance,
                    "Lead_Volume": np.random.randint(150, 400),
                    "Revenue": performance * np.random.randint(300000, 600000),
                }
            )

    return pd.DataFrame(data)


@st.cache_data(ttl=300)
def generate_cross_market_flows() -> List[CrossMarketFlow]:
    """Generate cross-market attribution data"""
    markets = ["Austin Metro", "San Antonio", "Houston West", "Dallas North", "Fort Worth"]
    flows = []

    # Simulate realistic cross-market flows
    flow_patterns = [
        ("Austin Metro", "San Antonio", 23, 0.16, 380000),
        ("Houston West", "Dallas North", 34, 0.19, 445000),
        ("Dallas North", "Fort Worth", 18, 0.14, 325000),
        ("Austin Metro", "Houston West", 29, 0.21, 498000),
        ("San Antonio", "Austin Metro", 15, 0.18, 472000),
        ("Fort Worth", "Dallas North", 12, 0.15, 368000),
    ]

    for source, target, count, rate, value in flow_patterns:
        flows.append(CrossMarketFlow(source, target, count, rate, value))

    return flows


def get_health_class(score: int) -> str:
    """Get CSS class based on health score"""
    if score >= 85:
        return "health-excellent"
    elif score >= 75:
        return "health-good"
    elif score >= 65:
        return "health-warning"
    else:
        return "health-critical"


def get_trend_class(value: float) -> str:
    """Get trend CSS class"""
    if value > 0.05:
        return "trend-up"
    elif value < -0.05:
        return "trend-down"
    else:
        return "trend-stable"


def render_market_overview(markets: List[MarketPerformance]):
    """Render market overview cards"""
    st.markdown('<div class="section-header">🏢 Market Overview</div>', unsafe_allow_html=True)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    total_leads = sum(m.active_leads for m in markets)
    avg_conversion = sum(m.conversion_rate for m in markets) / len(markets)
    total_revenue = sum(m.active_leads * m.conversion_rate * m.avg_deal_size for m in markets)
    avg_health = sum(m.health_score for m in markets) / len(markets)

    with col1:
        st.metric("Total Active Leads", f"{total_leads:,}", f"+{np.random.randint(50, 150)}")

    with col2:
        st.metric("Average Conversion", f"{avg_conversion:.1%}", f"+{np.random.uniform(0.5, 2.0):.1f}%")

    with col3:
        st.metric("Pipeline Value", f"${total_revenue / 1e6:.1f}M", f"+${np.random.uniform(0.2, 0.8):.1f}M")

    with col4:
        health_delta = np.random.randint(-3, 8)
        st.metric("Market Health", f"{avg_health:.0f}/100", f"{health_delta:+d}")

    # Market cards grid
    cols = st.columns(2)
    for idx, market in enumerate(markets):
        col_idx = idx % 2
        health_class = get_health_class(market.health_score)
        trend_class = get_trend_class(market.month_over_month)

        with cols[col_idx]:
            st.markdown(
                f"""
            <div class="market-card {health_class}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
                    <div>
                        <h3 style="margin: 0; font-size: 1.2rem; font-weight: 700; color: #1e293b;">{market.name}</h3>
                        <div style="font-size: 0.85rem; color: #64748b; margin-top: 2px;">{market.region}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.8rem; font-weight: 700; color: #1e293b;">{market.health_score}</div>
                        <div style="font-size: 0.75rem; color: #64748b;">HEALTH</div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 600;">Active Leads</div>
                        <div style="font-size: 1.4rem; font-weight: 700; color: #1e293b;">{market.active_leads}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 600;">Conversion</div>
                        <div style="font-size: 1.4rem; font-weight: 700; color: #1e293b;">{market.conversion_rate:.1%}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 600;">Avg Deal Size</div>
                        <div style="font-size: 1.4rem; font-weight: 700; color: #1e293b;">${market.avg_deal_size / 1000:.0f}K</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 600;">Market Share</div>
                        <div style="font-size: 1.4rem; font-weight: 700; color: #1e293b;">{market.market_share:.1%}</div>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #e2e8f0; padding-top: 12px;">
                    <div>
                        <span style="font-size: 0.8rem; color: #64748b;">MoM Growth:</span>
                        <span class="{trend_class}" style="margin-left: 4px;">{market.month_over_month:+.1%}</span>
                    </div>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #3b82f6;">
                        {market.competitive_position}
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_performance_trends(time_series_data: pd.DataFrame):
    """Render performance trends over time"""
    st.markdown('<div class="section-header">📈 Performance Trends</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Conversion rate trends
        fig = px.line(
            time_series_data,
            x="Date",
            y="Conversion_Rate",
            color="Market",
            title="Conversion Rate Trends",
            labels={"Conversion_Rate": "Conversion Rate (%)"},
        )

        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
            yaxis=dict(tickformat=".1%"),
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Revenue trends
        fig = px.line(
            time_series_data,
            x="Date",
            y="Revenue",
            color="Market",
            title="Revenue Trends",
            labels={"Revenue": "Revenue ($)"},
        )

        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
            yaxis=dict(tickformat="$.0f"),
        )

        st.plotly_chart(fig, use_container_width=True)

    # Market comparison matrix
    st.markdown("**Market Performance Matrix**")

    # Latest data for each market
    latest_data = time_series_data.groupby("Market").tail(1)

    fig = px.scatter(
        latest_data,
        x="Lead_Volume",
        y="Conversion_Rate",
        size="Revenue",
        color="Market",
        title="Market Position Matrix (Latest Period)",
        labels={"Lead_Volume": "Lead Volume", "Conversion_Rate": "Conversion Rate", "Revenue": "Revenue ($)"},
    )

    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,0.95)",
        plot_bgcolor="rgba(255,255,255,0.95)",
        font_family="Inter",
        yaxis=dict(tickformat=".1%"),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_cross_market_attribution(flows: List[CrossMarketFlow], markets: List[MarketPerformance]):
    """Render cross-market attribution analysis"""
    st.markdown('<div class="section-header">🔄 Cross-Market Attribution</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Attribution flow chart
        flow_data = pd.DataFrame(
            [
                {
                    "Source": flow.source_market,
                    "Target": flow.target_market,
                    "Leads": flow.lead_count,
                    "Value": flow.avg_value,
                }
                for flow in flows
            ]
        )

        # Create Sankey diagram
        sources = []
        targets = []
        values = []
        labels = list(set(flow_data["Source"].tolist() + flow_data["Target"].tolist()))

        for _, row in flow_data.iterrows():
            source_idx = labels.index(row["Source"])
            target_idx = labels.index(row["Target"])
            sources.append(source_idx)
            targets.append(target_idx)
            values.append(row["Leads"])

        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=labels,
                        color="rgba(59, 130, 246, 0.8)",
                    ),
                    link=dict(source=sources, target=targets, value=values, color="rgba(59, 130, 246, 0.3)"),
                )
            ]
        )

        fig.update_layout(
            title_text="Lead Flow Between Markets",
            font_size=10,
            paper_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Attribution insights
        st.markdown("**Attribution Insights**")

        # Calculate top flows
        sorted_flows = sorted(flows, key=lambda x: x.lead_count, reverse=True)

        for flow in sorted_flows[:5]:
            value_per_lead = flow.avg_value / 1000
            total_value = flow.lead_count * flow.avg_value / 1000000

            st.markdown(
                f"""
            <div class="attribution-node">
                <div style="font-weight: 700; margin-bottom: 4px;">{flow.source_market} → {flow.target_market}</div>
                <div style="font-size: 1.2rem; color: #3b82f6; font-weight: 700;">{flow.lead_count} leads</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">
                    ${value_per_lead:.0f}K avg • ${total_value:.1f}M total
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Attribution sources breakdown
        st.markdown("**Top Attribution Sources**")

        all_sources = {}
        for market in markets:
            for source, count in market.attribution_sources.items():
                all_sources[source] = all_sources.get(source, 0) + count

        source_df = pd.DataFrame(list(all_sources.items()), columns=["Source", "Count"])
        source_df = source_df.sort_values("Count", ascending=True)

        fig = px.bar(
            source_df,
            x="Count",
            y="Source",
            orientation="h",
            title="Lead Attribution by Source",
            color="Count",
            color_continuous_scale="Blues",
        )

        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
            height=300,
        )

        st.plotly_chart(fig, use_container_width=True)


def render_market_health_scores(markets: List[MarketPerformance]):
    """Render market health scores and alerts"""
    st.markdown('<div class="section-header">🏥 Market Health Monitoring</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        # Health score radar chart
        categories = ["Health Score", "Growth Rate", "Market Share", "Conversion Rate", "Lead Volume"]

        fig = go.Figure()

        for market in markets:
            # Normalize values for radar chart (0-100 scale)
            values = [
                market.health_score,
                min(100, market.growth_rate * 500),  # Scale growth rate
                market.market_share * 300,  # Scale market share
                market.conversion_rate * 500,  # Scale conversion rate
                min(100, market.active_leads / 5),  # Scale lead volume
            ]

            fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill="toself", name=market.name, opacity=0.7))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            title="Market Health Radar",
            paper_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Market alerts and recommendations
        st.markdown("**Market Alerts & Recommendations**")

        # Generate alerts based on performance
        alerts = []

        for market in markets:
            if market.health_score < 70:
                alerts.append(
                    {
                        "type": "risk",
                        "market": market.name,
                        "message": f"Health score below 70 ({market.health_score}). Immediate attention required.",
                        "action": "Review conversion funnel and lead quality",
                    }
                )

            if market.month_over_month < -0.05:
                alerts.append(
                    {
                        "type": "risk",
                        "market": market.name,
                        "message": f"Negative MoM growth ({market.month_over_month:+.1%})",
                        "action": "Analyze recent campaign performance",
                    }
                )

            if market.growth_rate > 0.15:
                alerts.append(
                    {
                        "type": "opportunity",
                        "market": market.name,
                        "message": f"Strong growth rate ({market.growth_rate:.1%}). Scale opportunity.",
                        "action": "Consider increasing ad spend and team size",
                    }
                )

        # Display alerts
        for alert in alerts:
            alert_class = "alert-risk" if alert["type"] == "risk" else "alert-opportunity"
            icon = "⚠️" if alert["type"] == "risk" else "💡"

            st.markdown(
                f"""
            <div class="market-alert {alert_class}">
                <div style="font-weight: 700; margin-bottom: 4px;">{icon} {alert["market"]}</div>
                <div style="margin-bottom: 6px;">{alert["message"]}</div>
                <div style="font-size: 0.85rem; font-style: italic;">Recommended: {alert["action"]}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        if not alerts:
            st.markdown(
                """
            <div class="market-alert alert-opportunity">
                <div style="font-weight: 700;">✅ All Markets Healthy</div>
                <div>No critical alerts detected. Continue monitoring performance.</div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_competitive_positioning(markets: List[MarketPerformance]):
    """Render competitive positioning analysis"""
    st.markdown('<div class="section-header">🎯 Competitive Positioning</div>', unsafe_allow_html=True)

    # Competitive position matrix
    col1, col2 = st.columns([2, 1])

    with col1:
        # Market share vs growth rate scatter
        fig = px.scatter(
            pd.DataFrame(
                [
                    {
                        "Market": m.name,
                        "Market_Share": m.market_share,
                        "Growth_Rate": m.growth_rate,
                        "Position": m.competitive_position,
                        "Health": m.health_score,
                        "Revenue": m.active_leads * m.conversion_rate * m.avg_deal_size,
                    }
                    for m in markets
                ]
            ),
            x="Market_Share",
            y="Growth_Rate",
            size="Revenue",
            color="Position",
            hover_data=["Health"],
            title="Competitive Position Matrix",
            labels={"Market_Share": "Market Share (%)", "Growth_Rate": "Growth Rate (%)"},
            color_discrete_map={"Leader": "#22c55e", "Challenger": "#f59e0b", "Follower": "#ef4444"},
        )

        # Add quadrant lines
        fig.add_hline(y=0.1, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=0.2, line_dash="dash", line_color="gray", opacity=0.5)

        # Add quadrant labels
        fig.add_annotation(x=0.35, y=0.2, text="Stars", showarrow=False, font_color="gray")
        fig.add_annotation(x=0.35, y=0.05, text="Cash Cows", showarrow=False, font_color="gray")
        fig.add_annotation(x=0.1, y=0.2, text="Question Marks", showarrow=False, font_color="gray")
        fig.add_annotation(x=0.1, y=0.05, text="Dogs", showarrow=False, font_color="gray")

        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
            xaxis=dict(tickformat=".1%"),
            yaxis=dict(tickformat=".1%"),
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Competitive insights
        st.markdown("**Strategic Insights**")

        # Sort markets by competitive position
        leaders = [m for m in markets if m.competitive_position == "Leader"]
        challengers = [m for m in markets if m.competitive_position == "Challenger"]
        followers = [m for m in markets if m.competitive_position == "Follower"]

        for category, markets_list, class_name in [
            ("🏆 Market Leaders", leaders, "competitive-leader"),
            ("⚡ Challengers", challengers, "competitive-challenger"),
            ("📈 Followers", followers, "competitive-follower"),
        ]:
            if markets_list:
                st.markdown(f"**{category}**")
                for market in markets_list:
                    st.markdown(
                        f"""
                    <div class="metric-card {class_name}">
                        <div style="font-weight: 600;">{market.name}</div>
                        <div style="font-size: 0.85rem; margin-top: 4px;">
                            Share: {market.market_share:.1%} | Growth: {market.growth_rate:+.1%}
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )


def render_multi_market_analytics_view():
    """Main function to render the multi-market analytics dashboard"""

    # Header
    st.markdown("""
    # 🌍 Multi-Market Analytics View
    **Geographic Performance Intelligence Center**
    
    Comprehensive analytics across all active markets with competitive positioning and cross-market insights.
    """)

    # Sidebar controls
    with st.sidebar:
        st.markdown("### Analytics Controls")

        date_range = st.date_input(
            "Date Range", value=(datetime.now() - timedelta(days=30), datetime.now()), max_value=datetime.now()
        )

        selected_markets = st.multiselect(
            "Select Markets",
            ["Austin Metro", "San Antonio", "Houston West", "Dallas North", "Fort Worth"],
            default=["Austin Metro", "San Antonio", "Houston West", "Dallas North", "Fort Worth"],
        )

        metric_focus = st.selectbox(
            "Primary Metric", ["Conversion Rate", "Lead Volume", "Revenue", "Market Share", "Growth Rate"]
        )

        show_trends = st.checkbox("Show Historical Trends", value=True)
        show_attribution = st.checkbox("Show Cross-Market Attribution", value=True)

        st.markdown("---")
        st.markdown("**Export Options**")
        if st.button("📊 Export Dashboard Data"):
            st.success("Dashboard data exported successfully!")

        if st.button("📧 Schedule Report"):
            st.success("Weekly report scheduled!")

    # Load data
    all_markets = load_market_performance_data()
    markets = [m for m in all_markets if m.name in selected_markets]
    time_series_data = generate_time_series_data()
    time_series_data = time_series_data[time_series_data["Market"].isin(selected_markets)]
    cross_market_flows = generate_cross_market_flows()

    # Filter flows for selected markets
    cross_market_flows = [
        f for f in cross_market_flows if f.source_market in selected_markets and f.target_market in selected_markets
    ]

    # Render dashboard sections
    render_market_overview(markets)

    st.markdown("---")

    if show_trends:
        render_performance_trends(time_series_data)
        st.markdown("---")

    if show_attribution and cross_market_flows:
        render_cross_market_attribution(cross_market_flows, markets)
        st.markdown("---")

    render_market_health_scores(markets)

    st.markdown("---")

    render_competitive_positioning(markets)

    # Footer with summary
    st.markdown(
        f"""
    ---
    <div style="text-align: center; opacity: 0.6; font-size: 0.8rem; margin-top: 32px;">
        Multi-Market Analytics | {len(markets)} Markets Union[Analyzed, Last] updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 
        Data range: {date_range[0]} to {date_range[1] if len(date_range) > 1 else date_range[0]}
    </div>
    """,
        unsafe_allow_html=True,
    )


# Main execution
if __name__ == "__main__":
    render_multi_market_analytics_view()
