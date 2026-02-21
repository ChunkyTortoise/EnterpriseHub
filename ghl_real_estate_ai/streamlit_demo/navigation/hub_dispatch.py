"""Hub-to-component routing dispatch.

Routes the selected hub name to the appropriate component renderer.
"""

import json
import time

import pandas as pd
import plotly.express as px
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.config.page_config import ASYNC_UTILS_AVAILABLE, run_async
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import render_dossier_block, style_obsidian_chart

try:
    from ghl_real_estate_ai.streamlit_demo.services.service_registry import (
        CLAUDE_COMPANION_AVAILABLE,
        SERVICES_LOADED,
        claude_companion,
    )
except ImportError:
    SERVICES_LOADED = False
    CLAUDE_COMPANION_AVAILABLE = False
    claude_companion = None

# Pre-import components that are always needed
try:
    # AI & Automation
    from ghl_real_estate_ai.streamlit_demo.components.automation_studio import AutomationStudioHub

    # Analytics
    from ghl_real_estate_ai.streamlit_demo.components.billing_dashboard import show as render_billing_dashboard

    # Buyer/Seller journey
    from ghl_real_estate_ai.streamlit_demo.components.buyer_journey import render_buyer_journey_hub
    from ghl_real_estate_ai.streamlit_demo.components.claude_cost_tracking_dashboard import (
        render_claude_cost_tracking_dashboard,
    )
    from ghl_real_estate_ai.streamlit_demo.components.claude_panel import render_claude_assistant
    from ghl_real_estate_ai.streamlit_demo.components.executive_hub import render_executive_hub
    from ghl_real_estate_ai.streamlit_demo.components.financing_calculator import render_financing_calculator
    from ghl_real_estate_ai.streamlit_demo.components.floating_claude import render_floating_claude
    from ghl_real_estate_ai.streamlit_demo.components.landing_page import render_landing_page
    from ghl_real_estate_ai.streamlit_demo.components.lead_intelligence_hub import render_lead_intelligence_hub
    from ghl_real_estate_ai.streamlit_demo.components.marketplace_management import render_marketplace_management
    from ghl_real_estate_ai.streamlit_demo.components.neighborhood_intelligence import render_neighborhood_explorer
    from ghl_real_estate_ai.streamlit_demo.components.ops_optimization import OpsOptimizationHub
    from ghl_real_estate_ai.streamlit_demo.components.property_valuation import render_property_valuation_engine
    from ghl_real_estate_ai.streamlit_demo.components.sales_copilot import SalesCopilotHub
    from ghl_real_estate_ai.streamlit_demo.components.seller_journey import (
        render_marketing_campaign_dashboard,
        render_seller_analytics,
        render_seller_communication_portal,
        render_seller_journey_hub,
        render_seller_prep_checklist,
        render_transaction_timeline,
    )
    from ghl_real_estate_ai.streamlit_demo.components.swarm_visualizer import render_swarm_visualizer
    from ghl_real_estate_ai.streamlit_demo.components.ui_elements import render_insight_card
    from ghl_real_estate_ai.streamlit_demo.realtime_dashboard_integration import render_realtime_intelligence_dashboard

    _COMPONENTS_LOADED = True
except ImportError:
    _COMPONENTS_LOADED = False


