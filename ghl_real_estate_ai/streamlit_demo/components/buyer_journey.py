import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import asyncio
import json
import time
from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

# Import enhanced services
try:
    from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

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
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart
        
        # Mock engagement data
        engagement_dates = pd.date_range(end=pd.Timestamp.now(), periods=10, freq='D')
        engagement_values = [5, 8, 12, 7, 15, 22, 18, 25, 30, 28]
        
        fig = px.area(x=engagement_dates, y=engagement_values, title="Activity Intensity (Last 10 Days)")
        fig.update_traces(line_color='#6366F1', fillcolor='rgba(99, 102, 241, 0.1)')
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

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
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        if churn_risk_data:
            # Churn risk breakdown
            st.markdown("##### Risk Factor Analysis")

            # Create risk factor visualization
            risk_factors = [
                "Activity Level", "Response Rate", "Tour Engagement",
                "Budget Alignment", "Timeline Pressure", "Agent Relationship"
            ]
            risk_scores = [0.1, 0.15, 0.2, 0.25, 0.45, 0.1]  # Mock risk scores

            fig = go.Figure(data=[go.Bar(
                x=risk_factors,
                y=risk_scores,
                marker_color=['#10b981', '#10b981', '#6366f1', '#f59e0b', '#ef4444', '#10b981']
            )])
            fig.update_layout(title="Individual Risk Factors Contributing to Churn")
            st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
            
            # New Behavioral DNA for Retention
            st.markdown("##### 🧬 Behavioral DNA Radar")
            dna_cats = ['Urgency', 'Stability', 'Rapport', 'Tech-Savvy', 'Price Sens.', 'Authority']
            dna_vals = [0.9, 0.4, 0.85, 0.7, 0.3, 0.6]
            
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=dna_vals,
                theta=dna_cats,
                fill='toself',
                line_color='#8B5CF6'
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
            st.plotly_chart(style_obsidian_chart(fig_radar), use_container_width=True)

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

