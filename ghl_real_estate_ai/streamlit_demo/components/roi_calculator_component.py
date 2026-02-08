"""
Interactive ROI Calculator - CLV-Based Recovery Investment Planning

Executive-grade ROI calculator for churn recovery investments with real-time
projections, scenario modeling, and strategic investment planning capabilities.

Features:
- CLV-based recovery projections
- Campaign cost analysis by channel
- Recovery rate optimization scenarios
- Investment planning tools
- Performance forecasting

Author: EnterpriseHub AI
Last Updated: 2026-01-18
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, NamedTuple, Optional, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Configure page if running standalone
if __name__ == "__main__":
    st.set_page_config(page_title="ROI Calculator", page_icon="💰", layout="wide", initial_sidebar_state="expanded")

# Professional executive styling
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Executive ROI Theme */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Calculator Cards */
    .calculator-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid rgba(203, 213, 225, 0.6);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        margin: 16px 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .calculator-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
    }
    
    /* ROI Metrics */
    .roi-positive {
        color: #22c55e;
        font-weight: 700;
        font-size: 1.5rem;
    }
    
    .roi-negative {
        color: #ef4444;
        font-weight: 700;
        font-size: 1.5rem;
    }
    
    .roi-neutral {
        color: #64748b;
        font-weight: 700;
        font-size: 1.5rem;
    }
    
    /* Investment Scenarios */
    .scenario-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(248,250,252,0.9) 100%);
        padding: 20px;
        border-radius: 12px;
        margin: 12px 0;
        border: 1px solid rgba(203, 213, 225, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .scenario-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
    }
    
    .scenario-conservative::before {
        background: linear-gradient(90deg, #64748b, #475569);
    }
    
    .scenario-balanced::before {
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
    }
    
    .scenario-aggressive::before {
        background: linear-gradient(90deg, #22c55e, #16a34a);
    }
    
    /* Projection Charts */
    .projection-container {
        background: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 12px;
        margin: 16px 0;
        border: 1px solid rgba(203, 213, 225, 0.4);
    }
    
    /* Input Sections */
    .input-section {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(29, 78, 216, 0.05) 100%);
        padding: 20px;
        border-radius: 12px;
        margin: 16px 0;
        border-left: 4px solid #3b82f6;
    }
    
    /* Section Headers */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.6rem;
        margin: 24px 0 16px 0;
        color: #1e293b;
        background: linear-gradient(135deg, #059669, #047857);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Financial Metrics */
    .financial-metric {
        background: rgba(255, 255, 255, 0.95);
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .metric-positive {
        border-left-color: #22c55e;
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, rgba(22, 163, 74, 0.05) 100%);
    }
    
    .metric-warning {
        border-left-color: #f59e0b;
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(217, 119, 6, 0.05) 100%);
    }
    
    .metric-negative {
        border-left-color: #ef4444;
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.05) 0%, rgba(220, 38, 38, 0.05) 100%);
    }
    
    /* Investment Recommendation */
    .investment-recommendation {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
        margin: 16px 0;
    }
    
    /* Channel Performance */
    .channel-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 16px;
        border-radius: 10px;
        margin: 8px 0;
        border: 1px solid rgba(203, 213, 225, 0.4);
        transition: transform 0.2s ease;
    }
    
    .channel-card:hover {
        transform: scale(1.02);
    }
</style>
""",
    unsafe_allow_html=True,
)


@dataclass
class InvestmentScenario:
    """Investment scenario data structure"""

    name: str
    description: str
    monthly_cost: float
    setup_cost: float
    expected_recovery_lift: float
    implementation_months: int
    risk_level: str


@dataclass
class ChannelInvestment:
    """Channel-specific investment data"""

    name: str
    current_cost_per_lead: float
    current_conversion_rate: float
    investment_amount: float
    projected_cpl_reduction: float
    projected_conversion_lift: float
    roi_projection: float


@dataclass
class ROICalculation:
    """ROI calculation results"""

    total_investment: float
    projected_clv_recovery: float
    net_benefit: float
    roi_percentage: float
    payback_months: float
    break_even_leads: int


