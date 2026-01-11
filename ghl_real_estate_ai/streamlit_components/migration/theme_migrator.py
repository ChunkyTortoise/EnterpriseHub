"""
Theme Migrator - Unified Design System Migration
=================================================

Migrates legacy CSS and inline styles to the unified enterprise design system.

Features:
- Inline CSS detection and replacement
- Theme variable conversion
- Component styling standardization
- Accessibility improvements
- Responsive design updates

Author: EnterpriseHub Development Team
Date: January 2026
Version: 1.0.0
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ThemeMigrationResult:
    """Result of theme migration."""
    file_name: str
    success: bool
    css_lines_removed: int = 0
    inline_styles_replaced: int = 0
    theme_variables_added: int = 0
    design_system_calls_added: int = 0
    changes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ThemeMigrator:
    """
    Migrates component styling to unified enterprise design system.

    Handles:
    - Inline <style> blocks
    - style="" attributes
    - Legacy color values
    - Non-standard typography
    - Inconsistent spacing
    """

    # Color mapping from legacy to enterprise
    COLOR_MAPPINGS = {
        # Navy/Blue variants
        '#1e3a8a': 'var(--enterprise-primary-navy)',
        '#1a365d': 'var(--enterprise-primary-navy)',
        '#2563eb': 'var(--enterprise-info)',
        '#1e40af': 'var(--enterprise-info)',

        # Gold/Yellow variants
        '#d4af37': 'var(--enterprise-primary-gold)',
        '#b7791f': 'var(--enterprise-primary-gold)',
        '#f59e0b': 'var(--enterprise-warning)',
        '#d97706': 'var(--enterprise-warning)',

        # Green variants
        '#10b981': 'var(--enterprise-success)',
        '#047857': 'var(--enterprise-success)',
        '#22c55e': 'var(--enterprise-success)',

        # Red variants
        '#ef4444': 'var(--enterprise-danger)',
        '#b91c1c': 'var(--enterprise-danger)',
        '#dc2626': 'var(--enterprise-danger)',

        # Gray variants
        '#0f172a': 'var(--enterprise-charcoal-primary)',
        '#1e293b': 'var(--enterprise-charcoal-secondary)',
        '#475569': 'var(--enterprise-slate-primary)',
        '#64748b': 'var(--enterprise-slate-secondary)',
        '#94a3b8': 'var(--enterprise-slate-light)',
        '#f1f5f9': 'var(--enterprise-bg-secondary)',
        '#f8fafc': 'var(--enterprise-bg-primary)',
    }

    # Typography mappings
    TYPOGRAPHY_MAPPINGS = {
        'font-size: 12px': 'font-size: var(--enterprise-text-xs)',
        'font-size: 14px': 'font-size: var(--enterprise-text-sm)',
        'font-size: 16px': 'font-size: var(--enterprise-text-base)',
        'font-size: 18px': 'font-size: var(--enterprise-text-lg)',
        'font-size: 20px': 'font-size: var(--enterprise-text-xl)',
        'font-size: 24px': 'font-size: var(--enterprise-text-2xl)',
        'font-size: 30px': 'font-size: var(--enterprise-text-3xl)',
        'font-size: 36px': 'font-size: var(--enterprise-text-4xl)',

        '0.75rem': 'var(--enterprise-text-xs)',
        '0.875rem': 'var(--enterprise-text-sm)',
        '1rem': 'var(--enterprise-text-base)',
        '1.125rem': 'var(--enterprise-text-lg)',
        '1.25rem': 'var(--enterprise-text-xl)',
        '1.5rem': 'var(--enterprise-text-2xl)',
    }

    # Spacing mappings
    SPACING_MAPPINGS = {
        '4px': 'var(--enterprise-space-2)',
        '8px': 'var(--enterprise-space-4)',
        '12px': 'var(--enterprise-space-6)',
        '16px': 'var(--enterprise-space-8)',
        '20px': 'var(--enterprise-space-10)',
        '24px': 'var(--enterprise-space-12)',
        '32px': 'var(--enterprise-space-16)',
        '40px': 'var(--enterprise-space-20)',
        '48px': 'var(--enterprise-space-24)',
    }

    # Border radius mappings
    RADIUS_MAPPINGS = {
        'border-radius: 4px': 'border-radius: var(--enterprise-radius-sm)',
        'border-radius: 8px': 'border-radius: var(--enterprise-radius-md)',
        'border-radius: 12px': 'border-radius: var(--enterprise-radius-lg)',
        'border-radius: 16px': 'border-radius: var(--enterprise-radius-xl)',
        'border-radius: 9999px': 'border-radius: var(--enterprise-radius-full)',
    }

    # Shadow mappings
    SHADOW_MAPPINGS = {
        'box-shadow: 0 1px 3px': 'box-shadow: var(--enterprise-shadow-card)',
        'box-shadow: 0 4px 6px': 'box-shadow: var(--enterprise-shadow-card-lg)',
        'box-shadow: 0 10px 15px': 'box-shadow: var(--enterprise-shadow-card-xl)',
    }

    # Component replacement patterns
    COMPONENT_PATTERNS = {
        # st.metric -> enterprise_metric
        r'st\.metric\s*\(\s*label\s*=\s*["\']([^"\']+)["\']\s*,\s*value\s*=\s*([^,]+)':
            'enterprise_metric(title="\\1", value=str(\\2))',

        # Simple div with background -> enterprise_card
        r'<div\s+style="[^"]*background[^"]*padding[^"]*border-radius[^"]*">':
            'enterprise_card(content="""',
    }

    def __init__(self):
        """Initialize theme migrator."""
        self.design_system_import = '''
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

    def migrate_component(self, file_path: str) -> ThemeMigrationResult:
        """
        Migrate a component's styling to enterprise design system.

        Args:
            file_path: Path to component file

        Returns:
            ThemeMigrationResult with details
        """
        path = Path(file_path)
        result = ThemeMigrationResult(file_name=path.name, success=False)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # 1. Replace inline style blocks
            content, style_changes = self._migrate_style_blocks(content)
            result.css_lines_removed += style_changes

            # 2. Replace style attributes
            content, attr_changes = self._migrate_style_attributes(content)
            result.inline_styles_replaced += attr_changes

            # 3. Replace color values
            content, color_changes = self._migrate_colors(content)
            result.changes.extend(color_changes)

            # 4. Replace typography
            content, typo_changes = self._migrate_typography(content)
            result.changes.extend(typo_changes)

            # 5. Replace spacing
            content, space_changes = self._migrate_spacing(content)
            result.changes.extend(space_changes)

            # 6. Add design system import if needed
            if content != original_content:
                content = self._ensure_design_system_import(content)
                result.theme_variables_added += 1

            # Write if changed
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                result.success = True
            else:
                result.success = True
                result.changes.append("No theme changes needed")

        except Exception as e:
            logger.error(f"Theme migration failed for {path.name}: {e}")
            result.warnings.append(str(e))

        return result

    def _migrate_style_blocks(self, content: str) -> Tuple[str, int]:
        """Remove inline style blocks and replace with theme references."""
        # Find <style>...</style> blocks
        style_pattern = r'st\.markdown\s*\(\s*["\']<style>[\s\S]*?</style>["\']\s*,\s*unsafe_allow_html\s*=\s*True\s*\)'

        matches = list(re.finditer(style_pattern, content))
        lines_removed = 0

        for match in reversed(matches):
            style_content = match.group(0)
            style_lines = style_content.count('\n') + 1
            lines_removed += style_lines

            # Check if this is a critical style block
            if 'enterprise' in style_content.lower() or '@keyframes' in style_content:
                continue  # Keep enterprise theme blocks

            # Replace with comment referencing theme system
            replacement = '''
