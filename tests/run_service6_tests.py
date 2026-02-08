#!/usr/bin/env python3

"""
🧪 Service 6 Test Execution Suite - Comprehensive Test Runner
============================================================

Comprehensive test execution framework for Service 6 with multiple modes:
- unit: Fast isolated tests for individual components
- integration: Cross-service workflow testing
- performance: Load testing and latency benchmarks
- security: Vulnerability and data validation testing
- full: Complete test suite with coverage reporting

Features:
- Parallel test execution for speed
- Real-time progress reporting
- Detailed performance metrics
- Coverage analysis with thresholds
- CI/CD integration ready
- Custom test filtering and tagging

Usage:
    python tests/run_service6_tests.py [mode] [options]

Examples:
    python tests/run_service6_tests.py unit                    # Fast unit tests
    python tests/run_service6_tests.py integration             # Integration tests
    python tests/run_service6_tests.py performance             # Performance benchmarks
    python tests/run_service6_tests.py full --coverage         # Full suite with coverage
    python tests/run_service6_tests.py unit --parallel=4       # Parallel execution
    python tests/run_service6_tests.py --filter="test_service6_ai"  # Filtered tests

Author: Claude AI Enhancement System
Date: 2026-01-17
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import colorama
from colorama import Back, Fore, Style

# Initialize colorama for cross-platform colored output
colorama.init(autoreset=True)

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class TestResult:
    """Test execution result data"""

    mode: str
    test_file: str
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    coverage_percentage: Optional[float] = None
    errors: List[str] = None
    warnings: List[str] = None


@dataclass
class TestSuiteReport:
    """Complete test suite execution report"""

    total_tests: int
    total_passed: int
    total_failed: int
    total_skipped: int
    total_duration_seconds: float
    overall_coverage_percentage: Optional[float] = None
    test_results: List[TestResult] = None
    performance_metrics: Optional[Dict] = None
    security_findings: Optional[List] = None


class Service6TestRunner:
    """Main test runner for Service 6 testing suite"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        self.coverage_dir = self.tests_dir / "coverage"
        self.results = []

        # Test mode configurations
        self.test_modes = {
            "unit": {
                "description": "Fast isolated unit tests",
                "patterns": [
                    "tests/services/test_service6_ai_integration.py",
                    "tests/services/test_realtime_behavioral_network.py",
                    "tests/services/test_service6_database_comprehensive.py",
                ],
                "timeout": 300,
                "parallel": True,
            },
            "integration": {
                "description": "Cross-service integration tests",
                "patterns": [
                    "tests/integration/test_service6_end_to_end_comprehensive.py",
                    "tests/integration/test_workstream_integration.py",
                ],
                "timeout": 600,
                "parallel": False,
            },
            "performance": {
                "description": "Performance and load testing",
                "patterns": [
                    "tests/performance/test_service6_performance_load.py",
                    "tests/integration/test_service6_end_to_end_comprehensive.py::TestService6PerformanceBenchmarks",
                ],
                "timeout": 900,
                "parallel": False,
            },
            "security": {
                "description": "Security and vulnerability testing",
                "patterns": [
                    "tests/security/test_service6_webhook_security.py",
                    "tests/security/test_webhook_signatures.py",
                ],
                "timeout": 300,
                "parallel": True,
            },
            "full": {
                "description": "Complete test suite with coverage",
                "patterns": ["tests/services/test_*.py", "tests/integration/test_*.py", "tests/security/test_*.py"],
                "timeout": 1200,
                "parallel": True,
                "coverage": True,
            },
        }

    def print_banner(self):
        """Print test suite banner"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
        print(f"🧪 SERVICE 6 COMPREHENSIVE TEST SUITE")
        print(f"{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Enhanced Lead Recovery Engine - Test Framework{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Target: 80%+ coverage across all Service 6 components{Style.RESET_ALL}\n")

    def print_mode_info(self, mode: str):
        """Print information about the selected test mode"""
        if mode not in self.test_modes:
            self.print_error(f"Unknown test mode: {mode}")
            self.list_available_modes()
            return

        config = self.test_modes[mode]
        print(f"{Fore.CYAN}📋 Test Mode: {Fore.WHITE}{mode.upper()}{Style.RESET_ALL}")
        print(f"   Description: {config['description']}")
        print(f"   Timeout: {config['timeout']}s")
        print(f"   Parallel: {'Yes' if config['parallel'] else 'No'}")
        print(f"   Coverage: {'Yes' if config.get('coverage') else 'No'}")
        print(f"   Test Patterns: {len(config['patterns'])} patterns\n")

    def list_available_modes(self):
        """List all available test modes"""
        print(f"\n{Fore.YELLOW}Available Test Modes:{Style.RESET_ALL}")
        for mode, config in self.test_modes.items():
            print(f"  {Fore.GREEN}{mode:12}{Style.RESET_ALL} - {config['description']}")
        print()

    def print_success(self, message: str):
        """Print success message"""
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")

    def print_error(self, message: str):
        """Print error message"""
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")

    def print_info(self, message: str):
        """Print info message"""
        print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")

    def ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            self.coverage_dir,
            self.coverage_dir / "unit",
            self.coverage_dir / "integration",
            self.coverage_dir / "performance",
            self.coverage_dir / "security",
            self.coverage_dir / "full",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_pytest_command(self, mode: str, patterns: List[str], **kwargs) -> List[str]:
        """Build pytest command for the given mode and patterns"""
        cmd = [sys.executable, "-m", "pytest"]

        # Add test patterns
        for pattern in patterns:
            if "*" in pattern:
                # Expand glob patterns
                expanded = list(self.project_root.glob(pattern))
                cmd.extend([str(p) for p in expanded if p.exists()])
            else:
                test_path = self.project_root / pattern
                if test_path.exists():
                    cmd.append(str(test_path))

        # Add common options
        cmd.extend(
            [
                "-v",  # Verbose output
                "--tb=short",  # Shorter traceback format
                "--strict-markers",  # Strict marker validation
                "--durations=10",  # Show 10 slowest tests
            ]
        )

        # Add parallel execution if enabled
        if kwargs.get("parallel", False):
            parallel_count = kwargs.get("parallel_workers", 4)
            cmd.extend(["-n", str(parallel_count)])

        # Add coverage options
        if kwargs.get("coverage", False):
            coverage_target = f"ghl_real_estate_ai.services"
            cmd.extend(
                [
                    f"--cov={coverage_target}",
                    "--cov-report=term-missing",
                    f"--cov-report=html:{self.coverage_dir}/{mode}",
                    "--cov-report=json",
                    f"--cov-fail-under={kwargs.get('coverage_threshold', 80)}",
                ]
            )

        # Add performance options for performance tests
        if mode == "performance":
            cmd.extend(
                [
                    "--benchmark-only",
                    "--benchmark-sort=mean",
                    "--benchmark-columns=min,max,mean,stddev,rounds,iterations",
                ]
            )

        # Add security options for security tests
        if mode == "security":
            cmd.extend(
                [
                    "--strict-config",
                    "--capture=no",  # Show security output immediately
                ]
            )

        # Add timeout
        timeout = self.test_modes[mode].get("timeout", 300)
        cmd.extend(["--timeout", str(timeout)])

        # Add filter if specified
        if kwargs.get("filter"):
            cmd.extend(["-k", kwargs["filter"]])

        # Add marker selection if specified
        if kwargs.get("markers"):
            cmd.extend(["-m", kwargs["markers"]])

        return cmd

    async def run_pytest(self, mode: str, **kwargs) -> TestResult:
        """Run pytest for the specified mode"""
        config = self.test_modes[mode]
        patterns = config["patterns"]

        self.print_info(f"Starting {mode} tests...")

        # Prepare options for pytest command
        parallel_enabled = kwargs.get("parallel", config.get("parallel", False))
        coverage_enabled = kwargs.get("coverage", config.get("coverage", False))

        # Remove these from kwargs to avoid double passing
        cmd_kwargs = kwargs.copy()
        if "parallel" in cmd_kwargs:
            del cmd_kwargs["parallel"]
        if "coverage" in cmd_kwargs:
            del cmd_kwargs["coverage"]

        # Build pytest command
        cmd = self.get_pytest_command(
            mode, patterns, parallel=parallel_enabled, coverage=coverage_enabled, **cmd_kwargs
        )

        print(f"{Fore.CYAN}Command: {' '.join(cmd)}{Style.RESET_ALL}")

        # Run pytest
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True, timeout=config["timeout"]
            )

            end_time = time.time()
            duration = end_time - start_time

            # Parse pytest output
            output_lines = result.stdout.split("\n")
            error_lines = result.stderr.split("\n") if result.stderr else []

            # Extract test statistics
            passed, failed, skipped = self.parse_pytest_output(output_lines)

            # Extract coverage if available
            coverage_percentage = self.extract_coverage_percentage(output_lines)

            # Extract errors and warnings
            errors = [line for line in error_lines if "ERROR" in line.upper()]
            warnings = [line for line in output_lines if "WARNING" in line.upper()]

            test_result = TestResult(
                mode=mode,
                test_file=f"{mode}_tests",
                passed=passed,
                failed=failed,
                skipped=skipped,
                duration_seconds=duration,
                coverage_percentage=coverage_percentage,
                errors=errors,
                warnings=warnings,
            )

            # Print result summary
            self.print_test_result(test_result, result.returncode == 0)

            return test_result

        except subprocess.TimeoutExpired:
            self.print_error(f"{mode} tests timed out after {config['timeout']}s")
            return TestResult(
                mode=mode,
                test_file=f"{mode}_tests",
                passed=0,
                failed=1,
                skipped=0,
                duration_seconds=config["timeout"],
                errors=["Test execution timed out"],
            )

        except Exception as e:
            self.print_error(f"Failed to run {mode} tests: {e}")
            return TestResult(
                mode=mode, test_file=f"{mode}_tests", passed=0, failed=1, skipped=0, duration_seconds=0, errors=[str(e)]
            )

    def parse_pytest_output(self, output_lines: List[str]) -> Tuple[int, int, int]:
        """Parse pytest output to extract test statistics"""
        passed = failed = skipped = 0

        for line in output_lines:
            if "passed" in line and "failed" in line:
                # Look for summary line like "5 failed, 23 passed, 2 skipped"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        try:
                            passed = int(parts[i - 1])
                        except ValueError:
                            pass
                    elif part == "failed" and i > 0:
                        try:
                            failed = int(parts[i - 1])
                        except ValueError:
                            pass
                    elif part == "skipped" and i > 0:
                        try:
                            skipped = int(parts[i - 1])
                        except ValueError:
                            pass
                break
            elif "passed in" in line:
                # Look for simple pass line like "25 passed in 1.23s"
                parts = line.split()
                if len(parts) > 0 and parts[0].isdigit():
                    passed = int(parts[0])
                break

        return passed, failed, skipped

    def extract_coverage_percentage(self, output_lines: List[str]) -> Optional[float]:
        """Extract coverage percentage from pytest output"""
        for line in output_lines:
            if "%" in line and "TOTAL" in line:
                # Look for coverage summary line
                parts = line.split()
                for part in parts:
                    if part.endswith("%"):
                        try:
                            return float(part[:-1])
                        except ValueError:
                            pass
        return None

    def print_test_result(self, result: TestResult, success: bool):
        """Print formatted test result"""
        status_color = Fore.GREEN if success else Fore.RED
        status_icon = "✅" if success else "❌"

        print(f"\n{status_color}{status_icon} {result.mode.upper()} Tests Result:{Style.RESET_ALL}")
        print(f"   Passed: {Fore.GREEN}{result.passed}{Style.RESET_ALL}")
        print(f"   Failed: {Fore.RED}{result.failed}{Style.RESET_ALL}")
        print(f"   Skipped: {Fore.YELLOW}{result.skipped}{Style.RESET_ALL}")
        print(f"   Duration: {result.duration_seconds:.2f}s")

        if result.coverage_percentage is not None:
            coverage_color = Fore.GREEN if result.coverage_percentage >= 80 else Fore.YELLOW
            print(f"   Coverage: {coverage_color}{result.coverage_percentage:.1f}%{Style.RESET_ALL}")

        if result.errors:
            print(f"   {Fore.RED}Errors: {len(result.errors)}{Style.RESET_ALL}")

        if result.warnings:
            print(f"   {Fore.YELLOW}Warnings: {len(result.warnings)}{Style.RESET_ALL}")

    def generate_performance_report(self, results: List[TestResult]) -> Dict:
        """Generate performance analysis report"""
        performance_metrics = {
            "total_execution_time": sum(r.duration_seconds for r in results),
            "average_test_time": sum(r.duration_seconds for r in results) / len(results) if results else 0,
            "fastest_mode": min(results, key=lambda r: r.duration_seconds).mode if results else None,
            "slowest_mode": max(results, key=lambda r: r.duration_seconds).mode if results else None,
            "tests_per_second": sum(r.passed + r.failed for r in results) / sum(r.duration_seconds for r in results)
            if results
            else 0,
        }

        return performance_metrics

    def generate_coverage_report(self, results: List[TestResult]) -> Dict:
        """Generate coverage analysis report"""
        coverage_results = [r for r in results if r.coverage_percentage is not None]

        if not coverage_results:
            return {"overall_coverage": None, "coverage_by_mode": {}}

        # Calculate weighted average coverage
        total_tests = sum(r.passed + r.failed for r in coverage_results)
        weighted_coverage = (
            sum(r.coverage_percentage * (r.passed + r.failed) for r in coverage_results) / total_tests
            if total_tests > 0
            else 0
        )

        coverage_by_mode = {r.mode: r.coverage_percentage for r in coverage_results}

        return {
            "overall_coverage": weighted_coverage,
            "coverage_by_mode": coverage_by_mode,
            "coverage_threshold_met": weighted_coverage >= 80.0,
        }

    def print_final_report(self, suite_report: TestSuiteReport):
        """Print comprehensive final test report"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
        print(f"📊 FINAL SERVICE 6 TEST REPORT")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        # Overall statistics
        total_tests = suite_report.total_passed + suite_report.total_failed
        success_rate = (suite_report.total_passed / total_tests * 100) if total_tests > 0 else 0

        print(f"{Fore.WHITE}{Style.BRIGHT}Overall Statistics:{Style.RESET_ALL}")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {Fore.GREEN}{suite_report.total_passed}{Style.RESET_ALL}")
        print(f"   Failed: {Fore.RED}{suite_report.total_failed}{Style.RESET_ALL}")
        print(f"   Skipped: {Fore.YELLOW}{suite_report.total_skipped}{Style.RESET_ALL}")
        print(
            f"   Success Rate: {Fore.GREEN if success_rate > 90 else Fore.YELLOW}{success_rate:.1f}%{Style.RESET_ALL}"
        )
        print(f"   Total Duration: {suite_report.total_duration_seconds:.2f}s")

        # Coverage report
        if suite_report.overall_coverage_percentage is not None:
            coverage_color = Fore.GREEN if suite_report.overall_coverage_percentage >= 80 else Fore.RED
            print(
                f"   Overall Coverage: {coverage_color}{suite_report.overall_coverage_percentage:.1f}%{Style.RESET_ALL}"
            )

            target_met = "✅ TARGET MET" if suite_report.overall_coverage_percentage >= 80 else "❌ BELOW TARGET"
            print(f"   Coverage Target (80%): {target_met}")

        # Performance metrics
        if suite_report.performance_metrics:
            perf = suite_report.performance_metrics
            print(f"\n{Fore.WHITE}{Style.BRIGHT}Performance Metrics:{Style.RESET_ALL}")
            print(f"   Tests per Second: {perf.get('tests_per_second', 0):.1f}")
            print(f"   Fastest Mode: {perf.get('fastest_mode', 'N/A')}")
            print(f"   Slowest Mode: {perf.get('slowest_mode', 'N/A')}")

        # Mode breakdown
        if suite_report.test_results:
            print(f"\n{Fore.WHITE}{Style.BRIGHT}Results by Mode:{Style.RESET_ALL}")
            for result in suite_report.test_results:
                mode_total = result.passed + result.failed
                mode_success = (result.passed / mode_total * 100) if mode_total > 0 else 0

                print(f"   {result.mode.upper()}:")
                print(f"     Tests: {mode_total} | Passed: {result.passed} | Failed: {result.failed}")
                print(f"     Success: {mode_success:.1f}% | Duration: {result.duration_seconds:.1f}s")
                if result.coverage_percentage is not None:
                    print(f"     Coverage: {result.coverage_percentage:.1f}%")

        # Final status
        overall_success = suite_report.total_failed == 0 and (
            suite_report.overall_coverage_percentage is None or suite_report.overall_coverage_percentage >= 80
        )

        if overall_success:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 SERVICE 6 TEST SUITE: PASSED")
            print(f"All tests completed successfully with adequate coverage!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}{Style.BRIGHT}💥 SERVICE 6 TEST SUITE: FAILED")
            if suite_report.total_failed > 0:
                print(f"Some tests failed. Please review and fix failing tests.")
            if suite_report.overall_coverage_percentage is not None and suite_report.overall_coverage_percentage < 80:
                print(f"Coverage below 80% target. Add more tests for better coverage.")
            print(f"{Style.RESET_ALL}")

    async def run_mode(self, mode: str, **kwargs) -> TestResult:
        """Run tests for a specific mode"""
        if mode not in self.test_modes:
            raise ValueError(f"Unknown test mode: {mode}")

        self.print_mode_info(mode)
        result = await self.run_pytest(mode, **kwargs)
        self.results.append(result)
        return result

    async def run_all_modes(self, **kwargs) -> List[TestResult]:
        """Run tests for all modes except full"""
        modes = ["unit", "integration", "security"]  # Skip performance by default
        results = []

        for mode in modes:
            result = await self.run_mode(mode, **kwargs)
            results.append(result)

        return results

    def save_results_json(self, suite_report: TestSuiteReport, output_file: str):
        """Save test results to JSON file"""
        output_path = self.tests_dir / output_file

        with open(output_path, "w") as f:
            json.dump(asdict(suite_report), f, indent=2, default=str)

        self.print_success(f"Results saved to {output_path}")


