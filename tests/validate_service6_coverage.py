import pytest
pytestmark = pytest.mark.integration

#!/usr/bin/env python3

"""
📊 Service 6 Test Coverage Validation Script
============================================

Validates and reports test coverage across all Service 6 components to ensure
80%+ coverage target is met. Provides detailed analysis of coverage gaps
and actionable recommendations.

Features:
- Component-level coverage analysis
- Coverage gap identification
- Missing test recommendations
- Integration with CI/CD pipelines
- Detailed reporting with visualizations
- Automatic coverage threshold validation

Usage:
    python tests/validate_service6_coverage.py [options]

Examples:
    python tests/validate_service6_coverage.py                    # Run coverage validation
    python tests/validate_service6_coverage.py --threshold 85     # Custom threshold
    python tests/validate_service6_coverage.py --detailed         # Detailed analysis
    python tests/validate_service6_coverage.py --report-format json  # JSON output

Author: Claude AI Enhancement System
Date: 2026-01-17
"""

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import colorama
from colorama import Back, Fore, Style

# Initialize colorama for colored output
colorama.init(autoreset=True)


@dataclass
class CoverageResult:
    """Coverage analysis result for a component"""

    component_name: str
    file_path: str
    lines_total: int
    lines_covered: int
    coverage_percentage: float
    missing_lines: List[int]
    missing_functions: List[str]
    critical_gaps: List[str]


@dataclass
class CoverageReport:
    """Complete coverage report"""

    overall_coverage: float
    target_threshold: float
    target_met: bool
    components: List[CoverageResult]
    recommendations: List[str]
    summary_stats: Dict
    timestamp: str


