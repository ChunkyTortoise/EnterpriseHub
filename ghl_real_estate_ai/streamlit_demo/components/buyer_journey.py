import streamlit as st
import pandas as pd
import plotly.express as px

def render_buyer_dashboard():
    """Buyer's personal dashboard with saved properties and activity"""
    st.subheader("📅 Your Property Dashboard")

    # Dashboard summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("❤️ Saved Properties", "12")
    with col2:
        st.metric("📅 Scheduled Tours", "3")
    with col3:
        st.metric("📧 New Alerts", "5")
    with col4:
        st.metric("🔍 Searches Saved", "2")

    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "❤️ Saved Properties", "📅 Scheduled Tours", "🔔 Alerts & Updates", "📊 Search History"
    ])

    with tab1:
        st.markdown("#### Saved Properties")

        # Property list with action buttons
        saved_properties = [
            {
                "address": "1234 Oak Street, Austin, TX 78704",
                "price": "$485,000",
                "beds": 3,
                "baths": 2,
                "saved_date": "2 days ago",
                "status": "Active"
            },
            {
                "address": "5678 Pine Avenue, Austin, TX 78745",
                "price": "$425,000",
                "beds": 3,
                "baths": 2.5,
                "saved_date": "1 week ago",
                "status": "Under Contract"
            },
            {
                "address": "9012 Elm Drive, Austin, TX 78758",
                "price": "$399,000",
                "beds": 4,
                "baths": 2,
                "saved_date": "3 days ago",
                "status": "Active"
            }
        ]

        for i, prop in enumerate(saved_properties):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    status_color = "green" if prop["status"] == "Active" else "red"
                    st.markdown(f"**{prop['address']}**")
                    st.markdown(f"{prop['price']} • {prop['beds']} bed • {prop['baths']} bath")
                    st.markdown(f"<span style='color: {status_color};'>●</span> {prop['status']} • Saved {prop['saved_date']}", unsafe_allow_html=True)

                with col2:
                    if st.button("📱 Contact Agent", key=f"contact_{i}"):
                        st.success("Agent contacted!")

                with col3:
                    if st.button("📅 Schedule Tour", key=f"schedule_{i}"):
                        st.info("Tour scheduled!")

                with col4:
                    if st.button("🗑️ Remove", key=f"remove_{i}"):
                        st.warning("Property removed from saved list")

                st.markdown("---")

    with tab2:
        st.markdown("#### Upcoming Tours")

        tours = [
            {
                "address": "1234 Oak Street",
                "date": "Tomorrow",
                "time": "2:00 PM",
                "agent": "Sarah Johnson"
            },
            {
                "address": "9012 Elm Drive",
                "date": "Saturday",
                "time": "10:00 AM",
                "agent": "Mike Chen"
            }
        ]

        for tour in tours:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.markdown(f"**{tour['address']}**")
                    st.markdown(f"📅 {tour['date']} at {tour['time']}")
                    st.markdown(f"🏘️ Agent: {tour['agent']}")

                with col2:
                    if st.button("📞 Call Agent", key=f"call_{tour['address']}"):
                        st.success("Calling agent...")

                with col3:
                    if st.button("✏️ Reschedule", key=f"reschedule_{tour['address']}"):
                        st.info("Rescheduling options sent to email")

                st.markdown("---")

    with tab3:
        st.markdown("#### Recent Alerts & Updates")

        alerts = [
            {
                "type": "Price Drop",
                "message": "1234 Oak Street reduced by $10,000",
                "time": "2 hours ago",
                "action": "View Property"
            },
            {
                "type": "New Listing",
                "message": "New property matches your criteria in West Lake Hills",
                "time": "1 day ago",
                "action": "View Listing"
            },
            {
                "type": "Market Update",
                "message": "Austin market report: Inventory up 5% this month",
                "time": "3 days ago",
                "action": "Read Report"
            }
        ]

        for alert in alerts:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    alert_emoji = "💰" if alert["type"] == "Price Drop" else "🏠" if alert["type"] == "New Listing" else "📊"
                    st.markdown(f"**{alert_emoji} {alert['type']}**")
                    st.markdown(alert["message"])
                    st.markdown(f"🕒 {alert['time']}")

                with col2:
                    if st.button(alert["action"], key=f"action_{alert['message'][:10]}"):
                        st.info(f"{alert['action']} clicked!")

                st.markdown("---")

    with tab4:
        st.markdown("#### Search History")

        st.markdown("**Recent Searches:**")
        searches = [
            "3+ bed homes under $500K in West Lake Hills",
            "New construction in Austin ISD",
            "Condos near downtown with parking"
        ]

        for i, search in enumerate(searches):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"• {search}")
            with col2:
                if st.button("🔄 Repeat", key=f"repeat_{i}"):
                    st.success("Search repeated!")

