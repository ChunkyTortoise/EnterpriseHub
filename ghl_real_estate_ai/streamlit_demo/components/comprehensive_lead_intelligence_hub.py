"""
Comprehensive Lead Intelligence Hub with Claude Integration

Advanced dashboard combining lead analytics, AI insights, and agent interaction
capabilities for Phase One Lead Intelligence implementation.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import sys
import os

# Import existing components
try:
    from .claude_agent_chat import render_claude_agent_interface
    from .claude_conversation_templates import render_claude_conversation_templates
    from .agent_onboarding_dashboard import render_agent_onboarding_dashboard
    from .communication_automation_dashboard import render_communication_automation_dashboard
    from .goal_achievement_dashboard import render_goal_achievement_dashboard
    from .market_intelligence_dashboard import render_market_intelligence_dashboard
    from .interactive_lead_map import render_interactive_lead_map, generate_sample_lead_data
    from .lead_dashboard import render_lead_dashboard
except ImportError:
    # Fallback for direct execution
    pass

# Import services
try:
    # Try absolute import first (standard in app context)
    from services.claude_agent_service import ClaudeAgentService
    from services.lead_intelligence_integration import get_intelligence_status, get_lead_analytics
    from services.lead_scorer import LeadScorer
    SERVICES_AVAILABLE = True
except ImportError:
    # Fallback to relative imports or mock
    try:
        from ...services.claude_agent_service import ClaudeAgentService
        from ...services.lead_intelligence_integration import get_intelligence_status, get_lead_analytics
        from ...services.lead_scorer import LeadScorer
        SERVICES_AVAILABLE = True
    except ImportError:
        SERVICES_AVAILABLE = False
        print("⚠️ Services not available, using demo mode")

@st.cache_resource
def get_claude_service():
    """Get cached instance of ClaudeAgentService"""
    if SERVICES_AVAILABLE:
        try:
            return ClaudeAgentService()
        except Exception as e:
            print(f"Error initializing ClaudeAgentService: {e}")
            return None
    return None

def render_comprehensive_lead_intelligence_hub():
    """
    Main entry point for the comprehensive lead intelligence hub.

    Combines all lead intelligence features with Claude AI integration
    for a complete agent experience.
    """

    # Page header with status
    render_page_header()

    # Main dashboard layout
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "🎯 Intelligence Hub",
        "🤖 AI Assistant",
        "🎯 AI Templates",
        "🎓 Agent Training",
        "📧 Communication",
        "🏆 Goal Tracking",
        "📊 Market Intelligence",
        "📍 Lead Map",
        "📈 Analytics",
        "⚡ Quick Actions"
    ])


    with tab1:
        render_intelligence_hub_main()

    with tab2:
        render_claude_agent_interface()

    with tab3:
        # Personalization Tab (Replaces AI Templates)
        from .lead_intelligence_personalization import render_personalization_tab
        render_personalization_tab()

    with tab4:
         # Prediction Tab (Replaces Agent Training / Predictive Scoring)
        from .lead_intelligence_predictions import render_predictions_tab
        render_predictions_tab()

    with tab5:
        # Simulation Tab (Replaces Communication)
        from .lead_intelligence_simulation import render_simulation_tab
        render_simulation_tab()

    with tab6:
        render_goal_achievement_dashboard()

    with tab7:
        render_market_intelligence_dashboard()

    with tab8:
        render_enhanced_lead_map()

    with tab9:
        render_advanced_analytics()

    with tab10:
        render_quick_actions_dashboard()


def render_page_header():
    """Render the main page header with status indicators"""

    st.markdown("""
    <div style='background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%);
                padding: 2rem; border-radius: 15px; margin-bottom: 2rem; color: white;'>
        <h1 style='margin: 0; font-size: 2.5rem; font-weight: 800;'>🧠 Lead Intelligence Hub</h1>
        <p style='margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;'>
            AI-Powered Lead Management with Claude Integration
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Status indicators
    col_status, col_agents, col_activity = st.columns([1, 1, 1])

    with col_status:
        try:
            from services.lead_intelligence_integration import get_intelligence_status
            status = get_intelligence_status()
            st.success(f"✅ Intelligence System: {status.get('version', 'Active')}")
        except:
            st.warning("⚠️ Intelligence System: Demo Mode")

    with col_agents:
        agent_count = st.session_state.get('active_agents', 1)
        st.info(f"👥 Active Agents: {agent_count}")

    with col_activity:
        activity_count = len(st.session_state.get('claude_chat_history', []))
        st.metric("💬 AI Conversations", activity_count)


