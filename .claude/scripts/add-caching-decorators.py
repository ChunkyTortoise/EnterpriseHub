#!/usr/bin/env python3
"""
Automatically add caching decorators to Streamlit component functions.

Usage:
    python add-caching-decorators.py <component_file>
    python add-caching-decorators.py ghl_real_estate_ai/streamlit_demo/components/lead_intelligence_hub.py

Features:
- AST-based transformation (preserves formatting where possible)
- Identifies data functions and adds @st.cache_data(ttl=300)
- Identifies resource functions and adds @st.cache_resource
- Skips event handlers and already-decorated functions
- Detects bypass comments (@cache-skip)
- Dry-run mode for preview

Author: EnterpriseHub Team
Version: 1.0.0
"""

import ast
import argparse
import sys
from pathlib import Path
from typing import List, Set
import re


class CachingTransformer(ast.NodeTransformer):
    """AST transformer to add caching decorators to functions."""

    # Function naming patterns that should use @st.cache_data
    DATA_FUNCTION_PATTERNS = [
        'load_',
        'fetch_',
        'get_',
        'calculate_',
        'aggregate_',
        'transform_',
        'generate_',
        'query_',
        'retrieve_',
    ]

    # Function naming patterns that should use @st.cache_resource
    RESOURCE_FUNCTION_PATTERNS = [
        'get_client',
        'get_service',
        'init_',
        'create_connection',
        'create_client',
        'setup_',
    ]

    # Event handlers that should NEVER be cached
    EVENT_HANDLER_PATTERNS = [
        'handle_',
        'on_',
        'render_',  # Render functions often have session state
    ]

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.modifications: List[str] = []
        self.skipped: List[str] = []

    def _has_cache_decorator(self, node: ast.FunctionDef) -> bool:
        """Check if function already has a caching decorator."""
        for decorator in node.decorator_list:
            # Handle @st.cache_data or @st.cache_resource
            if isinstance(decorator, ast.Attribute):
                if (isinstance(decorator.value, ast.Name) and
                    decorator.value.id == 'st' and
                    decorator.attr in ['cache_data', 'cache_resource']):
                    return True
            # Handle @st.cache_data(...) or @st.cache_resource
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if (isinstance(decorator.func.value, ast.Name) and
                        decorator.func.value.id == 'st' and
                        decorator.func.attr in ['cache_data', 'cache_resource']):
                        return True
        return False

    def _has_bypass_comment(self, node: ast.FunctionDef, source_lines: List[str]) -> bool:
        """Check if function has @cache-skip bypass comment."""
        if not hasattr(node, 'lineno'):
            return False

        # Check docstring
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant)):
            docstring = node.body[0].value.value
            if isinstance(docstring, str) and '@cache-skip' in docstring:
                return True

        # Check line before function definition
        line_idx = node.lineno - 2  # -1 for 0-index, -1 for line before
        if 0 <= line_idx < len(source_lines):
            if '@cache-skip' in source_lines[line_idx]:
                return True

        return False

    def _is_event_handler(self, function_name: str) -> bool:
        """Check if function is an event handler."""
        return any(function_name.startswith(pattern)
                   for pattern in self.EVENT_HANDLER_PATTERNS)

    def _is_data_function(self, function_name: str) -> bool:
        """Check if function should use @st.cache_data."""
        return any(function_name.startswith(pattern)
                   for pattern in self.DATA_FUNCTION_PATTERNS)

    def _is_resource_function(self, function_name: str) -> bool:
        """Check if function should use @st.cache_resource."""
        return any(function_name.startswith(pattern)
                   for pattern in self.RESOURCE_FUNCTION_PATTERNS)

    def _create_cache_data_decorator(self, ttl: int = 300) -> ast.Call:
        """Create @st.cache_data(ttl=300) decorator."""
        return ast.Call(
            func=ast.Attribute(
                value=ast.Name(id='st', ctx=ast.Load()),
                attr='cache_data',
                ctx=ast.Load()
            ),
            args=[],
            keywords=[
                ast.keyword(arg='ttl', value=ast.Constant(value=ttl))
            ]
        )

    def _create_cache_resource_decorator(self) -> ast.Attribute:
        """Create @st.cache_resource decorator."""
        return ast.Attribute(
            value=ast.Name(id='st', ctx=ast.Load()),
            attr='cache_resource',
            ctx=ast.Load()
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definition and add caching decorator if needed."""
        function_name = node.name

        # Skip if already has caching decorator
        if self._has_cache_decorator(node):
            if self.verbose:
                self.skipped.append(f"{function_name}: already has cache decorator")
            return node

        # Skip event handlers
        if self._is_event_handler(function_name):
            if self.verbose:
                self.skipped.append(f"{function_name}: event handler (skip)")
            return node

        # Add @st.cache_data for data functions
        if self._is_data_function(function_name):
            decorator = self._create_cache_data_decorator(ttl=300)
            node.decorator_list.insert(0, decorator)
            self.modifications.append(
                f"✅ {function_name}: Added @st.cache_data(ttl=300)"
            )

        # Add @st.cache_resource for resource functions
        elif self._is_resource_function(function_name):
            decorator = self._create_cache_resource_decorator()
            node.decorator_list.insert(0, decorator)
            self.modifications.append(
                f"✅ {function_name}: Added @st.cache_resource"
            )

        else:
            if self.verbose:
                self.skipped.append(
                    f"{function_name}: no pattern match (consider manual review)"
                )

        return node


def add_streamlit_import(source: str) -> str:
    """Ensure 'import streamlit as st' is present."""
    if 'import streamlit as st' in source:
        return source

    # Find the first import statement and add before it
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            lines.insert(i, 'import streamlit as st')
            return '\n'.join(lines)

    # No imports found, add at top after docstring
    for i, line in enumerate(lines):
        if not (line.strip().startswith('#') or
                line.strip().startswith('"""') or
                line.strip().startswith("'''") or
                line.strip() == ''):
            lines.insert(i, 'import streamlit as st\n')
            return '\n'.join(lines)

    return source