def dispatch_hub(
    selected_hub,
    services,
    mock_data,
    claude,
    sparkline_fn,
    render_buyer_profile_builder,
    render_enhanced_property_search,
    render_voice_claude_hub,
    render_proactive_intelligence_hub,
):
    """Route the selected hub to its component renderer.

    Args:
        selected_hub: Name of the hub to render.
        services: Services dict from get_services().
        mock_data: Mock analytics data dict.
        claude: Claude assistant instance.
        sparkline_fn: Sparkline chart generator function.
        render_buyer_profile_builder: Inline buyer profile builder function.
        render_enhanced_property_search: Inline property search function.
        render_voice_claude_hub: Inline voice claude hub function.
        render_proactive_intelligence_hub: Inline proactive intelligence function.
    """
    if not _COMPONENTS_LOADED:
        st.error("Components not loaded. Cannot display hub content.")
        return

    render_claude_assistant(claude)

    selected_market = st.session_state.get("selected_market", "Rancho Cucamonga, CA")
    market_key = "Rancho Cucamonga" if "Rancho Cucamonga" in selected_market else "Rancho"
    elite_mode = st.session_state.get("elite_mode", False)

    if selected_hub == "Jorge AI Landing Page":
        render_landing_page()
    elif selected_hub == "Executive Command Center":
        _render_executive_command_center(services, mock_data, sparkline_fn)
    elif selected_hub == "Lead Intelligence Hub":
        render_lead_intelligence_hub(services, mock_data, claude, market_key, selected_market, elite_mode=elite_mode)
    elif selected_hub == "Data Arbitrage Hub":
        from ghl_real_estate_ai.streamlit_demo.components.data_arbitrage_dashboard import (
            render_data_arbitrage_dashboard,
        )

        render_data_arbitrage_dashboard()
    elif selected_hub == "Jorge War Room":
        from ghl_real_estate_ai.streamlit_demo.components.war_room_dashboard import render_war_room_dashboard

        render_war_room_dashboard()
    elif selected_hub == "Lead Source ROI":
        from ghl_real_estate_ai.streamlit_demo.components.source_roi_dashboard import render_source_roi_dashboard

        render_source_roi_dashboard()
    elif selected_hub == "Agent ROI Dashboard":
        from ghl_real_estate_ai.streamlit_demo.components.agent_roi_dashboard import render_agent_roi_dashboard

        render_agent_roi_dashboard()
    elif selected_hub == "Voice Claude":
        render_voice_claude_hub()
    elif selected_hub == "Voice AI Assistant":
        try:
            from ghl_real_estate_ai.streamlit_demo.components.voice_ai_interface import render_voice_ai_interface

            render_voice_ai_interface(agent_id="demo_agent")
        except ImportError as e:
            st.error(f"Voice AI Assistant temporarily unavailable: {e}")
            st.info("Please ensure all dependencies are installed.")
    elif selected_hub == "Proactive Intelligence":
        render_proactive_intelligence_hub()
    elif selected_hub == "Real-Time Intelligence":
        render_realtime_intelligence_dashboard()
    elif selected_hub == "Buyer Journey Hub":
        render_buyer_journey_hub(
            services,
            st.session_state.get("selected_lead_name", "-- Select a Lead --"),
            render_enhanced_property_search,
            render_buyer_profile_builder,
            render_financing_calculator,
            render_neighborhood_explorer,
        )
    elif selected_hub == "Seller Journey Hub":
        render_seller_journey_hub(
            services,
            render_property_valuation_engine,
            render_seller_prep_checklist,
            render_marketing_campaign_dashboard,
            render_seller_communication_portal,
            render_transaction_timeline,
            render_seller_analytics,
        )
    elif selected_hub == "Automation Studio":
        studio_hub = AutomationStudioHub(services, claude)
        studio_hub.render_hub()
    elif selected_hub == "SMS Compliance Dashboard":
        try:
            from ghl_real_estate_ai.streamlit_demo.components.sms_compliance_dashboard import (
                render_sms_compliance_dashboard,
            )

            render_sms_compliance_dashboard()
        except Exception as e:
            st.error("SMS Compliance Dashboard Temporarily Unavailable")
            st.info(f"Error: {str(e)}")
            st.info("SMS compliance monitoring is being optimized. Please try again shortly.")
    elif selected_hub == "Bot Health Monitoring":
        try:
            from ghl_real_estate_ai.streamlit_demo.components.bot_health_monitoring_dashboard import (
                render_bot_health_dashboard,
            )

            render_bot_health_dashboard()
        except Exception as e:
            st.error("Bot Health Monitoring Dashboard Temporarily Unavailable")
            st.info(f"Error: {str(e)}")
            st.info("Bot health monitoring is being optimized. Please try again shortly.")
    elif selected_hub == "Bot Coordination Flow":
        try:
            from ghl_real_estate_ai.streamlit_demo.components.bot_coordination_flow_dashboard import (
                render_bot_coordination_dashboard,
            )

            render_bot_coordination_dashboard()
        except Exception as e:
            st.error("Bot Coordination Flow Dashboard Temporarily Unavailable")
            st.info(f"Error: {str(e)}")
            st.info("Bot coordination visualization is being optimized. Please try again shortly.")
    elif selected_hub == "Lead Bot Sequences":
        try:
            from ghl_real_estate_ai.streamlit_demo.components.lead_bot_sequence_dashboard import (
                render_lead_bot_sequence_dashboard,
            )

            render_lead_bot_sequence_dashboard()
        except Exception as e:
            st.error("Lead Bot Sequence Dashboard Temporarily Unavailable")
            st.info(f"Error: {str(e)}")
            st.info("Lead bot sequence visualization is being optimized. Please try again shortly.")
    elif selected_hub == "Bot Testing & Validation":
        try:
            from ghl_real_estate_ai.streamlit_demo.components.bot_testing_dashboard import render_bot_testing_dashboard

            render_bot_testing_dashboard()
        except Exception as e:
            st.error("Bot Testing Dashboard Temporarily Unavailable")
            st.info(f"Error: {str(e)}")
            st.info("Bot testing interface is being optimized. Please try again shortly.")
    elif selected_hub == "Sales Copilot":
        copilot_hub = SalesCopilotHub(services, claude)
        copilot_hub.render_hub()
    elif selected_hub == "Billing Analytics":
        try:
            render_billing_dashboard()
        except Exception as e:
            st.error("Billing Analytics Temporarily Unavailable")
            st.info("Billing system integration is being optimized. Please try again shortly.")
            print(f"BILLING DASHBOARD ERROR: {str(e)}")
    elif selected_hub == "Marketplace Management":
        render_marketplace_management()
    elif selected_hub == "Ops & Optimization":
        ops_hub = OpsOptimizationHub(services, claude)
        ops_hub.render_hub()
    elif selected_hub == "Claude Cost Tracking":
        try:
            render_claude_cost_tracking_dashboard()
        except Exception as e:
            st.error(f"Error loading cost tracking dashboard: {str(e)}")
            st.info("Cost tracking dashboard is optimizing. Please try again.")
    elif selected_hub == "Swarm Intelligence":
        lead_name = st.session_state.get("selected_lead_name", "-- Select a Lead --")
        lead_data = st.session_state.get("lead_options", {}).get(lead_name)
        render_swarm_visualizer(lead_name, lead_data)
    elif selected_hub == "Deep Research":
        from ghl_real_estate_ai.streamlit_demo.components.deep_research import render_deep_research_hub

        render_deep_research_hub()
    elif selected_hub == "Services Portfolio":
        from ghl_real_estate_ai.streamlit_demo.services_portfolio import render_services_portfolio

        render_services_portfolio()
    elif selected_hub == "Case Studies":
        from ghl_real_estate_ai.streamlit_demo.case_studies import render_case_studies

        render_case_studies()
    elif selected_hub == "Revenue-Sprint Case Study":
        from ghl_real_estate_ai.streamlit_demo.case_study_revenue_sprint import render_revenue_sprint_case_study

        render_revenue_sprint_case_study()
    elif selected_hub == "Advanced RAG Case Study":
        from ghl_real_estate_ai.streamlit_demo.case_study_advanced_rag import render_advanced_rag_case_study

        render_advanced_rag_case_study()
    elif selected_hub == "DocQA Engine Case Study":
        from ghl_real_estate_ai.streamlit_demo.case_study_docqa import render_docqa_case_study

        render_docqa_case_study()
    elif selected_hub == "Request Quote":
        from ghl_real_estate_ai.streamlit_demo.components.quote_request_form import render_quote_request_form

        render_quote_request_form()

    # Floating Claude Assistant (always rendered)
    render_floating_claude()

    # Footer
    st.markdown("---")
    st.markdown(
        """
<div style='text-align: center; padding: 2rem; background: rgba(13, 17, 23, 0.6); border-radius: 12px; margin-top: 3rem; border: 1px solid rgba(255,255,255,0.05);'>
    <div style='color: #FFFFFF; font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;'>
        Production-Ready Multi-Tenant AI System
    </div>
    <div style='color: #8B949E; font-size: 0.9rem;'>
        Built for Jorge Union[Sales, Claude] Sonnet 4.Union[5, GHL] Integration Ready
    </div>
    <div style='margin-top: 1rem; color: #8B949E; font-size: 0.85rem;'>
        Consolidated Hub Architecture | Backend | 4,937+ Tests Passing
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_executive_command_center(services, mock_data, sparkline_fn):
    """Render the Executive Command Center hub with swarm intelligence."""
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### Executive Swarm Intelligence")
            st.markdown("*Deploy a swarm of specialized agents to analyze your entire business ecosystem*")
        with col2:
            if st.button("Deploy Executive Swarm", width="stretch"):
                st.session_state.deploy_executive_swarm = True

    if st.session_state.get("deploy_executive_swarm", False):
        with st.status("Swarm Intelligence Online. Synchronizing Agents...", expanded=True) as status:
            st.write("Market Analyst: Initializing semantic scan of Rancho Cucamonga real estate trends...")
            time.sleep(0.8)
            st.write("Performance Analyst: Auditing GHL lead conversion pipelines and response velocity...")
            time.sleep(0.8)
            st.write("Pipeline Analyst: Calculating multi-horizon revenue forecasts and leakage points...")
            time.sleep(0.8)
            st.write("Strategic Advisor: Synthesizing specialist findings into executive action plan...")
            time.sleep(0.5)

            # Simulated business data for swarm
            business_data = {
                "market": st.session_state.get("selected_market", "Rancho Cucamonga, CA"),
                "metrics": mock_data.get("executive_metrics", {}),
                "pipeline": mock_data.get("pipeline_data", {}),
            }

            if ASYNC_UTILS_AVAILABLE:
                swarm_results = run_async(claude_companion.run_executive_analysis(business_data))
            else:
                swarm_results = {
                    "executive_summary": "Market analysis complete. Key opportunities identified in Rancho Cucamonga real estate sector.",
                    "recommendations": [
                        "Focus on high-value listings",
                        "Expand digital marketing",
                        "Strengthen agent training",
                    ],
                }
            status.update(label="Swarm Intelligence Report Ready!", state="complete", expanded=False)

            # Display Swarm Results with Premium Styling
            st.markdown("### Executive Intelligence Report")
            advisor = swarm_results.get("strategic_advisor", {})

            synthesis_html = f"""
            <div style='margin-bottom: 1rem;'>
                <p style='font-size: 1.1rem; line-height: 1.6;'>{advisor.get("executive_summary", "N/A")}</p>
            </div>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 1rem;'>
                <div>
                    <h4 style='color: #6366F1; border-bottom: 1px solid rgba(99, 102, 241, 0.3); padding-bottom: 0.5rem;'>Strategic Actions</h4>
                    {"".join(f"<div style='margin-bottom: 0.8rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 4px;'><b>{i + 1}.</b> {item}</div>" for i, item in enumerate(advisor.get("top_3_action_items", [])))}
                </div>
                <div>
                    <h4 style='color: #6366F1; border-bottom: 1px solid rgba(99, 102, 241, 0.3); padding-bottom: 0.5rem;'>12-Month Horizon</h4>
                    <p style='font-style: italic; color: #cbd5e1;'>{advisor.get("strategic_horizon_view", "N/A")}</p>
                    <div style='margin-top: 1rem; display: flex; align-items: center; gap: 10px;'>
                        <span style='font-size: 0.8rem; color: #94a3b8;'>Confidence Index:</span>
                        <div style='flex-grow: 1; height: 8px; background: #161B22; border-radius: 4px; overflow: hidden;'>
                            <div style='width: {int(advisor.get("confidence_in_strategy", 0.8) * 100)}%; height: 100%; background: linear-gradient(90deg, #6366F1, #8B5CF6);'></div>
                        </div>
                        <span style='font-size: 0.8rem; color: #6366F1; font-weight: 700;'>{int(advisor.get("confidence_in_strategy", 0.8) * 100)}%</span>
                    </div>
                </div>
            </div>
            """
            render_dossier_block(synthesis_html, title="STRATEGIC SYNTHESIS: CHIEF STRATEGY OFFICER")

            # Revenue Arbitrage Map
            st.markdown("---")
            st.markdown("### Revenue Arbitrage Map")
            st.markdown("*Predictive yield analysis for institutional-grade decision making*")

            arbitrage_data = pd.DataFrame(
                {
                    "Zip Code": ["91730", "91730", "91730", "91737", "91758", "91739"],
                    "Net Yield %": [14.7, 14.6, 18.8, 13.9, 19.2, 20.1],
                    "Potential Profit": [125000, 110000, 85000, 95000, 75000, 105000],
                }
            )

            fig_map = px.bar(
                arbitrage_data,
                x="Zip Code",
                y="Potential Profit",
                color="Net Yield %",
                text="Net Yield %",
                color_continuous_scale="Viridis",
                title="Profit Potential by Zip Code (Ranked by Yield)",
            )
            fig_map.update_traces(texttemplate="%{text}%", textposition="outside")
            st.plotly_chart(style_obsidian_chart(fig_map), width="stretch")

            st.markdown("#### Specialist Findings")
            specialists = swarm_results.get("specialist_insights", {})

            spec_cols = st.columns(3)
            spec_icons = {"Market Analysis": "globe", "Performance Analysis": "chart", "Pipeline Analysis": "bar-chart"}

            for i, (name, result) in enumerate(specialists.items()):
                with spec_cols[i % 3]:
                    icon = spec_icons.get(name, "robot")

                    st.markdown(
                        f"""
                    <style>
                        .specialist-card {{
                            background: rgba(22, 27, 34, 0.6);
                            border: 1px solid rgba(255,255,255,0.1);
                            border-radius: 12px;
                            padding: 1.5rem;
                            height: 220px;
                            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                            position: relative;
                            overflow: hidden;
                        }}
                        .specialist-card:hover {{
                            transform: translateY(-8px) scale(1.02);
                            border-color: #6366F1;
                            box-shadow: 0 15px 30px rgba(99, 102, 241, 0.2);
                            background: rgba(99, 102, 241, 0.05);
                        }}
                        .specialist-card::before {{
                            content: "";
                            position: absolute;
                            top: 0; left: 0; width: 100%; height: 2px;
                            background: linear-gradient(90deg, transparent, #6366F1, transparent);
                            transform: translateX(-100%);
                            transition: transform 0.6s ease;
                        }}
                        .specialist-card:hover::before {{
                            transform: translateX(100%);
                        }}
                    </style>
                    <div class="specialist-card">
                        <div style='font-size: 1.8rem; margin-bottom: 0.8rem;'>{icon}</div>
                        <h4 style='margin: 0; color: white; font-family: "Space Grotesk", sans-serif;'>{name}</h4>
                        <div style='margin-top: 1rem; font-size: 0.85rem; color: #94a3b8; line-height: 1.4;'>
                            {json.dumps(result, indent=2)[:150]}...
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    with st.expander("Expand Intelligence"):
                        st.json(result)

            if st.button("Close Report", width="stretch"):
                st.session_state.deploy_executive_swarm = False
                st.rerun()

    st.markdown("---")
    render_executive_hub(services, mock_data, sparkline_fn, render_insight_card)
