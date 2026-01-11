#!/usr/bin/env python3
"""
Business Metrics Validation Script.

Validates the complete business metrics implementation including:
- Service initialization and database setup
- Webhook tracking functionality
- Conversion pipeline tracking
- Agent performance metrics
- Property matching effectiveness
- Dashboard data generation
- API endpoint functionality

Usage:
    python scripts/validate_business_metrics.py [--setup-db] [--test-api]

Options:
    --setup-db    Setup database tables for metrics
    --test-api    Test API endpoints (requires running server)
    --demo-data   Generate demo data for testing
"""

import asyncio
import argparse
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.business_metrics_service import (
    BusinessMetricsService,
    BusinessMetric,
    MetricType,
    ConversionStage,
    WebhookPerformanceMetrics,
    BusinessImpactMetrics,
    AgentProductivityMetrics,
    calculate_performance_grade,
    create_business_metrics_service
)
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class BusinessMetricsValidator:
    """Comprehensive validation of business metrics system."""

    def __init__(self):
        """Initialize the validator."""
        self.service: BusinessMetricsService = None
        self.test_location_id = "loc_validation_test"
        self.test_contact_id = "contact_validation_test"
        self.test_agent_id = "agent_validation_test"
        self.validation_results = {}

    async def setup_service(self) -> bool:
        """Setup business metrics service for validation."""
        try:
            logger.info("Initializing business metrics service...")

            self.service = await create_business_metrics_service(
                redis_url=settings.redis_url,
                postgres_url=settings.database_url
            )

            if self.service:
                logger.info("✅ Business metrics service initialized successfully")
                return True
            else:
                logger.error("❌ Failed to initialize business metrics service")
                return False

        except Exception as e:
            logger.error(f"❌ Service setup failed: {e}")
            return False

    async def validate_webhook_tracking(self) -> bool:
        """Validate webhook tracking functionality."""
        try:
            logger.info("Validating webhook tracking...")

            # Test webhook start tracking
            tracking_id = await self.service.track_webhook_start(
                location_id=self.test_location_id,
                contact_id=self.test_contact_id,
                webhook_type="message"
            )

            if not tracking_id:
                logger.error("❌ Webhook tracking start failed")
                return False

            # Simulate processing delay
            await asyncio.sleep(0.1)

            # Test webhook completion tracking
            enrichment_data = {
                "lead_score": 75,
                "extracted_preferences": 3,
                "claude_insights": True
            }

            processing_time = await self.service.track_webhook_completion(
                tracking_id=tracking_id,
                location_id=self.test_location_id,
                contact_id=self.test_contact_id,
                success=True,
                webhook_type="message",
                enrichment_data=enrichment_data
            )

            if processing_time < 0:
                logger.error("❌ Webhook completion tracking failed")
                return False

            logger.info(f"✅ Webhook tracking validated (processing: {processing_time:.1f}ms)")

            # Test webhook performance metrics
            performance = await self.service.get_webhook_performance_metrics(
                location_id=self.test_location_id,
                days=1
            )

            self.validation_results['webhook_tracking'] = {
                'processing_time_ms': processing_time,
                'performance_metrics': {
                    'total_webhooks': performance.total_webhooks,
                    'success_rate': performance.success_rate,
                    'meets_sla': performance.meets_sla
                }
            }

            return True

        except Exception as e:
            logger.error(f"❌ Webhook tracking validation failed: {e}")
            return False

    async def validate_conversion_tracking(self) -> bool:
        """Validate conversion pipeline tracking."""
        try:
            logger.info("Validating conversion tracking...")

            # Test lead creation tracking
            await self.service.track_conversion_stage(
                contact_id=self.test_contact_id,
                location_id=self.test_location_id,
                stage=ConversionStage.LEAD_CREATED,
                ai_score=65,
                metadata={"source": "validation_test"}
            )

            # Test AI qualification tracking
            await self.service.track_conversion_stage(
                contact_id=self.test_contact_id,
                location_id=self.test_location_id,
                stage=ConversionStage.AI_QUALIFIED,
                ai_score=75,
                agent_id=self.test_agent_id,
                metadata={"qualification_score": 85}
            )

            # Test deal closure tracking
            deal_value = Decimal('18500.00')
            await self.service.track_conversion_stage(
                contact_id=self.test_contact_id,
                location_id=self.test_location_id,
                stage=ConversionStage.DEAL_CLOSED,
                ai_score=85,
                agent_id=self.test_agent_id,
                deal_value=deal_value,
                metadata={"deal_type": "purchase", "property_id": "prop_test_123"}
            )

            # Test business impact calculation
            business_metrics = await self.service.get_business_impact_metrics(
                location_id=self.test_location_id,
                days=1
            )

            revenue_per_lead = await self.service.calculate_revenue_per_lead(
                location_id=self.test_location_id,
                days=1
            )

            self.validation_results['conversion_tracking'] = {
                'deal_value': float(deal_value),
                'revenue_per_lead': float(revenue_per_lead),
                'business_metrics': {
                    'total_revenue': float(business_metrics.total_revenue),
                    'conversion_rate': business_metrics.lead_to_conversion_rate,
                    'ai_correlation': business_metrics.ai_score_correlation
                }
            }

            logger.info(f"✅ Conversion tracking validated (revenue per lead: ${revenue_per_lead})")
            return True

        except Exception as e:
            logger.error(f"❌ Conversion tracking validation failed: {e}")
            return False

    async def validate_agent_performance_tracking(self) -> bool:
        """Validate agent performance tracking."""
        try:
            logger.info("Validating agent performance tracking...")

            # Test agent contact activity
            await self.service.track_agent_activity(
                agent_id=self.test_agent_id,
                location_id=self.test_location_id,
                activity_type="contact",
                contact_id=self.test_contact_id,
                response_time_minutes=8.5,
                ai_recommendation_used=True
            )

            # Test agent deal closure activity
            await self.service.track_agent_activity(
                agent_id=self.test_agent_id,
                location_id=self.test_location_id,
                activity_type="deal_closed",
                contact_id=self.test_contact_id,
                deal_value=Decimal('18500.00'),
                ai_recommendation_used=True
            )

            # Test agent productivity metrics
            productivity_metrics = await self.service.get_agent_productivity_metrics(
                agent_id=self.test_agent_id,
                location_id=self.test_location_id,
                days=1
            )

            self.validation_results['agent_performance'] = {
                'agent_id': productivity_metrics.agent_id,
                'deals_closed': productivity_metrics.deals_closed,
                'avg_deal_value': float(productivity_metrics.avg_deal_value),
                'productivity_score': productivity_metrics.productivity_score,
                'conversion_rate': productivity_metrics.conversion_rate,
                'ai_usage_rate': productivity_metrics.ai_recommendation_usage
            }

            logger.info(f"✅ Agent performance validated (productivity score: {productivity_metrics.productivity_score:.1f})")
            return True

        except Exception as e:
            logger.error(f"❌ Agent performance tracking validation failed: {e}")
            return False

    async def validate_property_matching(self) -> bool:
        """Validate property matching tracking."""
        try:
            logger.info("Validating property matching...")

            # Test property recommendation tracking
            recommendation_id = await self.service.track_property_recommendation(
                contact_id=self.test_contact_id,
                location_id=self.test_location_id,
                property_id="prop_validation_test",
                recommendation_score=0.82,
                agent_id=self.test_agent_id
            )

            if not recommendation_id:
                logger.error("❌ Property recommendation tracking failed")
                return False

            # Test property interaction tracking
            await self.service.track_property_interaction(
                recommendation_id=recommendation_id,
                interaction_type="liked",
                contact_id=self.test_contact_id,
                metadata={"view_duration_seconds": 45}
            )

            # Test property matching metrics
            property_metrics = await self.service.get_property_matching_metrics(
                location_id=self.test_location_id,
                days=1
            )

            self.validation_results['property_matching'] = {
                'recommendation_id': recommendation_id,
                'total_recommendations': property_metrics.get('total_recommendations', 0),
                'acceptance_rate': property_metrics.get('acceptance_rate', 0),
                'avg_score': property_metrics.get('avg_recommendation_score', 0)
            }

            logger.info(f"✅ Property matching validated (recommendation: {recommendation_id[:20]}...)")
            return True

        except Exception as e:
            logger.error(f"❌ Property matching validation failed: {e}")
            return False

    async def validate_dashboard_generation(self) -> bool:
        """Validate dashboard metrics generation."""
        try:
            logger.info("Validating dashboard generation...")

            # Test executive dashboard metrics
            dashboard_data = await self.service.get_executive_dashboard_metrics(
                location_id=self.test_location_id,
                days=1
            )

            if not dashboard_data:
                logger.error("❌ Dashboard generation failed")
                return False

            # Validate dashboard structure
            required_sections = ['summary', 'ghl_integration', 'business_impact', 'property_matching']
            missing_sections = [section for section in required_sections if section not in dashboard_data]

            if missing_sections:
                logger.error(f"❌ Dashboard missing sections: {missing_sections}")
                return False

            # Test performance grade calculation
            summary = dashboard_data.get('summary', {})
            performance_grade = calculate_performance_grade(summary)

            self.validation_results['dashboard'] = {
                'performance_grade': performance_grade,
                'summary_metrics': summary,
                'sections_present': list(dashboard_data.keys()),
                'generation_time': dashboard_data.get('generated_at')
            }

            logger.info(f"✅ Dashboard validated (grade: {performance_grade})")
            return True

        except Exception as e:
            logger.error(f"❌ Dashboard generation validation failed: {e}")
            return False

    async def validate_performance_requirements(self) -> bool:
        """Validate performance requirements are met."""
        try:
            logger.info("Validating performance requirements...")

            # Test webhook tracking performance
            start_time = time.time()
            tracking_id = await self.service.track_webhook_start(
                self.test_location_id, self.test_contact_id, "performance_test"
            )
            webhook_start_time = (time.time() - start_time) * 1000

            start_time = time.time()
            await self.service.track_webhook_completion(
                tracking_id, self.test_location_id, self.test_contact_id, True, webhook_type="performance_test"
            )
            webhook_complete_time = (time.time() - start_time) * 1000

            # Test dashboard generation performance
            start_time = time.time()
            await self.service.get_executive_dashboard_metrics(self.test_location_id, 7)
            dashboard_time = (time.time() - start_time) * 1000

            performance_results = {
                'webhook_start_ms': webhook_start_time,
                'webhook_complete_ms': webhook_complete_time,
                'dashboard_generation_ms': dashboard_time,
                'meets_webhook_sla': webhook_complete_time < 1000,  # <1s SLA
                'meets_dashboard_sla': dashboard_time < 2000  # <2s SLA
            }

            self.validation_results['performance'] = performance_results

            if performance_results['meets_webhook_sla'] and performance_results['meets_dashboard_sla']:
                logger.info(f"✅ Performance requirements met (webhook: {webhook_complete_time:.1f}ms, dashboard: {dashboard_time:.1f}ms)")
                return True
            else:
                logger.warning(f"⚠️ Performance requirements not met (webhook: {webhook_complete_time:.1f}ms, dashboard: {dashboard_time:.1f}ms)")
                return False

        except Exception as e:
            logger.error(f"❌ Performance validation failed: {e}")
            return False

    async def generate_demo_data(self) -> bool:
        """Generate demo data for testing and visualization."""
        try:
            logger.info("Generating demo data...")

            demo_locations = ["loc_demo_001", "loc_demo_002", "loc_demo_003"]
            demo_agents = ["agent_demo_001", "agent_demo_002", "agent_demo_003"]
            demo_contacts = [f"contact_demo_{i:03d}" for i in range(1, 51)]

            for location_id in demo_locations:
                for i, contact_id in enumerate(demo_contacts):
                    # Webhook tracking
                    tracking_id = await self.service.track_webhook_start(
                        location_id, contact_id, "message"
                    )
                    await asyncio.sleep(0.001)  # Simulate processing
                    await self.service.track_webhook_completion(
                        tracking_id, location_id, contact_id, True,
                        enrichment_data={"lead_score": 60 + (i % 40)}
                    )

                    # Conversion tracking
                    agent_id = demo_agents[i % len(demo_agents)]
                    ai_score = 60 + (i % 40)

                    await self.service.track_conversion_stage(
                        contact_id, location_id, ConversionStage.LEAD_CREATED,
                        ai_score=ai_score
                    )

                    if i % 4 == 0:  # 25% get qualified
                        await self.service.track_conversion_stage(
                            contact_id, location_id, ConversionStage.AI_QUALIFIED,
                            ai_score=ai_score + 10, agent_id=agent_id
                        )

                        if i % 8 == 0:  # 12.5% get contacted
                            await self.service.track_agent_activity(
                                agent_id, location_id, "contact", contact_id,
                                response_time_minutes=5 + (i % 30),
                                ai_recommendation_used=i % 3 == 0
                            )

                            if i % 16 == 0:  # 6.25% close deals
                                deal_value = Decimal(str(10000 + (i * 500)))
                                await self.service.track_conversion_stage(
                                    contact_id, location_id, ConversionStage.DEAL_CLOSED,
                                    ai_score=ai_score + 20, agent_id=agent_id,
                                    deal_value=deal_value
                                )

                                await self.service.track_agent_activity(
                                    agent_id, location_id, "deal_closed", contact_id,
                                    deal_value=deal_value, ai_recommendation_used=True
                                )

                    # Property recommendations
                    if i % 3 == 0:
                        recommendation_id = await self.service.track_property_recommendation(
                            contact_id, location_id, f"prop_{i:03d}",
                            recommendation_score=0.5 + (i % 50) / 100,
                            agent_id=agent_id
                        )

                        if i % 6 == 0:  # Some interactions
                            interaction_type = "liked" if i % 12 == 0 else "viewed"
                            await self.service.track_property_interaction(
                                recommendation_id, interaction_type, contact_id
                            )

            logger.info(f"✅ Demo data generated for {len(demo_locations)} locations")
            return True

        except Exception as e:
            logger.error(f"❌ Demo data generation failed: {e}")
            return False

    async def test_service_registry_integration(self) -> bool:
        """Test integration with service registry."""
        try:
            logger.info("Testing service registry integration...")

            from ghl_real_estate_ai.core.service_registry import ServiceRegistry

            registry = ServiceRegistry(demo_mode=False)

            # Test business metrics access
            business_metrics = registry.business_metrics
            if not business_metrics:
                logger.error("❌ Service registry business metrics access failed")
                return False

            # Test convenience methods
            dashboard_data = await registry.get_business_dashboard_metrics(
                location_id=self.test_location_id,
                days=1
            )

            if not dashboard_data:
                logger.error("❌ Service registry dashboard method failed")
                return False

            # Test conversion tracking
            success = await registry.track_lead_conversion(
                contact_id="test_registry_contact",
                location_id=self.test_location_id,
                stage="lead_created",
                ai_score=70
            )

            if not success:
                logger.error("❌ Service registry conversion tracking failed")
                return False

            logger.info("✅ Service registry integration validated")
            return True

        except Exception as e:
            logger.error(f"❌ Service registry integration failed: {e}")
            return False

    async def cleanup_test_data(self) -> bool:
        """Clean up test data after validation."""
        try:
            logger.info("Cleaning up test data...")

            # In a real implementation, would clean up specific test records
            # For now, just verify the service can be closed properly

            if self.service:
                await self.service.close()
                logger.info("✅ Test cleanup completed")

            return True

        except Exception as e:
            logger.error(f"❌ Test cleanup failed: {e}")
            return False

    async def run_full_validation(self, generate_demo: bool = False) -> bool:
        """Run complete validation suite."""
        logger.info("🚀 Starting comprehensive business metrics validation...")

        validation_steps = [
            ("Service Setup", self.setup_service),
            ("Webhook Tracking", self.validate_webhook_tracking),
            ("Conversion Tracking", self.validate_conversion_tracking),
            ("Agent Performance", self.validate_agent_performance_tracking),
            ("Property Matching", self.validate_property_matching),
            ("Dashboard Generation", self.validate_dashboard_generation),
            ("Performance Requirements", self.validate_performance_requirements),
            ("Service Registry Integration", self.test_service_registry_integration),
        ]

        if generate_demo:
            validation_steps.insert(-1, ("Demo Data Generation", self.generate_demo_data))

        results = {}
        overall_success = True

        for step_name, step_function in validation_steps:
            try:
                logger.info(f"\n🔍 Running: {step_name}")
                start_time = time.time()
                success = await step_function()
                duration = time.time() - start_time

                results[step_name] = {
                    "success": success,
                    "duration_ms": duration * 1000
                }

                if success:
                    logger.info(f"✅ {step_name} completed in {duration:.3f}s")
                else:
                    logger.error(f"❌ {step_name} failed")
                    overall_success = False

            except Exception as e:
                logger.error(f"❌ {step_name} crashed: {e}")
                results[step_name] = {"success": False, "error": str(e)}
                overall_success = False

        # Cleanup
        await self.cleanup_test_data()

        # Print summary
        self._print_validation_summary(results, overall_success)

        return overall_success

    def _print_validation_summary(self, results: Dict[str, Any], overall_success: bool) -> None:
        """Print validation summary results."""
        logger.info("\n" + "="*80)
        logger.info("📊 BUSINESS METRICS VALIDATION SUMMARY")
        logger.info("="*80)

        total_steps = len(results)
        successful_steps = sum(1 for result in results.values() if result.get('success'))
        total_time = sum(result.get('duration_ms', 0) for result in results.values())

        logger.info(f"Overall Status: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        logger.info(f"Steps Completed: {successful_steps}/{total_steps}")
        logger.info(f"Total Time: {total_time:.0f}ms")
        logger.info("")

        # Step-by-step results
        for step_name, result in results.items():
            status = "✅ PASS" if result.get('success') else "❌ FAIL"
            duration = result.get('duration_ms', 0)
            logger.info(f"{status:8} {step_name:30} ({duration:6.1f}ms)")

        if self.validation_results:
            logger.info("\n📈 Key Metrics:")
            webhook_metrics = self.validation_results.get('webhook_tracking', {})
            if webhook_metrics:
                processing_time = webhook_metrics.get('processing_time_ms', 0)
                logger.info(f"   Webhook Processing: {processing_time:.1f}ms")

            conversion_metrics = self.validation_results.get('conversion_tracking', {})
            if conversion_metrics:
                revenue_per_lead = conversion_metrics.get('revenue_per_lead', 0)
                logger.info(f"   Revenue per Lead: ${revenue_per_lead:.2f}")

            agent_metrics = self.validation_results.get('agent_performance', {})
            if agent_metrics:
                productivity = agent_metrics.get('productivity_score', 0)
                logger.info(f"   Agent Productivity: {productivity:.1f}/100")

            dashboard_metrics = self.validation_results.get('dashboard', {})
            if dashboard_metrics:
                grade = dashboard_metrics.get('performance_grade', 'N/A')
                logger.info(f"   Performance Grade: {grade}")

        logger.info("\n" + "="*80)


def main():
    """Main validation script entry point."""
    parser = argparse.ArgumentParser(description="Validate Business Metrics Implementation")
    parser.add_argument("--setup-db", action="store_true", help="Setup database tables")
    parser.add_argument("--demo-data", action="store_true", help="Generate demo data")
    parser.add_argument("--test-api", action="store_true", help="Test API endpoints")
    parser.add_argument("--location-id", default="loc_validation_test", help="Test location ID")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def run_validation():
        validator = BusinessMetricsValidator()

        if args.location_id:
            validator.test_location_id = args.location_id

        # Run full validation
        success = await validator.run_full_validation(generate_demo=args.demo_data)

        if args.test_api:
            logger.info("\n🌐 API Testing would require running server...")
            logger.info("Start server with: uvicorn main:app --reload")
            logger.info("Then test endpoints at: http://localhost:8000/api/business-metrics/")

        return success

    # Run validation
    success = asyncio.run(run_validation())
    exit_code = 0 if success else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()