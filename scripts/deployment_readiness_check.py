#!/usr/bin/env python3
"""
Enhanced ML Deployment Readiness Check
Validates system readiness for production deployment.
"""

import sys
import importlib
from pathlib import Path
import json
from typing import Dict, List, Any
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeploymentReadinessChecker:
    """Comprehensive deployment readiness validation."""

    def __init__(self):
        self.checks = []
        self.critical_services = [
            'services.enhanced_ml_personalization_engine',
            'services.predictive_churn_prevention',
            'services.real_time_model_training',
            'services.multimodal_communication_optimizer'
        ]

    def check_service_imports(self) -> Dict[str, Any]:
        """Verify all Enhanced ML services can be imported."""
        logger.info("🔍 Checking service imports...")

        import_results = {
            "all_imports_successful": True,
            "services_status": {},
            "total_services": len(self.critical_services)
        }

        for service_module in self.critical_services:
            try:
                module = importlib.import_module(service_module)
                service_name = service_module.split('.')[-1]

                # Get main class
                main_classes = [
                    'EnhancedMLPersonalizationEngine',
                    'PredictiveChurnPrevention',
                    'RealTimeModelTraining',
                    'MultiModalCommunicationOptimizer'
                ]

                class_found = False
                for class_name in main_classes:
                    if hasattr(module, class_name):
                        main_class = getattr(module, class_name)
                        class_found = True
                        break

                import_results["services_status"][service_name] = {
                    "import_successful": True,
                    "main_class_found": class_found,
                    "ready_for_deployment": class_found
                }

                logger.info(f"✅ {service_name}: Import successful")

            except Exception as e:
                import_results["all_imports_successful"] = False
                import_results["services_status"][service_module] = {
                    "import_successful": False,
                    "error": str(e),
                    "ready_for_deployment": False
                }
                logger.error(f"❌ {service_module}: Import failed - {e}")

        return import_results

    def check_documentation_completeness(self) -> Dict[str, Any]:
        """Verify documentation is complete."""
        logger.info("📚 Checking documentation completeness...")

        required_docs = [
            'docs/ENHANCED_ML_SYSTEM_DOCUMENTATION.md',
            'SESSION_HANDOFF_2026-01-09_ENHANCED_ML_COMPLETE.md'
        ]

        doc_results = {
            "all_docs_present": True,
            "docs_status": {},
            "total_docs_required": len(required_docs)
        }

        for doc_path in required_docs:
            doc_file = Path(doc_path)
            exists = doc_file.exists()

            if exists:
                size_kb = doc_file.stat().st_size / 1024
                doc_results["docs_status"][doc_path] = {
                    "exists": True,
                    "size_kb": round(size_kb, 1),
                    "ready": size_kb > 10  # At least 10KB
                }
                logger.info(f"✅ {doc_path}: {size_kb:.1f}KB")
            else:
                doc_results["all_docs_present"] = False
                doc_results["docs_status"][doc_path] = {
                    "exists": False,
                    "ready": False
                }
                logger.error(f"❌ {doc_path}: Missing")

        return doc_results

    def check_performance_validation(self) -> Dict[str, Any]:
        """Verify performance benchmarks meet targets."""
        logger.info("⚡ Checking performance validation...")

        perf_results = {
            "benchmarks_completed": False,
            "grade_achieved": None,
            "targets_met_percentage": 0,
            "ready_for_production": False
        }

        # Check for performance report
        perf_report_path = Path('scripts/enhanced_ml_performance_report.json')
        if perf_report_path.exists():
            try:
                with open(perf_report_path, 'r') as f:
                    perf_data = json.load(f)

                summary = perf_data.get('performance_summary', {})
                perf_results.update({
                    "benchmarks_completed": True,
                    "grade_achieved": summary.get('performance_grade', 'Unknown'),
                    "targets_met_percentage": summary.get('target_achievement_rate', 0),
                    "ready_for_production": summary.get('target_achievement_rate', 0) >= 80
                })

                logger.info(f"✅ Performance Grade: {perf_results['grade_achieved']}")
                logger.info(f"✅ Targets Met: {perf_results['targets_met_percentage']}%")

            except Exception as e:
                logger.error(f"❌ Error reading performance report: {e}")
        else:
            logger.error("❌ Performance report not found")

        return perf_results

    def check_validation_reports(self) -> Dict[str, Any]:
        """Check architecture validation results."""
        logger.info("🏗️ Checking architecture validation...")

        validation_results = {
            "validation_completed": False,
            "architecture_score": 0,
            "integration_validated": False,
            "ready_for_deployment": False
        }

        # Check for validation report
        validation_report_path = Path('scripts/enhanced_ml_validation_report.json')
        if validation_report_path.exists():
            try:
                with open(validation_report_path, 'r') as f:
                    validation_data = json.load(f)

                summary = validation_data.get('validation_summary', {})
                validation_results.update({
                    "validation_completed": True,
                    "architecture_score": summary.get('overall_score', 0),
                    "grade": summary.get('grade', 'Unknown'),
                    "integration_validated": summary.get('successful_imports', 0) >= 4,
                    "ready_for_deployment": summary.get('overall_score', 0) >= 80
                })

                logger.info(f"✅ Architecture Score: {validation_results['architecture_score']}/100")
                logger.info(f"✅ Architecture Grade: {validation_results['grade']}")

            except Exception as e:
                logger.error(f"❌ Error reading validation report: {e}")
        else:
            logger.error("❌ Validation report not found")

        return validation_results

    def generate_deployment_status(self) -> Dict[str, Any]:
        """Generate comprehensive deployment readiness status."""
        logger.info("🚀 Generating deployment readiness report...")

        # Run all checks
        import_check = self.check_service_imports()
        doc_check = self.check_documentation_completeness()
        perf_check = self.check_performance_validation()
        validation_check = self.check_validation_reports()

        # Calculate overall readiness score
        checks = [
            import_check.get("all_imports_successful", False),
            doc_check.get("all_docs_present", False),
            perf_check.get("ready_for_production", False),
            validation_check.get("ready_for_deployment", False)
        ]

        readiness_score = (sum(checks) / len(checks)) * 100

        deployment_status = {
            "overall_readiness_score": round(readiness_score, 1),
            "ready_for_deployment": readiness_score >= 75,
            "deployment_grade": self._calculate_deployment_grade(readiness_score),
            "checks": {
                "service_imports": import_check,
                "documentation": doc_check,
                "performance": perf_check,
                "validation": validation_check
            },
            "deployment_recommendations": self._generate_deployment_recommendations(checks),
            "next_steps": self._generate_next_steps(readiness_score)
        }

        return deployment_status

    def _calculate_deployment_grade(self, score: float) -> str:
        """Calculate deployment readiness grade."""
        if score >= 95: return "A+"
        elif score >= 90: return "A"
        elif score >= 85: return "A-"
        elif score >= 80: return "B+"
        elif score >= 75: return "B"
        else: return "C"

    def _generate_deployment_recommendations(self, checks: List[bool]) -> List[str]:
        """Generate deployment recommendations based on check results."""
        recommendations = []

        if all(checks):
            recommendations.append("✅ System ready for immediate production deployment")
            recommendations.append("🚀 Consider staged rollout with monitoring")
            recommendations.append("📊 Set up production performance dashboards")
        else:
            if not checks[0]:
                recommendations.append("⚠️ Fix service import issues before deployment")
            if not checks[1]:
                recommendations.append("⚠️ Complete missing documentation")
            if not checks[2]:
                recommendations.append("⚠️ Address performance benchmark failures")
            if not checks[3]:
                recommendations.append("⚠️ Resolve architecture validation issues")

        return recommendations

    def _generate_next_steps(self, readiness_score: float) -> List[str]:
        """Generate immediate next steps based on readiness."""
        next_steps = []

        if readiness_score >= 90:
            next_steps.extend([
                "Deploy to staging environment for final validation",
                "Run load testing with production-scale data",
                "Set up monitoring and alerting systems",
                "Schedule production deployment window",
                "Prepare rollback procedures"
            ])
        elif readiness_score >= 75:
            next_steps.extend([
                "Address remaining readiness issues",
                "Complete final validation testing",
                "Update deployment documentation",
                "Schedule staging deployment"
            ])
        else:
            next_steps.extend([
                "Complete all failing readiness checks",
                "Re-run validation testing",
                "Review and update documentation",
                "Schedule readiness re-assessment"
            ])

        return next_steps

