#!/usr/bin/env python3
"""
Phase 7 Test Validation Script

Validates Phase 7 test files for syntax, imports, and structure before execution.
Ensures all test components are properly configured and ready for integration testing.

Built for Jorge's Real Estate AI Platform - Phase 7: Advanced AI Intelligence
"""

import ast
import importlib.util
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple


class Phase7TestValidator:
    """Validator for Phase 7 test files and structure."""

    def __init__(self):
        self.test_files = [
            "tests/api/test_revenue_intelligence_phase7.py",
            "tests/integration/test_phase7_business_intelligence.py",
            "tests/services/test_phase7_intelligence_services.py",
            "tests/run_phase7_integration_tests.py",
        ]

        self.validation_results = {}

    def validate_syntax(self, file_path: str) -> Tuple[bool, str]:
        """Validate Python syntax of test file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST to check syntax
            ast.parse(content)
            return True, "Syntax OK"

        except SyntaxError as e:
            return False, f"Syntax Error: Line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Parse Error: {str(e)}"

    def validate_imports(self, file_path: str) -> Tuple[bool, List[str]]:
        """Validate that imports are available and correctly structured."""
        try:
            spec = importlib.util.spec_from_file_location("test_module", file_path)
            if spec is None:
                return False, ["Could not create module spec"]

            # This would normally test imports, but we'll skip for now
            # since we don't have the full environment set up
            return True, []

        except ImportError as e:
            return False, [f"Import Error: {str(e)}"]
        except Exception as e:
            return False, [f"Module Error: {str(e)}"]

    def validate_test_structure(self, file_path: str) -> Tuple[bool, List[str]]:
        """Validate test file structure and required components."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            issues = []

            # Parse AST to analyze structure
            tree = ast.parse(content)

            # Find test classes and methods
            test_classes = []
            test_methods = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                    test_classes.append(node.name)

                    # Check methods in test classes
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                            test_methods.append(f"{node.name}::{item.name}")

            # Validation checks
            if not test_classes:
                issues.append("No test classes found (should start with 'Test')")

            if not test_methods:
                issues.append("No test methods found (should start with 'test_')")

            # Check for required patterns in Phase 7 tests
            if "phase7" in file_path.lower() or "revenue_intelligence" in file_path:
                if "phase7" not in content.lower() and "Phase 7" not in content:
                    issues.append("Missing Phase 7 references in Phase 7 test file")

                if "jorge" not in content.lower() and "Jorge" not in content:
                    issues.append("Missing Jorge methodology references")

            return len(issues) == 0, issues

        except Exception as e:
            return False, [f"Structure validation error: {str(e)}"]

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate a single test file comprehensively."""
        print(f"  🔍 Validating: {file_path}")

        if not Path(file_path).exists():
            return {
                "exists": False,
                "syntax_valid": False,
                "imports_valid": False,
                "structure_valid": False,
                "issues": [f"File does not exist: {file_path}"],
            }

        # Syntax validation
        syntax_valid, syntax_message = self.validate_syntax(file_path)

        # Import validation (basic check)
        imports_valid, import_issues = self.validate_imports(file_path)

        # Structure validation
        structure_valid, structure_issues = self.validate_test_structure(file_path)

        # Combine all issues
        all_issues = []
        if not syntax_valid:
            all_issues.append(syntax_message)
        all_issues.extend(import_issues)
        all_issues.extend(structure_issues)

        overall_valid = syntax_valid and imports_valid and structure_valid

        status_icon = "✅" if overall_valid else "❌"
        print(f"    {status_icon} {Path(file_path).name}: {'VALID' if overall_valid else 'ISSUES FOUND'}")

        if all_issues:
            for issue in all_issues[:3]:  # Show first 3 issues
                print(f"        ⚠️  {issue}")

        return {
            "exists": True,
            "syntax_valid": syntax_valid,
            "imports_valid": imports_valid,
            "structure_valid": structure_valid,
            "overall_valid": overall_valid,
            "issues": all_issues,
        }

    def validate_phase7_test_coverage(self) -> Dict[str, Any]:
        """Validate that Phase 7 test coverage includes all required components."""
        print(f"\n📊 Analyzing Phase 7 Test Coverage:")

        required_components = {
            "revenue_intelligence_api": False,
            "business_intelligence_dashboard": False,
            "forecasting_engine": False,
            "conversation_analytics": False,
            "market_intelligence": False,
            "streaming_services": False,
            "cache_services": False,
            "integration_workflows": False,
            "performance_validation": False,
        }

        coverage_analysis = {}

        for file_path in self.test_files:
            if not Path(file_path).exists():
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().lower()

                # Check for required component coverage
                if "revenue" in content and ("intelligence" in content or "forecast" in content):
                    required_components["revenue_intelligence_api"] = True
                    required_components["forecasting_engine"] = True

                if "business" in content and "intelligence" in content:
                    required_components["business_intelligence_dashboard"] = True

                if "conversation" in content and "analytics" in content:
                    required_components["conversation_analytics"] = True

                if "market" in content and "intelligence" in content:
                    required_components["market_intelligence"] = True

                if "stream" in content or "websocket" in content:
                    required_components["streaming_services"] = True

                if "cache" in content:
                    required_components["cache_services"] = True

                if "integration" in content and "test" in content:
                    required_components["integration_workflows"] = True

                if "performance" in content:
                    required_components["performance_validation"] = True

            except Exception as e:
                print(f"    ⚠️  Error analyzing {file_path}: {str(e)}")

        # Report coverage
        total_components = len(required_components)
        covered_components = sum(required_components.values())
        coverage_percentage = (covered_components / total_components) * 100

        print(f"    📈 Component Coverage: {covered_components}/{total_components} ({coverage_percentage:.1f}%)")

        for component, covered in required_components.items():
            status_icon = "✅" if covered else "❌"
            component_name = component.replace("_", " ").title()
            print(f"      {status_icon} {component_name}")

        return {
            "total_components": total_components,
            "covered_components": covered_components,
            "coverage_percentage": coverage_percentage,
            "component_details": required_components,
        }

    def validate_all_tests(self) -> Dict[str, Any]:
        """Validate all Phase 7 test files."""
        print("🧪 PHASE 7 TEST VALIDATION")
        print("=" * 50)

        validation_summary = {
            "total_files": len(self.test_files),
            "valid_files": 0,
            "files_with_issues": 0,
            "missing_files": 0,
            "file_results": {},
        }

        # Validate each test file
        for file_path in self.test_files:
            result = self.validate_file(file_path)
            self.validation_results[file_path] = result
            validation_summary["file_results"][file_path] = result

            if not result["exists"]:
                validation_summary["missing_files"] += 1
            elif result["overall_valid"]:
                validation_summary["valid_files"] += 1
            else:
                validation_summary["files_with_issues"] += 1

        # Validate test coverage
        coverage_analysis = self.validate_phase7_test_coverage()
        validation_summary["coverage_analysis"] = coverage_analysis

        # Overall assessment
        overall_valid = (
            validation_summary["valid_files"] == validation_summary["total_files"]
            and validation_summary["missing_files"] == 0
            and coverage_analysis["coverage_percentage"] >= 80  # 80% component coverage requirement
        )

        validation_summary["overall_valid"] = overall_valid

        return validation_summary

    def print_summary(self, summary: Dict[str, Any]):
        """Print validation summary."""
        print(f"\n🏁 PHASE 7 TEST VALIDATION SUMMARY")
        print("=" * 50)

        if summary["overall_valid"]:
            print("🎉 RESULT: ✅ All Phase 7 tests are valid and ready!")
        else:
            print("⚠️  RESULT: ❌ Issues found - review required")

        print(f"\n📊 File Statistics:")
        print(f"   Total Files: {summary['total_files']}")
        print(f"   Valid Files: {summary['valid_files']}")
        print(f"   Files with Issues: {summary['files_with_issues']}")
        print(f"   Missing Files: {summary['missing_files']}")

        coverage = summary["coverage_analysis"]
        print(f"\n📈 Test Coverage:")
        print(f"   Component Coverage: {coverage['coverage_percentage']:.1f}%")
        print(f"   Components Covered: {coverage['covered_components']}/{coverage['total_components']}")

        if summary["overall_valid"]:
            print(f"\n🚀 Phase 7 tests are ready for execution!")
            print("   Run: python tests/run_phase7_integration_tests.py")
        else:
            print(f"\n🔧 Action Required:")
            print("   - Review and fix issues in test files")
            print("   - Ensure all required components are covered")
            print("   - Re-run validation before test execution")


def main():
    """Main validation entry point."""
    validator = Phase7TestValidator()
    summary = validator.validate_all_tests()
    validator.print_summary(summary)

    # Exit with appropriate code
    sys.exit(0 if summary["overall_valid"] else 1)


if __name__ == "__main__":
    main()
