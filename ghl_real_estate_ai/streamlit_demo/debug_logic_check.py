
import sys
from unittest.mock import MagicMock

# Mock streamlit
st_mock = MagicMock()
sys.modules['streamlit'] = st_mock

# Mock session state
st_mock.session_state = {'selected_market': 'Rancho Cucamonga, CA'}

# Mock pandas and plotly
sys.modules['pandas'] = MagicMock()
sys.modules['plotly.graph_objects'] = MagicMock()
sys.modules['plotly.express'] = MagicMock()

# Import the component
import sys
import os
project_root = "/Users/cave/enterprisehub/ghl_real_estate_ai/streamlit_demo"
sys.path.insert(0, project_root)

try:
    from components.comprehensive_lead_intelligence_hub import _get_current_market_key, _get_scored_leads
    
    print("Testing _get_current_market_key...")
    key = _get_current_market_key()
    print(f"Market Key: {key}")
    if key != "Rancho":
        print("FAILED: Expected 'Rancho'")
    else:
        print("SUCCESS")

    print("\nTesting _get_scored_leads...")
    # Mock generate_sample_lead_data since it lives in another module that might import st
    # Actually we just import it.
    
    leads = _get_scored_leads("Rancho")
    print(f"Leads count: {len(leads)}")
    print("SUCCESS")
    
except ImportError as e:
    print(f"Import Error: {e}")
except Exception as e:
    print(f"Runtime Error: {e}")
    import traceback
    traceback.print_exc()
