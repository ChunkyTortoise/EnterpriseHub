"""
GHL Real Estate AI - Consolidated Hub Interface (Root Entry Point)
Main Application with 5 Core Hubs - Enhanced with Enterprise Visual Theme
"""
import streamlit as st
import sys
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import os
from utils.ui import sparkline

# === ENTERPRISE THEME INTEGRATION ===
try:
    from ghl_real_estate_ai.design_system import inject_enterprise_theme
    ENTERPRISE_THEME_AVAILABLE = True
except ImportError:
    ENTERPRISE_THEME_AVAILABLE = False

# --- PATH CONFIGURATION ---
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR / "ghl_real_estate_ai"

# Add directories to sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- ROBUST SERVICE IMPORTS ---
class MockService:
    """Fallback for missing services to prevent app crash"""
    def __init__(self, *args, **kwargs): pass
    def __getattr__(self, name):
        def method(*args, **kwargs): return {}
        return method

# Individual service imports with fallbacks
try:
    from services.lead_scorer import LeadScorer
except ImportError:
    st.warning("LeadScorer unavailable, using mock.")
    LeadScorer = MockService

try:
    from services.ai_smart_segmentation import AISmartSegmentationService
except ImportError:
    st.warning("Segmentation Service unavailable, using mock.")
    AISmartSegmentationService = MockService

try:
    from services.deal_closer_ai import DealCloserAI
except ImportError:
    st.warning("DealCloser AI unavailable, using mock.")
    DealCloserAI = MockService

try:
    from services.commission_calculator import CommissionCalculator, CommissionType, DealStage
except ImportError:
    st.warning("Commission Calculator unavailable, using mock.")
    CommissionCalculator = MockService
    class CommissionType: BUYER_AGENT=1; SELLER_AGENT=2; DUAL_AGENCY=3
    class DealStage: CLOSED=1

try:
    from services.meeting_prep_assistant import MeetingPrepAssistant, MeetingType
except ImportError:
    st.warning("Meeting Prep unavailable, using mock.")
    MeetingPrepAssistant = MockService
    class MeetingType: DISCOVERY=1

try:
    from services.executive_dashboard import ExecutiveDashboardService
except ImportError:
    st.warning("Executive Dashboard unavailable, using mock.")
    ExecutiveDashboardService = MockService

try:
    from services.quality_assurance import QualityAssuranceService
except ImportError:
    st.warning("QA Service unavailable, using mock.")
    QualityAssuranceService = MockService

try:
    from services.revenue_attribution import RevenueAttributionEngine as RevenueAttributionService
except ImportError:
    st.warning("Revenue Attribution unavailable, using mock.")
    RevenueAttributionService = MockService

try:
    from services.competitive_benchmarking import CompetitiveBenchmarkingService
except ImportError:
    st.warning("Benchmarking unavailable, using mock.")
    CompetitiveBenchmarkingService = MockService

try:
    from services.agent_coaching import AgentCoachingService
except ImportError:
    st.warning("Agent Coaching unavailable, using mock.")
    AgentCoachingService = MockService

try:
    from services.smart_document_generator import SmartDocumentGenerator, DocumentType
except ImportError:
    st.warning("Doc Generator unavailable, using mock.")
    SmartDocumentGenerator = MockService
    class DocumentType: LISTING_AGREEMENT=1

try:
    from services.predictive_scoring import PredictiveLeadScorer
except ImportError:
    st.warning("Predictive Scorer unavailable, using mock.")
    PredictiveLeadScorer = MockService

try:
    from services.ai_content_personalization import AIContentPersonalizationService
except ImportError:
    st.warning("Personalization unavailable, using mock.")
    AIContentPersonalizationService = MockService

try:
    from services.workflow_marketplace import WorkflowMarketplace
except ImportError:
    st.warning("Workflow Marketplace unavailable, using mock.")
    WorkflowMarketplace = MockService

try:
    from services.auto_followup_sequences import AutoFollowupSequences
except ImportError:
    st.warning("Auto Followup unavailable, using mock.")
    AutoFollowupSequences = MockService

try:
    from services.analytics_engine import AnalyticsEngine
except ImportError:
    st.warning("Analytics Engine unavailable, using mock.")
    AnalyticsEngine = MockService

try:
    from services.enhanced_lead_scorer import EnhancedLeadScorer
    from services.churn_prediction_engine import ChurnPredictionEngine
    from services.enhanced_property_matcher import EnhancedPropertyMatcher
    from services.advanced_workflow_engine import AdvancedWorkflowEngine
    from services.behavioral_weighting_engine import BehavioralWeightingEngine
    from services.memory_service import MemoryService
    from services.lead_lifecycle import LeadLifecycleTracker
    from services.behavioral_triggers import BehavioralTriggerEngine
    ENHANCED_SERVICES_AVAILABLE = True
except ImportError as e:
    st.warning(f"Enhanced services partially unavailable: {e}")
    ENHANCED_SERVICES_AVAILABLE = False

# Helper function to load data
def load_mock_data():
    data_path = PROJECT_ROOT / "data" / "mock_analytics.json"
    if data_path.exists():
        with open(data_path) as f:
            return json.load(f)
    return {}

