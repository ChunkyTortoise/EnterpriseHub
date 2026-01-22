
import sys
from pathlib import Path
import os

# Add paths as done in app.py
cwd = Path.cwd()
current_dir = cwd / "ghl_real_estate_ai" / "streamlit_demo"
project_root = cwd / "ghl_real_estate_ai"
parent_root = cwd

sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(parent_root))

try:
    from ghl_real_estate_ai.services.enhanced_lead_intelligence import get_enhanced_lead_intelligence, EnhancedLeadIntelligence
    service = get_enhanced_lead_intelligence()
    print(f"Module file: {sys.modules['ghl_real_estate_ai.services.enhanced_lead_intelligence'].__file__}")
    print(f"Has render_deep_intelligence_tab: {hasattr(service, 'render_deep_intelligence_tab')}")
    print(f"Class methods: {[m for m in dir(EnhancedLeadIntelligence) if not m.startswith('__')]}")
except Exception as e:
    print(f"Error: {e}")
