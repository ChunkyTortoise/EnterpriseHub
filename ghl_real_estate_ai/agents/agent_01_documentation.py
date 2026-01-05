#!/usr/bin/env python3
"""
Documentation Agent - Add comprehensive inline comments
Focuses on critical business logic files
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple


class DocumentationAgent:
    """Analyzes Python code and adds comprehensive inline documentation."""
    
    def __init__(self, base_dir: str = "ghl_real_estate_ai"):
        self.base_dir = Path(base_dir)
        self.files_processed = []
        self.comments_added = 0
    
    def analyze_function_complexity(self, func_node: ast.FunctionDef) -> dict:
        """Analyze function to determine documentation needs."""
        lines = func_node.end_lineno - func_node.lineno
        
        # Count different statement types
        branches = sum(1 for _ in ast.walk(func_node) if isinstance(_, (ast.If, ast.For, ast.While)))
        returns = sum(1 for _ in ast.walk(func_node) if isinstance(_, ast.Return))
        calls = sum(1 for _ in ast.walk(func_node) if isinstance(_, ast.Call))
        
        complexity = branches * 2 + calls + (lines // 10)
        
        return {
            "name": func_node.name,
            "lines": lines,
            "branches": branches,
            "returns": returns,
            "calls": calls,
            "complexity": complexity,
            "needs_comments": complexity > 10 or lines > 20
        }
    
    def add_function_documentation(self, source: str, func_info: dict) -> str:
        """Add inline comments to complex functions."""
        # This would use AST to add strategic comments
        # For now, return source unchanged
        return source
    
    def process_file(self, file_path: Path) -> Tuple[int, List[str]]:
        """Process a single Python file and add documentation."""
        if not file_path.exists():
            return 0, [f"File not found: {file_path}"]
        
        source = file_path.read_text()
        
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return 0, [f"Syntax error in {file_path}: {e}"]
        
        issues = []
        comments_added = 0
        
        # Analyze all functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                info = self.analyze_function_complexity(node)
                
                # Check for missing docstring
                docstring = ast.get_docstring(node)
                if not docstring:
                    issues.append(f"Missing docstring: {info['name']}")
                
                # Check if complex function needs comments
                if info['needs_comments']:
                    issues.append(f"Complex function needs inline comments: {info['name']} (complexity: {info['complexity']})")
        
        return comments_added, issues
    
    def generate_report(self) -> str:
        """Generate documentation report."""
        report = ["# Documentation Agent Report\n"]
        report.append(f"Files processed: {len(self.files_processed)}\n")
        report.append(f"Comments added: {self.comments_added}\n")
        return "".join(report)


def main():
    """Run documentation agent."""
    agent = DocumentationAgent()
    
    target_files = [
        "services/analytics_engine.py",
        "services/lead_lifecycle.py",
        "services/campaign_analytics.py",
        "services/bulk_operations.py",
        "services/reengagement_engine.py",
        "core/rag_engine.py",
        "core/conversation_manager.py"
    ]
    
    print("🤖 Documentation Agent Starting...\n")
    
    for file_rel in target_files:
        file_path = Path("ghl_real_estate_ai") / file_rel
        print(f"Analyzing: {file_rel}")
        
        comments, issues = agent.process_file(file_path)
        
        if issues:
            print(f"  Issues found: {len(issues)}")
            for issue in issues[:5]:  # Show first 5
                print(f"    - {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more")
        else:
            print(f"  ✅ No issues found")
        print()
    
    print(agent.generate_report())


if __name__ == "__main__":
    main()
