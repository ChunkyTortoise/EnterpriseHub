import streamlit as st
import pandas as pd
import json
import datetime
from datetime import datetime, timedelta
import time
import asyncio
import numpy as np
import plotly.express as px
import traceback
from pathlib import Path
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
analytics_service = AnalyticsService()
try:
    from ghl_real_estate_ai.services.enhanced_lead_intelligence import get_enhanced_lead_intelligence
    ENHANCED_INTELLIGENCE_AVAILABLE = True
except ImportError:
    ENHANCED_INTELLIGENCE_AVAILABLE = False
try:
    from ghl_real_estate_ai.services.lead_swarm_service import get_lead_swarm_service
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False
try:
    from ghl_real_estate_ai.services.ghl_sync_service import get_ghl_sync_service
    GHL_SYNC_AVAILABLE = True
except ImportError:
    GHL_SYNC_AVAILABLE = False
try:
    from ghl_real_estate_ai.streamlit_demo.components.personalization_engine import render_personalization_engine
    from ghl_real_estate_ai.streamlit_demo.components.conversion_predictor import render_conversion_predictor
    from ghl_real_estate_ai.streamlit_demo.components.conversation_simulator import render_conversation_simulator
    from ghl_real_estate_ai.streamlit_demo.components.buyer_portal_manager import render_buyer_portal_manager
    from ghl_real_estate_ai.streamlit_demo.components.elite_refinements import render_elite_segmentation_tab, render_dynamic_timeline, render_feature_gap
    from ghl_real_estate_ai.streamlit_demo.components.journey_orchestrator_ui import render_journey_orchestrator
    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError:
    ENHANCED_COMPONENTS_AVAILABLE = False
try:
    from ghl_real_estate_ai.services.claude_conversation_intelligence import get_conversation_intelligence
    from ghl_real_estate_ai.services.claude_semantic_property_matcher import get_semantic_property_matcher
    from ghl_real_estate_ai.services.claude_lead_qualification import get_claude_qualification_engine
    CLAUDE_SERVICES_AVAILABLE = True
except ImportError:
    CLAUDE_SERVICES_AVAILABLE = False

