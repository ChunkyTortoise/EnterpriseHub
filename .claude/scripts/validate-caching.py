#!/usr/bin/env python3
"""
Validate Streamlit components for proper caching decorator usage.

Usage:
    python validate-caching.py <file_or_directory>
    python validate-caching.py ghl_real_estate_ai/streamlit_demo/components/

Features:
- Detects functions that should be cached but aren't
- Reports missing decorators with severity levels
- Generates actionable recommendations
- Supports bypass comments

Author: EnterpriseHub Team
Version: 1.0.0
"""

import ast
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Validation severity levels."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    """Represents a caching validation issue."""
    file_path: Path
    line_number: int
    function_name: str
    severity: Severity
    message: str
    recommendation: str


class CachingValidator(ast.NodeVisitor):
    """AST visitor to validate caching decorator usage."""

    DATA_FUNCTION_PATTERNS = [
        'load_', 'fetch_', 'get_', 'calculate_', 'aggregate_',
        'transform_', 'generate_', 'query_', 'retrieve_',
    ]

    RESOURCE_FUNCTION_PATTERNS = [
        'get_client', 'get_service', 'init_', 'create_connection',
        'create_client', 'setup_',
    ]

    EVENT_HANDLER_PATTERNS = [
        'handle_', 'on_', 'render_',
    ]

    def __init__(self, file_path: Path, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.issues: List[ValidationIssue] = []

    def _has_cache_decorator(self, node: ast.FunctionDef) -> bool:
        """Check if function has caching decorator."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Attribute):
                if (isinstance(decorator.value, ast.Name) and
                    decorator.value.id == 'st' and
                    decorator.attr in ['cache_data', 'cache_resource']):
                    return True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if (isinstance(decorator.func.value, ast.Name) and
                        decorator.func.value.id == 'st' and
                        decorator.func.attr in ['cache_data', 'cache_resource']):
                        return True
        return False

    def _has_bypass_comment(self, node: ast.FunctionDef) -> bool:
        """Check for @cache-skip bypass comment."""
        if not hasattr(node, 'lineno'):
            return False

        # Check docstring
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant)):
            docstring = node.body[0].value.value
            if isinstance(docstring, str) and '@cache-skip' in docstring:
                return True

        # Check line before function
        line_idx = node.lineno - 2
        if 0 <= line_idx < len(self.source_lines):
            if '@cache-skip' in self.source_lines[line_idx]:
                return True

        return False

    def _is_event_handler(self, name: str) -> bool:
        """Check if function is event handler."""
        return any(name.startswith(p) for p in self.EVENT_HANDLER_PATTERNS)

    def _is_data_function(self, name: str) -> bool:
        """Check if function should use @st.cache_data."""
        return any(name.startswith(p) for p in self.DATA_FUNCTION_PATTERNS)

    def _is_resource_function(self, name: str) -> bool:
        """Check if function should use @st.cache_resource."""
        return any(name.startswith(p) for p in self.RESOURCE_FUNCTION_PATTERNS)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        # Skip if already cached or bypassed
        if self._has_cache_decorator(node):
            return

        if self._has_bypass_comment(node):
            return

        # Skip event handlers (intentionally uncached)
        if self._is_event_handler(node.name):
            return

        # Check data functions
        if self._is_data_function(node.name):
            self.issues.append(ValidationIssue(
                file_path=self.file_path,
                line_number=node.lineno,
                function_name=node.name,
                severity=Severity.WARNING,
                message=f"Data function '{node.name}' missing @st.cache_data decorator",
                recommendation=f"""
Add caching decorator:

    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def {node.name}(...):
        pass

Choose TTL based on data freshness:
- Real-time data: ttl=60 (1 minute)
- Frequently changing: ttl=300 (5 minutes)
- Stable data: ttl=3600 (1 hour)
- Static data: no ttl parameter

Performance impact: 40-60% faster load times
"""
            ))

        # Check resource functions
        elif self._is_resource_function(node.name):
            self.issues.append(ValidationIssue(
                file_path=self.file_path,
                line_number=node.lineno,
                function_name=node.name,
                severity=Severity.WARNING,
                message=f"Resource function '{node.name}' missing @st.cache_resource decorator",
                recommendation=f"""
Add resource caching:

    @st.cache_resource
    def {node.name}(...):
        pass

Use for:
- Database connections
- API clients
- Expensive object initialization
- Singleton instances

Performance impact: Prevents redundant connection/initialization
"""
            ))

        self.generic_visit(node)


