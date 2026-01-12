#!/usr/bin/env python3
"""
Jorge's GHL Real Estate AI - System Verification Script
Checks that all components are ready and working
"""

import os
import sys
import importlib
import subprocess
from pathlib import Path

def print_banner():
    """Display verification banner"""
    print("=" * 60)
    print("🔍 VERIFYING JORGE'S GHL AI SYSTEM")
    print("✅ Checking all components are ready")
    print("=" * 60)

def check_python_version():
    """Verify Python version compatibility"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} - Need Python 3.8+")
        return False

def check_dependencies():
    """Check all required packages are available"""
    required_packages = [
        "streamlit",
        "anthropic",
        "requests",
        "python-dotenv",
        "pandas",
        "plotly"
    ]

    all_good = True
    print("\n📦 Checking Dependencies:")

    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - Missing")
            all_good = False

    return all_good

def check_env_file():
    """Verify environment configuration"""
    env_file = Path(".env")

    if not env_file.exists():
        print("❌ .env file missing")
        print("📋 Copy .env.example to .env and add your API keys")
        return False

    required_vars = ["ANTHROPIC_API_KEY", "GHL_API_KEY", "GHL_LOCATION_ID"]
    env_content = env_file.read_text()

    missing_vars = []
    for var in required_vars:
        if var not in env_content:
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ Environment file configured")
        return True

def check_core_files():
    """Verify all core application files exist"""
    required_files = [
        "app.py",
        "requirements.txt",
        ".env.example",
        "start_dashboard.py",
        "services/",
        "ghl_utils/"
    ]

    all_exist = True
    print("\n📁 Checking Core Files:")

    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - Missing")
            all_exist = False

    return all_exist

def test_app_import():
    """Test if the main app can be imported"""
    try:
        sys.path.insert(0, ".")
        # Test basic imports
        import streamlit as st
        print("✅ Streamlit import successful")

        # Don't fully import app.py as it might start the server
        with open("app.py", "r") as f:
            content = f.read()
            if "st.set_page_config" in content:
                print("✅ Main app.py looks valid")
                return True
            else:
                print("❌ app.py may have issues")
                return False

    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False

def check_services():
    """Verify service modules are available"""
    services_dir = Path("services")
    if not services_dir.exists():
        print("❌ Services directory missing")
        return False

    service_files = list(services_dir.glob("*.py"))
    if len(service_files) > 10:  # Should have many service files
        print(f"✅ Found {len(service_files)} service modules")
        return True
    else:
        print(f"❌ Only {len(service_files)} services found - may be incomplete")
        return False

def run_verification():
    """Run complete system verification"""
    print_banner()

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment Config", check_env_file),
        ("Core Files", check_core_files),
        ("App Structure", test_app_import),
        ("Services", check_services)
    ]

    all_passed = True

    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        if not check_func():
            all_passed = False

    print("\n" + "="*60)

    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Jorge's AI system is ready to launch")
        print("\n📋 Next Steps:")
        print("1. Run: python start_dashboard.py")
        print("2. Open: http://localhost:8501")
        print("3. Test with a lead in GHL")
        print("4. Deploy to cloud: python deploy_to_railway.py")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("📋 Fix the issues above before launching")
        print("❓ Need help? Contact your developer")

    return all_passed

def main():
    """Main verification process"""
    success = run_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()