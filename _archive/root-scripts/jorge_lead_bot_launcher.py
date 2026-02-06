#!/usr/bin/env python3
"""
Jorge's AI Lead Bot - Standalone Launcher

Quick launch script for Jorge's complete lead automation system.
Can be run independently or integrated into the main dashboard.

Usage:
    python jorge_lead_bot_launcher.py

Requirements:
    - EnterpriseHub API running on localhost:8000
    - Streamlit installed
"""

import sys
import subprocess
import os
from pathlib import Path

def check_requirements():
    """Check if all requirements are available."""
    try:
        import streamlit
        print("✅ Streamlit is available")
    except ImportError:
        print("❌ Streamlit not found. Install with: pip install streamlit")
        return False
    
    try:
        import requests
        print("✅ Requests library is available")
    except ImportError:
        print("⚠️  Requests not found. Install with: pip install requests")
        print("   (Will use demo mode without API connection)")
    
    return True

def check_api_server():
    """Check if the API server is running."""
    try:
        import requests
        response = requests.get("http://localhost:8000/jorge-advanced/health", timeout=5)
        if response.status_code == 200:
            print("✅ Jorge's API server is running")
            return True
    except:
        pass
    
    print("⚠️  API server not detected on localhost:8000")
    print("   Dashboard will run in demo mode")
    return False

def launch_jorge_dashboard():
    """Launch Jorge's Lead Bot Dashboard."""
    
    print("\n🤖 Jorge's AI Lead Bot System")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Missing requirements. Please install them and try again.")
        return
    
    # Check API status
    api_status = check_api_server()
    
    # Find the dashboard component
    dashboard_path = Path(__file__).parent / "ghl_real_estate_ai" / "streamlit_demo" / "components" / "jorge_lead_bot_dashboard.py"
    
    if not dashboard_path.exists():
        print(f"❌ Dashboard component not found at {dashboard_path}")
        return
    
    print(f"\n🚀 Launching Jorge's Lead Bot Dashboard...")
    print(f"📁 Component: {dashboard_path}")
    
    if api_status:
        print("🔗 Connected to live API")
    else:
        print("🎭 Running in demo mode")
    
    print("\n" + "=" * 50)
    print("🌐 Dashboard will open in your browser")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 50)
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Jorge's Lead Bot Dashboard stopped")

def launch_api_server():
    """Launch the FastAPI server for Jorge's system."""
    
    api_path = Path(__file__).parent / "ghl_real_estate_ai" / "api" / "main.py"
    
    if not api_path.exists():
        print(f"❌ API server not found at {api_path}")
        return
    
    print("\n🚀 Starting Jorge's API Server...")
    print("🌐 Server will be available at http://localhost:8000")
    print("📚 API docs at http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "ghl_real_estate_ai.api.main:app",
            "--host", "localhost",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Jorge's API Server stopped")

def show_help():
    """Show help information."""
    print("""
🤖 Jorge's AI Lead Bot System - Help

Available Commands:
    python jorge_lead_bot_launcher.py              # Launch dashboard only
    python jorge_lead_bot_launcher.py --api        # Launch API server only  
    python jorge_lead_bot_launcher.py --full       # Launch both API and dashboard
    python jorge_lead_bot_launcher.py --help       # Show this help

System Components:
    📞 Voice AI Phone Integration    - Automated lead qualification calls
    🎯 Marketing Automation         - AI-powered campaign generation
    🤝 Client Retention            - Lifecycle tracking & referrals
    📈 Market Intelligence         - Predictive analytics & opportunities

Quick Setup:
    1. Install requirements: pip install streamlit fastapi uvicorn requests
    2. Start API server: python jorge_lead_bot_launcher.py --api
    3. Open new terminal and launch dashboard: python jorge_lead_bot_launcher.py
    4. Access dashboard at http://localhost:8501

Jorge's System Features:
    ✅ Complete GHL Integration
    ✅ Claude AI Integration
    ✅ Real-time Lead Processing
    ✅ Automated Follow-ups
    ✅ Performance Analytics
    ✅ Market Predictions
    
For Support: Check the EnterpriseHub documentation
    """)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "--help" or command == "-h":
            show_help()
        elif command == "--api":
            launch_api_server()
        elif command == "--full":
            print("🚀 Starting Jorge's Complete Lead Bot System...")
            print("\n1️⃣ Starting API Server...")
            # Would need threading to run both simultaneously
            print("⚠️  For full system, run API and dashboard in separate terminals:")
            print("   Terminal 1: python jorge_lead_bot_launcher.py --api")
            print("   Terminal 2: python jorge_lead_bot_launcher.py")
        else:
            print(f"❌ Unknown command: {command}")
            show_help()
    else:
        launch_jorge_dashboard()