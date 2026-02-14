"""
Ops & Optimization Hub - Premium Management Suite
System health, revenue attribution, and Agentic OS orchestration.
"""

import datetime
from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

# Absolute imports
try:
    from components.agent_os import render_agent_os_tab
    from components.ai_training_feedback import render_rlhf_loop
    from components.calculators import render_revenue_funnel
    from components.security_governance import render_security_governance
except ImportError:
    pass


class OpsOptimizationHub:
    """Enterprise Operations & Optimization Hub"""

    def __init__(self, services: Dict[str, Any], claude: Optional[Any] = None):
        self.services = services
        self.claude = claude

    def render_hub(self):
        """Render the complete Ops & Optimization interface"""
        st.header("Ops & Optimization")
        st.markdown("*Manager-level analytics and team performance tracking*")

        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs(
            [
                "Quality",
                "Revenue",
                "Revenue Arbitrage",
                "Benchmarks",
                "Coaching",
                "Control",
                "Model Retraining",
                "RLHF Loop",
                "Governance",
                "Agentic OS",
                "Enterprise Pulse",
                "Ambiguity Queue",
            ]
        )

        with tab1:
            self._render_quality_assurance()

        with tab2:
            self._render_revenue_attribution()

        with tab3:
            self._render_revenue_arbitrage()

        with tab4:
            self._render_benchmarking()

        with tab4:
            self._render_coaching()

        with tab5:
            self._render_control_panel()

        with tab7:
            self._render_model_retraining()

        with tab9:
            render_agent_os_tab()

        with tab8:
            render_rlhf_loop()

        with tab7:
            render_security_governance()

        with tab9:
            self._render_enterprise_pulse()

        with tab10:
            self._render_ambiguity_queue()

    def _render_revenue_arbitrage(self):
        """Phase 6: Revenue Arbitrage Map & Investor Intelligence"""
        st.subheader("📈 Revenue Arbitrage Intelligence")
        st.markdown("Predictive financial engineering identifying the highest-margin investment opportunities.")

        # Quant Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg Portfolio CoC", "24.5%", "+3.2%")
        col2.metric("Target IRR", "18.2%", "Stable")
        col3.metric("Arbitrage Gap", "$1.2M", "+$250K")
        col4.metric("Quant Accuracy", "94.2%", "+1.5%")

        # Arbitrage Map
        st.markdown("---")
        st.markdown("#### 🗺️ Revenue Arbitrage Map (by Zip Code)")

        # Mock data for arbitrage map - In production, this pulls from QuantAgent logs
        arbitrage_data = pd.DataFrame(
            {
                "Zip Code": ["91730", "91730", "91730", "91737", "91758", "91739"],
                "Market Price": [850000, 750000, 450000, 680000, 390000, 520000],
                "Predicted Margin": [125000, 110000, 85000, 95000, 75000, 105000],
                "Net Yield %": [14.7, 14.6, 18.8, 13.9, 19.2, 20.1],
                "Competition": ["High", "High", "Medium", "Medium", "Low", "Medium"],
            }
        )

        fig = px.scatter(
            arbitrage_data,
            x="Zip Code",
            y="Net Yield %",
            size="Predicted Margin",
            color="Net Yield %",
            hover_name="Zip Code",
            hover_data=["Market Price", "Competition"],
            color_continuous_scale="Viridis",
            title="Opportunity Density vs. Yield",
        )

        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

        # Quantitative Strategy Breakdown
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 💎 High-Yield Clusters")
            st.info(
                "**91758 & 91739**: Identified as 'Prime Arbitrage' zones. Low competition combined with high predicted Net Yield (>19%)."
            )
            st.success("Recommendation: Deploy 'The Hunter' to aggressive CRAG scanning in these sectors.")

        with c2:
            st.markdown("#### 🛡️ Risk-Adjusted Forecasts")
            # Simulated forecasting chart
            forecast_dates = pd.date_range(start=datetime.datetime.now(), periods=6, freq="M")
            forecast_values = [1.2, 1.4, 1.35, 1.6, 1.8, 1.75]  # Millions
            fig_forecast = go.Figure()
            fig_forecast.add_trace(
                go.Scatter(
                    x=forecast_dates,
                    y=forecast_values,
                    mode="lines+markers",
                    name="Predicted Profit",
                    line=dict(color="#10B981", width=3),
                )
            )
            st.plotly_chart(style_obsidian_chart(fig_forecast), use_container_width=True)

    def _render_model_retraining(self):
        """Phase 7: Adaptive Model Retraining Management"""
        st.subheader("🔄 Adaptive Model Retraining")
        st.markdown("Closed-loop optimization of AI scoring weights based on GHL deal outcomes.")

        # 🚀 RLHF FEEDBACK STATS (Phase 4)
        try:
            from ghl_real_estate_ai.services.rlhf_service import get_rlhf_service

            rlhf_service = get_rlhf_service()
            feedback_stats = rlhf_service.get_feedback_summary()
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Failed to fetch RLHF summary: {str(e)}")
            feedback_stats = {"total_feedback": 0, "positive_rate": 0, "needs_review": 0}

        # Real-time Feedback Loop Stats
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Human Feedback", feedback_stats["total_feedback"], f"{feedback_stats['needs_review']} pending")
        col2.metric("Approval Rate", f"{feedback_stats['positive_rate'] * 100:.1f}%", "Target >80%")
        col3.metric("Model Lift", "+3.2%", "Last 7d")
        col4.metric("Model Health", "98.2%", "Healthy")

        st.markdown("---")

        # RETRAINING TRIGGER
        st.markdown("#### 🛰️ Weekly Retraining Control")
        retrain_col1, retrain_col2 = st.columns([2, 1])
        with retrain_col1:
            st.info(
                "The automated retraining simulation analyzes negative feedback to optimize the 'Voss Negotiator' and 'Lead Scorer' parameters."
            )
        with retrain_col2:
            if st.button("🚀 Run Retraining Simulation", type="primary", use_container_width=True):
                with st.spinner("Analyzing feedback traces..."):
                    result = run_async(rlhf_service.run_weekly_retraining_simulation())
                    if result.get("success"):
                        st.success(f"Retraining complete! Lift: {result['model_lift_estimate']}")
                        st.balloons()
                    else:
                        st.warning(result.get("message", "No data to retrain."))

        st.markdown("---")
        st.markdown("#### 🎯 Active Scoring Weights (Adaptive)")

        # Visualize dynamic weights
        weight_df = pd.DataFrame(
            [{"Factor": k.replace("_", " ").title(), "Weight": v} for k, v in dynamic_weights.items()]
        )
        fig = px.bar(
            weight_df, x="Factor", y="Weight", color="Factor", color_discrete_sequence=px.colors.qualitative.Pastel
        )
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

        # Manual Override
        with st.expander("🛠️ Manual Weight Adjustment (Expert Mode)"):
            st.warning("Manual overrides will temporarily pause the adaptive feedback loop.")
            cols = st.columns(len(dynamic_weights))
            for i, (factor, weight) in enumerate(dynamic_weights.items()):
                with cols[i]:
                    st.slider(f"{factor.title()}", 0.0, 1.0, weight, step=0.01, key=f"weight_slider_{factor}")

            if st.button("Apply Manual Weights"):
                st.success("Weights updated and logged to SharedBlackboard.")

        # Outcome Feed
        st.markdown("---")
        st.markdown("#### 📥 Recent Deal Outcomes")
        outcomes = [
            {"lead": "Sarah Chen", "outcome": "WON", "value": "$16,500", "date": "1h ago"},
            {"lead": "David Kim", "outcome": "WON", "value": "$10,500", "date": "3h ago"},
            {"lead": "Mike Rodriguez", "outcome": "LOST", "value": "$0", "date": "5h ago"},
        ]
        st.table(outcomes)

    def _render_ambiguity_queue(self):
        """Phase 5: HITL Ambiguity Queue for Jorge"""
        st.subheader("⚠️ Ambiguity Queue (HITL)")
        st.markdown(
            "Leads flagged by AI for **Conflicting Intent** or **High-Value Ambiguity** requiring manual review."
        )

        # Mock data for demonstration - in production, query the MemoryService/PredictiveScorer
        ambiguous_leads = [
            {
                "id": "cont_12345",
                "name": "Sarah Jenkins",
                "conflict": "Urgent timeline (30 days) but Firm on Price ($450k, 15% over ARV)",
                "score": 88,
                "potential": "$15,000",
            },
            {
                "id": "cont_67890",
                "name": "Mark Thompson",
                "conflict": "Major Repairs needed but expecting 'Excellent' condition pricing",
                "score": 72,
                "potential": "$22,500",
            },
        ]

        for lead in ambiguous_leads:
            with st.container():
                st.markdown(
                    f"""
                    <div style='background: rgba(245, 158, 11, 0.1); padding: 1rem; border-radius: 8px; border: 1px solid rgba(245, 158, 11, 0.3); margin-bottom: 1rem;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span style='font-weight: bold; color: #F59E0B;'>{lead["name"]} ({lead["id"]})</span>
                            <span style='color: #8B949E;'>Priority Score: {lead["score"]}</span>
                        </div>
                        <div style='margin-top: 0.5rem; color: #FFFFFF;'>
                            <strong>Conflict detected:</strong> {lead["conflict"]}
                        </div>
                        <div style='margin-top: 0.5rem; display: flex; gap: 10px;'>
                            <button style='background: #10B981; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;'>Approve AI Pathway</button>
                            <button style='background: #EF4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;'>Take Over Manually</button>
                        </div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

        if not ambiguous_leads:
            st.success("Clean queue! No high-value ambiguities detected.")

    def _render_enterprise_pulse(self):
        st.subheader("Enterprise AI Pulse")
        st.markdown("Real-time system health, multi-tenant latency, and predictive ROI.")

        # Metrics Row
        col1, col2, col3, col4 = st.columns(4)

        # Pull data from gemini_metrics.csv if it exists, otherwise use mock
        import os

        import pandas as pd

        metrics_file = "gemini_metrics.csv"

        if os.path.exists(metrics_file):
            df = pd.read_csv(metrics_file)
            total_cost = df["cost_usd"].sum()
            failover_count = df["is_failover"].sum()
            tenant_count = df["tenant_id"].nunique()
            avg_tokens = df["total_tokens"].mean()
        else:
            total_cost = 142.85
            failover_count = 3
            tenant_count = 12
            avg_tokens = 1450

        col1.metric("Total LLM Cost", f"${total_cost:.2f}", "-5%")
        col2.metric("Failover Events", failover_count, "-2" if failover_count > 0 else "0")
        col3.metric("Active Tenants", tenant_count, "+1")
        col4.metric("Avg Token/Msg", int(avg_tokens), "+12")

        # Pulse Charts
        st.markdown("---")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### ⚡ System Latency (ms)")
            # Simulated latency data - in production would pull from AnalyticsEngine
            latency_data = [350, 420, 380, 450, 310, 290, 320, 340, 310, 305]
            from app import sparkline

            st.plotly_chart(sparkline(latency_data, color="#6366F1", height=100), use_container_width=True)
            st.caption("P95 Latency: Union[342ms, P99] Latency: 485ms")

        with c2:
            st.markdown("#### 💰 Cost per Tenant")
            if os.path.exists(metrics_file):
                df = pd.read_csv(metrics_file)
                tenant_costs = df.groupby("tenant_id")["cost_usd"].sum().reset_index()
            else:
                tenant_costs = pd.DataFrame(
                    {
                        "tenant_id": ["loc_rancho_cucamonga", "loc_rancho", "loc_miami", "loc_dallas"],
                        "cost_usd": [45.20, 32.10, 28.50, 37.05],
                    }
                )

            fig = px.bar(tenant_costs, x="tenant_id", y="cost_usd", color="cost_usd", color_continuous_scale="Purples")
            from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

            st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🛡️ Circuit Breaker Failover Frequency")
        # Show failover distribution by provider
        failover_data = pd.DataFrame(
            {
                "Provider": ["Claude (Primary)", "Gemini (Failover)", "Perplexity (Research)"],
                "Requests": [850, failover_count, 45],
            }
        )
        fig_fail = px.pie(
            failover_data,
            values="Requests",
            names="Provider",
            hole=0.4,
            color_discrete_sequence=["#6366F1", "#10B981", "#F59E0B"],
        )
        st.plotly_chart(style_obsidian_chart(fig_fail), use_container_width=True)

    def _render_quality_assurance(self):
        st.subheader("AI Quality Assurance")
        qa_report = self.services["qa"].generate_qa_report("demo_location")

        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Quality", f"{qa_report['overall_score']}%", "+2%")
        col2.metric("Compliance Rate", f"{qa_report['compliance_rate']}%", "Stable")
        col3.metric("Empathy Score", f"{qa_report['empathy_score']}/10", "+0.5")

        st.markdown("#### 🎯 Improvement Areas")
        for area in qa_report["improvement_areas"]:
            st.warning(f"**{area['topic']}**: {area['recommendation']}")

    def _render_revenue_attribution(self):
        st.subheader("Revenue Attribution")
        attr_data = self.services["revenue"].get_attribution_data("demo_location")

        # Display attribution chart
        df_attr = pd.DataFrame(attr_data["channels"])

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=df_attr["channel"],
                    values=df_attr["revenue"],
                    hole=0.5,
                    marker=dict(colors=["#6366F1", "#8B5CF6", "#10B981", "#F59E0B", "#EF4444"]),
                    textinfo="label+percent",
                    textposition="outside",
                    insidetextorientation="radial",
                )
            ]
        )

        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            margin=dict(t=40, b=40, l=40, r=40),
        )

        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

        st.markdown(
            f"""
            <div style='background: rgba(99, 102, 241, 0.1); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.2); margin-top: 1rem;'>
                <div style='color: #8B949E; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>Total Attributed Revenue</div>
                <div style='color: #FFFFFF; font-size: 2rem; font-weight: 700; font-family: "Space Grotesk", sans-serif;'>${attr_data["total_revenue"]:,.0f}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        # UI-014: Funnel Velocity Chart
        st.markdown("---")
        st.subheader("Funnel Velocity")
        render_revenue_funnel()

    def _render_benchmarking(self):
        st.subheader("Competitive Benchmarking")
        bench = self.services["benchmarking"].get_benchmarks("demo_location")

        for metric, data in bench.items():
            percentile = data["percentile"]
            color = "#10B981" if percentile >= 80 else "#6366F1" if percentile >= 50 else "#F59E0B"

            st.markdown(
                f"""
                <div style='margin-bottom: 1.5rem;'>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                        <span style='color: #FFFFFF; font-weight: 600; font-family: "Space Grotesk", sans-serif;'>{metric.replace("_", " ").title()}</span>
                        <span style='color: {color}; font-weight: 700;'>{percentile}th Percentile</span>
                    </div>
                    <div style='background: rgba(255, 255, 255, 0.05); height: 8px; border-radius: 4px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.02);'>
                        <div style='background: {color}; width: {percentile}%; height: 100%; box-shadow: 0 0 10px {color}40;'></div>
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

    def _render_coaching(self):
        st.subheader("AI Agent Coaching")
        recommendations = self.services["coaching"].get_coaching_recommendations("demo_agent")

        for rec in recommendations:
            with st.expander(f"💡 {rec['title']}"):
                st.write(rec["description"])
                st.info(f"**Impact:** {rec['expected_impact']}")

    def _render_control_panel(self):
        st.subheader("AI Control Panel")

        # Prompt Versioning
        st.markdown("### 📝 Prompt Version Control")
        if "prompt_versions" not in st.session_state:
            st.session_state.prompt_versions = [
                {
                    "version": "v1.0",
                    "tag": "Baseline",
                    "timestamp": "2025-12-01",
                    "content": "You are a helpful assistant.",
                },
                {
                    "version": "v1.1",
                    "tag": "Production",
                    "timestamp": "2026-01-05",
                    "content": "You are Jorge's AI partner.",
                },
            ]

        selected_version = st.selectbox(
            "Active Prompt Version",
            options=[v["version"] for v in st.session_state.prompt_versions],
            index=len(st.session_state.prompt_versions) - 1,
        )

        version_data = next(v for v in st.session_state.prompt_versions if v["version"] == selected_version)

        st.info(f"**Tag:** {version_data['tag']} | **Deployed:** {version_data['timestamp']}")
        new_prompt = st.text_area("Prompt Content", value=version_data["content"], height=150)

        col_v1, col_v2 = st.columns(2)
        if col_v1.button("💾 Save as New Version", use_container_width=True):
            new_v = f"v1.{len(st.session_state.prompt_versions)}"
            st.session_state.prompt_versions.append(
                {
                    "version": new_v,
                    "tag": "Custom",
                    "content": new_prompt,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d"),
                }
            )
            st.success(f"Version {new_v} saved!")
            st.rerun()

        if col_v2.button("🚀 Rollback to Baseline", use_container_width=True):
            st.warning("Rolling back to Production Baseline...")
            st.toast("Rollback initiated", icon="⏪")

        st.markdown("---")

        # Model Retraining Loop
        st.markdown("### 🔄 Model Retraining Loop")
        st.write(
            "Feedback captured from Lead Intelligence Hub is automatically used to fine-tune your local matching models."
        )

        col_r1, col_r2 = st.columns(2)
        col_r1.metric("Captured Feedback", "128", "+12")
        col_r2.metric("Model Drift", "0.02", "Low")

        if st.button("🛰️ Initiate Model Retraining", type="primary", use_container_width=True):
            with st.spinner("Retraining Property Matcher ML..."):
                import time

                time.sleep(2)
                st.success("Model successfully retrained! Accuracy improved by 3.2%")
                st.balloons()
