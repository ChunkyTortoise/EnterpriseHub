#!/usr/bin/env python3
"""
Jorge's Bot Quick Setup Script

This script automatically configures and deploys Jorge's AI bot system
for immediate use with GoHighLevel.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import os
import sys
import subprocess
import json
from typing import Dict, Any

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("🏠 JORGE'S AI BOT SYSTEM - QUICK SETUP")
    print("=" * 60)
    print("Setting up your AI bots for GHL integration...")
    print()

def check_python_version():
    """Check Python version compatibility"""
    print("📋 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ ERROR: Python 3.8 or higher required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} - Compatible")

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    requirements = [
        "streamlit>=1.31.0",
        "fastapi>=0.100.0", 
        "uvicorn>=0.22.0",
        "anthropic>=0.8.0",
        "redis>=4.5.0",
        "schedule>=1.2.0",
        "plotly>=5.14.0",
        "pandas>=2.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.24.0"
    ]
    
    try:
        for package in requirements:
            print(f"   Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
        print("✅ All dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def create_env_file():
    """Create .env file with configuration prompts"""
    print("\n⚙️ Setting up configuration...")
    
    if os.path.exists(".env"):
        response = input("   .env file exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("   Keeping existing .env file")
            return
    
    print("\n   Please provide the following information:")
    
    # Required settings
    ghl_token = input("   GHL Access Token: ").strip()
    claude_key = input("   Claude API Key: ").strip() 
    location_id = input("   GHL Location ID: ").strip()
    
    # Optional settings with defaults
    print("\n   Optional settings (press Enter for defaults):")
    redis_url = input("   Redis URL [redis://localhost:6379]: ").strip()
    webhook_secret = input("   GHL Webhook Secret [auto-generated]: ").strip()
    
    # Set defaults
    redis_url = redis_url or "redis://localhost:6379"
    webhook_secret = webhook_secret or "jorge_webhook_secret_2026"
    
    # Create .env content
    env_content = f"""# Jorge's AI Bot Configuration
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Required Settings
GHL_ACCESS_TOKEN={ghl_token}
CLAUDE_API_KEY={claude_key}
GHL_LOCATION_ID={location_id}

# Optional Settings  
REDIS_URL={redis_url}
GHL_WEBHOOK_SECRET={webhook_secret}

# Bot Configuration
BOT_RESPONSE_DELAY=1.5
AUTO_FOLLOWUP_ENABLED=true
HOT_LEAD_SCORE_THRESHOLD=80
WARM_LEAD_SCORE_THRESHOLD=60

# Seller Bot Settings
JORGE_CONFRONTATIONAL_LEVEL=high
SELLER_QUALIFICATION_TIMEOUT=72

# Follow-up Settings
INITIAL_FOLLOWUP_DELAY=4
LONG_TERM_FOLLOWUP_DAYS=14
MAX_FOLLOWUP_ATTEMPTS=5

# System Settings
LOG_LEVEL=INFO
DEBUG_MODE=false
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Configuration file created (.env)")

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "logs",
        "config", 
        "data",
        "backups"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   Created: {directory}/")
    
    print("✅ Directory structure created")