def main():
    """Execute deployment readiness check."""
    print("🔧 Enhanced ML Deployment Readiness Check")
    print("=" * 50)

    checker = DeploymentReadinessChecker()
    status = checker.generate_deployment_status()

    # Print results
    print(f"\n📊 Overall Readiness Score: {status['overall_readiness_score']}%")
    print(f"🎯 Deployment Grade: {status['deployment_grade']}")
    print(f"🚀 Ready for Deployment: {'Yes' if status['ready_for_deployment'] else 'No'}")

    print(f"\n🔍 Check Results:")
    checks = status['checks']
    for check_name, check_data in checks.items():
        if check_name == 'service_imports':
            status_icon = "✅" if check_data.get('all_imports_successful') else "❌"
            print(f"{status_icon} Service Imports: {check_data.get('total_services', 0)} services")
        elif check_name == 'documentation':
            status_icon = "✅" if check_data.get('all_docs_present') else "❌"
            print(f"{status_icon} Documentation: {check_data.get('total_docs_required', 0)} docs required")
        elif check_name == 'performance':
            status_icon = "✅" if check_data.get('ready_for_production') else "❌"
            grade = check_data.get('grade_achieved', 'Unknown')
            print(f"{status_icon} Performance: Grade {grade}")
        elif check_name == 'validation':
            status_icon = "✅" if check_data.get('ready_for_deployment') else "❌"
            score = check_data.get('architecture_score', 0)
            print(f"{status_icon} Architecture: {score}/100")

    print(f"\n💡 Recommendations:")
    for rec in status['deployment_recommendations']:
        print(f"• {rec}")

    print(f"\n🎯 Immediate Next Steps:")
    for step in status['next_steps']:
        print(f"• {step}")

    # Save report
    report_file = Path('scripts/deployment_readiness_report.json')
    with open(report_file, 'w') as f:
        json.dump(status, f, indent=2, default=str)

    print(f"\n📄 Full report saved to: {report_file}")

    return status['ready_for_deployment']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)