#!/usr/bin/env python3
"""
Buyer Bot Test Suite Runner
Validates Jorge's Buyer Bot ecosystem implementation with comprehensive testing.

Usage:
    python tests/run_buyer_bot_tests.py [--coverage] [--verbose] [--integration]
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(command: List[str], description: str) -> Dict[str, Any]:
    """Run a command and return results."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=project_root
        )

        print(f"Command: {' '.join(command)}")
        print(f"Exit code: {result.returncode}")

        if result.stdout:
            print(f"\nSTDOUT:\n{result.stdout}")

        if result.stderr:
            print(f"\nSTDERR:\n{result.stderr}")

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command
        }

    except Exception as e:
        print(f"❌ Error running command: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": command
        }

def validate_buyer_bot_files():
    """Validate that all buyer bot files exist."""
    print("\n🔍 Validating Buyer Bot Files...")

    required_files = [
        "ghl_real_estate_ai/models/buyer_bot_state.py",
        "ghl_real_estate_ai/agents/buyer_intent_decoder.py",
        "ghl_real_estate_ai/agents/jorge_buyer_bot.py",
        "ghl_real_estate_ai/services/sms_compliance_service.py",
        "ghl_real_estate_ai/api/routes/sms_compliance.py",
        "tests/agents/test_buyer_bot.py",
        "tests/services/test_sms_compliance_service.py",
        "tests/integration/test_buyer_bot_integration.py"
    ]

    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")

    if missing_files:
        print(f"\n❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False

    print(f"\n✅ All {len(required_files)} buyer bot files are present")
    return True

def validate_imports():
    """Validate that all imports work correctly."""
    print("\n🔍 Validating Imports...")

    import_tests = [
        "from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState",
        "from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile",
        "from ghl_real_estate_ai.agents.buyer_intent_decoder import BuyerIntentDecoder",
        "from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot",
        "from ghl_real_estate_ai.services.sms_compliance_service import SMSComplianceService, OptOutReason",
        "from ghl_real_estate_ai.api.routes.sms_compliance import router",
    ]

    failed_imports = []
    for import_statement in import_tests:
        try:
            exec(import_statement)
            print(f"✅ {import_statement}")
        except Exception as e:
            print(f"❌ {import_statement} - {e}")
            failed_imports.append((import_statement, str(e)))

    if failed_imports:
        print(f"\n❌ {len(failed_imports)} import failures")
        return False

    print(f"\n✅ All imports successful")
    return True

def run_unit_tests(verbose: bool = False) -> Dict[str, Any]:
    """Run unit tests for buyer bot components."""
    command = [
        sys.executable, "-m", "pytest",
        "tests/agents/test_buyer_bot.py",
        "tests/services/test_sms_compliance_service.py",
        "-v" if verbose else "-q",
        "--tb=short"
    ]

    return run_command(command, "Running Unit Tests")

def run_integration_tests(verbose: bool = False) -> Dict[str, Any]:
    """Run integration tests for buyer bot workflows."""
    command = [
        sys.executable, "-m", "pytest",
        "tests/integration/test_buyer_bot_integration.py",
        "-v" if verbose else "-q",
        "--tb=short",
        "-m", "not slow"  # Skip slow integration tests by default
    ]

    return run_command(command, "Running Integration Tests")

def run_coverage_tests() -> Dict[str, Any]:
    """Run tests with coverage analysis."""
    command = [
        sys.executable, "-m", "pytest",
        "tests/agents/test_buyer_bot.py",
        "tests/services/test_sms_compliance_service.py",
        "tests/integration/test_buyer_bot_integration.py",
        "--cov=ghl_real_estate_ai.agents.jorge_buyer_bot",
        "--cov=ghl_real_estate_ai.agents.buyer_intent_decoder",
        "--cov=ghl_real_estate_ai.services.sms_compliance_service",
        "--cov=ghl_real_estate_ai.models.buyer_bot_state",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/buyer_bot",
        "--cov-fail-under=80"
    ]

    return run_command(command, "Running Coverage Analysis")

def validate_orchestrator_integration():
    """Validate that orchestrator integration works."""
    print("\n🔍 Validating Orchestrator Integration...")

    try:
        from ghl_real_estate_ai.agents.enhanced_bot_orchestrator import EnhancedBotOrchestrator
        from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

        # Try to create orchestrator (should import buyer bot)
        orchestrator = EnhancedBotOrchestrator()
        print("✅ Orchestrator imports buyer bot successfully")

        # Check if buyer conversation method exists
        if hasattr(orchestrator, '_orchestrate_buyer_conversation'):
            print("✅ Buyer conversation orchestration method exists")
        else:
            print("❌ Buyer conversation orchestration method missing")
            return False

        return True

    except Exception as e:
        print(f"❌ Orchestrator integration failed: {e}")
        return False

def validate_event_publisher_integration():
    """Validate event publisher has buyer-specific methods."""
    print("\n🔍 Validating Event Publisher Integration...")

    try:
        from ghl_real_estate_ai.services.event_publisher import EventPublisher
        from ghl_real_estate_ai.services.websocket_server import EventType

        # Check for buyer-specific event types
        buyer_events = [
            "BUYER_INTENT_ANALYSIS",
            "BUYER_QUALIFICATION_PROGRESS",
            "BUYER_QUALIFICATION_COMPLETE",
            "SMS_COMPLIANCE"
        ]

        missing_events = []
        for event in buyer_events:
            if hasattr(EventType, event):
                print(f"✅ Event type: {event}")
            else:
                print(f"❌ Missing event type: {event}")
                missing_events.append(event)

        if missing_events:
            print(f"\n❌ Missing {len(missing_events)} event types")
            return False

        # Check for buyer-specific methods
        publisher = EventPublisher()
        buyer_methods = [
            "publish_buyer_intent_analysis",
            "publish_buyer_qualification_progress",
            "publish_buyer_qualification_complete",
            "publish_sms_compliance_event"
        ]

        missing_methods = []
        for method in buyer_methods:
            if hasattr(publisher, method):
                print(f"✅ Publisher method: {method}")
            else:
                print(f"❌ Missing publisher method: {method}")
                missing_methods.append(method)

        if missing_methods:
            print(f"\n❌ Missing {len(missing_methods)} publisher methods")
            return False

        print("✅ Event publisher integration complete")
        return True

    except Exception as e:
        print(f"❌ Event publisher validation failed: {e}")
        return False

def generate_test_report(results: Dict[str, Any]):
    """Generate comprehensive test report."""
    print("\n" + "="*80)
    print("📊 BUYER BOT TEST REPORT")
    print("="*80)

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for test_name, result in results.items():
        print(f"\n{test_name}:")

        if result["success"]:
            print(f"  ✅ PASSED")
            passed_tests += 1
        else:
            print(f"  ❌ FAILED")
            if "error" in result:
                print(f"     Error: {result['error']}")
            failed_tests += 1

        total_tests += 1

    print(f"\n{'='*80}")
    print(f"📈 SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! Buyer bot implementation is ready for deployment.")
        return True
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed. Please review and fix issues before deployment.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run Jorge's Buyer Bot test suite")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage analysis")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--quick", action="store_true", help="Run only quick validation tests")

    args = parser.parse_args()

    print("🚀 Jorge's Buyer Bot Test Suite")
    print("="*80)

    results = {}

    # File validation
    results["File Validation"] = {"success": validate_buyer_bot_files()}

    # Import validation
    results["Import Validation"] = {"success": validate_imports()}

    # Integration validation
    results["Orchestrator Integration"] = {"success": validate_orchestrator_integration()}
    results["Event Publisher Integration"] = {"success": validate_event_publisher_integration()}

    if not args.quick:
        # Unit tests
        results["Unit Tests"] = run_unit_tests(args.verbose)

        # Integration tests (if requested)
        if args.integration:
            results["Integration Tests"] = run_integration_tests(args.verbose)

        # Coverage analysis (if requested)
        if args.coverage:
            results["Coverage Analysis"] = run_coverage_tests()

    # Generate final report
    success = generate_test_report(results)

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()