import streamlit as st
import pandas as pd
import sqlite3
import json
from modules.inventory_manager import InventoryManager
from modules.ghl_sync import GHLSyncService
import os

# --- Page Config ---
st.set_page_config(page_title="Real Estate AI Match Hub", layout="wide")

# Initialize Services
manager = InventoryManager()
ghl = GHLSyncService()

st.title("🏡 AI Match Command Center")
st.markdown("---")

# Sidebar for adding new data
with st.sidebar:
    st.header("🔌 GHL Connection")
    if st.button("🔄 Sync GHL Contacts"):
        with st.spinner("Fetching from GHL Cloud..."):
            count = ghl.sync_contacts_from_ghl()
            st.success(f"Synced {count} leads!")
            st.rerun()

    st.markdown("---")
    st.header("➕ Add New Listing")
    with st.form("listing_form"):
        street = st.text_input("Street Address")
        city = st.text_input("City", value="Rancho Cucamonga")
        price = st.number_input("Price ($)", min_value=0, step=10000)
        beds = st.number_input("Bedrooms", min_value=0, step=1)
        baths = st.number_input("Bathrooms", min_value=0.0, step=0.5)
        sqft = st.number_input("Sq Ft", min_value=0, step=100)
        
        # Tags Multiselect
        available_tags = ["has_pool", "modern_kitchen", "large_lot", "view", "fixer_upper", "smart_home"]
        selected_tags = st.multiselect("Features/Tags", available_tags)
        
        desc = st.text_area("Description (Optional)")
        
        submit_listing = st.form_submit_button("Ingest & Run Match")
        
        if submit_listing and street:
            listing_id = f"web_{int(pd.Timestamp.now().timestamp())}"
            listing = {
                "id": listing_id,
                "price": price,
                "bedrooms": beds,
                "bathrooms": baths,
                "sqft": sqft,
                "address": {"street": street, "city": city},
                "description": desc,
                "tags": selected_tags
            }
            manager.ingest_listing(listing)
            st.success(f"Added {street}!")
            st.session_state['last_ingested_id'] = listing_id

# Main Dashboard Tabs
tab1, tab2, tab3 = st.tabs(["📋 Inventory", "👤 Lead Database", "🎯 Match Engine"])

def get_db_connection():
    conn = sqlite3.connect(manager.db_path)
    conn.row_factory = sqlite3.Row
    return conn

with tab1:
    st.header("Current Inventory")
    conn = get_db_connection()
    df_props = pd.read_sql_query("SELECT * FROM properties", conn)
    conn.close()
    
    if not df_props.empty:
        st.dataframe(df_props, use_container_width=True)
    else:
        st.info("No properties in database yet.")

with tab2:
    st.header("Active Buyer Leads")
    conn = get_db_connection()
    df_leads = pd.read_sql_query("SELECT * FROM leads", conn)
    conn.close()
    
    if not df_leads.empty:
        st.dataframe(df_leads, use_container_width=True)
    else:
        st.info("No leads in database yet.")

with tab3:
    st.header("Weighted Match Engine")
    
    # Selection of Property to match
    conn = get_db_connection()
    props = conn.execute("SELECT id, address FROM properties").fetchall()
    conn.close()
    
    if props:
        prop_options = {p['address']: p['id'] for p in props}
        selected_prop_addr = st.selectbox("Select a Property to find Buyers", options=list(prop_options.keys()))
        selected_prop_id = prop_options[selected_prop_addr]
        
        matches = manager.find_weighted_matches(selected_prop_id)
        
        if matches:
            df_matches = pd.DataFrame(matches)
            
            # Heatmap Styling Function
            def color_score(val):
                if val >= 90: color = '#22c55e' # Bright Green
                elif val >= 75: color = '#84cc16' # Lime
                elif val >= 60: color = '#eab308' # Yellow
                else: color = '#ef4444' # Red
                return f'background-color: {color}; color: white; font-weight: bold'

            # Display with styling
            st.subheader(f"Top Matches for {selected_prop_addr}")
            st.dataframe(
                df_matches.style.applymap(color_score, subset=['score'])
                .format({"score": "{}%"}),
                use_container_width=True
            )
            
            # Trigger GHL Notification Section
            st.markdown("---")
            st.subheader("🚀 Bulk Action")
            if st.button("Send Match Alerts to Top Buyers"):
                success_count = 0
                for index, row in df_matches.iterrows():
                    if row['score'] >= 80:
                        # Find the lead ID (we need it for the webhook)
                        conn = get_db_connection()
                        lead = conn.execute("SELECT id FROM leads WHERE name=?", (row['buyer'],)).fetchone()
                        conn.close()
                        
                        if lead:
                            if ghl.trigger_match_webhook(lead['id'], row.to_dict()):
                                success_count += 1
                
                st.success(f"Successfully triggered {success_count} GHL Workflows!")
        else:
            st.warning("No buyers found with a score > 50% for this property.")
    else:
        st.info("Add a property first to see matches.")

# Demo Data Loader
st.markdown("---")
if st.button("🚀 Reload Demo Environment (Wipes DB)"):
    if os.path.exists(manager.db_path):
        os.remove(manager.db_path)
    
    manager._init_db()
    
    # Mock Leads
    manager.ingest_lead({
        "id": "l_01", "name": "Jorge Salas", 
        "preferences": {"budget": 1500000, "bedrooms": 4, "must_haves": ["has_pool", "modern_kitchen"]}
    })
    manager.ingest_lead({
        "id": "l_02", "name": "Maria Garcia", 
        "preferences": {"budget": 850000, "bedrooms": 3, "must_haves": ["modern_kitchen", "view"]}
    })
    manager.ingest_lead({
        "id": "l_03", "name": "Sam Smith", 
        "preferences": {"budget": 1200000, "bedrooms": 5, "must_haves": ["large_lot"]}
    })
    
    # Mock Listing
    manager.ingest_listing({
        "id": "p_01", "price": 1420000, "bedrooms": 5, "bathrooms": 4, "sqft": 4000,
        "address": {"street": "555 Estate Way", "city": "Rancho Cucamonga"},
        "description": "Luxury mansion with pool and kitchen.",
        "tags": ["has_pool", "modern_kitchen", "large_lot"]
    })
    
    st.rerun()