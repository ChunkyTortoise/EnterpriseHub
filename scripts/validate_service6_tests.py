#!/usr/bin/env python3
"""
Service 6 Test Validation Script

Comprehensive test runner and validation for Service 6 Lead Recovery Engine.
Runs all test categories, validates coverage, and generates detailed reports.

Usage:
    python scripts/validate_service6_tests.py [--fast] [--category=unit|integration|security]
    
Features:
- Runs complete test suite with coverage analysis
- Validates 80%+ coverage requirement
- Generates detailed coverage and quality reports  
- Validates webhook security tests
- Checks for missing test files
- Performance and quality metrics
"""

import sys
import subprocess
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Service6TestValidator:
    """Comprehensive test validation for Service 6"""
    
    def __init__(self, fast_mode: bool = False):
        self.fast_mode = fast_mode
        self.project_root = project_root
        self.results = {
            "test_summary": {},
            "coverage_metrics": {},
            "security_validation": {},
            "performance_metrics": {},
            "quality_gates": {}
        }
    
    def validate_test_environment(self) -> bool:
        """Validate that test environment is properly configured"""
        print("🔍 Validating test environment...")
        
        required_files = [
            "requirements-test.txt",
            "pytest.ini", 
            ".coveragerc",
            "tests/conftest.py",
            "tests/__init__.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing required test files: {missing_files}")
            return False
        
        # Check that test dependencies are available
        try:
            import pytest
            import pytest_asyncio
            import pytest_mock
            import coverage
            print("✅ Test environment validated")
            return True
        except ImportError as e:
            print(f"❌ Missing test dependency: {e}")
            print("Run: pip install -r requirements-test.txt")
            return False
    
    def run_unit_tests(self) -> Dict[str, any]:
        """Run unit tests for all Service 6 components"""
        print("🧪 Running unit tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/services/",
            "tests/mocks/", 
            "tests/fixtures/",
            "-m", "unit or not integration and not e2e",
            "--tb=short",
            "-v"
        ]
        
        if self.fast_mode:
            cmd.extend(["-x", "--lf"])  # Stop on first failure, run last failed
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "test_count": self._parse_test_count(result.stdout)
        }
    
    def run_integration_tests(self) -> Dict[str, any]:
        """Run integration and end-to-end tests"""
        print("🔗 Running integration tests...")
        
        cmd = [
            sys.executable, "-m", "pytest", 
            "tests/integration/",
            "-m", "integration or e2e",
            "--tb=short",
            "-v"
        ]
        
        if self.fast_mode:
            cmd.extend(["-x"])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout, 
            "stderr": result.stderr,
            "test_count": self._parse_test_count(result.stdout)
        }
    
    def run_security_tests(self) -> Dict[str, any]:
        """Run security validation tests"""
        print("🔒 Running security tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/security/",
            "-m", "security", 
            "--tb=short",
            "-v"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "test_count": self._parse_test_count(result.stdout)
        }
    
    def run_comprehensive_coverage_analysis(self) -> Dict[str, any]:
        """Run comprehensive coverage analysis with detailed reporting"""
        print("📊 Running comprehensive coverage analysis...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "--cov=ghl_real_estate_ai",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-report=json:coverage.json",
            "--cov-report=term-missing",
            "--cov-branch",
            "--cov-fail-under=80",
            "-v"
        ]
        
        if self.fast_mode:
            cmd.extend(["-x"])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        # Parse coverage data
        coverage_data = self._parse_coverage_data()
        
        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "coverage_data": coverage_data,
            "meets_threshold": coverage_data.get("overall_coverage", 0) >= 80.0
        }
    
    def _parse_coverage_data(self) -> Dict[str, any]:
        """Parse coverage.json to extract detailed metrics"""
        coverage_file = self.project_root / "coverage.json"
        
        if not coverage_file.exists():
            return {"error": "Coverage data not found"}
        
        try:
            with open(coverage_file, 'r') as f:
                data = json.load(f)
            
            totals = data.get("totals", {})
            files = data.get("files", {})
            
            # Calculate component-specific coverage
            service_files = {k: v for k, v in files.items() if "/services/" in k}
            api_files = {k: v for k, v in files.items() if "/api/" in k}
            
            return {
                "overall_coverage": totals.get("percent_covered", 0.0),
                "total_statements": totals.get("num_statements", 0),
                "covered_statements": totals.get("covered_lines", 0),
                "missing_statements": totals.get("missing_lines", 0),
                "branch_coverage": totals.get("percent_covered_display", "N/A"),
                "service_coverage": self._calculate_component_coverage(service_files),
                "api_coverage": self._calculate_component_coverage(api_files),
                "critical_components": self._analyze_critical_components(files)
            }
            
        except Exception as e:
            return {"error": f"Failed to parse coverage data: {e}"}
    
    def _calculate_component_coverage(self, files: Dict) -> Dict[str, float]:
        """Calculate average coverage for a component"""
        if not files:
            return {"average": 0.0, "files": {}}
        
        file_coverages = {}
        total_coverage = 0.0
        
        for filepath, filedata in files.items():
            coverage_pct = filedata.get("summary", {}).get("percent_covered", 0.0)
            file_coverages[filepath] = coverage_pct
            total_coverage += coverage_pct
        
        return {
            "average": total_coverage / len(files),
            "files": file_coverages
        }
    
    def _analyze_critical_components(self, files: Dict) -> Dict[str, any]:
        """Analyze coverage of critical Service 6 components"""
        critical_files = [
            "ghl_real_estate_ai/services/service6_ai_integration.py",
            "ghl_real_estate_ai/services/claude_assistant.py",
            "ghl_real_estate_ai/services/cache_service.py",
            "ghl_real_estate_ai/api/routes/webhooks.py"
        ]
        
        critical_analysis = {
            "covered": {},
            "missing": [],
            "below_threshold": {}
        }
        
        for critical_file in critical_files:
            if critical_file in files:
                coverage_pct = files[critical_file].get("summary", {}).get("percent_covered", 0.0)
                critical_analysis["covered"][critical_file] = coverage_pct
                
                if coverage_pct < 95.0:  # Critical files should have 95%+ coverage
                    critical_analysis["below_threshold"][critical_file] = coverage_pct
            else:
                critical_analysis["missing"].append(critical_file)
        
        return critical_analysis
    
    def _parse_test_count(self, pytest_output: str) -> Dict[str, int]:
        """Parse pytest output to extract test counts"""
        counts = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0
        }
        
        # Look for pytest summary line
        for line in pytest_output.split('\n'):
            if 'passed' in line and ('failed' in line or 'error' in line or '=====' in line):
                # Parse format like: "5 passed, 2 failed, 1 skipped in 1.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed' and i > 0:
                        counts["passed"] = int(parts[i-1])
                    elif part == 'failed' and i > 0:
                        counts["failed"] = int(parts[i-1])
                    elif part == 'skipped' and i > 0:
                        counts["skipped"] = int(parts[i-1])
                    elif part == 'error' and i > 0:
                        counts["errors"] = int(parts[i-1])
                break
        
        counts["total"] = sum([counts["passed"], counts["failed"], counts["skipped"], counts["errors"]])
        return counts
    
    def validate_quality_gates(self) -> Dict[str, bool]:
        """Validate all quality gates for Service 6"""
        print("🎯 Validating quality gates...")
        
        quality_gates = {
            "test_environment_ready": False,
            "all_unit_tests_pass": False,
            "all_integration_tests_pass": False,
            "security_tests_pass": False,
            "coverage_threshold_met": False,
            "critical_components_covered": False,
            "no_missing_test_files": False,
            "webhook_security_validated": False
        }
        
        # Run all validation checks
        env_valid = self.validate_test_environment()
        quality_gates["test_environment_ready"] = env_valid
        
        if not env_valid:
            return quality_gates
        
        # Run test suites
        unit_results = self.run_unit_tests()
        integration_results = self.run_integration_tests()
        security_results = self.run_security_tests()
        coverage_results = self.run_comprehensive_coverage_analysis()
        
        # Store results for reporting
        self.results.update({
            "test_summary": {
                "unit": unit_results,
                "integration": integration_results,
                "security": security_results
            },
            "coverage_metrics": coverage_results.get("coverage_data", {}),
            "performance_metrics": {
                "unit_test_duration": unit_results.get("duration", 0),
                "integration_test_duration": integration_results.get("duration", 0),
                "security_test_duration": security_results.get("duration", 0),
                "coverage_analysis_duration": coverage_results.get("duration", 0)
            }
        })
        
        # Validate quality gates
        quality_gates["all_unit_tests_pass"] = unit_results.get("success", False)
        quality_gates["all_integration_tests_pass"] = integration_results.get("success", False)
        quality_gates["security_tests_pass"] = security_results.get("success", False)
        quality_gates["coverage_threshold_met"] = coverage_results.get("meets_threshold", False)
        
        # Validate critical components
        coverage_data = coverage_results.get("coverage_data", {})
        critical_analysis = coverage_data.get("critical_components", {})
        quality_gates["critical_components_covered"] = len(critical_analysis.get("below_threshold", {})) == 0
        quality_gates["no_missing_test_files"] = len(critical_analysis.get("missing", [])) == 0
        
        # Validate webhook security
        quality_gates["webhook_security_validated"] = security_results.get("success", False)
        
        self.results["quality_gates"] = quality_gates
        return quality_gates
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive validation report"""
        report = f"""
