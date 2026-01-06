#!/usr/bin/env python3
"""
🔍 Alpha - Code Auditor Agent
============================

Specialized agent for code quality analysis, security scanning, and best practices.

Author: Agent Swarm System
Date: 2026-01-05
"""

import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import json


@dataclass
class CodeIssue:
    """Code issue definition"""
    file: str
    line: int
    severity: str  # critical, high, medium, low, info
    category: str  # security, performance, style, maintainability
    message: str
    suggestion: Optional[str] = None


class AlphaCodeAuditor:
    """Alpha Agent - Code Quality and Security Auditor"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[CodeIssue] = []
        self.stats = {
            "files_analyzed": 0,
            "total_lines": 0,
            "issues_found": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
    
    def analyze_project_structure(self) -> Dict:
        """Task 001: Analyze complete project structure"""
        print("\n🔍 Alpha Agent: Analyzing project structure...")
        
        structure = {
            "services": [],
            "tests": [],
            "agents": [],
            "api_routes": [],
            "core_modules": [],
            "scripts": [],
            "streamlit_pages": []
        }
        
        # Scan directory structure
        services_dir = self.project_root / "services"
        if services_dir.exists():
            structure["services"] = [f.name for f in services_dir.glob("*.py") if f.name != "__init__.py"]
        
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            structure["tests"] = [f.name for f in tests_dir.glob("test_*.py")]
        
        agents_dir = self.project_root / "agents"
        if agents_dir.exists():
            structure["agents"] = [f.name for f in agents_dir.glob("*.py") if f.name != "__init__.py"]
        
        api_dir = self.project_root / "api" / "routes"
        if api_dir.exists():
            structure["api_routes"] = [f.name for f in api_dir.glob("*.py") if f.name != "__init__.py"]
        
        core_dir = self.project_root / "core"
        if core_dir.exists():
            structure["core_modules"] = [f.name for f in core_dir.glob("*.py") if f.name != "__init__.py"]
        
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():
            structure["scripts"] = [f.name for f in scripts_dir.glob("*.py")]
        
        streamlit_dir = self.project_root / "streamlit_demo" / "pages"
        if streamlit_dir.exists():
            structure["streamlit_pages"] = [f.name for f in streamlit_dir.glob("*.py")]
        
        print(f"   ✅ Found {len(structure['services'])} services")
        print(f"   ✅ Found {len(structure['tests'])} test files")
        print(f"   ✅ Found {len(structure['agents'])} agent files")
        print(f"   ✅ Found {len(structure['api_routes'])} API routes")
        print(f"   ✅ Found {len(structure['core_modules'])} core modules")
        print(f"   ✅ Found {len(structure['streamlit_pages'])} Streamlit pages")
        
        return structure
    
    def run_code_quality_audit(self) -> Dict:
        """Task 003: Comprehensive code quality audit"""
        print("\n🔍 Alpha Agent: Running code quality audit...")
        
        # Check for common issues
        self._check_import_quality()
        self._check_function_complexity()
        self._check_docstring_coverage()
        self._check_error_handling()
        
        # Generate report
        report = {
            "timestamp": "2026-01-05",
            "issues": [
                {
                    "file": issue.file,
                    "line": issue.line,
                    "severity": issue.severity,
                    "category": issue.category,
                    "message": issue.message,
                    "suggestion": issue.suggestion
                }
                for issue in self.issues
            ],
            "statistics": self.stats
        }
        
        print(f"   ✅ Analyzed {self.stats['files_analyzed']} files")
        print(f"   ⚠️  Found {self.stats['issues_found']} issues")
        print(f"      - Critical: {self.stats['critical']}")
        print(f"      - High: {self.stats['high']}")
        print(f"      - Medium: {self.stats['medium']}")
        print(f"      - Low: {self.stats['low']}")
        
        return report
    
    def run_security_scan(self) -> Dict:
        """Task 004: Security vulnerability scanning"""
        print("\n🔒 Alpha Agent: Running security vulnerability scan...")
        
        security_issues = []
        
        # Check for common security issues
        self._check_hardcoded_secrets()
        self._check_sql_injection_risks()
        self._check_xss_risks()
        self._check_insecure_dependencies()
        
        # Filter security-specific issues
        security_issues = [i for i in self.issues if i.category == "security"]
        
        report = {
            "timestamp": "2026-01-05",
            "security_issues": len(security_issues),
            "critical_vulnerabilities": len([i for i in security_issues if i.severity == "critical"]),
            "high_vulnerabilities": len([i for i in security_issues if i.severity == "high"]),
            "issues": [
                {
                    "file": issue.file,
                    "line": issue.line,
                    "severity": issue.severity,
                    "message": issue.message,
                    "suggestion": issue.suggestion
                }
                for issue in security_issues
            ]
        }
        
        print(f"   ✅ Security scan complete")
        print(f"   🔒 Found {len(security_issues)} security issues")
        print(f"      - Critical: {report['critical_vulnerabilities']}")
        print(f"      - High: {report['high_vulnerabilities']}")
        
        return report
    
    def _check_import_quality(self):
        """Check import statement quality"""
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    # Check for wildcard imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if any(alias.name == "*" for alias in node.names):
                                self.issues.append(CodeIssue(
                                    file=str(py_file.relative_to(self.project_root)),
                                    line=node.lineno,
                                    severity="medium",
                                    category="style",
                                    message="Wildcard import detected",
                                    suggestion="Import specific names instead of using *"
                                ))
                                self.stats["medium"] += 1
                                self.stats["issues_found"] += 1
                
                self.stats["files_analyzed"] += 1
                self.stats["total_lines"] += len(content.splitlines())
                
            except Exception as e:
                pass  # Skip files that can't be parsed
    
    def _check_function_complexity(self):
        """Check function complexity"""
        # Simplified check - count functions with many lines
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file) or "test_" in py_file.name:
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            # Count lines in function
                            if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                                func_lines = node.end_lineno - node.lineno
                                if func_lines > 100:
                                    self.issues.append(CodeIssue(
                                        file=str(py_file.relative_to(self.project_root)),
                                        line=node.lineno,
                                        severity="low",
                                        category="maintainability",
                                        message=f"Function '{node.name}' is very long ({func_lines} lines)",
                                        suggestion="Consider breaking down into smaller functions"
                                    ))
                                    self.stats["low"] += 1
                                    self.stats["issues_found"] += 1
            except Exception as e:
                pass
    
    def _check_docstring_coverage(self):
        """Check docstring coverage"""
        missing_docstrings = 0
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file) or "test_" in py_file.name:
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            if not ast.get_docstring(node):
                                missing_docstrings += 1
                                # Only report for public functions/classes
                                if not node.name.startswith('_'):
                                    self.issues.append(CodeIssue(
                                        file=str(py_file.relative_to(self.project_root)),
                                        line=node.lineno,
                                        severity="low",
                                        category="maintainability",
                                        message=f"{node.__class__.__name__} '{node.name}' missing docstring",
                                        suggestion="Add docstring to document purpose and usage"
                                    ))
                                    self.stats["low"] += 1
                                    self.stats["issues_found"] += 1
            except Exception as e:
                pass
    
    def _check_error_handling(self):
        """Check error handling patterns"""
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ExceptHandler):
                            # Check for bare except
                            if node.type is None:
                                self.issues.append(CodeIssue(
                                    file=str(py_file.relative_to(self.project_root)),
                                    line=node.lineno,
                                    severity="medium",
                                    category="maintainability",
                                    message="Bare except clause detected",
                                    suggestion="Catch specific exception types"
                                ))
                                self.stats["medium"] += 1
                                self.stats["issues_found"] += 1
            except Exception as e:
                pass
    
    def _check_hardcoded_secrets(self):
        """Check for hardcoded secrets"""
        patterns = [
            "password =",
            "api_key =",
            "secret =",
            "token =",
            "AWS_SECRET",
            "PRIVATE_KEY"
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue
            
            try:
                with open(py_file) as f:
                    for line_num, line in enumerate(f, 1):
                        line_lower = line.lower()
                        for pattern in patterns:
                            if pattern.lower() in line_lower and "=" in line and not line.strip().startswith("#"):
                                # Check if it's not an env var reference
                                if "os.getenv" not in line and "environ" not in line:
                                    self.issues.append(CodeIssue(
                                        file=str(py_file.relative_to(self.project_root)),
                                        line=line_num,
                                        severity="high",
                                        category="security",
                                        message="Potential hardcoded secret detected",
                                        suggestion="Use environment variables or secret management"
                                    ))
                                    self.stats["high"] += 1
                                    self.stats["issues_found"] += 1
                                    break
            except Exception as e:
                pass
    
    def _check_sql_injection_risks(self):
        """Check for SQL injection risks"""
        # Look for string concatenation in SQL queries
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue
            
            try:
                with open(py_file) as f:
                    for line_num, line in enumerate(f, 1):
                        if "SELECT" in line.upper() or "INSERT" in line.upper() or "UPDATE" in line.upper():
                            if "+" in line or "%" in line or ".format(" in line:
                                self.issues.append(CodeIssue(
                                    file=str(py_file.relative_to(self.project_root)),
                                    line=line_num,
                                    severity="high",
                                    category="security",
                                    message="Potential SQL injection risk",
                                    suggestion="Use parameterized queries"
                                ))
                                self.stats["high"] += 1
                                self.stats["issues_found"] += 1
            except Exception as e:
                pass
    
    def _check_xss_risks(self):
        """Check for XSS risks"""
        # Basic check for unsafe HTML rendering
        patterns = ["innerHTML", "dangerouslySetInnerHTML", "eval("]
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue
            
            try:
                with open(py_file) as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern in patterns:
                            if pattern in line:
                                self.issues.append(CodeIssue(
                                    file=str(py_file.relative_to(self.project_root)),
                                    line=line_num,
                                    severity="medium",
                                    category="security",
                                    message=f"Potential XSS risk: {pattern}",
                                    suggestion="Sanitize user input before rendering"
                                ))
                                self.stats["medium"] += 1
                                self.stats["issues_found"] += 1
                                break
            except Exception as e:
                pass
    
    def _check_insecure_dependencies(self):
        """Check for known insecure dependencies"""
        requirements_file = self.project_root / "requirements.txt"
        
        if requirements_file.exists():
            print("   📦 Checking dependencies...")
            # This would integrate with pip-audit or safety
            # For now, just note that we should run it
            self.issues.append(CodeIssue(
                file="requirements.txt",
                line=1,
                severity="info",
                category="security",
                message="Run 'pip-audit' to check for vulnerable dependencies",
                suggestion="pip install pip-audit && pip-audit"
            ))
    
    def generate_report(self, output_file: Optional[Path] = None) -> str:
        """Generate comprehensive audit report"""
        report = f"""
