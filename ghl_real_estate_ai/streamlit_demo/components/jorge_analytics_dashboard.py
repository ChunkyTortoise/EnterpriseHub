"""
Jorge's Advanced Analytics Dashboard - Business Intelligence & Forecasting

Complete analytics system integrating:
- Real-time Revenue Forecasting
- Conversion Funnel Analysis
- Geographic Performance Analytics
- Lead Quality Intelligence
- Market Timing Optimization
- ROI Attribution Analysis

Built specifically for Jorge's GHL Real Estate AI system.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

# Add the services directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../services"))

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Import the analytics service
try:
    from ghl_real_estate_ai.services.jorge_analytics_service import JorgeAnalyticsService

    ANALYTICS_SERVICE_AVAILABLE = True
except ImportError:
    ANALYTICS_SERVICE_AVAILABLE = False


# Mock Analytics API Client for development
class JorgeAnalyticsAPIClient:
    """Client for Jorge's Advanced Analytics API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def get_analytics_dashboard_metrics(self) -> Dict[str, Any]:
        """Get unified analytics dashboard metrics."""
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(f"{self.base_url}/jorge-analytics/dashboard/metrics")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error getting analytics dashboard metrics: {e}")
            pass

        # Mock data for demo
        import random

        now = datetime.now()

        return {
            "revenue_forecast": {
                "current_month_revenue": random.randint(180000, 250000),
                "forecasted_revenue": random.randint(220000, 280000),
                "confidence_level": random.uniform(0.82, 0.94),
                "confidence_lower": random.randint(200000, 240000),
                "confidence_upper": random.randint(260000, 700000),
                "predicted_conversions": random.randint(45, 65),
                "model_accuracy": random.uniform(0.85, 0.92),
                "growth_rate": random.uniform(0.12, 0.28),
            },
            "conversion_funnel": {
                "leads_generated": random.randint(450, 650),
                "qualified_leads": random.randint(320, 420),
                "appointments_set": random.randint(180, 240),
                "showings_completed": random.randint(120, 180),
                "offers_made": random.randint(45, 75),
                "contracts_signed": random.randint(25, 45),
                "closings": random.randint(18, 35),
                "funnel_efficiency": random.uniform(0.65, 0.82),
                "bottleneck_stage": random.choice(
                    ["qualified_leads", "appointments_set", "showings_completed", "offers_made"]
                ),
            },
            "geographic_performance": {
                "rancho_cucamonga": {
                    "revenue": random.randint(85000, 125000),
                    "conversions": random.randint(12, 20),
                    "avg_deal_size": random.randint(750000, 950000),
                    "market_share": random.uniform(0.15, 0.28),
                },
                "upland": {
                    "revenue": random.randint(45000, 75000),
                    "conversions": random.randint(8, 14),
                    "avg_deal_size": random.randint(650000, 850000),
                    "market_share": random.uniform(0.10, 0.22),
                },
                "ontario": {
                    "revenue": random.randint(35000, 65000),
                    "conversions": random.randint(6, 12),
                    "avg_deal_size": random.randint(550000, 750000),
                    "market_share": random.uniform(0.08, 0.18),
                },
            },
            "lead_quality_metrics": {
                "avg_lead_score": random.uniform(68.5, 78.2),
                "score_trend": random.uniform(0.03, 0.08),
                "high_quality_percentage": random.uniform(0.32, 0.48),
                "speed_to_lead": random.randint(5, 15),  # New KPI: Seconds
                "appointment_rate": random.uniform(0.18, 0.25),  # New KPI: %
                "cma_value_variance": random.randint(15000, 45000),  # New KPI: $
                "conversion_by_score": {
                    "90-100": random.uniform(0.82, 0.95),
                    "80-89": random.uniform(0.65, 0.78),
                    "70-79": random.uniform(0.48, 0.62),
                    "60-69": random.uniform(0.28, 0.42),
                    "50-59": random.uniform(0.12, 0.25),
                },
            },
            "market_timing": {
                "optimal_contact_time": random.choice(["2:00-4:00 PM", "10:00 AM-12:00 PM", "6:00-8:00 PM"]),
                "best_day_of_week": random.choice(["Tuesday", "Wednesday", "Thursday"]),
                "seasonal_factor": random.uniform(0.85, 1.15),
                "market_velocity_score": random.uniform(72, 88),
                "timing_optimization_impact": random.uniform(0.18, 0.35),
            },
            "roi_attribution": {
                "facebook_ads": {
                    "spend": random.randint(8000, 15000),
                    "revenue": random.randint(45000, 85000),
                    "roi": random.uniform(3.2, 6.8),
                    "conversions": random.randint(8, 16),
                },
                "google_ads": {
                    "spend": random.randint(12000, 18000),
                    "revenue": random.randint(55000, 95000),
                    "roi": random.uniform(2.8, 5.9),
                    "conversions": random.randint(10, 18),
                },
                "zillow": {
                    "spend": random.randint(6000, 12000),
                    "revenue": random.randint(35000, 65000),
                    "roi": random.uniform(4.1, 7.2),
                    "conversions": random.randint(6, 14),
                },
                "referrals": {
                    "spend": random.randint(2000, 5000),
                    "revenue": random.randint(25000, 55000),
                    "roi": random.uniform(8.2, 15.5),
                    "conversions": random.randint(5, 12),
                },
            },
            "system_health": {
                "analytics_engine": "healthy",
                "forecasting_model": "healthy",
                "data_pipeline": "healthy",
                "overall_uptime": random.uniform(98.5, 99.8),
            },
            "last_updated": now.isoformat(),
        }

    async def get_revenue_forecast(self, horizon_days: int = 30) -> Dict[str, Any]:
        """Get detailed revenue forecasting data."""
        import random

        # Generate historical data
        base_date = datetime.now() - timedelta(days=90)
        historical_dates = [base_date + timedelta(days=i) for i in range(90)]
        historical_revenue = [random.randint(6000, 15000) for _ in range(90)]

        # Generate forecast data
        forecast_start = datetime.now()
        forecast_dates = [forecast_start + timedelta(days=i) for i in range(horizon_days)]

        # Trend-based forecasting with seasonality
        base_revenue = historical_revenue[-1]
        forecast_revenue = []

        for i in range(horizon_days):
            # Add trend and seasonality
            trend_factor = 1 + (0.02 * i / 30)  # 2% monthly growth
            seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * i / 30)  # Monthly cycle
            noise = random.uniform(0.9, 1.1)

            forecasted = base_revenue * trend_factor * seasonal_factor * noise
            forecast_revenue.append(forecasted)

        # Generate confidence intervals
        confidence_upper = [f * random.uniform(1.1, 1.25) for f in forecast_revenue]
        confidence_lower = [f * random.uniform(0.75, 0.9) for f in forecast_revenue]

        return {
            "horizon_days": horizon_days,
            "historical": {"dates": [d.isoformat() for d in historical_dates], "revenue": historical_revenue},
            "forecast": {
                "dates": [d.isoformat() for d in forecast_dates],
                "revenue": forecast_revenue,
                "confidence_upper": confidence_upper,
                "confidence_lower": confidence_lower,
            },
            "metrics": {
                "total_forecasted": sum(forecast_revenue),
                "average_daily": sum(forecast_revenue) / horizon_days,
                "confidence_level": random.uniform(0.82, 0.94),
                "model_accuracy": random.uniform(0.85, 0.92),
            },
        }

    async def get_funnel_analysis(self) -> Dict[str, Any]:
        """Get detailed conversion funnel analysis."""
        import random

        return {
            "current_period": {
                "leads_generated": 580,
                "qualified_leads": 395,
                "appointments_set": 210,
                "showings_completed": 156,
                "offers_made": 62,
                "contracts_signed": 34,
                "closings": 24,
            },
            "previous_period": {
                "leads_generated": 542,
                "qualified_leads": 368,
                "appointments_set": 185,
                "showings_completed": 142,
                "offers_made": 58,
                "contracts_signed": 31,
                "closings": 22,
            },
            "conversion_rates": {
                "lead_to_qualified": 0.681,
                "qualified_to_appointment": 0.532,
                "appointment_to_showing": 0.743,
                "showing_to_offer": 0.397,
                "offer_to_contract": 0.548,
                "contract_to_closing": 0.706,
            },
            "bottlenecks": [
                {
                    "stage": "showing_to_offer",
                    "conversion_rate": 0.397,
                    "improvement_potential": 0.15,
                    "recommended_actions": [
                        "Implement follow-up automation within 2 hours of showing",
                        "Provide market urgency data during showings",
                        "Create custom offer templates for quick turnaround",
                    ],
                }
            ],
            "optimization_opportunities": {
                "total_potential_increase": 0.28,
                "priority_stages": ["showing_to_offer", "offer_to_contract"],
                "estimated_additional_closings": 8,
            },
            "stage_performance_trends": {
                "dates": [(datetime.now() - timedelta(days=i)).isoformat() for i in range(30, 0, -1)],
                "qualified_rate": [random.uniform(0.60, 0.75) for _ in range(30)],
                "closing_rate": [random.uniform(0.03, 0.07) for _ in range(30)],
            },
        }

    async def get_geographic_analytics(self) -> Dict[str, Any]:
        """Get geographic performance analytics."""

        return {
            "market_analysis": {
                "rancho_cucamonga": {
                    "revenue": 112000,
                    "conversions": 16,
                    "avg_deal_size": 875000,
                    "market_share": 0.24,
                    "growth_rate": 0.18,
                    "competition_density": "medium",
                    "opportunity_score": 87,
                },
                "upland": {
                    "revenue": 68000,
                    "conversions": 11,
                    "avg_deal_size": 720000,
                    "market_share": 0.19,
                    "growth_rate": 0.12,
                    "competition_density": "high",
                    "opportunity_score": 74,
                },
                "ontario": {
                    "revenue": 52000,
                    "conversions": 9,
                    "avg_deal_size": 680000,
                    "market_share": 0.15,
                    "growth_rate": 0.08,
                    "competition_density": "high",
                    "opportunity_score": 68,
                },
                "claremont": {
                    "revenue": 45000,
                    "conversions": 6,
                    "avg_deal_size": 950000,
                    "market_share": 0.12,
                    "growth_rate": 0.22,
                    "competition_density": "low",
                    "opportunity_score": 82,
                },
            },
            "heatmap_data": {
                "zip_codes": ["91701", "91730", "91737", "91739", "91741", "91762", "91786"],
                "performance_scores": [87, 74, 68, 82, 65, 79, 71],
                "lead_density": [145, 98, 76, 62, 89, 112, 83],
            },
            "expansion_opportunities": [
                {
                    "area": "Claremont",
                    "opportunity_score": 82,
                    "rationale": "Low competition, high deal values, growing market",
                    "recommended_investment": 15000,
                    "projected_roi": 4.2,
                },
                {
                    "area": "San Dimas",
                    "opportunity_score": 76,
                    "rationale": "Emerging market, family demographics align with expertise",
                    "recommended_investment": 12000,
                    "projected_roi": 3.8,
                },
            ],
        }


