"""
Migration Engine - Automated Component Migration
================================================

Automated migration engine for converting Streamlit components to
enterprise standards with full rollback capability.

Features:
- Automated base class migration
- Theme system integration
- Claude AI integration injection
- Cache integration
- Validation and testing
- Git-based rollback support

Author: EnterpriseHub Development Team
Date: January 2026
Version: 1.0.0
"""

import os
import re
import ast
import shutil
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json

from .component_analyzer import (
    ComponentAnalyzer,
    ComponentAnalysis,
    MigrationStatus,
    BaseClassType,
    ThemeIntegrationLevel,
    ClaudeIntegrationLevel
)

logger = logging.getLogger(__name__)


@dataclass
class MigrationConfig:
    """Configuration for component migration."""

    # Migration options
    migrate_base_class: bool = True
    migrate_theme: bool = True
    integrate_claude: bool = True
    integrate_cache: bool = True

    # Target standards
    target_base_class: str = "EnterpriseDashboardComponent"
    target_theme_level: str = "unified_design_system"
    claude_integration_level: str = "full"

    # Safety options
    create_backup: bool = True
    backup_dir: str = ".migration_backups"
    dry_run: bool = False
    validate_after: bool = True

    # Code generation options
    preserve_docstrings: bool = True
    add_migration_comments: bool = True
    update_imports: bool = True