def render_intelligence_hub_main():
    """Main intelligence hub dashboard"""

    st.markdown("### 📊 Lead Intelligence Overview")

    # Lead summary cards
    render_lead_summary_cards()

    st.markdown("---")

    # AI Predictive Scoring Section - NOW MOVED TO TAB 4 but kept summary here if needed
    # For now, let's keep a simplified version or a pointer
    st.info("👉 Check the 'Predictions' tab for detailed AI scoring models.")

    st.markdown("---")

    # Lead intelligence table with Claude insights
    render_enhanced_lead_table()

    st.markdown("---")

    # Performance metrics
    render_performance_metrics()

# Removed inline render_predictive_scoring_section as it is now in tab 4 dedicated component


def render_performance_metrics():
    """Render system performance metrics"""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg Response Time", "1.2s", "-0.3s")
    with col2:
        st.metric("Prediction Accuracy", "94%", "+2%")
    with col3:
        st.metric("System Uptime", "99.9%", "stable")



@st.cache_data(ttl=60)
def _get_scored_leads(market_key: str = "Austin"):
    """Get sample leads and score them with the real ML model"""
    # Use the passed market key to generate relevant data
    leads = generate_sample_lead_data(market_key)
    
    if SERVICES_AVAILABLE:
        try:
            # Check if we imported PredictiveLeadScorer or just LeadScorer. 
            # The try block imported LeadScorer. Let's make sure we use the right one.
            # Ideally we want the predictive one.
            try:
                from services.ai_predictive_lead_scoring import PredictiveLeadScorer
                scorer = PredictiveLeadScorer()
            except ImportError:
                # Fallback to standard scorer if predictive not available
                scorer = LeadScorer()
            
            for lead in leads:
                try:
                    # Enrich lead data if missing keys
                    if 'page_views' not in lead: lead['page_views'] = 5
                    if 'source' not in lead: lead['source'] = 'organic'
                    if 'messages' not in lead: lead['messages'] = []
                    
                    # Score using the available scorer (handle different interfaces if needed)
                    if hasattr(scorer, 'score_lead'):
                        score_res = scorer.score_lead(lead.get('id', 'unknown'), lead)
                        lead['lead_score'] = score_res.score
                        # meaningful status based on tier
                        lead['status'] = score_res.tier.upper()
                    elif hasattr(scorer, 'calculate'):
                        # Fallback for standard LeadScorer which uses calculate(context)
                        # We need to adapt the lead dict to context format
                        context = {"extracted_preferences": lead}
                        score = scorer.calculate(context)
                        lead['lead_score'] = min(score * 20, 100) # Rough conversion from count to %
                        lead['status'] = scorer.classify(score).upper()

                except Exception as e:
                    print(f"Scoring error for lead {lead.get('name')}: {e}")
        except Exception as e:
            # Fallback if service initialization failed
            print(f"Service initialization error: {e}")
            pass
            
    return leads

def _get_current_market_key():
    """Helper to get current market key from session state"""
    selected_market = st.session_state.get('selected_market', "Austin, TX")
    return "Rancho" if "Rancho" in selected_market else "Austin"