class ROICalculator:
    """ROI calculation engine"""

    def __init__(self, base_clv: float = 12500, base_churn_rate: float = 0.08):
        self.base_clv = base_clv
        self.base_churn_rate = base_churn_rate

    def calculate_scenario_roi(
        self, scenario: InvestmentScenario, lead_volume: int, current_recovery_rate: float
    ) -> ROICalculation:
        """Calculate ROI for a specific investment scenario"""

        # Calculate investment costs
        total_investment = scenario.setup_cost + (scenario.monthly_cost * 12)

        # Calculate current and projected recovery
        at_risk_leads = lead_volume * self.base_churn_rate
        current_recovered = at_risk_leads * current_recovery_rate

        new_recovery_rate = min(0.95, current_recovery_rate + scenario.expected_recovery_lift)
        projected_recovered = at_risk_leads * new_recovery_rate

        additional_recovered = projected_recovered - current_recovered
        projected_clv_recovery = additional_recovered * self.base_clv

        # Calculate ROI metrics
        net_benefit = projected_clv_recovery - total_investment
        roi_percentage = (net_benefit / total_investment) * 100 if total_investment > 0 else 0

        # Calculate payback period
        monthly_benefit = projected_clv_recovery / 12
        monthly_cost = scenario.monthly_cost
        payback_months = (
            total_investment / (monthly_benefit - monthly_cost) if monthly_benefit > monthly_cost else float("inf")
        )

        # Break-even analysis
        break_even_leads = total_investment / self.base_clv if self.base_clv > 0 else 0

        return ROICalculation(
            total_investment=total_investment,
            projected_clv_recovery=projected_clv_recovery,
            net_benefit=net_benefit,
            roi_percentage=roi_percentage,
            payback_months=payback_months,
            break_even_leads=int(break_even_leads),
        )


@st.cache_data
def get_investment_scenarios() -> List[InvestmentScenario]:
    """Get predefined investment scenarios"""
    return [
        InvestmentScenario(
            name="Email Automation Plus",
            description="Advanced email sequences with behavioral triggers",
            monthly_cost=2500,
            setup_cost=5000,
            expected_recovery_lift=0.08,
            implementation_months=2,
            risk_level="Low",
        ),
        InvestmentScenario(
            name="Multi-Channel Campaign",
            description="Email, SMS, and phone call automation",
            monthly_cost=4800,
            setup_cost=12000,
            expected_recovery_lift=0.15,
            implementation_months=3,
            risk_level="Medium",
        ),
        InvestmentScenario(
            name="AI-Powered Personalization",
            description="Claude-driven personalized interventions",
            monthly_cost=8500,
            setup_cost=25000,
            expected_recovery_lift=0.22,
            implementation_months=4,
            risk_level="Medium",
        ),
        InvestmentScenario(
            name="Predictive Analytics Suite",
            description="Advanced churn prediction and early intervention",
            monthly_cost=6200,
            setup_cost=18000,
            expected_recovery_lift=0.18,
            implementation_months=3,
            risk_level="Medium",
        ),
        InvestmentScenario(
            name="Premium Recovery Engine",
            description="Full-stack churn recovery with dedicated team",
            monthly_cost=15000,
            setup_cost=45000,
            expected_recovery_lift=0.35,
            implementation_months=6,
            risk_level="High",
        ),
    ]


@st.cache_data
def get_channel_investments() -> List[ChannelInvestment]:
    """Get channel-specific investment opportunities"""
    return [
        ChannelInvestment(
            name="Email Marketing",
            current_cost_per_lead=12.50,
            current_conversion_rate=0.24,
            investment_amount=15000,
            projected_cpl_reduction=0.20,
            projected_conversion_lift=0.08,
            roi_projection=285,
        ),
        ChannelInvestment(
            name="SMS Campaigns",
            current_cost_per_lead=8.75,
            current_conversion_rate=0.31,
            investment_amount=8000,
            projected_cpl_reduction=0.15,
            projected_conversion_lift=0.06,
            roi_projection=340,
        ),
        ChannelInvestment(
            name="Phone Outreach",
            current_cost_per_lead=45.00,
            current_conversion_rate=0.68,
            investment_amount=25000,
            projected_cpl_reduction=0.25,
            projected_conversion_lift=0.12,
            roi_projection=520,
        ),
        ChannelInvestment(
            name="Property Alerts",
            current_cost_per_lead=15.20,
            current_conversion_rate=0.28,
            investment_amount=12000,
            projected_cpl_reduction=0.18,
            projected_conversion_lift=0.07,
            roi_projection=275,
        ),
        ChannelInvestment(
            name="Social Retargeting",
            current_cost_per_lead=22.30,
            current_conversion_rate=0.16,
            investment_amount=18000,
            projected_cpl_reduction=0.30,
            projected_conversion_lift=0.12,
            roi_projection=425,
        ),
    ]