def validate_file(file_path: Path) -> List[ValidationIssue]:
    """Validate a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
        source_lines = source.split('\n')

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [ValidationIssue(
            file_path=file_path,
            line_number=e.lineno or 0,
            function_name="<syntax error>",
            severity=Severity.ERROR,
            message=f"Syntax error: {e}",
            recommendation="Fix syntax error before validating caching"
        )]

    validator = CachingValidator(file_path, source_lines)
    validator.visit(tree)
    return validator.issues


def validate_directory(dir_path: Path) -> List[ValidationIssue]:
    """Validate all Python files in directory."""
    all_issues = []
    python_files = list(dir_path.glob('*.py'))

    for file_path in sorted(python_files):
        if file_path.name.startswith('__'):
            continue
        issues = validate_file(file_path)
        all_issues.extend(issues)

    return all_issues


def print_report(issues: List[ValidationIssue], verbose: bool = False):
    """Print validation report."""
    if not issues:
        print("\n✅ All components properly cached!")
        return

    # Group by severity
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    infos = [i for i in issues if i.severity == Severity.INFO]

    print(f"\n{'='*60}")
    print(f"CACHING VALIDATION REPORT")
    print(f"{'='*60}")

    print(f"\nSummary:")
    print(f"  ❌ Errors: {len(errors)}")
    print(f"  ⚠️  Warnings: {len(warnings)}")
    print(f"  ℹ️  Info: {len(infos)}")
    print(f"  📊 Total Issues: {len(issues)}")

    # Print errors
    if errors:
        print(f"\n{'='*60}")
        print("❌ ERRORS (Must Fix)")
        print(f"{'='*60}")
        for issue in errors:
            print(f"\n  {issue.file_path}:{issue.line_number}")
            print(f"  Function: {issue.function_name}")
            print(f"  {issue.message}")
            if verbose:
                print(f"\n  Recommendation:{issue.recommendation}")

    # Print warnings
    if warnings:
        print(f"\n{'='*60}")
        print("⚠️  WARNINGS (Should Fix)")
        print(f"{'='*60}")
        for issue in warnings:
            print(f"\n  {issue.file_path}:{issue.line_number}")
            print(f"  Function: {issue.function_name}")
            print(f"  {issue.message}")
            if verbose:
                print(f"\n  Recommendation:{issue.recommendation}")

    # Print infos
    if infos and verbose:
        print(f"\n{'='*60}")
        print("ℹ️  INFO (Consider)")
        print(f"{'='*60}")
        for issue in infos:
            print(f"\n  {issue.file_path}:{issue.line_number}")
            print(f"  Function: {issue.function_name}")
            print(f"  {issue.message}")
            print(f"\n  Recommendation:{issue.recommendation}")

    # Print next steps
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("\n1. Review warnings and add appropriate decorators")
    print("2. Run auto-fix script:")
    print("   python .claude/scripts/add-caching-decorators.py <file>")
    print("\n3. Or add bypass comment if intentional:")
    print("   # @cache-skip: <reason>")
    print("\n4. Re-run validation to verify fixes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate Streamlit component caching',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate single file
  python validate-caching.py components/lead_intelligence_hub.py

  # Validate all components
  python validate-caching.py ghl_real_estate_ai/streamlit_demo/components/

  # Verbose output with recommendations
  python validate-caching.py --verbose components/
        """
    )

    parser.add_argument(
        'path',
        type=Path,
        help='File or directory to validate'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed recommendations'
    )

    args = parser.parse_args()

    if not args.path.exists():
        print(f"❌ Error: Path not found: {args.path}")
        sys.exit(1)

    # Validate
    if args.path.is_file():
        issues = validate_file(args.path)
    else:
        issues = validate_directory(args.path)

    # Report
    print_report(issues, verbose=args.verbose)

    # Exit code
    errors = [i for i in issues if i.severity == Severity.ERROR]
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