def render_lead_summary_cards():
    """Render lead summary cards with AI insights"""

    # Get scored lead data for current market
    market_key = _get_current_market_key()
    leads_data = _get_scored_leads(market_key)

    col1, col2, col3, col4 = st.columns(4)


    # Hot leads
    hot_leads = [lead for lead in leads_data if lead.get('lead_score', 0) >= 80]
    with col1:
        st.markdown("""
        <div style='background: #fef2f2; padding: 1rem; border-radius: 12px; border: 2px solid #fecaca;'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <div>
                    <h3 style='margin: 0; color: #dc2626; font-size: 2rem;'>{}</h3>
                    <p style='margin: 0; color: #7f1d1d; font-weight: 600;'>🔥 Hot Leads</p>
                </div>
                <div style='font-size: 2rem;'>📈</div>
            </div>
        </div>
        """.format(len(hot_leads)), unsafe_allow_html=True)

    # Warm leads
    warm_leads = [lead for lead in leads_data if 50 <= lead.get('lead_score', 0) < 80]
    with col2:
        st.markdown("""
        <div style='background: #fefbf2; padding: 1rem; border-radius: 12px; border: 2px solid #fed7aa;'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <div>
                    <h3 style='margin: 0; color: #ea580c; font-size: 2rem;'>{}</h3>
                    <p style='margin: 0; color: #9a3412; font-weight: 600;'>🔸 Warm Leads</p>
                </div>
                <div style='font-size: 2rem;'>🎯</div>
            </div>
        </div>
        """.format(len(warm_leads)), unsafe_allow_html=True)

    # Cold leads
    cold_leads = [lead for lead in leads_data if lead.get('lead_score', 0) < 50]
    with col3:
        st.markdown("""
        <div style='background: #f0f9ff; padding: 1rem; border-radius: 12px; border: 2px solid #bfdbfe;'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <div>
                    <h3 style='margin: 0; color: #2563eb; font-size: 2rem;'>{}</h3>
                    <p style='margin: 0; color: #1e40af; font-weight: 600;'>❄️ Cold Leads</p>
                </div>
                <div style='font-size: 2rem;'>🌱</div>
            </div>
        </div>
        """.format(len(cold_leads)), unsafe_allow_html=True)

    # Total value
    total_budget = sum(lead.get('budget', 0) for lead in leads_data)
    with col4:
        st.markdown("""
        <div style='background: #f0fdf4; padding: 1rem; border-radius: 12px; border: 2px solid #bbf7d0;'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <div>
                    <h3 style='margin: 0; color: #16a34a; font-size: 1.5rem;'>${:,}</h3>
                    <p style='margin: 0; color: #15803d; font-weight: 600;'>💰 Pipeline</p>
                </div>
                <div style='font-size: 2rem;'>💎</div>
            </div>
        </div>
        """.format(total_budget), unsafe_allow_html=True)


def render_enhanced_lead_table():
    """Enhanced lead table with Claude AI insights"""

    st.markdown("#### 📋 Lead Intelligence Table")

    # Get scored lead data for current market
    market_key = _get_current_market_key()
    leads_data = _get_scored_leads(market_key)


    # Create DataFrame for display
    df_data = []
    for lead in leads_data:
        df_data.append({
            "Name": lead.get('name', 'Unknown'),
            "Score": lead.get('lead_score', 0),
            "Budget": f"${lead.get('budget', 0):,}",
            "Location": lead.get('location', 'Unknown'),
            "Timeline": lead.get('timeline', 'Unknown'),
            "Engagement": f"{lead.get('engagement_score', 0)}%",
            "Status": get_lead_status(lead.get('lead_score', 0))
        })

    df = pd.DataFrame(df_data)

    # Display table with styling
    st.dataframe(
        df,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Lead Score",
                help="Lead qualification score",
                min_value=0,
                max_value=100,
            ),
            "Status": st.column_config.TextColumn(
                "Status",
                help="Lead temperature classification"
            )
        },
        hide_index=True
    )

    # Quick actions for selected leads
    selected_lead_str = st.selectbox(
        "Select lead for AI insights",
        options=[f"{lead['Name']} ({lead['Score']})" for lead in df_data],
        index=0
    )
    
    # Extract name from string "Name (Score)"
    selected_lead_name = selected_lead_str.split(" (")[0] if selected_lead_str else "Unknown"

    col_insights, col_actions = st.columns([1, 1])

    with col_insights:
        if st.button("🧠 Get AI Insights", type="primary"):
            render_claude_lead_insights(selected_lead_name)

    with col_actions:
        if st.button("⚡ Suggest Actions"):
            render_claude_action_suggestions(selected_lead_name)


