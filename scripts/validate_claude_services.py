#!/usr/bin/env python3
"""
Claude Services Validation Script

Comprehensive validation script to verify Claude services are functioning
correctly, performing within expected parameters, and properly integrated
with the EnterpriseHub ecosystem.

Usage:
    python scripts/validate_claude_services.py --full
    python scripts/validate_claude_services.py --quick
    python scripts/validate_claude_services.py --service agent_orchestrator
    python scripts/validate_claude_services.py --performance

Created: January 2026
Author: Enterprise Development Team
"""

import asyncio
import argparse
import logging
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ghl_real_estate_ai.services.claude_agent_orchestrator import (
    ClaudeAgentOrchestrator, AgentRole, TaskPriority
)
from ghl_real_estate_ai.services.claude_enterprise_intelligence import (
    ClaudeEnterpriseIntelligence
)
from ghl_real_estate_ai.services.claude_business_intelligence_automation import (
    ClaudeBusinessIntelligenceAutomation
)
from ghl_real_estate_ai.services.claude_api_integration import (
    ClaudeAPIIntegration, ClaudeServiceStatus
)
from ghl_real_estate_ai.services.claude_management_orchestration import (
    ClaudeManagementOrchestration, ServiceLifecycleState
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ValidationResult:
    """Validation test result."""

    def __init__(self, test_name: str, passed: bool, message: str,
                 duration: float = 0.0, details: Dict[str, Any] = None):
        self.test_name = test_name
        self.passed = passed
        self.message = message
        self.duration = duration
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class ClaudeServicesValidator:
    """Main validator for Claude services."""

    def __init__(self):
        self.results: List[ValidationResult] = []
        self.services = {}

    async def initialize_services(self) -> ValidationResult:
        """Initialize all Claude services."""
        start_time = time.time()

        try:
            self.services = {
                'orchestrator': ClaudeAgentOrchestrator(),
                'intelligence': ClaudeEnterpriseIntelligence(),
                'business': ClaudeBusinessIntelligenceAutomation(),
                'api': ClaudeAPIIntegration(),
                'management': ClaudeManagementOrchestration()
            }

            # Initialize services that support it
            for service_name, service in self.services.items():
                if hasattr(service, 'initialize'):
                    await service.initialize()

            duration = time.time() - start_time
            return ValidationResult(
                "Service Initialization",
                True,
                f"All {len(self.services)} Claude services initialized successfully",
                duration,
                {"services_count": len(self.services)}
            )

        except Exception as e:
            duration = time.time() - start_time
            return ValidationResult(
                "Service Initialization",
                False,
                f"Failed to initialize services: {str(e)}",
                duration,
                {"error": str(e)}
            )

    async def validate_service_health(self) -> List[ValidationResult]:
        """Validate health of all Claude services."""
        results = []

        for service_name, service in self.services.items():
            start_time = time.time()

            try:
                # Test basic service functionality
                if hasattr(service, 'health_check'):
                    await service.health_check()

                # Service-specific health checks
                if service_name == 'orchestrator':
                    await self._validate_orchestrator_health(service)
                elif service_name == 'intelligence':
                    await self._validate_intelligence_health(service)
                elif service_name == 'business':
                    await self._validate_business_health(service)
                elif service_name == 'management':
                    await self._validate_management_health(service)

                duration = time.time() - start_time
                results.append(ValidationResult(
                    f"{service_name.title()} Health Check",
                    True,
                    f"{service_name} service is healthy",
                    duration
                ))

            except Exception as e:
                duration = time.time() - start_time
                results.append(ValidationResult(
                    f"{service_name.title()} Health Check",
                    False,
                    f"{service_name} health check failed: {str(e)}",
                    duration,
                    {"error": str(e)}
                ))

        return results

    async def _validate_orchestrator_health(self, orchestrator):
        """Validate orchestrator-specific functionality."""
        # Test task submission
        task_id = await orchestrator.submit_task(
            task_type="health_check",
            description="Health check validation task",
            context={"validation": True},
            agent_role=AgentRole.SYSTEM_ARCHITECT,
            priority=TaskPriority.LOW
        )

        if not task_id:
            raise ValueError("Task submission failed")

        # Test task status retrieval
        status = await orchestrator.get_task_status(task_id)
        if status not in ["pending", "processing", "completed"]:
            raise ValueError(f"Invalid task status: {status}")

    async def _validate_intelligence_health(self, intelligence):
        """Validate intelligence service functionality."""
        # Test system health analysis
        analysis = await intelligence.analyze_system_health()
        if not hasattr(analysis, 'system_metrics'):
            raise ValueError("Invalid analysis result structure")

    async def _validate_business_health(self, business):
        """Validate business intelligence functionality."""
        # Test real-time insights generation
        insights = await business.generate_real_time_insights()
        if not isinstance(insights, list):
            raise ValueError("Invalid insights format")

    async def _validate_management_health(self, management):
        """Validate management orchestration functionality."""
        # Test system status retrieval
        status = await management.get_system_status()
        if not hasattr(status, 'overall_state'):
            raise ValueError("Invalid system status structure")

    async def validate_integration_points(self) -> List[ValidationResult]:
        """Validate integration between services."""
        results = []

        # Test orchestrator-intelligence integration
        results.append(await self._validate_orchestrator_intelligence())

        # Test intelligence-business integration
        results.append(await self._validate_intelligence_business())

        # Test management coordination
        results.append(await self._validate_management_coordination())

        return results

    async def _validate_orchestrator_intelligence(self) -> ValidationResult:
        """Validate orchestrator and intelligence integration."""
        start_time = time.time()

        try:
            orchestrator = self.services['orchestrator']
            intelligence = self.services['intelligence']

            # Submit analysis task
            task_id = await orchestrator.submit_task(
                task_type="system_analysis",
                description="Integration validation analysis",
                context={"integration_test": True},
                agent_role=AgentRole.SYSTEM_ARCHITECT,
                priority=TaskPriority.NORMAL
            )

            # Run intelligence analysis
            analysis = await intelligence.analyze_system_health()

            # Both should complete successfully
            duration = time.time() - start_time
            return ValidationResult(
                "Orchestrator-Intelligence Integration",
                True,
                "Integration between orchestrator and intelligence validated",
                duration,
                {"task_id": task_id, "analysis_completed": True}
            )

        except Exception as e:
            duration = time.time() - start_time
            return ValidationResult(
                "Orchestrator-Intelligence Integration",
                False,
                f"Integration validation failed: {str(e)}",
                duration,
                {"error": str(e)}
            )

    async def _validate_intelligence_business(self) -> ValidationResult:
        """Validate intelligence and business integration."""
        start_time = time.time()

        try:
            intelligence = self.services['intelligence']
            business = self.services['business']

            # Run both services
            analysis = await intelligence.analyze_system_health()
            insights = await business.generate_real_time_insights()

            duration = time.time() - start_time
            return ValidationResult(
                "Intelligence-Business Integration",
                True,
                "Integration between intelligence and business validated",
                duration,
                {"analysis_completed": True, "insights_generated": len(insights) if insights else 0}
            )

        except Exception as e:
            duration = time.time() - start_time
            return ValidationResult(
                "Intelligence-Business Integration",
                False,
                f"Integration validation failed: {str(e)}",
                duration,
                {"error": str(e)}
            )

    async def _validate_management_coordination(self) -> ValidationResult:
        """Validate management coordination capabilities."""
        start_time = time.time()

        try:
            management = self.services['management']

            # Test workflow coordination
            workflow_request = {
                "workflow_type": "validation_test",
                "priority": "normal",
                "data": {"validation": True, "test_id": str(uuid.uuid4())},
                "requirements": {"response_time_target": 5000}
            }

            coordination_result = await management.coordinate_intelligent_workflow(workflow_request)

            if not coordination_result or "workflow_id" not in coordination_result:
                raise ValueError("Invalid coordination result")

            duration = time.time() - start_time
            return ValidationResult(
                "Management Coordination",
                True,
                "Management coordination validated successfully",
                duration,
                {"workflow_id": coordination_result["workflow_id"]}
            )

        except Exception as e:
            duration = time.time() - start_time
            return ValidationResult(
                "Management Coordination",
                False,
                f"Management coordination failed: {str(e)}",
                duration,
                {"error": str(e)}
            )

    async def validate_performance(self) -> List[ValidationResult]:
        """Validate performance of Claude services."""
        results = []

        # Test response times
        results.append(await self._validate_response_times())

        # Test concurrent operations
        results.append(await self._validate_concurrent_operations())

        # Test resource utilization
        results.append(await self._validate_resource_utilization())

        return results

    async def _validate_response_times(self) -> ValidationResult:
        """Validate response times meet SLA requirements."""
        start_time = time.time()

        try:
            response_times = {}

            # Test orchestrator response time
            start = time.time()
            task_id = await self.services['orchestrator'].submit_task(
                task_type="performance_test",
                description="Performance validation",
                context={"test": True},
                agent_role=AgentRole.PERFORMANCE_ENGINEER,
                priority=TaskPriority.HIGH
            )
            response_times['orchestrator'] = (time.time() - start) * 1000

            # Test intelligence response time
            start = time.time()
            analysis = await self.services['intelligence'].analyze_system_health()
            response_times['intelligence'] = (time.time() - start) * 1000

            # Test business response time
            start = time.time()
            insights = await self.services['business'].generate_real_time_insights()
            response_times['business'] = (time.time() - start) * 1000

            # Check against SLA targets
            sla_targets = {
                'orchestrator': 1000,  # 1 second
                'intelligence': 5000,  # 5 seconds
                'business': 3000       # 3 seconds
            }

            violations = []
            for service, time_ms in response_times.items():
                if time_ms > sla_targets[service]:
                    violations.append(f"{service}: {time_ms:.0f}ms > {sla_targets[service]}ms")

            duration = time.time() - start_time

            if violations:
                return ValidationResult(
                    "Response Time Validation",
                    False,
                    f"SLA violations: {'; '.join(violations)}",
                    duration,
                    {"response_times": response_times, "violations": violations}
                )
            else:
                return ValidationResult(
                    "Response Time Validation",
                    True,
                    "All services meet response time SLAs",
                    duration,
                    {"response_times": response_times}
                )

        except Exception as e:
            duration = time.time() - start_time
            return ValidationResult(
                "Response Time Validation",
                False,
                f"Response time validation failed: {str(e)}",
                duration,
                {"error": str(e)}
            )

    async def _validate_concurrent_operations(self) -> ValidationResult:
        """Validate concurrent operation handling."""
        start_time = time.time()

        try:
            orchestrator = self.services['orchestrator']

            # Submit multiple concurrent tasks
            tasks = []
            for i in range(10):
                task = orchestrator.submit_task(
                    task_type=f"concurrent_test_{i}",
                    description=f"Concurrent validation task {i}",
                    context={"test_id": i, "concurrent": True},
                    agent_role=AgentRole.BUSINESS_INTELLIGENCE,
                    priority=TaskPriority.NORMAL
                )
                tasks.append(task)

            # Execute all tasks concurrently
            task_ids = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successful tasks
            successful_tasks = [tid for tid in task_ids if isinstance(tid, str)]
            failed_tasks = [tid for tid in task_ids if isinstance(tid, Exception)]

            duration = time.time() - start_time

            if len(successful_tasks) >= 8:  # Allow 2 failures out of 10
                return ValidationResult(
                    "Concurrent Operations",
                    True,
                    f"Concurrent operations validated: {len(successful_tasks)}/10 successful",
                    duration,
                    {"successful": len(successful_tasks), "failed": len(failed_tasks)}
                )
            else:
                return ValidationResult(
                    "Concurrent Operations",
                    False,
                    f"Too many concurrent operation failures: {len(failed_tasks)}/10",
                    duration,
                    {"successful": len(successful_tasks), "failed": len(failed_tasks)}
                )

        except Exception as e:
            duration = time.time() - start_time
            return ValidationResult(
                "Concurrent Operations",
                False,
                f"Concurrent operations validation failed: {str(e)}",
                duration,
                {"error": str(e)}
            )

    async def _validate_resource_utilization(self) -> ValidationResult:
        """Validate resource utilization is within acceptable ranges."""
        start_time = time.time()

        try:
            management = self.services['management']

            # Get system status
            status = await management.get_system_status()

            # Check resource utilization
            utilization = status.resource_utilization

            thresholds = {
                'cpu_usage': 90.0,
                'memory_usage': 85.0,
                'network_io': 80.0,
                'disk_io': 75.0
            }

            violations = []
            for resource, current_usage in utilization.items():
                if resource in thresholds and current_usage > thresholds[resource]:
                    violations.append(f"{resource}: {current_usage:.1f}% > {thresholds[resource]}%")

            duration = time.time() - start_time

            if violations:
                return ValidationResult(
                    "Resource Utilization",
                    False,
                    f"Resource utilization too high: {'; '.join(violations)}",
                    duration,
                    {"utilization": utilization, "violations": violations}
                )
            else:
                return ValidationResult(
                    "Resource Utilization",
                    True,
                    "Resource utilization within acceptable ranges",
                    duration,
                    {"utilization": utilization}
                )

        except Exception as e:
            duration = time.time() - start_time
            return ValidationResult(
                "Resource Utilization",
                False,
                f"Resource utilization validation failed: {str(e)}",
                duration,
                {"error": str(e)}
            )

    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        print("🔍 Starting comprehensive Claude services validation...")

        # Initialize services
        init_result = await self.initialize_services()
        self.results.append(init_result)

        if not init_result.passed:
            return self._generate_report()

        print("✅ Services initialized, running validation tests...")

        # Health checks
        health_results = await self.validate_service_health()
        self.results.extend(health_results)

        # Integration tests
        integration_results = await self.validate_integration_points()
        self.results.extend(integration_results)

        # Performance tests
        performance_results = await self.validate_performance()
        self.results.extend(performance_results)

        return self._generate_report()

    async def run_quick_validation(self) -> Dict[str, Any]:
        """Run quick validation (health checks only)."""
        print("⚡ Starting quick Claude services validation...")

        # Initialize services
        init_result = await self.initialize_services()
        self.results.append(init_result)

        if not init_result.passed:
            return self._generate_report()

        # Health checks only
        health_results = await self.validate_service_health()
        self.results.extend(health_results)

        return self._generate_report()

    async def run_service_validation(self, service_name: str) -> Dict[str, Any]:
        """Run validation for specific service."""
        print(f"🎯 Validating specific service: {service_name}")

        # Initialize services
        init_result = await self.initialize_services()
        self.results.append(init_result)

        if not init_result.passed:
            return self._generate_report()

        # Validate specific service
        if service_name in self.services:
            service = self.services[service_name]
            start_time = time.time()

            try:
                if service_name == 'orchestrator':
                    await self._validate_orchestrator_health(service)
                elif service_name == 'intelligence':
                    await self._validate_intelligence_health(service)
                elif service_name == 'business':
                    await self._validate_business_health(service)
                elif service_name == 'management':
                    await self._validate_management_health(service)

                duration = time.time() - start_time
                self.results.append(ValidationResult(
                    f"{service_name.title()} Validation",
                    True,
                    f"{service_name} validation completed successfully",
                    duration
                ))

            except Exception as e:
                duration = time.time() - start_time
                self.results.append(ValidationResult(
                    f"{service_name.title()} Validation",
                    False,
                    f"{service_name} validation failed: {str(e)}",
                    duration,
                    {"error": str(e)}
                ))

        return self._generate_report()

    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.passed])
        failed_tests = total_tests - passed_tests

        total_duration = sum(r.duration for r in self.results)

        report = {
            "validation_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration": total_duration,
                "timestamp": datetime.utcnow().isoformat()
            },
            "test_results": [
                {
                    "test": result.test_name,
                    "status": "PASS" if result.passed else "FAIL",
                    "message": result.message,
                    "duration": f"{result.duration:.3f}s",
                    "details": result.details
                }
                for result in self.results
            ],
            "overall_status": "HEALTHY" if failed_tests == 0 else "DEGRADED" if passed_tests > failed_tests else "UNHEALTHY"
        }

        return report

    async def cleanup_services(self):
        """Cleanup services after validation."""
        for service in self.services.values():
            if hasattr(service, 'shutdown'):
                try:
                    await service.shutdown()
                except Exception as e:
                    logger.warning(f"Error during service cleanup: {e}")

