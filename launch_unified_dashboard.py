#!/usr/bin/env python3
"""
Jorge AI Unified Bot Dashboard Launcher
======================================

Quick launcher for the new unified bot dashboard with dedicated tabs
for Lead Bot, Buyer Bot, and Seller Bot.

Usage:
    python launch_unified_dashboard.py

Or:
    python -m streamlit run ghl_real_estate_ai/streamlit_demo/jorge_unified_bot_dashboard.py

Author: Claude Code Assistant
Created: 2026-01-25
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the unified bot dashboard."""
    print("🤖 Jorge AI Unified Bot Dashboard")
    print("=" * 50)
    print("🎯 Lead Bot - 3-7-30 Day Sequences & Nurturing")
    print("🏠 Buyer Bot - Property Matching & Qualification")
    print("💼 Seller Bot - Confrontational Qualification")
    print("=" * 50)

    # Get the project root directory
    script_dir = Path(__file__).parent
    dashboard_path = script_dir / "ghl_real_estate_ai" / "streamlit_demo" / "jorge_unified_bot_dashboard.py"

    # Check if the dashboard file exists
    if not dashboard_path.exists():
        print(f"❌ Dashboard file not found at: {dashboard_path}")
        print("Please ensure you're running this from the project root directory.")
        return 1

    print(f"🚀 Launching dashboard from: {dashboard_path}")
    print("📱 Opening in your default browser...")
    print("\n💡 Features:")
    print("   • Live chat interfaces for each bot")
    print("   • Bot-specific KPIs and metrics")
    print("   • Real-time analytics and insights")
    print("   • Lead management and property data")
    print("   • Bot configuration settings")
    print("\n🔗 Dashboard will be available at: http://localhost:8501")
    print("⌨️  Press Ctrl+C to stop the server")
    print("=" * 50)

    try:
        # Launch Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", str(dashboard_path), "--server.port=8501"]
        subprocess.run(cmd, cwd=script_dir)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped. Thanks for using Jorge AI!")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())