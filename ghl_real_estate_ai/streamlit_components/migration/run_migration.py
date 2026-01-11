#!/usr/bin/env python3
"""
Component Migration CLI Runner
==============================

Command-line interface for running component analysis, migration, and validation.

Usage:
    python run_migration.py analyze              # Analyze all components
    python run_migration.py migrate --priority high   # Migrate high priority components
    python run_migration.py validate             # Validate all components
    python run_migration.py report               # Generate full migration report

Author: EnterpriseHub Development Team
Date: January 2026
Version: 1.0.0
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

# Add parent directories to path for imports
script_dir = Path(__file__).parent
streamlit_dir = script_dir.parent
ghl_dir = streamlit_dir.parent
sys.path.insert(0, str(ghl_dir.parent))

from ghl_real_estate_ai.streamlit_components.migration.component_analyzer import (
    ComponentAnalyzer,
    MigrationStatus
)
from ghl_real_estate_ai.streamlit_components.migration.migration_engine import (
    MigrationEngine,
    MigrationConfig
)
from ghl_real_estate_ai.streamlit_components.migration.theme_migrator import ThemeMigrator
from ghl_real_estate_ai.streamlit_components.migration.validation_suite import ValidationSuite

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_components_dir() -> str:
    """Get the streamlit_components directory path."""
    return str(streamlit_dir)


def analyze_components(args) -> None:
    """Analyze all components and generate report."""
    print("\n" + "=" * 60)
    print(" COMPONENT ANALYSIS")
    print("=" * 60)

    analyzer = ComponentAnalyzer(get_components_dir())
    analyses = analyzer.analyze_all_components()

    print(f"\nAnalyzed {len(analyses)} components\n")

    # Summary table
    print("-" * 80)
    print(f"{'Component':<45} {'Score':>6} {'Priority':>10} {'Claude':>10}")
    print("-" * 80)

    sorted_analyses = sorted(
        analyses.items(),
        key=lambda x: x[1].overall_score
    )

    for name, analysis in sorted_analyses:
        print(f"{name:<45} {analysis.overall_score:>6} {analysis.migration_priority:>10} {analysis.claude_level.value:>10}")

    print("-" * 80)

    # Generate report
    report = analyzer.generate_migration_report()

    print(f"\n{'Summary Statistics':^60}")
    print("-" * 60)
    print(f"  Total Components:           {report['summary']['total_components']}")
    print(f"  Average Score:              {report['summary']['average_score']:.1f}")
    print(f"  Components Needing Work:    {report['summary']['components_needing_migration']}")
    print(f"  Migration Percentage:       {report['summary']['migration_percentage']:.1f}%")

    print(f"\n{'Base Class Distribution':^60}")
    print("-" * 60)
    for base_type, count in report['base_class_distribution'].items():
        pct = count / report['summary']['total_components'] * 100
        print(f"  {base_type:<30} {count:>5} ({pct:.1f}%)")

    print(f"\n{'Claude Integration Distribution':^60}")
    print("-" * 60)
    for claude_type, count in report['claude_distribution'].items():
        pct = count / report['summary']['total_components'] * 100
        print(f"  {claude_type:<30} {count:>5} ({pct:.1f}%)")

    print(f"\n{'Theme Distribution':^60}")
    print("-" * 60)
    for theme_type, count in report['theme_distribution'].items():
        pct = count / report['summary']['total_components'] * 100
        print(f"  {theme_type:<30} {count:>5} ({pct:.1f}%)")

    print(f"\n{'Priority Breakdown':^60}")
    print("-" * 60)
    for priority, count in report['priority_breakdown'].items():
        pct = count / report['summary']['total_components'] * 100
        print(f"  {priority:<30} {count:>5} ({pct:.1f}%)")

    # Save report
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {args.output}")


def migrate_components(args) -> None:
    """Run component migration."""
    print("\n" + "=" * 60)
    print(" COMPONENT MIGRATION")
    print("=" * 60)

    config = MigrationConfig(
        migrate_base_class=not args.skip_base,
        migrate_theme=not args.skip_theme,
        integrate_claude=not args.skip_claude,
        integrate_cache=not args.skip_cache,
        dry_run=args.dry_run,
        create_backup=not args.no_backup
    )

    engine = MigrationEngine(get_components_dir(), config)

    # Filter by priority if specified
    priority_filter = None
    if args.priority:
        priority_filter = [args.priority]

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]\n")

    # Run migration
    results = engine.migrate_all(priority_filter=priority_filter, config=config)

    # Print results
    print("\n" + "-" * 80)
    print(f"{'Component':<40} {'Status':>10} {'Before':>8} {'After':>8} {'Changes':>8}")
    print("-" * 80)

    for name, result in results.items():
        status = "SUCCESS" if result.success else "FAILED"
        print(f"{name:<40} {status:>10} {result.before_score:>8} {result.after_score:>8} {len(result.changes_made):>8}")

        if result.errors:
            for error in result.errors:
                print(f"    ERROR: {error}")
        if args.verbose and result.changes_made:
            for change in result.changes_made:
                print(f"    - {change}")

    # Summary
    summary = engine.generate_migration_summary()
    print("\n" + "-" * 60)
    print(f"{'Migration Summary':^60}")
    print("-" * 60)
    print(f"  Total Components:        {summary['total_components']}")
    print(f"  Successful Migrations:   {summary['successful_migrations']}")
    print(f"  Failed Migrations:       {summary['failed_migrations']}")
    print(f"  Success Rate:            {summary['success_rate']:.1f}%")
    print(f"  Score Improvement:       +{summary['total_score_improvement']} points")
    print(f"  Avg Improvement:         +{summary['average_score_improvement']:.1f} per component")
    print(f"  Total Time:              {summary['total_migration_time_ms']/1000:.2f}s")


def validate_components(args) -> None:
    """Validate all components."""
    print("\n" + "=" * 60)
    print(" COMPONENT VALIDATION")
    print("=" * 60)

    suite = ValidationSuite(get_components_dir())

    # Select validation types
    validation_types = None
    if args.types:
        validation_types = args.types.split(',')

    # Run validation
    results = suite.validate_all_components(validation_types)

    # Print results by component
    print("\n" + "-" * 80)
    print(f"{'Component':<40} {'Syntax':>8} {'Imports':>8} {'Theme':>8} {'Claude':>8}")
    print("-" * 80)

    for name, val_results in results.items():
        scores = {r.validation_type: r.score for r in val_results}
        print(f"{name:<40} {scores.get('syntax', '-'):>8} {scores.get('imports', '-'):>8} {scores.get('theme', '-'):>8} {scores.get('claude', '-'):>8}")

    # Generate report
    report = suite.generate_validation_report()

    print("\n" + "-" * 60)
    print(f"{'Validation Summary':^60}")
    print("-" * 60)
    print(f"  Total Components:     {report['summary']['total_components']}")
    print(f"  Total Validations:    {report['summary']['total_validations']}")
    print(f"  Overall Pass Rate:    {report['summary']['overall_pass_rate']:.1f}%")
    print(f"  Average Score:        {report['summary']['average_score']:.1f}")

    if report['components_needing_attention']:
        print(f"\n{'Components Needing Attention':^60}")
        print("-" * 60)
        for comp in report['components_needing_attention']:
            print(f"  {comp['component']}: score {comp['avg_score']:.1f} - issues: {', '.join(comp['issues'])}")


def generate_report(args) -> None:
    """Generate comprehensive migration report."""
    print("\n" + "=" * 60)
    print(" COMPREHENSIVE MIGRATION REPORT")
    print("=" * 60)

    # Run analysis
    analyzer = ComponentAnalyzer(get_components_dir())
    analysis_report = analyzer.generate_migration_report()

    # Run theme analysis
    theme_migrator = ThemeMigrator()
    theme_report = theme_migrator.generate_style_guide_compliance_report(get_components_dir())

    # Run validation
    suite = ValidationSuite(get_components_dir())
    suite.validate_all_components()
    validation_report = suite.generate_validation_report()

    # Combine reports
    full_report = {
        'generated_at': datetime.now().isoformat(),
        'component_analysis': analysis_report,
        'theme_compliance': theme_report,
        'validation_results': validation_report,
        'recommendations': []
    }

    # Generate recommendations
    if analysis_report['summary']['migration_percentage'] > 50:
        full_report['recommendations'].append(
            f"High migration need: {analysis_report['summary']['migration_percentage']:.0f}% of components require migration"
        )

    if theme_report.get('design_system_adoption', 0) < 50:
        full_report['recommendations'].append(
            f"Low design system adoption: Only {theme_report.get('design_system_adoption', 0):.0f}% use unified design system"
        )

    claude_none = analysis_report['claude_distribution'].get('none', 0)
    if claude_none > analysis_report['summary']['total_components'] / 2:
        full_report['recommendations'].append(
            f"Claude integration opportunity: {claude_none} components lack Claude AI integration"
        )

    # Print summary
    print(f"\n{'Executive Summary':^60}")
    print("=" * 60)

    print("\n[Component Analysis]")
    print(f"  - {analysis_report['summary']['total_components']} total components analyzed")
    print(f"  - Average enterprise compliance score: {analysis_report['summary']['average_score']:.1f}/100")
    print(f"  - {analysis_report['summary']['components_needing_migration']} components need migration")

    print("\n[Theme Compliance]")
    print(f"  - Design system adoption: {theme_report.get('design_system_adoption', 0):.1f}%")
    print(f"  - Enterprise theme adoption: {theme_report.get('enterprise_theme_adoption', 0):.1f}%")
    print(f"  - Components needing theme migration: {theme_report.get('needs_migration', 0)}")

    print("\n[Validation Results]")
    print(f"  - Overall pass rate: {validation_report['summary']['overall_pass_rate']:.1f}%")
    print(f"  - Average validation score: {validation_report['summary']['average_score']:.1f}/100")
    print(f"  - Components needing attention: {len(validation_report['components_needing_attention'])}")

    print("\n[Recommendations]")
    for i, rec in enumerate(full_report['recommendations'], 1):
        print(f"  {i}. {rec}")

    # High value components
    high_value = analysis_report.get('high_value_components', [])
    if high_value:
        print(f"\n[Priority Migration Targets - High Business Value]")
        for comp in high_value[:10]:
            print(f"  - {comp}")

    # Save report
    output_file = args.output or f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(full_report, f, indent=2)

    print(f"\nFull report saved to: {output_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='EnterpriseHub Component Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_migration.py analyze
  python run_migration.py analyze --output analysis.json
  python run_migration.py migrate --priority high --dry-run
  python run_migration.py migrate --skip-claude --skip-cache
  python run_migration.py validate --types syntax,imports
  python run_migration.py report
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze components')
    analyze_parser.add_argument('--output', '-o', help='Output file for report')
    analyze_parser.set_defaults(func=analyze_components)

    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate components')
    migrate_parser.add_argument('--priority', choices=['critical', 'high', 'medium', 'low'],
                                help='Only migrate components with this priority')
    migrate_parser.add_argument('--dry-run', action='store_true',
                                help='Simulate migration without making changes')
    migrate_parser.add_argument('--no-backup', action='store_true',
                                help='Skip creating backups')
    migrate_parser.add_argument('--skip-base', action='store_true',
                                help='Skip base class migration')
    migrate_parser.add_argument('--skip-theme', action='store_true',
                                help='Skip theme migration')
    migrate_parser.add_argument('--skip-claude', action='store_true',
                                help='Skip Claude integration')
    migrate_parser.add_argument('--skip-cache', action='store_true',
                                help='Skip cache integration')
    migrate_parser.add_argument('--verbose', '-v', action='store_true',
                                help='Show detailed changes')
    migrate_parser.set_defaults(func=migrate_components)

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate components')
    validate_parser.add_argument('--types', help='Comma-separated validation types')
    validate_parser.add_argument('--output', '-o', help='Output file for report')
    validate_parser.set_defaults(func=validate_components)

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate full migration report')
    report_parser.add_argument('--output', '-o', help='Output file for report')
    report_parser.set_defaults(func=generate_report)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == '__main__':
    main()
