"""
Component Analyzer - Comprehensive Analysis for Migration Planning
==================================================================

Analyzes Streamlit components to determine migration requirements,
enterprise standards compliance, and Claude AI integration status.

Features:
- Component inheritance analysis
- Theme system usage detection
- Claude integration status
- Cache integration detection
- Code quality metrics
- Migration complexity scoring
- Priority recommendation

Author: EnterpriseHub Development Team
Date: January 2026
Version: 1.0.0
"""

import os
import re
import ast
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """Component migration status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    FAILED = "failed"


class BaseClassType(Enum):
    """Component base class types."""
    ENHANCED_ENTERPRISE = "EnhancedEnterpriseComponent"
    ENTERPRISE_DASHBOARD = "EnterpriseDashboardComponent"
    ENTERPRISE_DATA = "EnterpriseDataComponent"
    ENTERPRISE_COMPONENT = "EnterpriseComponent"  # Legacy
    CLAUDE_MIXIN = "ClaudeComponentMixin"
    NO_BASE = "NoBase"


class ThemeIntegrationLevel(Enum):
    """Theme integration level."""
    UNIFIED_DESIGN_SYSTEM = "unified_design_system"
    ENTERPRISE_THEME = "enterprise_theme"
    LEGACY_CSS = "legacy_css"
    INLINE_STYLES = "inline_styles"
    NO_THEME = "no_theme"


class ClaudeIntegrationLevel(Enum):
    """Claude AI integration level."""
    FULL = "full"  # ClaudeComponentMixin with all features
    PARTIAL = "partial"  # Some Claude services imported
    DEMO = "demo"  # Demo mode only
    NONE = "none"  # No Claude integration


@dataclass
class ComponentAnalysis:
    """Complete analysis of a Streamlit component."""

    # Basic info
    file_path: str
    file_name: str
    class_name: str
    line_count: int
    created_date: Optional[str] = None
    last_modified: Optional[str] = None

    # Inheritance analysis
    base_classes: List[str] = field(default_factory=list)
    base_class_type: BaseClassType = BaseClassType.NO_BASE
    implements_mixin: bool = False

    # Theme integration
    theme_level: ThemeIntegrationLevel = ThemeIntegrationLevel.NO_THEME
    uses_unified_design_system: bool = False
    uses_enterprise_theme: bool = False
    has_inline_css: bool = False
    css_line_count: int = 0

    # Claude integration
    claude_level: ClaudeIntegrationLevel = ClaudeIntegrationLevel.NONE
    claude_services: List[str] = field(default_factory=list)
    claude_operations: List[str] = field(default_factory=list)

    # Cache integration
    uses_streamlit_cache: bool = False
    uses_cache_integration: bool = False
    cache_operations: List[str] = field(default_factory=list)

    # Code quality metrics
    has_docstring: bool = False
    has_type_hints: bool = False
    method_count: int = 0
    async_method_count: int = 0
    error_handling_count: int = 0

    # Dependencies
    imports: List[str] = field(default_factory=list)
    internal_imports: List[str] = field(default_factory=list)
    external_imports: List[str] = field(default_factory=list)

    # Migration assessment
    migration_complexity: str = "low"  # low, medium, high
    migration_priority: str = "medium"  # low, medium, high, critical
    migration_status: MigrationStatus = MigrationStatus.NOT_STARTED
    migration_issues: List[str] = field(default_factory=list)
    migration_recommendations: List[str] = field(default_factory=list)

    # Scores (0-100)
    enterprise_compliance_score: int = 0
    claude_readiness_score: int = 0
    theme_compliance_score: int = 0
    cache_optimization_score: int = 0
    overall_score: int = 0

    # Business impact
    business_value: str = "medium"  # low, medium, high
    user_facing: bool = True

    @property
    def needs_migration(self) -> bool:
        """Check if component needs migration."""
        return self.overall_score < 80

    @property
    def needs_claude_integration(self) -> bool:
        """Check if component needs Claude integration."""
        return self.claude_level in [ClaudeIntegrationLevel.NONE, ClaudeIntegrationLevel.DEMO]

    @property
    def needs_theme_migration(self) -> bool:
        """Check if component needs theme migration."""
        return self.theme_level in [ThemeIntegrationLevel.LEGACY_CSS,
                                     ThemeIntegrationLevel.INLINE_STYLES,
                                     ThemeIntegrationLevel.NO_THEME]


class ComponentAnalyzer:
    """
    Comprehensive analyzer for Streamlit components.

    Analyzes components to determine:
    - Current enterprise standards compliance
    - Claude AI integration status
    - Theme system usage
    - Cache integration
    - Migration requirements
    """

    # Pattern definitions for analysis
    BASE_CLASS_PATTERNS = {
        'EnhancedEnterpriseComponent': BaseClassType.ENHANCED_ENTERPRISE,
        'EnterpriseDashboardComponent': BaseClassType.ENTERPRISE_DASHBOARD,
        'EnterpriseDataComponent': BaseClassType.ENTERPRISE_DATA,
        'EnterpriseComponent': BaseClassType.ENTERPRISE_COMPONENT,
        'ClaudeComponentMixin': BaseClassType.CLAUDE_MIXIN,
    }

    CLAUDE_SERVICE_PATTERNS = [
        'ClaudeAgentService',
        'ClaudeSemanticAnalyzer',
        'QualificationOrchestrator',
        'ClaudeActionPlanner',
        'ClaudeVoiceIntegration',
        'ClaudeComponentMixin',
    ]

    CLAUDE_OPERATION_PATTERNS = [
        'get_real_time_coaching',
        'analyze_lead_semantics',
        'get_intelligent_questions',
        'generate_executive_summary',
        'explain_model_prediction',
        'analyze_property_valuation',
        'optimize_campaign_strategy',
    ]

    CACHE_PATTERNS = [
        'st.cache_data',
        'st.cache_resource',
        'StreamlitCacheIntegration',
        'cached_render',
        '@st.cache',
    ]

    THEME_PATTERNS = {
        'unified_design_system': [
            'from ..design_system import',
            'enterprise_metric',
            'enterprise_card',
            'ENTERPRISE_COLORS',
        ],
        'enterprise_theme': [
            'EnterpriseThemeManager',
            'inject_enterprise_theme',
            'create_enterprise_card',
            'create_enterprise_metric',
            'ThemeVariant',
        ],
        'legacy_css': [
            'st.markdown.*<style>',
            'unsafe_allow_html=True',
            'background-color:',
            'font-size:',
        ],
    }

    # Business value indicators
    HIGH_VALUE_INDICATORS = [
        'coaching', 'valuation', 'lead', 'conversion', 'revenue',
        'analytics', 'intelligence', 'business', 'performance'
    ]

    def __init__(self, components_dir: str):
        """
        Initialize analyzer with components directory.

        Args:
            components_dir: Path to streamlit_components directory
        """
        self.components_dir = Path(components_dir)
        self.analyses: Dict[str, ComponentAnalysis] = {}

    def analyze_all_components(self) -> Dict[str, ComponentAnalysis]:
        """
        Analyze all Python files in the components directory.

        Returns:
            Dictionary mapping file names to ComponentAnalysis objects
        """
        component_files = list(self.components_dir.glob('*.py'))

        # Exclude non-component files
        exclude_patterns = [
            '__init__', 'base', 'mixin', 'utils', 'helpers',
            'constants', 'types', 'models'
        ]

        for file_path in component_files:
            if any(pattern in file_path.name.lower() for pattern in exclude_patterns):
                continue

            # Skip if it's clearly a utility file
            if file_path.name.startswith('_'):
                continue

            try:
                analysis = self.analyze_component(str(file_path))
                self.analyses[file_path.name] = analysis
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")

        return self.analyses

    def analyze_component(self, file_path: str) -> ComponentAnalysis:
        """
        Analyze a single component file.

        Args:
            file_path: Path to the component file

        Returns:
            ComponentAnalysis with complete analysis
        """
        path = Path(file_path)

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Basic file info
        lines = content.split('\n')
        line_count = len(lines)

        # Parse AST for class analysis
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return ComponentAnalysis(
                file_path=str(path),
                file_name=path.name,
                class_name="ParseError",
                line_count=line_count,
                migration_issues=[f"Syntax error: {e}"]
            )

        # Find main class
        class_name = self._find_main_class(tree, path.stem)
        base_classes = self._get_base_classes(tree, class_name)

        # Determine base class type
        base_class_type = self._determine_base_class_type(base_classes)

        # Analyze theme integration
        theme_level = self._analyze_theme_integration(content)
        css_line_count = self._count_css_lines(content)

        # Analyze Claude integration
        claude_level, claude_services, claude_ops = self._analyze_claude_integration(content)

        # Analyze cache integration
        cache_info = self._analyze_cache_integration(content)

        # Analyze code quality
        quality_info = self._analyze_code_quality(tree, content)

        # Analyze imports
        imports = self._extract_imports(tree)

        # Calculate scores
        scores = self._calculate_scores(
            base_class_type, theme_level, claude_level, cache_info, quality_info
        )

        # Determine migration requirements
        migration_info = self._assess_migration(
            base_class_type, theme_level, claude_level, cache_info, scores
        )

        # Determine business value
        business_value = self._assess_business_value(path.name, class_name, content)

        return ComponentAnalysis(
            file_path=str(path),
            file_name=path.name,
            class_name=class_name,
            line_count=line_count,
            base_classes=base_classes,
            base_class_type=base_class_type,
            implements_mixin='ClaudeComponentMixin' in base_classes,
            theme_level=theme_level,
            uses_unified_design_system=theme_level == ThemeIntegrationLevel.UNIFIED_DESIGN_SYSTEM,
            uses_enterprise_theme=theme_level in [
                ThemeIntegrationLevel.UNIFIED_DESIGN_SYSTEM,
                ThemeIntegrationLevel.ENTERPRISE_THEME
            ],
            has_inline_css=bool(re.search(r'st\.markdown.*<style>', content)),
            css_line_count=css_line_count,
            claude_level=claude_level,
            claude_services=claude_services,
            claude_operations=claude_ops,
            uses_streamlit_cache=any(p in content for p in ['st.cache_data', 'st.cache_resource']),
            uses_cache_integration='StreamlitCacheIntegration' in content,
            cache_operations=cache_info['operations'],
            has_docstring='"""' in content[:500],
            has_type_hints='->' in content or ': str' in content or ': int' in content,
            method_count=quality_info['method_count'],
            async_method_count=quality_info['async_count'],
            error_handling_count=quality_info['error_handling'],
            imports=imports['all'],
            internal_imports=imports['internal'],
            external_imports=imports['external'],
            migration_complexity=migration_info['complexity'],
            migration_priority=migration_info['priority'],
            migration_issues=migration_info['issues'],
            migration_recommendations=migration_info['recommendations'],
            enterprise_compliance_score=scores['enterprise'],
            claude_readiness_score=scores['claude'],
            theme_compliance_score=scores['theme'],
            cache_optimization_score=scores['cache'],
            overall_score=scores['overall'],
            business_value=business_value,
        )

    def _find_main_class(self, tree: ast.AST, expected_name: str) -> str:
        """Find the main class in the module."""
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        # Try to find class matching filename
        for cls in classes:
            if expected_name.lower().replace('_', '') in cls.lower().replace('_', ''):
                return cls

        # Return first class that looks like a component
        for cls in classes:
            if 'Dashboard' in cls or 'Component' in cls or 'Manager' in cls:
                return cls

        return classes[0] if classes else "Unknown"

    def _get_base_classes(self, tree: ast.AST, class_name: str) -> List[str]:
        """Get base classes for the main class."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(base.attr)
                return bases
        return []

    def _determine_base_class_type(self, base_classes: List[str]) -> BaseClassType:
        """Determine the primary base class type."""
        for base in base_classes:
            if base in self.BASE_CLASS_PATTERNS:
                return self.BASE_CLASS_PATTERNS[base]
        return BaseClassType.NO_BASE

    def _analyze_theme_integration(self, content: str) -> ThemeIntegrationLevel:
        """Analyze theme integration level."""
        # Check for unified design system first (highest level)
        if any(p in content for p in self.THEME_PATTERNS['unified_design_system']):
            return ThemeIntegrationLevel.UNIFIED_DESIGN_SYSTEM

        # Check for enterprise theme
        if any(p in content for p in self.THEME_PATTERNS['enterprise_theme']):
            return ThemeIntegrationLevel.ENTERPRISE_THEME

        # Check for legacy CSS
        if re.search(r'st\.markdown.*<style>', content) or 'style="' in content:
            return ThemeIntegrationLevel.LEGACY_CSS

        # Check for inline styles
        if 'background-color' in content or 'font-size' in content:
            return ThemeIntegrationLevel.INLINE_STYLES

        return ThemeIntegrationLevel.NO_THEME

    def _count_css_lines(self, content: str) -> int:
        """Count lines of CSS in the component."""
        css_matches = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
        css_lines = sum(len(match.strip().split('\n')) for match in css_matches)

        # Also count inline style attributes
        inline_styles = len(re.findall(r'style="[^"]*"', content))

        return css_lines + inline_styles

    def _analyze_claude_integration(
        self, content: str
    ) -> Tuple[ClaudeIntegrationLevel, List[str], List[str]]:
        """Analyze Claude AI integration level."""
        services = []
        operations = []

        # Check for Claude services
        for service in self.CLAUDE_SERVICE_PATTERNS:
            if service in content:
                services.append(service)

        # Check for Claude operations
        for operation in self.CLAUDE_OPERATION_PATTERNS:
            if operation in content:
                operations.append(operation)

        # Determine level
        if 'ClaudeComponentMixin' in content and len(operations) >= 3:
            level = ClaudeIntegrationLevel.FULL
        elif services and operations:
            level = ClaudeIntegrationLevel.PARTIAL
        elif 'demo_mode' in content.lower() and services:
            level = ClaudeIntegrationLevel.DEMO
        else:
            level = ClaudeIntegrationLevel.NONE

        return level, services, operations

    def _analyze_cache_integration(self, content: str) -> Dict[str, Any]:
        """Analyze cache integration."""
        operations = []

        for pattern in self.CACHE_PATTERNS:
            if pattern in content:
                operations.append(pattern)

        return {
            'operations': operations,
            'uses_streamlit_cache': 'st.cache' in content,
            'uses_custom_cache': 'StreamlitCacheIntegration' in content
        }

    def _analyze_code_quality(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze code quality metrics."""
        method_count = 0
        async_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_count += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                async_count += 1
                method_count += 1

        error_handling = len(re.findall(r'try:', content))

        return {
            'method_count': method_count,
            'async_count': async_count,
            'error_handling': error_handling
        }

    def _extract_imports(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Extract and categorize imports."""
        all_imports = []
        internal = []
        external = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    all_imports.append(alias.name)
                    if alias.name.startswith('ghl_real_estate_ai'):
                        internal.append(alias.name)
                    else:
                        external.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                all_imports.append(module)
                if 'ghl_real_estate_ai' in module or module.startswith('.'):
                    internal.append(module)
                else:
                    external.append(module)

        return {
            'all': all_imports,
            'internal': internal,
            'external': external
        }

    def _calculate_scores(
        self,
        base_class_type: BaseClassType,
        theme_level: ThemeIntegrationLevel,
        claude_level: ClaudeIntegrationLevel,
        cache_info: Dict[str, Any],
        quality_info: Dict[str, Any]
    ) -> Dict[str, int]:
        """Calculate compliance and quality scores."""

        # Enterprise compliance score
        enterprise = 0
        if base_class_type == BaseClassType.ENHANCED_ENTERPRISE:
            enterprise = 100
        elif base_class_type == BaseClassType.ENTERPRISE_DASHBOARD:
            enterprise = 100
        elif base_class_type == BaseClassType.ENTERPRISE_DATA:
            enterprise = 100
        elif base_class_type == BaseClassType.ENTERPRISE_COMPONENT:
            enterprise = 70
        elif base_class_type == BaseClassType.CLAUDE_MIXIN:
            enterprise = 50
        else:
            enterprise = 20

        # Theme compliance score
        theme = 0
        if theme_level == ThemeIntegrationLevel.UNIFIED_DESIGN_SYSTEM:
            theme = 100
        elif theme_level == ThemeIntegrationLevel.ENTERPRISE_THEME:
            theme = 80
        elif theme_level == ThemeIntegrationLevel.LEGACY_CSS:
            theme = 40
        elif theme_level == ThemeIntegrationLevel.INLINE_STYLES:
            theme = 20
        else:
            theme = 10

        # Claude readiness score
        claude = 0
        if claude_level == ClaudeIntegrationLevel.FULL:
            claude = 100
        elif claude_level == ClaudeIntegrationLevel.PARTIAL:
            claude = 60
        elif claude_level == ClaudeIntegrationLevel.DEMO:
            claude = 30
        else:
            claude = 0

        # Cache optimization score
        cache = 0
        if cache_info['uses_custom_cache']:
            cache = 100
        elif cache_info['uses_streamlit_cache']:
            cache = 60
        elif cache_info['operations']:
            cache = 30
        else:
            cache = 10

        # Overall score (weighted average)
        overall = int(
            enterprise * 0.35 +
            theme * 0.25 +
            claude * 0.25 +
            cache * 0.15
        )

        return {
            'enterprise': enterprise,
            'theme': theme,
            'claude': claude,
            'cache': cache,
            'overall': overall
        }

    def _assess_migration(
        self,
        base_class_type: BaseClassType,
        theme_level: ThemeIntegrationLevel,
        claude_level: ClaudeIntegrationLevel,
        cache_info: Dict[str, Any],
        scores: Dict[str, int]
    ) -> Dict[str, Any]:
        """Assess migration requirements."""
        issues = []
        recommendations = []

        # Base class issues
        if base_class_type == BaseClassType.NO_BASE:
            issues.append("No enterprise base class - requires full migration")
            recommendations.append("Migrate to EnterpriseDashboardComponent or EnhancedEnterpriseComponent")
        elif base_class_type == BaseClassType.ENTERPRISE_COMPONENT:
            issues.append("Using legacy EnterpriseComponent - upgrade recommended")
            recommendations.append("Upgrade to EnhancedEnterpriseComponent")

        # Theme issues
        if theme_level == ThemeIntegrationLevel.LEGACY_CSS:
            issues.append("Using legacy inline CSS - migrate to unified design system")
            recommendations.append("Replace inline styles with enterprise_metric, enterprise_card utilities")
        elif theme_level == ThemeIntegrationLevel.INLINE_STYLES:
            issues.append("Inline styles detected - standardize with theme system")
            recommendations.append("Use EnterpriseThemeManager for consistent styling")
        elif theme_level == ThemeIntegrationLevel.NO_THEME:
            issues.append("No theme integration detected")
            recommendations.append("Integrate with enterprise theme system")

        # Claude issues
        if claude_level == ClaudeIntegrationLevel.NONE:
            issues.append("No Claude AI integration")
            recommendations.append("Consider adding ClaudeComponentMixin for AI-powered features")
        elif claude_level == ClaudeIntegrationLevel.DEMO:
            issues.append("Claude integration in demo mode only")
            recommendations.append("Implement full Claude service integration")

        # Cache issues
        if not cache_info['uses_custom_cache'] and not cache_info['uses_streamlit_cache']:
            issues.append("No caching implemented")
            recommendations.append("Add StreamlitCacheIntegration for performance optimization")

        # Determine complexity
        issue_count = len(issues)
        if issue_count >= 4:
            complexity = "high"
        elif issue_count >= 2:
            complexity = "medium"
        else:
            complexity = "low"

        # Determine priority based on score
        if scores['overall'] < 40:
            priority = "critical"
        elif scores['overall'] < 60:
            priority = "high"
        elif scores['overall'] < 80:
            priority = "medium"
        else:
            priority = "low"

        return {
            'complexity': complexity,
            'priority': priority,
            'issues': issues,
            'recommendations': recommendations
        }

    def _assess_business_value(
        self, file_name: str, class_name: str, content: str
    ) -> str:
        """Assess business value of component."""
        text = (file_name + class_name + content[:1000]).lower()

        high_value_count = sum(1 for ind in self.HIGH_VALUE_INDICATORS if ind in text)

        if high_value_count >= 3:
            return "high"
        elif high_value_count >= 1:
            return "medium"
        else:
            return "low"

    def generate_migration_report(self) -> Dict[str, Any]:
        """Generate comprehensive migration report."""
        if not self.analyses:
            self.analyze_all_components()

        # Summary statistics
        total = len(self.analyses)

        # Base class distribution
        base_class_dist = {}
        for analysis in self.analyses.values():
            key = analysis.base_class_type.value
            base_class_dist[key] = base_class_dist.get(key, 0) + 1

        # Theme distribution
        theme_dist = {}
        for analysis in self.analyses.values():
            key = analysis.theme_level.value
            theme_dist[key] = theme_dist.get(key, 0) + 1

        # Claude distribution
        claude_dist = {}
        for analysis in self.analyses.values():
            key = analysis.claude_level.value
            claude_dist[key] = claude_dist.get(key, 0) + 1

        # Priority breakdown
        priority_breakdown = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for name, analysis in self.analyses.items():
            priority_breakdown[analysis.migration_priority].append(name)

        # Score statistics
        scores = [a.overall_score for a in self.analyses.values()]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Components needing migration
        needs_migration = [
            (name, a) for name, a in self.analyses.items() if a.needs_migration
        ]

        return {
            'summary': {
                'total_components': total,
                'average_score': round(avg_score, 1),
                'components_needing_migration': len(needs_migration),
                'migration_percentage': round(len(needs_migration) / total * 100, 1) if total else 0
            },
            'base_class_distribution': base_class_dist,
            'theme_distribution': theme_dist,
            'claude_distribution': claude_dist,
            'priority_breakdown': {
                k: len(v) for k, v in priority_breakdown.items()
            },
            'priority_lists': priority_breakdown,
            'components_by_score': sorted(
                [(name, a.overall_score) for name, a in self.analyses.items()],
                key=lambda x: x[1]
            ),
            'high_value_components': [
                name for name, a in self.analyses.items() if a.business_value == "high"
            ],
            'timestamp': datetime.now().isoformat()
        }

    def get_migration_order(self) -> List[Tuple[str, ComponentAnalysis]]:
        """Get recommended migration order based on priority and dependencies."""
        if not self.analyses:
            self.analyze_all_components()

        # Sort by priority and business value
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        value_order = {'high': 0, 'medium': 1, 'low': 2}

        sorted_components = sorted(
            self.analyses.items(),
            key=lambda x: (
                priority_order.get(x[1].migration_priority, 4),
                value_order.get(x[1].business_value, 3),
                -x[1].line_count  # Larger components first (more impact)
            )
        )

        return sorted_components