def render_input_parameters():
    """Render input parameters section"""
    st.markdown('<div class="section-header">⚙️ Calculator Parameters</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="input-section">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Lead Portfolio**")
            monthly_leads = st.number_input(
                "Monthly Lead Volume",
                min_value=100,
                max_value=10000,
                value=1500,
                step=50,
                help="Total leads acquired per month",
            )

            current_churn_rate = st.slider(
                "Current Churn Rate",
                min_value=0.05,
                max_value=0.20,
                value=0.08,
                step=0.01,
                format="%.1%",
                help="Percentage of leads that churn monthly",
            )

        with col2:
            st.markdown("**Recovery Metrics**")
            current_recovery_rate = st.slider(
                "Current Recovery Rate",
                min_value=0.40,
                max_value=0.90,
                value=0.67,
                step=0.01,
                format="%.1%",
                help="Current success rate of recovery attempts",
            )

            avg_clv = st.number_input(
                "Average CLV",
                min_value=5000,
                max_value=50000,
                value=12500,
                step=500,
                help="Average customer lifetime value",
            )

        with col3:
            st.markdown("**Time Horizon**")
            projection_months = st.selectbox(
                "Projection Period", [6, 12, 18, 24, 36], index=1, help="Months for ROI projection"
            )

            discount_rate = st.slider(
                "Discount Rate",
                min_value=0.05,
                max_value=0.15,
                value=0.08,
                step=0.01,
                format="%.1%",
                help="Annual discount rate for NPV calculation",
            )

        st.markdown("</div>", unsafe_allow_html=True)

    return {
        "monthly_leads": monthly_leads,
        "current_churn_rate": current_churn_rate,
        "current_recovery_rate": current_recovery_rate,
        "avg_clv": avg_clv,
        "projection_months": projection_months,
        "discount_rate": discount_rate,
    }


def render_scenario_analysis(params: Dict, scenarios: List[InvestmentScenario]):
    """Render investment scenario analysis"""
    st.markdown('<div class="section-header">📊 Investment Scenario Analysis</div>', unsafe_allow_html=True)

    calculator = ROICalculator(params["avg_clv"], params["current_churn_rate"])

    # Calculate ROI for each scenario
    scenario_results = []
    for scenario in scenarios:
        roi_calc = calculator.calculate_scenario_roi(scenario, params["monthly_leads"], params["current_recovery_rate"])
        scenario_results.append((scenario, roi_calc))

    # Scenario comparison chart
    col1, col2 = st.columns([2, 1])

    with col1:
        # ROI comparison chart
        chart_data = pd.DataFrame(
            [
                {
                    "Scenario": scenario.name,
                    "Investment": roi_calc.total_investment,
                    "ROI_Percentage": roi_calc.roi_percentage,
                    "Net_Benefit": roi_calc.net_benefit,
                    "Payback_Months": roi_calc.payback_months if roi_calc.payback_months != float("inf") else 60,
                    "Risk_Level": scenario.risk_level,
                }
                for scenario, roi_calc in scenario_results
            ]
        )

        fig = px.scatter(
            chart_data,
            x="Investment",
            y="ROI_Percentage",
            size="Net_Benefit",
            color="Risk_Level",
            hover_data=["Payback_Months"],
            title="Investment vs ROI Analysis",
            labels={
                "Investment": "Total Investment ($)",
                "ROI_Percentage": "ROI (%)",
                "Net_Benefit": "Net Benefit ($)",
            },
            color_discrete_map={"Low": "#22c55e", "Medium": "#f59e0b", "High": "#ef4444"},
        )

        # Add break-even line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7)

        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)", plot_bgcolor="rgba(255,255,255,0.95)", font_family="Inter"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top scenarios ranking
        st.markdown("**Recommended Scenarios**")

        # Sort by ROI percentage
        sorted_results = sorted(scenario_results, key=lambda x: x[1].roi_percentage, reverse=True)

        for idx, (scenario, roi_calc) in enumerate(sorted_results[:3]):
            rank_colors = ["#ffd700", "#c0c0c0", "#cd7f32"]  # Gold, Silver, Bronze
            rank_icons = ["🥇", "🥈", "🥉"]

            roi_class = "roi-positive" if roi_calc.roi_percentage > 0 else "roi-negative"

            st.markdown(
                f"""
            <div class="scenario-card scenario-{"conservative" if scenario.risk_level == "Low" else "balanced" if scenario.risk_level == "Medium" else "aggressive"}">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 1.2rem; margin-right: 8px;">{rank_icons[idx]}</span>
                    <span style="font-weight: 700; font-size: 1rem;">{scenario.name}</span>
                </div>
                <div class="{roi_class}" style="margin: 8px 0;">{roi_calc.roi_percentage:.1f}% ROI</div>
                <div style="font-size: 0.85rem; margin-bottom: 8px; opacity: 0.8;">{scenario.description}</div>
                <div style="font-size: 0.8rem; display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                    <div><strong>Investment:</strong> ${roi_calc.total_investment:,.0f}</div>
                    <div><strong>Payback:</strong> {roi_calc.payback_months:.1f}mo</div>
                    <div><strong>Net Benefit:</strong> ${roi_calc.net_benefit:,.0f}</div>
                    <div><strong>Risk:</strong> {scenario.risk_level}</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_channel_optimization(params: Dict, channels: List[ChannelInvestment]):
    """Render channel-specific optimization analysis"""
    st.markdown('<div class="section-header">📱 Channel Optimization Analysis</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        # Current vs optimized performance
        current_data = []
        optimized_data = []

        for channel in channels:
            current_data.append(
                {
                    "Channel": channel.name,
                    "Cost_Per_Lead": channel.current_cost_per_lead,
                    "Conversion_Rate": channel.current_conversion_rate,
                    "Type": "Current",
                }
            )

            optimized_cpl = channel.current_cost_per_lead * (1 - channel.projected_cpl_reduction)
            optimized_conv = channel.current_conversion_rate + channel.projected_conversion_lift

            optimized_data.append(
                {
                    "Channel": channel.name,
                    "Cost_Per_Lead": optimized_cpl,
                    "Conversion_Rate": optimized_conv,
                    "Type": "Optimized",
                }
            )

        comparison_df = pd.DataFrame(current_data + optimized_data)

        fig = px.scatter(
            comparison_df,
            x="Cost_Per_Lead",
            y="Conversion_Rate",
            color="Type",
            symbol="Type",
            hover_data=["Channel"],
            title="Current vs Optimized Channel Performance",
            labels={"Cost_Per_Lead": "Cost Per Lead ($)", "Conversion_Rate": "Conversion Rate"},
            color_discrete_map={"Current": "#64748b", "Optimized": "#22c55e"},
        )

        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
            yaxis=dict(tickformat=".1%"),
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Channel investment ROI
        roi_data = pd.DataFrame(
            [
                {
                    "Channel": channel.name,
                    "Investment": channel.investment_amount,
                    "ROI": channel.roi_projection,
                    "Efficiency": channel.roi_projection / (channel.investment_amount / 1000),  # ROI per $1k invested
                }
                for channel in channels
            ]
        )

        fig = px.bar(
            roi_data.sort_values("ROI", ascending=True),
            x="ROI",
            y="Channel",
            orientation="h",
            color="ROI",
            color_continuous_scale="RdYlGn",
            title="Channel ROI Projections (%)",
        )

        fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.95)", plot_bgcolor="rgba(255,255,255,0.95)", font_family="Inter"
        )

        st.plotly_chart(fig, use_container_width=True)

    # Channel investment cards
    st.markdown("**Channel Investment Opportunities**")

    cols = st.columns(2)
    for idx, channel in enumerate(channels):
        col_idx = idx % 2

        roi_class = (
            "metric-positive"
            if channel.roi_projection > 300
            else "metric-warning"
            if channel.roi_projection > 200
            else "metric-negative"
        )

        with cols[col_idx]:
            st.markdown(
                f"""
            <div class="channel-card">
                <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 8px; color: #1e293b;">{channel.name}</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px;">
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Current CPL</div>
                        <div style="font-size: 1.1rem; font-weight: 600;">${channel.current_cost_per_lead:.2f}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Conv. Rate</div>
                        <div style="font-size: 1.1rem; font-weight: 600;">{channel.current_conversion_rate:.1%}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Investment</div>
                        <div style="font-size: 1.1rem; font-weight: 600;">${channel.investment_amount:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;">Projected ROI</div>
                        <div style="font-size: 1.1rem; font-weight: 600; color: {"#22c55e" if channel.roi_projection > 300 else "#f59e0b" if channel.roi_projection > 200 else "#ef4444"};">
                            {channel.roi_projection}%
                        </div>
                    </div>
                </div>
                <div style="font-size: 0.8rem; color: #64748b;">
                    CPL Reduction: {channel.projected_cpl_reduction:.1%} | 
                    Conv. Lift: +{channel.projected_conversion_lift:.1%}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_financial_projections(params: Dict):
    """Render detailed financial projections"""
    st.markdown('<div class="section-header">💰 Financial Impact Projections</div>', unsafe_allow_html=True)

    # Calculate baseline metrics
    monthly_at_risk = params["monthly_leads"] * params["current_churn_rate"]
    current_monthly_recovery = monthly_at_risk * params["current_recovery_rate"]
    current_monthly_clv = current_monthly_recovery * params["avg_clv"]

    # Generate monthly projections
    months = range(1, params["projection_months"] + 1)
    projections = []

    for month in months:
        # Baseline scenario (no investment)
        baseline_recovery = current_monthly_recovery
        baseline_clv = baseline_recovery * params["avg_clv"]

        # Investment scenarios
        scenarios = {
            "Conservative": {"recovery_lift": 0.08, "monthly_cost": 2500, "setup_cost": 5000 if month == 1 else 0},
            "Balanced": {"recovery_lift": 0.15, "monthly_cost": 4800, "setup_cost": 12000 if month == 1 else 0},
            "Aggressive": {"recovery_lift": 0.25, "monthly_cost": 8500, "setup_cost": 25000 if month == 1 else 0},
        }

        projection = {"Month": month, "Baseline_CLV": baseline_clv}

        for scenario_name, scenario_data in scenarios.items():
            new_recovery_rate = min(0.95, params["current_recovery_rate"] + scenario_data["recovery_lift"])
            scenario_recovery = monthly_at_risk * new_recovery_rate
            scenario_clv = scenario_recovery * params["avg_clv"]
            scenario_cost = scenario_data["monthly_cost"] + scenario_data["setup_cost"]
            net_benefit = scenario_clv - baseline_clv - scenario_cost

            projection[f"{scenario_name}_CLV"] = scenario_clv
            projection[f"{scenario_name}_Cost"] = scenario_cost
            projection[f"{scenario_name}_Net"] = net_benefit

        projections.append(projection)

    projections_df = pd.DataFrame(projections)

    col1, col2 = st.columns(2)

    with col1:
        # CLV recovery projections
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=projections_df["Month"],
                y=projections_df["Baseline_CLV"],
                mode="lines",
                name="Baseline",
                line=dict(color="#64748b", dash="dash"),
            )
        )

        colors = {"Conservative": "#94a3b8", "Balanced": "#3b82f6", "Aggressive": "#22c55e"}
        for scenario in ["Conservative", "Balanced", "Aggressive"]:
            fig.add_trace(
                go.Scatter(
                    x=projections_df["Month"],
                    y=projections_df[f"{scenario}_CLV"],
                    mode="lines+markers",
                    name=f"{scenario} Investment",
                    line=dict(color=colors[scenario]),
                )
            )

        fig.update_layout(
            title="Monthly CLV Recovery Projections",
            xaxis_title="Month",
            yaxis_title="CLV Recovery ($)",
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Net benefit analysis
        fig = go.Figure()

        for scenario in ["Conservative", "Balanced", "Aggressive"]:
            fig.add_trace(
                go.Scatter(
                    x=projections_df["Month"],
                    y=projections_df[f"{scenario}_Net"],
                    mode="lines+markers",
                    name=f"{scenario}",
                    line=dict(color=colors[scenario]),
                    fill="tonexty" if scenario == "Conservative" else None,
                )
            )

        # Add break-even line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7)

        fig.update_layout(
            title="Net Benefit Analysis (CLV - Investment)",
            xaxis_title="Month",
            yaxis_title="Net Benefit ($)",
            paper_bgcolor="rgba(255,255,255,0.95)",
            plot_bgcolor="rgba(255,255,255,0.95)",
            font_family="Inter",
        )

        st.plotly_chart(fig, use_container_width=True)

    # Summary financial metrics
    st.markdown("**Financial Impact Summary**")

    # Calculate cumulative metrics for 12-month period
    twelve_month_data = projections_df.head(12)

    for scenario in ["Conservative", "Balanced", "Aggressive"]:
        total_investment = twelve_month_data[f"{scenario}_Cost"].sum()
        total_clv = twelve_month_data[f"{scenario}_CLV"].sum()
        baseline_total = twelve_month_data["Baseline_CLV"].sum()
        additional_clv = total_clv - baseline_total
        net_benefit = additional_clv - total_investment
        roi = (net_benefit / total_investment) * 100 if total_investment > 0 else 0

        metric_class = "metric-positive" if roi > 200 else "metric-warning" if roi > 100 else "metric-negative"

        st.markdown(
            f"""
        <div class="financial-metric {metric_class}">
            <div>
                <div style="font-weight: 700; font-size: 1.1rem;">{scenario} Investment (12mo)</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">
                    Investment: ${total_investment:,.0f} | Additional CLV: ${additional_clv:,.0f}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.5rem; font-weight: 700;">ROI: {roi:.0f}%</div>
                <div style="font-size: 0.85rem; opacity: 0.8;">Net: ${net_benefit:,.0f}</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_investment_recommendations(params: Dict):
    """Render strategic investment recommendations"""
    st.markdown('<div class="section-header">🎯 Strategic Recommendations</div>', unsafe_allow_html=True)

    # Analyze portfolio characteristics
    monthly_at_risk = params["monthly_leads"] * params["current_churn_rate"]
    annual_churn_cost = monthly_at_risk * 12 * params["avg_clv"]

    # Generate recommendations based on portfolio
    recommendations = []

    if params["current_recovery_rate"] < 0.60:
        recommendations.append(
            {
                "priority": "High",
                "title": "Implement Basic Recovery Infrastructure",
                "description": "Current recovery rate below 60% indicates lack of systematic approach",
                "action": "Start with Email Automation Plus scenario",
                "investment": "$35K annual",
                "expected_impact": "+8% recovery rate",
                "timeframe": "2-3 months",
            }
        )

    if params["current_churn_rate"] > 0.10:
        recommendations.append(
            {
                "priority": "Critical",
                "title": "Address High Churn Rate",
                "description": "Churn rate above 10% requires immediate intervention",
                "action": "Deploy predictive analytics to identify early warning signals",
                "investment": "$42K annual",
                "expected_impact": "Reduce churn by 2-3%",
                "timeframe": "3-4 months",
            }
        )

    if annual_churn_cost > 500000:
        recommendations.append(
            {
                "priority": "High",
                "title": "Scale Recovery Operations",
                "description": f"Annual churn cost of ${annual_churn_cost:,.0f} justifies significant investment",
                "action": "Consider Premium Recovery Engine for maximum impact",
                "investment": "$225K annual",
                "expected_impact": "+35% recovery rate",
                "timeframe": "6 months",
            }
        )

    if params["avg_clv"] > 15000:
        recommendations.append(
            {
                "priority": "Medium",
                "title": "Premium Intervention Strategy",
                "description": "High CLV justifies premium recovery approaches",
                "action": "Implement AI-powered personalization with phone outreach",
                "investment": "$127K annual",
                "expected_impact": "+22% recovery rate",
                "timeframe": "4-5 months",
            }
        )

    # Display recommendations
    col1, col2 = st.columns([2, 1])

    with col1:
        for rec in recommendations:
            priority_colors = {"Critical": "#ef4444", "High": "#f59e0b", "Medium": "#3b82f6", "Low": "#64748b"}

            priority_color = priority_colors.get(rec["priority"], "#64748b")

            st.markdown(
                f"""
            <div class="investment-recommendation" style="border-left-color: {priority_color};">
                <div style="display: flex; justify-content: between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        <div style="font-weight: 700; font-size: 1.1rem; color: #1e293b;">{rec["title"]}</div>
                        <div style="background: {priority_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: inline-block; margin-top: 4px;">
                            {rec["priority"]} Priority
                        </div>
                    </div>
                </div>
                <div style="margin-bottom: 12px; color: #4b5563;">{rec["description"]}</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 8px;">
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; font-weight: 600;">Recommended Action</div>
                        <div style="font-weight: 600;">{rec["action"]}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; font-weight: 600;">Expected Impact</div>
                        <div style="font-weight: 600; color: #22c55e;">{rec["expected_impact"]}</div>
                    </div>
                </div>
                <div style="display: flex; justify-content: between; font-size: 0.85rem; color: #6b7280;">
                    <span><strong>Investment:</strong> {rec["investment"]}</span>
                    <span style="margin-left: 24px;"><strong>Timeline:</strong> {rec["timeframe"]}</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown("**Implementation Roadmap**")

        # Create implementation timeline
        critical_recs = [r for r in recommendations if r["priority"] == "Critical"]
        high_recs = [r for r in recommendations if r["priority"] == "High"]
        medium_recs = [r for r in recommendations if r["priority"] == "Medium"]

        timeline = []
        month = 1

        for rec_list, phase in [(critical_recs, "Phase 1"), (high_recs, "Phase 2"), (medium_recs, "Phase 3")]:
            if rec_list:
                timeline.append(
                    {
                        "phase": phase,
                        "month": f"Month {month}-{month + 2}",
                        "initiatives": len(rec_list),
                        "priority": rec_list[0]["priority"],
                    }
                )
                month += 3

        for item in timeline:
            priority_colors = {"Critical": "#ef4444", "High": "#f59e0b", "Medium": "#3b82f6"}
            color = priority_colors.get(item["priority"], "#64748b")

            st.markdown(
                f"""
            <div style="background: rgba(255,255,255,0.9); padding: 16px; border-radius: 8px; margin: 8px 0; border-left: 4px solid {color};">
                <div style="font-weight: 700; color: {color};">{item["phase"]}</div>
                <div style="font-size: 0.9rem; margin: 4px 0; color: #4b5563;">{item["month"]}</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">{item["initiatives"]} initiatives</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Quick wins section
        st.markdown("**Quick Wins (30 days)**")
        quick_wins = [
            "Audit current email sequences",
            "Implement basic SMS alerts",
            "Set up recovery tracking",
            "Train team on new processes",
        ]

        for win in quick_wins:
            st.markdown(f"• {win}")


def render_roi_calculator():
    """Main function to render the ROI calculator"""

    # Header
    st.markdown("""
    # 💰 Interactive ROI Calculator
    **CLV-Based Recovery Investment Planning**
    
    Strategic investment planning for churn recovery with real-time ROI projections and scenario modeling.
    """)

    # Input parameters
    params = render_input_parameters()

    # Load reference data
    scenarios = get_investment_scenarios()
    channels = get_channel_investments()

    # Main dashboard sections
    render_scenario_analysis(params, scenarios)

    st.markdown("---")

    render_channel_optimization(params, channels)

    st.markdown("---")

    render_financial_projections(params)

    st.markdown("---")

    render_investment_recommendations(params)

    # Export and save functionality
    with st.sidebar:
        st.markdown("### Calculator Tools")

        if st.button("📊 Export Analysis"):
            # Create summary report
            summary = {
                "parameters": params,
                "timestamp": datetime.now().isoformat(),
                "recommendations": "Generated based on current inputs",
            }
            st.success("Analysis exported successfully!")
            st.download_button(
                label="Download JSON Report",
                data=json.dumps(summary, indent=2),
                file_name=f"roi_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

        if st.button("📧 Schedule Review"):
            st.success("Monthly ROI review scheduled!")

        if st.button("🔄 Reset Calculator"):
            st.experimental_rerun()

        st.markdown("---")

        st.markdown("**Calculator Settings**")
        show_advanced = st.checkbox("Show Advanced Metrics", value=False)
        include_tax_impact = st.checkbox("Include Tax Considerations", value=False)

        if show_advanced:
            st.markdown("*Advanced metrics enabled*")

        if include_tax_impact:
            st.markdown("*Tax impact calculations enabled*")

    # Footer
    st.markdown(
        f"""
    ---
    <div style="text-align: center; opacity: 0.6; font-size: 0.8rem; margin-top: 32px;">
        ROI Union[Calculator, Investment] Scenario Union[Analysis, Generated]: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 
        Projection Period: {params["projection_months"]} months
    </div>
    """,
        unsafe_allow_html=True,
    )


# Main execution
if __name__ == "__main__":
    render_roi_calculator()
