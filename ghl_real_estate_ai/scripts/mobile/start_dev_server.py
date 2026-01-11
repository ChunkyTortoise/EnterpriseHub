#!/usr/bin/env python3
"""
Mobile Development Server

Starts the development server with mobile-optimized settings.
"""

import os
import subprocess
import sys
from pathlib import Path

def start_mobile_dev_server():
    """Start development server with mobile configuration"""
    print("🚀 Starting Mobile Development Server...")

    # Set mobile development environment variables
    os.environ["MOBILE_DEV_MODE"] = "true"
    os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "true"
    os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"

    # Start streamlit with mobile settings
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "app.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--browser.gatherUsageStats=false",
            "--server.runOnSave=true"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Development server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    start_mobile_dev_server()