@dataclass
class MigrationResult:
    """Result of a component migration."""

    file_name: str
    success: bool
    status: MigrationStatus
    changes_made: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    backup_path: Optional[str] = None
    before_score: int = 0
    after_score: int = 0
    migration_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MigrationEngine:
    """
    Automated migration engine for Streamlit components.

    Handles:
    - Base class upgrades
    - Theme integration
    - Claude AI integration
    - Cache optimization
    - Validation and rollback
    """

    # Import templates
    ENTERPRISE_IMPORTS = '''
# === ENTERPRISE BASE IMPORTS ===
from .enhanced_enterprise_base import (
    EnhancedEnterpriseComponent,
    EnterpriseDashboardComponent,
    EnterpriseDataComponent,
    ComponentMetrics,
    ComponentState
)
from .enterprise_theme_system import (
    EnterpriseThemeManager,
    ThemeVariant,
    ComponentType,
    inject_enterprise_theme,
    create_enterprise_card,
    create_enterprise_metric,
    create_enterprise_alert
)
'''

    CLAUDE_IMPORTS = '''
# === CLAUDE AI INTEGRATION ===
from .claude_component_mixin import (
    ClaudeComponentMixin,
    ClaudeOperationType,
    ClaudeServiceStatus,
    create_claude_mixin
)
'''

    CACHE_IMPORTS = '''
# === CACHE INTEGRATION ===
from .streamlit_cache_integration import (
    StreamlitCacheIntegration,
    ComponentCacheConfig,
    ComponentCacheMetrics,
    cached_render
)
'''

    DESIGN_SYSTEM_IMPORTS = '''
# === UNIFIED DESIGN SYSTEM ===
try:
    from ..design_system import (
        enterprise_metric,
        enterprise_card,
        enterprise_badge,
        enterprise_progress_ring,
        enterprise_status_indicator,
        enterprise_kpi_grid,
        enterprise_section_header,
        apply_plotly_theme,
        ENTERPRISE_COLORS
    )
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = False
'''

    def __init__(
        self,
        components_dir: str,
        config: Optional[MigrationConfig] = None
    ):
        """
        Initialize migration engine.

        Args:
            components_dir: Path to streamlit_components directory
            config: Migration configuration
        """
        self.components_dir = Path(components_dir)
        self.config = config or MigrationConfig()
        self.analyzer = ComponentAnalyzer(components_dir)
        self.results: Dict[str, MigrationResult] = {}

        # Create backup directory if needed
        if self.config.create_backup:
            self.backup_dir = self.components_dir / self.config.backup_dir
            self.backup_dir.mkdir(parents=True, exist_ok=True)

    def migrate_component(
        self,
        file_path: str,
        config: Optional[MigrationConfig] = None
    ) -> MigrationResult:
        """
        Migrate a single component to enterprise standards.

        Args:
            file_path: Path to component file
            config: Optional override configuration

        Returns:
            MigrationResult with details
        """
        import time
        start_time = time.time()

        config = config or self.config
        path = Path(file_path)
        file_name = path.name

        result = MigrationResult(
            file_name=file_name,
            success=False,
            status=MigrationStatus.IN_PROGRESS
        )

        try:
            # Analyze current state
            analysis = self.analyzer.analyze_component(str(path))
            result.before_score = analysis.overall_score

            # Create backup
            if config.create_backup and not config.dry_run:
                backup_path = self._create_backup(path)
                result.backup_path = str(backup_path)

            # Read current content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Apply migrations based on config
            if config.migrate_base_class and analysis.base_class_type not in [
                BaseClassType.ENHANCED_ENTERPRISE,
                BaseClassType.ENTERPRISE_DASHBOARD,
                BaseClassType.ENTERPRISE_DATA
            ]:
                content, change = self._migrate_base_class(
                    content, analysis, config.target_base_class
                )
                if change:
                    result.changes_made.append(change)

            if config.migrate_theme and analysis.theme_level not in [
                ThemeIntegrationLevel.UNIFIED_DESIGN_SYSTEM,
                ThemeIntegrationLevel.ENTERPRISE_THEME
            ]:
                content, changes = self._migrate_theme(content, analysis)
                result.changes_made.extend(changes)

            if config.integrate_claude and analysis.claude_level == ClaudeIntegrationLevel.NONE:
                content, change = self._integrate_claude(content, analysis)
                if change:
                    result.changes_made.append(change)

            if config.integrate_cache and not analysis.uses_cache_integration:
                content, change = self._integrate_cache(content, analysis)
                if change:
                    result.changes_made.append(change)

            # Update imports
            if config.update_imports and result.changes_made:
                content = self._update_imports(content, result.changes_made)

            # Add migration comments if requested
            if config.add_migration_comments and result.changes_made:
                content = self._add_migration_header(content, result.changes_made)

            # Write changes (unless dry run)
            if not config.dry_run and content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Validate if requested
            if config.validate_after and not config.dry_run:
                validation = self._validate_migration(path)
                if not validation['valid']:
                    result.errors.extend(validation['errors'])
                    result.warnings.extend(validation['warnings'])
                    result.status = MigrationStatus.FAILED
                    # Rollback
                    if result.backup_path:
                        self._rollback(path, Path(result.backup_path))
                    result.success = False
                    return result

            # Re-analyze to get new score
            if not config.dry_run:
                new_analysis = self.analyzer.analyze_component(str(path))
                result.after_score = new_analysis.overall_score

            result.success = True
            result.status = MigrationStatus.COMPLETED

        except Exception as e:
            logger.error(f"Migration failed for {file_name}: {e}")
            result.errors.append(str(e))
            result.status = MigrationStatus.FAILED
            result.success = False

            # Attempt rollback
            if result.backup_path:
                try:
                    self._rollback(path, Path(result.backup_path))
                    result.warnings.append("Rolled back to backup after error")
                except Exception as rollback_error:
                    result.errors.append(f"Rollback failed: {rollback_error}")

        result.migration_time_ms = (time.time() - start_time) * 1000
        self.results[file_name] = result
        return result

    def migrate_all(
        self,
        priority_filter: Optional[List[str]] = None,
        config: Optional[MigrationConfig] = None
    ) -> Dict[str, MigrationResult]:
        """
        Migrate all components based on priority.

        Args:
            priority_filter: Optional list of priorities to migrate
            config: Optional override configuration

        Returns:
            Dictionary of migration results
        """
        migration_order = self.analyzer.get_migration_order()

        for file_name, analysis in migration_order:
            # Filter by priority if specified
            if priority_filter and analysis.migration_priority not in priority_filter:
                continue

            # Skip if already migrated
            if analysis.overall_score >= 80:
                self.results[file_name] = MigrationResult(
                    file_name=file_name,
                    success=True,
                    status=MigrationStatus.COMPLETED,
                    before_score=analysis.overall_score,
                    after_score=analysis.overall_score,
                    changes_made=["Already meets enterprise standards"]
                )
                continue

            file_path = self.components_dir / file_name
            result = self.migrate_component(str(file_path), config)
            logger.info(
                f"Migrated {file_name}: score {result.before_score} -> {result.after_score}"
            )

        return self.results

    def _create_backup(self, path: Path) -> Path:
        """Create backup of file before migration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_{timestamp}{path.suffix}"
        backup_path = self.backup_dir / backup_name
        shutil.copy2(path, backup_path)
        return backup_path

    def _rollback(self, target: Path, backup: Path) -> None:
        """Rollback migration from backup."""
        shutil.copy2(backup, target)
        logger.info(f"Rolled back {target.name} from backup")

    def _migrate_base_class(
        self,
        content: str,
        analysis: ComponentAnalysis,
        target_class: str
    ) -> Tuple[str, Optional[str]]:
        """Migrate to enterprise base class."""
        if analysis.base_class_type == BaseClassType.NO_BASE:
            # Need to add inheritance
            class_pattern = rf'class\s+{re.escape(analysis.class_name)}\s*:'
            replacement = f'class {analysis.class_name}({target_class}):'

            if re.search(class_pattern, content):
                content = re.sub(class_pattern, replacement, content, count=1)
                return content, f"Added base class: {target_class}"

        elif analysis.base_class_type == BaseClassType.ENTERPRISE_COMPONENT:
            # Upgrade from legacy base
            content = content.replace(
                '(EnterpriseComponent)',
                f'({target_class})'
            )
            return content, f"Upgraded base class from EnterpriseComponent to {target_class}"

        elif analysis.base_class_type == BaseClassType.CLAUDE_MIXIN:
            # Add enterprise base alongside mixin
            content = content.replace(
                '(ClaudeComponentMixin)',
                f'({target_class}, ClaudeComponentMixin)'
            )
            return content, f"Added {target_class} alongside ClaudeComponentMixin"

        return content, None

    def _migrate_theme(
        self,
        content: str,
        analysis: ComponentAnalysis
    ) -> Tuple[str, List[str]]:
        """Migrate theme integration."""
        changes = []

        # Add design system import check if not present
        if 'UNIFIED_DESIGN_SYSTEM_AVAILABLE' not in content:
            # Find first import section
            import_match = re.search(r'^(import\s+|from\s+)', content, re.MULTILINE)
            if import_match:
                insert_pos = content.find('\n', import_match.end()) + 1
                content = (
                    content[:insert_pos] +
                    self.DESIGN_SYSTEM_IMPORTS +
                    content[insert_pos:]
                )
                changes.append("Added unified design system import check")

        # Replace common inline style patterns with enterprise components
        style_replacements = [
            (
                r'st\.markdown\([^)]*<div style="[^"]*background[^"]*"[^)]*\)',
                'enterprise_card(content="...")',
                "Consider replacing inline styled divs with enterprise_card"
            ),
            (
                r'st\.metric\s*\(',
                'enterprise_metric(',
                "Consider using enterprise_metric for consistent styling"
            ),
        ]

        for pattern, replacement, message in style_replacements:
            if re.search(pattern, content):
                changes.append(message)

        return content, changes

    def _integrate_claude(
        self,
        content: str,
        analysis: ComponentAnalysis
    ) -> Tuple[str, Optional[str]]:
        """Integrate Claude AI capabilities."""

        # Check if class already has mixin
        if 'ClaudeComponentMixin' in analysis.base_classes:
            return content, None

        # Add Claude mixin to class inheritance
        class_pattern = rf'class\s+{re.escape(analysis.class_name)}\s*\(([^)]+)\)\s*:'
        match = re.search(class_pattern, content)

        if match:
            current_bases = match.group(1)
            new_bases = f"{current_bases}, ClaudeComponentMixin"
            new_class_def = f'class {analysis.class_name}({new_bases}):'
            content = content[:match.start()] + new_class_def + content[match.end():]

            # Add Claude initialization to __init__
            init_pattern = r'def __init__\s*\([^)]*\)\s*:'
            init_match = re.search(init_pattern, content)

            if init_match:
                # Find the line after super().__init__
                super_pattern = r'super\(\).__init__\([^)]*\)'
                super_match = re.search(super_pattern, content[init_match.end():])

                if super_match:
                    insert_pos = init_match.end() + super_match.end()
                    claude_init = '''

        # Initialize Claude AI integration
        ClaudeComponentMixin.__init__(
            self,
            enable_claude_caching=True,
            cache_ttl_seconds=300,
            enable_performance_monitoring=True,
            demo_mode=False
        )
'''
                    content = content[:insert_pos] + claude_init + content[insert_pos:]

            return content, "Added ClaudeComponentMixin integration"

        return content, None

    def _integrate_cache(
        self,
        content: str,
        analysis: ComponentAnalysis
    ) -> Tuple[str, Optional[str]]:
        """Integrate cache optimization."""

        # Add cache integration import
        if 'StreamlitCacheIntegration' not in content:
            # Find import section
            import_end = self._find_import_section_end(content)
            content = (
                content[:import_end] +
                self.CACHE_IMPORTS +
                content[import_end:]
            )

            # Add cache initialization to __init__
            init_pattern = r'def __init__\s*\([^)]*\)\s*:'
            init_match = re.search(init_pattern, content)

            if init_match:
                # Find end of __init__ method (next method definition or class-level code)
                method_body_start = init_match.end()
                next_def = re.search(r'\n    def ', content[method_body_start:])
                insert_pos = method_body_start + (next_def.start() if next_def else 100)

                cache_init = '''

        # Initialize cache integration for performance optimization
        self.cache = StreamlitCacheIntegration(
            component_id=self.component_id if hasattr(self, 'component_id') else self.__class__.__name__,
            config=ComponentCacheConfig(
                component_id=self.__class__.__name__,
                enable_l1_cache=True,
                enable_l2_cache=True,
                enable_predictive=True,
                default_ttl_seconds=300
            )
        )
'''
                # Find a suitable place to insert (after super().__init__)
                super_match = re.search(r'super\(\).__init__\([^)]*\)\n', content)
                if super_match:
                    insert_pos = super_match.end()
                    content = content[:insert_pos] + cache_init + content[insert_pos:]

            return content, "Added StreamlitCacheIntegration"

        return content, None

    def _find_import_section_end(self, content: str) -> int:
        """Find the end of the import section."""
        lines = content.split('\n')
        last_import_line = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                last_import_line = i
            elif stripped and not stripped.startswith('#') and last_import_line > 0:
                # Found first non-import, non-comment line
                break

        # Return position after last import line
        return sum(len(lines[j]) + 1 for j in range(last_import_line + 1))

    def _update_imports(self, content: str, changes: List[str]) -> str:
        """Update imports based on changes made."""
        imports_to_add = []

        for change in changes:
            if 'EnterpriseDashboardComponent' in change:
                imports_to_add.append(self.ENTERPRISE_IMPORTS)
            if 'ClaudeComponentMixin' in change:
                imports_to_add.append(self.CLAUDE_IMPORTS)
            if 'StreamlitCacheIntegration' in change:
                imports_to_add.append(self.CACHE_IMPORTS)

        if imports_to_add:
            # Remove duplicates and add
            unique_imports = list(set(imports_to_add))
            import_end = self._find_import_section_end(content)

            for imp in unique_imports:
                if imp.strip() not in content:
                    content = content[:import_end] + imp + '\n' + content[import_end:]
                    import_end += len(imp) + 1

        return content

    def _add_migration_header(self, content: str, changes: List[str]) -> str:
        """Add migration documentation header."""
        header = f'''
# ============================================================================
# MIGRATION NOTES (Automated Migration - {datetime.now().strftime("%Y-%m-%d")})
# ============================================================================
# Changes Applied:
# {chr(10).join(f"# - {change}" for change in changes)}
#
# This component has been migrated to enterprise standards.
# See migration documentation for details.
# ============================================================================

'''
        # Insert after docstring if present
        docstring_match = re.search(r'^"""[\s\S]*?"""', content)
        if docstring_match:
            insert_pos = docstring_match.end()
            content = content[:insert_pos] + '\n' + header + content[insert_pos:]
        else:
            content = header + content

        return content

    def _validate_migration(self, path: Path) -> Dict[str, Any]:
        """Validate migrated component."""
        errors = []
        warnings = []

        try:
            # Try to parse the file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            ast.parse(content)

            # Check for common issues
            if 'import' not in content[:500]:
                warnings.append("No imports found in first 500 characters")

            if 'def render' not in content and 'def main' not in content:
                warnings.append("No render or main method found")

            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }

        except SyntaxError as e:
            errors.append(f"Syntax error after migration: {e}")
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }

    def generate_migration_summary(self) -> Dict[str, Any]:
        """Generate summary of all migrations."""
        successful = sum(1 for r in self.results.values() if r.success)
        failed = sum(1 for r in self.results.values() if not r.success)

        total_score_improvement = sum(
            r.after_score - r.before_score
            for r in self.results.values()
            if r.success
        )

        avg_improvement = total_score_improvement / successful if successful else 0

        return {
            'total_components': len(self.results),
            'successful_migrations': successful,
            'failed_migrations': failed,
            'success_rate': round(successful / len(self.results) * 100, 1) if self.results else 0,
            'total_score_improvement': total_score_improvement,
            'average_score_improvement': round(avg_improvement, 1),
            'total_migration_time_ms': sum(r.migration_time_ms for r in self.results.values()),
            'results': {
                name: {
                    'success': r.success,
                    'before_score': r.before_score,
                    'after_score': r.after_score,
                    'changes': r.changes_made,
                    'errors': r.errors
                }
                for name, r in self.results.items()
            },
            'timestamp': datetime.now().isoformat()
        }