# NOTE: Inline styles migrated to enterprise theme system
# Use enterprise_card, enterprise_metric, etc. for consistent styling
# Original styles available in .migration_backups/ if needed
'''
            content = content[:match.start()] + replacement + content[match.end():]

        return content, lines_removed

    def _migrate_style_attributes(self, content: str) -> Tuple[str, int]:
        """Replace inline style attributes with theme variables."""
        changes = 0

        # Pattern for style="..." attributes
        style_attr_pattern = r'style\s*=\s*["\']([^"\']+)["\']'

        def replace_style(match):
            nonlocal changes
            style_value = match.group(1)
            new_style = style_value

            # Replace colors
            for old_color, new_color in self.COLOR_MAPPINGS.items():
                if old_color.lower() in new_style.lower():
                    new_style = re.sub(
                        re.escape(old_color),
                        new_color,
                        new_style,
                        flags=re.IGNORECASE
                    )
                    changes += 1

            # Replace typography
            for old_typo, new_typo in self.TYPOGRAPHY_MAPPINGS.items():
                if old_typo in new_style:
                    new_style = new_style.replace(old_typo, new_typo)
                    changes += 1

            # Replace spacing
            for old_space, new_space in self.SPACING_MAPPINGS.items():
                # Only replace in padding/margin contexts
                if old_space in new_style:
                    # Be careful with spacing replacements
                    new_style = re.sub(
                        rf'(padding|margin):\s*{re.escape(old_space)}',
                        rf'\1: {new_space}',
                        new_style
                    )
                    changes += 1

            return f'style="{new_style}"'

        content = re.sub(style_attr_pattern, replace_style, content)
        return content, changes

    def _migrate_colors(self, content: str) -> Tuple[str, List[str]]:
        """Replace hardcoded colors with theme variables."""
        changes = []

        for old_color, new_color in self.COLOR_MAPPINGS.items():
            if old_color.lower() in content.lower():
                content = re.sub(
                    re.escape(old_color),
                    new_color,
                    content,
                    flags=re.IGNORECASE
                )
                changes.append(f"Replaced color {old_color} -> {new_color}")

        return content, changes

    def _migrate_typography(self, content: str) -> Tuple[str, List[str]]:
        """Replace hardcoded typography with theme variables."""
        changes = []

        for old_typo, new_typo in self.TYPOGRAPHY_MAPPINGS.items():
            if old_typo in content:
                content = content.replace(old_typo, new_typo)
                changes.append(f"Replaced typography {old_typo} -> {new_typo}")

        return content, changes

    def _migrate_spacing(self, content: str) -> Tuple[str, List[str]]:
        """Replace hardcoded spacing with theme variables."""
        changes = []

        for old_space, new_space in self.SPACING_MAPPINGS.items():
            # Only replace in CSS contexts
            pattern = rf'(padding|margin|gap):\s*{re.escape(old_space)}'
            if re.search(pattern, content):
                content = re.sub(pattern, rf'\1: {new_space}', content)
                changes.append(f"Replaced spacing {old_space} -> {new_space}")

        return content, changes

    def _ensure_design_system_import(self, content: str) -> str:
        """Ensure design system import is present."""
        if 'UNIFIED_DESIGN_SYSTEM_AVAILABLE' not in content:
            # Find import section
            import_match = re.search(r'^(import\s+|from\s+)', content, re.MULTILINE)
            if import_match:
                # Find end of imports
                lines = content.split('\n')
                last_import_idx = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        last_import_idx = i

                # Insert after last import
                insert_idx = sum(len(lines[j]) + 1 for j in range(last_import_idx + 1))
                content = content[:insert_idx] + self.design_system_import + content[insert_idx:]

        return content

    def analyze_styling(self, file_path: str) -> Dict[str, Any]:
        """Analyze current styling patterns in a component."""
        path = Path(file_path)

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        analysis = {
            'file_name': path.name,
            'inline_style_blocks': 0,
            'style_attributes': 0,
            'hardcoded_colors': [],
            'hardcoded_fonts': [],
            'hardcoded_spacing': [],
            'uses_design_system': False,
            'uses_enterprise_theme': False,
            'migration_effort': 'low'
        }

        # Count style blocks
        analysis['inline_style_blocks'] = len(
            re.findall(r'<style>[\s\S]*?</style>', content)
        )

        # Count style attributes
        analysis['style_attributes'] = len(
            re.findall(r'style\s*=\s*["\']', content)
        )

        # Find hardcoded colors
        hex_colors = set(re.findall(r'#[0-9a-fA-F]{6}', content))
        analysis['hardcoded_colors'] = [
            c for c in hex_colors
            if c.lower() not in [v.lower() for v in self.COLOR_MAPPINGS.keys()]
        ]

        # Check for design system usage
        analysis['uses_design_system'] = 'UNIFIED_DESIGN_SYSTEM_AVAILABLE' in content
        analysis['uses_enterprise_theme'] = 'EnterpriseThemeManager' in content

        # Estimate migration effort
        total_issues = (
            analysis['inline_style_blocks'] +
            analysis['style_attributes'] / 10 +
            len(analysis['hardcoded_colors'])
        )

        if total_issues > 20:
            analysis['migration_effort'] = 'high'
        elif total_issues > 5:
            analysis['migration_effort'] = 'medium'
        else:
            analysis['migration_effort'] = 'low'

        return analysis

    def generate_style_guide_compliance_report(
        self,
        components_dir: str
    ) -> Dict[str, Any]:
        """Generate compliance report for all components."""
        path = Path(components_dir)
        files = list(path.glob('*.py'))

        report = {
            'total_components': 0,
            'uses_design_system': 0,
            'uses_enterprise_theme': 0,
            'needs_migration': 0,
            'migration_effort': {'low': 0, 'medium': 0, 'high': 0},
            'components': []
        }

        for file_path in files:
            if file_path.name.startswith('_') or 'base' in file_path.name.lower():
                continue

            analysis = self.analyze_styling(str(file_path))
            report['total_components'] += 1
            report['components'].append(analysis)

            if analysis['uses_design_system']:
                report['uses_design_system'] += 1
            if analysis['uses_enterprise_theme']:
                report['uses_enterprise_theme'] += 1
            if not analysis['uses_design_system'] and not analysis['uses_enterprise_theme']:
                report['needs_migration'] += 1

            report['migration_effort'][analysis['migration_effort']] += 1

        # Calculate percentages
        total = report['total_components']
        if total > 0:
            report['design_system_adoption'] = round(
                report['uses_design_system'] / total * 100, 1
            )
            report['enterprise_theme_adoption'] = round(
                report['uses_enterprise_theme'] / total * 100, 1
            )
            report['migration_needed_percentage'] = round(
                report['needs_migration'] / total * 100, 1
            )

        return report


# Export
__all__ = ['ThemeMigrator', 'ThemeMigrationResult']
