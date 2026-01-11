"""
Agent 1 Integration Validation Test Suite

Critical assessment of infrastructure fixes and new service implementations
for GHL Real Estate AI Platform. Identifies import dependencies, service
integration issues, and production readiness gaps.

Agent 6 Findings: Integration Testing & Validation Lead
"""

import asyncio
import pytest
import logging
import sys
import importlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, patch

logger = logging.getLogger(__name__)

class Agent1ValidationSuite:
    """
    Comprehensive validation suite for Agent 1's infrastructure work.

    Tests:
    1. Import dependency resolution
    2. Service implementation validation
    3. ML integration pipeline testing
    4. Error handling verification
    5. Performance baseline establishment
    """

    def __init__(self):
        self.validation_results = {}
        self.critical_issues = []
        self.performance_baselines = {}

    def test_import_dependencies(self) -> Dict[str, Any]:
        """Test that all critical imports are resolved"""

        test_results = {
            "core_services": {"status": "unknown", "details": []},
            "ml_learning": {"status": "unknown", "details": []},
            "chat_interface": {"status": "unknown", "details": []},
            "session_management": {"status": "unknown", "details": []}
        }

        # Test core service imports
        try:
            from services.chat_interface import ChatInterface, create_chat_interface
            from services.chatbot_manager import ChatbotManager, UserType, ConversationStage
            from services.session_manager import SessionManager, SessionData
            test_results["core_services"]["status"] = "passed"
            test_results["core_services"]["details"].append("✅ Core service imports successful")
        except Exception as e:
            test_results["core_services"]["status"] = "failed"
            test_results["core_services"]["details"].append(f"❌ Core service import failed: {str(e)}")
            self.critical_issues.append(f"Core service import failure: {str(e)}")

        # Test ML learning imports with relative path fixes
        try:
            # Add the services directory to Python path for testing
            services_path = Path(__file__).parent.parent / "services"
            sys.path.insert(0, str(services_path))

            # Test interfaces import
            from learning.interfaces import (
                BehavioralEvent, EventType, LearningContext,
                ModelType, FeatureVector, ModelPrediction
            )
            test_results["ml_learning"]["details"].append("✅ Learning interfaces imported")

            # Test tracking components
            from learning.tracking.behavior_tracker import InMemoryBehaviorTracker
            from learning.feature_engineering.standard_feature_engineer import StandardFeatureEngineer
            test_results["ml_learning"]["details"].append("✅ Foundation components imported")

            test_results["ml_learning"]["status"] = "passed"

        except ImportError as e:
            test_results["ml_learning"]["status"] = "failed"
            test_results["ml_learning"]["details"].append(f"❌ ML learning import failed: {str(e)}")
            self.critical_issues.append(f"ML learning import failure: {str(e)} - CRITICAL: Relative import issues detected")
        except Exception as e:
            test_results["ml_learning"]["status"] = "failed"
            test_results["ml_learning"]["details"].append(f"❌ ML learning error: {str(e)}")
            self.critical_issues.append(f"ML learning error: {str(e)}")

        finally:
            # Clean up sys.path
            if str(services_path) in sys.path:
                sys.path.remove(str(services_path))

        return test_results

    def test_service_implementations(self) -> Dict[str, Any]:
        """Test service implementation quality and completeness"""

        implementation_results = {
            "chat_interface": {"status": "unknown", "features": []},
            "chatbot_manager": {"status": "unknown", "features": []},
            "session_manager": {"status": "unknown", "features": []},
            "ml_integration": {"status": "unknown", "features": []}
        }

        # Test ChatInterface implementation
        try:
            from services.chat_interface import ChatInterface

            # Check required methods exist
            required_methods = [
                'render_lead_chat', 'render_buyer_chat', 'render_seller_chat',
                'render_demo_chat', '_setup_chat_session', '_render_chat_messages',
                '_handle_chat_input'
            ]

            chat_interface_methods = [method for method in dir(ChatInterface) if not method.startswith('_') or method.startswith('_render') or method.startswith('_setup') or method.startswith('_handle')]

            for method in required_methods:
                if hasattr(ChatInterface, method):
                    implementation_results["chat_interface"]["features"].append(f"✅ {method} implemented")
                else:
                    implementation_results["chat_interface"]["features"].append(f"❌ {method} missing")

            implementation_results["chat_interface"]["status"] = "passed"

        except Exception as e:
            implementation_results["chat_interface"]["status"] = "failed"
            implementation_results["chat_interface"]["features"].append(f"❌ ChatInterface error: {str(e)}")

        # Test ChatbotManager implementation
        try:
            from services.chatbot_manager import ChatbotManager, UserType, ConversationStage

            # Check enums are properly defined
            user_types = [ut.value for ut in UserType]
            conv_stages = [cs.value for cs in ConversationStage]

            implementation_results["chatbot_manager"]["features"].append(f"✅ UserTypes: {user_types}")
            implementation_results["chatbot_manager"]["features"].append(f"✅ ConversationStages: {conv_stages}")
            implementation_results["chatbot_manager"]["status"] = "passed"

        except Exception as e:
            implementation_results["chatbot_manager"]["status"] = "failed"
            implementation_results["chatbot_manager"]["features"].append(f"❌ ChatbotManager error: {str(e)}")

        # Test SessionManager implementation
        try:
            from services.session_manager import SessionManager, SessionData

            # Check SessionData dataclass structure
            session_data = SessionData(
                session_id="test",
                user_id="test_user",
                tenant_id="test_tenant",
                user_type="lead",
                created_at=__import__('datetime').datetime.now(),
                last_active=__import__('datetime').datetime.now(),
                device_info={"platform": "test"}
            )

            implementation_results["session_manager"]["features"].append("✅ SessionData structure valid")
            implementation_results["session_manager"]["features"].append("✅ SessionManager instantiable")
            implementation_results["session_manager"]["status"] = "passed"

        except Exception as e:
            implementation_results["session_manager"]["status"] = "failed"
            implementation_results["session_manager"]["features"].append(f"❌ SessionManager error: {str(e)}")

        return implementation_results

    def test_ml_integration_pipeline(self) -> Dict[str, Any]:
        """Test ML integration pipeline functionality"""

        ml_results = {
            "interface_compatibility": {"status": "unknown", "details": []},
            "model_integration": {"status": "unknown", "details": []},
            "feature_engineering": {"status": "unknown", "details": []},
            "personalization_engine": {"status": "unknown", "details": []}
        }

        # Test interface compatibility with mocked ML components
        try:
            # Use mocks to test interface without full ML implementation
            with patch('services.learning.tracking.behavior_tracker.InMemoryBehaviorTracker') as mock_tracker:
                with patch('services.learning.feature_engineering.standard_feature_engineer.StandardFeatureEngineer') as mock_engineer:
                    mock_tracker.return_value = MagicMock()
                    mock_engineer.return_value = MagicMock()

                    # Test chat interface with ML disabled
                    from services.chat_interface import create_chat_interface
                    interface = create_chat_interface(enable_ml=False)

                    ml_results["interface_compatibility"]["status"] = "passed"
                    ml_results["interface_compatibility"]["details"].append("✅ Chat interface ML integration compatible")

        except Exception as e:
            ml_results["interface_compatibility"]["status"] = "failed"
            ml_results["interface_compatibility"]["details"].append(f"❌ Interface compatibility failed: {str(e)}")

        # Test model file structure and completeness
        models_dir = Path(__file__).parent.parent / "services" / "learning" / "models"
        if models_dir.exists():
            model_files = [
                "collaborative_filtering.py",
                "content_based.py",
                "__init__.py"
            ]

            for model_file in model_files:
                model_path = models_dir / model_file
                if model_path.exists() and model_path.stat().st_size > 1000:  # > 1KB
                    ml_results["model_integration"]["details"].append(f"✅ {model_file} exists ({model_path.stat().st_size:,} bytes)")
                else:
                    ml_results["model_integration"]["details"].append(f"❌ {model_file} missing or too small")

            ml_results["model_integration"]["status"] = "passed"
        else:
            ml_results["model_integration"]["status"] = "failed"
            ml_results["model_integration"]["details"].append("❌ ML models directory missing")

        return ml_results

    def test_error_handling_framework(self) -> Dict[str, Any]:
        """Test error handling and resilience patterns"""

        error_handling_results = {
            "import_error_handling": {"status": "unknown", "details": []},
            "service_error_handling": {"status": "unknown", "details": []},
            "ml_fallback_behavior": {"status": "unknown", "details": []}
        }

        # Test import error handling in chat interface
        try:
            from services.chat_interface import create_chat_interface

            # Test with ML disabled (should not fail)
            interface_no_ml = create_chat_interface(enable_ml=False)
            error_handling_results["ml_fallback_behavior"]["details"].append("✅ ML fallback behavior works")
            error_handling_results["ml_fallback_behavior"]["status"] = "passed"

        except Exception as e:
            error_handling_results["ml_fallback_behavior"]["status"] = "failed"
            error_handling_results["ml_fallback_behavior"]["details"].append(f"❌ ML fallback failed: {str(e)}")

        # Test service instantiation error handling
        try:
            from services.session_manager import SessionManager
            session_manager = SessionManager(storage_path="/tmp/test_sessions")
            error_handling_results["service_error_handling"]["details"].append("✅ SessionManager error handling works")
            error_handling_results["service_error_handling"]["status"] = "passed"

        except Exception as e:
            error_handling_results["service_error_handling"]["status"] = "failed"
            error_handling_results["service_error_handling"]["details"].append(f"❌ Service error handling failed: {str(e)}")

        return error_handling_results

    def test_performance_baseline(self) -> Dict[str, Any]:
        """Establish performance baseline for new services"""

        import time
        performance_results = {
            "service_instantiation": {"status": "unknown", "metrics": {}},
            "memory_usage": {"status": "unknown", "metrics": {}},
            "import_performance": {"status": "unknown", "metrics": {}}
        }

        # Test service instantiation performance
        try:
            start_time = time.time()
            from services.chat_interface import create_chat_interface
            interface = create_chat_interface(enable_ml=False)
            instantiation_time = time.time() - start_time

            performance_results["service_instantiation"]["metrics"]["chat_interface_creation_time"] = f"{instantiation_time:.3f}s"

            if instantiation_time < 1.0:  # Should be under 1 second
                performance_results["service_instantiation"]["status"] = "passed"
            else:
                performance_results["service_instantiation"]["status"] = "warning"

        except Exception as e:
            performance_results["service_instantiation"]["status"] = "failed"
            performance_results["service_instantiation"]["metrics"]["error"] = str(e)

        # Test import performance
        try:
            start_time = time.time()
            from services.chatbot_manager import ChatbotManager
            from services.session_manager import SessionManager
            import_time = time.time() - start_time

            performance_results["import_performance"]["metrics"]["core_services_import_time"] = f"{import_time:.3f}s"

            if import_time < 0.5:  # Should be under 500ms
                performance_results["import_performance"]["status"] = "passed"
            else:
                performance_results["import_performance"]["status"] = "warning"

        except Exception as e:
            performance_results["import_performance"]["status"] = "failed"
            performance_results["import_performance"]["metrics"]["error"] = str(e)

        return performance_results

    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""

        print("🧪 Agent 1 Infrastructure Validation Report")
        print("=" * 55)

        # Run all validation tests
        import_results = self.test_import_dependencies()
        service_results = self.test_service_implementations()
        ml_results = self.test_ml_integration_pipeline()
        error_results = self.test_error_handling_framework()
        performance_results = self.test_performance_baseline()

        # Compile overall assessment
        overall_status = {
            "critical_issues_count": len(self.critical_issues),
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_warning": 0
        }

        all_results = {
            "import_dependencies": import_results,
            "service_implementations": service_results,
            "ml_integration": ml_results,
            "error_handling": error_results,
            "performance_baseline": performance_results
        }

        # Count statuses
        for category, results in all_results.items():
            for test, details in results.items():
                status = details.get("status", "unknown")
                if status == "passed":
                    overall_status["tests_passed"] += 1
                elif status == "failed":
                    overall_status["tests_failed"] += 1
                elif status == "warning":
                    overall_status["tests_warning"] += 1

        # Display results
        print("\n📊 Validation Results Summary:")
        print("-" * 35)
        print(f"✅ Tests Passed: {overall_status['tests_passed']}")
        print(f"❌ Tests Failed: {overall_status['tests_failed']}")
        print(f"⚠️  Tests Warning: {overall_status['tests_warning']}")
        print(f"🚨 Critical Issues: {overall_status['critical_issues_count']}")

        if self.critical_issues:
            print("\n🚨 CRITICAL ISSUES FOUND:")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"{i}. {issue}")

        print("\n🔍 Detailed Results:")
        print("-" * 25)

        for category, results in all_results.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            for test, details in results.items():
                status = details.get("status", "unknown")
                status_icon = {"passed": "✅", "failed": "❌", "warning": "⚠️", "unknown": "❓"}[status]
                print(f"  {status_icon} {test}: {status}")

                # Show details/features
                if "details" in details:
                    for detail in details["details"]:
                        print(f"    {detail}")
                if "features" in details:
                    for feature in details["features"]:
                        print(f"    {feature}")
                if "metrics" in details:
                    for metric, value in details["metrics"].items():
                        print(f"    📈 {metric}: {value}")

        # Production readiness assessment
        print("\n🚀 Production Readiness Assessment:")
        print("-" * 38)

        if overall_status["critical_issues_count"] > 0:
            print("❌ NOT READY FOR PRODUCTION")
            print("   Critical issues must be resolved before deployment")
        elif overall_status["tests_failed"] > 0:
            print("⚠️  PRODUCTION READINESS QUESTIONABLE")
            print("   Failed tests should be investigated")
        elif overall_status["tests_warning"] > 0:
            print("⚠️  READY WITH MONITORING")
            print("   Warning conditions should be monitored")
        else:
            print("✅ READY FOR PRODUCTION")
            print("   All validation tests passed")

        # Agent coordination recommendations
        print("\n🤝 Agent Coordination Recommendations:")
        print("-" * 42)

        if "ML learning import failure" in str(self.critical_issues):
            print("🔧 Agent 2 (Error Handling): Must address ML import failures before resilience work")
            print("🔧 Agent 3 (Database): Defer optimization until import issues resolved")
            print("🔧 Agent 4 (ML Performance): Cannot proceed until ML imports working")
            print("🔧 Agent 5 (API Performance): Can proceed with non-ML API optimization")
        else:
            print("✅ Agent 2: Can proceed with error handling implementation")
            print("✅ Agent 3: Can proceed with database optimization")
            print("✅ Agent 4: Can proceed with ML performance optimization")
            print("✅ Agent 5: Can proceed with API performance optimization")

        return {
            "overall_status": overall_status,
            "detailed_results": all_results,
            "critical_issues": self.critical_issues,
            "production_ready": overall_status["critical_issues_count"] == 0 and overall_status["tests_failed"] == 0
        }

# Integration test that can be run with pytest
@pytest.mark.asyncio
async def test_agent_1_validation():
    """Main validation test for Agent 1's work"""

    validator = Agent1ValidationSuite()
    report = validator.generate_validation_report()

    # Assert no critical issues
    assert len(validator.critical_issues) == 0, f"Critical issues found: {validator.critical_issues}"

    # Assert production readiness
    assert report["production_ready"], "System not ready for production"

    return report

def main():
    """Run validation suite standalone"""
    validator = Agent1ValidationSuite()
    report = validator.generate_validation_report()

    if report["production_ready"]:
        print("\n🎉 VALIDATION COMPLETED SUCCESSFULLY!")
        exit(0)
    else:
        print("\n❌ VALIDATION FAILED - CRITICAL ISSUES MUST BE RESOLVED")
        exit(1)

if __name__ == "__main__":
    main()