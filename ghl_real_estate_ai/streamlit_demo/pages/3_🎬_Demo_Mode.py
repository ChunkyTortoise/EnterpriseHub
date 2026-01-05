"""
GHL Real Estate AI - Demo Mode Manager
Interactive demo scenarios and data management
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Any

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from ghl_real_estate_ai.services.demo_mode import DemoModeManager
    SERVICE_AVAILABLE = True
except ImportError as e:
    SERVICE_AVAILABLE = False
    import_error = str(e)

# Page config
st.set_page_config(
    page_title="Demo Mode Manager",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .demo-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 15px 0;
        border-left: 4px solid #667eea;
    }
    .scenario-active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .data-preview {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 0.9em;
        max-height: 300px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🎬 Demo Mode Manager")
st.markdown("**Control demo scenarios and manage synthetic data**")
st.markdown("---")

# Check service availability
if not SERVICE_AVAILABLE:
    st.error(f"⚠️ Demo Mode service not available: {import_error}")
    st.info("💡 This page requires the DemoModeManager service to be properly configured.")
    st.stop()

# Initialize service
@st.cache_resource
def get_demo_service():
    return DemoModeManager(data_dir="data")

demo_manager = get_demo_service()

# Sidebar - Demo controls
with st.sidebar:
    st.markdown("### 🎮 Demo Controls")
    
    demo_enabled = st.toggle("Enable Demo Mode", value=True)
    
    if demo_enabled:
        st.success("✅ Demo Mode Active")
    else:
        st.warning("⚠️ Demo Mode Disabled")
    
    st.markdown("---")
    st.markdown("### 🎯 Quick Actions")
    
    if st.button("🔄 Reset All Data"):
        demo_manager.reset_demo_data("demo_location")
        st.success("✅ Demo data reset!")
        st.rerun()
    
    if st.button("🎲 Generate New Data"):
        demo_manager.generate_demo_data("demo_location", num_leads=50)
        st.success("✅ New demo data generated!")
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Data Settings")
    
    num_leads = st.slider("Number of Leads", 10, 200, 50)
    time_range = st.selectbox("Time Range", ["Last 7 Days", "Last 30 Days", "Last 90 Days"])

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎭 Scenarios", "📊 Data Management", "⚙️ Settings", "📖 Usage Guide"])

with tab1:
    st.markdown("### 🎭 Demo Scenarios")
    
    scenarios = demo_manager.list_scenarios("demo_location")
    
    if not scenarios:
        scenarios = [
            {
                "id": "cold_lead",
                "name": "Cold Lead Journey",
                "description": "New prospect with minimal engagement",
                "duration": "5 minutes",
                "leads": 10
            },
            {
                "id": "warm_lead",
                "name": "Warm Lead Nurture",
                "description": "Engaged prospect ready for follow-up",
                "duration": "3 minutes",
                "leads": 15
            },
            {
                "id": "hot_lead",
                "name": "Hot Lead Conversion",
                "description": "Ready-to-buy prospect with urgency",
                "duration": "2 minutes",
                "leads": 5
            },
            {
                "id": "full_pipeline",
                "name": "Full Pipeline Demo",
                "description": "Complete sales pipeline with all stages",
                "duration": "10 minutes",
                "leads": 50
            }
        ]
    
    col1, col2 = st.columns(2)
    
    for idx, scenario in enumerate(scenarios):
        with col1 if idx % 2 == 0 else col2:
            st.markdown(f"""
            <div class="demo-card">
                <h4>{scenario['name']}</h4>
                <p>{scenario['description']}</p>
                <p><strong>⏱️ Duration:</strong> {scenario['duration']}</p>
                <p><strong>👥 Leads:</strong> {scenario['leads']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(f"▶️ Load", key=f"load_{scenario['id']}"):
                    demo_manager.load_scenario("demo_location", scenario['id'])
                    st.success(f"✅ Loaded: {scenario['name']}")
                    st.rerun()
            with col_b:
                if st.button(f"👁️ Preview", key=f"preview_{scenario['id']}"):
                    st.session_state.preview_scenario = scenario['id']

with tab2:
    st.markdown("### 📊 Demo Data Management")
    
    # Data statistics
    col1, col2, col3, col4 = st.columns(4)
    
    stats = demo_manager.get_stats("demo_location")
    
    with col1:
        st.metric("Total Leads", stats.get("total_leads", 0))
    with col2:
        st.metric("Conversations", stats.get("conversations", 0))
    with col3:
        st.metric("Properties", stats.get("properties", 0))
    with col4:
        st.metric("Scenarios", len(scenarios))
    
    st.markdown("---")
    
    # Data preview
    st.markdown("#### 📋 Current Demo Data")
    
    data_type = st.selectbox("Select Data Type", ["Leads", "Conversations", "Properties", "Campaigns"])
    
    if data_type == "Leads":
        leads = demo_manager.get_demo_leads("demo_location")
        if leads:
            st.dataframe(leads[:10], use_container_width=True)
            st.info(f"Showing 10 of {len(leads)} leads")
        else:
            st.warning("No demo leads available. Generate demo data to get started.")
    
    elif data_type == "Conversations":
        st.json({
            "conversation_id": "conv_12345",
            "contact_id": "contact_123",
            "timestamp": "2026-01-04T14:30:00Z",
            "messages": 8,
            "sentiment": "positive",
            "lead_score": 75
        })
    
    elif data_type == "Properties":
        st.json({
            "property_id": "prop_456",
            "address": "123 Main St",
            "price": 450000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 2000
        })
    
    elif data_type == "Campaigns":
        st.json({
            "campaign_id": "camp_789",
            "name": "Spring Open House",
            "status": "active",
            "leads_generated": 45,
            "conversion_rate": 12.5
        })
    
    st.markdown("---")
    
    # Bulk operations
    st.markdown("#### ⚡ Bulk Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Clear All Data"):
            if st.checkbox("Confirm deletion"):
                demo_manager.clear_all_data("demo_location")
                st.success("✅ All demo data cleared!")
                st.rerun()
    
    with col2:
        if st.button("📤 Export Data"):
            export_data = demo_manager.export_data("demo_location")
            st.download_button(
                "💾 Download JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"demo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col3:
        uploaded_file = st.file_uploader("📥 Import Data", type="json")
        if uploaded_file:
            import_data = json.load(uploaded_file)
            if st.button("Import"):
                demo_manager.import_data("demo_location", import_data)
                st.success("✅ Data imported successfully!")
                st.rerun()

with tab3:
    st.markdown("### ⚙️ Demo Mode Settings")
    
    st.markdown("#### 🎯 Scenario Configuration")
    
    default_scenario = st.selectbox(
        "Default Scenario",
        ["None", "Cold Lead", "Warm Lead", "Hot Lead", "Full Pipeline"]
    )
    
    auto_reset = st.checkbox("Auto-reset after demo", value=True)
    reset_interval = st.number_input("Reset interval (minutes)", min_value=5, value=30)
    
    st.markdown("---")
    
    st.markdown("#### 📊 Data Generation Settings")
    
    lead_distribution = st.slider("Lead Distribution (Cold/Warm/Hot)", 0, 100, [60, 30, 10])
    
    st.markdown(f"""
    - **Cold Leads:** {lead_distribution[0]}%
    - **Warm Leads:** {lead_distribution[1]}%
    - **Hot Leads:** {lead_distribution[2]}%
    """)
    
    include_negative_sentiment = st.checkbox("Include negative sentiment scenarios", value=True)
    include_objections = st.checkbox("Include objection handling scenarios", value=True)
    
    st.markdown("---")
    
    if st.button("💾 Save Settings", type="primary"):
        settings = {
            "default_scenario": default_scenario,
            "auto_reset": auto_reset,
            "reset_interval": reset_interval,
            "lead_distribution": lead_distribution,
            "include_negative_sentiment": include_negative_sentiment,
            "include_objections": include_objections
        }
        demo_manager.save_settings("demo_location", settings)
        st.success("✅ Settings saved successfully!")

with tab4:
    st.markdown("### 📖 Demo Mode Usage Guide")
    
    st.markdown("""
    #### 🎯 Quick Start
    
    1. **Enable Demo Mode** - Toggle the switch in the sidebar
    2. **Select a Scenario** - Choose from pre-built scenarios in the Scenarios tab
    3. **Generate Data** - Click "Generate New Data" to populate with synthetic leads
    4. **Start Presenting** - Use the demo data across all platform features
    
    ---
    
    #### 🎭 Available Scenarios
    
    **Cold Lead Journey** (5 min)
    - Shows initial contact and qualification process
    - Demonstrates lead scoring from 0-40 range
    - Perfect for showing nurture campaigns
    
    **Warm Lead Nurture** (3 min)
    - Mid-funnel engagement scenarios
    - Score range: 40-70
    - Highlights follow-up automation
    
    **Hot Lead Conversion** (2 min)
    - High-intent prospects ready to buy
    - Score range: 70-100
    - Shows conversion optimization
    
    **Full Pipeline Demo** (10 min)
    - Complete sales cycle demonstration
    - All lead stages represented
    - Comprehensive platform showcase
    
    ---
    
    #### 📊 Data Management
    
    **Generate Data:**
    - Creates realistic synthetic leads
    - Includes conversations, properties, and campaigns
    - Customizable volume and distribution
    
    **Reset Data:**
    - Clears all demo data
    - Returns to clean slate
    - Preserves configuration settings
    
    **Export/Import:**
    - Save demo configurations
    - Share scenarios with team
    - Restore previous states
    
    ---
    
    #### ⚡ Best Practices
    
    ✅ **Do:**
    - Reset data before each demo
    - Use scenario appropriate for audience
    - Test demo flow beforehand
    - Keep data volume manageable
    
    ❌ **Don't:**
    - Mix demo and production data
    - Leave demo mode on in production
    - Use real client information
    - Forget to reset between sessions
    
    ---
    
    #### 🆘 Troubleshooting
    
    **Issue:** Demo mode won't activate
    - Check that demo mode toggle is enabled
    - Verify data directory permissions
    - Restart the application
    
    **Issue:** No data showing
    - Generate demo data first
    - Check selected scenario has data
    - Verify data filters aren't too restrictive
    
    **Issue:** Performance slow with large datasets
    - Reduce number of generated leads
    - Clear old demo data
    - Use specific scenarios instead of full pipeline
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>🎬 Demo Mode Manager | Safe sandbox for presentations and testing</p>
    <p>Demo data is isolated and does not affect production systems</p>
</div>
""", unsafe_allow_html=True)
