"""
GHL Real Estate AI - Admin Dashboard
Manage tenants and knowledge base.
"""
import streamlit as st
import sys
import os
import asyncio
import json
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from services.tenant_service import TenantService
from services.analytics_service import AnalyticsService
from core.rag_engine import RAGEngine
from ghl_utils.config import settings

# Page config
st.set_page_config(
    page_title="GHL AI Admin",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ GHL Real Estate AI Admin Dashboard")
st.markdown("Manage multi-tenant configurations, knowledge bases, and view performance analytics.")

# Initialize services
tenant_service = TenantService()
analytics_service = AnalyticsService()

# Helper for async calls
def run_async(coro):
    return asyncio.run(coro)

# Sidebar navigation
page = st.sidebar.selectbox("Navigation", ["Tenant Management", "Knowledge Base", "Analytics"])

if page == "Tenant Management":
    st.header("🏢 Tenant Management")
    
    # 0. Agency Master Key (Jorge's Requirement)
    with st.expander("🔑 Agency-Wide Master Key", expanded=True):
        st.info("Setting an Agency Master Key allows the AI to automatically work across ALL sub-accounts without adding them one-by-one.")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            agency_id = st.text_input("Agency ID", value=settings.ghl_agency_id or "")
        with col_a2:
            agency_key = st.text_input("Agency API Key", type="password", value=settings.ghl_agency_api_key or "")
        
        if st.button("Save Agency Master Key"):
            if agency_id and agency_key:
                run_async(tenant_service.save_agency_config(agency_id, agency_key))
                st.success("Agency Master Key saved! All sub-accounts are now empowered.")
            else:
                st.error("Please provide both Agency ID and Key.")

    # 1. Register New Tenant (Override)
    with st.expander("📍 Individual Sub-Account Override", expanded=False):
        st.write("Use this ONLY if a specific sub-account needs a different API key or Anthropic key than the master settings.")
        with st.form("register_tenant_form"):
            col1, col2 = st.columns(2)
            with col1:
                loc_id = st.text_input("GHL Location ID", help="The unique identifier for the GHL sub-account")
                anthropic_key = st.text_input("Anthropic API Key", type="password")
            with col2:
                ghl_key = st.text_input("GHL API Key / OAuth Token", type="password")
                
            submitted = st.form_submit_button("Save Tenant Configuration")
            if submitted:
                if loc_id and anthropic_key and ghl_key:
                    run_async(tenant_service.save_tenant_config(loc_id, anthropic_key, ghl_key))
                    st.success(f"Tenant {loc_id} registered successfully!")
                else:
                    st.error("Please fill in all fields.")

    # 2. List Registered Tenants
    st.subheader("Registered Tenants")
    tenants_dir = Path("data/tenants")
    if tenants_dir.exists():
        tenant_files = list(tenants_dir.glob("*.json"))
        if tenant_files:
            for t_file in tenant_files:
                with open(t_file, "r") as f:
                    config = json.load(f)
                
                with st.container():
                    c1, c2, c3 = st.columns([1, 2, 1])
                    c1.markdown(f"**{config.get('location_id')}**")
                    c2.code(f"Anthropic: {config.get('anthropic_api_key')[:10]}...", language=None)
                    if c3.button("Delete", key=f"del_{config.get('location_id')}"):
                        os.remove(t_file)
                        st.rerun()
                    st.divider()
        else:
            st.info("No tenants registered yet.")
    else:
        st.info("No tenants directory found.")

elif page == "Knowledge Base":
    st.header("📚 Knowledge Base Management")
    
    # Select Tenant
    tenants_dir = Path("data/tenants")
    available_locations = ["global"]
    if tenants_dir.exists():
        available_locations.extend([f.stem for f in tenants_dir.glob("*.json")])
    
    selected_loc = st.selectbox("Select Location Context", available_locations)
    
    st.info(f"Managing knowledge for: **{selected_loc}**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Load Default Data")
        st.write("Load the standard property listings and FAQs into this location's context.")
        if st.button("Load Standard Knowledge Base"):
            with st.spinner(f"Loading knowledge for {selected_loc}..."):
                # Use the script logic here (simplified for demo)
                import subprocess
                cmd = [sys.executable, "scripts/load_knowledge_base.py", "--location_id", selected_loc]
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_root))
                if result.returncode == 0:
                    st.success(f"Successfully loaded knowledge base for {selected_loc}")
                    with st.expander("Show Logs"):
                        st.code(result.stdout)
                else:
                    st.error(f"Failed to load knowledge base: {result.stderr}")

    with col2:
        st.subheader("RAG Engine Status")
        rag_engine = RAGEngine(
            collection_name=settings.chroma_collection_name,
            persist_directory=settings.chroma_persist_directory
        )
        
        # This is a bit of a hack to count documents for a location
        # Since our search implementation filters by location, we can try to search for something common
        res = rag_engine.search("", n_results=100, location_id=selected_loc)
        st.metric("Documents in Context", len(res))
        
        if st.button("Clear Vector Store (ALL DATA)", type="primary"):
            rag_engine.clear()
            st.warning("All vector data has been cleared.")
            st.rerun()

    st.divider()
    st.subheader("Test Retrieval")
    query = st.text_input("Test Search Query")
    if query:
        results = rag_engine.search(query, location_id=selected_loc)
        if results:
            for r in results:
                with st.expander(f"Result (Dist: {r.distance:.4f}) - Source: {r.source}"):
                    st.write(r.text)
                    st.json(r.metadata)
        else:
            st.warning("No matches found for this location.")

