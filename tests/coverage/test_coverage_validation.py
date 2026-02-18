"""
Test Coverage Validation and Reporting for Service 6

This module provides comprehensive coverage analysis and validation
to ensure Service 6 meets the 80% coverage threshold with quality tests.

Coverage Goals:
- Overall coverage: 80%+
- Service layer coverage: 85%+
- Critical path coverage: 95%+
- Integration workflow coverage: 75%+
"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

import pytest



class CoverageValidator:
    """Validates test coverage meets quality and percentage thresholds"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.coverage_thresholds = {"overall": 80.0, "services": 85.0, "critical_paths": 95.0, "integration": 75.0}

        # Critical Service 6 components that must have high coverage
        self.critical_components = [
            "ghl_real_estate_ai/services/service6_ai_integration.py",
            "ghl_real_estate_ai/services/claude_assistant.py",
            "ghl_real_estate_ai/services/cache_service.py",
            "ghl_real_estate_ai/api/routes/webhooks.py",
        ]

        # Service layer components requiring 85%+ coverage
        self.service_components = [
            "ghl_real_estate_ai/services/database_service.py",
            "ghl_real_estate_ai/services/apollo_client.py",
            "ghl_real_estate_ai/services/twilio_client.py",
            "ghl_real_estate_ai/services/sendgrid_client.py",
        ]

    def run_coverage_analysis(self) -> Dict[str, float]:
        """Run pytest with coverage and return detailed metrics"""
        try:
            # Run pytest with coverage reporting
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "--cov=ghl_real_estate_ai",
                "--cov-report=json",
                "--cov-report=xml",
                "--cov-report=html",
                "--cov-report=term-missing",
                "-v",
                "--tb=short",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.base_path)

            if result.returncode != 0:
                print("ERROR: Tests failed before coverage analysis:")
                print(result.stdout)
                print(result.stderr)
                return {}

            # Parse coverage JSON report
            coverage_json = self.base_path / "coverage.json"
            if coverage_json.exists():
                with open(coverage_json, "r") as f:
                    coverage_data = json.load(f)

                return self._analyze_coverage_data(coverage_data)

            return {}

        except Exception as e:
            print(f"Coverage analysis failed: {e}")
            return {}

    def _analyze_coverage_data(self, coverage_data: Dict) -> Dict[str, float]:
        """Analyze coverage data and return component-specific metrics"""
        files = coverage_data.get("files", {})
        totals = coverage_data.get("totals", {})

        metrics = {
            "overall": totals.get("percent_covered", 0.0),
            "total_statements": totals.get("num_statements", 0),
            "covered_statements": totals.get("covered_lines", 0),
            "missing_statements": totals.get("missing_lines", 0),
        }

        # Calculate service component coverage
        service_coverage = []
        for component in self.service_components:
            if component in files:
                file_data = files[component]["summary"]
                coverage_pct = file_data.get("percent_covered", 0.0)
                service_coverage.append(coverage_pct)

        metrics["services"] = sum(service_coverage) / len(service_coverage) if service_coverage else 0.0

        # Calculate critical path coverage
        critical_coverage = []
        for component in self.critical_components:
            if component in files:
                file_data = files[component]["summary"]
                coverage_pct = file_data.get("percent_covered", 0.0)
                critical_coverage.append(coverage_pct)

        metrics["critical_paths"] = sum(critical_coverage) / len(critical_coverage) if critical_coverage else 0.0

        # Calculate integration test coverage (based on test files)
        integration_files = [f for f in files.keys() if "integration" in f or "end_to_end" in f]
        if integration_files:
            integration_coverage = [files[f]["summary"]["percent_covered"] for f in integration_files]
            metrics["integration"] = sum(integration_coverage) / len(integration_coverage)
        else:
            metrics["integration"] = 0.0

        return metrics

    def validate_coverage_thresholds(self, metrics: Dict[str, float]) -> Tuple[bool, List[str]]:
        """Validate that coverage meets all required thresholds"""
        failures = []

        for category, threshold in self.coverage_thresholds.items():
            actual_coverage = metrics.get(category, 0.0)

            if actual_coverage < threshold:
                failures.append(f"{category.title()} coverage {actual_coverage:.1f}% below threshold {threshold:.1f}%")

        return len(failures) == 0, failures

    def identify_coverage_gaps(self, coverage_data: Dict) -> Dict[str, List[str]]:
        """Identify specific functions/lines with poor coverage"""
        gaps = {
            "uncovered_critical": [],
            "uncovered_services": [],
            "missing_test_files": [],
            "low_coverage_functions": [],
        }

        files = coverage_data.get("files", {})

        # Check critical components for coverage gaps
        for component in self.critical_components:
            if component not in files:
                gaps["missing_test_files"].append(component)
                continue

            file_data = files[component]
            if file_data["summary"]["percent_covered"] < self.coverage_thresholds["critical_paths"]:
                missing_lines = file_data.get("missing_lines", [])
                gaps["uncovered_critical"].append(f"{component}: lines {missing_lines}")

        # Check service components
        for component in self.service_components:
            if component not in files:
                gaps["missing_test_files"].append(component)
                continue

            file_data = files[component]
            if file_data["summary"]["percent_covered"] < self.coverage_thresholds["services"]:
                missing_lines = file_data.get("missing_lines", [])
                gaps["uncovered_services"].append(f"{component}: lines {missing_lines}")

        return gaps

    def generate_coverage_report(self, metrics: Dict[str, float], gaps: Dict[str, List[str]]) -> str:
        """Generate comprehensive coverage report"""
        report = """
=== SERVICE 6 TEST COVERAGE REPORT ===

COVERAGE METRICS:
"""

        for category, value in metrics.items():
            threshold = self.coverage_thresholds.get(category, 0.0)
            status = "✅ PASS" if value >= threshold else "❌ FAIL"
            report += f"  {category.title()}: {value:.1f}% (threshold: {threshold:.1f}%) {status}\n"

        report += "\nCOVERAGE GAPS:\n"

        if gaps["uncovered_critical"]:
            report += "\nCritical Path Gaps (URGENT):\n"
            for gap in gaps["uncovered_critical"]:
                report += f"  ❌ {gap}\n"

        if gaps["uncovered_services"]:
            report += "\nService Layer Gaps:\n"
            for gap in gaps["uncovered_services"]:
                report += f"  ⚠️  {gap}\n"

        if gaps["missing_test_files"]:
            report += "\nMissing Test Coverage:\n"
            for missing in gaps["missing_test_files"]:
                report += f"  🔍 {missing}\n"

        if not any(gaps.values()):
            report += "  ✅ No significant coverage gaps detected!\n"

        report += "\nRECOMMENDATIONS:\n"

        if metrics.get("overall", 0) < 80:
            report += """
  1. Add unit tests for uncovered functions in service layer
  2. Expand integration test scenarios for end-to-end workflows  
  3. Add edge case testing for error handling paths
  4. Implement property-based testing for data validation logic
"""

        if metrics.get("critical_paths", 0) < 95:
            report += """
  5. PRIORITY: Add comprehensive tests for AI integration pipeline
  6. PRIORITY: Test all webhook signature verification paths
  7. PRIORITY: Add error simulation tests for external service failures
"""

        if metrics.get("services", 0) < 85:
            report += """
  8. Add negative test cases for all service methods
  9. Test concurrent access patterns for cache service
  10. Add timeout and retry logic testing
"""

        report += "\n=== END COVERAGE REPORT ===\n"
        return report