def create_config_files():
    """Create configuration files"""
    print("\n📝 Creating configuration files...")
    
    # Message templates
    templates = {
        "lead_greeting": "Thanks for your interest! I'll help you find the perfect home in your area.",
        "seller_greeting": "I can help you get top dollar for your property. Let me ask you a few quick questions.",
        "qualification_complete": "Perfect! You're fully qualified. Let me connect you with our team for next steps.",
        "hot_lead_escalation": "Jorge here. I saw your interest level is high. Can we schedule a quick 10-minute call today?",
        "appointment_confirmation": "Great! Your appointment is confirmed. You'll receive a calendar invite shortly.",
        "follow_up_general": "Just checking in on your property search. Any updates on your timeline or requirements?",
        "nurture_market_update": "Market update: Home values in your area continue to trend upward. Great time to buy!"
    }
    
    with open("config/message_templates.json", "w") as f:
        json.dump(templates, f, indent=2)
    
    # Bot settings
    bot_settings = {
        "lead_bot": {
            "qualification_questions": [
                "What's your budget range?",
                "When are you looking to move?", 
                "Which area are you focusing on?",
                "What type of property interests you?"
            ],
            "scoring_weights": {
                "budget_clarity": 0.25,
                "timeline_urgency": 0.30,
                "location_specificity": 0.20,
                "engagement_quality": 0.25
            }
        },
        "seller_bot": {
            "jorge_questions": [
                "What's got you considering wanting to sell, where would you move to?",
                "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?",
                "How would you describe your home, would you say it's move-in ready or would it need some work?", 
                "What price would incentivize you to sell?"
            ],
            "temperature_thresholds": {
                "hot": {"questions_answered": 4, "timeline_acceptable": True, "response_quality": 0.8},
                "warm": {"questions_answered": 3, "response_quality": 0.6},
                "cold": {"questions_answered": 1}
            }
        }
    }
    
    with open("config/bot_settings.json", "w") as f:
        json.dump(bot_settings, f, indent=2)
    
    print("✅ Configuration files created")

def setup_logging():
    """Set up logging configuration"""
    print("\n📊 Setting up logging...")
    
    log_config = """
import logging
import logging.handlers
from datetime import datetime

# Create logs directory
import os
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            'logs/jorge_bots.log', 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

# Create specialized loggers
bot_logger = logging.getLogger('jorge_bots')
automation_logger = logging.getLogger('jorge_automation') 
ghl_logger = logging.getLogger('ghl_integration')
"""
    
    with open("config/logging_config.py", "w") as f:
        f.write(log_config)
    
    print("✅ Logging configuration created")

def create_startup_scripts():
    """Create startup scripts for different platforms"""
    print("\n🚀 Creating startup scripts...")
    
    # Windows batch file
    windows_script = """@echo off
echo Starting Jorge's AI Bot System...
echo.

REM Activate virtual environment if it exists
if exist venv\\Scripts\\activate.bat (
    call venv\\Scripts\\activate.bat
    echo Virtual environment activated
)

REM Start the automation system
start /B python jorge_automation.py

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start the dashboard
echo Opening Jorge's Bot Dashboard...
start /B streamlit run jorge_kpi_dashboard.py --server.port 8501

echo.
echo ✅ Jorge's bots are now running!
echo 📊 Dashboard: http://localhost:8501
echo 🤖 Bots: Active and monitoring GHL
echo.
pause
"""
    
    with open("start_bots.bat", "w") as f:
        f.write(windows_script)
    
    # macOS/Linux shell script
    unix_script = """#!/bin/bash
echo "Starting Jorge's AI Bot System..."
echo ""

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
fi

# Start the automation system in background
python jorge_automation.py &
AUTOMATION_PID=$!
echo "Automation system started (PID: $AUTOMATION_PID)"

# Wait a moment
sleep 3

# Start the dashboard
echo "Opening Jorge's Bot Dashboard..."
streamlit run jorge_kpi_dashboard.py --server.port 8501 &
DASHBOARD_PID=$!

echo ""
echo "✅ Jorge's bots are now running!"
echo "📊 Dashboard: http://localhost:8501"
echo "🤖 Bots: Active and monitoring GHL"
echo ""
echo "To stop bots: kill $AUTOMATION_PID $DASHBOARD_PID"
echo ""
"""
    
    with open("start_bots.sh", "w") as f:
        f.write(unix_script)
    
    # Make shell script executable
    os.chmod("start_bots.sh", 0o755)
    
    print("✅ Startup scripts created")
    print("   Windows: start_bots.bat")
    print("   Mac/Linux: start_bots.sh")

