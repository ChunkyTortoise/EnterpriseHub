#!/usr/bin/env python3
"""
Enhanced ML Interface Validation
Validates service interfaces, data models, and architecture without requiring ML dependencies.
"""

import sys
import time
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any
import json
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServiceInterfaceValidator:
    """Validates Enhanced ML service interfaces and architecture."""

    def __init__(self):
        self.results = []
        self.services_to_validate = [
            {
                "module": "services.enhanced_ml_personalization_engine",
                "class": "EnhancedMLPersonalizationEngine",
                "expected_methods": ["initialize", "generate_personalized_experience"],
                "data_models": ["AdvancedPersonalizationOutput", "EmotionalState", "LeadJourneyStage"]
            },
            {
                "module": "services.predictive_churn_prevention",
                "class": "PredictiveChurnPrevention",
                "expected_methods": ["initialize", "assess_churn_risk"],
                "data_models": ["ChurnRiskAssessment", "ChurnRiskLevel", "InterventionType"]
            },
            {
                "module": "services.real_time_model_training",
                "class": "RealTimeModelTraining",
                "expected_methods": ["initialize", "update_model", "detect_drift"],
                "data_models": ["ModelPerformanceSnapshot", "ModelType", "DriftType"]
            },
            {
                "module": "services.multimodal_communication_optimizer",
                "class": "MultiModalCommunicationOptimizer",
                "expected_methods": ["initialize", "optimize_communication"],
                "data_models": ["OptimizedCommunication", "CommunicationModality"]
            }
        ]

    def validate_imports_and_structure(self) -> Dict[str, Any]:
        """Validate that all services can be imported and have correct structure."""
        logger.info("🔍 Validating Enhanced ML service imports and structure...")

        validation_results = {
            "total_services": len(self.services_to_validate),
            "successful_imports": 0,
            "services": {},
            "shared_models_validated": False,
            "architecture_score": 0
        }

        # First validate shared models
        try:
            from models.shared_models import LeadProfile
            logger.info("✅ Shared models imported successfully")
            validation_results["shared_models_validated"] = True
        except Exception as e:
            logger.error(f"❌ Shared models import failed: {e}")
            validation_results["shared_models_validated"] = False

        # Validate each service
        for service_config in self.services_to_validate:
            service_name = service_config["class"]
            service_results = {
                "import_successful": False,
                "class_exists": False,
                "methods_validated": 0,
                "expected_methods": len(service_config["expected_methods"]),
                "data_models_validated": 0,
                "expected_data_models": len(service_config["data_models"]),
                "interface_score": 0,
                "errors": []
            }

            try:
                # Import the module
                module = importlib.import_module(service_config["module"])
                service_results["import_successful"] = True
                logger.info(f"✅ {service_name} module imported")

                # Check if class exists
                if hasattr(module, service_config["class"]):
                    service_class = getattr(module, service_config["class"])
                    service_results["class_exists"] = True
                    logger.info(f"✅ {service_name} class found")

                    # Validate methods
                    for method_name in service_config["expected_methods"]:
                        if hasattr(service_class, method_name):
                            method = getattr(service_class, method_name)
                            if callable(method):
                                service_results["methods_validated"] += 1
                                logger.info(f"✅ {service_name}.{method_name}() method validated")
                            else:
                                service_results["errors"].append(f"{method_name} is not callable")
                        else:
                            service_results["errors"].append(f"Missing method: {method_name}")

                    # Validate data models
                    for data_model in service_config["data_models"]:
                        if hasattr(module, data_model):
                            model_class = getattr(module, data_model)
                            service_results["data_models_validated"] += 1
                            logger.info(f"✅ {data_model} data model found")
                        else:
                            service_results["errors"].append(f"Missing data model: {data_model}")

                else:
                    service_results["errors"].append(f"Class {service_config['class']} not found")

            except Exception as e:
                service_results["errors"].append(f"Import failed: {str(e)}")
                logger.error(f"❌ {service_name} validation failed: {e}")

            # Calculate interface score
            method_score = (service_results["methods_validated"] / service_results["expected_methods"]) * 50
            model_score = (service_results["data_models_validated"] / service_results["expected_data_models"]) * 30
            class_score = 20 if service_results["class_exists"] else 0
            service_results["interface_score"] = round(method_score + model_score + class_score, 2)

            if service_results["import_successful"]:
                validation_results["successful_imports"] += 1

            validation_results["services"][service_name] = service_results

        # Calculate overall architecture score
        import_score = (validation_results["successful_imports"] / validation_results["total_services"]) * 40
        shared_models_score = 20 if validation_results["shared_models_validated"] else 0
        avg_interface_score = sum(
            service["interface_score"] for service in validation_results["services"].values()
        ) / len(validation_results["services"]) * 0.4

        validation_results["architecture_score"] = round(import_score + shared_models_score + avg_interface_score, 2)

        return validation_results

    def validate_data_flow_consistency(self) -> Dict[str, Any]:
        """Validate data flow consistency between services."""
        logger.info("🔄 Validating data flow consistency...")

        data_flow_results = {
            "lead_profile_compatibility": False,
            "enum_consistency": False,
            "memory_optimization": False,
            "type_safety": False,
            "consistency_score": 0
        }

        try:
            from models.shared_models import LeadProfile, CommunicationChannel, InteractionType, LeadSource

            # Test LeadProfile creation
            test_profile = LeadProfile(
                lead_id="test_001",
                name="Test User",
                email="test@example.com"
            )
            data_flow_results["lead_profile_compatibility"] = True
            logger.info("✅ LeadProfile data flow validated")

            # Test enum consistency
            channels = list(CommunicationChannel)
            interactions = list(InteractionType)
            sources = list(LeadSource)

            if len(channels) >= 5 and len(interactions) >= 10 and len(sources) >= 5:
                data_flow_results["enum_consistency"] = True
                logger.info("✅ Enum consistency validated")

            # Test memory optimization (check for float32 usage)
            import numpy as np
            if hasattr(test_profile, 'engagement_score'):
                if isinstance(test_profile.engagement_score, np.float32):
                    data_flow_results["memory_optimization"] = True
                    logger.info("✅ Memory optimization with float32 validated")

            # Test type safety (dataclass with slots)
            if hasattr(LeadProfile, '__slots__'):
                data_flow_results["type_safety"] = True
                logger.info("✅ Type safety with slots validated")

        except Exception as e:
            logger.error(f"❌ Data flow validation failed: {e}")

        # Calculate consistency score
        scores = [
            25 if data_flow_results["lead_profile_compatibility"] else 0,
            25 if data_flow_results["enum_consistency"] else 0,
            25 if data_flow_results["memory_optimization"] else 0,
            25 if data_flow_results["type_safety"] else 0
        ]
        data_flow_results["consistency_score"] = sum(scores)

        return data_flow_results

    def validate_performance_architecture(self) -> Dict[str, Any]:
        """Validate performance optimization architecture."""
        logger.info("⚡ Validating performance architecture...")

        performance_results = {
            "async_support": False,
            "parallel_processing": False,
            "caching_architecture": False,
            "memory_optimization": False,
            "performance_score": 0
        }

        try:
            # Check for async method signatures
            from services.enhanced_ml_personalization_engine import EnhancedMLPersonalizationEngine

            # Inspect the class for async methods
            methods = inspect.getmembers(EnhancedMLPersonalizationEngine, predicate=inspect.isfunction)
            async_methods = [name for name, method in methods if inspect.iscoroutinefunction(method)]

            if len(async_methods) > 0:
                performance_results["async_support"] = True
                logger.info(f"✅ Async support validated ({len(async_methods)} async methods)")

            # Check for parallel processing patterns (asyncio.gather, concurrent.futures)
            import ast

            personalization_file = Path(__file__).parent.parent / "services" / "enhanced_ml_personalization_engine.py"
            if personalization_file.exists():
                with open(personalization_file, 'r') as f:
                    content = f.read()

                if "asyncio.gather" in content:
                    performance_results["parallel_processing"] = True
                    logger.info("✅ Parallel processing with asyncio.gather validated")

                if "_cache" in content or "Cache" in content:
                    performance_results["caching_architecture"] = True
                    logger.info("✅ Caching architecture validated")

                if "float32" in content:
                    performance_results["memory_optimization"] = True
                    logger.info("✅ Memory optimization with float32 validated")

        except Exception as e:
            logger.error(f"❌ Performance architecture validation failed: {e}")

        # Calculate performance score
        scores = [
            25 if performance_results["async_support"] else 0,
            25 if performance_results["parallel_processing"] else 0,
            25 if performance_results["caching_architecture"] else 0,
            25 if performance_results["memory_optimization"] else 0
        ]
        performance_results["performance_score"] = sum(scores)

        return performance_results

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        start_time = time.time()

        # Run all validations
        structure_results = self.validate_imports_and_structure()
        data_flow_results = self.validate_data_flow_consistency()
        performance_results = self.validate_performance_architecture()

        execution_time = (time.time() - start_time) * 1000

        # Calculate overall score
        overall_score = round(
            (structure_results["architecture_score"] * 0.4 +
             data_flow_results["consistency_score"] * 0.3 +
             performance_results["performance_score"] * 0.3), 2
        )

        report = {
            "validation_summary": {
                "total_services": structure_results["total_services"],
                "successful_imports": structure_results["successful_imports"],
                "overall_score": overall_score,
                "grade": self._calculate_grade(overall_score),
                "execution_time_ms": round(execution_time, 2)
            },
            "service_structure": structure_results,
            "data_flow": data_flow_results,
            "performance_architecture": performance_results,
            "recommendations": self._generate_recommendations(
                structure_results, data_flow_results, performance_results
            )
        }

        return report

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score."""
        if score >= 90: return "A"
        elif score >= 80: return "B"
        elif score >= 70: return "C"
        elif score >= 60: return "D"
        else: return "F"

    def _generate_recommendations(self, structure, data_flow, performance) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if structure["successful_imports"] == structure["total_services"]:
            recommendations.append("✅ All Enhanced ML services successfully imported and validated")
        else:
            recommendations.append(f"⚠️ Fix {structure['total_services'] - structure['successful_imports']} failed service imports")

        if data_flow["consistency_score"] >= 75:
            recommendations.append("✅ Data flow consistency meets production standards")
        else:
            recommendations.append("⚠️ Improve data flow consistency between services")

        if performance["performance_score"] >= 75:
            recommendations.append("✅ Performance architecture optimizations validated")
        else:
            recommendations.append("⚠️ Enhance performance optimizations (async, caching, memory)")

        if structure["shared_models_validated"]:
            recommendations.append("✅ Shared models provide consistent interfaces")
        else:
            recommendations.append("⚠️ Fix shared models import issues")

        return recommendations

def main():
    """Main validation execution."""
    print("🔧 Enhanced ML Interface Validation")
    print("=" * 50)

    validator = ServiceInterfaceValidator()
    report = validator.generate_comprehensive_report()

    # Print results
    print("\n📊 Validation Summary")
    print("=" * 50)
    print(f"Services Validated: {report['validation_summary']['total_services']}")
    print(f"Successful Imports: {report['validation_summary']['successful_imports']}")
    print(f"Overall Score: {report['validation_summary']['overall_score']}/100")
    print(f"Grade: {report['validation_summary']['grade']}")
    print(f"Execution Time: {report['validation_summary']['execution_time_ms']}ms")

    print("\n🏗️ Service Structure")
    print("=" * 50)
    for service_name, results in report['service_structure']['services'].items():
        status = "✅" if results['interface_score'] >= 80 else "⚠️" if results['interface_score'] >= 60 else "❌"
        print(f"{status} {service_name}: {results['interface_score']}/100")
        if results['errors']:
            for error in results['errors'][:2]:  # Show first 2 errors
                print(f"   • {error}")

    print("\n🔄 Data Flow Consistency")
    print("=" * 50)
    print(f"Lead Profile Compatibility: {'✅' if report['data_flow']['lead_profile_compatibility'] else '❌'}")
    print(f"Enum Consistency: {'✅' if report['data_flow']['enum_consistency'] else '❌'}")
    print(f"Memory Optimization: {'✅' if report['data_flow']['memory_optimization'] else '❌'}")
    print(f"Type Safety: {'✅' if report['data_flow']['type_safety'] else '❌'}")
    print(f"Consistency Score: {report['data_flow']['consistency_score']}/100")

    print("\n⚡ Performance Architecture")
    print("=" * 50)
    print(f"Async Support: {'✅' if report['performance_architecture']['async_support'] else '❌'}")
    print(f"Parallel Processing: {'✅' if report['performance_architecture']['parallel_processing'] else '❌'}")
    print(f"Caching Architecture: {'✅' if report['performance_architecture']['caching_architecture'] else '❌'}")
    print(f"Memory Optimization: {'✅' if report['performance_architecture']['memory_optimization'] else '❌'}")
    print(f"Performance Score: {report['performance_architecture']['performance_score']}/100")

    print("\n💡 Recommendations")
    print("=" * 50)
    for rec in report['recommendations']:
        print(f"• {rec}")

    # Save report
    report_file = Path(__file__).parent / "enhanced_ml_validation_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n📄 Full report saved to: {report_file}")

    return report['validation_summary']['overall_score'] >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)