class TestCoverageValidation:
    """Test suite to validate coverage analysis and reporting"""

    @pytest.fixture
    def coverage_validator(self):
        """Coverage validator fixture"""
        return CoverageValidator()

    def test_coverage_thresholds_configured(self, coverage_validator):
        """Test that coverage thresholds are properly configured"""
        thresholds = coverage_validator.coverage_thresholds

        assert thresholds["overall"] == 80.0
        assert thresholds["services"] == 85.0
        assert thresholds["critical_paths"] == 95.0
        assert thresholds["integration"] == 75.0

    def test_critical_components_defined(self, coverage_validator):
        """Test that critical components are properly identified"""
        critical = coverage_validator.critical_components

        # Must include core AI integration
        assert any("service6_ai_integration.py" in comp for comp in critical)

        # Must include webhook security
        assert any("webhooks.py" in comp for comp in critical)

        # Must include caching service
        assert any("cache_service.py" in comp for comp in critical)

    def test_service_components_defined(self, coverage_validator):
        """Test that service components are properly identified"""
        services = coverage_validator.service_components

        # Must include all external service clients
        expected_services = ["database_service.py", "apollo_client.py", "twilio_client.py", "sendgrid_client.py"]

        for expected in expected_services:
            assert any(expected in comp for comp in services)

    def test_coverage_metrics_calculation(self, coverage_validator):
        """Test coverage metrics calculation with mock data"""
        mock_coverage_data = {
            "totals": {"percent_covered": 82.5, "num_statements": 1000, "covered_lines": 825, "missing_lines": 175},
            "files": {
                "ghl_real_estate_ai/services/service6_ai_integration.py": {"summary": {"percent_covered": 96.0}},
                "ghl_real_estate_ai/services/database_service.py": {"summary": {"percent_covered": 87.5}},
                "ghl_real_estate_ai/api/routes/webhooks.py": {"summary": {"percent_covered": 94.0}},
            },
        }

        metrics = coverage_validator._analyze_coverage_data(mock_coverage_data)

        assert metrics["overall"] == 82.5
        assert metrics["total_statements"] == 1000
        assert metrics["covered_statements"] == 825

    def test_coverage_threshold_validation(self, coverage_validator):
        """Test coverage threshold validation logic"""
        # Test passing metrics
        passing_metrics = {"overall": 85.0, "services": 90.0, "critical_paths": 98.0, "integration": 80.0}

        is_valid, failures = coverage_validator.validate_coverage_thresholds(passing_metrics)
        assert is_valid is True
        assert len(failures) == 0

        # Test failing metrics
        failing_metrics = {
            "overall": 75.0,  # Below 80%
            "services": 82.0,  # Below 85%
            "critical_paths": 90.0,  # Below 95%
            "integration": 80.0,  # Above 75%
        }

        is_valid, failures = coverage_validator.validate_coverage_thresholds(failing_metrics)
        assert is_valid is False
        assert len(failures) == 3  # Three categories below threshold

    def test_coverage_gap_identification(self, coverage_validator):
        """Test identification of coverage gaps"""
        mock_coverage_data = {
            "files": {
                "ghl_real_estate_ai/services/service6_ai_integration.py": {
                    "summary": {"percent_covered": 85.0},  # Below critical threshold (95%)
                    "missing_lines": [45, 67, 89],
                },
                "ghl_real_estate_ai/services/database_service.py": {
                    "summary": {"percent_covered": 80.0},  # Below service threshold (85%)
                    "missing_lines": [23, 34],
                },
            }
        }

        gaps = coverage_validator.identify_coverage_gaps(mock_coverage_data)

        assert len(gaps["uncovered_critical"]) > 0
        assert len(gaps["uncovered_services"]) > 0
        assert "service6_ai_integration.py" in gaps["uncovered_critical"][0]
        assert "database_service.py" in gaps["uncovered_services"][0]

    def test_coverage_report_generation(self, coverage_validator):
        """Test coverage report generation"""
        metrics = {"overall": 82.5, "services": 87.0, "critical_paths": 96.5, "integration": 78.0}

        gaps = {
            "uncovered_critical": [],
            "uncovered_services": ["database_service.py: lines [23, 34]"],
            "missing_test_files": [],
            "low_coverage_functions": [],
        }

        report = coverage_validator.generate_coverage_report(metrics, gaps)

        assert "SERVICE 6 TEST COVERAGE REPORT" in report
        assert "82.5%" in report  # Overall coverage
        assert "87.0%" in report  # Service coverage
        assert "PASS" in report  # Some passing metrics
        assert "RECOMMENDATIONS" in report


