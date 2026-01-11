#!/usr/bin/env python3
"""
Test migration using the working CLI approach on a single component
"""
import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_single_component_migration():
    """Test migration on a single component using CLI approach."""

    # Set up paths
    project_root = Path.cwd()
    components_dir = project_root / 'ghl_real_estate_ai' / 'streamlit_components'

    # Target component for testing - choose a small one
    target_component = 'claude_coaching_widget.py'
    component_path = components_dir / target_component

    if not component_path.exists():
        print(f"Component not found: {component_path}")
        return False

    print(f"Testing migration on: {target_component}")
    print(f"Component size: {component_path.stat().st_size} bytes")

    # Create backup
    backup_path = components_dir / f'{target_component}.pre_migration_backup'
    shutil.copy2(component_path, backup_path)
    print(f"Created backup: {backup_path.name}")

    # Create temporary component list with just our target
    temp_dir = tempfile.mkdtemp()
    temp_component_path = Path(temp_dir) / target_component
    shutil.copy2(component_path, temp_component_path)

    print(f"Temp directory: {temp_dir}")

    try:
        # Change to project root and set up Python path
        os.chdir(project_root)
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root)

        # Run migration on the temporary component
        cmd = [
            sys.executable, '-m',
            'ghl_real_estate_ai.streamlit_components.migration.run_migration',
            'migrate',
            '--priority', 'critical',
            '--skip-claude',    # Skip Claude integration to reduce complexity
            '--skip-cache',     # Skip cache integration to reduce complexity
            '--verbose'
        ]

        print(f"Running command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"Return code: {result.returncode}")

        if result.returncode == 0:
            print("✅ Migration command completed successfully")
        else:
            print("❌ Migration command failed")

        # Check if the original file was modified
        if component_path.stat().st_mtime > backup_path.stat().st_mtime:
            print("✅ Original component file was modified")

            # Show first few lines of changes
            print("\nFirst few lines of migrated file:")
            with open(component_path, 'r') as f:
                for i, line in enumerate(f):
                    print(f"{i+1:3d}: {line.rstrip()}")
                    if i >= 20:  # Show first 20 lines
                        print("...")
                        break
        else:
            print("⚠️  Original component file was not modified")

    except subprocess.TimeoutExpired:
        print("❌ Migration command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)

    return result.returncode == 0

if __name__ == '__main__':
    success = run_single_component_migration()
    print(f"\nMigration test {'PASSED' if success else 'FAILED'}")