elif page == "Analytics":
    st.header("📊 Performance Analytics")
    
    # Select Tenant
    tenants_dir = Path("data/tenants")
    available_locations = ["global"]
    if tenants_dir.exists():
        available_locations.extend([f.stem for f in tenants_dir.glob("*.json")])
    
    selected_loc = st.selectbox("Select Location for Analytics", available_locations)
    
    # Date selection
    selected_date = st.date_input("Select Date", datetime.utcnow())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    st.divider()
    
    # Fetch summary
    summary = run_async(analytics_service.get_daily_summary(selected_loc, date_str))
    
    if summary["total_messages"] > 0 or summary["leads_scored"] > 0:
        # Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Messages", summary["total_messages"])
        col2.metric("Active Contacts", summary["active_contacts_count"])
        col3.metric("Hot Leads", summary["hot_leads"])
        col4.metric("Avg Lead Score", f"{summary['avg_lead_score']:.1f}")
        
        # Detail Row
        st.subheader("Conversation Volume")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.write("**Inbound vs Outbound**")
            chart_data = {
                "Type": ["Incoming", "Outgoing"],
                "Count": [summary["incoming_messages"], summary["outgoing_messages"]]
            }
            st.bar_chart(chart_data, x="Type", y="Count")
            
        with col_m2:
            st.write("**Lead Quality Distribution**")
            # We'd need to fetch all events to get the distribution, 
            # but for now let's show the summary counts if we had them.
            st.info("Lead quality distribution will appear here as more data is collected.")

        # Raw Events Table
        st.subheader("Recent Events")
        events = run_async(analytics_service.get_events(selected_loc, date_str))
        if events:
            # Sort by timestamp desc
            events.sort(key=lambda x: x["timestamp"], reverse=True)
            
            display_events = []
            for e in events:
                display_events.append({
                    "Time": e["timestamp"].split("T")[1][:8],
                    "Event": e["event_type"],
                    "Contact": e["contact_id"],
                    "Details": str(e["data"])
                })
            st.table(display_events[:20]) # Show last 20 events
    else:
        st.info(f"No analytics data found for {selected_loc} on {date_str}.")
        
        # Add some demo data button
        if st.button("Generate Demo Analytics Data"):
            async def generate_demo():
                await analytics_service.track_event("message_received", selected_loc, "demo_contact_1", {"message_type": "sms"})
                await analytics_service.track_event("message_sent", selected_loc, "demo_contact_1", {"message_length": 45})
                await analytics_service.track_event("lead_scored", selected_loc, "demo_contact_1", {"score": 85, "classification": "hot"})
                await analytics_service.track_event("message_received", selected_loc, "demo_contact_2", {"message_type": "sms"})
                await analytics_service.track_event("message_sent", selected_loc, "demo_contact_2", {"message_length": 30})
                await analytics_service.track_event("lead_scored", selected_loc, "demo_contact_2", {"score": 45, "classification": "warm"})
            
            run_async(generate_demo())
            st.success("Demo data generated! Refreshing...")
            st.rerun()