def render_buyer_analytics(SERVICES_LOADED=False, get_services=None):
    """Enhanced analytics and insights for buyer journey with churn prediction"""
    st.subheader("📊 Enhanced Buyer Journey Analytics with AI Insights")

    # Get enhanced services for churn prediction
    churn_risk_data = None
    if SERVICES_LOADED and get_services:
        try:
            services = get_services()
            churn_predictor = services.get("churn_prediction")
            
            if churn_predictor:
                # Simulated churn prediction analysis
                churn_risk_data = {
                    "churn_risk_score": 0.25,  # 25% churn risk
                    "risk_tier": "Low",
                    "engagement_trend": "Stable",
                    "days_since_last_activity": 3,
                    "activity_level": "High",
                    "conversion_probability": 0.78
                }
                st.info("🧠 AI Churn Prediction & Retention Analytics Active")
        except Exception as e:
            st.warning(f"⚠️ Enhanced analytics temporarily unavailable: {str(e)}")

    # Enhanced analytics overview with churn insights
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🔍 Properties Viewed", "47", delta="12 this week")
    with col2:
        st.metric("❤️ Saved Items", "12", delta="+2")
    with col3:
        st.metric("📅 Tour Intent", "High", delta="17% conv")
    with col4:
        st.metric("📉 Churn Risk", f"{churn_risk_data['churn_risk_score']*100:.0f}%" if churn_risk_data else "Low", 
                  delta="Stable", delta_color="inverse")
    with col5:
        st.metric("🎯 Conversion Prob", f"{churn_risk_data['conversion_probability']*100:.0f}%" if churn_risk_data else "75%", 
                  delta="+5%")

    # Analytics tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Engagement", "💰 Price Patterns", "🎯 Preferences", "🚨 Retention"
    ])

    with tab1:
        st.markdown("#### Real-time Engagement Velocity")
        
        # Mock engagement data
        engagement_dates = pd.date_range(end=pd.Timestamp.now(), periods=10, freq='D')
        engagement_values = [5, 8, 12, 7, 15, 22, 18, 25, 30, 28]
        
        fig = px.area(x=engagement_dates, y=engagement_values, title="Activity Intensity (Last 10 Days)")
        fig.update_layout(xaxis_title="Date", yaxis_title="Action Count")
        st.plotly_chart(fig, use_container_width=True)

        # Engagement insights
        if churn_risk_data:
            st.markdown("##### 🔥 AI Engagement Insights")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"• **Activity Level**: {churn_risk_data['activity_level']}")
                st.markdown(f"• **Engagement Trend**: {churn_risk_data['engagement_trend']}")
                st.markdown(f"• **Days Since Last Activity**: {churn_risk_data['days_since_last_activity']}")
            with col2:
                st.markdown("• **Peak Activity Time**: Evenings & Weekends")
                st.markdown("• **Response Rate**: 85% (Excellent)")
                st.markdown("• **Tour-to-View Ratio**: 17% (Above Average)")

    with tab2:
        st.markdown("#### Enhanced Price Analysis with AI Insights")

        price_ranges = ["$300-400K", "$400-500K", "$500-600K", "$600-700K", "$700K+"]
        properties_in_range = [5, 15, 18, 7, 2]

        fig = px.bar(x=price_ranges, y=properties_in_range, title="Properties Viewed by Price Range")
        st.plotly_chart(fig, use_container_width=True)

        # AI price insights
        st.markdown("##### 🧠 AI Price Pattern Analysis")
        st.markdown("• **Sweet Spot**: $500-600K (38% of activity)")
        st.markdown("• **Budget Creep**: +5% average vs. initial budget")
        st.markdown("• **Value Perception**: High value focus (avg. $/sqft viewed)")
        if churn_risk_data and churn_risk_data["conversion_probability"] > 0.7:
            st.success("💰 **Budget Confidence**: Strong indicators of realistic pricing expectations")

    with tab3:
        st.markdown("#### AI-Enhanced Preference Learning")

        st.markdown("**🎯 AI-Discovered Top Features in Saved Properties:**")
        st.markdown("• Updated Kitchen (75% of saved properties) - **High Priority**")
        st.markdown("• 2+ Car Garage (67% of saved properties) - **Important**")
        st.markdown("• Hardwood Floors (58% of saved properties) - **Preferred**")
        st.markdown("• Large Yard (50% of saved properties) - **Desired**")

        st.markdown("**📍 AI-Analyzed Location Preferences:**")
        st.markdown("• West Lake Hills: 35% of searches - **Top Choice**")
        st.markdown("• Central Austin: 25% of searches - **Secondary**")
        st.markdown("• Cedar Park: 20% of searches - **Considering**")
        st.markdown("• Round Rock: 20% of searches - **Backup Option**")

        # AI learning insights
        st.markdown("**🤖 AI Pattern Recognition:**")
        st.markdown("• **Commute Factor**: Strong correlation with location preferences")
        st.markdown("• **School Priority**: High importance detected (8/10 average)")
        st.markdown("• **Move-in Timeline**: Flexible - can wait for right property")
        st.markdown("• **Style Preference**: Transitional/Contemporary over Traditional")

    with tab4:
        st.markdown("#### 🚨 AI Retention & Churn Analytics")

        if churn_risk_data:
            # Churn risk breakdown
            st.markdown("##### Risk Factor Analysis")

            # Create risk factor visualization
            risk_factors = [
                "Activity Level", "Response Rate", "Tour Engagement",
                "Budget Alignment", "Timeline Pressure", "Agent Relationship"
            ]
            risk_scores = [0.1, 0.15, 0.2, 0.25, 0.45, 0.1]  # Mock risk scores

            fig = px.bar(
                x=risk_factors,
                y=risk_scores,
                title="Individual Risk Factors Contributing to Churn",
                color=risk_scores,
                color_continuous_scale=["green", "orange", "red"]
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # Detailed retention recommendations
            st.markdown("##### 💡 AI Retention Recommendations")

            risk_score = churn_risk_data["churn_risk_score"]
            if risk_score < 0.3:
                st.success("✅ **Continue Current Strategy**: Buyer is well-engaged. Maintain weekly check-ins and property alerts.")
            elif risk_score < 0.7:
                st.warning("⚠️ **Enhance Engagement**: Consider:")
                st.markdown("• Increase communication frequency to bi-weekly")
                st.markdown("• Provide market trend insights and exclusive listings")
                st.markdown("• Schedule additional property tours this week")
                st.markdown("• Send personalized neighborhood analysis")
            else:
                st.error("🚨 **Immediate Intervention Required**:")
                st.markdown("• **Schedule urgent call within 24 hours**")
                st.markdown("• **Reassess needs and preferences**")
                st.markdown("• **Provide exclusive market opportunities**")
                st.markdown("• **Consider incentive strategies**")

            # Predictive insights
            st.markdown("##### 🔮 AI Conversion Predictions")
            st.markdown(f"• **7-Day Conversion Probability**: {churn_risk_data['conversion_probability']*0.3:.1%}")
            st.markdown(f"• **30-Day Conversion Probability**: {churn_risk_data['conversion_probability']:.1%}")
            st.markdown(f"• **90-Day Conversion Probability**: {min(churn_risk_data['conversion_probability']*1.2, 0.95):.1%}")

        else:
            st.info("🧠 Enhanced retention analytics available when AI services are loaded")

            # Fallback engagement tips
            st.markdown("##### General Retention Best Practices")
            st.markdown("• Maintain regular communication every 3-5 days")
            st.markdown("• Provide market updates and new listing alerts")
            st.markdown("• Schedule property tours within 48 hours of interest")
            st.markdown("• Send personalized neighborhood and school reports")
            st.markdown("• Monitor response times and engagement levels")

def render_buyer_journey_hub(selected_lead_name, render_enhanced_property_search, render_buyer_profile_builder, render_financing_calculator, render_neighborhood_explorer):
    """Render the complete buyer journey experience"""
    st.title("🏠 Buyer Journey Hub")
    st.markdown("*Comprehensive buyer experience from search to closing*")

    # Claude's Journey Counsel
    with st.container(border=True):
        col_c1, col_c2 = st.columns([1, 8])
        with col_c1:
            st.markdown("<div style='font-size: 3rem; text-align: center;'>🗺️</div>", unsafe_allow_html=True)
        with col_c2:
            st.markdown("### Claude's Buyer Journey Counsel")
            
            # Dynamic journey insights
            if selected_lead_name == "Sarah Chen (Apple Engineer)":
                journey_text = """
                *Monitoring Sarah's North Austin search:*
                - **🧭 Path Finder:** Sarah has reached the 'Viewing' stage. She's 40% more likely to close if we show her the Teravista property this weekend.
                - **📉 Value Alert:** New listing in Cedar Park just hit the market. It aligns with her 45-day relocation timeline perfectly.
                """
            elif selected_lead_name == "David Kim (Investor)":
                journey_text = """
                *Monitoring David's portfolio expansion:*
                - **🧭 Path Finder:** David is in 'Evaluation' mode. He's analyzed 4 Manor properties. High probability of multi-unit offer if Cap Rate is > 5%.
                - **📉 Value Alert:** An off-market duplex in Del Valle just became available. I've sent him the ROI breakdown.
                """
            elif selected_lead_name == "Mike & Jessica Rodriguez (Growing Family)":
                journey_text = """
                *Monitoring the Rodriguez family journey:*
                - **🧭 Path Finder:** They are currently in 'Education' stage. Providing a 'First-Time Buyer' guide will increase their engagement by 60%.
                - **📉 Value Alert:** Found a home in Pflugerville with a huge fenced yard - their top 'must-have'.
                """
            else:
                journey_text = """
                *Monitoring your active buyers in Austin:*
                - **🧭 Path Finder:** Sarah Johnson has reached the 'Viewing' stage. She's 40% more likely to close if we show her properties in the Avery Ranch district this weekend.
                - **📉 Value Alert:** 2 listings in the $500k range just had price drops. I've flagged these for your 'Move-up Buyer' segment.
                """
            st.markdown(journey_text)
            
            if st.button("🚀 Alert All Matching Buyers"):
                st.toast("Syncing price-drop alerts to GHL workflows...", icon="🔔")

    # Buyer navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔍 Property Search",
        "👤 Buyer Profile",
        "💰 Financing",
        "🌍 Neighborhoods",
        "📅 Saved & Scheduled",
        "📊 Buyer Analytics"
    ])

    with tab1:
        render_enhanced_property_search()

    with tab2:
        render_buyer_profile_builder()

    with tab3:
        render_financing_calculator()

    with tab4:
        render_neighborhood_explorer()

    with tab5:
        render_buyer_dashboard()

    with tab6:
        render_buyer_analytics()
