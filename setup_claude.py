"""
Setup Script for Claude AI Integration

Quick setup script to configure Claude AI services for the GHL Real Estate platform.
Run this script to test Claude integration and verify API connectivity.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent / "ghl_real_estate_ai"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def check_api_key():
    """Check if Claude API key is configured."""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")

    if not api_key:
        print("❌ No Claude API key found!")
        print("\n🔧 Setup Required:")
        print("   1. Get API key from https://console.anthropic.com")
        print("   2. Set environment variable: ANTHROPIC_API_KEY=your_key_here")
        print("   3. Or add to your .env file: ANTHROPIC_API_KEY=your_key_here")
        print("\n💡 For development:")
        print("   export ANTHROPIC_API_KEY=your_key_here")
        return False
    else:
        print("✅ Claude API key configured!")
        print(f"   Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else 'short_key'}")
        return True

async def test_claude_services():
    """Test Claude services connectivity."""
    print("\n🧪 Testing Claude Services...")

    try:
        from services.claude_semantic_analyzer import get_semantic_analyzer

        analyzer = get_semantic_analyzer()

        # Test basic connectivity
        health_check = await analyzer.health_check()

        if health_check.get("status") == "healthy":
            print("✅ Claude Semantic Analyzer: HEALTHY")
        else:
            print(f"❌ Claude Semantic Analyzer: {health_check.get('error', 'Unknown error')}")

        await analyzer.close()

    except Exception as e:
        print(f"❌ Claude Services Error: {e}")
        return False

    print("\n🎯 Testing Lead Intelligence...")

    try:
        from services.claude_lead_qualification_engine import ClaudeLeadQualificationEngine

        # Test with sample data
        sample_lead = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "555-1234",
            "budget": 400000,
            "timeline": "3 months",
            "location": "Austin, TX"
        }

        engine = ClaudeLeadQualificationEngine()
        result = await engine.qualify_lead(
            lead_data=sample_lead,
            source_type="test",
            agent_id="test_agent"
        )

        print(f"✅ Lead Qualification Test: Score {result.qualification_score}/100")
        print(f"   Priority: {result.priority_level.value}")

    except Exception as e:
        print(f"❌ Lead Intelligence Error: {e}")
        return False

    return True

async def test_conversational_interface():
    """Test conversational interface."""
    print("\n💬 Testing Conversational Interface...")

    try:
        from streamlit_components.claude_conversational_interface import ClaudeConversationalInterface

        interface = ClaudeConversationalInterface()

        # Test message processing
        test_message = "Analyze this lead for qualification score"
        test_context = {"current_section": "lead_intelligence"}
        test_lead = {
            "name": "Sample Lead",
            "email": "sample@test.com",
            "budget": 350000
        }

        response = await interface.process_user_message(test_message, test_context, test_lead)

        print(f"✅ Conversational Interface: Working")
        print(f"   Intent: {response['intent']}")
        print(f"   Confidence: {response['confidence']}")

    except Exception as e:
        print(f"❌ Conversational Interface Error: {e}")
        return False

    return True

def test_streamlit_integration():
    """Test Streamlit app integration."""
    print("\n📱 Checking Streamlit Integration...")

    app_file = Path(__file__).parent / "app.py"

    if not app_file.exists():
        print("❌ app.py not found")
        return False

    # Check if Claude imports are in app.py
    content = app_file.read_text()

    if "claude_conversational_interface" in content:
        print("✅ Claude interface integrated in app.py")
    else:
        print("❌ Claude interface not found in app.py")
        return False

    if "Claude AI Assistant" in content:
        print("✅ Claude greeting and context awareness added")
    else:
        print("⚠️  Claude context awareness may not be fully integrated")

    return True

async def main():
    """Main setup and test function."""
    print("🚀 Claude AI Integration Setup & Test")
    print("=====================================\n")

    # Step 1: Check API key
    if not check_api_key():
        print("\n❌ Setup incomplete. Please configure API key first.")
        return

    # Step 2: Test services
    services_ok = await test_claude_services()

    # Step 3: Test conversational interface
    interface_ok = await test_conversational_interface()

    # Step 4: Test Streamlit integration
    streamlit_ok = test_streamlit_integration()

    print("\n" + "="*50)
    print("📊 SETUP SUMMARY:")
    print("="*50)
    print(f"🔑 API Key:              {'✅ Configured' if check_api_key() else '❌ Missing'}")
    print(f"🧠 Claude Services:      {'✅ Working' if services_ok else '❌ Issues'}")
    print(f"💬 Chat Interface:       {'✅ Working' if interface_ok else '❌ Issues'}")
    print(f"📱 Streamlit App:        {'✅ Integrated' if streamlit_ok else '❌ Issues'}")

    if all([services_ok, interface_ok, streamlit_ok]):
        print("\n🎉 SUCCESS! Claude AI is fully integrated and ready!")
        print("\nTo start the app:")
        print("   streamlit run app.py")
        print("\nClaude will greet you when you open the app and provide")
        print("contextual assistance throughout, especially in Lead Intelligence!")
    else:
        print("\n⚠️  Some issues detected. Please check the errors above.")

    print("\n💡 Pro tip: Navigate to 'Lead Intelligence Hub' for the full")
    print("   Claude conversational experience with lead analysis!")

if __name__ == "__main__":
    asyncio.run(main())