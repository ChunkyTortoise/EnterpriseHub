#!/usr/bin/env python3
"""
Service 6 Test Validation Script
===============================

Validates the quality and coverage of the Service 6 test suite.
Checks for test completeness, missing test scenarios, and code coverage.

Usage:
    python tests/validate_service6_tests.py
    python tests/validate_service6_tests.py --detailed
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class TestValidator:
    """Validates Service 6 test suite completeness."""

    def __init__(self):
        self.validation_results = {
            "total_tests": 0,
            "todo_methods_tested": 0,
            "performance_tests": 0,
            "integration_tests": 0,
            "error_handling_tests": 0,
            "missing_scenarios": [],
            "recommendations": [],
        }

    def analyze_test_file(self, test_file_path: Path) -> Dict:
        """Analyze a test file for completeness."""

        if not test_file_path.exists():
            return {"error": f"Test file not found: {test_file_path}"}

        try:
            with open(test_file_path, "r") as f:
                content = f.read()
                tree = ast.parse(content)

            return self._extract_test_info(tree, content)

        except Exception as e:
            return {"error": f"Failed to parse {test_file_path}: {e}"}

    def _extract_test_info(self, tree: ast.AST, content: str) -> Dict:
        """Extract test information from AST."""

        test_info = {
            "test_functions": [],
            "test_classes": [],
            "async_tests": 0,
            "performance_tests": 0,
            "error_tests": 0,
            "integration_tests": 0,
            "todo_method_tests": 0,
            "fixtures": [],
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name

                # Count test functions
                if func_name.startswith("test_"):
                    test_info["test_functions"].append(func_name)

                    # Check for async tests
                    if isinstance(node, ast.AsyncFunctionDef):
                        test_info["async_tests"] += 1

                    # Check for performance tests
                    if any(
                        keyword in func_name.lower()
                        for keyword in ["performance", "benchmark", "latency", "speed", "time"]
                    ):
                        test_info["performance_tests"] += 1

                    # Check for error handling tests
                    if any(
                        keyword in func_name.lower()
                        for keyword in ["error", "failure", "exception", "fallback", "recovery"]
                    ):
                        test_info["error_tests"] += 1

                    # Check for integration tests
                    if any(
                        keyword in func_name.lower()
                        for keyword in ["integration", "workflow", "end_to_end", "complete"]
                    ):
                        test_info["integration_tests"] += 1

                    # Check for TODO method tests
                    if any(
                        keyword in func_name.lower()
                        for keyword in ["alert", "notify", "priority", "response", "content", "todo"]
                    ):
                        test_info["todo_method_tests"] += 1

                # Count fixtures
                if any(
                    decorator.id == "fixture" for decorator in node.decorator_list if isinstance(decorator, ast.Name)
                ):
                    test_info["fixtures"].append(func_name)

            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    test_info["test_classes"].append(node.name)

        return test_info

    def validate_service6_ai_integration_tests(self) -> Dict:
        """Validate Service 6 AI Integration test coverage."""

        test_file = Path("tests/services/test_service6_ai_integration.py")
        analysis = self.analyze_test_file(test_file)

        if "error" in analysis:
            return analysis

        # Expected test scenarios for Service 6 AI Integration
        required_scenarios = {
            "comprehensive_lead_analysis": False,
            "realtime_lead_scoring": False,
            "performance_benchmarking": False,
            "error_handling": False,
            "concurrent_processing": False,
            "cache_integration": False,
            "memory_integration": False,
            "configuration_validation": False,
            "orchestrator_operations": False,
        }

        # Check which scenarios are covered
        for test_func in analysis["test_functions"]:
            test_lower = test_func.lower()

            if "comprehensive" in test_lower and "analysis" in test_lower:
                required_scenarios["comprehensive_lead_analysis"] = True
            if "realtime" in test_lower and "scoring" in test_lower:
                required_scenarios["realtime_lead_scoring"] = True
            if "performance" in test_lower or "benchmark" in test_lower:
                required_scenarios["performance_benchmarking"] = True
            if "error" in test_lower or "handling" in test_lower:
                required_scenarios["error_handling"] = True
            if "concurrent" in test_lower:
                required_scenarios["concurrent_processing"] = True
            if "cache" in test_lower:
                required_scenarios["cache_integration"] = True
            if "memory" in test_lower:
                required_scenarios["memory_integration"] = True
            if "config" in test_lower:
                required_scenarios["configuration_validation"] = True
            if "orchestrator" in test_lower:
                required_scenarios["orchestrator_operations"] = True

        missing_scenarios = [scenario for scenario, covered in required_scenarios.items() if not covered]

        return {
            "file": str(test_file),
            "total_tests": len(analysis["test_functions"]),
            "async_tests": analysis["async_tests"],
            "performance_tests": analysis["performance_tests"],
            "error_tests": analysis["error_tests"],
            "fixtures": len(analysis["fixtures"]),
            "test_classes": len(analysis["test_classes"]),
            "scenario_coverage": len(required_scenarios) - len(missing_scenarios),
            "total_scenarios": len(required_scenarios),
            "missing_scenarios": missing_scenarios,
            "coverage_percentage": ((len(required_scenarios) - len(missing_scenarios)) / len(required_scenarios)) * 100,
        }

    def validate_behavioral_network_tests(self) -> Dict:
        """Validate Real-time Behavioral Network test coverage."""

        test_file = Path("tests/services/test_realtime_behavioral_network.py")
        analysis = self.analyze_test_file(test_file)

        if "error" in analysis:
            return analysis

        # Expected TODO method tests (the 5 critical methods)
        todo_methods = {
            "send_immediate_alert": False,
            "notify_agent": False,
            "set_priority_flag": False,
            "send_automated_response": False,
            "deliver_personalized_content": False,
        }

        # Expected additional test scenarios
        additional_scenarios = {
            "signal_processing": False,
            "pattern_recognition": False,
            "intent_prediction": False,
            "trigger_generation": False,
            "error_recovery": False,
            "performance_metrics": False,
            "integration_workflow": False,
        }

        # Check TODO method coverage
        for test_func in analysis["test_functions"]:
            test_lower = test_func.lower()

            # Check TODO methods
            if "send_immediate_alert" in test_lower or "immediate_alert" in test_lower:
                todo_methods["send_immediate_alert"] = True
            if "notify_agent" in test_lower or "agent_notification" in test_lower:
                todo_methods["notify_agent"] = True
            if "priority_flag" in test_lower or "set_priority" in test_lower:
                todo_methods["set_priority_flag"] = True
            if "automated_response" in test_lower or "send_automated" in test_lower:
                todo_methods["send_automated_response"] = True
            if "personalized_content" in test_lower or "deliver_personalized" in test_lower:
                todo_methods["deliver_personalized_content"] = True

            # Check additional scenarios
            if "signal" in test_lower and ("processing" in test_lower or "detector" in test_lower):
                additional_scenarios["signal_processing"] = True
            if "pattern" in test_lower:
                additional_scenarios["pattern_recognition"] = True
            if "intent" in test_lower:
                additional_scenarios["intent_prediction"] = True
            if "trigger" in test_lower:
                additional_scenarios["trigger_generation"] = True
            if "error" in test_lower or "recovery" in test_lower:
                additional_scenarios["error_recovery"] = True
            if "performance" in test_lower or "metrics" in test_lower:
                additional_scenarios["performance_metrics"] = True
            if "workflow" in test_lower or "integration" in test_lower:
                additional_scenarios["integration_workflow"] = True

        missing_todo_methods = [method for method, covered in todo_methods.items() if not covered]
        missing_scenarios = [scenario for scenario, covered in additional_scenarios.items() if not covered]

        total_scenarios = len(todo_methods) + len(additional_scenarios)
        covered_scenarios = (
            len(todo_methods) - len(missing_todo_methods) + len(additional_scenarios) - len(missing_scenarios)
        )

        return {
            "file": str(test_file),
            "total_tests": len(analysis["test_functions"]),
            "async_tests": analysis["async_tests"],
            "todo_methods_tested": len(todo_methods) - len(missing_todo_methods),
            "total_todo_methods": len(todo_methods),
            "missing_todo_methods": missing_todo_methods,
            "additional_scenarios_covered": len(additional_scenarios) - len(missing_scenarios),
            "total_additional_scenarios": len(additional_scenarios),
            "missing_scenarios": missing_scenarios,
            "coverage_percentage": (covered_scenarios / total_scenarios) * 100,
        }

    def validate_integration_tests(self) -> Dict:
        """Validate end-to-end integration test coverage."""

        test_file = Path("tests/integration/test_service6_end_to_end.py")
        analysis = self.analyze_test_file(test_file)

        if "error" in analysis:
            return analysis

        # Expected integration test scenarios
        integration_scenarios = {
            "high_intent_fast_track": False,
            "realtime_scoring_pipeline": False,
            "behavioral_trigger_workflow": False,
            "error_recovery_fallback": False,
            "concurrent_processing": False,
            "system_health_monitoring": False,
        }

        # Check integration scenario coverage
        for test_func in analysis["test_functions"]:
            test_lower = test_func.lower()

            if "high_intent" in test_lower and "fast_track" in test_lower:
                integration_scenarios["high_intent_fast_track"] = True
            if "realtime" in test_lower and ("scoring" in test_lower or "pipeline" in test_lower):
                integration_scenarios["realtime_scoring_pipeline"] = True
            if "behavioral" in test_lower and ("trigger" in test_lower or "workflow" in test_lower):
                integration_scenarios["behavioral_trigger_workflow"] = True
            if "error" in test_lower and ("recovery" in test_lower or "fallback" in test_lower):
                integration_scenarios["error_recovery_fallback"] = True
            if "concurrent" in test_lower:
                integration_scenarios["concurrent_processing"] = True
            if "health" in test_lower or "monitoring" in test_lower:
                integration_scenarios["system_health_monitoring"] = True

        missing_scenarios = [scenario for scenario, covered in integration_scenarios.items() if not covered]

        return {
            "file": str(test_file),
            "total_tests": len(analysis["test_functions"]),
            "integration_tests": analysis["integration_tests"],
            "scenario_coverage": len(integration_scenarios) - len(missing_scenarios),
            "total_scenarios": len(integration_scenarios),
            "missing_scenarios": missing_scenarios,
            "coverage_percentage": ((len(integration_scenarios) - len(missing_scenarios)) / len(integration_scenarios))
            * 100,
        }

    def generate_recommendations(self, validation_results: Dict) -> List[str]:
        """Generate recommendations based on validation results."""

        recommendations = []

        # Check overall test coverage
        for test_type, results in validation_results.items():
            if isinstance(results, dict) and "coverage_percentage" in results:
                coverage = results["coverage_percentage"]

                if coverage < 70:
                    recommendations.append(
                        f"🔴 {test_type}: Coverage is {coverage:.1f}% - Add more tests to reach 80%+"
                    )
                elif coverage < 85:
                    recommendations.append(
                        f"🟡 {test_type}: Coverage is {coverage:.1f}% - Good, consider adding edge cases"
                    )
                else:
                    recommendations.append(f"🟢 {test_type}: Coverage is {coverage:.1f}% - Excellent!")

        # Check for missing TODO method tests
        behavioral_results = validation_results.get("behavioral_network", {})
        if behavioral_results.get("missing_todo_methods"):
            methods = ", ".join(behavioral_results["missing_todo_methods"])
            recommendations.append(f"🔴 Missing TODO method tests: {methods}")

        # Check for performance tests
        total_perf_tests = sum(
            results.get("performance_tests", 0) for results in validation_results.values() if isinstance(results, dict)
        )
        if total_perf_tests < 3:
            recommendations.append("🟡 Add more performance benchmark tests (<200ms targets)")

        # Check for error handling
        total_error_tests = sum(
            results.get("error_tests", 0) for results in validation_results.values() if isinstance(results, dict)
        )
        if total_error_tests < 5:
            recommendations.append("🟡 Add more error handling and fallback tests")

        return recommendations

    def run_validation(self, detailed: bool = False) -> Dict:
        """Run complete validation of Service 6 test suite."""

        print("🔍 Validating Service 6 Test Suite")
        print("=" * 50)

        validation_results = {}

        # Validate AI Integration tests
        print("\n📋 Validating Service 6 AI Integration Tests...")
        ai_integration_results = self.validate_service6_ai_integration_tests()
        validation_results["ai_integration"] = ai_integration_results

        if "error" not in ai_integration_results:
            print(f"   Tests: {ai_integration_results['total_tests']}")
            print(f"   Coverage: {ai_integration_results['coverage_percentage']:.1f}%")
            if ai_integration_results["missing_scenarios"]:
                print(f"   Missing: {', '.join(ai_integration_results['missing_scenarios'])}")

        # Validate Behavioral Network tests
        print("\n📋 Validating Real-time Behavioral Network Tests...")
        behavioral_results = self.validate_behavioral_network_tests()
        validation_results["behavioral_network"] = behavioral_results

        if "error" not in behavioral_results:
            print(f"   Tests: {behavioral_results['total_tests']}")
            print(
                f"   TODO Methods: {behavioral_results['todo_methods_tested']}/{behavioral_results['total_todo_methods']}"
            )
            print(f"   Coverage: {behavioral_results['coverage_percentage']:.1f}%")
            if behavioral_results["missing_todo_methods"]:
                print(f"   Missing TODO: {', '.join(behavioral_results['missing_todo_methods'])}")

        # Validate Integration tests
        print("\n📋 Validating End-to-End Integration Tests...")
        integration_results = self.validate_integration_tests()
        validation_results["integration"] = integration_results

        if "error" not in integration_results:
            print(f"   Tests: {integration_results['total_tests']}")
            print(f"   Coverage: {integration_results['coverage_percentage']:.1f}%")
            if integration_results["missing_scenarios"]:
                print(f"   Missing: {', '.join(integration_results['missing_scenarios'])}")

        # Generate recommendations
        recommendations = self.generate_recommendations(validation_results)
        validation_results["recommendations"] = recommendations

        return validation_results

    def print_detailed_results(self, validation_results: Dict):
        """Print detailed validation results."""

        print(f"\n{'=' * 60}")
        print("📊 DETAILED VALIDATION RESULTS")
        print(f"{'=' * 60}")

        for test_type, results in validation_results.items():
            if test_type == "recommendations":
                continue

            if isinstance(results, dict) and "error" not in results:
                print(f"\n🧪 {test_type.replace('_', ' ').title()}:")
                print(f"   • File: {results.get('file', 'N/A')}")
                print(f"   • Total Tests: {results.get('total_tests', 0)}")
                print(f"   • Async Tests: {results.get('async_tests', 0)}")
                print(f"   • Performance Tests: {results.get('performance_tests', 0)}")
                print(f"   • Error Tests: {results.get('error_tests', 0)}")
                print(f"   • Coverage: {results.get('coverage_percentage', 0):.1f}%")

                if "todo_methods_tested" in results:
                    print(f"   • TODO Methods: {results['todo_methods_tested']}/{results['total_todo_methods']}")

                if results.get("missing_scenarios"):
                    print(f"   • Missing Scenarios: {', '.join(results['missing_scenarios'])}")

    def print_summary(self, validation_results: Dict):
        """Print validation summary."""

        print(f"\n{'=' * 60}")
        print("🎯 VALIDATION SUMMARY")
        print(f"{'=' * 60}")

        # Calculate totals
        total_tests = sum(
            results.get("total_tests", 0)
            for results in validation_results.values()
            if isinstance(results, dict) and "error" not in results
        )

        avg_coverage = sum(
            results.get("coverage_percentage", 0)
            for results in validation_results.values()
            if isinstance(results, dict) and "coverage_percentage" in results
        ) / max(1, len([r for r in validation_results.values() if isinstance(r, dict) and "coverage_percentage" in r]))

        print(f"📈 Total Tests: {total_tests}")
        print(f"📊 Average Coverage: {avg_coverage:.1f}%")

        # Print recommendations
        recommendations = validation_results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   {rec}")

        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if avg_coverage >= 85:
            print("   ✅ EXCELLENT - Test suite is production-ready!")
        elif avg_coverage >= 75:
            print("   🟡 GOOD - Minor improvements needed")
        else:
            print("   🔴 NEEDS WORK - Significant test gaps identified")


def main():
    """Main validation function."""

    parser = argparse.ArgumentParser(description="Validate Service 6 test suite")
    parser.add_argument("--detailed", action="store_true", help="Show detailed results")

    args = parser.parse_args()

    validator = TestValidator()
    validation_results = validator.run_validation(detailed=args.detailed)

    if args.detailed:
        validator.print_detailed_results(validation_results)

    validator.print_summary(validation_results)

    # Exit with appropriate code
    avg_coverage = sum(
        results.get("coverage_percentage", 0)
        for results in validation_results.values()
        if isinstance(results, dict) and "coverage_percentage" in results
    ) / max(1, len([r for r in validation_results.values() if isinstance(r, dict) and "coverage_percentage" in r]))

    sys.exit(0 if avg_coverage >= 75 else 1)


if __name__ == "__main__":
    main()
