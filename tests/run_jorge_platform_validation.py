import pytest
pytestmark = pytest.mark.integration

#!/usr/bin/env python3
"""
Jorge's Revenue Acceleration Platform - Integration Test Runner & Validator
Phase 4.1: Comprehensive End-to-End Workflow Validation

Executes all integration tests and generates detailed validation reports.

Author: Claude Code Agent Swarm
Created: 2026-01-17
"""

import asyncio
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class TestResult:
    """Test execution result"""

    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    coverage_percentage: float
    failures: List[Dict[str, str]]


@dataclass
class ValidationReport:
    """Complete validation report"""

    timestamp: datetime
    platform_version: str
    test_results: List[TestResult]
    overall_status: str
    total_tests: int
    total_passed: int
    total_failed: int
    total_duration: float
    coverage_summary: Dict[str, float]
    critical_issues: List[str]
    recommendations: List[str]


class JorgePlatformValidator:
    """
    Comprehensive validation orchestrator for Jorge's Revenue Acceleration Platform.

    Executes test suites in order:
    1. Unit tests for individual services
    2. Integration tests for cross-service workflows
    3. End-to-end tests for complete user journeys
    4. Performance benchmarks
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.test_root = Path(__file__).parent.parent
        self.results: List[TestResult] = []
        self.start_time = datetime.now()

    def run_validation(self) -> ValidationReport:
        """
        Execute complete validation suite and generate report.

        Returns:
            ValidationReport with comprehensive results
        """
        print("=" * 80)
        print("🚀 JORGE'S REVENUE ACCELERATION PLATFORM - VALIDATION SUITE")
        print("=" * 80)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Test Suite 1: Core Service Unit Tests
        print("📋 TEST SUITE 1: Core Services")
        print("-" * 80)
        self._run_test_suite(
            "Core Services Unit Tests",
            [
                "tests/services/test_dynamic_pricing_optimizer.py",
                "tests/services/test_roi_calculator_service.py",
                "tests/services/test_realtime_behavioral_network.py",
            ],
        )

        # Test Suite 2: API Integration Tests
        print("\n📋 TEST SUITE 2: API Integration")
        print("-" * 80)
        self._run_test_suite(
            "API Integration Tests",
            ["tests/api/test_pricing_optimization_routes.py", "tests/integration/test_pricing_system_integration.py"],
        )

        # Test Suite 3: End-to-End Workflow Tests
        print("\n📋 TEST SUITE 3: End-to-End Workflows")
        print("-" * 80)
        self._run_test_suite(
            "E2E Workflow Tests",
            [
                "tests/integration/test_jorge_revenue_platform_e2e.py",
                "test_jorge_integration.py",
                "test_pricing_end_to_end.py",
            ],
        )

        # Test Suite 4: Security & Performance
        print("\n📋 TEST SUITE 4: Security & Performance")
        print("-" * 80)
        self._run_test_suite("Security & Performance Tests", ["tests/security/test_jorge_webhook_security.py"])

        # Generate comprehensive report
        return self._generate_report()

    def _run_test_suite(self, suite_name: str, test_files: List[str]) -> TestResult:
        """
        Run a specific test suite.

        Args:
            suite_name: Name of the test suite
            test_files: List of test file paths relative to project root

        Returns:
            TestResult with execution details
        """
        print(f"\n🧪 Running: {suite_name}")

        # Filter to existing test files
        existing_files = []
        for test_file in test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                existing_files.append(str(test_path))
            else:
                print(f"  ⚠️  Test file not found: {test_file}")

        if not existing_files:
            print(f"  ⚠️  No test files found for {suite_name}")
            result = TestResult(
                suite_name=suite_name,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration_seconds=0.0,
                coverage_percentage=0.0,
                failures=[],
            )
            self.results.append(result)
            return result

        # Execute pytest with coverage
        start_time = datetime.now()
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            *existing_files,
            "-v",
            "--tb=short",
            "--asyncio-mode=auto",
            "--junit-xml=test-results.xml",
            "--cov=ghl_real_estate_ai",
            "--cov-report=term-missing",
            "--cov-report=json",
            "-m",
            "not slow",  # Skip slow tests for quick validation
        ]

        try:
            result_output = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_root))

            duration = (datetime.now() - start_time).total_seconds()

            # Parse pytest output
            output = result_output.stdout + result_output.stderr
            test_result = self._parse_pytest_output(suite_name, output, duration)

            # Display summary
            if test_result.failed == 0:
                print(f"  ✅ {test_result.passed}/{test_result.total_tests} tests passed")
            else:
                print(f"  ❌ {test_result.failed}/{test_result.total_tests} tests failed")

            print(f"  ⏱️  Duration: {duration:.2f}s")
            print(f"  📊 Coverage: {test_result.coverage_percentage:.1f}%")

            self.results.append(test_result)
            return test_result

        except Exception as e:
            print(f"  ❌ Error running tests: {e}")
            error_result = TestResult(
                suite_name=suite_name,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0,
                duration_seconds=0.0,
                coverage_percentage=0.0,
                failures=[{"error": str(e)}],
            )
            self.results.append(error_result)
            return error_result

    def _parse_pytest_output(self, suite_name: str, output: str, duration: float) -> TestResult:
        """
        Parse pytest output to extract test results.

        Args:
            suite_name: Name of test suite
            output: Combined stdout/stderr from pytest
            duration: Test execution duration

        Returns:
            TestResult parsed from output
        """
        # Simple parsing - look for pytest summary line
        # Example: "===== 10 passed, 2 failed, 1 skipped in 5.23s ====="

        passed = 0
        failed = 0
        skipped = 0
        failures = []

        # Parse summary line
        for line in output.split("\n"):
            if "passed" in line.lower() or "failed" in line.lower():
                # Extract numbers
                import re

                if match := re.search(r"(\d+)\s+passed", line):
                    passed = int(match.group(1))
                if match := re.search(r"(\d+)\s+failed", line):
                    failed = int(match.group(1))
                if match := re.search(r"(\d+)\s+skipped", line):
                    skipped = int(match.group(1))

        # Parse failures
        if "FAILED" in output:
            for line in output.split("\n"):
                if "FAILED" in line:
                    failures.append({"test": line.strip()})

        # Try to read coverage from json
        coverage_pct = 0.0
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    cov_data = json.load(f)
                    coverage_pct = cov_data.get("totals", {}).get("percent_covered", 0.0)
            except:
                pass

        total_tests = passed + failed + skipped

        return TestResult(
            suite_name=suite_name,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
            coverage_percentage=coverage_pct,
            failures=failures,
        )

    def _generate_report(self) -> ValidationReport:
        """
        Generate comprehensive validation report.

        Returns:
            ValidationReport with all test results and analysis
        """
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        # Aggregate results
        total_tests = sum(r.total_tests for r in self.results)
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)

        # Determine overall status
        if total_failed == 0 and total_tests > 0:
            overall_status = "PASSED"
        elif total_failed > 0:
            overall_status = "FAILED"
        else:
            overall_status = "NO_TESTS"

        # Coverage summary by service
        coverage_summary = {
            "dynamic_pricing": 0.0,  # Would be populated from coverage report
            "roi_calculator": 0.0,
            "golden_lead_detector": 0.0,
            "api_routes": 0.0,
            "overall": sum(r.coverage_percentage for r in self.results) / max(len(self.results), 1),
        }

        # Identify critical issues
        critical_issues = []
        for result in self.results:
            if result.failed > 0:
                critical_issues.append(f"{result.suite_name}: {result.failed} test(s) failed")

        # Generate recommendations
        recommendations = []
        if total_failed > 0:
            recommendations.append("Fix failing tests before production deployment")
        if coverage_summary["overall"] < 80.0:
            recommendations.append("Increase test coverage to ≥80% for production readiness")
        if total_tests < 50:
            recommendations.append("Add more integration and end-to-end tests")

        if overall_status == "PASSED":
            recommendations.append("✅ Platform ready for production deployment")
            recommendations.append("Consider adding performance benchmarking tests")
            recommendations.append("Monitor golden lead detection accuracy in production")

        report = ValidationReport(
            timestamp=end_time,
            platform_version="1.0.0",
            test_results=self.results,
            overall_status=overall_status,
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            total_duration=total_duration,
            coverage_summary=coverage_summary,
            critical_issues=critical_issues,
            recommendations=recommendations,
        )

        # Print report
        self._print_report(report)

        # Save report to file
        self._save_report(report)

        return report

    def _print_report(self, report: ValidationReport):
        """Print formatted validation report to console."""
        print("\n" + "=" * 80)
        print("📊 VALIDATION REPORT")
        print("=" * 80)
        print(f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Platform Version: {report.platform_version}")
        print(
            f"Overall Status: {'✅ ' + report.overall_status if report.overall_status == 'PASSED' else '❌ ' + report.overall_status}"
        )
        print()

        print("Test Summary:")
        print(f"  • Total Tests: {report.total_tests}")
        print(f"  • Passed: {report.total_passed}")
        print(f"  • Failed: {report.total_failed}")
        print(f"  • Duration: {report.total_duration:.2f}s")
        print()

        print("Coverage Summary:")
        for service, coverage in report.coverage_summary.items():
            status = "✅" if coverage >= 80.0 else "⚠️"
            print(f"  {status} {service}: {coverage:.1f}%")
        print()

        if report.critical_issues:
            print("Critical Issues:")
            for issue in report.critical_issues:
                print(f"  ❌ {issue}")
            print()

        print("Recommendations:")
        for rec in report.recommendations:
            print(f"  • {rec}")
        print()

        # Test suite breakdown
        print("Test Suite Breakdown:")
        print("-" * 80)
        for result in report.test_results:
            status = "✅" if result.failed == 0 and result.total_tests > 0 else "❌"
            print(f"{status} {result.suite_name}")
            print(f"   Tests: {result.passed}/{result.total_tests} passed")
            print(f"   Duration: {result.duration_seconds:.2f}s")
            print(f"   Coverage: {result.coverage_percentage:.1f}%")
            if result.failures:
                print(f"   Failures: {len(result.failures)}")
            print()

        print("=" * 80)

    def _save_report(self, report: ValidationReport):
        """Save validation report to JSON file."""
        report_file = self.project_root / "jorge_platform_validation_report.json"

        report_dict = {
            "timestamp": report.timestamp.isoformat(),
            "platform_version": report.platform_version,
            "overall_status": report.overall_status,
            "summary": {
                "total_tests": report.total_tests,
                "total_passed": report.total_passed,
                "total_failed": report.total_failed,
                "total_duration": report.total_duration,
            },
            "coverage_summary": report.coverage_summary,
            "test_results": [asdict(r) for r in report.test_results],
            "critical_issues": report.critical_issues,
            "recommendations": report.recommendations,
        }

        with open(report_file, "w") as f:
            json.dump(report_dict, f, indent=2)

        print(f"📄 Report saved to: {report_file}")


def main():
    """Main entry point for validation runner."""
    validator = JorgePlatformValidator()

    try:
        report = validator.run_validation()

        # Exit with appropriate code
        if report.overall_status == "PASSED":
            print("\n🎉 ALL VALIDATIONS PASSED - Platform Ready for Production!")
            sys.exit(0)
        else:
            print(f"\n❌ VALIDATION FAILED - {report.total_failed} test(s) failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
