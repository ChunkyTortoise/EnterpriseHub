#!/usr/bin/env python3
"""
Deployment Setup Script
Sets up the environment for deployment readiness

Business Impact: Automated deployment preparation with dependency management
Author: Claude Code Agent - Deployment Specialist
Created: 2026-01-25
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json

def run_command(command, description="", check=True):
    """Run a command and handle errors"""
    print(f"🔄 {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        return False, e.stderr

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python Version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"   ❌ Python {version.major}.{version.minor} detected. Python 3.11+ required")
        return False
    print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def setup_environment_file():
    """Set up environment configuration file"""
    print("📝 Setting up Environment File...")

    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_example.exists():
        print("   ❌ .env.example not found")
        return False

    if env_file.exists():
        print("   ⚠️  .env file already exists - backing up as .env.backup")
        shutil.copy(env_file, ".env.backup")

    # Copy example to .env if it doesn't exist or is requested
    if not env_file.exists():
        shutil.copy(env_example, env_file)
        print("   ✅ Created .env from .env.example")
        print("   📝 Please edit .env with your actual API keys and configuration")
    else:
        print("   ✅ .env file exists")

    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing Dependencies...")

    # Check for requirements files
    requirements_files = [
        "requirements.txt",
        "ghl_real_estate_ai/requirements_clean.txt"
    ]

    installed = False
    for req_file in requirements_files:
        if Path(req_file).exists():
            print(f"   📋 Installing from {req_file}...")
            success, output = run_command(f"pip install -r {req_file}", f"Installing {req_file}")
            if success:
                print(f"   ✅ Successfully installed dependencies from {req_file}")
                installed = True
            else:
                print(f"   ❌ Failed to install dependencies from {req_file}")
                # Try with --break-system-packages for managed environments
                print("   🔄 Trying with --break-system-packages...")
                success, output = run_command(f"pip install -r {req_file} --break-system-packages", f"Installing {req_file} (forced)")
                if success:
                    print(f"   ✅ Successfully installed dependencies from {req_file}")
                    installed = True

    if not installed:
        print("   ❌ Could not install dependencies from any requirements file")
        return False

    # Install critical missing dependencies individually
    critical_deps = ["tiktoken", "python-dotenv", "streamlit", "anthropic"]
    for dep in critical_deps:
        print(f"   🔧 Ensuring {dep} is installed...")
        success, output = run_command(f"pip show {dep}", f"Checking {dep}", check=False)
        if not success:
            print(f"   📦 Installing {dep}...")
            success, output = run_command(f"pip install {dep}", f"Installing {dep}")
            if not success:
                # Try with --break-system-packages
                success, output = run_command(f"pip install {dep} --break-system-packages", f"Installing {dep} (forced)")

            if success:
                print(f"   ✅ {dep} installed successfully")
            else:
                print(f"   ❌ Failed to install {dep}")
        else:
            print(f"   ✅ {dep} is already installed")

    return True

def validate_environment():
    """Run environment validation"""
    print("🔍 Validating Environment Configuration...")

    # Check if validation script exists
    validator_script = Path("validate_environment.py")
    if not validator_script.exists():
        print("   ❌ validate_environment.py not found")
        return False

    success, output = run_command("python3 validate_environment.py", "Running environment validation", check=False)

    return success

def setup_docker_config():
    """Set up Docker configuration"""
    print("🐳 Checking Docker Configuration...")

    dockerfile_paths = [
        "Dockerfile",
        "ghl_real_estate_ai/Dockerfile"
    ]

    for dockerfile_path in dockerfile_paths:
        dockerfile = Path(dockerfile_path)
        if dockerfile.exists():
            print(f"   ✅ Found Dockerfile at {dockerfile_path}")

            # Check if requirements_clean.txt is referenced and exists
            with open(dockerfile, 'r') as f:
                content = f.read()
                if 'requirements_clean.txt' in content:
                    clean_req = Path("ghl_real_estate_ai/requirements_clean.txt")
                    if clean_req.exists():
                        print(f"   ✅ requirements_clean.txt exists for Docker build")
                    else:
                        print(f"   ⚠️  requirements_clean.txt referenced but not found")
        else:
            print(f"   ➖ No Dockerfile at {dockerfile_path}")

    return True

def create_deployment_checklist():
    """Create deployment checklist"""
    print("📋 Creating Deployment Checklist...")

    checklist = """
