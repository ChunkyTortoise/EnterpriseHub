import asyncio
import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

analytics_service = AnalyticsService()

# Import enhanced services
try:
    from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False


def render_executive_hub(services, mock_data, sparkline, render_insight_card):
    st.header("Executive Command Center")
    st.markdown("*High-level KPIs, revenue tracking, and system health*")

    # NEW: Claude's Strategic Briefing Area - NANO BANANA PRO EDITION
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(20, 184, 166, 0.1) 100%); 
                    border: 1px solid rgba(99, 102, 241, 0.3); 
                    border-radius: 20px; 
                    padding: 2.5rem; 
                    margin-bottom: 2.5rem; 
                    backdrop-filter: blur(10px);'>
            <div style='display: flex; align-items: flex-start; gap: 2rem;'>
                <div style='font-size: 4rem; filter: drop-shadow(0 0 15px rgba(99, 102, 241, 0.4));'>🔮</div>
                <div style='flex-grow: 1;'>
                    <h3 style='margin: 0 0 1rem 0; color: white !important; font-family: "Space Grotesk", sans-serif; font-size: 1.75rem;'>Claude's Strategic Briefing</h3>
                    <div style='color: #E6EDF3; font-size: 1.1rem; line-height: 1.6;'>
    """,
        unsafe_allow_html=True,
    )

    if CLAUDE_AVAILABLE:
        from ghl_real_estate_ai.services.claude_orchestrator import (
            ClaudeRequest,
            ClaudeTaskType,
            get_claude_orchestrator,
        )

        orchestrator = get_claude_orchestrator()
        summary_metrics = {
            "pipeline_value": "$2.4M",
            "hot_leads": 5,
            "avg_response_time": "1.8m",
            "market": st.session_state.get("selected_market", "Rancho Cucamonga"),
        }

        with st.spinner("Synthesizing strategic intelligence..."):
            try:
                request = ClaudeRequest(
                    task_type=ClaudeTaskType.EXECUTIVE_BRIEFING,
                    context={"metrics": summary_metrics, "task": "executive_briefing"},
                    prompt="Provide a 3-bullet executive briefing based on the current pipeline status. Focus on high-impact revenue opportunities.",
                    temperature=0.7,
                )

                briefing_result = run_async(orchestrator.process_request(request))

                # Record usage
                run_async(
                    analytics_service.track_llm_usage(
                        location_id="demo_location",
                        model=briefing_result.model or "claude-3-5-sonnet",
                        provider=briefing_result.provider or "claude",
                        input_tokens=briefing_result.input_tokens or 0,
                        output_tokens=briefing_result.output_tokens or 0,
                        cached=False,
                    )
                )

                st.markdown(
                    f"<div style='color: #FFFFFF; font-weight: 500;'>{briefing_result.content}</div>",
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.markdown(
                    """
                <ul style='color: #FFFFFF; font-weight: 500;'>
                    <li><strong>High-Velocity Cluster:</strong> Interest peaking in Alta Loma district. 3 leads shifted to 'Ready' tier.</li>
                    <li><strong>Strategic Retention:</strong> 2 high-value Facebook leads silent for 48h. Prepared re-engagement sequence.</li>
                    <li><strong>Revenue Catalyst:</strong> Converting Sarah Johnson this week hits 115% of Q1 target.</li>
                </ul>
                """,
                    unsafe_allow_html=True,
                )
    else:
        st.markdown(
            """
        <ul style='color: #FFFFFF; font-weight: 500;'>
            <li><strong>High-Velocity Cluster:</strong> Interest peaking in Alta Loma district. 3 leads shifted to 'Ready' tier.</li>
            <li><strong>Strategic Retention:</strong> 2 high-value Facebook leads silent for 48h. Prepared re-engagement sequence.</li>
            <li><strong>Revenue Catalyst:</strong> Converting Sarah Johnson this week hits 115% of Q1 target.</li>
        </ul>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("</div></div></div>", unsafe_allow_html=True)

    if st.button("Execute Strategic Re-engagement", use_container_width=True, type="primary"):
        st.toast("Triggering AI re-engagement for silent leads...", icon="⚡")

    st.markdown("---")

    # Tabs for sub-features
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Dashboard", "Advanced Metrics", "AI Insights", "Reports", "Market Expansion", "Market Digest"]
    )

    with tab1:
        st.subheader("Executive Dashboard")

        # Enterprise Color Palette - NANO BANANA PRO
        COLORS = {
            "primary": "#6366f1",
            "secondary": "#14b8a6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "text": "#f8fafc",
            "grid": "rgba(255,255,255,0.05)",
            "channels": ["#6366f1", "#818cf8", "#14b8a6", "#0d9488"],
        }

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pipeline", "$2.4M", "+15%")
            st.plotly_chart(
                sparkline([1.8, 2.1, 1.9, 2.4, 2.2, 2.4], color=COLORS["primary"], height=50),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with col2:
            st.metric("Commission Capture", "$136.7K", "+$42K")
            st.plotly_chart(
                sparkline([80, 95, 110, 105, 120, 136], color=COLORS["secondary"], height=50),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with col3:
            st.metric("Conversion Rate", "34%", "+2%")
            st.plotly_chart(
                sparkline([28, 30, 31, 32, 33, 34], color=COLORS["success"], height=50),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with col4:
            st.metric("AI Lead Velocity", "4.2/day", "+1.1")
            st.plotly_chart(
                sparkline([2.1, 2.5, 3.0, 3.8, 4.0, 4.2], color="#8b5cf6", height=50),
                use_container_width=True,
                config={"displayModeBar": False},
            )

        st.markdown("---")

        # NEW: High-Impact Visualizations Row
        viz_col1, viz_col2 = st.columns([1, 1])

        with viz_col1:
            st.markdown("#### 🚀 Conversion Funnel")
            try:
                from components.calculators import render_revenue_funnel

                render_revenue_funnel()
            except ImportError:
                st.info("Funnel visualization loading...")

        with viz_col2:
            # Mock data for revenue trends
            dates = pd.date_range(end=pd.Timestamp.now(), periods=6, freq="M")
            revenue_data = {
                "Month": dates.strftime("%b %Y"),
                "Revenue": [180000, 210000, 195000, 240000, 225000, 280000],
                "Target": [200000, 200000, 220000, 220000, 250000, 250000],
            }
            df_rev = pd.DataFrame(revenue_data)

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_rev["Month"],
                    y=df_rev["Revenue"],
                    name="Actual Revenue",
                    line=dict(color=COLORS["primary"], width=4),
                    marker=dict(size=10, color=COLORS["primary"], line=dict(width=2, color="#FFFFFF")),
                    fill="tozeroy",
                    fillcolor="rgba(99, 102, 241, 0.1)",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df_rev["Month"],
                    y=df_rev["Target"],
                    name="Revenue Target",
                    line=dict(color="#8B949E", width=2, dash="dot"),
                    opacity=0.8,
                )
            )

            fig.update_layout(title="<b>Revenue Performance vs Target</b>", hovermode="x unified")
            st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

        st.markdown("---")

        # NEW: Channel Attribution and Forecasting Row
        attr_col1, attr_col2 = st.columns([1, 1])

        with attr_col1:
            st.markdown("#### 🎯 Revenue Attribution by Channel")
            # Get channel data from service
            attr_report = services["revenue"].get_full_attribution_report("demo_location")
            channel_df = pd.DataFrame(attr_report["channel_performance"])

            fig_pie = go.Figure(
                data=[
                    go.Pie(
                        labels=channel_df["channel"],
                        values=channel_df["revenue"],
                        hole=0.4,
                        marker=dict(colors=COLORS["channels"]),
                    )
                ]
            )

            st.plotly_chart(style_obsidian_chart(fig_pie), use_container_width=True)

        with attr_col2:
            st.markdown("#### 🔮 AI Revenue Projection (Q1 2026)")
            # Simulated forecasting data
            forecast_data = {
                "Scenario": ["Conservative", "AI-Optimized (Target)", "Elite Performance"],
                "Projection": [295000, 342000, 415000],
                "Confidence": [0.92, 0.85, 0.68],
            }
            df_forecast = pd.DataFrame(forecast_data)

            fig_bar = go.Figure(
                data=[
                    go.Bar(
                        x=df_forecast["Scenario"],
                        y=df_forecast["Projection"],
                        marker_color=[COLORS["secondary"], COLORS["primary"], COLORS["success"]],
                        text=[f"${v / 1000:.0f}K" for v in df_forecast["Projection"]],
                        textposition="auto",
                    )
                ]
            )

            st.plotly_chart(style_obsidian_chart(fig_bar), use_container_width=True)
            st.caption("AI-Optimized projection assumes 15% increase in conversion via Swarm Intelligence.")

        st.markdown("---")

        # NEW: ROI Analysis and Quality Distribution Row
        roi_col1, roi_col2 = st.columns([1.2, 1])

        with roi_col1:
            st.markdown("#### 💰 Strategic ROI & Efficiency")
            # Using data from executive dashboard service
            from ghl_real_estate_ai.services.executive_dashboard import calculate_roi

            roi = calculate_roi(system_cost_monthly=170.0, conversations_per_month=300)

            st.markdown(
                f"""
            <div style='background: rgba(22, 27, 34, 0.7); padding: 1.5rem; border-radius: 16px; color: #E6EDF3; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;'>
                    <div>
                        <div style='font-size: 0.8rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Current Period ROI</div>
                        <div style='font-size: 2.75rem; font-weight: 700; color: #6366F1; text-shadow: 0 0 15px rgba(99, 102, 241, 0.4); font-family: "Space Grotesk", sans-serif;'>{roi["roi"]["percentage"]}%</div>
                    </div>
                    <div style='background: rgba(99, 102, 241, 0.15); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.3);'>
                        <span style='font-size: 2rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5));'>📈</span>
                    </div>
                </div>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;'>
                    <div style='background: rgba(255,255,255,0.03); padding: 1.25rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);'>
                        <div style='font-size: 0.7rem; opacity: 0.7;'>Net Monthly Profit</div>
                        <div style='font-size: 1.2rem; font-weight: 700;'>${roi["roi"]["net_profit_monthly"]:,.0f}</div>
                    </div>
                    <div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px;'>
                        <div style='font-size: 0.7rem; opacity: 0.7;'>Payback Period</div>
                        <div style='font-size: 1.2rem; font-weight: 700;'>{roi["roi"]["payback_days"]} Days</div>
                    </div>
                </div>
                <div style='margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.8rem; opacity: 0.9;'>
                    ✨ <b>AI Impact:</b> Swarm Intelligence has reduced manual labor by 156 hours this month.
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with roi_col2:
            st.markdown("#### 📊 Lead Quality Distribution")
            # Get data from executive service
            exec_summary = services["executive"].get_executive_summary("demo_location")
            quality = exec_summary["metrics"]["lead_quality"]

            fig_donut = go.Figure(
                data=[
                    go.Pie(
                        labels=["Hot", "Warm", "Cold"],
                        values=[quality["hot_leads"], quality["warm_leads"], quality["cold_leads"]],
                        hole=0.6,
                        marker=dict(colors=[COLORS["danger"], COLORS["warning"], COLORS["primary"]]),
                    )
                ]
            )

            fig_donut.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=280,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                annotations=[
                    dict(
                        text=f"{quality['hot_leads'] + quality['warm_leads'] + quality['cold_leads']}<br>Total",
                        x=0.5,
                        y=0.5,
                        font_size=20,
                        showarrow=False,
                    )
                ],
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("---")

        # NEW: Global AI System Health
        st.markdown("#### ⚡ Infrastructure Health")
        h_col1, h_col2, h_col3, h_col4 = st.columns(4)

        # Get dynamic health data
        safe_data = mock_data if mock_data is not None else {}
        health = safe_data.get("system_health", {})

        with h_col1:
            st.markdown(
                f"""
            <div style='background: rgba(22, 27, 34, 0.7); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); border-top: 4px solid #10b981; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); backdrop-filter: blur(12px);'>
                <div style='font-size: 0.75rem; color: #8B949E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>API Uptime</div>
                <div style='font-size: 1.75rem; font-weight: 700; color: #FFFFFF; margin: 8px 0; font-family: "Space Grotesk", sans-serif;'>{health.get("uptime_percentage", 99.9)}%</div>
                <div style='font-size: 0.65rem; color: #10b981; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>🟢 Operational</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with h_col2:
            st.markdown(
                f"""
            <div style='background: rgba(22, 27, 34, 0.7); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); border-top: 4px solid #6366F1; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); backdrop-filter: blur(12px);'>
                <div style='font-size: 0.75rem; color: #8B949E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Avg Latency</div>
                <div style='font-size: 1.75rem; font-weight: 700; color: #FFFFFF; margin: 8px 0; font-family: "Space Grotesk", sans-serif;'>{health.get("avg_response_time_ms", 142)}ms</div>
                <div style='font-size: 0.65rem; color: #6366F1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>⚡ Fast Response</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with h_col3:
            st.markdown(
                f"""
            <div style='background: rgba(22, 27, 34, 0.7); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); border-top: 4px solid #f59e0b; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); backdrop-filter: blur(12px);'>
                <div style='font-size: 0.75rem; color: #8B949E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Compliance</div>
                <div style='font-size: 1.75rem; font-weight: 700; color: #FFFFFF; margin: 8px 0; font-family: "Space Grotesk", sans-serif;'>{int(health.get("sms_compliance_rate", 1) * 100)}%</div>
                <div style='font-size: 0.65rem; color: #f59e0b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>📜 A2P VERIFIED</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with h_col4:
            st.markdown(
                f"""
            <div style='background: rgba(22, 27, 34, 0.7); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); border-top: 4px solid #8b5cf6; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); backdrop-filter: blur(12px);'>
                <div style='font-size: 0.75rem; color: #8B949E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Swarm Status</div>
                <div style='font-size: 1.75rem; font-weight: 700; color: #FFFFFF; margin: 8px 0; font-family: "Space Grotesk", sans-serif;'>Active</div>
                <div style='font-size: 0.65rem; color: #8b5cf6; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>🐝 12 Agents</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Add last updated timestamp
        last_updated = datetime.datetime.now().strftime("%b %d, %Y at %I:%M %p")
        st.markdown(
            f"<div style='margin-top: 2rem; font-size: 0.75rem; color: #9ca3af; font-style: italic; text-align: right;'>Last architectural sync: {last_updated}</div>",
            unsafe_allow_html=True,
        )

    with tab2:
        st.subheader("High-Impact Executive Metrics")
        st.markdown("*Unit economics, market-wide performance, and operational efficiency*")

        exec_summary = services["executive"].get_executive_summary("demo_location")

        # Safety check for economics key
        if "economics" not in exec_summary:
            st.warning("⚠️ Economics data missing from service. Using default metrics for display.")
            economics = {"ltv_cac_ratio": 3.2, "avg_cac": 450.0, "ltv": 12500 * 0.34}
        else:
            economics = exec_summary["economics"]

        market_perf = exec_summary.get(
            "market_performance",
            {
                "Rancho Cucamonga": {"leads": 45, "revenue": 1200000},
                "Miami": {"leads": 35, "revenue": 800000},
                "Other": {"leads": 20, "revenue": 400000},
            },
        )

        leakage = exec_summary.get(
            "leakage",
            {
                "Contact -> Qualified": 15.2,
                "Qualified -> Hot": 22.4,
                "Hot -> Appointment": 34.1,
                "Appointment -> Closed": 45.8,
            },
        )

        # Row 1: Unit Economics
        st.markdown("#### 💰 Unit Economics & Profitability")
        ec_col1, ec_col2, ec_col3 = st.columns(3)

        with ec_col1:
            st.metric("LTV/CAC Ratio", f"{economics['ltv_cac_ratio']}x", "+0.4x")
            st.caption("Target: > 3.0x")
        with ec_col2:
            st.metric("Avg. CAC", f"${economics['avg_cac']}", "-$42")
            st.caption("Blended acquisition cost")
        with ec_col3:
            st.metric("Lead LTV", f"${economics['ltv']:,}", "+$850")
            st.caption("34% conversion baseline")

        st.markdown("---")

        # Row 2: Market Performance & Funnel Leakage
        m_col1, m_col2 = st.columns([1.2, 1])

        with m_col1:
            st.markdown("#### 🌍 Regional Revenue Distribution")
            df_market = pd.DataFrame(
                [{"Market": k, "Revenue": v["revenue"], "Leads": v["leads"]} for k, v in market_perf.items()]
            )

            fig_market = px.bar(
                df_market,
                x="Market",
                y="Revenue",
                text="Leads",
                color="Market",
                color_discrete_sequence=COLORS["channels"],
            )
            fig_market.update_traces(texttemplate="%{text} Leads", textposition="outside")
            st.plotly_chart(style_obsidian_chart(fig_market), use_container_width=True)

        with m_col2:
            st.markdown("#### 📉 Funnel Leakage Analysis")
            df_leakage = pd.DataFrame([{"Stage": k, "Drop-off %": v} for k, v in leakage.items()])

            fig_leak = px.line(
                df_leakage, x="Stage", y="Drop-off %", markers=True, color_discrete_sequence=[COLORS["danger"]]
            )
            fig_leak.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(style_obsidian_chart(fig_leak), use_container_width=True)
            st.caption("High drop-off in 'Hot -> Appointment' suggests a need for faster human handoff.")

        st.markdown("---")

        # Row 3: Agent vs AI Swarm Performance
        st.markdown("#### 🐝 AI Swarm vs. Human Benchmarking")

        perf_data = {
            "Metric": ["Response Time", "Engagement Depth", "Accuracy", "Availability"],
            "Human Agent": [45, 62, 88, 40],
            "AI Swarm": [1.8, 85, 94, 100],
        }
        df_perf = pd.DataFrame(perf_data)

        fig_radar = go.Figure()
        fig_radar.add_trace(
            go.Scatterpolar(
                r=df_perf["Human Agent"],
                theta=df_perf["Metric"],
                fill="toself",
                name="Human Benchmark",
                line_color="#94A3B8",
                fillcolor="rgba(148, 163, 184, 0.2)",
            )
        )
        fig_radar.add_trace(
            go.Scatterpolar(
                r=df_perf["AI Swarm"],
                theta=df_perf["Metric"],
                fill="toself",
                name="AI Swarm Intelligence",
                line_color="#6366F1",
                fillcolor="rgba(99, 102, 241, 0.2)",
            )
        )

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    gridcolor="rgba(255,255,255,0.1)",
                    angle=45,
                    tickfont=dict(size=10, color="#8B949E"),
                ),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.1)", tickfont=dict(size=12, color="#E6EDF3")),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(t=40, b=40, l=40, r=40),
        )
        st.plotly_chart(style_obsidian_chart(fig_radar), use_container_width=True)
        st.info(
            "✨ **Efficiency Gain:** AI Swarm is currently handling 94% of top-of-funnel discovery, saving Jorge 42 hours/week."
        )

    with tab3:
        st.subheader("AI System Insights")

        # Add AI Performance Metrics Dashboard
        try:
            from components.ai_performance_metrics import render_ai_metrics_dashboard

            render_ai_metrics_dashboard()
            st.markdown("---")
        except ImportError:
            pass

        # Get dynamic insights
        summary = services["executive"].get_executive_summary("demo_location")
        insights = summary.get("insights", [])

        if not insights:
            insights = [
                {
                    "type": "success",
                    "title": "Response Time Excellence",
                    "value": "1.8 mins",
                    "message": "Average response time beats target by 40%",
                },
                {
                    "type": "warning",
                    "title": "Conversion Opportunity",
                    "value": "20% Gap",
                    "message": "12 leads are stalling at the 'Financing' stage. Focus required.",
                    "action": "🎯 Fix Conversion Gap Now",
                },
                {
                    "type": "info",
                    "title": "Lead Sentiment",
                    "value": "Strong",
                    "message": "85% of recent conversations show positive buying intent.",
                },
            ]

        for i, insight in enumerate(insights):
            # Map 'opportunity' to 'warning' for visual consistency in the UI
            insight_status = "warning" if insight["type"] == "opportunity" else insight["type"]

            render_insight_card(
                insight["title"],
                insight.get("value", "N/A"),
                insight["message"],
                status=insight_status,
                action_label=insight.get("action"),
                action_key=f"insight_btn_{i}",
            )

        st.markdown("#### 📈 System Performance")
        safe_data = mock_data if mock_data is not None else {}
        health = safe_data.get("system_health", {})

        if health:
            c1, c2, c3 = st.columns(3)
            resp_time = health.get("avg_response_time_ms", 0)
            resp_display = f"{resp_time}ms" if resp_time > 0 else "Evaluating"

            c1.metric("API Uptime", f"{health.get('uptime_percentage', 100)}%")
            c2.metric("Avg Latency", resp_display)
            c3.metric("SMS Compliance", f"{int(health.get('sms_compliance_rate', 1) * 100)}%")

        # NEW: Elite AI Market DNA
        st.markdown("---")
        st.markdown("#### 🧬 Market-wide Lifestyle DNA Topology")
        st.markdown(
            f"*Aggregate priority dimensions across all leads in {st.session_state.get('selected_market', 'Rancho Cucamonga')}*"
        )

        market_dna_data = {
            "Dimension": [
                "Convenience",
                "Security",
                "Investment",
                "Status",
                "Privacy",
                "Tech Integration",
                "Family",
                "Commute",
            ],
            "Rancho Cucamonga": [85, 72, 90, 65, 50, 88, 70, 82],
            "Rancho": [70, 85, 60, 75, 80, 55, 92, 65],
        }

        current_market = "Rancho Cucamonga" if "Rancho Cucamonga" in st.session_state.get("selected_market", "Rancho Cucamonga") else "Rancho"

        fig_market_radar = go.Figure()
        fig_market_radar.add_trace(
            go.Scatterpolar(
                r=market_dna_data[current_market],
                theta=market_dna_data["Dimension"],
                fill="toself",
                name=current_market,
                line_color="#6366F1",
            )
        )

        fig_market_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.05)"),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=True,
            height=400,
        )
        st.plotly_chart(style_obsidian_chart(fig_market_radar), use_container_width=True)
        st.info(
            f"✨ **Strategic Insight:** The {current_market} market shows a high concentration of {'Investment & Tech' if current_market == 'Rancho Cucamonga' else 'Security & Family'} focused leads. Tailor market-wide campaigns accordingly."
        )

    with tab4:
        st.subheader("Actionable Executive Report")

        if CLAUDE_AVAILABLE:
            if st.button("🪄 Generate Claude Executive Report", type="primary", use_container_width=True):
                with st.spinner("Claude is synthesizing comprehensive pipeline data..."):
                    try:
                        orchestrator = get_claude_orchestrator()

                        # Generate full report
                        report_data = {
                            "pipeline": revenue_data,
                            "leads": summary.get("action_items", []),
                            "system": health,
                        }

                        report_result = run_async(
                            orchestrator.synthesize_report(
                                metrics=report_data,
                                report_type="executive_quarterly_projection",
                                market_context={"location": st.session_state.get("selected_market", "Rancho Cucamonga")},
                            )
                        )

                        # Record usage
                        run_async(
                            analytics_service.track_llm_usage(
                                location_id="demo_location",
                                model=report_result.model or "claude-3-5-sonnet",
                                provider=report_result.provider or "claude",
                                input_tokens=report_result.input_tokens or 0,
                                output_tokens=report_result.output_tokens or 0,
                                cached=False,
                            )
                        )

                        st.markdown(report_result.content)
                        st.success("Executive report synthesized successfully!")
                    except Exception as e:
                        st.error(f"Report Synthesis Error: {str(e)}")

        st.markdown("---")
        action_items = summary.get("action_items", [])
        if not action_items:
            action_items = [
                {
                    "priority": "high",
                    "title": "5 Hot Leads Pending",
                    "action": "Schedule showings for Downtown cluster",
                    "impact": "Potential $2.5M Volume",
                },
                {
                    "priority": "medium",
                    "title": "Review Weekend Staffing",
                    "action": "Add on-call agent for Saturdays",
                    "impact": "Improve conversion by ~5%",
                },
            ]

        st.dataframe(
            pd.DataFrame(action_items),
            column_config={
                "priority": "Priority",
                "title": "Opportunity",
                "action": "Recommended Action",
                "impact": "Estimated Impact",
            },
            hide_index=True,
            use_container_width=True,
        )

        if st.button("📧 Email Report to Jorge"):
            st.toast("Report sent to jorge@example.com")

    with tab5:
        st.subheader("🚀 Multi-Market Predictive Expansion")
        st.markdown("*Using psychological DNA clusters to predict success in new territories*")

        with st.container(border=True):
            col_exp1, col_exp2 = st.columns([1, 1])

            with col_exp1:
                st.markdown("#### 🧬 Source Market DNA Synthesis")
                st.write(
                    "Aggregating conversion clusters from Rancho Cucamonga and Rancho to identify Jorge's 'Winning Lead Profile'."
                )

                # DNA Comparison Chart
                dna_metrics = ["Investment", "Security", "Status", "Family", "Convenience", "Privacy"]
                rancho_cucamonga_dna = [0.9, 0.7, 0.6, 0.7, 0.8, 0.5]
                rancho_dna = [0.6, 0.85, 0.75, 0.9, 0.7, 0.8]

                # Weighted "Winning Profile" based on conversion
                winning_profile = [(a * 0.6 + r * 0.4) for a, r in zip(rancho_cucamonga_dna, rancho_dna)]

                fig_exp = go.Figure()
                fig_exp.add_trace(
                    go.Scatterpolar(
                        r=rancho_cucamonga_dna,
                        theta=dna_metrics,
                        fill="toself",
                        name="Rancho Cucamonga Cluster",
                        line_color="rgba(99, 102, 241, 0.4)",
                    )
                )
                fig_exp.add_trace(
                    go.Scatterpolar(
                        r=rancho_dna,
                        theta=dna_metrics,
                        fill="toself",
                        name="Rancho Cluster",
                        line_color="rgba(20, 184, 166, 0.4)",
                    )
                )
                fig_exp.add_trace(
                    go.Scatterpolar(
                        r=winning_profile,
                        theta=dna_metrics,
                        fill="toself",
                        name="WINNING DNA",
                        line_color="#FFFFFF",
                        line_width=3,
                    )
                )

                fig_exp.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1], gridcolor="rgba(255,255,255,0.1)"),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    showlegend=True,
                    margin=dict(t=30, b=30, l=30, r=30),
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_exp, use_container_width=True)

            with col_exp2:
                st.markdown("#### 🎯 Predicted Expansion Target: **Dallas, CA**")
                st.write(
                    "Based on Jorge's high success rate with **'Status-Conscious Investors'** and **'Security-First Families'**, Claude predicts high resonance in the following Dallas pockets:"
                )

                expansion_targets = [
                    {
                        "zip": "75205",
                        "area": "Highland Park",
                        "match": "94%",
                        "reason": "Matches 'Status + Privacy' cluster from Rancho.",
                    },
                    {
                        "zip": "75201",
                        "area": "Uptown/Downtown",
                        "match": "89%",
                        "reason": "Matches 'Investment + Tech' cluster from Rancho Cucamonga.",
                    },
                    {
                        "zip": "75024",
                        "area": "Legacy West / Plano",
                        "match": "82%",
                        "reason": "Matches 'Convenience + Status' hybrid profile.",
                    },
                ]

                for target in expansion_targets:
                    with st.container(border=True):
                        c_t1, c_t2 = st.columns([1, 3])
                        with c_t1:
                            st.metric("Match", target["match"])
                        with c_t2:
                            st.markdown(f"**{target['area']} ({target['zip']})**")
                            st.caption(target["reason"])

                if st.button("📊 Generate Orange County Market Entry Strategy", type="primary", use_container_width=True):
                    with st.spinner("Claude is drafting market entry scripts..."):
                        time.sleep(2)
                        st.success("Orange County Strategy Dossier Generated.")
                        st.info(
                            "💡 **Key Insight:** Orange County leads in 92660 respond 30% better to 'Prestige-First' messaging than 'Value-First' messaging."
                        )

        st.markdown("---")
        st.markdown("#### 🔮 Geographic Migration Logic")
        st.write("Claude is tracking lead migration patterns from Coastal California to the Inland Empire to predict future demand.")
        st.image(
            "https://img.freepik.com/free-vector/world-map-with-lines-connection_1017-14238.jpg?size=626&ext=jpg",
            caption="Simulated Migration Heatmap",
        )

    with tab6:
        st.subheader("📰 Market Intelligence Weekly Digest")
        st.markdown("*White-label automated outreach for your client database*")

        with st.container(border=True):
            col_digest1, col_digest2 = st.columns([1, 2])

            with col_digest1:
                st.markdown("#### ⚙️ Configuration")
                digest_market = st.selectbox(
                    "Target Market", ["Rancho Cucamonga, CA", "Rancho Cucamonga, CA"], key="digest_market_sel"
                )
                digest_zips = st.text_input("Focus ZIP Codes (comma-separated)", "91730, 91730, 91730")
                agency_name = st.text_input("Agency Name", "Lyrio AI Rancho Cucamonga")

                if st.button("🪄 Generate Weekly Digest", type="primary", use_container_width=True):
                    st.session_state.digest_requested = True

            with col_digest2:
                if st.session_state.get("digest_requested"):
                    from ghl_real_estate_ai.services.market_digest_generator import MarketDigestGenerator

                    digest_gen = MarketDigestGenerator()

                    with st.spinner("Claude is synthesizing hyper-local trends..."):
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                            zips_list = [z.strip() for z in digest_zips.split(",")]
                            digest_result = run_async(
                                digest_gen.generate_weekly_digest(
                                    market_name=digest_market,
                                    zip_codes=zips_list,
                                    agency_branding={"name": agency_name},
                                )
                            )

                            if "error" in digest_result:
                                st.error(f"Failed to generate digest: {digest_result['error']}")
                            else:
                                st.markdown(f"### {agency_name} | Weekly Intel")
                                st.markdown(digest_result["content"])

                                st.markdown("---")
                                if st.button("📨 Sync to GHL Email Campaign", use_container_width=True):
                                    st.success("Digest synced to GHL Email Builder! Sent to 1,245 contacts.")
                                    st.balloons()
                        except Exception as e:
                            st.error(f"Digest generation failed: {e}")
                else:
                    st.info("Configure the digest parameters and click 'Generate' to initialize the narrative engine.")
