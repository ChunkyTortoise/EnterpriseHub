import streamlit as st
import sqlite3
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Jorge AI Brain", layout="wide")

def get_db_path():
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return os.getenv("DB_PATH", "real_estate_engine.db")

DB_PATH = get_db_path()

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

st.title("🧠 Jorge Real Estate AI: Live Intelligence")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 Hot Properties (Most Swiped)")
    df = load_data()
    if df.empty:
        st.write("No 'Like' interactions recorded yet.")
    else:
        for index, row in df.iterrows():
            st.write(f"**{row['address']}** - ❤️ {row['likes']} Likes")
            if row['image_url']:
                st.image(row['image_url'], width=300)
            else:
                st.image("https://via.placeholder.com/300x200?text=No+Image+Available", width=300)
            st.caption(f"${row['price']:,.0f}")
            st.divider()

with col2:
    st.subheader("🤖 Recent Logic Logs")
    st.info("System Status: PRODUCTION (Railway)")
    
    # In a real app, this could pull from a log file or a dedicated logs table
    st.code("""
    [10:00:01] New Swipe: LIKE on 123 Palm Dr
    [10:00:02] Intelligence: Generated Persona 'Modernist Pool Lover'
    [10:00:03] GHL: Updated Custom Field
    [10:00:05] Vapi: Triggered Call to +1 (555)...
    """, language="bash")
    
    st.subheader("🔄 Latest Leads & Personas")
    # Add a table showing latest leads and their generated personas if available
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
