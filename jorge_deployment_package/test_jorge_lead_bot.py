#!/usr/bin/env python3
"""
Test the updated Jorge Lead Bot with the Tesla VP case
"""

import asyncio
import sys
from jorge_lead_bot import create_jorge_lead_bot

async def test_tesla_vp_lead():
    """Test the Tesla VP lead case that was failing"""

    # Tesla VP test case
    test_message = "Sarah Martinez, VP at Tesla, $750k budget, Westlake Hills, pre-approved, 45 days"
    test_contact_id = "test_sarah_martinez"
    test_location_id = "test_austin"

    print("=== JORGE LEAD BOT OPTIMIZATION TEST ===")
    print(f"Input: {test_message}")
    print()

    # Create Jorge's lead bot
    lead_bot = create_jorge_lead_bot()

    try:
        # Process the lead message
        result = await lead_bot.process_lead_message(
            contact_id=test_contact_id,
            location_id=test_location_id,
            message=test_message,
            contact_data={"firstName": "Sarah", "lastName": "Martinez"}
        )

        print("=== JORGE'S RESULTS (Fixed) ===")
        print(f"Lead Score: {result.get('lead_score', 'N/A')}")
        print(f"Temperature: {result.get('lead_temperature', 'N/A')}")
        print(f"Budget Detected: ${result.get('budget_max', 'N/A'):,}" if result.get('budget_max') else "Budget: Not detected")
        print(f"Timeline Detected: {result.get('timeline', 'N/A')}")
        print(f"Location: {result.get('location_preferences', 'N/A')}")
        print(f"Pre-approved: {result.get('analytics', {}).get('is_pre_approved', 'N/A')}")
        print(f"Priority: Priority-{result.get('analytics', {}).get('priority', 'unknown').title()}")
        print()

        print("=== JORGE'S RESPONSE ===")
        jorge_response = result.get('message', result.get('response', 'No response'))
        print(f'"{jorge_response}"')
        print()

        print("=== ACTIONS TRIGGERED ===")
        actions = result.get('actions', [])
        for action in actions:
            print(f"- {action}")
        print()

        print("=== COMPARISON WITH REQUIREMENTS ===")
        requirements = {
            "Lead Score": ("90+", result.get('lead_score', 0)),
            "Temperature": ("HOT", result.get('lead_temperature', 'COLD')),
            "Budget Detection": ("$750,000", f"${result.get('budget_max', 0):,}" if result.get('budget_max') else "Failed"),
            "Timeline Detection": ("45 days → 2_months", result.get('timeline', 'Failed')),
            "Jorge Response": ("Generated", "Generated" if jorge_response and jorge_response != "No response" else "Failed"),
            "Priority": ("Priority-High", f"Priority-{result.get('analytics', {}).get('priority', 'unknown').title()}")
        }

        print("Requirement | Expected | Actual | Status")
        print("-" * 50)
        for req, (expected, actual) in requirements.items():
            if req == "Lead Score":
                status = "✅ PASS" if float(actual) >= 90 else "❌ FAIL"
            elif req == "Temperature":
                status = "✅ PASS" if actual == "HOT" else "❌ FAIL"
            elif req == "Budget Detection":
                status = "✅ PASS" if "$750,000" in str(actual) else "❌ FAIL"
            elif req == "Timeline Detection":
                status = "✅ PASS" if "2_months" in str(actual) else "❌ FAIL"
            elif req == "Jorge Response":
                status = "✅ PASS" if "Generated" in str(actual) else "❌ FAIL"
            elif req == "Priority":
                status = "✅ PASS" if "High" in str(actual) else "❌ FAIL"
            else:
                status = "✅ PASS" if expected == actual else "❌ FAIL"

            print(f"{req:<15} | {expected:<12} | {actual:<12} | {status}")

        return result

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_webhook_simulation():
    """Test simulating what the webhook server would do"""

    print("\n=== WEBHOOK SIMULATION TEST ===")

    test_message = "Sarah Martinez, VP at Tesla, $750k budget, Westlake Hills, pre-approved, 45 days"

    # Simulate webhook server processing
    from jorge_webhook_server import determine_lead_type, lead_bot

    lead_type = determine_lead_type(test_message)
    print(f"Detected Lead Type: {lead_type}")

    if lead_type == "lead":
        result = await lead_bot.process_lead_message(
            contact_id="webhook_test_sarah",
            location_id="webhook_test_location",
            message=test_message
        )

        print(f"Webhook Response Structure:")
        webhook_response = {
            "status": "processed",
            "type": "lead",
            "score": result.get("lead_score", 0),
            "temperature": result.get("lead_temperature", "cold"),
            "response_sent": bool(result.get("message"))
        }

        for key, value in webhook_response.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_tesla_vp_lead())

    # Run webhook simulation
    asyncio.run(test_webhook_simulation())

    if result and result.get('lead_score', 0) >= 90:
        print("\n🎉 SUCCESS: Jorge's lead bot is now optimized!")
        sys.exit(0)
    else:
        print("\n❌ NEEDS MORE WORK: Some requirements not met")
        sys.exit(1)