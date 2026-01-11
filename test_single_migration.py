#!/usr/bin/env python3
"""
Test migration for a single component
"""
import sys
import os
from pathlib import Path

# Set up the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from ghl_real_estate_ai.streamlit_components.migration.migration_engine import MigrationEngine, MigrationConfig
    from ghl_real_estate_ai.streamlit_components.migration.component_analyzer import ComponentAnalyzer

    # Test with claude_coaching_widget.py
    components_dir = str(current_dir / 'ghl_real_estate_ai' / 'streamlit_components')
    component_file = 'claude_coaching_widget.py'
    full_component_path = str(current_dir / 'ghl_real_estate_ai' / 'streamlit_components' / component_file)

    config = MigrationConfig(dry_run=False, create_backup=True)

    # First analyze the component
    analyzer = ComponentAnalyzer(components_dir)
    analysis = analyzer.analyze_component(full_component_path)
    print(f"Before migration - Score: {analysis.overall_score}, Status: {analysis.migration_priority}")

    # Run migration
    engine = MigrationEngine(components_dir, config)
    result = engine.migrate_component(component_file, config)

    print(f"\nMigration result:")
    print(f"  Success: {result.success}")
    print(f"  Before score: {result.before_score}")
    print(f"  After score: {result.after_score}")
    print(f"  Changes made: {len(result.changes_made)}")

    for change in result.changes_made:
        print(f"    - {change}")

    if result.errors:
        print(f"  Errors:")
        for error in result.errors:
            print(f"    - {error}")

    if result.warnings:
        print(f"  Warnings:")
        for warning in result.warnings:
            print(f"    - {warning}")

except Exception as e:
    print(f"Error running migration test: {e}")
    import traceback
    traceback.print_exc()