# Alpha Code Auditor Report
Generated: 2026-01-05

## Summary
- Files Analyzed: {self.stats['files_analyzed']}
- Total Lines: {self.stats['total_lines']:,}
- Issues Found: {self.stats['issues_found']}

## Issue Breakdown
- 🔴 Critical: {self.stats['critical']}
- 🟠 High: {self.stats['high']}
- 🟡 Medium: {self.stats['medium']}
- 🔵 Low: {self.stats['low']}

## Issues by Category
"""
        
        # Group issues by category
        by_category = {}
        for issue in self.issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)
        
        for category, issues in by_category.items():
            report += f"\n### {category.title()} ({len(issues)} issues)\n"
            for issue in issues[:10]:  # Show first 10 per category
                report += f"- [{issue.severity}] {issue.file}:{issue.line} - {issue.message}\n"
        
        if output_file:
            output_file.write_text(report)
        
        return report


def main():
    """Test the agent"""
    project_root = Path(__file__).parent.parent
    agent = AlphaCodeAuditor(project_root)
    
    # Run analysis
    structure = agent.analyze_project_structure()
    print(f"\n📊 Project Structure:")
    print(json.dumps(structure, indent=2))
    
    # Run quality audit
    quality_report = agent.run_code_quality_audit()
    
    # Run security scan
    security_report = agent.run_security_scan()
    
    # Generate report
    report_file = project_root / "reports" / "alpha_audit_report.md"
    report_file.parent.mkdir(exist_ok=True)
    agent.generate_report(report_file)
    
    print(f"\n✅ Alpha Agent complete!")
    print(f"📄 Report saved to: {report_file}")


if __name__ == "__main__":
    main()
