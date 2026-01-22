
import os

replacements = {
    "from jorge_analytics_service import JorgeAnalyticsService": "from ghl_real_estate_ai.services.jorge_analytics_service import JorgeAnalyticsService",
    "from jorge_property_matching_service import JorgePropertyMatchingService": "from ghl_real_estate_ai.services.jorge_property_matching_service import JorgePropertyMatchingService",
    "from jorge_property_matching_dashboard import": "from ghl_real_estate_ai.streamlit_demo.components.jorge_property_matching_dashboard import",
    "from jorge_analytics_dashboard import": "from ghl_real_estate_ai.streamlit_demo.components.jorge_analytics_dashboard import"
}

files = [
    "ghl_real_estate_ai/streamlit_demo/components/jorge_analytics_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/components/jorge_lead_bot_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/components/jorge_property_matching_dashboard.py"
]

for file_path in files:
    if not os.path.exists(file_path):
        print(f"⚠️ Skip: {file_path}")
        continue
        
    with open(file_path, "r") as f:
        content = f.read()
    
    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    if content != original:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✅ Fixed imports in: {file_path}")
    else:
        print(f"ℹ️ No changes needed in: {file_path}")