def render_buyer_journey_hub(services, selected_lead_name, render_enhanced_property_search, render_buyer_profile_builder, render_financing_calculator, render_neighborhood_explorer):
    """Render the complete buyer journey experience - Obsidian Command Edition"""
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart, render_dossier_block
    
    st.markdown("""
        <div style="background: rgba(22, 27, 34, 0.85); backdrop-filter: blur(20px); padding: 1.5rem 2.5rem; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);">
            <div>
                <h1 style="font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; margin: 0; color: #FFFFFF; letter-spacing: -0.04em; text-transform: uppercase;">🏠 BUYER JOURNEY HUB</h1>
                <p style="font-family: 'Inter', sans-serif; font-size: 1rem; margin: 0.5rem 0 0 0; color: #8B949E; font-weight: 500; letter-spacing: 0.02em;">Comprehensive buyer experience from search to closing</p>
            </div>
            <div style="text-align: right;">
                <div style="background: rgba(99, 102, 241, 0.1); color: #6366F1; padding: 10px 20px; border-radius: 12px; font-size: 0.85rem; font-weight: 800; border: 1px solid rgba(99, 102, 241, 0.3); letter-spacing: 0.1em;">
                    NODE: {selected_lead_name.upper() if selected_lead_name != '-- Select a Lead --' else 'READY'}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Claude's Journey Counsel - Obsidian Glassmorphism
    st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%); 
                    border: 1px solid rgba(99, 102, 241, 0.2); 
                    border-radius: 20px; 
                    padding: 2.5rem; 
                    margin-bottom: 3rem; 
                    backdrop-filter: blur(10px);'>
            <div style='display: flex; align-items: flex-start; gap: 2rem;'>
                <div style='font-size: 4rem; filter: drop-shadow(0 0 15px rgba(99, 102, 241, 0.4));'>🧭</div>
                <div style='flex-grow: 1;'>
                    <h3 style='margin: 0 0 1rem 0; color: white !important; font-family: "Space Grotesk", sans-serif; font-size: 1.75rem;'>Claude's Journey Counsel</h3>
                    <div style='color: #f8fafc; font-size: 1.1rem; line-height: 1.6; font-weight: 500;'>
    """, unsafe_allow_html=True)
    
    if CLAUDE_AVAILABLE and selected_lead_name != "-- Select a Lead --":
        orchestrator = get_claude_orchestrator()
        
        with st.spinner("Claude is mapping the buyer journey..."):
            try:
                # Get lead context
                lead_options = st.session_state.get('lead_options', {})
                lead_data = lead_options.get(selected_lead_name, {})
                
                # Use chat_query for journey advice
                journey_result = run_async(
                    orchestrator.chat_query(
                        query="Provide strategic buyer journey counsel for this lead. Map their current stage and suggest 2 immediate next steps.",
                        context={"lead_name": selected_lead_name, "lead_data": lead_data, "task": "journey_counsel"}
                    )
                )
                st.markdown(journey_result.content)
            except Exception as e:
                st.markdown(f"Monitoring **{selected_lead_name}**. High probability of conversion if we maintain momentum.")
    else:
        # Dynamic journey insights (Legacy/Fallback)
        if selected_lead_name == "Sarah Chen (Apple Engineer)":
            journey_text = """
            <ul style='margin: 0; padding-left: 1.5rem;'>
                <li><strong>🧭 Path Finder:</strong> Sarah has reached the 'Viewing' stage. She's 40% more likely to close if we show her the Teravista property this weekend.</li>
                <li><strong>📉 Value Alert:</strong> New listing in Cedar Park just hit the market. It aligns with her 45-day relocation timeline perfectly.</li>
            </ul>
            """
        elif selected_lead_name == "David Kim (Investor)":
            journey_text = """
            <ul style='margin: 0; padding-left: 1.5rem;'>
                <li><strong>🧭 Path Finder:</strong> David is in 'Evaluation' mode. He's analyzed 4 Manor properties. High probability of multi-unit offer if Cap Rate is > 5%.</li>
                <li><strong>📉 Value Alert:</strong> An off-market duplex in Del Valle just became available. I've sent him the ROI breakdown.</li>
            </ul>
            """
        else:
            journey_text = """
            <ul style='margin: 0; padding-left: 1.5rem;'>
                <li><strong>🧭 Path Finder:</strong> General engagement is steady. Recommend personalized property alerts for the 'Warm' lead segment.</li>
                <li><strong>📉 Value Alert:</strong> Recent price drops in East Austin provide an opening for first-time buyers.</li>
            </ul>
            """
        st.markdown(journey_text, unsafe_allow_html=True)
    
    st.markdown("</div></div></div>", unsafe_allow_html=True)
    
    if st.button("🚀 Execute Strategic Engagement", use_container_width=True, type="primary"):
        st.toast("Syncing alerts to GHL workflows...", icon="🔔")

    # Buyer navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🔍 Property Search",
        "🔥 Smart Swipe",
        "👤 Buyer Profile",
        "💰 Financing",
        "🌍 Neighborhoods",
        "📅 Saved & Scheduled",
        "📊 Buyer Analytics"
    ])

    with tab1:
        render_enhanced_property_search()

    with tab2:
        try:
            from ghl_real_estate_ai.streamlit_demo.components.property_swipe import render_property_swipe
            render_property_swipe(services, selected_lead_name)
        except ImportError:
            st.info("🔥 Smart Swipe component coming soon")

    with tab3:
        render_buyer_profile_builder()

    with tab4:
        render_financing_calculator()

    with tab5:
        lead_options = st.session_state.get('lead_options', {})
        lead_data = lead_options.get(selected_lead_name)
        render_neighborhood_explorer(lead_data)

    with tab6:
        render_buyer_dashboard()

    with tab7:
        render_buyer_analytics(SERVICES_LOADED=True, get_services=lambda: services)
