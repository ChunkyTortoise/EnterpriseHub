import streamlit as st
import pandas as pd
import json
import datetime
from pathlib import Path

def render_lead_intelligence_hub(services, mock_data, claude, market_key, selected_market):
    st.header("🧠 Lead Intelligence Hub")
    st.markdown("*Deep dive into individual leads with AI-powered insights*")
    
    # Access global lead_options - ensure it exists
    if 'lead_options' not in st.session_state:
        st.error("Lead options not initialized. Please refresh the page.")
        return
    
    lead_options = st.session_state.lead_options
    
    # Lead selector at the top for all tabs to use
    st.markdown("### 🎯 Select a Lead")
    lead_names = list(st.session_state.lead_options.keys())
    try:
        default_idx = lead_names.index(st.session_state.selected_lead_name)
    except ValueError:
        default_idx = 0

    selected_lead_name = st.selectbox(
        "Choose a lead to analyze:",
        lead_names,
        index=default_idx,
        key="hub_lead_selector_top",
        on_change=lambda: st.session_state.update({"selected_lead_name": st.session_state.hub_lead_selector_top})
    )
    
    # Update session state
    st.session_state.selected_lead_name = selected_lead_name
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🎯 Lead Scoring",
        "🚨 Churn Early Warning",
        "🏠 Property Matcher (Phase 2)",
        "🌐 Buyer Portal (Phase 3)",
        "📊 Segmentation",
        "🎨 Personalization",
        "🔮 Predictions",
        "💬 Simulator"
    ])
    
    with tab1:
        st.subheader("AI Lead Scoring")
        
        # Create columns for all cases
        col_map, col_details = st.columns([1, 1])
        
        with col_map:
            # Try to use the enhanced interactive map component
            try:
                from components.interactive_lead_map import render_interactive_lead_map, generate_sample_lead_data
                
                # Load or generate lead data with geographic coordinates
                lead_map_data_path = Path(__file__).parent / "data" / "lead_map_data.json"
                if lead_map_data_path.exists():
                    with open(lead_map_data_path) as f:
                        all_lead_data = json.load(f)
                        leads_with_geo = all_lead_data.get(market_key, [])
                else:
                    # Fallback to generating sample data
                    leads_with_geo = generate_sample_lead_data(market_key)
                
                # Render the interactive map
                render_interactive_lead_map(leads_with_geo, market=market_key)
                
            except ImportError:
                # Fallback to legacy static map
                st.markdown("#### 📍 Hot Lead Clusters")
                # Generate mock map data
                if market_key == "Rancho":
                    map_data = pd.DataFrame({
                        'lat': [34.1200, 34.1100, 34.1000, 34.1300, 34.1150],
                        'lon': [-117.5700, -117.5800, -117.5600, -117.5900, -117.5750],
                        'type': ['Hot', 'Hot', 'Warm', 'Cold', 'Hot'],
                        'value': [100, 80, 50, 20, 90]
                    })
                else:
                    map_data = pd.DataFrame({
                        'lat': [30.2672, 30.2700, 30.2500, 30.2800, 30.2600],
                        'lon': [-97.7431, -97.7500, -97.7300, -97.7600, -97.7400],
                        'type': ['Hot', 'Hot', 'Warm', 'Cold', 'Hot'],
                        'value': [100, 80, 50, 20, 90]
                    })
                
                st.map(map_data, zoom=11, use_container_width=True)
                st.caption(f"Real-time visualization of high-value lead activity in {selected_market}")

        with col_details:
            st.markdown("#### 🎯 Lead Analysis")
            st.markdown(f"**Analyzing:** {selected_lead_name}")
            
            # Claude's Behavioral Deep Dive
            with st.container(border=True):
                st.markdown(f"**🤖 Claude's Behavioral Insight: {selected_lead_name}**")
                if selected_lead_name == "Sarah Chen (Apple Engineer)":
                    insight_text = "High-velocity lead. Apple engineers are data-driven; she responded to the 'Market Trend' link within 12 seconds. She's prioritizing commute efficiency over sqft. Focus on: Teravista connectivity."
                elif selected_lead_name == "Mike & Jessica Rodriguez (Growing Family)":
                    insight_text = "High-sentiment, low-confidence lead. They are checking 'First-time buyer' articles daily. Sentiment: 88% Positive but cautious. Focus on: Safety metrics and monthly payment breakdown."
                elif selected_lead_name == "David Kim (Investor)":
                    insight_text = "Analytical veteran. He's ignored the 'Lifestyle' highlights and went straight to the 'Cap Rate' tool. He has 3 tabs open on Manor area comps. Focus on: Off-market yield analysis."
                elif selected_lead_name == "Robert & Linda Williams (Luxury Downsizer)":
                    insight_text = "Relationship-focused. They've spent 4 minutes reading Jorge's 'About Me'. Sentiment: 95% Positive. They value trust over automation. Focus on: Personal concierge and exclusive downtown access."
                elif selected_lead_name == "Sarah Johnson":
                    insight_text = "Highly motivated. She responded within 45 seconds to my last text. Sentiment: 92% Positive. Focus on: School District accuracy."
                elif selected_lead_name == "Mike Chen":
                    insight_text = "Cautious. He's asking about 'Value per SqFt' comparison. Sentiment: Neutral. Focus on: Investment ROI data."
                else:
                    insight_text = "Initial discovery phase. Engagement is low. Sentiment: Undetermined. Focus on: Qualifying location preferences."
                st.info(insight_text)

            # Empty state when no lead selected
            if selected_lead_name == "-- Select a Lead --":
                st.markdown("""
                <div style='background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                            padding: 3rem 2rem; 
                            border-radius: 15px; 
                            text-align: center;
                            border: 2px dashed #0ea5e9;
                            margin-top: 2rem;'>
                    <div style='font-size: 4rem; margin-bottom: 1rem;'>🎯</div>
                    <h3 style='color: #0369a1; margin: 0 0 0.5rem 0;'>Select a Lead to Begin Analysis</h3>
                    <p style='color: #075985; font-size: 0.95rem; max-width: 400px; margin: 0 auto;'>
                        Choose a lead from the dropdown above to view their AI-powered intelligence profile, 
                        property matches, and predictive insights.
                    </p>
                    <div style='margin-top: 2rem; display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;'>
                        <div style='background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                            <div style='font-size: 1.5rem;'>📊</div>
                            <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;'>Lead Scoring</div>
                        </div>
                        <div style='background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                            <div style='font-size: 1.5rem;'>🏠</div>
                            <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;'>Property Match</div>
                        </div>
                        <div style='background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                            <div style='font-size: 1.5rem;'>🔮</div>
                            <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;'>AI Predictions</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.stop()
        
        # Calculate Score using centralized service
        lead_context = lead_options[selected_lead_name]
        result = services["lead_scorer"].calculate_with_reasoning(lead_context)
        
        # Display Results
        score = result["score"]
        classification = result["classification"]
        
        if classification == "hot":
            st.success(f"🔥 **Hot Lead** - Score: {score}/7 Questions Answered")
        elif classification == "warm":
            st.warning(f"⚠️ **Warm Lead** - Score: {score}/7 Questions Answered")
        else:
            st.info(f"❄️ **Cold Lead** - Score: {score}/7 Questions Answered")
            
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions Answered", f"{score}/7", "")
        with col2:
            st.metric("Engagement Class", classification.title(), "")
        with col3:
            st.metric("Lead Intent", "Calculated", "")
        
        st.markdown("#### AI Analysis Breakdown")
        st.info(f"**Qualifying Data Found:** {result['reasoning']}")
        
        # Quick Actions Toolbar
        st.markdown("---")
        st.markdown("#### ⚡ Quick Actions")
        
        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
        
        with col_act1:
            if st.button("📞 Call Now", use_container_width=True, type="primary"):
                st.toast(f"Calling {selected_lead_name}...", icon="📞")
                st.success("Call initiated via GHL")
        
        with col_act2:
            if st.button("💬 Send SMS", use_container_width=True):
                st.toast(f"Opening SMS composer for {selected_lead_name}", icon="💬")
                st.info("SMS template loaded in GHL")
        
        with col_act3:
            if st.button("📧 Send Email", use_container_width=True):
                st.toast(f"Email draft created for {selected_lead_name}", icon="📧")
                st.success("Email queued in GHL")
        
        with col_act4:
            if st.button("📅 Schedule Tour", use_container_width=True):
                st.toast("Opening calendar...", icon="📅")
                st.success("Calendar integration ready")
        
        # Last Contact Info
        st.caption("📊 Last Contact: 2 days ago via SMS | Next Follow-up: Tomorrow")
        
        st.markdown("---")
        st.markdown("#### Recommended Actions")
        for action in result["recommended_actions"]:
            st.markdown(f"- {action}")

        # PREMIUM FEATURE: AI Lead Insights Panel
        st.markdown("---")
        try:
            from components.enhanced_services import render_ai_lead_insights

            # Convert result to format expected by enhanced services
            lead_data_enhanced = {
                'lead_id': result.get('lead_id', 'demo_lead'),
                'name': selected_lead_name,
                'health_score': result.get('overall_score', 85),
                'engagement_level': 'high' if result.get('overall_score', 85) > 80 else 'medium',
                'last_contact': '2 days ago',
                'communication_preference': result.get('communication_preference', 'text'),
                'stage': 'qualification',
                'urgency_indicators': result.get('urgency_indicators', []),
                'extracted_preferences': result.get('extracted_preferences', {}),
                'conversation_history': []  # Would be real conversation data
            }

            render_ai_lead_insights(lead_data_enhanced)

        except ImportError:
            st.info("🚀 Premium AI Insights available in enterprise version")

    with tab2:
        # Churn Early Warning Dashboard
        try:
            from streamlit_demo.components.churn_early_warning_dashboard import ChurnEarlyWarningDashboard
            st.subheader("🚨 Churn Early Warning System")
            st.markdown("*Real-time monitoring and intervention orchestration for lead retention*")

            # Initialize and render the churn dashboard
            churn_dashboard = ChurnEarlyWarningDashboard(claude_assistant=claude)
            churn_dashboard.render_dashboard()

        except Exception as e:
            st.error("⚠️ Churn Dashboard Temporarily Unavailable")
            st.info("This enterprise feature requires full system integration. Demo mode available.")

            # Fallback demo content
            st.markdown("### 📊 Sample Churn Risk Analytics")

            # Demo metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Leads", "147", "+12")
            with col2:
                st.metric("Critical Risk", "3", "+1", delta_color="inverse")
            with col3:
                st.metric("High Risk", "8", "-2")
            with col4:
                st.metric("Success Rate", "78.5%", "+2.1%")

            st.info("💡 The full Churn Prediction Engine provides 26 behavioral features, multi-horizon risk scoring, and automated intervention orchestration.")

    with tab3:
        # Use the AI Property Matcher component
        try:
            from components.property_matcher_ai import render_property_matcher

            # Check if a lead is selected
            if selected_lead_name == "-- Select a Lead --":
                st.info("👈 Please select a lead from Tab 1 to see AI-powered property matches")
            else:
                lead_context = lead_options[selected_lead_name]
                render_property_matcher(lead_context)

                # PREMIUM FEATURE: Dynamic Timeline & Feature Gap Analysis
                st.markdown("---")
                try:
                    from components.elite_refinements import render_dynamic_timeline, render_feature_gap

                    # Dynamic timeline based on lead activity
                    actions_completed = lead_context.get('actions_completed', 2)
                    render_dynamic_timeline(
                        days_remaining=45,
                        actions_completed=actions_completed,
                        agent_name="Jorge"
                    )

                    # Feature gap analysis for property matching
                    st.markdown("---")
                    property_sample = {
                        'features': ['3-car garage', 'swimming pool', 'granite countertops', 'hardwood floors'],
                        'price': 650000,
                        'bedrooms': 4,
                        'bathrooms': 3
                    }
                    must_haves = lead_context.get('extracted_preferences', {}).get('must_haves',
                        ['swimming pool', '3-car garage', 'updated kitchen', 'good schools'])

                    if must_haves:
                        render_feature_gap(
                            property_data=property_sample,
                            lead_must_haves=must_haves,
                            match_score=87
                        )

                except ImportError:
                    st.info("🚀 Premium Timeline & Gap Analysis available in enterprise version")

        except ImportError as e:
            st.error(f"Property Matcher component not available: {e}")
            st.info("Property Matcher coming in Phase 2")

    with tab4:
        st.subheader("🌐 Self-Service Buyer Portal (Phase 3)")
        st.markdown("*Real-time behavioral telemetry from the proprietary portal environment*")
        
        # Get current preferences for the selected lead
        if selected_lead_name != "-- Select a Lead --":
            current_prefs = st.session_state.lead_options[selected_lead_name].get("extracted_preferences", {})
            lead_key = selected_lead_name.lower().replace(" ", "_")
        else:
            current_prefs = {}
            lead_key = "demo_lead"
        
        # Mock telemetry service if not available
        class MockTelemetry:
            def get_intent_score(self, key): return 85
            def get_lead_history(self, key): return []
            def record_interaction(self, key, action, meta): pass
        
        telemetry = services.get("telemetry", MockTelemetry())
        portal_url = f"/portal?id={lead_key}"
        st.info(f"Unique Architectural URL: `https://portal.lyrio.io/l/{lead_key}`")
        
        col_portal_left, col_portal_right = st.columns([1, 1])
        
        with col_portal_left:
            st.markdown(f"""
            <div style='background: white; padding: 1.5rem; border-radius: 15px; border: 1px solid #006AFF; text-align: center;'>
                <h3 style='color: #006AFF; margin-top: 0;'>🚀 Live Portal Status</h3>
                <p style='font-size: 0.9rem;'>The standalone architectural portal is active for <b>{selected_lead_name}</b>.</p>
                <div style='background: #F0F7FF; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                    <span style='font-size: 0.8rem; color: #64748B;'>PORTAL INTENT SCORE</span><br/>
                    <span style='font-size: 2rem; font-weight: 800; color: #006AFF;'>{telemetry.get_intent_score(lead_key)}/100</span>
                </div>
                <a href='{portal_url}' target='_blank' style='display: inline-block; background-color: #006AFF; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 10px; font-weight: 700; width: 100%;'>View as Lead</a>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### 📱 Portal Interface Preview")
            st.image("https://via.placeholder.com/400x600?text=Portal+Mobile+Mockup", width=300)

        with col_portal_right:
            st.markdown("#### 📡 Real-Time Telemetry Feed")
            
            history = telemetry.get_lead_history(lead_key)
            
            if not history:
                st.info("No portal interactions recorded for this lead yet.")
                # Add some demo history if empty
                if st.button("Simulate Portal Activity"):
                    telemetry.record_interaction(lead_key, "view", {"prop_id": "prop_001"})
                    telemetry.record_interaction(lead_key, "save", {"prop_id": "prop_002"})
                    st.rerun()
            else:
                for event in reversed(history[-10:]):
                    icon = "👀" if event["action"] == "view" else "💾" if event["action"] == "save" else "⚙️"
                    dt = datetime.datetime.fromisoformat(event["timestamp"])
                    time_str = dt.strftime("%H:%M:%S")
                    
                    st.markdown(f"""
                    <div style='background: #f8fafc; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #3b82f6;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span>{icon} <b>{event['action'].upper()}</b></span>
                            <span style='font-size: 0.7rem; color: #64748b;'>{time_str}</span>
                        </div>
                        <div style='font-size: 0.8rem; color: #475569;'>
                            Metadata: {json.dumps(event['metadata'])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("#### 🔄 Bi-Directional Sync Status")
            st.success("✅ Portal preferences automatically synced to GHL Custom Fields")
            st.success("✅ Intent Score Escalation trigger active")
    
    with tab5:
        # Smart Segmentation
        try:
            from components.segmentation_pulse import render_segmentation_pulse
            
            # Prepare lead data for segmentation
            leads_for_segmentation = []
            if "conversations" in mock_data:
                for conv in mock_data["conversations"]:
                    leads_for_segmentation.append({
                        "id": conv.get("contact_id"),
                        "name": conv.get("contact_name"),
                        "engagement_score": conv.get("message_count") * 10,
                        "lead_score": conv.get("lead_score"),
                        "budget": 500000 if conv.get("budget") == "unknown" else 1500000,
                        "last_activity_days_ago": 2,
                        "buyer_type": "luxury_buyer" if "lux" in conv.get("contact_id", "") else "standard",
                        "interested_property_type": "single_family"
                    })

            if leads_for_segmentation:
                import asyncio
                result = asyncio.run(services["segmentation"].segment_leads(leads_for_segmentation, method="behavioral"))
                
                # Render the enhanced pulse dashboard for the most important segment
                if result["segments"]:
                    main_segment = result["segments"][0]
                    render_segmentation_pulse(main_segment)
                    
                    st.markdown("---")
                    st.markdown("### 📋 All Segments Overview")
                    
                    # Use flexbox layout for all segments
                    st.markdown('<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 1rem;">', unsafe_allow_html=True)
                    
                    for seg in result["segments"]:
                        seg_name = seg["name"].replace("_", " ").title()
                        char = seg["characteristics"]
                        
                        segment_html = f"""
                        <div style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: transform 0.2s ease;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                                <h3 style="margin: 0; color: #1e293b; font-size: 1.25rem; font-weight: 700;">{seg_name}</h3>
                                <div style="background: #dbeafe; color: #1e40af; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">{seg['size']} Leads</div>
                            </div>
                            
                            <div style="display: flex; flex-direction: column; gap: 0.5rem; margin: 1rem 0; padding: 1rem; background: #f8fafc; border-radius: 8px;">
                                <div style="display: flex; align-items: center; gap: 0.5rem;">
                                    <span>📊</span>
                                    <span style="color: #475569; font-size: 0.875rem;">Engagement: <strong style="color: #1e293b;">{char['avg_engagement']}%</strong></span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 0.5rem;">
                                    <span>⭐</span>
                                    <span style="color: #475569; font-size: 0.875rem;">Score: <strong style="color: #1e293b;">{char['avg_lead_score']}</strong></span>
                                </div>
                            </div>
                            
                            <div style="font-size: 1.5rem; font-weight: 700; color: #2563eb; margin: 0.5rem 0;">${char['total_value']:,.0f}</div>
                            
                            <div style="margin: 1rem 0;">
                                <strong style="font-size: 0.875rem; color: #6b7280;">Recommended Actions:</strong>
                                <ul style="margin: 0.5rem 0; padding-left: 1.25rem; font-size: 0.875rem; color: #374151; line-height: 1.6;">
                                    {''.join(f'<li>{action}</li>' for action in seg['recommended_actions'][:2])}
                                </ul>
                            </div>
                        </div>
                        """
                        st.markdown(segment_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

        except ImportError:
            st.info("Smart Segmentation module coming soon")

    with tab6:
        st.subheader("🎨 Personalized Content Engine")
        render_personalization_tab(services, selected_lead_name)

    with tab7:
        st.subheader("🔮 Predictive Conversion Insights")
        render_predictions_tab(services, selected_lead_name)

    with tab8:
        st.subheader("💬 AI Conversation Simulator")
        render_simulator_tab(services, selected_lead_name)

def render_personalization_tab(services, selected_lead_name):
    st.markdown("*Generate tailored outreach materials based on lead behavior and preferences*")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        content_type = st.selectbox("Content Type:", ["SMS Outreach", "Email Market Update", "Video Script Outline", "Property Pitch"])
        tone = st.select_slider("Persona Matching:", options=["Professional", "Consultative", "Friendly", "Urgent"], value="Consultative")
        
        if st.button("✨ Generate Personalized Content"):
            with st.spinner("Claude is analyzing behavioral history..."):
                content = services["personalization"].generate_personalized_content(selected_lead_name, content_type, tone)
                st.session_state.generated_outreach = content
                st.success("Content tailored to lead's cognitive profile!")

    with col2:
        if "generated_outreach" in st.session_state:
            st.markdown("#### Preview")
            st.markdown(f"""
            <div style='background: #f1f5f9; padding: 1.5rem; border-radius: 10px; border: 1px solid #cbd5e1;'>
                {st.session_state.generated_outreach}
            </div>
            """, unsafe_allow_html=True)
            
            c_a, c_b = st.columns(2)
            with c_a:
                if st.button("🚀 Push to GHL"):
                    st.toast("Content synced to GHL draft!")
            with c_b:
                st.button("📋 Copy to Clipboard")

def render_predictions_tab(services, selected_lead_name):
    st.markdown("*Statistical modeling of future lead actions*")
    
    if selected_lead_name == "-- Select a Lead --":
        st.info("Select a lead to view predictions")
        return

    # Call predictive service
    prediction = services["predictive_scorer"].predict_next_action(selected_lead_name)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.metric("Conversion Probability", f"{prediction['probability']}%", delta=f"{prediction['delta']}%")
        
        # Risk factors
        st.markdown("#### Primary Drivers")
        for factor, impact in prediction['factors'].items():
            cols = st.columns([3, 1])
            cols[0].write(factor)
            color = "green" if impact > 0 else "red"
            cols[1].markdown(f"<span style='color: {color};'>+{impact}%</span>" if impact > 0 else f"<span style='color: {color};'>{impact}%</span>", unsafe_allow_html=True)

    with col2:
        # Time to convert prediction
        st.markdown("#### Estimated Timeline")
        st.write(f"**Target Close:** {prediction['target_date']}")
        st.progress(prediction['progress_pct'] / 100)
        st.caption(f"Lead is {prediction['progress_pct']}% through the standard {selected_market} buying cycle.")

def render_simulator_tab(services, selected_lead_name):
    st.markdown("*Test how the AI assistant would handle specific scenarios with this lead*")
    
    if "sim_messages" not in st.session_state:
        st.session_state.sim_messages = []

    for msg in st.session_state.sim_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask the lead a qualifying question..."):
        st.session_state.sim_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Simulating lead response..."):
                response = services["predictive_scorer"].simulate_response(selected_lead_name, prompt)
                st.markdown(response)
                st.session_state.sim_messages.append({"role": "assistant", "content": response})
