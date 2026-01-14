import os
import sys
from pathlib import Path

# Set up paths to ensure all modules are findable
BASE_DIR = Path(__file__).parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Redirect to the main production entry point
# This ensures that 'streamlit run app.py' launches the latest Elite v4.0 dashboard
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    main_app_path = str(BASE_DIR / "ghl_real_estate_ai" / "streamlit_demo" / "app.py")
    sys.argv = ["streamlit", "run", main_app_path]
    sys.exit(stcli.main())