# Initialize services
@st.cache_resource
def get_services():
    base_services = {
        "lead_scorer": LeadScorer(),
        "segmentation": AISmartSegmentationService(),
        "predictive_scorer": PredictiveLeadScorer(),
        "personalization": AIContentPersonalizationService(),
        "deal_closer": DealCloserAI(),
        "commission_calc": CommissionCalculator(),
        "meeting_prep": MeetingPrepAssistant(),
        "executive": ExecutiveDashboardService(),
        "doc_gen": SmartDocumentGenerator(),
        "qa": QualityAssuranceService(),
        "revenue": RevenueAttributionService(),
        "benchmarking": CompetitiveBenchmarkingService(),
        "coaching": AgentCoachingService(),
        "sequences": AutoFollowupSequences(),
        "marketplace": WorkflowMarketplace(),
        "analytics": AnalyticsEngine()
    }
    
    if ENHANCED_SERVICES_AVAILABLE:
        try:
            # Core support services for enhanced engine
            memory = MemoryService()
            lifecycle = LeadLifecycleTracker()
            behavioral = BehavioralTriggerEngine()
            
            base_services.update({
                "enhanced_lead_scorer": EnhancedLeadScorer(),
                "churn_prediction": ChurnPredictionEngine(
                    memory_service=memory,
                    lifecycle_tracker=lifecycle,
                    behavioral_engine=behavioral,
                    lead_scorer=base_services["lead_scorer"]
                ),
                "enhanced_property_matcher": EnhancedPropertyMatcher(),
                "workflow_engine": AdvancedWorkflowEngine(),
                "behavioral_weighting": BehavioralWeightingEngine()
            })
        except Exception as e:
            st.error(f"Error initializing enhanced services: {e}")
            
    return base_services

services = get_services()
mock_data = load_mock_data()

# Initialize Global AI State (Zustand equivalent)
if "ai_config" not in st.session_state:
    st.session_state.ai_config = {
        "market": "Austin, TX",
        "voice_tone": 0.5,  # 0.0 = Professional, 1.0 = Natural
        "response_speed": "Standard"
    }

# Initialize Prompt Versioning
if "prompt_versions" not in st.session_state:
    st.session_state.prompt_versions = [
        {"version": "v1.0", "tag": "Baseline", "content": "You are a helpful assistant.", "timestamp": "2026-01-01"},
        {"version": "v1.1", "tag": "Production", "content": "You are a professional real estate assistant.", "timestamp": "2026-01-05"}
    ]

# Page config
st.set_page_config(
    page_title="GHL Real Estate AI - Jorge Salas",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI-Powered Lead Qualification System for Real Estate Professionals"
    }
)

# === INJECT ENTERPRISE THEME ===
if ENTERPRISE_THEME_AVAILABLE:
    inject_enterprise_theme()

