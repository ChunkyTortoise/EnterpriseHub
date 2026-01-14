import streamlit as st
import pandas as pd
import json
import datetime
import time
import asyncio
import numpy as np
import traceback
from pathlib import Path

# Import enhanced services
try:
    from services.enhanced_lead_intelligence import get_enhanced_lead_intelligence
    ENHANCED_INTELLIGENCE_AVAILABLE = True
except ImportError:
    ENHANCED_INTELLIGENCE_AVAILABLE = False

try:
    from services.lead_swarm_service import get_lead_swarm_service
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False

# Import new Lead Hub components
try:
    from components.personalization_engine import render_personalization_engine
    from components.conversion_predictor import render_conversion_predictor
    from components.conversation_simulator import render_conversation_simulator
    from components.buyer_portal_manager import render_buyer_portal_manager
    from components.elite_refinements import render_elite_segmentation_tab, render_dynamic_timeline, render_feature_gap
    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError:
    ENHANCED_COMPONENTS_AVAILABLE = False

# Import Claude Intelligence Services
try:
    from services.claude_conversation_intelligence import get_conversation_intelligence
    from services.claude_semantic_property_matcher import get_semantic_property_matcher
    from services.claude_lead_qualification import get_claude_qualification_engine
    CLAUDE_SERVICES_AVAILABLE = True
except ImportError:
    CLAUDE_SERVICES_AVAILABLE = False

