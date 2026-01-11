#!/usr/bin/env python3
"""
Simple Claude Voice Integration Validation Script

This script validates the core Claude services without complex dependencies.
"""

import asyncio
import sys
import time
from pathlib import Path
import logging

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeValidationTest:
    """Simple validation tests for Claude services"""

    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = {}

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"    Details: {details}")

        self.test_results[test_name] = {
            "passed": passed,
            "details": details
        }

        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    async def test_import_core_services(self):
        """Test importing core Claude services"""
        try:
            # Test claude_semantic_analyzer
            from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
            self.log_test("Import ClaudeSemanticAnalyzer", True, "Successfully imported")
        except Exception as e:
            self.log_test("Import ClaudeSemanticAnalyzer", False, f"Import failed: {e}")

        try:
            # Test qualification_orchestrator
            from ghl_real_estate_ai.services.qualification_orchestrator import QualificationOrchestrator
            self.log_test("Import QualificationOrchestrator", True, "Successfully imported")
        except Exception as e:
            self.log_test("Import QualificationOrchestrator", False, f"Import failed: {e}")

        try:
            # Test claude_action_planner
            from ghl_real_estate_ai.services.claude_action_planner import ClaudeActionPlanner
            self.log_test("Import ClaudeActionPlanner", True, "Successfully imported")
        except Exception as e:
            self.log_test("Import ClaudeActionPlanner", False, f"Import failed: {e}")

    async def test_service_instantiation(self):
        """Test basic service instantiation"""
        try:
            from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
            analyzer = ClaudeSemanticAnalyzer()
            self.log_test("Instantiate ClaudeSemanticAnalyzer", True, "Service created successfully")
        except Exception as e:
            self.log_test("Instantiate ClaudeSemanticAnalyzer", False, f"Instantiation failed: {e}")

        try:
            from ghl_real_estate_ai.services.claude_action_planner import ClaudeActionPlanner
            planner = ClaudeActionPlanner()
            self.log_test("Instantiate ClaudeActionPlanner", True, "Service created successfully")
        except Exception as e:
            self.log_test("Instantiate ClaudeActionPlanner", False, f"Instantiation failed: {e}")

    async def test_basic_functionality(self):
        """Test basic functionality without external dependencies"""
        try:
            from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
            analyzer = ClaudeSemanticAnalyzer()

            # Test basic method existence
            if hasattr(analyzer, 'analyze_lead_intent'):
                self.log_test("ClaudeSemanticAnalyzer.analyze_lead_intent method", True, "Method exists")
            else:
                self.log_test("ClaudeSemanticAnalyzer.analyze_lead_intent method", False, "Method missing")

            if hasattr(analyzer, 'extract_semantic_preferences'):
                self.log_test("ClaudeSemanticAnalyzer.extract_semantic_preferences method", True, "Method exists")
            else:
                self.log_test("ClaudeSemanticAnalyzer.extract_semantic_preferences method", False, "Method missing")
        except Exception as e:
            self.log_test("ClaudeSemanticAnalyzer basic functionality", False, f"Error: {e}")

    async def test_performance_timing(self):
        """Test basic performance timing"""
        try:
            # Test import timing
            start_time = time.time()
            from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
            import_time = (time.time() - start_time) * 1000  # Convert to ms

            if import_time < 1000:  # Less than 1 second
                self.log_test("Import timing performance", True, f"Import took {import_time:.2f}ms")
            else:
                self.log_test("Import timing performance", False, f"Import took {import_time:.2f}ms (too slow)")

            # Test instantiation timing
            start_time = time.time()
            analyzer = ClaudeSemanticAnalyzer()
            instantiation_time = (time.time() - start_time) * 1000

            if instantiation_time < 500:  # Less than 500ms
                self.log_test("Instantiation timing", True, f"Instantiation took {instantiation_time:.2f}ms")
            else:
                self.log_test("Instantiation timing", False, f"Instantiation took {instantiation_time:.2f}ms (too slow)")

        except Exception as e:
            self.log_test("Performance timing test", False, f"Error: {e}")

    async def test_config_structure(self):
        """Test configuration structure"""
        try:
            config_files = [
                "ghl_real_estate_ai/config/__init__.py",
                "ghl_real_estate_ai/config/settings.py"
            ]

            for config_file in config_files:
                config_path = project_root / config_file
                if config_path.exists():
                    self.log_test(f"Config file exists: {config_file}", True, "File found")
                else:
                    self.log_test(f"Config file exists: {config_file}", False, "File missing")
        except Exception as e:
            self.log_test("Configuration structure test", False, f"Error: {e}")

    async def run_all_tests(self):
        """Run all validation tests"""
        logger.info("🚀 Starting Claude Voice Integration Validation")
        logger.info("=" * 60)

        await self.test_config_structure()
        await self.test_import_core_services()
        await self.test_service_instantiation()
        await self.test_basic_functionality()
        await self.test_performance_timing()

        logger.info("=" * 60)
        logger.info("📊 Test Results Summary:")
        logger.info(f"✅ Passed: {self.passed_tests}")
        logger.info(f"❌ Failed: {self.failed_tests}")
        logger.info(f"📈 Success Rate: {(self.passed_tests / (self.passed_tests + self.failed_tests)) * 100:.1f}%")

        if self.failed_tests == 0:
            logger.info("🎉 All tests passed! Claude Voice Integration validation successful.")
            return True
        else:
            logger.info("⚠️ Some tests failed. Check the issues above.")
            return False

    def get_validation_report(self):
        """Get detailed validation report"""
        return {
            "total_tests": self.passed_tests + self.failed_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": (self.passed_tests / (self.passed_tests + self.failed_tests)) * 100,
            "test_details": self.test_results
        }


async def main():
    """Main validation function"""
    validator = ClaudeValidationTest()
    success = await validator.run_all_tests()

    # Generate report
    report = validator.get_validation_report()

    logger.info("\n📋 Detailed Validation Report:")
    for test_name, result in report["test_details"].items():
        status = "✅" if result["passed"] else "❌"
        logger.info(f"  {status} {test_name}: {result['details']}")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)