# Deployment Checklist

## Environment Setup
- [ ] Python 3.11+ installed
- [ ] All dependencies installed (requirements.txt)
- [ ] .env file configured with real API keys
- [ ] Environment validation passes

## Required API Keys
- [ ] Anthropic API key (ANTHROPIC_API_KEY)
- [ ] GoHighLevel API key (GHL_API_KEY)
- [ ] GoHighLevel Location ID (GHL_LOCATION_ID)
- [ ] Database URL configured (DATABASE_URL)
- [ ] JWT Secret key set (JWT_SECRET_KEY)

## Security Configuration
- [ ] JWT secret is 32+ characters in production
- [ ] Webhook secrets configured (32+ characters)
- [ ] Redis password set for production
- [ ] ENVIRONMENT variable set correctly

## Optional Services (Configure if needed)
- [ ] Stripe API keys for billing
- [ ] Twilio credentials for SMS
- [ ] SendGrid API key for email
- [ ] Voice AI providers (Vapi/Retell)

## Database Setup
- [ ] PostgreSQL database created
- [ ] Database migrations run
- [ ] Redis server running
- [ ] Connection pooling configured

## Testing
- [ ] Environment validation passes
- [ ] Application starts successfully
- [ ] Core features working
- [ ] API endpoints responding

## Production Deployment
- [ ] Environment set to "production"
- [ ] Debug mode disabled
- [ ] CORS configured for production domains
- [ ] Health checks configured
- [ ] Monitoring and logging set up

## Performance Optimizations
- [ ] Phase 1-4 optimizations enabled
- [ ] Token budget limits configured
- [ ] Semantic caching enabled
- [ ] Database connection pooling active

Run these commands to validate:
1. python3 setup_deployment.py
2. python3 validate_environment.py
3. streamlit run app.py

For issues, check the generated validation report.
"""

    with open("DEPLOYMENT_CHECKLIST.md", "w") as f:
        f.write(checklist.strip())

    print("   ✅ Created DEPLOYMENT_CHECKLIST.md")
    return True

def main():
    """Main deployment setup process"""
    print("🚀 ENTERPRISE HUB DEPLOYMENT SETUP")
    print("=" * 50)
    print()

    success_count = 0
    total_steps = 6

    # Step 1: Check Python version
    if check_python_version():
        success_count += 1
    print()

    # Step 2: Setup environment file
    if setup_environment_file():
        success_count += 1
    print()

    # Step 3: Install dependencies
    if install_dependencies():
        success_count += 1
    print()

    # Step 4: Setup Docker config
    if setup_docker_config():
        success_count += 1
    print()

    # Step 5: Create deployment checklist
    if create_deployment_checklist():
        success_count += 1
    print()

    # Step 6: Validate environment
    if validate_environment():
        success_count += 1
    print()

    # Final report
    print("📊 SETUP SUMMARY")
    print("=" * 30)
    print(f"✅ Completed: {success_count}/{total_steps} steps")

    if success_count == total_steps:
        print("🎉 SETUP COMPLETE - Ready for deployment!")
        print()
        print("🔄 NEXT STEPS:")
        print("   1. Edit .env with your actual API keys")
        print("   2. Run: python3 validate_environment.py")
        print("   3. Start application: streamlit run app.py")
        print("   4. Check DEPLOYMENT_CHECKLIST.md for complete guide")
        return True
    else:
        print(f"⚠️  SETUP INCOMPLETE - {total_steps - success_count} steps failed")
        print()
        print("🔄 NEXT STEPS:")
        print("   1. Review error messages above")
        print("   2. Fix any issues")
        print("   3. Run this script again")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)