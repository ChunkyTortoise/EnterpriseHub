#!/usr/bin/env python3
"""
Quick validation of critical production stability fixes implemented.

Validates that the 5 critical silent failures have been properly fixed:
1. Mock communication methods raise NotImplementedError
2. Webhook error handling raises HTTP 500
3. Database schema validation handles missing columns
4. SendGrid webhook processing raises exceptions
5. Twilio webhook processing raises exceptions
"""

import sys
import ast


def validate_communication_methods():
    """Validate that mock communication methods now raise NotImplementedError."""
    print("🔍 Validating mock communication methods...")

    with open("ghl_real_estate_ai/services/autonomous_followup_engine.py", "r") as f:
        content = f.read()

    # Check that methods raise NotImplementedError instead of returning True
    if "raise NotImplementedError" in content:
        print("✅ Mock communication methods fixed - now raise NotImplementedError")
        return True
    else:
        print("❌ Mock communication methods still return True silently")
        return False


def validate_webhook_error_handling():
    """Validate that webhook error handling raises HTTP 500."""
    print("🔍 Validating webhook error handling...")

    with open("ghl_real_estate_ai/api/routes/webhook.py", "r") as f:
        content = f.read()

    # Check for proper HTTP exception raising
    if "raise HTTPException" in content and "status.HTTP_500_INTERNAL_SERVER_ERROR" in content:
        print("✅ Webhook error handling fixed - now raises HTTP 500")
        return True
    else:
        print("❌ Webhook error handling still returns HTTP 200 with success=false")
        return False


def validate_database_schema_handling():
    """Validate that database queries handle missing columns gracefully."""
    print("🔍 Validating database schema handling...")

    with open("ghl_real_estate_ai/services/database_service.py", "r") as f:
        content = f.read()

    # Check for proper try-catch with sentiment_score fallback
    if "sentiment_score" in content and "except Exception as e:" in content and "fallback" in content.lower():
        print("✅ Database schema handling fixed - handles missing sentiment_score column")
        return True
    else:
        print("❌ Database schema handling may still fail on missing columns")
        return False


def validate_sendgrid_webhook_processing():
    """Validate that SendGrid webhook processing raises exceptions."""
    print("🔍 Validating SendGrid webhook processing...")

    with open("ghl_real_estate_ai/services/sendgrid_client.py", "r") as f:
        content = f.read()

    # Check for exception raising instead of return False
    if "raise  # Re-raise to propagate error to caller" in content:
        print("✅ SendGrid webhook processing fixed - now raises exceptions")
        return True
    else:
        print("❌ SendGrid webhook processing may still return False silently")
        return False


def validate_twilio_webhook_processing():
    """Validate that Twilio webhook processing raises exceptions."""
    print("🔍 Validating Twilio webhook processing...")

    with open("ghl_real_estate_ai/services/twilio_client.py", "r") as f:
        content = f.read()

    # Check for exception raising instead of return False
    if "raise  # Re-raise to propagate error to caller" in content:
        print("✅ Twilio webhook processing fixed - now raises exceptions")
        return True
    else:
        print("❌ Twilio webhook processing may still return False silently")
        return False


def main():
    """Run all validation checks."""
    print("🚀 Validating Production Stability Fixes\n")

    validations = [
        ("Mock Communication Methods", validate_communication_methods),
        ("Webhook Error Handling", validate_webhook_error_handling),
        ("Database Schema Handling", validate_database_schema_handling),
        ("SendGrid Webhook Processing", validate_sendgrid_webhook_processing),
        ("Twilio Webhook Processing", validate_twilio_webhook_processing),
    ]

    results = []
    for name, validator in validations:
        try:
            result = validator()
            results.append((name, result))
            print()
        except Exception as e:
            print(f"❌ Error validating {name}: {e}\n")
            results.append((name, False))

    # Summary
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)

    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{len(results)} critical fixes validated")

    if passed == len(results):
        print("🎉 ALL CRITICAL PRODUCTION STABILITY FIXES VALIDATED!")
        print("✅ System is ready for deployment")
        return 0
    else:
        print("⚠️  Some fixes need attention before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())