import asyncio
import os
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ghl_real_estate_ai.services.analytics_service import AnalyticsService

load_dotenv()

st.set_page_config(page_title="Jorge AI Brain - Multi-Tenant", layout="wide")


def get_db_path():
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return os.getenv("DB_PATH", "real_estate_engine.db")


DB_PATH = get_db_path()


def get_available_locations():
    analytics_dir = Path("data/analytics")
    locations = ["All Locations"]
    if analytics_dir.exists():
        for loc_dir in analytics_dir.iterdir():
            if loc_dir.is_dir():
                locations.append(loc_dir.name)
    return locations


# Sidebar for multi-tenancy control
st.sidebar.title("🏢 Tenant Management")
available_locs = get_available_locations()
selected_location = st.sidebar.selectbox("Select Location", available_locs)
force_refresh = st.sidebar.button("Force Refresh Data")


def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    # Most Liked Properties
    query_likes = """
    SELECT p.address, COUNT(i.id) as likes, p.price, p.image_url
    FROM interactions i
    JOIN properties p ON i.property_id = p.id
    WHERE i.action = 'like'
    GROUP BY p.id
    ORDER BY likes DESC
    LIMIT 10
    """
    try:
        df_likes = pd.read_sql(query_likes, conn)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        df_likes = pd.DataFrame()
    finally:
        conn.close()
    return df_likes


async def get_dashboard_data(location_id: str, force_refresh: bool = False):
    service = AnalyticsService()

    if location_id == "All Locations":
        # Aggregate all locations (for Jorge/SuperAdmin)
        all_events = []
        summary = {
            "total_messages": 0,
            "leads_scored": 0,
            "hot_leads": 0,
            "vague_streaks": 0,
            "take_away_closes": 0,
            "recent_events": [],
        }

        locs = get_available_locations()
        locs.remove("All Locations")

        for loc in locs:
            loc_summary = await service.get_cached_daily_summary(loc, force_refresh=force_refresh)
            loc_events = await service.get_events(loc)  # Get raw events for "Recent Logs"

            summary["total_messages"] += loc_summary.get("total_messages", 0)
            summary["leads_scored"] += loc_summary.get("leads_scored", 0)
            summary["hot_leads"] += loc_summary.get("hot_leads", 0)

            # Count specific Jorge metrics from raw events
            seller_events = [e for e in loc_events if e.get("event_type") == "jorge_seller_interaction"]
            summary["vague_streaks"] += sum(1 for e in seller_events if e.get("data", {}).get("vague_streak", 0) > 0)
            summary["take_away_closes"] += sum(
                1 for e in seller_events if e.get("data", {}).get("response_type") == "take_away_close"
            )

            summary["recent_events"].extend(seller_events)

        # Sort recent events
        summary["recent_events"] = sorted(summary["recent_events"], key=lambda x: x["timestamp"], reverse=True)[:10]
        return summary
    else:
        # Single location optimization
        loc_summary = await service.get_cached_daily_summary(location_id, force_refresh=force_refresh)
        loc_events = await service.get_events(location_id)

        seller_events = [e for e in loc_events if e.get("event_type") == "jorge_seller_interaction"]

        return {
            "total_messages": loc_summary.get("total_messages", 0),
            "leads_scored": loc_summary.get("leads_scored", 0),
            "hot_leads": loc_summary.get("hot_leads", 0),
            "vague_streaks": sum(1 for e in seller_events if e.get("data", {}).get("vague_streak", 0) > 0),
            "take_away_closes": sum(
                1 for e in seller_events if e.get("data", {}).get("response_type") == "take_away_close"
            ),
            "recent_events": sorted(seller_events, key=lambda x: x["timestamp"], reverse=True)[:10],
        }


st.title(f"🧠 Jorge AI Brain: {selected_location}")

# --- ELITE COMMAND CENTER LAUNCHER ---
st.markdown(
    """
<div style="background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%); padding: 2rem; border-radius: 16px; margin-bottom: 2rem; text-align: center; box-shadow: 0 10px 30px rgba(30, 136, 229, 0.3);">
    <h2 style="color: white; margin: 0;">🚀 ELITE PHASE 4.0 ACTIVE</h2>
    <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 1.5rem 0;">Experience the full Lead & Seller Command interface with Obsidian Styling</p>
</div>
""",
    unsafe_allow_html=True,
)

if st.button("🛰️ LAUNCH UNIFIED BOT COMMAND CENTER", type="primary", use_container_width=True):
    st.info(
        "To launch the full Elite Command Center, run: streamlit run ghl_real_estate_ai/streamlit_demo/jorge_bot_command_center.py"
    )
    # In a real environment, we could use a link or redirect if hosted
    st.markdown("[Open Command Center (Local Connection)](http://localhost:8501)")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 Hot Properties (Most Swiped)")
    df = load_data()
    if df.empty:
        st.write("No 'Like' interactions recorded yet.")
    else:
        # Filter logic here if DB had location_id
        for index, row in df.iterrows():
            st.write(f"**{row['address']}** - ❤️ {row['likes']} Likes")
            if row["image_url"]:
                st.image(row["image_url"], width=300)
            else:
                st.image("https://via.placeholder.com/300x200?text=No+Image+Available", width=300)
            st.caption(f"${row['price']:,.0f}")
            st.divider()

with col2:
    st.subheader("🤖 Recent Logic Logs")
    st.info(f"Viewing: {selected_location} | Status: PRODUCTION")

    st.code(
        """
    [SYSTEM] Intelligence Engine Online
    [SYSTEM] Multi-Tenant Isolation: ENABLED
    [SYSTEM] Cache Layer: REDIS + MEMORY FALLBACK
    """,
        language="bash",
    )

    st.subheader("🔄 Latest Leads & Personas")
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        try:
            leads_query = "SELECT id, name, phone, preferred_neighborhood FROM leads LIMIT 10"
            df_leads = pd.read_sql(leads_query, conn)
            st.table(df_leads)
        except Exception as e:
            st.error(f"Error loading leads: {e}")
        finally:
            conn.close()

# --- Jorge Bot Ecosystem Analytics ---
st.markdown("---")
st.header("🤖 Jorge Bot Ecosystem Analytics")

# Run async code safely
try:
    dashboard_data = asyncio.run(get_dashboard_data(selected_location, force_refresh))
except RuntimeError:
    loop = asyncio.get_event_loop()
    dashboard_data = loop.run_until_complete(get_dashboard_data(selected_location, force_refresh))

if dashboard_data:
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Messages (Today)", dashboard_data["total_messages"])
    col_b.metric("Take-Away Closes Triggered", dashboard_data["take_away_closes"])
    col_c.metric("Vague Streaks Detected", dashboard_data["vague_streaks"])

    st.subheader("Recent Seller Bot Logs")
    if dashboard_data["recent_events"]:
        for e in dashboard_data["recent_events"]:
            data = e.get("data", {})
            st.text(
                f"[{e['timestamp']}] Temp: {data.get('temperature')} | Q: {data.get('questions_answered')}/4 | Vague: {data.get('vague_streak')}"
            )
    else:
        st.write("No seller bot interactions recorded yet today.")
else:
    st.info("No analytics data found for the selected location today.")
