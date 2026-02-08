import asyncio
import os

from ghl_real_estate_ai.agent_system.skills.visual_qa import VisualRegressionAgent


async def test_visual_qa():
    print("🚀 Testing Visual QA Infrastructure...")

    agent = VisualRegressionAgent()

    # 1. Test Screenshot Capture
    # We will try to capture a public site since our local server might not be up
    print("📸 Testing screenshot capture (Google.com)...")
    path = await agent.capture_screenshot(url="https://www.google.com", filename="test_google.png")

    if path and os.path.exists(path):
        print(f"✅ Screenshot captured at: {path}")
    else:
        print("❌ Screenshot capture failed!")
        return

    # 2. Test Gemini Vision Analysis
    print("🧠 Testing Gemini Vision analysis...")
    spec = "A search engine page with a central search bar and two buttons below it."

    analysis = await agent.analyze_with_vision(path, spec)

    print("\n🔍 Vision Analysis Result:")
    import json

    print(json.dumps(analysis, indent=2))

    if "error" not in analysis:
        print("\n✅ Visual QA logic is fully operational!")
    else:
        print("❌ Vision analysis failed!")


if __name__ == "__main__":
    asyncio.run(test_visual_qa())