def run_comprehensive_coverage_analysis():
    """Main function to run complete coverage analysis"""
    print("Starting Service 6 comprehensive coverage analysis...")

    validator = CoverageValidator()

    # Run coverage analysis
    print("Running pytest with coverage reporting...")
    metrics = validator.run_coverage_analysis()

    if not metrics:
        print("❌ Coverage analysis failed - check test execution")
        return False

    # Validate thresholds
    print("Validating coverage thresholds...")
    is_valid, failures = validator.validate_coverage_thresholds(metrics)

    # Load coverage data for gap analysis
    coverage_json_path = Path("coverage.json")
    if coverage_json_path.exists():
        with open(coverage_json_path, "r") as f:
            coverage_data = json.load(f)
        gaps = validator.identify_coverage_gaps(coverage_data)
    else:
        gaps = {
            "uncovered_critical": [],
            "uncovered_services": [],
            "missing_test_files": [],
            "low_coverage_functions": [],
        }

    # Generate and display report
    report = validator.generate_coverage_report(metrics, gaps)
    print(report)

    # Save report to file
    report_path = Path("tests/coverage/coverage_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)

    print(f"📊 Detailed coverage report saved to: {report_path}")

    if is_valid:
        print("✅ All coverage thresholds met!")
        return True
    else:
        print("❌ Coverage validation failed:")
        for failure in failures:
            print(f"  - {failure}")
        return False


if __name__ == "__main__":
    # Run comprehensive coverage analysis
    success = run_comprehensive_coverage_analysis()
    sys.exit(0 if success else 1)