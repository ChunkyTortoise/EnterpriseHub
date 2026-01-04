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
from core.rag_engine import RAGEngine
from ghl_utils.config import settings

# Page config
st.set_page_config(
    page_title="GHL AI Admin",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ GHL Real Estate AI Admin Dashboard")
st.markdown("Manage multi-tenant configurations and knowledge bases.")

# Initialize service
tenant_service = TenantService()

# Helper for async calls
def run_async(coro):
    return asyncio.run(coro)

# Sidebar navigation
page = st.sidebar.selectbox("Navigation", ["Tenant Management", "Knowledge Base"])

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