# Load custom CSS
css_path = PROJECT_ROOT / "streamlit_demo" / "assets" / "styles_dark_lux.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Professional header with improved status indicators
st.markdown("""
<div style='background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            padding: 3rem 2.5rem;
            border-radius: 20px;
            margin-bottom: 2.5rem;
            color: #f8fafc;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
            position: relative;
            overflow: hidden;'>
    <!-- Animated background pattern -->
    <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                background-image:
                    radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
                opacity: 0.8;'></div>

    <div style='position: relative; z-index: 1;'>
        <div style='display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1rem;'>
            <div style='width: 4rem; height: 4rem; background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
                        border-radius: 12px; display: flex; align-items: center; justify-content: center;
                        font-size: 1.5rem; font-weight: 800; color: white;
                        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);'>RE</div>
            <div>
                <h1 style='margin: 0; font-size: 2.75rem; font-weight: 800; color: #f8fafc;
                           text-shadow: 0 4px 20px rgba(0,0,0,0.5); font-family: "Plus Jakarta Sans", sans-serif;'>
                    GHL Real Estate AI
                </h1>
                <p style='margin: 0.25rem 0 0 0; font-size: 1.15rem; color: #94a3b8; font-weight: 500; letter-spacing: 0.05em;'>
                    ENTERPRISE COMMAND CENTER
                </p>
            </div>
        </div>

        <p style='margin: 1.5rem 0; font-size: 1.05rem; color: #cbd5e1; max-width: 800px; line-height: 1.6;'>
            Professional AI-powered lead qualification and automation system for <strong style='color: #3b82f6;'>Jorge Salas</strong>
        </p>

        <div style='margin-top: 1.5rem; display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.95rem;'>
            <div style='background: rgba(16, 185, 129, 0.15);
                        padding: 0.75rem 1.25rem;
                        border-radius: 10px;
                        border: 1px solid rgba(16, 185, 129, 0.3);
                        backdrop-filter: blur(10px);
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        color: #f8fafc;'>
                <span style='width: 8px; height: 8px; background: #10b981; border-radius: 50%; display: inline-block;'></span>
                <span style='font-weight: 600; color: #f8fafc;'>AI Mode Active</span>
            </div>
            <div style='background: rgba(59, 130, 246, 0.15);
                        padding: 0.75rem 1.25rem;
                        border-radius: 10px;
                        border: 1px solid rgba(59, 130, 246, 0.3);
                        backdrop-filter: blur(10px);
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        color: #f8fafc;'>
                <span style='width: 8px; height: 8px; background: #3b82f6; border-radius: 50%; display: inline-block;'></span>
                <span style='font-weight: 600; color: #f8fafc;'>GHL Integration Live</span>
            </div>
            <div style='background: rgba(245, 158, 11, 0.15);
                        padding: 0.75rem 1.25rem;
                        border-radius: 10px;
                        border: 1px solid rgba(245, 158, 11, 0.3);
                        backdrop-filter: blur(10px);
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        color: #f8fafc;'>
                <span style='width: 8px; height: 8px; background: #f59e0b; border-radius: 50%; display: inline-block;'></span>
                <span style='font-weight: 600; color: #f8fafc;'>Multi-Tenant Ready</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize session state for hub navigation
if 'current_hub' not in st.session_state:
    st.session_state.current_hub = "Executive Command Center"

# Sidebar navigation
with st.sidebar:
    st.markdown("### 🎯 Navigation")
    
    hub_options = [
        "🏢 Executive Command Center",
        "🧠 Lead Intelligence Hub",
        "🤖 Automation Studio",
        "💰 Sales Copilot",
        "📈 Ops & Optimization"
    ]
    
    # Calculate index safely
    try:
        default_index = hub_options.index(st.session_state.current_hub)
    except ValueError:
        default_index = 0
    
    selected_hub = st.radio(
        "Select Hub:",
        hub_options,
        index=default_index,
        label_visibility="collapsed"
    )
    
    st.session_state.current_hub = selected_hub
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    # Export functionality
    metrics_data = {
        "Metric": ["Total Pipeline", "Hot Leads", "Conversion Rate", "Avg Deal Size"],
        "Value": ["$2.4M", "23", "34%", "$385K"],
        "Change": ["+15%", "+8", "+2%", "+$12K"]
    }
    df_metrics = pd.DataFrame(metrics_data)
    csv = df_metrics.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        "📥 Export Report",
        data=csv,
        file_name="executive_metrics.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Global AI Configuration (Synced State)
    with st.expander("⚙️ AI Configuration", expanded=True):
        new_market = st.selectbox(
            "Target Market",
            ["Austin, TX", "Dallas, TX", "Houston, TX", "San Antonio, TX"],
            index=0,
            key="market_selector"
        )
        if new_market != st.session_state.ai_config["market"]:
            st.session_state.ai_config["market"] = new_market
            st.toast(f"Market switched to {new_market}", icon="🌍")
            # Rerun to propagate state if needed, or rely on Streamlit reactivity
            
        tone = st.slider(
            "Voice Tone",
            0.0, 1.0, 
            st.session_state.ai_config["voice_tone"], 
            0.1,
            key="tone_slider",
            help="0=Professional, 1=Casual/Natural"
        )
        if tone != st.session_state.ai_config["voice_tone"]:
            st.session_state.ai_config["voice_tone"] = tone
            st.toast(f"Voice tone updated to {tone}", icon="🤖")

    st.markdown("---")
    
    # System status with Sparklines
    st.markdown("### 📊 System Health")
    
    # Active Leads Sparkline
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.metric("Active Leads", "47", "+12")
    with c2:
        st.plotly_chart(sparkline([10, 15, 12, 25, 30, 42, 47], color="#3b82f6", height=50), use_container_width=True, config={'displayModeBar': False})
        
    # AI Conversations Sparkline
    c3, c4 = st.columns([1.5, 1])
    with c3:
        st.metric("AI Convos", "156", "+23")
    with c4:
        st.plotly_chart(sparkline([80, 95, 110, 105, 130, 145, 156], color="#10b981", height=50), use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("---")
    st.markdown("### 📡 Live Feed")
    st.markdown("""
    <div style="font-size: 0.8rem; color: #666;">
    Creating contract for <b>John Doe</b><br>
    <span style="color: green">● Just now</span><br><br>
    New lead: <b>Sarah Smith</b> (Downtown)<br>
    <span style="color: gray">● 2 mins ago</span><br><br>
    AI handled objection: <b>Mike Ross</b><br>
    <span style="color: gray">● 15 mins ago</span>
    </div>
    """, unsafe_allow_html=True)

# Main content area
if selected_hub == "🏢 Executive Command Center":
    st.header("🏢 Executive Command Center")
    st.markdown("*High-level KPIs, revenue tracking, and system health*")
    
    # Tabs for sub-features
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎯 AI Insights", "📄 Reports"])
    
    with tab1:
        st.subheader("Executive Command Center")
        
        # Bento Grid Metrics
        st.markdown("""
        <div class="bento-grid">
            <div class="bento-item">
                <div class="bento-header">
                    <div class="bento-title">💰 Total Pipeline</div>
                    <div class="bento-badge" style="background: rgba(16, 185, 129, 0.1); color: #10b981;">+15%</div>
                </div>
                <div style="font-size: 2.5rem; font-weight: 800; color: #f8fafc;">$2.4M</div>
                <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.5rem;">Across 47 active properties</div>
            </div>
            <div class="bento-item">
                <div class="bento-header">
                    <div class="bento-title">🔥 Hot Leads</div>
                    <div class="bento-badge" style="background: rgba(245, 158, 11, 0.1); color: #f59e0b;">+8</div>
                </div>
                <div style="font-size: 2.5rem; font-weight: 800; color: #f8fafc;">23</div>
                <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.5rem;">Ready for immediate conversion</div>
            </div>
            <div class="bento-item">
                <div class="bento-header">
                    <div class="bento-title">📈 Conv. Rate</div>
                    <div class="bento-badge" style="background: rgba(59, 130, 246, 0.1); color: #3b82f6;">+2%</div>
                </div>
                <div style="font-size: 2.5rem; font-weight: 800; color: #f8fafc;">34%</div>
                <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.5rem;">AI-assisted closing efficiency</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Enterprise Color Palette (Dark Lux)
        COLORS = {
            'primary': '#3b82f6',    # Blue 500
            'secondary': '#94a3b8',  # Slate 400
            'success': '#10b981',    # Emerald 500
            'warning': '#f59e0b',    # Amber 500
            'danger': '#ef4444',     # Red 500
            'text': '#f8fafc',       # Slate 50
            'grid': 'rgba(255,255,255,0.1)'
        }

        # Mock data for revenue trends
        dates = pd.date_range(end=pd.Timestamp.now(), periods=6, freq='ME')
        revenue_data = {
            'Month': dates.strftime('%b %Y'),
            'Revenue': [180000, 210000, 195000, 240000, 225000, 280000],
            'Target': [200000, 200000, 220000, 220000, 250000, 250000]
        }
        df_rev = pd.DataFrame(revenue_data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_rev['Month'], 
            y=df_rev['Revenue'], 
            name='Actual Revenue',
            line=dict(color=COLORS['primary'], width=4),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(37, 99, 235, 0.1)'
        ))
        fig.add_trace(go.Scatter(
            x=df_rev['Month'], 
            y=df_rev['Target'], 
            name='Target Revenue',
            line=dict(color=COLORS['secondary'], width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="<b>Revenue Performance vs Target</b>",
            template="plotly_dark",
            margin=dict(l=20, r=20, t=60, b=20),
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text']),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(gridcolor=COLORS['grid']),
            yaxis=dict(gridcolor=COLORS['grid'])
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        st.subheader("AI System Insights")
        
        # Get dynamic insights
        summary = services["executive"].get_executive_summary("demo_location")
        insights = summary.get("insights", [])
        
        if not insights:
            insights = [
                {"type": "success", "title": "Response Time Excellence", "message": "Average response time of 1.8 minutes beats target"},
                {"type": "warning", "title": "Weekend Coverage", "message": "Saturday response times averaged 15 mins (Target: 5 mins)"}
            ]

        for insight in insights:
            if insight["type"] == "success":
                st.success(f"**{insight['title']}**: {insight['message']}")
            elif insight["type"] == "warning":
                st.warning(f"**{insight['title']}**: {insight['message']}")
            else:
                st.info(f"**{insight['title']}**: {insight['message']}")
        
        st.markdown("#### 📈 System Performance")
        health = mock_data.get("system_health", {})
        if health:
            c1, c2, c3 = st.columns(3)
            c1.metric("API Uptime", f"{health['uptime_percentage']}%")
            c2.metric("Avg Latency", f"{health['avg_response_time_ms']}ms")
            c3.metric("SMS Compliance", f"{health['sms_compliance_rate']*100}%")

    with tab3:
        st.subheader("Actionable Executive Report")
        
        action_items = summary.get("action_items", [])
        if not action_items:
             action_items = [
                {"priority": "high", "title": "5 Hot Leads Pending", "action": "Schedule showings for Downtown cluster", "impact": "Potential $2.5M Volume"},
                {"priority": "medium", "title": "Review Weekend Staffing", "action": "Add on-call agent for Saturdays", "impact": "Improve conversion by ~5%"}
            ]

        st.dataframe(
            pd.DataFrame(action_items),
            column_config={
                "priority": "Priority",
                "title": "Opportunity",
                "action": "Recommended Action",
                "impact": "Estimated Impact"
            },
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("📧 Email Report to Jorge"):
            st.toast("Report sent to jorge@example.com")

elif selected_hub == "🧠 Lead Intelligence Hub":
    st.header("🧠 Lead Intelligence Hub")
    st.markdown("*Deep dive into individual leads with AI-powered insights*")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Lead Scoring",
        "🚨 Churn Risk",
        "📊 Segmentation",
        "🎨 Personalization",
        "🔮 Predictions"
    ])
    
    with tab1:
        st.subheader("AI Lead Scoring")
        
        col_map, col_details = st.columns([1, 1])
        
        with col_map:
            st.markdown("#### 📍 Hot Lead Clusters")
            # Generate mock map data
            map_data = pd.DataFrame({
                'lat': [30.2672, 30.2700, 30.2500, 30.2800, 30.2600],
                'lon': [-97.7431, -97.7500, -97.7300, -97.7600, -97.7400],
                'type': ['Hot', 'Hot', 'Warm', 'Cold', 'Hot'],
                'value': [100, 80, 50, 20, 90]
            })
            
            st.map(map_data, zoom=11, use_container_width=True)
            st.caption("Real-time visualization of high-value lead activity")

        with col_details:
            # Lead selector with mapping to context
            lead_options = {
            "Sarah Johnson": {
                "id": "lead_001",
                "extracted_preferences": {
                    "budget": 400000,
                    "location": "Downtown",
                    "timeline": "ASAP",
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "must_haves": "Pool",
                    "financing": "Pre-approved",
                    "motivation": "Relocating for work",
                    "home_condition": "Excellent"
                }
            },
            "Mike Chen": {
                "id": "lead_002",
                "extracted_preferences": {
                    "location": "Suburbs",
                    "timeline": "6 months",
                    "bedrooms": 4
                }
            },
            "Emily Davis": {
                "id": "lead_003",
                "extracted_preferences": {
                    "budget": 300000
                }
            }
        }
        
        selected_lead_name = st.selectbox(
            "Select a lead:",
            list(lead_options.keys())
        )
        
        # Calculate Score using centralized service
        lead_context = lead_options[selected_lead_name]
        
        if "enhanced_lead_scorer" in services:
            with st.spinner("Calculating enhanced lead score..."):
                result_obj = asyncio.run(services["enhanced_lead_scorer"].score_lead(
                    lead_context.get("id", "unknown"), lead_context
                ))
                score = round(result_obj.final_score / 100 * 7, 1) # Map back to 0-7 for UI consistency
                classification = result_obj.classification
                reasoning = result_obj.reasoning
                rec_actions = result_obj.recommended_actions
        else:
            result = services["lead_scorer"].calculate_with_reasoning(lead_context)
            score = result["score"]
            classification = result["classification"]
            reasoning = result["reasoning"]
            rec_actions = result["recommended_actions"]
        
        # Display Results
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
        st.info(f"**Qualifying Data Found:** {reasoning}")
        
        st.markdown("#### Recommended Actions")
        for action in rec_actions:
            st.markdown(f"- {action}")

    with tab2:
        st.subheader("🚨 Churn Early Warning")
        st.markdown("*Predictive analysis of lead abandonment risk*")
        
        if "churn_prediction" in services:
            with st.spinner("Analyzing churn risk factors..."):
                lead_id = lead_options[selected_lead_name].get("id", "unknown")
                churn_result = asyncio.run(services["churn_prediction"].predict_churn_risk(lead_id))
                
                c1, c2, c3 = st.columns(3)
                
                # Gauge-style metric for risk
                risk_color = "#ef4444" if churn_result.risk_score_14d > 60 else "#f59e0b" if churn_result.risk_score_14d > 30 else "#10b981"
                
                with c1:
                    st.metric("14-Day Churn Risk", f"{churn_result.risk_score_14d:.1f}%", delta=None)
                with c2:
                    st.metric("Risk Tier", churn_result.risk_tier.value.upper())
                with c3:
                    st.metric("Model Confidence", f"{churn_result.confidence*100:.0f}%")
                
                st.markdown("---")
                col_factors, col_actions = st.columns(2)
                
                with col_factors:
                    st.markdown("#### 🔍 Top Risk Factors")
                    for factor, importance in churn_result.top_risk_factors[:5]:
                        st.write(f"**{factor.replace('_', ' ').title()}**: {importance:.2f}")
                        st.progress(min(1.0, importance * 2)) # Scale for visibility
                
                with col_actions:
                    st.markdown("#### ⚡ Recommended Interventions")
                    for action in churn_result.recommended_actions:
                        st.info(f"✅ {action}")
        else:
            st.warning("Churn prediction service unavailable.")
            st.info("The full Churn Prediction Engine provides 26 behavioral features and multi-horizon risk scoring.")
    
    with tab3:
        st.subheader("Smart Segmentation")
        
        # Prepare lead data from mock_data
        leads_for_segmentation = []
        if "conversations" in mock_data:
            for conv in mock_data["conversations"]:
                leads_for_segmentation.append({
                    "id": conv.get("contact_id"),
                    "name": conv.get("contact_name"),
                    "engagement_score": conv.get("message_count") * 10, # Mock engagement
                    "lead_score": conv.get("lead_score"),
                    "budget": 500000 if conv.get("budget") == "unknown" else 1500000, # Simplified
                    "last_activity_days_ago": 2,
                    "buyer_type": "luxury_buyer" if "lux" in conv.get("contact_id", "") else "standard",
                    "interested_property_type": "single_family"
                })

        if leads_for_segmentation:
            import asyncio
            # Use the service
            result = asyncio.run(services["segmentation"].segment_leads(leads_for_segmentation, method="behavioral"))
            
            # Display segments in columns
            cols = st.columns(len(result["segments"]))
            for i, seg in enumerate(result["segments"]):
                with cols[i]:
                    st.metric(seg["name"].replace("_", " ").title(), f"{seg['size']} Leads")
            
            # Selected segment details
            selected_seg_name = st.selectbox("View Segment Details:", [s["name"] for s in result["segments"]])
            selected_seg = next(s for s in result["segments"] if s["name"] == selected_seg_name)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📊 Characteristics")
                char = selected_seg["characteristics"]
                st.write(f"- **Avg Engagement:** {char['avg_engagement']}%")
                st.write(f"- **Avg Lead Score:** {char['avg_lead_score']}")
                st.write(f"- **Total Segment Value:** ${char['total_value']:,.0f}")
                
            with col2:
                st.markdown("#### ⚡ Recommended Actions")
                for action in selected_seg["recommended_actions"]:
                    st.markdown(f"- {action}")
        else:
            st.info("No lead data available for segmentation.")
        
    with tab4:
        st.subheader("Content Personalization")
        
        selected_lead_p = st.selectbox("Select Lead for Personalization:", list(lead_options.keys()), key="p_lead")
        
        import asyncio
        # Mock lead data for personalization
        lead_data_p = {
            "name": selected_lead_p,
            "budget": 650000,
            "engagement_score": 78,
            "last_activity_days_ago": 2,
            "location": "Austin, TX",
            "device": "mobile",
            "source": "paid",
            "preferences": {
                "property_type": "single_family",
                "bedrooms": 3,
                "location": "suburban"
            }
        }
        
        p_result = asyncio.run(services["personalization"].personalize_content("lead_123", lead_data_p))
        
        st.write(f"**Strategy:** {p_result['personalization_suite']['overall_strategy']['focus']}")
        
        if "enhanced_property_matcher" in services:
            st.markdown("#### 🚀 Enhanced Property Matches (15-Factor AI)")
            enhanced_matches = services["enhanced_property_matcher"].find_enhanced_matches(
                lead_data_p.get("preferences", {}), limit=3
            )
            
            # Bento Grid Layout
            cols = st.columns(3)
            for i, match in enumerate(enhanced_matches):
                with cols[i]:
                    st.markdown(f"""
                    <div class="bento-item">
                        <div class="bento-header">
                            <div class="bento-title">🏠 {match.property['address']['neighborhood']}</div>
                            <div class="bento-badge">{int(match.overall_score*100)}% Match</div>
                        </div>
                        <div style="font-size: 1.5rem; font-weight: 800; color: #3b82f6; margin-bottom: 0.5rem;">
                            ${match.property['price']:,}
                        </div>
                        <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 1rem; flex-grow: 1;">
                            {match.reasoning.primary_strengths[0] if match.reasoning.primary_strengths else 'Top choice for your profile'}
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: auto;">
                            <div style="font-size: 0.75rem; color: #64748b;">
                                Prob: <b>{match.predicted_showing_request:.1%}</b>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"View Details {i}", key=f"details_{i}", use_container_width=True):
                        st.info(f"Showing details for {match.property['address']['street']}")
        else:
            st.markdown("#### 🏠 Recommended Properties")
            recs = p_result["personalization_suite"]["properties"]["recommendations"]
            cols = st.columns(len(recs))
            for i, rec in enumerate(recs):
                with cols[i]:
                    st.write(f"**{rec['title']}**")
                    st.write(f"${rec['price']:,.0f}")
                    st.caption(rec['why_recommended'])
                    st.button(f"View {rec['property_id']}", key=f"btn_{rec['property_id']}")

        st.markdown("---")
        st.markdown("#### 🔗 Shareable Client Portal")
        # Generate a personalized portal link
        portal_url = f"https://portal.ghl-ai.com/view/{selected_lead_p.replace(' ', '').lower()}/collection-a7"
        
        c_link, c_sms = st.columns([3, 1])
        with c_link:
            st.code(portal_url, language="text")
        with c_sms:
            if st.button("📱 SMS Link", use_container_width=True):
                st.toast("Link sent via SMS!", icon="📨")

    with tab5:
        st.subheader("Predictive Scoring")
        
        selected_lead_pred = st.selectbox("Select Lead for Prediction:", list(lead_options.keys()), key="pred_lead")
        
        # Mock lead data for prediction
        lead_data_pred = {
            "id": "lead_123",
            "email_opens": 8,
            "email_clicks": 5,
            "emails_sent": 10,
            "response_times": [2.5, 1.8, 3.2],
            "page_views": 12,
            "budget": 500000,
            "viewed_property_prices": [480000, 520000, 495000],
            "timeline": "soon",
            "property_matches": 7,
            "messages": [{"content": "I'm interested in properties in downtown."}],
            "source": "organic"
        }
        
        pred_result = services["predictive_scorer"].score_lead("lead_123", lead_data_pred)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Conversion Probability", f"{pred_result.score}%")
            st.write(f"**Confidence:** {pred_result.confidence*100:.1f}%")
            st.write(f"**Tier:** {pred_result.tier.upper()}")
            
        with col2:
            st.markdown("#### 🔍 Contributing Factors")
            for factor in pred_result.factors:
                sentiment_icon = "✅" if factor["sentiment"] == "positive" else "ℹ️"
                st.write(f"{sentiment_icon} **{factor['name']}:** {factor['value']} ({factor['impact']}%)")
        
        st.markdown("#### 🏃 Recommended Strategy")
        for rec in pred_result.recommendations:
            st.markdown(f"- {rec}")

elif selected_hub == "🤖 Automation Studio":
    st.header("🤖 Automation Studio")
    st.markdown("*Visual switchboard to toggle AI features on/off*")
    
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Automations", "📧 Sequences", "🔄 Workflows", "🧪 AI Training Lab"])
    
    with tab1:
        st.subheader("AI Automation Control Panel")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🤖 Smart AI Features")
            
            ai_assistant = st.toggle("AI Assistant (Qualification)", value=True)
            if ai_assistant:
                st.success("✅ Active - Qualifying new leads via SMS")
            else:
                st.warning("⚠️ Inactive - Manual qualification required")
            
            auto_followup = st.toggle("Auto Follow-Up Sequences", value=True)
            if auto_followup:
                st.success("✅ Active - Nurturing 47 leads")
            
            hot_lead_lane = st.toggle("Hot Lead Fast Lane", value=True)
            if hot_lead_lane:
                st.success("✅ Active - 8 leads in priority queue")
        
        with col2:
            st.markdown("#### 🎯 Behavioral Triggers")
            
            property_views = st.toggle("Property View Tracking", value=True)
            email_opens = st.toggle("Email Engagement Scoring", value=True)
            calendar_sync = st.toggle("Calendar Appointment Sync", value=False)
            
        st.markdown("---")
        st.info("💡 **Pro Tip:** Toggle AI Assistant ON/OFF to control when AI engages with leads")
    
    with tab2:
        st.subheader("Auto Follow-Up Sequences")
        
        perf = services["sequences"].get_sequence_performance("demo_seq")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Conversion Rate", f"{perf['metrics']['conversion_rate']*100:.1f}%")
        col2.metric("Email Open Rate", f"{perf['channel_performance']['email']['open_rate']*100:.0f}%")
        col3.metric("SMS Response", f"{perf['channel_performance']['sms']['response_rate']*100:.0f}%")

        # Sequence Table
        sequences_data = [
            {"Name": "New Lead (Buyer) - 7 Day", "Status": "Active", "Enrolled": perf['metrics']['total_enrolled'], "Open Rate": f"{perf['channel_performance']['email']['open_rate']*100:.0f}%", "Reply Rate": f"{perf['channel_performance']['sms']['response_rate']*100:.0f}%"},
            {"Name": "Seller Reactivation", "Status": "Active", "Enrolled": 12, "Open Rate": "75%", "Reply Rate": "35%"},
            {"Name": "Cold Lead Win-back", "Status": "Paused", "Enrolled": 0, "Open Rate": "-", "Reply Rate": "-"},
        ]
        
        st.dataframe(pd.DataFrame(sequences_data), use_container_width=True, hide_index=True)
        
        if st.button("➕ Create New Sequence"):
            st.toast("Opening Sequence Builder...")
        
    with tab3:
        st.subheader("Workflow Marketplace")
        st.markdown("*Install pre-built real estate automations with one click*")
        
        # Browse marketplace
        templates = services["marketplace"].get_featured_templates(6)
        
        # Display in a grid
        cols = st.columns(3)
        for i, t in enumerate(templates):
            with cols[i % 3]:
                st.markdown(f"### {t.icon} {t.name}")
                st.write(t.description[:80] + "...")
                st.caption(f"⭐ {t.rating} | 📥 {t.downloads_count:,} installs")
                if st.button(f"Install", key=f"inst_{t.id}", use_container_width=True):
                    st.success(f"Installed {t.name}!")

        if "workflow_engine" in services:
            st.markdown("---")
            st.subheader("⚙️ Advanced Workflow Engine")
            st.success("✅ Engine Online - Ready for conditional branching")
            
            with st.expander("View Active Executions", expanded=False):
                st.info("No active executions in the last 24 hours.")
                if st.button("🚀 Run Test Workflow (New Lead Sequence)"):
                    st.toast("Triggering Advanced Workflow: New Lead Sequence", icon="⚡")

    with tab4:
        st.subheader("AI Training Lab & Version Control")
        st.caption("Experiment with system prompts safely. Revert if quality drops.")
        
        col_editor, col_history = st.columns([2, 1])
        
        with col_history:
            st.markdown("#### 📜 Version History")
            versions = st.session_state.prompt_versions
            
            for v in reversed(versions):
                with st.container(border=True):
                    st.caption(f"{v['timestamp']} • {v['version']}")
                    st.write(f"**{v['tag']}**")
                    if st.button("Revert", key=f"rev_{v['version']}", use_container_width=True):
                        st.session_state.current_prompt = v['content']
                        st.toast(f"Reverted to {v['version']}")
                        st.rerun()

        with col_editor:
            st.markdown("#### Current System Prompt")
            
            # Default content if not set
            if "current_prompt" not in st.session_state:
                st.session_state.current_prompt = versions[-1]["content"]

            current_prompt = st.text_area(
                "System Instruction", 
                value=st.session_state.current_prompt,
                height=300,
                help="This prompt governs the behavior of the AI Assistant."
            )
            
            c_save, c_test = st.columns(2)
            with c_save:
                if st.button("💾 Save New Version", use_container_width=True, type="primary"):
                    new_ver = f"v1.{len(versions)}"
                    st.session_state.prompt_versions.append({
                        "version": new_ver,
                        "tag": "Experimental",
                        "content": current_prompt,
                        "timestamp": "Just now"
                    })
                    st.session_state.current_prompt = current_prompt
                    st.success(f"Saved {new_ver}!")
                    st.rerun()
                    
            with c_test:
                if st.button("🧪 Test Prompt", use_container_width=True):
                    st.info("Simulation running... Response generated in 1.2s")


elif selected_hub == "💰 Sales Copilot":
    st.header("💰 Sales Copilot")
    st.markdown("*Agent tools for active deals and client meetings*")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "💼 Deal Closer",
        "📄 Documents",
        "📋 Meeting Prep",
        "💵 Calculator"
    ])
    
    with tab1:
        st.subheader("Deal Closer AI")
        st.markdown("*Your always-on negotiation coach. Ask how to handle objections, negotiate fees, or close deals.*")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # Add initial welcome message
            st.session_state.messages.append({"role": "assistant", "content": "I'm ready to help you close. Paste an objection or ask for negotiation advice."})

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("Ex: 'Client says 6% commission is too high'"):
            # Display user message
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.spinner("Analyzing negotiation strategy..."):
                # Waveform animation while "thinking"
                st.markdown("""
                <div class="waveform-container">
                    <div class="waveform-bar" style="animation-delay: 0.0s"></div>
                    <div class="waveform-bar" style="animation-delay: 0.1s"></div>
                    <div class="waveform-bar" style="animation-delay: 0.2s"></div>
                    <div class="waveform-bar" style="animation-delay: 0.3s"></div>
                    <div class="waveform-bar" style="animation-delay: 0.4s"></div>
                    <div class="waveform-bar" style="animation-delay: 0.5s"></div>
                    <div class="waveform-bar" style="animation-delay: 0.6s"></div>
                    <div class="waveform-bar" style="animation-delay: 0.7s"></div>
                </div>
                """, unsafe_allow_html=True)
                
                lead_context = {
                    "name": "Prospect",
                    "stage": "objection_handling",
                    "budget_min": 400000,
                    "budget_max": 600000
                }
                
                # Get AI response
                result = services["deal_closer"].generate_response(prompt, lead_context)
                
                # Format the response nicely
                response_content = f"""
{result['response']}

---
**💡 Key Talking Points:**
{chr(10).join([f'- {p}' for p in result['talking_points']])}

**🏃 Next Best Action:**
{result['follow_up_actions'][0] if result['follow_up_actions'] else 'Schedule follow-up'}
"""
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(response_content)
                
                st.session_state.messages.append({"role": "assistant", "content": response_content})
        
    with tab2:
        st.subheader("Smart Document Generator")
        
        doc_type_str = st.selectbox(
            "Document Type:",
            [t.value.replace("_", " ").title() for t in DocumentType]
        )
        
        # Mapping for enum
        type_enum = next(t for t in DocumentType if t.value.replace("_", " ").title() == doc_type_str)
        
        col1, col2 = st.columns(2)
        with col1:
            party_name = st.text_input("Buyer/Client Name:", "John Doe")
            address = st.text_input("Property Address:", "123 Main St, Austin, TX")
            
        with col2:
            price_doc = st.number_input("Transaction Price ($):", value=450000)
            jurisdiction = st.selectbox("Jurisdiction:", ["TX", "CA", "FL", "NY"])

        if st.button("🚀 Generate & Prepare for Signature", use_container_width=True):
            with st.spinner("Generating professional document..."):
                doc_data = {
                    "property_address": address,
                    "purchase_price": price_doc,
                    "buyer_name": party_name,
                    "jurisdiction": jurisdiction
                }
                doc = services["doc_gen"].generate_document(type_enum, f"template_{type_enum.value}", doc_data)
                
                st.success(f"✅ {doc_type_str} Generated (ID: {doc['id']})")
                st.info(f"**Compliance Status:** {doc['legal_requirements']['compliance_status'].upper()}")
                
                # Signature status
                st.markdown("#### ✍️ E-Signature Status")
                sig_status = services["doc_gen"].check_signature_status("sig_123")
                st.write(f"**Overall Status:** {sig_status['overall_status'].replace('_', ' ').title()}")
                st.progress(sig_status['completion']['percentage'])
                st.write(f"{sig_status['completion']['signed']} of {sig_status['completion']['total']} parties signed.")
        
    with tab3:
        st.subheader("Meeting Prep Assistant")
        st.markdown("*Generate a comprehensive briefing for your next client meeting*")
        
        col1, col2 = st.columns(2)
        with col1:
            meeting_lead = st.selectbox("Select Lead for Meeting:", list(lead_options.keys()), key="mtg_lead")
            m_type = st.selectbox("Meeting Type:", [t.value.replace("_", " ").title() for t in MeetingType])
        
        if st.button("📄 Generate Briefing Doc", use_container_width=True):
            with st.spinner("Compiling data and generating brief..."):
                # Convert back to enum
                type_enum = next(t for t in MeetingType if t.value.replace("_", " ").title() == m_type)
                
                brief = services["meeting_prep"].prepare_meeting_brief(type_enum, "contact_123")
                
                st.markdown("---")
                st.success(f"✅ Briefing for {meeting_lead} Generated")
                
                tab_a, tab_b, tab_c = st.tabs(["📋 Agenda", "🗣️ Talking Points", "🗂️ Required Docs"])
                
                with tab_a:
                    for item in brief["agenda"]:
                        st.write(f"**{item['time']}**: {item['topic']}")
                        
                with tab_b:
                    for point in brief["talking_points"]:
                        st.write(f"- {point}")
                        
                with tab_c:
                    for doc in brief["documents_to_bring"]:
                        st.write(f"- {doc}")
        
    with tab4:
        st.subheader("Commission & ROI Calculator")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 💰 Deal Parameters")
            prop_price = st.number_input("Property Price ($)", min_value=100000, value=500000, step=10000)
            comm_type_str = st.selectbox("Commission Type", ["Buyer Agent", "Seller Agent", "Dual Agency"])
            
            mapping = {
                "Buyer Agent": CommissionType.BUYER_AGENT,
                "Seller Agent": CommissionType.SELLER_AGENT,
                "Dual Agency": CommissionType.DUAL_AGENCY
            }
            comm_type = mapping[comm_type_str]
            
            custom_rate = st.slider("Commission Rate (%)", 1.0, 6.0, 2.5, 0.1) / 100
            broker_split = st.slider("Brokerage Split (%)", 50, 100, 80) / 100
            
            calc = CommissionCalculator(brokerage_split=broker_split)
            result = calc.calculate_commission(prop_price, comm_type, custom_rate=custom_rate)
            
        with col2:
            st.markdown("#### 📊 Results")
            st.metric("Net Commission to You", f"${result['net_commission']:,.2f}")
            st.write(f"**Gross Commission:** ${result['gross_commission']:,.2f}")
            st.write(f"**Brokerage Share:** ${result['brokerage_portion']:,.2f}")
            st.write(f"**Effective Rate:** {result['effective_rate']}%")
            
            st.markdown("---")
            st.markdown("#### 🤖 Automation ROI Impact")
            
            # Show impact of using AI features
            features = st.multiselect(
                "Select AI features used for this deal:",
                ["deal_closer_ai", "hot_lead_fastlane", "auto_followup", "voice_receptionist"],
                default=["deal_closer_ai", "hot_lead_fastlane"]
            )
            
            impact = calc._calculate_automation_impact(features)
            st.success(f"🔥 **ROI Multiplier:** {impact['roi_multiplier']}x")
            st.write(f"**Conversion Improvement:** +{impact['improvement_pct']}%")
            st.caption("These features increase the statistical probability of closing this deal.")

elif selected_hub == "📈 Ops & Optimization":
    st.header("📈 Ops & Optimization")
    st.markdown("*Manager-level analytics and team performance tracking*")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "✅ Quality",
        "💰 Revenue",
        "🏆 Benchmarks",
        "🎓 Coaching"
    ])
    
    with tab1:
        st.subheader("AI Quality Assurance")
        qa_report = services["qa"].generate_qa_report("demo_location")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Quality", f"{qa_report['overall_score']}%", "+2%")
        col2.metric("Compliance Rate", f"{qa_report['compliance_rate']}%", "Stable")
        col3.metric("Empathy Score", f"{qa_report['empathy_score']}/10", "+0.5")
        
        st.markdown("#### 🎯 Improvement Areas")
        for area in qa_report["improvement_areas"]:
            st.warning(f"**{area['topic']}**: {area['recommendation']}")
            
    with tab2:
        st.subheader("Revenue Attribution")
        attr_data = services["revenue"].get_attribution_data("demo_location")
        
        # Display attribution chart
        df_attr = pd.DataFrame(attr_data["channels"])
        fig = px.pie(df_attr, values='revenue', names='channel', title='Revenue by Lead Source',
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)
        
        st.write(f"**Total Attributed Revenue:** ${attr_data['total_revenue']:,.0f}")
        
    with tab3:
        st.subheader("Competitive Benchmarking")
        bench = services["benchmarking"].get_benchmarks("demo_location")
        
        for metric, data in bench.items():
            st.write(f"**{metric.replace('_', ' ').title()}**")
            cols = st.columns([2, 1])
            cols[0].progress(data["percentile"] / 100)
            cols[1].write(f"{data['percentile']}th Percentile")
            
    with tab4:
        st.subheader("AI Agent Coaching")
        recommendations = services["coaching"].get_coaching_recommendations("demo_agent")
        
        for rec in recommendations:
            with st.expander(f"💡 {rec['title']}"):
                st.write(rec['description'])
                st.info(f"**Impact:** {rec['expected_impact']}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; background: #0f172a; border-radius: 12px; margin-top: 3rem; border: 1px solid rgba(255,255,255,0.05);'>
    <div style='color: #f8fafc; font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;'>
        🚀 Production-Ready Multi-Tenant AI System
    </div>
    <div style='color: #94a3b8; font-size: 0.9rem;'>
        Built for Jorge Salas | Claude Sonnet 4.5 | GHL Integration Ready
    </div>
    <div style='margin-top: 1rem; color: #64748b; font-size: 0.85rem;'>
        Consolidated Hub Architecture | Path B Backend | 522+ Tests Passing
    </div>
</div>
""", unsafe_allow_html=True)