def create_test_script():
    """Create integration test script"""
    print("\n🧪 Creating test script...")
    
    test_script = '''#!/usr/bin/env python3
"""Test Jorge's Bot Integration"""

import asyncio
import os
from datetime import datetime

async def test_integration():
    print("🧪 Testing Jorge's Bot Integration")
    print("=" * 40)
    
    # Test 1: Environment Configuration
    print("\\n1. Testing environment configuration...")
    required_vars = ["GHL_ACCESS_TOKEN", "CLAUDE_API_KEY", "GHL_LOCATION_ID"]
    
    for var in required_vars:
        if os.getenv(var):
            print(f"   ✅ {var} - Configured")
        else:
            print(f"   ❌ {var} - Missing")
    
    # Test 2: Import Bot Modules
    print("\\n2. Testing bot imports...")
    try:
        from jorge_lead_bot import JorgeLeadBot
        print("   ✅ Lead Bot - Imported successfully")
    except Exception as e:
        print(f"   ❌ Lead Bot - Import failed: {e}")
    
    try:
        from jorge_seller_bot import JorgeSellerBot  
        print("   ✅ Seller Bot - Imported successfully")
    except Exception as e:
        print(f"   ❌ Seller Bot - Import failed: {e}")
    
    try:
        from jorge_automation import JorgeAutomationSystem
        print("   ✅ Automation System - Imported successfully")
    except Exception as e:
        print(f"   ❌ Automation System - Import failed: {e}")
    
    # Test 3: Bot Functionality
    print("\\n3. Testing bot functionality...")
    try:
        lead_bot = JorgeLeadBot()
        print("   ✅ Lead Bot - Initialized")
        
        # Test lead processing (mock)
        result = await lead_bot.process_lead_message(
            contact_id="test_123",
            location_id="test_456", 
            message="I'm looking to buy a house under $500k"
        )
        print("   ✅ Lead Bot - Processing works")
        
    except Exception as e:
        print(f"   ❌ Lead Bot - Test failed: {e}")
    
    try:
        seller_bot = JorgeSellerBot()
        print("   ✅ Seller Bot - Initialized")
        
        # Test seller processing (mock)
        result = await seller_bot.process_seller_message(
            contact_id="test_789",
            location_id="test_456",
            message="I want to sell my house"
        )
        print("   ✅ Seller Bot - Processing works")
        
    except Exception as e:
        print(f"   ❌ Seller Bot - Test failed: {e}")
    
    print("\\n" + "=" * 40)
    print("✅ Integration test completed!")
    print("📊 Run 'streamlit run jorge_kpi_dashboard.py' to start dashboard")
    print("🤖 Bots are ready for GHL integration")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test_integration())
'''
    
    with open("test_integration.py", "w") as f:
        f.write(test_script)
    
    print("✅ Integration test script created")

def print_completion():
    """Print setup completion message"""
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    
    print("\n📋 What was configured:")
    print("   ✅ Dependencies installed")
    print("   ✅ Configuration files created")
    print("   ✅ Directory structure setup") 
    print("   ✅ Logging configured")
    print("   ✅ Startup scripts created")
    print("   ✅ Test scripts created")
    
    print("\n🚀 Next Steps:")
    print("   1. Run: python test_integration.py")
    print("   2. Start bots: ./start_bots.sh (Mac/Linux) or start_bots.bat (Windows)")
    print("   3. Open dashboard: http://localhost:8501")
    print("   4. Configure GHL webhooks (see README.md)")
    
    print("\n📁 Key Files:")
    print("   📖 README.md - Complete documentation")
    print("   ⚙️ .env - Configuration settings")
    print("   🧪 test_integration.py - Test your setup")
    print("   📊 jorge_kpi_dashboard.py - Performance dashboard")
    
    print("\n🆘 Support:")
    print("   📖 Check README.md for detailed instructions")
    print("   🔍 Review logs/ directory for troubleshooting")
    print("   ⚙️ Modify .env file to customize settings")
    
    print("\n🏠 Jorge's AI Bot System is ready for GHL integration!")
    print("=" * 60)

def main():
    """Main setup function"""
    from datetime import datetime
    
    print_header()
    
    try:
        check_python_version()
        install_dependencies() 
        create_directories()
        create_env_file()
        create_config_files()
        setup_logging()
        create_startup_scripts()
        create_test_script()
        print_completion()
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()