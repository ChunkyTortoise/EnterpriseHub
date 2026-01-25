#!/usr/bin/env python3
"""
Jorge's Real Estate AI Platform - Demo Environment Seeding Script
Creates professional demo environments for client presentations
Version: 2.0.0
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from ghl_real_estate_ai.services.client_demo_service import (
    ClientDemoService,
    DemoScenario,
    DemoEnvironment
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoEnvironmentSeeder:
    """Professional demo environment seeding and management"""

    def __init__(self):
        self.demo_service = ClientDemoService()
        self.created_sessions = []

    async def initialize(self):
        """Initialize the demo service"""
        await self.demo_service.initialize()
        logger.info("Demo environment seeder initialized")

    async def create_all_scenarios(self) -> List[DemoEnvironment]:
        """Create demo environments for all scenarios"""
        scenarios = list(DemoScenario)
        environments = []

        for scenario in scenarios:
            logger.info(f"Creating demo environment for {scenario.value}")

            try:
                demo_env = await self.demo_service.create_demo_session(
                    scenario=scenario,
                    client_name=f"Demo {scenario.value.replace('_', ' ').title()}",
                    agency_name=f"Professional {scenario.value.replace('_', ' ').title()} Agency"
                )

                environments.append(demo_env)
                self.created_sessions.append(demo_env.session_id)

                logger.info(
                    f"Created {scenario.value} demo: {demo_env.session_id} "
                    f"({demo_env.client_profile.name})"
                )

            except Exception as e:
                logger.error(f"Failed to create {scenario.value} demo: {str(e)}")

        return environments

    async def create_specific_scenario(
        self,
        scenario: str,
        client_name: str = None,
        agency_name: str = None,
        custom_params: Dict[str, Any] = None
    ) -> DemoEnvironment:
        """Create demo environment for specific scenario"""

        try:
            scenario_enum = DemoScenario(scenario)
        except ValueError:
            raise ValueError(f"Invalid scenario: {scenario}. Valid options: {[s.value for s in DemoScenario]}")

        logger.info(f"Creating demo environment for {scenario}")

        demo_env = await self.demo_service.create_demo_session(
            scenario=scenario_enum,
            client_name=client_name,
            agency_name=agency_name,
            custom_params=custom_params
        )

        self.created_sessions.append(demo_env.session_id)

        logger.info(
            f"Created {scenario} demo: {demo_env.session_id} "
            f"({demo_env.client_profile.name})"
        )

        return demo_env

    async def export_demo_data(self, demo_env: DemoEnvironment, output_file: str):
        """Export demo environment data to file"""

        export_data = {
            "session_info": {
                "session_id": demo_env.session_id,
                "scenario": demo_env.client_profile.market_segment.value,
                "created_at": demo_env.created_at.isoformat(),
                "expires_at": demo_env.expires_at.isoformat()
            },
            "client_profile": {
                "name": demo_env.client_profile.name,
                "agency_name": demo_env.client_profile.agency_name,
                "market_segment": demo_env.client_profile.market_segment.value,
                "monthly_leads": demo_env.client_profile.monthly_leads,
                "avg_deal_size": demo_env.client_profile.avg_deal_size,
                "commission_rate": demo_env.client_profile.commission_rate,
                "geographic_market": demo_env.client_profile.geographic_market,
                "experience_level": demo_env.client_profile.experience_level,
                "tech_adoption": demo_env.client_profile.tech_adoption,
                "current_challenges": demo_env.client_profile.current_challenges,
                "goals": demo_env.client_profile.goals,
                "pain_points": demo_env.client_profile.pain_points
            },
            "demo_metrics": {
                "total_leads": len(demo_env.demo_leads),
                "total_properties": len(demo_env.demo_properties),
                "total_conversations": len(demo_env.demo_conversations)
            },
            "roi_summary": demo_env.roi_calculation.get("summary", {}),
            "performance_highlights": {
                "response_time_improvement": demo_env.performance_metrics.get("response_times", {}).get("improvement", "N/A"),
                "conversion_improvement": demo_env.performance_metrics.get("conversion_rates", {}).get("improvement", "N/A"),
                "accuracy_improvement": demo_env.performance_metrics.get("accuracy_scores", {}).get("improvement", "N/A"),
                "monthly_revenue_increase": demo_env.performance_metrics.get("monthly_performance", {}).get("additional_revenue", 0),
                "business_impact": demo_env.performance_metrics.get("business_impact", {})
            }
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        logger.info(f"Demo data exported to {output_file}")

    async def validate_demo_environment(self, demo_env: DemoEnvironment) -> Dict[str, bool]:
        """Validate demo environment completeness"""

        validations = {
            "has_client_profile": bool(demo_env.client_profile),
            "has_leads": len(demo_env.demo_leads) > 0,
            "has_properties": len(demo_env.demo_properties) > 0,
            "has_conversations": len(demo_env.demo_conversations) > 0,
            "has_roi_calculation": bool(demo_env.roi_calculation),
            "has_performance_metrics": bool(demo_env.performance_metrics),
            "roi_has_summary": "summary" in demo_env.roi_calculation,
            "has_business_impact": "business_impact" in demo_env.performance_metrics
        }

        # Detailed validations
        if demo_env.client_profile:
            validations["profile_has_challenges"] = len(demo_env.client_profile.current_challenges) > 0
            validations["profile_has_goals"] = len(demo_env.client_profile.goals) > 0
            validations["profile_has_contact_info"] = bool(demo_env.client_profile.name and demo_env.client_profile.agency_name)

        # ROI calculation validations
        if demo_env.roi_calculation and "summary" in demo_env.roi_calculation:
            summary = demo_env.roi_calculation["summary"]
            validations["roi_has_savings"] = "net_savings" in summary and summary["net_savings"] > 0
            validations["roi_has_percentage"] = "roi_percentage" in summary and summary["roi_percentage"] > 0

        all_valid = all(validations.values())

        if all_valid:
            logger.info(f"Demo environment {demo_env.session_id} validation: PASSED")
        else:
            failed_checks = [k for k, v in validations.items() if not v]
            logger.warning(f"Demo environment {demo_env.session_id} validation: FAILED - {failed_checks}")

        return validations

    async def cleanup_created_sessions(self):
        """Clean up all sessions created during this run"""
        for session_id in self.created_sessions:
            try:
                await self.demo_service.cleanup_demo_session(session_id)
                logger.info(f"Cleaned up demo session: {session_id}")
            except Exception as e:
                logger.error(f"Failed to cleanup session {session_id}: {str(e)}")

    async def print_demo_summary(self, demo_env: DemoEnvironment):
        """Print demo environment summary"""
        print("\n" + "="*80)
        print(f"DEMO ENVIRONMENT SUMMARY")
        print("="*80)

        profile = demo_env.client_profile

        print(f"Session ID: {demo_env.session_id}")
        print(f"Scenario: {profile.market_segment.value.replace('_', ' ').title()}")
        print(f"Client: {profile.name} ({profile.agency_name})")
        print(f"Market: {profile.geographic_market}")
        print(f"Experience: {profile.experience_level.title()}")
        print(f"Monthly Leads: {profile.monthly_leads}")
        print(f"Avg Deal Size: ${profile.avg_deal_size:,}")
        print(f"Commission Rate: {profile.commission_rate:.1%}")

        print(f"\nDemo Data Generated:")
        print(f"  • {len(demo_env.demo_leads)} realistic leads")
        print(f"  • {len(demo_env.demo_properties)} property listings")
        print(f"  • {len(demo_env.demo_conversations)} Jorge bot conversations")

        if "summary" in demo_env.roi_calculation:
            summary = demo_env.roi_calculation["summary"]
            print(f"\nROI Analysis:")
            print(f"  • Annual Savings: ${summary.get('net_savings', 0):,}")
            print(f"  • ROI: {summary.get('roi_percentage', 0):.1f}%")
            print(f"  • Payback Period: {summary.get('payback_period_months', 0):.1f} months")
            print(f"  • Cost Reduction: {summary.get('cost_reduction_percentage', 0):.1f}%")

        perf = demo_env.performance_metrics
        if "business_impact" in perf:
            impact = perf["business_impact"]
            print(f"\nBusiness Impact:")
            print(f"  • Revenue Increase: {impact.get('revenue_increase', 'N/A')}")
            print(f"  • Cost Reduction: {impact.get('cost_reduction', 'N/A')}")
            print(f"  • Overall ROI: {impact.get('roi', 'N/A')}")
            print(f"  • Payback Period: {impact.get('payback_period', 'N/A')}")

        print(f"\nExpires: {demo_env.expires_at}")
        print("="*80)


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Jorge AI Platform Demo Environment Seeder')

    parser.add_argument(
        '--scenario',
        choices=[s.value for s in DemoScenario],
        help='Specific scenario to create (creates all if not specified)'
    )

    parser.add_argument(
        '--client-name',
        help='Custom client name for demo'
    )

    parser.add_argument(
        '--agency-name',
        help='Custom agency name for demo'
    )

    parser.add_argument(
        '--export',
        help='Export demo data to JSON file'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing demo environments'
    )

    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up created sessions after completion'
    )

    parser.add_argument(
        '--custom-params',
        help='Custom parameters as JSON string'
    )

    args = parser.parse_args()

    seeder = DemoEnvironmentSeeder()

    try:
        await seeder.initialize()

        # Parse custom parameters if provided
        custom_params = None
        if args.custom_params:
            try:
                custom_params = json.loads(args.custom_params)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in custom-params: {str(e)}")
                sys.exit(1)

        if args.validate_only:
            # Validation mode - would need to load existing sessions
            logger.info("Validation-only mode - feature not yet implemented")
            return

        # Create demo environments
        if args.scenario:
            # Create specific scenario
            demo_env = await seeder.create_specific_scenario(
                args.scenario,
                args.client_name,
                args.agency_name,
                custom_params
            )

            await seeder.print_demo_summary(demo_env)
            validations = await seeder.validate_demo_environment(demo_env)

            if args.export:
                await seeder.export_demo_data(demo_env, args.export)

        else:
            # Create all scenarios
            logger.info("Creating demo environments for all scenarios...")
            demo_environments = await seeder.create_all_scenarios()

            print(f"\n\nCreated {len(demo_environments)} demo environments:")

            for demo_env in demo_environments:
                await seeder.print_demo_summary(demo_env)
                await seeder.validate_demo_environment(demo_env)

                if args.export:
                    scenario = demo_env.client_profile.market_segment.value
                    export_file = f"{Path(args.export).stem}_{scenario}{Path(args.export).suffix}"
                    await seeder.export_demo_data(demo_env, export_file)

        if args.cleanup:
            logger.info("Cleaning up created demo sessions...")
            await seeder.cleanup_created_sessions()

        logger.info("Demo environment seeding completed successfully")

    except Exception as e:
        logger.error(f"Demo seeding failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())