def render_lead_intelligence_hub(services, mock_data, claude, market_key, selected_market, elite_mode=False):
    st.header("🧠 Lead Intelligence Hub")
    st.markdown("*Deep dive into individual leads with AI-powered insights*")
    
    if elite_mode:
        if CLAUDE_SERVICES_AVAILABLE and claude_services:
            st.success("🧠 **Claude AI Integration Active**: Real-time conversation intelligence, semantic property matching, and autonomous qualification enabled.")
        else:
            st.info("💎 **Elite Phase Features Active**: Adaptive Scoring and Semantic Memory enabled.")
            if not CLAUDE_SERVICES_AVAILABLE:
                st.warning("⚠️ **Claude Services Unavailable**: Check Claude integration dependencies.")
    
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

    # Initialize Claude Services for Elite Mode
    claude_services = {}
    if elite_mode and CLAUDE_SERVICES_AVAILABLE:
        try:
            claude_services = {
                'conversation': get_conversation_intelligence(),
                'properties': get_semantic_property_matcher(),
                'qualification': get_claude_qualification_engine()
            }
        except Exception as e:
            st.warning(f"Claude services initialization failed: {str(e)}")
            claude_services = {}

    # Initialize Enhanced Intelligence
    enhanced_intelligence = None
    analysis_result = None
    
    if ENHANCED_INTELLIGENCE_AVAILABLE and selected_lead_name != "-- Select a Lead --":
        enhanced_intelligence = get_enhanced_lead_intelligence()
        lead_context = lead_options[selected_lead_name]
        
        with st.spinner(f"🧠 Claude is performing multi-dimensional analysis for {selected_lead_name}..."):
            # Use asyncio to run the async analysis method
            try:
                # In Streamlit, we need to handle the event loop carefully
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                analysis_result = loop.run_until_complete(
                    enhanced_intelligence.get_comprehensive_lead_analysis(
                        selected_lead_name, lead_context
                    )
                )
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
    
    # Calculate Score globally for the header (and Tab 1)
    if selected_lead_name != "-- Select a Lead --":
        lead_context = lead_options[selected_lead_name]
        
        if analysis_result:
            # Render the enhanced header from the service
            enhanced_intelligence.render_enhanced_lead_profile_header(selected_lead_name, analysis_result)
        else:
            # Fallback to legacy header
            result = services["lead_scorer"].calculate_with_reasoning(lead_context)
            score = result["score"]
            classification = result["classification"]
            
            # Standardized Lead Profile Header
            score_color = "#ef4444" if score >= 5 else "#f59e0b" if score >= 3 else "#3b82f6"
            score_label = "🔥 HOT LEAD" if score >= 5 else "🔸 WARM LEAD" if score >= 3 else "❄️ COLD LEAD"
            
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {score_color}10 0%, {score_color}05 100%); 
                        padding: 1.25rem; border-radius: 12px; border-left: 5px solid {score_color}; margin-bottom: 1.5rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <h2 style='margin: 0; color: #1e293b; font-size: 1.5rem;'>{selected_lead_name}</h2>
                        <div style='display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem;'>
                            <span style='background: white; color: {score_color}; padding: 0.2rem 0.6rem; 
                                         border-radius: 999px; font-size: 0.75rem; font-weight: 700; border: 1px solid {score_color}30;'>
                                {score_label}
                            </span>
                            <span style='color: #64748b; font-size: 0.85rem;'>• {lead_context.get('occupation', 'Unknown Occupation')}</span>
                            <span style='color: #64748b; font-size: 0.85rem;'>• {lead_context.get('location', 'Unknown Location')}</span>
                        </div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 1.8rem; font-weight: 800; color: {score_color}; line-height: 1;'>{int((score/7)*100)}%</div>
                        <div style='font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>Match Score</div>
                    </div>
                </div>
                {f"<div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid {score_color}20; font-size: 0.9rem; color: #1e293b;'><b>Claude's Strategy:</b> {analysis_result.strategic_summary if analysis_result else 'Run analysis to generate strategy.'}</div>" if analysis_result else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        analysis_result = None

    st.markdown("---")
    
    tab1, tab_swarm, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "🎯 Lead Scoring",
        "🐝 Agent Swarm",
        "🕵️ Deep Dossier",
        "🚨 Churn Early Warning",
        "🏠 Property Matcher (Phase 2)",
        "🔥 Smart Swipe",
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
            
            # Claude's Behavioral Deep Dive - Enhanced with Claude Services
            if claude_services.get('qualification') and elite_mode:
                # Use Claude qualification for real-time analysis
                with st.spinner("🧠 Claude is analyzing lead qualification..."):
                    try:
                        lead_context = lead_options[selected_lead_name]
                        qualification_engine = claude_services['qualification']

                        # Safe Claude qualification call with fallback
                        try:
                            qualification_result = qualification_engine.qualify_lead_comprehensive(lead_context)
                            if qualification_result:
                                qualification_engine.render_qualification_dashboard(lead_context, [])
                            else:
                                raise Exception("No qualification result returned")
                        except Exception as e:
                            st.warning(f"Claude qualification failed: {str(e)}")
                            # Fall back to static insights
                            st.info("🧠 **Fallback Mode**: Using cached behavioral insights")
                    except Exception as e:
                        st.error(f"Claude analysis error: {str(e)}")

            elif analysis_result:
                enhanced_intelligence.render_enhanced_behavioral_insight(selected_lead_name, analysis_result)
            else:
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
                        insight_text = "Highly motivated school teacher. She's focused on Avery Ranch school boundary shifts. Sentiment: 92% Positive. Focus on: Alta Loma vs. North RC safety metrics."
                    elif selected_lead_name == "Mike Chen":
                        insight_text = "Downsizing executive. He's spending significant time on the Victoria Gardens condo floor plans. Sentiment: Neutral/Analytical. Focus on: HOA stability and walkability scores."
                    elif selected_lead_name == "Emily Davis":
                        insight_text = "Growth-oriented investor. She's tracking Alta Loma price-per-acre trends. Sentiment: Professional. Focus on: Multi-generational living potential and lot size ROI."
                    else:
                        insight_text = "Initial discovery phase. Engagement is low. Sentiment: Undetermined. Focus on: Qualifying location preferences."
                    st.info(insight_text)

            # Add Conversation Intelligence Panel if available
            if claude_services.get('conversation') and elite_mode and selected_lead_name != "-- Select a Lead --":
                st.markdown("---")
                st.markdown("#### 💬 Claude Conversation Intelligence")
                try:
                    conversation_engine = claude_services['conversation']
                    lead_context = lead_options[selected_lead_name]
                    # Use empty conversation history for demo
                    conversation_engine.render_intelligence_panel([], lead_context)
                except Exception as e:
                    st.warning(f"Conversation intelligence unavailable: {str(e)}")

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
        
        # Display Results - Enhanced with Claude Integration
        if claude_services.get('qualification') and elite_mode and selected_lead_name != "-- Select a Lead --":
            # Claude-powered metrics
            st.markdown("#### 🧠 Claude Intelligence Dashboard")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Claude Score", "87%", "+12%")
            with col2:
                st.metric("Intent Level", "High", "↑ Increasing")
            with col3:
                st.metric("Qualification", "Hot Lead", "Autonomous")
            with col4:
                st.metric("Match Rate", "92%", "+15%")

            st.info("🎯 **Claude Insight**: This lead shows immediate buying signals with high lifestyle compatibility. Recommend priority agent assignment within 24 hours.")

        elif analysis_result:
            # Multi-dimensional stats from Claude analysis
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Final Score", f"{analysis_result.final_score:.0f}%", "")
            with col2:
                st.metric("ML Score", f"{analysis_result.ml_conversion_score:.0f}%", "")
            with col3:
                st.metric("Jorge Score", f"{analysis_result.jorge_score}/7", "")
            with col4:
                st.metric("Churn Risk", f"{analysis_result.churn_risk_score:.0f}%", "", delta_color="inverse")

            st.markdown("#### Claude's Strategic Summary")
            st.info(analysis_result.strategic_summary)
        else:
            # Fallback to legacy result (calculated earlier if analysis failed)
            result = services["lead_scorer"].calculate_with_reasoning(lead_context)
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
        
        if analysis_result:
            # Use the enhanced quick actions from service
            enhanced_intelligence.render_enhanced_quick_actions(selected_lead_name, analysis_result)
        else:
            # Fallback quick actions
            st.markdown("#### ⚡ Quick Actions")
            
            col_act1, col_act2, col_act3, col_act4 = st.columns(4)
            
            with col_act1:
                if st.button("📞 Call Now", use_container_width=True, type="primary"):
                    with st.spinner("Connecting via Bridge..."):
                        time.sleep(1.2)
                        st.toast(f"Calling {selected_lead_name}...", icon="📞")
                        st.success("Call initiated via GHL")
            
            with col_act2:
                if st.button("💬 Send SMS", use_container_width=True):
                    with st.spinner("Loading templates..."):
                        time.sleep(0.5)
                        st.toast(f"Opening SMS composer for {selected_lead_name}", icon="💬")
                        st.info("SMS template loaded in GHL")
            
            with col_act3:
                if st.button("📧 Send Email", use_container_width=True):
                    with st.spinner("Generating draft..."):
                        time.sleep(0.8)
                        st.toast(f"Email draft created for {selected_lead_name}", icon="📧")
                        st.success("Email queued in GHL")
            
            with col_act4:
                if st.button("📅 Schedule Tour", use_container_width=True):
                    with st.spinner("Syncing calendar..."):
                        time.sleep(1.0)
                        st.toast("Opening calendar...", icon="📅")
                        st.success("Calendar integration ready")
        
        # Last Contact Info
        if analysis_result:
            st.caption(f"📊 Claude Confidence: {analysis_result.confidence_score:.0%} | Analysis Time: {analysis_result.analysis_time_ms}ms")
            
            st.markdown("---")
            st.markdown("#### Claude's Recommended Actions")
            for action_item in analysis_result.recommended_actions[:3]:
                action = action_item.get("action", "Follow up")
                priority = action_item.get("priority", "medium")
                st.markdown(f"- **[{priority.upper()}]** {action}")
        else:
            st.caption("📊 Last Contact: 2 days ago via SMS | Next Follow-up: Tomorrow")
            st.markdown("---")
            st.markdown("#### Recommended Actions")
            for action in result["recommended_actions"]:
                st.markdown(f"- {action}")

        st.markdown("---")
        # NEW: Temporal Activity Heatmap Refinement (Screenshot 23 Fix)
        try:
            from components.elite_refinements import render_actionable_heatmap
            
            # Generate mock temporal data for the heatmap
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_data = []
            for d in days:
                for h in range(24):
                    # Higher activity during business hours and early evening
                    base = 10 if 9 <= h <= 18 else 2
                    activity = base + np.random.randint(0, 15)
                    heatmap_data.append({'day': d, 'hour': h, 'activity_count': activity})
            
            df_activity = pd.DataFrame(heatmap_data)
            render_actionable_heatmap(df_activity)
        except ImportError:
            st.info("🚀 Advanced Temporal Heatmap available in enterprise version")

        # PREMIUM FEATURE: AI Lead Insights Panel
        st.markdown("---")
        try:
            from components.enhanced_services import render_ai_lead_insights

            # Try to get predictive score if available
            health_score = lead_context.get('overall_score', 85)
            try:
                if "predictive_scorer" in services:
                    # Map lead_context to expected format
                    scoring_data = {
                        "contact_id": lead_context.get('lead_id'),
                        "extracted_preferences": lead_context.get('extracted_preferences', {}),
                        "page_views": 15,  # Mocked
                        "email_opens": 4   # Mocked
                    }
                    pred_result = services["predictive_scorer"].predict_conversion(scoring_data)
                    health_score = pred_result.get("conversion_probability", health_score)
            except Exception:
                pass

            # Convert context to format expected by enhanced services
            lead_data_enhanced = {
                'lead_id': lead_context.get('lead_id', 'demo_lead'),
                'name': selected_lead_name,
                'health_score': health_score,
                'engagement_level': 'high' if health_score > 80 else 'medium' if health_score > 40 else 'low',
                'last_contact': '2 days ago',
                'communication_preference': lead_context.get('communication_preference', 'text'),
                'stage': 'qualification',
                'urgency_indicators': lead_context.get('urgency_indicators', []),
                'extracted_preferences': lead_context.get('extracted_preferences', {}),
                'conversation_history': []  # Would be real conversation data
            }

            render_ai_lead_insights(lead_data_enhanced)

        except ImportError:
            st.info("🚀 Premium AI Insights available in enterprise version")

    with tab_swarm:
        st.subheader("🐝 Autonomous Agent Swarm")
        st.markdown("*Multi-agent analysis system for comprehensive lead profiling*")
        
        if not SWARM_AVAILABLE:
            st.error("⚠️ Swarm Service not available. Check dependencies.")
        elif selected_lead_name == "-- Select a Lead --":
            st.info("👈 Select a lead to deploy the agent swarm.")
        else:
            col_swarm_ctrl, col_swarm_status = st.columns([1, 2])
            with col_swarm_ctrl:
                if st.button("🚀 Deploy Swarm", type="primary", use_container_width=True):
                    with st.status("🐝 Swarm Active", expanded=True) as status:
                        st.write("Initializing agents...")
                        swarm_service = get_lead_swarm_service()
                        lead_context = lead_options[selected_lead_name]
                        
                        st.write("Running parallel analysis...")
                        try:
                            # Handle event loop
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                
                            swarm_results = loop.run_until_complete(swarm_service.run_swarm(lead_context))
                            st.session_state[f"swarm_results_{selected_lead_name}"] = swarm_results
                            status.update(label="✅ Swarm Mission Complete", state="complete", expanded=False)
                        except Exception as e:
                            st.error(f"Swarm failure: {str(e)}")
                            status.update(label="❌ Swarm Failed", state="error")

            # Display Results
            results_key = f"swarm_results_{selected_lead_name}"
            if results_key in st.session_state:
                results = st.session_state[results_key]
                
                # 2x2 Grid Layout for Agents
                c1, c2 = st.columns(2)
                
                # Financial Agent
                with c1:
                    with st.container(border=True):
                        st.markdown("### 💰 Financial Analyst")
                        fin = results.get("Financial Analyst", {})
                        if "error" in fin:
                            st.error(fin["error"])
                        else:
                            st.markdown(f"**Status:** {fin.get('qualification_status', 'Unknown')}")
                            st.markdown(f"**Budget:** {fin.get('estimated_budget_range', 'Unknown')}")
                            st.caption("Signals:")
                            for sig in fin.get('financial_signals', []):
                                st.markdown(f"- {sig}")
                
                # Timeline Agent
                with c2:
                    with st.container(border=True):
                        st.markdown("### ⏳ Timeline Assessor")
                        time_agent = results.get("Timeline Assessor", {})
                        if "error" in time_agent:
                            st.error(time_agent["error"])
                        else:
                            st.markdown(f"**Urgency:** {time_agent.get('urgency_level', 'Unknown')}")
                            st.markdown(f"**Target:** {time_agent.get('target_move_date', 'Unknown')}")
                            st.caption("Drivers:")
                            for driver in time_agent.get('drivers', []):
                                st.markdown(f"- {driver}")

                c3, c4 = st.columns(2)
                
                # Psych Agent
                with c3:
                    with st.container(border=True):
                        st.markdown("### 🧠 Behavioral Psychologist")
                        psych = results.get("Behavioral Psychologist", {})
                        if "error" in psych:
                            st.error(psych["error"])
                        else:
                            st.markdown(f"**Type:** {psych.get('personality_type', 'Unknown')}")
                            st.markdown(f"**Style:** {psych.get('communication_style', 'Unknown')}")
                            st.caption("Motivators:")
                            for mot in psych.get('motivators', []):
                                st.markdown(f"- {mot}")

                # Risk Agent
                with c4:
                    with st.container(border=True):
                        st.markdown("### 🛡️ Risk Analyst")
                        risk = results.get("Risk Analyst", {})
                        if "error" in risk:
                            st.error(risk["error"])
                        else:
                            risk_level = risk.get('risk_level', 'Unknown')
                            color = "red" if "High" in risk_level else "orange" if "Medium" in risk_level else "green"
                            st.markdown(f"**Risk:** :{color}[{risk_level}]")
                            st.markdown(f"**Competitors:** {'Yes' if risk.get('competitor_risk') else 'No'}")
                            st.caption("Primary Objections:")
                            for obj in risk.get('primary_objections', []):
                                st.markdown(f"- {obj}")

    with tab2:
        if analysis_result:
            enhanced_intelligence.render_deep_intelligence_tab(selected_lead_name, lead_context, analysis_result)
        else:
            st.info("Select a lead and run analysis to unlock Deep Dossier research.")

    with tab3:
        # Churn Early Warning Dashboard
        try:
            from components.churn_early_warning_dashboard import ChurnEarlyWarningDashboard
            st.subheader("🚨 Churn Early Warning System")
            st.markdown("*Real-time monitoring and intervention orchestration for lead retention*")

            # Initialize and render the churn dashboard
            churn_dashboard = ChurnEarlyWarningDashboard(claude_assistant=claude)
            churn_dashboard.render_dashboard()

        except Exception as e:
            st.error(f"⚠️ Churn Dashboard Error: {str(e)}")
            st.code(str(type(e).__name__) + ": " + str(e))
            st.code(traceback.format_exc())

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

    with tab4:
        # Enhanced Property Matcher with Claude Semantic Matching
        st.subheader("🏠 Claude Semantic Property Matching")

        if selected_lead_name == "-- Select a Lead --":
            st.info("👈 Please select a lead from Tab 1 to see AI-powered property matches")
        elif claude_services.get('properties') and elite_mode:
            # Use Claude Semantic Property Matcher
            st.markdown("*Advanced lifestyle-based property matching using Claude AI*")

            try:
                lead_context = lead_options[selected_lead_name]
                semantic_matcher = claude_services['properties']

                with st.spinner("🧠 Claude is analyzing lifestyle compatibility..."):
                    # Render the enhanced semantic matching interface
                    semantic_matcher.render_semantic_matching_interface(lead_context)
            except Exception as e:
                st.error(f"Claude semantic matching failed: {str(e)}")
                # Fallback to standard property matcher
                try:
                    from components.property_matcher_ai import render_property_matcher
                    lead_context = lead_options[selected_lead_name]
                    render_property_matcher(lead_context, elite_mode=elite_mode, analysis_result=analysis_result)
                except ImportError:
                    st.warning("Fallback property matcher not available")
        else:
            # Standard Property Matcher fallback
            try:
                from components.property_matcher_ai import render_property_matcher
                if selected_lead_name != "-- Select a Lead --":
                    lead_context = lead_options[selected_lead_name]
                    render_property_matcher(lead_context, elite_mode=elite_mode, analysis_result=analysis_result)
            except ImportError:
                st.info("Property Matcher component loading...")

        # PREMIUM FEATURE: Dynamic Timeline & Feature Gap Analysis
        st.markdown("---")
        try:
            from components.elite_refinements import render_dynamic_timeline, render_feature_gap

            # Dynamic timeline based on lead activity
            if selected_lead_name != "-- Select a Lead --":
                lead_context = lead_options[selected_lead_name]
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

    with tab5:
        try:
            from components.property_swipe import render_property_swipe
            render_property_swipe(selected_lead_name)
        except ImportError:
            st.info("🔥 Smart Swipe component coming soon")

    with tab6:
        if ENHANCED_COMPONENTS_AVAILABLE:
            render_buyer_portal_manager(selected_lead_name)
        else:
            st.subheader("🌐 Buyer Portal (Phase 3)")
            st.info("Enhanced Buyer Portal Manager loading...")
    
    with tab7:
        # Smart Segmentation
        if elite_mode:
            render_elite_segmentation_tab()
        else:
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
                    # Handle Streamlit event loop
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                    result = loop.run_until_complete(services["segmentation"].segment_leads(leads_for_segmentation, method="behavioral"))
                    
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
            except (ImportError, Exception) as e:
                st.info(f"Smart Segmentation module unavailable: {e}")

    with tab8:
        if ENHANCED_COMPONENTS_AVAILABLE:
            render_personalization_engine(services, selected_lead_name, analysis_result=analysis_result)
        else:
            st.subheader("🎨 Personalized Content Engine")
            render_personalization_tab(services, selected_lead_name)

    with tab9:
        if ENHANCED_COMPONENTS_AVAILABLE:
            render_conversion_predictor(services, selected_lead_name, analysis_result=analysis_result)
        else:
            st.subheader("🔮 Predictive Conversion Insights")
            render_predictions_tab(services, selected_lead_name)
            
            # Add Contact Timing Badges
            try:
                from components.contact_timing import render_contact_timing_badges
                best_times = [
                    {"day": "Tomorrow", "time": "2:00 PM - 4:00 PM", "urgency": "high", "probability": 87},
                    {"day": "Friday", "time": "10:00 AM - 12:00 PM", "urgency": "medium", "probability": 68}
                ]
                render_contact_timing_badges(best_times)
            except ImportError:
                pass

    with tab10:
        # Enhanced Conversation Simulator with Claude Intelligence
        st.subheader("💬 Claude Conversation Intelligence")

        if selected_lead_name == "-- Select a Lead --":
            st.info("👈 Please select a lead to start intelligent conversation simulation")
        elif claude_services.get('conversation') and elite_mode:
            # Use Claude-enhanced conversation simulator
            st.markdown("*Real-time conversation analysis with AI response suggestions*")

            try:
                conversation_engine = claude_services['conversation']
                lead_context = lead_options[selected_lead_name]

                # Render enhanced conversation simulator with Claude intelligence
                render_claude_enhanced_simulator(claude_services, lead_context, selected_lead_name)
            except Exception as e:
                st.error(f"Claude conversation simulation failed: {str(e)}")
                # Fallback to standard simulator
                if ENHANCED_COMPONENTS_AVAILABLE:
                    render_conversation_simulator(services, selected_lead_name)
                else:
                    render_simulator_tab(services, selected_lead_name)
        else:
            # Standard conversation simulator
            if ENHANCED_COMPONENTS_AVAILABLE:
                render_conversation_simulator(services, selected_lead_name)
            else:
                st.subheader("💬 AI Conversation Simulator")
                render_simulator_tab(services, selected_lead_name)

# Claude-Enhanced Conversation Simulator
def render_claude_enhanced_simulator(claude_services, lead_context, selected_lead_name):
    """Enhanced conversation simulator with Claude intelligence."""
    st.markdown(f"**Simulating conversation with {selected_lead_name}**")

    # Conversation Intelligence Sidebar
    with st.sidebar:
        st.markdown("### 🧠 Claude Real-Time Insights")

        if 'conversation_messages' not in st.session_state:
            st.session_state.conversation_messages = []

        # Real-time metrics
        col_int1, col_int2 = st.columns(2)
        with col_int1:
            st.metric("Intent Level", "65%")
            st.metric("Urgency Score", "42%")
        with col_int2:
            st.metric("Engagement", "High")
            st.metric("Readiness", "Medium")

    # Main conversation interface
    col_chat, col_intelligence = st.columns([2, 1])

    with col_chat:
        st.markdown("#### 💬 Conversation Simulation")

        # Chat interface
        if 'conversation_messages' not in st.session_state:
            st.session_state.conversation_messages = [
                {"role": "assistant", "content": f"Hi {selected_lead_name.split(' ')[0]}! I saw you've been looking at properties in the area. What kind of home are you hoping to find?"}
            ]

        # Display conversation
        for message in st.session_state.conversation_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # User input
        if user_input := st.chat_input("Type your response..."):
            st.session_state.conversation_messages.append({"role": "user", "content": user_input})

            # Generate Claude response
            with st.spinner("🧠 Claude is analyzing response..."):
                try:
                    conversation_engine = claude_services['conversation']
                    # Simple demo response
                    response = f"Thanks for sharing that! Based on your interests in {lead_context.get('location', 'the area')}, I have some great options to show you."
                    st.session_state.conversation_messages.append({"role": "assistant", "content": response})
                    st.rerun()
                except Exception as e:
                    st.error(f"Claude response generation failed: {str(e)}")

    with col_intelligence:
        st.markdown("#### 🎯 Claude Guidance")

        # Real-time analysis panel
        if len(st.session_state.conversation_messages) > 1:
            with st.container(border=True):
                st.markdown("**Intent Analysis**")
                st.progress(0.65, text="Buying Intent: 65%")
                st.progress(0.42, text="Urgency: 42%")
                st.progress(0.78, text="Financial Readiness: 78%")

        # Response suggestions
        st.markdown("#### 💡 Suggested Responses")

        suggestions = [
            "Ask about their timeline for moving",
            "Inquire about their budget range",
            "Offer to schedule a property viewing",
            "Share relevant market insights"
        ]

        for i, suggestion in enumerate(suggestions, 1):
            if st.button(f"Option {i}", key=f"suggestion_{i}", use_container_width=True):
                st.session_state.conversation_messages.append({"role": "assistant", "content": suggestion})
                st.rerun()

# Fallback implementations for backwards compatibility
def render_personalization_tab(services, selected_lead_name):
    """Fallback implementation - basic personalization tab"""
    st.markdown("*Generate tailored outreach materials based on lead behavior and preferences*")
    st.info("Enhanced Personalization Engine loading...")

def render_predictions_tab(services, selected_lead_name):
    """Fallback implementation - basic predictions tab"""
    st.markdown("*Statistical modeling of future lead actions*")
    st.info("Enhanced Conversion Predictor loading...")

def render_simulator_tab(services, selected_lead_name):
    """Fallback implementation - basic simulator tab"""
    st.markdown("*Test how the AI assistant would handle specific scenarios with this lead*")
    st.info("Enhanced Conversation Simulator loading...")
