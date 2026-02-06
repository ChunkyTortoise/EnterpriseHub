#!/usr/bin/env python3
"""
Install ML Dependencies for Jorge AI System
Helper script to ensure all ML dependencies are properly installed
"""

import subprocess
import sys

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return False

def main():
    """Install ML dependencies"""
    print("🚀 Installing ML Dependencies for Jorge AI System")
    print("=" * 60)

    # Check if pip is available
    if not run_command("pip --version", "Checking pip availability"):
        print("\n❌ pip not found. Please install pip first.")
        return 1

    # Install core ML dependencies
    dependencies = [
        ("scikit-learn==1.4.0", "Installing scikit-learn for ML models"),
        ("joblib==1.3.2", "Installing joblib for model serialization"),
        ("shap==0.43.0", "Installing SHAP for model explainability"),
        ("sqlalchemy>=2.0.0", "Installing SQLAlchemy for database integration")
    ]

    success_count = 0
    for package, description in dependencies:
        if run_command(f"pip install {package}", description):
            success_count += 1

    print(f"\n📊 Installation Summary: {success_count}/{len(dependencies)} packages installed")

    if success_count == len(dependencies):
        print("🎉 All ML dependencies installed successfully!")
        print("\n🧪 Run validation: python validate_ml_integration.py")
        return 0
    else:
        print("⚠️ Some dependencies failed to install")
        print("   Try installing manually with: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())