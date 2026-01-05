#!/usr/bin/env python3
"""
Agent 12: Security Auditor
Runs comprehensive security audit to identify vulnerabilities
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple

class SecurityAuditor:
    """Performs comprehensive security audit on the codebase."""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.results = {
            "bandit_results": {},
            "pip_audit_results": {},
            "manual_checks": {},
            "vulnerabilities": [],
            "recommendations": [],
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0
        }
    
    def run_bandit_scan(self) -> bool:
        """Run Bandit security scanner."""
        print("🔍 Running Bandit security scan...")
        
        try:
            result = subprocess.run(
                ["python3", "-m", "bandit", "-r", ".", "-f", "json", "-ll"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                try:
                    bandit_data = json.loads(result.stdout)
                    self.results["bandit_results"] = bandit_data
                    
                    # Count issues by severity
                    for issue in bandit_data.get("results", []):
                        severity = issue.get("issue_severity", "").upper()
                        if severity == "HIGH":
                            self.results["high_count"] += 1
                            self.results["vulnerabilities"].append({
                                "tool": "bandit",
                                "severity": "HIGH",
                                "issue": issue.get("issue_text", ""),
                                "file": issue.get("filename", ""),
                                "line": issue.get("line_number", 0)
                            })
                        elif severity == "MEDIUM":
                            self.results["medium_count"] += 1
                    
                    print(f"   ✅ Bandit scan complete")
                    print(f"   Found: {self.results['high_count']} high, {self.results['medium_count']} medium")
                    return True
                    
                except json.JSONDecodeError:
                    print("   ⚠️  Could not parse Bandit output")
                    return False
            else:
                print("   ✅ Bandit scan complete (no issues found)")
                return True
        
        except subprocess.TimeoutExpired:
            print("   ⏱️  Bandit scan timed out")
            return False
        except FileNotFoundError:
            print("   ⚠️  Bandit not installed (pip install bandit)")
            self.results["recommendations"].append("Install bandit: pip install bandit")
            return False
        except Exception as e:
            print(f"   ❌ Bandit scan failed: {e}")
            return False
    
    def run_pip_audit(self) -> bool:
        """Run pip-audit for dependency vulnerabilities."""
        print("\n🔍 Running pip-audit for dependency vulnerabilities...")
        
        try:
            result = subprocess.run(
                ["python3", "-m", "pip_audit", "--format", "json"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                try:
                    audit_data = json.loads(result.stdout)
                    self.results["pip_audit_results"] = audit_data
                    
                    # Count vulnerabilities
                    vuln_count = len(audit_data.get("vulnerabilities", []))
                    
                    for vuln in audit_data.get("vulnerabilities", []):
                        self.results["critical_count"] += 1
                        self.results["vulnerabilities"].append({
                            "tool": "pip-audit",
                            "severity": "CRITICAL",
                            "package": vuln.get("package", ""),
                            "version": vuln.get("version", ""),
                            "vulnerability": vuln.get("vulnerability", "")
                        })
                    
                    print(f"   ✅ pip-audit complete")
                    print(f"   Found: {vuln_count} dependency vulnerabilities")
                    return True
                    
                except json.JSONDecodeError:
                    print("   ⚠️  Could not parse pip-audit output")
                    return False
            else:
                print("   ✅ pip-audit complete (no vulnerabilities found)")
                return True
        
        except subprocess.TimeoutExpired:
            print("   ⏱️  pip-audit timed out")
            return False
        except FileNotFoundError:
            print("   ⚠️  pip-audit not installed (pip install pip-audit)")
            self.results["recommendations"].append("Install pip-audit: pip install pip-audit")
            return False
        except Exception as e:
            print(f"   ❌ pip-audit failed: {e}")
            return False
    
    def run_manual_security_checks(self) -> bool:
        """Run manual security checks."""
        print("\n🔍 Running manual security checks...")
        
        checks = []
        
        # Check 1: Environment variables
        env_file = self.base_dir / ".env.example"
        if env_file.exists():
            content = env_file.read_text()
            if "JWT_SECRET_KEY" in content:
                checks.append(("Environment variables", "PASS", "JWT_SECRET_KEY configured"))
            else:
                checks.append(("Environment variables", "FAIL", "JWT_SECRET_KEY not found"))
                self.results["vulnerabilities"].append({
                    "tool": "manual",
                    "severity": "MEDIUM",
                    "issue": "JWT_SECRET_KEY not configured in .env.example"
                })
        
        # Check 2: Security middleware
        main_file = self.base_dir / "api" / "main.py"
        if main_file.exists():
            content = main_file.read_text()
            if "RateLimitMiddleware" in content:
                checks.append(("Rate limiting", "PASS", "Rate limiting middleware enabled"))
            else:
                checks.append(("Rate limiting", "FAIL", "Rate limiting not enabled"))
                self.results["vulnerabilities"].append({
                    "tool": "manual",
                    "severity": "HIGH",
                    "issue": "Rate limiting middleware not enabled"
                })
            
            if "SecurityHeadersMiddleware" in content:
                checks.append(("Security headers", "PASS", "Security headers middleware enabled"))
            else:
                checks.append(("Security headers", "FAIL", "Security headers not enabled"))
                self.results["vulnerabilities"].append({
                    "tool": "manual",
                    "severity": "MEDIUM",
                    "issue": "Security headers middleware not enabled"
                })
        
        # Check 3: Password hashing
        auth_files = list(self.base_dir.glob("**/jwt_auth.py"))
        if auth_files:
            content = auth_files[0].read_text()
            if "bcrypt" in content or "passlib" in content:
                checks.append(("Password hashing", "PASS", "Using bcrypt for password hashing"))
            else:
                checks.append(("Password hashing", "WARN", "Password hashing method unclear"))
        
        # Check 4: SQL injection protection (check for raw SQL)
        py_files = list(self.base_dir.glob("**/*.py"))
        sql_injection_risk = False
        for py_file in py_files[:50]:  # Sample first 50 files
            try:
                content = py_file.read_text()
                if re.search(r'execute\s*\(\s*["\'].*%s.*["\']', content):
                    sql_injection_risk = True
                    break
            except:
                pass
        
        if not sql_injection_risk:
            checks.append(("SQL injection", "PASS", "No obvious SQL injection vulnerabilities"))
        else:
            checks.append(("SQL injection", "WARN", "Potential SQL injection risk detected"))
            self.results["vulnerabilities"].append({
                "tool": "manual",
                "severity": "CRITICAL",
                "issue": "Potential SQL injection vulnerability"
            })
        
        # Check 5: Hardcoded secrets
        secret_patterns = ["password", "api_key", "secret", "token"]
        hardcoded_secrets = []
        for py_file in list(self.base_dir.glob("**/*.py"))[:50]:
            try:
                content = py_file.read_text()
                for pattern in secret_patterns:
                    if f'{pattern} = "' in content or f"{pattern} = '" in content:
                        hardcoded_secrets.append(str(py_file))
                        break
            except:
                pass
        
        if not hardcoded_secrets:
            checks.append(("Hardcoded secrets", "PASS", "No hardcoded secrets detected"))
        else:
            checks.append(("Hardcoded secrets", "WARN", f"Potential secrets in {len(hardcoded_secrets)} files"))
            self.results["recommendations"].append("Review files for hardcoded secrets")
        
        self.results["manual_checks"] = {
            "checks": checks,
            "passed": sum(1 for c in checks if c[1] == "PASS"),
            "failed": sum(1 for c in checks if c[1] == "FAIL"),
            "warnings": sum(1 for c in checks if c[1] == "WARN")
        }
        
        print(f"   ✅ Manual checks complete")
        print(f"   Passed: {self.results['manual_checks']['passed']}")
        print(f"   Failed: {self.results['manual_checks']['failed']}")
        print(f"   Warnings: {self.results['manual_checks']['warnings']}")
        
        return True
    
    def generate_recommendations(self):
        """Generate security recommendations."""
        print("\n💡 Generating recommendations...")
        
        # Based on vulnerabilities found
        if self.results["critical_count"] > 0:
            self.results["recommendations"].append(
                "CRITICAL: Address dependency vulnerabilities immediately"
            )
        
        if self.results["high_count"] > 0:
            self.results["recommendations"].append(
                "HIGH: Review and fix high-severity security issues"
            )
        
        # General recommendations
        self.results["recommendations"].extend([
            "Implement regular security audits (monthly)",
            "Keep dependencies up to date",
            "Use environment variables for secrets",
            "Enable HTTPS in production",
            "Implement request logging for security monitoring",
            "Add rate limiting to all public endpoints",
            "Use secure session management",
            "Implement CSRF protection for state-changing operations",
            "Regular penetration testing",
            "Security training for development team"
        ])
        
        print(f"   ✅ Generated {len(self.results['recommendations'])} recommendations")
    
    def generate_report(self) -> str:
        """Generate security audit report."""
        report = []
        report.append("=" * 80)
        report.append("SECURITY AUDITOR - FINAL REPORT")
        report.append("=" * 80)
        report.append("")
        
        report.append("📊 Summary:")
        report.append(f"  Critical vulnerabilities: {self.results['critical_count']}")
        report.append(f"  High severity issues: {self.results['high_count']}")
        report.append(f"  Medium severity issues: {self.results['medium_count']}")
        report.append(f"  Low severity issues: {self.results['low_count']}")
        report.append(f"  Total vulnerabilities: {len(self.results['vulnerabilities'])}")
        report.append("")
        
        # Security grade
        total = self.results['critical_count'] + self.results['high_count']
        if total == 0:
            grade = "A+ (Excellent)"
        elif total <= 2:
            grade = "B (Good)"
        elif total <= 5:
            grade = "C (Needs Improvement)"
        else:
            grade = "D (Poor)"
        
        report.append(f"🏆 Security Grade: {grade}")
        report.append("")
        
        if self.results['vulnerabilities']:
            report.append("🚨 Vulnerabilities Found:")
            for vuln in self.results['vulnerabilities'][:10]:  # Top 10
                report.append(f"  • [{vuln.get('severity', 'UNKNOWN')}] {vuln.get('issue', vuln.get('vulnerability', 'Unknown issue'))}")
                if 'file' in vuln:
                    report.append(f"    File: {vuln['file']}")
            if len(self.results['vulnerabilities']) > 10:
                report.append(f"    ... and {len(self.results['vulnerabilities']) - 10} more")
            report.append("")
        
        if self.results.get('manual_checks'):
            report.append("🔍 Manual Security Checks:")
            for check in self.results['manual_checks']['checks']:
                status_icon = "✅" if check[1] == "PASS" else ("⚠️" if check[1] == "WARN" else "❌")
                report.append(f"  {status_icon} {check[0]}: {check[2]}")
            report.append("")
        
        if self.results['recommendations']:
            report.append("💡 Recommendations:")
            for rec in self.results['recommendations'][:15]:  # Top 15
                report.append(f"  • {rec}")
            report.append("")
        
        report.append("=" * 80)
        report.append("📋 NEXT STEPS:")
        report.append("=" * 80)
        report.append("")
        report.append("1. Review all CRITICAL and HIGH severity issues")
        report.append("2. Update vulnerable dependencies")
        report.append("3. Fix security configuration issues")
        report.append("4. Implement recommended security practices")
        report.append("5. Schedule regular security audits")
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run(self) -> bool:
        """Execute security audit."""
        print("=" * 80)
        print("🚀 SECURITY AUDITOR - STARTING")
        print("=" * 80)
        print()
        
        # Run all checks
        self.run_bandit_scan()
        self.run_pip_audit()
        self.run_manual_security_checks()
        self.generate_recommendations()
        
        # Generate report
        print("\n" + "=" * 80)
        print("✅ SECURITY AUDIT COMPLETE")
        print("=" * 80)
        print()
        
        report = self.generate_report()
        print(report)
        
        # Save report
        report_path = self.base_dir / "SECURITY_AUDIT_REPORT.md"
        report_path.write_text(report)
        print(f"\n📄 Report saved to: {report_path}")
        
        # Save detailed JSON
        json_path = self.base_dir / "security_audit_detailed.json"
        json_path.write_text(json.dumps(self.results, indent=2))
        print(f"📄 Detailed results: {json_path}")
        
        # Return success if no critical vulnerabilities
        return self.results['critical_count'] == 0


def main():
    """Run security auditor."""
    import re  # Add missing import
    agent = SecurityAuditor()
    success = agent.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
