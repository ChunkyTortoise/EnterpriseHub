
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Set up paths similar to app.py
BASE_DIR = Path(os.getcwd())
DEMO_DIR = BASE_DIR / "ghl_real_estate_ai" / "streamlit_demo"
SERVICES_DIR = BASE_DIR / "ghl_real_estate_ai"

sys.path.insert(0, str(DEMO_DIR))
sys.path.insert(0, str(SERVICES_DIR))
sys.path.insert(0, str(BASE_DIR))

# Mock streamlit
sys.modules['streamlit'] = MagicMock()
import streamlit as st

# Setup session state mock
st.session_state = MagicMock()
st.session_state.get.return_value = "🏢 Executive Command Center"

print("DEBUG: Attempting to import app components...")
try:
    from components.executive_hub import render_executive_hub
    print("✅ Imported executive_hub")
    from components.lead_intelligence_hub import render_lead_intelligence_hub
    print("✅ Imported lead_intelligence_hub")
    from realtime_dashboard_integration import render_realtime_intelligence_dashboard
    print("✅ Imported realtime_dashboard")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✅ All components imported successfully in test script")