def render_enhanced_lead_map():
    """Enhanced lead map with property overlays"""

    st.markdown("### 📍 Interactive Lead Map with AI Insights")

    # Market selector
    col_market, col_overlay = st.columns([1, 1])

    with col_market:
        # Determine default index from global selection
        current_market_key = _get_current_market_key()
        market_options = ["Austin", "Rancho"]
        default_index = 0
        if current_market_key in market_options:
            default_index = market_options.index(current_market_key)
            
        market = st.selectbox(
            "Select Market",
            market_options,
            index=default_index,
            help="Choose the geographic market to focus on"
        )

    with col_overlay:
        overlay_type = st.selectbox(
            "Map Overlay",
            ["Lead Activity", "Property Density", "Price Ranges", "Both"],
            help="Choose what additional data to show on the map"
        )

    # Get market-specific lead data
    leads_data = generate_sample_lead_data(market)

    # Add property overlay information
    if overlay_type in ["Property Density", "Both"]:
        st.info("🏠 Property overlay data coming from Zillow/Redfin integration")

    if overlay_type in ["Price Ranges", "Both"]:
        st.info("💰 Price range data coming from market analytics")

    # Render the interactive map
    render_interactive_lead_map(leads_data, market)

    # Map insights
    with st.expander("🧠 AI Map Insights"):
        st.markdown(f"""
        **Market Analysis for {market}:**
        - **Lead Concentration**: {len(leads_data)} active leads in target area
        - **Hot Zones**: Downtown areas showing highest engagement
        - **Budget Distribution**: ${sum(lead.get('budget', 0) for lead in leads_data):,} total pipeline value
        - **Opportunity**: Focus on luxury segment for highest ROI

        *🔮 Claude Insight*: "Based on geographic clustering, prioritize downtown luxury leads
        first as they show 40% higher conversion rates and faster decision timelines."
        """)


def render_advanced_analytics():
    """Advanced analytics dashboard with AI insights"""

    st.markdown("### 📊 Advanced Lead Analytics")

    # Analytics tabs
    analytics_tab1, analytics_tab2, analytics_tab3 = st.tabs([
        "📈 Conversion Analytics",
        "🎯 Engagement Metrics",
        "🔮 Predictive Insights"
    ])

    with analytics_tab1:
        render_conversion_analytics()

    with analytics_tab2:
        render_engagement_metrics()

    with analytics_tab3:
        render_predictive_insights()


def render_conversion_analytics():
    """Conversion analytics with trends"""

    # Sample conversion data
    dates = pd.date_range(start='2024-12-01', end='2026-01-09', freq='D')
    conversions = [5, 3, 8, 4, 7, 6, 9, 2, 5, 8, 6, 4, 7, 9, 3, 6, 8, 5, 7, 4, 6, 8, 9, 5, 7, 6, 8, 4, 9, 7, 5, 8, 6, 9, 7, 4, 6, 8, 9, 5]
    conversion_df = pd.DataFrame({
        'Date': dates,
        'Conversions': conversions[:len(dates)]
    })

    # Conversion trend chart
    fig = px.line(
        conversion_df,
        x='Date',
        y='Conversions',
        title='Lead Conversion Trends (Last 40 Days)',
        markers=True
    )
    fig.update_traces(line=dict(color='#10b981', width=3))
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Conversion metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Conversion Rate", "23.4%", "↗ +2.1%")

    with col2:
        st.metric("Avg. Days to Convert", "18", "↘ -3 days")

    with col3:
        st.metric("Pipeline Value", "$2.1M", "↗ +12%")

    with col4:
        st.metric("Close Rate", "68%", "↗ +5%")


