import asyncio

import streamlit as st

from ghl_real_estate_ai.agent_system.v2.conductor import process_request
from ghl_real_estate_ai.services.performance_monitoring_service import performance_monitor
from ghl_real_estate_ai.services.property_visualizer import PropertyVisualizer

st.set_page_config(page_title="V2 Agentic Property Showcase", layout="wide")


# Custom CSS for Dynamic Styling based on Agent Output
def apply_custom_style(colors):
    if not colors or len(colors) < 2:
        colors = ["#0A0E14", "#00E5FF"]

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {colors[0]};
            color: #FFFFFF;
        }}
        .property-card {{
            background: rgba(255, 255, 255, 0.05);
            border-left: 5px solid {colors[1]};
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .agent-badge {{
            background: {colors[1]};
            color: {colors[0]};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 5px;
        }}
        .match-score {{
            color: {colors[1]};
            font-size: 1.2em;
            font-weight: bold;
        }}
        .metric-box {{
            background: rgba(0, 229, 255, 0.1);
            border: 1px solid rgba(0, 229, 255, 0.3);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        </style>
    """,
        unsafe_allow_html=True,
    )


st.title("🏙️ Modular Agentic Powerhouse (V2)")
st.subheader("Phase 6: Enterprise Production Platform")

with st.sidebar:
    st.header("Control Center")
    address = st.text_input("Property Address", "123 Maple St, Rancho Cucamonga, CA")
    market = st.text_input("Market", "Rancho Cucamonga, CA")
    run_button = st.button("🚀 TRIGGER ENTERPRISE PIPELINE")

    st.divider()
    st.success("✅ Phase 6 Complete: Enterprise Polish, High-Fidelity Visuals, and Performance Monitoring active.")

    # Live Platform Metrics
    st.markdown("### 📊 Platform Health")
    stats = performance_monitor.get_summary_metrics()
    if stats.get("status") != "No data":
        st.metric("Avg Latency", f"{stats['avg_latency']}s")
        st.metric("Data Moat Size", f"{stats['moat_size']} samples")
        st.metric("Total Est. Cost", f"${stats['total_estimated_cost']}")
    else:
        st.info("No runs logged yet.")

if run_button:
    with st.status("🛠️ Orchestrating Enterprise Agents...", expanded=True) as status:
        st.write("🔍 Researching Market Data...")
        try:
            # We use a wrapper to handle asyncio in streamlit
            result = asyncio.run(process_request(address, "full_pipeline", market))

            if result.get("errors"):
                st.error(f"Pipeline encountered errors: {result['errors']}")

            status.update(label="✅ Enterprise Pipeline Complete!", state="complete", expanded=False)

            # 1. Apply Dynamic Styling
            design_data = result.get("design_data", {})
            theme_colors = ["#0A0E14", "#00E5FF"]  # Default
            if design_data.get("staged_rooms"):
                theme_colors = design_data["staged_rooms"][0].get("color_palette", theme_colors)

            apply_custom_style(theme_colors)

            # 2. Responsive Layout using Tabs for Mobile Excellence
            tab_main, tab_visuals, tab_market, tab_lead_recovery = st.tabs(
                ["📋 Summary", "🎨 Visuals", "📊 Market & Moat", "🚀 Lead Recovery"]
            )

            with tab_main:
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.markdown(
                        f"### <span class='agent-badge'>EXECUTIVE</span> {result.get('executive_summary', {}).get('investment_verdict', 'ANALYSIS_COMPLETE')}",
                        unsafe_allow_html=True,
                    )
                    st.write(result.get("executive_summary", {}).get("executive_summary", "No summary generated."))

                    st.markdown("---")
                    st.markdown(
                        "### <span class='agent-badge'>ANALYST</span> Financial Projections", unsafe_allow_html=True
                    )
                    financials = result.get("analysis_results", {}).get("financials", {})
                    f_cols = st.columns(2)
                    for i, (k, v) in enumerate(financials.items()):
                        if isinstance(v, (int, float)):
                            with f_cols[i % 2]:
                                st.metric(label=k.replace("_", " ").title(), value=f"${v:,.0f}" if v > 1000 else v)

                with col_right:
                    st.markdown("### <span class='agent-badge'>MATCHES</span> GHL Lead Bridge", unsafe_allow_html=True)
                    matched_leads = result.get("matched_leads", [])
                    if matched_leads:
                        for lead in matched_leads[:3]:
                            st.markdown(
                                f"""
                            <div class='property-card'>
                                <strong>{lead["first_name"]} {lead["last_name"]}</strong><br/>
                                <span class='match-score'>{lead["match_score"]}% Match</span>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                    st.markdown("### <span class='agent-badge'>PLATFORM_EVAL</span> Integrity", unsafe_allow_html=True)
                    evals = result.get("evaluations", {})
                    if evals:
                        score = evals.get("overall_platform_score", 0) * 100
                        st.progress(score / 100, text=f"Score: {score:.1f}%")

            with tab_visuals:
                st.markdown(
                    "### <span class='agent-badge'>AI_STAGING</span> High-Fidelity Gallery", unsafe_allow_html=True
                )
                staged_images = result.get("staged_images", [])
                if staged_images:
                    cols = st.columns(min(len(staged_images), 3))
                    for idx, img in enumerate(staged_images):
                        with cols[idx % 3]:
                            st.image(img["url"], caption=f"{img['room']} ({img['provider']})", use_container_width=True)

                st.markdown("---")
                st.markdown("### <span class='agent-badge'>VISUALIZER</span> 3D Digital Twin", unsafe_allow_html=True)
                viz = PropertyVisualizer()
                html = viz.generate_threejs_html(address)
                st.components.v1.html(html, height=400)

            with tab_market:
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown("### <span class='agent-badge'>RESEARCH</span> Market Context", unsafe_allow_html=True)
                    research = result.get("research_data", {})
                    context = research.get("market_context", {})
                    if context:
                        st.info(
                            f"**Neighborhood:** {context.get('neighborhood')}\n\n**Price Trend:** {context.get('price_trend')}\n\n**Inventory:** {context.get('inventory_level')}"
                        )

                with col_m2:
                    st.markdown("### <span class='agent-badge'>PHASE_7</span> Competitive Moat", unsafe_allow_html=True)
                    analysis = result.get("analysis_results", {})
                    comp = analysis.get("competitive_landscape")
                    if comp:
                        st.metric("Competitor Count", comp.get("competitor_count", 0))
                        st.metric("Threat Level", comp.get("threat_level", "Unknown"))
                        st.write(f"**Strategic Advantage:** {comp.get('strategic_advantage')}")
                    else:
                        st.warning("Competitive intelligence data pending.")

            with tab_lead_recovery:
                st.markdown(
                    "### <span class='agent-badge'>SERVICE_6</span> Hardened Lead Recovery", unsafe_allow_html=True
                )
                s6 = result.get("service6_insights", {})
                recovery = s6.get("recovery_analysis", [])
                if recovery:
                    for item in recovery:
                        with st.expander(f"Lead ID: {item['lead_id']} - Priority: {item['priority'].upper()}"):
                            col_rec1, col_rec2 = st.columns([2, 1])
                            with col_rec1:
                                st.write(f"**Unified Score:** {item['unified_score']}/100")
                                st.write(f"**Sentiment:** {item['sentiment']}")
                                st.write("**Recommended Actions:**")
                                for action in item["recommended_actions"]:
                                    st.write(f"- {action}")
                            with col_rec2:
                                if item.get("ghl_hardened"):
                                    st.success("⚡ GHL HARDENED")
                                    st.caption("Automated tags & workflows triggered.")
                                else:
                                    st.info("Status: Monitored")
                else:
                    st.info("No lead recovery analysis available for this property.")

                st.markdown("---")
                st.markdown(
                    "### <span class='agent-badge'>MARKETING</span> Personalized Outreach", unsafe_allow_html=True
                )
                marketing = result.get("marketing_campaigns", {})
                if marketing:
                    st.success(f"**Campaign:** {marketing.get('campaign_name')}")
                    st.text_area("📱 SMS Copy", marketing.get("sms_copy"), height=100)
                    st.text_area("📧 Email Body", marketing.get("email_body"), height=200)

        except Exception as e:
            st.error(f"Pipeline Failed: {str(e)}")
            st.exception(e)
else:
    st.write("Enter a property address and hit trigger to see the fully polished Phase 6 Enterprise Platform.")
    st.image(
        "https://images.unsplash.com/photo-1460472178825-e5240623abe5?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
        caption="Modular Agentic Powerhouse: Enterprise Edition",
    )