# Initialize clients
@st.cache_resource
def get_analytics_api_client():
    return JorgeAnalyticsAPIClient()


@st.cache_resource
def get_analytics_service():
    if ANALYTICS_SERVICE_AVAILABLE:
        return JorgeAnalyticsService()
    return None


def render_analytics_dashboard_css():
    """Inject custom CSS for analytics dashboard - Jorge Professional Edition"""
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');

    /* Jorge Analytics Dashboard Styles */
    .analytics-container {
        background: rgba(5, 7, 10, 0.8) !important;
        border-radius: 20px;
        padding: 2.5rem;
        margin: 1rem 0;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9);
        border: 1px solid rgba(30, 136, 229, 0.1);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(20px);
    }

    .analytics-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 10% 10%, rgba(30, 136, 229, 0.05) 0%, transparent 50%),
                    radial-gradient(circle at 90% 90%, rgba(16, 185, 129, 0.03) 0%, transparent 50%);
        pointer-events: none;
    }

    .dashboard-header {
        text-align: left;
        color: white;
        margin-bottom: 3rem;
        position: relative;
        z-index: 1;
        border-bottom: 1px solid rgba(30, 136, 229, 0.2);
        padding-bottom: 2rem;
    }

    .dashboard-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        color: #1E88E5;
        letter-spacing: -0.04em;
        text-transform: uppercase;
    }

    .dashboard-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        margin: 0.75rem 0 0 0;
        color: #8B949E;
        font-weight: 500;
        letter-spacing: 0.02em;
    }

    .analytics-kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }

    .analytics-kpi-card {
        background: rgba(22, 27, 34, 0.7) !important;
        border-radius: 12px;
        padding: 1.75rem;
        text-align: left;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(30, 136, 229, 0.1);
        border-top: 1px solid rgba(30, 136, 229, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .analytics-kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 48px rgba(30, 136, 229, 0.3);
        border-color: rgba(30, 136, 229, 0.4);
    }

    .analytics-kpi-icon {
        font-size: 1.75rem;
        margin-bottom: 1.25rem;
        background: rgba(30, 136, 229, 0.1);
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
        border: 1px solid rgba(30, 136, 229, 0.2);
    }

    .analytics-kpi-value {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin: 0.5rem 0;
        text-shadow: 0 0 15px rgba(30, 136, 229, 0.3);
    }

    .analytics-kpi-label {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.75rem;
        color: #8B949E;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .analytics-kpi-change {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        margin-top: 0.75rem;
    }

    .analytics-kpi-change.positive {
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .analytics-kpi-change.negative {
        background: rgba(239, 68, 68, 0.1);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }

    .analytics-chart-section {
        background: rgba(22, 27, 34, 0.6) !important;
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(30, 136, 229, 0.1);
    }

    .chart-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.25rem;
        font-weight: 700;
        color: #1E88E5;
        margin: 0 0 1.5rem 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .funnel-stage {
        display: flex;
        align-items: center;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        background: rgba(30, 136, 229, 0.05);
        border-radius: 8px;
        border: 1px solid rgba(30, 136, 229, 0.1);
        transition: all 0.3s ease;
    }

    .funnel-stage:hover {
        background: rgba(30, 136, 229, 0.1);
        border-color: rgba(30, 136, 229, 0.2);
    }

    .stage-name {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        color: #FFFFFF;
        flex: 1;
    }

    .stage-value {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        color: #1E88E5;
        margin: 0 1rem;
    }

    .stage-rate {
        font-size: 0.9rem;
        color: #8B949E;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_revenue_forecasting_section(api_client: JorgeAnalyticsAPIClient):
    """Render the Revenue Forecasting section."""
    st.header("💰 Revenue Forecasting Engine")
    st.markdown("**AI-powered revenue predictions with confidence intervals**")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🔮 Forecast Configuration")

        # Forecast parameters
        horizon_days = st.selectbox(
            "Forecast Horizon", [30, 60, 90, 120], index=0, help="Number of days to forecast ahead"
        )

        confidence_level = st.slider(
            "Confidence Level",
            min_value=0.80,
            max_value=0.99,
            value=0.85,
            step=0.01,
            format="%.0f%%",
            help="Statistical confidence for prediction intervals",
        )

        include_seasonality = st.checkbox(
            "Include Seasonality", value=True, help="Account for seasonal market patterns"
        )

        if st.button("🚀 Generate Forecast", type="primary", use_container_width=True):
            with st.spinner("🧠 Analyzing market patterns and generating forecast..."):
                forecast_data = run_async(api_client.get_revenue_forecast(horizon_days))
                st.session_state["forecast_data"] = forecast_data
                st.success("✅ Revenue forecast generated successfully!")

    with col2:
        st.subheader("📈 Forecast Results")

        # Display forecast if available
        if "forecast_data" in st.session_state:
            forecast_data = st.session_state["forecast_data"]

            # Key metrics
            metrics = forecast_data["metrics"]
            col_m1, col_m2 = st.columns(2)

            with col_m1:
                st.metric(
                    "Total Forecasted",
                    f"${metrics['total_forecasted']:,.0f}",
                    delta=f"${metrics['average_daily']:,.0f}/day",
                )

            with col_m2:
                st.metric(
                    "Model Confidence",
                    f"{metrics['confidence_level']:.1%}",
                    delta=f"{metrics['model_accuracy']:.1%} accuracy",
                )

            # Create forecasting chart
            historical = forecast_data["historical"]
            forecast = forecast_data["forecast"]

            fig = go.Figure()

            # Historical data
            fig.add_trace(
                go.Scatter(
                    x=historical["dates"],
                    y=historical["revenue"],
                    mode="lines",
                    name="Historical Revenue",
                    line=dict(color="#8B949E", width=2),
                )
            )

            # Forecast data
            fig.add_trace(
                go.Scatter(
                    x=forecast["dates"],
                    y=forecast["revenue"],
                    mode="lines",
                    name="Forecasted Revenue",
                    line=dict(color="#1E88E5", width=3),
                )
            )

            # Confidence intervals
            fig.add_trace(
                go.Scatter(
                    x=forecast["dates"] + forecast["dates"][::-1],
                    y=forecast["confidence_upper"] + forecast["confidence_lower"][::-1],
                    fill="toself",
                    fillcolor="rgba(30, 136, 229, 0.2)",
                    line=dict(color="rgba(255,255,255,0)"),
                    name=f"{confidence_level:.0%} Confidence Interval",
                )
            )

            fig.update_layout(
                title="Revenue Forecast with Confidence Intervals",
                xaxis_title="Date",
                yaxis_title="Daily Revenue ($)",
                height=400,
                showlegend=True,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("👆 Configure and generate a forecast above to see detailed predictions")


def render_conversion_funnel_section(api_client: JorgeAnalyticsAPIClient):
    """Render the Conversion Funnel Analysis section."""
    st.header("🎯 Conversion Funnel Analysis")
    st.markdown("**Identify bottlenecks and optimize conversion rates**")

    # Get funnel data
    funnel_data = run_async(api_client.get_funnel_analysis())

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Funnel Performance")

        # Funnel stages
        current = funnel_data["current_period"]
        conversion_rates = funnel_data["conversion_rates"]

        stages = [
            ("Leads Generated", current["leads_generated"], None),
            ("Qualified Leads", current["qualified_leads"], conversion_rates["lead_to_qualified"]),
            ("Appointments Set", current["appointments_set"], conversion_rates["qualified_to_appointment"]),
            ("Showings Completed", current["showings_completed"], conversion_rates["appointment_to_showing"]),
            ("Offers Made", current["offers_made"], conversion_rates["showing_to_offer"]),
            ("Offers Accepted", int(current["offers_made"] * 0.6), 0.60),
            ("Escrow / Under Contract", current["under_contract"], 0.85),
            ("Closings", current["closings"], conversion_rates["contract_to_closing"]),
        ]

        # Render funnel stages
        for i, (stage_name, count, rate) in enumerate(stages):
            rate_display = f"{rate:.1%}" if rate else "—"

            # Color code based on performance
            if rate and rate < 0.4:
                border_color = "rgba(239, 68, 68, 0.3)"  # Red for poor performance
            elif rate and rate > 0.7:
                border_color = "rgba(16, 185, 129, 0.3)"  # Green for good performance
            else:
                border_color = "rgba(30, 136, 229, 0.1)"  # Blue default

            st.markdown(
                f"""
            <div class="funnel-stage" style="border-color: {border_color};">
                <div class="stage-name">{stage_name}</div>
                <div class="stage-value">{count:,}</div>
                <div class="stage-rate">{rate_display}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Add conversion arrow between stages
            if i < len(stages) - 1:
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;↓")

        # Bottleneck analysis
        st.subheader("🚨 Bottleneck Analysis")
        bottlenecks = funnel_data["bottlenecks"]

        for bottleneck in bottlenecks:
            st.error(f"**Bottleneck Identified**: {bottleneck['stage'].replace('_', ' ').title()}")
            st.write(f"Current conversion rate: {bottleneck['conversion_rate']:.1%}")
            st.write(f"Improvement potential: +{bottleneck['improvement_potential']:.1%}")

            st.markdown("**Recommended Actions:**")
            for action in bottleneck["recommended_actions"]:
                st.markdown(f"• {action}")

    with col2:
        st.subheader("📈 Optimization Impact")

        optimization = funnel_data["optimization_opportunities"]

        st.metric(
            "Potential Revenue Increase",
            f"{optimization['total_potential_increase']:.1%}",
            help="Estimated revenue increase from funnel optimization",
        )

        st.metric(
            "Additional Closings/Month",
            f"+{optimization['estimated_additional_closings']}",
            help="Extra closings possible with optimization",
        )

        # Priority stages
        st.markdown("**Priority Optimization Stages:**")
        for stage in optimization["priority_stages"]:
            st.markdown(f"• {stage.replace('_', ' ').title()}")

        # Performance trends
        st.subheader("📊 Trend Analysis")
        trends = funnel_data["stage_performance_trends"]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=trends["dates"],
                y=[rate * 100 for rate in trends["qualified_rate"]],
                mode="lines+markers",
                name="Qualification Rate",
                line=dict(color="#1E88E5", width=2),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=trends["dates"],
                y=[rate * 100 for rate in trends["closing_rate"]],
                mode="lines+markers",
                name="Closing Rate",
                line=dict(color="#10b981", width=2),
            )
        )

        fig.update_layout(
            title="Conversion Rate Trends (30 Days)",
            xaxis_title="Date",
            yaxis_title="Conversion Rate (%)",
            height=300,
            showlegend=True,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )

        st.plotly_chart(fig, use_container_width=True)


def render_geographic_analytics_section(api_client: JorgeAnalyticsAPIClient):
    """Render the Geographic Analytics section."""
    st.header("🗺️ Geographic Performance Analytics")
    st.markdown("**Market-specific insights and expansion opportunities**")

    # Get geographic data
    geo_data = run_async(api_client.get_geographic_analytics())

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📍 Market Performance")

        # Create market comparison chart
        market_analysis = geo_data["market_analysis"]

        markets = list(market_analysis.keys())
        revenues = [market_analysis[market]["revenue"] for market in markets]
        conversions = [market_analysis[market]["conversions"] for market in markets]
        opportunity_scores = [market_analysis[market]["opportunity_score"] for market in markets]

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Revenue by Market",
                "Conversions by Market",
                "Opportunity Score vs Market Share",
                "Market Performance Heatmap",
            ),
            specs=[[{"type": "bar"}, {"type": "bar"}], [{"type": "scatter"}, {"type": "bar"}]],
        )

        # Revenue chart
        fig.add_trace(go.Bar(x=markets, y=revenues, name="Revenue", marker_color="#1E88E5"), row=1, col=1)

        # Conversions chart
        fig.add_trace(go.Bar(x=markets, y=conversions, name="Conversions", marker_color="#10b981"), row=1, col=2)

        # Opportunity vs Market Share scatter
        market_shares = [market_analysis[market]["market_share"] * 100 for market in markets]
        fig.add_trace(
            go.Scatter(
                x=market_shares,
                y=opportunity_scores,
                mode="markers+text",
                text=markets,
                textposition="top center",
                marker=dict(size=10, color="#f59e0b"),
                name="Markets",
            ),
            row=2,
            col=1,
        )

        # Performance heatmap data
        growth_rates = [market_analysis[market]["growth_rate"] * 100 for market in markets]
        fig.add_trace(go.Bar(x=markets, y=growth_rates, name="Growth Rate (%)", marker_color="#8b5cf6"), row=2, col=2)

        fig.update_layout(
            height=600,
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎯 Market Insights")

        # Top performing market
        top_market = max(market_analysis.keys(), key=lambda x: market_analysis[x]["opportunity_score"])
        top_data = market_analysis[top_market]

        st.success(f"**Top Market**: {top_market.title()}")
        st.metric("Opportunity Score", f"{top_data['opportunity_score']}/100")
        st.metric("Market Share", f"{top_data['market_share']:.1%}")
        st.metric("Growth Rate", f"{top_data['growth_rate']:.1%}")

        st.divider()

        # Expansion opportunities
        st.subheader("🚀 Expansion Opportunities")

        opportunities = geo_data["expansion_opportunities"]
        for opp in opportunities:
            with st.expander(f"📍 {opp['area']} (Score: {opp['opportunity_score']})"):
                st.write(f"**Rationale**: {opp['rationale']}")
                st.metric("Recommended Investment", f"${opp['recommended_investment']:,}")
                st.metric("Projected ROI", f"{opp['projected_roi']:.1f}x")

        st.divider()

        # ZIP code performance
        st.subheader("📬 ZIP Code Performance")

        heatmap_data = geo_data["heatmap_data"]
        zip_performance = list(
            zip(heatmap_data["zip_codes"], heatmap_data["performance_scores"], heatmap_data["lead_density"])
        )

        # Sort by performance score
        zip_performance.sort(key=lambda x: x[1], reverse=True)

        for zip_code, score, density in zip_performance[:5]:
            st.markdown(f"**{zip_code}**: {score}/100 ({density} leads)")


def render_lead_quality_intelligence_section(api_client: JorgeAnalyticsAPIClient):
    """Render the Lead Quality Intelligence section."""
    st.header("🧠 Lead Quality Intelligence")
    st.markdown("**AI-driven insights into lead scoring and quality trends**")

    # Get dashboard metrics for lead quality
    dashboard_metrics = run_async(api_client.get_analytics_dashboard_metrics())
    quality_metrics = dashboard_metrics["lead_quality_metrics"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Quality Metrics")

        # Key quality KPIs
        st.metric(
            "Average Lead Score",
            f"{quality_metrics['avg_lead_score']:.1f}/100",
            delta=f"+{quality_metrics['score_trend']:.1%} vs last month",
        )

        st.metric(
            "High Quality Leads",
            f"{quality_metrics['high_quality_percentage']:.1%}",
            help="Percentage of leads scoring 80+ points",
        )

        # Score distribution
        st.subheader("📈 Score Distribution")
        conversion_by_score = quality_metrics["conversion_by_score"]

        score_ranges = list(conversion_by_score.keys())
        conversion_rates = [rate * 100 for rate in conversion_by_score.values()]

        fig = px.bar(
            x=score_ranges,
            y=conversion_rates,
            title="Conversion Rate by Lead Score Range",
            labels={"x": "Score Range", "y": "Conversion Rate (%)"},
            color=conversion_rates,
            color_continuous_scale="RdYlGn",
        )

        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎯 Quality Analysis")

        # Quality insights
        insights = [
            {
                "metric": "Avg Speed to Lead",
                "value": f"{quality_metrics['speed_to_lead']}s",
                "insight": "Time from inbound inquiry to first bot response",
            },
            {
                "metric": "CMA Engagement Rate",
                "value": "74.2%",
                "insight": "Percentage of leads who interact with the AI-generated CMA",
            },
            {
                "metric": "Lead Score Correlation",
                "value": "87.2%",
                "insight": "Strong correlation between lead score and conversion probability",
            },
            {"metric": "Score Accuracy", "value": "91.4%", "insight": "High-scoring leads convert at predicted rates"},
        ]

        for insight in insights:
            with st.container():
                col_metric, col_value = st.columns([2, 1])
                with col_metric:
                    st.write(f"**{insight['metric']}**")
                    st.caption(insight["insight"])
                with col_value:
                    st.metric("", insight["value"])
                st.divider()

        # Quality improvement recommendations
        st.subheader("💡 Improvement Recommendations")

        recommendations = [
            "Focus marketing spend on channels generating 80+ score leads",
            "Implement rapid response for leads scoring 90+",
            "Develop nurture sequences for 60-79 score range",
            "Consider disqualifying leads consistently scoring <40",
        ]

        for rec in recommendations:
            st.markdown(f"• {rec}")


def render_roi_attribution_section(api_client: JorgeAnalyticsAPIClient):
    """Render the ROI Attribution Analysis section."""
    st.header("💵 ROI Attribution Analysis")
    st.markdown("**Comprehensive marketing channel performance and attribution insights**")

    # Get dashboard metrics for ROI data
    dashboard_metrics = run_async(api_client.get_analytics_dashboard_metrics())
    roi_attribution = dashboard_metrics["roi_attribution"]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Channel Performance Overview")

        # Create ROI comparison chart
        channels = list(roi_attribution.keys())
        spend_data = [roi_attribution[channel]["spend"] for channel in channels]
        revenue_data = [roi_attribution[channel]["revenue"] for channel in channels]
        roi_data = [roi_attribution[channel]["roi"] for channel in channels]
        conversions_data = [roi_attribution[channel]["conversions"] for channel in channels]

        # Multi-metric comparison chart
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=("ROI by Channel", "Revenue vs Spend", "Conversion Performance", "Channel Efficiency"),
            specs=[[{"type": "bar"}, {"type": "scatter"}], [{"type": "bar"}, {"type": "bar"}]],
        )

        # ROI chart
        colors = ["#3498DB", "#2ECC71", "#F39C12", "#E74C3C"]
        fig.add_trace(
            go.Bar(
                x=channels,
                y=roi_data,
                name="ROI",
                marker_color=colors,
                text=[f"{roi:.1f}x" for roi in roi_data],
                textposition="auto",
            ),
            row=1,
            col=1,
        )

        # Revenue vs Spend scatter
        fig.add_trace(
            go.Scatter(
                x=spend_data,
                y=revenue_data,
                mode="markers+text",
                text=channels,
                textposition="top center",
                marker=dict(
                    size=[conv / 2 for conv in conversions_data],
                    color=roi_data,
                    colorscale="RdYlGn",
                    showscale=True,
                    colorbar=dict(title="ROI"),
                ),
                name="Revenue vs Spend",
            ),
            row=1,
            col=2,
        )

        # Conversions chart
        fig.add_trace(go.Bar(x=channels, y=conversions_data, name="Conversions", marker_color="#8b5cf6"), row=2, col=1)

        # Efficiency (Revenue per dollar spent)
        efficiency = [revenue / spend for revenue, spend in zip(revenue_data, spend_data)]
        fig.add_trace(go.Bar(x=channels, y=efficiency, name="Revenue/$Spent", marker_color="#f59e0b"), row=2, col=2)

        fig.update_layout(
            height=600,
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎯 Channel Rankings")

        # Rank channels by ROI
        channel_performance = []
        for channel in channels:
            data = roi_attribution[channel]
            channel_performance.append(
                {
                    "channel": channel.replace("_", " ").title(),
                    "roi": data["roi"],
                    "revenue": data["revenue"],
                    "spend": data["spend"],
                    "conversions": data["conversions"],
                    "cost_per_conversion": data["spend"] / data["conversions"] if data["conversions"] > 0 else 0,
                }
            )

        # Sort by ROI
        channel_performance.sort(key=lambda x: x["roi"], reverse=True)

        for i, channel in enumerate(channel_performance):
            rank_colors = ["🥇", "🥈", "🥉", "4️⃣"]
            rank_icon = rank_colors[i] if i < len(rank_colors) else "📊"

            with st.container():
                st.markdown(
                    f"""
                <div style="
                    background: rgba(22, 27, 34, 0.6);
                    border-radius: 8px;
                    padding: 1rem;
                    margin: 0.5rem 0;
                    border: 1px solid rgba(30, 136, 229, 0.1);
                ">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.2rem; margin-right: 0.5rem;">{rank_icon}</span>
                        <span style="font-weight: 600; color: #FFFFFF;">{channel["channel"]}</span>
                    </div>
                    <div style="font-size: 0.9rem; color: #8B949E;">
                        <div><strong>ROI:</strong> {channel["roi"]:.1f}x</div>
                        <div><strong>Revenue:</strong> ${channel["revenue"]:,}</div>
                        <div><strong>Cost/Conversion:</strong> ${channel["cost_per_conversion"]:,.0f}</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    # Detailed Channel Analysis
    st.divider()
    st.subheader("🔍 Detailed Channel Analysis")

    # Channel selection for deep dive
    selected_channel = st.selectbox(
        "Select Channel for Deep Analysis", options=channels, format_func=lambda x: x.replace("_", " ").title()
    )

    if selected_channel:
        channel_data = roi_attribution[selected_channel]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Spend", f"${channel_data['spend']:,}")
            st.metric("Total Revenue", f"${channel_data['revenue']:,}")

        with col2:
            st.metric("ROI", f"{channel_data['roi']:.1f}x")
            st.metric("Conversions", f"{channel_data['conversions']}")

        with col3:
            cost_per_conversion = (
                channel_data["spend"] / channel_data["conversions"] if channel_data["conversions"] > 0 else 0
            )
            revenue_per_conversion = (
                channel_data["revenue"] / channel_data["conversions"] if channel_data["conversions"] > 0 else 0
            )
            st.metric("Cost per Conversion", f"${cost_per_conversion:,.0f}")
            st.metric("Revenue per Conversion", f"${revenue_per_conversion:,.0f}")

        # Channel-specific insights and recommendations
        channel_insights = {
            "facebook_ads": {
                "strengths": ["High engagement rates", "Excellent targeting options", "Visual content performs well"],
                "opportunities": ["Optimize ad creative rotation", "Expand lookalike audiences", "Test video formats"],
                "recommendations": [
                    "Increase budget by 15%",
                    "Focus on conversion campaigns",
                    "A/B test landing pages",
                ],
            },
            "google_ads": {
                "strengths": ["High intent traffic", "Broad reach", "Strong conversion tracking"],
                "opportunities": ["Improve Quality Score", "Expand keyword targeting", "Optimize ad extensions"],
                "recommendations": ["Refine negative keywords", "Test responsive search ads", "Increase mobile bids"],
            },
            "zillow": {
                "strengths": ["High-quality leads", "Ready-to-buy audience", "Local market focus"],
                "opportunities": ["Improve response time", "Enhance profile optimization", "Better lead nurturing"],
                "recommendations": [
                    "Upgrade to Premier Agent",
                    "Optimize profile photos",
                    "Implement instant response",
                ],
            },
            "referrals": {
                "strengths": ["Highest ROI", "Pre-qualified leads", "Trust factor"],
                "opportunities": ["Systematize referral process", "Expand referral network", "Improve tracking"],
                "recommendations": [
                    "Launch referral rewards program",
                    "Create referral marketing materials",
                    "Automate follow-up sequences",
                ],
            },
        }

        insights = channel_insights.get(
            selected_channel,
            {
                "strengths": ["Strong performance metrics"],
                "opportunities": ["Continue optimization"],
                "recommendations": ["Monitor and adjust strategy"],
            },
        )

        col_insights1, col_insights2, col_insights3 = st.columns(3)

        with col_insights1:
            st.markdown("**💪 Strengths**")
            for strength in insights["strengths"]:
                st.markdown(f"• {strength}")

        with col_insights2:
            st.markdown("**🎯 Opportunities**")
            for opportunity in insights["opportunities"]:
                st.markdown(f"• {opportunity}")

        with col_insights3:
            st.markdown("**💡 Recommendations**")
            for recommendation in insights["recommendations"]:
                st.markdown(f"• {recommendation}")

    # ROI Optimization Simulator
    st.divider()
    st.subheader("🚀 ROI Optimization Simulator")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**Budget Reallocation Simulator**")

        total_current_spend = sum(roi_attribution[channel]["spend"] for channel in channels)

        st.write(f"Current Total Budget: ${total_current_spend:,}")

        # Budget sliders for each channel
        new_budgets = {}
        for channel in channels:
            current_spend = roi_attribution[channel]["spend"]
            current_percentage = (current_spend / total_current_spend) * 100

            new_percentage = st.slider(
                f"{channel.replace('_', ' ').title()} Budget %",
                min_value=0.0,
                max_value=100.0,
                value=current_percentage,
                step=1.0,
                key=f"budget_{channel}",
            )
            new_budgets[channel] = total_current_spend * new_percentage / 100

    with col2:
        st.markdown("**Projected Impact**")

        # Calculate projected performance with new budget allocation
        total_projected_revenue = 0
        total_projected_conversions = 0

        for channel in channels:
            current_data = roi_attribution[channel]
            new_budget = new_budgets[channel]

            # Simple linear scaling assumption (in reality this would be more complex)
            scaling_factor = new_budget / current_data["spend"] if current_data["spend"] > 0 else 1

            projected_revenue = current_data["revenue"] * scaling_factor
            projected_conversions = current_data["conversions"] * scaling_factor

            total_projected_revenue += projected_revenue
            total_projected_conversions += projected_conversions

        current_total_revenue = sum(roi_attribution[channel]["revenue"] for channel in channels)
        current_total_conversions = sum(roi_attribution[channel]["conversions"] for channel in channels)

        # Display projected results
        revenue_change = ((total_projected_revenue - current_total_revenue) / current_total_revenue) * 100
        conversion_change = (
            (total_projected_conversions - current_total_conversions) / current_total_conversions
        ) * 100

        st.metric("Projected Revenue", f"${total_projected_revenue:,.0f}", delta=f"{revenue_change:+.1f}%")

        st.metric("Projected Conversions", f"{total_projected_conversions:.0f}", delta=f"{conversion_change:+.1f}%")

        projected_roi = total_projected_revenue / total_current_spend if total_current_spend > 0 else 0
        current_roi = current_total_revenue / total_current_spend if total_current_spend > 0 else 0
        roi_change = ((projected_roi - current_roi) / current_roi) * 100 if current_roi > 0 else 0

        st.metric("Projected Overall ROI", f"{projected_roi:.1f}x", delta=f"{roi_change:+.1f}%")

        # Show optimization recommendation
        best_channel = max(channels, key=lambda c: roi_attribution[c]["roi"])
        worst_channel = min(channels, key=lambda c: roi_attribution[c]["roi"])

        st.info(f"""
        💡 **Optimization Insight**:
        Consider reallocating budget from {worst_channel.replace("_", " ").title()}
        (ROI: {roi_attribution[worst_channel]["roi"]:.1f}x) to {best_channel.replace("_", " ").title()}
        (ROI: {roi_attribution[best_channel]["roi"]:.1f}x) for improved overall performance.
        """)


def render_analytics_integration_dashboard(api_client: JorgeAnalyticsAPIClient):
    """Render the unified analytics integration dashboard."""
    st.header("📊 Jorge's Analytics Command Center")
    st.markdown("**Real-time business intelligence and forecasting overview**")

    # Get dashboard metrics
    metrics = run_async(api_client.get_analytics_dashboard_metrics())

    # System health indicators
    st.subheader("🚀 Analytics Engine Health")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        analytics_status = metrics["system_health"]["analytics_engine"]
        status_icon = "🟢" if analytics_status == "healthy" else "🔴"
        st.metric("Analytics Engine", f"{status_icon} {analytics_status.title()}")

    with col2:
        forecasting_status = metrics["system_health"]["forecasting_model"]
        status_icon = "🟢" if forecasting_status == "healthy" else "🔴"
        st.metric("Forecasting Model", f"{status_icon} {forecasting_status.title()}")

    with col3:
        pipeline_status = metrics["system_health"]["data_pipeline"]
        status_icon = "🟢" if pipeline_status == "healthy" else "🔴"
        st.metric("Data Pipeline", f"{status_icon} {pipeline_status.title()}")

    with col4:
        st.metric("System Uptime", f"{metrics['system_health']['overall_uptime']:.1f}%")

    st.divider()

    # Analytics KPI Grid
    st.subheader("📈 Key Analytics Intelligence")

    # Create KPI grid with analytics data
    revenue_forecast = metrics["revenue_forecast"]
    funnel_data = metrics["conversion_funnel"]
    quality_data = metrics["lead_quality_metrics"]
    timing_data = metrics["market_timing"]

    st.markdown('<div class="analytics-kpi-grid">', unsafe_allow_html=True)

    kpis = [
        {
            "icon": "⚡",
            "label": "Speed to Lead",
            "value": f"{quality_data['speed_to_lead']}s",
            "change": -12.5,
            "trend": "positive",  # Lower is better for speed
        },
        {
            "icon": "📅",
            "label": "Appointment Rate",
            "value": f"{quality_data['appointment_rate']:.1%}",
            "change": 4.8,
            "trend": "positive",
        },
        {
            "icon": "🛡️",
            "label": "CMA Value Edge",
            "value": f"${quality_data['cma_value_variance']:,.0f}",
            "change": 1200,
            "trend": "positive",
        },
        {
            "icon": "🎯",
            "label": "Funnel Efficiency",
            "value": f"{funnel_data['funnel_efficiency']:.1%}",
            "change": 5.2,
            "trend": "positive",
        },
        {
            "icon": "🧠",
            "label": "Avg Lead Quality",
            "value": f"{quality_data['avg_lead_score']:.0f}/100",
            "change": quality_data["score_trend"] * 100,
            "trend": "positive" if quality_data["score_trend"] > 0 else "negative",
        },
        {
            "icon": "🚨",
            "label": "Funnel Bottleneck",
            "value": funnel_data["bottleneck_stage"].replace("_", " ").title(),
            "change": 0,
            "trend": "neutral",
        },
    ]

    for kpi in kpis:
        trend = kpi.get("trend", "neutral")
        trend_icon = "📈" if trend == "positive" else "📉" if trend == "negative" else "📊"
        change_sign = "+" if kpi["change"] > 0 else ""
        change_display = f"{change_sign}{kpi['change']:.1f}%" if kpi["change"] != 0 else "—"

        st.markdown(
            f"""
        <div class="analytics-kpi-card">
            <div class="analytics-kpi-icon">{kpi["icon"]}</div>
            <div class="analytics-kpi-label">{kpi["label"]}</div>
            <div class="analytics-kpi-value">{kpi["value"]}</div>
            <div class="analytics-kpi-change {trend}">
                {trend_icon} {change_display}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Core Analytics Performance Summary
    st.subheader("🎯 Performance Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 💰 Revenue Intelligence")
        revenue_data = metrics["revenue_forecast"]
        st.metric(
            "Revenue Growth Rate",
            f"{revenue_data['growth_rate']:.1%}",
            delta=f"${revenue_data['forecasted_revenue'] - revenue_data['current_month_revenue']:,.0f} increase",
            help="Month-over-month revenue growth trajectory",
        )

    with col2:
        st.markdown("#### 🎯 Conversion Intelligence")
        funnel_efficiency = metrics["conversion_funnel"]["funnel_efficiency"]
        st.metric(
            "Overall Efficiency",
            f"{funnel_efficiency:.1%}",
            delta=f"{metrics['conversion_funnel']['closings']} closings",
            help="End-to-end funnel conversion efficiency",
        )

    with col3:
        st.markdown("#### ⏰ Timing Intelligence")
        market_timing = metrics["market_timing"]
        st.metric(
            "Timing Score",
            f"{market_timing['market_velocity_score']:.0f}/100",
            delta=f"{market_timing['timing_optimization_impact']:.1%} impact",
            help="Market timing optimization effectiveness",
        )


def render_jorge_analytics_dashboard():
    """Main function to render Jorge's Analytics Dashboard."""

    # Apply custom CSS
    render_analytics_dashboard_css()

    # Main container
    st.markdown('<div class="analytics-container">', unsafe_allow_html=True)

    # Header
    st.markdown(
        """
    <div class="dashboard-header">
        <h1 class="dashboard-title">📊 Advanced Analytics Center</h1>
        <p class="dashboard-subtitle">AI-powered business intelligence and revenue forecasting for Jorge's real estate empire</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Initialize API client
    api_client = get_analytics_api_client()

    # Main analytics overview
    render_analytics_integration_dashboard(api_client)

    # Tab navigation for different analytics sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "💰 Revenue Forecasting",
            "🎯 Conversion Funnel",
            "🗺️ Geographic Analytics",
            "🧠 Lead Intelligence",
            "💵 ROI Attribution",
        ]
    )

    with tab1:
        st.markdown('<div class="analytics-chart-section">', unsafe_allow_html=True)
        render_revenue_forecasting_section(api_client)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="analytics-chart-section">', unsafe_allow_html=True)
        render_conversion_funnel_section(api_client)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="analytics-chart-section">', unsafe_allow_html=True)
        render_geographic_analytics_section(api_client)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="analytics-chart-section">', unsafe_allow_html=True)
        render_lead_quality_intelligence_section(api_client)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab5:
        st.markdown('<div class="analytics-chart-section">', unsafe_allow_html=True)
        render_roi_attribution_section(api_client)
        st.markdown("</div>", unsafe_allow_html=True)

    # Footer with analytics quick actions
    st.divider()
    st.markdown("### ⚡ Analytics Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📧 Email Report", use_container_width=True):
            st.info("📊 Analytics report sent to jorge@realestate.com")

    with col2:
        if st.button("📱 SMS Alert Setup", use_container_width=True):
            st.info("🚨 Revenue threshold alerts configured")

    with col3:
        if st.button("🔄 Refresh Models", use_container_width=True):
            st.info("🧠 Forecasting models refreshed with latest data")

    with col4:
        if st.button("⚙️ Analytics Settings", use_container_width=True):
            st.info("⚙️ Advanced analytics configuration panel")

    # Close main container
    st.markdown("</div>", unsafe_allow_html=True)


# Main function call
if __name__ == "__main__":
    render_jorge_analytics_dashboard()
