#!/usr/bin/env python3
"""
Quick test runner for Autonomous Deal Orchestration system.
Run this script to execute all tests and get a deployment readiness report.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run all orchestration tests."""
    print("🏠 Autonomous Deal Orchestration System - Test Runner")
    print("=" * 60)

    try:
        # Import and run the comprehensive test suite
        from tests.test_autonomous_orchestration_suite import main as run_tests

        results = run_tests()

        # Print quick summary
        if results["overall_status"]["ready_for_deployment"]:
            print("\n🎉 SUCCESS: System ready for deployment!")
            return 0
        else:
            print("\n❌ FAILURE: System not ready - fix issues and retry")
            return 1

    except ImportError as e:
        print(f"❌ Error importing test modules: {e}")
        print("Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)