async def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(
        description="Service 6 Comprehensive Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Modes:
  unit         Fast isolated unit tests
  integration  Cross-service workflow tests  
  performance  Performance and load tests
  security     Security and vulnerability tests
  full         Complete suite with coverage
  all          Run unit + integration + security modes

Examples:
  python tests/run_service6_tests.py unit
  python tests/run_service6_tests.py full --coverage
  python tests/run_service6_tests.py --filter="test_service6_ai"
  python tests/run_service6_tests.py performance --parallel=2
        """,
    )

    parser.add_argument(
        "mode",
        nargs="?",
        default="unit",
        choices=["unit", "integration", "performance", "security", "full", "all"],
        help="Test mode to run (default: unit)",
    )

    parser.add_argument("--coverage", action="store_true", help="Enable coverage reporting")

    parser.add_argument("--parallel", type=int, default=4, help="Number of parallel workers (default: 4)")

    parser.add_argument("--filter", type=str, help="Filter tests by name pattern")

    parser.add_argument("--markers", type=str, help="Run tests with specific markers")

    parser.add_argument(
        "--coverage-threshold", type=int, default=80, help="Coverage percentage threshold (default: 80)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="service6_test_results.json",
        help="Output file for test results (default: service6_test_results.json)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Create test runner
    runner = Service6TestRunner()
    runner.print_banner()
    runner.ensure_directories()

    # Prepare kwargs
    kwargs = {
        "coverage": args.coverage,
        "parallel_workers": args.parallel,
        "filter": args.filter,
        "markers": args.markers,
        "coverage_threshold": args.coverage_threshold,
    }

    # Remove None values
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    try:
        start_time = time.time()

        # Run tests based on mode
        if args.mode == "all":
            results = await runner.run_all_modes(**kwargs)
        else:
            result = await runner.run_mode(args.mode, **kwargs)
            results = [result]

        end_time = time.time()
        total_duration = end_time - start_time

        # Generate comprehensive report
        total_passed = sum(r.passed for r in results)
        total_failed = sum(r.failed for r in results)
        total_skipped = sum(r.skipped for r in results)

        performance_metrics = runner.generate_performance_report(results)
        coverage_report = runner.generate_coverage_report(results)

        suite_report = TestSuiteReport(
            total_tests=total_passed + total_failed,
            total_passed=total_passed,
            total_failed=total_failed,
            total_skipped=total_skipped,
            total_duration_seconds=total_duration,
            overall_coverage_percentage=coverage_report.get("overall_coverage"),
            test_results=results,
            performance_metrics=performance_metrics,
        )

        # Print final report
        runner.print_final_report(suite_report)

        # Save results
        runner.save_results_json(suite_report, args.output)

        # Exit with appropriate code
        exit_code = 0 if total_failed == 0 else 1

        if args.coverage and suite_report.overall_coverage_percentage is not None:
            if suite_report.overall_coverage_percentage < args.coverage_threshold:
                exit_code = 1

        sys.exit(exit_code)

    except KeyboardInterrupt:
        runner.print_error("Test execution interrupted by user")
        sys.exit(1)

    except Exception as e:
        runner.print_error(f"Test execution failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
