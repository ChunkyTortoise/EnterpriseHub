import pandas as pd
import plotly.express as px
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async


def render_neighborhood_explorer(lead_profile: dict = None):
    """Comprehensive neighborhood analysis and exploration"""
    st.subheader("🌍 Neighborhood Intelligence")

    # Try to get Claude service
    try:
        from ghl_real_estate_ai.services.claude_semantic_property_matcher import get_semantic_property_matcher

        semantic_matcher = get_semantic_property_matcher()
        CLAUDE_AVAILABLE = True
    except ImportError:
        CLAUDE_AVAILABLE = False

    # Location input
    col1, col2 = st.columns(2)
    with col1:
        target_address = st.text_input(
            "Enter Address or Neighborhood", placeholder="1234 Oak Street, Austin, TX or 'West Lake Hills'"
        )
    with col2:
        analysis_radius = st.selectbox("Analysis Radius", ["0.5 miles", "1 mile", "2 miles", "5 miles"])

    if st.button("🔍 Analyze Neighborhood", type="primary"):
        with st.spinner("Analyzing neighborhood data..."):
            # Neighborhood overview
            st.markdown("#### 📊 Neighborhood Overview")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏫 School Rating", "9/10", delta="Excellent")
            with col2:
                st.metric("🚶 Walk Score", "75/100", delta="Very Walkable")
            with col3:
                st.metric("🛡️ Safety Score", "8.5/10", delta="Very Safe")
            with col4:
                st.metric("📈 Property Values", "+12%", delta="vs. last year")

            # Detailed analysis tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["🏫 Schools", "🚗 Commute", "🛒 Amenities", "📊 Market Data", "🌐 Demographics"]
            )

            with tab1:
                st.markdown("##### School Information")
                schools_data = [
                    {"School": "Westlake Elementary", "Rating": "10/10", "Distance": "0.3 mi", "Type": "Public"},
                    {"School": "Hill Country Middle", "Rating": "9/10", "Distance": "0.7 mi", "Type": "Public"},
                    {"School": "Westlake High School", "Rating": "10/10", "Distance": "1.2 mi", "Type": "Public"},
                    {"School": "Austin Montessori", "Rating": "8/10", "Distance": "0.5 mi", "Type": "Private"},
                ]
                schools_df = pd.DataFrame(schools_data)
                st.dataframe(schools_df, use_container_width=True)

            with tab2:
                st.markdown("##### Commute Analysis")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**To Downtown Austin:**")
                    st.markdown("• 🚗 Driving: 25-40 minutes")
                    st.markdown("• 🚌 Public Transit: 45-60 minutes")
                    st.markdown("• 🚴 Biking: Not recommended")

                with col2:
                    st.markdown("**To Austin Airport:**")
                    st.markdown("• 🚗 Driving: 35-50 minutes")
                    st.markdown("• 🚌 Public Transit: 60-75 minutes")
                    st.markdown("• 🚕 Rideshare: $45-65")

            with tab3:
                st.markdown("##### Nearby Amenities")

                amenities = {
                    "🍕 Restaurants": ["The Oasis (0.5 mi)", "Hopdoddy Burger (1.2 mi)", "Torchy's Tacos (0.8 mi)"],
                    "🛒 Shopping": [
                        "Whole Foods (0.3 mi)",
                        "Barton Creek Mall (2.1 mi)",
                        "Hill Country Galleria (1.5 mi)",
                    ],
                    "🏥 Healthcare": ["Austin Regional (2.3 mi)", "Urgent Care Plus (0.7 mi)", "CVS Pharmacy (0.4 mi)"],
                    "🎯 Recreation": [
                        "Zilker Park (3.2 mi)",
                        "Austin Country Club (1.1 mi)",
                        "Greenbelt Trail (0.5 mi)",
                    ],
                }

                for category, places in amenities.items():
                    st.markdown(f"**{category}**")
                    for place in places:
                        st.markdown(f"• {place}")
                    st.markdown("")

            with tab4:
                st.markdown("##### Market Trends")

                # Mock market data
                months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
                avg_prices = [485000, 492000, 501000, 515000, 528000, 542000]
                days_on_market = [18, 16, 12, 8, 6, 5]

                col1, col2 = st.columns(2)

                with col1:
                    fig_price = px.line(x=months, y=avg_prices, title="Average Home Prices")
                    fig_price.update_layout(yaxis_title="Price ($)", xaxis_title="Month")
                    st.plotly_chart(fig_price, use_container_width=True)

                with col2:
                    fig_dom = px.bar(x=months, y=days_on_market, title="Average Days on Market")
                    fig_dom.update_layout(yaxis_title="Days", xaxis_title="Month")
                    st.plotly_chart(fig_dom, use_container_width=True)

            with tab5:
                st.markdown("##### Demographics")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Population Stats:**")
                    st.markdown("• Total Population: 12,847")
                    st.markdown("• Median Age: 42 years")
                    st.markdown("• Households: 4,523")
                    st.markdown("• Median Income: $125,000")

                with col2:
                    st.markdown("**Family Composition:**")
                    st.markdown("• Married with Children: 45%")
                    st.markdown("• Young Professionals: 25%")
                    st.markdown("• Empty Nesters: 20%")
                    st.markdown("• Retirees: 10%")

                # ENHANCED: Claude's Social/Cultural Fit
                if CLAUDE_AVAILABLE and lead_profile:
                    st.markdown("---")
                    st.markdown("#### 🧠 Claude's Social/Cultural Fit Analysis")
                    with st.spinner("Analyzing social alignment..."):

                        neighborhood_data = {"name": target_address or "Selected Area"}
                        compatibility = run_async(
                            semantic_matcher.get_neighborhood_compatibility(lead_profile, neighborhood_data)
                        )

                        fit_col1, fit_col2 = st.columns([1, 2])
                        with fit_col1:
                            st.metric("Social Fit Score", f"{compatibility['compatibility_score']:.0%}")
                        with fit_col2:
                            st.success(f"**Cultural Alignment:** {compatibility['cultural_fit']}")

                        st.info(f"**Social Resonance:** {compatibility['social_fit']}")
                        st.write(f"**Lifestyle Alignment:** {compatibility['lifestyle_resonance']}")
                        st.markdown(f"💡 **Agent Strategy:** {compatibility['strategic_tip']}")
