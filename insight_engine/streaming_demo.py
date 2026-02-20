"""
Insight Engine Streaming Demo
Shows real-time SSE consumption from the /dashboard/stream endpoint.

Run: streamlit run streaming_demo.py
Requires: uvicorn insight_engine.api.app:app running on port 8080
"""
import json

import httpx
import streamlit as st

st.set_page_config(page_title="Insight Engine Streaming Demo", layout="wide")
st.title("Real-Time Dashboard Streaming")
st.caption("Metrics appear as they're generated -- no waiting for the full render")

if st.button("Generate Dashboard (Streaming)", type="primary"):
    progress = st.progress(0, text="Connecting to stream...")
    results = st.container()

    payload = {
        "title": "Live Sales Dashboard",
        "metrics": [
            {"value": "$2.4M", "label": "Revenue", "variant": "success", "trend": "up", "comparison_value": "+18%"},
            {"value": "847", "label": "Leads Qualified", "variant": "info"},
            {"value": "8.2%", "label": "Conversion Rate", "variant": "success"},
        ],
        "cards": [
            {"title": "Pipeline Status", "content": "3 deals closing this week", "variant": "success"},
        ],
    }

    try:
        with httpx.Client(timeout=30) as client:
            with client.stream("POST", "http://localhost:8080/dashboard/stream", json=payload) as resp:
                items_received = 0
                total = len(payload["metrics"]) + len(payload["cards"])

                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        event = json.loads(line[6:])

                        if event["event"] == "start":
                            progress.progress(10, text=f"Building {event['title']}...")
                        elif event["event"] in ("metric", "card"):
                            items_received += 1
                            pct = int(10 + (items_received / total) * 80)
                            label = event.get("label") or event.get("title", "")
                            progress.progress(pct, text=f"Rendered: {label}")
                            results.markdown(f"**{label}** rendered", unsafe_allow_html=False)
                        elif event["event"] == "complete":
                            progress.progress(100, text="Complete!")
                            st.success("Dashboard assembled!")
                            st.components.v1.html(event["html"], height=400, scrolling=True)
    except Exception as e:
        st.error(f"Cannot connect to Insight Engine API (is it running on port 8080?): {e}")
        st.info("Start it with: uvicorn insight_engine.api.app:app --port 8080")
