
import os
import re

files_to_fix = [
    "ghl_real_estate_ai/streamlit_demo/components/client_expansion_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/components/executive_portfolio_interface.py",
    "ghl_real_estate_ai/streamlit_demo/components/jorge_analytics_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/components/jorge_lead_bot_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/components/jorge_property_matching_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/components/jorge_seller_bot_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/components/lead_intelligence_hub.py",
    "ghl_real_estate_ai/streamlit_demo/components/negotiation_intelligence_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/components/ops_optimization.py",
    "ghl_real_estate_ai/streamlit_demo/components/real_time_value_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/components/redis_customer_intelligence_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/components/ultra_premium_dashboard.py",
    "ghl_real_estate_ai/streamlit_demo/admin.py",
    "ghl_real_estate_ai/streamlit_demo/jorge_bot_command_center.py"
]

import_line = "from ghl_real_estate_ai.streamlit_demo.async_utils import run_async\n"

for file_path in files_to_fix:
    if not os.path.exists(file_path):
        print(f"⚠️ Skip: {file_path} (not found)")
        continue
        
    with open(file_path, "r") as f:
        content = f.read()
    
    # 1. Add import if not present
    if "run_async" not in content:
        # Insert after other imports
        if "import streamlit" in content:
            content = content.replace("import streamlit", "import streamlit\n" + import_line)
        else:
            content = import_line + content
            
    # 2. Replace asyncio.run(
    content = content.replace("asyncio.run(", "run_async(")
    
    # 3. Specific fix for jorge_bot_command_center.py where I removed asyncio.run already for health
    # Actually, I should probably just leave that one or revert it to use run_async
    
    with open(file_path, "w") as f:
        f.write(content)
    print(f"✅ Fixed: {file_path}")

print("\n🚀 All files updated with run_async utility.")
