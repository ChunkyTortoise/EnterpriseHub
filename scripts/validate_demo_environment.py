#!/usr/bin/env python3
"""
Jorge's Real Estate AI Platform - Demo Environment Validation Script
Validates demo environment functionality and data quality
Version: 2.0.0
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from ghl_real_estate_ai.services.client_demo_service import (
    ClientDemoService,
    DemoScenario
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemoEnvironmentValidator:
    """Comprehensive demo environment validation"""

    def __init__(self):
        self.demo_service = ClientDemoService()

    async def run_comprehensive_validation(self):
        """Run comprehensive validation of demo system"""

        logger.info("Starting comprehensive demo environment validation...")

        try:
            await self.demo_service.initialize()

            # Test 1: Service initialization
            logger.info("✅ Demo service initialization: PASSED")

            # Test 2: Create demo for each scenario
            results = {}
            for scenario in DemoScenario:
                logger.info(f"Testing scenario: {scenario.value}")

                try:
                    demo_env = await self.demo_service.create_demo_session(
                        scenario=scenario,
                        client_name=f"Test {scenario.value}",
                        agency_name=f"Test Agency {scenario.value}"
                    )

                    # Validate demo environment
                    validation_results = await self._validate_demo_environment(demo_env)
                    results[scenario.value] = validation_results

                    # Cleanup
                    await self.demo_service.cleanup_demo_session(demo_env.session_id)

                    if all(validation_results.values()):
                        logger.info(f"✅ {scenario.value}: ALL VALIDATIONS PASSED")
                    else:
                        failed = [k for k, v in validation_results.items() if not v]
                        logger.warning(f"❌ {scenario.value}: FAILED - {failed}")

                except Exception as e:
                    logger.error(f"❌ {scenario.value}: EXCEPTION - {str(e)}")
                    results[scenario.value] = {"error": str(e)}

            # Summary
            self._print_validation_summary(results)

            return results

        except Exception as e:
            logger.error(f"Comprehensive validation failed: {str(e)}")
            return {"error": str(e)}

    async def _validate_demo_environment(self, demo_env):
        """Validate individual demo environment"""

        validations = {
            "has_session_id": bool(demo_env.session_id),
            "has_client_profile": bool(demo_env.client_profile),
            "has_demo_leads": len(demo_env.demo_leads) > 0,
            "has_demo_properties": len(demo_env.demo_properties) > 0,
            "has_demo_conversations": len(demo_env.demo_conversations) > 0,
            "has_roi_calculation": bool(demo_env.roi_calculation),
            "has_performance_metrics": bool(demo_env.performance_metrics),
        }

        # Client profile validations
        if demo_env.client_profile:
            profile = demo_env.client_profile
            validations.update({
                "profile_has_name": bool(profile.name),
                "profile_has_agency": bool(profile.agency_name),
                "profile_has_monthly_leads": profile.monthly_leads > 0,
                "profile_has_deal_size": profile.avg_deal_size > 0,
                "profile_has_commission": 0 < profile.commission_rate < 1,
                "profile_has_challenges": len(profile.current_challenges) > 0,
                "profile_has_goals": len(profile.goals) > 0
            })

        # Lead data validations
        if demo_env.demo_leads:
            sample_lead = demo_env.demo_leads[0]
            validations.update({
                "leads_have_names": bool(sample_lead.get("name")),
                "leads_have_budgets": bool(sample_lead.get("budget_min")),
                "leads_have_sources": bool(sample_lead.get("source")),
                "leads_have_status": bool(sample_lead.get("qualification_status"))
            })

        # Property validations
        if demo_env.demo_properties:
            sample_property = demo_env.demo_properties[0]
            validations.update({
                "properties_have_addresses": bool(sample_property.get("address")),
                "properties_have_prices": bool(sample_property.get("price")),
                "properties_have_features": bool(sample_property.get("features"))
            })

        # ROI calculation validations
        if demo_env.roi_calculation:
            roi = demo_env.roi_calculation
            validations.update({
                "roi_has_summary": "summary" in roi,
                "roi_has_traditional_costs": "traditional_costs" in roi,
                "roi_has_jorge_costs": "jorge_costs" in roi,
                "roi_has_benefits": "jorge_benefits" in roi
            })

            if "summary" in roi:
                summary = roi["summary"]
                validations.update({
                    "roi_has_net_savings": "net_savings" in summary,
                    "roi_has_percentage": "roi_percentage" in summary,
                    "roi_savings_positive": summary.get("net_savings", 0) > 0,
                    "roi_percentage_positive": summary.get("roi_percentage", 0) > 0
                })

        # Performance metrics validations
        if demo_env.performance_metrics:
            perf = demo_env.performance_metrics
            validations.update({
                "perf_has_response_times": "response_times" in perf,
                "perf_has_conversion_rates": "conversion_rates" in perf,
                "perf_has_accuracy": "accuracy_scores" in perf,
                "perf_has_business_impact": "business_impact" in perf
            })

        return validations

    def _print_validation_summary(self, results: Dict[str, Any]):
        """Print comprehensive validation summary"""

        print("\n" + "="*80)
        print("DEMO ENVIRONMENT VALIDATION SUMMARY")
        print("="*80)

        total_scenarios = 0
        passed_scenarios = 0

        for scenario, validations in results.items():
            total_scenarios += 1

            if "error" in validations:
                print(f"\n❌ {scenario.upper()}: FAILED - {validations['error']}")
                continue

            passed_validations = sum(1 for v in validations.values() if v)
            total_validations = len(validations)

            if passed_validations == total_validations:
                print(f"\n✅ {scenario.upper()}: PASSED ({passed_validations}/{total_validations})")
                passed_scenarios += 1
            else:
                failed = [k for k, v in validations.items() if not v]
                print(f"\n❌ {scenario.upper()}: FAILED ({passed_validations}/{total_validations})")
                print(f"   Failed checks: {', '.join(failed)}")

        print(f"\n{'='*80}")
        print(f"OVERALL RESULTS: {passed_scenarios}/{total_scenarios} scenarios passed")

        if passed_scenarios == total_scenarios:
            print("🎉 ALL DEMO ENVIRONMENTS VALIDATED SUCCESSFULLY!")
        else:
            print(f"⚠️  {total_scenarios - passed_scenarios} scenarios need attention")

        print("="*80)

        return passed_scenarios == total_scenarios


async def main():
    """Main validation execution"""
    validator = DemoEnvironmentValidator()

    try:
        results = await validator.run_comprehensive_validation()

        # Export results
        with open("demo_validation_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("Validation results exported to demo_validation_results.json")

        # Determine exit code
        if all(
            isinstance(v, dict) and "error" not in v and all(v.values())
            for v in results.values()
        ):
            logger.info("All validations passed!")
            sys.exit(0)
        else:
            logger.warning("Some validations failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Validation failed with exception: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())