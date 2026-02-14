import plotly.express as px
import streamlit as st


def render_property_valuation_engine():
    """AI-powered property valuation and CMA engine"""
    st.subheader("📊 AI Property Valuation Engine")

    # Property details input
    st.markdown("#### 🏠 Property Information")

    col1, col2 = st.columns(2)
    with col1:
        property_address = st.text_input("Property Address", placeholder="1234 Main Street, Rancho Cucamonga, CA 91730")
        property_type = st.selectbox("Property Type", ["Single Family", "Townhome", "Condo", "Duplex", "Multi-Family"])
        year_built = st.number_input("Year Built", value=1995, step=1)
        lot_size = st.number_input("Lot Size (acres)", value=0.25, step=0.05)

    with col2:
        bedrooms = st.selectbox("Bedrooms", [1, 2, 3, 4, 5, 6, "7+"])
        bathrooms = st.selectbox("Bathrooms", [1, 1.5, 2, 2.5, 3, 3.5, 4, "4.5+"])
        square_footage = st.number_input("Square Footage", value=1856, step=50)
        garage_spaces = st.selectbox("Garage Spaces", [0, 1, 2, 3, "4+"])

    # Property features
    st.markdown("#### ✨ Property Features & Condition")
    col1, col2, col3 = st.columns(3)

    with col1:
        features = st.multiselect(
            "Special Features",
            [
                "Swimming Pool",
                "Fireplace",
                "Hardwood Floors",
                "Granite Counters",
                "Updated Kitchen",
                "Master Suite",
                "Office/Study",
                "Basement",
                "Deck/Patio",
                "Fenced Yard",
                "Workshop/Storage",
            ],
        )

    with col2:
        condition = st.selectbox(
            "Overall Condition",
            [
                "Excellent - Move-in Ready",
                "Good - Minor Updates Needed",
                "Fair - Some Improvements Required",
                "Needs Work - Major Renovations",
            ],
        )

    with col3:
        recent_updates = st.multiselect(
            "Recent Updates (Last 5 Years)",
            [
                "Roof Replacement",
                "HVAC System",
                "Windows",
                "Flooring",
                "Kitchen Renovation",
                "Bathroom Remodel",
                "Paint Interior",
                "Paint Exterior",
                "Appliances",
                "Landscaping",
            ],
        )

    # Market analysis
    if st.button("🔍 Generate Valuation Analysis", type="primary"):
        with st.spinner("Analyzing property value..."):
            # Main valuation results
            st.markdown("#### 🎯 Valuation Results")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏠 Estimated Value", "$487,500", delta="$12,500 vs. last month")
            with col2:
                st.metric("📊 Value Range", "$465K - $510K", delta="95% confidence")
            with col3:
                st.metric("💰 $/Sq Ft", "$263", delta="$8 above market avg")
            with col4:
                st.metric("📈 Market Position", "Strong", delta="Good timing to sell")

            # Valuation methodology tabs
            tab1, tab2, tab3, tab4 = st.tabs(
                ["🏘️ Comparable Sales", "📊 Market Analysis", "🎯 Pricing Strategy", "📈 Value Drivers"]
            )

            with tab1:
                st.markdown("##### Recent Comparable Sales")

                comps = [
                    {
                        "address": "1245 Oak Street (0.2 mi)",
                        "sold_price": "$495,000",
                        "sold_date": "45 days ago",
                        "beds": 3,
                        "baths": 2,
                        "sqft": 1920,
                        "price_per_sqft": "$258",
                        "adjustments": "+$7,500",
                    },
                    {
                        "address": "1156 Pine Avenue (0.3 mi)",
                        "sold_price": "$475,000",
                        "sold_date": "62 days ago",
                        "beds": 3,
                        "baths": 2.5,
                        "sqft": 1785,
                        "price_per_sqft": "$266",
                        "adjustments": "-$2,200",
                    },
                    {
                        "address": "1289 Elm Drive (0.4 mi)",
                        "sold_price": "$510,000",
                        "sold_date": "28 days ago",
                        "beds": 4,
                        "baths": 2,
                        "sqft": 1945,
                        "price_per_sqft": "$262",
                        "adjustments": "+$5,100",
                    },
                ]

                for comp in comps:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                        with col1:
                            st.markdown(f"**{comp['address']}**")
                            st.markdown(f"💰 {comp['sold_price']} • Sold {comp['sold_date']}")
                            st.markdown(f"🛏️ {comp['beds']} bed • 🛁 {comp['baths']} bath • 📐 {comp['sqft']} sqft")

                        with col2:
                            st.markdown(f"**{comp['price_per_sqft']}**/sqft")

                        with col3:
                            adjustment_color = "green" if "+" in comp["adjustments"] else "red"
                            st.markdown(
                                f"<span style='color: {adjustment_color};'>**{comp['adjustments']}**</span>",
                                unsafe_allow_html=True,
                            )

                        with col4:
                            sold_val = int(comp["sold_price"].replace("$", "").replace(",", ""))
                            adj_val = int(comp["adjustments"].replace("$", "").replace(",", "").replace("+", ""))
                            st.markdown(f"**Adjusted**: ${sold_val + adj_val:,}")

                        st.markdown("---")

            with tab2:
                st.markdown("##### Market Conditions Analysis")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Neighborhood Trends (Last 6 Months)**")
                    st.markdown("• Average Days on Market: 8 days")
                    st.markdown("• Price Appreciation: +12% YoY")
                    st.markdown("• Inventory Level: Low (2.1 months)")
                    st.markdown("• Market Type: Strong Seller's Market")

                    st.markdown("**Seasonal Factors**")
                    st.markdown("• Current Season: Peak selling season")
                    st.markdown("• Interest Rates: 7.25% (stable)")
                    st.markdown("• Economic Outlook: Positive")

                with col2:
                    # Market trends chart
                    months = ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"]
                    median_prices = [425000, 435000, 448000, 455000, 465000, 475000]

                    fig = px.line(x=months, y=median_prices, title="Neighborhood Median Prices")
                    fig.update_layout(yaxis_title="Price ($)", xaxis_title="Month")
                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown("**Price Per Square Foot Trends**")
                    price_per_sqft = [245, 250, 255, 258, 260, 263]
                    fig2 = px.bar(x=months, y=price_per_sqft, title="Price Per Sq Ft")
                    st.plotly_chart(fig2, use_container_width=True)

            with tab3:
                st.markdown("##### Strategic Pricing Recommendations")

                pricing_strategies = [
                    {
                        "strategy": "🎯 Competitive Pricing",
                        "price": "$485,000",
                        "pros": "Quick sale, multiple offers likely",
                        "cons": "May leave money on table",
                        "timeline": "5-10 days",
                    },
                    {
                        "strategy": "💰 Market Value Pricing",
                        "price": "$495,000",
                        "pros": "Full market value, good negotiating room",
                        "cons": "May take longer to sell",
                        "timeline": "10-20 days",
                    },
                    {
                        "strategy": "🚀 Aspirational Pricing",
                        "price": "$510,000",
                        "pros": "Maximum return if market supports",
                        "cons": "Risk of sitting on market too long",
                        "timeline": "20-45 days",
                    },
                ]

                for strategy in pricing_strategies:
                    with st.expander(f"{strategy['strategy']} - {strategy['price']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**✅ Pros:** {strategy['pros']}")
                            st.markdown(f"**⚠️ Cons:** {strategy['cons']}")
                        with col2:
                            st.markdown(f"**⏱️ Expected Timeline:** {strategy['timeline']}")

                st.info(
                    "💡 **Recommendation:** Start with Market Value Pricing ($495,000) to maximize return while ensuring reasonable sale timeline."
                )

            with tab4:
                st.markdown("##### Value Enhancement Opportunities")

                improvements = [
                    {
                        "improvement": "Fresh Interior Paint",
                        "cost": "$2,500",
                        "value_add": "$5,000",
                        "roi": "100%",
                        "priority": "High",
                    },
                    {
                        "improvement": "Kitchen Counter Update",
                        "cost": "$4,500",
                        "value_add": "$7,500",
                        "roi": "67%",
                        "priority": "Medium",
                    },
                    {
                        "improvement": "Landscape Enhancement",
                        "cost": "$1,500",
                        "value_add": "$3,500",
                        "roi": "133%",
                        "priority": "High",
                    },
                    {
                        "improvement": "Master Bath Update",
                        "cost": "$8,000",
                        "value_add": "$10,000",
                        "roi": "25%",
                        "priority": "Low",
                    },
                ]

                st.markdown("**Recommended Pre-Sale Improvements:**")

                for improvement in improvements:
                    priority_color = (
                        "green"
                        if improvement["priority"] == "High"
                        else "orange"
                        if improvement["priority"] == "Medium"
                        else "red"
                    )

                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

                        with col1:
                            st.markdown(f"**{improvement['improvement']}**")
                        with col2:
                            st.markdown(f"Cost: {improvement['cost']}")
                        with col3:
                            st.markdown(f"Value: {improvement['value_add']}")
                        with col4:
                            st.markdown(f"ROI: {improvement['roi']}")
                        with col5:
                            st.markdown(
                                f"<span style='color: {priority_color};'>**{improvement['priority']}**</span>",
                                unsafe_allow_html=True,
                            )

                st.markdown("**Total Investment:** $16,500 | **Total Value Add:** $26,000 | **Net Gain:** $9,500")

    # Additional tools
    st.markdown("#### 🛠️ Additional Valuation Tools")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📧 Email CMA Report"):
            st.success("Comprehensive CMA report sent to your email!")

    with col2:
        if st.button("📊 Generate Listing Sheet"):
            st.info("Professional listing sheet created!")

    with col3:
        if st.button("📱 Share with Client"):
            st.info("Valuation summary shared with client!")
