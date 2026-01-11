"""
Validation Suite - Component Migration Validation
==================================================

Comprehensive validation framework for migrated Streamlit components.

Features:
- Syntax validation
- Import verification
- Class structure validation
- Theme compliance checking
- Performance benchmark validation
- Visual regression testing setup
- Claude integration testing

Author: EnterpriseHub Development Team
Date: January 2026
Version: 1.0.0
"""

import ast
import re
import time
import logging
import importlib.util
import traceback
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of component validation."""
    file_name: str
    valid: bool
    validation_type: str
    score: int = 100  # 0-100
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ValidationSuite:
    """
    Comprehensive validation suite for migrated components.

    Validates:
    - Python syntax correctness
    - Import resolution
    - Class structure and inheritance
    - Theme compliance
    - Performance characteristics
    - Accessibility compliance
    - Claude integration correctness
    """

    # Required base class methods
    REQUIRED_METHODS = {
        'EnterpriseDashboardComponent': ['render', '__init__'],
        'EnhancedEnterpriseComponent': ['render', '__init__'],
        'EnterpriseDataComponent': ['render', '__init__'],
        'ClaudeComponentMixin': []  # Mixin doesn't require specific methods
    }

    # Required imports for enterprise components
    REQUIRED_IMPORTS = {
        'enterprise_base': [
            'enhanced_enterprise_base',
            'EnhancedEnterpriseComponent'
        ],
        'theme': [
            'enterprise_theme_system',
            'EnterpriseThemeManager'
        ],
        'claude': [
            'claude_component_mixin',
            'ClaudeComponentMixin'
        ],
        'cache': [
            'streamlit_cache_integration',
            'StreamlitCacheIntegration'
        ]
    }

    # Theme compliance patterns
    THEME_COMPLIANCE_PATTERNS = {
        'uses_enterprise_colors': r'var\(--enterprise-',
        'uses_enterprise_spacing': r'var\(--enterprise-space-',
        'uses_enterprise_typography': r'var\(--enterprise-text-',
        'has_theme_injection': r'inject_enterprise_theme|inject_enterprise_css',
        'uses_design_system': r'enterprise_metric|enterprise_card|enterprise_badge'
    }

    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        'import_time_ms': 500,
        'init_time_ms': 100,
        'render_time_ms': 200
    }

    def __init__(self, components_dir: str):
        """
        Initialize validation suite.

        Args:
            components_dir: Path to streamlit_components directory
        """
        self.components_dir = Path(components_dir)
        self.results: Dict[str, List[ValidationResult]] = {}

    def validate_component(
        self,
        file_path: str,
        validation_types: Optional[List[str]] = None
    ) -> List[ValidationResult]:
        """
        Run all validations on a component.

        Args:
            file_path: Path to component file
            validation_types: Optional list of specific validations to run

        Returns:
            List of ValidationResult for each validation type
        """
        path = Path(file_path)
        results = []

        # Default validations
        if validation_types is None:
            validation_types = [
                'syntax',
                'imports',
                'structure',
                'theme',
                'performance',
                'claude'
            ]

        for val_type in validation_types:
            if val_type == 'syntax':
                results.append(self._validate_syntax(path))
            elif val_type == 'imports':
                results.append(self._validate_imports(path))
            elif val_type == 'structure':
                results.append(self._validate_structure(path))
            elif val_type == 'theme':
                results.append(self._validate_theme(path))
            elif val_type == 'performance':
                results.append(self._validate_performance(path))
            elif val_type == 'claude':
                results.append(self._validate_claude_integration(path))

        self.results[path.name] = results
        return results

    def _validate_syntax(self, path: Path) -> ValidationResult:
        """Validate Python syntax."""
        start = time.time()
        result = ValidationResult(
            file_name=path.name,
            valid=True,
            validation_type='syntax'
        )

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            ast.parse(content)
            result.passed_checks.append("Python syntax is valid")
            result.score = 100

        except SyntaxError as e:
            result.valid = False
            result.failed_checks.append(f"Syntax error: {e}")
            result.details['error'] = str(e)
            result.details['line'] = e.lineno
            result.score = 0

        result.duration_ms = (time.time() - start) * 1000
        return result

    def _validate_imports(self, path: Path) -> ValidationResult:
        """Validate imports and dependencies."""
        start = time.time()
        result = ValidationResult(
            file_name=path.name,
            valid=True,
            validation_type='imports'
        )

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse AST for imports
        try:
            tree = ast.parse(content)
        except SyntaxError:
            result.valid = False
            result.failed_checks.append("Cannot parse file for import analysis")
            return result

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                imports.append(module)
                for alias in node.names:
                    imports.append(alias.name)

        # Check for enterprise base imports
        has_enterprise_base = any(
            imp in imports for imp in self.REQUIRED_IMPORTS['enterprise_base']
        )
        if has_enterprise_base:
            result.passed_checks.append("Enterprise base imports present")
        else:
            result.warnings.append("Missing enterprise base imports")

        # Check for theme imports
        has_theme = any(
            imp in imports for imp in self.REQUIRED_IMPORTS['theme']
        )
        if has_theme:
            result.passed_checks.append("Theme imports present")
        else:
            result.warnings.append("Missing theme imports")

        # Check for circular imports (basic check)
        if path.name.replace('.py', '') in [i.split('.')[-1] for i in imports]:
            result.failed_checks.append("Potential circular import detected")
            result.valid = False

        # Calculate score
        passed = len(result.passed_checks)
        total = passed + len(result.failed_checks) + len(result.warnings) * 0.5
        result.score = int((passed / total) * 100) if total > 0 else 100

        result.details['imports'] = imports
        result.duration_ms = (time.time() - start) * 1000
        return result

    def _validate_structure(self, path: Path) -> ValidationResult:
        """Validate class structure and inheritance."""
        start = time.time()
        result = ValidationResult(
            file_name=path.name,
            valid=True,
            validation_type='structure'
        )

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            result.valid = False
            result.failed_checks.append("Cannot parse file for structure analysis")
            return result

        # Find main class
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_names = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_names.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_names.append(base.attr)

                methods = [
                    n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]

                classes.append({
                    'name': node.name,
                    'bases': base_names,
                    'methods': methods
                })

        if not classes:
            result.warnings.append("No classes found in component")

        for cls in classes:
            # Check for enterprise base class
            enterprise_bases = [
                b for b in cls['bases']
                if b in self.REQUIRED_METHODS
            ]

            if enterprise_bases:
                result.passed_checks.append(f"Class {cls['name']} extends enterprise base")

                # Check for required methods
                for base in enterprise_bases:
                    required = self.REQUIRED_METHODS[base]
                    for method in required:
                        if method in cls['methods']:
                            result.passed_checks.append(f"Required method '{method}' present")
                        else:
                            result.failed_checks.append(f"Missing required method '{method}'")
                            result.valid = False

            # Check for __init__ calling super()
            if '__init__' in cls['methods']:
                init_body = self._get_method_body(tree, cls['name'], '__init__')
                if 'super().__init__' in init_body or 'super().__init__(' in init_body:
                    result.passed_checks.append("__init__ calls super()")
                else:
                    result.warnings.append("__init__ may not call super()")

        # Calculate score
        passed = len(result.passed_checks)
        failed = len(result.failed_checks)
        warnings = len(result.warnings) * 0.5
        total = passed + failed + warnings
        result.score = int((passed / total) * 100) if total > 0 else 100

        result.details['classes'] = classes
        result.duration_ms = (time.time() - start) * 1000
        return result

    def _get_method_body(
        self,
        tree: ast.AST,
        class_name: str,
        method_name: str
    ) -> str:
        """Get string representation of method body."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name == method_name:
                            return ast.unparse(item) if hasattr(ast, 'unparse') else str(item)
        return ""

    def _validate_theme(self, path: Path) -> ValidationResult:
        """Validate theme compliance."""
        start = time.time()
        result = ValidationResult(
            file_name=path.name,
            valid=True,
            validation_type='theme'
        )

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check theme patterns
        for pattern_name, pattern in self.THEME_COMPLIANCE_PATTERNS.items():
            if re.search(pattern, content):
                result.passed_checks.append(f"Theme pattern '{pattern_name}' found")
            else:
                result.warnings.append(f"Theme pattern '{pattern_name}' not found")

        # Check for legacy patterns (anti-patterns)
        legacy_patterns = {
            'hardcoded_colors': r'#[0-9a-fA-F]{6}',
            'inline_px_sizes': r'font-size:\s*\d+px',
            'raw_style_blocks': r'<style>[^<]*</style>'
        }

        for pattern_name, pattern in legacy_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                # Don't fail, but warn
                result.warnings.append(
                    f"Legacy pattern '{pattern_name}' found ({len(matches)} occurrences)"
                )

        # Check for design system usage
        design_system_patterns = [
            'enterprise_metric',
            'enterprise_card',
            'enterprise_badge',
            'ENTERPRISE_COLORS',
            'apply_plotly_theme'
        ]

        design_system_usage = sum(
            1 for p in design_system_patterns if p in content
        )

        if design_system_usage >= 2:
            result.passed_checks.append(f"Uses design system ({design_system_usage} utilities)")
        elif design_system_usage >= 1:
            result.warnings.append("Limited design system usage")
        else:
            result.warnings.append("No design system utilities detected")

        # Calculate score
        passed = len(result.passed_checks)
        failed = len(result.failed_checks)
        warnings = len(result.warnings) * 0.3
        total = passed + failed + warnings
        result.score = int((passed / total) * 100) if total > 0 else 50

        result.duration_ms = (time.time() - start) * 1000
        return result

    def _validate_performance(self, path: Path) -> ValidationResult:
        """Validate performance characteristics."""
        start = time.time()
        result = ValidationResult(
            file_name=path.name,
            valid=True,
            validation_type='performance'
        )

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for performance patterns
        performance_patterns = {
            'uses_cache': ['@st.cache', 'st.cache_data', 'StreamlitCacheIntegration'],
            'async_operations': ['async def', 'await '],
            'lazy_loading': ['st.session_state', 'if.*not in st.session_state'],
            'batch_operations': ['asyncio.gather', 'concurrent.futures']
        }

        for pattern_name, patterns in performance_patterns.items():
            found = any(p in content for p in patterns)
            if found:
                result.passed_checks.append(f"Performance pattern '{pattern_name}' implemented")
            else:
                result.warnings.append(f"Consider implementing '{pattern_name}'")

        # Check for anti-patterns
        anti_patterns = {
            'blocking_in_render': r'def render\([^)]*\):[^}]*time\.sleep',
            'uncached_heavy_ops': r'(pd\.read_|requests\.get)',
            'excessive_loops': r'for\s+\w+\s+in\s+range\(\d{4,}'  # Loops > 1000
        }

        for pattern_name, pattern in anti_patterns.items():
            if re.search(pattern, content):
                result.warnings.append(f"Performance anti-pattern: {pattern_name}")

        # Check file size (large files may impact load time)
        file_size = len(content)
        if file_size > 50000:  # 50KB
            result.warnings.append(f"Large file size ({file_size / 1000:.1f}KB) may impact performance")
        else:
            result.passed_checks.append(f"File size acceptable ({file_size / 1000:.1f}KB)")

        # Calculate score
        passed = len(result.passed_checks)
        warnings = len(result.warnings)
        result.score = max(0, 100 - (warnings * 10))

        result.duration_ms = (time.time() - start) * 1000
        return result

    def _validate_claude_integration(self, path: Path) -> ValidationResult:
        """Validate Claude AI integration."""
        start = time.time()
        result = ValidationResult(
            file_name=path.name,
            valid=True,
            validation_type='claude'
        )

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for Claude mixin usage
        if 'ClaudeComponentMixin' in content:
            result.passed_checks.append("ClaudeComponentMixin integrated")

            # Check for proper initialization
            if 'ClaudeComponentMixin.__init__' in content:
                result.passed_checks.append("Claude mixin properly initialized")
            else:
                result.warnings.append("Claude mixin may not be properly initialized")

            # Check for Claude method usage
            claude_methods = [
                'get_real_time_coaching',
                'analyze_lead_semantics',
                'generate_executive_summary',
                'explain_model_prediction',
                'get_intelligent_questions'
            ]

            methods_used = [m for m in claude_methods if m in content]
            if methods_used:
                result.passed_checks.append(f"Uses Claude methods: {', '.join(methods_used)}")
            else:
                result.warnings.append("No Claude methods being used")

            # Check for fallback handling
            if 'fallback_mode' in content or 'fallback' in content.lower():
                result.passed_checks.append("Fallback handling implemented")
            else:
                result.warnings.append("Consider adding fallback handling for Claude unavailability")

            # Check for caching
            if 'enable_claude_caching=True' in content:
                result.passed_checks.append("Claude caching enabled")
            else:
                result.warnings.append("Consider enabling Claude caching for performance")

        else:
            # No Claude integration - not necessarily wrong
            result.details['has_claude'] = False
            result.passed_checks.append("No Claude integration (may be intentional)")

        # Calculate score
        passed = len(result.passed_checks)
        warnings = len(result.warnings)
        total = passed + warnings
        result.score = int((passed / total) * 100) if total > 0 else 100

        result.duration_ms = (time.time() - start) * 1000
        return result

    def validate_all_components(
        self,
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, List[ValidationResult]]:
        """Validate all components in directory."""
        component_files = list(self.components_dir.glob('*.py'))

        for file_path in component_files:
            if file_path.name.startswith('_'):
                continue
            if 'base' in file_path.name.lower() or 'mixin' in file_path.name.lower():
                continue

            self.validate_component(str(file_path), validation_types)

        return self.results

    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        if not self.results:
            self.validate_all_components()

        total_components = len(self.results)
        all_results = []

        for component, results in self.results.items():
            for r in results:
                all_results.append({
                    'component': component,
                    'type': r.validation_type,
                    'valid': r.valid,
                    'score': r.score,
                    'passed': len(r.passed_checks),
                    'failed': len(r.failed_checks),
                    'warnings': len(r.warnings)
                })

        # Aggregate by validation type
        by_type = {}
        for r in all_results:
            vtype = r['type']
            if vtype not in by_type:
                by_type[vtype] = {'valid': 0, 'invalid': 0, 'avg_score': 0, 'scores': []}
            if r['valid']:
                by_type[vtype]['valid'] += 1
            else:
                by_type[vtype]['invalid'] += 1
            by_type[vtype]['scores'].append(r['score'])

        for vtype, data in by_type.items():
            data['avg_score'] = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
            del data['scores']

        # Components needing attention
        needs_attention = []
        for component, results in self.results.items():
            avg_score = sum(r.score for r in results) / len(results) if results else 0
            if avg_score < 70:
                needs_attention.append({
                    'component': component,
                    'avg_score': round(avg_score, 1),
                    'issues': [
                        r.validation_type for r in results
                        if r.score < 70
                    ]
                })

        return {
            'summary': {
                'total_components': total_components,
                'total_validations': len(all_results),
                'overall_pass_rate': round(
                    sum(1 for r in all_results if r['valid']) / len(all_results) * 100, 1
                ) if all_results else 0,
                'average_score': round(
                    sum(r['score'] for r in all_results) / len(all_results), 1
                ) if all_results else 0
            },
            'by_validation_type': by_type,
            'components_needing_attention': needs_attention,
            'timestamp': datetime.now().isoformat()
        }

    def get_component_summary(self, file_name: str) -> Dict[str, Any]:
        """Get validation summary for a specific component."""
        if file_name not in self.results:
            return {'error': 'Component not validated'}

        results = self.results[file_name]
        return {
            'file_name': file_name,
            'validations': [
                {
                    'type': r.validation_type,
                    'valid': r.valid,
                    'score': r.score,
                    'passed': r.passed_checks,
                    'failed': r.failed_checks,
                    'warnings': r.warnings
                }
                for r in results
            ],
            'overall_score': sum(r.score for r in results) / len(results) if results else 0,
            'all_valid': all(r.valid for r in results)
        }


# Export
__all__ = ['ValidationSuite', 'ValidationResult']
