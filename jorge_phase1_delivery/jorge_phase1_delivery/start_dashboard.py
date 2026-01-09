#!/usr/bin/env python3
"""
Jorge's GHL Real Estate AI - One-Click Startup Script
Automatically handles setup, validation, and dashboard launch
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Display startup banner"""
    print("=" * 60)
    print("🎯 JORGE'S GHL REAL ESTATE AI - PHASE 1")
    print("🚀 Starting your $2,726/month AI Real Estate Suite")
    print("=" * 60)

def check_python_version():
    """Ensure Python 3.8+ is running"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ required")
        print("📋 Current version:", sys.version)
        sys.exit(1)
    print("✅ Python version:", sys.version_info.major, ".", sys.version_info.minor)

def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("⚠️  Some dependencies may already be installed")

def check_env_file():
    """Verify .env file exists and has required keys"""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists():
        if env_example.exists():
            print("📋 Creating .env from example...")
            env_example.rename(env_file)
        else:
            print("❌ Error: No .env file found!")
            print("📋 Please create .env with your API keys")
            return False

    # Check for required keys
    required_keys = ["ANTHROPIC_API_KEY", "GHL_API_KEY", "GHL_LOCATION_ID"]
    env_content = env_file.read_text()

    missing_keys = []
    for key in required_keys:
        if key not in env_content or f"{key}=" in env_content:
            missing_keys.append(key)

    if missing_keys:
        print(f"⚠️  Missing API keys: {', '.join(missing_keys)}")
        print("📋 Please edit .env file with your actual API keys")
        print("📝 Required:")
        print("   ANTHROPIC_API_KEY=sk-ant-api03-...")
        print("   GHL_API_KEY=eyJhbGc...")
        print("   GHL_LOCATION_ID=REDACTED_LOCATION_ID")
        return False

    print("✅ Environment configuration found")
    return True

def start_dashboard():
    """Launch the Streamlit dashboard"""
    print("\n🚀 Starting Jorge's AI Dashboard...")
    print("📊 Dashboard will open at: http://localhost:8502")
    print("🔄 Starting in 3 seconds...")
    time.sleep(3)

    try:
        # Launch Streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py",
                       "--server.port", "8502", "--server.headless", "true"])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        print("📋 Try running manually: streamlit run app.py --server.port 8502")

def main():
    """Main startup sequence"""
    print_banner()

    # Step 1: Check Python version
    check_python_version()

    # Step 2: Install dependencies
    install_dependencies()

    # Step 3: Verify environment
    if not check_env_file():
        print("\n⏸️  Setup incomplete. Please configure .env file first.")
        input("Press Enter after configuring .env to continue...")

    # Step 4: Launch dashboard
    start_dashboard()

if __name__ == "__main__":
    main()