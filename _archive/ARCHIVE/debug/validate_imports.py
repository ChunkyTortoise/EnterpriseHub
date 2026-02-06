
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")

try:
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css
    print("✅ obsidian_theme import success")
except Exception as e:
    print(f"❌ obsidian_theme import failed: {e}")

try:
    from ghl_real_estate_ai.streamlit_demo.components.jorge_lead_bot_dashboard import render_jorge_lead_bot_dashboard
    print("✅ jorge_lead_bot_dashboard import success")
except Exception as e:
    print(f"❌ jorge_lead_bot_dashboard import failed: {e}")

try:
    from ghl_real_estate_ai.streamlit_demo.components.jorge_seller_bot_dashboard import render_jorge_seller_bot_dashboard
    print("✅ jorge_seller_bot_dashboard import success")
except Exception as e:
    print(f"❌ jorge_seller_bot_dashboard import failed: {e}")

try:
    from ghl_real_estate_ai.streamlit_demo.components.jorge_analytics_dashboard import render_jorge_analytics_dashboard
    print("✅ jorge_analytics_dashboard import success")
except Exception as e:
    print(f"❌ jorge_analytics_dashboard import failed: {e}")

try:
    from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
    print("✅ LeadBotWorkflow import success")
except Exception as e:
    print(f"❌ LeadBotWorkflow import failed: {e}")

try:
    from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
    print("✅ JorgeSellerBot import success")
except Exception as e:
    print(f"❌ JorgeSellerBot import failed: {e}")
