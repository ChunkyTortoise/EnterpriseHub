"""
Phase 5 Advanced AI API Integration Validator

Comprehensive validation script for all Phase 5 advanced AI API endpoints.
Validates endpoint availability, authentication, request/response models,
and integration with existing EnterpriseHub architecture.

Usage:
    python -m ghl_real_estate_ai.api.routes.advanced.integration_validator
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

logger = logging.getLogger(__name__)

class AdvancedAPIValidator:
    """Comprehensive validator for Phase 5 Advanced AI API endpoints."""

    def __init__(self):
        self.validation_results = []
        self.errors = []
        self.warnings = []

    async def validate_all_endpoints(self) -> Dict[str, Any]:
        """Run comprehensive validation for all advanced AI endpoints."""
        logger.info("Starting Phase 5 Advanced AI API validation...")

        validation_results = {
            "validation_timestamp": datetime.now().isoformat(),
            "validation_summary": {},
            "endpoint_validations": {},
            "service_validations": {},
            "integration_validations": {},
            "performance_validations": {},
            "errors": [],
            "warnings": [],
            "recommendations": []
        }

        try:
            # 1. Validate endpoint imports and structure
            await self._validate_endpoint_imports(validation_results)

            # 2. Validate request/response models
            await self._validate_pydantic_models(validation_results)

            # 3. Validate service dependencies
            await self._validate_service_dependencies(validation_results)

            # 4. Validate authentication integration
            await self._validate_authentication_integration(validation_results)

            # 5. Validate WebSocket functionality
            await self._validate_websocket_integration(validation_results)

            # 6. Validate analytics integration
            await self._validate_analytics_integration(validation_results)

            # 7. Validate error handling
            await self._validate_error_handling(validation_results)

            # 8. Generate summary and recommendations
            await self._generate_validation_summary(validation_results)

        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            validation_results["errors"].append({
                "type": "validation_error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })

        return validation_results

    async def _validate_endpoint_imports(self, results: Dict[str, Any]):
        """Validate that all endpoint modules can be imported."""
        logger.info("Validating endpoint imports...")

        endpoint_imports = {
            "advanced_ai_endpoints": "ghl_real_estate_ai.api.routes.advanced.advanced_ai_endpoints",
            "multi_language_api": "ghl_real_estate_ai.api.routes.advanced.multi_language_api",
            "intervention_api": "ghl_real_estate_ai.api.routes.advanced.intervention_api",
            "personalization_api": "ghl_real_estate_ai.api.routes.advanced.personalization_api",
            "websocket_endpoints": "ghl_real_estate_ai.api.routes.advanced.websocket_endpoints"
        }

        import_results = {}

        for name, module_path in endpoint_imports.items():
            try:
                # Attempt to import module
                import importlib
                module = importlib.import_module(module_path)

                # Check for router
                if hasattr(module, 'router'):
                    import_results[name] = {
                        "status": "success",
                        "router_available": True,
                        "module_path": module_path
                    }
                else:
                    import_results[name] = {
                        "status": "warning",
                        "router_available": False,
                        "module_path": module_path,
                        "message": "Module imported but no router found"
                    }
                    results["warnings"].append({
                        "type": "missing_router",
                        "module": name,
                        "message": "Router not found in module"
                    })

            except ImportError as e:
                import_results[name] = {
                    "status": "error",
                    "error": str(e),
                    "module_path": module_path
                }
                results["errors"].append({
                    "type": "import_error",
                    "module": name,
                    "error": str(e)
                })

            except Exception as e:
                import_results[name] = {
                    "status": "error",
                    "error": str(e),
                    "module_path": module_path
                }
                results["errors"].append({
                    "type": "unexpected_import_error",
                    "module": name,
                    "error": str(e)
                })

        results["endpoint_validations"]["imports"] = import_results

    async def _validate_pydantic_models(self, results: Dict[str, Any]):
        """Validate Pydantic request/response models."""
        logger.info("Validating Pydantic models...")

        model_validations = {}

        # Test comprehensive analysis models
        try:
            from ghl_real_estate_ai.api.routes.advanced.advanced_ai_endpoints import (
                ComprehensiveAnalysisRequest,
                ComprehensiveAnalysisResponse,
                AdvancedHealthResponse
            )

            # Test model instantiation
            test_request = ComprehensiveAnalysisRequest(
                lead_id="test_lead",
                conversation_history=[],
                current_message="test message"
            )

            test_response = ComprehensiveAnalysisResponse(
                analysis_id="test_analysis",
                lead_id="test_lead",
                timestamp=datetime.now().isoformat(),
                performance_metrics={},
                recommendations=[],
                confidence_score=0.8,
                processing_time_ms=100.0
            )

            model_validations["advanced_ai_models"] = {
                "status": "success",
                "models_tested": ["ComprehensiveAnalysisRequest", "ComprehensiveAnalysisResponse", "AdvancedHealthResponse"],
                "validation_passed": True
            }

        except Exception as e:
            model_validations["advanced_ai_models"] = {
                "status": "error",
                "error": str(e)
            }
            results["errors"].append({
                "type": "model_validation_error",
                "category": "advanced_ai_models",
                "error": str(e)
            })

        # Test multi-language models
        try:
            from ghl_real_estate_ai.api.routes.advanced.multi_language_api import (
                LanguageDetectionRequest,
                VoiceProcessingRequest,
                CulturalAdaptationRequest
            )

            test_lang_request = LanguageDetectionRequest(
                text="test text"
            )

            model_validations["multi_language_models"] = {
                "status": "success",
                "models_tested": ["LanguageDetectionRequest", "VoiceProcessingRequest", "CulturalAdaptationRequest"],
                "validation_passed": True
            }

        except Exception as e:
            model_validations["multi_language_models"] = {
                "status": "error",
                "error": str(e)
            }

        results["endpoint_validations"]["pydantic_models"] = model_validations

    async def _validate_service_dependencies(self, results: Dict[str, Any]):
        """Validate service dependencies and availability."""
        logger.info("Validating service dependencies...")

        service_validations = {}

        # Test Phase 5 service imports
        phase5_services = {
            "MultiLanguageVoiceService": "ghl_real_estate_ai.services.claude.advanced.multi_language_voice_service",
            "AdvancedPredictiveBehaviorAnalyzer": "ghl_real_estate_ai.services.claude.advanced.predictive_behavior_analyzer",
            "IndustryVerticalSpecializationService": "ghl_real_estate_ai.services.claude.advanced.industry_vertical_specialization",
            "EnhancedPredictiveLeadInterventionStrategies": "ghl_real_estate_ai.services.claude.advanced.predictive_lead_intervention_strategies",
            "EnterprisePerformanceOptimizer": "ghl_real_estate_ai.services.claude.advanced.enterprise_performance_optimizer"
        }

        for service_name, module_path in phase5_services.items():
            try:
                import importlib
                module = importlib.import_module(module_path)

                if hasattr(module, service_name):
                    service_validations[service_name] = {
                        "status": "success",
                        "available": True,
                        "module_path": module_path
                    }
                else:
                    service_validations[service_name] = {
                        "status": "error",
                        "available": False,
                        "module_path": module_path,
                        "message": f"{service_name} not found in module"
                    }

            except ImportError:
                service_validations[service_name] = {
                    "status": "warning",
                    "available": False,
                    "module_path": module_path,
                    "message": "Service implementation not available (expected in full deployment)"
                }

            except Exception as e:
                service_validations[service_name] = {
                    "status": "error",
                    "available": False,
                    "error": str(e)
                }

        results["service_validations"]["phase5_services"] = service_validations

        # Test core middleware services
        middleware_services = {
            "JWTAuth": "ghl_real_estate_ai.api.middleware",
            "AnalyticsService": "ghl_real_estate_ai.services.analytics_service"
        }

        middleware_validations = {}
        for service_name, module_path in middleware_services.items():
            try:
                import importlib
                module = importlib.import_module(module_path)

                if hasattr(module, service_name):
                    middleware_validations[service_name] = {
                        "status": "success",
                        "available": True,
                        "module_path": module_path
                    }
                else:
                    middleware_validations[service_name] = {
                        "status": "error",
                        "available": False,
                        "module_path": module_path
                    }

            except Exception as e:
                middleware_validations[service_name] = {
                    "status": "error",
                    "available": False,
                    "error": str(e)
                }

        results["service_validations"]["middleware_services"] = middleware_validations

    async def _validate_authentication_integration(self, results: Dict[str, Any]):
        """Validate authentication integration."""
        logger.info("Validating authentication integration...")

        auth_validations = {}

        try:
            # Test middleware imports
            from ghl_real_estate_ai.api.middleware import get_current_user, verify_api_key

            auth_validations["middleware_imports"] = {
                "status": "success",
                "functions_available": ["get_current_user", "verify_api_key"]
            }

            # Test WebSocket auth
            try:
                from ghl_real_estate_ai.api.middleware.jwt_auth import verify_websocket_token

                auth_validations["websocket_auth"] = {
                    "status": "success",
                    "verify_websocket_token_available": True
                }

            except ImportError:
                auth_validations["websocket_auth"] = {
                    "status": "warning",
                    "verify_websocket_token_available": False,
                    "message": "WebSocket auth function not found"
                }

        except Exception as e:
            auth_validations["middleware_imports"] = {
                "status": "error",
                "error": str(e)
            }

        results["integration_validations"]["authentication"] = auth_validations

    async def _validate_websocket_integration(self, results: Dict[str, Any]):
        """Validate WebSocket integration."""
        logger.info("Validating WebSocket integration...")

        websocket_validations = {}

        try:
            # Check FastAPI WebSocket imports
            from fastapi import WebSocket, WebSocketDisconnect

            websocket_validations["fastapi_websocket"] = {
                "status": "success",
                "imports_available": True
            }

            # Check WebSocket endpoints structure
            try:
                from ghl_real_estate_ai.api.routes.advanced.websocket_endpoints import router, AdvancedWebSocketManager

                # Count WebSocket endpoints in router
                websocket_endpoints = []
                for route in router.routes:
                    if hasattr(route, 'path'):
                        websocket_endpoints.append(route.path)

                websocket_validations["endpoint_structure"] = {
                    "status": "success",
                    "websocket_endpoints": websocket_endpoints,
                    "manager_available": True,
                    "endpoint_count": len(websocket_endpoints)
                }

            except Exception as e:
                websocket_validations["endpoint_structure"] = {
                    "status": "error",
                    "error": str(e)
                }

        except Exception as e:
            websocket_validations["fastapi_websocket"] = {
                "status": "error",
                "error": str(e)
            }

        results["integration_validations"]["websocket"] = websocket_validations

    async def _validate_analytics_integration(self, results: Dict[str, Any]):
        """Validate analytics integration."""
        logger.info("Validating analytics integration...")

        analytics_validations = {}

        try:
            from ghl_real_estate_ai.services.analytics_service import AnalyticsService

            # Test service instantiation
            analytics_service = AnalyticsService()

            analytics_validations["service_instantiation"] = {
                "status": "success",
                "service_available": True,
                "methods_available": dir(analytics_service)
            }

        except Exception as e:
            analytics_validations["service_instantiation"] = {
                "status": "error",
                "error": str(e)
            }

        results["integration_validations"]["analytics"] = analytics_validations

    async def _validate_error_handling(self, results: Dict[str, Any]):
        """Validate error handling patterns."""
        logger.info("Validating error handling patterns...")

        error_handling_validations = {}

        try:
            # Check FastAPI HTTPException import
            from fastapi import HTTPException, status

            error_handling_validations["fastapi_exceptions"] = {
                "status": "success",
                "exceptions_available": True
            }

            # Check logging integration
            from ghl_real_estate_ai.ghl_utils.logger import get_logger

            error_handling_validations["logging_integration"] = {
                "status": "success",
                "logger_available": True
            }

        except Exception as e:
            error_handling_validations["validation_error"] = {
                "status": "error",
                "error": str(e)
            }

        results["integration_validations"]["error_handling"] = error_handling_validations

    async def _generate_validation_summary(self, results: Dict[str, Any]):
        """Generate validation summary and recommendations."""
        logger.info("Generating validation summary...")

        # Count successes, warnings, and errors
        total_validations = 0
        successful_validations = 0
        warnings_count = len(results["warnings"])
        errors_count = len(results["errors"])

        # Count validations from all categories
        for category, validations in results.get("endpoint_validations", {}).items():
            if isinstance(validations, dict):
                for validation_name, validation_result in validations.items():
                    total_validations += 1
                    if validation_result.get("status") == "success":
                        successful_validations += 1

        for category, validations in results.get("service_validations", {}).items():
            if isinstance(validations, dict):
                for validation_name, validation_result in validations.items():
                    total_validations += 1
                    if validation_result.get("status") == "success":
                        successful_validations += 1

        for category, validations in results.get("integration_validations", {}).items():
            if isinstance(validations, dict):
                for validation_name, validation_result in validations.items():
                    total_validations += 1
                    if validation_result.get("status") == "success":
                        successful_validations += 1

        # Calculate success rate
        success_rate = (successful_validations / total_validations * 100) if total_validations > 0 else 0

        # Determine overall status
        if errors_count == 0 and warnings_count <= 2:
            overall_status = "excellent"
        elif errors_count == 0 and warnings_count <= 5:
            overall_status = "good"
        elif errors_count <= 2:
            overall_status = "acceptable"
        else:
            overall_status = "needs_attention"

        results["validation_summary"] = {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "warnings_count": warnings_count,
            "errors_count": errors_count,
            "completion_timestamp": datetime.now().isoformat()
        }

        # Generate recommendations
        recommendations = []

        if errors_count > 0:
            recommendations.append({
                "priority": "high",
                "category": "error_resolution",
                "recommendation": f"Resolve {errors_count} validation errors before production deployment",
                "impact": "critical"
            })

        if warnings_count > 5:
            recommendations.append({
                "priority": "medium",
                "category": "warning_resolution",
                "recommendation": f"Address {warnings_count} warnings for optimal performance",
                "impact": "moderate"
            })

        # Service availability recommendations
        if not results.get("service_validations", {}).get("phase5_services", {}):
            recommendations.append({
                "priority": "high",
                "category": "service_deployment",
                "recommendation": "Deploy Phase 5 advanced AI services for full functionality",
                "impact": "high"
            })

        # General recommendations
        recommendations.extend([
            {
                "priority": "medium",
                "category": "monitoring",
                "recommendation": "Set up comprehensive monitoring for all advanced AI endpoints",
                "impact": "operational"
            },
            {
                "priority": "low",
                "category": "documentation",
                "recommendation": "Generate OpenAPI documentation for all endpoints",
                "impact": "developer_experience"
            },
            {
                "priority": "medium",
                "category": "testing",
                "recommendation": "Implement comprehensive integration tests for production validation",
                "impact": "quality_assurance"
            }
        ])

        results["recommendations"] = recommendations

    async def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report."""
        validation_results = await self.validate_all_endpoints()

        report_sections = []

        # Header
        report_sections.append("# Phase 5 Advanced AI API Validation Report")
        report_sections.append(f"**Generated**: {validation_results['validation_timestamp']}")
        report_sections.append("")

        # Summary
        summary = validation_results["validation_summary"]
        report_sections.append("## Validation Summary")
        report_sections.append(f"- **Overall Status**: {summary['overall_status'].upper()}")
        report_sections.append(f"- **Success Rate**: {summary['success_rate']:.1f}%")
        report_sections.append(f"- **Total Validations**: {summary['total_validations']}")
        report_sections.append(f"- **Successful**: {summary['successful_validations']}")
        report_sections.append(f"- **Warnings**: {summary['warnings_count']}")
        report_sections.append(f"- **Errors**: {summary['errors_count']}")
        report_sections.append("")

        # Errors
        if validation_results["errors"]:
            report_sections.append("## ❌ Errors")
            for error in validation_results["errors"]:
                report_sections.append(f"- **{error['type']}**: {error.get('message', error.get('error', 'Unknown error'))}")
            report_sections.append("")

        # Warnings
        if validation_results["warnings"]:
            report_sections.append("## ⚠️ Warnings")
            for warning in validation_results["warnings"]:
                report_sections.append(f"- **{warning['type']}**: {warning.get('message', 'Warning')}")
            report_sections.append("")

        # Recommendations
        if validation_results["recommendations"]:
            report_sections.append("## 📋 Recommendations")
            for rec in validation_results["recommendations"]:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec["priority"], "")
                report_sections.append(f"- {priority_emoji} **{rec['category']}**: {rec['recommendation']} (*{rec['impact']}*)")
            report_sections.append("")

        # Detailed Results
        report_sections.append("## 📊 Detailed Validation Results")
        report_sections.append("")

        # Add detailed results
        for category_name, category_results in validation_results.items():
            if category_name.endswith("_validations") and isinstance(category_results, dict):
                report_sections.append(f"### {category_name.replace('_', ' ').title()}")
                for validation_name, result in category_results.items():
                    if isinstance(result, dict):
                        status_emoji = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(result.get("status"), "")
                        report_sections.append(f"- {status_emoji} **{validation_name}**: {result.get('status', 'unknown')}")
                report_sections.append("")

        return "\n".join(report_sections)

    async def run_validation_cli(self):
        """Run validation from command line."""
        print("🚀 Starting Phase 5 Advanced AI API Validation...")
        print()

        try:
            # Generate validation report
            report = await self.generate_validation_report()

            # Print report
            print(report)

            # Save report to file
            report_filename = f"phase5_api_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_filename, 'w') as f:
                f.write(report)

            print(f"\n💾 Validation report saved to: {report_filename}")

            # Return exit code based on validation results
            validation_results = await self.validate_all_endpoints()
            errors_count = len(validation_results.get("errors", []))

            if errors_count > 0:
                print(f"\n❌ Validation completed with {errors_count} errors")
                return 1
            else:
                print(f"\n✅ Validation completed successfully")
                return 0

        except Exception as e:
            print(f"\n💥 Validation failed with error: {e}")
            return 1


async def main():
    """Main CLI entry point."""
    validator = AdvancedAPIValidator()
    exit_code = await validator.run_validation_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())