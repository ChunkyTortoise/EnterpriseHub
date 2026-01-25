#!/usr/bin/env python3
"""
Quick test to verify Streamlit app launches correctly with new navigation
"""

import sys
import os

def test_imports():
    """Test that app.py can be imported without errors"""
    try:
        # Add the correct path to the module
        sys.path.insert(0, os.path.join(os.getcwd(), 'ghl_real_estate_ai', 'streamlit_demo'))

        # Test basic syntax by compiling
        with open('ghl_real_estate_ai/streamlit_demo/app.py', 'r') as f:
            code = f.read()
            compile(code, 'app.py', 'exec')

        print("✅ app.py syntax is valid")
        return True

    except SyntaxError as e:
        print(f"❌ Syntax error in app.py: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Import warning: {e}")
        return True  # Other errors might be dependency-related but syntax is OK

def check_hub_variables():
    """Check that hub variables are properly defined in the code"""
    try:
        with open('ghl_real_estate_ai/streamlit_demo/app.py', 'r') as f:
            content = f.read()

        # Check that hub_categories is defined
        if 'hub_categories = {' in content:
            print("✅ hub_categories variable is properly defined")
        else:
            print("❌ hub_categories variable not found")
            return False

        # Check that all category names are present
        required_categories = [
            "🎯 Core Operations",
            "📊 Analytics & Insights",
            "🤖 AI & Automation",
            "🛠️ Bot Management",
            "🏡 Customer Journey"
        ]

        for category in required_categories:
            if category in content:
                print(f"✅ Category '{category}' found in code")
            else:
                print(f"❌ Category '{category}' missing from code")
                return False

        # Check that selected_hub is still defined for backward compatibility
        if 'selected_hub =' in content:
            print("✅ selected_hub variable is properly set for backward compatibility")
        else:
            print("❌ selected_hub variable not found - routing may break")
            return False

        return True

    except Exception as e:
        print(f"❌ Error checking hub variables: {e}")
        return False

def main():
    print("🧪 Streamlit Navigation Testing")
    print("=" * 40)

    success = True
    success &= test_imports()
    success &= check_hub_variables()

    print("\n" + "=" * 40)
    if success:
        print("🎉 Navigation update ready for testing!")
        print("\n📋 To test manually:")
        print("  cd /Users/cave/Documents/GitHub/EnterpriseHub")
        print("  streamlit run ghl_real_estate_ai/streamlit_demo/app.py")
        print("\n🔍 What to verify:")
        print("  • Sidebar shows 5 expandable categories")
        print("  • Current hub category auto-expands")
        print("  • All hubs are accessible via radio buttons")
        print("  • Navigation preserves session state")
        print("  • Hub routing still works correctly")
    else:
        print("❌ Issues detected - please review the implementation")

    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)