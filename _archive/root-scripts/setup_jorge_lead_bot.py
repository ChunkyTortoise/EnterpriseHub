#!/usr/bin/env python3
"""
Jorge's AI Lead Bot - Complete Setup Script

Automated setup script that installs all dependencies and prepares
Jorge's lead bot system for immediate use.

Usage:
    python setup_jorge_lead_bot.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    """Print welcome header."""
    print("\n🤖 Jorge's AI Lead Bot System - Setup")
    print("=" * 50)
    print("🎯 Automated Lead Generation & Qualification for GHL")
    print("🚀 Setting up your complete lead automation system...")
    print("=" * 50)

def check_python_version():
    """Check Python version compatibility."""
    print("\n🔍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python {version.major}.{version.minor} is not supported")
        print("📋 Please install Python 3.10 or higher")
        print("🌐 Download from: https://python.org")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_virtual_environment():
    """Create and activate virtual environment."""
    print("\n🏗️  Setting up virtual environment...")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def get_pip_command():
    """Get the correct pip command for the platform."""
    system = platform.system().lower()
    
    if system == "windows":
        return ["venv\\Scripts\\pip.exe"]
    else:
        return ["venv/bin/pip"]

def install_dependencies():
    """Install all required dependencies."""
    print("\n📦 Installing dependencies...")
    
    requirements_files = [
        "ghl_real_estate_ai/requirements.txt",
        "requirements.txt"
    ]
    
    requirements_file = None
    for req_file in requirements_files:
        if Path(req_file).exists():
            requirements_file = req_file
            break
    
    if not requirements_file:
        print("❌ No requirements.txt file found")
        return False
    
    print(f"📋 Installing from {requirements_file}...")
    
    pip_cmd = get_pip_command()
    
    try:
        # Upgrade pip first
        subprocess.run(pip_cmd + ["install", "--upgrade", "pip"], check=True)
        print("✅ Pip upgraded")
        
        # Install requirements
        subprocess.run(pip_cmd + ["install", "-r", requirements_file], check=True)
        print("✅ All dependencies installed")
        
        # Install additional packages needed for Jorge's system
        additional_packages = [
            "python-dateutil",  # For date handling
            "aiofiles",         # For async file operations
            "jinja2",           # For template rendering
        ]
        
        for package in additional_packages:
            try:
                subprocess.run(pip_cmd + ["install", package], check=True)
                print(f"✅ {package} installed")
            except:
                print(f"⚠️  {package} installation failed (may not be critical)")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_environment_file():
    """Create .env file with configuration template."""
    print("\n⚙️  Setting up environment configuration...")
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    env_template = """# Jorge's AI Lead Bot Configuration
# ==================================

# Claude AI Configuration
ANTHROPIC_API_KEY=your_claude_api_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# GoHighLevel Integration
GHL_API_KEY=your_ghl_api_key_here
GHL_WEBHOOK_SECRET=your_webhook_secret_here
GHL_BASE_URL=https://rest.gohighlevel.com

# System Configuration
ENVIRONMENT=development
APP_NAME=Jorge's AI Lead Bot
VERSION=1.0.0
DEBUG=true

# Server Configuration
HOST=localhost
PORT_API=8000
PORT_DASHBOARD=8501

# Database (Optional - SQLite used by default)
# DATABASE_URL=postgresql://user:pass@localhost/jorge_leads

# Redis Cache (Optional - memory cache used by default)
# REDIS_URL=redis://localhost:6379
# REDIS_PASSWORD=your_redis_password

# Security
SECRET_KEY=your_secret_key_here_change_in_production

# Logging
LOG_LEVEL=INFO

# Performance Settings
MAX_WORKERS=4
CACHE_TTL=3600

# Voice AI Settings
VOICE_AI_ENABLED=true
VOICE_QUALIFICATION_THRESHOLD=70
MAX_CALL_DURATION=1800

# Marketing Settings
MARKETING_AUTO_ENABLED=true
DEFAULT_CAMPAIGN_BUDGET=1000
AB_TEST_DURATION_DAYS=14

# Client Retention Settings
RETENTION_TRACKING_ENABLED=true
REFERRAL_REWARDS_ENABLED=true
ENGAGEMENT_SCORE_THRESHOLD=75

# Market Prediction Settings
MARKET_PREDICTION_ENABLED=true
PREDICTION_CONFIDENCE_THRESHOLD=80
DEFAULT_PREDICTION_HORIZON=6_months

# Notification Settings
EMAIL_NOTIFICATIONS=true
SMS_NOTIFICATIONS=false
WEBHOOK_NOTIFICATIONS=true

# Performance Monitoring
METRICS_ENABLED=true
PERFORMANCE_TRACKING=true
ERROR_REPORTING=true

