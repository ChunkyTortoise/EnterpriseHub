
import sys
import types
from unittest.mock import MagicMock

# Mock streamlit before importing components
sys.modules['streamlit'] = MagicMock()
# Also mock streamlit.components.v1
st_components = MagicMock()
sys.modules['streamlit.components.v1'] = st_components

# Mock other streamlit submodules if needed
sys.modules['streamlit.runtime.scriptrunner'] = MagicMock()

import sys
import os
from pathlib import Path

# Add project root to path
project_root = "/Users/cave/enterprisehub/ghl_real_estate_ai/streamlit_demo"
sys.path.insert(0, project_root)

print("Checking imports with mocked streamlit...")

try:
    print("1. Importing interactive_lead_map...")
    from components.interactive_lead_map import render_interactive_lead_map
    print("   Success")
except Exception as e:
    print(f"   FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    print("2. Importing claude_agent_chat...")
    from components.claude_agent_chat import render_claude_agent_interface
    print("   Success")
except Exception as e:
    print(f"   FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    print("3. Importing comprehensive_lead_intelligence_hub...")
    from components.comprehensive_lead_intelligence_hub import render_comprehensive_lead_intelligence_hub
    print("   Success")
except Exception as e:
    print(f"   FAILED: {e}")
    import traceback
    traceback.print_exc()

print("Done.")
