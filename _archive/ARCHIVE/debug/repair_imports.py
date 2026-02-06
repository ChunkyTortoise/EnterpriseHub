import os

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

for file_path in files_to_fix:
    if not os.path.exists(file_path): continue
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Fix the messed up import
    content = content.replace("import streamlit\nfrom ghl_real_estate_ai.streamlit_demo.async_utils import run_async\n as st", "import streamlit as st\nfrom ghl_real_estate_ai.streamlit_demo.async_utils import run_async")
    
    with open(file_path, "w") as f:
        f.write(content)
    print(f"✅ Repaired: {file_path}")
