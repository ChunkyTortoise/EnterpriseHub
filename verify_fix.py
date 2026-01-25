
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("Importing ClaudeAssistantOptimized...")
try:
    from ghl_real_estate_ai.services.claude_assistant_optimized import ClaudeAssistantOptimized
    print("Successfully imported.")
    
    print("Initializing ClaudeAssistantOptimized...")
    # Mock streamlit session state if needed
    import streamlit as st
    if not hasattr(st, "session_state"):
        st.session_state = {}
        
    claude = ClaudeAssistantOptimized()
    print("Successfully initialized ClaudeAssistantOptimized!")
except Exception as e:
    print(f"FAILED to initialize: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
