#!/usr/bin/env python3
"""
🎯 Jorge Demo Premium Launch Script
==================================

Optimized launcher for Jorge's demo presentation with all premium features activated.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    print("🚀 Launching Jorge Demo - Premium Real Estate AI")
    print("🎯 All premium features activated for demonstration")
    print("=" * 60)

    # Ensure we're in the right directory
    if not Path("app.py").exists():
        print("❌ app.py not found. Please run from streamlit_demo directory.")
        return False

    # Check for enhanced demo version
    enhanced_app = Path("app_enhanced_demo.py")
    if enhanced_app.exists():
        print("✅ Using enhanced demo version with all premium features")
        app_file = "app_enhanced_demo.py"
    else:
        print("✅ Using standard version (premium features may be limited)")
        app_file = "app.py"

    print(f"🎨 Launching: {app_file}")
    print("🌐 Demo will open in your browser automatically")
    print("=" * 60)

    try:
        # Launch Streamlit with optimal settings for demo
        cmd = [
            "streamlit",
            "run",
            app_file,
            "--server.port",
            "8501",
            "--server.headless",
            "false",
            "--browser.serverAddress",
            "localhost",
            "--theme.base",
            "light",
        ]

        subprocess.run(cmd)

    except FileNotFoundError:
        print("❌ Streamlit not found. Please install: pip install streamlit")
        return False
    except KeyboardInterrupt:
        print("\n🎯 Demo session ended. Premium features showcased successfully!")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