# Feature Flags
ENABLE_VOICE_AI=true
ENABLE_MARKETING_AUTO=true
ENABLE_CLIENT_RETENTION=true
ENABLE_MARKET_PREDICTIONS=true
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_template)
        print("✅ .env configuration file created")
        print("📋 Please edit .env with your actual API keys!")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def verify_installation():
    """Verify that the installation is working correctly."""
    print("\n🧪 Verifying installation...")
    
    python_cmd = ["venv/bin/python"] if platform.system() != "Windows" else ["venv\\Scripts\\python.exe"]
    
    # Test imports
    test_script = """
import sys
try:
    import streamlit
    import fastapi
    import anthropic
    import pandas
    import plotly
    print("✅ All critical packages imported successfully")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run(python_cmd + ["-c", test_script], 
                                capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(f"❌ Import test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def create_startup_scripts():
    """Create convenient startup scripts."""
    print("\n📝 Creating startup scripts...")
    
    # Windows batch file
    if platform.system() == "Windows":
        batch_content = """@echo off
echo Starting Jorge's Lead Bot System...
echo =====================================

echo Starting API Server...
start "Jorge API" cmd /c "venv\\Scripts\\python.exe jorge_lead_bot_launcher.py --api"

echo Waiting 5 seconds for API to start...
timeout /t 5 /nobreak > nul

echo Starting Dashboard...
start "Jorge Dashboard" cmd /c "venv\\Scripts\\python.exe jorge_lead_bot_launcher.py"

echo.
echo Both systems are starting...
echo API: http://localhost:8000
echo Dashboard: http://localhost:8501
echo.
pause
"""
        with open("start_jorge_system.bat", "w") as f:
            f.write(batch_content)
        print("✅ Windows startup script created: start_jorge_system.bat")
    
    # Unix shell script
    shell_content = """#!/bin/bash
echo "Starting Jorge's Lead Bot System..."
echo "====================================="

# Start API server in background
echo "Starting API Server..."
./venv/bin/python jorge_lead_bot_launcher.py --api &
API_PID=$!

# Wait for API to start
echo "Waiting 5 seconds for API to start..."
sleep 5

# Start dashboard
echo "Starting Dashboard..."
./venv/bin/python jorge_lead_bot_launcher.py

# Cleanup function
cleanup() {
    echo "Shutting down Jorge's system..."
    kill $API_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

wait $API_PID
"""
    
    with open("start_jorge_system.sh", "w") as f:
        f.write(shell_content)
    
    # Make executable on Unix systems
    if platform.system() != "Windows":
        os.chmod("start_jorge_system.sh", 0o755)
    
    print("✅ Unix startup script created: start_jorge_system.sh")

def show_next_steps():
    """Show the user what to do next."""
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE! Jorge's Lead Bot is ready!")
    print("=" * 60)
    
    print("\n📋 NEXT STEPS:")
    print("1. ✏️  Edit the .env file with your API keys:")
    print("      - Add your Claude API key (ANTHROPIC_API_KEY)")
    print("      - Add your GHL API key (GHL_API_KEY)")
    print("      - Add your GHL webhook secret (GHL_WEBHOOK_SECRET)")
    
    print("\n2. 🚀 Start Jorge's system:")
    
    if platform.system() == "Windows":
        print("      - Double-click: start_jorge_system.bat")
        print("      - OR manually: python jorge_lead_bot_launcher.py")
    else:
        print("      - Run: ./start_jorge_system.sh")
        print("      - OR manually: python jorge_lead_bot_launcher.py")
    
    print("\n3. 🌐 Access your dashboard:")
    print("      - API Server: http://localhost:8000")
    print("      - Dashboard: http://localhost:8501")
    print("      - API Docs: http://localhost:8000/docs")
    
    print("\n4. ⚙️  Configure GHL webhooks:")
    print("      - URL: http://your-server:8000/webhooks/ghl")
    print("      - Events: Contact Created, Contact Updated, Opportunity Created")
    
    print("\n📚 DOCUMENTATION:")
    print(f"     - Complete guide: {Path('JORGE_LEAD_BOT_README.md').absolute()}")
    
    print("\n🆘 TROUBLESHOOTING:")
    print("     - Check .env file configuration")
    print("     - Verify API keys are valid")
    print("     - Review log files for errors")
    print("     - Test individual components using API endpoints")
    
    print("\n🎯 JORGE'S LEAD BOT FEATURES:")
    print("     📞 Voice AI Phone Integration")
    print("     🎯 Automated Marketing Campaigns")
    print("     🤝 Client Retention & Referrals")
    print("     📈 Market Prediction Analytics")
    
    print("\n🚀 Ready to automate your lead generation!")

def main():
    """Main setup function."""
    print_header()
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create virtual environment
    if not create_virtual_environment():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create environment file
    if not create_environment_file():
        return False
    
    # Verify installation
    if not verify_installation():
        return False
    
    # Create startup scripts
    create_startup_scripts()
    
    # Show next steps
    show_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        sys.exit(1)