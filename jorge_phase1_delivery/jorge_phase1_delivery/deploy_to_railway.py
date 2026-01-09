#!/usr/bin/env python3
"""
Jorge's GHL Real Estate AI - Railway Deployment Script
Automatically deploys the system to Railway for 24/7 cloud access
"""

import os
import subprocess
import sys
import time

def print_banner():
    """Display deployment banner"""
    print("=" * 60)
    print("🚀 DEPLOYING JORGE'S AI TO RAILWAY CLOUD")
    print("📡 Creating live demo URL for 24/7 access")
    print("=" * 60)

def check_railway_cli():
    """Check if Railway CLI is installed"""
    try:
        result = subprocess.run(["railway", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Railway CLI found:", result.stdout.strip())
            return True
        else:
            print("❌ Railway CLI not working properly")
            return False
    except FileNotFoundError:
        print("❌ Railway CLI not installed")
        print("📋 Install with: npm install -g @railway/cli")
        print("🔗 Or download from: https://railway.app/cli")
        return False

def railway_login():
    """Handle Railway login process"""
    print("\n🔐 Railway Login Required...")
    try:
        result = subprocess.run(["railway", "whoami"], capture_output=True, text=True)
        if "Logged in as" in result.stdout:
            print("✅ Already logged in to Railway")
            return True
        else:
            print("🌐 Opening Railway login in browser...")
            subprocess.run(["railway", "login"])
            return True
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def create_railway_files():
    """Create necessary Railway deployment files"""

    # Create railway.toml
    railway_toml = """[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"

[env]
PYTHONPATH = "/app"
PORT = "8000"
"""

    with open("railway.toml", "w") as f:
        f.write(railway_toml)
    print("✅ Created railway.toml")

    # Create Procfile for Railway
    procfile = """web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
"""

    with open("Procfile", "w") as f:
        f.write(procfile)
    print("✅ Created Procfile")

def deploy_to_railway():
    """Deploy the application to Railway"""
    print("\n🚀 Starting Railway deployment...")

    try:
        # Initialize Railway project
        print("📋 Creating Railway project...")
        result = subprocess.run(["railway", "login"], check=True)

        print("📦 Deploying to Railway...")
        result = subprocess.run(["railway", "up"], check=True)

        print("🌐 Getting deployment URL...")
        result = subprocess.run(["railway", "domain"], capture_output=True, text=True)

        if result.returncode == 0:
            url = result.stdout.strip()
            print(f"\n🎉 DEPLOYMENT SUCCESSFUL!")
            print(f"🔗 Live Demo URL: {url}")
            print(f"📱 Jorge can access from anywhere: {url}")
            return url
        else:
            print("⚠️  Deployment completed but URL not immediately available")
            print("🔍 Check Railway dashboard for your app URL")
            return "Check Railway dashboard"

    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e}")
        print("📋 Check Railway dashboard for details")
        return None

def create_env_template():
    """Create production .env template for Railway"""
    env_prod = """# Jorge's GHL AI - Railway Production Environment
# Copy your actual API keys here

ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
GHL_API_KEY=your-actual-ghl-api-key
GHL_LOCATION_ID=REDACTED_LOCATION_ID

# Railway Configuration
PORT=8000
ENVIRONMENT=production
PYTHONPATH=/app

# Optional
GHL_CALENDAR_ID=your_calendar_id_here
"""

    with open(".env.production", "w") as f:
        f.write(env_prod)
    print("✅ Created .env.production template")

def main():
    """Main deployment process"""
    print_banner()

    # Step 1: Check Railway CLI
    if not check_railway_cli():
        print("\n⏸️  Please install Railway CLI first, then run this script again")
        return False

    # Step 2: Login to Railway
    if not railway_login():
        print("\n⏸️  Please complete Railway login, then run this script again")
        return False

    # Step 3: Create deployment files
    print("\n📝 Creating deployment configuration...")
    create_railway_files()
    create_env_template()

    # Step 4: Deploy
    url = deploy_to_railway()

    if url:
        print("\n" + "="*60)
        print("🎉 JORGE'S AI IS NOW LIVE IN THE CLOUD!")
        print(f"🔗 Demo URL: {url}")
        print("📱 Accessible from any device, anywhere")
        print("🔄 Runs 24/7 without your computer")
        print("="*60)
        print("\n📋 Next Steps:")
        print("1. Test the live URL")
        print("2. Configure your production API keys in Railway dashboard")
        print("3. Share URL with Jorge for immediate access")
        return True
    else:
        print("\n⚠️  Deployment had issues. Check Railway dashboard.")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❓ Need help? Contact your original developer")
        sys.exit(1)