class Service6CoverageValidator:
    """Main coverage validator for Service 6 components"""

    def __init__(self, threshold: float = 80.0):
        self.threshold = threshold
        self.project_root = Path(__file__).parent.parent
        self.coverage_dir = self.project_root / "tests" / "coverage"

        # Service 6 core components to analyze
        self.service6_components = {
            "service6_ai_integration.py": {
                "path": "ghl_real_estate_ai/services/service6_ai_integration.py",
                "description": "Core AI orchestration and integration",
                "critical_functions": [
                    "comprehensive_lead_analysis",
                    "realtime_lead_scoring",
                    "synthesize_insights",
                    "initialize",
                ],
            },
            "realtime_behavioral_network.py": {
                "path": "ghl_real_estate_ai/services/realtime_behavioral_network.py",
                "description": "Real-time behavioral analysis and triggers",
                "critical_functions": [
                    "process_signal",
                    "detect_patterns",
                    "generate_insights",
                    "_send_immediate_alert",
                    "_notify_agent",
                    "_set_priority_flag",
                    "_send_automated_response",
                    "_deliver_personalized_content",
                ],
            },
            "autonomous_followup_engine.py": {
                "path": "ghl_real_estate_ai/services/autonomous_followup_engine.py",
                "description": "Autonomous follow-up orchestration",
                "critical_functions": ["analyze_lead_for_followup", "execute_followup_sequence", "optimize_timing"],
            },
            "database_service.py": {
                "path": "ghl_real_estate_ai/services/database_service.py",
                "description": "Enhanced database operations",
                "critical_functions": [
                    "save_lead",
                    "get_lead",
                    "store_ai_analysis",
                    "update_lead_score",
                    "update_lead_intelligence",
                ],
            },
        }

    def print_banner(self):
        """Print validation banner"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
        print(f"📊 SERVICE 6 TEST COVERAGE VALIDATION")
        print(f"{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Target Coverage Threshold: {self.threshold}%{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Components Analyzed: {len(self.service6_components)}{Style.RESET_ALL}\n")

    def run_coverage_analysis(self) -> Tuple[bool, str]:
        """Run pytest with coverage to generate coverage data"""
        print(f"{Fore.BLUE}🧪 Running comprehensive test suite with coverage...{Style.RESET_ALL}")

        # Coverage command for Service 6 components
        coverage_paths = [comp["path"] for comp in self.service6_components.values()]
        coverage_target = ",".join(coverage_paths)

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/services/test_service6_ai_integration.py",
            "tests/services/test_realtime_behavioral_network.py",
            "tests/services/test_service6_database_comprehensive.py",
            "tests/integration/test_service6_end_to_end_comprehensive.py",
            "-v",
            "--tb=short",
            f"--cov={coverage_target}",
            "--cov-report=term-missing",
            "--cov-report=xml:tests/coverage/coverage.xml",
            "--cov-report=html:tests/coverage/html",
            "--cov-report=json:tests/coverage/coverage.json",
            f"--cov-fail-under={self.threshold}",
            "--timeout=600",
        ]

        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, timeout=900)

            return result.returncode == 0, result.stdout + "\n" + result.stderr

        except subprocess.TimeoutExpired:
            return False, "Coverage analysis timed out"
        except Exception as e:
            return False, f"Coverage analysis failed: {e}"

    def parse_coverage_xml(self) -> Dict:
        """Parse coverage XML report"""
        xml_path = self.coverage_dir / "coverage.xml"

        if not xml_path.exists():
            return {}

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            coverage_data = {}

            for package in root.findall(".//package"):
                for class_elem in package.findall("classes/class"):
                    filename = class_elem.get("filename", "")

                    # Extract component name from path
                    component_name = Path(filename).name

                    if component_name in self.service6_components:
                        lines = class_elem.findall("lines/line")

                        total_lines = len(lines)
                        covered_lines = len([l for l in lines if l.get("hits", "0") != "0"])
                        missing_lines = [int(l.get("number", 0)) for l in lines if l.get("hits", "0") == "0"]

                        coverage_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0

                        coverage_data[component_name] = {
                            "lines_total": total_lines,
                            "lines_covered": covered_lines,
                            "coverage_percentage": coverage_percentage,
                            "missing_lines": missing_lines,
                        }

            return coverage_data

        except Exception as e:
            print(f"{Fore.RED}❌ Failed to parse coverage XML: {e}{Style.RESET_ALL}")
            return {}

    def parse_coverage_json(self) -> Dict:
        """Parse coverage JSON report for detailed analysis"""
        json_path = self.coverage_dir / "coverage.json"

        if not json_path.exists():
            return {}

        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            return data.get("files", {})

        except Exception as e:
            print(f"{Fore.RED}❌ Failed to parse coverage JSON: {e}{Style.RESET_ALL}")
            return {}

    def analyze_missing_functions(self, component_name: str, missing_lines: List[int]) -> Tuple[List[str], List[str]]:
        """Analyze which functions are missing coverage"""
        component_config = self.service6_components.get(component_name, {})
        component_path = self.project_root / component_config.get("path", "")

        if not component_path.exists():
            return [], []

        try:
            with open(component_path, "r") as f:
                source_lines = f.readlines()

            missing_functions = []
            critical_gaps = []

            critical_function_names = component_config.get("critical_functions", [])

            # Simple function detection (could be improved with AST)
            for i, line in enumerate(source_lines, 1):
                line_stripped = line.strip()

                # Look for function definitions
                if line_stripped.startswith("def ") or line_stripped.startswith("async def "):
                    # Extract function name
                    func_match = re.match(r"(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)", line_stripped)
                    if func_match:
                        func_name = func_match.group(1)

                        # Check if this line is missing coverage
                        if i in missing_lines:
                            missing_functions.append(func_name)

                            # Check if it's a critical function
                            if func_name in critical_function_names:
                                critical_gaps.append(f"Critical function '{func_name}' not tested")

            return missing_functions, critical_gaps

        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Failed to analyze functions in {component_name}: {e}{Style.RESET_ALL}")
            return [], []

    def generate_recommendations(self, components: List[CoverageResult]) -> List[str]:
        """Generate actionable recommendations based on coverage analysis"""
        recommendations = []

        # Overall coverage recommendations
        low_coverage_components = [c for c in components if c.coverage_percentage < self.threshold]

        if low_coverage_components:
            recommendations.append(
                f"🎯 Priority: {len(low_coverage_components)} components below {self.threshold}% threshold need attention"
            )

        # Component-specific recommendations
        for component in sorted(components, key=lambda x: x.coverage_percentage):
            if component.coverage_percentage < self.threshold:
                gap = self.threshold - component.coverage_percentage
                recommendations.append(
                    f"📝 {component.component_name}: Add tests to cover {gap:.1f}% gap ({len(component.missing_lines)} uncovered lines)"
                )

                # Critical function recommendations
                if component.critical_gaps:
                    for gap in component.critical_gaps:
                        recommendations.append(f"🚨 {component.component_name}: {gap}")

                # Specific function recommendations
                if component.missing_functions:
                    top_missing = component.missing_functions[:3]  # Top 3 missing functions
                    recommendations.append(
                        f"🔧 {component.component_name}: Add tests for functions: {', '.join(top_missing)}"
                    )

        # General recommendations
        if any(c.coverage_percentage > 90 for c in components):
            recommendations.append("✨ Excellent coverage in some components - use as examples for others")

        if all(c.coverage_percentage >= self.threshold for c in components):
            recommendations.append("🎉 All components meet coverage threshold - consider increasing target to 85%")

        return recommendations

    def validate_coverage(self, detailed: bool = False) -> CoverageReport:
        """Main coverage validation workflow"""
        from datetime import datetime

        print(f"{Fore.BLUE}📊 Starting Service 6 coverage validation...{Style.RESET_ALL}\n")

        # Run coverage analysis
        success, output = self.run_coverage_analysis()

        if not success:
            print(f"{Fore.RED}❌ Coverage analysis failed:{Style.RESET_ALL}")
            print(output)
            return CoverageReport(
                overall_coverage=0.0,
                target_threshold=self.threshold,
                target_met=False,
                components=[],
                recommendations=["Fix test failures before analyzing coverage"],
                summary_stats={},
                timestamp=datetime.now().isoformat(),
            )

        print(f"{Fore.GREEN}✅ Coverage analysis completed successfully{Style.RESET_ALL}\n")

        # Parse coverage data
        xml_data = self.parse_coverage_xml()
        json_data = self.parse_coverage_json()

        # Analyze each component
        components = []
        total_coverage = 0.0

        for component_name, config in self.service6_components.items():
            if component_name in xml_data:
                xml_component = xml_data[component_name]

                # Analyze missing functions if detailed analysis requested
                missing_functions = []
                critical_gaps = []

                if detailed:
                    missing_functions, critical_gaps = self.analyze_missing_functions(
                        component_name, xml_component["missing_lines"]
                    )

                component_result = CoverageResult(
                    component_name=component_name,
                    file_path=config["path"],
                    lines_total=xml_component["lines_total"],
                    lines_covered=xml_component["lines_covered"],
                    coverage_percentage=xml_component["coverage_percentage"],
                    missing_lines=xml_component["missing_lines"],
                    missing_functions=missing_functions,
                    critical_gaps=critical_gaps,
                )

                components.append(component_result)
                total_coverage += xml_component["coverage_percentage"]

        # Calculate overall coverage
        overall_coverage = total_coverage / len(components) if components else 0.0
        target_met = overall_coverage >= self.threshold

        # Generate recommendations
        recommendations = self.generate_recommendations(components)

        # Summary statistics
        summary_stats = {
            "total_components": len(components),
            "components_above_threshold": len([c for c in components if c.coverage_percentage >= self.threshold]),
            "components_below_threshold": len([c for c in components if c.coverage_percentage < self.threshold]),
            "highest_coverage": max((c.coverage_percentage for c in components), default=0),
            "lowest_coverage": min((c.coverage_percentage for c in components), default=0),
            "total_lines": sum(c.lines_total for c in components),
            "total_covered_lines": sum(c.lines_covered for c in components),
        }

        return CoverageReport(
            overall_coverage=overall_coverage,
            target_threshold=self.threshold,
            target_met=target_met,
            components=components,
            recommendations=recommendations,
            summary_stats=summary_stats,
            timestamp=datetime.now().isoformat(),
        )

    def print_coverage_report(self, report: CoverageReport, detailed: bool = False):
        """Print formatted coverage report"""
        print(f"{Fore.CYAN}{Style.BRIGHT}📋 SERVICE 6 COVERAGE REPORT{Style.RESET_ALL}")
        print("=" * 60)

        # Overall status
        status_color = Fore.GREEN if report.target_met else Fore.RED
        status_icon = "✅" if report.target_met else "❌"

        print(
            f"\n{status_color}{Style.BRIGHT}{status_icon} Overall Coverage: {report.overall_coverage:.1f}%{Style.RESET_ALL}"
        )
        print(f"   Target Threshold: {report.target_threshold}%")
        print(f"   Target Met: {'Yes' if report.target_met else 'No'}")

        # Summary statistics
        stats = report.summary_stats
        print(f"\n{Fore.WHITE}{Style.BRIGHT}📊 Summary Statistics:{Style.RESET_ALL}")
        print(f"   Total Components: {stats['total_components']}")
        print(f"   Above Threshold: {Fore.GREEN}{stats['components_above_threshold']}{Style.RESET_ALL}")
        print(f"   Below Threshold: {Fore.RED}{stats['components_below_threshold']}{Style.RESET_ALL}")
        print(f"   Highest Coverage: {stats['highest_coverage']:.1f}%")
        print(f"   Lowest Coverage: {stats['lowest_coverage']:.1f}%")
        print(f"   Total Lines: {stats['total_lines']:,}")
        print(f"   Covered Lines: {stats['total_covered_lines']:,}")

        # Component breakdown
        print(f"\n{Fore.WHITE}{Style.BRIGHT}🔍 Component Analysis:{Style.RESET_ALL}")

        # Sort by coverage percentage (lowest first)
        sorted_components = sorted(report.components, key=lambda x: x.coverage_percentage)

        for component in sorted_components:
            coverage_color = Fore.GREEN if component.coverage_percentage >= report.target_threshold else Fore.RED

            print(f"\n   {coverage_color}{component.component_name}{Style.RESET_ALL}")
            print(f"     Coverage: {coverage_color}{component.coverage_percentage:.1f}%{Style.RESET_ALL}")
            print(f"     Lines: {component.lines_covered}/{component.lines_total}")
            print(f"     Missing Lines: {len(component.missing_lines)}")

            if detailed and component.missing_functions:
                print(f"     Missing Functions: {', '.join(component.missing_functions[:5])}")
                if len(component.missing_functions) > 5:
                    print(f"                        ... and {len(component.missing_functions) - 5} more")

            if component.critical_gaps:
                print(f"     {Fore.RED}Critical Gaps: {len(component.critical_gaps)}{Style.RESET_ALL}")
                for gap in component.critical_gaps:
                    print(f"       - {gap}")

        # Recommendations
        if report.recommendations:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}💡 Recommendations:{Style.RESET_ALL}")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"   {i}. {rec}")

        # Final status
        if report.target_met:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 SERVICE 6 COVERAGE VALIDATION: PASSED")
            print(f"All components meet the {report.target_threshold}% coverage threshold!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}{Style.BRIGHT}💥 SERVICE 6 COVERAGE VALIDATION: FAILED")
            print(f"Some components are below the {report.target_threshold}% coverage threshold.")
            print(f"Review recommendations and add tests to improve coverage.{Style.RESET_ALL}")

    def save_report(self, report: CoverageReport, format: str = "json", output_file: Optional[str] = None):
        """Save coverage report to file"""
        if not output_file:
            output_file = f"service6_coverage_report.{format}"

        output_path = self.coverage_dir / output_file

        if format == "json":
            with open(output_path, "w") as f:
                json.dump(asdict(report), f, indent=2, default=str)
        elif format == "txt":
            with open(output_path, "w") as f:
                # Simple text format
                f.write(f"Service 6 Coverage Report\n")
                f.write(f"========================\n\n")
                f.write(f"Overall Coverage: {report.overall_coverage:.1f}%\n")
                f.write(f"Target Threshold: {report.target_threshold}%\n")
                f.write(f"Target Met: {report.target_met}\n\n")

                f.write("Components:\n")
                for component in sorted(report.components, key=lambda x: x.coverage_percentage):
                    f.write(f"  {component.component_name}: {component.coverage_percentage:.1f}%\n")

                if report.recommendations:
                    f.write("\nRecommendations:\n")
                    for i, rec in enumerate(report.recommendations, 1):
                        f.write(f"  {i}. {rec}\n")

        print(f"{Fore.GREEN}✅ Coverage report saved to {output_path}{Style.RESET_ALL}")


def main():
    """Main entry point for coverage validation"""
    parser = argparse.ArgumentParser(
        description="Service 6 Test Coverage Validation", formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--threshold", type=float, default=80.0, help="Coverage threshold percentage (default: 80.0)")

    parser.add_argument("--detailed", action="store_true", help="Enable detailed analysis including function coverage")

    parser.add_argument(
        "--report-format", choices=["json", "txt"], default="json", help="Report output format (default: json)"
    )

    parser.add_argument("--output", type=str, help="Output file for coverage report")

    parser.add_argument("--ci", action="store_true", help="CI mode - exit with error code if coverage fails")

    args = parser.parse_args()

    # Create validator
    validator = Service6CoverageValidator(threshold=args.threshold)
    validator.print_banner()

    try:
        # Validate coverage
        report = validator.validate_coverage(detailed=args.detailed)

        # Print report
        validator.print_coverage_report(report, detailed=args.detailed)

        # Save report
        validator.save_report(report, format=args.report_format, output_file=args.output)

        # Exit with appropriate code
        if args.ci:
            exit_code = 0 if report.target_met else 1
            sys.exit(exit_code)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Coverage validation interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Coverage validation failed: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
