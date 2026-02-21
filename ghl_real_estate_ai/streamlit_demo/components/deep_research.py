"""
Deep Research Hub Component - Powered by Perplexity AI.
Provides real-time web research and market intelligence within the dashboard.
"""

import asyncio

import streamlit as st

from ghl_real_estate_ai.services.perplexity_researcher import get_perplexity_researcher
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async


def render_deep_research_hub():
    """Renders the Deep Research hub interface."""
    st.markdown(
        """
    <div style='display: flex; align-items: center; gap: 15px; margin-bottom: 1.5rem;'>
        <div style='background: #1e293b; padding: 12px; border-radius: 12px; border: 1px solid #334155;'>
            <span style='font-size: 2rem;'>🛰️</span>
        </div>
        <div>
            <h1 style='margin: 0; font-size: 2rem; font-weight: 700; color: white;'>Deep Research</h1>
            <p style='margin: 0; color: #8B949E; font-size: 1rem;'>Perplexity-powered real-time market & property intelligence</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    researcher = get_perplexity_researcher()

    if not researcher.enabled:
        st.warning("⚠️ Perplexity API key not detected. Deep Research is currently in simulated mode.")
        st.info("To enable real-time research, add PERPLEXITY_API_KEY to your .env file.")

    # Research Tabs
    tabs = st.tabs(
        [
            "🌐 Market Intelligence",
            "🏠 Property Deep Dive",
            "🏙️ Neighborhood Analysis",
            "🧠 Custom Research",
            "🧪 Hybrid Synthesis",
        ]
    )

    with tabs[0]:
        st.subheader("Market Intelligence")
        col1, col2 = st.columns([2, 1])
        with col1:
            market_query = st.text_input(
                "Location", placeholder="Ex: Rancho Cucamonga, CA or Miami, FL", key="market_loc"
            )
        with col2:
            period = st.selectbox(
                "Period", ["Current", "Last Quarter", "2025 Review", "2026 Forecast"], key="market_period"
            )

        if st.button("🛰️ Run Market Research", type="primary"):
            if market_query:
                with st.spinner(f"Performing deep research on {market_query}..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = run_async(researcher.get_market_trends(market_query, period))
                    st.markdown("### Research Results")
                    st.markdown(result)
            else:
                st.error("Please enter a location.")

    with tabs[1]:
        st.subheader("Property Deep Dive")
        property_address = st.text_input(
            "Property Address", placeholder="Ex: 123 Maple Ave, Rancho Cucamonga, CA", key="prop_address"
        )

        if st.button("🔍 Analyze Property", type="primary"):
            if property_address:
                with st.spinner(f"Searching public records for {property_address}..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = run_async(researcher.find_property_info(property_address))
                    st.markdown("### Property Report")
                    st.markdown(result)
            else:
                st.error("Please enter an address.")

    with tabs[2]:
        st.subheader("Neighborhood Analysis")
        col1, col2 = st.columns(2)
        with col1:
            nb_name = st.text_input("Neighborhood", placeholder="Ex: Victoria Gardens", key="nb_name")
        with col2:
            nb_city = st.text_input("City", placeholder="Ex: Rancho Cucamonga", key="nb_city")

        if st.button("🏙️ Analyze Neighborhood", type="primary"):
            if nb_name and nb_city:
                with st.spinner(f"Analyzing {nb_name} in {nb_city}..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = run_async(researcher.analyze_neighborhood(nb_name, nb_city))
                    st.markdown("### Neighborhood Profile")
                    st.markdown(result)
            else:
                st.error("Please enter both neighborhood and city.")

    with tabs[3]:
        st.subheader("Custom Research Query")
        custom_topic = st.text_area(
            "Research Topic",
            placeholder="Enter any real estate related topic you want to research in depth...",
            height=150,
        )
        custom_context = st.text_input(
            "Additional Context (Optional)", placeholder="Ex: Focus on multi-family investment opportunities"
        )

        if st.button("🧠 Execute Deep Research", type="primary"):
            if custom_topic:
                with st.spinner("Executing deep research..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = run_async(researcher.research_topic(custom_topic, custom_context))
                    st.markdown("### Research Report")
                    st.markdown(result)
            else:
                st.error("Please enter a research topic.")

    with tabs[4]:
        st.subheader("🧪 Hybrid Synthesis (Perplexity + Claude)")
        st.info("This mode uses Perplexity for real-time data and Claude for strategic architectural synthesis.")

        hybrid_topic = st.text_input(
            "Strategic Research Topic",
            placeholder="Ex: Impact of Apple's expansion on North Rancho Cucamonga property values",
        )

        if st.button("🚀 Run Hybrid Analysis", type="primary"):
            if hybrid_topic:
                from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

                orchestrator = get_claude_orchestrator()

                with st.spinner("Step 1: Gathering real-time data via Perplexity..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # We can use the orchestrator's new perform_research method
                    with st.spinner("Step 2: Synthesizing strategic insights via Claude..."):
                        response = run_async(orchestrator.perform_research(hybrid_topic))

                        st.markdown("### 🧠 Claude's Strategic Synthesis")
                        st.markdown(response.content)

                        with st.expander("📊 View Raw Data Sources", expanded=False):
                            st.caption("Data gathered via Perplexity Pro")
                            # In a real implementation, we'd store the raw research too
                            st.info("Raw research data was used to generate the synthesis above.")
            else:
                st.error("Please enter a topic for analysis.")

    # Sidebar Research History (Mocked for now)
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📜 Research History")
        st.caption("Recent Perplexity Queries")
        st.markdown("""
        - *Rancho Cucamonga Market Trends (Jan 2026)*
        - *Victoria Gardens Park Neighborhood Analysis*
        - *91730 Zip Code Investment Potential*
        """)
