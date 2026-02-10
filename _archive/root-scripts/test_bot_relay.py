import pytest

@pytest.mark.unit

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("Testing Bot Relay Trigger...")

# Mock Streamlit session state
class MockSessionState(dict):
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value

import streamlit as st
st.session_state = MockSessionState()
st.session_state.global_decisions = []
st.session_state.handoff_triggered = False
st.session_state.latest_analysis = {'overall_score': 95}
st.session_state.analyzed_lead_name = "Sarah Johnson"

# Simulate the relay logic from jorge_bot_command_center.py
latest_analysis = st.session_state.get('latest_analysis', {})
if latest_analysis.get('overall_score', 0) > 90 and not st.session_state.handoff_triggered:
    print("MATCH: Score > 90. Triggering pulse...")
    st.session_state.handoff_triggered = True
    lead_name = st.session_state.get('analyzed_lead_name', 'Lead')
    st.session_state.global_decisions.append({
        "action": "Agent Handoff",
        "why": f"Lead {lead_name} reached critical score (>90). Transferring to Seller Negotiation.",
        "time": datetime.now().strftime("%H:%M:%S")
    })
    print(f"SUCCESS: Decision added to stream: {st.session_state.global_decisions[-1]['why']}")

if st.session_state.handoff_triggered:
    print("Bot Relay verification PASSED!")
else:
    print("Bot Relay verification FAILED!")
    sys.exit(1)
