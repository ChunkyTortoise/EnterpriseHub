import pytest

pytestmark = pytest.mark.integration

#!/usr/bin/env python3
"""
Service 6 Critical Test Runner
=============================

Runs the most critical test files for immediate production readiness validation.
Focus on core functionality with specific coverage targets.

Usage:
    python tests/run_service6_critical_tests.py
    python tests/run_service6_critical_tests.py --coverage
    python tests/run_service6_critical_tests.py --performance
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def run_test_suite(test_file, coverage_target=None, show_coverage=False):
    """Run a specific test suite with optional coverage reporting."""

    print(f"\n🧪 Running {test_file}")
    print("=" * 60)

    # Build pytest command
    cmd = ["python", "-m", "pytest", test_file, "-v"]

    if show_coverage:
        # Extract service name from test file for coverage
        if "service6_ai_integration" in test_file:
            service_module = "ghl_real_estate_ai.services.service6_ai_integration"
        elif "realtime_behavioral_network" in test_file:
            service_module = "ghl_real_estate_ai.services.realtime_behavioral_network"
        elif "end_to_end" in test_file:
            service_module = "ghl_real_estate_ai.services"
        else:
            service_module = "ghl_real_estate_ai.services"

        cmd.extend([f"--cov={service_module}", "--cov-report=term-missing", "--cov-report=html:tests/coverage/html"])

        if coverage_target:
            cmd.append(f"--cov-fail-under={coverage_target}")

    # Add performance markers
    cmd.extend(
        [
            "-m",
            "not slow",  # Skip slow tests by default
            "--tb=short",  # Shorter traceback for cleaner output
        ]
    )

    start_time = time.time()
    try:
        result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=False)
        execution_time = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ {test_file} PASSED in {execution_time:.1f}s")
            if coverage_target:
                print(f"   Coverage target: {coverage_target}% ✓")
        else:
            print(f"❌ {test_file} FAILED in {execution_time:.1f}s")
            return False

    except Exception as e:
        print(f"💥 Error running {test_file}: {e}")
        return False

    return True


def run_performance_benchmarks():
    """Run performance-focused tests."""

    print("\n⚡ Running Performance Benchmarks")
    print("=" * 60)

    perf_cmd = [
        "python",
        "-m",
        "pytest",
        "tests/services/test_service6_ai_integration.py::TestPerformanceBenchmarks",
        "tests/services/test_realtime_behavioral_network.py::TestPerformanceMetrics",
        "tests/integration/test_service6_end_to_end.py::TestService6EndToEndWorkflows::test_high_intent_lead_fast_track_workflow",
        "-v",
        "--tb=short",
    ]

    start_time = time.time()
    result = subprocess.run(perf_cmd, cwd=Path.cwd())
    execution_time = time.time() - start_time

    if result.returncode == 0:
        print(f"✅ Performance benchmarks PASSED in {execution_time:.1f}s")
    else:
        print(f"❌ Performance benchmarks FAILED")

    return result.returncode == 0


def validate_test_dependencies():
    """Validate that all required test dependencies are available."""

    print("🔍 Validating test dependencies...")

    required_packages = ["pytest", "pytest-asyncio", "pytest-cov"]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install pytest pytest-asyncio pytest-cov")
        return False

    print("✅ All test dependencies available")
    return True


def main():
    """Main test execution function."""

    parser = argparse.ArgumentParser(description="Run Service 6 critical tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--performance", action="store_true", help="Run performance benchmarks only")
    parser.add_argument("--fast", action="store_true", help="Skip coverage and run faster")

    args = parser.parse_args()

    print("🎯 Service 6 Critical Test Suite")
    print("=" * 60)
    print("Target: Validate production readiness of core Service 6 components")

    # Validate dependencies first
    if not validate_test_dependencies():
        sys.exit(1)

    # Performance benchmarks only
    if args.performance:
        success = run_performance_benchmarks()
        sys.exit(0 if success else 1)

    # Define critical test files with coverage targets
    critical_tests = [
        {
            "file": "tests/services/test_service6_ai_integration.py",
            "coverage_target": 90,
            "description": "Core AI Integration Service",
        },
        {
            "file": "tests/services/test_realtime_behavioral_network.py",
            "coverage_target": 85,
            "description": "Real-time Behavioral Network (5 TODO methods)",
        },
        {
            "file": "tests/integration/test_service6_end_to_end.py",
            "coverage_target": None,  # Integration tests don't need coverage targets
            "description": "End-to-End Workflow Validation",
        },
    ]

    # Run each critical test suite
    all_passed = True
    start_time = time.time()

    for test_config in critical_tests:
        test_file = test_config["file"]
        coverage_target = test_config["coverage_target"] if not args.fast else None
        show_coverage = args.coverage and not args.fast

        print(f"\n📋 {test_config['description']}")

        if not Path(test_file).exists():
            print(f"❌ Test file not found: {test_file}")
            all_passed = False
            continue

        success = run_test_suite(test_file, coverage_target, show_coverage)
        if not success:
            all_passed = False

    # Run performance benchmarks if requested
    if args.coverage and not args.fast:
        perf_success = run_performance_benchmarks()
        if not perf_success:
            all_passed = False

    total_time = time.time() - start_time

    # Final results
    print(f"\n{'=' * 60}")
    print("🎯 Service 6 Critical Test Results")
    print(f"{'=' * 60}")

    if all_passed:
        print("✅ ALL CRITICAL TESTS PASSED")
        print(f"⏱️  Total execution time: {total_time:.1f}s")
        print("\n🚀 Service 6 is ready for production deployment!")

        if args.coverage:
            print("\n📊 Coverage reports generated:")
            print("   • HTML: tests/coverage/html/index.html")
            print("   • Terminal output above")

    else:
        print("❌ SOME CRITICAL TESTS FAILED")
        print(f"⏱️  Total execution time: {total_time:.1f}s")
        print("\n🔧 Fix failing tests before production deployment")

    # Coverage summary if available
    coverage_file = Path("tests/coverage/html/index.html")
    if coverage_file.exists() and args.coverage:
        print(f"\n🔗 Open coverage report: file://{coverage_file.absolute()}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