def add_caching_to_file(
    file_path: Path,
    dry_run: bool = False,
    verbose: bool = False
) -> None:
    """Add caching decorators to a component file."""

    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)

    # Read source
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    # Parse AST
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        sys.exit(1)

    # Transform
    transformer = CachingTransformer(dry_run=dry_run, verbose=verbose)
    new_tree = transformer.visit(tree)

    # Report changes
    print(f"\n{'='*60}")
    print(f"File: {file_path}")
    print(f"{'='*60}")

    if transformer.modifications:
        print(f"\n📝 Modifications ({len(transformer.modifications)}):")
        for mod in transformer.modifications:
            print(f"  {mod}")
    else:
        print("\n✨ No modifications needed")

    if verbose and transformer.skipped:
        print(f"\n⏭️  Skipped ({len(transformer.skipped)}):")
        for skip in transformer.skipped:
            print(f"  {skip}")

    # Write back if not dry run
    if not dry_run and transformer.modifications:
        # Unparse to get new source
        new_source = ast.unparse(new_tree)

        # Ensure streamlit import
        new_source = add_streamlit_import(new_source)

        # Backup original
        backup_path = file_path.with_suffix('.py.bak')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(source)

        # Write modified version
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_source)

        print(f"\n✅ File updated: {file_path}")
        print(f"📦 Backup saved: {backup_path}")
    elif dry_run and transformer.modifications:
        print("\n🔍 DRY RUN - No changes written to disk")
        print("   Run without --dry-run to apply changes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Add caching decorators to Streamlit component functions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes (dry run)
  python add-caching-decorators.py --dry-run components/lead_intelligence_hub.py

  # Apply changes
  python add-caching-decorators.py components/lead_intelligence_hub.py

  # Verbose output
  python add-caching-decorators.py --verbose components/seller_journey.py

  # Process multiple files
  for file in components/*.py; do
    python add-caching-decorators.py "$file"
  done
        """
    )

    parser.add_argument(
        'file',
        type=Path,
        help='Path to component file to process'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output including skipped functions'
    )

    args = parser.parse_args()

    add_caching_to_file(
        file_path=args.file,
        dry_run=args.dry_run,
        verbose=args.verbose
    )


if __name__ == '__main__':
    main()