async def main():
    """Main validation script entry point."""
    parser = argparse.ArgumentParser(description="Claude Services Validation Tool")
    parser.add_argument("--full", action="store_true", help="Run full validation suite")
    parser.add_argument("--quick", action="store_true", help="Run quick health check validation")
    parser.add_argument("--service", help="Validate specific service")
    parser.add_argument("--performance", action="store_true", help="Run performance validation only")
    parser.add_argument("--output", help="Output file for validation report")

    args = parser.parse_args()

    if not any([args.full, args.quick, args.service, args.performance]):
        args.quick = True  # Default to quick validation

    validator = ClaudeServicesValidator()

    try:
        if args.full:
            report = await validator.run_full_validation()
        elif args.quick:
            report = await validator.run_quick_validation()
        elif args.service:
            report = await validator.run_service_validation(args.service)
        elif args.performance:
            await validator.initialize_services()
            performance_results = await validator.validate_performance()
            validator.results.extend(performance_results)
            report = validator._generate_report()

        # Output report
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Validation report saved to {args.output}")
        else:
            print("\n📊 Validation Report:")
            print(json.dumps(report, indent=2))

        # Print summary
        summary = report["validation_summary"]
        status = report["overall_status"]

        print(f"\n🎯 Validation Summary:")
        print(f"   Status: {status}")
        print(f"   Tests: {summary['passed']}/{summary['total_tests']} passed ({summary['success_rate']:.1f}%)")
        print(f"   Duration: {summary['total_duration']:.2f}s")

        # Exit with appropriate code
        if status == "UNHEALTHY":
            sys.exit(2)
        elif status == "DEGRADED":
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        print(f"❌ Validation failed: {e}")
        sys.exit(3)

    finally:
        await validator.cleanup_services()

if __name__ == "__main__":
    asyncio.run(main())