=== SERVICE 6 COMPREHENSIVE TEST VALIDATION REPORT ===
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY:
"""
        
        quality_gates = self.results.get("quality_gates", {})
        passed_gates = sum(1 for gate in quality_gates.values() if gate)
        total_gates = len(quality_gates)
        
        overall_success = passed_gates == total_gates
        report += f"  Overall Status: {'✅ SUCCESS' if overall_success else '❌ FAILED'}\n"
        report += f"  Quality Gates: {passed_gates}/{total_gates} passed\n"
        
        # Coverage Summary
        coverage_metrics = self.results.get("coverage_metrics", {})
        overall_coverage = coverage_metrics.get("overall_coverage", 0)
        report += f"  Test Coverage: {overall_coverage:.1f}% ({'✅' if overall_coverage >= 80 else '❌'})\n"
        
        # Test Summary
        test_summary = self.results.get("test_summary", {})
        total_tests = 0
        total_passed = 0
        
        for category, results in test_summary.items():
            test_count = results.get("test_count", {})
            total_tests += test_count.get("total", 0)
            total_passed += test_count.get("passed", 0)
        
        report += f"  Tests Status: {total_passed}/{total_tests} passed\n\n"
        
        # Detailed Quality Gates
        report += "QUALITY GATES VALIDATION:\n"
        for gate_name, gate_status in quality_gates.items():
            status_icon = "✅" if gate_status else "❌"
            gate_display = gate_name.replace("_", " ").title()
            report += f"  {status_icon} {gate_display}\n"
        
        # Coverage Details
        report += "\nCOVERAGE ANALYSIS:\n"
        report += f"  Overall Coverage: {overall_coverage:.1f}%\n"
        
        service_coverage = coverage_metrics.get("service_coverage", {})
        if service_coverage:
            report += f"  Service Layer: {service_coverage.get('average', 0):.1f}%\n"
        
        api_coverage = coverage_metrics.get("api_coverage", {})
        if api_coverage:
            report += f"  API Layer: {api_coverage.get('average', 0):.1f}%\n"
        
        # Critical Components
        critical_analysis = coverage_metrics.get("critical_components", {})
        if critical_analysis.get("below_threshold"):
            report += "\nCRITICAL COVERAGE GAPS:\n"
            for file_path, coverage_pct in critical_analysis["below_threshold"].items():
                report += f"  ❌ {file_path}: {coverage_pct:.1f}% (target: 95%)\n"
        
        if critical_analysis.get("missing"):
            report += "\nMISSING CRITICAL TESTS:\n"
            for missing_file in critical_analysis["missing"]:
                report += f"  🔍 {missing_file}\n"
        
        # Performance Metrics
        perf_metrics = self.results.get("performance_metrics", {})
        report += "\nPERFORMANCE METRICS:\n"
        total_duration = sum(perf_metrics.values())
        report += f"  Total Test Duration: {total_duration:.2f}s\n"
        
        for metric_name, duration in perf_metrics.items():
            metric_display = metric_name.replace("_", " ").title()
            report += f"  {metric_display}: {duration:.2f}s\n"
        
        # Recommendations
        report += "\nRECOMMENDATIONS:\n"
        
        if not overall_success:
            if not quality_gates.get("coverage_threshold_met"):
                report += "  1. PRIORITY: Increase test coverage to meet 80% threshold\n"
            
            if not quality_gates.get("critical_components_covered"):
                report += "  2. CRITICAL: Add comprehensive tests for critical components\n"
            
            if not quality_gates.get("security_tests_pass"):
                report += "  3. SECURITY: Fix failing webhook security validation tests\n"
            
            failing_tests = [k for k, v in quality_gates.items() if not v]
            report += f"  4. Review and fix failing quality gates: {', '.join(failing_tests)}\n"
        else:
            report += "  🎉 All quality gates passed! Service 6 tests are production-ready.\n"
            report += "  ✨ Consider adding performance tests for load testing.\n"
            report += "  📈 Monitor test coverage as new features are added.\n"
        
        report += "\n=== END VALIDATION REPORT ===\n"
        return report
    
    def save_reports(self, report_dir: Path = None):
        """Save all reports to files"""
        if report_dir is None:
            report_dir = self.project_root / "test_reports"
        
        report_dir.mkdir(exist_ok=True)
        
        # Save comprehensive report
        comprehensive_report = self.generate_comprehensive_report()
        with open(report_dir / "service6_validation_report.txt", 'w') as f:
            f.write(comprehensive_report)
        
        # Save JSON results for programmatic access
        with open(report_dir / "service6_validation_results.json", 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"📄 Reports saved to: {report_dir}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Service 6 Test Validation")
    parser.add_argument("--fast", action="store_true", help="Run in fast mode (stop on first failure)")
    parser.add_argument("--category", choices=["unit", "integration", "security", "all"], 
                       default="all", help="Run specific test category")
    parser.add_argument("--report-dir", type=Path, help="Directory to save reports")
    
    args = parser.parse_args()
    
    print("🚀 Starting Service 6 Test Validation")
    print(f"Mode: {'Fast' if args.fast else 'Comprehensive'}")
    print(f"Category: {args.category}")
    print("-" * 60)
    
    validator = Service6TestValidator(fast_mode=args.fast)
    
    if args.category == "all":
        # Run comprehensive validation
        quality_gates = validator.validate_quality_gates()
        
        # Generate and display report
        report = validator.generate_comprehensive_report()
        print(report)
        
        # Save reports
        validator.save_reports(args.report_dir)
        
        # Exit with appropriate code
        all_passed = all(quality_gates.values())
        sys.exit(0 if all_passed else 1)
    
    else:
        # Run specific category
        if args.category == "unit":
            results = validator.run_unit_tests()
        elif args.category == "integration":
            results = validator.run_integration_tests()
        elif args.category == "security":
            results = validator.run_security_tests()
        
        print(f"\n{args.category.title()} Test Results:")
        print(f"Success: {results.get('success', False)}")
        print(f"Duration: {results.get('duration', 0):.2f}s")
        print(f"Test Count: {results.get('test_count', {})}")
        
        if not results.get("success", False):
            print("\nOutput:")
            print(results.get("stdout", ""))
            print("\nErrors:")
            print(results.get("stderr", ""))
        
        sys.exit(0 if results.get("success", False) else 1)


if __name__ == "__main__":
    main()