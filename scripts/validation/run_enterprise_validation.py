#!/usr/bin/env python3
"""
Enterprise Scale Validation Runner for EnterpriseHub
Comprehensive validation of all Phase 4 enterprise targets
Validates 1000+ concurrent users, 99.95% uptime, ROI targets, and performance
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
import logging
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.validation.enterprise_scale_validator import get_enterprise_validator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_full_validation(output_file: str = None) -> int:
    """Run comprehensive enterprise scale validation."""
    logger.info("Starting comprehensive enterprise scale validation...")

    try:
        validator = get_enterprise_validator()
        validation_report = await validator.run_comprehensive_validation()

        # Print results
        validator.print_validation_summary()

        # Export if requested
        if output_file:
            success = await validator.export_validation_report(output_file)
            if success:
                logger.info(f"Validation report exported to: {output_file}")
            else:
                logger.error("Failed to export validation report")

        # Return exit code based on validation result
        if validation_report.overall_result.value == "PASS":
            logger.info("✓ All enterprise scale targets PASSED validation")
            return 0
        elif validation_report.overall_result.value == "WARNING":
            logger.warning("⚠ Enterprise scale validation completed with WARNINGS")
            return 0
        else:
            logger.error("✗ Enterprise scale validation FAILED")
            return 1

    except Exception as e:
        logger.error(f"Error during validation: {e}")
        return 1

async def run_specific_tests(test_ids: List[str], output_file: str = None) -> int:
    """Run specific validation tests."""
    logger.info(f"Running specific validation tests: {', '.join(test_ids)}")

    try:
        validator = get_enterprise_validator()

        # Filter test cases to run only specified tests
        original_test_cases = validator.test_cases
        validator.test_cases = [tc for tc in original_test_cases if tc.test_id in test_ids]

        if not validator.test_cases:
            logger.error(f"No matching test cases found for: {test_ids}")
            return 1

        validation_report = await validator.run_comprehensive_validation()

        # Restore original test cases
        validator.test_cases = original_test_cases

        # Print results
        validator.print_validation_summary()

        # Export if requested
        if output_file:
            await validator.export_validation_report(output_file)

        return 0 if validation_report.overall_result.value != "FAIL" else 1

    except Exception as e:
        logger.error(f"Error during specific test validation: {e}")
        return 1

def list_available_tests() -> None:
    """List all available validation tests."""
    validator = get_enterprise_validator()

    print("\nAvailable Validation Tests:")
    print("="*60)

    categories = {}
    for test_case in validator.test_cases:
        category = test_case.target.category
        if category not in categories:
            categories[category] = []
        categories[category].append(test_case)

    for category, tests in categories.items():
        print(f"\n{category.upper()} TESTS:")
        print("-" * 30)
        for test in tests:
            critical_marker = " [CRITICAL]" if test.target.critical else ""
            print(f"  {test.test_id}: {test.name}{critical_marker}")
            print(f"    Target: {test.target.comparison} {test.target.target_value} {test.target.unit}")
            print(f"    Description: {test.description}")
            print()

async def validate_readiness_for_production() -> int:
    """Special validation mode for production readiness."""
    logger.info("Validating production readiness...")

    try:
        validator = get_enterprise_validator()

        # Run only critical tests
        critical_test_cases = [tc for tc in validator.test_cases if tc.target.critical]
        original_test_cases = validator.test_cases
        validator.test_cases = critical_test_cases

        validation_report = await validator.run_comprehensive_validation()

        # Restore original test cases
        validator.test_cases = original_test_cases

        print("\n" + "="*80)
        print("PRODUCTION READINESS ASSESSMENT")
        print("="*80)

        if validation_report.overall_result.value == "PASS":
            print("✓ PRODUCTION READY")
            print("All critical enterprise targets validated successfully.")
            print("System meets enterprise scale requirements for production deployment.")
        elif validation_report.overall_result.value == "WARNING":
            print("⚠ PRODUCTION READY WITH MONITORING")
            print("Critical targets met but some performance warnings detected.")
            print("Production deployment approved with enhanced monitoring.")
        else:
            print("✗ NOT PRODUCTION READY")
            print("Critical enterprise targets not met.")
            print("Address critical issues before production deployment.")

        if validation_report.recommendations:
            print("\nRecommendations:")
            for rec in validation_report.recommendations:
                print(f"  • {rec}")

        print("="*80)

        return 0 if validation_report.overall_result.value != "FAIL" else 1

    except Exception as e:
        logger.error(f"Error during production readiness validation: {e}")
        return 1

async def generate_performance_report() -> int:
    """Generate detailed performance report."""
    logger.info("Generating comprehensive performance report...")

    try:
        validator = get_enterprise_validator()
        validation_report = await validator.run_comprehensive_validation()

        # Generate detailed performance analysis
        print("\n" + "="*80)
        print("ENTERPRISEHUB PERFORMANCE ANALYSIS REPORT")
        print("="*80)

        # Enterprise targets achievement
        targets_met = 0
        targets_total = len([tc for tc in validator.test_cases if tc.target.critical])

        for result in validation_report.test_results:
            test_case = next(tc for tc in validator.test_cases if tc.test_id == result.test_id)
            if test_case.target.critical and result.result.value == "PASS":
                targets_met += 1

        achievement_rate = (targets_met / targets_total) * 100

        print(f"Enterprise Targets Achievement: {targets_met}/{targets_total} ({achievement_rate:.1f}%)")
        print(f"Enterprise Readiness Score: {validation_report.summary.get('enterprise_readiness_score', 0):.1f}/100")

        # Detailed results by category
        print(f"\nDetailed Results by Category:")
        categories = validation_report.summary.get('categories', {})

        for category, stats in categories.items():
            success_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"\n{category.upper()}:")
            print(f"  Success Rate: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")

            # Show individual test results for this category
            category_results = [
                r for r in validation_report.test_results
                if any(tc.target.category == category for tc in validator.test_cases if tc.test_id == r.test_id)
            ]

            for result in category_results:
                status_icon = "✓" if result.result.value == "PASS" else "⚠" if result.result.value == "WARNING" else "✗"
                measured_str = f"{result.measured_value:.3f}" if result.measured_value is not None else "N/A"
                print(f"    {status_icon} {result.name}: {measured_str} {result.unit}")

        # Performance highlights
        if validation_report.summary.get('performance_highlights'):
            print(f"\nPerformance Highlights:")
            for highlight in validation_report.summary['performance_highlights']:
                print(f"  🏆 {highlight}")

        # Business impact summary
        print(f"\nBusiness Impact Summary:")

        # ROI calculation
        roi_results = [r for r in validation_report.test_results if 'roi' in r.test_id]
        if roi_results:
            max_roi = max(r.measured_value for r in roi_results if r.measured_value)
            print(f"  Annual ROI Achievement: ${max_roi:,.0f}")

        # Cost optimization
        cost_result = next((r for r in validation_report.test_results if r.test_id == "cost_optimization_test"), None)
        if cost_result and cost_result.measured_value:
            cost_savings_percent = cost_result.measured_value * 100
            print(f"  Cost Reduction: {cost_savings_percent:.1f}%")

        # Productivity gains
        productivity_result = next((r for r in validation_report.test_results if r.test_id == "agent_productivity_test"), None)
        if productivity_result and productivity_result.measured_value:
            productivity_gain = productivity_result.measured_value * 100
            print(f"  Agent Productivity Increase: {productivity_gain:.1f}%")

        # Training efficiency
        training_result = next((r for r in validation_report.test_results if r.test_id == "training_time_reduction_test"), None)
        if training_result and training_result.measured_value:
            training_improvement = training_result.measured_value * 100
            print(f"  Training Time Reduction: {training_improvement:.1f}%")

        print("="*80)

        return 0

    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        return 1

async def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='EnterpriseHub Enterprise Scale Validation')

    subparsers = parser.add_subparsers(dest='command', help='Validation commands')

    # Full validation command
    full_parser = subparsers.add_parser('full', help='Run comprehensive enterprise validation')
    full_parser.add_argument('--output', help='Output file path for validation report')

    # Specific tests command
    test_parser = subparsers.add_parser('test', help='Run specific validation tests')
    test_parser.add_argument('tests', nargs='+', help='Test IDs to run')
    test_parser.add_argument('--output', help='Output file path for validation report')

    # List tests command
    subparsers.add_parser('list', help='List available validation tests')

    # Production readiness command
    prod_parser = subparsers.add_parser('production', help='Validate production readiness (critical tests only)')

    # Performance report command
    subparsers.add_parser('performance', help='Generate detailed performance report')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == 'full':
            return await run_full_validation(args.output)

        elif args.command == 'test':
            return await run_specific_tests(args.tests, args.output)

        elif args.command == 'list':
            list_available_tests()
            return 0

        elif args.command == 'production':
            return await validate_readiness_for_production()

        elif args.command == 'performance':
            return await generate_performance_report()

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        logger.info("Validation cancelled by user")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    print(f"\n{'='*60}")
    if exit_code == 0:
        print("✓ VALIDATION COMPLETED SUCCESSFULLY")
        print("EnterpriseHub meets enterprise scale requirements")
    else:
        print("✗ VALIDATION FAILED")
        print("Address identified issues before production deployment")
    print(f"{'='*60}")
    sys.exit(exit_code)