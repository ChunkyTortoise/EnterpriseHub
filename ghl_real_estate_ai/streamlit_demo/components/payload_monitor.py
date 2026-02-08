import json
import random
from datetime import datetime

import streamlit as st


def render_payload_monitor():
    """
    Elite Live Payload Monitor.
    Shows real-time GHL webhook activity with code-level transparency.
    """
    st.subheader("🛰️ Live Payload Monitor")
    st.markdown("*Streaming raw webhook data from GHL Edge nodes...*")

    # Monitor Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(
            """
        <div style="padding: 10px; background: #0f172a; border-radius: 8px; color: #10b981; font-family: monospace; font-size: 0.8rem;">
            $ tail -f /var/log/ghl/webhooks.log
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.button("⏸️ Pause Stream", use_container_width=True)
    with col3:
        st.button("🗑️ Clear Buffer", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Mock Payloads
    payloads = [
        {
            "event": "contact_created",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "id": "c_9921",
                "name": "James Wilson",
                "email": "james@example.com",
                "source": "Zillow_Sync",
                "customFields": {"budget": 950000, "neighborhood": "Lakeway"},
            },
        },
        {
            "event": "message_received",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "contactId": "c_1442",
                "body": "Is the roof recently replaced?",
                "direction": "inbound",
                "channel": "SMS",
            },
        },
        {
            "event": "appointment_scheduled",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "id": "apt_882",
                "contactId": "c_9921",
                "startTime": "2026-01-15T14:00:00Z",
                "title": "Zilker Property Tour",
            },
        },
    ]

    for i, p in enumerate(payloads):
        with st.expander(f"📦 {p['event'].upper()} - {p['timestamp'].split('T')[1][:8]}", expanded=(i == 0)):
            st.code(json.dumps(p, indent=2), language="json")

            # AI Inference on Payload
            st.markdown(
                """
            <div style="background: rgba(139, 92, 246, 0.05); padding: 10px; border-radius: 8px; border-left: 3px solid #8B5CF6;">
                <div style="font-size: 0.7rem; color: #8B5CF6; font-weight: 700;">AI INFERENCE</div>
                <div style="font-size: 0.8rem; color: #1e293b;">Detected <b>high-intent</b> inquiry. Triggering 'Property Detail' swarm agent.</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Infrastructure Health
    st.markdown("#### 🏗️ Infrastructure Health")
    h_col1, h_col2, h_col3, h_col4 = st.columns(4)
    h_col1.metric("Webhook Success", "100%", "0.0%")
    h_col2.metric("Avg Latency", "82ms", "-12ms")
    h_col3.metric("Redis Cache", "Active", "99.2% Hit")
    h_col4.metric("Worker Load", "14%", "Low")
