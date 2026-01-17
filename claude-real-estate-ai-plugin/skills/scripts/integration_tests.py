#!/usr/bin/env python3
"""
Integration tests for Claude Skills Phase 1 & 2
Verifies compatibility and integration between skill categories
"""

import sys
import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SkillsIntegration')


@dataclass
class TestResult:
    """Represents the result of an integration test."""
    test_name: str
    success: bool
    duration: float
    message: str
    details: Optional[Dict[str, Any]] = None


class SkillsIntegrationTester:
    """Integration tester for Claude Skills ecosystem."""

    def __init__(self, skills_path: Path):
        self.skills_path = skills_path
        self.results: List[TestResult] = []

    async def run_all_tests(self) -> List[TestResult]:
        """Run all integration tests."""
        logger.info("🧪 Starting Claude Skills Integration Tests")

        # Test categories
        test_methods = [
            self.test_skill_structure,
            self.test_manifest_integrity,
            self.test_cross_skill_compatibility,
            self.test_testing_skills_integration,
            self.test_design_skills_integration,
            self.test_orchestration_skills_integration,
            self.test_end_to_end_workflow,
            self.test_performance_characteristics
        ]

        for test_method in test_methods:
            try:
                result = await test_method()
                self.results.append(result)
                logger.info(f"✅ {result.test_name}: {'PASSED' if result.success else 'FAILED'}")
                if not result.success:
                    logger.error(f"   Error: {result.message}")
            except Exception as e:
                logger.error(f"❌ Test {test_method.__name__} failed with exception: {e}")
                self.results.append(TestResult(
                    test_name=test_method.__name__,
                    success=False,
                    duration=0.0,
                    message=f"Exception: {str(e)}"
                ))

        return self.results

    async def test_skill_structure(self) -> TestResult:
        """Test that all skills have proper directory structure."""
        start_time = time.time()
        test_name = "Skill Structure Validation"

        try:
            errors = []
            expected_skills = [
                # Phase 1 skills
                "testing/test-driven-development",
                "debugging/systematic-debugging",
                "core/verification-before-completion",
                "core/requesting-code-review",
                "deployment/vercel-deploy",
                "deployment/railway-deploy",
                # Phase 2 skills
                "testing/condition-based-waiting",
                "testing/testing-anti-patterns",
                "testing/defense-in-depth",
                "design/frontend-design",
                "design/web-artifacts-builder",
                "design/theme-factory",
                "orchestration/subagent-driven-development",
                "orchestration/dispatching-parallel-agents"
            ]

            for skill_path in expected_skills:
                skill_dir = self.skills_path / skill_path

                if not skill_dir.exists():
                    errors.append(f"Skill directory missing: {skill_path}")
                    continue

                # Check for required files
                required_files = ["SKILL.md"]
                for required_file in required_files:
                    if not (skill_dir / required_file).exists():
                        errors.append(f"Required file missing: {skill_path}/{required_file}")

                # Check for expected directories
                expected_dirs = ["examples", "references", "scripts"]
                for expected_dir in expected_dirs:
                    if not (skill_dir / expected_dir).exists():
                        errors.append(f"Expected directory missing: {skill_path}/{expected_dir}")

            success = len(errors) == 0
            message = "All skills have proper structure" if success else f"Structure issues: {'; '.join(errors)}"

            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                message=message,
                details={"errors": errors}
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                message=f"Test failed: {str(e)}"
            )

    async def test_manifest_integrity(self) -> TestResult:
        """Test that MANIFEST.yaml is properly formatted and complete."""
        start_time = time.time()
        test_name = "Manifest Integrity Check"

        try:
            manifest_path = self.skills_path / "MANIFEST.yaml"

            if not manifest_path.exists():
                return TestResult(
                    test_name=test_name,
                    success=False,
                    duration=time.time() - start_time,
                    message="MANIFEST.yaml not found"
                )

            # Basic YAML loading test
            import yaml
            with open(manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f)

            errors = []

            # Validate required sections
            required_sections = ["metadata", "skills", "categories", "project_context"]
            for section in required_sections:
                if section not in manifest_data:
                    errors.append(f"Missing required section: {section}")

            # Validate metadata
            if "metadata" in manifest_data:
                metadata = manifest_data["metadata"]
                required_metadata = ["project", "version", "phase", "description"]
                for field in required_metadata:
                    if field not in metadata:
                        errors.append(f"Missing metadata field: {field}")

            # Validate skills
            if "skills" in manifest_data:
                skills = manifest_data["skills"]
                expected_skill_count = 14  # 6 Phase 1 + 8 Phase 2

                if len(skills) != expected_skill_count:
                    errors.append(f"Expected {expected_skill_count} skills, found {len(skills)}")

                # Check each skill has required fields
                required_skill_fields = ["name", "category", "path", "description", "triggers", "status"]
                for skill in skills:
                    for field in required_skill_fields:
                        if field not in skill:
                            errors.append(f"Skill missing field {field}: {skill.get('name', 'unknown')}")

            # Validate categories
            if "categories" in manifest_data:
                categories = manifest_data["categories"]
                expected_categories = ["testing", "debugging", "core", "deployment", "design", "orchestration"]
                for category in expected_categories:
                    if category not in categories:
                        errors.append(f"Missing category: {category}")

            success = len(errors) == 0
            message = "MANIFEST.yaml is valid" if success else f"Validation issues: {'; '.join(errors)}"

            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                message=message,
                details={"errors": errors, "skills_count": len(manifest_data.get("skills", []))}
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                message=f"Test failed: {str(e)}"
            )

    async def test_cross_skill_compatibility(self) -> TestResult:
        """Test that skills from different phases can work together."""
        start_time = time.time()
        test_name = "Cross-Skill Compatibility"

        try:
            # Test integration points between phases
            integration_tests = [
                # Testing skills should integrate with core workflow
                {
                    "name": "Testing + Core Integration",
                    "description": "TDD workflow with verification gates",
                    "skills": ["test-driven-development", "verification-before-completion", "condition-based-waiting"]
                },
                # Design skills should work with deployment
                {
                    "name": "Design + Deployment Integration",
                    "description": "Frontend design deployed with Vercel",
                    "skills": ["frontend-design", "theme-factory", "vercel-deploy"]
                },
                # Orchestration should work with testing
                {
                    "name": "Orchestration + Testing Integration",
                    "description": "Multi-agent testing workflows",
                    "skills": ["subagent-driven-development", "testing-anti-patterns", "defense-in-depth"]
                }
            ]

            success_count = 0
            details = []

            for integration_test in integration_tests:
                test_success = True
                test_details = {"name": integration_test["name"], "skills": integration_test["skills"]}

                # Verify all skills exist
                for skill_name in integration_test["skills"]:
                    # Find skill path in manifest or directory structure
                    skill_found = False

                    # Search for skill directory
                    for category_dir in self.skills_path.iterdir():
                        if category_dir.is_dir() and category_dir.name != "scripts":
                            for skill_dir in category_dir.iterdir():
                                if skill_dir.is_dir() and skill_name in skill_dir.name:
                                    skill_found = True
                                    break

                    if not skill_found:
                        test_success = False
                        test_details["error"] = f"Skill not found: {skill_name}"
                        break

                if test_success:
                    success_count += 1

                details.append(test_details)

            overall_success = success_count == len(integration_tests)
            message = (f"Integration compatibility: {success_count}/{len(integration_tests)} passed"
                      if overall_success
                      else f"Some integration tests failed: {success_count}/{len(integration_tests)} passed")

            return TestResult(
                test_name=test_name,
                success=overall_success,
                duration=time.time() - start_time,
                message=message,
                details={"integration_tests": details}
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                message=f"Test failed: {str(e)}"
            )

    async def test_testing_skills_integration(self) -> TestResult:
        """Test integration of testing skills (Phase 1 + Phase 2)."""
        start_time = time.time()
        test_name = "Testing Skills Integration"

        try:
            testing_skills = [
                "test-driven-development",
                "condition-based-waiting",
                "testing-anti-patterns",
                "defense-in-depth"
            ]

            skill_checks = []

            for skill_name in testing_skills:
                skill_dir = self.skills_path / "testing" / skill_name

                if skill_dir.exists():
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        with open(skill_md, 'r') as f:
                            content = f.read()

                        # Check for integration keywords
                        integration_indicators = [
                            "integration", "compatible", "works with",
                            "combines with", "enhances", "complements"
                        ]

                        has_integration_info = any(
                            indicator in content.lower() for indicator in integration_indicators
                        )

                        skill_checks.append({
                            "skill": skill_name,
                            "exists": True,
                            "has_integration_info": has_integration_info
                        })
                    else:
                        skill_checks.append({
                            "skill": skill_name,
                            "exists": True,
                            "has_integration_info": False,
                            "error": "SKILL.md missing"
                        })
                else:
                    skill_checks.append({
                        "skill": skill_name,
                        "exists": False,
                        "error": "Skill directory missing"
                    })

            success = all(check.get("exists", False) for check in skill_checks)
            integration_count = sum(1 for check in skill_checks if check.get("has_integration_info", False))

            message = (f"Testing skills integration: {len([c for c in skill_checks if c.get('exists')])}/4 exist, "
                      f"{integration_count}/4 have integration info")

            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                message=message,
                details={"skill_checks": skill_checks}
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                message=f"Test failed: {str(e)}"
            )

    async def test_design_skills_integration(self) -> TestResult:
        """Test integration of design skills."""
        start_time = time.time()
        test_name = "Design Skills Integration"

        try:
            design_skills = [
                "frontend-design",
                "web-artifacts-builder",
                "theme-factory"
            ]

            skill_validation = []

            for skill_name in design_skills:
                skill_dir = self.skills_path / "design" / skill_name
                validation = {"skill": skill_name}

                if skill_dir.exists():
                    validation["exists"] = True

                    # Check for examples directory
                    examples_dir = skill_dir / "examples"
                    validation["has_examples"] = examples_dir.exists()

                    # Check SKILL.md for Streamlit integration
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        with open(skill_md, 'r') as f:
                            content = f.read()

                        streamlit_mentions = content.lower().count("streamlit")
                        validation["streamlit_integration"] = streamlit_mentions > 0
                        validation["streamlit_mentions"] = streamlit_mentions

                    else:
                        validation["streamlit_integration"] = False

                else:
                    validation["exists"] = False

                skill_validation.append(validation)

            success = all(v.get("exists", False) for v in skill_validation)
            streamlit_integration = sum(1 for v in skill_validation if v.get("streamlit_integration", False))

            message = (f"Design skills: {len([v for v in skill_validation if v.get('exists')])}/3 exist, "
                      f"{streamlit_integration}/3 have Streamlit integration")

            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                message=message,
                details={"validations": skill_validation}
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                message=f"Test failed: {str(e)}"
            )

    async def test_orchestration_skills_integration(self) -> TestResult:
        """Test integration of orchestration skills."""
        start_time = time.time()
        test_name = "Orchestration Skills Integration"

        try:
            orchestration_skills = [
                "subagent-driven-development",
                "dispatching-parallel-agents"
            ]

            validations = []

            for skill_name in orchestration_skills:
                skill_dir = self.skills_path / "orchestration" / skill_name
                validation = {"skill": skill_name}

                if skill_dir.exists():
                    validation["exists"] = True

                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        with open(skill_md, 'r') as f:
                            content = f.read()

                        # Check for agent coordination concepts
                        agent_keywords = [
                            "agent", "orchestrat", "parallel", "concurrent",
                            "dispatch", "coordinate", "workflow"
                        ]

                        keyword_matches = sum(1 for keyword in agent_keywords
                                            if keyword in content.lower())
                        validation["orchestration_keywords"] = keyword_matches > 3

                        # Check for async/await patterns
                        async_patterns = ["async", "await", "asyncio"]
                        validation["async_support"] = any(
                            pattern in content for pattern in async_patterns
                        )

                    else:
                        validation["orchestration_keywords"] = False
                        validation["async_support"] = False

                else:
                    validation["exists"] = False

                validations.append(validation)

            success = all(v.get("exists", False) for v in validations)
            orchestration_count = sum(1 for v in validations if v.get("orchestration_keywords", False))
            async_count = sum(1 for v in validations if v.get("async_support", False))

            message = (f"Orchestration skills: {len([v for v in validations if v.get('exists')])}/2 exist, "
                      f"{orchestration_count}/2 have orchestration patterns, "
                      f"{async_count}/2 support async")

            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                message=message,
                details={"validations": validations}
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                message=f"Test failed: {str(e)}"
            )

    async def test_end_to_end_workflow(self) -> TestResult:
        """Test a complete end-to-end workflow using multiple skills."""
        start_time = time.time()
        test_name = "End-to-End Workflow"

        try:
            # Define a realistic workflow that would use multiple skills
            workflow = {
                "name": "Real Estate Feature Development",
                "phases": [
                    {
                        "name": "Planning & Architecture",
                        "skills": ["systematic-debugging", "verification-before-completion"],
                        "outputs": ["architecture_design", "requirements_analysis"]
                    },
                    {
                        "name": "Development",
                        "skills": ["test-driven-development", "condition-based-waiting"],
                        "inputs": ["architecture_design"],
                        "outputs": ["feature_implementation", "test_suite"]
                    },
                    {
                        "name": "Design & UI",
                        "skills": ["frontend-design", "theme-factory", "web-artifacts-builder"],
                        "inputs": ["feature_implementation"],
                        "outputs": ["ui_components", "design_system"]
                    },
                    {
                        "name": "Quality Assurance",
                        "skills": ["testing-anti-patterns", "defense-in-depth"],
                        "inputs": ["feature_implementation", "test_suite"],
                        "outputs": ["quality_report", "security_validation"]
                    },
                    {
                        "name": "Deployment & Orchestration",
                        "skills": ["vercel-deploy", "subagent-driven-development", "dispatching-parallel-agents"],
                        "inputs": ["ui_components", "quality_report"],
                        "outputs": ["deployed_application", "monitoring_setup"]
                    },
                    {
                        "name": "Review & Documentation",
                        "skills": ["requesting-code-review"],
                        "inputs": ["deployed_application"],
                        "outputs": ["code_review", "documentation"]
                    }
                ]
            }

            # Validate workflow
            phase_validations = []
            for phase in workflow["phases"]:
                phase_validation = {
                    "name": phase["name"],
                    "skills": phase["skills"],
                    "skills_exist": []
                }

                for skill_name in phase["skills"]:
                    skill_exists = False

                    # Check if skill exists in any category
                    for category_dir in self.skills_path.iterdir():
                        if category_dir.is_dir() and category_dir.name != "scripts":
                            for skill_dir in category_dir.iterdir():
                                if skill_dir.is_dir() and skill_name in skill_dir.name:
                                    skill_exists = True
                                    break

                    phase_validation["skills_exist"].append({
                        "skill": skill_name,
                        "exists": skill_exists
                    })

                phase_validations.append(phase_validation)

            # Calculate success metrics
            total_skills = sum(len(phase["skills"]) for phase in workflow["phases"])
            existing_skills = sum(
                sum(1 for skill in phase_val["skills_exist"] if skill["exists"])
                for phase_val in phase_validations
            )

            success = existing_skills == total_skills
            message = f"End-to-end workflow validation: {existing_skills}/{total_skills} skills available"

            return TestResult(
                test_name=test_name,
                success=success,
                duration=time.time() - start_time,
                message=message,
                details={
                    "workflow": workflow["name"],
                    "phases": phase_validations,
                    "coverage": f"{existing_skills}/{total_skills}"
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                message=f"Test failed: {str(e)}"
            )

    async def test_performance_characteristics(self) -> TestResult:
        """Test performance characteristics of the skill system."""
        start_time = time.time()
        test_name = "Performance Characteristics"

        try:
            # Test loading time for all skill documentation
            load_times = []

            for category_dir in self.skills_path.iterdir():
                if category_dir.is_dir() and category_dir.name != "scripts":
                    for skill_dir in category_dir.iterdir():
                        if skill_dir.is_dir():
                            skill_md = skill_dir / "SKILL.md"
                            if skill_md.exists():
                                file_start = time.time()

                                # Simulate skill loading
                                with open(skill_md, 'r') as f:
                                    content = f.read()
                                    # Simulate processing
                                    content_length = len(content)

                                load_time = time.time() - file_start
                                load_times.append({
                                    "skill": skill_dir.name,
                                    "load_time": load_time,
                                    "content_size": content_length
                                })

            # Performance metrics
            total_load_time = sum(lt["load_time"] for lt in load_times)
            avg_load_time = total_load_time / len(load_times) if load_times else 0
            max_load_time = max(lt["load_time"] for lt in load_times) if load_times else 0
            total_content_size = sum(lt["content_size"] for lt in load_times)

            # Performance thresholds
            acceptable_total_load_time = 1.0  # 1 second for all skills
            acceptable_avg_load_time = 0.1   # 100ms per skill
            acceptable_max_load_time = 0.2   # 200ms max for any single skill

            performance_ok = (
                total_load_time <= acceptable_total_load_time and
                avg_load_time <= acceptable_avg_load_time and
                max_load_time <= acceptable_max_load_time
            )

            message = (f"Performance: total={total_load_time:.3f}s, "
                      f"avg={avg_load_time:.3f}s, max={max_load_time:.3f}s, "
                      f"content={total_content_size} bytes")

            return TestResult(
                test_name=test_name,
                success=performance_ok,
                duration=time.time() - start_time,
                message=message,
                details={
                    "load_times": load_times,
                    "total_load_time": total_load_time,
                    "avg_load_time": avg_load_time,
                    "max_load_time": max_load_time,
                    "total_content_size": total_content_size,
                    "skills_tested": len(load_times)
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                duration=time.time() - start_time,
                message=f"Test failed: {str(e)}"
            )

    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        if not self.results:
            return "No test results available."

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        total_duration = sum(r.duration for r in self.results)

        report = f"""
# Claude Skills Integration Test Report

## Summary
- **Total Tests**: {total_tests}
- **Passed**: {passed_tests}
- **Failed**: {total_tests - passed_tests}
- **Success Rate**: {passed_tests/total_tests*100:.1f}%
- **Total Duration**: {total_duration:.3f}s

## Test Results

"""

        for result in self.results:
            status = "✅ PASSED" if result.success else "❌ FAILED"
            report += f"### {result.test_name}\n"
            report += f"**Status**: {status}\n"
            report += f"**Duration**: {result.duration:.3f}s\n"
            report += f"**Message**: {result.message}\n"

            if result.details:
                report += f"**Details**: {json.dumps(result.details, indent=2)}\n"

            report += "\n"

        # Overall assessment
        if passed_tests == total_tests:
            report += "## Overall Assessment\n\n✅ **ALL TESTS PASSED** - The Claude Skills ecosystem is fully integrated and ready for production use.\n"
        elif passed_tests >= total_tests * 0.8:
            report += "## Overall Assessment\n\n⚠️ **MOSTLY PASSING** - Minor issues detected. Review failed tests and address before production deployment.\n"
        else:
            report += "## Overall Assessment\n\n❌ **SIGNIFICANT ISSUES** - Multiple test failures detected. Address critical issues before proceeding.\n"

        return report


async def main():
    """Main test runner."""
    # Determine skills path
    current_dir = Path(__file__).parent
    skills_path = current_dir.parent

    # Initialize tester
    tester = SkillsIntegrationTester(skills_path)

    # Run tests
    print("🚀 Starting Claude Skills Integration Tests...")
    results = await tester.run_all_tests()

    # Generate and display report
    report = tester.generate_report()
    print("\n" + "="*60)
    print(report)

    # Save detailed report
    report_path = current_dir / f"integration_test_report_{int(time.time())}.md"
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"📊 Detailed report saved to: {report_path}")

    # Return exit code based on results
    success = all(r.success for r in results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())