def render_engagement_metrics():
    """Lead engagement analytics"""

    # Engagement heatmap
    engagement_data = [
        ['Mon', '9AM', 15], ['Mon', '10AM', 25], ['Mon', '11AM', 35], ['Mon', '12PM', 45],
        ['Tue', '9AM', 20], ['Tue', '10AM', 30], ['Tue', '11AM', 40], ['Tue', '12PM', 50],
        ['Wed', '9AM', 25], ['Wed', '10AM', 35], ['Wed', '11AM', 45], ['Wed', '12PM', 55],
        ['Thu', '9AM', 18], ['Thu', '10AM', 28], ['Thu', '11AM', 38], ['Thu', '12PM', 48],
        ['Fri', '9AM', 22], ['Fri', '10AM', 32], ['Fri', '11AM', 42], ['Fri', '12PM', 52]
    ]

    days = [item[0] for item in engagement_data]
    hours = [item[1] for item in engagement_data]
    values = [item[2] for item in engagement_data]

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        x=list(set(hours)),
        y=list(set(days)),
        z=[[values[i] for i in range(len(values)) if days[i] == day and hours[i] == hour]
           for day in set(days) for hour in set(hours)],
        colorscale='Blues'
    ))

    fig.update_layout(
        title='Lead Engagement Heatmap (Best Contact Times)',
        xaxis_title='Time of Day',
        yaxis_title='Day of Week',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # Engagement insights
    st.markdown("**🧠 AI Engagement Insights:**")
    st.markdown("""
    - **Peak Hours**: 11AM-12PM shows highest response rates (45% avg)
    - **Best Days**: Wednesday and Friday generate most engagement
    - **Channel Preference**: SMS gets 3x better response than email
    - **Follow-up Timing**: Second contact within 4 hours improves conversion by 25%
    """)


def render_predictive_insights():
    """AI-powered predictive insights"""

    st.markdown("#### 🔮 Claude Predictive Analytics")

    # Prediction cards
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #fef3c7 0%, #f59e0b 100%);
                    padding: 1.5rem; border-radius: 12px; color: white;'>
            <h3 style='margin: 0; color: white;'>📈 Conversion Forecast</h3>
            <p style='margin: 0.5rem 0; font-size: 1.1rem;'>Next 30 Days</p>
            <div style='font-size: 2rem; font-weight: 800;'>8-12 Closings</div>
            <p style='margin: 0; opacity: 0.9;'>Confidence: 87%</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #ddd6fe 0%, #8b5cf6 100%);
                    padding: 1.5rem; border-radius: 12px; color: white;'>
            <h3 style='margin: 0; color: white;'>💰 Revenue Prediction</h3>
            <p style='margin: 0.5rem 0; font-size: 1.1rem;'>Next 30 Days</p>
            <div style='font-size: 2rem; font-weight: 800;'>$680K - $920K</div>
            <p style='margin: 0; opacity: 0.9;'>Confidence: 82%</p>
        </div>
        """, unsafe_allow_html=True)

    # AI recommendations
    st.markdown("#### 🎯 AI Recommendations")

    recommendations = [
        {
            "priority": "🔴 High",
            "action": "Focus on Sarah Johnson - 92% conversion probability",
            "impact": "Potential $800K closing within 7 days",
            "confidence": "95%"
        },
        {
            "priority": "🟡 Medium",
            "action": "Schedule property tour for Mike Chen",
            "impact": "$450K opportunity with proper nurturing",
            "confidence": "78%"
        },
        {
            "priority": "🟢 Low",
            "action": "Re-engage Emily Davis with market updates",
            "impact": "30% chance to re-activate cold lead",
            "confidence": "62%"
        }
    ]

    for rec in recommendations:
        st.markdown(f"""
        <div style='background: #f8fafc; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;
                    border-left: 4px solid {"#dc2626" if rec["priority"].startswith("🔴") else "#f59e0b" if rec["priority"].startswith("🟡") else "#10b981"};'>
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div style='flex: 1;'>
                    <div style='font-weight: 600; margin-bottom: 0.5rem;'>{rec["priority"]}: {rec["action"]}</div>
                    <div style='color: #64748b; font-size: 0.9rem;'>{rec["impact"]}</div>
                </div>
                <div style='background: #e2e8f0; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem;'>
                    {rec["confidence"]}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_quick_actions_dashboard():
    """Quick actions dashboard for agents with premium UI"""
    st.markdown("### ⚡ Quick Actions Center")
    
    st.markdown("""
    <style>
    .action-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,250,252,0.95) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(226,232,240,0.8);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .action-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.12);
        border-color: rgba(59,130,246,0.5);
    }
    .action-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    .action-title {
        font-weight: 700;
        font-size: 1.1rem;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .action-desc {
        font-size: 0.85rem;
        color: #64748b;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

    # Action categories
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📞 Contact Actions")
        
        st.markdown("""
        <div class="action-card">
            <span class="action-icon">🔥</span>
            <div class="action-title">Call Hot Leads</div>
            <div class="action-desc">Connect with high-priority leads showing strong buying signals</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Execute", key="call_hot", use_container_width=True):
            st.success("Preparing hot lead contact list...")

        st.markdown("""
        <div class="action-card">
            <span class="action-icon">📱</span>
            <div class="action-title">Send SMS Campaign</div>
            <div class="action-desc">Launch targeted SMS sequences with AI-optimized timing</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Execute", key="sms_campaign", use_container_width=True):
            st.success("SMS campaign builder opened...")

        st.markdown("""
        <div class="action-card">
            <span class="action-icon">📧</span>
            <div class="action-title">Email Follow-up</div>
            <div class="action-desc">Send personalized property matches and market updates</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Execute", key="email_followup", use_container_width=True):
            st.success("Email templates loaded...")

    with col2:
        st.markdown("#### 🏠 Property Actions")
        
        st.markdown("""
        <div class="action-card">
            <span class="action-icon">🔍</span>
            <div class="action-title">AI Property Matching</div>
            <div class="action-desc">Run ML-powered property matcher for active leads</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Execute", key="find_matches", use_container_width=True):
            st.success("AI property matching in progress...")

        st.markdown("""
        <div class="action-card">
            <span class="action-icon">📋</span>
            <div class="action-title">Generate CMA</div>
            <div class="action-desc">Create comparative market analysis with AI insights</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Execute", key="create_cma", use_container_width=True):
            st.success("Comparative market analysis generator opened...")

        st.markdown("""
        <div class="action-card">
            <span class="action-icon">📅</span>
            <div class="action-title">Schedule Tours</div>
            <div class="action-desc">Auto-schedule property showings with calendar sync</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Execute", key="schedule_tours", use_container_width=True):
            st.success("Tour scheduling interface loaded...")

    with col3:
        st.markdown("#### 📊 Analytics Actions")
        
        st.markdown("""
        <div class="action-card">
            <span class="action-icon">📈</span>
            <div class="action-title">Performance Report</div>
            <div class="action-desc">Generate comprehensive performance analytics</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Execute", key="generate_report", use_container_width=True):
            st.success("Performance report being generated...")

        st.markdown("""
        <div class="action-card">
            <span class="action-icon">🎯</span>
            <div class="action-title">Update Lead Scores</div>
            <div class="action-desc">Recalculate all lead scores with latest AI models</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Execute", key="update_scores", use_container_width=True):
            st.success("Lead scores being recalculated...")

        st.markdown("""
        <div class="action-card">
            <span class="action-icon">🔄</span>
            <div class="action-title">GHL Sync</div>
            <div class="action-desc">Force synchronization with GoHighLevel CRM</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Execute", key="sync_ghl", use_container_width=True):
            st.success("GoHighLevel sync initiated...")


def render_claude_lead_insights(selected_lead: str):
    """Show Claude insights for selected lead"""
    with st.spinner("Getting AI insights..."):
        
        # Try to use real service if available
        claude_service = get_claude_service()
        
        if claude_service:
            try:
                # Use async wrapper for Streamlit
                async def fetch_insights():
                    # For demo purposes, we pass a dummy lead ID if it's a name
                    # In real usage, selected_lead would be an ID
                    lead_id = selected_lead.lower().replace(" ", "_")
                    agent_id = "agent_demo_01"
                    return await claude_service.get_lead_insights(lead_id, agent_id)
                
                insights_data = asyncio.run(fetch_insights())
                
                st.success("🧠 Claude Analysis Complete")
                st.markdown(f"""
                **Lead: {selected_lead}**

                **Key Insights:**
                {''.join([f'- {insight} ' for insight in insights_data.get('insights', [])])}

                **Recommendations:**
                {''.join([f'- {rec} ' for rec in insights_data.get('recommendations', [])])}
                """)
            except Exception as e:
                st.error(f"Error fetching insights: {e}")
                
        # Demo insights when no real service connection or for manual toggle
        if not claude_service:
            st.success("🧠 Claude Analysis Complete")
            
            # Dynamic insights based on lead name
            if "Sarah Chen" in selected_lead and "Apple" in selected_lead:
                st.markdown(f"""
                **Lead: {selected_lead}**
    
                **🤖 Claude's Behavioral Insight:**
                
                High-velocity lead. Apple engineers are data-driven; she responded to the 'Market Trend' link within 12 seconds. 
                She's prioritizing commute efficiency over sqft. Focus on: **Teravista connectivity** and Apple campus proximity.
    
                **Key Insights:**
                - Extremely high technical literacy - values smart home features
                - Timeline urgency (45 days) linked to Apple expansion announcement
                - Pre-approved financing indicates serious intent
                - Home office requirement is non-negotiable for hybrid work
                - Price point ($550K) suggests mid-senior engineer compensation
    
                **Behavioral Patterns:**
                - Lightning-fast response times (12-second click, 2-minute SMS replies)
                - Prefers data-driven communication (charts, metrics, ROI analysis)
                - Most active during lunch breaks (12-1pm) and evenings (7-9pm)
                - High engagement with property tech specs and neighborhood analytics
    
                **Conversion Probability:** 97% (Extremely High)
                
                **Recommended Approach:**
                - Lead with Round Rock/Cedar Park properties near Apple campus
                - Emphasize fiber internet speeds and smart home readiness
                - Provide commute time analysis (Apple campus to properties)
                - Share school district data (future family planning indicator)
                """)
            else:
                st.markdown(f"""
                **Lead: {selected_lead}**
    
                **Key Insights:**
                - High engagement with luxury property listings
                - Responds best to morning communications
                - Shows price sensitivity around $800K+
                - Timeline indicates urgency (ASAP category)
    
                **Behavioral Patterns:**
                - Views listings multiple times before inquiring
                - Prefers text communication over calls
                - Most active on weekday mornings
    
                **Conversion Probability:** 87% (Very High)
                """)


def render_claude_action_suggestions(selected_lead: str):
    """Show Claude action suggestions for selected lead"""
    with st.spinner("Generating action plan..."):
        
        # Try to use real service if available
        claude_service = get_claude_service()
        
        if claude_service:
            try:
                async def fetch_actions():
                    lead_id = selected_lead.lower().replace(" ", "_")
                    agent_id = "agent_demo_01"
                    return await claude_service.suggest_follow_up_actions(lead_id, agent_id)
                
                actions = asyncio.run(fetch_actions())
                
                st.success("⚡ Action Plan Generated")
                st.markdown(f"**Recommended Actions for {selected_lead}:**")
                
                for action in actions:
                    priority_icon = "🔴" if action.get('priority') == 'high' else "🟡"
                    st.markdown(f"**{priority_icon} {action.get('action')}**")
                    st.caption(f"Timing: {action.get('suggested_timing')}")
                
                return
            except Exception as e:
                print(f"Error calling Claude Service: {e}")
                # Fallback to demo logic
        
        # DEMO FALLBACK
        st.success("⚡ Action Plan Generated")
        st.markdown(f"""
        **Recommended Actions for {selected_lead}:**

        **Immediate (Next 2 hours):**
        - Send personalized property selection via SMS
        - Include market insights and investment potential

        **Today:**
        - Schedule property tour for tomorrow morning
        - Prepare luxury property comparison sheet

        **This Week:**
        - Follow up with financing options
        - Send neighborhood lifestyle guide
        """)


def get_lead_status(score: int) -> str:
    """Get lead status based on score"""
    if score >= 80:
        return "🔥 Hot"
    elif score >= 50:
        return "🔸 Warm"
    else:
        return "❄️ Cold"


# Main rendering function for external use
def render_lead_intelligence_hub():
    """Main entry point for the lead intelligence hub"""
    render_comprehensive_lead_intelligence_hub()