def render_lead_intelligence_hub(services, mock_data, claude, market_key, selected_market, elite_mode=False):
    import inspect
    import os
    st.sidebar.info(f'HUB FILE: {__file__}')
    _render_lead_roi_sidebar()
    try:
        from ghl_real_estate_ai.services.enhanced_lead_intelligence import EnhancedLeadIntelligence
        st.sidebar.info(f'SRV FILE: {inspect.getfile(EnhancedLeadIntelligence)}')
    except:
        st.sidebar.warning('SRV NOT FOUND')
    st.header('🧠 Lead Intelligence Hub')
    st.markdown('*Deep dive into individual leads with AI-powered insights*')
    claude_services = {}
    if elite_mode and CLAUDE_SERVICES_AVAILABLE:
        try:
            from ghl_real_estate_ai.services.claude_conversation_intelligence import get_conversation_intelligence
            from ghl_real_estate_ai.services.claude_semantic_property_matcher import get_semantic_property_matcher
            from ghl_real_estate_ai.services.claude_lead_qualification import get_claude_qualification_engine
            claude_services = {'conversation': get_conversation_intelligence(), 'properties': get_semantic_property_matcher(), 'qualification': get_claude_qualification_engine()}
        except Exception as e:
            st.warning(f'Claude services initialization failed: {str(e)}')
            claude_services = {}
    if elite_mode:
        if CLAUDE_SERVICES_AVAILABLE and claude_services:
            st.success('🧠 **Claude AI Integration Active**: Real-time conversation intelligence, semantic property matching, and autonomous qualification enabled.')
        else:
            st.info('💎 **Elite Phase Features Active**: Adaptive Scoring and Semantic Memory enabled.')
            if not CLAUDE_SERVICES_AVAILABLE:
                st.warning('⚠️ **Claude Services Unavailable**: Check Claude integration dependencies.')
    with st.container(border=True):
        st.markdown('### 📊 Global Lead Intelligence Telemetry')
        col_glob1, col_glob2, col_glob3, col_glob4 = st.columns(4)
        with col_glob1:
            st.metric('Avg Conversion Prob', '68.4%', '+2.1%')
        with col_glob2:
            st.metric('Lead Velocity', '12.5 hrs', '-1.4 hrs')
        with col_glob3:
            st.metric('Market Sentiment', 'Positive', '↑ Rising')
        with col_glob4:
            st.metric('DNA Coverage', '16 Dimensions', 'Maximized')
        st.markdown('#### 🧬 Market-wide Lifestyle DNA (Top Priorities)')
        dna_cols = st.columns(6)
        top_dna = {'Convenience': 0.85, 'Security': 0.78, 'Commute': 0.82, 'Investment': 0.65, 'Status': 0.45, 'Tech': 0.72}
        for idx, (dim, score) in enumerate(top_dna.items()):
            with dna_cols[idx]:
                st.progress(score, text=dim)
    if 'lead_options' not in st.session_state:
        st.error('Lead options not initialized. Please refresh the page.')
        return
    lead_options = st.session_state.lead_options
    st.markdown('### 🎯 Select & Filter Leads')
    with st.expander('🔍 Advanced Lead Filters', expanded=True):
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
        with col_filter1:
            conversation_health_filter = st.selectbox('Conversation Health', ['All', 'Excellent', 'Good', 'Concerning', 'Poor'], key='health_filter')
        with col_filter2:
            emotional_state_filter = st.selectbox('Emotional State', ['All', 'Excited', 'Analytical', 'Cautious', 'Frustrated', 'Ready'], key='emotion_filter')
        with col_filter3:
            closing_readiness_filter = st.selectbox('Closing Readiness', ['All', 'High', 'Medium', 'Low'], key='closing_filter')
        with col_filter4:
            trust_level_filter = st.selectbox('Trust Level', ['All', 'Strong', 'Established', 'Building', 'Weak'], key='trust_filter')
    enhanced_lead_data = {}
    for lead_name, lead_context in st.session_state.lead_options.items():
        if lead_name == '-- Select a Lead --' or lead_context is None:
            continue
        enhanced_lead_data[lead_name] = {**lead_context, 'conversation_health': get_conversation_health_score(lead_name), 'emotional_state': get_emotional_state(lead_name), 'closing_readiness': get_closing_readiness(lead_name), 'trust_level': get_trust_level(lead_name), 'last_activity': get_last_activity(lead_name)}
    filtered_leads = apply_lead_filters(enhanced_lead_data, conversation_health_filter, emotional_state_filter, closing_readiness_filter, trust_level_filter)
    if len(filtered_leads) < len(enhanced_lead_data):
        st.info(f'🔍 Showing {len(filtered_leads)} of {len(enhanced_lead_data)} leads after filtering')
    lead_names = list(filtered_leads.keys())
    lead_display_names = []
    lead_names.insert(0, '-- Select a Lead --')
    lead_display_names.append('-- Select a Lead --')
    for lead_name in lead_names[1:]:
        lead_data = filtered_leads[lead_name]
        health = lead_data['conversation_health']
        emotion = lead_data['emotional_state']
        health_status = {'Excellent': 'Optimal', 'Good': 'Stable', 'Concerning': 'At Risk', 'Poor': 'Critical'}.get(health, 'Unknown')
        emotion_status = {'Excited': 'High Intent', 'Analytical': 'Deep Research', 'Cautious': 'Refining', 'Frustrated': 'Action Required', 'Ready': 'Closing'}.get(emotion, 'Discovery')
        display_name = f'{lead_name} | {health_status} | {emotion_status}'
        lead_display_names.append(display_name)
    try:
        current_lead = st.session_state.get('selected_lead_name', lead_names[0])
        if current_lead in lead_names:
            default_idx = lead_names.index(current_lead)
            default_display_idx = default_idx
        else:
            default_idx = 0
            default_display_idx = 0
    except (ValueError, IndexError):
        default_idx = 0
        default_display_idx = 0
    selected_display_name = st.selectbox('Choose a lead to analyze:', lead_display_names, index=default_display_idx, key='hub_lead_selector_enhanced')
    selected_lead_name = lead_names[lead_display_names.index(selected_display_name)]
    st.session_state.selected_lead_name = selected_lead_name
    st.session_state.filtered_leads = filtered_leads
    enhanced_intelligence = None
    analysis_result = None
    if ENHANCED_INTELLIGENCE_AVAILABLE and selected_lead_name != '-- Select a Lead --':
        enhanced_intelligence = get_enhanced_lead_intelligence()
        lead_context = lead_options[selected_lead_name]
        analysis_cache_key = f'analysis_result_{selected_lead_name}'
        if analysis_cache_key in st.session_state:
            analysis_result = st.session_state[analysis_cache_key]
        else:
            with st.spinner(f'🧠 Claude is performing multi-dimensional analysis for {selected_lead_name}...'):
                try:
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    analysis_result = loop.run_until_complete(enhanced_intelligence.get_comprehensive_lead_analysis(selected_lead_name, lead_context))
                    st.session_state[analysis_cache_key] = analysis_result
                except Exception as e:
                    st.error(f'Analysis failed: {str(e)}')
    if selected_lead_name != '-- Select a Lead --':
        lead_context = lead_options[selected_lead_name]
        if analysis_result:
            enhanced_intelligence.render_enhanced_lead_profile_header(selected_lead_name, analysis_result)
        else:
            result = services['lead_scorer'].calculate_with_reasoning(lead_context)
            score = result['score']
            classification = result['classification']
            score_color = '#ef4444' if score >= 5 else '#f59e0b' if score >= 3 else '#6366f1'
            score_label = 'PRIORITY: HOT' if score >= 5 else 'PRIORITY: WARM' if score >= 3 else 'PRIORITY: STABLE'
            st.markdown(f"""\n            <div style='background: rgba(30, 41, 59, 0.6); \n                        padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); \n                        border-left: 6px solid {score_color}; margin-bottom: 2rem; backdrop-filter: blur(10px);'>\n                <div style='display: flex; justify-content: space-between; align-items: center;'>\n                    <div>\n                        <h2 style='margin: 0; color: #FFFFFF !important; font-size: 1.75rem; font-family: "Space Grotesk", sans-serif; letter-spacing: -0.02em;'>{selected_lead_name}</h2>\n                        <div style='display: flex; align-items: center; gap: 0.75rem; margin-top: 0.5rem;'>\n                            <span style='background: {score_color}20; color: {score_color}; padding: 0.25rem 0.75rem; \n                                         border-radius: 999px; font-size: 0.75rem; font-weight: 800; border: 1px solid {score_color}40; text-transform: uppercase;'>\n                                {score_label}\n                            </span>\n                            <span style='color: #E6EDF3; font-size: 0.95rem; font-weight: 500;'>• {lead_context.get('occupation', 'Unknown Occupation')}</span>\n                            <span style='color: #E6EDF3; font-size: 0.95rem; font-weight: 500;'>• {lead_context.get('location', 'Unknown Location')}</span>\n                        </div>\n                    </div>\n                    <div style='text-align: right;'>\n                        <div style='font-size: 2.25rem; font-weight: 800; color: #FFFFFF; line-height: 1; font-family: "Space Grotesk", sans-serif; text-shadow: 0 0 20px {score_color}40;'>{int(score / 7 * 100)}%</div>\n                        <div style='font-size: 0.75rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-top: 4px;'>Compatibility Score</div>\n                    </div>\n                </div>\n                {(f"<div style='margin-top: 1.25rem; padding-top: 1.25rem; border-top: 1px solid rgba(255,255,255,0.05); font-size: 1rem; color: #f8fafc; line-height: 1.5;'><b>Claude's Strategy:</b> <span style='color: #cbd5e1;'>{(analysis_result.strategic_summary if analysis_result else 'Run analysis to generate strategy.')}</span></div>" if analysis_result else '')}\n            </div>\n            """, unsafe_allow_html=True)
    else:
        analysis_result = None
    st.markdown('---')
    tab1, tab_swarm, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab_journey, tab9, tab10 = st.tabs(['Lead Scoring', 'Agent Swarm', 'Deep Dossier', 'Retention Monitor', 'Property Matcher', 'Smart Swipe', 'Buyer Portal', 'Segmentation', 'Personalization', 'Journey Orchestration', 'Predictions', 'Simulator'])
    with tab1:
        st.subheader('AI Lead Scoring')
        col_map, col_details = st.columns([1, 1])
        with col_map:
            try:
                from components.interactive_lead_map import render_interactive_lead_map, generate_sample_lead_data
                lead_map_data_path = Path(__file__).parent / 'data' / 'lead_map_data.json'
                if lead_map_data_path.exists():
                    with open(lead_map_data_path) as f:
                        all_lead_data = json.load(f)
                        leads_with_geo = all_lead_data.get(market_key, [])
                else:
                    leads_with_geo = generate_sample_lead_data(market_key)
                render_interactive_lead_map(leads_with_geo, market=market_key)
            except ImportError:
                st.markdown('#### 📍 Hot Lead Clusters')
                if market_key == 'Rancho':
                    map_data = pd.DataFrame({'lat': [34.12, 34.11, 34.1, 34.13, 34.115], 'lon': [-117.57, -117.58, -117.56, -117.59, -117.575], 'type': ['Hot', 'Hot', 'Warm', 'Cold', 'Hot'], 'value': [100, 80, 50, 20, 90]})
                else:
                    map_data = pd.DataFrame({'lat': [30.2672, 30.27, 30.25, 30.28, 30.26], 'lon': [-97.7431, -97.75, -97.73, -97.76, -97.74], 'type': ['Hot', 'Hot', 'Warm', 'Cold', 'Hot'], 'value': [100, 80, 50, 20, 90]})
                st.map(map_data, zoom=11, use_container_width=True)
                st.caption(f'Real-time visualization of high-value lead activity in {selected_market}')
        with col_details:
            st.markdown('#### 🎯 Lead Analysis')
            st.markdown(f'**Analyzing:** {selected_lead_name}')
            if claude_services.get('qualification') and elite_mode:
                try:
                    lead_context = lead_options[selected_lead_name]
                    qualification_engine = claude_services['qualification']
                    qualification_engine.render_qualification_dashboard(lead_context, [])
                    st.markdown('#### Psychological DNA Radar')
                    categories = ['Intent', 'Finance', 'Timeline', 'Trust', 'Authority', 'Flexibility']
                    dna_values = [0.85, 0.72, 0.9, 0.65, 0.8, 0.45]
                    df_radar = pd.DataFrame(dict(r=dna_values, theta=categories))
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(r=dna_values, theta=categories, fill='toself', line_color='#6366F1', fillcolor='rgba(99, 102, 241, 0.2)'))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1], gridcolor='rgba(255,255,255,0.1)', tickfont=dict(size=10, color='#8B949E')), angularaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(size=11, color='#E6EDF3')), bgcolor='rgba(0,0,0,0)'), showlegend=False, margin=dict(l=40, r=40, t=40, b=40), height=300)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f'Claude qualification component error: {str(e)}')
                    st.info('🧠 **Fallback Mode**: Using cached behavioral insights')
            elif analysis_result:
                enhanced_intelligence.render_enhanced_behavioral_insight(selected_lead_name, analysis_result)
            else:
                with st.container(border=True):
                    st.markdown(f"**🤖 Claude's Behavioral Insight: {selected_lead_name}**")
                    if selected_lead_name == 'Sarah Chen (Apple Engineer)':
                        insight_text = "High-velocity lead. Apple engineers are data-driven; she responded to the 'Market Trend' link within 12 seconds. She's prioritizing commute efficiency over sqft. Focus on: Teravista connectivity."
                    elif selected_lead_name == 'Mike & Jessica Rodriguez (Growing Family)':
                        insight_text = "High-sentiment, low-confidence lead. They are checking 'First-time buyer' articles daily. Sentiment: 88% Positive but cautious. Focus on: Safety metrics and monthly payment breakdown."
                    elif selected_lead_name == 'David Kim (Investor)':
                        insight_text = "Analytical veteran. He's ignored the 'Lifestyle' highlights and went straight to the 'Cap Rate' tool. He has 3 tabs open on Manor area comps. Focus on: Off-market yield analysis."
                    elif selected_lead_name == 'Robert & Linda Williams (Luxury Downsizer)':
                        insight_text = "Relationship-focused. They've spent 4 minutes reading Jorge's 'About Me'. Sentiment: 95% Positive. They value trust over automation. Focus on: Personal concierge and exclusive downtown access."
                    elif selected_lead_name == 'Sarah Johnson':
                        insight_text = "Highly motivated school teacher. She's focused on Avery Ranch school boundary shifts. Sentiment: 92% Positive. Focus on: Alta Loma vs. North RC safety metrics."
                    elif selected_lead_name == 'Mike Chen':
                        insight_text = "Downsizing executive. He's spending significant time on the Victoria Gardens condo floor plans. Sentiment: Neutral/Analytical. Focus on: HOA stability and walkability scores."
                    elif selected_lead_name == 'Emily Davis':
                        insight_text = "Growth-oriented investor. She's tracking Alta Loma price-per-acre trends. Sentiment: Professional. Focus on: Multi-generational living potential and lot size ROI."
                    else:
                        insight_text = 'Initial discovery phase. Engagement is low. Sentiment: Undetermined. Focus on: Qualifying location preferences.'
                    st.info(insight_text)
            if claude_services.get('conversation') and elite_mode and (selected_lead_name != '-- Select a Lead --'):
                st.markdown('---')
                st.markdown('#### 🧠 Enhanced Conversation Intelligence Dashboard')
                try:
                    conversation_engine = claude_services['conversation']
                    lead_context = lead_options[selected_lead_name]
                    session_timestamp = int(time.time())
                    thread_id = f"{lead_context.get('lead_id', selected_lead_name)}_{session_timestamp}"
                    conversation_history = [{'role': 'user', 'content': f"Hi, I'm interested in properties in {lead_context.get('location', 'the area')}. I'm looking for a {lead_context.get('bedrooms', '3')} bedroom home.", 'timestamp': datetime.now() - timedelta(hours=2)}, {'role': 'assistant', 'content': f"Hi {selected_lead_name.split(' ')[0]}! Great to hear from you. I'd love to help you find the perfect home. What's your ideal timeline for moving?", 'timestamp': datetime.now() - timedelta(hours=2) + timedelta(minutes=5)}, {'role': 'user', 'content': f"We're hoping to move within {lead_context.get('timeline', '60 days')}. Budget is around {lead_context.get('budget_formatted', '$500k')}.", 'timestamp': datetime.now() - timedelta(hours=1)}, {'role': 'assistant', 'content': "Perfect! That's a great timeline to work with. Let me show you some properties that match your criteria and budget.", 'timestamp': datetime.now() - timedelta(hours=1) + timedelta(minutes=3)}]
                    auto_refresh_enabled = st.checkbox('🔄 Live Updates', value=True, help='Auto-refresh conversation intelligence every 30 seconds')
                    conversation_engine.render_enhanced_intelligence_dashboard(thread_id=thread_id, messages=conversation_history, lead_context=lead_context)
                    if auto_refresh_enabled:
                        st.caption('🔄 Live updates enabled - Dashboard refreshes every 30 seconds')
                        time.sleep(0.1)
                except Exception as e:
                    st.warning(f'Enhanced conversation intelligence unavailable: {str(e)}')
                    try:
                        conversation_engine.render_intelligence_panel([], lead_context)
                    except Exception:
                        st.info('💡 **Enhanced Intelligence Offline**: Basic conversation analysis temporarily unavailable')
            if selected_lead_name == '-- Select a Lead --':
                st.markdown('\n                <div style=\'background: rgba(22, 27, 34, 0.7); \n                            padding: 4rem 2rem; \n                            border-radius: 20px; \n                            text-align: center;\n                            border: 1px dashed rgba(99, 102, 241, 0.3);\n                            margin-top: 2rem;\n                            backdrop-filter: blur(12px);\n                            box-shadow: 0 8px 32px rgba(0,0,0,0.4);\'>\n                    <div style=\'font-size: 4rem; margin-bottom: 1.5rem; filter: drop-shadow(0 0 15px rgba(99, 102, 241, 0.2));\'>🎯</div>\n                    <h2 style=\'color: #FFFFFF; margin: 0 0 1rem 0; font-family: "Space Grotesk", sans-serif;\'>SELECT TARGET NODE</h2>\n                    <p style=\'color: #8B949E; font-size: 1.1rem; max-width: 500px; margin: 0 auto; font-family: "Inter", sans-serif;\'>\n                        Choose a lead identity to initialize multi-dimensional intelligence synthesis, \n                        property alignment, and predictive behavioral modeling.\n                    </p>\n                    <div style=\'margin-top: 3rem; display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;\'>\n                        <div style=\'background: rgba(255,255,255,0.03); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); min-width: 140px;\'>\n                            <div style=\'font-size: 2rem; margin-bottom: 0.5rem;\'>📊</div>\n                            <div style=\'font-size: 0.75rem; color: #6366F1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;\'>Scoring Engine</div>\n                        </div>\n                        <div style=\'background: rgba(255,255,255,0.03); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); min-width: 140px;\'>\n                            <div style=\'font-size: 2rem; margin-bottom: 0.5rem;\'>🏠</div>\n                            <div style=\'font-size: 0.75rem; color: #6366F1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;\'>Property Align</div>\n                        </div>\n                        <div style=\'background: rgba(255,255,255,0.03); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); min-width: 140px;\'>\n                            <div style=\'font-size: 2rem; margin-bottom: 0.5rem;\'>🔮</div>\n                            <div style=\'font-size: 0.75rem; color: #6366F1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;\'>AI Projections</div>\n                        </div>\n                    </div>\n                </div>\n                ', unsafe_allow_html=True)
                st.stop()
        if claude_services.get('qualification') and elite_mode and (selected_lead_name != '-- Select a Lead --'):
            st.markdown('#### 🧠 Claude Intelligence Dashboard')
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric('Claude Score', '87%', '+12%')
            with col2:
                st.metric('Intent Level', 'High', '↑ Increasing')
            with col3:
                st.metric('Qualification', 'Hot Lead', 'Autonomous')
            with col4:
                st.metric('Match Rate', '92%', '+15%')
            st.info('🎯 **Claude Insight**: This lead shows immediate buying signals with high lifestyle compatibility. Recommend priority agent assignment within 24 hours.')
        elif analysis_result:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric('Final Score', f'{analysis_result.final_score:.0f}%', '')
            with col2:
                st.metric('ML Score', f'{analysis_result.ml_conversion_score:.0f}%', '')
            with col3:
                st.metric('Jorge Score', f'{analysis_result.jorge_score}/7', '')
            with col4:
                st.metric('Churn Risk', f'{analysis_result.churn_risk_score:.0f}%', '', delta_color='inverse')
            st.markdown("#### Claude's Strategic Summary")
            st.info(analysis_result.strategic_summary)
        else:
            result = services['lead_scorer'].calculate_with_reasoning(lead_context)
            score = result['score']
            classification = result['classification']
            if classification == 'hot':
                st.success(f'🔥 **Hot Lead** - Score: {score}/7 Questions Answered')
            elif classification == 'warm':
                st.warning(f'⚠️ **Warm Lead** - Score: {score}/7 Questions Answered')
            else:
                st.info(f'❄️ **Cold Lead** - Score: {score}/7 Questions Answered')
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric('Questions Answered', f'{score}/7', '')
            with col2:
                st.metric('Engagement Class', classification.title(), '')
            with col3:
                st.metric('Lead Intent', 'Calculated', '')
            st.markdown('#### AI Analysis Breakdown')
            st.info(f"**Qualifying Data Found:** {result['reasoning']}")
        st.markdown('---')
        if analysis_result:
            enhanced_intelligence.render_enhanced_quick_actions(selected_lead_name, analysis_result)
        else:
            st.markdown('#### ⚡ Quick Actions')
            col_act1, col_act2, col_act3, col_act4 = st.columns(4)
            with col_act1:
                if st.button('📞 Call Now', use_container_width=True, type='primary'):
                    with st.spinner('Connecting via Bridge...'):
                        time.sleep(1.2)
                        st.toast(f'Calling {selected_lead_name}...', icon='📞')
                        st.success('Call initiated via GHL')
            with col_act2:
                if st.button('💬 Send SMS', use_container_width=True):
                    with st.spinner('Loading templates...'):
                        time.sleep(0.5)
                        st.toast(f'Opening SMS composer for {selected_lead_name}', icon='💬')
                        st.info('SMS template loaded in GHL')
            with col_act3:
                if st.button('📧 Send Email', use_container_width=True):
                    with st.spinner('Generating draft...'):
                        time.sleep(0.8)
                        st.toast(f'Email draft created for {selected_lead_name}', icon='📧')
                        st.success('Email queued in GHL')
            with col_act4:
                if st.button('📅 Schedule Tour', use_container_width=True):
                    with st.spinner('Syncing calendar...'):
                        time.sleep(1.0)
                        st.toast('Opening calendar...', icon='📅')
                        st.success('Calendar integration ready')
        if analysis_result:
            st.caption(f'📊 Claude Confidence: {analysis_result.confidence_score:.0%} | Analysis Time: {analysis_result.analysis_time_ms}ms')
            st.markdown('---')
            st.markdown("#### Claude's Recommended Actions")
            for action_item in analysis_result.recommended_actions[:3]:
                action = action_item.get('action', 'Follow up')
                priority = action_item.get('priority', 'medium')
                st.markdown(f'- **[{priority.upper()}]** {action}')
        else:
            st.caption('📊 Last Contact: 2 days ago via SMS | Next Follow-up: Tomorrow')
            st.markdown('---')
            st.markdown('#### Recommended Actions')
            for action in result['recommended_actions']:
                st.markdown(f'- {action}')
        if selected_lead_name != '-- Select a Lead --':
            st.markdown('---')
            st.markdown('### 🧬 CRM DNA Synchronization')
            sync_col1, sync_col2 = st.columns([2, 1])
            with sync_col1:
                st.write("Push Claude's deep psychological analysis and lifestyle dimensions directly to Jorge's GoHighLevel CRM.")
                st.caption('This enables GHL-native automation based on Trust Scores, Investment Mindsets, and 16+ Lifestyle Dimensions.')
            with sync_col2:
                if GHL_SYNC_AVAILABLE:
                    if st.button('🔄 Sync DNA to CRM', type='primary', use_container_width=True):
                        with st.spinner('🧬 Mapping psychological DNA to GHL...'):
                            sync_service = get_ghl_sync_service()
                            dna_payload = {}
                            if analysis_result:
                                dna_payload = {'factors': getattr(analysis_result, 'factor_scores', {}), 'dimensions': getattr(analysis_result, 'lifestyle_dimensions', {}), 'metadata': {'confidence': getattr(analysis_result, 'confidence_score', 0), 'strategic_summary': getattr(analysis_result, 'strategic_summary', '')}}
                            else:
                                dna_payload = {'factors': {'intent_level': 0.85, 'financial_readiness': 0.72, 'trust_building': 0.9, 'decision_authority': 0.8}, 'dimensions': {'status': 0.4, 'convenience': 0.9, 'security': 0.75, 'investment_mindset': 0.6}}
                            contact_id = lead_options[selected_lead_name].get('contact_id', 'contact_123_demo')
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            sync_result = loop.run_until_complete(sync_service.sync_dna_to_ghl(contact_id, dna_payload))
                            if sync_result['status'] == 'success':
                                st.success(f"✅ DNA Dossier synced! {sync_result['fields_updated']} fields updated in GHL.")
                                st.balloons()
                            else:
                                st.error(f"❌ Sync failed: {sync_result.get('message', 'Unknown error')}")
                else:
                    st.warning('GHL Sync Service Offline')
        st.markdown('---')
        try:
            from components.elite_refinements import render_actionable_heatmap
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_data = []
            for d in days:
                for h in range(24):
                    base = 10 if 9 <= h <= 18 else 2
                    activity = base + np.random.randint(0, 15)
                    heatmap_data.append({'day': d, 'hour': h, 'activity_count': activity})
            df_activity = pd.DataFrame(heatmap_data)
            render_actionable_heatmap(df_activity)
        except ImportError:
            st.info('🚀 Advanced Temporal Heatmap available in enterprise version')
        st.markdown('---')
        try:
            from components.enhanced_services import render_ai_lead_insights
            health_score = lead_context.get('overall_score', 85)
            try:
                if 'predictive_scorer' in services:
                    scoring_data = {'contact_id': lead_context.get('lead_id'), 'extracted_preferences': lead_context.get('extracted_preferences', {}), 'page_views': 15, 'email_opens': 4}
                    pred_result = services['predictive_scorer'].predict_conversion(scoring_data)
                    health_score = pred_result.get('conversion_probability', health_score)
            except Exception:
                pass
            lead_data_enhanced = {'lead_id': lead_context.get('lead_id', 'demo_lead'), 'name': selected_lead_name, 'health_score': health_score, 'engagement_level': 'high' if health_score > 80 else 'medium' if health_score > 40 else 'low', 'last_contact': '2 days ago', 'communication_preference': lead_context.get('communication_preference', 'text'), 'stage': 'qualification', 'urgency_indicators': lead_context.get('urgency_indicators', []), 'extracted_preferences': lead_context.get('extracted_preferences', {}), 'conversation_history': []}
            render_ai_lead_insights(lead_data_enhanced)
        except ImportError:
            st.info('🚀 Premium AI Insights available in enterprise version')
    with tab_swarm:
        st.subheader('🐝 Autonomous Agent Swarm')
        st.markdown('*Multi-agent analysis system for comprehensive lead profiling*')
        if not SWARM_AVAILABLE:
            st.error('⚠️ Swarm Service not available. Check dependencies.')
        elif selected_lead_name == '-- Select a Lead --':
            st.info('👈 Select a lead to deploy the agent swarm.')
        else:
            col_swarm_ctrl, col_swarm_status = st.columns([1, 2])
            with col_swarm_ctrl:
                if st.button('🚀 Deploy Swarm', type='primary', use_container_width=True):
                    with st.status('🐝 Swarm Active', expanded=True) as status:
                        st.write('Initializing agents...')
                        swarm_service = get_lead_swarm_service()
                        lead_context = lead_options[selected_lead_name]
                        st.write('Running parallel analysis...')
                        try:
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                            swarm_results = loop.run_until_complete(swarm_service.run_swarm(lead_context))
                            st.session_state[f'swarm_results_{selected_lead_name}'] = swarm_results
                            status.update(label='✅ Swarm Mission Complete', state='complete', expanded=False)
                        except Exception as e:
                            st.error(f'Swarm failure: {str(e)}')
                            status.update(label='❌ Swarm Failed', state='error')
                        results_key = f'swarm_results_{selected_lead_name}'
                        if results_key in st.session_state:
                            full_results = st.session_state[results_key]
                            results = full_results.get('specialist_findings', {})
                            synthesis = full_results.get('strategic_synthesis', {})
                            st.markdown('### 📋 Executive Strategic Synthesis')
                            with st.container(border=True):
                                col_syn1, col_syn2 = st.columns([2, 1])
                                with col_syn1:
                                    st.markdown(f'#### 🎯 Summary')
                                    st.write(synthesis.get('executive_summary', 'Synthesis loading...'))
                                    st.markdown(f"**Custom Hook:** `{synthesis.get('custom_outreach_hook', 'N/A')}`")
                                with col_syn2:
                                    conf = synthesis.get('confidence_index', 0.8)
                                    st.metric('Swarm Confidence', f'{int(conf * 100)}%', delta='High Accuracy')
                                    st.warning(f"**Bottleneck:** {synthesis.get('conversion_bottleneck', 'None detected')}")
                                st.markdown('#### ⚡ Tactical Next Steps')
                                t_cols = st.columns(3)
                                for i, step in enumerate(synthesis.get('tactical_next_steps', ['Follow up'])):
                                    with t_cols[i % 3]:
                                        st.info(f'**{i + 1}.** {step}')
                            st.markdown('---')
                            st.markdown('#### 🔍 Specialist Findings')
                            st.markdown("\n                <style>\n                    .agent-card {\n                        background: rgba(22, 27, 34, 0.6);\n                        border: 1px solid rgba(255, 255, 255, 0.1);\n                        border-radius: 12px;\n                        padding: 1.5rem;\n                        margin-bottom: 1rem;\n                        transition: all 0.3s ease;\n                        height: 100%;\n                    }\n                    .agent-card:hover {\n                        border-color: #6366F1;\n                        box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);\n                        transform: translateY(-2px);\n                    }\n                    .agent-header {\n                        display: flex;\n                        align-items: center;\n                        gap: 10px;\n                        margin-bottom: 1rem;\n                        border-bottom: 1px solid rgba(255, 255, 255, 0.05);\n                        padding-bottom: 0.5rem;\n                    }\n                    .agent-icon {\n                        font-size: 1.5rem;\n                    }\n                    .agent-name {\n                        font-family: 'Space Grotesk', sans-serif;\n                        font-weight: 700;\n                        color: #FFFFFF;\n                        font-size: 1.1rem;\n                    }\n                    .agent-stat {\n                        display: flex;\n                        justify-content: space-between;\n                        margin-bottom: 0.5rem;\n                        font-size: 0.9rem;\n                    }\n                    .stat-label { color: #8B949E; }\n                    .stat-value { color: #E6EDF3; font-weight: 600; }\n                    .agent-tags {\n                        display: flex;\n                        flex-wrap: wrap;\n                        gap: 6px;\n                        margin-top: 1rem;\n                    }\n                    .agent-tag {\n                        background: rgba(99, 102, 241, 0.1);\n                        color: #6366F1;\n                        padding: 2px 8px;\n                        border-radius: 4px;\n                        font-size: 0.75rem;\n                        border: 1px solid rgba(99, 102, 241, 0.2);\n                    }\n                </style>\n                ", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    fin = results.get('Financial Analyst', {})
                    if 'error' in fin:
                        st.error(fin['error'])
                    else:
                        st.markdown(f"""\n                        <div class="agent-card">\n                            <div class="agent-header">\n                                <span class="agent-icon">💰</span>\n                                <span class="agent-name">Financial Analyst</span>\n                            </div>\n                            <div class="agent-stat">\n                                <span class="stat-label">Qualification:</span>\n                                <span class="stat-value">{fin.get('qualification_status', 'Unknown')}</span>\n                            </div>\n                            <div class="agent-stat">\n                                <span class="stat-label">Budget Range:</span>\n                                <span class="stat-value">{fin.get('estimated_budget_range', 'Unknown')}</span>\n                            </div>\n                            <div class="agent-tags">\n                                {' '.join((f'<span class="agent-tag">{sig}</span>' for sig in fin.get('financial_signals', [])))}\n                            </div>\n                        </div>\n                        """, unsafe_allow_html=True)
                        with st.expander('🔍 View Reasoning Trace'):
                            st.info(fin.get('reasoning_trace', 'No trace available.'))
                with c2:
                    time_agent = results.get('Timeline Assessor', {})
                    if 'error' in time_agent:
                        st.error(time_agent['error'])
                    else:
                        st.markdown(f"""\n                        <div class="agent-card">\n                            <div class="agent-header">\n                                <span class="agent-icon">⏳</span>\n                                <span class="agent-name">Timeline Assessor</span>\n                            </div>\n                            <div class="agent-stat">\n                                <span class="stat-label">Urgency:</span>\n                                <span class="stat-value">{time_agent.get('urgency_level', 'Unknown')}</span>\n                            </div>\n                            <div class="agent-stat">\n                                <span class="stat-label">Target Date:</span>\n                                <span class="stat-value">{time_agent.get('target_move_date', 'Unknown')}</span>\n                            </div>\n                            <div class="agent-tags">\n                                {' '.join((f'<span class="agent-tag">{driver}</span>' for driver in time_agent.get('drivers', [])))}\n                            </div>\n                        </div>\n                        """, unsafe_allow_html=True)
                        with st.expander('🔍 View Reasoning Trace'):
                            st.info(time_agent.get('reasoning_trace', 'No trace available.'))
                c3, c4 = st.columns(2)
                with c3:
                    psych = results.get('Behavioral Psychologist', {})
                    if 'error' in psych:
                        st.error(psych['error'])
                    else:
                        st.markdown(f"""\n                        <div class="agent-card">\n                            <div class="agent-header">\n                                <span class="agent-icon">🧠</span>\n                                <span class="agent-name">Behavioral Psychologist</span>\n                            </div>\n                            <div class="agent-stat">\n                                <span class="stat-label">Personality:</span>\n                                <span class="stat-value">{psych.get('personality_type', 'Unknown')}</span>\n                            </div>\n                            <div class="agent-stat">\n                                <span class="stat-label">Style:</span>\n                                <span class="stat-value">{psych.get('communication_style', 'Unknown')}</span>\n                            </div>\n                            <div class="agent-tags">\n                                {' '.join((f'<span class="agent-tag">{mot}</span>' for mot in psych.get('motivators', [])))}\n                            </div>\n                        </div>\n                        """, unsafe_allow_html=True)
                        with st.expander('🔍 View Reasoning Trace'):
                            st.info(psych.get('reasoning_trace', 'No trace available.'))
                with c4:
                    risk = results.get('Risk Analyst', {})
                    if 'error' in risk:
                        st.error(risk['error'])
                    else:
                        risk_level = risk.get('risk_level', 'Unknown')
                        risk_color = '#ef4444' if 'High' in risk_level else '#f59e0b' if 'Medium' in risk_level else '#10b981'
                        st.markdown(f"""\n                        <div class="agent-card">\n                            <div class="agent-header">\n                                <span class="agent-icon">🛡️</span>\n                                <span class="agent-name">Risk Analyst</span>\n                            </div>\n                            <div class="agent-stat">\n                                <span class="stat-label">Risk Level:</span>\n                                <span class="stat-value" style="color: {risk_color};">{risk_level}</span>\n                            </div>\n                            <div class="agent-stat">\n                                <span class="stat-label">Competitor Risk:</span>\n                                <span class="stat-value">{('YES' if risk.get('competitor_risk') else 'NO')}</span>\n                            </div>\n                            <div class="agent-tags">\n                                {' '.join((f'<span class="agent-tag" style="color: #ef4444; border-color: rgba(239, 68, 68, 0.2);">{obj}</span>' for obj in risk.get('primary_objections', [])))}\n                            </div>\n                        </div>\n                        """, unsafe_allow_html=True)
                        with st.expander('🔍 View Reasoning Trace'):
                            st.info(risk.get('reasoning_trace', 'No trace available.'))
                st.markdown('---')
                neg = results.get('Negotiation Engine', {})
                if neg:
                    st.markdown(f'''\n                    <div class="agent-card" style="border-left: 5px solid #6366F1;">\n                        <div class="agent-header">\n                            <span class="agent-icon">🤝</span>\n                            <span class="agent-name">Negotiation Engine (Active Defense)</span>\n                        </div>\n                        <div class="agent-stat">\n                            <span class="stat-label">Tactical Style:</span>\n                            <span class="stat-value">{neg.get('negotiation_style', 'Adaptive')}</span>\n                        </div>\n                        <div class="agent-stat">\n                            <span class="stat-label">Counter-Scripts Ready:</span>\n                            <span class="stat-value">{len(neg.get('counter_scripts', []))}</span>\n                        </div>\n                        <div style="margin-top: 1rem;">\n                            <strong>🎯 Primary Counter:</strong><br>\n                            <span style="color: #6366F1; font-style: italic;">"{neg.get('counter_scripts', ['Ready to assist'])[0]}"</span>\n                        </div>\n                    </div>\n                    ''', unsafe_allow_html=True)
                    with st.expander('🔍 View Negotiation Reasoning & Inter-Agent Messages'):
                        if 'swarm_metadata' in full_results:
                            msgs = full_results['swarm_metadata'].get('inter_agent_messages', [])
                            if msgs:
                                st.warning('💬 **Inter-Agent Signal Received:**')
                                for m in msgs:
                                    st.write(f"**From {m['from']}:** {m['deal_killer']}")
                        st.info(neg.get('reasoning_trace', 'No trace available.'))
    with tab2:
        if analysis_result:
            enhanced_intelligence.render_deep_intelligence_tab(selected_lead_name, lead_context, analysis_result)
        else:
            st.info('Select a lead and run analysis to unlock Deep Dossier research.')
    with tab3:
        try:
            from components.churn_early_warning_dashboard import ChurnEarlyWarningDashboard
            st.subheader('🚨 Churn Early Warning System')
            st.markdown('*Real-time monitoring and intervention orchestration for lead retention*')
            churn_dashboard = ChurnEarlyWarningDashboard(claude_assistant=claude)
            churn_dashboard.render_dashboard()
        except Exception as e:
            st.error(f'⚠️ Churn Dashboard Error: {str(e)}')
            st.code(str(type(e).__name__) + ': ' + str(e))
            st.code(traceback.format_exc())
            st.markdown('### 📊 Sample Churn Risk Analytics')
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric('Total Leads', '147', '+12')
            with col2:
                st.metric('Critical Risk', '3', '+1', delta_color='inverse')
            with col3:
                st.metric('High Risk', '8', '-2')
            with col4:
                st.metric('Success Rate', '78.5%', '+2.1%')
            st.info('💡 The full Churn Prediction Engine provides 26 behavioral features, multi-horizon risk scoring, and automated intervention orchestration.')
    with tab4:
        st.subheader('🏠 Claude Semantic Property Matching')
        if selected_lead_name == '-- Select a Lead --':
            st.info('👈 Please select a lead from Tab 1 to see AI-powered property matches')
        elif claude_services.get('properties') and elite_mode:
            st.markdown('*Advanced lifestyle-based property matching using Claude AI*')
            try:
                lead_context = lead_options[selected_lead_name]
                semantic_matcher = claude_services['properties']
                with st.spinner('🧠 Claude is analyzing lifestyle compatibility...'):
                    semantic_matcher.render_semantic_matching_interface(lead_context)
                st.markdown('---')
                st.markdown('### 🔮 Life Transition & Investment Forecast')
                col_trans1, col_trans2 = st.columns(2)
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                lifestyle_profile = loop.run_until_complete(semantic_matcher._extract_lifestyle_profile(lead_context))
                transitions = loop.run_until_complete(semantic_matcher.predict_life_transitions(lifestyle_profile))
                investment_psych = loop.run_until_complete(semantic_matcher.get_investment_psychology(lead_context))
                with col_trans1:
                    st.markdown('#### ⏳ Life Transition')
                    st.success(f"**Predicted Next Stage:** {transitions.get('predicted_next_stage', 'Unknown').title()}")
                    st.write(f"**Timeframe:** {transitions.get('estimated_timeframe')}")
                    st.write(f"**Future Needs:** {transitions.get('future_space_needs')}")
                    st.progress(transitions.get('long_term_suitability_score', 0.5), text='Long-term Suitability')
                with col_trans2:
                    st.markdown('#### 💰 Investment Psychology')
                    st.info(f"**Focus:** {investment_psych.get('focus')}")
                    st.write(f"**Risk Tolerance:** {investment_psych.get('risk_tolerance')}")
                    st.progress(investment_psych.get('exit_strategy_importance', 0.5), text='Exit Strategy Priority')
                    st.progress(investment_psych.get('emotional_attachment', 0.5), text='Emotional Attachment')
            except Exception as e:
                st.error(f'Claude semantic matching failed: {str(e)}')
                try:
                    from components.property_matcher_ai import render_property_matcher
                    lead_context = lead_options[selected_lead_name]
                    render_property_matcher(lead_context, elite_mode=elite_mode, analysis_result=analysis_result)
                except ImportError:
                    st.warning('Fallback property matcher not available')
        else:
            try:
                from components.property_matcher_ai import render_property_matcher
                if selected_lead_name != '-- Select a Lead --':
                    lead_context = lead_options[selected_lead_name]
                    render_property_matcher(lead_context, elite_mode=elite_mode, analysis_result=analysis_result)
            except ImportError:
                st.info('Property Matcher component loading...')
        st.markdown('---')
        try:
            from components.elite_refinements import render_dynamic_timeline, render_feature_gap
            if selected_lead_name != '-- Select a Lead --':
                lead_context = lead_options[selected_lead_name]
                actions_completed = lead_context.get('actions_completed', 2)
                render_dynamic_timeline(days_remaining=45, actions_completed=actions_completed, agent_name='Jorge')
                st.markdown('---')
                property_sample = {'features': ['3-car garage', 'swimming pool', 'granite countertops', 'hardwood floors'], 'price': 650000, 'bedrooms': 4, 'bathrooms': 3}
                must_haves = lead_context.get('extracted_preferences', {}).get('must_haves', ['swimming pool', '3-car garage', 'updated kitchen', 'good schools'])
                if must_haves:
                    render_feature_gap(property_data=property_sample, lead_must_haves=must_haves, match_score=87)
        except ImportError:
            st.info('🚀 Premium Timeline & Gap Analysis available in enterprise version')
    with tab5:
        try:
            from ghl_real_estate_ai.streamlit_demo.components.property_swipe import render_property_swipe
            render_property_swipe(services, selected_lead_name)
        except ImportError:
            st.info('🔥 Smart Swipe component coming soon')
    with tab6:
        if ENHANCED_COMPONENTS_AVAILABLE:
            render_buyer_portal_manager(selected_lead_name)
        else:
            st.subheader('🌐 Buyer Portal (Phase 3)')
            st.info('Enhanced Buyer Portal Manager loading...')
    with tab7:
        if elite_mode:
            render_elite_segmentation_tab()
        else:
            try:
                from components.segmentation_pulse import render_segmentation_pulse
                leads_for_segmentation = []
                if 'conversations' in mock_data:
                    for conv in mock_data['conversations']:
                        leads_for_segmentation.append({'id': conv.get('contact_id'), 'name': conv.get('contact_name'), 'engagement_score': conv.get('message_count') * 10, 'lead_score': conv.get('lead_score'), 'budget': 500000 if conv.get('budget') == 'unknown' else 1500000, 'last_activity_days_ago': 2, 'buyer_type': 'luxury_buyer' if 'lux' in conv.get('contact_id', '') else 'standard', 'interested_property_type': 'single_family'})
                if leads_for_segmentation:
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(services['segmentation'].segment_leads(leads_for_segmentation, method='behavioral'))
                    if result['segments']:
                        main_segment = result['segments'][0]
                        render_segmentation_pulse(main_segment)
                        st.markdown('---')
                        st.markdown('### 📋 All Segments Overview')
                        st.markdown('<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 1rem;">', unsafe_allow_html=True)
                        for seg in result['segments']:
                            seg_name = seg['name'].replace('_', ' ').title()
                            char = seg['characteristics']
                            segment_html = f"""\n                            <div style="background: rgba(22, 27, 34, 0.7); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); backdrop-filter: blur(12px);">\n                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">\n                                    <h3 style="margin: 0; color: #FFFFFF; font-size: 1.25rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif;">{seg_name}</h3>\n                                    <div style="background: rgba(99, 102, 241, 0.15); color: #6366F1; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; border: 1px solid rgba(99, 102, 241, 0.3); text-transform: uppercase;">{seg['size']} NODES</div>\n                                </div>\n                                \n                                <div style="display: flex; flex-direction: column; gap: 0.5rem; margin: 1rem 0; padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">\n                                    <div style="display: flex; align-items: center; gap: 0.5rem;">\n                                        <span>📊</span>\n                                        <span style="color: #8B949E; font-size: 0.875rem;">Engagement: <strong style="color: #FFFFFF;">{char['avg_engagement']}%</strong></span>\n                                    </div>\n                                    <div style="display: flex; align-items: center; gap: 0.5rem;">\n                                        <span>⭐</span>\n                                        <span style="color: #8B949E; font-size: 0.875rem;">Score: <strong style="color: #FFFFFF;">{char['avg_lead_score']}</strong></span>\n                                    </div>\n                                </div>\n                                \n                                <div style="font-size: 1.75rem; font-weight: 700; color: #6366F1; margin: 0.5rem 0; font-family: 'Space Grotesk', sans-serif; text-shadow: 0 0 10px rgba(99, 102, 241, 0.3);">${char['total_value']:,.0f}</div>\n                                \n                                <div style="margin: 1rem 0;">\n                                    <strong style="font-size: 0.75rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;">Tactical Directives:</strong>\n                                    <ul style="margin: 0.5rem 0; padding-left: 1.25rem; font-size: 0.875rem; color: #E6EDF3; line-height: 1.6; opacity: 0.9;">\n                                        {''.join((f'<li>{action}</li>' for action in seg['recommended_actions'][:2]))}\n                                    </ul>\n                                </div>\n                            </div>\n                            """
                            st.markdown(segment_html, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
            except (ImportError, Exception) as e:
                st.info(f'Smart Segmentation module unavailable: {e}')
    with tab8:
        if ENHANCED_COMPONENTS_AVAILABLE:
            render_personalization_engine(services, selected_lead_name, analysis_result=analysis_result)
        else:
            st.subheader('🎨 Personalized Content Engine')
            render_personalization_tab(services, selected_lead_name)
    with tab_journey:
        if ENHANCED_INTELLIGENCE_AVAILABLE and selected_lead_name != '-- Select a Lead --':
            lead_context = lead_options[selected_lead_name]
            enhanced_intelligence.render_journey_orchestration_tab(selected_lead_name, lead_context, analysis_result)
        else:
            st.info('Select a lead and run analysis to initialize Journey Orchestration.')
    with tab9:
        if ENHANCED_COMPONENTS_AVAILABLE:
            render_conversion_predictor(services, selected_lead_name, analysis_result=analysis_result)
        else:
            st.subheader('🔮 Predictive Conversion Insights')
            render_predictions_tab(services, selected_lead_name)
            try:
                from components.contact_timing import render_contact_timing_badges
                best_times = [{'day': 'Tomorrow', 'time': '2:00 PM - 4:00 PM', 'urgency': 'high', 'probability': 87}, {'day': 'Friday', 'time': '10:00 AM - 12:00 PM', 'urgency': 'medium', 'probability': 68}]
                render_contact_timing_badges(best_times)
            except ImportError:
                pass
    with tab10:
        st.subheader('💬 Real-Time Conversation Coaching')
        if selected_lead_name == '-- Select a Lead --':
            st.info('👈 Please select a lead to start real-time conversation coaching')
        elif claude_services.get('conversation') and elite_mode:
            st.markdown('*Live agent assistance with AI-powered response suggestions and objection handling*')
            try:
                conversation_engine = claude_services['conversation']
                lead_context = lead_options[selected_lead_name]
                render_real_time_conversation_coach(claude_services, lead_context, selected_lead_name)
            except Exception as e:
                st.error(f'Real-time conversation coaching failed: {str(e)}')
                if ENHANCED_COMPONENTS_AVAILABLE:
                    render_conversation_simulator(services, selected_lead_name)
                else:
                    render_simulator_tab(services, selected_lead_name)
        elif ENHANCED_COMPONENTS_AVAILABLE:
            render_conversation_simulator(services, selected_lead_name)
        else:
            st.subheader('💬 AI Conversation Simulator')
            render_simulator_tab(services, selected_lead_name)

def render_real_time_conversation_coach(claude_services, lead_context, selected_lead_name):
    """
    Advanced real-time conversation coaching with live agent assistance.

    Features:
    - Live conversation analysis during active chats
    - Instant response suggestions and objection handling
    - Closing signal alerts and timing recommendations
    - A/B tested response optimization
    - Real-time emotional state monitoring
    """
    st.markdown(f'**🎯 Live Coaching Session: {selected_lead_name}**')
    messages_key = f'coaching_messages_{selected_lead_name}'
    analytics_key = f'coaching_analytics_{selected_lead_name}'
    if messages_key not in st.session_state:
        st.session_state[messages_key] = [{'role': 'lead', 'content': f"Hi, I've been looking at some properties online and I'm interested in learning more about the {lead_context.get('location', 'area')} market.", 'timestamp': datetime.now() - timedelta(minutes=5), 'emotional_state': 'curious', 'intent_score': 0.6}]
    if analytics_key not in st.session_state:
        st.session_state[analytics_key] = {'conversation_health': 85, 'intent_trajectory': [0.6, 0.65, 0.7], 'emotional_state': 'curious', 'closing_readiness': 0.4, 'objection_risk': 0.2}
    coaching_messages = st.session_state[messages_key]
    coaching_analytics = st.session_state[analytics_key]
    st.markdown('### 📊 Live Conversation Analytics')
    col_analytics1, col_analytics2, col_analytics3, col_analytics4 = st.columns(4)
    with col_analytics1:
        health_score = coaching_analytics['conversation_health']
        health_color = 'green' if health_score >= 80 else 'orange' if health_score >= 60 else 'red'
        st.metric('Conversation Health', f'{health_score}%', delta='+5%' if len(coaching_messages) > 1 else None)
    with col_analytics2:
        intent_level = coaching_analytics['intent_trajectory'][-1]
        st.metric('Buying Intent', f'{intent_level:.0%}', delta='+10%' if len(coaching_analytics['intent_trajectory']) > 1 else None)
    with col_analytics3:
        emotional_state = coaching_analytics['emotional_state']
        emotion_emoji = {'curious': '🤔', 'excited': '😊', 'concerned': '😟', 'analytical': '🧐', 'ready': '🎯'}.get(emotional_state, '😐')
        st.metric('Emotional State', f'{emotion_emoji} {emotional_state.title()}')
    with col_analytics4:
        closing_readiness = coaching_analytics['closing_readiness']
        st.metric('Closing Readiness', f'{closing_readiness:.0%}', delta='+15%' if closing_readiness > 0.5 else None)
    col_conversation, col_coaching = st.columns([2, 1])
    with col_conversation:
        st.markdown('#### 💬 Live Conversation')
        for i, message in enumerate(coaching_messages):
            is_agent = message['role'] == 'agent'
            with st.chat_message(message['role']):
                st.write(message['content'])
                if not is_agent:
                    col_analytics_inline1, col_analytics_inline2 = st.columns(2)
                    with col_analytics_inline1:
                        st.caption(f"🎯 Intent: {message.get('intent_score', 0.5):.0%}")
                    with col_analytics_inline2:
                        st.caption(f"💭 Emotion: {message.get('emotional_state', 'neutral')}")
        if (agent_input := st.chat_input('Type your response (coaching suggestions will appear on the right)...')):
            lead_responses = {'tell me more about the market': {'content': "I'm particularly interested in appreciation trends and what's driving the market. Are we in a buyer's or seller's market right now?", 'emotional_state': 'analytical', 'intent_score': 0.75}, 'what properties do you have': {'content': f"I'm looking for a {lead_context.get('bedrooms', '3')} bedroom home in {lead_context.get('location', 'the area')} with a budget around {lead_context.get('budget_formatted', '$500k')}. Do you have anything that fits?", 'emotional_state': 'excited', 'intent_score': 0.85}, 'schedule a showing': {'content': "That sounds perfect! When would be a good time to see it? I'm available this weekend.", 'emotional_state': 'ready', 'intent_score': 0.95}}
            coaching_messages.append({'role': 'agent', 'content': agent_input, 'timestamp': datetime.now()})
            best_match = None
            best_score = 0
            for key, response in lead_responses.items():
                if any((word in agent_input.lower() for word in key.split())):
                    score = sum((1 for word in key.split() if word in agent_input.lower()))
                    if score > best_score:
                        best_score = score
                        best_match = response
            if not best_match:
                best_match = {'content': "That's interesting. Can you tell me more about what makes this area special?", 'emotional_state': 'curious', 'intent_score': 0.65}
            coaching_messages.append({'role': 'lead', 'content': best_match['content'], 'timestamp': datetime.now() + timedelta(seconds=30), 'emotional_state': best_match['emotional_state'], 'intent_score': best_match['intent_score']})
            coaching_analytics['emotional_state'] = best_match['emotional_state']
            coaching_analytics['intent_trajectory'].append(best_match['intent_score'])
            coaching_analytics['closing_readiness'] = min(1.0, best_match['intent_score'] * 1.1)
            st.rerun()
    with col_coaching:
        st.markdown('#### 🧠 Live AI Coaching')
        try:
            conversation_engine = claude_services['conversation']
            with st.spinner('Analyzing thread state...'):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                formatted_msgs = []
                for m in coaching_messages:
                    formatted_msgs.append({'role': 'user' if m['role'] == 'lead' else 'assistant', 'content': m['content']})
                thread_analysis = loop.run_until_complete(conversation_engine.analyze_conversation_thread(f'coaching_{selected_lead_name}', formatted_msgs, lead_context))
                closing_signals = thread_analysis.get('closing_signals')
                if closing_signals:
                    readiness = closing_signals.closing_readiness_score
                    st.progress(readiness, text=f'Closing Readiness: {readiness:.0%}')
                    st.markdown(f'**Strategy:** {closing_signals.optimal_closing_strategy}')
                emotional = thread_analysis.get('emotional_state')
                if emotional:
                    st.info(f'**Tone:** {emotional.primary_emotion.title()} ({emotional.emotional_trajectory})')
        except Exception as e:
            st.warning('Advanced live coaching offline.')
        st.markdown('#### 💡 Suggested Responses')
        if coaching_messages and latest_lead_message:
            emotional_state = latest_lead_message.get('emotional_state', 'curious')
            intent_score = latest_lead_message.get('intent_score', 0.5)
            if emotional_state == 'analytical':
                suggestions = ['Share local market appreciation data for the area', 'Discuss comparable sales and pricing trends', 'Provide neighborhood demographic insights', 'Offer to send a detailed market report']
            elif emotional_state == 'excited':
                suggestions = ['Ask about their timeline for moving', 'Inquire about must-have features', 'Suggest scheduling a property viewing', 'Discuss financing options and budget']
            elif emotional_state == 'ready':
                suggestions = ['Schedule an immediate property viewing', 'Discuss pre-approval status', 'Ask about their decision-making process', 'Offer to prepare a property shortlist']
            else:
                suggestions = ['Ask about their housing goals and timeline', 'Understand their current living situation', 'Discuss their ideal property features', 'Share success stories from similar clients']
            for i, suggestion in enumerate(suggestions, 1):
                if st.button(f'💬 Option {i}', key=f'coaching_suggestion_{i}_{selected_lead_name}', use_container_width=True, help=suggestion):
                    coaching_messages.append({'role': 'agent', 'content': suggestion, 'timestamp': datetime.now(), 'suggested': True})
                    st.rerun()
        objection_risk = coaching_analytics.get('objection_risk', 0.2)
        if objection_risk > 0.3:
            with st.container(border=True):
                st.markdown('#### ⚠️ Objection Alert')
                st.warning('Potential objection detected. Consider addressing concerns proactively.')
                objection_handlers = ['Acknowledge their concern and ask for specifics', 'Share how other clients overcame similar concerns', 'Provide data that addresses their specific worry', 'Offer to connect them with past clients']
                for handler in objection_handlers:
                    st.markdown(f'• {handler}')
        closing_readiness = coaching_analytics.get('closing_readiness', 0.4)
        if closing_readiness >= 0.7:
            with st.container(border=True):
                st.markdown('#### 🎯 Closing Opportunity')
                st.success('High closing readiness detected! Time to move toward next steps.')
                closing_actions = ['🏠 Schedule property viewing', '💰 Discuss financing pre-approval', '📅 Set timeline for decision', '🤝 Introduce to lender partner']
                for action in closing_actions:
                    st.markdown(f'• {action}')
        st.markdown('#### 📈 Session Performance')
        if len(coaching_messages) > 2:
            intent_improvement = (coaching_analytics['intent_trajectory'][-1] - coaching_analytics['intent_trajectory'][0]) * 100
            st.metric('Intent Improvement', f'+{intent_improvement:.0f}%')
            response_effectiveness = min(100, len([m for m in coaching_messages if m['role'] == 'agent']) * 15)
            st.metric('Response Effectiveness', f'{response_effectiveness}%')
        objection_risk = st.session_state.coaching_analytics.get('objection_risk', 0.2)
        if objection_risk > 0.3:
            with st.container(border=True):
                st.markdown('#### ⚠️ Objection Alert')
                st.warning('Potential objection detected. Consider addressing concerns proactively.')
                objection_handlers = ['Acknowledge their concern and ask for specifics', 'Share how other clients overcame similar concerns', 'Provide data that addresses their specific worry', 'Offer to connect them with past clients']
                for handler in objection_handlers:
                    st.markdown(f'• {handler}')
        closing_readiness = st.session_state.coaching_analytics.get('closing_readiness', 0.4)
        if closing_readiness >= 0.7:
            with st.container(border=True):
                st.markdown('#### 🎯 Closing Opportunity')
                st.success('High closing readiness detected! Time to move toward next steps.')
                closing_actions = ['🏠 Schedule property viewing', '💰 Discuss financing pre-approval', '📅 Set timeline for decision', '🤝 Introduce to lender partner']
                for action in closing_actions:
                    st.markdown(f'• {action}')
        st.markdown('#### 📈 Session Performance')
        if len(st.session_state.coaching_messages) > 2:
            intent_improvement = (st.session_state.coaching_analytics['intent_trajectory'][-1] - st.session_state.coaching_analytics['intent_trajectory'][0]) * 100
            st.metric('Intent Improvement', f'+{intent_improvement:.0f}%')
            response_effectiveness = min(100, len([m for m in st.session_state.coaching_messages if m['role'] == 'agent']) * 15)
            st.metric('Response Effectiveness', f'{response_effectiveness}%')

def render_claude_enhanced_simulator(claude_services, lead_context, selected_lead_name):
    """Enhanced conversation simulator with Claude intelligence."""
    st.markdown(f'**Simulating conversation with {selected_lead_name}**')
    with st.sidebar:
        st.markdown('### 🧠 Claude Real-Time Insights')
        if 'conversation_messages' not in st.session_state:
            st.session_state.conversation_messages = []
        col_int1, col_int2 = st.columns(2)
        with col_int1:
            st.metric('Intent Level', '65%')
            st.metric('Urgency Score', '42%')
        with col_int2:
            st.metric('Engagement', 'High')
            st.metric('Readiness', 'Medium')
    col_chat, col_intelligence = st.columns([2, 1])
    with col_chat:
        st.markdown('#### 💬 Conversation Simulation')
        if 'conversation_messages' not in st.session_state:
            st.session_state.conversation_messages = [{'role': 'assistant', 'content': f"Hi {selected_lead_name.split(' ')[0]}! I saw you've been looking at properties in the area. What kind of home are you hoping to find?"}]
        for message in st.session_state.conversation_messages:
            with st.chat_message(message['role']):
                st.write(message['content'])
        if (user_input := st.chat_input('Type your response...')):
            st.session_state.conversation_messages.append({'role': 'user', 'content': user_input})
            with st.spinner('🧠 Claude is analyzing response...'):
                try:
                    conversation_engine = claude_services['conversation']
                    response = f"Thanks for sharing that! Based on your interests in {lead_context.get('location', 'the area')}, I have some great options to show you."
                    st.session_state.conversation_messages.append({'role': 'assistant', 'content': response})
                    st.rerun()
                except Exception as e:
                    st.error(f'Claude response generation failed: {str(e)}')
    with col_intelligence:
        st.markdown('#### 🎯 Claude Guidance')
        if len(st.session_state.conversation_messages) > 1:
            with st.container(border=True):
                st.markdown('**Intent Analysis**')
                st.progress(0.65, text='Buying Intent: 65%')
                st.progress(0.42, text='Urgency: 42%')
                st.progress(0.78, text='Financial Readiness: 78%')
        st.markdown('#### 💡 Suggested Responses')
        suggestions = ['Ask about their timeline for moving', 'Inquire about their budget range', 'Offer to schedule a property viewing', 'Share relevant market insights']
        for i, suggestion in enumerate(suggestions, 1):
            if st.button(f'Option {i}', key=f'suggestion_{i}', use_container_width=True):
                st.session_state.conversation_messages.append({'role': 'assistant', 'content': suggestion})
                st.rerun()

def render_personalization_tab(services, selected_lead_name):
    """Fallback implementation - basic personalization tab"""
    st.markdown('*Generate tailored outreach materials based on lead behavior and preferences*')
    st.info('Enhanced Personalization Engine loading...')

def render_predictions_tab(services, selected_lead_name):
    """Fallback implementation - basic predictions tab"""
    st.markdown('*Statistical modeling of future lead actions*')
    st.info('Enhanced Conversion Predictor loading...')

def render_simulator_tab(services, selected_lead_name):
    """Fallback implementation - basic simulator tab"""
    st.markdown('*Test how the AI assistant would handle specific scenarios with this lead*')
    st.info('Enhanced Conversation Simulator loading...')

@st.cache_data(ttl=300)
def get_conversation_health_score(lead_name: str) -> str:
    """Get conversation health score for lead filtering."""
    lead_health_map = {'Sarah Chen (Apple Engineer)': 'Excellent', 'Mike & Jessica Rodriguez (Growing Family)': 'Good', 'David Kim (Investor)': 'Concerning', 'Robert & Linda Williams (Luxury Downsizer)': 'Excellent', 'Sarah Johnson': 'Good', 'Mike Chen': 'Good', 'Emily Davis': 'Excellent'}
    return lead_health_map.get(lead_name, 'Good')

@st.cache_data(ttl=300)
def get_emotional_state(lead_name: str) -> str:
    """Get emotional state for lead filtering."""
    emotional_state_map = {'Sarah Chen (Apple Engineer)': 'Analytical', 'Mike & Jessica Rodriguez (Growing Family)': 'Cautious', 'David Kim (Investor)': 'Analytical', 'Robert & Linda Williams (Luxury Downsizer)': 'Excited', 'Sarah Johnson': 'Excited', 'Mike Chen': 'Analytical', 'Emily Davis': 'Ready'}
    return emotional_state_map.get(lead_name, 'Analytical')

@st.cache_data(ttl=300)
def get_closing_readiness(lead_name: str) -> str:
    """Get closing readiness level for lead filtering."""
    closing_readiness_map = {'Sarah Chen (Apple Engineer)': 'High', 'Mike & Jessica Rodriguez (Growing Family)': 'Medium', 'David Kim (Investor)': 'Low', 'Robert & Linda Williams (Luxury Downsizer)': 'High', 'Sarah Johnson': 'Medium', 'Mike Chen': 'Medium', 'Emily Davis': 'High'}
    return closing_readiness_map.get(lead_name, 'Medium')

@st.cache_data(ttl=300)
def get_trust_level(lead_name: str) -> str:
    """Get trust level for lead filtering."""
    trust_level_map = {'Sarah Chen (Apple Engineer)': 'Building', 'Mike & Jessica Rodriguez (Growing Family)': 'Established', 'David Kim (Investor)': 'Building', 'Robert & Linda Williams (Luxury Downsizer)': 'Strong', 'Sarah Johnson': 'Established', 'Mike Chen': 'Building', 'Emily Davis': 'Strong'}
    return trust_level_map.get(lead_name, 'Building')

@st.cache_data(ttl=300)
def get_last_activity(lead_name: str) -> str:
    """Get last activity time for lead filtering."""
    import random
    activities = ['2 hours ago', '1 day ago', '3 days ago', '1 week ago', '2 weeks ago']
    random.seed(hash(lead_name) % 1000)
    return random.choice(activities)

def apply_lead_filters(enhanced_lead_data: dict, health_filter: str, emotion_filter: str, closing_filter: str, trust_filter: str) -> dict:
    """
    Apply enhanced filters to lead data.

    Args:
        enhanced_lead_data: Dictionary of leads with enhanced analytics
        health_filter: Conversation health filter
        emotion_filter: Emotional state filter
        closing_filter: Closing readiness filter
        trust_filter: Trust level filter

    Returns:
        Filtered dictionary of leads
    """
    filtered_leads = {}
    for lead_name, lead_data in enhanced_lead_data.items():
        passes_health = health_filter == 'All' or lead_data['conversation_health'] == health_filter
        passes_emotion = emotion_filter == 'All' or lead_data['emotional_state'] == emotion_filter
        passes_closing = closing_filter == 'All' or lead_data['closing_readiness'] == closing_filter
        passes_trust = trust_filter == 'All' or lead_data['trust_level'] == trust_filter
        if passes_health and passes_emotion and passes_closing and passes_trust:
            filtered_leads[lead_name] = lead_data
    return filtered_leads

def _render_lead_roi_sidebar():
    """Renders a specialized AI ROI card for the selected lead in the sidebar."""
    selected_lead = st.session_state.get('selected_lead_name', '-- Select a Lead --')
    if selected_lead == '-- Select a Lead --':
        return
    lead_options = st.session_state.get('lead_options', {})
    lead_data = lead_options.get(selected_lead, {})
    lead_id = lead_data.get('lead_id', 'unknown')
    location_id = lead_data.get('location_id', 'demo_location')
    try:
        from ghl_real_estate_ai.streamlit_demo.analytics import run_async
        summary = run_async(analytics_service.get_daily_summary(location_id))
        events = run_async(analytics_service.get_events(location_id, event_type='llm_usage'))
        lead_events = [e for e in events if e.get('contact_id') == lead_id]
        lead_tokens = sum((e['data'].get('total_tokens', 0) for e in lead_events))
        lead_cost = sum((e['data'].get('cost', 0.0) for e in lead_events))
        lead_saved = sum((e['data'].get('saved_cost', 0.0) for e in lead_events))
        lead_hits = sum((1 for e in lead_events if e['data'].get('cached')))
        st.sidebar.markdown(f"\n        <div style='background: rgba(16, 185, 129, 0.1); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.3); margin-top: 1rem;'>\n            <div style='font-size: 0.75rem; color: #10B981; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;'>AI ROI Intelligence</div>\n            <div style='display: flex; justify-content: space-between; align-items: center;'>\n                <div style='font-size: 1.5rem; font-weight: 700; color: #FFFFFF;'>${lead_saved:.4f}</div>\n                <div style='background: #10B981; color: white; font-size: 0.65rem; padding: 2px 8px; border-radius: 4px;'>SAVED</div>\n            </div>\n            <div style='font-size: 0.7rem; color: #8B949E; margin-top: 8px;'>\n                <b>{lead_hits}</b> Cache Hits | <b>{lead_tokens:,}</b> Tokens\n            </div>\n        </div>\n        ", unsafe_allow_html=True)
    except Exception as e:
        pass